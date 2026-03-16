from overlay_paths import get_resource_dir, get_user_data_dir

# GENERAL
ENABLE_COLLAPSE_ANIMATION = True
LABEL_DEFAULT_TEXT = "Captions Placeholder"
FONT_FAMILY = "Segoe UI"
SECONDARY_ACTION_INDICATOR_ACTIVE = False
EXCLUDE_OVERLAY_FROM_CAPTURE = False

# CAPTURE / PREVIEW
CAPTURE_FPS = 30
CAPTURE_FLIP_HORIZONTAL = True
SIGN_PREDICTION_MIN_CONFIDENCE = 0.6
DETECTION_MAX_DIM = 640
DETECTION_MIN_DIM = 320
ENABLE_DETECTION_RESIZE = True
ENABLE_DETECTION_SQUARE = True
SELECTION_INSTRUCTION_TEXT = "Drag to select capture region. Press ENTER or SPACE to confirm."
SELECTION_TEXT_FONT_SIZE = 13
SELECTION_TEXT_MARGIN_TOP = 20
SELECTION_DIM_ALPHA = 120
SELECTION_BORDER_WIDTH = 1
HIGHLIGHT_BORDER_WIDTH = 1
HIGHLIGHT_DURATION_MS = 1000
PREVIEW_WIDTH = 320
PREVIEW_HEIGHT = 180
PREVIEW_MARGIN = 24
PREVIEW_TITLE_HEIGHT = 28
PREVIEW_TITLE_BG = "rgba(18, 18, 20, 235)"
PREVIEW_TITLE_TEXT = "rgba(255, 255, 255, 235)"
PREVIEW_TITLE_SUBTEXT = "rgba(255, 255, 255, 200)"
PREVIEW_REGION_BG = "rgba(0, 0, 0, 160)"
PREVIEW_REGION_TEXT = "rgba(255, 255, 255, 220)"
PREVIEW_HINT_TEXT = "rgba(255, 255, 255, 200)"
STATUS_UPDATE_INTERVAL_MS = 500
STATUS_PANEL_PADDING = 10
STATUS_PANEL_BG = "rgba(20, 20, 22, 235)"
STATUS_PANEL_BORDER = "rgba(255, 255, 255, 24)"
STATUS_PANEL_TEXT = "rgba(255, 255, 255, 220)"
STATUS_PANEL_TITLE = "rgba(255, 255, 255, 235)"
STATUS_PANEL_FONT_SIZE = 12
STATUS_PANEL_TITLE_SIZE = 13

# OVERLAY WINDOW
OVERLAY_WIDTH = 520
OVERLAY_MARGIN = 20
OUTER_PADDING = 10
PANEL_SPACING = 8
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
CAPTION_FONT_SIZE_MIN = 12
CAPTION_FONT_SIZE_MAX = 24
PRIMARY_BOX_SIZE_MIN = 90
PRIMARY_BOX_SIZE_MAX = 260
DEFAULT_PRIMARY_BOX_SIZE = 110

# SECONDARY PANEL
SECONDARY_INNER_SPACING = 24
SECONDARY_COLUMN_SPACING = 20
SECONDARY_ACTION_ROW_SPACING = 22
SECONDARY_LABEL_FONT_SIZE = 16
SECONDARY_CONTROL_FONT_SIZE = 15
SECONDARY_CONTROL_MIN_HEIGHT = 36
SECONDARY_SLIDER_GROOVE_HEIGHT = 8
SECONDARY_SLIDER_HANDLE_SIZE = 20
SECONDARY_CHECKBOX_MIN_HEIGHT = 30
SECONDARY_DROPDOWN_WIDTH = 30
SECONDARY_ACTION_BUTTON_SIZE = 58
SECONDARY_PLAY_BUTTON_SIZE = 99
SECONDARY_SIDE_BUTTON_RADIUS = 14
SECONDARY_PLAY_BUTTON_RADIUS = 49
SECONDARY_ACTION_ICON_SIZE = 26
SECONDARY_PLAY_ICON_SIZE = 36

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

THEME_DARK = {
    "is_light": False,
    "primary_bg": PRIMARY_BG,
    "secondary_bg": SECONDARY_BG,
    "border_color": BORDER_COLOR,
    "text_color": TEXT_COLOR,
    "text_muted": "rgba(220, 220, 220, 190)",
    "button_bg": BUTTON_BG,
    "button_hover_bg": BUTTON_HOVER_BG,
    "button_border": BORDER_COLOR,
    "tooltip_bg": "rgba(20, 20, 24, 235)",
    "tooltip_text": TEXT_COLOR,
    "status_chip_bg": "rgba(255, 255, 255, 10)",
    "status_chip_text": TEXT_COLOR,
    "icon_color": "rgba(255, 255, 255, 255)",
    "preview_title_bg": PREVIEW_TITLE_BG,
    "preview_title_text": PREVIEW_TITLE_TEXT,
    "preview_title_subtext": PREVIEW_TITLE_SUBTEXT,
    "preview_region_bg": PREVIEW_REGION_BG,
    "preview_region_text": PREVIEW_REGION_TEXT,
    "preview_hint_text": PREVIEW_HINT_TEXT,
    "preview_container_bg": "rgba(0, 0, 0, 210)",
    "preview_container_border": "rgba(255, 255, 255, 40)",
    "status_panel_bg": STATUS_PANEL_BG,
    "status_panel_border": STATUS_PANEL_BORDER,
    "status_panel_text": STATUS_PANEL_TEXT,
    "status_panel_title": STATUS_PANEL_TITLE,
    "dropdown_bg": "rgba(40, 40, 43, 240)",
    "selection_bg": "rgba(255, 255, 255, 46)",
    "slider_groove_bg": "rgba(255, 255, 255, 36)",
    "slider_handle_bg": "rgba(255, 255, 255, 190)",
    "slider_handle_border": "rgba(255, 255, 255, 80)",
}

THEME_LIGHT = {
    "is_light": True,
    "primary_bg": "rgba(246, 247, 249, 255)",
    "secondary_bg": "rgba(236, 238, 242, 255)",
    "border_color": "rgba(0, 0, 0, 22)",
    "text_color": "rgba(0, 0, 0, 235)",
    "text_muted": "rgba(110, 114, 124, 220)",
    "button_bg": "rgba(0, 0, 0, 8)",
    "button_hover_bg": "rgba(0, 0, 0, 16)",
    "button_border": "rgba(0, 0, 0, 44)",
    "tooltip_bg": "rgba(250, 250, 252, 245)",
    "tooltip_text": "rgba(0, 0, 0, 235)",
    "status_chip_bg": "rgba(0, 0, 0, 6)",
    "status_chip_text": "rgba(0, 0, 0, 235)",
    "icon_color": "rgba(0, 0, 0, 235)",
    "preview_title_bg": "rgba(236, 238, 242, 255)",
    "preview_title_text": "rgba(0, 0, 0, 235)",
    "preview_title_subtext": "rgba(40, 40, 46, 220)",
    "preview_region_bg": "rgba(0, 0, 0, 10)",
    "preview_region_text": "rgba(0, 0, 0, 235)",
    "preview_hint_text": "rgba(40, 40, 46, 220)",
    "preview_container_bg": "rgba(255, 255, 255, 255)",
    "preview_container_border": "rgba(0, 0, 0, 20)",
    "status_panel_bg": "rgba(246, 247, 249, 255)",
    "status_panel_border": "rgba(0, 0, 0, 18)",
    "status_panel_text": "rgba(0, 0, 0, 235)",
    "status_panel_title": "rgba(0, 0, 0, 235)",
    "dropdown_bg": "rgba(246, 247, 249, 255)",
    "selection_bg": "rgba(0, 0, 0, 10)",
    "slider_groove_bg": "rgba(0, 0, 0, 16)",
    "slider_handle_bg": "rgba(0, 0, 0, 200)",
    "slider_handle_border": "rgba(0, 0, 0, 120)",
}


def get_theme_palette(light_theme: bool):
    return THEME_LIGHT if light_theme else THEME_DARK

# OPTIONS
CORNER_TOP_LEFT = "Top Left"
CORNER_TOP_RIGHT = "Top Right"
CORNER_BOTTOM_LEFT = "Bottom Left"
CORNER_BOTTOM_RIGHT = "Bottom Right"
DEFAULT_CORNER = CORNER_BOTTOM_RIGHT
CORNER_OPTIONS = [CORNER_TOP_LEFT, CORNER_TOP_RIGHT, CORNER_BOTTOM_LEFT, CORNER_BOTTOM_RIGHT]

# PREFERENCES
PROJECT_DIR = get_resource_dir()
DEFAULT_SETTINGS_PATH = PROJECT_DIR / "default_settings.json"
USER_PREFERENCES_PATH = get_user_data_dir() / "user_preferences.json"

DEFAULT_SETTINGS = {
    "caption_box_size": DEFAULT_PRIMARY_BOX_SIZE,
    "caption_font_size": DEFAULT_FONT_SIZE,
    "opacity_percent": int(DEFAULT_OPACITY * 100),
    "freeze_on_detection_loss": False,
    "enable_llm_smoothing": False,
    "corner": DEFAULT_CORNER,
    "show_miniplayer": True,
    "flip_input": CAPTURE_FLIP_HORIZONTAL,
    "primary_hand_only": True,
    "light_theme": False,
}
