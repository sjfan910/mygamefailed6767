import sys
from math import floor
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QTimer
from modules.boardGen import BoardGenerator
from modules.validation import shared_validator
from modules.wordFinder import WordFinder
from modules.analyticsWindow import AnalyticsWindow
from modules.aiHelper import AIHelper
from css.boggleGamecss import *


class _TileButton(QPushButton):
    def __init__(self, letter, row, col):
        super().__init__(letter)
        self.row = row
        self.col = col
        self.is_selected = False
        self.is_ai_highlighted = False
        self.setFixedSize(70, 70)
        self._update_style()

    def _update_style(self):
        if self.is_ai_highlighted:
            # AI Helper highlighting
            self.setStyleSheet(aiStyle)
        elif self.is_selected:
            # User selection
            self.setStyleSheet(playerStyle)
        else:
            # Default state
            self.setStyleSheet(defaultStyle)

    def set_selected(self, selected):
        self.is_selected = selected
        self._update_style()

    def set_ai_highlighted(self, highlighted):
        self.is_ai_highlighted = highlighted
        self._update_style()

    def _flash_color(self, color, border_color):
        self.setStyleSheet(flashStyle.format(color=color, border_color=border_color))


class _EndGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("End Game?")
        self.setModal(True)
        self.setFixedSize(400, 200)
        layout = QVBoxLayout()
        question = QLabel("End the current game?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet("font-size: 16px; color: #666; padding: 20px;")
        button_layout = QHBoxLayout()

        no_btn = QPushButton("No, Return")
        no_btn.setStyleSheet(returnConfirm)
        no_btn.clicked.connect(self.reject)

        yes_btn = QPushButton("Yes, End and Exit")
        yes_btn.setStyleSheet(endgameConfirm)
        yes_btn.clicked.connect(self.accept)

        button_layout.addWidget(no_btn)
        button_layout.addWidget(yes_btn)
        layout.addWidget(question)
        layout.addLayout(button_layout)
        self.setLayout(layout)


class BoggleGame(QWidget):
    def __init__(self, config, main_window=None):
        super().__init__()
        self.config = config
        self.config_window = None
        self.main_window = main_window

        # grid_size is stored as e.g. "4x4" — take the number before the 'x'
        self.grid_size = int(config['grid_size'].split('x')[0])
        self.timer_seconds = self.__parse_timer(config['timer'])
        self.difficulty = config['difficulty']
        self.ai_helper_enabled = config['ai_helper'] == 'On'

        self.board_letters = []
        self.tiles = []
        self.selected_path = []
        self.current_word = ""
        self.found_words = []
        self.all_possible_words = []
        self.score = 0
        self.is_dragging = False
        self.ai_helper_uses = 0

        self.ai_cooldown_time = 20
        self.ai_cooldown_remaining = 0
        self.ai_cooldown_timer = None
        self.ai_highlighted_path = []

        self.board_gen = BoardGenerator(self.grid_size, self.difficulty)
        self.validator = shared_validator
        self.word_finder = WordFinder()
        self.ai_helper = AIHelper() if self.ai_helper_enabled else None

        self.__initUI()
        self.__generate_board()
        if self.timer_seconds > 0:
            self.__start_timer()

    def __parse_timer(self, timer_str):
        if timer_str == "Off":
            return 0
        minutes, seconds = timer_str.split(':')
        return int(minutes) * 60 + int(seconds)

    def __initUI(self):
        self.setWindowTitle('Boggle Game')
        self.setGeometry(200, 100, 900, 750)
        self.setStyleSheet("background-color: white;")
        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        self.timer_label = QLabel('Time: --:--')
        self.timer_label.setStyleSheet(timerLabel)

        end_game_btn = QPushButton('End Game')
        end_game_btn.setFixedSize(120, 40)
        end_game_btn.setStyleSheet(endbuttonStyle)
        end_game_btn.clicked.connect(self.__confirm_end_game)

        top_bar.addWidget(self.timer_label)
        top_bar.addStretch()
        top_bar.addWidget(end_game_btn)

        self.score_label = QLabel('Score: 0')
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet(scoreStyle)

        self.word_display = QLabel('')
        self.word_display.setAlignment(Qt.AlignCenter)
        self.word_display.setStyleSheet(wordStyle)

        board_container = QWidget()
        self.board_layout = QGridLayout()
        self.board_layout.setSpacing(25)
        board_container.setLayout(self.board_layout)
        board_container.setMaximumSize(500, 500)

        self.words_label = QLabel('Found Words:')
        self.words_label.setStyleSheet(wordsLabelStyle)
        self.words_display = QLabel('')
        self.words_display.setStyleSheet(foundwordsStyle)
        self.words_display.setWordWrap(True)
        self.words_display.setMaximumHeight(100)

        if self.ai_helper_enabled:
            ai_helper_container = QVBoxLayout()
            ai_helper_container.setAlignment(Qt.AlignCenter)

            self.ai_helper_btn = QPushButton('AI Helper')
            self.ai_helper_btn.setFixedSize(180, 50)
            self.ai_helper_btn.setStyleSheet(aibuttonStyle)
            self.ai_helper_btn.clicked.connect(self.__use_ai_helper)

            self.ai_cooldown_label = QLabel('')
            self.ai_cooldown_label.setAlignment(Qt.AlignCenter)
            self.ai_cooldown_label.setStyleSheet("""
                font-size: 12px;
                color: #666;
                padding: 5px;
            """)

            ai_helper_container.addWidget(self.ai_helper_btn)
            ai_helper_container.addWidget(self.ai_cooldown_label)

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.score_label)
        main_layout.addWidget(self.word_display)
        main_layout.addWidget(board_container, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.words_label)
        main_layout.addWidget(self.words_display)

        if self.ai_helper_enabled:
            main_layout.addLayout(ai_helper_container)

        main_layout.addStretch()
        self.setLayout(main_layout)
        self.setMouseTracking(True)

    def __generate_board(self):
        self.board_letters = self.board_gen.generate()
        self.all_possible_words = self.word_finder.find_all_words(self.board_letters)

        # Clear existing tiles
        for i in reversed(range(self.board_layout.count())):
            self.board_layout.itemAt(i).widget().setParent(None)

        self.tiles = []
        for row in range(self.grid_size):
            tile_row = []
            for col in range(self.grid_size):
                letter = self.board_letters[row][col]
                tile = _TileButton(letter, row, col)
                # Use a helper to capture the correct row/col for each tile
                def make_handler(r, c):
                    return lambda: self.__start_selection(r, c)
                tile.pressed.connect(make_handler(row, col))
                tile.clicked.connect(self.__clear_ai_highlight)
                self.board_layout.addWidget(tile, row, col)
                tile_row.append(tile)
            self.tiles.append(tile_row)

    def __use_ai_helper(self):
        if self.ai_cooldown_remaining > 0:
            return

        self.ai_helper_btn.setEnabled(False)
        self.ai_helper_btn.setText('Searching...')
        QApplication.processEvents()
        found_words_upper = set()
        for w in self.found_words:
            found_words_upper.add(w.upper())
        word, path = self.ai_helper.suggest_word(self.board_letters, found_words_upper)
        self.__handle_ai_suggestion(word, path)

    def __handle_ai_suggestion(self, word, path):
        if word is None:
            QMessageBox.information(self, "No Suggestions", "No valid suggestions found on the board.")
            self.ai_helper_btn.setText('AI Helper')
            self.ai_helper_btn.setEnabled(True)
            return
        self.word_display.setText(f"AI suggests: {word.capitalize()}")
        self.word_display.setStyleSheet(aiFonting)
        self.__animate_ai_path(path)
        self.__start_ai_cooldown()

    def __animate_ai_path(self, path):
        self.ai_highlighted_path = path
        def highlight_tile(index):
            if index < len(path):
                row, col = path[index]
                self.tiles[row][col].set_ai_highlighted(True)
                QTimer.singleShot(300, lambda: highlight_tile(index + 1))
        highlight_tile(0)

    def __clear_ai_highlight(self):
        for row, col in self.ai_highlighted_path:
            if row < len(self.tiles) and col < len(self.tiles[0]):
                self.tiles[row][col].set_ai_highlighted(False)
        self.ai_highlighted_path = []
        if "AI suggests:" in self.word_display.text():
            self.word_display.setText("")
            self.word_display.setStyleSheet(defaultFonting)

    def __start_ai_cooldown(self):
        self.ai_cooldown_remaining = self.ai_cooldown_time
        self.ai_helper_btn.setText('AI Helper')
        self.ai_helper_btn.setEnabled(False)
        self.ai_cooldown_timer = QTimer()
        self.ai_cooldown_timer.timeout.connect(self.__update_ai_cooldown)
        self.ai_cooldown_timer.start(1000)
        self.__update_ai_cooldown()

    def __update_ai_cooldown(self):
        if self.ai_cooldown_remaining > 0:
            self.ai_cooldown_label.setText(f"Cooldown: {self.ai_cooldown_remaining}s")
            self.ai_cooldown_remaining -= 1
        else:
            self.ai_cooldown_label.setText("")
            self.ai_helper_btn.setEnabled(True)
            if self.ai_cooldown_timer:
                self.ai_cooldown_timer.stop()
                self.ai_cooldown_timer = None

    def __confirm_end_game(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.ai_cooldown_timer:
            self.ai_cooldown_timer.stop()
        dialog = _EndGameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.__end_game()
        else:
            if hasattr(self, 'timer') and self.timer_seconds > 0:
                self.timer.start()
            if self.ai_cooldown_timer and self.ai_cooldown_remaining > 0:
                self.ai_cooldown_timer.start()

    def __after_word_feedback(self):
        # Called after the 1-second flash to reset the board back to normal
        self.__reset_all_tiles()
        self.__clear_selection()
        self.setEnabled(True)

    def __submit_word(self):
        if len(self.current_word) < 3:
            self.__clear_selection()
            return

        if self.current_word.upper() in self.found_words:
            self.setEnabled(False)
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    self.tiles[row][col]._flash_color('orange', 'darkorange')
            self.word_display.setText("<b>Word Already Found</b>")
            self.word_display.setStyleSheet(alreadyFound)
            QTimer.singleShot(1000, self.__after_word_feedback)
            return

        elif self.validator.is_valid_word(self.current_word):
            self.found_words.append(self.current_word.upper())
            points = floor((len(self.current_word) - 2) * 1.5)
            self.score += points
            self.score_label.setText(f'Score: {self.score}')
            self.words_display.setText(', '.join(w.capitalize() for w in self.found_words))
            self.setEnabled(False)
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    self.tiles[row][col]._flash_color('green', 'darkgreen')
            self.word_display.setText(f"<b>+{points}</b>")
            self.word_display.setStyleSheet(validWord)
            QTimer.singleShot(1000, self.__after_word_feedback)

        else:
            self.setEnabled(False)
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    self.tiles[row][col]._flash_color('red', 'darkred')
            self.word_display.setText(f"<b>{self.current_word.capitalize()} is not valid</b>")
            self.word_display.setStyleSheet(invalidWord)
            QTimer.singleShot(1000, self.__after_word_feedback)

    def __start_selection(self, row, col):
        self.__clear_selection()
        self.__clear_ai_highlight()
        self.is_dragging = True
        self.__add_to_selection(row, col)

    def __add_to_selection(self, row, col):
        if (row, col) in self.selected_path:
            return
        if self.selected_path and not self.__is_adjacent(row, col):
            return
        self.selected_path.append((row, col))
        self.tiles[row][col].set_selected(True)
        self.current_word += self.board_letters[row][col]
        self.word_display.setText(self.current_word.capitalize())

    def __is_adjacent(self, row, col):
        if not self.selected_path:
            return True
        last_row, last_col = self.selected_path[-1]
        return abs(row - last_row) <= 1 and abs(col - last_col) <= 1

    def mouseMoveEvent(self, event):
        if not self.is_dragging:
            return
        pos = event.pos()
        widget = self.childAt(pos)
        if isinstance(widget, _TileButton):
            self.__add_to_selection(widget.row, widget.col)

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.__submit_word()

    def __clear_selection(self):
        for row, col in self.selected_path:
            self.tiles[row][col].set_selected(False)
        self.selected_path = []
        self.current_word = ""
        if "AI suggests:" not in self.word_display.text():
            self.word_display.setText("")
            self.word_display.setStyleSheet(wordStyle)

    def __reset_all_tiles(self):
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                tile = self.tiles[row][col]
                tile.is_selected = False
                tile.is_ai_highlighted = False
                tile._update_style()

    def __start_timer(self):
        self.time_left = self.timer_seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.__update_timer)
        self.timer.start(1000)
        self.__update_timer()

    def __update_timer(self):
        if self.time_left <= 0:
            self.timer.stop()
            self.__end_game()
            return
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f'Time: {minutes:02d}:{seconds:02d}')
        self.time_left -= 1

    def __end_game(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.ai_cooldown_timer:
            self.ai_cooldown_timer.stop()
        game_data = {
            'score': self.score,
            'found_words': self.found_words,
            'all_possible_words': self.all_possible_words,
            'board': self.board_letters,
            'grid_size': self.grid_size,
            'time_played': self.timer_seconds - (self.time_left if hasattr(self, 'time_left') else 0),
            'ai_helper_uses': self.ai_helper_uses,
            'difficulty': self.difficulty,
            'timer': self.timer_seconds
        }
        self.hide()
        self.analytics = AnalyticsWindow(game_data, self.main_window)
        self.analytics.show()
