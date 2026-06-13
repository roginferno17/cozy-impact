<div align="center">

# ✨ flik ✨

### *blink, and the dialogue's gone* 💨

**A cozy, screen-reading auto-presser for Genshin Impact's unskippable quest chatter.**

`flik` watches your screen and gently taps **F** through dialogue lines while you sip your coffee ☕ —
then *stops the instant the conversation ends*, so you never accidentally re-trigger a chat.

<br>

![status](https://img.shields.io/badge/status-working-success?style=for-the-badge)
![python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![mode](https://img.shields.io/badge/mode-foreground_only-orange?style=for-the-badge)
![input](https://img.shields.io/badge/input-only-9cf?style=for-the-badge)
![res](https://img.shields.io/badge/tuned_for-1080p-ff69b4?style=for-the-badge)

</div>

---

## 💡 The idea

Some quest cutscenes in Genshin *can't* be skipped — you just have to sit there mashing **F**.
`flik` does the mashing for you, but **only when there's actually dialogue on screen**:

- 🗣️ Sees a real conversation → taps **F** every `0.3s`
- 🛑 Sees free roam, menus, or world prompts → stays completely quiet
- 🪟 Only ever presses while **Genshin is the focused window** — tab away and it auto-pauses

> It's the digital equivalent of a friend nudging the F key for you. Nothing more. 🫶

---

## 🔍 How it works

`flik` never reads or touches the game's process or memory. It just **looks at pixels** and presses a
key — the same lane as a hardware macro keyboard. 🎹

To decide "is this *really* dialogue?", it checks **two things that must BOTH be true**:

```
   screen ─▶ capture (mss) ─▶ detect (opencv) ─┬─ ① gold speaker-name in the bottom band?
                                               │
                                               └─ ② "⏸ Playing" HUD bar in the top-left?
                                                          │
                                       both yes ▼                    anything else ▼
                                    tap F every 0.3s                    stay quiet
```

| # | Signal | Why it matters |
| :-: | :----- | :------------- |
| ① | 🟡 **Gold speaker-name** | The warm-gold name line at the bottom, shaped like *text* (many letter-strokes), not a solid gold blob. |
| ② | ⏸️ **"Playing" HUD bar** | Genshin shows this top-left bar during dialogue/cutscenes **when conversation mode is set to _Auto_** — free roam shows the minimap + party list instead. *(Auto mode is required — see Quick start.)* |

That second check is the secret sauce. 🔑 Plenty of things in the open world are gold — gilded NPC
guards, a gold-trimmed outfit, sunlight on water — and color alone can't always tell them apart from
gold *text*. But the **"Playing" bar only ever appears in real dialogue**, so requiring it means
flik stays silent in the open world no matter how much gold is on screen.

> 🧪 Detection is regression-tested against a labeled set of real dialogue **and** real free-roam
> frames (including ones that *used* to false-fire) — every one classifies correctly.

---

## 🚀 Quick start

> ⚠️ **Required in-game setting: turn conversation mode to _Auto_.**
> That's what makes the **"⏸ Playing"** bar appear during dialogue — the exact signal flik
> watches for. **If it's not on Auto, flik will not press F at all.** This is by design: the
> auto-mode HUD is how flik knows it's safe to act.

### 🖱️ The easy way (just double-click)

On Windows you don't need to touch a terminal:

| Double-click… | What it does |
| :------------ | :----------- |
| 1️⃣ `install.bat` | one-time setup — grabs the libraries flik needs |
| 2️⃣ `observe.bat` | **safe test** — watches the screen and shows what it *would* do, but **never presses F** |
| 3️⃣ `flik.bat` | the real thing — taps F through dialogue for you |

> 🛡️ `flik.bat` and `observe.bat` will ask for **Administrator** permission — say yes.
> Genshin runs as admin, so flik has to as well or your F presses won't register in the game.

> 🩺 **Always try `observe.bat` first.** Hop into a quest cutscene and watch it print
> `dialogue=True` only while real dialogue is on screen — and stay quiet on menus, prompts,
> free roam, and lore documents. Once you're happy, use `flik.bat`.

### ⌨️ The terminal way (for developers)

```bash
pip install -r requirements.txt
python run.py               # run for real
python run.py --dry-run -v  # observe only, with live readout
```

| Key | Action |
| :-: | :----- |
| <kbd>F9</kbd>  | ⏯️ pause / resume |
| <kbd>F12</kbd> | 🚪 quit |

> ⏱️ You get a 3-second grace period on launch to tab back into the game.

### 🎯 Calibrate before you fly

Want to sanity-check detection on a screenshot first?

```bash
python calibrate.py path\to\dialogue_screenshot.png
```

It prints the gold / HUD / choice readouts + the dialogue decision, and writes `calibrate_out.png`
with the detection regions drawn on top so you can *see* what `flik` sees. 👀

---

## 📦 Project layout

```
flik/
 ├─ config.py    🎛️  ROIs, colors, thresholds, hotkeys, timing
 ├─ capture.py   📸  mss screen grab + ROI cropping
 ├─ detect.py    🔎  gold-name + "Playing" HUD detection
 ├─ window.py    🪟  focused-window guard
 ├─ inputs.py    ⌨️  F keypress via pydirectinput
 ├─ assets/
 │   └─ playing_bar.png   🧩  the "⏸ Playing" HUD template flik matches against
 └─ main.py      🔁  the loop
calibrate.py     🧪  detection debug / tuning tool
validate.py      ✅  regression check over a labeled sample corpus
run.py           ▶️  entry point
```

> 🖼️ The only image that ships with flik is `flik/assets/playing_bar.png` — a tiny, cropped grayscale
> picture of the **"⏸ Playing"** HUD glyph. It contains no account data and is required for detection.

---

## 📈 Progress

- [x] 🎯 **Concept locked** — dialogue-aware foreground F auto-presser
- [x] 🏗️ **Scaffold built** — full package compiles clean
- [x] 📸 **Capture + detection pipeline** — mss grab → opencv ROI analysis
- [x] 🟡 **Gold-name detector** — text-shaped gold in the bottom band (left-aligned *and* centered)
- [x] ⏸️ **"Playing" HUD veto** — requires the dialogue-only top-left bar, so gold clothing and gold
  scenery in free roam can never trigger a press
- [x] 🌑 **"Click to continue" interludes** — also taps through the near-black story-transition
  screens (gold prompt on black), gated so tightly it can't fire during normal play
- [x] 🪟 **Focused-window guard** — won't spam F into other apps
- [x] ⌨️ **Press loop** — clean 0.3s cadence with pause / quit hotkeys
- [x] 🩺 **Safe observe mode** — `--dry-run` logs decisions live without ever pressing F
- [x] ✅ **Regression corpus** — labeled real-dialogue + free-roam frames, all classified correctly
- [ ] 🎮 **Field-testing** across full quest chains

---

## ⚖️ Honest limits

- **Doesn't pick dialogue options for you.** When an NPC shows a multi-option
  choice (a service menu like Katheryne, or a branching reply), flik can't
  reliably tell those semi-transparent option pills apart from busy scenery on a
  single frame — so it doesn't try. It just keeps pressing through normal
  dialogue. **When you need to choose, tap <kbd>F9</kbd> to pause flik**, pick
  your option, then <kbd>F9</kbd> again to resume. 🕹️
- **Foreground only.** No background input injection — that's deliberate, it's the part anti-cheat
  actually cares about. Works while Genshin is focused; that's it.
- **Input-only**, no process/memory access — same lane as a hardware macro.
- This is **not** an officially-blessed tool. HoYoverse's ToS has broad anti-automation language,
  so use it thoughtfully and at your own risk. 🙏
- Thresholds and the HUD template are tuned for **1080p**. The template auto-scales to your
  resolution, but if detection feels off, run `calibrate.py` to check. 🎚️

<div align="center">

<br>

*made for cozy questing 🍃*

</div>
