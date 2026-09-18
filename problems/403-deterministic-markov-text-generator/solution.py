import re


def _tokens(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)*", text.lower())


def build_frequency_map(corpus):
    tokens = _tokens(corpus)
    counts = {}
    for a, b in zip(tokens, tokens[1:]):
        row = counts.setdefault(a, {})
        row[b] = row.get(b, 0) + 1
    return counts


def generate_text(transition_map, start_word, steps):
    result = _tokens(start_word)
    for _ in range(steps):
        choices = transition_map.get(result[-1], {})
        if not choices:
            break
        result.append(min(choices, key=lambda word: (-choices[word], word)))
    return " ".join(result)
