import pytest

from singtcommon import JitterBuffer

def test_create_jitter_buffer():
    jitter_buffer = JitterBuffer()

def test_len_zero_items_zero_buffer():
    jitter_buffer = JitterBuffer(buffer_length=0)
    assert len(jitter_buffer) == 0

def test_len_zero_items_non_zero_buffer():
    buffer_length=2
    jitter_buffer = JitterBuffer(
        buffer_length=buffer_length
    )
    assert len(jitter_buffer) == buffer_length

def test_repeated_alternating_put_get():
    jitter_buffer = JitterBuffer(buffer_length=0)
    
    for i in range(1000):
        jitter_buffer.put_packet(i,i)
        out = jitter_buffer.get_packet()
        assert out == i
        assert len(jitter_buffer) == 0

def test_repeated_alternating_put_get_with_buffer():
    buffer_length = 3
    jitter_buffer = JitterBuffer(
        buffer_length=buffer_length
    )

    for i in range(1000):
        jitter_buffer.put_packet(i,i)
        out = jitter_buffer.get_packet()
        if i < buffer_length:
            assert out is None
        else:
            assert out == i-buffer_length
        assert len(jitter_buffer) == buffer_length

def test_out_of_order_packet():
    jitter_buffer = JitterBuffer(buffer_length=0)

    jitter_buffer.put_packet(0,0)
    assert len(jitter_buffer) == 1

    out = jitter_buffer.get_packet()
    assert out == 0
    assert len(jitter_buffer) == 0

    # Packet should be discarded
    jitter_buffer.put_packet(0,0)
    assert len(jitter_buffer) == 0
    
    # Packet should be kept
    jitter_buffer.put_packet(2,2)
    assert len(jitter_buffer) == 1
    
def test_ignores_before_first_put():
    buffer_length = 1
    jitter_buffer = JitterBuffer(
        buffer_length = buffer_length
    )

    # Get before put
    out = jitter_buffer.get_packet()
    assert out is None
    assert len(jitter_buffer) == buffer_length

    # First valid put
    value = 0
    jitter_buffer.put_packet(0, value)
    assert len(jitter_buffer) == buffer_length+1

    # Get after put
    out = jitter_buffer.get_packet()
    assert out is None
    assert len(jitter_buffer) == buffer_length

    out = jitter_buffer.get_packet()
    assert out == value
    assert len(jitter_buffer) == buffer_length-1
    
def test_get_from_empty():
    buffer_length = 0
    jitter_buffer = JitterBuffer(
        buffer_length = buffer_length
    )

    # First valid put
    value = 0
    jitter_buffer.put_packet(0, value)
    assert len(jitter_buffer) == buffer_length+1

    # Get after put
    out = jitter_buffer.get_packet()
    assert out == value
    assert len(jitter_buffer) == buffer_length

    # Second get (from empty buffer)
    out = jitter_buffer.get_packet()
    assert out is None
    assert len(jitter_buffer) == 0
    
def test_get_out_of_order_packets():
    # Create jitter buffer
    buffer_length = 0
    jitter_buffer = JitterBuffer(
        buffer_length = buffer_length
    )

    # First valid put (sets expected value)
    value0 = 0
    jitter_buffer.put_packet(value0, value0)
    assert len(jitter_buffer) == buffer_length+1

    # Out-of-order put
    value1 = 2
    jitter_buffer.put_packet(value1, value1)
    assert len(jitter_buffer) == buffer_length+2

    # Get initial packet
    out = jitter_buffer.get_packet()
    assert out is value0
    assert len(jitter_buffer) == buffer_length+1

    # Get missing packet
    out = jitter_buffer.get_packet()
    assert out is None
    assert len(jitter_buffer) == buffer_length+1 # because the None wasn't ever stored

    # Second get (from out-of-order packets)
    out = jitter_buffer.get_packet()
    assert out is value1
    assert len(jitter_buffer) == buffer_length
    
def test_stress_test():
    import random
    random.seed(1234)
    buffer_length = 5
    jitter_buffer = JitterBuffer(
        buffer_length=buffer_length
    )

    # Set the roll-over value to a lower number to test the roll-over
    # code
    roll_over = 30
    jitter_buffer._seq_no_rollover = roll_over

    # Put the first value of zero to set the expected sequence number
    jitter_buffer.put_packet(0,0)
    
    buf = []
    i = 1
    j = 0
    gots = 0
    expected = 0
    while True:
        if i > 1000 and len(buf)==0:
            break
        if len(buf) == 0:
            buf = list(range(i,i+5))
            random.shuffle(buf)
            i += 5
        x = buf.pop()
        print("putting", x)
        jitter_buffer.put_packet(
            x%roll_over,
            x
        )
        out = jitter_buffer.get_packet()
        gots += 1
        print("got", out)
        if gots <= buffer_length:
            assert out is None
        else:
            print("expected:", expected)
            assert out == expected
            expected += 1

def test_overly_large_seq_no():
    jitter_buffer = JitterBuffer()

    # Set the roll-over value to a lower number to test the roll-over
    # code
    roll_over = 2
    jitter_buffer._seq_no_rollover = roll_over

    with pytest.raises(Exception):
        jitter_buffer.put_packet(roll_over, None)
