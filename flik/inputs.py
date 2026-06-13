"""
Key input via pydirectinput (SendInput + scancodes).

pydirectinput speaks the low-level scancode path that DirectInput games like
Genshin actually listen to, unlike high-level WM_KEY messages which the game
ignores. This sends to the *focused* window only (foreground); we never inject
into the game process.
"""

from __future__ import annotations

import pydirectinput

# Don't insert pydirectinput's own delay after each call; we time it ourselves.
pydirectinput.PAUSE = 0.0
# Don't abort if the cursor is slammed into a screen corner.
pydirectinput.FAILSAFE = False


def press(key: str) -> None:
    pydirectinput.press(key)
