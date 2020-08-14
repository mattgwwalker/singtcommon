from singtcommon import TCPPacketizer
from mock_transport import MockTransport

def test_init():
    t = MockTransport()
    p = TCPPacketizer(t)

    assert p

def test_send_recv_one_packet():
    t = MockTransport()
    p = TCPPacketizer(t)
    msg = "test message"
    p.write(msg)

    encoded_msg = t._buffer
    print("encoded_msg:", encoded_msg)
    result = p.decode(encoded_msg)
    
    assert result == [msg]
    
def test_send_recv_two_packets():
    t = MockTransport()
    p = TCPPacketizer(t)
    msg1 = "test message #1"
    msg2 = "test message #2"
    p.write(msg1)
    p.write(msg2)

    encoded_msg = t._buffer
    print("encoded_msg:", encoded_msg)
    result = p.decode(encoded_msg)
    
    assert result == [msg1, msg2]
    
