# SignFlow

SignFlow is a real-time sign language to English captioning system with a floating caption overlay.

## Current Status

The current implementation is focused on a stable, demo-ready overlay UI shell.

Implemented now:
- Windows-only PyQt5 desktop overlay UI
- Always-on-top, frameless caption overlay
- Expand/collapse secondary settings panel
- Persistent settings via JSON

Not connected yet:
- Live ML/caption pipeline integration

Python version: 3.10

## Overlay Features

- Frameless, always-on-top overlay window
- Rounded, minimal dark UI
- Clickable overlay (not click-through)
- Corner placement:
  - Top Left
  - Top Right
  - Bottom Left
  - Bottom Right
- Expand/collapse settings panel with animation
- Caption display area with placeholder text
- Quit button and panel toggle button

## Settings Panel

Available controls:

- Caption font size (`16-48`)
- Overlay opacity (`50%-100%`)
- Show raw tokens (toggle)
- Freeze captions on detection loss (toggle)
- Enable LLM smoothing (toggle)
- Model selection (`Local Small`, `Local Medium`)
- Show latency (toggle)
- Overlay corner selection

## Restart-Based Font Apply

Font size changes are deferred:
- Moving the font slider updates a pending preference only.
- Click `Restart` to relaunch and apply the new font size.
- This avoids runtime dimension shifts while testing layout stability.

## Preferences

Settings are persisted in project root:

- `default_settings.json`: default settings source
- `user_preferences.json`: user settings loaded on startup

`Reset Preferences To Default` restores defaults and restarts the app.

## Opacity Behavior

- Slider range is fixed at `50%` to `100%`.
- At `100%`, the overlay is fully opaque.

## Windows

1. Create virtual environment:
`py -3.10 -m venv venv`

2. Activate virtual environment:
`venv\Scripts\activate`

3. Install dependencies:
`python -m pip install --upgrade pip setuptools wheel`
`pip install -r requirements.txt`

4. Run:
`run_signflow.bat`

Manual run (two terminals):
Terminal 1: `python overlay.py`
Terminal 2: `python realtime_sender.py`

## Linux

Overlay UI is Windows-only. Linux instructions below are for the broader project flow and may not support the current overlay behavior.

1. Create virtual environment:
`python3.10 -m venv venv`

2. Activate virtual environment:
`source venv/bin/activate`

3. Install dependencies:
`python -m pip install --upgrade pip setuptools wheel`
`pip install -r requirements.txt`

4. Run (two terminals):
Terminal 1: `python overlay.py`
Terminal 2: `python realtime_sender.py`
