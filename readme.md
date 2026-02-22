# SignFlow

SignFlow is a real-time sign language to English captioning project, built around a live desktop overlay experience for calls, streams, and demos.

Python version: `3.10`

## Current Status

The project currently has a working Windows overlay application and sender-side scaffolding.

What is implemented now:
- Stable PyQt5 overlay window (`overlay.py`) for live caption display
- Always-on-top, frameless overlay UX designed for in-call usage
- Configurable settings panel with persistent user preferences
- Restart-safe settings flow for layout-sensitive controls
- Companion sender entrypoint (`realtime_sender.py`) for pipeline-side integration

What is not complete yet:
- End-to-end production inference pipeline integration
- Finalized smoothing/post-processing logic
- Full system validation across varied real-world signing conditions

## Near-Term Roadmap

Planned next steps:
- Connect overlay to finalized real-time recognition outputs
- Improve temporal stability and caption quality during fast signing
- Add robust latency and drop-handling behavior in live sessions
- Expand evaluation and benchmarking on representative datasets
- Harden packaging and startup flow for hackathon/demo deployment

## Project Structure

- `overlay.py`: Windows desktop overlay UI (PyQt5)
- `realtime_sender.py`: runtime sender/bridge script
- `default_settings.json`: baseline overlay settings
- `user_preferences.json`: persisted per-user settings
- `run_signflow.bat`: Windows run helper

## Setup (Windows)

1. Create venv  
`py -3.10 -m venv venv`

2. Activate  
`venv\Scripts\activate`

3. Install dependencies  
`python -m pip install --upgrade pip setuptools wheel`  
`pip install -r requirements.txt`

4. Run  
`run_signflow.bat`

Manual run (two terminals):
- Terminal 1: `python overlay.py`
- Terminal 2: `python realtime_sender.py`

## Notes on Linux

Linux setup commands can work for non-UI components, but the current overlay target is Windows-first.
