import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

windows = []
def enum_proc(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            if title:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                is_min = bool(user32.IsIconic(hwnd))
                windows.append((hwnd, is_min, (rect.left, rect.top, rect.right, rect.bottom), title))
    return True

user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
for w in windows:
    print(f"HWND {w[0]} | Min={w[1]} | Rect={w[2]} | Title: {w[3]}")
