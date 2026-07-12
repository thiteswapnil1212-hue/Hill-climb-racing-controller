# ============================================================
#  GesturePilot AI – gestures.py
#  Translates a HandResult into a named gesture string.
#  Also implements gesture smoothing / debouncing so that
#  brief or jittery detections don't fire the keyboard.
# ============================================================

from collections import deque
import config
from detector import HandResult


# ──────────────────────────────────────────────────────────
# Gesture name constants  (keep in sync with config.KEY_MAP)
# ──────────────────────────────────────────────────────────
GESTURE_FIST        = "FIST"
GESTURE_OPEN_PALM   = "OPEN_PALM"
GESTURE_PEACE       = "PEACE"
GESTURE_UNKNOWN     = "UNKNOWN"


class GestureRecognizer:
    """
    Classifies a HandResult into one of the supported gesture names
    and smooths the output to prevent jitter.

    Call recognize(result) each frame to get the smoothed gesture.
    """

    def __init__(self):
        # Ring-buffer that stores the last N raw gesture names
        self._buffer       = deque(maxlen=config.GESTURE_BUFFER_SIZE)
        # Current debounce counter for the candidate gesture
        self._candidate    = None
        self._streak       = 0           # how many frames in a row we've seen candidate
        # The confirmed (smoothed) gesture that callers read
        self.current       = GESTURE_UNKNOWN
        # Raw gesture from the most recent frame (before smoothing)
        self.raw           = GESTURE_UNKNOWN
        # Confidence of the last detected hand (0-1)
        self.confidence    = 0.0

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def recognize(self, result: HandResult | None) -> str:
        """
        Given a HandResult (or None if no hand found), return the
        smoothed gesture string.  Also updates self.confidence.
        """
        if result is None:
            # No hand → reset everything
            self._reset()
            self.confidence = 0.0
            return self.current

        self.confidence = result.confidence

        # Classify raw gesture from landmark geometry
        raw_gesture = self._classify(result)
        self.raw    = raw_gesture
        self._buffer.append(raw_gesture)

        # ── Smoothing / debounce logic ────────────────────────
        # Adjust required streak based on sensitivity (1–10).
        # Higher sensitivity ⇒ fewer frames needed ⇒ more responsive
        # but potentially more jitter.
        required_streak = self._debounce_frames()

        if raw_gesture == self._candidate:
            self._streak += 1
        else:
            self._candidate = raw_gesture
            self._streak    = 1

        if self._streak >= required_streak:
            self.current = self._candidate

        return self.current

    # ----------------------------------------------------------
    # Gesture classification rules
    # ----------------------------------------------------------

    def _classify(self, r: HandResult) -> str:
        index_up = r.finger_extended(r.INDEX_TIP, r.INDEX_PIP)
        middle_up = r.finger_extended(r.MIDDLE_TIP, r.MIDDLE_PIP)
        ring_up = r.finger_extended(r.RING_TIP, r.RING_PIP)
        pinky_up = r.finger_extended(r.PINKY_TIP, r.PINKY_PIP)
        thumb_ext = r.thumb_extended()

        # ✋ Open Palm
        if thumb_ext and index_up and middle_up and ring_up and pinky_up:
            return GESTURE_OPEN_PALM

        # ✌️ Peace
        if index_up and middle_up and not ring_up and not pinky_up:
            return GESTURE_PEACE

        # ✊ Fist
        if (not thumb_ext and
            not index_up and
            not middle_up and
            not ring_up and
            not pinky_up):
            return GESTURE_FIST

        return GESTURE_UNKNOWN
        # ── ✋ Open Palm ────────────────────────────────────────
        # All four fingers extended
        if fingers_up_count == 4:
            return GESTURE_OPEN_PALM

        # ── ✊ Closed Fist ──────────────────────────────────────
        # No fingers extended AND thumb is NOT extended
        if fingers_up_count == 0 and not thumb_ext:
            return GESTURE_FIST

        return GESTURE_UNKNOWN

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _debounce_frames(self) -> int:
        """
        Map sensitivity (1–10) to required streak length.
        sensitivity=1  → 9 frames (very strict)
        sensitivity=10 → 1 frame  (instant)
        """
        sens = max(1, min(10, config.GESTURE_SENSITIVITY))
        # Linear interpolation: frames = 10 - sens + 1
        return 10 - sens + 1

    def _reset(self):
        self._buffer.clear()
        self._candidate = None
        self._streak    = 0
        self.current    = GESTURE_UNKNOWN
        self.raw        = GESTURE_UNKNOWN
