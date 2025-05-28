import sys
import random
import csv
import os
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QSizePolicy, QGroupBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtGui import QFont


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


CSV_FILE = resource_path("reactions.csv")
HIGH_SCORE_FILE = resource_path("high_score.txt")
SCORE_HISTORY_FILE = resource_path("score_history.csv")


class ReactionGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Reaction Quiz Game")
        self.setGeometry(100, 100, 1300, 750)

        self.reactions = self.load_reactions()
        self.current_reaction = None
        self.score = 0
        self.high_score = self.load_high_score()
        self.timer = QTimer()
        self.time_left = 60

        self.correct_sound = QSoundEffect()
        self.correct_sound.setSource(QUrl.fromLocalFile(resource_path("complete.oga")))

        self.wrong_sound = QSoundEffect()
        self.wrong_sound.setSource(QUrl.fromLocalFile(resource_path("dialog-warning.oga")))

        self.init_ui()
        self.next_question()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout()
        self.central_widget.setLayout(main_layout)

        quiz_widget = QWidget()
        quiz_widget.setMinimumWidth(450)
        quiz_layout = QVBoxLayout()
        quiz_widget.setLayout(quiz_layout)
        quiz_widget.setStyleSheet("background-color: #f4f4f4; padding: 20px;")

        title_label = QLabel("\U0001F9EA Chemical Reaction Challenge")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        quiz_layout.addWidget(title_label)

        self.reaction_label = QLabel("Element A + Element B = ?")
        self.reaction_label.setAlignment(Qt.AlignCenter)
        self.reaction_label.setFont(QFont("Arial", 16))

        reaction_row = QHBoxLayout()
        reaction_row.addWidget(self.reaction_label)

        help_btn = QPushButton("\u2753")
        help_btn.setFixedWidth(30)
        help_btn.setToolTip("Show Reaction Details")
        help_btn.clicked.connect(self.show_equation_dialog)
        reaction_row.addWidget(help_btn)
        quiz_layout.addLayout(reaction_row)

        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setFont(QFont("Arial", 12, QFont.StyleItalic))
        self.details_label.setWordWrap(True)
        quiz_layout.addWidget(self.details_label)

        copy_btn = QPushButton("\u2398 Copy Details")
        copy_btn.clicked.connect(self.copy_details_to_clipboard)
        quiz_layout.addWidget(copy_btn)

        input_box = QGroupBox("Enter Your Answers")
        input_layout = QVBoxLayout()

        self.products_input = QLineEdit()
        self.products_input.setPlaceholderText("Products")
        input_layout.addWidget(self.products_input)

        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Reaction Type")
        input_layout.addWidget(self.type_input)

        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Conditions")
        input_layout.addWidget(self.condition_input)

        input_box.setLayout(input_layout)
        quiz_layout.addWidget(input_box)

        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("\u2705 Submit")
        self.submit_btn.clicked.connect(self.check_answer)
        self.next_btn = QPushButton("\u27A1\uFE0F Next")
        self.next_btn.clicked.connect(self.next_question)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.next_btn)
        quiz_layout.addLayout(btn_layout)

        self.hint_btn = QPushButton("\U0001F4A1 Show Hint")
        self.hint_btn.clicked.connect(self.show_hint)
        quiz_layout.addWidget(self.hint_btn)

        self.score_label = QLabel(f"Score: {self.score} | High Score: {self.high_score}")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setFont(QFont("Arial", 14))
        quiz_layout.addWidget(self.score_label)

        self.timer_label = QLabel("Time Left: 60s")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 12))
        quiz_layout.addWidget(self.timer_label)

        quiz_layout.addStretch()

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://graphoverflow.com/graphs/3d-periodic-table.html"))
        self.browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.browser.setStyleSheet("border: 2px solid #ccc;")

        main_layout.addWidget(quiz_widget, 1)
        main_layout.addWidget(self.browser, 2)

        self.timer.timeout.connect(self.update_timer)

    def load_reactions(self):
        if not os.path.exists(CSV_FILE):
            QMessageBox.critical(self, "Error", f"CSV file '{CSV_FILE}' not found.")
            sys.exit()

        with open(CSV_FILE, newline='') as csvfile:
            return list(csv.DictReader(csvfile))

    def load_high_score(self):
        return int(open(HIGH_SCORE_FILE).read()) if os.path.exists(HIGH_SCORE_FILE) else 0

    def save_high_score(self):
        with open(HIGH_SCORE_FILE, 'w') as f:
            f.write(str(self.high_score))

    def log_score(self, correct_count):
        with open(SCORE_HISTORY_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if os.stat(SCORE_HISTORY_FILE).st_size == 0:
                writer.writerow(["Timestamp", "Score", "Correct Fields"])
            writer.writerow([datetime.datetime.now().isoformat(), self.score, correct_count])

    def next_question(self):
        self.current_reaction = random.choice(self.reactions)
        self.reaction_label.setText(f"{self.current_reaction['Element A']} + {self.current_reaction['Element B']} = ?")
        self.details_label.setText("")
        self.products_input.clear()
        self.type_input.clear()
        self.condition_input.clear()
        self.time_left = 60
        self.timer_label.setText("Time Left: 60s")
        self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(f"Time Left: {self.time_left}s")
        if self.time_left <= 0:
            self.timer.stop()
            self.score = 0
            self.score_label.setText(f"Score: {self.score} | High Score: {self.high_score}")
            self.next_question()

    def show_hint(self):
        notes = self.current_reaction.get("Notes", "No hints available.")
        QMessageBox.information(self, "Hint", notes)

    def show_equation_dialog(self):
        equation = self.current_reaction.get("Reaction Equation", "")
        typ = self.current_reaction.get("Reaction Type", "")
        cond = self.current_reaction.get("Conditions", "")
        notes = self.current_reaction.get("Notes", "No additional notes.")

        details_text = (f"<b>Reaction Equation:</b> {equation}<br>"
                        f"<b>Reaction Type:</b> {typ}<br>"
                        f"<b>Conditions:</b> {cond}<br>"
                        f"<b>Notes:</b> {notes}")
        self.details_label.setText(details_text)

    def copy_details_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.details_label.text().replace("<br>", "\n").replace("<b>", "").replace("</b>", ""))
        QMessageBox.information(self, "Copied", "Reaction details copied to clipboard.")

    def check_answer(self):
        self.timer.stop()
        products = self.products_input.text().strip().lower()
        typ = self.type_input.text().strip().lower()
        cond = self.condition_input.text().strip().lower()

        correct_products = self.current_reaction["Products"].strip().lower()
        correct_type = self.current_reaction["Reaction Type"].strip().lower()
        correct_cond = self.current_reaction["Conditions"].strip().lower()

        correct_count = sum([
            products == correct_products,
            typ == correct_type,
            cond == correct_cond
        ])

        points = [0, 10, 20, 30][correct_count]
        if points > 0:
            self.correct_sound.play()
            self.score += points
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            QMessageBox.information(self, "Result", f"Correct Fields: {correct_count}\nPoints Earned: {points}")
        else:
            self.wrong_sound.play()
            QMessageBox.warning(self, "Incorrect",
                                f"Correct Answer:\nProducts: {correct_products}\n"
                                f"Type: {correct_type}\nConditions: {correct_cond}")
            self.score = 0

        self.log_score(correct_count)
        self.score_label.setText(f"Score: {self.score} | High Score: {self.high_score}")
        self.next_question()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = ReactionGame()
    game.show()
    sys.exit(app.exec_())
