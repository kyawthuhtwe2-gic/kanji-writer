"""Download KanjiVG stroke SVGs (CC BY-SA 3.0, http://kanjivg.tagaini.net)."""
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from practice.character_data import PRACTICE_SETS  # noqa: E402

URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{:05x}.svg"
OUT = ROOT / "practice" / "strokes"
OUT.mkdir(exist_ok=True)
chars = {item.character for items in PRACTICE_SETS.values() for item in items}
for ch in sorted(chars):
    target = OUT / f"{ord(ch):05x}.svg"
    if target.exists():
        continue
    try:
        with urllib.request.urlopen(URL.format(ord(ch)), timeout=20) as r:
            target.write_bytes(r.read())
    except Exception as exc:
        print("FAILED", ch, exc)
print("done", len(list(OUT.glob("*.svg"))), "of", len(chars))
