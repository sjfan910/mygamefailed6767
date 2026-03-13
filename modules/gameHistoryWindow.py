import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QtWarningMsg

"""
GameHistoryWindow displays a scrollable list of all previously played games.
Each game is shown as a clickable block with summary information.

Key Features:
- Loads game data from data/game_history.json
- Displays games in reverse chronological order (most recent first)
- Each game block shows: completion %, timestamp, game settings
- Click any block to view detailed breakdown
- Delete button on each block to remove individual games
- Back button returns to main menu
"""


class GameBlock(QFrame):
    def __init__(self, game_data, index, parent_window):
        super().__init__()
        self.game_data = game_data
        self.index = index
        self.parent_window = parent_window
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.PointingHandCursor)
        self.initUI()

    def initUI(self):
        self.setFixedHeight(100)
        self.setStyleSheet("""
            GameBlock {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 15px;
                padding: 10px;
            }
            GameBlock:hover {
                border: 2px solid #4CAF50;
                background-color: #f9f9f9;
            }
        """)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        found = len(self.game_data.get('found_words', []))
        total = len(self.game_data.get('all_possible_words', []))
        completion = (found / total * 100) if total > 0 else 0

        completion_badge = QLabel(f"{completion:.1f}%")
        completion_badge.setFixedSize(80, 60)
        completion_badge.setAlignment(Qt.AlignCenter)
        completion_badge.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
            }
        """)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        timestamp_str = self.game_data.get('timestamp', '')
        formatted_time = self.format_timestamp(timestamp_str)

        timestamp_label = QLabel(formatted_time)
        timestamp_label.setStyleSheet("""
            font-size: 14px;
            color: #666;
        """)

        grid_size = self.game_data.get('grid_size', 4)
        difficulty = self.game_data.get('difficulty', 'Unknown')
        timer = self.game_data.get('timer', None)

        if timer is None or timer == 'Unknown':
            # Fallback: show time played in mm:ss format
            time_played = self.game_data.get('time_played', 0)
            minutes = time_played // 60
            seconds = time_played % 60
            timer = f"{minutes}:{seconds:02d} played"

        settings_text = f"{grid_size}x{grid_size} Grid, {difficulty} mode, {timer}"
        settings_label = QLabel(settings_text)
        settings_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
        """)

        info_layout.addWidget(timestamp_label)
        info_layout.addWidget(settings_label)
        info_layout.addStretch()

        delete_btn = QPushButton('🗑️')
        delete_btn.setFixedSize(40, 40)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 20px;
                border-radius: 20px;
                border: 2px solid #d32f2f;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(self.delete_game)

        main_layout.addWidget(completion_badge)
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        main_layout.addWidget(delete_btn)

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.open_game_detail(self.game_data, self.index)

    def delete_game(self):
        self.parent_window.delete_game_at_index(self.index)


class GameHistoryWindow(QWidget):
    def __init__(self, main_menu=None):
        super().__init__()
        self.main_menu = main_menu
        self.game_history = []
        self.history_file = 'data/game_history.json'
        self.load_history()
        self.initUI()

    def load_history(self):
        if not os.path.exists(self.history_file):
            self.game_history = []
            return

        try:
            with open(self.history_file, 'r') as f:
                self.game_history = json.load(f)
                self.game_history.reverse()
        except Exception as e:
            QMessageBox.warning(self, "Error loading history: {e}")
            self.game_history = []

    def initUI(self):
        self.setWindowTitle('Game History')
        self.setGeometry(200, 100, 900, 700)
        self.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        header_layout = QHBoxLayout()

        title = QLabel('Game History')
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #333;
        """)

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
        back_btn.clicked.connect(self.back_to_menu)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        self.games_layout = QVBoxLayout()
        self.games_layout.setSpacing(15)

        if len(self.game_history) == 0:
            empty_label = QLabel('No games played yet.\nStart playing to build your history!')
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                font-size: 24px;
                color: #999;
                padding: 100px;
            """)
            self.games_layout.addWidget(empty_label)
        else:
            for i, game_data in enumerate(self.game_history):
                game_block = GameBlock(game_data, i, self)
                self.games_layout.addWidget(game_block)

        self.games_layout.addStretch()
        scroll_content.setLayout(self.games_layout)
        scroll.setWidget(scroll_content)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def delete_game_at_index(self, index):
        actual_index = len(self.game_history) - 1 - index
        try:
            with open(self.history_file, 'r') as f:
                original_history = json.load(f)
            del original_history[actual_index]
            with open(self.history_file, 'w') as f:
                json.dump(original_history, f, indent=2)
            self.load_history()
            self.refresh_display()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete game: {e}")

    def refresh_display(self):
        while self.games_layout.count():
            child = self.games_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if len(self.game_history) == 0:
            empty_label = QLabel('No games played yet.\nStart playing to build your history!')
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                font-size: 24px;
                color: #999;
                padding: 100px;
            """)
            self.games_layout.addWidget(empty_label)
        else:
            for i, game_data in enumerate(self.game_history):
                game_block = GameBlock(game_data, i, self)
                self.games_layout.addWidget(game_block)
        self.games_layout.addStretch()

    def open_game_detail(self, game_data, index):
        from modules.gameDetailWindow import GameDetailWindow
        self.hide()
        self.detail_window = GameDetailWindow(game_data, self)
        self.detail_window.show()

    def back_to_menu(self):
        if self.main_menu:
            self.hide()
            self.main_menu.show()
        else:
            self.close()