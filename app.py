# ============================================================
#  GesturePilot AI – app.py
#  Main entry point: captures webcam frames, runs hand detection,
#  gesture recognition, keyboard control, and renders the HUD.
# ============================================================

import cv2
import time
import sys
import numpy as np

import config
from detector    import HandDetector
from gestures    import GestureRecognizer, GESTURE_UNKNOWN
from controller  import KeyController


# ──────────────────────────────────────────────────────────
# HUD / Overlay helpers
# ──────────────────────────────────────────────────────────

FONT = cv2.FONT_HERSHEY_SIMPLEX

# Emoji-like gesture labels for the overlay (plain ASCII fallback)
GESTURE_DISPLAY = {
    "FIST"       : "FIST       -> Brake      (LEFT)",
    "OPEN_PALM"  : "OPEN PALM  -> Accelerate (RIGHT)",
    "PEACE"      : "PEACE SIGN -> Pause      (P)",
    "UNKNOWN"    : "No gesture -> Release",
}

# Color per gesture for the info panel accent
GESTURE_COLOR = {
    "FIST"       : config.COLOR_DANGER,
    "OPEN_PALM"  : config.COLOR_SUCCESS,
    "PEACE"      : config.COLOR_WARNING,
    "UNKNOWN"    : (80, 80, 100),
}


def draw_hud(frame, fps: float, gesture: str, raw_gesture: str,
             confidence: float, active_key: str, sensitivity: int,
             calibration_mode: bool):
    """
    Render a dark futuristic HUD panel on the left side of the frame.
    All drawing is done in-place on *frame*.
    """
    h, w, _ = frame.shape
    panel_w  = 340

    # ── Semi-transparent dark panel ──────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, h),
                  config.COLOR_BG_PANEL, -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # ── Cyan accent border ────────────────────────────────────
    cv2.rectangle(frame, (0, 0), (panel_w, h),
                  config.COLOR_ACCENT, 1)
    cv2.line(frame, (panel_w, 0), (panel_w, h), config.COLOR_ACCENT, 2)

    # ── Title ─────────────────────────────────────────────────
    cv2.putText(frame, "GesturePilot AI", (12, 38), FONT,
                0.85, config.COLOR_ACCENT, 2, cv2.LINE_AA)
    cv2.putText(frame, "Hill Climb Racing Controller", (12, 62), FONT,
                config.FONT_SCALE_SMALL, config.COLOR_TEXT, 1, cv2.LINE_AA)

    # Divider
    cv2.line(frame, (12, 72), (panel_w - 12, 72), config.COLOR_ACCENT, 1)

    # ── FPS ───────────────────────────────────────────────────
    if config.SHOW_FPS:
        fps_color = config.COLOR_SUCCESS if fps >= 25 else config.COLOR_WARNING
        cv2.putText(frame, f"FPS : {fps:5.1f}", (12, 100), FONT,
                    config.FONT_SCALE_MEDIUM, fps_color, 1, cv2.LINE_AA)

    # ── Confidence ────────────────────────────────────────────
    if config.SHOW_CONFIDENCE:
        conf_pct = int(confidence * 100)
        conf_color = (config.COLOR_SUCCESS if conf_pct >= 80
                      else config.COLOR_WARNING if conf_pct >= 60
                      else config.COLOR_DANGER)
        cv2.putText(frame, f"CONF: {conf_pct:3d}%", (12, 128), FONT,
                    config.FONT_SCALE_MEDIUM, conf_color, 1, cv2.LINE_AA)
        # Mini confidence bar
        bar_x, bar_y, bar_h = 80, 118, 8
        bar_total_w = panel_w - bar_x - 20
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + bar_total_w, bar_y + bar_h),
                      (50, 50, 70), -1)
        filled_w = int(bar_total_w * confidence)
        cv2.rectangle(frame, (bar_x, bar_y),
                      (bar_x + filled_w, bar_y + bar_h),
                      conf_color, -1)

    # Divider
    cv2.line(frame, (12, 140), (panel_w - 12, 140), (40, 40, 60), 1)

    # ── Active gesture ────────────────────────────────────────
    if config.SHOW_GESTURE_LABEL:
        g_color = GESTURE_COLOR.get(gesture, (80, 80, 100))
        g_label = GESTURE_DISPLAY.get(gesture, gesture)

        cv2.putText(frame, "GESTURE", (12, 162), FONT,
                    config.FONT_SCALE_SMALL, config.COLOR_TEXT, 1, cv2.LINE_AA)
        cv2.putText(frame, gesture, (12, 188), FONT,
                    0.80, g_color, 2, cv2.LINE_AA)

        # Wrap long label
        short_label = g_label.split("->")[-1].strip() if "->" in g_label else g_label
        cv2.putText(frame, short_label, (12, 212), FONT,
                    config.FONT_SCALE_SMALL, g_color, 1, cv2.LINE_AA)

    # Divider
    cv2.line(frame, (12, 222), (panel_w - 12, 222), (40, 40, 60), 1)

    # ── Active key ────────────────────────────────────────────
    if config.SHOW_ACTIVE_KEY:
        key_color = (config.COLOR_SUCCESS if active_key != "None"
                     else (80, 80, 100))
        cv2.putText(frame, "ACTIVE KEY", (12, 244), FONT,
                    config.FONT_SCALE_SMALL, config.COLOR_TEXT, 1, cv2.LINE_AA)
        cv2.putText(frame, active_key, (12, 270), FONT,
                    0.80, key_color, 2, cv2.LINE_AA)

    # Divider
    cv2.line(frame, (12, 282), (panel_w - 12, 282), (40, 40, 60), 1)

    # ── Sensitivity ───────────────────────────────────────────
    cv2.putText(frame, f"SENSITIVITY: {sensitivity}/10", (12, 304), FONT,
                config.FONT_SCALE_SMALL, config.COLOR_TEXT, 1, cv2.LINE_AA)
    # Sensitivity bar
    sens_total_w = panel_w - 24
    cv2.rectangle(frame, (12, 310), (12 + sens_total_w, 320),
                  (50, 50, 70), -1)
    sens_filled = int(sens_total_w * sensitivity / 10)
    cv2.rectangle(frame, (12, 310), (12 + sens_filled, 320),
                  config.COLOR_ACCENT, -1)

    # ── Calibration mode banner ───────────────────────────────
    if calibration_mode:
        cv2.putText(frame, "! CALIBRATION MODE !", (12, 345), FONT,
                    config.FONT_SCALE_MEDIUM, config.COLOR_WARNING, 2,
                    cv2.LINE_AA)

    # ── Keybindings legend (bottom of panel) ──────────────────
    legend_items = [
        "Q  – Quit",
        "C  – Toggle Calibration",
        "+ / - – Sensitivity",
    ]
    base_y = h - (len(legend_items) * 22 + 10)
    for i, txt in enumerate(legend_items):
        cv2.putText(frame, txt, (12, base_y + i * 22), FONT,
                    config.FONT_SCALE_SMALL, (120, 120, 140), 1,
                    cv2.LINE_AA)

    # ── Gesture reference guide (top-right corner) ────────────
    ref_x = w - 280
    ref_y_start = 20
    cv2.putText(frame, "Gesture Guide", (ref_x, ref_y_start), FONT,
                config.FONT_SCALE_MEDIUM, config.COLOR_ACCENT, 1, cv2.LINE_AA)
    gestures_guide = [
        ("OPEN PALM",  "→ RIGHT (Accel)"),
        ("FIST",       "→ LEFT  (Brake)"),
        ("PEACE",      "→ P (Pause)"),
    ]
    for i, (g, action) in enumerate(gestures_guide):
        y = ref_y_start + 22 + i * 22
        cv2.putText(frame, f"{g:<12} {action}", (ref_x, y), FONT,
                    config.FONT_SCALE_SMALL, config.COLOR_TEXT, 1, cv2.LINE_AA)


# ──────────────────────────────────────────────────────────
# Main application
# ──────────────────────────────────────────────────────────

def main():
    # ── Initialise subsystems ─────────────────────────────────
    detector   = HandDetector()
    recognizer = GestureRecognizer()
    ctrl       = KeyController()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check CAMERA_INDEX in config.py.")
        sys.exit(1)

    print("=" * 56)
    print("  GesturePilot AI – Hand Gesture Game Controller")
    print("=" * 56)
    print("  Hand the webcam view towards your hand.")
    print("  Q = Quit   C = Calibration   +/- = Sensitivity")
    print("=" * 56)

    calibration_mode = config.CALIBRATION_MODE
    sensitivity      = config.GESTURE_SENSITIVITY

    # FPS tracking
    fps        = 0.0
    frame_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Failed to grab frame.")
            continue

        if config.FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)

        # ── Detection ─────────────────────────────────────────
        result = detector.process(frame)

        # ── Gesture recognition ───────────────────────────────
        gesture = recognizer.recognize(result)

        # ── Keyboard control ──────────────────────────────────
        ctrl.update(gesture)

        # ── Draw landmarks on frame ───────────────────────────
        if result is not None:
            detector.draw(frame, result)

        # ── FPS calculation ───────────────────────────────────
        now        = time.time()
        fps        = 1.0 / max(now - frame_time, 1e-9)
        frame_time = now

        # ── HUD overlay ───────────────────────────────────────
        draw_hud(
            frame       = frame,
            fps         = fps,
            gesture     = gesture,
            raw_gesture = recognizer.raw,
            confidence  = recognizer.confidence,
            active_key  = ctrl.active_key_name,
            sensitivity = sensitivity,
            calibration_mode = calibration_mode,
        )

        # ── Show ──────────────────────────────────────────────
        cv2.imshow("GesturePilot AI", frame)

        # ── Keyboard input (OpenCV window) ────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("[INFO] Quit requested.")
            break

        elif key == ord("c"):
            calibration_mode = not calibration_mode
            config.CALIBRATION_MODE = calibration_mode
            print(f"[INFO] Calibration mode: {'ON' if calibration_mode else 'OFF'}")

        elif key == ord("+") or key == ord("="):
            sensitivity = min(10, sensitivity + 1)
            config.GESTURE_SENSITIVITY = sensitivity
            print(f"[INFO] Sensitivity → {sensitivity}")

        elif key == ord("-"):
            sensitivity = max(1, sensitivity - 1)
            config.GESTURE_SENSITIVITY = sensitivity
            print(f"[INFO] Sensitivity → {sensitivity}")

    # ── Cleanup ───────────────────────────────────────────────
    ctrl.release_all()
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] GesturePilot AI shut down cleanly.")


if __name__ == "__main__":
    main()
