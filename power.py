# file: power_menu.py
import tkinter as tk
import subprocess
import os
import sys
import platform

# --- Config ---
BG_COLOR = "#1C1C1C"
HOVER_COLOR = "#333333"
TEXT_COLOR = "white"
FONT = ("Segoe UI", 12, "bold")
OPACITY = 0.95
WINDOW_SIZE = (300, 270)


def safe_run(cmd: str):
    """Run system commands safely."""
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}", file=sys.stderr)


def power_off():
    safe_run("shutdown /s /t 0")


def restart():
    safe_run("shutdown /r /t 0")


def sleep():
    safe_run("rundll32.exe powrprof.dll,SetSuspendState Sleep")


def log_off():
    safe_run("shutdown /l")


def make_button(root, text, command):
    """Custom label-based button with hover effect."""
    btn = tk.Label(
        root,
        text=text,
        bg=BG_COLOR,
        fg=TEXT_COLOR,
        font=FONT,
        width=20,
        height=2,
        relief="flat",
    )
    btn.pack(pady=5)

    btn.bind("<Enter>", lambda e: btn.config(bg=HOVER_COLOR))
    btn.bind("<Leave>", lambda e: btn.config(bg=BG_COLOR))
    btn.bind("<Button-1>", lambda e: command())

    return btn


def create_window():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", OPACITY)
    root.configure(bg=BG_COLOR)

    # --- Position window in top-right corner ---
    w, h = WINDOW_SIZE
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = screen_w - w - 75   # 20px from right edge
    y = 100                  # 20px from top edge
    root.geometry(f"{w}x{h}+{x}+{y}")

    # --- Add window drag ---
    def start_drag(event):
        root._drag_x, root._drag_y = event.x, event.y

    def do_drag(event):
        x = root.winfo_pointerx() - root._drag_x
        y = root.winfo_pointery() - root._drag_y
        root.geometry(f"+{x}+{y}")

    root.bind("<Button-1>", start_drag)
    root.bind("<B1-Motion>", do_drag)
    root.bind("<Escape>", lambda e: root.destroy())

    return root


def main():
    if platform.system() != "Windows":
        print("⚠️ Windows-only tool.")
        sys.exit(1)

    root = create_window()

    make_button(root, "Power Off", power_off)
    make_button(root, "Restart", restart)
    make_button(root, "Sleep", sleep)
    make_button(root, "Log Out", log_off)
    make_button(root, "Cancel", root.destroy)

    root.mainloop()


if __name__ == "__main__":
    main()
