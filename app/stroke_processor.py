from PySide6.QtCore import QPointF


class StrokeProcessor:
    def __init__(self, smoothing_window=3, minimum_distance=1.5):
        self.smoothing_window = smoothing_window
        self.minimum_distance = minimum_distance
        self._recent = []
        self._last_output = None

    def start(self, point):
        self._recent = [QPointF(point)]
        self._last_output = QPointF(point)
        return QPointF(point)

    def add(self, point):
        point = QPointF(point)
        if self._last_output is not None:
            dx = point.x() - self._last_output.x()
            dy = point.y() - self._last_output.y()
            if (dx * dx + dy * dy) ** 0.5 < self.minimum_distance:
                return None
        self._recent.append(point)
        self._recent = self._recent[-self.smoothing_window:]
        smooth = QPointF(
            sum(item.x() for item in self._recent) / len(self._recent),
            sum(item.y() for item in self._recent) / len(self._recent),
        )
        self._last_output = smooth
        return smooth

    def finish(self):
        self._recent = []
        self._last_output = None
