"""
Dialogue detection.

Two independent signals; either one being present means "dialogue is on
screen, flik should run":

  1. Gold speaker-name text in the bottom-center band (normal dialogue lines).
  2. Bright reply-choice pills on the right (choice screens, which may have
     no bottom subtitle).
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .config import Config
from .capture import ScreenCapture


@dataclass
class DetectResult:
    dialogue: bool          # final decision: is dialogue on screen?
    gold_pixels: int        # gold count in name ROI (debug)
    choice_pixels: int      # bright count in choice ROI (debug)
    name_hit: bool
    choice_hit: bool


def _count_in_hsv_range(bgr_roi: np.ndarray, lower, upper) -> int:
    hsv = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower, np.uint8), np.array(upper, np.uint8))
    return int(cv2.countNonZero(mask))


def detect(frame: np.ndarray, cap: ScreenCapture, cfg: Config) -> DetectResult:
    name_crop = cap.crop(frame, cfg.name_roi)
    choice_crop = cap.crop(frame, cfg.choice_roi)

    gold = _count_in_hsv_range(name_crop, cfg.gold_hsv_lower, cfg.gold_hsv_upper)
    choice = _count_in_hsv_range(
        choice_crop, cfg.choice_white_hsv_lower, cfg.choice_white_hsv_upper
    )

    name_hit = gold >= cfg.gold_pixel_min
    choice_hit = choice >= cfg.choice_pixel_min

    return DetectResult(
        dialogue=name_hit or choice_hit,
        gold_pixels=gold,
        choice_pixels=choice,
        name_hit=name_hit,
        choice_hit=choice_hit,
    )
