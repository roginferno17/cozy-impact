"""
flik configuration.

All regions of interest (ROIs) are expressed as fractions of the screen
(0.0 - 1.0) so they scale across resolutions. Defaults are tuned from
1080p Genshin dialogue screenshots.

Run `python calibrate.py <screenshot.png>` to verify/adjust these against
your own screen, then tweak the numbers here.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Roi:
    """A rectangular region as fractions of screen width/height."""
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class Config:
    # --- Window targeting -------------------------------------------------
    # flik only sends keys while the focused window title contains this
    # substring (case-insensitive). This both makes it correct (keys land in
    # the game) and safe (won't spam F into YouTube/Discord/etc).
    window_title_contains: str = "genshin"

    # --- Key + timing -----------------------------------------------------
    skip_key: str = "f"
    press_interval_s: float = 0.5      # "flik": one F every 0.5s
    poll_interval_s: float = 0.1       # how often we look at the screen (~10 fps)

    # --- Hotkeys ----------------------------------------------------------
    toggle_hotkey: str = "f9"          # pause/resume flik
    kill_hotkey: str = "f12"           # quit the program

    # --- Detection: gold speaker-name band (bottom-center) ----------------
    # The gold speaker name appears here during dialogue lines.
    name_roi: Roi = Roi(0.28, 0.77, 0.72, 0.85)
    # Genshin gold in OpenCV HSV (H 0-179). Tune with calibrate.py.
    gold_hsv_lower: tuple = (15, 80, 120)
    gold_hsv_upper: tuple = (35, 255, 255)
    # Minimum count of gold pixels in name_roi to call it "dialogue".
    # Calibration: real dialogue names measure ~4600-5400 px; normal scenery
    # should be far below this. 1500 keeps ~3x headroom over the signal.
    gold_pixel_min: int = 1500

    # --- Detection: reply-choice pills (right side) -----------------------
    # Covers choice screens that may have no bottom subtitle.
    choice_roi: Roi = Roi(0.60, 0.60, 0.99, 0.82)
    # The choice pills are light/near-white rounded boxes. Detect bright,
    # low-saturation regions here.
    choice_white_hsv_lower: tuple = (0, 0, 180)
    choice_white_hsv_upper: tuple = (179, 60, 255)
    choice_pixel_min: int = 1500

    # --- Misc -------------------------------------------------------------
    startup_delay_s: float = 3.0       # grace period to tab into the game
    # Keep flik running for a short tail after dialogue vanishes, to ride out
    # 1-frame detection dropouts mid-conversation (animation transitions etc).
    off_grace_s: float = 0.6


CONFIG = Config()
