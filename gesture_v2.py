import cv2
import mediapipe as mp
import math
import numpy as np
import pyautogui
import time
import os
import webbrowser
from PIL import Image, ImageDraw, ImageFont

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# -------------------------------
# Screen Size
# -------------------------------
screenWidth, screenHeight = pyautogui.size()

# -------------------------------
# MediaPipe Hands
# -------------------------------
mpHands = mp.solutions.hands

hands = mpHands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

mpDraw = mp.solutions.drawing_utils

# -------------------------------
# Volume Setup
# -------------------------------
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]

# -------------------------------
# Camera
# -------------------------------
cap = cv2.VideoCapture(0)

# -------------------------------
# Screenshot state
# -------------------------------
palmDetected = False
palmStartTime = 0
screenshotTaken = False
SCREENSHOT_HOLD_SECONDS = 2

SAVE_DIR = os.path.join(os.getcwd(), "screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)

tipIds = [4, 8, 12, 16, 20]

# -------------------------------
# Gesture -> Website mapping
# Pattern order = [thumb, index, middle, ring, pinky]  (1 = up, 0 = down)
# -------------------------------
GESTURE_MAP = {
    (0, 1, 1, 0, 0): ("YouTube",   "https://youtube.com"),
    (1, 0, 0, 0, 1): ("WhatsApp",  "https://web.whatsapp.com"),
    (1, 0, 0, 0, 0): ("Google",    "https://google.com"),
    (0, 1, 0, 0, 1): ("Instagram", "https://instagram.com"),
    (0, 1, 1, 1, 0): ("GitHub",    "https://github.com"),
}

GESTURE_HOLD_SECONDS = 1.5
gestureDetected = None
gestureStartTime = 0
gestureLaunched = False

showLegend = True

# Emoji label per gesture pattern
EMOJI_LABELS = {
    (0, 1, 1, 0, 0): "\u270C\ufe0f",   # Peace sign
    (1, 0, 0, 0, 1): "\U0001F919",     # Call-me hand
    (1, 0, 0, 0, 0): "\U0001F44D",     # Thumbs up
    (0, 1, 0, 0, 1): "\U0001F91F",     # Rock sign
    (0, 1, 1, 1, 0): "3\ufe0f\u20e3",  # Three fingers (keycap 3)
}

# Try to load a color-emoji-capable font (Windows default). Falls back to
# a plain text label if the font isn't found on this machine.
_EMOJI_FONT_PATH_CANDIDATES = [
    r"C:\Windows\Fonts\seguiemj.ttf",   # Windows
    "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux (Noto)
]

_emoji_font = None
_text_font = None
for _path in _EMOJI_FONT_PATH_CANDIDATES:
    if os.path.exists(_path):
        try:
            _emoji_font = ImageFont.truetype(_path, 32)
            break
        except Exception:
            pass

try:
    _text_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 18)
except Exception:
    _text_font = ImageFont.load_default()

# -------------------------------
# Helper: draw the legend panel (with real emoji, via PIL)
# -------------------------------
def draw_legend(frame):
    panel_w, panel_h = 300, 30 + len(GESTURE_MAP) * 40
    x0, y0 = frame.shape[1] - panel_w - 10, 20

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), cv2.FILLED)
    frame[:] = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    # Convert to PIL to draw text/emoji, then convert back
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    draw.text((x0 + 10, y0 + 5), "Gestures (press 'h' to hide)", font=_text_font, fill=(0, 255, 255))

    row_y = y0 + 35
    for pattern, (name, _) in GESTURE_MAP.items():
        emoji = EMOJI_LABELS.get(pattern, "")
        if _emoji_font is not None:
            draw.text((x0 + 10, row_y), emoji, font=_emoji_font, embedded_color=True)
        text = f"-> {name}"
        draw.text((x0 + 55, row_y + 6), text, font=_text_font, fill=(255, 255, 255))
        row_y += 40

    frame[:] = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape

    imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mpDraw.draw_landmarks(frame, handLms, mpHands.HAND_CONNECTIONS)

            lmList = []
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])

            if len(lmList) != 0:

                # -----------------------------
                # Finger state detection
                # -----------------------------
                fingers = []

                # Thumb (compare x-position, since thumb moves sideways)
                if lmList[4][1] > lmList[3][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

                # Index, Middle, Ring, Pinky
                for id in range(1, 5):
                    if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                fingersTuple = tuple(fingers)

                # -----------------------------
                # Thumb + Index tip positions
                # -----------------------------
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]

                cv2.circle(frame, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                cv2.circle(frame, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                length = math.hypot(x2 - x1, y2 - y1)

                vol = np.interp(length, [20, 220], [minVol, maxVol])
                volPer = np.interp(length, [20, 220], [0, 100])
                volBar = np.interp(length, [20, 220], [400, 150])

                currentTime = time.time()

                # -----------------------------
                # Priority order: screenshot (open palm) > website gesture > volume
                # -----------------------------
                if sum(fingers) >= 4:
                    # ---- Screenshot (open palm) ----
                    gestureDetected = None
                    gestureLaunched = False

                    if not palmDetected:
                        palmDetected = True
                        palmStartTime = currentTime
                        screenshotTaken = False
                    else:
                        remaining = max(0, SCREENSHOT_HOLD_SECONDS - (currentTime - palmStartTime))
                        cv2.putText(frame, f"Screenshot in {remaining:.1f}s", (120, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                        if currentTime - palmStartTime >= SCREENSHOT_HOLD_SECONDS and not screenshotTaken:
                            screenshot = pyautogui.screenshot()
                            filename = os.path.join(SAVE_DIR, f"screenshot_{int(currentTime)}.png")
                            screenshot.save(filename)
                            screenshotTaken = True
                            cv2.putText(frame, "Screenshot saved!", (120, 90),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                elif fingersTuple in GESTURE_MAP:
                    # ---- Website launch gesture ----
                    palmDetected = False
                    screenshotTaken = False

                    name, url = GESTURE_MAP[fingersTuple]

                    if gestureDetected != fingersTuple:
                        gestureDetected = fingersTuple
                        gestureStartTime = currentTime
                        gestureLaunched = False
                    else:
                        remaining = max(0, GESTURE_HOLD_SECONDS - (currentTime - gestureStartTime))
                        cv2.putText(frame, f"Opening {name} in {remaining:.1f}s", (120, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                        if currentTime - gestureStartTime >= GESTURE_HOLD_SECONDS and not gestureLaunched:
                            webbrowser.open(url)
                            gestureLaunched = True
                            cv2.putText(frame, f"Opened {name}!", (120, 90),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                else:
                    # ---- Volume control (only index finger up = pinch mode) ----
                    palmDetected = False
                    screenshotTaken = False
                    gestureDetected = None
                    gestureLaunched = False

                    if fingers[1] == 1 and sum(fingers) == 1:
                        volume.SetMasterVolumeLevel(vol, None)

                # -----------------------------
                # Volume Bar UI
                # -----------------------------
                cv2.rectangle(frame, (50, 150), (85, 400), (255, 0, 0), 3)
                cv2.rectangle(frame, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
                cv2.putText(frame, f'{int(volPer)}%', (35, 430),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    else:
        palmDetected = False
        screenshotTaken = False
        gestureDetected = None
        gestureLaunched = False

    if showLegend:
        draw_legend(frame)

    cv2.imshow("Hand Gesture Control", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('h'):
        showLegend = not showLegend

cap.release()
cv2.destroyAllWindows()