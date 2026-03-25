import random
from modules.wordFinder import WordFinder
from modules.validation import PreProcessing

"""
This file generates a Boggle board using real dice configurations.
We use WordFinder and PreProcessing to ensure the board has enough difficulty-appropriate words.

Key Attributes:
 - self.size - Grid dimensions (4 for classic 4x4, 5 for big 5x5)
 - self.difficulty - String value of 'Easy', 'Medium', or 'Hard'
 - self.word_finder - WordFinder instance used to find all words on a candidate board
 - self.band_validator - PreProcessing instance built for the chosen difficulty
        - Used to count only words that fall within the difficulty's Zipf frequency band

Constants (These are static data fixed for this file):
 - CLASSIC_DICE - Array of 16 Boggle dice, each containing 6 letters (for 4x4)
 - BIG_DICE - Array of 25 Boggle dice, each containing 6 letters (for 5x5)
 - These are real Boggle dice — letter distribution is designed to produce playable boards

Key Methods:
 - __init__(self, size=4, difficulty='Easy'):
        - Initialises board size and difficulty
        - Creates WordFinder for full word discovery
        - Creates PreProcessing(difficulty) as band_validator to filter by difficulty band
 - generate(self):
        - Attempts up to 100 times to produce a playable board
        - Uses dice-based generation for 4x4 and 5x5, falls back to weighted random
        - Finds all words on the board using WordFinder
        - Counts only words in the difficulty band using band_validator
        - Returns the first board with 50+ band words, or the last attempt if none qualify
 - __generate_from_dice(self, dice):
        - Shuffles the dice array to randomise tile positions
        - Picks one random face from each die
        - Converts 'Q' to 'Qu' (standard Boggle rule)
        - Returns completed 2D board array
 - __generate_random(self):
        - Fallback method using weighted English letter frequencies
        - Builds a letter pool where each letter appears proportional to its weight
        - Randomly samples from the pool to fill the board
 - __meets_difficulty(self, word_count):
        - Returns True if the board has at least 50 difficulty-band words
        - Difficulty shapes word frequency, not board structure

Algorithm Flow:
    - generate() called with size and difficulty already set
    - Loop up to 100 attempts
    - generate_from_dice() produces a candidate board
    - WordFinder.find_all_words() returns all valid words on the board
    - band_validator filters to words within the difficulty's Zipf band
    - meets_difficulty() checks band word count >= 50
    - Return board if suitable, otherwise retry
"""
class BoardGenerator:
    """Generates Boggle boards based on Boggle Dice"""

    # Classic Boggle dice (16 dice for 4x4)
    CLASSIC_DICE = [
        "AAEEGN", "ELRTTY", "AOOTTW", "ABBJOO",
        "EHRTVW", "CIMOTU", "DISTTY", "EIOSST",
        "DELRVY", "ACHOPS", "HIMNQU", "EEINSU",
        "EEGHNW", "AFFKPS", "HLNNRZ", "DEILRX"
    ]

    # Big Boggle dice (25 dice for 5x5)
    BIG_DICE = [
        "AAAFRS", "AAEEEE", "AAFIRS", "ADENNN", "AEEEEM",
        "AEEGMU", "AEGMNN", "AFIRSY", "BJKQXZ", "CCNSTW",
        "CEIILT", "CEILPT", "CEIPST", "DDLNOR", "DHHLOR",
        "DHHNOT", "DHLNOR", "EIIITT", "EMOTTT", "ENSSSU",
        "FIPRSY", "GORRVW", "HIPRRY", "NOOTUW", "OOOTTU"
    ]

    def __init__(self, size=4, difficulty='Easy'):
        self.size = size
        self.difficulty = difficulty
        self.word_finder = WordFinder()
        self.band_validator = PreProcessing(difficulty)

    def generate(self):
        max_attempts = 100

        for attempt in range(max_attempts):
            if self.size == 4:
                board = self.__generate_from_dice(self.CLASSIC_DICE)
            elif self.size == 5:
                board = self.__generate_from_dice(self.BIG_DICE)

            else: # Generate from random function (This was used for testing)
                board = self.__generate_random()

            all_words = self.word_finder.find_all_words(board)
            # Count only words that fall within this difficulty's frequency band
            band_count = sum(1 for w in all_words if self.band_validator.is_valid_word(w))
            if self.__meets_difficulty(band_count):
                print(f"Board generated in {attempt} attempts with {band_count} difficulty-band words (Difficulty: {self.difficulty})")
                return board

        print(f"Warning: Could not generate board meeting {self.difficulty} difficulty")
        return board

    def __generate_from_dice(self, dice):
        """Generate board using Boggle dice"""
        shuffled_dice = dice.copy()
        random.shuffle(shuffled_dice)
        board = []
        dice_index = 0
        for row in range(self.size):
            board_row = []
            for col in range(self.size):
                die = shuffled_dice[dice_index]
                letter = random.choice(die)
                if letter == 'Q':
                    letter = 'Qu'
                board_row.append(letter)
                dice_index += 1
            board.append(board_row)
        return board

    def __generate_random(self):
        """Generate board with weighted letters (This was used for testing)"""
        letter_weights = {
            'E': 12, 'T': 9, 'A': 8, 'O': 8, 'I': 7, 'N': 7,
            'S': 6, 'H': 6, 'R': 6, 'L': 4, 'D': 4, 'C': 3,
            'U': 3, 'M': 3, 'W': 2, 'F': 2, 'G': 2, 'Y': 2,
            'P': 2, 'B': 1, 'V': 1, 'K': 1, 'J': 1, 'X': 1,
            'Qu': 1, 'Z': 1
        }
        letter_pool = []
        for letter, weight in letter_weights.items():
            letter_pool.extend([letter] * weight)
        board = []
        for row in range(self.size):
            board_row = []
            for col in range(self.size):
                letter = random.choice(letter_pool)
                board_row.append(letter)
            board.append(board_row)
        return board

    def __meets_difficulty(self, word_count):
        """Check board has enough words to be playable (min 50, regardless of difficulty)"""
        return word_count >= 50
