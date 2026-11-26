import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.trackpad_input import TrackpadInputManager
from app.main_window import MainWindow
from app.windows_touchpad import WM_POINTERDOWN, WM_POINTERUP, WM_POINTERUPDATE
from app.writing_canvas import WritingCanvas
from practice.character_data import PRACTICE_SETS
from practice.recognition import shape_similarity


class PracticeDataTests(unittest.TestCase):
    def test_all_practice_sets_have_japanese_characters_and_stroke_counts(self):
        self.assertEqual(set(PRACTICE_SETS), {"Hiragana", "Katakana", "Kanji"})
        self.assertEqual(len(PRACTICE_SETS["Hiragana"]), 46)
        self.assertEqual(len(PRACTICE_SETS["Katakana"]), 46)
        for items in PRACTICE_SETS.values():
            self.assertTrue(all(item.character and item.strokes > 0 for item in items))


class RecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_writing_has_zero_similarity(self):
        self.assertEqual(shape_similarity([], "あ"), 0)

    def test_target_shaped_writing_scores_above_unrelated_shape(self):
        cross = [
            [QPointF(50, 20), QPointF(50, 100)],
            [QPointF(20, 60), QPointF(80, 60)],
        ]
        score = shape_similarity(cross, chr(0x5341))
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_mouse_clicks_never_create_canvas_strokes(self):
        canvas = WritingCanvas()
        canvas.show()
        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton)
        self.assertEqual(canvas.strokes, [])
        canvas.close()

    def test_c_key_clears_the_main_canvas(self):
        window = MainWindow()
        window.show()
        window.canvas.start_stroke([QPointF(10, 10), QPointF(20, 20)])
        window.canvas.finish_stroke()
        window.canvas.setFocus()
        QTest.keyClick(window.canvas, Qt.Key.Key_C)
        self.app.processEvents()
        self.assertEqual(window.canvas.strokes, [])
        window.close()


class _FakeCanvas(QObject):
    def __init__(self):
        super().__init__()
        self.strokes = []
        self.cancelled = 0

    def start_stroke(self, point):
        self.strokes.append([QPointF(point)])

    def extend_stroke(self, point):
        self.strokes[-1].append(QPointF(point))

    def finish_stroke(self):
        pass

    def cancel_current_stroke(self):
        self.cancelled += 1
        self.strokes.pop()


class _FakeWindowsTouchpad:
    def __init__(self):
        self.message = None

    def decode_message(self, _):
        return self.message


class TrackpadInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.canvas = _FakeCanvas()
        self.manager = TrackpadInputManager(self.canvas)
        self.manager.windows = _FakeWindowsTouchpad()

    def send(self, message, pointer_id, x, y):
        self.manager.windows.message = ("pointer", message, pointer_id, x, y)
        with patch("app.trackpad_input.screen_pixels_to_widget",
                   return_value=QPoint(x, y)):
            self.manager.process_native_message(0)

    def test_contact_down_move_up_forms_one_stroke(self):
        self.send(WM_POINTERDOWN, 1, 10, 10)
        self.send(WM_POINTERUPDATE, 1, 30, 30)
        self.send(WM_POINTERUP, 1, 50, 50)
        self.assertEqual(len(self.canvas.strokes), 1)
        self.assertGreaterEqual(len(self.canvas.strokes[0]), 2)
        self.assertEqual(self.manager.observed_events, {"down", "move", "up"})

    def test_multiple_contacts_cancel_the_gesture(self):
        self.send(WM_POINTERDOWN, 1, 10, 10)
        self.send(WM_POINTERDOWN, 2, 20, 20)
        self.assertEqual(self.canvas.cancelled, 1)
        self.assertEqual(self.canvas.strokes, [])

    def test_no_native_pointer_message_does_not_draw(self):
        self.manager.windows.message = None
        self.manager.process_native_message(0)
        self.assertEqual(self.canvas.strokes, [])

    def test_raw_contact_reports_start_move_and_end_a_stroke(self):
        common = {
            "contact_id": 7,
            "device_id": 99,
            "x_min": 0,
            "x_max": 1000,
            "y_min": 0,
            "y_max": 1000,
            "tip": True,
            "confidence": True,
            "contact_count": 1,
        }
        reports = [
            dict(common, x=100, y=100),
            dict(common, x=500, y=500),
            dict(common, x=900, y=900, tip=False, confidence=False,
                 contact_count=0),
        ]
        self.manager.windows.message = ("raw", reports)
        with patch("app.trackpad_input.touchpad_to_widget",
                   side_effect=lambda x, y, *_: QPoint(x, y)):
            self.manager.process_native_message(0)
        self.assertEqual(len(self.canvas.strokes), 1)
        self.assertEqual(self.manager.observed_events, {"down", "move", "up"})


if __name__ == "__main__":
    unittest.main()
