def find_straight_words(board, words):
    if not board:
        return set()
    rows, cols = len(board), len(board[0])
    directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
    found = set()
    for word in words:
        for row in range(rows):
            for col in range(cols):
                for dr, dc in directions:
                    if all(0 <= row + step * dr < rows
                           and 0 <= col + step * dc < cols
                           and board[row + step * dr][col + step * dc] == letter
                           for step, letter in enumerate(word)):
                        found.add(word)
    return found
