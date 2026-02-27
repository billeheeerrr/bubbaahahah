"""Local build helper for creating a distributable executable with PyInstaller."""

from __future__ import annotations

import os
import platform
import subprocess
import sys


def main() -> int:
    exe_name = "CrazyWheel.exe" if os.name == "nt" else "CrazyWheel"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        exe_name,
        "wheel_app.py",
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        return result.returncode

    target = f"dist/{exe_name}"
    print(f"Built executable at: {target}")
    if platform.system() != "Windows":
        print("Note: On non-Windows systems this produces a native binary, not a Windows .exe.")
        print("Use the GitHub Actions workflow to generate a real downloadable Windows EXE artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
