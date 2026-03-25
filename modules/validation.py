import os
from wordfreq import zipf_frequency

"""
This file validates the current word against a difficulty-filtered dictionary
Uses a prefix tree (Trie) data structure built dynamically at runtime
Enables real-time word validation during gameplay

_TrieNode Class:
Key Attributes:
 - self.children - Dictionary mapping letters to child _TrieNodes
 - self.is_word - Boolean value indicating if path to this node forms a word
 - Each node can have up to 26 children and may represent the end of a word

_Trie Class:
Key Attributes:
 - self.root - The root _TrieNode

Key Methods:
 - __init__(self):
        - Constructor that creates an empty _Trie with root node
 - insert(self, word):
        - Adds a word to the _Trie
        - Start at a root
        - Process each letter in the word
        - If letter path doesn't exist, create new _TrieNode
        - Move down the tree following/creating the path
        - Set 'is_word' to True at final node
        - Ensure multiple words share common prefixes
 - search(self, word):
        - Checks if complete word exists in dictionary
        - Follow path letter by letter from root
        - Return False if any letter path missing
        - Check is_word at final node
        - True only if complete path exists and is_word is True
        - O(n) where n = word length
 - starts_with(self, prefix):
        - Check if prefix exists in dictionary
        - Follow prefix path letter by letter from root
        - Return False if prefix path does not exist
        - Return True if path exists

PreProcessing Class:
Key Attributes:
 - self.trie - _Trie instance built from difficulty-filtered word list

Constants:
 - DIFFICULTY_THRESHOLDS - Maps difficulty string to a (low, high) Zipf frequency band
        - Easy:   (4.00, 8.00) — very common everyday words
        - Medium: (3.50, 5.50) — moderately common words
        - Hard:   (3.00, 4.50) — includes rarer but valid Boggle words
        - Zipf scale runs 0-8; most known English words fall between 3 and 7
        - Bands are exclusive of each other so each word belongs to exactly one difficulty

Key Methods:
 - __init__(self, difficulty, dictionary_path, profanity_path):
        - Looks up Zipf frequency threshold for given difficulty
        - Loads banned words from profanity list into a set for O(1) lookup
        - Iterates over the source dictionary file
        - Filters out words shorter than 4 or longer than 15 characters
        - Filters out any word found in the profanity set
        - Calls zipf_frequency() on each remaining word
        - Inserts word into _Trie only if its frequency exceeds the threshold
        - Produces a _Trie whose contents are entirely determined by difficulty
 - is_valid_word(self, word):
        - Public interface checking if word exists in filtered dictionary
 - is_valid_prefix(self, prefix):
        - Public interface checking if prefix exists in filtered dictionary

WordValidator Class:
Key Attributes:
 - self.trie - Unfiltered _Trie built from the full dictionary (Zipf > 3.0, profanity removed)

Key Methods:
 - __init__(self, dictionary_path):
        - Builds an unfiltered Trie accepting any word with Zipf > 3.0
        - Used during gameplay — validates any word the player finds regardless of difficulty
 - __load_dictionary(self, path, profanity_path):
        - Loads profanity list into a set for O(1) lookup
        - Inserts words into Trie if length >= 3, not banned, and Zipf > 3.0
 - is_valid_word(self, word):
        - Public interface checking if word exists in dictionary
 - is_valid_prefix(self, prefix):
        - Public interface checking if prefix exists in dictionary

Algorithm Flow:
    - shared_validator built once at module load with full unfiltered dictionary
    - PreProcessing built per game with banded difficulty thresholds (used only by boardGen)
    - DFS and gameplay word checks use shared_validator
    - boardGen uses PreProcessing.trie to count difficulty-band words during generation
"""

class _TrieNode:
    def __init__(self):
        self.children = {} # Implement Nodes as HashMap
        self.is_word = False

class _Trie:
    def __init__(self):
        self.root = _TrieNode()

    def insert(self, word) -> None: # add a children node
        node = self.root
        for char in word.upper():
            if char not in node.children:
                node.children[char] = _TrieNode()
            node = node.children[char] # Travel down a layer
        node.is_word = True

    def search(self, word) -> bool:
        node = self.root
        for char in word.upper():
            if char not in node.children:
                return False
            node = node.children[char] # Travel down a layer
        return node.is_word

    def starts_with(self, prefix) -> bool: # Stops early for better performance
        node = self.root
        for char in prefix.upper():
            if char not in node.children:
                return False
            node = node.children[char]
        return True

class PreProcessing:
    DIFFICULTY_THRESHOLDS = {
        'Easy':   (4.00, 8.00),
        'Medium': (3.50, 5.50),
        'Hard':   (3.00, 4.50),
    }

    def __init__(self, difficulty, dictionary_path='data/enable1.txt', profanity_path='data/profanity_wordlist.txt'):
        self.trie = _Trie()
        low, high = self.DIFFICULTY_THRESHOLDS[difficulty]  # unpack the frequency band for this difficulty

        # Load profanity list into a set for fast O(1) lookup during filtering
        banned = set()
        if os.path.exists(profanity_path):
            with open(profanity_path, 'r') as f:
                for line in f:
                    banned.add(line.strip().lower())

        word_count = 0
        with open(dictionary_path, 'r') as f:
            for line in f:
                word = line.strip()
                # Skip words that are too short, too long, or banned
                if len(word) < 3 or len(word) > 16 or word.lower() in banned:
                    continue
                frequency = zipf_frequency(word, 'en')
                # Only insert words that fall within this difficulty's frequency band
                if low < frequency <= high:
                    self.trie.insert(word)
                    word_count += 1
        print(f"[DEBUG] Built trie using word list of {word_count} words | Difficulty: {difficulty} (Zipf {low} - {high})")

    def is_valid_word(self, word):
        return self.trie.search(word)

    def is_valid_prefix(self, prefix):
        return self.trie.starts_with(prefix)


class WordValidator:
    def __init__(self, dictionary_path='data/enable1.txt'):
        self.trie = _Trie()
        self.__load_dictionary(dictionary_path)

    def __load_dictionary(self, path, profanity_path='data/profanity_wordlist.txt'):
        if not os.path.exists(path):
            print(f"Dictionary not found at {path}.")
            return
        banned = set()
        if os.path.exists(profanity_path):
            with open(profanity_path, 'r') as f:
                for line in f:
                    banned.add(line.strip().lower())
        word_count = 0
        with open(path, 'r') as f:
            for line in f:
                word = line.strip()
                if len(word) >= 3 and word.lower() not in banned and zipf_frequency(word, 'en') > 3.10:
                    self.trie.insert(word)
                    word_count += 1
        print(f"[DEBUG] WordValidator loaded {word_count} words (Zipf > 3.10, profanity filtered)")

    def is_valid_word(self, word):
        return self.trie.search(word)

    def is_valid_prefix(self, prefix):
        return self.trie.starts_with(prefix)

# Shared singleton — accepts any valid English word regardless of difficulty
shared_validator = WordValidator()
