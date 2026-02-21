# SignFlow

SignFlow is a real-time sign language to English captioning system with a floating caption overlay.

Python version: 3.10

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