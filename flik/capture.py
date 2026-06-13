"""Screen capture utilities built on mss."""

from __future__ import annotations

import numpy as np
from mss import mss

from .config import Roi


class ScreenCapture:
    """Grabs the primary monitor as BGR numpy frames."""

    def __init__(self) -> None:
        self._sct = mss()
        # monitor[1] is the primary physical monitor (monitor[0] is "all").
        self.monitor = self._sct.monitors[1]
        self.width = self.monitor["width"]
        self.height = self.monitor["height"]

    def grab(self) -> np.ndarray:
        """Return the full primary monitor as a BGR uint8 array (H, W, 3)."""
        raw = self._sct.grab(self.monitor)
        frame = np.asarray(raw)          # BGRA
        return frame[:, :, :3]           # drop alpha -> BGR

    def crop(self, frame: np.ndarray, roi: Roi) -> np.ndarray:
        """Slice a fractional ROI out of a full frame."""
        h, w = frame.shape[:2]
        x1 = int(roi.x1 * w)
        y1 = int(roi.y1 * h)
        x2 = int(roi.x2 * w)
        y2 = int(roi.y2 * h)
        return frame[y1:y2, x1:x2]

    def close(self) -> None:
        self._sct.close()
