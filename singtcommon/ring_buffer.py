import numpy

class RingBuffer:
    def __init__(self, shape, dtype=numpy.int16):
        self._buffer = numpy.zeros(shape, dtype=dtype)
        self._producer_index = 0
        self._consumer_index = 0

    def put(self, array):
        # Check we have matching dtypes
        if self._buffer.dtype != array.dtype:
            raise Exception(
                f"Buffer type ({self._buffer.dtype}) and "+
                f"array type ({array.dtype}) do not match"
            )
        
        # Calculate space remaining
        if self._producer_index >= self._consumer_index:
            space_remaining = (
                len(self._buffer)
                - (self._producer_index - self._consumer_index)
            )
        else:
            space_remaining = (
                self._consumer_index
                - self._producer_index
                - 1
            )
            
        # Check that array is not too big for the buffer
        if len(array) > space_remaining:
            raise Exception(
                f"Buffer overrun: Length of array ({len(array)}) "+
                f"too great for space remaining in buffer "+
                f"({space_remaining})"
            )
        
        # Copy the array into the buffer.  Check if copy can be direct
        # or whether we have to deal with wrapping from the end to the
        # start.
        if self._producer_index+len(array) <= len(self._buffer):
            # There's no wrap around, we can just do a straight copy
            self._buffer[
                self._producer_index:self._producer_index+len(array)
            ] = array[:]
            
            # Update the producer index
            self._producer_index += len(array)
            
        else:
            # The new data will overflow the end of the buffer and so
            # the overflow needs to be copied into the start of the
            # buffer.

            # First copy to the end of the buffer
            remaining_buffer = len(self._buffer) - self._producer_index
            self._buffer[
                self._producer_index:
            ] = array[:remaining_buffer]
            
            # Then copy to the start of the buffer
            self._buffer[
                :len(array)-remaining_buffer
            ] = array[remaining_buffer:]

            # Update the producee index
            self._producer_index = len(array)-remaining_buffer
        
    def get(self, out):
        # Check that there's sufficient data available
        if self._producer_index >= self._consumer_index:
            data_available = (
                self._producer_index - self._consumer_index
            )
        else:
            # Handle the wrap-around case
            data_available = (
                self._producer_index
                + len(self._buffer) - self._consumer_index
            )

        if len(out) > data_available:
            raise Exception(
                f"Buffer underrun: insufficient data available "+
                f"({data_available}) for the size of the request "+
                f"({len(out)})."
            )
                
        
        # Copy from the buffer to the ouput array.

        # Check if copy can be direct or if we have to deal with a
        # wrap-around from the end to the start.
        if self._consumer_index+len(out) <= len(self._buffer):
            # Copy the data into the output array directly; there's no
            # wrap-around to worry about.
            out[:] = self._buffer[
                self._consumer_index:self._consumer_index+len(out)
            ]

            # Update the consumer index
            self._consumer_index += len(out)

        else:
            # We have to deal with a wrap-around.
            # First copy up to the end of the buffer
            remaining_buffer = len(self._buffer) - self._consumer_index
            out[:remaining_buffer] = self._buffer[
                self._consumer_index:
            ]

            # Then copy from the start
            out[remaining_buffer:] = self._buffer[
                :len(out) - remaining_buffer
            ]

            # Update the consumer index
            self._consumer_index = len(out) - remaining_buffer
