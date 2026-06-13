"""
Dialogue detection.

The golden speaker-name bar in the bottom-center band is the NECESSARY signal:
every real dialogue screen — plain lines AND in-dialogue choice screens — shows
it. So it is the gate.

  1. Gold speaker-name text in the bottom-center band  -> the gate (name_hit).
  2. Bright reply-choice text on the right             -> informational only.

The choice signal alone is NOT trusted, because bright text on the right also
appears on things flik must ignore: world-interaction F-prompts ("Enter
Sanctuary..."), the party-member list during free roam, and full-screen
readable lore documents (which can only be closed with the ✕, not F). All of
those lack the bottom gold name, so gating on name_hit rejects them.
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
    gold_fill: float        # gold pixels / name ROI area (debug)
    gold_band: float        # height-fraction of the dense gold band (debug)
    gold_components: int    # number of gold blobs >= min area (debug)
    name_hit: bool
    choice_hit: bool


def _count_in_hsv_range(bgr_roi: np.ndarray, lower, upper) -> int:
    hsv = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower, np.uint8), np.array(upper, np.uint8))
    return int(cv2.countNonZero(mask))


def _gold_mask(bgr_roi: np.ndarray, lower, upper) -> np.ndarray:
    hsv = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, np.array(lower, np.uint8), np.array(upper, np.uint8))


def _dense_band_fraction(mask: np.ndarray, coverage: float) -> float:
    """Height (as a fraction of ROI) of the shortest row-band that holds
    `coverage` of the mask's set pixels. Small = gold concentrated in a thin
    horizontal line (text); large = spread vertically (scattered scenery)."""
    h = mask.shape[0]
    rowsum = mask.sum(axis=1).astype(np.float64)
    total = rowsum.sum()
    if total <= 0:
        return 1.0
    target = coverage * total
    for bh in range(1, h + 1):
        if np.convolve(rowsum, np.ones(bh), "valid").max() >= target:
            return bh / h
    return 1.0


def _component_count(mask: np.ndarray, min_area: int) -> int:
    num, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    return int(sum(1 for i in range(1, num)
                   if stats[i, cv2.CC_STAT_AREA] >= min_area))


def detect(frame: np.ndarray, cap: ScreenCapture, cfg: Config) -> DetectResult:
    name_crop = cap.crop(frame, cfg.name_roi)
    choice_crop = cap.crop(frame, cfg.choice_roi)

    gold = _count_in_hsv_range(name_crop, cfg.gold_hsv_lower, cfg.gold_hsv_upper)
    mask = _gold_mask(name_crop, cfg.gold_hsv_lower, cfg.gold_hsv_upper)
    choice = _count_in_hsv_range(
        choice_crop, cfg.choice_white_hsv_lower, cfg.choice_white_hsv_upper
    )

    name_area = int(name_crop.shape[0] * name_crop.shape[1]) or 1
    gold_fill = gold / name_area

    # Structural checks only matter once there's enough gold to consider.
    if gold >= cfg.gold_pixel_min:
        gold_band = _dense_band_fraction(mask, cfg.gold_band_coverage)
        gold_components = _component_count(mask, cfg.gold_component_min_area)
    else:
        gold_band, gold_components = 1.0, 0

    # A real speaker-name must be: enough gold, sparse (not a solid flood),
    # a single horizontal line (not vertically scattered scenery), and made of
    # several strokes (not one blobby sun / golden texture).
    name_hit = (
        gold >= cfg.gold_pixel_min
        and gold_fill <= cfg.gold_fill_max
        and gold_band <= cfg.gold_band_max
        and gold_components >= cfg.gold_min_components
    )
    choice_hit = choice >= cfg.choice_pixel_min

    # Gold speaker-name is the gate. Choice is kept for debugging/telemetry but
    # never triggers on its own — that's what caused false-fires on world
    # prompts, the party list, and lore documents.
    dialogue = name_hit

    return DetectResult(
        dialogue=dialogue,
        gold_pixels=gold,
        choice_pixels=choice,
        gold_fill=gold_fill,
        gold_band=gold_band,
        gold_components=gold_components,
        name_hit=name_hit,
        choice_hit=choice_hit,
    )
