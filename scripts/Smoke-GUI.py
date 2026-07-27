from __future__ import annotations

"""Headless GUI construction smoke test used by native release builds.

This does not access the microphone, download models, or start global hooks. It
constructs every principal window/dialog and exercises language/theme refresh so
Qt API mismatches and missing widgets fail the release build early.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Must be set before importing platformdirs, Qt or pynput.
_SANDBOX = tempfile.TemporaryDirectory(prefix="localvoice-gui-smoke-")
_ROOT = Path(_SANDBOX.name)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYNPUT_BACKEND", "dummy")
os.environ["XDG_CONFIG_HOME"] = str(_ROOT / "config")
os.environ["XDG_DATA_HOME"] = str(_ROOT / "data")
os.environ["XDG_CACHE_HOME"] = str(_ROOT / "cache")
os.environ["XDG_STATE_HOME"] = str(_ROOT / "state")
os.environ["APPDATA"] = str(_ROOT / "appdata")
os.environ["LOCALAPPDATA"] = str(_ROOT / "localappdata")

from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from localvoice.core.controller import AppController  # noqa: E402
from localvoice.core.database import LocalDatabase  # noqa: E402
from localvoice.core.hotkeys import GlobalHotkeyService  # noqa: E402
from localvoice.core.models import Profile, TranscriptionResult  # noqa: E402
from localvoice.core.security import SecureStore  # noqa: E402
from localvoice.core.settings import SettingsStore  # noqa: E402
from localvoice.core.system import TextInjector  # noqa: E402
from localvoice.core.translation import LocalTranslator  # noqa: E402
from localvoice.ui.dialogs import (  # noqa: E402
    HistoryDialog,
    HistoryEditDialog,
    InfoDialog,
    LanguageSelectionDialog,
    ModelManagerDialog,
    OnboardingDialog,
    PreviewDialog,
    ProfileEditDialog,
    ProfilesDialog,
    SettingsDialog,
    StatisticsDialog,
    VocabularyDialog,
    VocabularyEditDialog,
)
from localvoice.ui.main_window import MainWindow  # noqa: E402
from localvoice.ui.overlay import RecordingOverlay  # noqa: E402
from localvoice.ui.theme import stylesheet  # noqa: E402


def _close(widget) -> None:
    try:
        # The model manager intentionally warns users when they close without a
        # model. A headless construction smoke test must not open a modal prompt.
        if isinstance(widget, ModelManagerDialog):
            widget.accept()
        else:
            widget.close()
        widget.deleteLater()
    except RuntimeError:
        pass


def main() -> int:
    app = QApplication.instance() or QApplication(["LocalVoice-GUI-Smoke"])
    app.setQuitOnLastWindowClosed(False)
    store = SettingsStore()
    store.current.first_run_complete = True
    store.save()
    secure = SecureStore()
    database = LocalDatabase(secure)
    injector = TextInjector(app.clipboard().setText, app.clipboard().clear, app.clipboard().text)
    controller = AppController(store, database, injector)
    hotkeys = GlobalHotkeyService()

    sample = TranscriptionResult(
        original_text="Hello LocalVoice",
        final_text="Hallo LocalVoice",
        detected_language="en",
        language_probability=0.98,
        translated=True,
        duration_seconds=1.5,
        word_count=2,
        target_application="SmokeTest",
    )
    database.add_history(sample)
    database.add_vocabulary("Dayter X", "DateraX", "all", True, False)
    database.save_profile(Profile(name="Smoke profile", applications=["SmokeTest"]))

    widgets = []
    try:
        for language in ("de", "en", "fr", "it", "es", "zh"):
            store.current.ui_language = language
            store.save()
            app.setStyleSheet(stylesheet("dark"))
            widgets.extend(
                [
                    PreviewDialog(sample, language),
                    LanguageSelectionDialog(language, ["de", "en", "fr"]),
                    OnboardingDialog(store),
                    SettingsDialog(store, secure, database),
                    StatisticsDialog(database, language),
                    HistoryEditDialog({"original_text": sample.original_text, "final_text": sample.final_text}, language),
                    HistoryDialog(database, language),
                    VocabularyEditDialog(language),
                    VocabularyDialog(database, language),
                    ProfileEditDialog(language, Profile(name="Smoke")),
                    ProfilesDialog(database, store, language),
                    ModelManagerDialog(store, LocalTranslator(), language),
                    InfoDialog("LocalVoice", "# Smoke", None),
                    RecordingOverlay(store.current),
                ]
            )
            for widget in widgets[-14:]:
                widget.ensurePolished()

        # Do not install system-wide hooks during a headless smoke test.
        with patch.object(MainWindow, "_configure_hotkeys", lambda self: None):
            window = MainWindow(store, secure, database, controller, hotkeys, QIcon())
            widgets.append(window)
            window.ensurePolished()
            window.refresh_texts()
            window.refresh_status_cards()
            window.overlay.start_recording(store.current)
            window.overlay.set_level(0.5)
            window.overlay.set_detected_language("English")
            window.overlay.set_state("processing")
            window.overlay.hide()

        app.processEvents()
        print("GUI smoke test passed: principal windows and dialogs constructed in 6 UI languages.")
        return 0
    finally:
        hotkeys.stop()
        for widget in reversed(widgets):
            _close(widget)
        app.processEvents()
        _SANDBOX.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
