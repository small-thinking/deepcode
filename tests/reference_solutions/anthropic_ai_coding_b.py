import asyncio


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
