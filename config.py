# ============================================================
#  GesturePilot AI – config.py
#  Central configuration: tweak these values without touching
#  any other file.
# ============================================================

# ──────────────────────────────────────────────────────────
# Camera / Vision
# ──────────────────────────────────────────────────────────
CAMERA_INDEX        = 0          # Webcam index (0 = default)
FRAME_WIDTH         = 1280       # Capture width  (px)
FRAME_HEIGHT        = 720        # Capture height (px)
FLIP_HORIZONTAL     = True       # Mirror the feed (feels natural)

# ──────────────────────────────────────────────────────────
# MediaPipe Hand Detector
# ──────────────────────────────────────────────────────────
MAX_HANDS           = 1          # Only track one hand
DETECTION_CONFIDENCE  = 0.75     # Min confidence to detect a hand
TRACKING_CONFIDENCE   = 0.75     # Min confidence to keep tracking

# ──────────────────────────────────────────────────────────
# Gesture Smoothing / Debouncing
# ──────────────────────────────────────────────────────────
# A gesture must appear this many consecutive frames before
# it is accepted – prevents jitter / accidental keypresses.
GESTURE_DEBOUNCE_FRAMES = 5

# How many past gestures to keep in the smoothing buffer.
GESTURE_BUFFER_SIZE     = 7

KEY_MAP = {
    "OPEN_PALM": "right",
    "FIST": "left",
    "PEACE": "p",
    "UNKNOWN": None,
}

SHOW_FPS            = True
SHOW_LANDMARKS      = True
SHOW_GESTURE_LABEL  = True
SHOW_CONFIDENCE     = True
SHOW_ACTIVE_KEY     = True

COLOR_BG_PANEL      = (15,  15,  25)     
COLOR_ACCENT        = (0,  210, 255)     
COLOR_SUCCESS       = (0,  230, 118)    
COLOR_WARNING       = (0,  165, 255)     
COLOR_DANGER        = (60,  20, 220)     
COLOR_TEXT          = (220, 220, 240)    
COLOR_LANDMARK      = (0,  210, 255)     
COLOR_CONNECTION    = (100, 230, 100)    
OLOR_BOUNDING_BOX  = (0,  210, 255)    

FONT_SCALE_LARGE    = 1.0
FONT_SCALE_MEDIUM   = 0.65
FONT_SCALE_SMALL    = 0.50
FONT_THICKNESS      = 2

# ──────────────────────────────────────────────────────────
# Calibration Mode
# ──────────────────────────────────────────────────────────
CALIBRATION_MODE    = False     # Toggle with 'C' key at runtime
CALIBRATION_FRAMES  = 60        # Frames per pose during calibration

# ──────────────────────────────────────────────────────────
# Sensitivity  (1 = strictest, 10 = most lenient)
# ──────────────────────────────────────────────────────────
GESTURE_SENSITIVITY = 5         # Adjustable 1-10 at runtime (+/- keys)
