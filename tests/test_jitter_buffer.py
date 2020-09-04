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
    

def test_overly_large_seq_no():
    jitter_buffer = JitterBuffer()

    # Set the roll-over value to a lower number to test the roll-over
    # code
    roll_over = 2
    jitter_buffer._seq_no_rollover = roll_over

    with pytest.raises(Exception):
        jitter_buffer.put_packet(roll_over, None)


def test_stress_test2():
    import random
    random.seed(1234)
    from collections import deque
    
    # Create jitter buffer
    jitter_buffer = JitterBuffer()
    
    # Set the roll-over value
    roll_over = 1000
    jitter_buffer._seq_no_rollover = roll_over
    
    # Number of packets to simulate
    number_of_packets = 200000

    # Duration per packet at source
    packet_duration = 20 / 1000 # seconds

    # Packet values
    packet_values = [i for i in range(number_of_packets)]

    # Generate missing packets
    prob_missing = 0.05
    keep = int(len(packet_values) * (1-prob_missing))
    packet_values = random.sample(packet_values, keep)

    # Packet arrival times (no delay)
    packet_times = [i*packet_duration for i in packet_values]

    # Add noise in packet arrival time
    mu = 0
    sigma = packet_duration * 5
    packet_times = [t + random.gauss(mu, sigma) for t in packet_times]
    
    # Join the values and times
    packets = zip(packet_values, packet_times)

    # Sort the packets into the correct order
    sorted_packets = sorted(packets, key = lambda p: p[1])
    sorted_packets = deque(sorted_packets)


    t = 0 + packet_duration
    while True:
        # If the deque is empty, break
        if len(sorted_packets) == 0:
            break

        # Put first packet into the buffer if it appears before time t
        if sorted_packets[0][1] < t:
            value = sorted_packets[0][0]
            #print("putting", value)
            jitter_buffer.put_packet(
                value % roll_over,
                value
            )
            sorted_packets.popleft()
        else:
            # Get the next packet
            out = jitter_buffer.get_packet()
            #print("got", out)

            # Increment simulated time
            t += packet_duration

            # Check the length of the buffer
            #print("length:", len(jitter_buffer),"\n")

        
