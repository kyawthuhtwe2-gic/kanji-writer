from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from app.trackpad_input import TrackpadInputManager


class WritingCanvas(QWidget):
    stroke_count_changed = Signal(int)
    trackpad_status_changed = Signal(str)
    trackpad_event = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 360)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self.strokes = []
        self._active_stroke = None
        self._undo_stack = []
        self._redo_stack = []
        self.target_character = ""
        self.pen_width = 6
        self.press_mode = False
        self.theme = None
        self.pen_color = QColor("#2563eb")
        self.input_manager = TrackpadInputManager(self)
        self.input_manager.status_changed.connect(self.trackpad_status_changed)
        self.input_manager.contact_event.connect(self.trackpad_event)

    def set_target(self, character):
        self.target_character = character
        self.update()

    def set_press_mode(self, enabled):
        """True: draw by pressing mouse/trackpad button. False: touch-only, no click."""
        self.finish_stroke()
        self.press_mode = enabled

    def set_pen_color(self, color):
        self.pen_color = QColor(color)
        self.update()

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def _c(self, key, default):
        return self.theme[key] if self.theme else default

    def set_pen_width(self, width):
        self.pen_width = width
        self.update()

    def start_stroke(self, point):
        self._snapshot()
        self._active_stroke = [QPointF(point)]
        self.strokes.append(self._active_stroke)
        self.stroke_count_changed.emit(len(self.strokes))
        self.update()

    def extend_stroke(self, point):
        if self._active_stroke is not None:
            self._active_stroke.append(QPointF(point))
            self.update()

    def finish_stroke(self):
        if self._active_stroke is not None:
            self._active_stroke = None
            self.update()

    def cancel_current_stroke(self):
        if self._active_stroke is not None:
            self.strokes.pop()
            self._active_stroke = None
            if self._undo_stack:
                self._undo_stack.pop()
            self.stroke_count_changed.emit(len(self.strokes))
            self.update()

    def _snapshot(self):
        self._undo_stack.append([[QPointF(point) for point in stroke]
                                 for stroke in self.strokes])
        self._redo_stack.clear()

    def nativeEvent(self, event_type, message):
        if not self.press_mode and self.input_manager.process_native_message(message):
            return True, 0
        return super().nativeEvent(event_type, message)

    def showEvent(self, event):
        self.input_manager.register_raw_input(int(self.winId()))
        super().showEvent(event)

    def mousePressEvent(self, event):
        if self.press_mode and event.button() == Qt.MouseButton.LeftButton:
            self.start_stroke(event.position())
        event.accept()

    def mouseMoveEvent(self, event):
        if self.press_mode and event.buttons() & Qt.MouseButton.LeftButton:
            self.extend_stroke(event.position())
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.press_mode:
            self.finish_stroke()
        event.accept()

    def undo(self):
        if self._active_stroke is not None:
            self.finish_stroke()
        if self._undo_stack:
            self._redo_stack.append([[QPointF(point) for point in stroke]
                                     for stroke in self.strokes])
            self.strokes = self._undo_stack.pop()
            self.stroke_count_changed.emit(len(self.strokes))
            self.update()

    def redo(self):
        if self._redo_stack:
            self._undo_stack.append([[QPointF(point) for point in stroke]
                                     for stroke in self.strokes])
            self.strokes = self._redo_stack.pop()
            self.stroke_count_changed.emit(len(self.strokes))
            self.update()

    def clear(self):
        if self.strokes:
            self._snapshot()
            self.strokes = []
            self._active_stroke = None
            self.stroke_count_changed.emit(0)
            self.update()

    def reset_canvas(self):
        self.strokes = []
        self._active_stroke = None
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.stroke_count_changed.emit(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QPainterPath()
        card.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        painter.setClipPath(card)
        painter.fillRect(self.rect(), QColor(self._c("cv_bg", "#fbfcff")))
        painter.setPen(QPen(QColor(self._c("cv_grid", "#edf0f5")), 1))
        spacing = 32
        for x in range(spacing, self.width(), spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(spacing, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)
        painter.setPen(QPen(QColor(self._c("cv_axis", "#e0e5ec")), 1,
                            Qt.PenStyle.DashLine))
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())
        painter.drawLine(0, self.height() // 2, self.width(), self.height() // 2)

        if self.target_character and not self.strokes:
            painter.setPen(QColor(*self._c("cv_ghost", (210, 216, 225, 125))))
            painter.setFont(self.font())
            font = painter.font()
            font.setFamily("Yu Gothic UI")
            font.setPixelSize(min(self.width(), self.height()) // 2)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             self.target_character)

        painter.setPen(QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        for stroke in self.strokes:
            if not stroke:
                continue
            path = QPainterPath(stroke[0])
            for point in stroke[1:]:
                path.lineTo(point)
            if len(stroke) == 1:
                path.lineTo(stroke[0] + QPointF(0.1, 0.1))
            painter.drawPath(path)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(self._c("cv_border", "#e1e7f2")), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        painter.end()
