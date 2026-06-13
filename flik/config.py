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
    press_interval_s: float = 0.3      # "flik": one F every 0.3s
    poll_interval_s: float = 0.1       # how often we look at the screen (~10 fps)

    # --- Hotkeys ----------------------------------------------------------
    toggle_hotkey: str = "f9"          # pause/resume flik
    kill_hotkey: str = "f12"           # quit the program

    # --- Detection: gold speaker-name band (bottom-center) ----------------
    # The gold speaker name appears here during dialogue lines.
    # Bottom band where the gold speaker-name sits. Genshin LEFT-aligns the
    # name for long/multi-line lines (name starts ~x0.16) but centers it for
    # short ones, so the band spans from the left margin across the centre.
    # Widening leftward is safe now that the "|| Playing" HUD veto (below)
    # guards against free-roam gold; the band alone no longer has to be picky.
    name_roi: Roi = Roi(0.14, 0.77, 0.72, 0.87)
    # Genshin name-gold in OpenCV HSV (H 0-179), measured from real dialogue:
    # hue tightly clusters 15-30 and saturation stays high (>=~85). Warm
    # scenery (pale sun glow, oranges) tends to fall outside this tighter band.
    gold_hsv_lower: tuple = (15, 85, 120)
    gold_hsv_upper: tuple = (30, 255, 255)
    # Minimum count of gold pixels in name_roi to call it "dialogue".
    # Calibration: real dialogue names measure ~4600-5400 px; normal scenery
    # should be far below this. 1000 still clears scattered noise while
    # admitting very short names (e.g. a 3-glyph "???" reads ~1165 gold px).
    # Safe to keep low: every non-dialogue frame is already rejected by the
    # HUD veto, so this count is a secondary text-shape gate, not the guard.
    gold_pixel_min: int = 1000
    # Maximum fraction of name_roi that may be gold. A speaker name is thin
    # text and fills only a small part of the band (positives: 4-19%). A
    # glowing gold object that engulfs the band -- e.g. the "Enter Sanctuary"
    # portal door -- fills ~85%+. This upper gate rejects those solid fills
    # while leaving huge headroom over real names.
    gold_fill_max: float = 0.40
    # The gold must be shaped like TEXT, not like scenery (sun, flowers, warm
    # textures). Two structural gates, both comfortably satisfied by real names:
    #   * it forms a single horizontal line -> the tightest row-band holding 85%
    #     of the gold is short (names: 38-74% of the band; scattered scenery
    #     spills taller).
    #   * it breaks into many letter-strokes (names: 9-33 components; a sun or
    #     flat golden texture is only 1-2 blobs).
    gold_band_max: float = 0.90       # max height-fraction of the 85%-gold band
                                       # (0.90, not 0.82: a character's tall gold
                                       # armor/hair beside the name spreads the
                                       # band vertically on real dialogue; the
                                       # HUD veto now guards free-roam gold)
    gold_min_components: int = 4      # min distinct gold blobs to look like text
    gold_band_coverage: float = 0.85  # fraction of gold the band must contain
    gold_component_min_area: int = 8  # ignore specks smaller than this
    # The single strongest "is this a line of text" signal: a real name flips
    # gold->dark->gold many times across its busiest row (letters + gaps).
    # Measured on real names: 11-35 transitions. A solid blob or smooth golden
    # scenery yields 1-2; sparse scatter a few. Require a clearly text-like row.
    gold_min_row_transitions: int = 6

    # --- Detection: reply-choice pills (right side) -----------------------
    # Covers choice screens that may have no bottom subtitle.
    choice_roi: Roi = Roi(0.60, 0.60, 0.99, 0.82)
    # The choice pills are light/near-white rounded boxes. Detect bright,
    # low-saturation regions here.
    choice_white_hsv_lower: tuple = (0, 0, 180)
    choice_white_hsv_upper: tuple = (179, 60, 255)
    choice_pixel_min: int = 1500

    # --- Detection: dialogue HUD ("|| Playing" control bar, top-left) -----
    # The single most reliable "we are actually in dialogue/a cutscene" signal:
    # Genshin hides the minimap + party list during dialogue and shows the
    # "|| Playing" control bar top-left instead. Free roam (even when standing
    # at an NPC with an F-prompt, surrounded by gold-clad guards) always shows
    # the minimap and never this bar. We template-match the shipped glyph in
    # this region; a real match scores >=0.62, free roam <=0.22, so 0.42 splits
    # them with wide margin. This vetoes gold *clothing* in the name band that
    # color/shape checks alone cannot distinguish from gold *text*.
    hud_roi: Roi = Roi(0.0, 0.0, 0.26, 0.09)
    hud_template_file: str = "assets/playing_bar.png"  # relative to flik/
    hud_match_min: float = 0.42

    # --- Detection: "Click to continue" interlude (near-black narration) --
    # An ADDITIVE third trigger for the black story-interlude screens: white
    # narration text + a gold "Click to continue" prompt, with NO "Playing"
    # bar and NO bottom speaker-name (so the two checks above miss them on
    # purpose). It is gated behind "the screen is almost entirely black", which
    # NEVER happens during normal dialogue or free roam (measured max ~0.55),
    # so this can't disturb the existing detection. Lore documents are also
    # mostly black but carry no gold prompt in this band, so they stay rejected.
    continue_roi: Roi = Roi(0.34, 0.85, 0.66, 0.96)   # bottom-center prompt band
    dark_screen_min: float = 0.85       # >=85% near-black -> interlude/loading
    dark_v_max: int = 50                # a pixel counts as "dark" at V <= this
    # Slightly wider gold than the name band (the amber prompt), applied ONLY
    # here on an already-confirmed black screen -- keeps the name gate untouched.
    continue_gold_hsv_lower: tuple = (12, 80, 110)
    continue_gold_hsv_upper: tuple = (35, 255, 255)
    continue_gold_min: int = 250
    continue_min_row_transitions: int = 6

    # --- Veto: 3+ selectable options (a real choice the player must make) ----
    # An NPC/service menu (e.g. Katheryne) shows more than two option pills;
    # pressing F would blindly pick one. So when >2 option pills are present,
    # suppress firing. Pills are detected by GEOMETRY: each option is a dark
    # translucent rounded box that is flush to the LEFT of this region (a fixed
    # left margin where the icon sits) and extends RIGHT by a variable amount
    # depending on the text length -- "See you." is short, "Claim Daily
    # Commission Reward" is long. So we key on the left cap/icon band being
    # dark pill background, NOT a right-edge alignment (an earlier version
    # tested the right edge and missed every pill, since they never reach it).
    # This survives the pills' transparency (they read dark even over a bright
    # wooden counter) and text wrapping (one box = one option even across two
    # lines). Tuned so every real-dialogue frame reads <=2 pills while a 3- or
    # 6-option menu reads >=3.
    options_roi: Roi = Roi(0.66, 0.16, 0.99, 0.82)
    option_pill_v_max: int = 120          # pill bg is dark-ish
    option_pill_s_max: int = 95           # ...and desaturated
    option_pill_left_frac: float = 0.13   # inspect the left cap/icon band only
    option_pill_left_min: float = 0.55    # that left band is >=55% pill bg
    option_text_v_min: int = 200          # bright text sitting on the pill
    option_text_frac_lo: float = 0.015    # sparse: real text, not a solid blob
    option_text_frac_hi: float = 0.45
    option_text_min_transitions: int = 4  # bright<->dark flips => letters
    option_gap_close: int = 11            # bridge wrapped lines within one pill
    option_min_band_h: int = 10           # a pill box is at least this tall (px)
    option_veto_count: int = 3            # >2 options -> do not fire

    # --- Misc -------------------------------------------------------------
    startup_delay_s: float = 3.0       # grace period to tab into the game
    # Keep flik running for a short tail after dialogue vanishes, to ride out
    # 1-frame detection dropouts mid-conversation (animation transitions etc).
    off_grace_s: float = 0.6


CONFIG = Config()
