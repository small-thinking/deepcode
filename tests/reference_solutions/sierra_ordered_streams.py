import heapq


class Stream:
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        raise NotImplementedError


class OrderedIntStream(Stream):
    def __init__(self, items):
        self.items = items
        self.index = 0

    def next(self):
        if self.index == len(self.items):
            raise StopIteration
        value = self.items[self.index]
        self.index += 1
        return value


class MultiplesStream(Stream):
    def __init__(self, base):
        self.base = base
        self.value = 0

    def next(self):
        self.value += self.base
        return self.value


class MergeStream(Stream):
    def __init__(self, streams):
        self.streams = list(streams)
        self.heap = []
        for index, stream in enumerate(self.streams):
            try:
                value = stream.next()
            except StopIteration:
                continue
            self.heap.append((value, index))
        heapq.heapify(self.heap)

    def next(self):
        if not self.heap:
            raise StopIteration
        value, index = heapq.heappop(self.heap)
        try:
            following = self.streams[index].next()
        except StopIteration:
            pass
        else:
            heapq.heappush(self.heap, (following, index))
        return value
