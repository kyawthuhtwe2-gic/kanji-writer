from PySide6.QtCore import QObject, QPointF, Signal

from app.coordinate_mapper import (
    screen_pixels_to_widget,
    touchpad_to_widget,
)
from app.stroke_processor import StrokeProcessor
from app.windows_touchpad import (
    PT_TOUCHPAD,
    WM_POINTERCAPTURECHANGED,
    WM_POINTERDOWN,
    WM_POINTERUP,
    WM_POINTERUPDATE,
    WindowsTouchpad,
)


class TrackpadInputManager(QObject):
    """Accepts PT_TOUCHPAD contacts exclusively; ignores mouse and touch input."""

    status_changed = Signal(str)
    contact_event = Signal(str)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.windows = WindowsTouchpad()
        self.processor = StrokeProcessor()
        self.contacts = set()
        self.active_source = None
        self.cancelled_gesture = False
        self.detected_contact = False
        self.observed_events = set()
        self.status_changed.emit(
            "Waiting for native Windows PT_TOUCHPAD contact events. "
            "Mouse events are disabled."
        )

    def register_raw_input(self, hwnd):
        registered, message = self.windows.register_raw_input(hwnd)
        self.status_changed.emit(message)
        return registered

    def process_native_message(self, message_address):
        try:
            decoded = self.windows.decode_message(message_address)
        except (TypeError, ValueError, OSError) as exc:
            self.status_changed.emit(f"Touchpad input error: {exc}")
            return False
        if decoded is None:
            return False
        if decoded[0] == "raw":
            reports = decoded[1]
            for report in reports:
                self._process_raw_report(report)
            return True
        if decoded[0] == "pointer":
            _, message, pointer_id, screen_x, screen_y = decoded
            point = screen_pixels_to_widget(screen_x, screen_y, self.canvas)
            phase = {
                WM_POINTERDOWN: "down",
                WM_POINTERUPDATE: "move",
                WM_POINTERUP: "up",
            }.get(message)
            if message == WM_POINTERCAPTURECHANGED:
                if self.active_source == "pointer":
                    self._cancel_gesture()
                    self.contacts.clear()
                    self.active_source = None
                    self.contact_event.emit(
                        "Touchpad contact capture changed; stroke cancelled."
                    )
                return True
            if phase:
                self._process_contact(
                    "pointer", phase, pointer_id, QPointF(point), 1
                )
                return True
        return False

    def _process_raw_report(self, report):
        tip = report["tip"]
        confidence = report["confidence"]
        contact_id = (report["device_id"], report["contact_id"])
        if tip and confidence:
            phase = "move" if contact_id in self.contacts else "down"
        elif contact_id in self.contacts:
            phase = "up"
        else:
            return

        point = touchpad_to_widget(
            report["x"],
            report["y"],
            report["x_min"],
            report["x_max"],
            report["y_min"],
            report["y_max"],
            self.canvas,
        )
        self._process_contact(
            "raw",
            phase,
            contact_id,
            QPointF(point),
            report["contact_count"],
        )

    def _process_contact(self, source, phase, contact_id, point, contact_count):
        if self.active_source is not None and self.active_source != source:
            return
        if phase == "down":
            if not self.contacts:
                self.active_source = source
                self.cancelled_gesture = False
            self.contacts.add(contact_id)
            self.observed_events.add("down")
            self.detected_contact = True
            if contact_count > 1 or len(self.contacts) > 1:
                self._cancel_gesture()
                self.cancelled_gesture = True
                self.contact_event.emit(
                    "Multiple touchpad contacts detected — gesture ignored."
                )
            elif not self.cancelled_gesture:
                self.canvas.start_stroke(point)
                self.processor.start(point)
                self.contact_event.emit("Touchpad contact down — stroke started.")
                self.status_changed.emit("Click-free touchpad contact detected.")
            return

        if contact_id not in self.contacts:
            return
        self.detected_contact = True
        if phase == "move":
            self.observed_events.add("move")
            if contact_count > 1 and not self.cancelled_gesture:
                self._cancel_gesture()
                self.cancelled_gesture = True
                self.contact_event.emit(
                    "Multiple touchpad contacts detected — gesture ignored."
                )
            elif not self.cancelled_gesture:
                smooth = self.processor.add(point)
                if smooth is not None:
                    self.canvas.extend_stroke(smooth)
                    self.contact_event.emit("Touchpad contact moved.")
            return

        if phase == "up":
            self.observed_events.add("up")
            if not self.cancelled_gesture:
                self.canvas.finish_stroke()
                self.contact_event.emit("Touchpad contact up — stroke finished.")
            self.contacts.discard(contact_id)
            self.processor.finish()
            if not self.contacts:
                self.cancelled_gesture = False
                self.active_source = None

    def _cancel_gesture(self):
        if self.contacts and not self.cancelled_gesture:
            self.canvas.cancel_current_stroke()
        self.processor.finish()

    def compatibility_message(self):
        if self.observed_events == {"down", "move", "up"}:
            return (
                "Verified: native touchpad contact-down, move, and contact-up "
                "events were received."
            )
        if self.detected_contact:
            missing = ", ".join(sorted({"down", "move", "up"} - self.observed_events))
            return (
                "PT_TOUCHPAD input was detected, but the diagnostic did not observe "
                f"all contact phases (missing: {missing}). Click-free support is not "
                "fully verified."
            )
        return (
            "No native PT_TOUCHPAD contact was received. This touchpad/driver may "
            "expose only pointer or mouse emulation; those events are deliberately "
            "ignored. Click-free writing is unavailable until Raw Input or "
            "PT_TOUCHPAD pointer contact phases are detected."
        )

    def reset_diagnostic(self):
        self.detected_contact = False
        self.observed_events.clear()
        self.status_changed.emit(
            "Test now: glide one finger over the canvas without pressing or clicking."
        )
