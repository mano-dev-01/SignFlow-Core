import os
import cv2
import mediapipe as mp
import joblib
import numpy as np

BASE_DIR = os.path.dirname(__file__)
MODEL_NAME = "model.pkl"
MODEL_PATH = os.path.join(BASE_DIR, "models", MODEL_NAME)

model = joblib.load(MODEL_PATH)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

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

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    prediction_text = "No Hand"

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

        if max_prob > 0.8:
            prediction_text = model.predict(features)[0]
        else:
            prediction_text = "Uncertain"

    cv2.putText(frame, prediction_text, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("ASL Prediction", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()