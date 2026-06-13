"""
Dialogue detection.

Two conditions must BOTH hold to call it dialogue:

  1. A gold speaker-name TEXT line in the bottom-center band (name_hit) -- enough
     gold, shaped like a thin horizontal line of letter-strokes (not a solid
     flood or vertically-scattered scenery).
  2. The "|| Playing" dialogue HUD bar in the top-left (hud_hit) -- Genshin only
     shows this during dialogue/cutscenes; free roam shows the minimap + party
     list instead.

Condition 2 is the decisive veto. Free roam can put real gold *into* the name
band -- gilded NPC guards, a gold-patterned player outfit, golden scenery --
which color and shape checks alone cannot reliably tell from gold *text*. But
free roam never shows the "Playing" bar, so requiring it rejects those frames.

A bright reply-choice signal on the right (choice_hit) is computed for
telemetry only; it never triggers on its own (world F-prompts, the party list,
and lore documents all have bright right-side text but are not dialogue).

A third, ADDITIVE trigger (continue_hit) handles the black "Click to continue"
story interludes, which have neither the HUD bar nor a bottom speaker-name. It
only fires when the whole screen is almost black AND a text-shaped gold prompt
sits in the bottom-center band -- conditions that never occur in normal
dialogue or free roam, so it leaves the gold-name + HUD path untouched.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

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
    gold_row_trans: int     # max gold->dark transitions in any row (debug)
    hud_match: float        # "|| Playing" bar template score 0..1 (debug)
    dark_frac: float        # fraction of frame that is near-black (debug)
    name_hit: bool
    choice_hit: bool
    hud_hit: bool
    continue_hit: bool      # near-black "Click to continue" interlude


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


def _max_row_transitions(mask: np.ndarray) -> int:
    """Most gold->non-gold(->gold) edges found in any single row. A line of
    text has many (letters + gaps); a blob or smooth region has very few."""
    if mask.size == 0:
        return 0
    b = (mask > 0).astype(np.int8)
    trans = (np.diff(b, axis=1) == 1).sum(axis=1)
    return int(trans.max()) if trans.size else 0


@lru_cache(maxsize=4)
def _load_template(path: str) -> np.ndarray | None:
    """Load the grayscale '|| Playing' HUD template once (cached)."""
    tmpl = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return tmpl


def _hud_match(frame: np.ndarray, cap: ScreenCapture, cfg: Config) -> float:
    """Best normalized-correlation score for the '|| Playing' control bar in
    the top-left HUD region. The template was captured at 1080p, so it is
    rescaled to the current frame width -- this keeps the check working across
    resolutions. Returns 0..1; ~0 when the bar is absent (free roam)."""
    here = os.path.dirname(os.path.abspath(__file__))
    tmpl = _load_template(os.path.join(here, cfg.hud_template_file))
    if tmpl is None:
        return 0.0

    win = cap.crop(frame, cfg.hud_roi)
    if win.ndim == 3:
        win = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY)

    # Rescale the 1080p-reference template to this frame's resolution.
    scale = frame.shape[1] / 1920.0
    th = max(1, int(round(tmpl.shape[0] * scale)))
    tw = max(1, int(round(tmpl.shape[1] * scale)))
    if scale != 1.0:
        tmpl = cv2.resize(tmpl, (tw, th), interpolation=cv2.INTER_AREA)

    if win.shape[0] < tmpl.shape[0] or win.shape[1] < tmpl.shape[1]:
        return 0.0
    res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
    return float(res.max())


def _dark_fraction(frame: np.ndarray, v_max: int) -> float:
    """Fraction of the (downsampled) frame that is near-black. Story interludes
    and loading screens are almost entirely black; normal dialogue and free
    roam never are (measured max ~0.55)."""
    small = frame[::4, ::4]
    v = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)[:, :, 2]
    return float((v <= v_max).mean())


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
        gold_row_trans = _max_row_transitions(mask)
    else:
        gold_band, gold_components, gold_row_trans = 1.0, 0, 0

    # A real speaker-name must be: enough gold, sparse (not a solid flood),
    # a single horizontal line (not vertically scattered scenery), made of
    # several strokes, AND text-like across a row (many gold/dark transitions
    # -- the strongest "this is a line of letters, not scenery" signal).
    name_hit = (
        gold >= cfg.gold_pixel_min
        and gold_fill <= cfg.gold_fill_max
        and gold_band <= cfg.gold_band_max
        and gold_components >= cfg.gold_min_components
        and gold_row_trans >= cfg.gold_min_row_transitions
    )
    choice_hit = choice >= cfg.choice_pixel_min

    # The dialogue HUD veto: Genshin only shows the "|| Playing" control bar
    # (top-left) during dialogue/cutscenes, replacing the free-roam minimap +
    # party list. This is what finally separates real gold *text* from gold
    # *clothing* (e.g. gilded NPC guards) standing in the name band during free
    # roam -- color and shape alone cannot.
    hud_match = _hud_match(frame, cap, cfg)
    hud_hit = hud_match >= cfg.hud_match_min

    # Additive third trigger: the near-black "Click to continue" story
    # interlude. Only considered when the WHOLE screen is almost black -- which
    # never happens in normal dialogue/free roam -- so it cannot affect the
    # gold-name + HUD path above. Requires a text-shaped gold prompt in the
    # bottom-center band (lore documents are also black but have none there).
    dark_frac = _dark_fraction(frame, cfg.dark_v_max)
    if dark_frac >= cfg.dark_screen_min:
        cont_crop = cap.crop(frame, cfg.continue_roi)
        cont_gold = _count_in_hsv_range(
            cont_crop, cfg.continue_gold_hsv_lower, cfg.continue_gold_hsv_upper
        )
        cont_mask = _gold_mask(
            cont_crop, cfg.continue_gold_hsv_lower, cfg.continue_gold_hsv_upper
        )
        cont_trans = _max_row_transitions(cont_mask)
        continue_hit = (
            cont_gold >= cfg.continue_gold_min
            and cont_trans >= cfg.continue_min_row_transitions
        )
    else:
        continue_hit = False

    # Real dialogue (gold name + HUD) OR a "Click to continue" interlude.
    dialogue = (name_hit and hud_hit) or continue_hit

    return DetectResult(
        dialogue=dialogue,
        gold_pixels=gold,
        choice_pixels=choice,
        gold_fill=gold_fill,
        gold_band=gold_band,
        gold_components=gold_components,
        gold_row_trans=gold_row_trans,
        hud_match=hud_match,
        dark_frac=dark_frac,
        name_hit=name_hit,
        choice_hit=choice_hit,
        hud_hit=hud_hit,
        continue_hit=continue_hit,
    )
