import random


def generate_sentence(corpus, k, rng=None):
    tokens = corpus.split()
    if k <= 0:
        return ""

    transitions = {}
    for current, next_word in zip(tokens, tokens[1:]):
        transitions.setdefault(current, []).append(next_word)

    chooser = rng or random
    result = [chooser.choice(tokens)]
    for _ in range(k - 1):
        result.append(chooser.choice(transitions[result[-1]]))
    return " ".join(result)
