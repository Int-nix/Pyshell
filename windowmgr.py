import win32gui
import win32con
import win32api
import win32process
import os
import math

def get_open_windows():
    """Return a list of hwnds for all visible, normal app windows except this script."""
    windows = []
    current_pid = os.getpid() 

    def enum_window_callback(hwnd, extra):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return True
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        if width < 100 or height < 100:
            return True
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid == current_pid:
            return True
        windows.append(hwnd)
        return True

    win32gui.EnumWindows(enum_window_callback, None)
    return windows

def tile_windows(hwnds):
    """Tile windows once in a grid."""
    if len(hwnds) <= 1:
        return

    work_area = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))['Work']
    screen_x, screen_y, screen_right, screen_bottom = work_area
    screen_width = screen_right - screen_x
    screen_height = screen_bottom - screen_y

    n = len(hwnds)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    cell_width = screen_width // cols
    cell_height = screen_height // rows

    for i, hwnd in enumerate(hwnds):
        col = i % cols
        row = i // cols
        x = screen_x + col * cell_width
        y = screen_y + row * cell_height
        w = cell_width if col != cols - 1 else screen_width - col * cell_width
        h = cell_height if row != rows - 1 else screen_height - row * cell_height
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.MoveWindow(hwnd, x, y, w, h, True)
        except:
            pass

if __name__ == "__main__":
    windows = get_open_windows()
    tile_windows(windows)
    # Exit immediately after tiling
