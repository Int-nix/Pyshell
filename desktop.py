import os
import json
import time
import tkinter as tk
from tkinter import Menu
from PIL import Image, ImageTk
import subprocess

# ==============================
# --- Configuration ---
# ==============================
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
ICON_SIZE = 64
FONT = ("Segoe UI", 10, "bold")
TEXT_COLOR = "#FFFFFF"
ICON_SPACING_X = 130
ICON_SPACING_Y = 120
MARGIN_X = 80
MARGIN_Y = 80
POSITIONS_FILE = os.path.join(os.path.dirname(__file__), "desktop_positions.json")

DEFAULT_ICON_PATH = os.path.join(os.path.dirname(__file__), "default.png")
BACKGROUND_PATH = os.path.join(os.path.dirname(__file__), "BERTAPOINT.jpg")

# ==============================
# --- Window Setup ---
# ==============================
root = tk.Tk()
root.title("Nebula Desktop")
root.attributes("-fullscreen", True)
root.configure(bg="black")

# Hide Windows taskbar
try:
    import win32gui, win32con
    taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
    win32gui.ShowWindow(taskbar, win32con.SW_HIDE)
except Exception:
    taskbar = None

# ==============================
# --- Background ---
# ==============================
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

try:
    bg_raw = Image.open(BACKGROUND_PATH).resize((screen_w, screen_h), Image.LANCZOS)
    bg_img = ImageTk.PhotoImage(bg_raw)
    canvas = tk.Canvas(root, width=screen_w, height=screen_h, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_img, anchor="nw")
except Exception:
    canvas = tk.Canvas(root, bg="#1E1E1E", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

# ==============================
# --- Load Saved Positions ---
# ==============================
if os.path.exists(POSITIONS_FILE):
    with open(POSITIONS_FILE, "r") as f:
        saved_positions = json.load(f)
else:
    saved_positions = {}

# ==============================
# --- Helper Functions ---
# ==============================
def open_item(path):
    try:
        if os.path.isdir(path):
            subprocess.Popen(f'explorer "{path}"')
        else:
            os.startfile(path)
    except Exception as e:
        print(f"Failed to open {path}: {e}")

def save_positions():
    with open(POSITIONS_FILE, "w") as f:
        json.dump(saved_positions, f, indent=2)

# --- Context Menu Logic ---
def show_context_menu(event, path):
    """Creates and displays a right-click context menu for a file/folder."""
    menu = Menu(root, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#444", activeforeground="white")

    is_dir = os.path.isdir(path)
    ext = os.path.splitext(path)[1].lower()

    menu_items = ["Open", "Copy Path", "Delete", "Rename"]
    if is_dir:
        menu_items += ["Open in Explorer", "New File", "New Folder"]
    else:
        if ext in (".py", ".txt", ".json", ".html", ".js"):
            menu_items.append("Edit")
        if ext in (".zip", ".tar", ".gz"):
            menu_items.append("Extract Here")

    # --- Command actions ---
    def run_action(action):
        if action == "Open":
            open_item(path)
        elif action == "Edit":
            subprocess.Popen(["notepad", path])
        elif action == "Copy Path":
            root.clipboard_clear()
            root.clipboard_append(path)
            print(f"📋 Copied path: {path}")
        elif action == "Delete":
            try:
                if os.path.isdir(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
                print(f"🗑️ Deleted {path}")
                root.destroy()  # Refresh for simplicity
                os.system(f'python "{__file__}"')
            except Exception as e:
                print(f"⚠️ Failed to delete {path}: {e}")
        elif action == "Rename":
            new_name = tk.simpledialog.askstring("Rename", "Enter new name:")
            if new_name:
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
                print(f"✏️ Renamed to {new_name}")
                root.destroy()
                os.system(f'python "{__file__}"')
        elif action == "Open in Explorer":
            subprocess.Popen(f'explorer "{path}"')
        elif action == "New File":
            new_file = os.path.join(path, "newfile.txt")
            with open(new_file, "w") as f:
                f.write("")
            print(f"📄 Created: {new_file}")
            root.destroy()
            os.system(f'python "{__file__}"')
        elif action == "New Folder":
            new_folder = os.path.join(path, "NewFolder")
            os.makedirs(new_folder, exist_ok=True)
            print(f"📁 Created folder: {new_folder}")
            root.destroy()
            os.system(f'python "{__file__}"')
        elif action == "Extract Here":
            import zipfile
            try:
                with zipfile.ZipFile(path, "r") as zip_ref:
                    zip_ref.extractall(os.path.dirname(path))
                print(f"📦 Extracted {path}")
            except Exception as e:
                print(f"⚠️ Extraction failed: {e}")

    for item in menu_items:
        menu.add_command(label=item, command=lambda i=item: run_action(i))

    menu.tk_popup(event.x_root, event.y_root)

# ==============================
# --- Desktop Icon Class ---
# ==============================
class DesktopIcon:
    def __init__(self, name, path, x, y):
        self.name = name
        self.path = path
        self.x = x
        self.y = y
        self.last_click_time = 0
        self.create_icon()

    def create_icon(self):
        img_raw = Image.open(DEFAULT_ICON_PATH).resize((ICON_SIZE, ICON_SIZE))
        self.icon_img = ImageTk.PhotoImage(img_raw)

        # --- Icon ---
        self.icon_btn = tk.Label(root, image=self.icon_img, bg="#000000", borderwidth=0)
        self.label = tk.Label(root, text=self.name, font=FONT, fg=TEXT_COLOR, bg="#000000",
                              wraplength=ICON_SIZE * 2, justify="center")

        self.icon_window = canvas.create_window(self.x, self.y, window=self.icon_btn, anchor="nw")
        self.label_window = canvas.create_window(self.x + ICON_SIZE // 2 - 30,
                                                 self.y + ICON_SIZE + 5,
                                                 window=self.label, anchor="nw")

        # --- Event bindings ---
        for widget in (self.icon_btn, self.label):
            widget.bind("<ButtonPress-1>", self.on_click)
            widget.bind("<B1-Motion>", self.do_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<Button-3>", self.on_right_click)  # Right-click

        self.drag_data = {"x": 0, "y": 0}
        self.dragging = False

    def on_click(self, event):
        now = time.time()
        if now - self.last_click_time < 0.4:
            open_item(self.path)
        self.last_click_time = now
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.dragging = True

    def do_drag(self, event):
        if not self.dragging:
            return
        dx, dy = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
        self.x += dx
        self.y += dy
        canvas.move(self.icon_window, dx, dy)
        canvas.move(self.label_window, dx, dy)

    def stop_drag(self, event):
        if self.dragging:
            self.dragging = False
            saved_positions[self.name] = {"x": self.x, "y": self.y}
            save_positions()

    def on_right_click(self, event):
        show_context_menu(event, self.path)

# ==============================
# --- Create Desktop Icons ---
# ==============================
try:
    desktop_items = os.listdir(DESKTOP_PATH)
except FileNotFoundError:
    desktop_items = []

x, y = MARGIN_X, MARGIN_Y
icons = []

for i, item in enumerate(desktop_items):
    path = os.path.join(DESKTOP_PATH, item)
    if item in saved_positions:
        pos = saved_positions[item]
        x, y = pos["x"], pos["y"]
    else:
        col, row = i % 8, i // 8
        x = MARGIN_X + col * ICON_SPACING_X
        y = MARGIN_Y + row * ICON_SPACING_Y
    icon = DesktopIcon(item, path, x, y)
    icons.append(icon)

# ==============================
# --- Exit Shortcut ---
# ==============================
def exit_fullscreen(event=None):
    if taskbar:
        try:
            win32gui.ShowWindow(taskbar, win32con.SW_SHOW)
        except Exception:
            pass
    root.destroy()

root.bind("<Escape>", exit_fullscreen)
root.mainloop()
