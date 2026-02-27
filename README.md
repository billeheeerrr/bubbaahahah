# Ultimate Crazy RGB Spin Wheel App

Now upgraded to be much more awesome:
- 🎡 crazy smooth spin wheel animation with adjustable spin duration
- 🌈 RGB-style palette + animated color glow background
- 🔊 sound effects for add/remove/warn/spin/win + mute toggle
- ➕ add names with **weight** (higher weight = higher chance)
- 🖱️ double-click a name to remove it
- 🔎 live name filter
- 🧠 winner history log
- 🗂️ save/load players to JSON
- 🏁 optional auto-remove winner mode
- ⌨️ shortcuts: `Space` spin, `Ctrl+S` save, `Ctrl+O` load

## Run

```bash
python wheel_app.py
```

## Build a Windows EXE

From a Windows machine:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name CrazyWheel wheel_app.py
```

Then run:

```text
dist/CrazyWheel.exe
```

## Test

```bash
pytest -q
```
