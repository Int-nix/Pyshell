import os
import ast
import operator as op
import sys 
import re
import inspect

dock_window = None
dock_thread = None

def register_command(name):
    """Temporary decorator for plugin compatibility."""
    from __main__ import registered_commands
    def wrapper(func):
        registered_commands[name] = func
        return func
    return wrapper

@register_command("cal")
def cal_cmd(args):
    """Evaluate a basic algebra expression using BEDMAS order."""
    if not args:
        print("Usage: cal <expression>")
        print("Example: cal (3 + 4) * 2^3 / 4")
        return

    expression = " ".join(args)

    # Allowed operators (safe evaluation)
    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
        ast.USub: op.neg,
    }

    def eval_expr(node):
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Num):  # numbers
            return node.n
        elif isinstance(node, ast.BinOp):  # binary operation
            left = eval_expr(node.left)
            right = eval_expr(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):  # negative numbers
            return operators[type(node.op)](eval_expr(node.operand))
        else:
            raise TypeError(f"Unsupported expression: {node}")

    try:
        # Replace ^ with ** for exponentiation
        expression = expression.replace("^", "**")

        # Parse safely
        node = ast.parse(expression, mode="eval").body
        result = eval_expr(node)
        print(f"🧮 {expression.replace('**', '^')} = {result}")
    except ZeroDivisionError:
        print("❌ Error: Division by zero.")
    except Exception as e:
        print(f"⚠️ Invalid expression: {e}")
        
@register_command("goto")
def goto_cmd(args):
    """
    Instantly go to any directory or file path from anywhere.
    Usage:
      goto <path>
    Examples:
      goto /Users/owena
      goto ../Desktop
      goto C:\\Projects\\MyApp
    """
    import os

    if not args:
        print("Usage: goto <path>")
        return

    target = args[0]

    # Expand things like ~ or relative paths
    target_path = os.path.expanduser(target)
    target_path = os.path.abspath(target_path)

    if not os.path.exists(target_path):
        print(f"❌ Path not found: {target_path}")
        return

    if os.path.isdir(target_path):
        try:
            os.chdir(target_path)
            print(f"📁 Changed directory to: {target_path}")
        except Exception as e:
            print(f"⚠️ Error changing directory: {e}")
    else:
        print(f"📄 Target is a file: {target_path}")

@register_command("root")
def root_cmd(args):
    """
    Instantly go to the root directory of the system.
    Usage:
      root
    """
    import os

    try:
        # Detect platform and set root path
        root_path = "C:\\" if os.name == "nt" else "/"
        os.chdir(root_path)
        print(f"📁 Changed directory to root: {root_path}")
    except Exception as e:
        print(f"⚠️ Error changing to root directory: {e}")


@register_command("dock")
def dock_cmd(args):
    """
    Stable single-instance PyNix Dock (threaded & folder-based).
    - Each folder in /dockitems represents an app.
      Example:
         /dockitems/chrome/chrome.lnk
         /dockitems/chrome/chrome.png
    - Folder name = tooltip text.
    - Supports: dock left / right / bottom
    - Supports: dock kill → closes the dock.
    """
    import tkinter as tk
    import os, subprocess, pythoncom, win32com.client, time, threading
    from PIL import Image, ImageTk

    global dock_window, dock_thread

    # --- Kill command ---
    if args and args[0].lower() == "kill":
        global dock_window, dock_thread

        def _close_dock():
            try:
                if dock_window and dock_window.winfo_exists():
                    dock_window.quit()
                    dock_window.destroy()
            except Exception:
                pass

        if dock_window:
            try:
                dock_window.after(0, _close_dock)
            except Exception:
                _close_dock()

        if dock_thread and dock_thread.is_alive():
            dock_thread.join(timeout=1.5)

        dock_window = None
        dock_thread = None

        print("🧹 Dock closed.", flush=True)
        return

    # --- Prevent multiple docks ---
    if 'dock_window' in globals() and dock_window and dock_window.winfo_exists():
        dock_window.lift()
        print("🔁 Dock already open; bringing to front.")
        return

    # ---------------- CONFIG ----------------
    ORIENTATION = args[0].lower() if args else "right"
    ICON_SIZE, HOVER_SIZE, SPACING = 48, 56, 8
    BG_COLOR, OPACITY = "#1C1C1C", 0.93

    # ✅ FIX: Get PyTerm root (not command script folder)
    try:
        import __main__
        BASE_DIR = os.path.dirname(os.path.abspath(__main__.__file__))
    except Exception:
        BASE_DIR = os.getcwd()  # fallback if interactive

    DOCKITEMS_DIR = os.path.join(BASE_DIR, "dockitems")
    DEFAULT_ICON_PATH = os.path.join(BASE_DIR, "default.png")
    os.makedirs(DOCKITEMS_DIR, exist_ok=True)

    print(f"🗂 Dock looking in: {DOCKITEMS_DIR}")

    # ---------------- THREAD TARGET ----------------
    def run_dock():
        nonlocal ORIENTATION
        last_state = set()

        # ---------- HELPERS ----------
        def resolve_shortcut(path):
            try:
                pythoncom.CoInitialize()
                link = win32com.client.Dispatch("WScript.Shell").CreateShortcut(path)
                target = link.TargetPath
                return target if os.path.exists(target) else path
            except Exception:
                return path

        def safe_image(path, size):
            try:
                img = Image.open(path).resize((size, size))
            except Exception:
                if os.path.exists(DEFAULT_ICON_PATH):
                    img = Image.open(DEFAULT_ICON_PATH).resize((size, size))
                else:
                    from PIL import ImageDraw
                    img = Image.new("RGBA", (size, size), (90, 90, 90, 255))
                    draw = ImageDraw.Draw(img)
                    draw.text((size//3, size//3), "?", fill="white")
            return img

        def make_photo(img, master):
            return ImageTk.PhotoImage(img, master=master)

        def launch(path):
            try:
                target = resolve_shortcut(path)
                if target.endswith(".py"):
                    subprocess.Popen(["python", target], shell=True)
                else:
                    os.startfile(target)
            except Exception as e:
                print(f"⚠️ Launch failed: {e}")

        # ---------- UI ----------
        root = tk.Tk()
        root.title("PyNix Dock")
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", OPACITY)
        root.configure(bg=BG_COLOR)
        globals()["dock_window"] = root

        frame = tk.Frame(root, bg=BG_COLOR)
        frame.pack(expand=True, fill="both", padx=6, pady=6)
        frame._image_refs = []

        # Tooltip
        tooltip = tk.Toplevel(root)
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        tooltip.configure(bg="#333")
        tooltip.withdraw()
        t_label = tk.Label(tooltip, bg="#333", fg="white", font=("Segoe UI", 9))
        t_label.pack(padx=6, pady=2)

        def show_tip(btn, text):
            t_label.config(text=text)
            tooltip.update_idletasks()
            x = btn.winfo_rootx() + btn.winfo_width() + 6
            y = btn.winfo_rooty()
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tip():
            tooltip.withdraw()

        app_buttons = {}

        # ---------- POSITION ----------
        def resize():
            root.update_idletasks()
            if ORIENTATION in ("right", "left"):
                w, h = ICON_SIZE + 20, frame.winfo_reqheight() + 20
                x = (root.winfo_screenwidth() - w - 10) if ORIENTATION == "right" else 10
                y = (root.winfo_screenheight() - h) // 2
            else:
                w, h = frame.winfo_reqwidth() + 20, ICON_SIZE + 20
                x = (root.winfo_screenwidth() - w) // 2
                y = root.winfo_screenheight() - h - 10
            root.geometry(f"{w}x{h}+{x}+{y}")

        # ---------- BUILD ----------
        def build():
            for b in list(app_buttons.values()):
                b.destroy()
            app_buttons.clear()
            frame._image_refs.clear()

            for folder in sorted(os.listdir(DOCKITEMS_DIR)):
                app_dir = os.path.join(DOCKITEMS_DIR, folder)
                if not os.path.isdir(app_dir):
                    continue

                launch_file = None
                icon_file = None

                for f in os.listdir(app_dir):
                    fpath = os.path.join(app_dir, f)
                    if f.lower().endswith((".lnk", ".exe", ".py", ".bat")):
                        launch_file = fpath
                    elif f.lower().endswith((".png", ".jpg", ".jpeg", ".ico")):
                        icon_file = fpath

                if not launch_file:
                    continue

                icon_img = safe_image(icon_file or DEFAULT_ICON_PATH, ICON_SIZE)
                icon_hover_img = safe_image(icon_file or DEFAULT_ICON_PATH, HOVER_SIZE)
                icon = make_photo(icon_img, root)
                icon_hover = make_photo(icon_hover_img, root)
                frame._image_refs += [icon, icon_hover]

                display_name = os.path.basename(app_dir)
                btn = tk.Label(frame, image=icon, bg=BG_COLOR, cursor="hand2")
                btn.pack(side="left" if ORIENTATION == "bottom" else "top",
                         pady=SPACING, padx=SPACING)
                btn.bind("<Enter>", lambda e, b=btn, h=icon_hover, n=display_name:
                         (b.config(image=h), show_tip(b, n)))
                btn.bind("<Leave>", lambda e, b=btn, n=icon:
                         (b.config(image=n), hide_tip()))
                btn.bind("<Button-1>", lambda e, p=launch_file: launch(p))
                app_buttons[display_name] = btn

            resize()

        # ---------- WATCH ----------
        def check_folder():
            nonlocal last_state
            current = set(os.listdir(DOCKITEMS_DIR))
            if current != last_state:
                last_state = current
                build()
            root.after(1500, check_folder)

        # ---------- INIT ----------
        build()
        check_folder()
        resize()
        try:
            root.mainloop()
        except tk.TclError:
            pass
        finally:
            globals()["dock_window"] = None

    # ---------------- START THREAD ----------------
    dock_thread = threading.Thread(target=run_dock, daemon=True)
    dock_thread.start()
    print("🚀 Dock launched (non-blocking). You can keep typing.")


@register_command("topbar")
def topbar_cmd(args):
    """
    Unified PyNix Top Bar (macOS-style)
    -----------------------------------
    - Shows open windows (click to focus)
    - Displays live time, date, and weather
    - Includes consistent, aligned system icons
    - Auto-hides after 10s of inactivity or when mouse leaves top area

    Usage:
        topbar        → launch top bar
        topbar kill   → close it
    """
    import tkinter as tk
    import threading, time, requests, os, subprocess
    import win32gui, win32con, win32api
    from PIL import Image, ImageTk

    global topbar_window, topbar_thread

    # --- Kill existing instance ---
    if args and args[0].lower() == "kill":
        if 'topbar_window' in globals() and topbar_window:
            try:
                topbar_window.after(0, topbar_window.destroy)
            except Exception:
                pass
            topbar_window = None
            print("🧹 Top bar closed.")
        else:
            print("⚠️ No top bar running.")
        return

    if 'topbar_window' in globals() and topbar_window:
        print("🔁 Top bar already running.")
        return

    # --- Config ---
    BG = "#1C1C1C"
    FG = "#ffffff"
    FONT = ("Segoe UI", 10, "bold")
    REFRESH_MS = 1000
    AUTOHIDE_DELAY = 3  # seconds
    DETECT_RADIUS = 5   # pixels from top of screen to show again
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    def run_topbar():
        global topbar_window
        root = tk.Tk()
        root.title("PyNix Top Bar")
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.95)
        root.configure(bg=BG)

        screen_w = root.winfo_screenwidth()
        bar_h = 32
        root.geometry(f"{screen_w}x{bar_h}+0+0")
        topbar_window = root

        # --- Layout frames ---
        left_frame = tk.Frame(root, bg=BG)
        center_frame = tk.Frame(root, bg=BG)
        right_frame = tk.Frame(root, bg=BG)
        left_frame.pack(side="left", fill="y", padx=10)
        center_frame.pack(side="left", expand=True, fill="both")
        right_frame.pack(side="right", fill="y", padx=6)

        # ============================================================== #
        #                     WINDOW LIST SECTION                        #
        # ============================================================== #
        window_buttons = {}

        def is_taskbar_window(hwnd):
            if not win32gui.IsWindowVisible(hwnd):
                return False
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return False
            IGNORE_TITLES = {
                "Program Manager", "Settings", "Back", "Find",
                "Windows Shell Experience Host", "Task Switching",
                "Default IME", "MSCTFIME UI"
            }
            if title.strip() in IGNORE_TITLES:
                return False
            if any(x in title for x in ["PyNix Top Bar", "PyNix Dock", "Nebula Desktop"]):
                return False
            if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
                return False
            return True

        def simplify_title(title):
            if not title:
                return title
            if "Notepad++" in title:
                return "Notepad++"
            if " - Google Chrome" in title:
                return "Google Chrome"
            if " - Microsoft Edge" in title:
                return "Microsoft Edge"
            if " - Brave" in title:
                return "Brave"
            if " - Visual Studio Code" in title:
                return "VS Code"
            return title.split(" - ")[0][:30]

        def get_open_windows():
            wins = []
            def enum(hwnd, _):
                if is_taskbar_window(hwnd):
                    wins.append((hwnd, win32gui.GetWindowText(hwnd)))
            win32gui.EnumWindows(enum, None)
            return wins

        def activate_window(hwnd):
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

        def update_windows():
            wins = get_open_windows()
            hwnds = {h for h, _ in wins}
            # Remove closed
            for h in list(window_buttons):
                if h not in hwnds:
                    window_buttons[h].destroy()
                    del window_buttons[h]
            # Add new
            for hwnd, raw_title in wins:
                title = simplify_title(raw_title)
                if hwnd in window_buttons:
                    continue
                btn = tk.Label(center_frame, text=f" {title} ", fg=FG, bg=BG, font=FONT, cursor="hand2")
                btn.pack(side="left", padx=4, pady=1)
                btn.bind("<Button-1>", lambda e, h=hwnd: activate_window(h))
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#333"))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG))
                window_buttons[hwnd] = btn
            root.after(REFRESH_MS, update_windows)

        # ============================================================== #
        #                     RIGHT SIDE (TIME + WEATHER)                #
        # ============================================================== #
        time_label = tk.Label(right_frame, text="", fg="white", bg=BG, font=("Segoe UI", 10, "bold"))
        time_label.pack(side="right", padx=10)

        weather_label = tk.Label(right_frame, text="", fg="#cccccc", bg=BG, font=("Segoe UI", 10, "bold"))
        weather_label.pack(side="right", padx=10)

        def update_time():
            time_label.config(text=time.strftime("%H:%M:%S  %d %b %Y"))
            root.after(1000, update_time)

        def update_weather():
            try:
                lat, lon = 43.4643, -80.5204
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                data = requests.get(url, timeout=5).json()
                if "current_weather" in data:
                    temp = data["current_weather"]["temperature"]
                    code = data["current_weather"]["weathercode"]
                    symbols = {
                        0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",
                        51:"🌦️",61:"🌧️",71:"🌨️",80:"🌦️",95:"⛈️"
                    }
                    icon = symbols.get(code, "🌡️")
                    weather_label.config(text=f"{icon} {temp}°C")
                else:
                    weather_label.config(text="🌥️ --°C")
            except Exception:
                weather_label.config(text="🌥️ --°C")
            root.after(600000, update_weather)

        # ============================================================== #
        #                   SYSTEM ICONS (RIGHT SIDE)                    #
        # ============================================================== #
        def make_icon(symbol, color, cmd):
            wrapper = tk.Frame(right_frame, bg=BG, width=38, height=38)
            wrapper.pack_propagate(False)
            wrapper.pack(side="right", padx=2)

            btn = tk.Label(wrapper, text=symbol, font=("Segoe UI Emoji", 14),
                           fg="white", bg=BG, cursor="hand2", anchor="center")
            btn.pack(expand=True, fill="both")
            btn.bind("<Button-1>", lambda e: cmd())
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=color))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="white"))

        def run_script(name):
            path = os.path.join(BASE_DIR, f"{name}.py")
            if os.path.exists(path):
                subprocess.Popen(["python", path], shell=True)

        make_icon("⏻", "#ff5555", lambda: handle_command("power"))
        make_icon("ᛒ", "#33aaff", lambda: run_script("bluetooth"))
        make_icon("🔊", "#00ff88", lambda: handle_command("volume"))
        make_icon("⚙️", "#ffaa00", lambda: subprocess.Popen(["start", "ms-settings:"], shell=True))
        make_icon("🖥️", "#55aaff", lambda: handle_command("desktop"))
        make_icon("🪟", "#66ccff", lambda: subprocess.Popen(["python", os.path.join(BASE_DIR, "winmgr.py")], shell=True))

        # ============================================================== #
        #                     AUTOHIDE LOGIC                              #
        # ============================================================== #
        last_activity = time.time()
        hidden = False
        start_y = 0
        hide_y = -bar_h

        def move_bar(target_y, steps=10):
            """Smooth slide animation."""
            current = int(root.winfo_y())
            delta = (target_y - current) // max(1, steps)
            for _ in range(steps):
                current += delta
                root.geometry(f"{screen_w}x{bar_h}+0+{current}")
                root.update_idletasks()
                time.sleep(0.01)
            root.geometry(f"{screen_w}x{bar_h}+0+{target_y}")

        def check_mouse():
            nonlocal last_activity, hidden
            x, y = win32api.GetCursorPos()
            if y < DETECT_RADIUS:
                last_activity = time.time()
                if hidden:
                    move_bar(start_y)
                    hidden = False
            elif time.time() - last_activity > AUTOHIDE_DELAY and not hidden:
                move_bar(hide_y)
                hidden = True
            root.after(500, check_mouse)

        # ============================================================== #
        #                        LOOP START                              #
        # ============================================================== #
        update_windows()
        update_time()
        update_weather()
        check_mouse()

        try:
            root.mainloop()
        except tk.TclError:
            pass
        finally:
            topbar_window = None

    # --- Launch thread ---
    topbar_thread = threading.Thread(target=run_topbar, daemon=True)
    topbar_thread.start()
    print("🚀 Top bar launched with auto-hide feature.")




@register_command("winmgr")
def winmgr_cmd(args):
    """
    PyNix Window Manager (Command-Line Edition)
    --------------------------------------------
    Manage Windows directly from the terminal.
    Commands:
        winmgr list                   → Lists all open windows
        winmgr tile                   → Tiles all visible windows (below top bar)
        winmgr center                 → Centers all windows
        winmgr close <title|hwnd>     → Closes a window by title or handle
    """
    import win32gui, win32con, win32api, win32process, psutil

    # --- Filter: Only user-facing, tileable windows ---
    def is_task_window(hwnd):
        if not win32gui.IsWindowVisible(hwnd):
            return False

        title = win32gui.GetWindowText(hwnd) or ""
        if not title.strip():
            return False

        # Get owning process name
        try:
            tid, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc_name = psutil.Process(pid).name().lower()
        except Exception:
            proc_name = ""

        # --- Block our own GUIs and Python shells ---
        if proc_name in ("python.exe", "pythonw.exe"):
            # All PyNix/desktop apps are python-based → ignore
            return False

        # --- Blacklist titles and partial keywords ---
        BLACKLIST = [
            "Program Manager", "Settings", "Back", "Default IME",
            "MSCTFIME UI", "NVIDIA GeForce Overlay", "Task Switching",
            "Nebula Desktop", "desktop.py", "Nebula Desktop — Tk",
            "PyNix Dock", "Dock", "AeroDock", "Launchpad", "PyNix Top Bar",
            "PyNix Window Manager"
        ]
        EXCLUDE_KEYWORDS = [
            "nebula desktop", "pynix", "dock", "launchpad", "aerodock",
            "desktop.py", "intnix", "nebulaos"
        ]

        for banned in BLACKLIST:
            if title.strip().lower() == banned.strip().lower():
                return False
        for kw in EXCLUDE_KEYWORDS:
            if kw in title.lower():
                return False

        # Skip tool windows or tiny popups
        if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
            return False

        try:
            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] < 100 or rect[3] - rect[1] < 50:
                return False
        except Exception:
            return False

        return True

    # --- Gather visible windows ---
    def get_windows():
        wins = []
        def enum(hwnd, _):
            if is_task_window(hwnd):
                wins.append((hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum, None)
        return wins

    # --- Helpers ---
    def close_window(hwnd):
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception:
            pass

    def center_window(hwnd):
        try:
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            sw, sh = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
            x = (sw - w) // 2
            y = (sh - h) // 2
            win32gui.MoveWindow(hwnd, x, y, w, h, True)
        except Exception:
            pass

    def tile_windows():
        wins = get_windows()
        if not wins:
            print("⚠️ No windows found.")
            return

        sw, sh = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
        cols = int(len(wins) ** 0.5) + 1
        rows = (len(wins) + cols - 1) // cols

        TOP_MARGIN = 40
        SIDE_MARGIN = 10
        BOTTOM_MARGIN = 10

        usable_width = sw - (2 * SIDE_MARGIN)
        usable_height = sh - TOP_MARGIN - BOTTOM_MARGIN
        w = usable_width // cols
        h = usable_height // rows

        i = 0
        for hwnd, title in wins:
            try:
                r, c = divmod(i, cols)
                x = SIDE_MARGIN + c * w
                y = TOP_MARGIN + r * h
                win32gui.MoveWindow(hwnd, x, y, w, h, True)
                i += 1
            except Exception:
                pass

        print(f"🧱 Tiled {i} windows into {rows}x{cols} grid (excluding desktop/dock).")

    # --- Command handling ---
    if not args:
        print("Usage: winmgr [list|tile|center|close <title|hwnd>]")
        return

    cmd = args[0].lower()
    wins = get_windows()

    if cmd == "list":
        print(f"🪟 Found {len(wins)} open windows:\n")
        for hwnd, title in wins:
            print(f"  {hwnd:<10} {title}")
        return

    elif cmd == "tile":
        tile_windows()
        return

    elif cmd == "center":
        for hwnd, title in wins:
            center_window(hwnd)
        print(f"🎯 Centered {len(wins)} windows.")
        return

    elif cmd == "close":
        if len(args) < 2:
            print("Usage: winmgr close <title or hwnd>")
            return

        target = " ".join(args[1:])
        for hwnd, title in wins:
            if target.lower() in title.lower() or target == str(hwnd):
                close_window(hwnd)
                print(f"❌ Closed window: {title} ({hwnd})")
                return
        print("⚠️ No matching window found.")
        return

    else:
        print("⚙️ Unknown command. Use: list | tile | center | close")


desktop_process = None


@register_command("power")
def power_cmd(args):
    """
    Power Menu (Windows)
    ---------------------
    Opens a floating translucent GUI with options:
    • Power Off

    • Restart
    • Sleep
    • Log Out
    • Cancel

    Usage:
        power        → open power menu
        power kill   → close if running
    """
    import tkinter as tk
    import subprocess, os, sys, platform, threading, psutil, signal, tempfile

    # --- Kill existing instance ---
    if args and args[0].lower() == "kill":
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                if proc.info['cmdline'] and "power_menu_temp.py" in " ".join(proc.info['cmdline']):
                    os.kill(proc.info['pid'], signal.SIGTERM)
                    print("🧹 Power menu closed.")
                    return
            except Exception:
                pass
        print("⚠️ No power menu running.")
        return

    # --- Only run on Windows ---
    if platform.system() != "Windows":
        print("⚠️ Power menu is Windows-only.")
        return

    # --- Create temporary file for GUI ---
    POWER_CODE = r'''
import tkinter as tk
import subprocess, os, sys, platform

BG_COLOR = "#1C1C1C"
HOVER_COLOR = "#333333"
TEXT_COLOR = "white"
FONT = ("Segoe UI", 12, "bold")
OPACITY = 0.95
WINDOW_SIZE = (300, 270)

def safe_run(cmd: str):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}", file=sys.stderr)

def power_off(): safe_run("shutdown /s /t 0")
def restart(): safe_run("shutdown /r /t 0")
def sleep(): safe_run("rundll32.exe powrprof.dll,SetSuspendState Sleep")
def log_off(): safe_run("shutdown /l")

def make_button(root, text, command):
    btn = tk.Label(root, text=text, bg=BG_COLOR, fg=TEXT_COLOR,
                   font=FONT, width=20, height=2, relief="flat")
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

    w, h = WINDOW_SIZE
    screen_w = root.winfo_screenwidth()
    x = screen_w - w - 75
    y = 100
    root.geometry(f"{w}x{h}+{x}+{y}")

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
'''

    tmp_path = os.path.join(tempfile.gettempdir(), "power_menu_temp.py")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(POWER_CODE)

    # --- Launch non-blocking process ---
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.Popen([sys.executable, tmp_path], creationflags=creationflags)
    print("⚡ Power menu launched (non-blocking). You can keep typing.")

@register_command("desktop")
def desktop_cmd(args):
    """
    Launch or kill the Nebula Desktop (runs desktop.py).
    - `desktop` → runs desktop.py as a separate process
    - `desktop kill` → closes the desktop window if open
    """
    import os, subprocess, signal, sys

    global desktop_process

    # --- Kill Command ---
    if args and args[0].lower() == "kill":
        if "desktop_process" in globals() and desktop_process:
            try:
                desktop_process.terminate()
                print("🧹 Desktop closed.")
            except Exception as e:
                print(f"⚠️ Failed to close desktop: {e}")
            desktop_process = None
        else:
            print("⚠️ No desktop currently running.")
        return

    # --- Prevent Multiple Instances ---
    if "desktop_process" in globals() and desktop_process:
        print("🔁 Desktop already running.")
        return

    # --- Locate desktop.py ---
    try:
        import __main__
        base_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    except Exception:
        base_dir = os.getcwd()

    desktop_path = os.path.join(base_dir, "desktop.py")

    if not os.path.exists(desktop_path):
        print(f"❌ Could not find {desktop_path}")
        return

    # --- Launch desktop.py as new process ---
    try:
        desktop_process = subprocess.Popen([sys.executable, desktop_path])
        print(f"🖥️ Nebula Desktop launched from {desktop_path}")
    except Exception as e:
        print(f"⚠️ Failed to launch desktop.py: {e}")

@register_command("taskbarb")
def taskbarb_cmd(args):
    """
    Launch or kill the Nebula Taskbar (runs taskbarb.py).
    - `taskbarb` → runs taskbarb.py as a separate process
    - `taskbarb kill` → terminates it
    """
    import os, subprocess, sys

    global taskbarb_process

    # --- Kill existing taskbar ---
    if args and args[0].lower() == "kill":
        if "taskbarb_process" in globals() and taskbarb_process:
            try:
                taskbarb_process.terminate()
                print("🧹 Taskbar closed.")
            except Exception as e:
                print(f"⚠️ Failed to close taskbar: {e}")
            taskbarb_process = None
        else:
            print("⚠️ No taskbar currently running.")
        return

    # --- Prevent multiple instances ---
    if "taskbarb_process" in globals() and taskbarb_process:
        print("🔁 Taskbar already running.")
        return

    # --- Find path to taskbarb.py ---
    try:
        import __main__
        base_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    except Exception:
        base_dir = os.getcwd()

    script_path = os.path.join(base_dir, "taskbarb.py")

    if not os.path.exists(script_path):
        print(f"❌ Could not find {script_path}")
        return

    # --- Launch script ---
    try:
        taskbarb_process = subprocess.Popen([sys.executable, script_path])
        print(f"🧭 Taskbar launched from {script_path}")
    except Exception as e:
        print(f"⚠️ Failed to launch taskbarb.py: {e}")
