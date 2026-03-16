import json

from overlay_constants import (
    CORNER_OPTIONS,
    DEFAULT_SETTINGS,
    DEFAULT_SETTINGS_PATH,
    CAPTION_FONT_SIZE_MAX,
    CAPTION_FONT_SIZE_MIN,
    MAX_OPACITY_PERCENT,
    MIN_OPACITY_PERCENT,
    PRIMARY_BOX_SIZE_MAX,
    PRIMARY_BOX_SIZE_MIN,
    USER_PREFERENCES_PATH,
)


def _clamp_int(value, low, high, fallback):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, parsed))


def _as_bool(value, fallback):
    if isinstance(value, bool):
        return value
    return fallback


def _sanitize_settings(raw):
    source = raw if isinstance(raw, dict) else {}
    return {
        "caption_box_size": _clamp_int(
            source.get("caption_box_size", source.get("font_size")),
            PRIMARY_BOX_SIZE_MIN,
            PRIMARY_BOX_SIZE_MAX,
            DEFAULT_SETTINGS["caption_box_size"],
        ),
        "caption_font_size": _clamp_int(
            source.get("caption_font_size"),
            CAPTION_FONT_SIZE_MIN,
            CAPTION_FONT_SIZE_MAX,
            DEFAULT_SETTINGS["caption_font_size"],
        ),
        "opacity_percent": _clamp_int(
            source.get("opacity_percent"),
            MIN_OPACITY_PERCENT,
            MAX_OPACITY_PERCENT,
            DEFAULT_SETTINGS["opacity_percent"],
        ),
        "freeze_on_detection_loss": _as_bool(
            source.get("freeze_on_detection_loss"),
            DEFAULT_SETTINGS["freeze_on_detection_loss"],
        ),
        "enable_llm_smoothing": _as_bool(source.get("enable_llm_smoothing"), DEFAULT_SETTINGS["enable_llm_smoothing"]),
        "corner": source.get("corner") if source.get("corner") in CORNER_OPTIONS else DEFAULT_SETTINGS["corner"],
        "show_miniplayer": _as_bool(source.get("show_miniplayer"), DEFAULT_SETTINGS["show_miniplayer"]),
        "flip_input": _as_bool(source.get("flip_input"), DEFAULT_SETTINGS["flip_input"]),
        "primary_hand_only": _as_bool(source.get("primary_hand_only"), DEFAULT_SETTINGS["primary_hand_only"]),
        "light_theme": _as_bool(source.get("light_theme"), DEFAULT_SETTINGS["light_theme"]),
    }


def _read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_preferences_files():
    default_raw = _read_json(DEFAULT_SETTINGS_PATH)
    defaults = _sanitize_settings(default_raw if default_raw is not None else DEFAULT_SETTINGS)

    user_raw = _read_json(USER_PREFERENCES_PATH)
    user = _sanitize_settings(user_raw if user_raw is not None else defaults)
    _write_json(USER_PREFERENCES_PATH, user)

    return defaults, user


def save_user_preferences(preferences):
    _write_json(USER_PREFERENCES_PATH, _sanitize_settings(preferences))
