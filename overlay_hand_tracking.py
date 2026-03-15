import importlib
import os
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from overlay_constants import SIGN_PREDICTION_MIN_CONFIDENCE


def _safe_import(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception:  # pragma: no cover - allow runtime without optional deps
        return None


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


from overlay_constants import (
    DETECTION_MAX_DIM,
    DETECTION_MIN_DIM,
    ENABLE_DETECTION_RESIZE,
    ENABLE_DETECTION_SQUARE,
)


class HandTracker:
    def __init__(self, primary_hand_only: bool = True):
        self.available = False
        self._primary_hand_only = bool(primary_hand_only)
        self._initialized = False
        self._model = None
        self.last_features = None
        self.last_left_features = None
        self.last_right_features = None
        self.last_status = {
            "hands_detected": 0,
            "left_conf": 0.0,
            "right_conf": 0.0,
            "prediction": "No Hand",
            "prediction_conf": 0.0,
        }
        self._joblib = None
        self._cv2 = None
        self._mp = None
        self._mp_hands = None
        self._mp_draw = None
        self._hands = None
        self._landmark_pb2 = None

    @property
    def primary_hand_only(self):
        return self._primary_hand_only

    def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        self._joblib = _safe_import("joblib")
        self._cv2 = _safe_import("cv2")
        self._mp = _safe_import("mediapipe")

        if self._joblib is not None:
            model_path = Path(__file__).resolve().parent / "models" / "model.pkl"
            if model_path.exists():
                try:
                    self._model = self._joblib.load(os.fspath(model_path))
                except Exception:
                    self._model = None

        if self._mp is None:
            self.available = False
            return

        self._mp_hands = self._mp.solutions.hands
        self._mp_draw = self._mp.solutions.drawing_utils
        try:
            from mediapipe.framework.formats import landmark_pb2
        except Exception:
            landmark_pb2 = None
        self._landmark_pb2 = landmark_pb2
        self._build_hands()

    def _build_hands(self):
        if self._mp_hands is None:
            self.available = False
            return
        max_hands = 1 if self._primary_hand_only else 2
        try:
            self._hands = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
            )
            self.available = True
        except Exception:
            self._hands = None
            self.available = False

    def reconfigure(self, primary_hand_only: bool):
        primary_hand_only = bool(primary_hand_only)
        if primary_hand_only == self._primary_hand_only and self._hands is not None:
            return
        self._primary_hand_only = primary_hand_only
        if not self._initialized:
            return
        self._close_hands()
        self._build_hands()

    def _close_hands(self):
        if self._hands is not None:
            try:
                self._hands.close()
            except Exception:
                pass
        self._hands = None

    def close(self):
        self._close_hands()

    def process(self, frame: dict, flip_horizontal: bool = False):
        if not self.available or self._hands is None or frame is None:
            return frame, self.last_status

        rgb = frame.get("rgb")
        width = int(frame.get("width", 0) or 0)
        height = int(frame.get("height", 0) or 0)
        if rgb is None or width <= 0 or height <= 0:
            return frame, self.last_status

        start_time = time.perf_counter()
        image = np.frombuffer(rgb, dtype=np.uint8).reshape(height, width, 3).copy()
        if flip_horizontal:
            image = image[:, ::-1, :].copy()

        det_image = image
        resized = False
        padded = False
        scale = 1.0
        pad_x = 0
        pad_y = 0
        if ENABLE_DETECTION_RESIZE and self._cv2 is not None:
            max_dim = max(width, height)
            if max_dim > DETECTION_MAX_DIM:
                scale = DETECTION_MAX_DIM / float(max_dim)
            elif max_dim < DETECTION_MIN_DIM:
                scale = DETECTION_MIN_DIM / float(max_dim)
            if abs(scale - 1.0) > 1e-3:
                new_w = max(1, int(width * scale))
                new_h = max(1, int(height * scale))
                det_image = self._cv2.resize(
                    det_image,
                    (new_w, new_h),
                    interpolation=self._cv2.INTER_AREA if scale < 1.0 else self._cv2.INTER_LINEAR,
                )
                resized = True

        if ENABLE_DETECTION_SQUARE:
            h, w = det_image.shape[:2]
            side = max(h, w)
            if h != w:
                square = np.zeros((side, side, 3), dtype=det_image.dtype)
                pad_x = int((side - w) // 2)
                pad_y = int((side - h) // 2)
                square[pad_y : pad_y + h, pad_x : pad_x + w] = det_image
                det_image = square
                padded = True

        results = self._hands.process(det_image)

        left_features = None
        right_features = None
        left_conf = 0.0
        right_conf = 0.0
        unknown_features = []
        prediction_text = "No Hand"
        prediction_conf = 0.0
        label = None

        if results.multi_hand_landmarks:
            det_h, det_w = det_image.shape[:2]

            def draw_landmarks(hand_lms):
                if self._mp_draw is None or self._mp_hands is None:
                    return
                if self._landmark_pb2 is not None and det_w > 0 and det_h > 0:
                    adjusted = self._landmark_pb2.NormalizedLandmarkList()
                    for lm in hand_lms.landmark:
                        x_det = lm.x * det_w
                        y_det = lm.y * det_h
                        x_unpad = x_det - pad_x
                        y_unpad = y_det - pad_y
                        x_orig = x_unpad / scale
                        y_orig = y_unpad / scale
                        x_norm = x_orig / float(width)
                        y_norm = y_orig / float(height)
                        if x_norm < 0.0:
                            x_norm = 0.0
                        elif x_norm > 1.0:
                            x_norm = 1.0
                        if y_norm < 0.0:
                            y_norm = 0.0
                        elif y_norm > 1.0:
                            y_norm = 1.0
                        adjusted.landmark.append(
                            self._landmark_pb2.NormalizedLandmark(x=x_norm, y=y_norm, z=lm.z)
                        )
                    self._mp_draw.draw_landmarks(image, adjusted, self._mp_hands.HAND_CONNECTIONS)
                else:
                    self._mp_draw.draw_landmarks(image, hand_lms, self._mp_hands.HAND_CONNECTIONS)

            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                if self._primary_hand_only and idx > 0:
                    break
                draw_landmarks(hand_landmarks)
                features = build_hand_features(hand_landmarks.landmark)

                score = 0.0
                hand_label = None
                if results.multi_handedness and len(results.multi_handedness) > idx:
                    classification = results.multi_handedness[idx].classification
                    if classification:
                        hand_label = classification[0].label
                        score = float(classification[0].score)

                if label is None and hand_label:
                    label = hand_label

                if hand_label == "Right":
                    if right_features is None or score >= right_conf:
                        right_features = features
                        right_conf = score
                elif hand_label == "Left":
                    if left_features is None or score >= left_conf:
                        left_features = features
                        left_conf = score
                else:
                    unknown_features.append((features, score))

            if right_features is None and unknown_features:
                right_features, right_conf = unknown_features.pop(0)
            if left_features is None and unknown_features:
                left_features, left_conf = unknown_features.pop(0)

        if results.multi_hand_landmarks:
            primary = right_features if right_features is not None else zero_hand_features()
            secondary = left_features if left_features is not None else zero_hand_features()
            only_primary_hand = 1 if right_features is not None and left_features is None else 0

            self.last_features = [only_primary_hand] + primary + secondary
            self.last_left_features = left_features
            self.last_right_features = right_features

            if self._model is not None:
                features = np.array(self.last_features, dtype=np.float32).reshape(1, -1)
                probs = self._model.predict_proba(features)[0]
                prediction_conf = float(np.max(probs))
                if prediction_conf >= SIGN_PREDICTION_MIN_CONFIDENCE:
                    prediction_text = self._model.predict(features)[0]
                else:
                    prediction_text = "Uncertain"
            else:
                prediction_text = "No Model"

        hands_detected = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
        det_h, det_w = det_image.shape[:2]
        processing_ms = (time.perf_counter() - start_time) * 1000.0

        self.last_status = {
            "hands_detected": hands_detected,
            "left_conf": left_conf,
            "right_conf": right_conf,
            "prediction": prediction_text,
            "prediction_conf": prediction_conf,
            "input_w": width,
            "input_h": height,
            "det_w": det_w,
            "det_h": det_h,
            "det_scale": scale,
            "pad_x": pad_x,
            "pad_y": pad_y,
            "flip": bool(flip_horizontal),
            "model_loaded": self._model is not None,
            "hand_label": label or "Unknown",
            "processing_ms": processing_ms,
        }

        out_frame = dict(frame)
        out_frame["rgb"] = image.tobytes()
        return out_frame, self.last_status


class HandTrackingWorker(QThread):
    status_updated = pyqtSignal(dict)
    frame_processed = pyqtSignal(object)
    fps_updated = pyqtSignal(float)
    prediction_updated = pyqtSignal(str)

    def __init__(self, flip_horizontal: bool = False, primary_hand_only: bool = True):
        super().__init__()
        self._tracker = None
        self._flip_horizontal = bool(flip_horizontal)
        self._primary_hand_only = bool(primary_hand_only)
        self._pending_reconfigure = False
        self._queue = deque(maxlen=1)
        self._lock = threading.Lock()
        self._config_lock = threading.Lock()
        self._event = threading.Event()
        self._running = True
        self._fps = 0.0
        self._last_time = None

    @property
    def available(self):
        return bool(self._tracker and self._tracker.available)

    def set_flip_horizontal(self, enabled: bool):
        with self._config_lock:
            self._flip_horizontal = bool(enabled)
        self._event.set()

    def set_primary_hand_only(self, enabled: bool):
        with self._config_lock:
            enabled = bool(enabled)
            if enabled != self._primary_hand_only:
                self._primary_hand_only = enabled
                self._pending_reconfigure = True
        self._event.set()

    def _snapshot_config(self):
        with self._config_lock:
            flip = self._flip_horizontal
            primary_only = self._primary_hand_only
            reconfigure = self._pending_reconfigure
            self._pending_reconfigure = False
        return flip, primary_only, reconfigure

    def _ensure_tracker(self, primary_only: bool):
        if self._tracker is None:
            self._tracker = HandTracker(primary_hand_only=primary_only)
            self._tracker.initialize()
            return
        if self._tracker.primary_hand_only != primary_only:
            self._tracker.reconfigure(primary_only)

    def submit(self, frame: dict):
        if frame is None or not self._running:
            return
        with self._lock:
            self._queue.clear()
            self._queue.append(frame)
        self._event.set()

    def run(self):
        flip, primary_only, _ = self._snapshot_config()
        self._ensure_tracker(primary_only)
        try:
            while self._running:
                if not self._event.wait(0.5):
                    continue
                self._event.clear()

                flip, primary_only, reconfigure = self._snapshot_config()
                if reconfigure:
                    self._ensure_tracker(primary_only)

                with self._lock:
                    frame = self._queue.pop() if self._queue else None
                if frame is None:
                    continue
                if self._tracker is None or not self._tracker.available:
                    continue

                processed, status = self._tracker.process(frame, flip_horizontal=flip)

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
                    prediction = status.get("prediction") if isinstance(status, dict) else None
                    if prediction is not None:
                        self.prediction_updated.emit(str(prediction))
                if processed is not None:
                    self.frame_processed.emit(processed)
        finally:
            if self._tracker is not None:
                self._tracker.close()
                self._tracker = None

    def stop(self):
        self._running = False
        self._event.set()
        self.wait(500)
