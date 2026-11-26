from PySide6.QtCore import Qt, QTimer
from PySide6.QtTextToSpeech import QTextToSpeech
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QKeySequence, QShortcut
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
from app.progress_store import (
    load_settings,
    load_state,
    save_settings,
    save_state,
)
from app.themes import THEMES, build_stylesheet
from app.stroke_guide import StrokeGuide
from app.writing_canvas import WritingCanvas


class ColorDot(QPushButton):
    """Small round color swatch, painted by hand so it is always a true circle."""

    SIZE = 16

    def __init__(self, color):
        super().__init__()
        self.color = QColor(color)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip("Pen color")

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        ring = QColor("#64748b") if self.underMouse() else QColor("#cbd5e1")
        painter.setPen(QPen(ring, 1.5))
        painter.setBrush(self.color)
        painter.drawEllipse(self.rect().adjusted(1, 1, -1, -1))
        painter.end()


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
        self._restore_settings()
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
        header.addSpacing(10)
        header.addWidget(QLabel("THEME"))
        self.theme_select = QComboBox()
        self.theme_select.addItem("Day", "day")
        self.theme_select.addItem("Night", "night")
        self.theme_select.setToolTip("Theme")
        self.theme_select.currentIndexChanged.connect(self._theme_selected)
        header.addWidget(self.theme_select)
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
        self.press_radio.toggled.connect(self._save_settings)
        canvas_controls.addWidget(self.touch_radio)
        canvas_controls.addWidget(self.press_radio)
        canvas_controls.addSpacing(16)
        canvas_controls.addWidget(QLabel("Pen"))
        self.pen_slider = QSlider(Qt.Orientation.Horizontal)
        self.pen_slider.setRange(2, 16)
        self.pen_slider.setValue(6)
        self.pen_slider.valueChanged.connect(self.canvas.set_pen_width)
        self.pen_slider.valueChanged.connect(self._save_settings)
        self.pen_slider.setFixedWidth(140)
        canvas_controls.addWidget(self.pen_slider)
        self.color_button = ColorDot("#2563eb")
        self.color_button.clicked.connect(self._choose_color)
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
        self.next_button = QPushButton("Next (N)")
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
        self.theme = "day"
        self.setFont(QFont("Segoe UI", 10))
        self.target_label.setFont(QFont("Meiryo", 48))
        self._apply_theme(self.theme)

    def _apply_theme(self, name):
        if name not in THEMES:
            name = "day"
        self.theme = name
        self.setStyleSheet(build_stylesheet(name))
        self.canvas.set_theme(THEMES[name])
        self.guide_character.set_theme(THEMES[name])
        self.theme_select.blockSignals(True)
        self.theme_select.setCurrentIndex(self.theme_select.findData(name))
        self.theme_select.blockSignals(False)

    def _theme_selected(self, index):
        self._apply_theme(self.theme_select.itemData(index))
        self._save_settings()

    def _change_category(self, category):
        if category not in PRACTICE_SETS:
            return
        self.category = category
        self.character_index = 0
        self._refresh_character()
        self._save()

    def _restore_settings(self):
        settings = load_settings()
        self._apply_theme(settings.get("theme", "day"))
        width = settings.get("pen_width")
        if isinstance(width, int) and self.pen_slider.minimum() <= width <= self.pen_slider.maximum():
            self.pen_slider.setValue(width)
        color = QColor(str(settings.get("pen_color", "")))
        if color.isValid():
            self.canvas.set_pen_color(color)
            self._show_color(color)
            self._save_settings()
        if settings.get("press_mode") is True:
            self.press_radio.setChecked(True)

    def _save_settings(self, *_):
        save_settings({
            "pen_width": self.pen_slider.value(),
            "pen_color": self.canvas.pen_color.name(),
            "press_mode": self.press_radio.isChecked(),
            "theme": self.theme,
        })

    def _save(self):
        save_state(self.category, self.character_index, self.completed)

    def closeEvent(self, event):
        self._save()
        self._save_settings()
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
        self.color_button.set_color(color)

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
