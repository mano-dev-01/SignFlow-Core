import os
import random
import sys
import warnings

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QApplication

from overlay_constants import (
    BUTTON_WIDTH,
    CAPTION_HORIZONTAL_PADDING,
    CAPTION_VERTICAL_PADDING,
    OUTER_PADDING,
    OVERLAY_WIDTH,
    PRIMARY_INNER_SPACING,
)
from overlay_preferences import ensure_preferences_files
from overlay_window import OverlayWindow

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("GLOG_minloglevel", "2")
warnings.filterwarnings(
    "ignore",
    message=r"SymbolDatabase\\.GetPrototype\\(\\) is deprecated.*",
)

DEBUG_CAPTIONS = "--random" in sys.argv
ENABLE_LOGGING = "--log" in sys.argv
if DEBUG_CAPTIONS or ENABLE_LOGGING:
    sys.argv = [arg for arg in sys.argv if arg not in ("--random", "--log")]
DEBUG_CAPTION_INTERVAL_MS = 450


class CaptionSimulator:
    def __init__(self, overlay: OverlayWindow, interval_ms: int = DEBUG_CAPTION_INTERVAL_MS):
        self._overlay = overlay
        self._timer = QTimer(overlay)
        self._timer.setInterval(int(interval_ms))
        self._timer.timeout.connect(self._tick)
        self._lines = []
        self._start_new_line = False

        self._sentences = [
            "I am going to the store.",
            "We should review the schedule for tomorrow.",
            "Please let me know when you are ready.",
            "The meeting starts in ten minutes.",
            "This is a quick test of the caption stream.",
            "Thanks for checking the overlay responsiveness.",
            "Let us keep the conversation clear and natural.",
            "The weather looks great for the afternoon.",
            "We can follow up with the design review later.",
            "I will send the updated notes after this call.",
        ]
        self._sentence_queue = []
        self._current_words = []
        self._word_index = 0
        self._load_next_sentence()
        self._timer.start()

    def _load_next_sentence(self):
        if not self._sentence_queue:
            self._sentence_queue = list(self._sentences)
            random.shuffle(self._sentence_queue)
        sentence = self._sentence_queue.pop(0)
        self._current_words = sentence.split()
        self._word_index = 0

    def _compute_layout(self):
        label = self._overlay.primary_panel.caption_label
        width = label.width()
        if width < 120:
            fallback = (
                OVERLAY_WIDTH
                - (OUTER_PADDING * 2)
                - BUTTON_WIDTH
                - PRIMARY_INNER_SPACING
                - (CAPTION_HORIZONTAL_PADDING * 2)
            )
            width = max(120, int(fallback))
        metrics = QFontMetrics(label.font())
        avg_char = max(6, int(metrics.averageCharWidth()))
        max_chars = max(12, int(width / avg_char))

        line_height = max(1, metrics.lineSpacing())
        available_height = max(1, int(self._overlay.applied_caption_box_size - (OUTER_PADDING * 2)))
        max_lines = max(1, int((available_height - CAPTION_VERTICAL_PADDING) / line_height))
        max_lines = max(1, min(5, max_lines))
        return max_chars, max_lines

    def _append_word(self, word: str, max_chars: int):
        if not self._lines:
            self._lines.append(word)
            return
        current = self._lines[-1]
        if not current:
            self._lines[-1] = word
            return
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            self._lines[-1] = candidate
        else:
            self._lines.append(word)

    def _tick(self):
        max_chars, max_lines = self._compute_layout()
        if self._start_new_line:
            if not self._lines or self._lines[-1]:
                self._lines.append("")
            self._start_new_line = False

        if self._word_index >= len(self._current_words):
            self._load_next_sentence()

        emitted_word = None
        if self._word_index < len(self._current_words):
            word = self._current_words[self._word_index]
            self._word_index += 1
            self._append_word(word, max_chars)
            emitted_word = word

        if self._word_index >= len(self._current_words):
            self._start_new_line = True

        if max_lines > 0 and len(self._lines) > max_lines:
            self._lines = self._lines[-max_lines:]

        text = "\n".join(line for line in self._lines if line is not None)
        self._overlay._has_prediction = True
        self._overlay._set_caption_mode()
        self._overlay.set_caption_text(text.strip() if text.strip() else " ")
        if emitted_word and getattr(self._overlay, "caption_logger", None) is not None:
            self._overlay.caption_logger.log_event(
                tokens_predicted=[emitted_word],
                raw_output=emitted_word,
                smoothed_output=emitted_word,
                prediction_latency_ms=0.0,
                model_name="debug_random_generator",
                llm_smoothing_enabled=False,
            )


def main():
    defaults, preferences = ensure_preferences_files()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    overlay = OverlayWindow(
        defaults=defaults,
        preferences=preferences,
        debug_captions=DEBUG_CAPTIONS,
        enable_logging=ENABLE_LOGGING,
    )
    overlay.show()
    overlay.raise_()

    if DEBUG_CAPTIONS:
        overlay._caption_simulator = CaptionSimulator(overlay)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
