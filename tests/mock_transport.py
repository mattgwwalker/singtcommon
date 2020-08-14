class MockTransport:
    def __init__(self):
        self._buffer = b''
        
    def write(self, msg):
        print(f"Ignoring transport of message: {msg}")
        self._buffer += msg
        print("self._buffer:", self._buffer)
