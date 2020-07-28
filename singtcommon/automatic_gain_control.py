import numpy
import math

class AutomaticGainControl:
    def __init__(self, max_gain=30):
        self.gain = 1
        self.mu = 0.1
        self.target = 0.5
        self.max_gain = max_gain

    def apply(self, sample):
        """Applies automatic gain to the given sample.

        Overwrites data in place.

        """
        # Store previous gain
        old_gain = self.gain

        # Apply previous gain to form temp array
        temp = sample * self.gain

        # Measure max of scaled input
        max_in_sample = numpy.max(abs(temp))

        # Calculate difference compared to desired gain
        error = self.target - max_in_sample

        # Check if there's been a very loud noise.
        if max_in_sample > 0.95:
            # A very loud noise has been detected, cut the gain in
            # half immediately
            self.gain /= 2
        else:
            # A very loud noise hasn't been detected, so just
            # calculate the new gain normally.
            self.gain += self.mu * error
            if math.isnan(self.gain):
                self.gain = 1
            if self.gain > self.max_gain:
                self.gain = self.max_gain
            if self.gain < 0:
                self.gain = 0

        # Create a linear scaling from the old value to the new one
        channels = sample.shape[1]
        multiplier = numpy.linspace(
            start = [old_gain] * channels,
            stop = [self.gain] * channels,
            num = len(sample)
        )

        # Apply multiplier to input
        sample *= multiplier


if __name__ == "__main__":
    try:
        import sounddevice as sd
    except:
        print("The module 'sounddevice' must be installed for this script to run.")
        exit()
    
    print("Testing automatic gain control:")

    agc = AutomaticGainControl()

    def callback(indata, outdata, frames, time, status):
        if status:
            print(status)

        # Automatic gain control
        agc.apply(indata)
        print("gain:", agc.gain)
        
        # Ensure that indata is clipped from -1 to 1.  This isn't the
        # case on a Mac, but it most certainly is the case once the
        # audio has been encoded and decoded with Opus.
        numpy.clip(indata, -1, 1)
            

        # Write to output
        outdata[:] = indata


    stream = sd.Stream(
        callback = callback
    )

    with stream:
        print("Press any key to finish")
        input()
