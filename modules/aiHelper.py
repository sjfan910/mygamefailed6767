import threading
from wordfreq import zipf_frequency
from modules.validation import shared_validator

"""
AI Helper module for Boggle Game.
Suggests a common word still available on the board using a greedy beam search.

__BeamSearchNode Class:
Key Attributes:
 - self.row, self.col - Current tile position on the board
 - self.word - Word string built so far along this path
 - self.path - List of (row, col) tiles visited in order
 - self.visited - Set of (row, col) tiles used, prevents revisiting
 - self.score - Zipf frequency score used to rank this node against others

Key Methods:
 - _calculate_score(self):
        - Scores a single starting letter using a fixed frequency table
        - For longer words, uses zipf_frequency() to score the full word
        - Higher score = more common = prioritised in the beam

AIHelper Class:
Key Attributes:
 - self.validator - Shared WordValidator used to check prefixes and words
 - self.beam_width - Number of top-scoring paths kept at each step (2)
 - self.max_word_length - Maximum word length the search will build (5)

Key Methods:
 - suggest_word(self, board, found_words, initial_threshold):
        - Entry point: tries to find a word above the frequency threshold
        - If no word found at current threshold, lowers it by 1.0 and retries
        - Returns (word, path) or (None, None) if nothing found
 - __search_with_threshold(self, board, found_words, threshold):
        - Launches one thread per tile, each running beam search from that tile
        - Uses a threading Event to stop all threads once a result is found
        - Picks the highest-frequency result from all threads
 - __beam_search(self, board, start_row, start_col, found_words, threshold, found_result):
        - Beam search from a single starting tile
        - Each step: checks current beam nodes for valid words above threshold
        - Expands each node in all 8 directions, keeping only top beam_width candidates
        - Prunes paths that don't match any dictionary prefix (early termination)

Algorithm Flow:
    - suggest_word() called with current board and already-found words
    - One thread launched per tile on the board
    - Each thread runs __beam_search() from its tile
    - Beam keeps top 2 paths by Zipf score at each expansion step
    - First valid word above threshold is returned
    - If no result, threshold lowered and search retried
"""


class _BeamSearchNode:
    def __init__(self, row, col, word, path, visited):
        self.row = row
        self.col = col
        self.word = word
        self.path = path.copy()
        self.visited = visited.copy()
        self.score = self._calculate_score()

    def _calculate_score(self):
        if len(self.word) < 2:
            # Single letter — use a fixed frequency table to bias toward common starting letters
            letter_freq = {
                'E': 8, 'T': 7.5, 'A': 7.5, 'O': 7, 'I': 7, 'N': 7,
                'S': 6.5, 'H': 6.5, 'R': 6, 'D': 5.5, 'L': 5.5, 'U': 5
            }
            return letter_freq.get(self.word[-1], 3.0)
        # For longer words, score by actual word frequency
        return zipf_frequency(self.word.lower(), 'en')


class AIHelper:
    def __init__(self):
        self.validator = shared_validator
        self.beam_width = 2       # keep only top 2 paths at each step
        self.max_word_length = 5  # don't build words longer than 5 letters

    def suggest_word(self, board, found_words, initial_threshold=4.0) -> str:
        threshold = initial_threshold
        # Lower threshold by 1.0 each retry until a word is found or threshold hits 0
        while threshold >= 0:
            result = self.__search_with_threshold(board, found_words, threshold)
            if result[0] is not None:
                return result
            threshold -= 1.0
        return (None, None)

    def __search_with_threshold(self, board, found_words, threshold) -> str:
        rows = len(board)
        cols = len(board[0])
        results = []
        results_lock = threading.Lock()
        found_result = threading.Event()  # signals all threads to stop once a result is found

        def search_from_tile(start_row, start_col):
            if found_result.is_set():
                return
            result = self.__beam_search(board, start_row, start_col, found_words, threshold, found_result)
            if result[0] is not None:
                with results_lock:
                    results.append(result)
                    found_result.set()

        # Launch one thread per board tile so all starting positions are searched in parallel
        threads = []
        for row in range(rows):
            for col in range(cols):
                thread = threading.Thread(target=search_from_tile, args=(row, col))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        if results:
            # Return the highest-frequency word found across all threads
            results.sort(key=lambda x: zipf_frequency(x[0].lower(), 'en'), reverse=True)
            return results[0]
        return (None, None)

    def __beam_search(self, board, start_row, start_col, found_words, threshold, found_result):
        rows = len(board)
        cols = len(board[0])

        visited = set()
        visited.add((start_row, start_col))
        initial_node = _BeamSearchNode(
            start_row, start_col,
            board[start_row][start_col],
            [(start_row, start_col)],
            visited
        )
        beam = [initial_node]

        directions = [(-1, -1), (-1, 0), (-1, 1),
                      ( 0, -1),          ( 0, 1),
                      ( 1, -1), ( 1, 0), ( 1, 1)]

        while beam and len(beam[0].word) <= self.max_word_length:
            if found_result.is_set():
                return (None, None)

            # Check each node in the current beam for a valid word above threshold
            for node in beam:
                if (len(node.word) >= 3 and
                        node.word.upper() not in found_words and
                        self.validator.is_valid_word(node.word)):
                    if zipf_frequency(node.word.lower(), 'en') >= threshold:
                        return (node.word.upper(), node.path)

            # Expand beam: try all 8 directions from each current node
            candidates = []
            for node in beam:
                for dr, dc in directions:
                    new_row = node.row + dr
                    new_col = node.col + dc

                    if not (0 <= new_row < rows and 0 <= new_col < cols):
                        continue
                    if (new_row, new_col) in node.visited:
                        continue
                    new_word = node.word + board[new_row][new_col]
                    # Prune paths that can't lead to any dictionary word
                    if not self.validator.is_valid_prefix(new_word):
                        continue

                    new_visited = node.visited.copy()
                    new_visited.add((new_row, new_col))
                    new_path = node.path + [(new_row, new_col)]
                    candidates.append(_BeamSearchNode(new_row, new_col, new_word, new_path, new_visited))

            if not candidates:
                break

            # Keep only the top beam_width candidates by score
            candidates.sort(key=lambda n: n.score, reverse=True)
            beam = candidates[:self.beam_width]

        return (None, None)
