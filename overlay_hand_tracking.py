import threading
import time
from collections import deque

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

try:
    import mediapipe as mp
except Exception:  # pragma: no cover - allow runtime without mediapipe
    mp = None


def normalize_landmarks(landmarks):
    lm = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    base = lm[0]
    lm = lm - base
    scale = np.linalg.norm(lm[9]) if lm.shape[0] > 9 else 0.0
    if scale < 1e-6:
        scale = 1.0
    return lm / scale


def angle_at(a, b, c):
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return 0.0
    cos = float(np.dot(ba, bc) / denom)
    cos = max(-1.0, min(1.0, cos))
    return float(np.arccos(cos))


def compute_angles(lm):
    idx = lambda i: lm[i]
    return [
        angle_at(idx(1), idx(2), idx(3)),
        angle_at(idx(2), idx(3), idx(4)),
        angle_at(idx(5), idx(6), idx(7)),
        angle_at(idx(6), idx(7), idx(8)),
        angle_at(idx(9), idx(10), idx(11)),
        angle_at(idx(10), idx(11), idx(12)),
        angle_at(idx(13), idx(14), idx(15)),
        angle_at(idx(14), idx(15), idx(16)),
        angle_at(idx(17), idx(18), idx(19)),
        angle_at(idx(18), idx(19), idx(20)),
    ]


def build_hand_features(landmarks):
    norm = normalize_landmarks(landmarks)
    coords = norm.flatten().tolist()
    angles = compute_angles(norm)
    return coords + angles


def zero_hand_features():
    return [0.0] * 73


class HandTracker:
    def __init__(self):
        self.available = mp is not None
        self.last_features = None
        self.last_left_features = None
        self.last_right_features = None
        self.last_status = {
            "hands_detected": 0,
            "left_conf": 0.0,
            "right_conf": 0.0,
        }

        if not self.available:
            self._hands = None
            self._mp_draw = None
            self._mp_hands = None
            return

        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

    def process(self, frame: dict):
        if not self.available or frame is None:
            return frame, self.last_status

        rgb = frame.get("rgb")
        width = int(frame.get("width", 0) or 0)
        height = int(frame.get("height", 0) or 0)
        if rgb is None or width <= 0 or height <= 0:
            return frame, self.last_status

        image = np.frombuffer(rgb, dtype=np.uint8).reshape(height, width, 3).copy()
        results = self._hands.process(image)

        left_features = None
        right_features = None
        left_conf = 0.0
        right_conf = 0.0
        unknown_features = []

        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                self._mp_draw.draw_landmarks(image, hand_landmarks, self._mp_hands.HAND_CONNECTIONS)
                features = build_hand_features(hand_landmarks.landmark)

                label = None
                score = 0.0
                if results.multi_handedness and len(results.multi_handedness) > idx:
                    classification = results.multi_handedness[idx].classification
                    if classification:
                        label = classification[0].label
                        score = float(classification[0].score)

                if label == "Right":
                    right_features = features
                    right_conf = score
                elif label == "Left":
                    left_features = features
                    left_conf = score
                else:
                    unknown_features.append((features, score))

            if right_features is None and unknown_features:
                right_features, right_conf = unknown_features.pop(0)
            if left_features is None and unknown_features:
                left_features, left_conf = unknown_features.pop(0)

        primary = right_features if right_features is not None else zero_hand_features()
        secondary = left_features if left_features is not None else zero_hand_features()
        only_primary_hand = 1 if right_features is not None and left_features is None else 0

        self.last_features = [only_primary_hand] + primary + secondary
        self.last_left_features = left_features
        self.last_right_features = right_features

        hands_detected = 0
        if results.multi_hand_landmarks:
            hands_detected = len(results.multi_hand_landmarks)

        self.last_status = {
            "hands_detected": hands_detected,
            "left_conf": left_conf,
            "right_conf": right_conf,
        }

        out_frame = dict(frame)
        out_frame["rgb"] = image.tobytes()
        return out_frame, self.last_status


class HandTrackingWorker(QThread):
    status_updated = pyqtSignal(dict)
    frame_processed = pyqtSignal(object)
    fps_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._tracker = HandTracker()
        self._queue = deque(maxlen=1)
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._running = True
        self._fps = 0.0
        self._last_time = None

    @property
    def available(self):
        return self._tracker.available

    def submit(self, frame: dict):
        if not self.available or frame is None:
            return
        with self._lock:
            self._queue.clear()
            self._queue.append(frame)
        self._event.set()

    def run(self):
        while self._running:
            if not self._event.wait(0.5):
                continue
            self._event.clear()
            with self._lock:
                frame = self._queue.pop() if self._queue else None
            if frame is None:
                continue
            processed, status = self._tracker.process(frame)

            now = time.perf_counter()
            if self._last_time is not None:
                delta = now - self._last_time
                if delta > 1e-6:
                    instant = 1.0 / delta
                    self._fps = (self._fps * 0.85) + (instant * 0.15)
                    self.fps_updated.emit(self._fps)
            self._last_time = now

            if status is not None:
                self.status_updated.emit(status)
            if processed is not None:
                self.frame_processed.emit(processed)

    def stop(self):
        self._running = False
        self._event.set()
        self.wait(500)
