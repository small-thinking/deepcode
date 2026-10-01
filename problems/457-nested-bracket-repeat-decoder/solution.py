def decode_bracket_repeats(encoded: str) -> str:
    frames = []
    current = ""
    count = 0

    for char in encoded:
        if char.isdigit():
            count = count * 10 + int(char)
        elif char == "[":
            frames.append((current, count))
            current = ""
            count = 0
        elif char == "]":
            prefix, repeats = frames.pop()
            current = prefix + current * repeats
        else:
            current += char

    return current
