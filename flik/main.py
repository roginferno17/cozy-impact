"""
flik main loop.

While Genshin is the focused window AND dialogue is detected on screen, press
F every `press_interval_s` seconds. The moment dialogue disappears (plus a
short grace tail), pressing stops -- so you never get stuck re-triggering a
conversation with the same NPC.

Hotkeys:
  F9  -> pause / resume
  F12 -> quit
"""

from __future__ import annotations

import os
import time
from datetime import datetime

import cv2
import keyboard

from .config import CONFIG, Config
from .capture import ScreenCapture
from .detect import detect, DetectResult
from .inputs import press
from .window import is_target_focused


def _is_admin() -> bool:
    """True if running with Administrator rights (Windows)."""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class Flik:
    def __init__(self, cfg: Config = CONFIG, *, dry_run: bool = False,
                 verbose: bool = False, capture: bool = False) -> None:
        self.cfg = cfg
        self.dry_run = dry_run      # observe only: never actually press F
        self.verbose = verbose      # log detection telemetry every poll
        self.capture = capture      # save a screenshot each time flik fires
        self.capture_dir = "flik-captures"
        self.cap = ScreenCapture()
        self.enabled = True
        self.running = True
        self._last_press = 0.0
        self._last_dialogue_seen = 0.0
        self._last_verbose = 0.0
        if self.capture:
            os.makedirs(self.capture_dir, exist_ok=True)

    def _save_capture(self, frame, result: DetectResult) -> None:
        stamp = datetime.now().strftime("%H%M%S_%f")[:-3]
        fname = (f"fire_{stamp}_gold{result.gold_pixels}"
                 f"_band{int(result.gold_band * 100)}"
                 f"_comps{result.gold_components}.png")
        path = os.path.join(self.capture_dir, fname)
        try:
            cv2.imwrite(path, frame)
            print(f"[flik] saved evidence frame -> {path}")
        except Exception as exc:
            print(f"[flik] could not save capture: {exc}")

    # --- hotkey handlers --------------------------------------------------
    def _toggle(self) -> None:
        self.enabled = not self.enabled
        print(f"[flik] {'ENABLED' if self.enabled else 'PAUSED'} (F9)")

    def _kill(self) -> None:
        self.running = False
        print("[flik] quitting (F12)")

    # --- lifecycle --------------------------------------------------------
    def _banner(self) -> None:
        print("=" * 56)
        print(" flik - dialogue-aware F auto-presser (foreground only)")
        print("=" * 56)
        print(f" target window : *{self.cfg.window_title_contains}*")
        print(f" key / interval: {self.cfg.skip_key.upper()} every "
              f"{self.cfg.press_interval_s}s")
        if self.dry_run:
            print(" MODE          : DRY-RUN (observe only, F is NEVER pressed)")
        print(f" F9  = pause/resume   F12 = quit")
        print(f" starting in {self.cfg.startup_delay_s:.0f}s - tab into the game...")
        print("=" * 56)

        # --- plain-language health checks --------------------------------
        if not self.dry_run and not _is_admin():
            print(" NOTE: not running as Administrator. Genshin runs as admin,")
            print("       so your F presses may NOT register in-game. If nothing")
            print("       happens, close this and use the flik.bat launcher,")
            print("       which asks for admin automatically.")
            print("-" * 56)
        if (self.cap.width, self.cap.height) != (1920, 1080):
            print(f" NOTE: your screen is {self.cap.width}x{self.cap.height}, not")
            print("       1920x1080. Detection is tuned for 1080p and may be off.")
            print("-" * 56)

    def run(self) -> None:
        self._banner()
        keyboard.add_hotkey(self.cfg.toggle_hotkey, self._toggle)
        keyboard.add_hotkey(self.cfg.kill_hotkey, self._kill)
        time.sleep(self.cfg.startup_delay_s)

        active = False  # are we currently flik-ing a conversation?
        try:
            while self.running:
                loop_start = time.time()

                focused = is_target_focused(self.cfg.window_title_contains)
                if self.enabled and focused:
                    frame = self.cap.grab()
                    result = detect(frame, self.cap, self.cfg)
                    now = time.time()

                    if self.verbose and now - self._last_verbose >= 0.5:
                        self._last_verbose = now
                        print(f"[flik] dialogue={result.dialogue!s:<5} "
                              f"gold={result.gold_pixels:>5} "
                              f"fill={result.gold_fill:>5.1%} "
                              f"band={result.gold_band:>5.1%} "
                              f"comps={result.gold_components:>3} "
                              f"trans={result.gold_row_trans:>3} "
                              f"hud={result.hud_match:>4.2f} "
                              f"dark={result.dark_frac:>4.2f} "
                              f"cont={result.continue_hit!s:<5} "
                              f"choice={result.choice_pixels:>6}")

                    if result.dialogue:
                        self._last_dialogue_seen = now

                    # Stay active through brief dropouts via the grace window,
                    # so 1-frame detection dips mid-conversation (animation
                    # transitions etc.) don't flip flik off and on.
                    dialogue_live = (
                        now - self._last_dialogue_seen <= self.cfg.off_grace_s
                    )

                    if dialogue_live:
                        if not active:
                            active = True
                            tag = ("continue" if result.continue_hit
                                   else "choice" if result.choice_hit else "line")
                            mode = " [dry-run]" if self.dry_run else ""
                            print(f"[flik] dialogue start ({tag}) -> flik ON{mode}")
                            if self.capture:
                                self._save_capture(frame, result)
                        if now - self._last_press >= self.cfg.press_interval_s:
                            if self.dry_run:
                                print("[flik] (dry-run) would press "
                                      f"{self.cfg.skip_key.upper()}")
                            else:
                                press(self.cfg.skip_key)
                            self._last_press = now
                    elif active:
                        active = False
                        print("[flik] dialogue end -> flik OFF")
                else:
                    if active:
                        active = False
                        print("[flik] window lost focus / paused -> flik OFF")

                # pace the loop
                elapsed = time.time() - loop_start
                time.sleep(max(0.0, self.cfg.poll_interval_s - elapsed))
        finally:
            self.cap.close()
            keyboard.clear_all_hotkeys()
            print("[flik] stopped.")


def main() -> None:
    Flik().run()


if __name__ == "__main__":
    main()
