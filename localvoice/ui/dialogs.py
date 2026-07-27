from __future__ import annotations

import copy
import shutil
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeyEvent, QKeySequence, QMouseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from localvoice.core.audio import AudioRecorder
from localvoice.core.database import LocalDatabase
from localvoice.core.hotkeys import GlobalHotkeyService
from localvoice.core.i18n import LANGUAGES, SPEECH_LANGUAGES, speech_language_name, tr
from localvoice.core.models import AppSettings, Profile, TranscriptionResult
from localvoice.core.paths import DATA_DIR, EXPORT_DIR
from localvoice.core.security import SecureStore
from localvoice.core.settings import SettingsStore
from localvoice.core.system import AutostartManager, open_path
from localvoice.core.translation import LocalTranslator
from localvoice.core.transcription import WhisperEngine
from localvoice.core.validation import (
    COMPUTE_TYPES,
    normalize_app_list,
    normalize_hotkey,
    normalize_language_list,
    normalize_language_target_rules,
)


class HotkeyEdit(QLineEdit):
    """Read-only field that records keyboard combinations and extra mouse buttons."""

    def __init__(self, value: str = "") -> None:
        super().__init__(value.upper())
        self.setReadOnly(True)
        self.setPlaceholderText("F8 / Ctrl+Space / Num5 / Mouse4")

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        key = int(event.key())
        if key in {int(Qt.Key_Backspace), int(Qt.Key_Delete)}:
            self.clear()
            return
        modifier_keys = {int(Qt.Key_Control), int(Qt.Key_Shift), int(Qt.Key_Alt), int(Qt.Key_Meta)}
        if key in modifier_keys:
            return
        parts: list[str] = []
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.MetaModifier:
            parts.append("meta")
        name = ""
        if modifiers & Qt.KeypadModifier and int(Qt.Key_0) <= key <= int(Qt.Key_9):
            name = f"num{key - int(Qt.Key_0)}"
        elif int(Qt.Key_F1) <= key <= int(Qt.Key_F35):
            name = f"f{key - int(Qt.Key_F1) + 1}"
        else:
            special = {
                int(Qt.Key_Space): "space", int(Qt.Key_Return): "enter", int(Qt.Key_Enter): "enter",
                int(Qt.Key_Tab): "tab", int(Qt.Key_Escape): "escape", int(Qt.Key_Insert): "insert",
            }
            name = special.get(key, "")
            if not name:
                text = event.text().strip().lower()
                name = text if len(text) == 1 else QKeySequence(key).toString().lower().replace(" ", "")
        if name:
            normalized = normalize_hotkey("+".join(parts + [name]), default="")
            if normalized:
                self.setText(normalized.upper())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        mapping = {
            Qt.MouseButton.MiddleButton: "mousemiddle",
            Qt.MouseButton.BackButton: "mouse4",
            Qt.MouseButton.ForwardButton: "mouse5",
        }
        value = mapping.get(event.button())
        if value:
            self.setText(value.upper())
            event.accept()
            return
        super().mousePressEvent(event)


def combo_with_items(items: list[tuple[str, object]], current: object | None = None) -> QComboBox:
    """Create a combo without duplicate entries and restore by item data."""
    combo = QComboBox()
    seen: set[tuple[str, str]] = set()
    for label, data in items:
        identity = (str(label), repr(data))
        if identity in seen:
            continue
        seen.add(identity)
        combo.addItem(label, data)
    if current is not None:
        index = combo.findData(current)
        if index >= 0:
            combo.setCurrentIndex(index)
    return combo


def spin_control(spin: QSpinBox | QDoubleSpinBox) -> QWidget:
    """Wrap a spin box with reliable decrement/increment buttons."""
    spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
    wrapper = QWidget()
    wrapper.setObjectName("SpinControl")
    row = QHBoxLayout(wrapper)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(7)
    row.addWidget(spin, 1)
    down = QToolButton()
    down.setObjectName("StepButton")
    down.setText("−")
    down.setAutoRepeat(True)
    down.clicked.connect(spin.stepDown)
    up = QToolButton()
    up.setObjectName("StepButton")
    up.setText("+")
    up.setAutoRepeat(True)
    up.clicked.connect(spin.stepUp)
    row.addWidget(down)
    row.addWidget(up)
    return wrapper


class LanguageSelectionDialog(QDialog):
    """Searchable language picker while preserving manual code entry."""

    COMMON = ("de", "en", "fr", "it", "es", "tr", "ar", "pt", "nl", "pl", "ru", "zh", "ja", "ko")

    def __init__(self, language: str, selected: list[str], parent=None) -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(tr(language, "choose_languages"))
        self.resize(620, 620)
        root = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr(language, "search_languages"))
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)
        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.setSelectionMode(QAbstractItemView.NoSelection)
        selected_set = set(normalize_language_list(selected))
        entries = [
            (speech_language_name(language, code), code)
            for code in SPEECH_LANGUAGES
            if code != "auto"
        ]
        for label, code in sorted(entries, key=lambda item: item[0].casefold()):
            item = QListWidgetItem(f"{label}   ·   {code}")
            item.setData(Qt.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked if code in selected_set else Qt.Unchecked)
            self.list.addItem(item)
        root.addWidget(self.list, 1)
        actions = QHBoxLayout()
        common = QPushButton(tr(language, "select_common_languages"))
        common.clicked.connect(self._select_common)
        clear = QPushButton(tr(language, "clear_selection"))
        clear.clicked.connect(self._clear)
        actions.addWidget(common)
        actions.addWidget(clear)
        actions.addStretch(1)
        self.counter = QLabel()
        self.counter.setObjectName("Muted")
        actions.addWidget(self.counter)
        root.addLayout(actions)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr(language, "apply"))
        buttons.button(QDialogButtonBox.Ok).setObjectName("Primary")
        buttons.button(QDialogButtonBox.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.list.itemChanged.connect(lambda _item: self._update_counter())
        self._update_counter()

    def _filter(self, text: str) -> None:
        needle = text.strip().casefold()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(bool(needle) and needle not in item.text().casefold())

    def _select_common(self) -> None:
        common = set(self.COMMON)
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setCheckState(Qt.Checked if item.data(Qt.UserRole) in common else Qt.Unchecked)

    def _clear(self) -> None:
        for index in range(self.list.count()):
            self.list.item(index).setCheckState(Qt.Unchecked)

    def _update_counter(self) -> None:
        self.counter.setText(tr(self.language, "languages_selected", count=len(self.selected_codes)))

    @property
    def selected_codes(self) -> list[str]:
        result: list[str] = []
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.checkState() == Qt.Checked:
                result.append(str(item.data(Qt.UserRole)))
        return result


def scrollable_popup_page(widget: QWidget) -> QScrollArea:
    """Keep popup settings accessible on smaller displays without page-long scrolling."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(widget)
    return scroll


def speech_items(include_auto: bool = True, include_same: bool = False, language: str = "en") -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if include_same:
        values.append((tr(language, "same_as_spoken"), "same"))
    for code in SPEECH_LANGUAGES:
        if code == "auto":
            if include_auto:
                values.append((tr(language, "auto_detect"), code))
        else:
            values.append((speech_language_name(language, code), code))
    return values


class HotkeyTestDialog(QDialog):
    """Test the real global-hotkey backend, not only a focused text field."""

    detected = Signal(str)
    backend_ready = Signal(str)
    backend_error = Signal(str)

    def __init__(self, expected: str, language: str, parent=None) -> None:
        super().__init__(parent)
        self.expected = normalize_hotkey(expected, default="")
        self.language = language
        self.service = GlobalHotkeyService()
        self._cleaned = False
        self.setWindowTitle(tr(language, "hotkey_test"))
        self.resize(600, 320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(13)
        title = QLabel(tr(language, "hotkey_test"))
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        hint = QLabel(tr(language, "hotkey_test_hint"))
        hint.setWordWrap(True)
        hint.setObjectName("Muted")
        layout.addWidget(hint)
        expected = QLabel(self.expected.upper())
        expected.setObjectName("BigValue")
        layout.addWidget(expected)
        self.status = QLabel(tr(language, "status_starting"))
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr(language, "close"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.detected.connect(self._detected)
        self.backend_ready.connect(self._ready)
        self.backend_error.connect(self._failed)
        self.finished.connect(lambda _result: self._cleanup())
        QTimer.singleShot(80, self._start_backend)

    def _start_backend(self) -> None:
        if self._cleaned or not self.expected:
            self._failed(tr(self.language, "invalid_hotkey"))
            return
        self.service.configure(self.expected, "toggle", True, suppress_keystroke=False)
        self.service.on_toggle = self.detected.emit
        self.service.on_start = self.detected.emit
        self.service.on_backend_ready = self.backend_ready.emit
        self.service.on_backend_error = self.backend_error.emit
        try:
            self.service.start()
        except Exception as exc:
            self._failed(str(exc))

    def _ready(self, backend: str) -> None:
        self.status.setText(tr(self.language, "hotkey_test_waiting", backend=backend))

    def _detected(self, identity: str) -> None:
        if normalize_hotkey(identity, default="") == self.expected:
            self.status.setText("✓ " + tr(self.language, "hotkey_test_success"))
            self.status.setStyleSheet("color:#35D3A7;font-weight:800;")

    def _failed(self, message: str) -> None:
        self.status.setText(tr(self.language, "hotkey_unavailable") + "\n" + str(message)[:700])
        self.status.setStyleSheet("color:#FFB84D;font-weight:700;")

    def _cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        self.service.stop()
        self.service.on_toggle = None
        self.service.on_start = None
        self.service.on_backend_ready = None
        self.service.on_backend_error = None

    def reject(self) -> None:
        self._cleanup()
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._cleanup()
        event.accept()


class PreviewDialog(QDialog):
    def __init__(self, result: TranscriptionResult, language: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr(language, "preview"))
        self.resize(720, 470)
        layout = QVBoxLayout(self)
        info = QLabel(
            f"{tr(language, 'detected_language')}: {speech_language_name(language, result.detected_language)}  ·  "
            f"{result.language_probability:.0%}  ·  {result.word_count} {tr(language, 'words')}"
        )
        info.setObjectName("Muted")
        layout.addWidget(info)
        self.editor = QTextEdit(result.final_text)
        layout.addWidget(self.editor, 1)
        buttons = QDialogButtonBox()
        insert_button = buttons.addButton(tr(language, "insert"), QDialogButtonBox.AcceptRole)
        buttons.addButton(tr(language, "cancel"), QDialogButtonBox.RejectRole)
        insert_button.setObjectName("Primary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def text(self) -> str:
        return self.editor.toPlainText().strip()


class PinDialog(QDialog):
    def __init__(self, language: str, mode: str = "unlock", parent=None) -> None:
        super().__init__(parent)
        self.language = language
        self.mode = mode
        self.setWindowTitle(tr(language, "pin_protection"))
        layout = QFormLayout(self)
        self.pin = QLineEdit()
        self.pin.setEchoMode(QLineEdit.Password)
        self.pin.setMaxLength(256)
        layout.addRow(tr(language, "pin"), self.pin)
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)
        self.confirm.setMaxLength(256)
        if mode == "set":
            layout.addRow(tr(language, "confirm_pin"), self.confirm)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr(language, "apply" if mode == "set" else "unlock"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _accept(self) -> None:
        if self.mode == "set" and self.pin.text() != self.confirm.text():
            QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "pin_mismatch"))
            return
        if not 4 <= len(self.pin.text()) <= 256:
            QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "pin_length"))
            return
        self.accept()


class MicrophoneTestDialog(QDialog):
    """Five-second microphone test without Qt objects in PortAudio callbacks."""

    def __init__(self, device: int | None, language: str, parent=None) -> None:
        super().__init__(parent)
        self.language = language
        self.device = device
        self.recorder = AudioRecorder()
        self._peak_level = 0.0
        self._closed = False
        self._cleaned = False
        self.setWindowTitle(tr(language, "microphone_test"))
        self.resize(620, 340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)
        label = QLabel(tr(language, "test_recording"))
        label.setObjectName("SectionTitle")
        layout.addWidget(label)
        explainer = QLabel(tr(language, "microphone_test_explainer"))
        explainer.setWordWrap(True)
        explainer.setObjectName("Muted")
        layout.addWidget(explainer)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)
        self.status = QLabel(tr(language, "recording_running"))
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr(language, "close"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Poll a plain float from AudioRecorder. Never store a bound Qt signal in
        # PortAudio's CFFI callback; the dialog may be destroyed before the final
        # native callback completes.
        self._level_timer = QTimer(self)
        self._level_timer.setInterval(45)
        self._level_timer.timeout.connect(self._poll_level)
        self._finish_timer = QTimer(self)
        self._finish_timer.setSingleShot(True)
        self._finish_timer.timeout.connect(self._finish)
        self.finished.connect(lambda _result: self._cleanup())
        QTimer.singleShot(120, self._start)

    def _poll_level(self) -> None:
        if self._closed:
            return
        value = self.recorder.latest_level
        self._peak_level = max(self._peak_level, value)
        self.progress.setValue(int(max(0.0, min(1.0, value)) * 100))

    def _start(self) -> None:
        if self._closed:
            return
        try:
            self.recorder.start(self.device)
            self.status.setText(
                f"{tr(self.language, 'recording_running')} · {self.recorder.recording_sample_rate / 1000:g} kHz"
            )
            self._level_timer.start()
            self._finish_timer.start(5000)
        except Exception as exc:
            self._level_timer.stop()
            self.recorder.detach_callbacks()
            self.status.setText(f"{tr(self.language, 'microphone_error')}\n{str(exc)[:700]}")

    def _finish(self) -> None:
        if self._closed:
            return
        self._level_timer.stop()
        path = None
        try:
            self.recorder.detach_callbacks()
            if self.recorder.is_recording:
                path, _ = self.recorder.stop()
        except Exception as exc:
            self.status.setText(f"{tr(self.language, 'microphone_error')}\n{str(exc)[:700]}")
            return
        finally:
            if path and path.exists():
                path.unlink(missing_ok=True)
        self.progress.setValue(int(max(0.0, min(1.0, self._peak_level)) * 100))
        if not self.status.text().startswith(tr(self.language, "microphone_error")):
            self.status.setText(
                tr(self.language, "test_success")
                if path is not None and self._peak_level >= 0.012
                else tr(self.language, "microphone_no_signal")
            )

    def _cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        self._closed = True
        self._finish_timer.stop()
        self._level_timer.stop()
        self.recorder.detach_callbacks()
        if self.recorder.is_recording:
            try:
                self.recorder.cancel()
            except Exception:
                pass

    def reject(self) -> None:
        self._cleanup()
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._cleanup()
        event.accept()


class OnboardingDialog(QDialog):
    def __init__(self, store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.settings = copy.deepcopy(store.current)
        self.language = self.settings.ui_language
        # Keep the user's explicit selection independently from the combo box.
        # This prevents Qt rebuild/index side effects from ever changing the saved
        # language to the last entry (Chinese) on Windows.
        self._selected_ui_language = self.language if self.language in LANGUAGES else "de"
        self.setWindowTitle("LocalVoice")
        self.setModal(True)
        self.resize(780, 540)
        root = QVBoxLayout(self)
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)
        self._build_pages()
        footer = QHBoxLayout()
        self.step_label = QLabel()
        self.step_label.setObjectName("Muted")
        footer.addWidget(self.step_label)
        footer.addStretch(1)
        self.back_button = QPushButton(tr(self.language, "back"))
        self.next_button = QPushButton(tr(self.language, "next"))
        self.next_button.setObjectName("Primary")
        self.back_button.clicked.connect(self._back)
        self.next_button.clicked.connect(self._next)
        footer.addWidget(self.back_button)
        footer.addWidget(self.next_button)
        root.addLayout(footer)
        self._update_footer()

    def _page(self, title_key: str, text_key: str | None = None) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 24)
        title = QLabel(tr(self.language, title_key))
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        if text_key:
            text = QLabel(tr(self.language, text_key))
            text.setObjectName("Muted")
            text.setWordWrap(True)
            layout.addWidget(text)
        layout.addSpacing(18)
        return page, layout

    def _build_pages(self) -> None:
        page, layout = self._page("first_language_title", "first_language_text")
        self.ui_language_combo = combo_with_items(
            [(name, code) for code, name in LANGUAGES.items()],
            self._selected_ui_language,
        )
        # Keep the cached language in sync for live button translations, but
        # the final persisted value is always read directly from currentData().
        # This avoids stale signal/index state on Windows and in frozen builds.
        self.ui_language_combo.currentIndexChanged.connect(self._language_changed)
        layout.addWidget(self.ui_language_combo)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_privacy_title", "onboarding_privacy_text")
        privacy_card = QFrame()
        privacy_card.setObjectName("Card")
        card_layout = QVBoxLayout(privacy_card)
        for line in ("🔒  " + tr(self.language, "local_only"), "✓  " + tr(self.language, "no_api")):
            label = QLabel(line)
            label.setWordWrap(True)
            card_layout.addWidget(label)
        layout.addWidget(privacy_card)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_microphone_title")
        self.microphone_combo = QComboBox()
        devices = AudioRecorder.input_devices()
        if not devices:
            self.microphone_combo.addItem(tr(self.language, "no_microphones"), None)
        for device in devices:
            self.microphone_combo.addItem(str(device["name"]), device["index"])
        layout.addWidget(self.microphone_combo)
        mic_test_button = QPushButton(tr(self.language, "microphone_test"))
        mic_test_button.setEnabled(bool(devices))
        mic_test_button.clicked.connect(lambda: MicrophoneTestDialog(self.microphone_combo.currentData(), self.language, self).exec())
        layout.addWidget(mic_test_button)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_hotkey_title")
        form = QFormLayout()
        self.hotkey_edit = HotkeyEdit(self.settings.hotkey)
        self.recording_mode_combo = combo_with_items([
            (tr(self.language, "hold_mode"), "hold"),
            (tr(self.language, "toggle_mode"), "toggle"),
        ], self.settings.recording_mode)
        form.addRow(tr(self.language, "active_hotkey"), self.hotkey_edit)
        form.addRow(tr(self.language, "recording_mode"), self.recording_mode_combo)
        layout.addLayout(form)
        hint = QLabel(tr(self.language, "hotkey_hint"))
        hint.setWordWrap(True)
        hint.setObjectName("Muted")
        layout.addWidget(hint)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_language_title")
        form = QFormLayout()
        self.input_combo = combo_with_items(speech_items(True, False, self.language), self.settings.input_language)
        self.target_combo = combo_with_items(speech_items(False, True, self.language), self.settings.target_language)
        self.original_check = QCheckBox(tr(self.language, "show_original_translation"))
        form.addRow(tr(self.language, "input_language"), self.input_combo)
        form.addRow(tr(self.language, "target_language"), self.target_combo)
        form.addRow("", self.original_check)
        layout.addLayout(form)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_output_title")
        self.output_combo = combo_with_items([
            (tr(self.language, "insert_active_app"), "insert"),
            (tr(self.language, "clipboard_only"), "clipboard"),
            (tr(self.language, "preview_first"), "preview"),
            (tr(self.language, "localvoice_only"), "app"),
        ], self.settings.output_mode)
        layout.addWidget(self.output_combo)
        self.auto_enter = QCheckBox(tr(self.language, "auto_enter"))
        layout.addWidget(self.auto_enter)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_model_title", "download_on_use")
        self.model_combo = combo_with_items([
            (tr(self.language, "very_fast") + " · Tiny", "tiny"),
            (tr(self.language, "balanced") + " · Small", "small"),
            (tr(self.language, "accurate") + " · Medium", "medium"),
            (tr(self.language, "maximum_accuracy") + " · Large-v3", "large"),
        ], self.settings.model_size)
        layout.addWidget(self.model_combo)
        offline = QLabel(tr(self.language, "model_offline_required"))
        offline.setWordWrap(True)
        offline.setObjectName("Muted")
        layout.addWidget(offline)
        layout.addStretch(1)
        self.pages.addWidget(page)

        page, layout = self._page("onboarding_done_title", "onboarding_done_text")
        big = QLabel("🎙️")
        big.setAlignment(Qt.AlignCenter)
        big.setStyleSheet("font-size:92px;")
        layout.addWidget(big, 1)
        self.pages.addWidget(page)

    def _language_changed(self, _index: int) -> None:
        """Mirror the combo's current data for live onboarding translations."""
        selected = self.ui_language_combo.currentData()
        if selected not in LANGUAGES:
            return
        self._selected_ui_language = str(selected)
        self.language = self._selected_ui_language
        self.settings.ui_language = self._selected_ui_language
        self.back_button.setText(tr(self.language, "back"))
        self.next_button.setText(tr(self.language, "next"))
        self._update_footer()

    def _back(self) -> None:
        self.pages.setCurrentIndex(max(0, self.pages.currentIndex() - 1))
        self._update_footer()

    def _next(self) -> None:
        if self.pages.currentIndex() == self.pages.count() - 1:
            if self._commit():
                self.accept()
            return
        self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
        self._update_footer()

    def _update_footer(self) -> None:
        index = self.pages.currentIndex()
        self.step_label.setText(f"{index + 1} / {self.pages.count()}")
        self.back_button.setEnabled(index > 0)
        self.next_button.setText(tr(self.language, "finish" if index == self.pages.count() - 1 else "next"))

    def _commit(self) -> bool:
        # The combo's currentData is the sole authoritative value. Do not save
        # a cached signal value: it can become stale in Qt/PyInstaller builds.
        selected_language = self.ui_language_combo.currentData()
        if selected_language not in LANGUAGES:
            selected_language = self._selected_ui_language
        if selected_language not in LANGUAGES:
            selected_language = "de"
        self.language = str(selected_language)
        self.settings.ui_language = self.language
        self.settings.ui_language_confirmed = True
        self.settings.microphone_device = self.microphone_combo.currentData()
        self.settings.hotkey = normalize_hotkey(self.hotkey_edit.text(), default="f8")
        self.settings.recording_mode = str(self.recording_mode_combo.currentData())
        self.settings.input_language = str(self.input_combo.currentData())
        if self.settings.input_language == "auto":
            ordered = [self.language, *self.settings.preferred_languages, "en", "fr"]
            self.settings.preferred_languages = list(dict.fromkeys(code for code in ordered if code and code != "auto"))[:12]
        self.settings.target_language = str(self.target_combo.currentData())
        self.settings.show_original_and_translation = self.original_check.isChecked()
        self.settings.output_mode = str(self.output_combo.currentData())
        self.settings.auto_press_enter = self.auto_enter.isChecked()
        self.settings.model_size = str(self.model_combo.currentData())
        self.settings.first_run_complete = True
        try:
            self.store.confirm_ui_language(self.language)
            # confirm_ui_language validates the locale record; save the rest of
            # onboarding only after that validation has succeeded.
            self.store.save(self.settings)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "LocalVoice", str(exc))
            return False
        if (
            self.store.current.ui_language != self.language
            or not self.store.current.ui_language_confirmed
        ):
            QMessageBox.critical(self, "LocalVoice", tr(self.language, "language_save_failed"))
            return False
        return True


class SettingsDialog(QDialog):
    applied = Signal()

    def __init__(self, store: SettingsStore, secure_store: SecureStore, database: LocalDatabase | None = None, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.secure_store = secure_store
        self.database = database
        self.settings = copy.deepcopy(store.current)
        self.language = self.settings.ui_language
        self.setWindowTitle(tr(self.language, "settings"))
        self.resize(920, 690)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(scrollable_popup_page(self._general_tab()), tr(self.language, "appearance"))
        tabs.addTab(scrollable_popup_page(self._recording_tab()), tr(self.language, "recording"))
        tabs.addTab(scrollable_popup_page(self._languages_tab()), tr(self.language, "speech"))
        tabs.addTab(scrollable_popup_page(self._output_tab()), tr(self.language, "output_mode"))
        tabs.addTab(scrollable_popup_page(self._overlay_tab()), tr(self.language, "overlay"))
        tabs.addTab(scrollable_popup_page(self._privacy_tab()), tr(self.language, "privacy"))
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr(self.language, "save"))
        buttons.button(QDialogButtonBox.Save).setObjectName("Primary")
        buttons.button(QDialogButtonBox.Cancel).setText(tr(self.language, "cancel"))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _general_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        self.ui_language = combo_with_items([(name, code) for code, name in LANGUAGES.items()], self.settings.ui_language)
        self.ui_size = combo_with_items([
            (tr(self.language, "ui_size_small"), "small"),
            (tr(self.language, "ui_size_medium"), "medium"),
            (tr(self.language, "ui_size_large"), "large"),
        ], self.settings.ui_size)
        self.theme = combo_with_items([
            (tr(self.language, "dark"), "dark"), (tr(self.language, "light"), "light"),
            (tr(self.language, "system"), "system"),
        ], self.settings.theme)
        self.autostart = QCheckBox(tr(self.language, "autostart")); self.autostart.setChecked(self.settings.autostart)
        self.start_minimized = QCheckBox(tr(self.language, "start_minimized")); self.start_minimized.setChecked(self.settings.start_minimized)
        self.minimize_tray = QCheckBox(tr(self.language, "minimize_tray")); self.minimize_tray.setChecked(self.settings.minimize_to_tray)
        self.close_tray = QCheckBox(tr(self.language, "close_tray")); self.close_tray.setChecked(self.settings.close_to_tray)
        self.auto_profile = QCheckBox(tr(self.language, "auto_profile")); self.auto_profile.setChecked(self.settings.auto_profile_switching)
        form.addRow(tr(self.language, "app_language"), self.ui_language)
        form.addRow(tr(self.language, "theme"), self.theme)
        form.addRow(tr(self.language, "ui_size"), self.ui_size)
        for widget in (self.autostart, self.start_minimized, self.minimize_tray, self.close_tray, self.auto_profile):
            form.addRow("", widget)
        return tab

    def _recording_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        self.mic = QComboBox()
        self.mic.addItem(tr(self.language, "automatic"), None)
        for device in AudioRecorder.input_devices():
            self.mic.addItem(str(device["name"]), device["index"])
        index = self.mic.findData(self.settings.microphone_device)
        self.mic.setCurrentIndex(max(0, index))
        self.hotkey_enabled = QCheckBox(tr(self.language, "hotkey_enabled")); self.hotkey_enabled.setChecked(self.settings.hotkey_enabled)
        self.suppress_hotkey = QCheckBox(tr(self.language, "suppress_hotkey")); self.suppress_hotkey.setChecked(self.settings.suppress_hotkey_keystroke)
        self.hotkey = HotkeyEdit(self.settings.hotkey)
        self.secondary_hotkey = HotkeyEdit(self.settings.secondary_hotkey)
        self.mode = combo_with_items([
            (tr(self.language, "hold_mode"), "hold"), (tr(self.language, "toggle_mode"), "toggle")
        ], self.settings.recording_mode)
        self.noise = QCheckBox(tr(self.language, "noise_reduction")); self.noise.setChecked(self.settings.noise_reduction)
        self.normalize = QCheckBox(tr(self.language, "normalize_audio")); self.normalize.setChecked(self.settings.normalize_audio)
        self.auto_gain = QCheckBox(tr(self.language, "auto_microphone_gain")); self.auto_gain.setChecked(self.settings.auto_microphone_gain)
        self.microphone_gain = QDoubleSpinBox(); self.microphone_gain.setRange(.25, 8.0); self.microphone_gain.setSingleStep(.25); self.microphone_gain.setValue(self.settings.microphone_gain); self.microphone_gain.setSuffix("×")
        self.silence = QCheckBox(tr(self.language, "silence_stop")); self.silence.setChecked(self.settings.silence_stop_enabled)
        self.silence_seconds = QDoubleSpinBox(); self.silence_seconds.setRange(1, 30); self.silence_seconds.setValue(self.settings.silence_seconds); self.silence_seconds.setSuffix(" s")
        self.silence_threshold = QDoubleSpinBox(); self.silence_threshold.setDecimals(3); self.silence_threshold.setRange(.001, .25); self.silence_threshold.setSingleStep(.005); self.silence_threshold.setValue(self.settings.silence_threshold)
        self.max_duration = QSpinBox(); self.max_duration.setRange(0, 86_400); self.max_duration.setValue(self.settings.max_recording_seconds); self.max_duration.setSpecialValueText(tr(self.language, "unlimited")); self.max_duration.setSuffix(" s")
        self.sounds = QCheckBox(tr(self.language, "start_stop_sound")); self.sounds.setChecked(self.settings.start_stop_sound)
        self.hotkey_include = QLineEdit(", ".join(self.settings.hotkey_include_apps))
        self.hotkey_exclude = QLineEdit(", ".join(self.settings.hotkey_exclude_apps))
        mic_test = QPushButton(tr(self.language, "microphone_test"))
        mic_test.clicked.connect(lambda: MicrophoneTestDialog(self.mic.currentData(), self.language, self).exec())
        hotkey_test = QPushButton(tr(self.language, "hotkey_test"))
        hotkey_test.clicked.connect(lambda: HotkeyTestDialog(self.hotkey.text(), self.language, self).exec())
        form.addRow(tr(self.language, "microphone"), self.mic)
        form.addRow("", mic_test)
        form.addRow("", self.hotkey_enabled)
        form.addRow("", self.suppress_hotkey)
        form.addRow(tr(self.language, "active_hotkey"), self.hotkey)
        form.addRow("", hotkey_test)
        form.addRow(tr(self.language, "secondary_hotkey"), self.secondary_hotkey)
        form.addRow(tr(self.language, "recording_mode"), self.mode)
        form.addRow(tr(self.language, "hotkey_include_apps"), self.hotkey_include)
        form.addRow(tr(self.language, "hotkey_exclude_apps"), self.hotkey_exclude)
        form.addRow("", self.noise)
        form.addRow("", self.normalize)
        form.addRow("", self.auto_gain)
        auto_gain_hint = QLabel(tr(self.language, "auto_microphone_gain_hint")); auto_gain_hint.setObjectName("Muted"); auto_gain_hint.setWordWrap(True); form.addRow("", auto_gain_hint)
        form.addRow(tr(self.language, "microphone_gain"), spin_control(self.microphone_gain))
        form.addRow("", self.silence)
        form.addRow(tr(self.language, "silence_seconds"), spin_control(self.silence_seconds))
        form.addRow(tr(self.language, "level"), spin_control(self.silence_threshold))
        form.addRow(tr(self.language, "max_duration"), spin_control(self.max_duration))
        max_hint = QLabel(tr(self.language, "max_duration_hint")); max_hint.setObjectName("Muted"); max_hint.setWordWrap(True); form.addRow("", max_hint)
        form.addRow("", self.sounds)
        return tab

    def _languages_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        self.input_lang = combo_with_items(speech_items(True, False, self.language), self.settings.input_language)
        self.target_lang = combo_with_items(speech_items(False, True, self.language), self.settings.target_language)
        self.preferred_langs = QLineEdit(", ".join(self.settings.preferred_languages))
        self.preferred_langs.setPlaceholderText("de, en, fr")
        preferred_button = QPushButton(tr(self.language, "choose_languages"))
        preferred_button.setObjectName("SoftPrimary")
        preferred_button.clicked.connect(self._choose_preferred_languages)
        preferred_row = QHBoxLayout()
        preferred_row.setContentsMargins(0, 0, 0, 0)
        preferred_row.addWidget(self.preferred_langs, 1)
        preferred_row.addWidget(preferred_button)
        self.prefer_primary = QCheckBox(tr(self.language, "prefer_primary_language")); self.prefer_primary.setChecked(self.settings.prefer_primary_language)
        self.original_translation = QCheckBox(tr(self.language, "show_original_translation")); self.original_translation.setChecked(self.settings.show_original_and_translation)
        self.model = combo_with_items([("Tiny", "tiny"), ("Base", "base"), ("Small", "small"), ("Medium", "medium"), ("Large-v3", "large"), ("Turbo", "turbo")], self.settings.model_size)
        self.device = combo_with_items([(tr(self.language, "automatic"), "auto"), (tr(self.language, "cpu"), "cpu"), (tr(self.language, "gpu"), "cuda")], self.settings.compute_device)
        self.compute_type = combo_with_items([(value, value) for value in sorted(COMPUTE_TYPES)], self.settings.compute_type)
        self.recognition_mode = combo_with_items([
            (tr(self.language, "recognition_fast"), "fast"),
            (tr(self.language, "recognition_balanced"), "balanced"),
            (tr(self.language, "recognition_accurate"), "accurate"),
        ], self.settings.recognition_mode)
        self.beam = QSpinBox(); self.beam.setRange(1, 10); self.beam.setValue(self.settings.beam_size)
        self.preload_model = QCheckBox(tr(self.language, "preload_model")); self.preload_model.setChecked(self.settings.preload_model)
        self.live_transcription = QCheckBox(tr(self.language, "live_transcription")); self.live_transcription.setChecked(self.settings.live_transcription_enabled)
        self.live_preview = QCheckBox(tr(self.language, "live_preview")); self.live_preview.setChecked(self.settings.live_preview_enabled)
        self.live_chunk = QDoubleSpinBox(); self.live_chunk.setRange(3.0, 12.0); self.live_chunk.setSingleStep(.5); self.live_chunk.setValue(self.settings.live_chunk_seconds); self.live_chunk.setSuffix(" s")
        self.local_model_path = QLineEdit(self.settings.local_model_path)
        browse_model = QPushButton("…"); browse_model.clicked.connect(self._browse_model)
        model_path_row = QHBoxLayout(); model_path_row.addWidget(self.local_model_path, 1); model_path_row.addWidget(browse_model)
        self.translation_enabled = QCheckBox(tr(self.language, "translation_enabled")); self.translation_enabled.setChecked(self.settings.translation_enabled)
        self.translation_bridge = combo_with_items(speech_items(False, False, self.language), self.settings.translation_intermediate_language)
        self.language_target_rules = QLineEdit(", ".join(f"{source}:{target}" for source, target in self.settings.language_target_rules.items()))
        self.language_target_rules.setPlaceholderText("en:de, fr:de, de:en")
        self.detection_threshold = QDoubleSpinBox(); self.detection_threshold.setRange(0.0, 1.0); self.detection_threshold.setSingleStep(.05); self.detection_threshold.setValue(self.settings.language_detection_threshold)
        self.commands = QCheckBox(tr(self.language, "spoken_commands")); self.commands.setChecked(self.settings.spoken_commands)
        self.fillers = QCheckBox(tr(self.language, "remove_fillers")); self.fillers.setChecked(self.settings.remove_filler_words)
        self.numbers = QCheckBox(tr(self.language, "numbers_digits")); self.numbers.setChecked(self.settings.numbers_as_digits)
        self.automatic_punctuation = QCheckBox(tr(self.language, "automatic_punctuation")); self.automatic_punctuation.setChecked(self.settings.automatic_punctuation)
        self.writing_style = combo_with_items([
            (tr(self.language, "neutral"), "neutral"), (tr(self.language, "email_mode"), "email"),
            (tr(self.language, "chat_mode"), "chat"), (tr(self.language, "code_mode"), "code"),
        ], self.settings.writing_style)
        form.addRow(tr(self.language, "input_language"), self.input_lang)
        form.addRow(tr(self.language, "preferred_languages"), preferred_row)
        hint = QLabel(tr(self.language, "preferred_languages_hint")); hint.setObjectName("Muted"); form.addRow("", hint)
        form.addRow("", self.prefer_primary)
        primary_hint = QLabel(tr(self.language, "prefer_primary_language_hint")); primary_hint.setObjectName("Muted"); primary_hint.setWordWrap(True); form.addRow("", primary_hint)
        form.addRow(tr(self.language, "target_language"), self.target_lang)
        form.addRow("", self.original_translation)
        form.addRow(tr(self.language, "model_quality"), self.model)
        form.addRow(tr(self.language, "local_model_path"), model_path_row)
        form.addRow(tr(self.language, "compute_device"), self.device)
        form.addRow(tr(self.language, "compute_type"), self.compute_type)
        form.addRow(tr(self.language, "recognition_mode"), self.recognition_mode)
        form.addRow(tr(self.language, "beam_size"), spin_control(self.beam))
        form.addRow("", self.preload_model)
        form.addRow("", self.live_transcription)
        form.addRow("", self.live_preview)
        form.addRow(tr(self.language, "live_chunk_seconds"), spin_control(self.live_chunk))
        live_hint = QLabel(tr(self.language, "live_transcription_hint")); live_hint.setObjectName("Muted"); live_hint.setWordWrap(True); form.addRow("", live_hint)
        speed_hint = QLabel(tr(self.language, "recognition_mode_hint")); speed_hint.setObjectName("Muted"); speed_hint.setWordWrap(True); form.addRow("", speed_hint)
        form.addRow(tr(self.language, "detection_threshold"), spin_control(self.detection_threshold))
        form.addRow("", self.translation_enabled)
        form.addRow(tr(self.language, "translation_bridge"), self.translation_bridge)
        form.addRow(tr(self.language, "language_target_rules"), self.language_target_rules)
        rule_hint = QLabel(tr(self.language, "language_target_rules_hint")); rule_hint.setObjectName("Muted"); rule_hint.setWordWrap(True); form.addRow("", rule_hint)
        form.addRow(tr(self.language, "writing_style"), self.writing_style)
        form.addRow("", self.commands)
        form.addRow("", self.fillers)
        form.addRow("", self.numbers)
        form.addRow("", self.automatic_punctuation)
        return tab

    def _choose_preferred_languages(self) -> None:
        current = normalize_language_list(self.preferred_langs.text())
        dialog = LanguageSelectionDialog(self.language, current, self)
        if dialog.exec() == QDialog.Accepted:
            self.preferred_langs.setText(", ".join(dialog.selected_codes))

    def _browse_model(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr(self.language, "local_model_path"), self.local_model_path.text())
        if path:
            self.local_model_path.setText(path)

    def _output_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        self.output = combo_with_items([
            (tr(self.language, "insert_active_app"), "insert"),
            (tr(self.language, "clipboard_only"), "clipboard"),
            (tr(self.language, "preview_first"), "preview"),
            (tr(self.language, "localvoice_only"), "app"),
        ], self.settings.output_mode)
        self.enter = QCheckBox(tr(self.language, "auto_enter")); self.enter.setChecked(self.settings.auto_press_enter)
        self.restore_clipboard = QCheckBox(tr(self.language, "restore_clipboard")); self.restore_clipboard.setChecked(self.settings.restore_clipboard_after_insert)
        self.clipboard_clear = QSpinBox(); self.clipboard_clear.setRange(0, 3600); self.clipboard_clear.setValue(self.settings.clipboard_clear_seconds); self.clipboard_clear.setSuffix(" s")
        form.addRow(tr(self.language, "output_mode"), self.output)
        form.addRow("", self.enter)
        form.addRow("", self.restore_clipboard)
        form.addRow(tr(self.language, "clipboard_clear"), spin_control(self.clipboard_clear))
        return tab

    def _overlay_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        screens = [(tr(self.language, "active_monitor"), "active"), (tr(self.language, "primary_monitor"), "primary")]
        try:
            screens += [(f"{tr(self.language, 'monitor_label')} {i + 1}: {screen.name()}", f"index:{i}") for i, screen in enumerate(QApplication.screens())]
        except Exception:
            pass
        self.overlay_screen = combo_with_items(screens, self.settings.overlay_screen)
        self.overlay_position = combo_with_items([
            (tr(self.language, "bottom_right"), "bottom_right"), (tr(self.language, "bottom_center"), "bottom_center"),
            (tr(self.language, "top_right"), "top_right"), (tr(self.language, "near_cursor"), "near_cursor"),
            (tr(self.language, "custom_position"), "custom"),
        ], self.settings.overlay_position)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(.35, 1); self.opacity.setSingleStep(.05); self.opacity.setValue(self.settings.overlay_opacity)
        self.overlay_scale = QDoubleSpinBox(); self.overlay_scale.setRange(.7, 1.6); self.overlay_scale.setSingleStep(.1); self.overlay_scale.setValue(self.settings.overlay_scale)
        self.custom_x = QSpinBox(); self.custom_x.setRange(0, 20_000); self.custom_x.setValue(self.settings.overlay_custom_x)
        self.custom_y = QSpinBox(); self.custom_y.setRange(0, 20_000); self.custom_y.setValue(self.settings.overlay_custom_y)
        self.overlay_processing = QCheckBox(tr(self.language, "overlay_processing")); self.overlay_processing.setChecked(self.settings.overlay_show_processing)
        form.addRow(tr(self.language, "overlay_screen"), self.overlay_screen)
        form.addRow(tr(self.language, "overlay_position"), self.overlay_position)
        form.addRow(tr(self.language, "opacity"), spin_control(self.opacity))
        form.addRow(tr(self.language, "size"), spin_control(self.overlay_scale))
        form.addRow(tr(self.language, "coordinate_x"), spin_control(self.custom_x))
        form.addRow(tr(self.language, "coordinate_y"), spin_control(self.custom_y))
        form.addRow("", self.overlay_processing)
        return tab

    def _privacy_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(22, 22, 22, 22)
        self.save_history = QCheckBox(tr(self.language, "save_history")); self.save_history.setChecked(self.settings.save_history)
        self.save_audio = QCheckBox(tr(self.language, "save_audio")); self.save_audio.setChecked(self.settings.save_audio)
        self.private = QCheckBox(tr(self.language, "private_mode")); self.private.setChecked(self.settings.private_mode)
        self.save_history.toggled.connect(self._update_privacy_controls)
        self.private.toggled.connect(self._update_privacy_controls)
        self.retention = QSpinBox(); self.retention.setRange(0, 3650); self.retention.setValue(self.settings.history_retention_days); self.retention.setSpecialValueText(tr(self.language, "never")); self.retention.setSuffix(" " + tr(self.language, "days"))
        self.audio_retention = QSpinBox(); self.audio_retention.setRange(0, 3650); self.audio_retention.setValue(self.settings.audio_retention_days); self.audio_retention.setSpecialValueText(tr(self.language, "never")); self.audio_retention.setSuffix(" " + tr(self.language, "days"))
        self.max_history = QSpinBox(); self.max_history.setRange(100, 1_000_000); self.max_history.setValue(self.settings.max_history_items)
        pin_row = QHBoxLayout()
        self.pin_button = QPushButton(tr(self.language, "remove_pin" if self.secure_store.has_pin else "set_pin"))
        self.pin_button.clicked.connect(self._pin_action)
        pin_row.addWidget(self.pin_button)
        pin_row.addStretch(1)
        open_button = QPushButton(tr(self.language, "open_data_folder")); open_button.clicked.connect(lambda: open_path(DATA_DIR))
        clear_audio = QPushButton(tr(self.language, "clear_audio")); clear_audio.clicked.connect(self._clear_audio)
        form.addRow("", self.save_history)
        form.addRow("", self.save_audio)
        form.addRow("", self.private)
        form.addRow(tr(self.language, "retention"), spin_control(self.retention))
        form.addRow(tr(self.language, "audio_retention"), spin_control(self.audio_retention))
        form.addRow(tr(self.language, "max_history"), spin_control(self.max_history))
        form.addRow(tr(self.language, "pin_protection"), pin_row)
        form.addRow("", open_button)
        privacy_hint = QLabel(tr(self.language, "audio_requires_history")); privacy_hint.setObjectName("Muted"); privacy_hint.setWordWrap(True)
        form.addRow("", privacy_hint)
        form.addRow("", clear_audio)
        self._update_privacy_controls()
        return tab

    def _update_privacy_controls(self) -> None:
        private = self.private.isChecked()
        if private:
            self.save_history.setChecked(False)
            self.save_audio.setChecked(False)
        if not self.save_history.isChecked():
            self.save_audio.setChecked(False)
        self.save_history.setEnabled(not private)
        self.save_audio.setEnabled(not private and self.save_history.isChecked())

    def _clear_audio(self) -> None:
        audio_dir = DATA_DIR / "audio"
        if QMessageBox.question(self, tr(self.language, "clear_audio"), tr(self.language, "confirm_clear_audio")) != QMessageBox.Yes:
            return
        if self.database is not None:
            self.database.clear_saved_audio()
            return
        if audio_dir.exists():
            for path in list(audio_dir.glob("recording-*.lva")) + list(audio_dir.glob("recording-*.wav")):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    continue

    def _pin_action(self) -> None:
        if self.secure_store.has_pin:
            dialog = PinDialog(self.language, "unlock", self)
            if dialog.exec() and self.secure_store.disable_pin(dialog.pin.text()):
                self.pin_button.setText(tr(self.language, "set_pin"))
            elif dialog.result() == QDialog.Accepted:
                remaining = self.secure_store.lockout_seconds_remaining
                text = tr(self.language, "pin_locked", seconds=remaining) if remaining else tr(self.language, "wrong_pin")
                QMessageBox.warning(self, tr(self.language, "error"), text)
        else:
            dialog = PinDialog(self.language, "set", self)
            if dialog.exec():
                self.secure_store.enable_pin(dialog.pin.text())
                self.pin_button.setText(tr(self.language, "remove_pin"))

    def _save(self) -> None:
        primary = normalize_hotkey(self.hotkey.text(), default="")
        secondary = normalize_hotkey(self.secondary_hotkey.text(), default="") if self.secondary_hotkey.text().strip() else ""
        if not primary:
            QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "invalid_hotkey"))
            return
        if secondary and primary == secondary:
            QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "hotkey_conflict"))
            return
        if self.database is not None:
            values = [primary, secondary]
            for profile in self.database.list_profiles():
                if profile.enabled:
                    values.extend([profile.hotkey, profile.secondary_hotkey])
            if GlobalHotkeyService.conflicts([value for value in values if value]):
                QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "profile_hotkey_conflict"))
                return
        preferred = normalize_language_list(self.preferred_langs.text())
        if not preferred:
            preferred = ["de", "en", "fr"]
        s = self.settings
        selected_ui_language = self.ui_language.currentData()
        s.ui_language = str(selected_ui_language) if selected_ui_language in LANGUAGES else self.language
        s.ui_language_confirmed = True
        s.theme = str(self.theme.currentData())
        s.ui_size = str(self.ui_size.currentData())
        s.autostart = self.autostart.isChecked()
        s.start_minimized = self.start_minimized.isChecked()
        s.minimize_to_tray = self.minimize_tray.isChecked()
        s.close_to_tray = self.close_tray.isChecked()
        s.auto_profile_switching = self.auto_profile.isChecked()
        s.microphone_device = self.mic.currentData()
        s.hotkey_enabled = self.hotkey_enabled.isChecked()
        s.suppress_hotkey_keystroke = self.suppress_hotkey.isChecked()
        s.hotkey = primary
        s.secondary_hotkey = secondary
        s.hotkey_include_apps = normalize_app_list(self.hotkey_include.text())
        s.hotkey_exclude_apps = normalize_app_list(self.hotkey_exclude.text())
        s.recording_mode = str(self.mode.currentData())
        s.noise_reduction = self.noise.isChecked()
        s.normalize_audio = self.normalize.isChecked()
        s.auto_microphone_gain = self.auto_gain.isChecked()
        s.microphone_gain = self.microphone_gain.value()
        s.silence_stop_enabled = self.silence.isChecked()
        s.silence_seconds = self.silence_seconds.value()
        s.silence_threshold = self.silence_threshold.value()
        s.max_recording_seconds = self.max_duration.value()
        s.start_stop_sound = self.sounds.isChecked()
        s.input_language = str(self.input_lang.currentData())
        s.preferred_languages = preferred
        s.prefer_primary_language = self.prefer_primary.isChecked()
        s.local_model_path = self.local_model_path.text().strip()
        s.translation_enabled = self.translation_enabled.isChecked()
        s.translation_intermediate_language = str(self.translation_bridge.currentData())
        s.language_target_rules = normalize_language_target_rules(self.language_target_rules.text())
        s.language_detection_threshold = self.detection_threshold.value()
        s.target_language = str(self.target_lang.currentData())
        s.show_original_and_translation = self.original_translation.isChecked()
        s.model_size = str(self.model.currentData())
        s.compute_device = str(self.device.currentData())
        s.compute_type = str(self.compute_type.currentData())
        s.recognition_mode = str(self.recognition_mode.currentData())
        s.beam_size = self.beam.value()
        s.preload_model = self.preload_model.isChecked()
        s.live_transcription_enabled = self.live_transcription.isChecked()
        s.live_preview_enabled = self.live_preview.isChecked()
        s.live_chunk_seconds = self.live_chunk.value()
        s.spoken_commands = self.commands.isChecked()
        s.remove_filler_words = self.fillers.isChecked()
        s.numbers_as_digits = self.numbers.isChecked()
        s.automatic_punctuation = self.automatic_punctuation.isChecked()
        s.writing_style = str(self.writing_style.currentData())
        s.output_mode = str(self.output.currentData())
        s.auto_press_enter = self.enter.isChecked()
        s.restore_clipboard_after_insert = self.restore_clipboard.isChecked()
        s.clipboard_clear_seconds = self.clipboard_clear.value()
        s.overlay_screen = str(self.overlay_screen.currentData())
        s.overlay_position = str(self.overlay_position.currentData())
        s.overlay_opacity = self.opacity.value()
        s.overlay_scale = self.overlay_scale.value()
        s.overlay_custom_x = self.custom_x.value()
        s.overlay_custom_y = self.custom_y.value()
        s.overlay_show_processing = self.overlay_processing.isChecked()
        s.private_mode = self.private.isChecked()
        s.save_history = self.save_history.isChecked() and not s.private_mode
        s.save_audio = self.save_audio.isChecked() and s.save_history
        s.history_retention_days = self.retention.value()
        s.audio_retention_days = self.audio_retention.value()
        s.max_history_items = self.max_history.value()
        self.store.save(s)
        AutostartManager.set_enabled(self.store.current.autostart)
        self.applied.emit()
        self.accept()


class StatisticsDialog(QDialog):
    def __init__(self, database: LocalDatabase, language: str, parent=None) -> None:
        super().__init__(parent)
        self.db = database
        self.language = language
        self.setWindowTitle(tr(language, "statistics"))
        self.resize(700, 500)
        root = QVBoxLayout(self)
        stats = database.history_statistics()
        cards = QHBoxLayout()
        values = [
            (tr(language, "transcriptions"), str(stats["total_items"])),
            (tr(language, "total_words"), str(stats["total_words"])),
            (tr(language, "recording_time"), self._duration(float(stats["total_seconds"]))),
            (tr(language, "translations"), str(stats["translated_items"])),
        ]
        for label, value in values:
            card = QFrame(); card.setObjectName("Card")
            layout = QVBoxLayout(card)
            title = QLabel(label); title.setObjectName("Muted")
            number = QLabel(value); number.setObjectName("SectionTitle")
            layout.addWidget(title); layout.addWidget(number)
            cards.addWidget(card, 1)
        root.addLayout(cards)
        audio = QLabel(f"{tr(language, 'saved_recordings')}: {stats['audio_items']}")
        audio.setObjectName("Muted")
        root.addWidget(audio)
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels([tr(language, "detected_language"), tr(language, "transcriptions"), tr(language, "word_count")])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        languages = list(stats["languages"])
        table.setRowCount(len(languages))
        for row_index, row in enumerate(languages):
            values = [
                speech_language_name(language, str(row.get("detected_language", ""))),
                str(int(row.get("item_count", 0) or 0)),
                str(int(row.get("word_count", 0) or 0)),
            ]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        root.addWidget(table, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr(language, "close"))
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _duration(seconds: float) -> str:
        total = max(0, int(seconds))
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class HistoryEditDialog(QDialog):
    def __init__(self, row: dict[str, object], language: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr(language, "edit_history"))
        self.resize(720, 560)
        layout = QFormLayout(self)
        self.original = QTextEdit(str(row.get("original_text", "")))
        self.final = QTextEdit(str(row.get("final_text", "")))
        layout.addRow(tr(language, "original_text"), self.original)
        layout.addRow(tr(language, "final_text"), self.final)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr(language, "save"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class HistoryDialog(QDialog):
    def __init__(self, database: LocalDatabase, language: str, parent=None) -> None:
        super().__init__(parent)
        self.db = database
        self.language = language
        self.setWindowTitle(tr(language, "history"))
        self.resize(1120, 650)
        root = QVBoxLayout(self)
        search_row = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText(tr(language, "search")); self.search.textChanged.connect(self.reload)
        search_row.addWidget(self.search, 1)
        root.addLayout(search_row)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            tr(language, "date"), tr(language, "final_text"), tr(language, "input_language"),
            tr(language, "duration"), tr(language, "word_count"), tr(language, "translated_status"),
            tr(language, "audio"), tr(language, "target_app"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self._edit)
        root.addWidget(self.table, 1)
        bottom = QHBoxLayout()
        for text, handler in [
            (tr(language, "copy"), self._copy), (tr(language, "edit"), self._edit),
            (tr(language, "delete_selected"), self._delete), (tr(language, "delete_all"), self._delete_all),
            (tr(language, "export"), self._export), (tr(language, "export_audio"), self._export_audio),
        ]:
            button = QPushButton(text); button.clicked.connect(handler); bottom.addWidget(button)
        bottom.addStretch(1)
        root.addLayout(bottom)
        self.rows: list[dict[str, object]] = []
        self.reload()

    def reload(self) -> None:
        self.rows = self.db.list_history(self.search.text(), 5000)
        self.table.setRowCount(len(self.rows))
        for r, row in enumerate(self.rows):
            values = [
                str(row.get("created_at", ""))[:19].replace("T", " "),
                str(row.get("final_text", "")),
                speech_language_name(self.language, str(row.get("detected_language", ""))),
                f"{float(row.get('duration_seconds', 0)):.1f}s",
                str(int(row.get("word_count", 0) or 0)),
                tr(self.language, "yes" if bool(row.get("translated", False)) else "no"),
                tr(self.language, "yes" if bool(row.get("audio_path", "")) else "no"),
                str(row.get("target_application", "")),
            ]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(value))

    def _selected_rows(self) -> list[int]:
        return [index.row() for index in self.table.selectionModel().selectedRows()]

    def _selected_ids(self) -> list[int]:
        return [int(self.rows[index]["id"]) for index in self._selected_rows()]

    def _copy(self) -> None:
        selected = self._selected_rows()
        if selected:
            QApplication.clipboard().setText(str(self.rows[selected[0]].get("final_text", "")))

    def _edit(self) -> None:
        selected = self._selected_rows()
        if not selected:
            return
        row = self.rows[selected[0]]
        dialog = HistoryEditDialog(row, self.language, self)
        if dialog.exec() and dialog.final.toPlainText().strip():
            self.db.update_history_text(int(row["id"]), dialog.original.toPlainText(), dialog.final.toPlainText())
            self.reload()

    def _delete(self) -> None:
        self.db.delete_history(self._selected_ids())
        self.reload()

    def _delete_all(self) -> None:
        if QMessageBox.question(self, tr(self.language, "delete_all"), tr(self.language, "confirm_delete_all")) == QMessageBox.Yes:
            self.db.delete_all_history()
            self.reload()

    def _export_audio(self) -> None:
        selected = self._selected_rows()
        if not selected:
            return
        row = self.rows[selected[0]]
        if not row.get("audio_path"):
            QMessageBox.information(self, tr(self.language, "audio"), tr(self.language, "no_saved_audio"))
            return
        default_name = f"LocalVoice-{str(row.get('created_at', 'recording'))[:19].replace(':', '-').replace('T', '-')}.wav"
        path, _ = QFileDialog.getSaveFileName(
            self, tr(self.language, "export_audio"), str(EXPORT_DIR / default_name), "WAV audio (*.wav)"
        )
        if not path:
            return
        try:
            if not self.db.export_history_audio(int(row["id"]), Path(path)):
                raise RuntimeError(tr(self.language, "no_saved_audio"))
            QMessageBox.information(self, tr(self.language, "export_audio"), tr(self.language, "export_complete"))
        except Exception as exc:
            QMessageBox.warning(self, tr(self.language, "error"), str(exc)[:1000])

    def _export(self) -> None:
        QMessageBox.information(self, tr(self.language, "export_warning_title"), tr(self.language, "plaintext_export_warning"))
        path, _ = QFileDialog.getSaveFileName(
            self, tr(self.language, "export"), str(EXPORT_DIR / "LocalVoice-History.json"),
            "JSON (*.json);;CSV (*.csv);;Text (*.txt)",
        )
        if path:
            suffix = Path(path).suffix.lower().lstrip(".") or "json"
            self.db.export_history(Path(path), suffix)
            QMessageBox.information(self, tr(self.language, "export"), tr(self.language, "export_complete"))


class VocabularyEditDialog(QDialog):
    def __init__(self, language: str, entry: dict[str, object] | None = None, parent=None) -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(tr(language, "personal_dictionary"))
        form = QFormLayout(self)
        entry = entry or {}
        self.spoken = QLineEdit(str(entry.get("spoken_form", ""))); self.spoken.setMaxLength(500)
        self.written = QLineEdit(str(entry.get("written_form", ""))); self.written.setMaxLength(500)
        self.lang = combo_with_items([(tr(language, "all"), "all")] + [(speech_language_name(language, code), code) for code in SPEECH_LANGUAGES if code != "auto"], entry.get("language", "all"))
        self.never = QCheckBox(tr(language, "never_translate")); self.never.setChecked(bool(entry.get("never_translate", False)))
        self.case = QCheckBox(tr(language, "case_sensitive")); self.case.setChecked(bool(entry.get("case_sensitive", False)))
        form.addRow(tr(language, "spoken_form"), self.spoken)
        form.addRow(tr(language, "written_form"), self.written)
        form.addRow(tr(language, "input_language"), self.lang)
        form.addRow("", self.never)
        form.addRow("", self.case)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr(language, "save"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); form.addRow(buttons)


class VocabularyDialog(QDialog):
    def __init__(self, database: LocalDatabase, language: str, parent=None) -> None:
        super().__init__(parent)
        self.db = database
        self.language = language
        self.setWindowTitle(tr(language, "dictionary"))
        self.resize(800, 540)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr(language, "spoken_form"), tr(language, "written_form"), tr(language, "input_language"), tr(language, "never_translate"), tr(language, "case_sensitive")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        root.addWidget(self.table, 1)
        bottom = QHBoxLayout()
        for text, handler in [(tr(language, "add"), self._add), (tr(language, "edit"), self._edit), (tr(language, "delete"), self._delete)]:
            button = QPushButton(text); button.clicked.connect(handler); bottom.addWidget(button)
        bottom.addStretch(1)
        root.addLayout(bottom)
        self.rows: list[dict[str, object]] = []
        self.reload()

    def reload(self) -> None:
        self.rows = self.db.list_vocabulary()
        self.table.setRowCount(len(self.rows))
        for r, row in enumerate(self.rows):
            language_name = tr(self.language, "all") if row["language"] == "all" else speech_language_name(self.language, str(row["language"]))
            values = [str(row["spoken_form"]), str(row["written_form"]), language_name, tr(self.language, "yes" if row["never_translate"] else "no"), tr(self.language, "yes" if row["case_sensitive"] else "no")]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(value))

    def _current(self) -> dict[str, object] | None:
        rows = self.table.selectionModel().selectedRows()
        return self.rows[rows[0].row()] if rows else None

    def _add(self) -> None:
        dialog = VocabularyEditDialog(self.language, parent=self)
        if dialog.exec() and dialog.spoken.text().strip() and dialog.written.text().strip():
            self.db.add_vocabulary(dialog.spoken.text(), dialog.written.text(), str(dialog.lang.currentData()), dialog.never.isChecked(), dialog.case.isChecked())
            self.reload()

    def _edit(self) -> None:
        entry = self._current()
        if not entry:
            return
        dialog = VocabularyEditDialog(self.language, entry, self)
        if dialog.exec() and dialog.spoken.text().strip() and dialog.written.text().strip():
            self.db.update_vocabulary(int(entry["id"]), spoken_form=dialog.spoken.text(), written_form=dialog.written.text(), language=str(dialog.lang.currentData()), never_translate=dialog.never.isChecked(), case_sensitive=dialog.case.isChecked())
            self.reload()

    def _delete(self) -> None:
        entry = self._current()
        if entry:
            self.db.delete_vocabulary(int(entry["id"]))
            self.reload()


class ProfileEditDialog(QDialog):
    """Compact per-application profile editor grouped into popup-style tabs."""

    def __init__(self, language: str, profile: Profile | None = None, parent=None) -> None:
        super().__init__(parent)
        self.language = language
        self.profile = copy.deepcopy(profile or Profile(name=tr(language, "new_profile")))
        self.setWindowTitle(tr(language, "profiles"))
        self.resize(760, 690)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(scrollable_popup_page(self._general_page()), tr(language, "profiles"))
        tabs.addTab(scrollable_popup_page(self._language_page()), tr(language, "profile_language"))
        tabs.addTab(scrollable_popup_page(self._output_page()), tr(language, "profile_output"))
        tabs.addTab(scrollable_popup_page(self._audio_page()), tr(language, "profile_audio"))
        tabs.addTab(scrollable_popup_page(self._privacy_page()), tr(language, "profile_privacy"))
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr(language, "save"))
        buttons.button(QDialogButtonBox.Save).setObjectName("Primary")
        buttons.button(QDialogButtonBox.Cancel).setText(tr(language, "cancel"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _form_page(self) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(22, 22, 22, 22)
        return page, form

    def _general_page(self) -> QWidget:
        page, form = self._form_page()
        self.name = QLineEdit(self.profile.name); self.name.setMaxLength(120)
        self.apps = QLineEdit(", ".join(self.profile.applications))
        self.hotkey = HotkeyEdit(self.profile.hotkey)
        self.secondary_hotkey = HotkeyEdit(self.profile.secondary_hotkey)
        self.mode = combo_with_items([(tr(self.language, "hold_mode"), "hold"), (tr(self.language, "toggle_mode"), "toggle")], self.profile.recording_mode)
        self.microphone = QComboBox()
        self.microphone.addItem(tr(self.language, "automatic"), None)
        for device in AudioRecorder.input_devices():
            self.microphone.addItem(str(device["name"]), device["index"])
        microphone_index = self.microphone.findData(self.profile.microphone_device)
        self.microphone.setCurrentIndex(max(0, microphone_index))
        self.enabled = QCheckBox(tr(self.language, "enabled")); self.enabled.setChecked(self.profile.enabled)
        form.addRow(tr(self.language, "profile_name"), self.name)
        form.addRow(tr(self.language, "applications"), self.apps)
        hint = QLabel(tr(self.language, "app_profiles_hint")); hint.setObjectName("Muted"); hint.setWordWrap(True); form.addRow("", hint)
        form.addRow(tr(self.language, "active_hotkey"), self.hotkey)
        form.addRow(tr(self.language, "secondary_hotkey"), self.secondary_hotkey)
        form.addRow(tr(self.language, "recording_mode"), self.mode)
        form.addRow(tr(self.language, "microphone"), self.microphone)
        form.addRow("", self.enabled)
        return page

    def _language_page(self) -> QWidget:
        page, form = self._form_page()
        self.input = combo_with_items(speech_items(True, False, self.language), self.profile.input_language)
        self.preferred = QLineEdit(", ".join(self.profile.preferred_languages)); self.preferred.setPlaceholderText("de, en, fr")
        preferred_button = QPushButton(tr(self.language, "choose_languages"))
        preferred_button.setObjectName("SoftPrimary")
        preferred_button.clicked.connect(self._choose_profile_languages)
        preferred_row = QHBoxLayout(); preferred_row.setContentsMargins(0, 0, 0, 0)
        preferred_row.addWidget(self.preferred, 1); preferred_row.addWidget(preferred_button)
        self.target = combo_with_items(speech_items(False, True, self.language), self.profile.target_language)
        self.language_target_rules = QLineEdit(", ".join(f"{source}:{target}" for source, target in self.profile.language_target_rules.items()))
        self.language_target_rules.setPlaceholderText("en:de, fr:de, de:en")
        self.translation_enabled = QCheckBox(tr(self.language, "translation_enabled")); self.translation_enabled.setChecked(self.profile.translation_enabled)
        self.translation_bridge = combo_with_items(speech_items(False, False, self.language), self.profile.translation_intermediate_language)
        self.detection_threshold = QDoubleSpinBox(); self.detection_threshold.setRange(0.0, 1.0); self.detection_threshold.setSingleStep(.05); self.detection_threshold.setValue(self.profile.language_detection_threshold)
        self.prefer_primary = QCheckBox(tr(self.language, "prefer_primary_language")); self.prefer_primary.setChecked(self.profile.prefer_primary_language)
        self.original_translation = QCheckBox(tr(self.language, "show_original_translation")); self.original_translation.setChecked(self.profile.show_original_and_translation)
        self.style = combo_with_items([(tr(self.language, "neutral"), "neutral"), (tr(self.language, "email_mode"), "email"), (tr(self.language, "chat_mode"), "chat"), (tr(self.language, "code_mode"), "code")], self.profile.writing_style)
        self.commands = QCheckBox(tr(self.language, "spoken_commands")); self.commands.setChecked(self.profile.spoken_commands)
        self.fillers = QCheckBox(tr(self.language, "remove_fillers")); self.fillers.setChecked(self.profile.remove_filler_words)
        self.numbers = QCheckBox(tr(self.language, "numbers_digits")); self.numbers.setChecked(self.profile.numbers_as_digits)
        self.automatic_punctuation = QCheckBox(tr(self.language, "automatic_punctuation")); self.automatic_punctuation.setChecked(self.profile.automatic_punctuation)
        form.addRow(tr(self.language, "input_language"), self.input)
        form.addRow(tr(self.language, "preferred_languages"), preferred_row)
        pref_hint = QLabel(tr(self.language, "preferred_languages_hint")); pref_hint.setObjectName("Muted"); form.addRow("", pref_hint)
        form.addRow("", self.prefer_primary)
        primary_hint = QLabel(tr(self.language, "prefer_primary_language_hint")); primary_hint.setObjectName("Muted"); primary_hint.setWordWrap(True); form.addRow("", primary_hint)
        form.addRow(tr(self.language, "target_language"), self.target)
        form.addRow(tr(self.language, "language_target_rules"), self.language_target_rules)
        rules_hint = QLabel(tr(self.language, "language_target_rules_hint")); rules_hint.setObjectName("Muted"); rules_hint.setWordWrap(True); form.addRow("", rules_hint)
        form.addRow("", self.translation_enabled)
        form.addRow(tr(self.language, "translation_bridge"), self.translation_bridge)
        form.addRow(tr(self.language, "detection_threshold"), spin_control(self.detection_threshold))
        form.addRow("", self.original_translation)
        form.addRow(tr(self.language, "writing_style"), self.style)
        for widget in (self.commands, self.fillers, self.numbers, self.automatic_punctuation):
            form.addRow("", widget)
        return page

    def _choose_profile_languages(self) -> None:
        dialog = LanguageSelectionDialog(
            self.language,
            normalize_language_list(self.preferred.text()),
            self,
        )
        if dialog.exec() == QDialog.Accepted:
            self.preferred.setText(", ".join(dialog.selected_codes))

    def _output_page(self) -> QWidget:
        page, form = self._form_page()
        self.output = combo_with_items([(tr(self.language, "insert_active_app"), "insert"), (tr(self.language, "clipboard_only"), "clipboard"), (tr(self.language, "preview_first"), "preview"), (tr(self.language, "localvoice_only"), "app")], self.profile.output_mode)
        self.enter = QCheckBox(tr(self.language, "auto_enter")); self.enter.setChecked(self.profile.auto_press_enter)
        self.restore_clipboard = QCheckBox(tr(self.language, "restore_clipboard")); self.restore_clipboard.setChecked(self.profile.restore_clipboard_after_insert)
        self.clipboard_clear = QSpinBox(); self.clipboard_clear.setRange(0, 3600); self.clipboard_clear.setValue(self.profile.clipboard_clear_seconds); self.clipboard_clear.setSuffix(" s")
        form.addRow(tr(self.language, "output_mode"), self.output)
        form.addRow("", self.enter)
        form.addRow("", self.restore_clipboard)
        form.addRow(tr(self.language, "clipboard_clear"), spin_control(self.clipboard_clear))
        return page

    def _audio_page(self) -> QWidget:
        page, form = self._form_page()
        self.model = combo_with_items([("Tiny", "tiny"), ("Base", "base"), ("Small", "small"), ("Medium", "medium"), ("Large-v3", "large"), ("Turbo", "turbo")], self.profile.model_size)
        self.local_model_path = QLineEdit(self.profile.local_model_path)
        browse_model = QPushButton("…")
        browse_model.clicked.connect(self._browse_profile_model)
        model_path_row = QHBoxLayout(); model_path_row.addWidget(self.local_model_path, 1); model_path_row.addWidget(browse_model)
        self.device = combo_with_items([(tr(self.language, "automatic"), "auto"), (tr(self.language, "cpu"), "cpu"), (tr(self.language, "gpu"), "cuda")], self.profile.compute_device)
        self.compute_type = combo_with_items([(value, value) for value in sorted(COMPUTE_TYPES)], self.profile.compute_type)
        self.recognition_mode = combo_with_items([
            (tr(self.language, "recognition_fast"), "fast"),
            (tr(self.language, "recognition_balanced"), "balanced"),
            (tr(self.language, "recognition_accurate"), "accurate"),
        ], self.profile.recognition_mode)
        self.beam = QSpinBox(); self.beam.setRange(1, 10); self.beam.setValue(self.profile.beam_size)
        self.live_transcription = QCheckBox(tr(self.language, "live_transcription")); self.live_transcription.setChecked(self.profile.live_transcription_enabled)
        self.live_preview = QCheckBox(tr(self.language, "live_preview")); self.live_preview.setChecked(self.profile.live_preview_enabled)
        self.live_chunk = QDoubleSpinBox(); self.live_chunk.setRange(3.0, 12.0); self.live_chunk.setSingleStep(.5); self.live_chunk.setValue(self.profile.live_chunk_seconds); self.live_chunk.setSuffix(" s")
        self.noise = QCheckBox(tr(self.language, "noise_reduction")); self.noise.setChecked(self.profile.noise_reduction)
        self.normalize = QCheckBox(tr(self.language, "normalize_audio")); self.normalize.setChecked(self.profile.normalize_audio)
        self.auto_gain = QCheckBox(tr(self.language, "auto_microphone_gain")); self.auto_gain.setChecked(self.profile.auto_microphone_gain)
        self.microphone_gain = QDoubleSpinBox(); self.microphone_gain.setRange(.25, 8.0); self.microphone_gain.setSingleStep(.25); self.microphone_gain.setValue(self.profile.microphone_gain); self.microphone_gain.setSuffix("×")
        self.silence = QCheckBox(tr(self.language, "silence_stop")); self.silence.setChecked(self.profile.silence_stop_enabled)
        self.silence_seconds = QDoubleSpinBox(); self.silence_seconds.setRange(1, 30); self.silence_seconds.setValue(self.profile.silence_seconds); self.silence_seconds.setSuffix(" s")
        self.silence_threshold = QDoubleSpinBox(); self.silence_threshold.setDecimals(3); self.silence_threshold.setRange(.001, .25); self.silence_threshold.setSingleStep(.005); self.silence_threshold.setValue(self.profile.silence_threshold)
        self.max_duration = QSpinBox(); self.max_duration.setRange(0, 86_400); self.max_duration.setValue(self.profile.max_recording_seconds); self.max_duration.setSpecialValueText(tr(self.language, "unlimited")); self.max_duration.setSuffix(" s")
        self.sounds = QCheckBox(tr(self.language, "start_stop_sound")); self.sounds.setChecked(self.profile.start_stop_sound)
        form.addRow(tr(self.language, "model_quality"), self.model)
        form.addRow(tr(self.language, "local_model_path"), model_path_row)
        form.addRow(tr(self.language, "compute_device"), self.device)
        form.addRow(tr(self.language, "compute_type"), self.compute_type)
        form.addRow(tr(self.language, "recognition_mode"), self.recognition_mode)
        form.addRow(tr(self.language, "beam_size"), spin_control(self.beam))
        form.addRow("", self.live_transcription)
        form.addRow("", self.live_preview)
        form.addRow(tr(self.language, "live_chunk_seconds"), spin_control(self.live_chunk))
        live_hint = QLabel(tr(self.language, "live_transcription_hint")); live_hint.setObjectName("Muted"); live_hint.setWordWrap(True); form.addRow("", live_hint)
        form.addRow("", self.noise)
        form.addRow("", self.normalize)
        form.addRow("", self.auto_gain)
        auto_gain_hint = QLabel(tr(self.language, "auto_microphone_gain_hint")); auto_gain_hint.setObjectName("Muted"); auto_gain_hint.setWordWrap(True); form.addRow("", auto_gain_hint)
        form.addRow(tr(self.language, "microphone_gain"), spin_control(self.microphone_gain))
        form.addRow("", self.silence)
        form.addRow(tr(self.language, "silence_seconds"), spin_control(self.silence_seconds))
        form.addRow(tr(self.language, "level"), spin_control(self.silence_threshold))
        form.addRow(tr(self.language, "max_duration"), spin_control(self.max_duration))
        form.addRow("", self.sounds)
        hint = QLabel(tr(self.language, "max_duration_hint")); hint.setObjectName("Muted"); hint.setWordWrap(True); form.addRow("", hint)
        return page

    def _browse_profile_model(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, tr(self.language, "local_model_path"), self.local_model_path.text())
        if selected:
            self.local_model_path.setText(selected)

    def _privacy_page(self) -> QWidget:
        page, form = self._form_page()
        self.save_history = QCheckBox(tr(self.language, "save_history")); self.save_history.setChecked(self.profile.save_history)
        self.save_audio = QCheckBox(tr(self.language, "save_audio")); self.save_audio.setChecked(self.profile.save_audio)
        self.private = QCheckBox(tr(self.language, "private_mode")); self.private.setChecked(self.profile.private_mode)
        self.save_history.toggled.connect(self._update_profile_privacy_controls)
        self.private.toggled.connect(self._update_profile_privacy_controls)
        form.addRow("", self.save_history)
        form.addRow("", self.save_audio)
        form.addRow("", self.private)
        hint = QLabel(tr(self.language, "audio_requires_history")); hint.setObjectName("Muted"); hint.setWordWrap(True); form.addRow("", hint)
        self._update_profile_privacy_controls()
        return page

    def _update_profile_privacy_controls(self) -> None:
        private = self.private.isChecked()
        if private:
            self.save_history.setChecked(False)
            self.save_audio.setChecked(False)
        if not self.save_history.isChecked():
            self.save_audio.setChecked(False)
        self.save_history.setEnabled(not private)
        self.save_audio.setEnabled(not private and self.save_history.isChecked())

    def _accept(self) -> None:
        if not self.name.text().strip():
            return
        primary = normalize_hotkey(self.hotkey.text(), default="")
        secondary = normalize_hotkey(self.secondary_hotkey.text(), default="") if self.secondary_hotkey.text().strip() else ""
        if not primary or (secondary and primary == secondary):
            QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "invalid_hotkey" if not primary else "hotkey_conflict"))
            return
        p = self.profile
        p.name = self.name.text().strip()
        p.applications = normalize_app_list(self.apps.text())
        p.hotkey = primary
        p.secondary_hotkey = secondary
        p.recording_mode = str(self.mode.currentData())
        p.microphone_device = self.microphone.currentData()
        p.input_language = str(self.input.currentData())
        p.preferred_languages = normalize_language_list(self.preferred.text()) or ["de", "en", "fr"]
        p.prefer_primary_language = self.prefer_primary.isChecked()
        p.target_language = str(self.target.currentData())
        p.language_target_rules = normalize_language_target_rules(self.language_target_rules.text())
        p.translation_enabled = self.translation_enabled.isChecked()
        p.translation_intermediate_language = str(self.translation_bridge.currentData())
        p.language_detection_threshold = self.detection_threshold.value()
        p.show_original_and_translation = self.original_translation.isChecked()
        p.writing_style = str(self.style.currentData())
        p.output_mode = str(self.output.currentData())
        p.auto_press_enter = self.enter.isChecked()
        p.restore_clipboard_after_insert = self.restore_clipboard.isChecked()
        p.clipboard_clear_seconds = self.clipboard_clear.value()
        p.spoken_commands = self.commands.isChecked()
        p.remove_filler_words = self.fillers.isChecked()
        p.numbers_as_digits = self.numbers.isChecked()
        p.automatic_punctuation = self.automatic_punctuation.isChecked()
        p.model_size = str(self.model.currentData())
        p.local_model_path = self.local_model_path.text().strip()
        p.compute_device = str(self.device.currentData())
        p.compute_type = str(self.compute_type.currentData())
        p.recognition_mode = str(self.recognition_mode.currentData())
        p.beam_size = self.beam.value()
        p.live_transcription_enabled = self.live_transcription.isChecked()
        p.live_preview_enabled = self.live_preview.isChecked()
        p.live_chunk_seconds = self.live_chunk.value()
        p.noise_reduction = self.noise.isChecked()
        p.normalize_audio = self.normalize.isChecked()
        p.auto_microphone_gain = self.auto_gain.isChecked()
        p.microphone_gain = self.microphone_gain.value()
        p.silence_stop_enabled = self.silence.isChecked()
        p.silence_seconds = self.silence_seconds.value()
        p.silence_threshold = self.silence_threshold.value()
        p.max_recording_seconds = self.max_duration.value()
        p.start_stop_sound = self.sounds.isChecked()
        p.private_mode = self.private.isChecked()
        p.save_history = self.save_history.isChecked() and not p.private_mode
        p.save_audio = self.save_audio.isChecked() and p.save_history
        p.enabled = self.enabled.isChecked()
        self.accept()


class ProfilesDialog(QDialog):
    def __init__(self, database: LocalDatabase, store: SettingsStore, language: str, parent=None) -> None:
        super().__init__(parent)
        self.db = database
        self.store = store
        self.language = language
        self.setWindowTitle(tr(language, "profiles"))
        self.resize(820, 540)
        root = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr(language, "profile_name"), tr(language, "applications"), tr(language, "active_hotkey"), tr(language, "recording_mode"), tr(language, "enabled")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        root.addWidget(self.table, 1)
        bottom = QHBoxLayout()
        for text, handler in [(tr(language, "add"), self._add), (tr(language, "edit"), self._edit), (tr(language, "delete"), self._delete)]:
            button = QPushButton(text); button.clicked.connect(handler); bottom.addWidget(button)
        bottom.addStretch(1)
        root.addLayout(bottom)
        self.rows: list[Profile] = []
        self.reload()

    def reload(self) -> None:
        self.rows = self.db.list_profiles()
        self.table.setRowCount(len(self.rows))
        for r, profile in enumerate(self.rows):
            values = [profile.name, ", ".join(profile.applications), profile.hotkey.upper(), tr(self.language, "hold_mode" if profile.recording_mode == "hold" else "toggle_mode"), tr(self.language, "yes" if profile.enabled else "no")]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(value))

    def _current(self) -> Profile | None:
        rows = self.table.selectionModel().selectedRows()
        return self.rows[rows[0].row()] if rows else None

    def _has_conflict(self, candidate: Profile) -> bool:
        values = [self.store.current.hotkey, self.store.current.secondary_hotkey]
        for profile in self.rows:
            if not profile.enabled or profile.id == candidate.id:
                continue
            values.extend([profile.hotkey, profile.secondary_hotkey])
        values.extend([candidate.hotkey, candidate.secondary_hotkey])
        return bool(GlobalHotkeyService.conflicts([value for value in values if value]))

    def _add(self) -> None:
        dialog = ProfileEditDialog(self.language, parent=self)
        if dialog.exec():
            if dialog.profile.enabled and self._has_conflict(dialog.profile):
                QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "profile_hotkey_conflict"))
                return
            self.db.save_profile(dialog.profile)
            self.reload()

    def _edit(self) -> None:
        profile = self._current()
        if not profile:
            return
        dialog = ProfileEditDialog(self.language, profile, self)
        if dialog.exec():
            if dialog.profile.enabled and self._has_conflict(dialog.profile):
                QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "profile_hotkey_conflict"))
                return
            self.db.save_profile(dialog.profile)
            self.reload()

    def _delete(self) -> None:
        profile = self._current()
        if profile and profile.id is not None:
            self.db.delete_profile(profile.id)
            self.reload()


class InstallSignals(QObject):
    done = Signal(str)
    error = Signal(str)
    status = Signal(str)
    finished = Signal(object)


class TranslationInstallJob(QRunnable):
    def __init__(self, translator: LocalTranslator, source: str, target: str, intermediate: str) -> None:
        super().__init__()
        self.translator = translator
        self.source = source
        self.target = target
        self.intermediate = intermediate
        self.signals = InstallSignals()

    def run(self) -> None:
        try:
            self.translator.install_pair(self.source, self.target, self.signals.status.emit, self.intermediate)
            self.signals.done.emit("")
        except Exception as exc:
            self.signals.error.emit(str(exc)[:2000])
        finally:
            self.signals.finished.emit(self)


class WhisperInstallJob(QRunnable):
    def __init__(self, engine: WhisperEngine, model_size: str, device: str, compute_type: str, local_model_path: str) -> None:
        super().__init__()
        self.engine = engine
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.local_model_path = local_model_path
        self.signals = InstallSignals()

    def run(self) -> None:
        try:
            self.engine.ensure_model(self.model_size, self.device, self.compute_type, self.local_model_path, self.signals.status.emit)
            self.signals.done.emit(self.model_size)
        except Exception as exc:
            self.signals.error.emit(str(exc)[:2000])
        finally:
            self.signals.finished.emit(self)


class ModelManagerDialog(QDialog):
    def __init__(self, store: SettingsStore, translator: LocalTranslator, language: str, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.translator = translator
        self.whisper = WhisperEngine()
        self._active_jobs: set[QRunnable] = set()
        self.language = language
        self.setWindowTitle(tr(language, "model_manager"))
        self.resize(800, 570)
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)

        speech = QWidget()
        speech_form = QFormLayout(speech)
        self.speech_model = combo_with_items([("Tiny (~75 MB)", "tiny"), ("Base (~150 MB)", "base"), ("Small (~500 MB)", "small"), ("Medium (~1.5 GB)", "medium"), ("Large-v3 (~3 GB)", "large"), ("Turbo (~1.6 GB)", "turbo")], store.current.model_size)
        self.speech_model.currentIndexChanged.connect(self._speech_status)
        speech_form.addRow(tr(language, "model_quality"), self.speech_model)
        hint = QLabel(tr(language, "download_on_use") + "\n" + tr(language, "model_offline_required")); hint.setWordWrap(True); hint.setObjectName("Muted"); speech_form.addRow("", hint)
        self.speech_status = QLabel(); self.speech_status.setWordWrap(True); speech_form.addRow(tr(language, "installed"), self.speech_status)
        button_row = QHBoxLayout()
        self.speech_button = QPushButton(tr(language, "install")); self.speech_button.setObjectName("Primary"); self.speech_button.clicked.connect(self._select_model)
        self.remove_speech_button = QPushButton(tr(language, "remove_model")); self.remove_speech_button.clicked.connect(self._remove_model)
        button_row.addWidget(self.speech_button); button_row.addWidget(self.remove_speech_button); button_row.addStretch(1)
        self.speech_progress = QProgressBar(); self.speech_progress.setRange(0, 1); self.speech_progress.setValue(0)
        speech_form.addRow("", button_row); speech_form.addRow("", self.speech_progress)
        tabs.addTab(speech, tr(language, "whisper_models"))

        translation = QWidget()
        form = QFormLayout(translation)
        self.source = combo_with_items(speech_items(False, False, language), "en")
        self.target = combo_with_items(speech_items(False, False, language), "de")
        self.install_button = QPushButton(tr(language, "install_pair")); self.install_button.setObjectName("Primary"); self.install_button.clicked.connect(self._install)
        self.progress = QProgressBar(); self.progress.setRange(0, 1); self.progress.setValue(0)
        self.installed_label = QLabel(); self.installed_label.setWordWrap(True)
        form.addRow(tr(language, "source_language"), self.source)
        form.addRow(tr(language, "destination_language"), self.target)
        form.addRow("", self.install_button)
        form.addRow("", self.progress)
        form.addRow(tr(language, "installed"), self.installed_label)
        route = QLabel(tr(language, "translation_route_hint")); route.setWordWrap(True); route.setObjectName("Muted"); form.addRow("", route)
        tabs.addTab(translation, tr(language, "translation_models"))
        self._speech_status()
        self._reload_pairs()
        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.button(QDialogButtonBox.Close).setText(tr(language, "close")); close.rejected.connect(self.reject); root.addWidget(close)

    def _installation_finished(self, job: object) -> None:
        self._active_jobs.discard(job)  # type: ignore[arg-type]

    def _installation_running(self) -> bool:
        return bool(self._active_jobs)

    def _close_allowed(self) -> bool:
        if self._installation_running():
            QMessageBox.information(
                self,
                tr(self.language, "model_manager"),
                tr(self.language, "model_install_in_progress"),
            )
            return False
        settings = self.store.current
        if not self.whisper.is_model_available(settings.model_size, settings.local_model_path):
            answer = QMessageBox.question(
                self,
                tr(self.language, "speech_model"),
                tr(self.language, "model_required_close_warning"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            return answer == QMessageBox.Yes
        return True

    def reject(self) -> None:
        if self._close_allowed():
            super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._close_allowed():
            event.accept()
        else:
            event.ignore()

    def _speech_status(self) -> None:
        model_size = str(self.speech_model.currentData())
        installed = self.whisper.is_model_available(model_size, self.store.current.local_model_path)
        self.speech_status.setText(tr(self.language, "model_installed") if installed else tr(self.language, "not_installed"))
        self.remove_speech_button.setEnabled(installed and not bool(self.store.current.local_model_path))

    def _select_model(self) -> None:
        model_size = str(self.speech_model.currentData())
        self.speech_button.setEnabled(False); self.speech_progress.setRange(0, 0)
        settings = self.store.current
        job = WhisperInstallJob(self.whisper, model_size, settings.compute_device, settings.compute_type, settings.local_model_path)
        job.signals.done.connect(self._speech_installed)
        job.signals.error.connect(self._speech_failed)
        job.signals.finished.connect(self._installation_finished)
        self._active_jobs.add(job)
        QThreadPool.globalInstance().start(job)

    def _speech_installed(self, model_size: str) -> None:
        self.store.update(model_size=model_size)
        self.speech_progress.setRange(0, 1); self.speech_progress.setValue(1); self.speech_button.setEnabled(True)
        self._speech_status()
        QMessageBox.information(self, tr(self.language, "models"), tr(self.language, "model_installed"))

    def _speech_failed(self, message: str) -> None:
        self.speech_progress.setRange(0, 1); self.speech_progress.setValue(0); self.speech_button.setEnabled(True)
        QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "download_failed") + "\n" + message)

    def _remove_model(self) -> None:
        model_size = str(self.speech_model.currentData())
        self.whisper.remove_model(model_size)
        self._speech_status()
        QMessageBox.information(self, tr(self.language, "models"), tr(self.language, "model_removed"))

    def _reload_pairs(self) -> None:
        try:
            pairs = self.translator.installed_pairs()
            self.installed_label.setText("\n".join(f"{speech_language_name(self.language, p.source)} → {speech_language_name(self.language, p.target)}" for p in pairs) or tr(self.language, "not_installed"))
        except Exception:
            self.installed_label.setText(tr(self.language, "not_installed"))

    def _install(self) -> None:
        source = str(self.source.currentData()); target = str(self.target.currentData())
        if source == target:
            return
        self.install_button.setEnabled(False); self.progress.setRange(0, 0)
        job = TranslationInstallJob(self.translator, source, target, self.store.current.translation_intermediate_language)
        job.signals.done.connect(self._installed); job.signals.error.connect(self._failed)
        job.signals.finished.connect(self._installation_finished)
        self._active_jobs.add(job)
        QThreadPool.globalInstance().start(job)

    def _installed(self, _model: str = "") -> None:
        self.progress.setRange(0, 1); self.progress.setValue(1); self.install_button.setEnabled(True); self._reload_pairs()
        QMessageBox.information(self, tr(self.language, "install"), tr(self.language, "language_pair_installed"))

    def _failed(self, message: str) -> None:
        self.progress.setRange(0, 1); self.progress.setValue(0); self.install_button.setEnabled(True)
        if message.startswith("TRANSLATION_PACKAGE_UNAVAILABLE"):
            message = tr(self.language, "translation_package_unavailable")
        QMessageBox.warning(self, tr(self.language, "error"), tr(self.language, "download_failed") + "\n" + message)


class InfoDialog(QDialog):
    def __init__(self, title: str, body: str, parent=None, language: str | None = None) -> None:
        super().__init__(parent)
        self.language = language or str(getattr(parent, "language", "en"))
        self.setWindowTitle(title)
        self.resize(660, 450)
        layout = QVBoxLayout(self)
        text = QTextEdit(); text.setReadOnly(True); text.setMarkdown(body); layout.addWidget(text, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText(tr(self.language, "close"))
        buttons.rejected.connect(self.reject); layout.addWidget(buttons)
