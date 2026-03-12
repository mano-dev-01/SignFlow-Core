# SignFlow

SignFlow is a Windows-first overlay app for capturing a screen region that contains a signing feed and previewing it live. It is designed to sit on top of calls/streams while collecting frames for a future ML pipeline.

Python version: `3.10`

## What It Does Now

- Always-on-top overlay window with controls
- Snipping-style region selection with dimmed screen + outline
- Live capture of the selected region (mss + QThread)
- Floating mini-player preview with status title and region label
- Toggleable �Current Status� panel with simulated system data
- Pause/resume preview updates (capture thread keeps running)
- Persistent user preferences

## What It Does Not Do Yet

- End-to-end sign recognition / inference pipeline
- Production-grade smoothing / token post-processing
- Full validation on diverse real-world signing conditions

## Runtime Flow (High Level)

1. Launch overlay
2. Click Capture Region
3. Select area, confirm with Enter/Space
4. Overlay returns, region highlights briefly
5. Capture thread streams frames
6. Mini-player shows live preview
7. Optional: show/hide status panel

## Project Structure

- Entry point
  - `overlay.py`
- Overlay UI + state
  - `overlay_window.py`
  - `overlay_panels.py`
- Capture + preview
  - `overlay_capture.py`
  - `overlay_selection.py`
  - `overlay_preview.py`
- Shared support
  - `overlay_constants.py`
  - `overlay_preferences.py`
  - `overlay_utils.py`
- Sender scaffold
  - `realtime_sender.py`
- Settings
  - `default_settings.json`
  - `user_preferences.json`
- Run helper
  - `run_signflow.bat`

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

## Notes

- Overlay and mini-player are always-on-top by design.
- The status panel is placeholder data and will be replaced by the ML pipeline later.
- Windows is the primary target for the overlay UI.
