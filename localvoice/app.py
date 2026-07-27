from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QLocale, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from localvoice import APP_NAME
from localvoice.core.audio import cleanup_stale_recordings
from localvoice.core.controller import AppController
from localvoice.core.database import LocalDatabase
from localvoice.core.hotkeys import GlobalHotkeyService
from localvoice.core.i18n import tr
from localvoice.core.paths import LOG_DIR, ensure_directories
from localvoice.core.security import SecureStore, SecurityError
from localvoice.core.settings import SettingsStore
from localvoice.core.single_instance import InstanceCommandServer, SingleInstanceGuard
from localvoice.core.transcription import WhisperEngine
from localvoice.core.translation import LocalTranslator
from localvoice.core.system import TextInjector
from localvoice.ui.dialogs import ModelManagerDialog, OnboardingDialog, PinDialog
from localvoice.ui.main_window import MainWindow
from localvoice.ui.theme import stylesheet


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    candidates = [
        base / relative,
        base / "resources" / Path(relative).name,
        Path(__file__).resolve().parents[1] / relative,
    ]
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def setup_logging() -> None:
    ensure_directories()
    handler = RotatingFileHandler(
        LOG_DIR / "localvoice.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[handler],
    )


def _show_security_error(language: str, detail: str) -> None:
    QMessageBox.critical(
        None,
        "LocalVoice",
        tr(language, "security_file_error") + "\n\n" + detail[:1000],
    )


def _unlock_store(secure_store: SecureStore, language: str) -> bool:
    if not secure_store.has_pin or not secure_store.is_locked:
        return True
    while secure_store.is_locked:
        remaining = secure_store.lockout_seconds_remaining
        if remaining > 0:
            QMessageBox.warning(
                None,
                "LocalVoice",
                tr(language, "pin_locked").format(seconds=remaining),
            )
            return False
        pin_dialog = PinDialog(language, "unlock")
        if pin_dialog.exec() != PinDialog.Accepted:
            return False
        try:
            if secure_store.unlock(pin_dialog.pin.text()):
                return True
        except SecurityError as exc:
            _show_security_error(language, str(exc))
            return False
        remaining = secure_store.lockout_seconds_remaining
        message = (
            tr(language, "pin_locked").format(seconds=remaining)
            if remaining > 0
            else tr(language, "wrong_pin")
        )
        QMessageBox.warning(pin_dialog, "LocalVoice", message)
    return True



def _package_smoke_test() -> int:
    """Verify that the frozen package can load its native runtime components."""
    try:
        import argostranslate  # noqa: F401
        import cryptography  # noqa: F401
        import dbus_next  # noqa: F401
        import faster_whisper  # noqa: F401
        import keyring  # noqa: F401
        import numpy  # noqa: F401
        import psutil  # noqa: F401
        import pynput  # noqa: F401
        import sounddevice  # noqa: F401
        application = QApplication.instance() or QApplication(["LocalVoice-Package-Smoke"])
        application.setApplicationName(APP_NAME)
        icon = QIcon(str(resource_path("resources/localvoice.png")))
        if icon.isNull():
            raise RuntimeError("The packaged application icon could not be loaded.")
        application.setWindowIcon(icon)
        application.processEvents()
        print("LocalVoice package smoke test passed.")
        return 0
    except Exception as exc:
        print(f"LocalVoice package smoke test failed: {exc}", file=sys.stderr)
        return 2

def main() -> int:
    parser = argparse.ArgumentParser(prog="LocalVoice")
    parser.add_argument("--minimized", action="store_true")
    parser.add_argument("--package-smoke-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--choose-language",
        action="store_true",
        help="show the language/onboarding selection without deleting user data",
    )
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("--show", action="store_true", help="show the running LocalVoice window")
    command_group.add_argument("--start", action="store_true", help="start recording in the running LocalVoice instance")
    command_group.add_argument("--stop", action="store_true", help="stop recording in the running LocalVoice instance")
    command_group.add_argument("--toggle", action="store_true", help="toggle recording in the running LocalVoice instance")
    command_group.add_argument("--cancel", action="store_true", help="cancel recording in the running LocalVoice instance")
    args = parser.parse_args()
    if args.package_smoke_test:
        return _package_smoke_test()
    requested_command = (
        "choose-language"
        if args.choose_language
        else next(
            (name for name in ("show", "start", "stop", "toggle", "cancel") if getattr(args, name, False)),
            "show",
        )
    )
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Rahmi Apps")
    app.setQuitOnLastWindowClosed(False)

    guard = SingleInstanceGuard()
    if not guard.acquired:
        if SingleInstanceGuard.send_command(requested_command):
            return 0
        QMessageBox.information(None, "LocalVoice", tr("en", "single_instance"))
        return 0
    app.aboutToQuit.connect(guard.release)
    command_server = InstanceCommandServer(app)
    if not command_server.start():
        logging.getLogger("localvoice.ipc").warning("Could not start the local command server")
    app.aboutToQuit.connect(command_server.close)

    try:
        store = SettingsStore(system_language=QLocale.system().name())
        if args.choose_language:
            store.prepare_language_selection()
    except Exception as exc:
        logging.exception("Settings initialization failed")
        QMessageBox.critical(None, "LocalVoice", str(exc)[:1000])
        return 1

    app.setStyleSheet(stylesheet(store.current.theme, store.current.ui_size))
    icon = QIcon(str(resource_path("resources/localvoice.png")))
    app.setWindowIcon(icon)

    # Language selection must happen before constructing the main window or any
    # language-dependent application UI. This guarantees that a stale setting
    # can never flash or leave the application in the wrong language.
    onboarding_completed_now = False
    if not store.current.first_run_complete or store.needs_language_confirmation:
        onboarding = OnboardingDialog(store, None)
        if onboarding.exec() != OnboardingDialog.Accepted:
            return 0
        onboarding_completed_now = True
        app.setStyleSheet(stylesheet(store.current.theme, store.current.ui_size))

    try:
        secure_store = SecureStore()
    except SecurityError as exc:
        logging.exception("Security store initialization failed")
        _show_security_error(store.current.ui_language, str(exc))
        return 1

    if not _unlock_store(secure_store, store.current.ui_language):
        return 0
    if secure_store.keyring_cleanup_pending:
        QMessageBox.warning(
            None,
            "LocalVoice",
            tr(store.current.ui_language, "keyring_cleanup_warning"),
        )

    try:
        cleanup_stale_recordings()
        database = LocalDatabase(secure_store)
        database.purge_history(store.current.history_retention_days)
        database.prune_history(store.current.max_history_items)
        database.purge_saved_audio(store.current.audio_retention_days)
    except Exception as exc:
        logging.exception("Local storage initialization failed")
        QMessageBox.critical(None, "LocalVoice", str(exc)[:1000])
        return 1

    clipboard = app.clipboard()
    injector = TextInjector(clipboard.setText, clipboard.clear, clipboard.text)
    controller = AppController(store, database, injector)
    app.aboutToQuit.connect(controller.shutdown)
    hotkeys = GlobalHotkeyService()
    window = MainWindow(store, secure_store, database, controller, hotkeys, icon)

    def handle_instance_command(command: str) -> None:
        if command == "show":
            window._show_window()
        elif command == "start":
            controller.request_start.emit()
        elif command == "stop":
            controller.request_stop.emit()
        elif command == "toggle":
            controller.request_toggle.emit()
        elif command == "cancel":
            controller.request_cancel.emit()
        elif command == "choose-language":
            store.prepare_language_selection()
            onboarding = OnboardingDialog(store, window)
            if onboarding.exec() == OnboardingDialog.Accepted:
                app.setStyleSheet(stylesheet(store.current.theme, store.current.ui_size))
                window._settings_applied()
                window._show_window()

    command_server.command_received.connect(handle_instance_command)

    def report_unhandled(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger("localvoice.crash").critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        QMessageBox.critical(window, tr(store.current.ui_language, "error"), str(exc_value)[:1000])

    sys.excepthook = report_unhandled

    if onboarding_completed_now:
        window._settings_applied()
        if not WhisperEngine().is_model_available(store.current.model_size, store.current.local_model_path):
            ModelManagerDialog(store, LocalTranslator(), store.current.ui_language, window).exec()
        QTimer.singleShot(200, controller.preload_current_model)

    if not args.minimized and not store.current.start_minimized:
        window.show()
    explicit_command = next(
        (name for name in ("start", "stop", "toggle", "cancel", "show") if getattr(args, name, False)),
        "",
    )
    if explicit_command:
        QTimer.singleShot(0, lambda value=explicit_command: handle_instance_command(value))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
