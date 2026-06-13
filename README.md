<div align="center">

# ✨ flik ✨

### *blink, and the dialogue's gone* 💨

**A cozy little screen-reading auto-presser for Genshin Impact's unskippable quest chatter.**

`flik` watches your screen and gently taps **F** through dialogue lines while you sip your coffee ☕ —
then *stops the instant the conversation ends*, so you never accidentally re-trigger a chat.

<br>

![status](https://img.shields.io/badge/status-detection_working-success?style=for-the-badge)
![python](https://img.shields.io/badge/python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![mode](https://img.shields.io/badge/mode-foreground_only-orange?style=for-the-badge)
![res](https://img.shields.io/badge/tuned_for-1080p-ff69b4?style=for-the-badge)

</div>

---

## 💡 The idea

Some quest cutscenes in Genshin *can't* be skipped — you just have to sit there mashing **F**.
`flik` does the mashing for you, but **only when there's actually dialogue on screen**:

- 🗣️ Sees the **golden speaker name** + subtitle at the bottom → taps F every `0.3s`
- 🛑 Sees nothing → goes quiet immediately (no stuck-in-a-loop re-chats!)
- 🪟 Only ever presses while **Genshin is the focused window** — tab away and it auto-pauses

> It's the digital equivalent of a friend nudging the F key for you. Nothing more. 🫶

---

## 🔍 How it works

```
   screen  ──▶  capture (mss)  ──▶  detect (opencv)  ──▶  is this real dialogue?
                                                              │
                                          ┌───────────────────┴───────────────────┐
                                       yes ▼                                    no ▼
                                  tap F every 0.3s                          stay quiet
```

Detection reads two regions of the frame:

| Signal | What it looks for | Region |
| :----- | :---------------- | :----- |
| 🟡 **Gold name bar** | the warm-gold speaker name at the bottom-center | `name_roi` |
| ⚪ **Reply pills** | bright white choice text on the right | `choice_roi` |

…and it's **read-only**: `flik` never reads or touches the game process or memory. It just looks at
pixels and presses a key, the same as a macro keyboard would. 🎹

---

## 🚀 Quick start

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
> and lore documents. Once you're happy, use `flik.bat`.

### ⌨️ The terminal way (for developers)

```bash
pip install -r requirements.txt
python run.py              # run for real
python run.py --dry-run -v # observe only, with live readout
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

It prints the gold/choice pixel counts + the dialogue decision, and writes `calibrate_out.png`
with the detection regions drawn on top so you can *see* what `flik` sees. 👀

---

## 📦 Project layout

```
flik/
 ├─ config.py    🎛️  ROIs, colors, thresholds, hotkeys, timing
 ├─ capture.py   📸  mss screen grab + ROI cropping
 ├─ detect.py    🔎  gold-name + choice-pill detection
 ├─ window.py    🪟  focused-window guard
 ├─ inputs.py    ⌨️  F keypress via pydirectinput
 └─ main.py      🔁  the loop
calibrate.py     🧪  detection debug / tuning tool
validate.py      ✅  regression check over the labeled sample corpus
run.py           ▶️  entry point
```

---

## 📈 Progress

- [x] 🎯 **Concept locked** — dialogue-aware foreground F auto-presser
- [x] 🏗️ **Scaffold built** — full package compiles clean
- [x] 📸 **Capture + detection pipeline** — mss grab → opencv ROI analysis
- [x] 🟡 **Gold-name detector** — validated on real dialogue (~4600+ gold px, 3× threshold headroom)
- [x] ⚪ **Choice-pill detector** — fires on reply-choice screens
- [x] 🪟 **Focused-window guard** — won't spam F into other apps
- [x] ⌨️ **Press loop** — clean 0.3s cadence with pause / quit hotkeys
- [x] 🧠 **Stricter dialogue gating** — gold speaker-name is the gate; ignores world-interaction
  prompts, the party list, and full-screen lore documents *(16/16 sample corpus passing)*
- [x] 🩺 **Safe observe mode** — `--dry-run` logs decisions live without ever pressing F
- [ ] 🔤 **F-glyph template fallback** — *deferred*: every dialogue/choice we've seen carries a gold
  name, and a raw F-glyph match would re-trigger on world prompts. Revisit only if a gold-name-less
  dialogue screen turns up.
- [ ] 🎮 **Field-testing** across full quest chains

---

## ⚖️ Honest limits

- **Foreground only.** No background input injection — that's deliberate, it's the part anti-cheat
  actually cares about. Works while Genshin is focused; that's it.
- **Input-only**, no process/memory access — same lane as a hardware macro.
- This is **not** an officially-blessed tool. HoYoverse's ToS has broad anti-automation language,
  so use it thoughtfully and at your own risk. 🙏
- Thresholds are tuned for **1080p** — other resolutions? Re-run `calibrate.py`. 🎚️

<div align="center">

<br>

*made for cozy questing 🍃*

</div>

