import json
import os
import sys
from pathlib import Path

from PyQt5.QtCore import QAbstractAnimation, QEasingCurve, Qt, QVariantAnimation, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QGuiApplication, QRegion
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

OVERLAY_WIDTH = 520
OVERLAY_MARGIN = 20
OUTER_PADDING = 10
PANEL_SPACING = 8
PRIMARY_INNER_SPACING = 10
SECONDARY_INNER_SPACING = 24
SECONDARY_COLUMN_SPACING = 20
BUTTON_COLUMN_SPACING = 8
BUTTON_WIDTH = 40
BUTTON_HEIGHT = 32
CAPTION_HORIZONTAL_PADDING = 12
CAPTION_VERTICAL_PADDING = 8
CAPTION_MIN_FONT_SIZE = 16
CAPTION_MAX_FONT_SIZE = 48
DEFAULT_FONT_SIZE = 18
DEFAULT_OPACITY = 0.80
MIN_OPACITY_PERCENT = 50
MAX_OPACITY_PERCENT = 100
SECONDARY_EXPANDED_HEIGHT = 360
ANIMATION_DURATION_MS = 220
ENABLE_COLLAPSE_ANIMATION = True
SECONDARY_LABEL_FONT_SIZE = 16
SECONDARY_CONTROL_FONT_SIZE = 15
SECONDARY_CONTROL_MIN_HEIGHT = 36
SECONDARY_SLIDER_GROOVE_HEIGHT = 8
SECONDARY_SLIDER_HANDLE_SIZE = 20
SECONDARY_CHECKBOX_MIN_HEIGHT = 30
SECONDARY_DROPDOWN_WIDTH = 30
CORNER_TOP_LEFT = "Top Left"
CORNER_TOP_RIGHT = "Top Right"
CORNER_BOTTOM_LEFT = "Bottom Left"
CORNER_BOTTOM_RIGHT = "Bottom Right"
DEFAULT_CORNER = CORNER_BOTTOM_RIGHT
FONT_FAMILY = "Segoe UI"
TEXT_COLOR = "rgba(255, 255, 255, 235)"
PRIMARY_BG = "rgba(28, 28, 30, 255)"
SECONDARY_BG = "rgba(40, 40, 43, 255)"
BORDER_COLOR = "rgba(255, 255, 255, 28)"
BUTTON_BG = "rgba(255, 255, 255, 24)"
BUTTON_HOVER_BG = "rgba(255, 255, 255, 52)"
RADIUS = 14
LABEL_DEFAULT_TEXT = "Captions Placeholder"
MODEL_OPTIONS = ["Local Small", "Local Medium"]
CORNER_OPTIONS = [CORNER_TOP_LEFT, CORNER_TOP_RIGHT, CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT]

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SETTINGS_PATH = PROJECT_DIR / "default_settings.json"
USER_PREFERENCES_PATH = PROJECT_DIR / "user_preferences.json"

DEFAULT_SETTINGS = {
    "font_size": DEFAULT_FONT_SIZE,
    "opacity_percent": int(DEFAULT_OPACITY * 100),
    "show_raw_tokens": False,
    "freeze_on_detection_loss": False,
    "enable_llm_smoothing": False,
    "model_selection": MODEL_OPTIONS[0],
    "show_latency": False,
    "corner": DEFAULT_CORNER,
}


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
        "font_size": _clamp_int(source.get("font_size"), CAPTION_MIN_FONT_SIZE, CAPTION_MAX_FONT_SIZE, DEFAULT_SETTINGS["font_size"]),
        "opacity_percent": _clamp_int(source.get("opacity_percent"), MIN_OPACITY_PERCENT, MAX_OPACITY_PERCENT, DEFAULT_SETTINGS["opacity_percent"]),
        "show_raw_tokens": _as_bool(source.get("show_raw_tokens"), DEFAULT_SETTINGS["show_raw_tokens"]),
        "freeze_on_detection_loss": _as_bool(source.get("freeze_on_detection_loss"), DEFAULT_SETTINGS["freeze_on_detection_loss"]),
        "enable_llm_smoothing": _as_bool(source.get("enable_llm_smoothing"), DEFAULT_SETTINGS["enable_llm_smoothing"]),
        "model_selection": source.get("model_selection") if source.get("model_selection") in MODEL_OPTIONS else DEFAULT_SETTINGS["model_selection"],
        "show_latency": _as_bool(source.get("show_latency"), DEFAULT_SETTINGS["show_latency"]),
        "corner": source.get("corner") if source.get("corner") in CORNER_OPTIONS else DEFAULT_SETTINGS["corner"],
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
    _write_json(DEFAULT_SETTINGS_PATH, defaults)

    user_raw = _read_json(USER_PREFERENCES_PATH)
    user = _sanitize_settings(user_raw if user_raw is not None else defaults)
    _write_json(USER_PREFERENCES_PATH, user)

    return defaults, user


def save_user_preferences(preferences):
    _write_json(USER_PREFERENCES_PATH, _sanitize_settings(preferences))


def restart_current_process():
    if getattr(sys, "frozen", False):
        os.execv(sys.executable, [sys.executable] + sys.argv[1:])
    else:
        script_path = os.path.abspath(sys.argv[0])
        os.execv(sys.executable, [sys.executable, script_path] + sys.argv[1:])


class PrimaryPanel(QFrame):
    toggle_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("primaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)

        root = QHBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(PRIMARY_INNER_SPACING)

        self.caption_label = QLabel(LABEL_DEFAULT_TEXT)
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.toggle_button = QPushButton("▲")
        self.toggle_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.toggle_button.clicked.connect(self.toggle_requested)

        self.quit_button = QPushButton("✕")
        self.quit_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.quit_button.clicked.connect(self.quit_requested)

        right_buttons = QVBoxLayout()
        right_buttons.setSpacing(BUTTON_COLUMN_SPACING)
        right_buttons.addWidget(self.toggle_button)
        right_buttons.addWidget(self.quit_button)
        right_buttons.addStretch(1)

        root.addWidget(self.caption_label, 1)
        root.addLayout(right_buttons)

        self.setStyleSheet(
            f"""
            QFrame#primaryPanel {{
                background-color: {PRIMARY_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: {RADIUS}px;
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
            QPushButton {{
                background-color: {BUTTON_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                color: {TEXT_COLOR};
                font: 600 13px '{FONT_FAMILY}';
            }}
            QPushButton:hover {{
                background-color: {BUTTON_HOVER_BG};
            }}
            """
        )

    def set_caption_text(self, text: str):
        self.caption_label.setText(text or LABEL_DEFAULT_TEXT)
        self._recompute_height()

    def set_caption_font_size(self, size: int):
        clamped = max(CAPTION_MIN_FONT_SIZE, min(CAPTION_MAX_FONT_SIZE, size))
        self.caption_label.setFont(QFont(FONT_FAMILY, clamped))
        self._recompute_height()

    def set_expanded_icon(self, expanded: bool):
        self.toggle_button.setText("▼" if expanded else "▲")

    def _recompute_height(self):
        width = self.caption_label.width()
        if width < 120:
            fallback = OVERLAY_WIDTH - (OUTER_PADDING * 2) - BUTTON_WIDTH - PRIMARY_INNER_SPACING - (CAPTION_HORIZONTAL_PADDING * 2)
            width = max(120, fallback)

        metrics = QFontMetrics(self.caption_label.font())
        text_rect = metrics.boundingRect(0, 0, width, 10000, Qt.TextWordWrap, self.caption_label.text())
        caption_height = max(text_rect.height() + CAPTION_VERTICAL_PADDING, metrics.height() + CAPTION_VERTICAL_PADDING)

        self.caption_label.setMinimumHeight(caption_height)
        self.caption_label.setMaximumHeight(caption_height)
        self.caption_label.setContentsMargins(
            CAPTION_HORIZONTAL_PADDING,
            CAPTION_VERTICAL_PADDING // 2,
            CAPTION_HORIZONTAL_PADDING,
            CAPTION_VERTICAL_PADDING // 2,
        )

        controls_height = (BUTTON_HEIGHT * 2) + BUTTON_COLUMN_SPACING
        content_height = max(caption_height, controls_height)
        self.setFixedHeight((OUTER_PADDING * 2) + content_height)


class SecondaryPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("secondaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setFixedHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(SECONDARY_COLUMN_SPACING)

        columns_row = QHBoxLayout()
        columns_row.setSpacing(SECONDARY_INNER_SPACING)

        left_col = QVBoxLayout()
        left_col.setSpacing(SECONDARY_COLUMN_SPACING)

        right_col = QVBoxLayout()
        right_col.setSpacing(SECONDARY_COLUMN_SPACING)

        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(CAPTION_MIN_FONT_SIZE, CAPTION_MAX_FONT_SIZE)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(MIN_OPACITY_PERCENT, MAX_OPACITY_PERCENT)

        self.show_raw_tokens_checkbox = QCheckBox("Show raw tokens")
        self.freeze_on_loss_checkbox = QCheckBox("Freeze captions on detection loss")

        self.restart_button = QPushButton("Restart")
        self.restart_button.setObjectName("restartButton")
        self.restart_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        self.enable_llm_checkbox = QCheckBox("Enable LLM smoothing")

        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_OPTIONS)

        self.show_latency_checkbox = QCheckBox("Show latency")

        self.corner_combo = QComboBox()
        self.corner_combo.addItems(CORNER_OPTIONS)

        self.reset_preferences_button = QPushButton("Reset Preferences To Default")
        self.reset_preferences_button.setObjectName("restartButton")
        self.reset_preferences_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        left_col.addLayout(self._labeled_row("Caption font size", self.font_size_slider))
        left_col.addLayout(self._labeled_row("Overlay opacity", self.opacity_slider))
        left_col.addWidget(self.show_raw_tokens_checkbox)
        left_col.addWidget(self.freeze_on_loss_checkbox)
        left_col.addWidget(self.restart_button)
        left_col.addStretch(1)

        right_col.addWidget(self.enable_llm_checkbox)
        right_col.addLayout(self._labeled_row("Model selection", self.model_combo))
        right_col.addWidget(self.show_latency_checkbox)
        right_col.addLayout(self._labeled_row("Overlay corner", self.corner_combo))
        right_col.addStretch(1)

        columns_row.addLayout(left_col, 1)
        columns_row.addLayout(right_col, 1)
        root.addLayout(columns_row)
        root.addWidget(self.reset_preferences_button)

        self.setStyleSheet(
            f"""
            QFrame#secondaryPanel {{
                background-color: {SECONDARY_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: {RADIUS}px;
            }}
            QLabel, QCheckBox {{
                color: {TEXT_COLOR};
                font: 500 {SECONDARY_LABEL_FONT_SIZE}px '{FONT_FAMILY}';
            }}
            QCheckBox {{
                min-height: {SECONDARY_CHECKBOX_MIN_HEIGHT}px;
                spacing: 10px;
            }}
            QComboBox {{
                background-color: rgba(255, 255, 255, 24);
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 6px 10px;
                padding-right: 28px;
                min-height: {SECONDARY_CONTROL_MIN_HEIGHT}px;
                font: 500 {SECONDARY_CONTROL_FONT_SIZE}px '{FONT_FAMILY}';
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {SECONDARY_DROPDOWN_WIDTH}px;
                border: none;
                border-left: 1px solid {BORDER_COLOR};
                background: rgba(255, 255, 255, 20);
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid rgba(255, 255, 255, 210);
                margin-top: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: rgba(40, 40, 43, 240);
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                selection-background-color: rgba(255, 255, 255, 46);
                selection-color: {TEXT_COLOR};
                outline: 0;
                padding: 6px;
                font: 500 {SECONDARY_CONTROL_FONT_SIZE}px '{FONT_FAMILY}';
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: {SECONDARY_SLIDER_GROOVE_HEIGHT}px;
                background: rgba(255, 255, 255, 36);
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: rgba(255, 255, 255, 180);
                border: none;
                width: {SECONDARY_SLIDER_HANDLE_SIZE}px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QPushButton#restartButton {{
                background-color: {BUTTON_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                color: {TEXT_COLOR};
                font: 600 {SECONDARY_CONTROL_FONT_SIZE}px '{FONT_FAMILY}';
                padding: 4px 10px;
            }}
            QPushButton#restartButton:hover {{
                background-color: {BUTTON_HOVER_BG};
            }}
            """
        )

    @staticmethod
    def _labeled_row(title: str, widget: QWidget):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        label = QLabel(title)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout


class OverlayWindow(QWidget):
    def __init__(self, defaults, preferences):
        super().__init__()

        self.defaults = defaults
        self.preferences = preferences
        self.caption_text = LABEL_DEFAULT_TEXT
        self.caption_font_size = self.preferences["font_size"]
        self.pending_font_size = self.preferences["font_size"]
        self.overlay_opacity = self.preferences["opacity_percent"] / 100.0
        self.show_raw_tokens = self.preferences["show_raw_tokens"]
        self.freeze_on_detection_loss = self.preferences["freeze_on_detection_loss"]
        self.enable_llm_smoothing = self.preferences["enable_llm_smoothing"]
        self.model_selection = self.preferences["model_selection"]
        self.show_latency = self.preferences["show_latency"]
        self.corner = self.preferences["corner"]
        self.secondary_expanded = False
        self.secondary_current_height = 0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        self.root_layout.setSpacing(0)

        self.primary_panel = PrimaryPanel()
        self.secondary_panel = SecondaryPanel()

        self.inter_panel_spacer = QWidget()
        self.inter_panel_spacer.setFixedHeight(0)
        self.inter_panel_spacer.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.secondary_animation = QVariantAnimation(self)
        self.secondary_animation.setDuration(ANIMATION_DURATION_MS)
        self.secondary_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.secondary_animation.valueChanged.connect(self.on_secondary_animation_value)
        self.secondary_animation.finished.connect(self.on_secondary_animation_finished)

        self._rebuild_stack()
        self._connect_signals()
        self.primary_panel.set_expanded_icon(self.secondary_expanded)
        self.apply_state_to_ui()

        app = QApplication.instance()
        if app is not None:
            app.screenAdded.connect(lambda _screen: self._position_window())
            app.screenRemoved.connect(lambda _screen: self._position_window())

        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is not None:
            primary_screen.geometryChanged.connect(lambda _rect: self._position_window())

    def _write_preferences(self):
        self.preferences["font_size"] = self.pending_font_size
        self.preferences["opacity_percent"] = int(round(self.overlay_opacity * 100))
        self.preferences["show_raw_tokens"] = self.show_raw_tokens
        self.preferences["freeze_on_detection_loss"] = self.freeze_on_detection_loss
        self.preferences["enable_llm_smoothing"] = self.enable_llm_smoothing
        self.preferences["model_selection"] = self.model_selection
        self.preferences["show_latency"] = self.show_latency
        self.preferences["corner"] = self.corner
        save_user_preferences(self.preferences)

    def _connect_signals(self):
        self.primary_panel.toggle_requested.connect(self.toggle_secondary_panel)
        self.primary_panel.quit_requested.connect(QApplication.instance().quit)

        self.secondary_panel.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        self.secondary_panel.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.secondary_panel.show_raw_tokens_checkbox.toggled.connect(self.on_show_raw_tokens_toggled)
        self.secondary_panel.freeze_on_loss_checkbox.toggled.connect(self.on_freeze_on_loss_toggled)
        self.secondary_panel.enable_llm_checkbox.toggled.connect(self.on_enable_llm_toggled)
        self.secondary_panel.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.secondary_panel.show_latency_checkbox.toggled.connect(self.on_show_latency_toggled)
        self.secondary_panel.corner_combo.currentTextChanged.connect(self.on_corner_changed)
        self.secondary_panel.restart_button.clicked.connect(self.on_restart_requested)
        self.secondary_panel.reset_preferences_button.clicked.connect(self.on_reset_preferences_requested)

    def _rebuild_stack(self):
        while self.root_layout.count():
            item = self.root_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        if self.corner in (CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT):
            self.root_layout.addStretch(1)
            self.root_layout.addWidget(self.secondary_panel)
            self.root_layout.addWidget(self.inter_panel_spacer)
            self.root_layout.addWidget(self.primary_panel)
        else:
            self.root_layout.addWidget(self.primary_panel)
            self.root_layout.addWidget(self.inter_panel_spacer)
            self.root_layout.addWidget(self.secondary_panel)
            self.root_layout.addStretch(1)

    def _screen_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _primary_height(self):
        h = self.primary_panel.height()
        if h > 0:
            return h
        return self.primary_panel.sizeHint().height()

    def _full_window_height(self):
        return (OUTER_PADDING * 2) + self._primary_height() + PANEL_SPACING + SECONDARY_EXPANDED_HEIGHT

    def _visible_stack_height(self):
        extra = PANEL_SPACING + self.secondary_current_height if self.secondary_current_height > 0 else 0
        return (OUTER_PADDING * 2) + self._primary_height() + extra

    def _set_secondary_height(self, height: int, force_hide: bool = False):
        clamped = max(0, min(SECONDARY_EXPANDED_HEIGHT, int(height)))
        self.secondary_current_height = clamped
        self.inter_panel_spacer.setFixedHeight(PANEL_SPACING if clamped > 0 else 0)
        self.secondary_panel.setFixedHeight(clamped)

        if force_hide or clamped == 0:
            self.secondary_panel.hide()
        else:
            self.secondary_panel.show()

    def _update_mask(self):
        visible_height = max(1, min(self._visible_stack_height(), self.height()))
        y_offset = 0
        if self.corner in (CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT):
            y_offset = self.height() - visible_height
        self.setMask(QRegion(0, y_offset, self.width(), visible_height))

    def _position_window(self):
        geo = self._screen_geometry()
        if geo is None:
            return

        if self.corner in (CORNER_TOP_LEFT, CORNER_BOTTOM_LEFT):
            x = geo.x() + OVERLAY_MARGIN
        else:
            x = geo.x() + geo.width() - self.width() - OVERLAY_MARGIN

        if self.corner in (CORNER_TOP_LEFT, CORNER_TOP_RIGHT):
            y = geo.y() + OVERLAY_MARGIN
        else:
            y = geo.y() + geo.height() - self.height() - OVERLAY_MARGIN

        self.move(x, y)

    def _refresh_window_geometry(self, reposition: bool):
        self.setFixedSize(OVERLAY_WIDTH + (OUTER_PADDING * 2), self._full_window_height())
        self._update_mask()
        if reposition:
            self._position_window()

    def apply_state_to_ui(self):
        self.primary_panel.set_caption_text(self.caption_text)
        self.primary_panel.set_caption_font_size(self.caption_font_size)
        self.setWindowOpacity(self.overlay_opacity)

        self.secondary_panel.font_size_slider.setValue(self.pending_font_size)
        self.secondary_panel.opacity_slider.setValue(int(round(self.overlay_opacity * 100)))
        self.secondary_panel.show_raw_tokens_checkbox.setChecked(self.show_raw_tokens)
        self.secondary_panel.freeze_on_loss_checkbox.setChecked(self.freeze_on_detection_loss)
        self.secondary_panel.enable_llm_checkbox.setChecked(self.enable_llm_smoothing)
        self.secondary_panel.model_combo.setCurrentText(self.model_selection)
        self.secondary_panel.show_latency_checkbox.setChecked(self.show_latency)
        self.secondary_panel.corner_combo.setCurrentText(self.corner)

        self._set_secondary_height(0, force_hide=True)
        self._refresh_window_geometry(reposition=True)

    def on_secondary_animation_value(self, value):
        self._set_secondary_height(int(value), force_hide=False)
        self._update_mask()

    def on_secondary_animation_finished(self):
        if not self.secondary_expanded:
            self._set_secondary_height(0, force_hide=True)
            self._update_mask()

    def on_font_size_changed(self, value: int):
        self.pending_font_size = max(CAPTION_MIN_FONT_SIZE, min(CAPTION_MAX_FONT_SIZE, int(value)))
        self._write_preferences()

    def on_opacity_changed(self, value: int):
        clamped = max(MIN_OPACITY_PERCENT, min(MAX_OPACITY_PERCENT, int(value)))
        self.overlay_opacity = clamped / 100.0
        self.setWindowOpacity(self.overlay_opacity)
        self._write_preferences()

    def on_show_raw_tokens_toggled(self, checked: bool):
        self.show_raw_tokens = checked
        self._write_preferences()

    def on_freeze_on_loss_toggled(self, checked: bool):
        self.freeze_on_detection_loss = checked
        self._write_preferences()

    def on_enable_llm_toggled(self, checked: bool):
        self.enable_llm_smoothing = checked
        self._write_preferences()

    def on_model_changed(self, text: str):
        self.model_selection = text
        self._write_preferences()

    def on_show_latency_toggled(self, checked: bool):
        self.show_latency = checked
        self._write_preferences()

    def on_corner_changed(self, text: str):
        self.corner = text
        self._rebuild_stack()
        self._refresh_window_geometry(reposition=True)
        self._write_preferences()

    def on_restart_requested(self):
        self._write_preferences()
        restart_current_process()

    def on_reset_preferences_requested(self):
        defaults = _read_json(DEFAULT_SETTINGS_PATH)
        normalized_defaults = _sanitize_settings(defaults if defaults is not None else DEFAULT_SETTINGS)
        save_user_preferences(normalized_defaults)
        restart_current_process()

    def set_caption_text(self, text: str):
        self.caption_text = text or LABEL_DEFAULT_TEXT
        self.primary_panel.set_caption_text(self.caption_text)
        self._refresh_window_geometry(reposition=True)

    def toggle_secondary_panel(self):
        if ENABLE_COLLAPSE_ANIMATION and self.secondary_animation.state() == QAbstractAnimation.Running:
            return

        self.secondary_expanded = not self.secondary_expanded
        self.primary_panel.set_expanded_icon(self.secondary_expanded)

        target = SECONDARY_EXPANDED_HEIGHT if self.secondary_expanded else 0

        if not ENABLE_COLLAPSE_ANIMATION:
            self.secondary_animation.stop()
            self._set_secondary_height(target, force_hide=not self.secondary_expanded)
            self._update_mask()
            return

        self.secondary_animation.stop()
        self.secondary_animation.setStartValue(self.secondary_current_height)
        self.secondary_animation.setEndValue(target)
        self.secondary_animation.start()


def main():
    defaults, preferences = ensure_preferences_files()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    overlay = OverlayWindow(defaults=defaults, preferences=preferences)
    overlay.show()
    overlay.raise_()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
