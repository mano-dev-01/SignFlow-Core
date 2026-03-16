# SignFlow

SignFlow is a Windows-first overlay application that captures a user-selected screen region and previews it live. It is designed to sit on top of calls or streams, keep the capture workflow lightweight, and provide a clean foundation for sign recognition workflows.

Python version: `3.10`

## What It Does Now

- Always-on-top overlay window with capture controls and persistent preferences
- Snipping-style region selection with a dimmed screen and outline
- Live capture of the selected region (mss + QThread)
- Floating preview window with optional status panel and region label
- Pause/resume preview updates (capture thread continues running)
- Caption panel with init mode (status text) and caption mode (live predictions)
- Caption font size control plus caption box size/opacity controls
- Optional hand tracking and prediction display when model + dependencies are present
- Voice-to-text mode with live microphone transcription (SpeechRecognition + PyAudio)
- Advanced settings: Show Miniplayer, Show Model Status, Disable LLM smoothing, Flip Input, Detect only one / primary hand
- Session logging to `logs/` as JSON (events + final caption transcript)
- `--random` caption simulator for UI testing

## What It Does Not Do Yet

- End-to-end, production-grade sign recognition pipeline
- Robust post-processing and sequence smoothing for real-world usage
- Validation on diverse signing conditions and camera setups

## How It Works (Detailed Flow)

1. **Startup**: `overlay.py` initializes the application and creates `OverlayWindow`.
2. **Region Selection**:
   - The user clicks Capture Region or Fullscreen.
   - `overlay_selection.py` displays the selection overlay.
   - The selection is normalized and saved into `capture_state`.
3. **Capture**:
   - `overlay_capture.py` starts a `ScreenCaptureThread` using the selected region.
   - Frames are streamed into `overlay_utils.process_frame`, which dispatches them to the overlay window.
4. **Preview**:
   - `overlay_preview.py` renders the most recent frame.
   - Preview updates are throttled by the UI timer while capture runs continuously.
5. **Optional Hand Tracking**:
   - `overlay_hand_tracking.py` consumes frames and extracts hand landmarks.
   - If a model is available, predictions are produced and surfaced to the UI.
   - Detection status and FPS are emitted as signals to update the status panel.
   - Heavy initialization runs in the worker thread to keep the UI responsive.
6. **Captions + Logging**:
   - Predictions update the caption panel in real time.
   - Each session is logged to `logs/` with metadata, events, and a final transcript.
7. **Debug Captions (Optional)**:
   - `overlay.py --random` enables a caption simulator for UI testing.
   - The simulator generates word-by-word caption output on a timer.
8. **UI State & Preferences**:
   - `overlay_preferences.py` stores user settings in `user_preferences.json`.
   - `overlay_constants.py` defines defaults and UI constants.

## Project Architecture (Current)

**Entry Point**
- `overlay.py`  
  - Application bootstrap and main window initialization
  - Optional caption simulator via `--random`

**Overlay UI + State**
- `overlay_window.py`  
  - Main window, capture lifecycle, preferences, and signal wiring
- `overlay_panels.py`  
  - Primary and secondary control panels
- `overlay_voice.py`  
  - SpeechRecognition-based voice-to-text worker (microphone transcription)

**Capture + Selection + Preview**
- `overlay_capture.py`  
  - Screen capture thread and frame emission
- `overlay_selection.py`  
  - Region selection overlay and highlight overlay
- `overlay_preview.py`  
  - Floating preview window and status view

**Hand Tracking + Prediction (Optional)**
- `overlay_hand_tracking.py`  
  - MediaPipe-based hand tracking, feature extraction, and model inference
  - Emits detection status, processed frames, FPS, and prediction text
  - Supports Flip Input and primary-hand-only detection
- `models/`  
  - `model.pkl`  
  - `model___.pkl` (alternate or legacy model)

**Shared Support**
- `overlay_constants.py`  
  - UI constants, defaults, and timing values
  - `SIGN_PREDICTION_MIN_CONFIDENCE` controls prediction filtering
- `overlay_preferences.py`  
  - Read/write user preferences and defaults
- `overlay_logging.py`  
  - Session logging to JSON files (events + final transcript)
- `overlay_utils.py`  
  - Frame conversion, capture control, and process helpers

**Settings**
- `default_settings.json`  
  - Baseline configuration shipped with the app
- `user_preferences.json`  
  - User-specific overrides written at runtime
- `logs/`  
  - Session logs (one JSON file per run)

**Utilities**
- `misc/realtime_sender.py`  
  - Experimental sender scaffold (not used by the overlay runtime)
- `misc/predict_realtime.py`  
  - Helper script for testing predictions outside the UI
- `misc/run_signflow.bat`  
  - Convenience launcher for Windows

## Directory Layout

```
SignFlow-Core/
  overlay.py
  overlay_window.py
  overlay_panels.py
  overlay_capture.py
  overlay_selection.py
  overlay_preview.py
  overlay_hand_tracking.py
  overlay_voice.py
  overlay_constants.py
  overlay_logging.py
  overlay_preferences.py
  overlay_utils.py
  default_settings.json
  user_preferences.json
  requirements.txt
  logs/
  models/
    model.pkl
    model___.pkl
  misc/
    predict_realtime.py
    realtime_sender.py
    run_signflow.bat
```

## Key Tunables

- `SIGN_PREDICTION_MIN_CONFIDENCE` in `overlay_constants.py`  
  Controls the minimum confidence required before a prediction is accepted. Raising this value reduces "Uncertain" labels at the cost of fewer predictions.
- `CAPTURE_FLIP_HORIZONTAL` in `overlay_constants.py`  
  Default for the Flip Input advanced setting.

## Setup (Windows)

1. Create venv  
`py -3.10 -m venv venv`

2. Activate  
`venv\Scripts\activate`

3. Install dependencies  
`python -m pip install --upgrade pip setuptools wheel`  
`pip install -r requirements.txt`

4. Run  
`python overlay.py`  
`python overlay.py --random` (debug captions)

## Voice To Text Setup (SpeechRecognition)

SignFlow uses SpeechRecognition + PyAudio for microphone transcription.

1. Install dependencies  
`pip install SpeechRecognition PyAudio`

2. Toggle **Voice to Speech** in the control panel to start/stop transcription.

Optional:
- The default engine is Google Web Speech (requires internet).
- To use offline CMU Sphinx, install `pocketsphinx` and set `SIGNFLOW_STT_ENGINE=sphinx`.

## Notes

- Overlay and preview windows are always-on-top by design.
- Hand tracking requires MediaPipe; model inference requires `models/model.pkl`.
- Logs are written per session to `logs/` (debug sessions use `pseudo-` session IDs).
- Windows is the primary target for the overlay UI.

## Future Vision

SignFlow will mature into a reliable, low-latency sign recognition toolchain with stable model integration, validated performance, and a clear separation between capture, inference, and UI responsibilities.
