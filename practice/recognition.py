import os

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QFont,
    QFontDatabase,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
)


_IMAGE_SIZE = 320
_GRID_SIZE = 32
_JAPANESE_FONT = None


def _japanese_font():
    global _JAPANESE_FONT
    if _JAPANESE_FONT is None:
        font_path = os.path.join(
            os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "meiryo.ttc"
        )
        if os.path.isfile(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            _JAPANESE_FONT = families[0] if families else "Yu Gothic UI"
        else:
            _JAPANESE_FONT = "Yu Gothic UI"
    return QFont(_JAPANESE_FONT, 170)


def _to_grid(image):
    grid = []
    for row in range(_GRID_SIZE):
        y = int((row + 0.5) * image.height() / _GRID_SIZE)
        grid_row = []
        for column in range(_GRID_SIZE):
            x = int((column + 0.5) * image.width() / _GRID_SIZE)
            grid_row.append(image.pixelColor(x, y).value() > 32)
        grid.append(grid_row)
    return grid


def _render_target(character):
    image = QImage(_IMAGE_SIZE, _IMAGE_SIZE, QImage.Format.Format_Grayscale8)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = _japanese_font()
    metrics = QFontMetricsF(font)
    bounds = metrics.tightBoundingRect(character)
    if bounds.isEmpty():
        painter.end()
        return image
    x = (_IMAGE_SIZE - bounds.width()) / 2 - bounds.left()
    y = (_IMAGE_SIZE - bounds.height()) / 2 - bounds.top()
    painter.setFont(font)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(x, y, character)
    painter.end()
    return image


def _render_strokes(strokes):
    points = [point for stroke in strokes for point in stroke]
    image = QImage(_IMAGE_SIZE, _IMAGE_SIZE, QImage.Format.Format_Grayscale8)
    image.fill(0)
    if not points:
        return image

    left = min(point.x() for point in points)
    top = min(point.y() for point in points)
    right = max(point.x() for point in points)
    bottom = max(point.y() for point in points)
    width = max(right - left, 1.0)
    height = max(bottom - top, 1.0)
    scale = (_IMAGE_SIZE * 0.72) / max(width, height)
    offset_x = (_IMAGE_SIZE - width * scale) / 2
    offset_y = (_IMAGE_SIZE - height * scale) / 2

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(Qt.GlobalColor.white, 16, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    for stroke in strokes:
        if not stroke:
            continue
        path = QPainterPath()
        first = stroke[0]
        path.moveTo((first.x() - left) * scale + offset_x,
                    (first.y() - top) * scale + offset_y)
        for point in stroke[1:]:
            path.lineTo((point.x() - left) * scale + offset_x,
                        (point.y() - top) * scale + offset_y)
        if len(stroke) == 1:
            path.lineTo((first.x() - left) * scale + offset_x + 0.1,
                        (first.y() - top) * scale + offset_y + 0.1)
        painter.drawPath(path)
    painter.end()
    return image


def _dilated_neighborhood(grid, row, column):
    return any(
        grid[y][x]
        for y in range(max(0, row - 1), min(_GRID_SIZE, row + 2))
        for x in range(max(0, column - 1), min(_GRID_SIZE, column + 2))
    )


def shape_similarity(strokes, character):
    """Return a tolerant, target-specific shape overlap estimate from 0 to 100."""
    if not any(strokes):
        return 0
    target = _to_grid(_render_target(character))
    drawing = _to_grid(_render_strokes(strokes))
    target_pixels = [(y, x) for y in range(_GRID_SIZE) for x in range(_GRID_SIZE)
                     if target[y][x]]
    drawing_pixels = [(y, x) for y in range(_GRID_SIZE) for x in range(_GRID_SIZE)
                      if drawing[y][x]]
    if not target_pixels or not drawing_pixels:
        return 0

    target_covered = sum(_dilated_neighborhood(drawing, y, x)
                         for y, x in target_pixels) / len(target_pixels)
    drawing_covered = sum(_dilated_neighborhood(target, y, x)
                          for y, x in drawing_pixels) / len(drawing_pixels)
    return round(200 * target_covered * drawing_covered /
                 (target_covered + drawing_covered), 1)
