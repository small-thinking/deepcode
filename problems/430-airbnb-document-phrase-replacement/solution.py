def redact_document(text, phrases, replacements):
    assert len(phrases) == len(replacements)
    assert all(phrases) and len(set(phrases)) == len(phrases)
    candidates = sorted(zip(phrases, replacements), key=lambda item: -len(item[0]))

    def is_word(char):
        return ('a' <= char <= 'z' or 'A' <= char <= 'Z'
                or '0' <= char <= '9' or char == '_')

    output = []
    i = 0
    while i < len(text):
        matched = False
        for phrase, replacement in candidates:
            end = i + len(phrase)
            if not text.startswith(phrase, i):
                continue
            if i > 0 and is_word(text[i - 1]):
                continue
            if end < len(text) and is_word(text[end]):
                continue
            output.append(replacement)
            i = end
            matched = True
            break
        if not matched:
            output.append(text[i])
            i += 1
    return ''.join(output)
