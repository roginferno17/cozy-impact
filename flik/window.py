"""Foreground-window guard: only act when Genshin is the active window."""

from __future__ import annotations

import pygetwindow as gw


def active_window_title() -> str:
    try:
        win = gw.getActiveWindow()
    except Exception:
        return ""
    if win is None:
        return ""
    # pygetwindow returns a Window object (or str on some backends).
    title = getattr(win, "title", win)
    return title or ""


def is_target_focused(title_substring: str) -> bool:
    return title_substring.lower() in active_window_title().lower()
