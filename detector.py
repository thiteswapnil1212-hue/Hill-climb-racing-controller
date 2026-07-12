# ============================================================
#  GesturePilot AI – detector.py
#  Wraps MediaPipe Hands to provide per-frame hand detection,
#  landmark extraction, and bounding-box calculation.
# ============================================================

import cv2
import mediapipe as mp
import math
import config


class HandDetector:
    """
    Wraps MediaPipe Hands for single-hand detection.

    Usage:
        detector = HandDetector()
        results  = detector.process(frame)          # returns HandResult or None
    """

    def __init__(self):
        self._mp_hands    = mp.solutions.hands
        self._mp_drawing  = mp.solutions.drawing_utils
        self._mp_styles   = mp.solutions.drawing_styles

        # Initialize MediaPipe Hands
        self.hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MAX_HANDS,
            min_detection_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE,
        )

        # Custom drawing specs for a futuristic look
        self._landmark_spec = self._mp_drawing.DrawingSpec(
            color=config.COLOR_LANDMARK,
            thickness=2,
            circle_radius=4,
        )
        self._connection_spec = self._mp_drawing.DrawingSpec(
            color=config.COLOR_CONNECTION,
            thickness=2,
        )

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def process(self, bgr_frame):
        """
        Detect a hand in *bgr_frame* and return a HandResult object,
        or None if no hand is found.

        The frame is NOT modified – drawing is handled separately.
        """
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False          # slight performance gain
        raw = self.hands.process(rgb)
        rgb.flags.writeable = True

        if not raw.multi_hand_landmarks:
            return None                       # no hand detected

        # Take the first hand only (MAX_HANDS = 1)
        hand_lms   = raw.multi_hand_landmarks[0]
        handedness = raw.multi_handedness[0]
        confidence = handedness.classification[0].score

        landmarks  = self._extract_landmarks(hand_lms, bgr_frame)
        bbox       = self._bounding_box(landmarks, bgr_frame)

        return HandResult(
            landmarks=landmarks,
            raw_landmarks=hand_lms,
            bounding_box=bbox,
            confidence=confidence,
            label=handedness.classification[0].label,  # "Left" / "Right"
        )

    def draw(self, frame, result: "HandResult"):
        """
        Overlay landmarks, connections, and bounding box on *frame*.
        Modifies the frame in place.
        """
        if result is None:
            return

        if config.SHOW_LANDMARKS:
            self._mp_drawing.draw_landmarks(
                frame,
                result.raw_landmarks,
                self._mp_hands.HAND_CONNECTIONS,
                self._landmark_spec,
                self._connection_spec,
            )

        # Draw bounding box
        x1, y1, x2, y2 = result.bounding_box
        cv2.rectangle(frame, (x1, y1), (x2, y2),
                      config.COLOR_BOUNDING_BOX, 2)

    # ----------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------

    @staticmethod
    def _extract_landmarks(hand_lms, frame):
        """
        Convert normalized MediaPipe landmarks to absolute pixel
        coordinates.  Returns a list of 21 (x, y) tuples.
        """
        h, w, _ = frame.shape
        return [
            (int(lm.x * w), int(lm.y * h))
            for lm in hand_lms.landmark
        ]

    @staticmethod
    def _bounding_box(landmarks, frame, padding: int = 20):
        """
        Compute an axis-aligned bounding box around all landmarks.
        Returns (x1, y1, x2, y2) clamped to frame dimensions.
        """
        h, w, _ = frame.shape
        xs = [p[0] for p in landmarks]
        ys = [p[1] for p in landmarks]

        x1 = max(0,   min(xs) - padding)
        y1 = max(0,   min(ys) - padding)
        x2 = min(w,   max(xs) + padding)
        y2 = min(h,   max(ys) + padding)

        return (x1, y1, x2, y2)


# ──────────────────────────────────────────────────────────
# Data class returned by HandDetector.process()
# ──────────────────────────────────────────────────────────

class HandResult:
    """Immutable snapshot of one detected hand in a single frame."""

    # MediaPipe landmark IDs (for readability in gestures.py)
    WRIST             = 0
    THUMB_CMC         = 1
    THUMB_MCP         = 2
    THUMB_IP          = 3
    THUMB_TIP         = 4
    INDEX_MCP         = 5
    INDEX_PIP         = 6
    INDEX_DIP         = 7
    INDEX_TIP         = 8
    MIDDLE_MCP        = 9
    MIDDLE_PIP        = 10
    MIDDLE_DIP        = 11
    MIDDLE_TIP        = 12
    RING_MCP          = 13
    RING_PIP          = 14
    RING_DIP          = 15
    RING_TIP          = 16
    PINKY_MCP         = 17
    PINKY_PIP         = 18
    PINKY_DIP         = 19
    PINKY_TIP         = 20

    def __init__(self, landmarks, raw_landmarks, bounding_box,
                 confidence, label):
        self.landmarks     = landmarks       # list of 21 (x, y) tuples
        self.raw_landmarks = raw_landmarks   # mediapipe NormalizedLandmarkList
        self.bounding_box  = bounding_box    # (x1, y1, x2, y2)
        self.confidence    = confidence      # float 0-1
        self.label         = label           # "Left" / "Right"

    # ----------------------------------------------------------
    # Convenience geometry helpers used by gestures.py
    # ----------------------------------------------------------

    def get(self, landmark_id: int):
        """Return (x, y) pixel coordinates for a landmark ID."""
        return self.landmarks[landmark_id]

    def distance(self, id_a: int, id_b: int) -> float:
        """Euclidean pixel distance between two landmarks."""
        ax, ay = self.landmarks[id_a]
        bx, by = self.landmarks[id_b]
        return math.hypot(ax - bx, ay - by)

    def finger_extended(self, tip_id: int, pip_id: int) -> bool:
        """
        Returns True if a finger is 'up' (extended).
        Checks whether the tip is above the PIP joint (smaller y = higher up).
        Works for all four fingers.  Thumb handled separately.
        """
        tip_y = self.landmarks[tip_id][1]
        pip_y = self.landmarks[pip_id][1]
        return tip_y < pip_y

    def thumb_extended(self) -> bool:
        """
        Thumb is extended when its tip is to the left of the IP joint
        (for a right hand visible in mirrored view).
        Uses horizontal distance to be robust to hand rotation.
        """
        tip  = self.landmarks[self.THUMB_TIP]
        ip   = self.landmarks[self.THUMB_IP]
        mcp  = self.landmarks[self.THUMB_MCP]
        wrist = self.landmarks[self.WRIST]

        # Distance-based: thumb tip is far from the palm center
        palm_center = self.landmarks[self.MIDDLE_MCP]
        d_tip   = math.hypot(tip[0]  - palm_center[0], tip[1]  - palm_center[1])
        d_mcp   = math.hypot(mcp[0]  - palm_center[0], mcp[1]  - palm_center[1])
        return d_tip > d_mcp * 1.3     # tip is significantly farther than MCP

    def thumb_pointing_up(self) -> bool:
        """True if thumb tip is substantially above the wrist."""
        tip   = self.landmarks[self.THUMB_TIP]
        wrist = self.landmarks[self.WRIST]
        return (wrist[1] - tip[1]) > 60   # tip is ≥ 60 px above wrist

    def thumb_pointing_down(self) -> bool:
        """True if thumb tip is substantially below the wrist."""
        tip   = self.landmarks[self.THUMB_TIP]
        wrist = self.landmarks[self.WRIST]
        return (tip[1] - wrist[1]) > 60   # tip is ≥ 60 px below wrist
