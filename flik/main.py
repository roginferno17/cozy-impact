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

import time

import keyboard

from .config import CONFIG, Config
from .capture import ScreenCapture
from .detect import detect
from .inputs import press
from .window import is_target_focused


class Flik:
    def __init__(self, cfg: Config = CONFIG) -> None:
        self.cfg = cfg
        self.cap = ScreenCapture()
        self.enabled = True
        self.running = True
        self._last_press = 0.0
        self._last_dialogue_seen = 0.0

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
        print(f" F9  = pause/resume   F12 = quit")
        print(f" starting in {self.cfg.startup_delay_s:.0f}s - tab into the game...")
        print("=" * 56)

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

                    if result.dialogue:
                        self._last_dialogue_seen = now

                    # Stay active through brief dropouts via the grace window.
                    dialogue_live = (
                        now - self._last_dialogue_seen <= self.cfg.off_grace_s
                    )

                    if dialogue_live:
                        if not active:
                            active = True
                            tag = "choice" if result.choice_hit else "line"
                            print(f"[flik] dialogue start ({tag}) -> flik ON")
                        if now - self._last_press >= self.cfg.press_interval_s:
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
