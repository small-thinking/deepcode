class BufferedFileWriter:
    def __init__(self, sink, capacity):
        assert type(capacity) is int and capacity > 0
        self.sink = sink
        self.capacity = capacity
        self.buffer = bytearray()

    def write(self, data):
        assert isinstance(data, bytes)
        offset = 0
        while offset < len(data):
            room = self.capacity - len(self.buffer)
            take = min(room, len(data) - offset)
            self.buffer.extend(data[offset:offset + take])
            offset += take
            if len(self.buffer) == self.capacity:
                self.flush()

    def flush(self):
        if self.buffer:
            self.sink.write(bytes(self.buffer))
            self.buffer.clear()
