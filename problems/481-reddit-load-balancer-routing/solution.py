class Router:
    def __init__(self, backends):
        if not backends or len(set(backends)) != len(backends):
            raise ValueError('backends must be nonempty and unique')
        self.backends = list(backends)
        self.healthy = {backend: True for backend in backends}
        self.cursor = 0

    def set_health(self, backend, healthy):
        if backend not in self.healthy:
            raise ValueError('unknown backend')
        self.healthy[backend] = healthy

    def choose(self):
        for offset in range(len(self.backends)):
            index = (self.cursor + offset) % len(self.backends)
            backend = self.backends[index]
            if self.healthy[backend]:
                self.cursor = (index + 1) % len(self.backends)
                return backend
        return None

    def choose_lowest_latency(self, latencies):
        candidates = [backend for backend in self.backends
                      if self.healthy[backend] and backend in latencies]
        return min(candidates, key=latencies.__getitem__, default=None)
