"""Animated stroke-order guide drawn from KanjiVG paths (CC BY-SA 3.0)."""
import math
import re
from pathlib import Path

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

STROKE_DIR = Path(__file__).resolve().parent.parent / "practice" / "strokes"
_TOKEN = re.compile(r"[MmCcSsLlHhVvZz]|-?\d*\.?\d+(?:e-?\d+)?")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Z": 0}


def parse_path(d):
    """Parse an SVG path (M L H V C S Z, abs/rel) into a QPainterPath."""
    tokens = _TOKEN.findall(d)
    path = QPainterPath()
    cur = QPointF(0, 0)
    start = QPointF(0, 0)
    last_ctrl = None
    i, cmd = 0, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                path.closeSubpath()
                cur = QPointF(start)
                last_ctrl = None
                continue
        up = cmd.upper()
        rel = cmd.islower()
        n = _ARGS[up]
        a = [float(t) for t in tokens[i:i + n]]
        i += n
        ox, oy = (cur.x(), cur.y()) if rel else (0.0, 0.0)
        if up == "M":
            cur = QPointF(a[0] + ox, a[1] + oy)
            start = QPointF(cur)
            path.moveTo(cur)
            cmd = "l" if rel else "L"
            last_ctrl = None
        elif up == "L":
            cur = QPointF(a[0] + ox, a[1] + oy)
            path.lineTo(cur)
            last_ctrl = None
        elif up == "H":
            cur = QPointF(a[0] + (cur.x() if rel else 0), cur.y())
            path.lineTo(cur)
            last_ctrl = None
        elif up == "V":
            cur = QPointF(cur.x(), a[0] + (cur.y() if rel else 0))
            path.lineTo(cur)
            last_ctrl = None
        elif up == "C":
            c1 = QPointF(a[0] + ox, a[1] + oy)
            c2 = QPointF(a[2] + ox, a[3] + oy)
            end = QPointF(a[4] + ox, a[5] + oy)
            path.cubicTo(c1, c2, end)
            last_ctrl, cur = c2, end
        elif up == "S":
            c1 = (QPointF(2 * cur.x() - last_ctrl.x(), 2 * cur.y() - last_ctrl.y())
                  if last_ctrl is not None else QPointF(cur))
            c2 = QPointF(a[0] + ox, a[1] + oy)
            end = QPointF(a[2] + ox, a[3] + oy)
            path.cubicTo(c1, c2, end)
            last_ctrl, cur = c2, end
    return path


def load_strokes(character):
    """Return list of stroke polylines (109x109 KanjiVG space), or []."""
    file = STROKE_DIR / f"{ord(character):05x}.svg"
    if not file.exists():
        return []
    text = file.read_text(encoding="utf-8")
    strokes = []
    for d in re.findall(r'<path[^>]*\sd="([^"]+)"', text):
        path = parse_path(d)
        length = path.length()
        if length <= 0:
            continue
        steps = max(8, int(length / 1.5))
        points = [path.pointAtPercent(k / steps) for k in range(steps + 1)]
        strokes.append(points)
    return strokes


class StrokeGuide(QWidget):
    """Plays the stroke order with numbers and a moving arrowhead, then loops."""

    FRAME_MS = 30
    DRAW_SECONDS = 0.8      # per stroke
    PAUSE_FRAMES = 40       # hold after the last stroke

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(190)
        self.character = ""
        self.theme = None
        self.strokes = []
        self._stroke = 0
        self._progress = 0.0
        self._pause = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def set_theme(self, theme):
        self.theme = theme
        self.update()

    def _c(self, key, default):
        return self.theme[key] if self.theme else default

    def set_character(self, character):
        self.character = character
        self.strokes = load_strokes(character)
        self.replay()

    def replay(self):
        self._stroke, self._progress, self._pause = 0, 0.0, 0
        if self.strokes:
            self._timer.start(self.FRAME_MS)
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        if self._stroke >= len(self.strokes):
            self._pause += 1
            if self._pause > self.PAUSE_FRAMES:
                self._stroke, self._progress, self._pause = 0, 0.0, 0
        else:
            self._progress += self.FRAME_MS / 1000 / self.DRAW_SECONDS
            if self._progress >= 1.0:
                self._stroke += 1
                self._progress = 0.0
        self.update()

    def mousePressEvent(self, event):
        self.replay()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(self._c("cv_border", "#e1e7f2")), 1))
        p.setBrush(QColor(self._c("cv_bg", "#fbfcff")))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        p.setBrush(Qt.BrushStyle.NoBrush)
        side = min(self.width(), self.height())
        scale = side / 109.0
        p.translate((self.width() - side) / 2, (self.height() - side) / 2)
        p.scale(scale, scale)
        if not self.strokes:
            p.resetTransform()
            p.setPen(QColor(self._c("sg_text", "#24395f")))
            font = QFont("Meiryo")
            font.setPixelSize(int(side * 0.7))
            p.setFont(font)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.character)
            return

        p.setPen(QPen(QColor(self._c("sg_axis", "#e3e8f0")), 0.6,
                              Qt.PenStyle.DashLine))
        p.drawLine(QPointF(54.5, 0), QPointF(54.5, 109))
        p.drawLine(QPointF(0, 54.5), QPointF(109, 54.5))

        done_pen = QPen(QColor(self._c("sg_done", "#9aa9c4")), 4.2, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        live_pen = QPen(QColor(self._c("sg_live", "#2563eb")), 4.6, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        number_font = QFont("Segoe UI")
        number_font.setPixelSize(7)
        number_font.setBold(True)

        for index, points in enumerate(self.strokes):
            if index < self._stroke:
                visible = points
            elif index == self._stroke:
                visible = points[:max(2, int(len(points) * self._progress) + 1)]
            else:
                continue
            live = index == self._stroke
            p.setPen(live_pen if live else done_pen)
            p.drawPolyline(QPolygonF(visible))
            if live and len(visible) >= 2:
                self._draw_arrow(p, visible)
            p.setFont(number_font)
            p.setPen(QColor(self._c("sg_mark", "#dc2626")))
            start = points[0]
            p.drawText(QPointF(start.x() - 6, start.y() - 2), str(index + 1))
        p.end()

    def _draw_arrow(self, p, visible):
        tip = visible[-1]
        back = visible[max(0, len(visible) - 5)]
        angle = math.atan2(tip.y() - back.y(), tip.x() - back.x())
        size = 6.0
        left = QPointF(tip.x() - size * math.cos(angle - 0.45),
                       tip.y() - size * math.sin(angle - 0.45))
        right = QPointF(tip.x() - size * math.cos(angle + 0.45),
                        tip.y() - size * math.sin(angle + 0.45))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._c("sg_mark", "#dc2626")))
        p.drawPolygon(QPolygonF([tip, left, right]))
        p.setBrush(Qt.BrushStyle.NoBrush)
