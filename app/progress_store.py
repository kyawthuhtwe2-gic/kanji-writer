"""Persist practice progress (category, position, completed characters) as JSON."""
import json
import os
from pathlib import Path


def state_path():
    override = os.environ.get("KANJI_WRITER_STATE")
    if override:
        return Path(override)
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "KanjiWriter" / "progress.json"


def load_state(valid_sets):
    """Return (category, index, completed set), validated against valid_sets."""
    try:
        data = json.loads(state_path().read_text(encoding="utf-8"))
        category = data["category"]
        items = valid_sets[category]
        index = int(data["index"])
        if not 0 <= index < len(items):
            index = 0
        completed = {
            (cat, int(i))
            for cat, i in data.get("completed", [])
            if cat in valid_sets and 0 <= int(i) < len(valid_sets[cat])
        }
        return category, index, completed
    except Exception:
        return None


def save_state(category, index, completed):
    try:
        path = state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "category": category,
            "index": index,
            "completed": sorted([cat, i] for cat, i in completed),
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def settings_path():
    return state_path().with_name("settings.json")


def load_settings():
    """Return saved UI settings dict (pen_width, pen_color, press_mode) or {}."""
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(settings):
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(settings), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass
