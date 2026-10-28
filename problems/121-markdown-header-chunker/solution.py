def chunk_markdown(markdown, max_size):
    headers = []
    previous = ()
    current = []
    chunks = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        level = len(line) - len(line.lstrip("#"))
        if 1 <= level <= 6 and line[level:level + 1] == " ":
            while headers and headers[-1][0] >= level:
                headers.pop()
            headers.append((level, line))
            continue

        breadcrumb = tuple(text for _, text in headers)
        common = 0
        while (common < min(len(previous), len(breadcrumb))
               and previous[common] == breadcrumb[common]):
            common += 1
        addition = list(breadcrumb[common:]) + [line]
        candidate = current + addition
        if len("\n".join(candidate).encode("utf-8")) <= max_size:
            current = candidate
        else:
            chunks.append("\n".join(current))
            current = list(breadcrumb) + [line]
        previous = breadcrumb

    if current:
        chunks.append("\n".join(current))
    return chunks
