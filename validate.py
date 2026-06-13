"""
Detection regression check for flik.

Runs detect() over the labeled sample corpus and verifies every frame lands on
the expected decision:

    images/                -> dialogue MUST be True   (real dialogue / choices)
    negative-images/       -> dialogue MUST be False  (world prompts, free roam)
    additional-flik-images/-> dialogue MUST be False  (lore documents; ✕ to close)

Usage:
    python validate.py

Exit code is non-zero if any sample is misclassified, so it doubles as a CI gate.
"""

from __future__ import annotations

import glob
import os
import sys

import cv2

from flik.config import CONFIG
from flik.capture import ScreenCapture
from flik.detect import detect

# (folder, expected dialogue decision)
LABELED_DIRS = [
    ("images", True),
    ("negative-images", False),
    ("additional-flik-images", False),
]


def _iter_images(folder: str):
    for path in sorted(glob.glob(os.path.join(folder, "*.png"))):
        yield path


def main() -> int:
    cap = ScreenCapture()
    total = 0
    failures = []

    for folder, expected in LABELED_DIRS:
        if not os.path.isdir(folder):
            print(f"(skipping missing folder: {folder})")
            continue
        print(f"\n== {folder}  (expect dialogue={expected}) ==")
        for path in _iter_images(folder):
            frame = cv2.imread(path)
            if frame is None:
                print(f"  !! could not read {path}")
                failures.append(path)
                continue
            r = detect(frame, cap, CONFIG)
            ok = r.dialogue == expected
            total += 1
            mark = "PASS" if ok else "FAIL"
            name = os.path.basename(path)
            print(f"  [{mark}] {name:<22} dialogue={r.dialogue!s:<5} "
                  f"gold={r.gold_pixels:>5} fill={r.gold_fill:>5.1%} "
                  f"band={r.gold_band:>5.1%} comps={r.gold_components:>3} "
                  f"choice={r.choice_pixels:>6}")
            if not ok:
                failures.append(path)

    cap.close()
    print("\n" + "-" * 56)
    if failures:
        print(f"RESULT: {len(failures)}/{total} FAILED")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"RESULT: all {total} samples classified correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
