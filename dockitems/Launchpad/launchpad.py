import tkinter as tk
from tkinter import PhotoImage
import subprocess
import os
import win32com.client
from PIL import Image, ImageTk
import win32gui
import win32con
import win32ui
import pythoncom

# ========================
# --- Configuration ---
# ========================


DESKTOP = os.path.join(os.path.expanduser("~"), "projects") 
DOCK_DIR = os.path.join(DESKTOP, "Dock")

LAUNCHPAD_DIR = os.path.join(DOCK_DIR, "LaunchpadApps")
COLUMNS = 4
ROWS = 5
ICONS_PER_PAGE = COLUMNS * ROWS
ICON_CACHE = {}

os.makedirs(LAUNCHPAD_DIR, exist_ok=True)

# ========================
# --- Utility Functions ---
# ========================

def extract_icon(exe_path, save_to):
    """Extract a 64x64 icon from an exe file."""
    try:
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        hicon = large[0] if large else (small[0] if small else None)
        if not hicon:
            return False

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 64, 64)
        hdc_temp = hdc.CreateCompatibleDC()
        hdc_temp.SelectObject(hbmp)
        win32gui.DrawIconEx(hdc_temp.GetHandleOutput(), 0, 0, hicon, 64, 64, 0, None, win32con.DI_NORMAL)
        hbmp.SaveBitmapFile(hdc_temp, save_to)
        win32gui.DestroyIcon(hicon)
        return True
    except Exception as e:
        print(f"[ICON] Failed to extract from {exe_path}: {e}")
        return False

def resolve_shortcut(path):
    """Resolve a Windows .lnk shortcut."""
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        return {
            "target": shortcut.Targetpath,
            "arguments": shortcut.Arguments,
            "working_dir": shortcut.WorkingDirectory
        }
    except Exception as e:
        print(f"[SHORTCUT] Failed to resolve {path}: {e}")
        return None

# ========================
# --- UWP / Shell Apps ---
# ========================

def get_uwp_apps():
    """Return a list of all apps from shell:AppsFolder."""
    pythoncom.CoInitialize()
    apps_list = []
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        apps_folder = shell.Namespace("shell:AppsFolder")
        for item in apps_folder.Items():
            try:
                name = item.Name
                apps_list.append({
                    "name": name,
                    "uwp_item": item,
                    "icon": os.path.join(DOCK_DIR, "default.png"),
                    "target": None,
                    "arguments": "",
                    "working_dir": None
                })
            except Exception:
                continue
    except Exception as e:
        print(f"[UWP] Failed to enumerate shell:AppsFolder: {e}")
    return apps_list

def launch_uwp(app_item):
    """Launch a UWP app from shell:AppsFolder item."""
    try:
        app_item.InvokeVerb("Open")
    except Exception as e:
        print(f"[UWP LAUNCH] Failed: {e}")

# ========================
# --- Load Apps ---
# ========================

def load_apps_from_folder():
    apps = []

    # Always include File Explorer
    explorer_icon = os.path.join(DOCK_DIR, "explorer.png")
    apps.append({
        "name": "File Explorer",
        "icon": explorer_icon if os.path.exists(explorer_icon) else os.path.join(DOCK_DIR, "default.png"),
        "target": "explorer",
        "arguments": "",
        "working_dir": None
    })

    # Scan LaunchpadApps folder
    for filename in os.listdir(LAUNCHPAD_DIR):
        file_path = os.path.join(LAUNCHPAD_DIR, filename)
        ext = filename.lower().split(".")[-1]

        if ext not in ("lnk", "exe", "bat", "cmd", "url"):
            continue

        resolved = None
        if ext == "lnk":
            resolved = resolve_shortcut(file_path)
            if not resolved or not resolved["target"]:
                continue
            target = resolved["target"]
            arguments = resolved.get("arguments", "")
            working_dir = resolved.get("working_dir", None)
        else:
            target = file_path
            arguments = ""
            working_dir = None

        name = os.path.splitext(filename)[0]
        icon_path = os.path.join(DOCK_DIR, f"{name.lower()}.png")

        if not os.path.exists(icon_path):
            tmp_bmp = os.path.join(DOCK_DIR, f"{name.lower()}_tmp.bmp")
            if extract_icon(target, tmp_bmp):
                try:
                    Image.open(tmp_bmp).convert("RGBA").save(icon_path)
                except Exception as e:
                    print(f"[ICON] Failed to convert {name}: {e}")
                finally:
                    os.remove(tmp_bmp)

        if not os.path.exists(icon_path):
            icon_path = os.path.join(DOCK_DIR, "default.png")

        apps.append({
            "name": name,
            "icon": icon_path,
            "target": target,
            "arguments": arguments,
            "working_dir": working_dir
        })

    # Add UWP apps
    apps.extend(get_uwp_apps())
    return apps

# ========================
# --- Launch App ---
# ========================

def launch_app(app):
    try:
        if "uwp_item" in app and app["uwp_item"] is not None:
            launch_uwp(app["uwp_item"])
            return

        target = app.get("target")
        args = app.get("arguments", "")
        wd = app.get("working_dir", None)
        if not target:
            return

        system32 = os.path.join(os.environ['WINDIR'], 'System32')
        if os.path.isfile(os.path.join(system32, target)):
            target = os.path.join(system32, target)

        ext = os.path.splitext(target)[1].lower()

        if os.path.isdir(target):
            cmd = f'start "" "{target}"'
        elif target.lower() in ("cmd.exe", "powershell.exe", "taskmgr.exe"):
            cmd = f'start "" "{target}"'
        else:
            cmd = f'start "" "{target}" {args}'

        subprocess.Popen(cmd, shell=True, cwd=wd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        root.destroy()
    except Exception as e:
        print(f"[LAUNCH] Failed to run {app.get('name','Unknown')}: {e}")

# ========================
# --- GUI Setup ---
# ========================

root = tk.Tk()
root.title("Launchpad")
root.attributes("-fullscreen", True)

TRANSPARENT_KEY_COLOR = 'gray1'
root.configure(bg=TRANSPARENT_KEY_COLOR)
root.attributes('-transparentcolor', TRANSPARENT_KEY_COLOR)
root.attributes("-alpha", 0.95)
root.bind("<Escape>", lambda e: root.destroy())

SCREEN_WIDTH = root.winfo_screenwidth()
SCREEN_HEIGHT = root.winfo_screenheight()
ICON_SIZE = max(64, SCREEN_WIDTH // (COLUMNS * 5))
HOVER_SIZE = int(ICON_SIZE * 1.25)

grid_frame = tk.Frame(root, bg="#1a1a1a", highlightthickness=0)
grid_frame.place(relx=0.5, rely=0.55, anchor="center", relwidth=1, relheight=1.1)

search_var = tk.StringVar()
search_bar = tk.Entry(
    root,
    textvariable=search_var,
    font=("Segoe UI", 18, "bold"),
    bd=2,
    relief="flat",
    highlightthickness=3,
    highlightbackground="#555",
    highlightcolor="#007aff",
    justify="center",
    bg="white",
    fg="black"
)
search_bar.place(relx=0.5, rely=0.0, anchor="n", relwidth=0.6, height=40)

# ========================
# --- UI Logic ---
# ========================

def get_icon(path, size):
    key = (path, size)
    if key not in ICON_CACHE:
        try:
            img = Image.open(path).resize((size, size), Image.Resampling.LANCZOS)
            ICON_CACHE[key] = ImageTk.PhotoImage(img)
        except Exception:
            ICON_CACHE[key] = None
    return ICON_CACHE[key]

current_page = 0
filtered_apps = []

BUTTON_STYLE = {
    "bg": "#f0f0f0",
    "fg": "#000000",
    "activebackground": "#e5e5e5",
    "activeforeground": "#000000",
    "font": ("San Francisco", 12, "bold"),
    "relief": "flat",
    "bd": 0,
    "highlightthickness": 0,
    "cursor": "hand2"
}

def style_hover(btn, normal_bg, hover_bg):
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=normal_bg))

def show_page(page):
    global current_page
    current_page = page
    for w in grid_frame.winfo_children():
        w.destroy()

    start_idx = page * ICONS_PER_PAGE
    end_idx = start_idx + ICONS_PER_PAGE
    page_apps = filtered_apps[start_idx:end_idx]

    spacing_x = SCREEN_WIDTH // (COLUMNS + 1)
    spacing_y = 180
    start_y = 150

    for idx, app in enumerate(page_apps):
        row, col = divmod(idx, COLUMNS)
        icon_normal = get_icon(app["icon"], ICON_SIZE)
        icon_hover = get_icon(app["icon"], HOVER_SIZE)
        if not icon_normal:
            continue

        btn = tk.Button(
            grid_frame,
            text=app["name"],
            image=icon_normal,
            compound="top",
            width=ICON_SIZE + 20,
            height=ICON_SIZE + 30,
            command=lambda a=app: launch_app(a),
            bg="#2e2e2e",
            fg="white",
            activebackground="#444",
            relief="flat",
            font=("Segoe UI", 10)
        )
        btn.bind("<Enter>", lambda e, b=btn, img=icon_hover: b.config(image=img, bg="#3a3a3a"))
        btn.bind("<Leave>", lambda e, b=btn, img=icon_normal: b.config(image=img, bg="#2e2e2e"))

        x = spacing_x * (col + 1)
        y = start_y + row * spacing_y
        btn.place(x=x, y=y, anchor="center")

    # Page navigation
    if page > 0:
        prev_btn = tk.Button(grid_frame, text="← Prev", **BUTTON_STYLE)
        prev_btn.place(x=100, y=SCREEN_HEIGHT-80, anchor="w")
        prev_btn.config(command=lambda: show_page(page-1))
        style_hover(prev_btn, BUTTON_STYLE["bg"], "#dcdcdc")

    if end_idx < len(filtered_apps):
        next_btn = tk.Button(grid_frame, text="Next →", **BUTTON_STYLE)
        next_btn.place(x=SCREEN_WIDTH-100, y=SCREEN_HEIGHT-80, anchor="e")
        next_btn.config(command=lambda: show_page(page+1))
        style_hover(next_btn, BUTTON_STYLE["bg"], "#dcdcdc")

def update_search(event=None):
    global filtered_apps
    query = search_var.get().lower()
    filtered_apps = [a for a in apps if query in a["name"].lower()]
    show_page(0)

# --- Initialize ---
apps = load_apps_from_folder()
update_search()
search_bar.bind("<KeyRelease>", update_search)

# --- Start Tkinter ---
root.mainloop()
