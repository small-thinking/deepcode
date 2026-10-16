from collections import Counter
from fractions import Fraction


def distinctive_characters(words, use_jaccard=False):
    counts = [Counter(word) for word in words]
    if use_jaccard:
        scores = []
        for i, left in enumerate(counts):
            total = Fraction(0)
            for j, right in enumerate(counts):
                if i != j:
                    intersection = sum((left & right).values())
                    union = sum((left | right).values())
                    total += Fraction(intersection, union)
            scores.append(total / (len(words) - 1))
    else:
        scores = [Fraction(max(count.values()), len(word))
                  for count, word in zip(counts, words)]

    best = min(scores)
    selected = [i for i, score in enumerate(scores) if score == best]
    selected_set = set(selected)
    excluded = set()
    for i, word in enumerate(words):
        if i not in selected_set:
            excluded.update(word)
    return ''.join(char for i in selected for char in words[i]
                   if char not in excluded)
