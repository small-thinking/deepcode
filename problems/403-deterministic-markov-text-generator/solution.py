import re


def _tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)*", text.lower())


def transition_counts(corpus):
    tokens = _tokens(corpus)
    counts = {}
    for a, b in zip(tokens, tokens[1:]):
        row = counts.setdefault(a, {})
        row[b] = row.get(b, 0) + 1
    return counts


def generate_text(corpus, start, steps):
    counts = transition_counts(corpus)
    result = _tokens(start)
    for _ in range(steps):
        choices = counts.get(result[-1], {})
        if not choices:
            break
        result.append(min(choices, key=lambda word: (-choices[word], word)))
    return " ".join(result)
