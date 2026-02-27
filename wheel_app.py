"""Ultimate Crazy RGB Spin Wheel desktop app.

Run:
    python wheel_app.py

Build Windows exe (from Windows):
    pyinstaller --noconfirm --onefile --windowed --name CrazyWheel wheel_app.py
"""

from __future__ import annotations

import json
import math
import random
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

RGB_COLORS = [
    "#ff1744",
    "#f50057",
    "#d500f9",
    "#651fff",
    "#3d5afe",
    "#2979ff",
    "#00b0ff",
    "#00e5ff",
    "#1de9b6",
    "#00e676",
    "#76ff03",
    "#c6ff00",
    "#ffea00",
    "#ffc400",
    "#ff9100",
    "#ff3d00",
]


@dataclass
class WheelEntry:
    name: str
    color: str
    weight: int = 1


def expanded_entries(entries: list[WheelEntry]) -> list[WheelEntry]:
    """Expand entries according to weight for fair weighted selection."""
    bag: list[WheelEntry] = []
    for item in entries:
        bag.extend([item] * max(1, item.weight))
    return bag


def pick_winner(entries: list[WheelEntry], stop_angle: float) -> WheelEntry:
    """Return the weighted entry under the top pointer for a given wheel angle."""
    if not entries:
        raise ValueError("entries must not be empty")
    weighted = expanded_entries(entries)
    slice_angle = 360 / len(weighted)
    normalized = stop_angle % 360
    relative = (90 - normalized) % 360
    index = int(relative // slice_angle) % len(weighted)
    return weighted[index]


class CrazyWheelApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Ultimate Crazy RGB Spin Wheel")
        self.root.geometry("1120x720")
        self.root.minsize(980, 660)

        self.entries: list[WheelEntry] = []
        self.angle = 0.0
        self.spinning = False
        self._bg_index = 0
        self._spin_job: str | None = None

        self.name_var = tk.StringVar()
        self.weight_var = tk.IntVar(value=1)
        self.search_var = tk.StringVar()
        self.muted = tk.BooleanVar(value=False)
        self.auto_remove = tk.BooleanVar(value=False)
        self.spin_seconds = tk.DoubleVar(value=4.8)
        self.result_var = tk.StringVar(value="Winner appears here")

        self._build_ui()
        self._bind_shortcuts()
        self._rgb_background_loop()
        self._seed_entries()

    def _build_ui(self) -> None:
        self.root.configure(bg="#0f0f10")

        shell = tk.Frame(self.root, bg="#0f0f10", padx=12, pady=12)
        shell.pack(fill="both", expand=True)

        left = tk.Frame(shell, bg="#141518", padx=12, pady=12)
        left.pack(side="left", fill="y")

        right = tk.Frame(shell, bg="#141518", padx=12, pady=12)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="🎡 Ultimate Wheel", bg="#141518", fg="#ffffff", font=("Segoe UI", 21, "bold")).pack(anchor="w")

        row = tk.Frame(left, bg="#141518")
        row.pack(fill="x", pady=(12, 6))

        self.input_name = tk.Entry(row, textvariable=self.name_var, font=("Segoe UI", 12), width=18)
        self.input_name.pack(side="left", padx=(0, 6))
        self.input_name.bind("<Return>", lambda _: self.add_name())

        tk.Spinbox(row, from_=1, to=10, textvariable=self.weight_var, width=4, font=("Segoe UI", 11)).pack(side="left", padx=(0, 6))
        tk.Button(row, text="Add", command=self.add_name, bg="#00c853", fg="white", font=("Segoe UI", 11, "bold")).pack(side="left")

        tk.Label(left, text="Weight improves odds. Double-click name to remove.", bg="#141518", fg="#b0bec5", font=("Segoe UI", 9)).pack(anchor="w")

        search_row = tk.Frame(left, bg="#141518")
        search_row.pack(fill="x", pady=(8, 6))
        tk.Label(search_row, text="Filter", bg="#141518", fg="#eceff1").pack(side="left", padx=(0, 6))
        tk.Entry(search_row, textvariable=self.search_var, width=16).pack(side="left")
        self.search_var.trace_add("write", lambda *_: self.refresh_list())

        self.listbox = tk.Listbox(left, width=34, height=16, font=("Consolas", 11), activestyle="none")
        self.listbox.pack(fill="both", pady=(0, 8))
        self.listbox.bind("<Double-Button-1>", self.remove_selected)

        controls = tk.Frame(left, bg="#141518")
        controls.pack(fill="x")

        self.spin_button = tk.Button(controls, text="⚡ CRAZY SPIN ⚡", command=self.spin, bg="#ff1744", fg="white", font=("Segoe UI", 12, "bold"))
        self.spin_button.pack(fill="x", pady=(0, 6))

        tk.Scale(
            controls,
            variable=self.spin_seconds,
            from_=2.0,
            to=8.0,
            resolution=0.1,
            orient="horizontal",
            label="Spin seconds",
            bg="#141518",
            fg="#eceff1",
            troughcolor="#263238",
            highlightthickness=0,
        ).pack(fill="x", pady=(0, 4))

        toggles = tk.Frame(controls, bg="#141518")
        toggles.pack(fill="x", pady=(0, 4))
        tk.Checkbutton(toggles, text="Mute", variable=self.muted, bg="#141518", fg="#eceff1", selectcolor="#263238").pack(side="left")
        tk.Checkbutton(toggles, text="Auto-remove winner", variable=self.auto_remove, bg="#141518", fg="#eceff1", selectcolor="#263238").pack(side="left", padx=8)

        btn_row = tk.Frame(controls, bg="#141518")
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Shuffle Colors", command=self.shuffle_colors, bg="#546e7a", fg="white").pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(btn_row, text="Clear", command=self.clear_names, bg="#546e7a", fg="white").pack(side="left", fill="x", expand=True)

        io_row = tk.Frame(controls, bg="#141518")
        io_row.pack(fill="x", pady=(6, 0))
        tk.Button(io_row, text="Save", command=self.save_names, bg="#455a64", fg="white").pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(io_row, text="Load", command=self.load_names, bg="#455a64", fg="white").pack(side="left", fill="x", expand=True)

        self.result = tk.Label(left, textvariable=self.result_var, bg="#141518", fg="#ffee58", font=("Segoe UI", 13, "bold"), wraplength=300, justify="left")
        self.result.pack(fill="x", pady=(12, 2))

        self.history = tk.Text(left, height=6, width=36, bg="#111318", fg="#b2dfdb", font=("Consolas", 10))
        self.history.pack(fill="x", pady=(4, 0))
        self.history.insert("end", "Win history:\n")
        self.history.configure(state="disabled")

        self.canvas = tk.Canvas(right, width=700, height=650, bg="#0b0c0f", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.draw_wheel())

        self._draw_pointer()

    def _bind_shortcuts(self) -> None:
        self.root.bind("<space>", lambda _: self.spin())
        self.root.bind("<Control-s>", lambda _: self.save_names())
        self.root.bind("<Control-o>", lambda _: self.load_names())

    def _seed_entries(self) -> None:
        seeds = [("Alex", 1), ("Jordan", 2), ("Casey", 1), ("Riley", 3), ("Morgan", 1)]
        for name, weight in seeds:
            self.entries.append(WheelEntry(name=name, color=self._random_color(), weight=weight))
        self.refresh_list()
        self.draw_wheel()

    def _random_color(self) -> str:
        return random.choice(RGB_COLORS)

    def _darken(self, color: str, factor: float) -> str:
        color = color.lstrip("#")
        r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"

    def _rgb_background_loop(self) -> None:
        self._bg_index = (self._bg_index + 1) % len(RGB_COLORS)
        glow = self._darken(RGB_COLORS[self._bg_index], 0.18)
        self.canvas.configure(bg=glow)
        self.root.after(95, self._rgb_background_loop)

    def _filtered_entries(self) -> list[WheelEntry]:
        q = self.search_var.get().strip().lower()
        if not q:
            return self.entries
        return [e for e in self.entries if q in e.name.lower()]

    def add_name(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            self._sound_warn()
            return
        weight = max(1, int(self.weight_var.get()))
        self.entries.append(WheelEntry(name=name, color=self._random_color(), weight=weight))
        self.name_var.set("")
        self.refresh_list()
        self.draw_wheel()
        self._sound_add()

    def remove_selected(self, _event: tk.Event | None = None) -> None:
        if not self.listbox.curselection():
            return
        selected = self.listbox.get(self.listbox.curselection()[0])
        name = selected.split("  ")[0]
        for i, entry in enumerate(self.entries):
            if entry.name == name:
                removed = self.entries.pop(i)
                self.result_var.set(f"Removed: {removed.name}")
                self._sound_remove()
                break
        self.refresh_list()
        self.draw_wheel()

    def clear_names(self) -> None:
        self.entries.clear()
        self.refresh_list()
        self.draw_wheel()
        self.result_var.set("All names removed")
        self._sound_remove()

    def shuffle_colors(self) -> None:
        for entry in self.entries:
            entry.color = self._random_color()
        self.draw_wheel()
        self.result_var.set("Colors shuffled")
        self._sound_add()

    def refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for item in self._filtered_entries():
            self.listbox.insert(tk.END, f"{item.name}  (w={item.weight})")

    def save_names(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save wheel entries",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        data = [entry.__dict__ for entry in self.entries]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.result_var.set(f"Saved {len(self.entries)} entries")

    def load_names(self) -> None:
        path = filedialog.askopenfilename(title="Load wheel entries", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.entries = [
                WheelEntry(name=str(item["name"]), color=str(item.get("color", self._random_color())), weight=max(1, int(item.get("weight", 1))))
                for item in data
                if isinstance(item, dict) and item.get("name")
            ]
        except Exception as exc:
            messagebox.showerror("Load failed", f"Could not load file:\n{exc}")
            self._sound_warn()
            return
        self.refresh_list()
        self.draw_wheel()
        self.result_var.set(f"Loaded {len(self.entries)} entries")

    def _draw_pointer(self) -> None:
        w = self.canvas.winfo_width() or 700
        self.canvas.delete("pointer")
        x = w // 2
        self.canvas.create_polygon(x, 20, x - 16, 52, x + 16, 52, fill="#fffde7", outline="#ffe082", width=2, tags="pointer")

    def draw_wheel(self) -> None:
        self.canvas.delete("wheel")
        if not self.entries:
            self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, text="Add names to spin", fill="#eceff1", font=("Segoe UI", 28, "bold"), tags="wheel")
            self._draw_pointer()
            return

        weighted = expanded_entries(self.entries)
        w = self.canvas.winfo_width() or 700
        h = self.canvas.winfo_height() or 650
        cx, cy = w // 2, h // 2 + 18
        radius = min(w, h) // 2 - 42
        slice_angle = 360 / len(weighted)

        for i, item in enumerate(weighted):
            start = self.angle + i * slice_angle
            self.canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=start, extent=slice_angle, fill=item.color, outline="#101010", width=2, tags="wheel")

            mid = math.radians(-(start + slice_angle / 2))
            tx = cx + math.cos(mid) * (radius * 0.70)
            ty = cy + math.sin(mid) * (radius * 0.70)
            text = item.name if len(item.name) <= 11 else item.name[:10] + "…"
            self.canvas.create_text(tx, ty, text=text, fill="white", font=("Segoe UI", 10, "bold"), angle=-(start + slice_angle / 2), tags="wheel")

        self.canvas.create_oval(cx - 32, cy - 32, cx + 32, cy + 32, fill="#fafafa", outline="#455a64", width=4, tags="wheel")
        self._draw_pointer()

    def spin(self) -> None:
        if self.spinning:
            return
        if len(self.entries) < 2:
            messagebox.showinfo("Need more names", "Add at least 2 names before spinning.")
            self._sound_warn()
            return

        self.spinning = True
        self.spin_button.configure(state="disabled")
        self.result_var.set("Spinning at maximum chaos...")

        duration = self.spin_seconds.get()
        total_frames = max(120, int(duration * 60))
        final_boost = random.uniform(0, 540)

        def frame(step: int) -> None:
            if step >= total_frames:
                self._end_spin()
                return
            t = step / total_frames
            ease_out = (1 - t) ** 2.5
            velocity = ease_out * 34 + 0.65
            self.angle = (self.angle + velocity + final_boost / total_frames) % 360
            self.draw_wheel()
            self._sound_tick(step)
            self._spin_job = self.root.after(16, lambda: frame(step + 1))

        frame(0)

    def _append_history(self, winner: WheelEntry) -> None:
        self.history.configure(state="normal")
        self.history.insert("end", f"• {winner.name} (w={winner.weight})\n")
        self.history.see("end")
        self.history.configure(state="disabled")

    def _end_spin(self) -> None:
        self.spinning = False
        self.spin_button.configure(state="normal")
        winner = pick_winner(self.entries, self.angle)
        self.result_var.set(f"🎉 Winner: {winner.name} (weight {winner.weight}) 🎉")
        self._append_history(winner)
        self._flash_winner(winner.color)
        self._sound_win()

        if self.auto_remove.get():
            for i, entry in enumerate(self.entries):
                if entry.name == winner.name:
                    self.entries.pop(i)
                    break
            self.refresh_list()
            self.draw_wheel()

    def _flash_winner(self, color: str, pulses: int = 10) -> None:
        def pulse(i: int) -> None:
            if i <= 0:
                self.draw_wheel()
                return
            if i % 2 == 0:
                w = self.canvas.winfo_width() or 700
                h = self.canvas.winfo_height() or 650
                self.canvas.create_oval(28, 40, w - 28, h - 24, outline=color, width=9, tags="wheel")
            else:
                self.draw_wheel()
            self.root.after(72, lambda: pulse(i - 1))

        pulse(pulses)

    def _beep(self) -> None:
        if not self.muted.get():
            self.root.bell()

    def _sound_add(self) -> None:
        self._beep()

    def _sound_remove(self) -> None:
        self._beep()
        self.root.after(50, self._beep)

    def _sound_warn(self) -> None:
        self._beep()
        self.root.after(50, self._beep)
        self.root.after(100, self._beep)

    def _sound_tick(self, step: int) -> None:
        if step % 4 == 0:
            self._beep()

    def _sound_win(self) -> None:
        for i in range(6):
            self.root.after(i * 82, self._beep)


def main() -> None:
    root = tk.Tk()
    app = CrazyWheelApp(root)
    app.draw_wheel()
    root.mainloop()


if __name__ == "__main__":
    main()
