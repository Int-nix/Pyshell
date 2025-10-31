# mirror_window.py
# A 100% custom GUI window that mirrors console output
# Uses only built-in ctypes – NO tkinter, NO imports beyond stdlib

import ctypes
from ctypes import wintypes
import time

# ---------- WinAPI Constants ----------
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

WM_PAINT = 0x000F
WM_DESTROY = 0x0002
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_CLOSE = 0x0010
WM_GETMINMAXINFO = 0x0024

CW_USEDEFAULT = -1
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WS_HSCROLL = 0x00100000
WS_VSCROLL = 0x00200000
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
COLOR_WINDOW = 5
WM_SETFONT = 0x0030
IDC_ARROW = 32512

# ---------- Structs ----------
class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", POINT),
        ("ptMaxSize", POINT),
        ("ptMaxPosition", POINT),
        ("ptMinTrackSize", POINT),
        ("ptMaxTrackSize", POINT),
    ]

# ---------- Global State ----------
buffer = []
max_lines = 1000
font_handle = None
hwnd = None
hdc = None
scroll_pos = 0

# ---------- Custom Print (mirrors to window) ----------
def print_mirror(*args, sep=" ", end="\n"):
    line = sep.join(map(str, args)) + end
    buffer.append(line)
    if len(buffer) > max_lines:
        buffer.pop(0)
    if hwnd:
        user32.InvalidateRect(hwnd, None, True)

# Override built-in print
import builtins
builtins.print = print_mirror

# ---------- Window Procedure ----------
def WndProc(hwnd, msg, wParam, lParam):
    global scroll_pos, hdc

    if msg == WM_PAINT:
        ps = ctypes.create_string_buffer(ctypes.sizeof(ctypes.c_int) * 16)
        hdc = user32.BeginPaint(hwnd, ps)
        DrawText()
        user32.EndPaint(hwnd, ps)
        return 0

    elif msg == WM_GETMINMAXINFO:
        info = ctypes.cast(lParam, ctypes.POINTER(MINMAXINFO)).contents
        info.ptMinTrackSize.x = 600
        info.ptMinTrackSize.y = 400
        return 0

    elif msg == WM_KEYDOWN:
        if wParam == 0x26:  # Up arrow
            scroll_pos = max(0, scroll_pos - 1)
            user32.InvalidateRect(hwnd, None, True)
        elif wParam == 0x28:  # Down arrow
            scroll_pos = min(len(buffer) - 20, scroll_pos + 1)
            user32.InvalidateRect(hwnd, None, True)
        return 0

    elif msg == WM_CLOSE:
        user32.DestroyWindow(hwnd)
        return 0

    elif msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0

    return user32.DefWindowProcW(hwnd, msg, wParam, lParam)

WndProc = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)(WndProc)

# ---------- Draw Text ----------
def DrawText():
    global hdc, font_handle, scroll_pos
    if not hdc or not font_handle:
        return

    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    gdi32.SelectObject(hdc, font_handle)
    gdi32.SetBkColor(hdc, 0x1e1e1e)
    gdi32.SetTextColor(hdc, 0xd4d4d4)

    line_height = 18
    start_y = rect.bottom - line_height * 20
    visible_lines = buffer[-20 + scroll_pos:len(buffer) + scroll_pos] if len(buffer) > 20 else buffer

    y = start_y
    for line in visible_lines:
        if y < 0:
            break
        text = line.rstrip()[:200]
        gdi32.TextOutW(hdc, 10, y, text, len(text))
        y -= line_height

# ---------- Create Window ----------
def create_window():
    global hwnd, font_handle

    hInstance = kernel32.GetModuleHandleW(None)
    class_name = "PyNixMirrorWindow"

    wc = WNDCLASSEX()
    wc.cbSize = ctypes.sizeof(WNDCLASSEX)
    wc.style = CS_HREDRAW | CS_VREDRAW
    wc.lpfnWndProc = WndProc
    wc.hInstance = hInstance
    wc.hbrBackground = COLOR_WINDOW + 1
    wc.lpszClassName = class_name
    wc.hCursor = user32.LoadCursorW(None, IDC_ARROW)

    user32.RegisterClassExW(ctypes.byref(wc))

    hwnd = user32.CreateWindowExW(
        0, class_name, "PyNixShell Mirror",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE | WS_HSCROLL | WS_VSCROLL,
        CW_USEDEFAULT, CW_USEDEFAULT, 900, 600,
        None, None, hInstance, None
    )

    # Create font
    font_handle = gdi32.CreateFontW(
        16, 0, 0, 0, 400, False, False, False,
        1, 0, 0, 0, 0, "Consolas"
    )
    user32.SendMessageW(hwnd, WM_SETFONT, font_handle, True)

    user32.ShowWindow(hwnd, 1)
    user32.UpdateWindow(hwnd)

# ---------- Message Loop ----------
def message_loop():
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

# ---------- Start Mirror ----------
def start_mirror():
    create_window()
    print("Mirror window opened. Close it to stop.")
    message_loop()

# ---------- Launch ----------
if __name__ == "__main__":
    import os
    import subprocess

    # Start your shell in background
    proc = subprocess.Popen(
        ["python", "pynixshell.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Forward output to mirror
    for line in proc.stdout:
        print_mirror(line.rstrip())

    proc.wait()