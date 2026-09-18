import random


def generate_sentence(corpus, k):
    tokens = corpus.split()
    if k <= 0:
        return ""

    transitions = {}
    for current, next_word in zip(tokens, tokens[1:]):
        transitions.setdefault(current, []).append(next_word)

    result = [random.choice(tokens)]
    for _ in range(k - 1):
        result.append(random.choice(transitions[result[-1]]))
    return " ".join(result)
