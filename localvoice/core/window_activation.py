from __future__ import annotations


def activate_windows_window(user32: object, hwnd: int) -> bool:
    """Activate a Windows window without changing its maximized state.

    SW_RESTORE is correct only for a minimized window. Applying it to a
    maximized target changes the user's window to its normal size.
    """
    try:
        is_iconic = bool(user32.IsIconic(hwnd))
        if is_iconic:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE only for minimized targets.
        try:
            user32.BringWindowToTop(hwnd)
        except Exception:
            pass
        return bool(user32.SetForegroundWindow(hwnd))
    except Exception:
        return False
