from modules.validation import shared_validator

"""
This file discovers all valid words hidden in a Boggle board.
We use DFS with prefix pruning to ensure optimisation.

Key Attributes:
 - self.validator - Reference to shared_validator (WordValidator) for word and prefix lookups

Key Methods:
 - __init__(self):
        - Constructor that assigns shared_validator so the same Trie is used across the game
 - find_all_words(self, board):
        - Starts DFS from every cell on the board — words can begin anywhere
        - Uses a set to store found words so duplicates from different paths are ignored
        - Returns a sorted list of all discovered valid words
 - __dfs(self, board, row, col, current_word, visited, found_words):
        - Recursive depth-first search that explores all possible word paths
        - board - 2D list of tile letters
        - row, col - current position
        - current_word - word being built as we traverse
        - visited - 2D boolean grid tracking which tiles are used in the current path
        - found_words - set collecting all valid words found
        - Base case: returns if out of bounds or tile already used in this path
        - Appends current tile's letter to current_word
        - Prefix pruning: abandons path immediately if no dictionary word starts with current_word
        - Marks tile as visited, checks if current_word is a valid word (length >= 3)
        - Recurses into all 8 adjacent tiles
        - Backtracks by unmarking the tile so other paths can use it
        - Time complexity: O(n) where n is board size

Algorithm Flow:
    - find_all_words() called with the generated board
    - DFS launched from every tile with a fresh visited grid
    - Each recursive call builds current_word one letter at a time
    - Trie prefix check prunes dead-end paths early
    - Valid words of 3+ letters added to found_words set
    - Sorted list returned to boardGen and gameplay
"""
class WordFinder:
    def __init__(self):
        self.validator = shared_validator

    def find_all_words(self, board):
        found_words = set()  # set prevents duplicate words from different paths
        rows = len(board)
        cols = len(board[0])
        # Start DFS from every cell — words can begin anywhere on the board
        for row in range(rows):
            for col in range(cols):
                visited = [[False] * cols for _ in range(rows)]
                self.__dfs(board, row, col, "", visited, found_words)

        return sorted(list(found_words))

    def __dfs(self, board, row, col, current_word, visited, found_words) -> None:
        # Base Cases: Out of Bounds or Path Used
        if row < 0 or row >= len(board) or col < 0 or col >= len(board[0]):
            return

        if visited[row][col]:
            return

        current_word += board[row][col]

        # Prefix pruning — abandon this path if no dictionary word starts with current_word
        if not self.validator.is_valid_prefix(current_word):
            return

        visited[row][col] = True  # mark tile as used for this path

        if len(current_word) >= 3 and self.validator.is_valid_word(current_word):
            found_words.add(current_word)

        # All 8 directions: diagonals + cardinal
        directions = [(-1, -1), (0, -1), (1, -1),
                      (-1,  0),          (1,  0),
                      (-1,  1), (0,  1), (1,  1)]

        for dr, dc in directions:
            self.__dfs(board, row + dr, col + dc, current_word, visited, found_words)

        visited[row][col] = False  # backtrack — unmark tile so other paths can use it