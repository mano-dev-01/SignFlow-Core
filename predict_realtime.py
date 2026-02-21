import os
import cv2
import mediapipe as mp
import joblib
import numpy as np

BASE_DIR = os.path.dirname(__file__)
MODEL_NAME = "model_ASL_alphabets.pkl"
MODEL_PATH = os.path.join(BASE_DIR, "models", MODEL_NAME)

model = joblib.load(MODEL_PATH)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

def normalize_landmarks(landmarks):
    lm_list = [[lm.x, lm.y, lm.z] for lm in landmarks]
    base_x, base_y, base_z = lm_list[0]
    normalized = []
    for x, y, z in lm_list:
        normalized.append(x - base_x)
        normalized.append(y - base_y)
        normalized.append(z - base_z)
    return normalized

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    prediction_text = "No Hand"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            features = normalize_landmarks(hand_landmarks.landmark)
            features = np.array(features).reshape(1, -1)

            probs = model.predict_proba(features)[0]
            max_prob = np.max(probs)

            if max_prob > 0.7:
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
