import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.writing_canvas import WritingCanvas


class TouchpadDiagnostic(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Click-Free Touchpad Compatibility Test")
        self.resize(760, 560)
        layout = QVBoxLayout(self)
        title = QLabel("Windows PT_TOUCHPAD input diagnostic")
        title.setStyleSheet("font-size: 20px; font-weight: 700")
        layout.addWidget(title)
        instructions = QLabel(
            "Press Start test, then glide one finger across the area below and lift. "
            "Do not click, press, or use a mouse. The test only passes when Windows "
            "delivers native PT_TOUCHPAD contact-down, move, and contact-up messages."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.canvas = WritingCanvas()
        self.canvas.trackpad_event.connect(self._event_received)
        self.canvas.trackpad_status_changed.connect(self._status_changed)
        layout.addWidget(self.canvas, 1)
        detected = self.canvas.input_manager.windows.enumerate_touchpads()
        if detected:
            summaries = [
                f"VID {device['vendor_id']:04X}/PID {device['product_id']:04X}, "
                f"{device['report_bytes']}-byte HID reports"
                for device in detected
            ]
            device_text = "HID touchpad collection found: " + "; ".join(summaries)
        else:
            device_text = "No HID Digitizer/Touchpad collection was found."
        self.device_info = QLabel(device_text)
        self.device_info.setWordWrap(True)
        layout.addWidget(self.device_info)
        self.status = QLabel("Waiting for test. Mouse input is ignored.")
        self.status.setWordWrap(True)
        self.status.setStyleSheet(
            "padding: 10px; background: #edf4ff; border-radius: 8px"
        )
        layout.addWidget(self.status)
        button = QPushButton("Start / reset test")
        button.clicked.connect(self._start_test)
        layout.addWidget(button)
        self._start_test()

    def _start_test(self):
        self.canvas.reset_canvas()
        self.canvas.input_manager.reset_diagnostic()
        self.status.setText(
            "TEST RUNNING — glide one finger over the canvas without pressing."
        )
        QTimer.singleShot(10000, self._finish_test)

    def _event_received(self, message):
        self.status.setText(message)

    def _status_changed(self, message):
        self.status.setText(message)

    def _finish_test(self):
        self.status.setText(self.canvas.input_manager.compatibility_message())


def main():
    app = QApplication(sys.argv)
    window = TouchpadDiagnostic()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
