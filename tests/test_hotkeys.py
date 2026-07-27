from __future__ import annotations

import os

from localvoice.core.hotkeys import GlobalHotkeyService, _WaylandPortalHotkeyBackend


def test_wayland_trigger_conversion_is_keyboard_only() -> None:
    assert _WaylandPortalHotkeyBackend.preferred_trigger("ctrl+alt+f8") == "CTRL+ALT+F8"
    assert _WaylandPortalHotkeyBackend.preferred_trigger("shift+num5") == "SHIFT+KP_5"
    assert _WaylandPortalHotkeyBackend.preferred_trigger("ctrl+enter") == "CTRL+Return"
    assert _WaylandPortalHotkeyBackend.preferred_trigger("mouse4") == ""


def test_wayland_callbacks_preserve_hold_and_toggle_semantics() -> None:
    events: list[tuple[str, str]] = []
    backend = _WaylandPortalHotkeyBackend(
        [],
        lambda identity: events.append(("start", identity)),
        lambda identity: events.append(("stop", identity)),
        lambda identity: events.append(("toggle", identity)),
    )
    backend._shortcut_map = {
        "hold": ("hold", "f8"),
        "toggle": ("toggle", "ctrl+space"),
    }
    backend._activated("/session", "hold", 0, {})
    backend._deactivated("/session", "hold", 0, {})
    backend._activated("/session", "toggle", 0, {})
    backend._deactivated("/session", "toggle", 0, {})
    assert events == [("start", "f8"), ("stop", "f8"), ("toggle", "ctrl+space")]


def test_disabled_hotkey_service_starts_no_native_backend(monkeypatch) -> None:
    service = GlobalHotkeyService()
    service.configure("f8", "hold", enabled=False)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    service.start()
    assert service.backend_name == "disabled"
    assert service._portal_backend is None
    assert service._listener is None


def test_plain_function_key_uses_reliable_windows_listener_path() -> None:
    service = GlobalHotkeyService()
    service.configure("f8", "toggle", suppress_keystroke=True)
    assert not service._requires_windows_suppression()
    events: list[tuple[str, str]] = []
    service.on_toggle = lambda identity: events.append(("toggle", identity))
    service._on_press_name("f8")
    service._on_release_name("f8")
    service._on_press_name("f8")
    service._on_release_name("f8")
    assert events == [("toggle", "f8"), ("toggle", "f8")]
