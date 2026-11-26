# Japanese Handwriting Practice

Windows 11 desktop practice for hiragana, katakana, and the original beginner
kanji set. The canvas accepts **native touchpad HID contact reports or Windows
`PT_TOUCHPAD` pointer contacts only**: finger contact starts a stroke, movement
extends it, and lift finishes it. Mouse, touch-screen, and click-and-drag events
are ignored; there is no webcam or alternate input mode.

## Requirements and installation

- Windows 11
- Python 3.11 or newer
- A Precision Touchpad/driver that delivers `PT_TOUCHPAD` `WM_POINTER` events
- Internet access for the initial PySide6 installation

Run `start.bat`. On first run it creates the virtual environment and installs
dependencies, then launches the app. To install manually, run
`python -m pip install -r requirements.txt` and `python main.py`.
`diagnose_trackpad.bat` opens the standalone input diagnostic.

## Verify click-free hardware input

1. Launch `diagnose_trackpad.bat`.
2. Select **Start / reset test**.
3. Glide one finger on the touchpad over the canvas without pressing or
   clicking, move it, then lift.
4. The test passes only when it reports native touchpad contact-down, move, and
   contact-up messages. Try several short strokes.
5. If the diagnostic reports no native `PT_TOUCHPAD` events, click-free writing
   is unsupported by the current hardware/driver/API path. The app deliberately
   does not fall back to mouse emulation or click-and-drag.

The application cannot infer support just because Windows enumerates a
touchpad; the finger test is required.

## Practice

- Select Hiragana, Katakana, or Kanji.
- Write with a single finger; multiple simultaneous contacts cancel the stroke.
- Use pen-width, undo, redo, clear, and next-character controls. Press **C** to
  clear the canvas from the keyboard.
- **Check writing** compares the drawing to the current target locally. Its
  score is a shape-overlap estimate, not general-purpose OCR.
- Progress and recent attempts are kept for the current app session.

The reference glyph and expected stroke count are shown. Authoritative
per-stroke vector animations are not bundled. The original eight N5 kanji and
their reading/meaning data are preserved, alongside 46 basic characters in
each kana set.

## Native input implementation and limits

The input path registers Windows Raw Input for HID Digitizer/Touchpad
(usage page `0x0D`, usage `0x05`), parses the device's HID report descriptor and
contact reports with `HidP_*`, and also recognizes `PT_TOUCHPAD` pointer type 5.
Only real HID tip-switch/contact-ID/X/Y data or `PT_TOUCHPAD` contacts can draw.
Windows may still withhold contact reports from an ordinary desktop app; those
machines show an incompatibility warning. The pointer-only test failed on the
development machine. Raw HID contact reporting must be confirmed using the
diagnostic before treating click-free writing as supported.

Implementation modules are in `app/`: native touchpad decoding, coordinate
mapping, stroke smoothing, canvas, recognition adapter, and main window.
