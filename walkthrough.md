# GesturePilot AI — Build Walkthrough

## ✅ All Checks Passed

| Check | Result |
|---|---|
| Syntax check (AST) — all 5 modules | ✅ Pass |
| `config`, `gestures`, `controller` imports | ✅ Pass |
| `detector` (MediaPipe) import | ✅ Pass |
| OpenCV 4.13.0 | ✅ Installed |
| MediaPipe 0.10.35 | ✅ Installed |
| NumPy 2.4.3 | ✅ Installed |
| pynput 1.8.2 | ✅ Installed (fresh) |
| Git first commit | ✅ `c18af27` |

---

## 📁 Project Structure

```
hillclimbcontroller/
├── app.py          ← Main loop + dark futuristic HUD
├── config.py       ← All settings in one place
├── detector.py     ← MediaPipe hand detection wrapper
├── gestures.py     ← Gesture rules + debounce smoothing
├── controller.py   ← pynput keyboard state machine
├── requirements.txt
├── README.md       ← Full GitHub-ready README
├── .gitignore
├── Screen Recording 2026-07-11 223204.mp4   ← Demo recording
└── Screen Recording 2026-07-12 121530.mp4   ← Demo recording
```

---

## 🎮 Gesture → Key Mapping

| Gesture | Key | Game Action |
|:---:|:---:|---|
| 👍 Thumb Up | `→` Right | Accelerate |
| ✊ Fist | `←` Left | Brake |
| ✋ Open Palm | *(release)* | Release all |
| ✌️ Peace | `P` | Pause |
| 👎 Thumb Down | `R` | Restart |

---

## 🏗 Architecture

```
Webcam Frame
     │
     ▼
HandDetector.process()        ← MediaPipe: 21 landmarks, confidence, bbox
     │  HandResult
     ▼
GestureRecognizer.recognize() ← Geometric rules + debounce ring-buffer
     │  gesture string
     ▼
KeyController.update()        ← pynput: hold / tap / release keys
     │  active_key_name
     ▼
draw_hud()                    ← OpenCV: FPS, confidence bar, gesture, key, sensitivity
     │
     ▼
cv2.imshow()
```

---

## 🔑 Key Design Decisions

### Gesture Smoothing
A **ring-buffer debounce** (`deque`) requires a gesture to appear in N consecutive frames before it's accepted. N is derived from `GESTURE_SENSITIVITY` (1–10):  
`required_streak = 10 - sensitivity + 1`  
This prevents jitter without adding input lag for deliberate gestures.

### Key Holding vs Tapping
- **Held gestures** (Thumb Up → Right, Fist → Left): `pynput.press()` is called once; key stays down until the gesture changes.
- **Tap gestures** (Peace → P, Thumb Down → R): `press()` + `release()` fire immediately on gesture change — not held.
- **Open Palm / Unknown**: all held keys are released via `_release_all()`.

### Modular Architecture
Each concern is fully isolated:
- Changing game → edit only `KEY_MAP` in `config.py`
- Tweaking detection → edit only `DETECTION_CONFIDENCE` in `config.py`
- Adding a new gesture → add a rule in `gestures.py` + entry in `config.KEY_MAP`

---

## 🚀 How to Run

```bash
# From the project directory
python app.py
```

### Runtime Hotkeys (in the OpenCV window)
| Key | Action |
|---|---|
| `Q` | Quit |
| `C` | Toggle calibration mode |
| `+` / `=` | Increase sensitivity |
| `-` | Decrease sensitivity |

---

## 💡 Tips for Best Results

1. **Good lighting** — MediaPipe is lighting-sensitive; face a window or lamp
2. **Plain background** — A contrasting background improves landmark detection
3. **Keep hand within frame** — Detection drops if hand exits the camera view
4. **Sensitivity tuning** — Start at 5, increase if gestures feel sluggish, decrease if jittery
5. **Window position** — GesturePilot AI window can be small; your game window gets the key events globally via pynput
