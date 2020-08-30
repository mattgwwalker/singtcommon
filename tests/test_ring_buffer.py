import numpy
import pytest

from singtcommon import RingBuffer

def test_create_ring_buffer():
    shape = (1000,2)
    ring_buffer = RingBuffer(shape)

    assert ring_buffer

def test_store_and_retrieve_1D_data():
    shape = (1000,)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    data = b"\x01" * 10
    array = numpy.frombuffer(data, dtype=numpy.uint8)

    # Put data into ring buffer
    ring_buffer.put(array)

    # Get data from ring buffer
    out_array = numpy.zeros(array.shape, dtype=numpy.uint8) 
    ring_buffer.get(out_array)

    # Check that the input and output are the same
    assert numpy.all(array == out_array)

def test_store_and_retrieve_2D_data():
    shape = (1000,2)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    data = b"\x01" * 10
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data)//2), 2)

    # Put data into ring buffer
    ring_buffer.put(array)

    # Get data from ring buffer
    out_array = numpy.zeros(array.shape, dtype=numpy.uint8) 
    ring_buffer.get(out_array)

    # Check that the input and output are the same
    assert numpy.all(array == out_array)

def test_wrap_around():
    shape = (10,1)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    data = b"\x01" * 8
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))

    # Put data into ring buffer
    ring_buffer.put(array)

    # Get data from ring buffer
    out_array = numpy.zeros(array.shape, dtype=numpy.uint8) 
    ring_buffer.get(out_array)

    # Check that the input and output are the same
    assert numpy.all(array == out_array)

    data = b"\x02\x03\x04"
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))

    # Put data into ring buffer
    ring_buffer.put(array)

    # Get data from ring buffer
    out_array = numpy.zeros(array.shape, dtype=numpy.uint8) 
    ring_buffer.get(out_array)

    # Check that the input and output are the same
    assert numpy.all(array == out_array)

def test_buffer_too_small():
    shape = (10,1)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    data = b"\x01" * 11
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))

    # Put data into ring buffer
    with pytest.raises(Exception):
        ring_buffer.put(array)

def test_buffer_overflow():
    shape = (10,1)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    data = b"\x01" * 9
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))
    ring_buffer.put(array)

    data = b"\x01" * 2
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))
    
    # Put data into ring buffer
    with pytest.raises(Exception):
        ring_buffer.put(array)

def test_buffer_overflow_in_wrap_around():
    shape = (10,1)
    ring_buffer = RingBuffer(shape, dtype=numpy.uint8)

    # Add and remove 9 items to place the consumer index towards the
    # end of the buffer.
    data = b"\x01" * 9
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))
    ring_buffer.put(array)
    out_data = numpy.zeros(array.shape, dtype=numpy.uint8)
    ring_buffer.get(out_data)

    # Add items to place the producer on the left of the consumer.
    data = b"\x01" * 6
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))
    ring_buffer.put(array)
    out_data = numpy.zeros(array.shape, dtype=numpy.uint8)

    # Attempt to add too many items for the remaining space.
    data = b"\x01" * 5
    array = numpy.frombuffer(data, dtype=numpy.uint8)
    array = array.reshape((len(data), 1))
    
    # Put data into ring buffer
    with pytest.raises(Exception):
        ring_buffer.put(array)
    
def test_buffer_underrun():
    shape = (3,)
    ring_buffer = RingBuffer(shape, dtype=numpy.int32)

    # Attempt to get data that's not available
    out_data = numpy.zeros((1,), dtype=numpy.uint8)
    with pytest.raises(Exception):
        ring_buffer.get(out_data)

def test_put_incorrect_shape():
    shape = (10,)
    ring_buffer = RingBuffer(shape, dtype=numpy.int32)

    # Attempt to put data that's not the right shape
    array = numpy.zeros((1,2), dtype=numpy.int32)
    with pytest.raises(Exception):
        ring_buffer.put(array)
    
def test_put_incorrect_type():
    shape = (10,)
    ring_buffer = RingBuffer(shape, dtype=numpy.int32)

    # Attempt to put data that's not the right type
    array = numpy.zeros((1), dtype=numpy.int8)
    with pytest.raises(Exception):
        ring_buffer.put(array)
    
def test_stress_test():
    import random
    random.seed(1234)

    # Create RingBuffer
    shape = (250,2)
    ring_buffer = RingBuffer(shape, dtype=numpy.int32)

    producer_value = None
    def start_producer():
        # Fill buffer half-way
        data = list(range(shape[0]))
        array = numpy.array(
            data,
            dtype=numpy.int32
        ).reshape(
            (shape[0]//shape[1],
             shape[1])
        )
        ring_buffer.put(array)
        return data[-1]+1
    
    def produce(producer_value):
        # Choose randomly how many items to add
        num_items = random.randint(1,10)
        # Add the items
        data = list(range(
            producer_value,
            producer_value+(num_items*shape[1])
        ))
        array = numpy.array(data, dtype=numpy.int32).reshape(
            (num_items,shape[1])
        )
        ring_buffer.put(array)
        print("Added:\n", array)
        return data[-1]+1

    consumer_value = 0
    def consume(consumer_value):
        # Choose randomly how many items to remove
        num_items = random.randint(1,10)
        # Remove the items
        array = numpy.zeros(
            (num_items, shape[1]),
            dtype=numpy.int32
        )
        ring_buffer.get(array)
        print("Consumed:\n", array)
        # Check their values
        data = list(range(
            consumer_value,
            consumer_value+(num_items*shape[1])
        ))
        expected_array = numpy.array(data).reshape(
            (num_items,shape[1])
        )
        assert numpy.all(array == expected_array)
        return data[-1]+1
    
    producer_value = start_producer()
    for _ in range(1000):
        producer_value = produce(producer_value)
        consumer_value = consume(consumer_value)
