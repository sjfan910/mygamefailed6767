import json
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QDialog, QHBoxLayout, QPushButton, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from css.analyticsWindowcss import *
from modules.mergeSort import MergeSort


class _DeleteGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Delete")
        self.setModal(True)
        self.setFixedSize(450, 180)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        question = QLabel("Are you sure you want to delete this game?\nThis action cannot be undone.")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet(dialogQuestionStyle)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(150, 40)
        cancel_btn.setStyleSheet(dialogCancelStyle)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setDefault(True)

        delete_btn = QPushButton("Delete Game")
        delete_btn.setFixedSize(150, 40)
        delete_btn.setStyleSheet(dialogDeleteStyle)
        delete_btn.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        layout.addWidget(question)
        layout.addLayout(button_layout)
        layout.setContentsMargins(30, 20, 30, 20)
        self.setLayout(layout)


class AnalyticsWindow(QWidget):
    def __init__(self, game_data, main_window=None):
        super().__init__()
        self.game_data = game_data
        self.main_window = main_window

        self.missed_words = []
        for word in game_data['all_possible_words']:
            if word not in game_data['found_words']:
                self.missed_words.append(word)

        self.__initUI()


    def __initUI(self):
        self.setWindowTitle('Game Analytics')
        self.setFixedSize(900, 700)
        self.setStyleSheet("background-color: #f5f5f5;")
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()
        main_layout = QVBoxLayout()

        title = QLabel('Post-Game Analytics')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(titleStyle)

        score_text = f"Final Score: {self.game_data['score']}"
        score_label = QLabel(score_text)
        score_label.setAlignment(Qt.AlignCenter)
        score_label.setStyleSheet(scoreStyle)

        stats_layout = QHBoxLayout()
        found_stat = QLabel(f"Words Found:\n{len(self.game_data['found_words'])}")
        found_stat.setAlignment(Qt.AlignCenter)
        found_stat.setStyleSheet(foundStatStyle)

        missed_stat = QLabel(f"Words Missed:\n{len(self.missed_words)}")
        missed_stat.setAlignment(Qt.AlignCenter)
        missed_stat.setStyleSheet(missedStatStyle)
        if self.game_data['all_possible_words']:
            percentage = (len(self.game_data['found_words']) /
                        len(self.game_data['all_possible_words']) * 100)
        else:
            percentage = 0

        percent_stat = QLabel(f"Completion:\n{percentage:.1f}%")
        percent_stat.setAlignment(Qt.AlignCenter)
        percent_stat.setStyleSheet(percentStatStyle)

        stats_layout.addWidget(found_stat)
        stats_layout.addWidget(missed_stat)
        stats_layout.addWidget(percent_stat)

        missed_label = QLabel('Missed Words:')
        missed_label.setStyleSheet(missedLabelStyle)

        if self.missed_words:
            MergeSort.sort(self.missed_words)
            missed_text = ', '.join(word.capitalize() for word in self.missed_words)
        else:
            missed_text = ''
        missed_display = QLabel(missed_text)
        missed_display.setWordWrap(True)
        missed_display.setStyleSheet(missedDisplayStyle)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(missed_display)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)

        button_layout = QHBoxLayout()
        save_btn = QPushButton('Save This Game')
        save_btn.setFixedSize(200, 50)
        save_btn.setStyleSheet(saveButtonStyle)
        save_btn.clicked.connect(self.save_game)

        delete_btn = QPushButton('Delete This Game')
        delete_btn.setFixedSize(200, 50)
        delete_btn.setStyleSheet(deleteButtonStyle)
        delete_btn.clicked.connect(self.delete_game)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(delete_btn)
        main_layout.addWidget(title)
        main_layout.addWidget(self.message_label)
        main_layout.addWidget(score_label)
        main_layout.addLayout(stats_layout)
        main_layout.addWidget(missed_label)
        main_layout.addWidget(scroll_area)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        main_layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(main_layout)

    def __hide_message(self):
        # Called after the message banner has been shown for 1 second
        self.message_label.hide()
        self.setEnabled(True)

    def __show_success_message(self, text):
        self.setEnabled(False)
        self.message_label.setText(text)
        self.message_label.setStyleSheet(successMessageStyle)
        self.message_label.show()
        QTimer.singleShot(1000, self.__hide_message)

    def __show_error_message(self, text):
        self.setEnabled(False)
        self.message_label.setText(text)
        self.message_label.setStyleSheet(errorMessageStyle)
        self.message_label.show()
        QTimer.singleShot(1000, self.__hide_message)

    def save_game(self):
        try:
            self.game_data['timestamp'] = datetime.now().isoformat()

            con = sqlite3.connect('data/game_history.db')

            cur = con.cursor()
            cur.execute("CREATE TABLE if not exists gameHistory(score, grid_size, time_played, ai_helper_uses, difficulty, timer, timestamp)")

            sql = f"""
                        INSERT INTO gameHistory VALUES ({self.game_data['score']}, {self.game_data['grid_size']}, {self.game_data['time_played']}, {self.game_data['ai_helper_uses']}, "{self.game_data['difficulty']}", {self.game_data['timer']}, "{self.game_data['timestamp']}")"""

            cur.execute(sql)
            con.commit()

            try:
                with open('data/game_history.json', 'r') as f:
                    games = json.load(f)
            except Exception:
                games = []

            games.append(self.game_data)
            with open('data/game_history.json', 'w') as f:
                json.dump(games, f, indent=2)

            self.__show_success_message("Game saved successfully!")
            QTimer.singleShot(1000, self.return_to_menu)

        except Exception as e:
            self.__show_error_message(f"Failed to save game: {str(e)}")

    def delete_game(self):
        dialog = _DeleteGameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.__show_success_message("Game deleted!")
            QTimer.singleShot(1000, self.return_to_menu)

    def return_to_menu(self):
        if self.main_window:
            self.hide()
            self.main_window.show()
        else:
            self.close()