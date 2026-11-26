from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.japanese_data import PRACTICE_SETS
from app.kanji_recognition import compare_to_target
from app.writing_canvas import WritingCanvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kana & Kanji — Click-Free Practice")
        self.resize(1180, 800)
        self.setMinimumSize(980, 710)
        self.category = "Hiragana"
        self.character_index = 0
        self.completed = set()
        self._build_ui()
        self._set_style()
        self._refresh_character()
        self.clear_shortcut = QShortcut(QKeySequence(Qt.Key.Key_C), self)
        self.clear_shortcut.activated.connect(self._clear)
        QTimer.singleShot(10000, self._show_compatibility_result)

    @property
    def characters(self):
        return PRACTICE_SETS[self.category]

    @property
    def current_character(self):
        return self.characters[self.character_index]

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(16)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Japanese handwriting")
        title.setObjectName("title")
        heading.addWidget(title)
        header.addLayout(heading)
        header.addStretch()
        header.addWidget(QLabel("PRACTICE"))
        self.category_select = QComboBox()
        self.category_select.addItems(PRACTICE_SETS.keys())
        self.category_select.currentTextChanged.connect(self._change_category)
        header.addWidget(self.category_select)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        practice_panel = QFrame()
        practice_panel.setObjectName("panel")
        practice_layout = QVBoxLayout(practice_panel)
        practice_layout.setContentsMargins(20, 18, 20, 18)
        practice_layout.setSpacing(12)

        target_row = QHBoxLayout()
        target_heading = QLabel("TARGET CHARACTER")
        target_heading.setObjectName("eyebrow")
        target_row.addWidget(target_heading)
        target_row.addStretch()
        self.sequence_label = QLabel()
        self.sequence_label.setObjectName("subtitle")
        target_row.addWidget(self.sequence_label)
        practice_layout.addLayout(target_row)

        self.target_label = QLabel()
        self.target_label.setObjectName("target")
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        practice_layout.addWidget(self.target_label)
        self.reading_label = QLabel()
        self.reading_label.setObjectName("reading")
        self.reading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        practice_layout.addWidget(self.reading_label)
        self.meaning_label = QLabel()
        self.meaning_label.setObjectName("subtitle")
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        practice_layout.addWidget(self.meaning_label)

        canvas_heading = QHBoxLayout()
        canvas_heading.addWidget(QLabel("WRITING CANVAS"))
        canvas_heading.addStretch()
        self.stroke_label = QLabel()
        self.stroke_label.setObjectName("subtitle")
        canvas_heading.addWidget(self.stroke_label)
        practice_layout.addLayout(canvas_heading)

        self.canvas = WritingCanvas()
        self.canvas.stroke_count_changed.connect(self._update_stroke_guide)
        self.canvas.trackpad_status_changed.connect(self._set_input_status)
        self.canvas.trackpad_event.connect(self._log_input_event)
        practice_layout.addWidget(self.canvas, 1)

        canvas_controls = QHBoxLayout()
        canvas_controls.addWidget(QLabel("Pen"))
        self.pen_slider = QSlider(Qt.Orientation.Horizontal)
        self.pen_slider.setRange(2, 16)
        self.pen_slider.setValue(6)
        self.pen_slider.valueChanged.connect(self.canvas.set_pen_width)
        canvas_controls.addWidget(self.pen_slider)
        self.input_status = QLabel(
            "Move one finger across the canvas without pressing. "
            "Waiting for native touchpad contacts…"
        )
        self.input_status.setObjectName("hint")
        self.input_status.setWordWrap(True)
        canvas_controls.addWidget(self.input_status, 3)
        practice_layout.addLayout(canvas_controls)

        controls = QHBoxLayout()
        self.check_button = QPushButton("Check writing")
        self.check_button.setObjectName("primary")
        self.check_button.clicked.connect(self._recognize)
        controls.addWidget(self.check_button)
        self._add_button(controls, "Undo", self.canvas.undo)
        self._add_button(controls, "Redo", self.canvas.redo)
        self._add_button(controls, "Clear", self._clear)
        practice_layout.addLayout(controls)
        body.addWidget(practice_panel, 3)

        side_panel = QFrame()
        side_panel.setObjectName("panel")
        side_panel.setMinimumWidth(250)
        side_panel.setMaximumWidth(320)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(18, 18, 18, 18)
        side_layout.setSpacing(11)

        guide_heading = QLabel("Stroke-order reference")
        guide_heading.setObjectName("sectionTitle")
        side_layout.addWidget(guide_heading)
        self.guide_character = QLabel()
        self.guide_character.setObjectName("guideCharacter")
        self.guide_character.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.guide_character)
        self.guide_step = QLabel()
        self.guide_step.setObjectName("reading")
        self.guide_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.guide_step)
        self.guide_detail = QLabel(
            "Use the reference glyph and follow standard Japanese stroke direction."
        )
        self.guide_detail.setObjectName("hint")
        self.guide_detail.setWordWrap(True)
        side_layout.addWidget(self.guide_detail)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        side_layout.addWidget(divider)
        recognition_heading = QLabel("Target comparison")
        recognition_heading.setObjectName("sectionTitle")
        side_layout.addWidget(recognition_heading)
        self.result_label = QLabel("Write the target, then check your shape.")
        self.result_label.setObjectName("result")
        self.result_label.setWordWrap(True)
        side_layout.addWidget(self.result_label)
        self.score_label = QLabel("—")
        self.score_label.setObjectName("score")
        side_layout.addWidget(self.score_label)

        progress_heading = QLabel("Practice progress")
        progress_heading.setObjectName("sectionTitle")
        side_layout.addWidget(progress_heading)
        self.progress_label = QLabel()
        self.progress_label.setObjectName("subtitle")
        side_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        side_layout.addWidget(self.progress_bar)
        self.next_button = QPushButton("Next character  →")
        self.next_button.setObjectName("primary")
        self.next_button.clicked.connect(self._next_character)
        side_layout.addWidget(self.next_button)
        self.reset_button = QPushButton("Reset progress")
        self.reset_button.clicked.connect(self._reset)
        side_layout.addWidget(self.reset_button)

        history_heading = QLabel("Recent practice")
        history_heading.setObjectName("sectionTitle")
        side_layout.addWidget(history_heading)
        self.history = QListWidget()
        self.history.setMaximumHeight(120)
        side_layout.addWidget(self.history)
        side_layout.addStretch()
        body.addWidget(side_panel, 1)

    @staticmethod
    def _add_button(layout, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def _set_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f7fb; color: #172033; }
            QFrame#panel { background: #fff; border: 1px solid #e4e9f1;
                           border-radius: 16px; }
            QLabel#title { font-size: 25px; font-weight: 700; color: #14213d; }
            QLabel#subtitle, QLabel#hint { color: #68758a; }
            QLabel#subtitle { font-size: 12px; }
            QLabel#hint { font-size: 11px; }
            QLabel#eyebrow { color: #758197; font-weight: 700; font-size: 10px; }
            QLabel#target { color: #172033; font-size: 58px; min-height: 65px; }
            QLabel#reading { color: #3156a4; font-size: 15px; font-weight: 600; }
            QLabel#sectionTitle { color: #19253b; font-size: 14px; font-weight: 700; }
            QLabel#guideCharacter { color: #24395f; font-size: 78px; min-height: 100px; }
            QLabel#result { color: #536176; font-size: 12px; }
            QLabel#score { color: #3156a4; font-size: 27px; font-weight: 700; }
            QLabel#modeBadge { color: #2563eb; background: #edf4ff;
                               border-radius: 8px; padding: 8px; font-weight: 700;
                               font-size: 10px; }
            QComboBox { background: white; border: 1px solid #dce3ed;
                        border-radius: 8px; padding: 8px 10px; }
            QPushButton { background: #f2f5fa; color: #334155; border: 0;
                          border-radius: 8px; padding: 9px 11px; font-weight: 600; }
            QPushButton:hover { background: #e7edf6; }
            QPushButton#primary { background: #3156a4; color: white; }
            QPushButton#primary:hover { background: #24478e; }
            QProgressBar { background: #e9eef6; border: 0; border-radius: 4px; }
            QProgressBar::chunk { background: #4f78d1; border-radius: 4px; }
            QFrame#divider { color: #e7ebf1; }
            QListWidget { background: #f9fafc; border: 1px solid #e9edf3;
                          border-radius: 8px; }
        """)
        self.setFont(QFont("Segoe UI", 10))
        target_font = QFont("Meiryo", 48)
        guide_font = QFont("Meiryo", 64)
        self.target_label.setFont(target_font)
        self.guide_character.setFont(guide_font)

    def _change_category(self, category):
        if category not in PRACTICE_SETS:
            return
        self.category = category
        self.character_index = 0
        self._refresh_character()

    def _refresh_character(self):
        item = self.current_character
        self.target_label.setText(item.character)
        self.guide_character.setText(item.character)
        self.reading_label.setText(item.reading)
        details = item.meaning
        if item.jlpt:
            details = f"{details}   ·   {item.jlpt}"
        self.meaning_label.setText(details)
        self.sequence_label.setText(
            f"{self.character_index + 1} / {len(self.characters)}"
        )
        self.canvas.reset_canvas()
        self.canvas.set_target(item.character)
        self.result_label.setText("Write the target, then check your shape.")
        self.score_label.setText("—")
        self._update_stroke_guide(0)
        self._update_progress()

    def _update_stroke_guide(self, count):
        expected = self.current_character.strokes
        self.stroke_label.setText(f"{count} strokes · {expected} expected")
        self.guide_step.setText(f"Stroke {min(count + 1, expected)} of {expected}")
        if count >= expected:
            self.guide_detail.setText(
                f"All {expected} strokes are down. Compare the complete shape with "
                "the reference character."
            )
        else:
            self.guide_detail.setText(
                f"Next: stroke {min(count + 1, expected)} of {expected}. "
                "Follow the reference in standard Japanese order."
            )

    def _recognize(self):
        score = compare_to_target(
            self.canvas.strokes, self.current_character.character
        )
        self.score_label.setText(f"{score:.0f}%")
        key = (self.category, self.character_index)
        if score >= 35:
            self.completed.add(key)
            result = "Good match to the target shape."
        elif score:
            result = "Some shape overlap. Compare with the reference and try again."
        else:
            result = "No writing detected or no supported touchpad contact received."
        self.result_label.setText(
            result + " Comparison is a local shape estimate, not general OCR."
        )
        self.history.insertItem(
            0, f"{self.current_character.character}  ·  {score:.0f}%"
        )
        while self.history.count() > 5:
            self.history.takeItem(self.history.count() - 1)
        self._update_progress()

    def _clear(self):
        self.canvas.clear()
        self.result_label.setText("Canvas cleared.")
        self.score_label.setText("—")

    def _next_character(self):
        self.character_index = (self.character_index + 1) % len(self.characters)
        self._refresh_character()

    def _update_progress(self):
        completed = sum(
            1 for category, _ in self.completed if category == self.category
        )
        total = len(self.characters)
        self.progress_label.setText(f"{completed} of {total} characters")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)

    def _reset(self):
        answer = QMessageBox.question(
            self,
            "Reset practice",
            "Clear progress and return to the first character?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.completed.clear()
            self.history.clear()
            self.character_index = 0
            self._refresh_character()

    def _set_input_status(self, message):
        self.input_status.setText(message)

    def _log_input_event(self, message):
        self.input_status.setText(message)

    def _show_compatibility_result(self):
        self.input_status.setText(self.canvas.input_manager.compatibility_message())
