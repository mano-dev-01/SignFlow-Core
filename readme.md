# SignFlow

SignFlow is a real-time sign language to English captioning system.

It captures a selected region of the screen (for example, a signing video), detects hand landmarks using MediaPipe, predicts signs using a machine learning model, and displays live captions as a floating translucent overlay.

This project is built for reliability, low latency, and demo stability.

---

## Features

- Screen region capture
- Two-hand landmark detection
- Temporal sign buffering
- ML-based sign classification
- Token → English smoothing
- Always-on-top caption overlay

---

## Run

Create a virtual environment:

python -m venv venv  
venv\Scripts\activate  (Windows)

Install dependencies:

pip install -r requirements.txt

Start the app:

python app/main.py

---

## Note

This is a proof-of-concept assistive system.  
It does not cover full sign language and does not replace human interpreters.