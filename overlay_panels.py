import html
import re

from PyQt5.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap
from PyQt5.QtWidgets import (
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

from overlay_constants import (
    BUTTON_BG,
    BUTTON_COLUMN_SPACING,
    BUTTON_HEIGHT,
    BUTTON_HOVER_BG,
    BUTTON_WIDTH,
    CAPTION_HORIZONTAL_PADDING,
    CAPTION_VERTICAL_PADDING,
    CORNER_OPTIONS,
    CAPTION_FONT_SIZE_MAX,
    CAPTION_FONT_SIZE_MIN,
    DEFAULT_FONT_SIZE,
    DEFAULT_PRIMARY_BOX_SIZE,
    FONT_FAMILY,
    get_theme_palette,
    LABEL_DEFAULT_TEXT,
    MAX_OPACITY_PERCENT,
    MIN_OPACITY_PERCENT,
    OUTER_PADDING,
    OVERLAY_WIDTH,
    PRIMARY_BG,
    PRIMARY_BOX_SIZE_MAX,
    PRIMARY_BOX_SIZE_MIN,
    PRIMARY_INNER_SPACING,
    RADIUS,
    SECONDARY_ACTION_BUTTON_SIZE,
    SECONDARY_ACTION_ICON_SIZE,
    SECONDARY_PLAY_BUTTON_RADIUS,
    SECONDARY_PLAY_BUTTON_SIZE,
    SECONDARY_PLAY_ICON_SIZE,
    SECONDARY_ACTION_INDICATOR_ACTIVE,
    SECONDARY_ACTION_ROW_SPACING,
    SECONDARY_BG,
    SECONDARY_CHECKBOX_MIN_HEIGHT,
    SECONDARY_SIDE_BUTTON_RADIUS,
    SECONDARY_COLUMN_SPACING,
    SECONDARY_CONTROL_FONT_SIZE,
    SECONDARY_CONTROL_MIN_HEIGHT,
    SECONDARY_DROPDOWN_WIDTH,
    SECONDARY_INNER_SPACING,
    SECONDARY_LABEL_FONT_SIZE,
    SECONDARY_SLIDER_GROOVE_HEIGHT,
    SECONDARY_SLIDER_HANDLE_SIZE,
    TEXT_COLOR,
    BORDER_COLOR,
)

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
        self.caption_label.setTextFormat(Qt.RichText)
        self._caption_plain = LABEL_DEFAULT_TEXT
        self._caption_mode = "caption"

        self.toggle_button = QPushButton("▾")
        self.toggle_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.toggle_button.clicked.connect(self.toggle_requested)

        self.quit_button = QPushButton("×")
        self.quit_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.quit_button.clicked.connect(self.quit_requested)

        right_buttons = QVBoxLayout()
        right_buttons.setSpacing(BUTTON_COLUMN_SPACING)
        right_buttons.addWidget(self.toggle_button)
        right_buttons.addWidget(self.quit_button)
        right_buttons.addStretch(1)

        root.addWidget(self.caption_label, 1)
        root.addLayout(right_buttons)

        self._theme = get_theme_palette(False)
        self._muted_text_color = self._theme.get("text_muted", "rgba(220, 220, 220, 190)")
        self._base_stylesheet = ""
        self.apply_theme(self._theme)

    def set_caption_mode(self, mode: str):
        mode = mode or "caption"
        self._caption_mode = mode
        if mode == "init":
            self.caption_label.setStyleSheet(f"color: {self._muted_text_color};")
        else:
            self.caption_label.setStyleSheet("")

    def set_caption_text(self, text: str):
        self._caption_plain = text or LABEL_DEFAULT_TEXT
        self.caption_label.setText(self._format_caption(self._caption_plain))
        self._recompute_height()

    def set_caption_font_size(self, size: int):
        self.caption_label.setFont(QFont(FONT_FAMILY, int(size)))
        self._recompute_height()

    def set_caption_box_size(self, size: int):
        self.user_box_size = max(PRIMARY_BOX_SIZE_MIN, min(PRIMARY_BOX_SIZE_MAX, int(size)))
        self._recompute_height()

    def set_expanded_icon(self, expanded: bool):
        self.toggle_button.setText("▴" if expanded else "▾")

    def _apply_panel_style(self, border_color: str):
        self.setStyleSheet(self._base_stylesheet.format(border_color=border_color))

    def apply_theme(self, theme: dict):
        self._theme = theme
        self._muted_text_color = theme.get("text_muted", "rgba(220, 220, 220, 190)")
        self._base_stylesheet = (
            "QFrame#primaryPanel {{"
            f"background-color: {theme['primary_bg']};"
            "border: 1px solid {border_color};"
            f"border-radius: {RADIUS}px;"
            "}}"
            "QLabel {{"
            f"color: {theme['text_color']};"
            "}}"
            "QPushButton {{"
            f"background-color: {theme['button_bg']};"
            f"border: 1px solid {theme['button_border']};"
            "border-radius: 8px;"
            f"color: {theme['text_color']};"
            f"font: 600 13px '{FONT_FAMILY}';"
            "}}"
            "QPushButton:hover {{"
            f"background-color: {theme['button_hover_bg']};"
            "}}"
        )
        self._apply_panel_style(theme["border_color"])
        if self._caption_mode == "init":
            self.caption_label.setStyleSheet(f"color: {self._muted_text_color};")
        else:
            self.caption_label.setStyleSheet("")

    def _recompute_height(self):
        width = self.caption_label.width()
        if width < 120:
            fallback = OVERLAY_WIDTH - (OUTER_PADDING * 2) - BUTTON_WIDTH - PRIMARY_INNER_SPACING - (CAPTION_HORIZONTAL_PADDING * 2)
            width = max(120, fallback)

        metrics = QFontMetrics(self.caption_label.font())
        text_rect = metrics.boundingRect(0, 0, width, 10000, Qt.TextWordWrap, self._caption_plain)
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



    def _format_caption(self, text: str):
        safe = text or ""
        parts = re.split(r"(\s+)", safe)
        last_word_index = None
        for idx in range(len(parts) - 1, -1, -1):
            if parts[idx].strip():
                last_word_index = idx
                break

        rendered = []
        for idx, part in enumerate(parts):
            if not part:
                continue
            if part.isspace():
                chunk = part.replace("\n", "<br>")
                rendered.append(chunk)
                continue
            escaped = html.escape(part)
            if self._caption_mode == "caption" and last_word_index is not None and idx == last_word_index:
                escaped = f"<span style=\"font-weight:600;\">{escaped}</span>"
            rendered.append(escaped)
        return "".join(rendered)

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QPainter, QPen, QColor, QPalette
from PyQt5.QtCore import Qt

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

        # If text color is dark → assume light mode
        light_mode = self.palette().color(self.foregroundRole()).lightness() < 128

        if light_mode:
            border_color = QColor(0, 0, 0, 110 if self.isChecked() else 85)
            fill_color = QColor(0, 0, 0, 48 if self.isChecked() else 18)
            tick_color = QColor(0, 0, 0, 240)
        else:
            # ORIGINAL COLORS (unchanged)
            border_color = QColor(255, 255, 255, 110 if self.isChecked() else 85)
            fill_color = QColor(255, 255, 255, 48 if self.isChecked() else 18)
            tick_color = QColor(245, 245, 245, 240)

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(fill_color)
        painter.drawRoundedRect(indicator_rect, 3, 3)

        if self.isChecked():
            check_pen = QPen(tick_color, 2)
            painter.setPen(check_pen)
            x = indicator_rect.x()
            y = indicator_rect.y()
            w = indicator_rect.width()
            h = indicator_rect.height()

            painter.drawLine(x + int(w * 0.20), y + int(h * 0.55),
                             x + int(w * 0.42), y + int(h * 0.78))
            painter.drawLine(x + int(w * 0.42), y + int(h * 0.78),
                             x + int(w * 0.80), y + int(h * 0.28))

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

def _panel_styles(panel_name: str, theme: dict):
    return f"""
        QFrame#{panel_name} {{
            background-color: {theme["secondary_bg"]};
            border: 1px solid {theme["border_color"]};
            border-radius: {RADIUS}px;
        }}
        QFrame#secondaryDivider {{
            border: none;
            min-height: 1px;
            max-height: 1px;
            background-color: {theme["border_color"]};
        }}
        QLabel, QCheckBox {{
            color: {theme["text_color"]};
            font: 500 {SECONDARY_LABEL_FONT_SIZE}px '{FONT_FAMILY}';
        }}
        QCheckBox {{
            min-height: {SECONDARY_CHECKBOX_MIN_HEIGHT}px;
            spacing: 10px;
        }}
        QComboBox {{
            background-color: {theme["button_bg"]};
            color: {theme["text_color"]};
            border: 1px solid {theme["border_color"]};
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
            border-left: 1px solid {theme["border_color"]};
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
            background-color: {theme["dropdown_bg"]};
            color: {theme["text_color"]};
            border: 1px solid {theme["border_color"]};
            selection-background-color: {theme["selection_bg"]};
            selection-color: {theme["text_color"]};
            outline: 0;
            padding: 6px;
            font: 500 {SECONDARY_CONTROL_FONT_SIZE}px '{FONT_FAMILY}';
        }}
        QSlider::groove:horizontal {{
            border: none;
            height: {SECONDARY_SLIDER_GROOVE_HEIGHT}px;
            background: {theme["slider_groove_bg"]};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {theme["slider_handle_bg"]};
            border: 1px solid {theme["slider_handle_border"]};
            width: {SECONDARY_SLIDER_HANDLE_SIZE}px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QPushButton#restartButton {{
            background-color: {theme["button_bg"]};
            border: 1px solid {theme["button_border"]};
            border-radius: 8px;
            color: {theme["text_color"]};
            font: 600 {SECONDARY_CONTROL_FONT_SIZE}px '{FONT_FAMILY}';
            padding: 4px 10px;
        }}
        QPushButton#restartButton:hover {{
            background-color: {theme["button_hover_bg"]};
        }}
        QPushButton#actionButton {{
            background-color: {theme["button_bg"]};
            border: 1px solid {theme["button_border"]};
            border-radius: {SECONDARY_SIDE_BUTTON_RADIUS}px;
            color: {theme["text_color"]};
            font: 600 18px '{FONT_FAMILY}';
        }}
        QPushButton#actionButton:hover {{
            background-color: {theme["button_hover_bg"]};
        }}
        QPushButton#actionButton:focus {{
            outline: none;
            border: 1px solid {BORDER_COLOR};
        }}
        QPushButton#actionPrimaryButton {{
            background-color: {theme["button_bg"]};
            border: 1px solid {theme["button_border"]};
            border-radius: {SECONDARY_PLAY_BUTTON_RADIUS}px;
            color: {theme["text_color"]};
            font: 600 18px '{FONT_FAMILY}';
        }}
        QPushButton#actionPrimaryButton:hover {{
            background-color: {theme["button_hover_bg"]};
        }}
        QPushButton#actionPrimaryButton:pressed {{
            background-color: rgba(255, 255, 255, 38);
            border: 1px solid {theme["button_border"]};
        }}
        QPushButton#actionPrimaryButton:focus {{
            outline: none;
            border: 1px solid {theme["button_border"]};
        }}
        QToolTip {{
            background-color: {theme["tooltip_bg"]};
            color: {theme["tooltip_text"]};
            border: 1px solid {theme["border_color"]};
            border-radius: 6px;
            padding: 7px 9px;
            font: 500 13px '{FONT_FAMILY}';
        }}
        QLabel#actionStatus {{
            color: {theme["status_chip_text"]};
            background: {theme["status_chip_bg"]};
            border: 1px solid {theme["border_color"]};
            border-radius: 7px;
            padding: 0 10px;
            font: 600 13px '{FONT_FAMILY}';
        }}
        """

class SecondaryPanel(QFrame):
    crop_clicked = pyqtSignal()
    play_pause_toggled = pyqtSignal(bool)
    clear_clicked = pyqtSignal()
    advanced_toggled = pyqtSignal(bool)
    voice_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setObjectName("secondaryPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._is_playing = False
        self._voice_active = False
        self._expanded_height = 0
        self._theme = get_theme_palette(False)
        self._icon_color = QColor(255, 255, 255, 235)

        root = QVBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(SECONDARY_COLUMN_SPACING)

        action_row = QHBoxLayout()
        action_row.setSpacing(SECONDARY_ACTION_ROW_SPACING)
        action_row.setContentsMargins(0, 0, 0, 0)
        self.crop_button = QPushButton("")
        self.crop_button.setObjectName("actionButton")
        self.crop_button.setFixedSize(SECONDARY_ACTION_BUTTON_SIZE, SECONDARY_ACTION_BUTTON_SIZE)
        self.crop_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.crop_button.setFocusPolicy(Qt.NoFocus)
        self.crop_button.setToolTip("Full screen")
        self.crop_button.clicked.connect(self.crop_clicked.emit)

        self.play_pause_button = QPushButton("")
        self.play_pause_button.setObjectName("actionPrimaryButton")
        self.play_pause_button.setFixedSize(SECONDARY_PLAY_BUTTON_SIZE, SECONDARY_PLAY_BUTTON_SIZE)
        self.play_pause_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.play_pause_button.setFocusPolicy(Qt.NoFocus)
        self.play_pause_button.setToolTip("Play / pause")
        self.play_pause_button.clicked.connect(self._toggle_play_pause)

        self.clear_button = QPushButton("")
        self.clear_button.setObjectName("actionButton")
        self.clear_button.setFixedSize(SECONDARY_ACTION_BUTTON_SIZE, SECONDARY_ACTION_BUTTON_SIZE)
        self.clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clear_button.setFocusPolicy(Qt.NoFocus)
        self.clear_button.setToolTip("Select region")
        self.clear_button.clicked.connect(self.clear_clicked.emit)

        self._set_action_icon_sizes()
        self.crop_button.setIcon(self._build_crop_icon(SECONDARY_ACTION_ICON_SIZE))
        self.clear_button.setIcon(self._build_region_icon(SECONDARY_ACTION_ICON_SIZE))
        self._apply_play_pause_icon()

        action_row.addStretch(1)
        action_row.addWidget(self.crop_button)
        action_row.addWidget(self.play_pause_button)
        action_row.addWidget(self.clear_button)
        action_row.addStretch(1)

        action_divider = QFrame()
        action_divider.setObjectName("secondaryDivider")
        action_divider.setFrameShape(QFrame.HLine)
        action_divider.setFrameShadow(QFrame.Plain)

        self.show_advanced_button = QPushButton("")
        self.show_advanced_button.setObjectName("restartButton")
        self.show_advanced_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)
        self.show_advanced_button.setCheckable(True)
        self.show_advanced_button.toggled.connect(self._on_advanced_toggled)
        self._apply_advanced_button_label(False)

        voice_divider = QFrame()
        voice_divider.setObjectName("secondaryDivider")
        voice_divider.setFrameShape(QFrame.HLine)
        voice_divider.setFrameShadow(QFrame.Plain)

        voice_row = QHBoxLayout()
        voice_row.setSpacing(SECONDARY_ACTION_ROW_SPACING)
        voice_row.setContentsMargins(0, 0, 0, 0)

        self.voice_label = QLabel("Voice to Speech")

        self.voice_status = QLabel()
        self.voice_status.setObjectName("actionStatus")
        self.voice_status.setAlignment(Qt.AlignCenter)
        self.voice_status.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)
        self.voice_status.setMaximumHeight(SECONDARY_CONTROL_MIN_HEIGHT)
        self.voice_status.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.voice_status.setMinimumWidth(90)

        self.voice_button = QPushButton("")
        self.voice_button.setObjectName("actionButton")
        self.voice_button.setFixedSize(SECONDARY_ACTION_BUTTON_SIZE, SECONDARY_ACTION_BUTTON_SIZE)
        self.voice_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.voice_button.setFocusPolicy(Qt.NoFocus)
        self.voice_button.clicked.connect(self._toggle_voice)
        self.voice_button.setIconSize(QSize(SECONDARY_ACTION_ICON_SIZE, SECONDARY_ACTION_ICON_SIZE))
        self._apply_voice_icon()

        root.addLayout(action_row)
        root.addWidget(action_divider)
        root.addWidget(self.show_advanced_button)
        root.addWidget(voice_divider)
        root.addLayout(voice_row)

        voice_row.addWidget(self.voice_label, 1)
        voice_row.addWidget(self.voice_status)
        voice_row.addWidget(self.voice_button)

        self.setStyleSheet(_panel_styles("secondaryPanel", self._theme))
        self._apply_voice_status()
        self._expanded_height = self.sizeHint().height()
        self.setFixedHeight(0)

    def expanded_height(self):
        if self._expanded_height <= 0:
            self._expanded_height = self.sizeHint().height()
        return self._expanded_height

    def set_advanced_expanded(self, expanded: bool):
        blocked = self.show_advanced_button.blockSignals(True)
        self.show_advanced_button.setChecked(bool(expanded))
        self.show_advanced_button.blockSignals(blocked)
        self._apply_advanced_button_label(bool(expanded))

    def _on_advanced_toggled(self, checked: bool):
        self._apply_advanced_button_label(bool(checked))
        self.advanced_toggled.emit(bool(checked))

    def _apply_advanced_button_label(self, expanded: bool):
        caret = "\u25B4" if expanded else "\u25BE"
        self.show_advanced_button.setText(f"Advanced {caret}")

    @staticmethod
    def _labeled_row(title: str, widget: QWidget):
        layout = QVBoxLayout()
        layout.setSpacing(14 if isinstance(widget, QSlider) else 10)
        label = QLabel(title)
        label.setMinimumHeight(int(SECONDARY_LABEL_FONT_SIZE * 1.4))
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def _set_action_icon_sizes(self):
        side_icon_size = QSize(SECONDARY_ACTION_ICON_SIZE, SECONDARY_ACTION_ICON_SIZE)
        play_icon_size = QSize(SECONDARY_PLAY_ICON_SIZE, SECONDARY_PLAY_ICON_SIZE)
        self.crop_button.setIconSize(side_icon_size)
        self.play_pause_button.setIconSize(play_icon_size)
        self.clear_button.setIconSize(side_icon_size)
        if hasattr(self, "voice_button"):
            self.voice_button.setIconSize(side_icon_size)

    def _new_icon_canvas(self, size: int):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        return pix

    def _build_crop_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self._icon_color, 1.8)
        painter.setPen(pen)
        m = 3
        painter.drawRect(m, m, size - (m * 2), size - (m * 2))
        painter.drawLine(m, size // 3, m, m)
        painter.drawLine(size // 3, m, m, m)
        painter.end()
        return QIcon(pix)

    def _build_region_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self._icon_color, 1.6)
        pen.setCapStyle(Qt.SquareCap)
        painter.setPen(pen)

        s = float(size)
        pad = int(s * 0.18)
        x1 = int(s * 0.40)
        x2 = int(s * 0.60)
        y1 = int(s * 0.40)
        y2 = int(s * 0.60)
        left = pad
        right = int(s - pad)
        top = pad
        bottom = int(s - pad)

        # 3x3 tic-tac-toe grid
        painter.drawLine(x1, top, x1, bottom)
        painter.drawLine(x2, top, x2, bottom)
        painter.drawLine(left, y1, right, y1)
        painter.drawLine(left, y2, right, y2)

        painter.end()
        return QIcon(pix)

    def _build_play_icon(self, size: int):
        pix = self._new_icon_canvas(size)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._icon_color)
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
        painter.setBrush(self._icon_color)
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
        pen = QPen(self._icon_color, 2.0)
        painter.setPen(pen)
        m = int(size * 0.24)
        painter.drawLine(m, m, int(size - m), int(size - m))
        painter.drawLine(m, int(size - m), int(size - m), m)
        painter.end()
        return QIcon(pix)

    def set_playing(self, is_playing: bool):
        self._is_playing = bool(is_playing)
        self._apply_play_pause_icon()

    def set_voice_active(self, active: bool):
        self._voice_active = bool(active)
        self._apply_voice_icon()
        self._apply_voice_status()

    def _apply_play_pause_icon(self):
        if self._is_playing:
            self.play_pause_button.setIcon(self._build_pause_icon(SECONDARY_PLAY_ICON_SIZE))
        else:
            self.play_pause_button.setIcon(self._build_play_icon(SECONDARY_PLAY_ICON_SIZE))

    def _apply_voice_icon(self):
        if self._voice_active:
            self.voice_button.setIcon(self._build_pause_icon(SECONDARY_ACTION_ICON_SIZE))
        else:
            self.voice_button.setIcon(self._build_play_icon(SECONDARY_ACTION_ICON_SIZE))

    def _apply_voice_status(self):
        if self._voice_active:
            self.voice_status.setText("Listening")
            self.voice_button.setToolTip("Stop voice to text")
        else:
            self.voice_status.setText("Inactive")
            self.voice_button.setToolTip("Start voice to text")

    def _toggle_play_pause(self):
        self._is_playing = not self._is_playing
        self._apply_play_pause_icon()
        self.play_pause_toggled.emit(self._is_playing)

    def _toggle_voice(self):
        self._voice_active = not self._voice_active
        self._apply_voice_icon()
        self._apply_voice_status()
        self.voice_toggled.emit(self._voice_active)

    def apply_theme(self, theme: dict):
        self._theme = theme
        if theme.get("is_light"):
            self._icon_color = QColor(theme["icon_color"])
        else:
            self._icon_color = QColor(255, 255, 255, 235)
        self.setStyleSheet(_panel_styles("secondaryPanel", theme))
        self.crop_button.setIcon(self._build_crop_icon(SECONDARY_ACTION_ICON_SIZE))
        self.clear_button.setIcon(self._build_region_icon(SECONDARY_ACTION_ICON_SIZE))
        self._apply_play_pause_icon()
        self._apply_voice_icon()

class AdvancedPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("advancedPanel")
        self.setFixedWidth(OVERLAY_WIDTH)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._status_active = False
        self._expanded_height = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING)
        root.setSpacing(SECONDARY_COLUMN_SPACING)

        columns_row = QHBoxLayout()
        columns_row.setSpacing(SECONDARY_INNER_SPACING)

        left_col = QVBoxLayout()
        left_col.setSpacing(SECONDARY_COLUMN_SPACING)

        right_col = QVBoxLayout()
        right_col.setSpacing(SECONDARY_COLUMN_SPACING)

        self.caption_box_size_slider = QSlider(Qt.Horizontal)
        self.caption_box_size_slider.setRange(PRIMARY_BOX_SIZE_MIN, PRIMARY_BOX_SIZE_MAX)

        self.caption_font_size_slider = QSlider(Qt.Horizontal)
        self.caption_font_size_slider.setRange(CAPTION_FONT_SIZE_MIN, CAPTION_FONT_SIZE_MAX)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(MIN_OPACITY_PERCENT, MAX_OPACITY_PERCENT)

        self.show_miniplayer_checkbox = ThemedCheckBox("Show miniplayer")
        self.show_model_status_checkbox = ThemedCheckBox("Show model status")
        self.disable_llm_checkbox = ThemedCheckBox("Disable LLM smoothing")
        self.flip_input_checkbox = ThemedCheckBox("Flip input")
        self.primary_hand_only_checkbox = ThemedCheckBox("Detect only one / primary hand")
        self.light_theme_checkbox = ThemedCheckBox("Light theme")

        self.corner_combo = ThemedComboBox()
        self.corner_combo.addItems(CORNER_OPTIONS)

        self.status_indicator = QLabel()
        self._apply_status_indicator()
        self.status_indicator.setObjectName("actionStatus")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setTextFormat(Qt.RichText)
        self.status_indicator.setMinimumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.status_indicator.setMaximumHeight(SECONDARY_ACTION_BUTTON_SIZE)
        self.status_indicator.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.restart_button = QPushButton("Restart")
        self.restart_button.setObjectName("restartButton")
        self.restart_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        self.reset_preferences_button = QPushButton("Reset Preferences To Default")
        self.reset_preferences_button.setObjectName("restartButton")
        self.reset_preferences_button.setMinimumHeight(SECONDARY_CONTROL_MIN_HEIGHT)

        left_col.addLayout(self._labeled_row("Caption box size", self.caption_box_size_slider))
        left_col.addLayout(self._labeled_row("Caption font size", self.caption_font_size_slider))
        left_col.addLayout(self._labeled_row("Caption box opacity", self.opacity_slider))
        left_col.addWidget(self.show_miniplayer_checkbox)
        left_col.addWidget(self.show_model_status_checkbox)
        left_col.addWidget(self.light_theme_checkbox)
        left_col.addStretch(1)

        right_col.addWidget(self.disable_llm_checkbox)
        right_col.addWidget(self.flip_input_checkbox)
        right_col.addWidget(self.primary_hand_only_checkbox)
        right_col.addLayout(self._labeled_row("Overlay corner", self.corner_combo))
        right_col.addLayout(self._labeled_row("Status", self.status_indicator))
        right_col.addWidget(self.restart_button)
        right_col.addStretch(1)

        columns_row.addLayout(left_col, 1)
        columns_row.addLayout(right_col, 1)

        root.addLayout(columns_row)
        root.addWidget(self.reset_preferences_button)

        self._theme = get_theme_palette(False)
        self.setStyleSheet(_panel_styles("advancedPanel", self._theme))
        self._expanded_height = self.sizeHint().height()
        self.setFixedHeight(0)

    def expanded_height(self):
        if self._expanded_height <= 0:
            self._expanded_height = self.sizeHint().height()
        return self._expanded_height

    @staticmethod
    def _labeled_row(title: str, widget: QWidget):
        layout = QVBoxLayout()
        layout.setSpacing(14 if isinstance(widget, QSlider) else 10)
        label = QLabel(title)
        label.setMinimumHeight(int(SECONDARY_LABEL_FONT_SIZE * 1.4))
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def _apply_status_indicator(self):
        indicator_symbol = "●" if self._status_active else "○"
        indicator_state = "Active" if self._status_active else "Inactive"
        indicator_symbol_color = "rgb(80, 200, 120)" if self._status_active else "rgb(145, 145, 145)"
        self.status_indicator.setText(
            f"Status: {indicator_state} "
            f"<span style=\"color:{indicator_symbol_color}; font-size:16px;\">{indicator_symbol}</span>"
        )

    def set_status_active(self, active: bool):
        self._status_active = bool(active)
        self._apply_status_indicator()

    def apply_theme(self, theme: dict):
        self._theme = theme
        self.setStyleSheet(_panel_styles("advancedPanel", theme))
