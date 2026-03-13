import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QFrame)
from PyQt5.QtCore import Qt

"""
GameDetailWindow displays detailed breakdown of a single game.
Shows completion percentage, timestamp, and words grouped by length.

Key Features:
- Words grouped by length (3-letter, 4-letter, etc., 7+ for long words)
- Color-coded: Green for found words, Red for missed words
- Green words displayed first, then red words
- Completion percentage shown for each word length category
- Back button returns to GameHistoryWindow
"""


class GameDetailWindow(QWidget):

    def __init__(self, game_data, history_window=None):
        super().__init__()
        self.game_data = game_data
        self.history_window = history_window
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Game Details')
        self.setGeometry(200, 100, 900, 700)
        self.setStyleSheet("background-color: #f0f0f0;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)

        found = len(self.game_data.get('found_words', []))
        total = len(self.game_data.get('all_possible_words', []))
        completion = (found / total * 100) if total > 0 else 0

        completion_label = QLabel(f'Completion: <span style="color: #FF9800;">{completion:.1f}%</span>')
        completion_label.setStyleSheet("""
            font-size: 42px;
            font-weight: bold;
            color: #333;
        """)

        timestamp_str = self.game_data.get('timestamp', '')
        formatted_time = self.format_timestamp(timestamp_str)

        grid_size = self.game_data.get('grid_size', 4)
        difficulty = self.game_data.get('difficulty', 'Unknown')
        timer = self.game_data.get('timer', None)
        if timer is None or timer == 'Unknown':
            # Fallback: show time played in mm:ss format
            time_played = self.game_data.get('time_played', 0)
            minutes = time_played // 60
            seconds = time_played % 60
            timer = f"{minutes}:{seconds:02d} played"

        info_text = f"{formatted_time} • {grid_size}x{grid_size} Grid, {difficulty} mode, {timer}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            font-size: 16px;
            color: #666;
        """)

        top_bar = QHBoxLayout()
        back_btn = QPushButton('Back')
        back_btn.setFixedSize(120, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                border: 2px solid #455A64;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        back_btn.clicked.connect(self.back_to_history)

        top_bar.addStretch()
        top_bar.addWidget(back_btn)

        header_layout.addLayout(top_bar)
        header_layout.addWidget(completion_label)
        header_layout.addWidget(info_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        separator.setFixedHeight(2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        words_layout = QVBoxLayout()
        words_layout.setSpacing(20)

        word_groups = self.group_words_by_length()

        for length in sorted(word_groups.keys()):
            if length >= 7:
                continue  # Handle 7+ separately

            group_widget = self.create_word_group_widget(length, word_groups[length])
            words_layout.addWidget(group_widget)

        if any(l >= 7 for l in word_groups.keys()):
            long_words = {'found': [], 'missed': []}
            for length in [l for l in word_groups.keys() if l >= 7]:
                long_words['found'].extend(word_groups[length]['found'])
                long_words['missed'].extend(word_groups[length]['missed'])

            if long_words['found'] or long_words['missed']:
                group_widget = self.create_word_group_widget('7+', long_words)
                words_layout.addWidget(group_widget)

        words_layout.addStretch()
        scroll_content.setLayout(words_layout)
        scroll.setWidget(scroll_content)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(separator)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def format_timestamp(self, timestamp_str):
        try:
            dt = datetime.fromisoformat(timestamp_str)
            day_name = dt.strftime('%A')
            day = dt.day
            month_name = dt.strftime('%B')
            time = dt.strftime('%H:%M')

            # Add ordinal suffix (st, nd, rd, th)
            if 10 <= day % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

            return f"{day_name} {day}{suffix} {month_name} {time}"
        except:
            return "Unknown date"

    def group_words_by_length(self):
        found_words = set(word.upper() for word in self.game_data.get('found_words', []))
        all_words = set(word.upper() for word in self.game_data.get('all_possible_words', []))
        missed_words = all_words - found_words
        word_groups = {}
        for word in all_words:
            length = len(word)
            if length not in word_groups:
                word_groups[length] = {'found': [], 'missed': []}

            if word in found_words:
                word_groups[length]['found'].append(word)
            else:
                word_groups[length]['missed'].append(word)
        for length in word_groups:
            word_groups[length]['found'].sort()
            word_groups[length]['missed'].sort()
        return word_groups

    def create_word_group_widget(self, length, words_dict):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        found_count = len(words_dict['found'])
        total_count = found_count + len(words_dict['missed'])
        completion = (found_count / total_count * 100) if total_count > 0 else 0

        length_str = f"{length}" if isinstance(length, int) else length
        header = QLabel(f'{length_str} Letter Words <span style="color: #4CAF50;">{completion:.1f}%</span>')
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #555;
        """)
        layout.addWidget(header)

        words_container = QWidget()
        words_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        words_layout = QVBoxLayout()
        words_layout.setSpacing(5)
        all_words = []

        for word in words_dict['found']:
            word_label = QLabel(word.lower())
            word_label.setStyleSheet("""
                font-size: 16px;
                color: #4CAF50;
                font-weight: bold;
                padding: 5px 10px;
            """)
            all_words.append(word_label)

        for word in words_dict['missed']:
            word_label = QLabel(word.lower())
            word_label.setStyleSheet("""
                font-size: 16px;
                color: #f44336;
                padding: 5px 10px;
            """)
            all_words.append(word_label)
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        words_per_row = 8

        for i, word_label in enumerate(all_words):
            row_layout.addWidget(word_label)
            if (i + 1) % words_per_row == 0 and i < len(all_words) - 1:
                row_layout.addStretch()
                words_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                row_layout.setSpacing(10)

        if row_layout.count() > 0:
            row_layout.addStretch()
            words_layout.addLayout(row_layout)

        words_container.setLayout(words_layout)
        layout.addWidget(words_container)
        container.setLayout(layout)
        return container

    def back_to_history(self):
        if self.history_window:
            self.hide()
            self.history_window.show()
        else:
            self.close()