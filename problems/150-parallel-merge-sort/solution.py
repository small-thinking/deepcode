from concurrent.futures import ThreadPoolExecutor
from heapq import merge


def parallel_merge_sort(values, workers):
    if not values:
        return []

    worker_count = min(workers, len(values))
    if worker_count == 1:
        return sorted(values)

    chunk_size = (len(values) + worker_count - 1) // worker_count
    chunks = [values[start:start + chunk_size] for start in range(0, len(values), chunk_size)]

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        sorted_chunks = list(pool.map(sorted, chunks))

    return list(merge(*sorted_chunks))
