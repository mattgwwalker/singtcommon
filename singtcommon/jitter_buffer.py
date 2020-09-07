import collections
import threading

# TODO: Given the Global interpreter lock (GIL), I'm not at all sure
# the reentrant lock is necessary.

class JitterBuffer:
    def __init__(self, buffer_length=3):
        self._buffer_lock = threading.RLock()

        with self._buffer_lock:
            self._buffer_length = buffer_length
            
            # The value at which sequence numbers roll back to zero
            self._seq_no_rollover = 2**16

            # Number of missed packets in a row to trigger buffer
            # reset
            self._max_missed_sequential_packets = 3

            self._reset_buffer()
            self._reset_stats()

    def __del__(self):
        self._print_stats()

    def __len__(self):
        with self._buffer_lock:
            return (
                len(self._buffer)
                + len(self._out_of_order_packets)
            )
            
    def put_packet(self, seq_no, packet):
        with self._buffer_lock:
            if seq_no >= self._seq_no_rollover:
                raise Exception(
                    f"Unexpectedly large sequence number ({seq_no}), "+
                    f"roll-over expected at {self._seq_no_rollover}"
                )

            # Update statistics
            self._put_packets += 1
            if len(self) > self._max_length:
                self._max_length = len(self)
            #print(f"jitter buffer recv'd packet number {seq_no} (buffer contains {self._get_buffer_size()} items)")

            self._started = True
            
            # If we don't know the expected sequence number, then just
            # use whatever we've received
            if self._expected_seq_no is None:
                self._expected_seq_no = seq_no

            # If this sequence number is the expected one then just
            # append it to the buffer
            if self._expected_seq_no == seq_no:
                self._buffer.append(packet)
                self._expected_seq_no += 1
                self._expected_seq_no %= self._seq_no_rollover

                # Check the out-of-order dictionary, maybe the next
                # packet is already waiting
                self._check_out_of_order_packets()
                
            else:
                # We have an out-of-order packet.  Check if it's
                # before or after the expected sequence number
                distance = self._calc_distance(
                    seq_no,
                    self._expected_seq_no
                )
                print("distance:",distance)

                # Check if the frame is too late
                if distance >= 0:
                    # Add it to the dictionary
                    print("Frame is ahead of what we were expecting; storing")
                    self._out_of_order_packets[seq_no] = packet
                else:
                    print("Frame is behind what we were expecting; discarding")
                    return

        
    def get_packet(self):
        with self._buffer_lock:
            #print(f"getting packet from jitter buffer (which contains {self._get_buffer_size()} items)")
            # Update statistics
            self._got_packets += 1
            self._total_length_at_get += len(self)

            if not self._started:
                #print("We haven't received our first packet; ignoring get request")
                return None
            
            # If the buffer is empty, give up on the currently
            # expected sequence number and return None
            if len(self._buffer) == 0:
                print(f"jitter buffer is giving up on the expected packet number {self._expected_seq_no} (total of {self._missed_packets} packets missed)")
                self._missed_packets += 1
                self._missed_sequential_packets += 1
                self._expected_seq_no += 1
                self._expected_seq_no %= self._seq_no_rollover
                self._check_out_of_order_packets()
                if self._missed_sequential_packets >= self._max_missed_sequential_packets:
                    print("Too many missed sequential packets; resetting jitter buffer")
                    self._reset_buffer()
                return None

            # Otherwise, return the first item
            self._missed_sequential_packets = 0
            packet = self._buffer.popleft()
            return packet


    def _reset_buffer(self):
        """Resets the buffer.

        Called as part of the constructor, but also called if too many
        packets have been missed.

        """
        with self._buffer_lock:
            self._expected_seq_no = None
            self._buffer = collections.deque()
            self._out_of_order_packets = {}

            # Only after the first packet has been 'put' do we allow
            # gets
            self._started = False

            # Fill the buffer with None's up to the given buffer
            # length
            for _ in range(self._buffer_length):
                self._buffer.append(None)

            self._missed_sequential_packets = 0

    def _reset_stats(self):
        self._put_packets = 0
        self._got_packets = 0
        self._missed_packets = 0
        self._max_length = 0
        self._total_length_at_get = 0

    def _print_stats(self):
        print("JitterBuffer statistics:")
        print("put packets:", self._put_packets)
        print("got packets:", self._got_packets)
        print("missed packets:", self._missed_packets)
        print("max length:", self._max_length)
        if self._got_packets > 0:
            print("average length at get:", round(self._total_length_at_get/self._got_packets, 1))
        
            
    def _check_out_of_order_packets(self):
        with self._buffer_lock:
            while self._expected_seq_no in self._out_of_order_packets:
                oo_packet = self._out_of_order_packets[self._expected_seq_no]
                self._buffer.append(oo_packet)
                del self._out_of_order_packets[self._expected_seq_no]
                self._expected_seq_no += 1
                self._expected_seq_no %= self._seq_no_rollover
                
        

    # Calculates most likely distance between two sequence numbers
    # given that they may have rolledover.
    def _calc_distance(self, new, current):
        adjusted_new = new + self._seq_no_rollover
        adjusted_current = current + self._seq_no_rollover

        distance = new - current

        def assess(n,c):
            if abs(n-c) < abs(distance):
                return n-c
            else:
                return distance

        distance = assess(adjusted_new, current)
        distance = assess(adjusted_new, adjusted_current)
        distance = assess(new, adjusted_current)

        return distance
