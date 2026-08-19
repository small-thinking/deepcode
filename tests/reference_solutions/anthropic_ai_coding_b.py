import asyncio
from collections import Counter

import numpy as np


async def crawl_work_queue(seed_urls, fetch, workers=4, retries=0):
    if not callable(fetch):
        raise ValueError("fetch must be callable")
    if type(workers) is not int or workers <= 0:
        raise ValueError("workers must be a positive integer")
    if type(retries) is not int or retries < 0:
        raise ValueError("retries must be a non-negative integer")
    if isinstance(seed_urls, str):
        raise ValueError("seed_urls must be a non-string iterable")
    try:
        seed_urls = list(seed_urls)
    except TypeError as error:
        raise ValueError("seed_urls must be iterable") from error
    if any(not isinstance(url, str) or not url for url in seed_urls):
        raise ValueError("seed URLs must be nonempty strings")

    queue = asyncio.Queue()
    states = {}
    attempts = {}
    scheduled = []

    def schedule(url):
        if url not in states:
            states[url] = "pending"
            attempts[url] = 0
            scheduled.append(url)
            queue.put_nowait(url)

    for url in seed_urls:
        schedule(url)

    async def worker():
        while True:
            url = await queue.get()
            try:
                attempts[url] += 1
                try:
                    links = await fetch(url)
                    if isinstance(links, str):
                        raise ValueError("fetch results must be non-string iterables")
                    links = list(links)
                    if any(not isinstance(link, str) or not link for link in links):
                        raise ValueError("fetch results contain an invalid URL")
                except Exception:
                    if attempts[url] <= retries:
                        queue.put_nowait(url)
                    else:
                        states[url] = "failed"
                else:
                    states[url] = "completed"
                    for link in links:
                        schedule(link)
            finally:
                queue.task_done()

    worker_tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    try:
        await queue.join()
    finally:
        for task in worker_tasks:
            task.cancel()
        await asyncio.gather(*worker_tasks, return_exceptions=True)

    return {
        "scheduled": scheduled,
        "completed": [url for url in scheduled if states[url] == "completed"],
        "failed": [url for url in scheduled if states[url] == "failed"],
        "attempts": attempts,
    }


def _merge_pair(tokens, pair):
    merged = []
    index = 0
    while index < len(tokens):
        if index + 1 < len(tokens) and (tokens[index], tokens[index + 1]) == pair:
            merged.append(tokens[index] + tokens[index + 1])
            index += 2
        else:
            merged.append(tokens[index])
            index += 1
    return merged


def fit_pair_tokenizer(corpus, max_merges):
    if isinstance(corpus, str):
        raise TypeError("corpus must be a non-string iterable")
    try:
        words = list(corpus)
    except TypeError as error:
        raise TypeError("corpus must be iterable") from error
    if any(not isinstance(word, str) for word in words):
        raise TypeError("corpus words must be strings")
    if any(not word for word in words):
        raise ValueError("corpus words must be nonempty")
    if type(max_merges) is not int:
        raise TypeError("max_merges must be an integer")
    if max_merges < 0:
        raise ValueError("max_merges must be non-negative")

    tokenized = [list(word) for word in words]
    merges = []
    for _ in range(max_merges):
        counts = Counter(
            (tokens[index], tokens[index + 1])
            for tokens in tokenized
            for index in range(len(tokens) - 1)
        )
        if not counts:
            break
        largest_count = max(counts.values())
        pair = min(pair for pair, count in counts.items() if count == largest_count)
        tokenized = [_merge_pair(tokens, pair) for tokens in tokenized]
        merges.append(pair)
    vocabulary = sorted({token for tokens in tokenized for token in tokens})
    return {"merges": merges, "vocabulary": vocabulary}


def encode_pair_tokens(text, merges):
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if isinstance(merges, str):
        raise TypeError("merges must be a non-string iterable")
    try:
        merges = list(merges)
    except TypeError as error:
        raise TypeError("merges must be iterable") from error
    normalized_merges = []
    for pair in merges:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError("each merge must contain two tokens")
        left, right = pair
        if not isinstance(left, str) or not isinstance(right, str):
            raise TypeError("merge tokens must be strings")
        if not left or not right:
            raise ValueError("merge tokens must be nonempty")
        normalized_merges.append((left, right))
    tokens = list(text)
    for pair in normalized_merges:
        tokens = _merge_pair(tokens, pair)
    return tokens


def process_image_batches(images, batch_size, process_batch):
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if not callable(process_batch):
        raise ValueError("process_batch must be callable")
    if isinstance(images, np.ndarray) or isinstance(images, (str, bytes)):
        raise ValueError("images must be a sequence of arrays")
    try:
        images = list(images)
    except TypeError as error:
        raise ValueError("images must be iterable") from error
    if not images:
        return []
    first_shape = None
    for image in images:
        if not isinstance(image, np.ndarray) or not image.shape or not image.size:
            raise ValueError("images must be nonempty NumPy arrays")
        if not np.issubdtype(image.dtype, np.number):
            raise ValueError("image dtypes must be numeric")
        if first_shape is None:
            first_shape = image.shape
        elif image.shape != first_shape:
            raise ValueError("image shapes must match")

    output = []
    for start in range(0, len(images), batch_size):
        batch = np.stack([image.copy() for image in images[start:start + batch_size]])
        processed = process_batch(batch)
        if not isinstance(processed, np.ndarray) or processed.shape != batch.shape:
            raise ValueError("process_batch must return a same-shaped NumPy array")
        output.extend(processed[index].copy() for index in range(processed.shape[0]))
    return output


def analyze_capacity_series(demand, capacity, window):
    if not isinstance(demand, np.ndarray) or not isinstance(capacity, np.ndarray):
        raise ValueError("demand and capacity must be NumPy arrays")
    if demand.ndim != 1 or capacity.ndim != 1 or demand.shape != capacity.shape or not demand.size:
        raise ValueError("arrays must be nonempty, one-dimensional, and aligned")
    if type(window) is not int or window <= 0:
        raise ValueError("window must be a positive integer")
    if not np.issubdtype(demand.dtype, np.number) or not np.issubdtype(capacity.dtype, np.number):
        raise ValueError("arrays must be numeric")
    if not np.isfinite(demand).all() or not np.isfinite(capacity).all():
        raise ValueError("arrays must be finite")
    if np.any(demand < 0) or np.any(capacity <= 0):
        raise ValueError("demand must be nonnegative and capacity positive")

    utilization = demand.astype(np.float64) / capacity.astype(np.float64)
    rolling_peak = np.empty_like(utilization)
    for index in range(utilization.size):
        rolling_peak[index] = utilization[max(0, index - window + 1):index + 1].max()
    overload_runs = []
    start = None
    for index, value in enumerate(utilization):
        if value > 1 and start is None:
            start = index
        elif value <= 1 and start is not None:
            overload_runs.append((start, index - 1))
            start = None
    if start is not None:
        overload_runs.append((start, utilization.size - 1))
    shortfall = np.maximum(demand.astype(np.float64) - capacity.astype(np.float64), 0.0).sum()
    return {
        "utilization": utilization,
        "rolling_peak": rolling_peak,
        "overload_runs": overload_runs,
        "summary": {
            "samples": int(utilization.size),
            "mean_utilization": float(utilization.mean()),
            "peak_utilization": float(utilization.max()),
            "total_shortfall": float(shortfall),
        },
    }
