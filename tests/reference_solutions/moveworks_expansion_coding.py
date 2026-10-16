def fullJustify(words, maxWidth):
    lines = []
    start = 0
    while start < len(words):
        end = start + 1
        letters = len(words[start])
        while end < len(words) and letters + (end - start) + len(words[end]) <= maxWidth:
            letters += len(words[end])
            end += 1

        count = end - start
        if end == len(words) or count == 1:
            line = " ".join(words[start:end]).ljust(maxWidth)
        else:
            gaps = count - 1
            spaces, extra = divmod(maxWidth - letters, gaps)
            line = "".join(
                word + " " * (spaces + (offset < extra))
                for offset, word in enumerate(words[start:end - 1])
            ) + words[end - 1]
        lines.append(line)
        start = end
    return lines


def parse_citation_ranges(text):
    ranges = []
    cursor = 0
    while cursor < len(text):
        if text[cursor] != "[":
            cursor += 1
            continue
        end = text.index("]", cursor + 1)
        citation = text[cursor + 1:end]
        if "-" in citation:
            start, stop = citation.split("-")
            ranges.append([int(start), int(stop)])
        else:
            number = int(citation)
            ranges.append([number, number])
        cursor = end + 1
    return ranges


def merge_citation_ranges(left, right):
    ranges = sorted(parse_citation_ranges(left) + parse_citation_ranges(right))
    merged = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def rewrite_queries(text, synonym_groups):
    words = text.split() if text else []
    alternatives = {}
    for group in synonym_groups:
        phrases = [tuple(phrase.split()) for phrase in group]
        for phrase in phrases:
            alternatives.setdefault(phrase, set()).update(phrases)

    def generate(start):
        if start == len(words):
            return {()}
        results = set()
        for ending in generate(start + 1):
            results.add((words[start],) + ending)
        for phrase, replacements in alternatives.items():
            stop = start + len(phrase)
            if tuple(words[start:stop]) != phrase:
                continue
            for replacement in replacements:
                for ending in generate(stop):
                    results.add(replacement + ending)
        return results

    return sorted(" ".join(result) for result in generate(0))


def word_break_sentences(s, word_dict):
    from functools import lru_cache

    dictionary = set(word_dict)

    @lru_cache(None)
    def sentences_from(start):
        if start == len(s):
            return ("",)
        results = []
        for end in range(start + 1, len(s) + 1):
            word = s[start:end]
            if word not in dictionary:
                continue
            for suffix in sentences_from(end):
                results.append(word if not suffix else word + " " + suffix)
        return tuple(results)

    return sorted(set(sentences_from(0)))
