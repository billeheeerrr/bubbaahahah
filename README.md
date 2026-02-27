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

## Build executable locally

```bash
pip install pyinstaller
python build_exe.py
```

- On Windows this produces `dist/CrazyWheel.exe`.
- On Linux/macOS this produces a native executable (`dist/CrazyWheel`) and prints a note.

## Get a downloadable Windows EXE (GitHub Actions)

A workflow is included at `.github/workflows/build-exe.yml`.

1. Push this branch to GitHub.
2. Open **Actions** → **Build Windows EXE**.
3. Run workflow.
4. Download artifact `CrazyWheel-windows-exe` (zip containing `CrazyWheel.exe`).

## Test

```bash
pytest -q
```
