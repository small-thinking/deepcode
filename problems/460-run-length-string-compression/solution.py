def compress_runs(s):
    parts = []
    start = 0
    while start < len(s):
        end = start + 1
        while end < len(s) and s[end] == s[start]:
            end += 1
        parts.append(s[start])
        if end - start > 1:
            parts.append(str(end - start))
        start = end
    return "".join(parts)
