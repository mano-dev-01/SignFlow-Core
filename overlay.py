import json
import os
import sys
from pathlib import Path

from PyQt5.QtCore import QAbstractAnimation, QEasingCurve, QRectF, QSize, Qt, QVariantAnimation, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRegion
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

# GENERAL
ENABLE_COLLAPSE_ANIMATION = True
LABEL_DEFAULT_TEXT = "Captions Placeholder"
FONT_FAMILY = "Segoe UI"
SECONDARY_ACTION_INDICATOR_ACTIVE = False

# OVERLAY WINDOW
OVERLAY_WIDTH = 520
OVERLAY_MARGIN = 20
OUTER_PADDING = 10
PANEL_SPACING = 8
SECONDARY_EXPANDED_HEIGHT = 420
ANIMATION_DURATION_MS = 220
RADIUS = 14

# PRIMARY PANEL
PRIMARY_INNER_SPACING = 10
BUTTON_COLUMN_SPACING = 8
BUTTON_WIDTH = 40
BUTTON_HEIGHT = 32
CAPTION_HORIZONTAL_PADDING = 12
CAPTION_VERTICAL_PADDING = 8
DEFAULT_FONT_SIZE = 14
PRIMARY_BOX_SIZE_MIN = 90
PRIMARY_BOX_SIZE_MAX = 260
DEFAULT_PRIMARY_BOX_SIZE = 110

# SECONDARY PANEL
SECONDARY_INNER_SPACING = 24
SECONDARY_COLUMN_SPACING = 20
SECONDARY_ACTION_ROW_SPACING = 10
SECONDARY_LABEL_FONT_SIZE = 16
SECONDARY_CONTROL_FONT_SIZE = 15
SECONDARY_CONTROL_MIN_HEIGHT = 36
SECONDARY_SLIDER_GROOVE_HEIGHT = 8
SECONDARY_SLIDER_HANDLE_SIZE = 20
SECONDARY_CHECKBOX_MIN_HEIGHT = 30
SECONDARY_DROPDOWN_WIDTH = 30
SECONDARY_ACTION_BUTTON_SIZE = 40
SECONDARY_ACTION_ICON_SIZE = 20

# OPACITY
DEFAULT_OPACITY = 0.80
MIN_OPACITY_PERCENT = 50
MAX_OPACITY_PERCENT = 100

# COLORS
TEXT_COLOR = "rgba(255, 255, 255, 235)"
PRIMARY_BG = "rgba(28, 28, 30, 255)"
SECONDARY_BG = "rgba(40, 40, 43, 255)"
BORDER_COLOR = "rgba(255, 255, 255, 28)"
BUTTON_BG = "rgba(255, 255, 255, 24)"
BUTTON_HOVER_BG = "rgba(255, 255, 255, 52)"

# OPTIONS
CORNER_TOP_LEFT = "Top Left"
CORNER_TOP_RIGHT = "Top Right"
CORNER_BOTTOM_LEFT = "Bottom Left"
CORNER_BOTTOM_RIGHT = "Bottom Right"
DEFAULT_CORNER = CORNER_BOTTOM_RIGHT
CORNER_OPTIONS = [CORNER_TOP_LEFT, CORNER_TOP_RIGHT, CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT]
MODEL_OPTIONS = ["Local Small", "Local Medium"]

# PREFERENCES
PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SETTINGS_PATH = PROJECT_DIR / "default_settings.json"
USER_PREFERENCES_PATH = PROJECT_DIR / "user_preferences.json"

DEFAULT_SETTINGS = {
    "caption_box_size": DEFAULT_PRIMARY_BOX_SIZE,
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
        "caption_box_size": _clamp_int(
            source.get("caption_box_size", source.get("font_size")),
            PRIMARY_BOX_SIZE_MIN,
            PRIMARY_BOX_SIZE_MAX,
            DEFAULT_SETTINGS["caption_box_size"],
        ),
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
        self.user_box_size = DEFAULT_PRIMARY_BOX_SIZE
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
        self.caption_label.setFont(QFont(FONT_FAMILY, DEFAULT_FONT_SIZE))
        self._recompute_height()

    def set_caption_box_size(self, size: int):
        self.user_box_size = max(PRIMARY_BOX_SIZE_MIN, min(PRIMARY_BOX_SIZE_MAX, int(size)))
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
        auto_height = (OUTER_PADDING * 2) + content_height
        panel_height = max(auto_height, self.user_box_size)
        self.setFixedHeight(panel_height)


class ThemedCheckBox(QCheckBox):
    def __init__(self, text: str):
        super().__init__(text)
        self._indicator_size = 16
        self._indicator_spacing = 10

    def sizeHint(self):
        base = super().sizeHint()
        width = self._indicator_size + self._indicator_spacing + base.width()
        height = max(base.height(), self._indicator_size)
        return base.expandedTo(base.__class__(width, height))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        indicator_x = 0
        indicator_y = (self.height() - self._indicator_size) // 2
        indicator_rect = self.rect().adjusted(
            indicator_x,
            indicator_y,
            -(self.width() - self._indicator_size),
            -(self.height() - indicator_y - self._indicator_size),
        )

        border_color = QColor(255, 255, 255, 110 if self.isChecked() else 85)
        fill_color = QColor(255, 255, 255, 48 if self.isChecked() else 18)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(fill_color)
        painter.drawRoundedRect(indicator_rect, 3, 3)

        if self.isChecked():
            check_pen = QPen(QColor(245, 245, 245, 240), 2)
            painter.setPen(check_pen)
            x = indicator_rect.x()
            y = indicator_rect.y()
            w = indicator_rect.width()
            h = indicator_rect.height()
            painter.drawLine(x + int(w * 0.20), y + int(h * 0.55), x + int(w * 0.42), y + int(h * 0.78))
            painter.drawLine(x + int(w * 0.42), y + int(h * 0.78), x + int(w * 0.80), y + int(h * 0.28))

        text_x = self._indicator_size + self._indicator_spacing
        text_rect = self.rect().adjusted(text_x, 0, 0, 0)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(self.font())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())


class ThemedComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 245, 245, 230))

        cx = self.width() - (SECONDARY_DROPDOWN_WIDTH // 2)
        cy = (self.height() // 2) + 1
        half_w = 4
        half_h = 3

        path = QPainterPath()
        path.moveTo(cx - half_w, cy - half_h)
        path.lineTo(cx + half_w, cy - half_h)
        path.lineTo(cx, cy + half_h)
        path.closeSubpath()
        painter.drawPath(path)
        painter.end()


class SecondaryPanel(QFrame):
    crop_clicked = pyqtSignal()
    play_pause_toggled = pyqtSignal(bool)
    clear_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("secondaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setFixedHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._is_playing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(SECONDARY_COLUMN_SPACING)

        action_row = QHBoxLayout()
        action_row.setSpacing(SECONDARY_ACTION_ROW_SPACING)
        action_row.setContentsMargins(0, 0, 0, 0)
        self.crop_button = QPushButton("")
        self.crop_button.setObjectName("actionButton")
        self.crop_button.setMinimumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.crop_button.setMaximumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.crop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.crop_button.setFocusPolicy(Qt.NoFocus)
        self.crop_button.clicked.connect(self.crop_clicked.emit)


        self.play_pause_button = QPushButton("")
        self.play_pause_button.setObjectName("actionToggleButton")
        self.play_pause_button.setMinimumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.play_pause_button.setMaximumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.play_pause_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.play_pause_button.setFocusPolicy(Qt.NoFocus)
        self.play_pause_button.clicked.connect(self._toggle_play_pause)

        self.clear_button = QPushButton("")
        self.clear_button.setObjectName("actionButton")
        self.clear_button.setMinimumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.clear_button.setMaximumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.clear_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.clicked.connect(self.clear_clicked.emit)

        self._set_action_icon_sizes()
        self.crop_button.setIcon(self._build_crop_icon(SECONDARY_ACTION_ICON_SIZE))
        self.clear_button.setIcon(self._build_clear_icon(SECONDARY_ACTION_ICON_SIZE))
        self._apply_play_pause_icon()

        indicator_symbol = "●" if SECONDARY_ACTION_INDICATOR_ACTIVE else "○"
        indicator_state = "Active" if SECONDARY_ACTION_INDICATOR_ACTIVE else "Inactive"
        indicator_symbol_color = "rgb(80, 160, 255)" if SECONDARY_ACTION_INDICATOR_ACTIVE else "rgb(145, 145, 145)"
        self.status_indicator = QLabel(
            f"Status: {indicator_state} "
            f"<span style=\"color:{indicator_symbol_color}; font-size:16px;\">{indicator_symbol}</span>"
        )
        self.status_indicator.setObjectName("actionStatus")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setTextFormat(Qt.RichText)
        self.status_indicator.setMinimumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.status_indicator.setMaximumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.status_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        action_row.addWidget(self.crop_button, 1)
        action_row.addWidget(self.play_pause_button, 1)
        action_row.addWidget(self.clear_button, 1)
        action_row.addWidget(self.status_indicator, 3)

        action_divider = QFrame()
        action_divider.setObjectName("secondaryDivider")
        action_divider.setFrameShape(QFrame.HLine)
        action_divider.setFrameShadow(QFrame.Plain)

        columns_row = QHBoxLayout()
        columns_row.setSpacing(SECONDARY_INNER_SPACING)

        left_col = QVBoxLayout()
        left_col.setSpacing(SECONDARY_COLUMN_SPACING)

        right_col = QVBoxLayout()
        right_col.setSpacing(SECONDARY_COLUMN_SPACING)

        self.caption_box_size_slider = QSlider(Qt.Horizontal)
        self.caption_box_size_slider.setRange(PRIMARY_BOX_SIZE_MIN, PRIMARY_BOX_SIZE_MAX)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(MIN_OPACITY_PERCENT, MAX_OPACITY_PERCENT)

        self.show_raw_tokens_checkbox = ThemedCheckBox("Show raw tokens")
        self.freeze_on_loss_checkbox = ThemedCheckBox("Freeze captions on detection loss")

        self.restart_button = QPushButton("Restart")
        self.restart_button.setObjectName("restartButton")
        self.restart_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        self.enable_llm_checkbox = ThemedCheckBox("Enable LLM smoothing")

        self.model_combo = ThemedComboBox()
        self.model_combo.addItems(MODEL_OPTIONS)

        self.show_latency_checkbox = ThemedCheckBox("Show latency")

        self.corner_combo = ThemedComboBox()
        self.corner_combo.addItems(CORNER_OPTIONS)

        self.reset_preferences_button = QPushButton("Reset Preferences To Default")
        self.reset_preferences_button.setObjectName("restartButton")
        self.reset_preferences_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        left_col.addLayout(self._labeled_row("Caption box size", self.caption_box_size_slider))
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

        root.addLayout(action_row)
        root.addWidget(action_divider)
        root.addLayout(columns_row)
        root.addWidget(self.reset_preferences_button)

        self.setStyleSheet(
            f"""
            QFrame#secondaryPanel {{
                background-color: {SECONDARY_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: {RADIUS}px;
            }}
            QFrame#secondaryDivider {{
                border: none;
                min-height: 1px;
                max-height: 1px;
                background-color: rgba(255, 255, 255, 30);
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
                background: transparent;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border: none;
                margin: 0px;
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
            QPushButton#actionButton {{
                background-color: {BUTTON_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 7px;
                color: {TEXT_COLOR};
                font: 600 18px '{FONT_FAMILY}';
            }}
            QPushButton#actionButton:hover {{
                background-color: {BUTTON_HOVER_BG};
            }}
            QPushButton#actionButton:focus {{
                outline: none;
                border: 1px solid {BORDER_COLOR};
            }}
            QPushButton#actionToggleButton {{
                background-color: {BUTTON_BG};
                border: 1px solid {BORDER_COLOR};
                border-radius: 7px;
                color: {TEXT_COLOR};
                font: 600 18px '{FONT_FAMILY}';
            }}
            QPushButton#actionToggleButton:hover {{
                background-color: {BUTTON_HOVER_BG};
            }}
            QPushButton#actionToggleButton:pressed {{
                background-color: rgba(255, 255, 255, 38);
                border: 1px solid {BORDER_COLOR};
            }}
            QPushButton#actionToggleButton:focus {{
                outline: none;
                border: 1px solid {BORDER_COLOR};
            }}
            QLabel#actionStatus {{
                color: {TEXT_COLOR};
                background: rgba(255, 255, 255, 10);
                border: 1px solid {BORDER_COLOR};
                border-radius: 7px;
                padding: 0 10px;
                font: 600 13px '{FONT_FAMILY}';
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

    def _set_action_icon_sizes(self):
        icon_size = QSize(SECONDARY_ACTION_ICON_SIZE, SECONDARY_ACTION_ICON_SIZE)
        self.crop_button.setIconSize(icon_size)
        self.play_pause_button.setIconSize(icon_size)
        self.clear_button.setIconSize(icon_size)

    def _new_icon_canvas(self, size: int):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        return pix

    def _build_crop_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(245, 245, 245, 235), 1.8)
        painter.setPen(pen)
        m = 3
        painter.drawRect(m, m, size - (m * 2), size - (m * 2))
        painter.drawLine(m, size // 3, m, m)
        painter.drawLine(size // 3, m, m, m)
        painter.end()
        return QIcon(pix)

    def _build_play_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 245, 245, 235))
        path = QPainterPath()
        path.moveTo(size * 0.30, size * 0.20)
        path.lineTo(size * 0.30, size * 0.80)
        path.lineTo(size * 0.78, size * 0.50)
        path.closeSubpath()
        painter.drawPath(path)
        painter.end()
        return QIcon(pix)

    def _build_pause_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(245, 245, 245, 235))
        w = size * 0.20
        gap = size * 0.14
        left = (size - (w * 2 + gap)) / 2.0
        r1 = QRectF(left, size * 0.20, w, size * 0.60)
        r2 = QRectF(left + w + gap, size * 0.20, w, size * 0.60)
        painter.drawRoundedRect(r1, 1.5, 1.5)
        painter.drawRoundedRect(r2, 1.5, 1.5)
        painter.end()
        return QIcon(pix)

    def _build_clear_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(245, 245, 245, 235), 2.0)
        painter.setPen(pen)
        m = int(size * 0.24)
        painter.drawLine(m, m, int(size - m), int(size - m))
        painter.drawLine(m, int(size - m), int(size - m), m)
        painter.end()
        return QIcon(pix)

    def _apply_play_pause_icon(self):
        if self._is_playing:
            self.play_pause_button.setIcon(self._build_pause_icon(SECONDARY_ACTION_ICON_SIZE))
        else:
            self.play_pause_button.setIcon(self._build_play_icon(SECONDARY_ACTION_ICON_SIZE))

    def _toggle_play_pause(self):
        self._is_playing = not self._is_playing
        self._apply_play_pause_icon()
        self.play_pause_toggled.emit(self._is_playing)


class OverlayWindow(QWidget):
    def __init__(self, defaults, preferences):
        super().__init__()

        self.defaults = defaults
        self.preferences = preferences
        self.caption_text = LABEL_DEFAULT_TEXT
        self.caption_font_size = DEFAULT_FONT_SIZE
        self.applied_caption_box_size = self.preferences["caption_box_size"]
        self.pending_caption_box_size = self.preferences["caption_box_size"]
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
        self.preferences["caption_box_size"] = self.pending_caption_box_size
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

        self.secondary_panel.caption_box_size_slider.valueChanged.connect(self.on_caption_box_size_changed)
        self.secondary_panel.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        self.secondary_panel.show_raw_tokens_checkbox.toggled.connect(self.on_show_raw_tokens_toggled)
        self.secondary_panel.freeze_on_loss_checkbox.toggled.connect(self.on_freeze_on_loss_toggled)
        self.secondary_panel.enable_llm_checkbox.toggled.connect(self.on_enable_llm_toggled)
        self.secondary_panel.model_combo.currentTextChanged.connect(self.on_model_changed)
        self.secondary_panel.show_latency_checkbox.toggled.connect(self.on_show_latency_toggled)
        self.secondary_panel.corner_combo.currentTextChanged.connect(self.on_corner_changed)
        self.secondary_panel.restart_button.clicked.connect(self.on_restart_requested)
        self.secondary_panel.reset_preferences_button.clicked.connect(self.on_reset_preferences_requested)
        self.secondary_panel.crop_clicked.connect(self.on_crop_clicked)
        self.secondary_panel.play_pause_toggled.connect(self.on_play_pause_toggled)
        self.secondary_panel.clear_clicked.connect(self.on_clear_clicked)

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
        self.primary_panel.set_caption_box_size(self.applied_caption_box_size)
        self.setWindowOpacity(self.overlay_opacity)

        self.secondary_panel.caption_box_size_slider.setValue(self.pending_caption_box_size)
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

    def on_caption_box_size_changed(self, value: int):
        self.pending_caption_box_size = max(PRIMARY_BOX_SIZE_MIN, min(PRIMARY_BOX_SIZE_MAX, int(value)))
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

    def on_crop_clicked(self):
        pass

    def on_play_pause_toggled(self, _is_playing: bool):
        pass

    def on_clear_clicked(self):
        pass

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
    
