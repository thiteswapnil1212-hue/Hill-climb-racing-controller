# ============================================================
#  GesturePilot AI – controller.py
#  Translates smoothed gesture strings into keyboard actions.
#  Uses pynput so keys are truly held down (not just tapped).
# ============================================================

from pynput.keyboard import Key, Controller as KeyboardController
import config
from gestures import (
    GESTURE_FIST, GESTURE_OPEN_PALM, GESTURE_PEACE, GESTURE_UNKNOWN,
)


# Mapping from pynput key string → pynput Key object
_KEY_LOOKUP = {
    "right" : Key.right,
    "left"  : Key.left,
    "up"    : Key.up,
    "down"  : Key.down,
    "space" : Key.space,
    "enter" : Key.enter,
    "esc"   : Key.esc,
    "p"     : "p",     # Regular character keys stay as strings
    "r"     : "r",
    "q"     : "q",
}


def _resolve_key(key_str: str | None):
    """Convert a config key name string to a pynput-compatible key."""
    if key_str is None:
        return None
    return _KEY_LOOKUP.get(key_str.lower(), key_str)


class KeyController:
    """
    Manages keyboard state: which keys are currently held down.

    Rules:
    - Arrow-type keys (right/left) are *held* while gesture is active.
    - Character keys (p, r) are *tapped* (pressed and immediately released).
    - OPEN_PALM releases all held keys.
    - If no hand is detected (gesture = UNKNOWN), all keys are released.
    """

    # Gestures that should be HELD (continuous press)
    _HOLD_GESTURES = {GESTURE_FIST, GESTURE_OPEN_PALM}
    # Gestures that should be TAPPED once
    _TAP_GESTURES  = {GESTURE_PEACE}

    def __init__(self):
        self._kb          = KeyboardController()
        self._held_keys   = set()      # currently held-down keys
        self._last_gesture = None      # to detect gesture changes
        self.active_key_name = "None"  # human-readable label for UI

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def update(self, gesture: str):
        """
        Called once per frame with the smoothed gesture string.
        Updates keyboard state accordingly.
        """
        # Always resolve the key string and key object first
        key_str = config.KEY_MAP.get(gesture)
        key     = _resolve_key(key_str)

        # Update the active key name for the UI regardless of whether we return early
        if gesture == GESTURE_UNKNOWN:
            self.active_key_name = "None"
        elif gesture in self._HOLD_GESTURES and key is not None:
            self.active_key_name = str(key_str).upper()
        elif gesture in self._TAP_GESTURES and key is not None:
            self.active_key_name = f"{str(key_str).upper()} (tap)"
        else:
            self.active_key_name = "None"

        # If gesture hasn't changed, we don't need to press/release keys again
        if gesture == self._last_gesture:
            return

        self._last_gesture = gesture

        # Always release previously held keys when gesture changes
        self._release_all()

        # Execute the actual key press
        if gesture in self._HOLD_GESTURES and key is not None:
            self._press_hold(key)
        elif gesture in self._TAP_GESTURES and key is not None:
            self._tap(key)


    def release_all(self):
        """Public method – call on program exit or hand loss."""
        self._release_all()
        self.active_key_name = "None"
        self._last_gesture   = None

    # ----------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------

    def _press_hold(self, key):
        """Hold a key down (will stay pressed until _release_all)."""
        if key not in self._held_keys:
            self._kb.press(key)
            self._held_keys.add(key)

    def _tap(self, key):
        """Press and immediately release a key (one-shot action)."""
        self._kb.press(key)
        self._kb.release(key)

    def _release_all(self):
        """Release every currently held key."""
        for k in list(self._held_keys):
            try:
                self._kb.release(k)
            except Exception:
                pass
        self._held_keys.clear()
