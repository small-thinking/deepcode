def format_book_titles(titles, width, wrap=False):
    if width <= 0:
        raise ValueError("width must be positive")
    if not titles:
        return []
    border = "+" + "-" * width + "+"
    result = [border]
    for title in titles:
        if not wrap:
            if len(title) > width:
                raise ValueError("title exceeds width")
            lines = [title]
        else:
            lines = []
            current = []
            current_length = 0
            for word in title.split():
                if len(word) > width:
                    raise ValueError("word exceeds width")
                if current and current_length + 1 + len(word) > width:
                    lines.append(" ".join(current))
                    current = []
                    current_length = 0
                current_length += len(word) + bool(current)
                current.append(word)
            lines.append(" ".join(current))
        for line in lines:
            result.append("|" + line.ljust(width) + "|")
        result.append(border)
    return result
