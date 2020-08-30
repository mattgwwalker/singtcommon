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
    
