from __future__ import annotations

import copy
import os
import platform
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from localvoice import __version__
from localvoice.core.audio import AudioRecorder
from localvoice.core.controller import AppController
from localvoice.core.database import LocalDatabase
from localvoice.core.hotkeys import GlobalHotkeyService
from localvoice.core.i18n import speech_language_name, tr
from localvoice.core.models import TranscriptionResult
from localvoice.core.paths import DATA_DIR
from localvoice.core.postprocess import count_words
from localvoice.core.security import SecureStore
from localvoice.core.settings import SettingsStore
from localvoice.core.system import is_wayland
from localvoice.core.transcription import WhisperEngine
from localvoice.core.translation import LocalTranslator
from localvoice.ui.dialogs import (
    HistoryDialog,
    InfoDialog,
    MicrophoneTestDialog,
    ModelManagerDialog,
    PreviewDialog,
    ProfilesDialog,
    SettingsDialog,
    StatisticsDialog,
    VocabularyDialog,
)
from localvoice.ui.overlay import RecordingOverlay
from localvoice.ui.theme import stylesheet


def _ui_resource(name: str) -> Path:
    """Return a packaged UI resource in source and PyInstaller builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    candidates = (
        base / "resources" / name,
        Path(__file__).resolve().parents[2] / "resources" / name,
    )
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


class MainWindow(QMainWindow):
    hotkey_backend_ready = Signal(str)
    hotkey_backend_error = Signal(str)

    def __init__(
        self,
        settings_store: SettingsStore,
        secure_store: SecureStore,
        database: LocalDatabase,
        controller: AppController,
        hotkeys: GlobalHotkeyService,
        icon: QIcon,
    ) -> None:
        super().__init__()
        self.store = settings_store
        self.secure_store = secure_store
        self.db = database
        self.controller = controller
        self.hotkeys = hotkeys
        self.icon = icon
        self.language = self.store.current.ui_language
        self._force_close = False
        self._hotkey_recovery_attempts = 0
        self.hotkey_backend_ready.connect(self._hotkey_backend_ready)
        self.hotkey_backend_error.connect(self._hotkey_backend_error)
        self.setWindowIcon(icon)
        self.resize(1380, 880)
        self.setMinimumSize(980, 680)
        self._build_ui()
        self._apply_ui_size()
        self.overlay = RecordingOverlay(self.store.current)
        self.overlay.stop_clicked.connect(self.controller.request_stop.emit)
        self.overlay.cancel_clicked.connect(self.controller.request_cancel.emit)
        self._connect_controller()
        self._configure_hotkeys()
        self._create_tray()
        self.refresh_texts()
        self.refresh_status_cards()

        self._retention_timer = QTimer(self)
        self._retention_timer.setInterval(6 * 60 * 60 * 1000)
        self._retention_timer.timeout.connect(self._apply_retention)
        self._retention_timer.start()

        self._health_timer = QTimer(self)
        self._health_timer.setInterval(4000)
        self._health_timer.timeout.connect(self._health_tick)
        self._health_timer.start()

        # Warm the verified local model after the UI is responsive so the first
        # dictation does not pay the complete model-loading delay.
        QTimer.singleShot(50, self.controller.preload_current_model)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(16, 18, 16, 18)
        side.setSpacing(6)

        brand = QFrame()
        brand.setObjectName("BrandCard")
        brand_row = QHBoxLayout(brand)
        brand_row.setContentsMargins(13, 12, 13, 12)
        self.brand_icon = QLabel()
        self.brand_icon.setObjectName("BrandMark")
        self.brand_icon.setAlignment(Qt.AlignCenter)
        self.brand_icon.setScaledContents(True)
        self.brand_icon.setPixmap(self.icon.pixmap(192, 192))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        self.brand_title = QLabel("LocalVoice")
        self.brand_title.setObjectName("AppTitle")
        self.brand_subtitle = QLabel()
        self.brand_subtitle.setObjectName("Subtitle")
        self.brand_subtitle.setWordWrap(True)
        brand_text.addWidget(self.brand_title)
        brand_text.addWidget(self.brand_subtitle)
        brand_row.addWidget(self.brand_icon)
        brand_row.addLayout(brand_text, 1)
        side.addWidget(brand)
        side.addSpacing(14)

        self.sidebar_buttons: dict[str, QPushButton] = {}
        navigation = [
            ("dashboard", "⌂", lambda: None),
            ("history", "◷", self.open_history),
            ("statistics", "▦", self.open_statistics),
            ("dictionary", "Aa", self.open_dictionary),
            ("profiles", "◇", self.open_profiles),
            ("models", "⬡", self.open_models),
            ("settings", "⚙", self.open_settings),
            ("privacy", "◉", self.open_privacy),
            ("help", "?", self.open_help),
            ("about", "i", self.open_about),
        ]
        for key, icon_text, handler in navigation:
            button = QPushButton()
            button.setObjectName("NavButton")
            button.setCheckable(key == "dashboard")
            button.setChecked(key == "dashboard")
            button.clicked.connect(lambda _checked=False, fn=handler: fn())
            button.setProperty("icon_text", icon_text)
            button.setCursor(Qt.PointingHandCursor)
            self.sidebar_buttons[key] = button
            side.addWidget(button)

        side.addStretch(1)
        self.local_badge = QLabel()
        self.local_badge.setObjectName("PrivacyBadge")
        self.local_badge.setWordWrap(True)
        side.addWidget(self.local_badge)
        outer.addWidget(self.sidebar)

        self.dashboard_scroll = QScrollArea()
        self.dashboard_scroll.setObjectName("DashboardScroll")
        self.dashboard_scroll.setWidgetResizable(True)
        self.dashboard_scroll.setFrameShape(QFrame.NoFrame)
        self.dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("DashboardContent")
        self.content_layout = main = QVBoxLayout(content)
        main.setContentsMargins(34, 28, 34, 34)
        main.setSpacing(20)
        self.dashboard_scroll.setWidget(content)
        outer.addWidget(self.dashboard_scroll, 1)

        top = QHBoxLayout()
        top.setSpacing(18)
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("Muted")
        self.page_subtitle.setWordWrap(True)
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)
        top.addLayout(title_box, 1)
        self.status_pill = QLabel()
        self.status_pill.setObjectName("StatusPill")
        top.addWidget(self.status_pill, 0, Qt.AlignTop)
        main.addLayout(top)

        # Hero / primary recording action
        self.hero = QFrame()
        self.hero.setObjectName("HeroCard")
        self.hero_layout = hero_layout = QHBoxLayout(self.hero)
        hero_layout.setContentsMargins(30, 28, 30, 28)
        hero_layout.setSpacing(24)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(9)
        self.hero_privacy = QLabel()
        self.hero_privacy.setObjectName("HeroBadge")
        self.hero_title = QLabel()
        self.hero_title.setObjectName("HeroTitle")
        self.hero_title.setWordWrap(True)
        self.hero_text = QLabel()
        self.hero_text.setObjectName("HeroText")
        self.hero_text.setWordWrap(True)
        self.hero_mode = QLabel()
        self.hero_mode.setObjectName("HeroMode")
        self.hero_mode.setWordWrap(True)
        hero_actions = QHBoxLayout()
        hero_actions.setSpacing(10)
        self.record_button = QPushButton()
        self.record_button.setObjectName("PrimaryLarge")
        self.record_button.setCursor(Qt.PointingHandCursor)
        self.record_button.clicked.connect(lambda _checked=False: self._request_record_action())
        self.install_model_button = QPushButton()
        self.install_model_button.setObjectName("HeroSecondary")
        self.install_model_button.setCursor(Qt.PointingHandCursor)
        self.install_model_button.clicked.connect(lambda _checked=False: self.open_models())
        hero_actions.addWidget(self.record_button)
        hero_actions.addWidget(self.install_model_button)
        hero_actions.addStretch(1)
        hero_text.addWidget(self.hero_privacy, 0, Qt.AlignLeft)
        hero_text.addWidget(self.hero_title)
        hero_text.addWidget(self.hero_text)
        hero_text.addWidget(self.hero_mode)
        hero_text.addStretch(1)
        hero_text.addLayout(hero_actions)
        hero_layout.addLayout(hero_text, 1)
        self.voice_icon = QIcon(str(_ui_resource("hero-logo.png")))
        self.mic_button = QPushButton()
        self.mic_button.setObjectName("VoiceOrb")
        self.mic_button.setIcon(self.voice_icon)
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.clicked.connect(lambda _checked=False: self._request_record_action())
        hero_layout.addWidget(self.mic_button, 0, Qt.AlignCenter)
        main.addWidget(self.hero)

        quick_header = QLabel()
        quick_header.setObjectName("SectionHeading")
        self.quick_header = quick_header
        main.addWidget(quick_header)
        self.quick_grid = QGridLayout()
        self.quick_grid.setHorizontalSpacing(12)
        self.quick_grid.setVerticalSpacing(12)
        self.quick_record = self._quick_button("●", self._request_record_action)
        self.quick_mic = self._quick_button("⌁", self.open_microphone_test)
        self.quick_models = self._quick_button("⬡", self.open_models)
        self.quick_settings = self._quick_button("⚙", self.open_settings)
        self.quick_check = self._quick_button("✓", self.open_system_check)
        self.quick_buttons = [self.quick_record, self.quick_mic, self.quick_models, self.quick_settings, self.quick_check]
        self._layout_quick_actions(3)
        main.addLayout(self.quick_grid)

        self.status_heading = QLabel()
        self.status_heading.setObjectName("SectionHeading")
        main.addWidget(self.status_heading)
        self.status_grid = QGridLayout()
        self.status_grid.setHorizontalSpacing(12)
        self.status_grid.setVerticalSpacing(12)
        self.mic_card, self.mic_status_title, self.mic_status_value, self.mic_status_detail = self._status_card("⌁")
        self.hotkey_card, self.hotkey_status_title, self.hotkey_status_value, self.hotkey_status_detail = self._status_card("⌨")
        self.model_card, self.model_status_title, self.model_status_value, self.model_status_detail = self._status_card("⬡")
        self.output_card, self.output_status_title, self.output_status_value, self.output_status_detail = self._status_card("→")
        self.status_cards = [self.mic_card, self.hotkey_card, self.model_card, self.output_card]
        self._layout_status_cards(2)
        main.addLayout(self.status_grid)

        last = QFrame()
        last.setObjectName("TranscriptCard")
        last_layout = QVBoxLayout(last)
        last_layout.setContentsMargins(22, 19, 22, 20)
        header = QHBoxLayout()
        self.last_title = QLabel()
        self.last_title.setObjectName("CardTitle")
        self.last_meta = QLabel()
        self.last_meta.setObjectName("Muted")
        header.addWidget(self.last_title)
        header.addStretch(1)
        header.addWidget(self.last_meta)
        last_layout.addLayout(header)
        self.last_text = QLabel("—")
        self.last_text.setWordWrap(True)
        self.last_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.last_text.setObjectName("LastText")
        self.last_text.setMinimumHeight(110)
        last_layout.addWidget(self.last_text, 1)
        actions = QHBoxLayout()
        self.copy_last = QPushButton()
        self.copy_last.clicked.connect(lambda _checked=False: self._copy_last())
        self.open_history_button = QPushButton()
        self.open_history_button.clicked.connect(lambda _checked=False: self.open_history())
        actions.addWidget(self.copy_last)
        actions.addWidget(self.open_history_button)
        actions.addStretch(1)
        last_layout.addLayout(actions)
        main.addWidget(last)
        main.addStretch(1)

    @staticmethod
    def _clear_grid(layout: QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _layout_quick_actions(self, columns: int) -> None:
        if not hasattr(self, "quick_grid") or not hasattr(self, "quick_buttons"):
            return
        columns = max(1, int(columns))
        if getattr(self, "_quick_columns", None) == columns:
            return
        self._quick_columns = columns
        self._clear_grid(self.quick_grid)
        for index, button in enumerate(self.quick_buttons):
            self.quick_grid.addWidget(button, index // columns, index % columns)
        for column in range(columns):
            self.quick_grid.setColumnStretch(column, 1)

    def _layout_status_cards(self, columns: int) -> None:
        if not hasattr(self, "status_grid") or not hasattr(self, "status_cards"):
            return
        columns = max(1, int(columns))
        if getattr(self, "_status_columns", None) == columns:
            return
        self._status_columns = columns
        self._clear_grid(self.status_grid)
        for index, card in enumerate(self.status_cards):
            self.status_grid.addWidget(card, index // columns, index % columns)
        for column in range(columns):
            self.status_grid.setColumnStretch(column, 1)

    def _quick_button(self, icon_text: str, handler) -> QPushButton:
        button = QPushButton()
        button.setObjectName("QuickAction")
        button.setProperty("icon_text", icon_text)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda _checked=False, fn=handler: fn())
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return button

    def _status_card(self, icon_text: str) -> tuple[QFrame, QLabel, QLabel, QLabel]:
        card = QFrame()
        card.setObjectName("StatusCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 17, 18, 17)
        layout.setSpacing(14)
        icon = QLabel(icon_text)
        icon.setObjectName("StatusIcon")
        icon.setAlignment(Qt.AlignCenter)
        text = QVBoxLayout()
        text.setSpacing(3)
        title = QLabel()
        title.setObjectName("StatusTitle")
        value = QLabel()
        value.setObjectName("StatusValue")
        value.setWordWrap(True)
        detail = QLabel()
        detail.setObjectName("StatusDetail")
        detail.setWordWrap(True)
        text.addWidget(title)
        text.addWidget(value)
        text.addWidget(detail)
        layout.addWidget(icon)
        layout.addLayout(text, 1)
        return card, title, value, detail

    def _apply_ui_size(self) -> None:
        mode = self.store.current.ui_size
        dimensions = {
            "small": (285, 42, 28),
            # Medium is exactly the former Large layout requested by the user.
            "medium": (400, 66, 42),
            # Large is a new additional step above that size.
            "large": (455, 76, 50),
        }
        sidebar_width, margin, spacing = dimensions.get(mode, dimensions["medium"])
        self.sidebar.setFixedWidth(sidebar_width)
        self.content_layout.setContentsMargins(margin, max(24, margin - 8), margin, margin)
        self.content_layout.setSpacing(spacing)
        hero_margin = max(26, margin - 6)
        self.hero_layout.setContentsMargins(hero_margin, hero_margin - 2, hero_margin, hero_margin - 2)
        minimums = {"small": (1120, 740), "medium": (1420, 900), "large": (1540, 950)}
        self.setMinimumSize(*minimums.get(mode, minimums["medium"]))
        brand_sizes = {"small": 54, "medium": 76, "large": 88}
        brand_size = brand_sizes.get(mode, brand_sizes["medium"])
        self.brand_icon.setFixedSize(brand_size, brand_size)
        self.brand_icon.setPixmap(self.icon.pixmap(brand_size * 3, brand_size * 3))
        orb_icon_sizes = {"small": 118, "medium": 176, "large": 204}
        orb_icon_size = orb_icon_sizes.get(mode, orb_icon_sizes["medium"])
        self.mic_button.setIconSize(QSize(orb_icon_size, orb_icon_size))

    # -------------------------------------------------------------- controllers
    def _request_record_action(self) -> None:
        """Start/stop from the visible UI with a clear model prerequisite."""
        settings = self.store.current
        if not self.controller.recorder.is_recording and not WhisperEngine().is_model_available(
            settings.model_size, settings.local_model_path
        ):
            answer = QMessageBox.question(
                self,
                tr(self.language, "speech_model"),
                tr(self.language, "model_missing") + "\n\n" + tr(self.language, "open_model_manager_question"),
            )
            if answer == QMessageBox.Yes:
                self.open_models()
            return
        self.controller.request_toggle.emit()

    def _connect_controller(self) -> None:
        self.controller.recording_started.connect(self._recording_started)
        self.controller.recording_stopped.connect(self._recording_stopped)
        self.controller.level_changed.connect(self.overlay.set_level)
        self.controller.state_changed.connect(self._state_changed)
        self.controller.partial_text_changed.connect(self.overlay.set_partial_text)
        self.controller.model_status_changed.connect(lambda _status: self.refresh_status_cards())
        self.controller.result_ready.connect(self._result_ready)
        self.controller.preview_requested.connect(self._preview)
        self.controller.error_occurred.connect(self._error)

    def _configure_hotkeys(self) -> None:
        self.hotkeys.stop()
        settings = self.store.current
        additional: list[tuple[str, str]] = []
        for profile in self.db.list_profiles():
            if not profile.enabled:
                continue
            additional.append((profile.hotkey, profile.recording_mode))
            if profile.secondary_hotkey:
                additional.append((profile.secondary_hotkey, profile.recording_mode))
        self.hotkeys.configure(
            settings.hotkey,
            settings.recording_mode,
            settings.hotkey_enabled,
            settings.secondary_hotkey,
            additional,
            settings.suppress_hotkey_keystroke,
        )
        self.hotkeys.on_start = self.controller.request_start_hotkey.emit
        self.hotkeys.on_stop = self.controller.request_stop_hotkey.emit
        self.hotkeys.on_toggle = self.controller.request_toggle_hotkey.emit
        self.hotkeys.on_backend_ready = self.hotkey_backend_ready.emit
        self.hotkeys.on_backend_error = self.hotkey_backend_error.emit
        try:
            self.hotkeys.start()
            self._hotkey_recovery_attempts = 0
        except Exception as exc:
            self.statusBar().showMessage(str(exc), 10000)
        self.refresh_status_cards()

    def _health_tick(self) -> None:
        settings = self.store.current
        if settings.hotkey_enabled and not self.hotkeys.is_running and self._hotkey_recovery_attempts < 2:
            self._hotkey_recovery_attempts += 1
            try:
                self._configure_hotkeys()
            except Exception:
                pass
        self.refresh_status_cards()

    # ---------------------------------------------------------------- tray/texts
    def _create_tray(self) -> None:
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.activated.connect(self._tray_activated)
        self.tray_menu = QMenu()
        self.tray_show = QAction(self)
        self.tray_show.triggered.connect(lambda _checked=False: self._show_window())
        self.tray_record = QAction(self)
        self.tray_record.triggered.connect(lambda _checked=False: self._request_record_action())
        self.tray_settings = QAction(self)
        self.tray_settings.triggered.connect(lambda _checked=False: self.open_settings())
        self.tray_exit = QAction(self)
        self.tray_exit.triggered.connect(lambda _checked=False: self._exit())
        self.tray_menu.addAction(self.tray_show)
        self.tray_menu.addAction(self.tray_record)
        self.tray_menu.addAction(self.tray_settings)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.tray_exit)
        self.tray.setContextMenu(self.tray_menu)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def refresh_texts(self) -> None:
        self.language = self.store.current.ui_language
        language = self.language
        settings = self.store.current
        self.setWindowTitle("LocalVoice")
        self.brand_subtitle.setText(tr(language, "app_subtitle"))
        self.page_title.setText(tr(language, "dashboard"))
        self.page_subtitle.setText(tr(language, "dashboard_intro"))
        self.hero_privacy.setText(tr(language, "privacy_badge"))
        self.hero_title.setText(tr(language, "dashboard_greeting"))
        self.hero_text.setText(tr(language, "local_only"))
        self.hero_mode.setText(tr(language, "help_hold" if settings.recording_mode == "hold" else "help_toggle"))
        self.record_button.setText("●  " + tr(language, "record_button"))
        self.install_model_button.setText(tr(language, "install_model_now"))
        self.quick_header.setText(tr(language, "quick_actions"))
        quick_labels = [
            (self.quick_record, "●", "record_button"),
            (self.quick_mic, "⌁", "quick_microphone_test"),
            (self.quick_models, "⬡", "quick_models"),
            (self.quick_settings, "⚙", "quick_settings"),
            (self.quick_check, "✓", "system_check"),
        ]
        for button, icon, key in quick_labels:
            button.setText(f"{icon}\n{tr(language, key)}")
        self.status_heading.setText(tr(language, "device_status"))
        self.last_title.setText(tr(language, "last_transcription"))
        self.copy_last.setText(tr(language, "copy"))
        self.open_history_button.setText(tr(language, "history"))
        self.local_badge.setText("🔒  " + tr(language, "privacy_badge"))
        for key, button in self.sidebar_buttons.items():
            button.setText(f"{button.property('icon_text')}    {tr(language, key)}")
        self.tray_show.setText(tr(language, "dashboard"))
        self.tray_record.setText(tr(language, "record_now"))
        self.tray_settings.setText(tr(language, "settings"))
        self.tray_exit.setText(tr(language, "close"))
        self.status_pill.setText("●  " + tr(language, "ready"))
        self.refresh_status_cards()

    def refresh_status_cards(self) -> None:
        if not hasattr(self, "mic_status_title"):
            return
        settings = self.store.current
        language = self.language
        devices = AudioRecorder.input_devices()
        selected = next((item for item in devices if item["index"] == settings.microphone_device), None)
        if settings.microphone_device is None:
            selected = devices[0] if devices else None
        self.mic_status_title.setText(tr(language, "microphone"))
        self.mic_status_value.setText(tr(language, "microphone_ready") if selected else tr(language, "microphone_missing"))
        self.mic_status_detail.setText(str(selected["name"]) if selected else tr(language, "status_attention"))
        self.mic_card.setProperty("status", "ok" if selected else "warning")

        self.hotkey_status_title.setText(tr(language, "hotkey_status"))
        if not settings.hotkey_enabled:
            self.hotkey_status_value.setText(tr(language, "disabled"))
            self.hotkey_status_detail.setText("")
            hotkey_state = "neutral"
        elif self.hotkeys.is_running:
            self.hotkey_status_value.setText(tr(language, "hotkey_active", hotkey=settings.hotkey.upper()))
            self.hotkey_status_detail.setText(tr(language, "hotkey_backend", backend=self.hotkeys.backend_name))
            hotkey_state = "ok"
        else:
            self.hotkey_status_value.setText(tr(language, "hotkey_unavailable"))
            self.hotkey_status_detail.setText(settings.hotkey.upper())
            hotkey_state = "warning"
        self.hotkey_card.setProperty("status", hotkey_state)

        available = WhisperEngine().is_model_available(settings.model_size, settings.local_model_path)
        loaded = self.controller.whisper.is_loaded_for(
            settings.model_size, settings.compute_device, settings.compute_type, settings.local_model_path
        )
        model_runtime = self.controller.whisper.loaded_status()
        self.model_status_title.setText(tr(language, "speech_model"))
        self.model_status_value.setText(tr(language, "model_ready") if available else tr(language, "model_required"))
        if loaded:
            detail = f"{settings.model_size.upper()} · {tr(language, 'model_loaded_memory')} · {str(model_runtime.get('device', '')).upper()}"
        elif available:
            detail = f"{settings.model_size.upper()} · {tr(language, 'model_installed_disk')}"
        else:
            detail = settings.model_size.upper()
        self.model_status_detail.setText(detail)
        self.model_card.setProperty("status", "ok" if available else "warning")
        self.install_model_button.setVisible(not available)

        self.output_status_title.setText(tr(language, "output_mode"))
        output_key = {
            "insert": "insert_active_app",
            "clipboard": "clipboard_only",
            "preview": "preview_first",
            "app": "localvoice_only",
        }.get(settings.output_mode, "insert_active_app")
        input_name = speech_language_name(language, settings.input_language)
        target_name = speech_language_name(language, settings.target_language)
        self.output_status_value.setText(tr(language, output_key))
        self.output_status_detail.setText(f"{input_name} → {target_name}")
        self.output_card.setProperty("status", "ok")

        # Dynamic properties require an explicit style refresh.
        for card in (self.mic_card, self.hotkey_card, self.model_card, self.output_card):
            card.style().unpolish(card)
            card.style().polish(card)

    # ------------------------------------------------------------- state/results
    def _recording_started(self) -> None:
        active = self.controller.active_settings
        if active.start_stop_sound:
            QApplication.beep()
        self.overlay.start_recording(active, self.controller.target_context)
        self.overlay.set_partial_text("")
        self.status_pill.setText("●  " + tr(self.language, "recording_running"))
        self.mic_button.setIcon(QIcon())
        self.mic_button.setText("■")
        self.record_button.setText("■  " + tr(self.language, "stop_recording_button"))
        self.quick_record.setText("■\n" + tr(self.language, "stop_recording_button"))

    def _recording_stopped(self) -> None:
        if self.controller.active_settings.start_stop_sound:
            QApplication.beep()
        self.status_pill.setText("◉  " + tr(self.language, "processing"))
        self.mic_button.setText("")
        self.mic_button.setIcon(self.voice_icon)
        self.record_button.setText("●  " + tr(self.language, "record_button"))
        self.quick_record.setText("●\n" + tr(self.language, "record_button"))

    def _state_changed(self, state: str) -> None:
        if state in {"live_listening", "live_behind"}:
            if self.controller.is_recording:
                self.overlay.set_state(state)
                self.status_pill.setText("●  " + tr(self.language, state))
            return
        if state.startswith("language:"):
            code = state.split(":", 1)[1]
            name = speech_language_name(self.language, code)
            self.overlay.set_detected_language(name)
            self.status_pill.setText("●  " + tr(self.language, "detected_language") + ": " + name)
            return
        self.overlay.set_state(state)
        key = {
            "recording": "recording_running",
            "processing": "processing",
            "loading_model": "status_model_loading",
            "translating": "translating",
            "inserted": "inserted",
            "copied": "copied",
            "cancelled": "cancelled",
            "error": "error",
            "ready": "ready",
            "model_missing": "status_attention",
        }.get(state, "ready")
        self.status_pill.setText("●  " + tr(self.language, key))

    def _result_ready(self, result: TranscriptionResult) -> None:
        self.last_text.setText(result.final_text)
        language_name = speech_language_name(self.language, result.detected_language)
        path_label = tr(self.language, "streaming_result" if result.streaming_used else "full_pass_result")
        ready_label = tr(self.language, "processing_time", seconds=result.processing_seconds)
        device = result.model_device.upper() if result.model_device else ""
        device_part = f" · {device}" if device else ""
        self.last_meta.setText(
            f"{language_name} · {result.word_count} {tr(self.language, 'words')} · "
            f"{result.duration_seconds:.1f}s · {ready_label} · {path_label}{device_part}"
        )
        if result.phase_timings:
            timing_text = " · ".join(
                f"{key}: {value:.2f}s" for key, value in result.phase_timings.items()
            )
            self.last_meta.setToolTip(timing_text)

    def _preview(self, result: TranscriptionResult) -> None:
        dialog = PreviewDialog(result, self.language, self)
        if dialog.exec() and dialog.text:
            result.final_text = dialog.text
            result.word_count = count_words(result.final_text)
            pending = copy.deepcopy(self.controller.active_settings)
            pending.output_mode = "insert" if pending.output_mode == "preview" else pending.output_mode
            self.controller.commit_result(result, pending)
        else:
            self.controller.discard_result(result)
            self._state_changed("cancelled")

    def _error(self, message: str) -> None:
        if message.startswith("MICROPHONE:"):
            text = tr(self.language, "microphone_error") + "\n" + message.split(":", 1)[1]
        elif message == "TOO_SHORT":
            text = tr(self.language, "recording_too_short")
        elif message == "NO_SPEECH":
            text = tr(self.language, "status_no_speech")
        elif message.startswith("AUDIO_WRITE:"):
            text = tr(self.language, "audio_write_error") + "\n" + message.split(":", 1)[1]
        elif message.startswith("MODEL_MISSING:"):
            text = tr(self.language, "model_missing") + "\n" + tr(self.language, "model_offline_required")
        elif message.startswith("TRANSLATION_PACKAGE_UNAVAILABLE:"):
            text = tr(self.language, "translation_package_unavailable")
        elif message.startswith("TRANSLATION_MODEL_MISSING:") or "No local translation route" in message:
            text = tr(self.language, "translation_model_missing")
        else:
            text = message
        if message.startswith(("MODEL_MISSING:", "TRANSLATION_MODEL_MISSING:", "TRANSLATION_PACKAGE_UNAVAILABLE:")):
            answer = QMessageBox.question(
                self,
                tr(self.language, "error"),
                text + "\n\n" + tr(self.language, "open_model_manager_question"),
            )
            if answer == QMessageBox.Yes:
                self.open_models()
            return
        QMessageBox.warning(self, tr(self.language, "error"), text)

    def _copy_last(self) -> None:
        text = self.last_text.text()
        if text and text != "—":
            QApplication.clipboard().setText(text)
            self._state_changed("copied")

    # ---------------------------------------------------------------- dialogs
    def open_microphone_test(self) -> None:
        settings = self.store.current
        dialog = MicrophoneTestDialog(settings.microphone_device, self.language, self)
        dialog.exec()
        self.refresh_status_cards()

    def open_system_check(self) -> None:
        settings = self.store.current
        checks: list[tuple[str, bool, str]] = []
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            writable = os.access(DATA_DIR, os.W_OK)
        except OSError:
            writable = False
        checks.append((tr(self.language, "check_data_folder"), writable, str(DATA_DIR)))
        model_ok = WhisperEngine().is_model_available(settings.model_size, settings.local_model_path)
        checks.append((tr(self.language, "check_model"), model_ok, settings.model_size.upper()))
        microphones = AudioRecorder.input_devices()
        checks.append((tr(self.language, "check_microphone"), bool(microphones), str(len(microphones))))
        hotkey_ok = (not settings.hotkey_enabled) or self.hotkeys.is_running
        checks.append((tr(self.language, "check_hotkey"), hotkey_ok, self.hotkeys.backend_name))
        try:
            free = shutil.disk_usage(DATA_DIR).free
        except OSError:
            free = 0
        disk_ok = free >= AudioRecorder.MIN_FREE_DISK_BYTES
        checks.append((tr(self.language, "check_disk"), disk_ok, f"{free / (1024 ** 3):.1f} GB"))
        lines = [f"# {tr(self.language, 'system_check_title')}", ""]
        for label, ok, detail in checks:
            lines.append(f"{'✅' if ok else '⚠️'} **{label}** — {detail}")
        lines.extend(["", tr(self.language, "system_check_ok" if all(item[1] for item in checks) else "system_check_issue")])
        InfoDialog(tr(self.language, "system_check"), "\n\n".join(lines), self, self.language).exec()

    def open_settings(self) -> None:
        self.hotkeys.stop()
        try:
            dialog = SettingsDialog(self.store, self.secure_store, self.db, self)
            dialog.applied.connect(self._settings_applied)
            dialog.exec()
        finally:
            self._configure_hotkeys()

    def _apply_retention(self) -> None:
        settings = self.store.current
        self.db.purge_history(settings.history_retention_days)
        self.db.prune_history(settings.max_history_items)
        self.db.purge_saved_audio(settings.audio_retention_days)

    def _settings_applied(self) -> None:
        QApplication.instance().setStyleSheet(stylesheet(self.store.current.theme, self.store.current.ui_size))
        self._apply_ui_size()
        self.controller.refresh_settings()
        self._configure_hotkeys()
        self.overlay.settings = self.store.current
        self._apply_retention()
        self.refresh_texts()
        QTimer.singleShot(250, self.controller.preload_current_model)

    def open_history(self) -> None:
        HistoryDialog(self.db, self.language, self).exec()

    def open_statistics(self) -> None:
        StatisticsDialog(self.db, self.language, self).exec()

    def open_dictionary(self) -> None:
        VocabularyDialog(self.db, self.language, self).exec()

    def open_profiles(self) -> None:
        self.hotkeys.stop()
        try:
            ProfilesDialog(self.db, self.store, self.language, self).exec()
        finally:
            self._configure_hotkeys()

    def open_models(self) -> None:
        ModelManagerDialog(self.store, LocalTranslator(), self.language, self).exec()
        self.controller.refresh_settings()
        self.refresh_status_cards()
        QTimer.singleShot(150, self.controller.preload_current_model)

    def open_privacy(self) -> None:
        body = (
            f"# {tr(self.language, 'privacy')}\n\n"
            f"- {tr(self.language, 'local_only')}\n"
            f"- {tr(self.language, 'no_api')}\n"
            f"- {tr(self.language, 'save_history')}\n"
            f"- {tr(self.language, 'private_mode')}\n"
            f"- {tr(self.language, 'pin_protection')}"
        )
        InfoDialog(tr(self.language, "privacy"), body, self, self.language).exec()

    def open_help(self) -> None:
        body = (
            f"# LocalVoice\n\n{tr(self.language, 'help_hold')}\n\n"
            f"{tr(self.language, 'help_toggle')}\n\n{tr(self.language, 'help_commands')}\n\n"
            f"**Linux:** {tr(self.language, 'wayland_warning')}\n\n"
            f"{tr(self.language, 'wayland_shortcut_command')}"
        )
        InfoDialog(tr(self.language, "help"), body, self, self.language).exec()

    def open_about(self) -> None:
        body = (
            f"# LocalVoice {__version__}\n\n{tr(self.language, 'about_text')}\n\n"
            f"**{tr(self.language, 'license')}**\n\nWindows · Linux · {platform.machine()}"
        )
        InfoDialog(tr(self.language, "about"), body, self, self.language).exec()

    # --------------------------------------------------------------- platform
    def _hotkey_backend_ready(self, backend: str) -> None:
        if backend == "xdg-portal":
            self.statusBar().showMessage(tr(self.language, "wayland_portal_active"), 8000)
        self.refresh_status_cards()

    def _hotkey_backend_error(self, message: str) -> None:
        self.refresh_status_cards()
        if is_wayland():
            text = (
                tr(self.language, "wayland_portal_failed")
                + "\n\n"
                + str(message)[:700]
                + "\n\n"
                + tr(self.language, "wayland_shortcut_command")
            )
            self.statusBar().showMessage(tr(self.language, "wayland_portal_failed"), 15000)
            QMessageBox.warning(self, "Linux Wayland", text)

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick}:
            self._show_window()

    def _show_window(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _exit(self) -> None:
        self._force_close = True
        self.hotkeys.stop()
        self.controller.shutdown()
        self.tray.hide()
        QApplication.quit()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        available = max(0, self.width() - (self.sidebar.width() if hasattr(self, "sidebar") else 0))
        self._layout_quick_actions(5 if available >= 1320 else 3 if available >= 760 else 2)
        self._layout_status_cards(4 if available >= 1380 else 2 if available >= 720 else 1)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if (
            event.type() == QEvent.WindowStateChange
            and self.isMinimized()
            and self.store.current.minimize_to_tray
            and hasattr(self, "tray")
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            QTimer.singleShot(0, self.hide)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.store.current.close_to_tray and not self._force_close:
            event.ignore()
            self.hide()
        else:
            self.hotkeys.stop()
            self.controller.shutdown()
            event.accept()
