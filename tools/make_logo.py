"""Generate assets/logo.png and assets/logo.ico. Replace those files to use a custom logo."""
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def render(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
    r = QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92)
    grad = QLinearGradient(r.topLeft(), r.bottomRight())
    grad.setColorAt(0, QColor("#e5484d"))
    grad.setColorAt(1, QColor("#a8242b"))
    path = QPainterPath()
    path.addRoundedRect(r, size * 0.22, size * 0.22)
    p.fillPath(path, grad)
    font = QFont("Yu Mincho")
    font.setPixelSize(int(size * 0.62))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor("white"))
    p.drawText(r, Qt.AlignCenter, "書")
    p.end()
    return img


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    ASSETS.mkdir(exist_ok=True)
    render(512).save(str(ASSETS / "logo.png"))
    ok = render(256).save(str(ASSETS / "logo.ico"))
    print("png ok, ico", "ok" if ok else "FAILED")
