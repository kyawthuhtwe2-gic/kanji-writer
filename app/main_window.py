from PySide6.QtCore import Qt, QTimer
from PySide6.QtTextToSpeech import QTextToSpeech
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.japanese_data import PRACTICE_SETS
from app.kanji_recognition import compare_to_target
from app.progress_store import load_state, save_state
from app.stroke_guide import StrokeGuide
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
        saved = load_state(PRACTICE_SETS)
        if saved:
            self.category, self.character_index, self.completed = saved
        self._init_speech()
        self._build_ui()
        self._set_style()
        self.category_select.blockSignals(True)
        self.category_select.setCurrentText(self.category)
        self.category_select.blockSignals(False)
        self._refresh_character()
        self._shortcuts = []
        for keys, action in (
            ((Qt.Key.Key_C,), self._clear),
            ((Qt.Key.Key_U,), self.canvas.undo),
            ((Qt.Key.Key_R,), self.canvas.redo),
            ((Qt.Key.Key_N,), self._next_character),
            ((Qt.Key.Key_S,), self._speak),
            ((Qt.Key.Key_Return, Qt.Key.Key_Enter), self._recognize),
        ):
            for key in keys:
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.activated.connect(action)
                self._shortcuts.append(shortcut)
        self.clear_shortcut = self._shortcuts[0]
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
        tagline = QLabel("Kana & Kanji practice · write with your touchpad")
        tagline.setObjectName("subtitle")
        heading.addWidget(tagline)
        heading.setSpacing(0)
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

        hero = QFrame()
        hero.setObjectName("hero")
        info_row = QHBoxLayout(hero)
        info_row.setContentsMargins(32, 14, 32, 14)
        info_row.setSpacing(32)
        self.target_label = QLabel()
        self.target_label.setObjectName("target")
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.target_label.setMinimumWidth(110)
        info_row.addWidget(self.target_label)
        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.addStretch()
        self.reading_label = QLabel()
        self.reading_label.setObjectName("reading")
        text_col.addWidget(self.reading_label)
        self.meaning_label = QLabel()
        self.meaning_label.setObjectName("subtitle")
        text_col.addWidget(self.meaning_label)
        text_col.addStretch()
        info_row.addLayout(text_col, 1)
        self.sound_button = QPushButton("🔊  Listen  (S)")
        self.sound_button.setObjectName("soft")
        self.sound_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sound_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sound_button.clicked.connect(self._speak)
        self.sound_button.setEnabled(self.speech is not None)
        if self.speech is None:
            self.sound_button.setToolTip("No Japanese text-to-speech voice found")
        self.sound_button.setMinimumWidth(150)
        info_row.addWidget(self.sound_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self._sound_frames = ("🔈", "🔉", "🔊")
        self._sound_frame = 0
        self._sound_timer = QTimer(self)
        self._sound_timer.timeout.connect(self._animate_sound)
        if self.speech is not None:
            self.speech.stateChanged.connect(self._speech_state_changed)
        practice_layout.addWidget(hero)

        canvas_heading = QHBoxLayout()
        canvas_title = QLabel("WRITING CANVAS")
        canvas_title.setObjectName("eyebrow")
        canvas_heading.addWidget(canvas_title)
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
        self.touch_radio = QRadioButton("Touch (no click)")
        self.press_radio = QRadioButton("Press / Mouse")
        self.touch_radio.setChecked(True)
        self.press_radio.toggled.connect(self.canvas.set_press_mode)
        canvas_controls.addWidget(self.touch_radio)
        canvas_controls.addWidget(self.press_radio)
        canvas_controls.addSpacing(16)
        canvas_controls.addWidget(QLabel("Pen"))
        self.pen_slider = QSlider(Qt.Orientation.Horizontal)
        self.pen_slider.setRange(2, 16)
        self.pen_slider.setValue(6)
        self.pen_slider.valueChanged.connect(self.canvas.set_pen_width)
        self.pen_slider.setFixedWidth(140)
        canvas_controls.addWidget(self.pen_slider)
        self.color_button = QPushButton()
        self.color_button.setFixedSize(26, 26)
        self.color_button.setToolTip("Pen color")
        self.color_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.color_button.clicked.connect(self._choose_color)
        self._show_color(QColor("#2563eb"))
        canvas_controls.addWidget(self.color_button)
        self.input_status = QLabel(
            "Move one finger across the canvas without pressing. "
            "Waiting for native touchpad contacts…"
        )
        self.input_status.setObjectName("banner")
        self.input_status.setWordWrap(True)
        canvas_controls.addStretch()
        practice_layout.addLayout(canvas_controls)
        practice_layout.addWidget(self.input_status)

        controls = QHBoxLayout()
        self.check_button = QPushButton("Check writing (Enter)")
        self.check_button.setObjectName("primary")
        self.check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_button.clicked.connect(self._recognize)
        controls.addWidget(self.check_button)
        self._add_button(controls, "Undo (U)", self.canvas.undo)
        self._add_button(controls, "Redo (R)", self.canvas.redo)
        self._add_button(controls, "Clear (C)", self._clear)
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
        self.guide_character = StrokeGuide()
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
        self.progress_bar.setFixedHeight(10)
        side_layout.addWidget(self.progress_bar)
        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("primary")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.clicked.connect(self._next_character)
        side_layout.addWidget(self.next_button)

        side_layout.addStretch()
        body.addWidget(side_panel, 1)

    @staticmethod
    def _add_button(layout, text, callback):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        layout.addWidget(button)

    def _set_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f3f5fb; color: #1b2438; }
            QLabel, QRadioButton { background: transparent; }
            QFrame#panel { background: #ffffff; border: 1px solid #dfe5f0;
                           border-radius: 20px; }
            QFrame#hero { background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 #f4f7ff, stop:1 #eef3ff);
                          border: 1px solid #e1e9fb; border-radius: 16px; }
            QFrame#hero QLabel { background: transparent; }
            QLabel#title { font-size: 26px; font-weight: 800; color: #14213d; }
            QLabel#subtitle { color: #6b778c; font-size: 12px; }
            QLabel#eyebrow { color: #8592a8; font-weight: 700; font-size: 10px;
                             letter-spacing: 1px; }
            QLabel#target { color: #16213a; font-size: 58px; min-height: 70px; }
            QLabel#reading { color: #2f55b8; font-size: 20px; font-weight: 700; }
            QLabel#sectionTitle { color: #19253b; font-size: 14px; font-weight: 700; }
            QLabel#result { color: #55627a; font-size: 12px; }
            QLabel#score { color: #2f55b8; font-size: 30px; font-weight: 800; }
            QLabel#banner { color: #6b778c; background: #f6f8fc; border-radius: 10px;
                            padding: 8px 12px; font-size: 11px; }
            QLabel#hint { color: #7a869b; font-size: 11px; }
            QRadioButton { spacing: 8px; color: #334155; font-weight: 600; }
            QRadioButton::indicator { width: 16px; height: 16px; border-radius: 9px;
                                      border: 2px solid #c3cde0; background: white; }
            QRadioButton::indicator:hover { border-color: #7f9be0; }
            QRadioButton::indicator:checked { border: 2px solid #2f55b8;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5,
                    fy:0.5, stop:0 #2f55b8, stop:0.5 #2f55b8, stop:0.56 white,
                    stop:1 white); }
            QSlider::groove:horizontal { height: 6px; border-radius: 3px;
                                         background: #e3e9f4; }
            QSlider::sub-page:horizontal { background: #6f8fe6; border-radius: 3px; }
            QSlider::handle:horizontal { background: #2f55b8; width: 16px;
                                         height: 16px; margin: -5px 0;
                                         border-radius: 8px; border: 3px solid white; }
            QComboBox { background: white; border: 1px solid #dbe3f0;
                        border-radius: 12px; padding: 8px 14px; min-width: 110px;
                        font-weight: 600; }
            QComboBox:hover { border-color: #9db3ea; }
            QComboBox::drop-down { border: 0; width: 24px; }
            QComboBox QAbstractItemView { background: white; border: 1px solid #dbe3f0;
                                          selection-background-color: #e8eefc;
                                          selection-color: #1b2438; outline: 0; }
            QPushButton { background: #eef2f9; color: #2f3b52; border: 0;
                          border-radius: 12px; padding: 11px 14px; font-weight: 600; }
            QPushButton:hover { background: #e2e9f6; }
            QPushButton:pressed { background: #d6dff1; }
            QPushButton:disabled { color: #a3adbf; background: #f2f4f8; }
            QPushButton#soft { background: #ffffff; color: #2f55b8;
                               border: 1px solid #d5e0fa; }
            QPushButton#soft:hover { background: #f2f6ff; }
            QPushButton#soft[speaking="true"] { background: #e3ebff;
                border: 1px solid #7f9be0; color: #24478e; }
            QPushButton#primary { color: white; background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1, stop:0 #4a74e0, stop:1 #2f55b8); }
            QPushButton#primary:hover { background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1, stop:0 #5a82ea, stop:1 #3a62c9); }
            QPushButton#primary:pressed { background: #274a9e; }
            QProgressBar { background: #e6ecf7; border: 0; border-radius: 5px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #6f8fe6, stop:1 #2f55b8);
                                  border-radius: 5px; }
            QFrame#divider { color: #e9edf4; }
        """)
        self.setFont(QFont("Segoe UI", 10))
        target_font = QFont("Meiryo", 48)
        self.target_label.setFont(target_font)

    def _change_category(self, category):
        if category not in PRACTICE_SETS:
            return
        self.category = category
        self.character_index = 0
        self._refresh_character()
        self._save()

    def _save(self):
        save_state(self.category, self.character_index, self.completed)

    def closeEvent(self, event):
        self._save()
        super().closeEvent(event)

    def _refresh_character(self):
        item = self.current_character
        self.target_label.setText(item.character)
        self.guide_character.set_character(item.character)
        self.reading_label.setText(item.reading)
        self.meaning_label.setText(item.meaning)
        self.meaning_label.setVisible(item.meaning != item.reading)
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
            self._save()
            result = "Good match to the target shape."
        elif score:
            result = "Some shape overlap. Compare with the reference and try again."
        else:
            result = "No writing detected or no supported touchpad contact received."
        self.result_label.setText(
            result + " Comparison is a local shape estimate, not general OCR."
        )
        self._update_progress()

    def _choose_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Pen color")
        if color.isValid():
            self.canvas.set_pen_color(color)
            self._show_color(color)

    def _show_color(self, color):
        self.color_button.setStyleSheet(
            f"QPushButton {{ background: {color.name()}; border: 2px solid #cbd5e1;"
            " border-radius: 13px; padding: 0; min-width: 26px; max-width: 26px;"
            " min-height: 26px; max-height: 26px; }"
            " QPushButton:hover { border-color: #64748b; }"
        )

    def _init_speech(self):
        self.speech = None
        try:
            engine = QTextToSpeech()
            for locale in engine.availableLocales():
                if locale.name().startswith("ja"):
                    engine.setLocale(locale)
                    self.speech = engine
                    break
        except Exception:
            self.speech = None

    def _speak(self):
        if self.speech is None:
            return
        item = self.current_character
        if item.category == "Kanji":
            text = item.reading.replace("・", "、")
        else:
            text = item.character
        self.speech.stop()
        self._start_sound_animation()
        self.speech.say(text)

    def _start_sound_animation(self):
        self._sound_frame = 0
        self.sound_button.setProperty("speaking", True)
        self.sound_button.style().unpolish(self.sound_button)
        self.sound_button.style().polish(self.sound_button)
        self._animate_sound()
        self._sound_timer.start(280)
        # Safety net: never leave the button stuck in the speaking state.
        QTimer.singleShot(8000, self._stop_sound_animation_if_idle)

    def _animate_sound(self):
        frame = self._sound_frames[self._sound_frame % len(self._sound_frames)]
        self._sound_frame += 1
        self.sound_button.setText(f"{frame}  Listen  (S)")

    def _stop_sound_animation(self):
        self._sound_timer.stop()
        self.sound_button.setText("🔊  Listen  (S)")
        self.sound_button.setProperty("speaking", False)
        self.sound_button.style().unpolish(self.sound_button)
        self.sound_button.style().polish(self.sound_button)

    def _stop_sound_animation_if_idle(self):
        if self.speech is None or self.speech.state() != QTextToSpeech.State.Speaking:
            self._stop_sound_animation()

    def _speech_state_changed(self, state):
        if state == QTextToSpeech.State.Ready:
            self._stop_sound_animation()

    def _clear(self):
        self.canvas.clear()
        self.result_label.setText("Canvas cleared.")
        self.score_label.setText("—")

    def _next_character(self):
        self.character_index = (self.character_index + 1) % len(self.characters)
        self._refresh_character()
        self._save()

    def _update_progress(self):
        completed = sum(
            1 for category, _ in self.completed if category == self.category
        )
        total = len(self.characters)
        self.progress_label.setText(f"{completed} of {total} characters")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)


    def _set_input_status(self, message):
        self.input_status.setText(message)

    def _log_input_event(self, message):
        self.input_status.setText(message)

    def _show_compatibility_result(self):
        self.input_status.setText(self.canvas.input_manager.compatibility_message())
