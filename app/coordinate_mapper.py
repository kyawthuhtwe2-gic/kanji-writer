import ctypes
import os
from ctypes import wintypes

from PySide6.QtCore import QPoint


def screen_pixels_to_widget(point_x, point_y, widget):
    """Map GetPointerInfo screen pixels to this Qt widget's logical coordinates."""
    logical_x = point_x
    logical_y = point_y
    if os.name == "nt":
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        get_dpi = getattr(user32, "GetDpiForWindow", None)
        if get_dpi:
            get_dpi.argtypes = [wintypes.HWND]
            get_dpi.restype = wintypes.UINT
            dpi = get_dpi(wintypes.HWND(int(widget.window().winId())))
            if dpi:
                logical_x = round(point_x * 96 / dpi)
                logical_y = round(point_y * 96 / dpi)
    return widget.mapFromGlobal(QPoint(logical_x, logical_y))


def touchpad_to_widget(point_x, point_y, x_min, x_max, y_min, y_max, widget):
    width = max(x_max - x_min, 1)
    height = max(y_max - y_min, 1)
    x = round((point_x - x_min) * max(widget.width() - 1, 0) / width)
    y = round((point_y - y_min) * max(widget.height() - 1, 0) / height)
    return QPoint(
        min(max(x, 0), max(widget.width() - 1, 0)),
        min(max(y, 0), max(widget.height() - 1, 0)),
    )
