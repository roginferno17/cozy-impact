"""
Calibration / debug tool for flik detection.

Usage:
    python calibrate.py path\\to\\screenshot.png   # test against an image
    python calibrate.py                            # live: grab screen in 3s

It prints the gold-pixel and choice-pixel counts (so you can tune the
thresholds in flik/config.py), reports the detection decision, and writes
`calibrate_out.png` with the ROIs drawn on top so you can confirm the regions
line up with your dialogue UI.
"""

from __future__ import annotations

import sys
import time

import cv2
import numpy as np

from flik.config import CONFIG, Roi
from flik.capture import ScreenCapture
from flik.detect import detect


def _roi_to_px(roi: Roi, w: int, h: int):
    return (int(roi.x1 * w), int(roi.y1 * h), int(roi.x2 * w), int(roi.y2 * h))


def main() -> None:
    cap = ScreenCapture()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        frame = cv2.imread(path)
        if frame is None:
            print(f"could not read image: {path}")
            return
        print(f"loaded {path}  ({frame.shape[1]}x{frame.shape[0]})")
    else:
        print("live mode: switch to the game, grabbing in 3s...")
        time.sleep(3.0)
        frame = cap.grab()
        print(f"grabbed screen ({frame.shape[1]}x{frame.shape[0]})")

    result = detect(frame, cap, CONFIG)

    print("-" * 48)
    print(f"gold pixels (name ROI)  : {result.gold_pixels:>6}  "
          f"(threshold {CONFIG.gold_pixel_min}) -> hit={result.name_hit}")
    print(f"gold fill (name ROI)    : {result.gold_fill:>6.1%}  "
          f"(max {CONFIG.gold_fill_max:.0%})")
    print(f"choice pixels (right ROI): {result.choice_pixels:>6}  "
          f"(threshold {CONFIG.choice_pixel_min}) -> hit={result.choice_hit}")
    print(f"HUD '|| Playing' match   : {result.hud_match:>6.2f}  "
          f"(min {CONFIG.hud_match_min:.2f}) -> hit={result.hud_hit}")
    print(f"dark-screen fraction     : {result.dark_frac:>6.2f}  "
          f"(min {CONFIG.dark_screen_min:.2f}) -> continue={result.continue_hit}")
    print(f"option pills (right)     : {result.option_rows:>6}  "
          f"(>={CONFIG.option_veto_count} vetoes) -> many_options={result.many_options}")
    print("-" * 48)
    print(f"DECISION: dialogue = {result.dialogue}  "
          f"((name_hit AND hud_hit) OR continue_hit) AND NOT many_options")
    print("-" * 48)

    # annotate
    h, w = frame.shape[:2]
    out = frame.copy()
    for roi, color, label in (
        (CONFIG.name_roi, (0, 215, 255), "name"),
        (CONFIG.choice_roi, (0, 255, 0), "choice"),
        (CONFIG.hud_roi, (255, 128, 0), "hud"),
        (CONFIG.continue_roi, (255, 0, 255), "continue"),
        (CONFIG.options_roi, (0, 0, 255), "options"),
    ):
        x1, y1, x2, y2 = _roi_to_px(roi, w, h)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, label, (x1, max(0, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imwrite("calibrate_out.png", out)
    print("wrote calibrate_out.png")
    cap.close()


if __name__ == "__main__":
    main()
