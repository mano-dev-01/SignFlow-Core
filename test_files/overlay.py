import sys

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QGuiApplication
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
CAPTION_HORIZONTAL_PADDING = 12
CAPTION_VERTICAL_PADDING = 8
CAPTION_MIN_FONT_SIZE = 16
CAPTION_MAX_FONT_SIZE = 48
DEFAULT_FONT_SIZE = 18
DEFAULT_OPACITY = 0.85
MIN_OPACITY = 0.5
MAX_OPACITY = 1.0
MIN_OPACITY_PERCENT = 50
MAX_OPACITY_PERCENT = 100
SECONDARY_EXPANDED_HEIGHT = 360
ANIMATION_DURATION_MS = 220
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
PRIMARY_BG = "rgba(28, 28, 30, 205)"
SECONDARY_BG = "rgba(40, 40, 43, 205)"
BORDER_COLOR = "rgba(255, 255, 255, 28)"
BUTTON_BG = "rgba(255, 255, 255, 24)"
BUTTON_HOVER_BG = "rgba(255, 255, 255, 52)"
RADIUS = 14
LABEL_DEFAULT_TEXT = "Captions Placeholder"
MODEL_OPTIONS = ["Local Small", "Local Medium"]
CORNER_OPTIONS = [CORNER_TOP_LEFT, CORNER_TOP_RIGHT, CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT]


class PrimaryPanel(QFrame):
    toggle_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._font_size = DEFAULT_FONT_SIZE

        self.setObjectName("primaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Minimum)

        root = QHBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(PRIMARY_INNER_SPACING)

        self.caption_label = QLabel(LABEL_DEFAULT_TEXT)
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.toggle_button = QPushButton("▲")
        self.toggle_button.setFixedWidth(BUTTON_WIDTH)
        self.toggle_button.clicked.connect(self.toggle_requested)

        self.quit_button = QPushButton("✕")
        self.quit_button.setFixedWidth(BUTTON_WIDTH)
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
                min-height: 28px;
                font: 600 13px '{FONT_FAMILY}';
            }}
            QPushButton:hover {{
                background-color: {BUTTON_HOVER_BG};
            }}
            """
        )

        self.set_caption_font_size(DEFAULT_FONT_SIZE)

    def set_caption_text(self, text: str):
        self.caption_label.setText(text or LABEL_DEFAULT_TEXT)
        self.update_caption_height()

    def set_caption_font_size(self, size: int):
        clamped = max(CAPTION_MIN_FONT_SIZE, min(CAPTION_MAX_FONT_SIZE, size))
        self._font_size = clamped
        self.caption_label.setFont(QFont(FONT_FAMILY, self._font_size))
        self.update_caption_height()

    def set_expanded_icon(self, expanded: bool):
        self.toggle_button.setText("▼" if expanded else "▲")

    def update_caption_height(self):
        width = self.caption_label.width()
        if width < 120:
            fallback = OVERLAY_WIDTH - (OUTER_PADDING * 2) - BUTTON_WIDTH - PRIMARY_INNER_SPACING - (CAPTION_HORIZONTAL_PADDING * 2)
            width = max(120, fallback)
        metrics = QFontMetrics(self.caption_label.font())
        text_rect = metrics.boundingRect(0, 0, width, 10000, Qt.TextWordWrap, self.caption_label.text())
        target = max(text_rect.height() + CAPTION_VERTICAL_PADDING, metrics.height() + CAPTION_VERTICAL_PADDING)
        self.caption_label.setMinimumHeight(target)
        self.caption_label.setMaximumHeight(target)
        self.caption_label.setContentsMargins(
            CAPTION_HORIZONTAL_PADDING,
            CAPTION_VERTICAL_PADDING // 2,
            CAPTION_HORIZONTAL_PADDING,
            CAPTION_VERTICAL_PADDING // 2,
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_caption_height()


class SecondaryPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("secondaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setMinimumHeight(0)
        self.setMaximumHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(SECONDARY_INNER_SPACING)

        left_col = QVBoxLayout()
        left_col.setSpacing(SECONDARY_COLUMN_SPACING)

        right_col = QVBoxLayout()
        right_col.setSpacing(SECONDARY_COLUMN_SPACING)

        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(CAPTION_MIN_FONT_SIZE, CAPTION_MAX_FONT_SIZE)
        self.font_size_slider.setValue(DEFAULT_FONT_SIZE)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(MIN_OPACITY_PERCENT, MAX_OPACITY_PERCENT)
        self.opacity_slider.setValue(int(DEFAULT_OPACITY * 100))

        self.show_raw_tokens_checkbox = QCheckBox("Show raw tokens")
        self.freeze_on_loss_checkbox = QCheckBox("Freeze captions on detection loss")

        self.enable_llm_checkbox = QCheckBox("Enable LLM smoothing")

        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_OPTIONS)

        self.show_latency_checkbox = QCheckBox("Show latency")

        self.corner_combo = QComboBox()
        self.corner_combo.addItems(CORNER_OPTIONS)

        left_col.addLayout(self._labeled_row("Caption font size", self.font_size_slider))
        left_col.addLayout(self._labeled_row("Overlay opacity", self.opacity_slider))
        left_col.addWidget(self.show_raw_tokens_checkbox)
        left_col.addWidget(self.freeze_on_loss_checkbox)
        left_col.addStretch(1)

        right_col.addWidget(self.enable_llm_checkbox)
        right_col.addLayout(self._labeled_row("Model selection", self.model_combo))
        right_col.addWidget(self.show_latency_checkbox)
        right_col.addLayout(self._labeled_row("Overlay corner", self.corner_combo))
        right_col.addStretch(1)

        root.addLayout(left_col, 1)
        root.addLayout(right_col, 1)

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
                border: none;
                width: 0px;
                height: 0px;
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
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 3px;
                background: rgba(255, 255, 255, 20);
            }}
            QCheckBox::indicator:checked {{
                background: rgba(255, 255, 255, 170);
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
    def __init__(self):
        super().__init__()

        self.caption_text = LABEL_DEFAULT_TEXT
        self.caption_font_size = DEFAULT_FONT_SIZE
        self.overlay_opacity = DEFAULT_OPACITY
        self.show_raw_tokens = False
        self.freeze_on_detection_loss = False
        self.enable_llm_smoothing = False
        self.model_selection = MODEL_OPTIONS[0]
        self.show_latency = False
        self.corner = DEFAULT_CORNER
        self.secondary_expanded = False
        self._primary_base_height = 0
        self._animation_anchor_y = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(OVERLAY_WIDTH + OUTER_PADDING * 2)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        self.root_layout.setSpacing(PANEL_SPACING)

        self.primary_panel = PrimaryPanel()
        self.secondary_panel = SecondaryPanel()

        self.root_layout.addWidget(self.secondary_panel)
        self.root_layout.addWidget(self.primary_panel)

        self.secondary_animation = QPropertyAnimation(self.secondary_panel, b"maximumHeight", self)
        self.secondary_animation.setDuration(ANIMATION_DURATION_MS)
        self.secondary_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.secondary_animation.valueChanged.connect(self.on_secondary_height_changed)
        self.secondary_animation.finished.connect(self.on_secondary_animation_finished)

        self._connect_signals()
        self.primary_panel.set_expanded_icon(self.secondary_expanded)
        self.apply_corner_layout()
        self.apply_state_to_ui()

        app = QApplication.instance()
        if app is not None:
            app.screenAdded.connect(lambda _screen: self.reposition_to_corner())
            app.screenRemoved.connect(lambda _screen: self.reposition_to_corner())

        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is not None:
            primary_screen.geometryChanged.connect(lambda _rect: self.reposition_to_corner())

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

    def apply_state_to_ui(self):
        self.primary_panel.set_caption_text(self.caption_text)
        self.primary_panel.set_caption_font_size(self.caption_font_size)
        self._primary_base_height = self.primary_panel.sizeHint().height()
        self.setWindowOpacity(self.overlay_opacity)

        self.secondary_panel.font_size_slider.setValue(self.caption_font_size)
        self.secondary_panel.opacity_slider.setValue(int(self.overlay_opacity * 100))
        self.secondary_panel.show_raw_tokens_checkbox.setChecked(self.show_raw_tokens)
        self.secondary_panel.freeze_on_loss_checkbox.setChecked(self.freeze_on_detection_loss)
        self.secondary_panel.enable_llm_checkbox.setChecked(self.enable_llm_smoothing)
        self.secondary_panel.model_combo.setCurrentText(self.model_selection)
        self.secondary_panel.show_latency_checkbox.setChecked(self.show_latency)
        self.secondary_panel.corner_combo.setCurrentText(self.corner)

        self.secondary_panel.setMinimumHeight(0)
        self.secondary_panel.setMaximumHeight(0)
        self.sync_window_height()
        self.reposition_to_corner()

    def sync_window_height(self):
        hint_height = self.primary_panel.sizeHint().height()
        if hint_height > 0:
            self._primary_base_height = hint_height
        primary_height = self._primary_base_height if self._primary_base_height > 0 else hint_height
        secondary_height = self.secondary_panel.maximumHeight()
        spacing = PANEL_SPACING if secondary_height > 0 else 0
        total_height = OUTER_PADDING * 2 + primary_height + secondary_height + spacing
        self.setFixedHeight(total_height)

    def _screen_geometry(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _target_position(self, total_height: int):
        geo = self._screen_geometry()
        if geo is None:
            return None

        if self.corner in (CORNER_TOP_LEFT, CORNER_BOTTOM_LEFT):
            x = geo.x() + OVERLAY_MARGIN
        else:
            x = geo.x() + geo.width() - self.width() - OVERLAY_MARGIN

        if self.corner in (CORNER_TOP_LEFT, CORNER_TOP_RIGHT):
            y = geo.y() + OVERLAY_MARGIN
        else:
            if self._animation_anchor_y is not None:
                y = self._animation_anchor_y - total_height
            else:
                bottom_anchor = geo.y() + geo.height() - OVERLAY_MARGIN
                y = bottom_anchor - total_height
        return x, y

    def _apply_geometry(self):
        position = self._target_position(self.height())
        if position is None:
            return
        x, y = position
        self.setGeometry(x, y, self.width(), self.height())

    def on_secondary_height_changed(self, value):
        height = int(value)
        self.secondary_panel.setMinimumHeight(height)
        self.secondary_panel.setMaximumHeight(height)
        self.sync_window_height()
        self._apply_geometry()

    def on_secondary_animation_finished(self):
        self._animation_anchor_y = None
        self.reposition_to_corner()

    def on_font_size_changed(self, value: int):
        self.caption_font_size = value
        self.primary_panel.set_caption_font_size(value)
        self.sync_window_height()
        self._apply_geometry()

    def on_opacity_changed(self, value: int):
        clamped = max(MIN_OPACITY_PERCENT, min(MAX_OPACITY_PERCENT, value))
        self.overlay_opacity = clamped / 100.0
        self.setWindowOpacity(self.overlay_opacity)

    def on_show_raw_tokens_toggled(self, checked: bool):
        self.show_raw_tokens = checked

    def on_freeze_on_loss_toggled(self, checked: bool):
        self.freeze_on_detection_loss = checked

    def on_enable_llm_toggled(self, checked: bool):
        self.enable_llm_smoothing = checked

    def on_model_changed(self, text: str):
        self.model_selection = text

    def on_show_latency_toggled(self, checked: bool):
        self.show_latency = checked

    def on_corner_changed(self, text: str):
        self.corner = text
        self.apply_corner_layout()
        self.reposition_to_corner()

    def set_caption_text(self, text: str):
        self.caption_text = text or LABEL_DEFAULT_TEXT
        self.primary_panel.set_caption_text(self.caption_text)
        self.sync_window_height()
        self._apply_geometry()

    def toggle_secondary_panel(self):
        geo = self._screen_geometry()
        if geo is not None and self.corner in (CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT):
            self._animation_anchor_y = geo.y() + geo.height() - OVERLAY_MARGIN
        else:
            self._animation_anchor_y = None

        self.secondary_expanded = not self.secondary_expanded
        self.primary_panel.set_expanded_icon(self.secondary_expanded)

        start_height = self.secondary_panel.maximumHeight()
        end_height = SECONDARY_EXPANDED_HEIGHT if self.secondary_expanded else 0

        self.secondary_animation.stop()
        self.secondary_animation.setStartValue(start_height)
        self.secondary_animation.setEndValue(end_height)
        self.secondary_animation.start()

    def apply_corner_layout(self):
        self.root_layout.removeWidget(self.primary_panel)
        self.root_layout.removeWidget(self.secondary_panel)

        if self.corner in (CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT):
            self.root_layout.addWidget(self.secondary_panel)
            self.root_layout.addWidget(self.primary_panel)
        else:
            self.root_layout.addWidget(self.primary_panel)
            self.root_layout.addWidget(self.secondary_panel)

        self.sync_window_height()
        self._apply_geometry()

    def reposition_to_corner(self):
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

        self.setGeometry(x, y, self.width(), self.height())


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    overlay = OverlayWindow()
    overlay.show()
    overlay.raise_()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
