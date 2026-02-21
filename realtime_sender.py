import os

import cv2
import joblib
import mediapipe as mp
import numpy as np
from PyQt5.QtNetwork import QLocalSocket

BASE_DIR = os.path.dirname(__file__)
MODEL_NAME = "model.pkl"
MODEL_PATH = os.path.join(BASE_DIR, "models", MODEL_NAME)

IPC_SERVER_NAME = "signflow_overlay_ipc_v2"
CONNECT_TIMEOUT_MS = 500
WRITE_TIMEOUT_MS = 500
DISCONNECT_TIMEOUT_MS = 200
MESSAGE_DELIMITER = "\n"
PREDICTION_THRESHOLD = 0.7
MIN_STABLE_FRAMES_FOR_APPEND = 4
NO_HAND_FRAMES_TO_RESET_REPEAT_LOCK = 6

model = joblib.load(MODEL_PATH)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

cap = cv2.VideoCapture(0)


def send_caption(caption_text):
    socket = QLocalSocket()
    socket.connectToServer(IPC_SERVER_NAME)

    if not socket.waitForConnected(CONNECT_TIMEOUT_MS):
        return False

    payload = (caption_text + MESSAGE_DELIMITER).encode("utf-8")
    if socket.write(payload) < 0:
        return False

    if not socket.waitForBytesWritten(WRITE_TIMEOUT_MS):
        return False

    socket.disconnectFromServer()
    if socket.state() != QLocalSocket.UnconnectedState:
        socket.waitForDisconnected(DISCONNECT_TIMEOUT_MS)

    return True


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


current_char = "INITIALIZED / WAITING..."
current_sentence = ""
last_sent_sentence = None
candidate_label = None
candidate_stable_frames = 0
last_appended_label = None
no_hand_frames = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    prediction_text = "No Hand"
    detected_label = None

    if results.multi_hand_landmarks:
        right_features = None
        left_features = None
        unknown_features = []

        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            features = build_hand_features(hand_landmarks.landmark)
            label = None
            if results.multi_handedness and len(results.multi_handedness) > idx:
                classification = results.multi_handedness[idx].classification
                if classification:
                    label = classification[0].label

            if label == "Right":
                right_features = features
            elif label == "Left":
                left_features = features
            else:
                unknown_features.append(features)

        if right_features is None and unknown_features:
            right_features = unknown_features.pop(0)
        if left_features is None and unknown_features:
            left_features = unknown_features.pop(0)

        primary = right_features if right_features is not None else zero_hand_features()
        secondary = left_features if left_features is not None else zero_hand_features()
        only_primary_hand = 1 if right_features is not None and left_features is None else 0

        features = [only_primary_hand] + primary + secondary
        features = np.array(features).reshape(1, -1)

        probs = model.predict_proba(features)[0]
        max_prob = np.max(probs)

        if max_prob > PREDICTION_THRESHOLD:
            detected_label = str(model.predict(features)[0]).strip()
            prediction_text = detected_label
        else:
            prediction_text = "Uncertain"

    current_char = str(prediction_text)

    if detected_label:
        no_hand_frames = 0
        if detected_label == candidate_label:
            candidate_stable_frames += 1
        else:
            candidate_label = detected_label
            candidate_stable_frames = 1

        if (
            candidate_stable_frames >= MIN_STABLE_FRAMES_FOR_APPEND
            and detected_label != last_appended_label
        ):
            current_sentence += detected_label
            last_appended_label = detected_label
            candidate_label = None
            candidate_stable_frames = 0

            if current_sentence != last_sent_sentence and send_caption(current_sentence):
                last_sent_sentence = current_sentence
    else:
        candidate_label = None
        candidate_stable_frames = 0
        no_hand_frames += 1
        if no_hand_frames >= NO_HAND_FRAMES_TO_RESET_REPEAT_LOCK:
            last_appended_label = None

    cv2.putText(frame, current_char, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Sentence: {current_sentence}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2)
    cv2.imshow("ASL Prediction", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
hands.close()
cv2.destroyAllWindows()
