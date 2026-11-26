"""Day / night palettes and the application stylesheet built from them."""
from string import Template

THEMES = {
    "day": {
        "bg": "#f3f5fb", "text": "#1b2438",
        "panel": "#ffffff", "panel_border": "#dfe5f0",
        "hero1": "#f4f7ff", "hero2": "#eef3ff", "hero_border": "#e1e9fb",
        "title": "#14213d", "subtitle": "#6b778c", "eyebrow": "#8592a8",
        "target": "#16213a", "accent": "#2f55b8", "section": "#19253b",
        "result": "#55627a", "banner_bg": "#f6f8fc", "banner_text": "#6b778c",
        "hint": "#7a869b", "radio_text": "#334155",
        "surface": "#ffffff", "ind_border": "#c3cde0", "ind_hover": "#7f9be0",
        "groove": "#e3e9f4", "fill": "#6f8fe6",
        "combo_border": "#dbe3f0", "combo_hover": "#9db3ea", "select": "#e8eefc",
        "btn_bg": "#eef2f9", "btn_text": "#2f3b52", "btn_hover": "#e2e9f6",
        "btn_pressed": "#d6dff1", "dis_text": "#a3adbf", "dis_bg": "#f2f4f8",
        "soft_bg": "#ffffff", "soft_text": "#2f55b8", "soft_border": "#d5e0fa",
        "soft_hover": "#f2f6ff", "speak_bg": "#e3ebff", "speak_border": "#7f9be0",
        "speak_text": "#24478e",
        "p1": "#4a74e0", "p2": "#2f55b8", "p1h": "#5a82ea", "p2h": "#3a62c9",
        "ppress": "#274a9e", "prog_bg": "#e6ecf7", "divider": "#e9edf4",
        # canvas / stroke guide
        "cv_bg": "#fbfcff", "cv_grid": "#edf0f5", "cv_axis": "#e0e5ec",
        "cv_ghost": (210, 216, 225, 125), "cv_border": "#e1e7f2",
        "sg_text": "#24395f", "sg_axis": "#e3e8f0", "sg_done": "#9aa9c4",
        "sg_live": "#2563eb", "sg_mark": "#dc2626",
    },
    "night": {
        "bg": "#0e1322", "text": "#e3e9f6",
        "panel": "#171f33", "panel_border": "#26314b",
        "hero1": "#1b2540", "hero2": "#1f2b4b", "hero_border": "#2c3a60",
        "title": "#f1f5ff", "subtitle": "#97a4bd", "eyebrow": "#7d8aa6",
        "target": "#f1f5ff", "accent": "#8fb0ff", "section": "#e3e9f6",
        "result": "#a5b1c9", "banner_bg": "#1b2438", "banner_text": "#97a4bd",
        "hint": "#8793ab", "radio_text": "#cbd5e8",
        "surface": "#171f33", "ind_border": "#3b4967", "ind_hover": "#6f8fe6",
        "groove": "#26314b", "fill": "#5b7bd6",
        "combo_border": "#2c3a5a", "combo_hover": "#5b7bd6", "select": "#243257",
        "btn_bg": "#212b45", "btn_text": "#d5ddef", "btn_hover": "#2a3658",
        "btn_pressed": "#334168", "dis_text": "#5d6a86", "dis_bg": "#1a2238",
        "soft_bg": "#1b2540", "soft_text": "#9bb8ff", "soft_border": "#32447a",
        "soft_hover": "#233059", "speak_bg": "#2a3a6e", "speak_border": "#6f8fe6",
        "speak_text": "#cfdcff",
        "p1": "#4f7bf0", "p2": "#3358c4", "p1h": "#6189f5", "p2h": "#3f66d6",
        "ppress": "#2a4aa6", "prog_bg": "#26314b", "divider": "#26314b",
        "cv_bg": "#121a2e", "cv_grid": "#1b2540", "cv_axis": "#263253",
        "cv_ghost": (120, 135, 170, 90), "cv_border": "#2c3a5a",
        "sg_text": "#cfdcff", "sg_axis": "#26314b", "sg_done": "#5d6f95",
        "sg_live": "#7ea2ff", "sg_mark": "#ff6b6b",
    },
}

_CSS = Template("""
QMainWindow, QWidget { background: $bg; color: $text; }
QLabel, QRadioButton { background: transparent; }
QFrame#panel { background: $panel; border: 1px solid $panel_border;
               border-radius: 20px; }
QFrame#hero { background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                  stop:0 $hero1, stop:1 $hero2);
              border: 1px solid $hero_border; border-radius: 16px; }
QFrame#hero QLabel { background: transparent; }
QLabel#title { font-size: 26px; font-weight: 800; color: $title; }
QLabel#subtitle { color: $subtitle; font-size: 12px; }
QLabel#eyebrow { color: $eyebrow; font-weight: 700; font-size: 10px;
                 letter-spacing: 1px; }
QLabel#target { color: $target; font-size: 58px; min-height: 70px; }
QLabel#reading { color: $accent; font-size: 20px; font-weight: 700; }
QLabel#sectionTitle { color: $section; font-size: 14px; font-weight: 700; }
QLabel#result { color: $result; font-size: 12px; }
QLabel#score { color: $accent; font-size: 30px; font-weight: 800; }
QLabel#banner { color: $banner_text; background: $banner_bg; border-radius: 10px;
                padding: 8px 12px; font-size: 11px; }
QLabel#hint { color: $hint; font-size: 11px; }
QRadioButton { spacing: 8px; color: $radio_text; font-weight: 600; }
QRadioButton::indicator { width: 16px; height: 16px; border-radius: 9px;
                          border: 2px solid $ind_border; background: $surface; }
QRadioButton::indicator:hover { border-color: $ind_hover; }
QRadioButton::indicator:checked { border: 2px solid $accent;
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 $accent, stop:0.5 $accent, stop:0.56 $surface, stop:1 $surface); }
QSlider::groove:horizontal { height: 6px; border-radius: 3px; background: $groove; }
QSlider::sub-page:horizontal { background: $fill; border-radius: 3px; }
QSlider::handle:horizontal { background: $accent; width: 16px; height: 16px;
                             margin: -5px 0; border-radius: 8px;
                             border: 3px solid $surface; }
QComboBox { background: $surface; border: 1px solid $combo_border;
            border-radius: 12px; padding: 8px 14px; min-width: 110px;
            font-weight: 600; }
QComboBox:hover { border-color: $combo_hover; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView { background: $surface; border: 1px solid $combo_border;
                              selection-background-color: $select;
                              selection-color: $text; outline: 0; }
QPushButton { background: $btn_bg; color: $btn_text; border: 0;
              border-radius: 12px; padding: 11px 14px; font-weight: 600; }
QPushButton:hover { background: $btn_hover; }
QPushButton:pressed { background: $btn_pressed; }
QPushButton:disabled { color: $dis_text; background: $dis_bg; }
QPushButton#soft { background: $soft_bg; color: $soft_text;
                   border: 1px solid $soft_border; }
QPushButton#soft:hover { background: $soft_hover; }
QPushButton#soft[speaking="true"] { background: $speak_bg;
    border: 1px solid $speak_border; color: $speak_text; }
QPushButton#primary { color: white; background: qlineargradient(
    x1:0, y1:0, x2:1, y2:1, stop:0 $p1, stop:1 $p2); }
QPushButton#primary:hover { background: qlineargradient(
    x1:0, y1:0, x2:1, y2:1, stop:0 $p1h, stop:1 $p2h); }
QPushButton#primary:pressed { background: $ppress; }
QProgressBar { background: $prog_bg; border: 0; border-radius: 5px; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 $fill, stop:1 $accent); border-radius: 5px; }
QFrame#divider { color: $divider; }
""")


def build_stylesheet(name):
    return _CSS.substitute(THEMES[name])
