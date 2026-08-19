from concurrent.futures import ThreadPoolExecutor


def crawl_in_rounds(seed_urls, fetch, workers=1):
    if not callable(fetch):
        raise ValueError("fetch must be callable")
    if type(workers) is not int or workers <= 0:
        raise ValueError("workers must be a positive integer")
    if isinstance(seed_urls, (str, bytes)):
        raise ValueError("seed_urls must be a non-string iterable")
    try:
        seeds = list(seed_urls)
    except TypeError as error:
        raise ValueError("seed_urls must be iterable") from error
    if any(not isinstance(url, str) or not url for url in seeds):
        raise ValueError("seed URLs must be non-empty strings")

    def fetch_links(url):
        links = fetch(url)
        if isinstance(links, (str, bytes)):
            raise ValueError("fetch results must be non-string iterables")
        try:
            links = list(links)
        except TypeError as error:
            raise ValueError("fetch results must be iterable") from error
        if any(not isinstance(link, str) or not link for link in links):
            raise ValueError("fetch results must contain non-empty strings")
        return links

    seen = set()
    frontier = []
    for seed in seeds:
        if seed not in seen:
            seen.add(seed)
            frontier.append(seed)

    levels = []
    while frontier:
        levels.append(frontier)
        if workers == 1:
            child_groups = [fetch_links(url) for url in frontier]
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                child_groups = list(executor.map(fetch_links, frontier))

        next_frontier = []
        for children in child_groups:
            for child in children:
                if child not in seen:
                    seen.add(child)
                    next_frontier.append(child)
        frontier = next_frontier

    return levels
