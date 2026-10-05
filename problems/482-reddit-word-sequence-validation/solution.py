def valid_word_sequence(words):
    for left, right in zip(words, words[1:]):
        if len(left) != len(right):
            return False
        if sum(a != b for a, b in zip(left, right)) != 1:
            return False
    return True
