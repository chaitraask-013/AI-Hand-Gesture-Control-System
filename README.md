# AI Hand Gesture Control System

Control your PC using just hand gestures! Built with Python, OpenCV, and MediaPipe. It uses your webcam to detect your hand and lets you control volume, take screenshots, and open websites — no mouse or keyboard needed.

## What it can do

- Control system volume by pinching your thumb and index finger
- Take a screenshot by holding an open palm for 2 seconds
- Open websites by making certain hand gestures:
  - ✌️ Index + Middle finger up → YouTube
  - 🤙 Thumb + Pinky up → WhatsApp Web
  - 👍 Thumb up → Google
  - 🤟 Index + Pinky up → Instagram
  - 3️⃣ Index + Middle + Ring up → GitHub
- Press `h` to show/hide a gesture guide on screen
- Press `q` to quit

## Built with

- OpenCV
- MediaPipe
- PyAutoGUI (for screenshots)
- pycaw (for volume control, Windows only)
- Pillow, NumPy

## How to run it

1. Clone this repo
   ```bash
   git clone https://github.com/chaitraask-013/AI-Hand-Gesture-Control-System.git
   cd AI-Hand-Gesture-Control-System
   ```

2. Create a virtual environment and activate it
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required packages
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app
   ```bash
   python gesture_v2.py
   ```

Note: Volume control only works on Windows since it uses `pycaw`.

## Files

- `app.py` – entry point
- `gesture_v2.py` – main gesture detection logic
- `requirements.txt` – dependencies
- `screenshots/` – screenshots get saved here automatically

## Note

This is a project I'm still improving. Feel free to try it out and suggest changes.
