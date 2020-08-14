import struct
import time
from enum import Enum

class _State(Enum):
    STARTING = 10
    CONTINUING = 20

class TCPPacketizer:
    def __init__(self, transport):
        self._transport = transport
        
        self._buffer = b""
        self._state = _State.STARTING
        self._length = None

        
    def write(self, msg):
        """Writes a string over TCP."""
        msg_as_bytes = msg.encode("utf-8")
        len_as_short = struct.pack("H", len(msg))
        encoded_msg = len_as_short + msg_as_bytes
        self._transport.write(encoded_msg)

        
    def decode(self, data):
        #print("Received data:", data)

        # Combine current data with buffer
        data = self._buffer + data

        packets = []
        while len(data) > 0:
            #print("Considering data:", data)
            
            if self._state == _State.STARTING:
                # Read the first two bytes as a short integer
                self._length = struct.unpack("H",data[0:2])[0]
                #print("length:",self._length)

                # Remove the short from the data
                data = data[2:]

                # Move to CONTINUING
                self._state = _State.CONTINUING

            if self._state == _State.CONTINUING:
                # Do we have all the required characters in the current data?
                if len(data) >= self._length:
                    # Separate the current message
                    msg = data[:self._length]

                    # Process the message
                    packets.append(msg.decode("utf-8"))

                    # Remove the current message from any remaining data
                    data = data[self._length:]

                    # Move back to STARTING
                    self._state = _State.STARTING
                else:
                    # We do not have sufficient characters.  Store them in
                    # the buffer till next time we receive data.
                    #print("We do not have sufficient characters; waiting")
                    #print("len(data):", len(data))
                    self._buffer = data
                    data = ""

        return packets
