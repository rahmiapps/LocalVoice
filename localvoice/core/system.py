from __future__ import annotations

import ctypes
import fnmatch
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import psutil
from PySide6.QtCore import QTimer
try:
    from pynput import keyboard
except ImportError:  # Wayland can run through wtype/ydotool without an X connection.
    keyboard = None  # type: ignore[assignment]

from .paths import CONFIG_DIR
from .window_activation import activate_windows_window


@dataclass(slots=True)
class ActiveWindowContext:
    process_name: str = ""
    native_id: str = ""
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None
    was_minimized: bool = False
    was_maximized: bool = False

    @property
    def center(self) -> tuple[int, int] | None:
        if None in {self.x, self.y, self.width, self.height}:
            return None
        return (int(self.x) + int(self.width) // 2, int(self.y) + int(self.height) // 2)


def active_window_context() -> ActiveWindowContext:
    system = platform.system()
    try:
        if system == "Windows":
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
            rect = RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return ActiveWindowContext(
                    psutil.Process(pid.value).name(), str(int(hwnd)),
                    int(rect.left), int(rect.top), max(0, int(rect.right - rect.left)), max(0, int(rect.bottom - rect.top)),
                    bool(user32.IsIconic(hwnd)), bool(user32.IsZoomed(hwnd)),
                )
            return ActiveWindowContext(
                psutil.Process(pid.value).name(), str(int(hwnd)),
                was_minimized=bool(user32.IsIconic(hwnd)),
                was_maximized=bool(user32.IsZoomed(hwnd)),
            )
        if system == "Linux" and shutil.which("xdotool") and not is_wayland():
            window_id = subprocess.check_output(
                ["xdotool", "getactivewindow"], text=True, timeout=2
            ).strip()
            pid_text = subprocess.check_output(
                ["xdotool", "getwindowpid", window_id], text=True, timeout=2
            ).strip()
            geometry_text = subprocess.check_output(
                ["xdotool", "getwindowgeometry", "--shell", window_id], text=True, timeout=2
            )
            values: dict[str, int] = {}
            for line in geometry_text.splitlines():
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key in {"X", "Y", "WIDTH", "HEIGHT"}:
                    values[key] = int(value)
            return ActiveWindowContext(
                psutil.Process(int(pid_text)).name(), window_id,
                values.get("X"), values.get("Y"), values.get("WIDTH"), values.get("HEIGHT"),
            )
    except (OSError, ValueError, subprocess.SubprocessError, psutil.Error):
        pass
    return ActiveWindowContext()


def active_application_name() -> str:
    return active_window_context().process_name


def application_matches(process_name: str, patterns: list[str]) -> bool:
    """Case-insensitive exact/glob matching for per-app profiles and zones."""
    name = process_name.strip().casefold()
    if not name:
        return False
    for raw in patterns:
        pattern = raw.strip().casefold()
        if pattern and fnmatch.fnmatchcase(name, pattern):
            return True
    return False


def restore_active_window(context: ActiveWindowContext | None) -> None:
    if context is None or not context.native_id:
        return
    try:
        if platform.system() == "Windows":
            hwnd = int(context.native_id)
            user32 = ctypes.windll.user32
            activate_windows_window(user32, hwnd)
        elif platform.system() == "Linux" and shutil.which("xdotool") and not is_wayland():
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", context.native_id],
                check=False,
                timeout=3,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except (OSError, ValueError, subprocess.SubprocessError):
        pass


def is_wayland() -> bool:
    return platform.system() == "Linux" and bool(os.environ.get("WAYLAND_DISPLAY"))


class TextInjector:
    MAX_OUTPUT_CHARACTERS = 2_000_000

    def __init__(
        self,
        set_clipboard: Callable[[str], None],
        clear_clipboard: Callable[[], None],
        get_clipboard: Callable[[], str] | None = None,
    ) -> None:
        self.set_clipboard = set_clipboard
        self.clear_clipboard = clear_clipboard
        self.get_clipboard = get_clipboard

    def output(
        self,
        text: str,
        mode: str,
        auto_enter: bool = False,
        clear_after: int = 0,
        context: ActiveWindowContext | None = None,
        restore_clipboard: bool = True,
    ) -> str:
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("There is no text to output.")
        if len(text) > self.MAX_OUTPUT_CHARACTERS:
            raise RuntimeError("The generated text is too large to insert safely.")
        previous = self.get_clipboard() if self.get_clipboard else ""
        self.set_clipboard(text)
        if mode == "insert":
            restore_active_window(context)
            inserted = self._paste(auto_enter)
            outcome = "inserted" if inserted else "copied"
            if inserted and restore_clipboard and self.get_clipboard is not None:
                self._schedule_clipboard_action(text, 1.0, lambda: self.set_clipboard(previous))
        else:
            outcome = "copied"
        if clear_after > 0 and not (mode == "insert" and restore_clipboard):
            self._schedule_clipboard_action(text, clear_after, self.clear_clipboard)
        return outcome

    def _schedule_clipboard_action(self, expected: str, delay: float, action: Callable[[], None]) -> None:
        def guarded() -> None:
            try:
                if self.get_clipboard is None or self.get_clipboard() == expected:
                    action()
            except Exception:
                return
        # Qt clipboard access must remain on the GUI thread. This method is
        # invoked from the controller's main-thread result slot.
        QTimer.singleShot(max(100, int(float(delay) * 1000)), guarded)

    @staticmethod
    def _paste(auto_enter: bool) -> bool:
        time.sleep(0.12)
        if is_wayland():
            if shutil.which("wtype"):
                try:
                    subprocess.run(
                        ["wtype", "-M", "ctrl", "v", "-m", "ctrl"],
                        check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    if auto_enter:
                        subprocess.run(
                            ["wtype", "-k", "Return"], check=True, timeout=3,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        )
                    return True
                except (OSError, subprocess.SubprocessError):
                    pass
            if shutil.which("ydotool"):
                try:
                    subprocess.run(
                        ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"],
                        check=True, timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    if auto_enter:
                        subprocess.run(
                            ["ydotool", "key", "28:1", "28:0"], check=True, timeout=3,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        )
                    return True
                except (OSError, subprocess.SubprocessError):
                    pass
            return False
        if keyboard is None:
            return False
        try:
            controller = keyboard.Controller()
            modifier = keyboard.Key.cmd if platform.system() == "Darwin" else keyboard.Key.ctrl
            with controller.pressed(modifier):
                controller.press("v")
                controller.release("v")
            if auto_enter:
                controller.press(keyboard.Key.enter)
                controller.release(keyboard.Key.enter)
            return True
        except Exception:
            return False


class AutostartManager:
    @staticmethod
    def set_enabled(enabled: bool) -> None:
        system = platform.system()
        if system == "Windows":
            AutostartManager._windows(enabled)
        elif system == "Linux":
            AutostartManager._linux(enabled)

    @staticmethod
    def _windows(enabled: bool) -> None:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        value_name = "LocalVoice"
        # Remove the legacy Startup-folder script from earlier versions.
        legacy = Path(os.environ.get("APPDATA", CONFIG_DIR)) / "Microsoft/Windows/Start Menu/Programs/Startup/LocalVoice.cmd"
        try:
            legacy.unlink(missing_ok=True)
        except OSError:
            pass
        access = winreg.KEY_SET_VALUE
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, access) as key:
            if enabled:
                executable = str(Path(sys.executable).resolve())
                if getattr(sys, "frozen", False):
                    arguments = [executable, "--minimized"]
                else:
                    launcher = str((Path(__file__).resolve().parents[2] / "run_localvoice.py").resolve())
                    arguments = [executable, launcher, "--minimized"]
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, subprocess.list2cmdline(arguments))
            else:
                try:
                    winreg.DeleteValue(key, value_name)
                except FileNotFoundError:
                    pass

    @staticmethod
    def _linux(enabled: bool) -> None:
        autostart_dir = Path.home() / ".config/autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / "localvoice.desktop"
        if enabled:
            if getattr(sys, "frozen", False):
                executable = str(Path(sys.executable).resolve()).replace('"', '\\"')
                command = f'"{executable}" --minimized'
            else:
                executable = str(Path(sys.executable).resolve()).replace('"', '\\"')
                launcher = str((Path(__file__).resolve().parents[2] / "run_localvoice.py").resolve()).replace('"', '\\"')
                command = f'"{executable}" "{launcher}" --minimized'
            desktop_file.write_text(
                "[Desktop Entry]\nType=Application\nName=LocalVoice\n"
                f"Exec={command}\nTerminal=false\nX-GNOME-Autostart-enabled=true\n",
                encoding="utf-8",
            )
            try:
                os.chmod(desktop_file, 0o600)
            except OSError:
                pass
        elif desktop_file.exists():
            desktop_file.unlink()


def open_path(path: Path) -> None:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    system = platform.system()
    if system == "Windows":
        os.startfile(resolved)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", str(resolved)])
    else:
        subprocess.Popen(["xdg-open", str(resolved)])
