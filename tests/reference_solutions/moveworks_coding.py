from collections import defaultdict


def next_hangman_letter(pattern, guessed, words):
    revealed = set(pattern) - {"_"}
    wrong = guessed - revealed
    containing_words = defaultdict(int)
    total_occurrences = defaultdict(int)

    for word in words:
        if len(word) != len(pattern):
            continue
        if any(
            shown != "_" and shown != letter
            for shown, letter in zip(pattern, word)
        ):
            continue
        if any(letter in wrong for letter in word):
            continue
        if any(
            shown == "_" and letter in guessed
            for shown, letter in zip(pattern, word)
        ):
            continue

        for letter in set(word) - guessed:
            containing_words[letter] += 1
        for letter in word:
            if letter not in guessed:
                total_occurrences[letter] += 1

    if not containing_words:
        return ""

    return min(
        containing_words,
        key=lambda letter: (
            -containing_words[letter],
            -total_occurrences[letter],
            letter,
        ),
    )


def highlight_unique_substrings(words):
    normalized = [word.lower() for word in words]
    owners = defaultdict(set)

    for word_index, word in enumerate(normalized):
        for start in range(len(word)):
            for end in range(start + 1, len(word) + 1):
                owners[word[start:end]].add(word_index)

    highlighted = []
    for word_index, (original, word) in enumerate(zip(words, normalized)):
        chosen = None
        for length in range(1, len(word) + 1):
            for start in range(len(word) - length + 1):
                end = start + length
                substring_owners = owners[word[start:end]]
                if len(substring_owners) == 1 and word_index in substring_owners:
                    chosen = (start, end)
                    break
            if chosen is not None:
                break

        assert chosen is not None
        start, end = chosen
        highlighted.append(original[:start] + "[" + original[start:end] + "]" + original[end:])

    return highlighted
