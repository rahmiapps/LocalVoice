from __future__ import annotations

import os
import platform
import threading
import time
from typing import Callable

try:
    from pynput import keyboard, mouse
except ImportError:  # Static/source validation can run without native input hooks.
    keyboard = None  # type: ignore[assignment]
    mouse = None  # type: ignore[assignment]

from .validation import normalize_hotkey as validate_hotkey


ALIASES = {
    "control": "ctrl", "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt",
    "shift_l": "shift", "shift_r": "shift",
    "cmd": "meta", "cmd_l": "meta", "cmd_r": "meta",
    "return": "enter", "space": "space", "esc": "escape",
    "decimal": "num_decimal", "insert": "insert", "delete": "delete",
    "numpad0": "num0", "numpad1": "num1", "numpad2": "num2", "numpad3": "num3",
    "numpad4": "num4", "numpad5": "num5", "numpad6": "num6", "numpad7": "num7",
    "numpad8": "num8", "numpad9": "num9",
}


class GlobalHotkeyService:
    def __init__(self) -> None:
        self.enabled = True
        self.bindings: list[tuple[frozenset[str], str, str]] = [(frozenset({"f8"}), "hold", "f8")]
        self.on_start: Callable[[str], None] | None = None
        self.on_stop: Callable[[str], None] | None = None
        self.on_toggle: Callable[[str], None] | None = None
        self.on_backend_error: Callable[[str], None] | None = None
        self.on_backend_ready: Callable[[str], None] | None = None
        self._listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._pressed: set[str] = set()
        self._triggered_target: frozenset[str] | None = None
        self._triggered_mode = "hold"
        self.suppress_keystroke = True
        self._win_pressed_vks: set[int] = set()
        self._win_suppressed_vks: set[int] = set()
        self._win_suppressed_mouse: set[str] = set()
        self._lock = threading.RLock()
        self._portal_backend: _WaylandPortalHotkeyBackend | None = None
        self.backend_name = "pynput"

    @property
    def is_running(self) -> bool:
        if not self.enabled:
            return False
        if self._portal_backend is not None:
            return self.backend_name in {"xdg-portal", "xdg-portal-pending"}
        keyboard_alive = bool(self._listener is not None and self._listener.is_alive())
        mouse_alive = bool(self._mouse_listener is not None and self._mouse_listener.is_alive())
        return keyboard_alive and mouse_alive

    def _dispatch(self, callback_name: str, identity: str) -> None:
        callback = getattr(self, callback_name, None)
        if callback is None:
            return
        try:
            callback(identity)
        except (RuntimeError, ReferenceError):
            # The Qt receiver may have been destroyed while a native listener was
            # stopping. Never terminate the input-hook thread for that race.
            setattr(self, callback_name, None)
        except Exception as exc:
            if self.on_backend_error:
                try:
                    self.on_backend_error(str(exc)[:700])
                except Exception:
                    pass

    def _requires_windows_suppression(self) -> bool:
        """Suppress only shortcuts that could type into the target application.

        Function keys such as F8 do not insert text, and running them through the
        low-level suppression filter has caused missed callbacks on some Windows
        systems. They are therefore captured through the simpler reliable path.
        """
        typing_keys = {"space", "enter", "tab", "backspace", "delete", "insert"}
        for target, _mode, _identity in self.bindings:
            for name in target:
                if len(name) == 1 or name in typing_keys:
                    return True
        return False

    def configure(
        self,
        hotkey: str,
        mode: str,
        enabled: bool = True,
        secondary_hotkey: str = "",
        additional: list[tuple[str, str]] | None = None,
        suppress_keystroke: bool = True,
    ) -> None:
        values = [(hotkey, mode)]
        if secondary_hotkey.strip():
            values.append((secondary_hotkey, mode))
        values.extend(additional or [])
        bindings: list[tuple[frozenset[str], str, str]] = []
        seen: set[frozenset[str]] = set()
        for value, binding_mode in values:
            normalized = self.normalize_hotkey(value)
            if not normalized:
                continue
            target = frozenset(normalized.split("+"))
            if target and target not in seen:
                seen.add(target)
                bindings.append((target, binding_mode, normalized))
        with self._lock:
            self.bindings = sorted(bindings, key=lambda item: len(item[0]), reverse=True)
            self.enabled = enabled
            self.suppress_keystroke = suppress_keystroke
            self._pressed.clear()
            self._win_pressed_vks.clear()
            self._win_suppressed_vks.clear()
            self._win_suppressed_mouse.clear()
            self._triggered_target = None

    def start(self) -> None:
        if self._listener is not None or self._portal_backend is not None:
            return
        if not self.enabled:
            self.backend_name = "disabled"
            return
        if platform.system() == "Linux" and bool(os.environ.get("WAYLAND_DISPLAY")):
            portal = _WaylandPortalHotkeyBackend(
                list(self.bindings), self.on_start, self.on_stop, self.on_toggle,
                on_ready=self._portal_ready, on_error=self._portal_error,
            )
            self._portal_backend = portal
            self.backend_name = "xdg-portal-pending"
            try:
                portal.start()
            except Exception:
                self._portal_backend = None
                self.backend_name = "unavailable"
                raise
            return
        self.backend_name = "pynput"
        if keyboard is None or mouse is None:
            raise RuntimeError("The pynput global-hotkey component is not installed.")
        keyboard_options = {}
        mouse_options = {}
        if platform.system() == "Windows" and self.suppress_keystroke and self._requires_windows_suppression():
            keyboard_options["win32_event_filter"] = self._win32_keyboard_filter
            mouse_options["win32_event_filter"] = self._win32_mouse_filter
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release, **keyboard_options)
        self._listener.daemon = True
        self._listener.start()
        self._mouse_listener = mouse.Listener(on_click=self._on_click, **mouse_options)
        self._mouse_listener.daemon = True
        self._mouse_listener.start()
        time.sleep(0.05)
        if not self.is_running:
            self.stop()
            raise RuntimeError("The global-hotkey listener could not be started.")
        if self.on_backend_ready:
            self.on_backend_ready(self.backend_name)

    def _portal_ready(self) -> None:
        self.backend_name = "xdg-portal"
        if self.on_backend_ready:
            self.on_backend_ready(self.backend_name)

    def _portal_error(self, message: str) -> None:
        self.backend_name = "unavailable"
        if self.on_backend_error:
            self.on_backend_error(message)

    def stop(self) -> None:
        if self._portal_backend is not None:
            self._portal_backend.stop()
            self._portal_backend = None
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    @staticmethod
    def normalize_hotkey(value: str) -> str:
        return validate_hotkey(value, default="")

    @staticmethod
    def conflicts(values: list[str]) -> list[str]:
        seen: set[frozenset[str]] = set()
        conflicts: list[str] = []
        for value in values:
            normalized = validate_hotkey(value, default="")
            if not normalized:
                continue
            target = frozenset(normalized.split("+"))
            if target in seen and normalized not in conflicts:
                conflicts.append(normalized)
            seen.add(target)
        return conflicts

    @staticmethod
    def _key_name(key: keyboard.Key | keyboard.KeyCode) -> str:
        if isinstance(key, keyboard.KeyCode):
            if key.vk is not None and 96 <= key.vk <= 105:
                return f"num{key.vk - 96}"
            if key.char:
                return key.char.lower()
            if key.vk is not None:
                return f"vk{key.vk}"
            return "unknown"
        name = getattr(key, "name", str(key).replace("Key.", ""))
        return ALIASES.get(name, name)

    @staticmethod
    def _normalise_windows_vk(vk: int) -> int:
        return {0xA0:0x10,0xA1:0x10,0xA2:0x11,0xA3:0x11,0xA4:0x12,0xA5:0x12,0x5C:0x5B}.get(vk,vk)

    @staticmethod
    def _name_to_windows_vk(name: str) -> int | None:
        fixed={"ctrl":0x11,"shift":0x10,"alt":0x12,"meta":0x5B,"space":0x20,"enter":0x0D,"tab":0x09,"esc":0x1B,"escape":0x1B,"backspace":0x08,"delete":0x2E}
        if name in fixed:return fixed[name]
        if name.startswith("f") and name[1:].isdigit():
            number=int(name[1:]); return 0x6F+number if 1 <= number <= 24 else None
        if name.startswith("num") and name[3:].isdigit():
            number=int(name[3:]); return 0x60+number if 0 <= number <= 9 else None
        if len(name)==1 and name.isalpha():return ord(name.upper())
        if len(name)==1 and name.isdigit():return ord(name)
        return None

    def _windows_vk_targets(self) -> list[frozenset[int]]:
        targets=[]
        for names, _mode, _identity in self.bindings:
            values={self._name_to_windows_vk(name) for name in names if not name.startswith("mouse")}
            values.discard(None)
            if values:targets.append(frozenset(int(value) for value in values))
        return targets

    def _win32_keyboard_filter(self, msg, data):
        if not self.enabled or not self.suppress_keystroke:return True
        vk=self._normalise_windows_vk(int(data.vkCode))
        is_down=int(msg) in {0x0100,0x0104}
        is_up=int(msg) in {0x0101,0x0105}
        modifiers={0x10,0x11,0x12,0x5B}
        suppress=False
        with self._lock:
            if is_down:
                self._win_pressed_vks.add(vk)
                if vk not in modifiers and any(target.issubset(self._win_pressed_vks) for target in self._windows_vk_targets()):
                    self._win_suppressed_vks.add(vk); suppress=True
            elif is_up:
                suppress=vk in self._win_suppressed_vks
                self._win_suppressed_vks.discard(vk); self._win_pressed_vks.discard(vk)
        if suppress and self._listener is not None:self._listener.suppress_event()
        return True

    def _win32_mouse_filter(self, msg, data):
        if not self.enabled or not self.suppress_keystroke:return True
        message=int(msg); name=None; pressed=False
        if message in {0x0207,0x0208}:name="mousemiddle";pressed=message==0x0207
        elif message in {0x020B,0x020C}:
            button=(int(data.mouseData)>>16)&0xFFFF; name="mouse4" if button==1 else "mouse5" if button==2 else None; pressed=message==0x020B
        if name is None:return True
        suppress=False
        with self._lock:
            if pressed:
                candidate=set(self._pressed); candidate.add(name)
                if any(target.issubset(candidate) for target, _mode, _identity in self.bindings):self._win_suppressed_mouse.add(name);suppress=True
            else:
                suppress=name in self._win_suppressed_mouse; self._win_suppressed_mouse.discard(name)
        if suppress and self._mouse_listener is not None:self._mouse_listener.suppress_event()
        return True

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._on_press_name(self._key_name(key))

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._on_release_name(self._key_name(key))

    @staticmethod
    def _mouse_name(button: mouse.Button) -> str:
        name = getattr(button, "name", str(button).replace("Button.", ""))
        return {"x1": "mouse4", "x2": "mouse5", "middle": "mousemiddle"}.get(name, f"mouse_{name}")

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        name = self._mouse_name(button)
        if pressed:
            self._on_press_name(name)
        else:
            self._on_release_name(name)

    def _on_press_name(self, name: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._pressed.add(name)
            if self._triggered_target is not None:
                return
            match = next(((target, mode, identity) for target, mode, identity in self.bindings if target.issubset(self._pressed)), None)
            if match is None:
                return
            self._triggered_target, self._triggered_mode, identity = match
        if self._triggered_mode == "toggle":
            self._dispatch("on_toggle", identity)
        else:
            self._dispatch("on_start", identity)

    def _on_release_name(self, name: str) -> None:
        should_stop = False
        with self._lock:
            target = self._triggered_target
            mode = self._triggered_mode
            if target is not None and mode == "hold" and name in target:
                should_stop = True
            self._pressed.discard(name)
            if target is not None and not target.issubset(self._pressed):
                self._triggered_target = None
        if should_stop:
            identity = "+".join(sorted(target)) if target else ""
            for binding_target, _binding_mode, binding_identity in self.bindings:
                if binding_target == target:
                    identity = binding_identity
                    break
            self._dispatch("on_stop", identity)
class _WaylandPortalHotkeyBackend:
    """XDG GlobalShortcuts portal backend for Wayland desktops.

    Portal calls run in a private asyncio thread.  The callbacks are Qt signals
    in production, which Qt safely queues back to the GUI thread.
    """

    PORTAL_NAME = "org.freedesktop.portal.Desktop"
    PORTAL_PATH = "/org/freedesktop/portal/desktop"
    PORTAL_INTERFACE = "org.freedesktop.portal.GlobalShortcuts"
    REQUEST_INTERFACE = "org.freedesktop.portal.Request"
    SESSION_INTERFACE = "org.freedesktop.portal.Session"

    def __init__(
        self,
        bindings: list[tuple[frozenset[str], str, str]],
        on_start: Callable[[str], None] | None,
        on_stop: Callable[[str], None] | None,
        on_toggle: Callable[[str], None] | None,
        on_ready: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self.bindings = bindings
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_toggle = on_toggle
        self.on_ready = on_ready
        self.on_error = on_error
        self._shortcut_map: dict[str, tuple[str, str]] = {}
        self._thread: threading.Thread | None = None
        self._loop = None
        self._stop_event = None
        self._ready = threading.Event()
        self._error = ""
        self._session_handle = ""
        self._bus = None
        self._stop_requested = threading.Event()

    @staticmethod
    def preferred_trigger(identity: str) -> str:
        """Convert LocalVoice's normalized syntax to the XDG shortcut syntax."""
        normalized = validate_hotkey(identity, default="")
        if not normalized:
            return ""
        modifier_names = {"ctrl": "CTRL", "alt": "ALT", "shift": "SHIFT", "meta": "LOGO"}
        key_names = {
            "space": "space", "enter": "Return", "tab": "Tab", "escape": "Escape",
            "backspace": "BackSpace", "delete": "Delete", "insert": "Insert",
            "num_decimal": "KP_Decimal",
        }
        modifiers: list[str] = []
        key = ""
        for token in normalized.split("+"):
            if token in modifier_names:
                modifiers.append(modifier_names[token])
            elif token.startswith("mouse"):
                # The current XDG shortcut specification is keyboard-only.
                return ""
            elif token.startswith("num") and token[3:].isdigit():
                key = f"KP_{token[3:]}"
            elif token.startswith("f") and token[1:].isdigit():
                key = token.upper()
            else:
                key = key_names.get(token, token)
        return "+".join([*modifiers, key]) if key else ""

    def start(self) -> None:
        supported = [binding for binding in self.bindings if self.preferred_trigger(binding[2])]
        if not supported:
            raise RuntimeError("No keyboard shortcut can be registered through the Wayland portal.")
        self.bindings = supported
        self._stop_requested.clear()
        self._thread = threading.Thread(target=self._thread_main, daemon=True, name="LocalVoiceWaylandPortal")
        self._thread.start()

    def stop(self) -> None:
        self._stop_requested.set()
        loop = self._loop
        event = self._stop_event
        if loop is not None and event is not None:
            try:
                loop.call_soon_threadsafe(event.set)
            except RuntimeError:
                pass
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=5)
        self._thread = None
        self._loop = None
        self._stop_event = None

    def _thread_main(self) -> None:
        import asyncio

        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        except Exception as exc:
            self._error = f"Wayland global-shortcuts portal unavailable: {str(exc)[:700]}"
            self._ready.set()
            if self.on_error:
                self.on_error(self._error)
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    async def _portal_request(self, bus, call, timeout: float = 60.0):
        """Execute a portal request without missing an immediate Response signal.

        XDG recommends subscribing before the method call.  A low-level message
        handler is used here because the Request object may not exist until after
        the method returns.  Response signals are unicast to this D-Bus client, and
        requests in this backend are strictly sequential.
        """
        import asyncio
        from dbus_next.constants import MessageType

        future = asyncio.get_running_loop().create_future()

        def message_received(message) -> bool:
            if (
                message.message_type == MessageType.SIGNAL
                and message.interface == self.REQUEST_INTERFACE
                and message.member == "Response"
                and len(message.body or []) == 2
                and not future.done()
            ):
                future.set_result((int(message.body[0]), message.body[1]))
            return False

        bus.add_message_handler(message_received)
        try:
            request_handle = str(await call())
            if not request_handle.startswith("/org/freedesktop/portal/desktop/request/"):
                raise RuntimeError("The desktop portal returned an invalid request handle.")
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            try:
                bus.remove_message_handler(message_received)
            except Exception:
                pass

    async def _run(self) -> None:
        import asyncio
        import hashlib
        import uuid
        from dbus_next import BusType, Variant
        from dbus_next.aio import MessageBus

        self._stop_event = asyncio.Event()
        if self._stop_requested.is_set():
            self._stop_event.set()
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        self._bus = bus
        try:
            introspection = await bus.introspect(self.PORTAL_NAME, self.PORTAL_PATH)
            portal_object = bus.get_proxy_object(self.PORTAL_NAME, self.PORTAL_PATH, introspection)
            portal = portal_object.get_interface(self.PORTAL_INTERFACE)

            portal.on_activated(self._activated)
            portal.on_deactivated(self._deactivated)

            token = "lv" + uuid.uuid4().hex
            response, results = await self._portal_request(
                bus,
                lambda: portal.call_create_session({
                    "handle_token": Variant("s", token),
                    "session_handle_token": Variant("s", "session" + uuid.uuid4().hex),
                }),
            )
            if response != 0:
                raise RuntimeError(f"Global-shortcuts session was rejected (portal response {response}).")
            raw_session = results.get("session_handle")
            self._session_handle = str(getattr(raw_session, "value", raw_session) or "")
            if not self._session_handle.startswith("/"):
                raise RuntimeError("The global-shortcuts portal returned an invalid session handle.")

            shortcuts = []
            for _target, mode, identity in self.bindings:
                shortcut_id = "lv_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
                self._shortcut_map[shortcut_id] = (mode, identity)
                shortcuts.append((shortcut_id, {
                    "description": Variant("s", f"LocalVoice – {identity.upper()}"),
                    "preferred_trigger": Variant("s", self.preferred_trigger(identity)),
                }))
            bind_response, bind_results = await self._portal_request(
                bus,
                lambda: portal.call_bind_shortcuts(
                    self._session_handle,
                    shortcuts,
                    "",
                    {"handle_token": Variant("s", "bind" + uuid.uuid4().hex)},
                ),
            )
            if bind_response != 0:
                raise RuntimeError(f"Global shortcuts were not approved (portal response {bind_response}).")
            raw_bound = bind_results.get("shortcuts", []) if isinstance(bind_results, dict) else []
            raw_bound = getattr(raw_bound, "value", raw_bound)
            bound_ids = {str(item[0]) for item in raw_bound if isinstance(item, (list, tuple)) and item}
            self._shortcut_map = {key: value for key, value in self._shortcut_map.items() if key in bound_ids}
            if not self._shortcut_map:
                raise RuntimeError("The Wayland desktop did not approve any LocalVoice shortcut.")
            self._ready.set()
            if self.on_ready:
                self.on_ready()
            await self._stop_event.wait()

            try:
                session_intro = await bus.introspect(self.PORTAL_NAME, self._session_handle)
                session_object = bus.get_proxy_object(self.PORTAL_NAME, self._session_handle, session_intro)
                await session_object.get_interface(self.SESSION_INTERFACE).call_close()
            except Exception:
                pass
        finally:
            self._ready.set()
            try:
                bus.disconnect()
            except Exception:
                pass

    def _activated(self, session_handle: str, shortcut_id: str, timestamp: int, options: dict) -> None:
        del session_handle, timestamp, options
        binding = self._shortcut_map.get(str(shortcut_id))
        if binding is None:
            return
        mode, identity = binding
        if mode == "toggle":
            if self.on_toggle:
                self.on_toggle(identity)
        elif self.on_start:
            self.on_start(identity)

    def _deactivated(self, session_handle: str, shortcut_id: str, timestamp: int, options: dict) -> None:
        del session_handle, timestamp, options
        binding = self._shortcut_map.get(str(shortcut_id))
        if binding is None:
            return
        mode, identity = binding
        if mode == "hold" and self.on_stop:
            self.on_stop(identity)

