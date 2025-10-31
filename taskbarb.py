import tkinter as tk
import subprocess
import os
import ctypes
import win32gui
import win32con
import win32ui
from PIL import Image, ImageTk

# ==============================
# --- Configuration ---
# ==============================
ICON_SIZE = 48
HOVER_SIZE = 52
SPACING = 10
REFRESH_INTERVAL = 400
OPACITY = 0.9
BG_COLOR = "#1C1C1C"
HIDE_DELAY = 1500
HOVER_AREA_HEIGHT = 50

DESKTOP = os.path.join(os.path.expanduser("~"), "projects")
DOCK_DIR = os.path.join(DESKTOP, "Dock")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ICON_PATH = os.path.join(BASE_DIR, "default.png")

BLACKLIST_TITLES = {
    "Program Manager", "tk", "Launchpad", "Settings",
    "Steam Properties", "Windows Shell Experience Host",
    "Back", "PopUp", "taskbar.py", "Nebula Desktop",
}

RECOGNIZED_PROGRAMS = {
    "Notepad": "notepad.png",
    "Calculator": "calculator.png",
    "Chrome": "chrome.png",
    "Edge": "edge.png",
    "Paint": "paint.png",
    "Spotify": "spotify.png",
    "Notepad++": "notepad.png",
    "Discord": "discord.png"
}
RECOGNIZED_PROGRAMS = {k: os.path.join(BASE_DIR, v) for k, v in RECOGNIZED_PROGRAMS.items()}

# ==============================
# --- Utility Functions ---
# ==============================
def launch(cmd):
    if callable(cmd):
        cmd()
    else:
        subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_taskbar_window(hwnd):
    if not win32gui.IsWindowVisible(hwnd):
        return False
    title = win32gui.GetWindowText(hwnd)
    if not title or title in BLACKLIST_TITLES:
        return False
    if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
        return False
    return True

def get_open_windows():
    windows = []
    def enum_callback(hwnd, _):
        if is_taskbar_window(hwnd):
            windows.append((hwnd, win32gui.GetWindowText(hwnd)))
    win32gui.EnumWindows(enum_callback, None)
    return windows

def activate_window(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except:
        pass

# ==============================
# --- Image Cache ---
# ==============================
_image_cache = {}

def load_icon(path, size):
    if not path or not os.path.exists(path):
        path = DEFAULT_ICON_PATH
    key = (path, size)
    if key in _image_cache:
        return _image_cache[key]
    try:
        img = Image.open(path).resize((size, size), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        _image_cache[key] = tk_img
        return tk_img
    except:
        return ImageTk.PhotoImage(Image.new("RGBA", (size, size), (0, 0, 0, 0)))

def get_window_icon(hwnd, size=ICON_SIZE):
    try:
        hicon = (win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0)
                 or win32gui.GetClassLong(hwnd, win32con.GCL_HICONSM))
        if not hicon:
            return None
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, size, size)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, size, size, 0, 0, win32con.DI_NORMAL)
        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer("RGB", (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                               bmpstr, "raw", "BGRX", 0, 1)
        return ImageTk.PhotoImage(img)
    except:
        return None

# ==============================
# --- Dock Setup ---
# ==============================
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", OPACITY)
root.configure(bg=BG_COLOR)

icons_frame = tk.Frame(root, bg=BG_COLOR)
icons_frame.pack(expand=True, fill="both", padx=10, pady=5)

# Tooltip
tooltip = tk.Toplevel(root)
tooltip.overrideredirect(True)
tooltip.attributes("-topmost", True)
tooltip.configure(bg="#333333")
tooltip.withdraw()
tooltip_label = tk.Label(tooltip, text="", bg="#333333", fg="white", font=("Segoe UI", 9))
tooltip_label.pack(padx=5, pady=2)

def show_tooltip(btn, text):
    if hidden:
        return
    tooltip_label.config(text=text)
    tooltip.update_idletasks()
    x = btn.winfo_rootx() + (btn.winfo_width() - tooltip.winfo_reqwidth()) // 2
    y = root.winfo_y() - tooltip.winfo_reqheight() - 8
    tooltip.geometry(f"+{x}+{y}")
    tooltip.deiconify()

def hide_tooltip():
    tooltip.withdraw()

# ==============================
# --- Static Buttons ---
# ==============================
STATIC_APPS = [
    {"name": "Launchpad", "icon": "launchpad.png", "cmd": f'python "{os.path.join(DOCK_DIR, "launchpad.py")}"'},
    {"name": "Explorer", "icon": "explorer.png", "cmd": "explorer"},
    {"name": "Terminal", "icon": "terminal.png", "cmd": "wt"},
    {"name": "Chrome", "icon": "chrome.png", "cmd": "start chrome"},
]

dynamic_buttons = {}
hidden = False
hide_after_id = None

for app in STATIC_APPS:
    path = os.path.join(BASE_DIR, app["icon"])
    normal = load_icon(path, ICON_SIZE)
    hover = load_icon(path, HOVER_SIZE)
    btn = tk.Button(
        icons_frame, image=normal, bg=BG_COLOR, bd=0,
        highlightthickness=0, activebackground=BG_COLOR,
        command=lambda c=app["cmd"]: launch(c)
    )
    btn.pack(side="left", padx=SPACING//2)
    btn.bind("<Enter>", lambda e, b=btn, h=hover, n=app["name"]: [b.config(image=h), show_tooltip(b, n)])
    btn.bind("<Leave>", lambda e, b=btn, n=normal: [b.config(image=n), hide_tooltip()])

# ==============================
# --- Dock Behavior ---
# ==============================
ANIMATION_SPEED = 4
ANIMATION_INTERVAL = 20

def resize_dock():
    root.update_idletasks()
    dock_width = icons_frame.winfo_reqwidth() + 20
    dock_height = ICON_SIZE + 20
    x = (root.winfo_screenwidth() - dock_width) // 2
    y = root.winfo_screenheight() - dock_height - 10
    root.geometry(f"{dock_width}x{dock_height}+{x}+{y}")

def slide_hide():
    y = root.winfo_y()
    target_y = root.winfo_screenheight()
    if y < target_y:
        y = min(y + ANIMATION_SPEED, target_y)
        root.geometry(f"+{root.winfo_x()}+{y}")
        root.after(ANIMATION_INTERVAL, slide_hide)
    else:
        root.withdraw()

def hide_dock():
    global hidden
    if hidden: return
    hidden = True
    hide_tooltip()
    slide_hide()

def slide_show():
    root.deiconify()
    resize_dock()
    target_y = root.winfo_screenheight() - root.winfo_height() - 10
    y = root.winfo_y()
    if y > target_y:
        y = max(y - ANIMATION_SPEED, target_y)
        root.geometry(f"+{root.winfo_x()}+{y}")
        root.after(ANIMATION_INTERVAL, slide_show)
    else:
        update_windows()

def show_dock():
    global hidden
    if not hidden: return
    hidden = False
    slide_show()

def schedule_hide():
    global hide_after_id
    if hide_after_id:
        root.after_cancel(hide_after_id)
    hide_after_id = root.after(5000, hide_dock)

def cancel_hide():
    global hide_after_id
    if hide_after_id:
        root.after_cancel(hide_after_id)
        hide_after_id = None

def check_mouse():
    try:
        x, y = root.winfo_pointerx(), root.winfo_pointery()
        screen_h = root.winfo_screenheight()
        dock_x1, dock_y1 = root.winfo_x(), root.winfo_y()
        dock_x2, dock_y2 = dock_x1 + root.winfo_width(), dock_y1 + root.winfo_height()

        if y >= screen_h - HOVER_AREA_HEIGHT:
            show_dock()
            cancel_hide()
        elif dock_y1 <= y <= dock_y2 and dock_x1 <= x <= dock_x2:
            cancel_hide()
        else:
            if not hidden and not hide_after_id:
                schedule_hide()
    except tk.TclError:
        pass
    root.after(200, check_mouse)

def update_windows():
    if hidden:
        root.after(REFRESH_INTERVAL, update_windows)
        return
    windows = get_open_windows()
    hwnds = {h for h, _ in windows}
    for hwnd in list(dynamic_buttons):
        if hwnd not in hwnds:
            dynamic_buttons[hwnd].destroy()
            del dynamic_buttons[hwnd]
    for hwnd, title in windows:
        if hwnd in dynamic_buttons:
            continue
        icon = None
        for name, path in RECOGNIZED_PROGRAMS.items():
            if name.lower() in title.lower():
                icon = load_icon(path, ICON_SIZE)
                break
        icon = icon or get_window_icon(hwnd) or load_icon(DEFAULT_ICON_PATH, ICON_SIZE)
        btn = tk.Button(
            icons_frame, image=icon, bg=BG_COLOR, bd=0,
            highlightthickness=0, activebackground=BG_COLOR,
            command=lambda h=hwnd: activate_window(h)
        )
        btn.image = icon
        btn.pack(side="left", padx=SPACING//2)
        dynamic_buttons[hwnd] = btn
        btn.bind("<Enter>", lambda e, b=btn, t=title: show_tooltip(b, t))
        btn.bind("<Leave>", lambda e: hide_tooltip())
    resize_dock()
    root.after(REFRESH_INTERVAL, update_windows)

# ==============================
# --- Start ---
# ==============================
check_mouse()
update_windows()
resize_dock()
root.mainloop()
