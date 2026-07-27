from __future__ import annotations

from PySide6.QtCore import QPoint, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from localvoice.core.i18n import tr
from localvoice.core.models import AppSettings
from localvoice.core.system import ActiveWindowContext


class WaveBars(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(130, 34)
        self._level = 0.0
        self._phase = 0
        self._color = QColor("#FF4D67")

    def set_level(self, value: float) -> None:
        self._level = max(0.0, min(1.0, float(value)))
        self._phase = (self._phase + 1) % 12
        self.update()

    def set_color(self, value: str) -> None:
        self._color = QColor(value)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        count = 13
        width = max(4.0, self.width() / (count * 1.8))
        gap = width * 0.8
        center = self.height() / 2
        for index in range(count):
            distance = abs(index - count // 2) / max(1, count // 2)
            pulse = (1.0 - distance * 0.55) * (0.3 + self._level * 0.7)
            variation = 0.75 + 0.25 * ((index + self._phase) % 3)
            height = max(4.0, (self.height() - 6) * pulse * variation)
            x = index * (width + gap)
            painter.drawRoundedRect(x, center - height / 2, width, height, width / 2, width / 2)


class RecordingOverlay(QWidget):
    stop_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, settings: AppSettings) -> None:
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
        super().__init__(None, flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.settings = settings
        self._elapsed = 0
        self._state = "ready"
        self._language = settings.ui_language
        self._display_generation = 0
        self._target_context = ActiveWindowContext()
        self._pulse_growing = True
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(350)
        self._pulse_timer.timeout.connect(self._pulse)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build()
        self.resize(420, 132)

    def _build(self) -> None:
        self.setStyleSheet(
            """
            QWidget#OverlayCard { background: rgba(17,24,39,246); border: 1px solid #34425F; border-radius: 18px; }
            QLabel { color: #F8FAFC; font-family: 'Segoe UI'; }
            QLabel#OverlayState { font-size: 15px; font-weight: 750; }
            QLabel#OverlayTime { color: #B6C2D8; font-size: 13px; }
            QLabel#OverlayPartial { color: #E8EEFF; font-size: 13px; background: rgba(38,52,79,150); border-radius: 8px; padding: 7px 9px; }
            QPushButton { background: #26344F; color: white; border: none; border-radius: 9px; padding: 7px 10px; }
            QPushButton:hover { background: #354766; }
            QFrame#RecordingBar { background: #FF4D67; border-radius: 2px; min-height: 4px; max-height: 4px; }
            """
        )
        card = QWidget(self)
        card.setObjectName("OverlayCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(card)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 13, 12)
        self.recording_bar = QFrame()
        self.recording_bar.setObjectName("RecordingBar")
        card_layout.addWidget(self.recording_bar)

        outer = QHBoxLayout()
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color:#FF4D67;font-size:25px;")
        outer.addWidget(self.dot)

        center = QVBoxLayout()
        top = QHBoxLayout()
        self.state_label = QLabel(tr(self._language, "recording_running"))
        self.state_label.setObjectName("OverlayState")
        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("OverlayTime")
        top.addWidget(self.state_label)
        top.addStretch(1)
        top.addWidget(self.time_label)
        center.addLayout(top)
        self.language_label = QLabel("")
        self.language_label.setObjectName("OverlayTime")
        self.language_label.hide()
        center.addWidget(self.language_label)
        self.partial_label = QLabel("")
        self.partial_label.setObjectName("OverlayPartial")
        self.partial_label.setWordWrap(True)
        self.partial_label.setMaximumHeight(58)
        self.partial_label.hide()
        center.addWidget(self.partial_label)
        self.wave = WaveBars()
        center.addWidget(self.wave)
        outer.addLayout(center, 1)

        buttons = QVBoxLayout()
        self.stop_button = QPushButton("■")
        self.cancel_button = QPushButton("×")
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.cancel_button)
        outer.addLayout(buttons)
        card_layout.addLayout(outer)

    def start_recording(self, settings: AppSettings, context: ActiveWindowContext | None = None) -> None:
        self._display_generation += 1
        self.settings = settings
        self._target_context = context or ActiveWindowContext()
        self._language = settings.ui_language
        self._elapsed = 0
        self._state = "recording"
        self.dot.setText("●")
        self.dot.setStyleSheet("color:#FF4D67;font-size:25px;")
        self.recording_bar.setStyleSheet("background:#FF4D67;border-radius:2px;min-height:4px;max-height:4px;")
        self.recording_bar.show()
        self.wave.set_color("#FF4D67")
        self.state_label.setText(tr(self._language, "recording_running"))
        self.time_label.setText("00:00")
        self.stop_button.setToolTip(tr(self._language, "stop"))
        self.cancel_button.setToolTip(tr(self._language, "cancel"))
        self.stop_button.show()
        self.cancel_button.show()
        self.language_label.clear()
        self.language_label.hide()
        self.partial_label.clear()
        self.partial_label.hide()
        scale = max(0.7, min(1.8, settings.overlay_scale))
        self.resize(int(420 * scale), int(132 * scale))
        self._timer.start(1000)
        self._pulse_timer.start()
        self._place()
        self.show()
        self.raise_()

    def set_detected_language(self, language_name: str) -> None:
        self.language_label.setText(f"{tr(self._language, 'detected_language')}: {language_name}")
        self.language_label.show()
        self._place()

    def set_partial_text(self, text: str) -> None:
        value = str(text or "").strip()
        if not value:
            self.partial_label.clear()
            self.partial_label.hide()
            self._place()
            return
        # Keep the newest part visible and bounded; the final result remains in
        # the main window/history. This avoids an ever-growing floating window.
        self.partial_label.setText(("…" if len(value) > 220 else "") + value[-220:])
        self.partial_label.show()
        scale = max(0.7, min(1.8, self.settings.overlay_scale))
        self.resize(int(460 * scale), int(190 * scale))
        self._place()

    def set_state(self, state: str) -> None:
        if state in {"live_listening", "live_behind"}:
            self._state = "recording"
            self.state_label.setText(tr(self._language, state))
            self.stop_button.show()
            self.cancel_button.show()
            return
        self._state = state
        mapping = {
            "processing": ("◉", "#F7B955", "processing"),
            "loading_model": ("◉", "#F7B955", "status_model_loading"),
            "translating": ("◆", "#5B8CFF", "translating"),
            "inserted": ("✓", "#2DD4A7", "inserted"),
            "copied": ("✓", "#2DD4A7", "copied"),
            "cancelled": ("×", "#9EABC2", "cancelled"),
            "error": ("!", "#FF4D67", "error"),
            "ready": ("✓", "#2DD4A7", "ready"),
        }
        if state == "recording":
            return
        icon, color, key = mapping.get(state, ("◉", "#9EABC2", "ready"))
        self.dot.setText(icon)
        self.dot.setStyleSheet(f"color:{color};font-size:23px;font-weight:800;")
        self.recording_bar.setStyleSheet(f"background:{color};border-radius:2px;min-height:4px;max-height:4px;")
        self.wave.set_color(color)
        self.state_label.setText(tr(self._language, key))
        self.stop_button.hide()
        self.cancel_button.hide()
        self.wave.set_level(0.15)
        self._timer.stop()
        self._pulse_timer.stop()
        if not self.settings.overlay_show_processing and state in {"processing", "loading_model", "translating"}:
            self.hide()
            return
        if state in {"inserted", "copied", "cancelled", "ready", "error"}:
            generation = self._display_generation
            QTimer.singleShot(1800, lambda: self._hide_if_current(generation))

    def _hide_if_current(self, generation: int) -> None:
        if generation == self._display_generation and self._state != "recording":
            self.hide()

    def set_level(self, value: float) -> None:
        self.wave.set_level(value)

    def _tick(self) -> None:
        self._elapsed += 1
        hours, remainder = divmod(self._elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}")

    def _pulse(self) -> None:
        if self._state != "recording":
            return
        size = 29 if self._pulse_growing else 23
        opacity = "FF" if self._pulse_growing else "B8"
        self.dot.setStyleSheet(f"color:#FF4D67{opacity};font-size:{size}px;font-weight:800;")
        self._pulse_growing = not self._pulse_growing

    def _place(self) -> None:
        app = QApplication.instance()
        screens = app.screens() if app else []
        if not screens:
            return
        if self.settings.overlay_screen == "primary":
            screen = app.primaryScreen()
        elif self.settings.overlay_screen.startswith("index:"):
            try:
                index = int(self.settings.overlay_screen.split(":", 1)[1])
                screen = screens[max(0, min(index, len(screens) - 1))]
            except ValueError:
                screen = app.screenAt(self.cursor().pos()) or app.primaryScreen()
        else:
            center = self._target_context.center
            screen = app.screenAt(QPoint(*center)) if center is not None else None
            screen = screen or app.screenAt(self.cursor().pos()) or app.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        margin = 22
        if self.settings.overlay_position == "custom":
            x = geometry.left() + self.settings.overlay_custom_x
            y = geometry.top() + self.settings.overlay_custom_y
        elif self.settings.overlay_position == "top_right":
            x, y = geometry.right() - self.width() - margin, geometry.top() + margin
        elif self.settings.overlay_position == "bottom_center":
            x, y = geometry.center().x() - self.width() // 2, geometry.bottom() - self.height() - margin
        elif self.settings.overlay_position == "near_cursor":
            cursor = self.cursor().pos()
            x, y = cursor.x() + 18, cursor.y() + 18
        else:
            x, y = geometry.right() - self.width() - margin, geometry.bottom() - self.height() - margin
        min_x = geometry.left() + margin
        max_x = max(min_x, geometry.right() - self.width() - margin)
        min_y = geometry.top() + margin
        max_y = max(min_y, geometry.bottom() - self.height() - margin)
        self.move(max(min_x, min(x, max_x)), max(min_y, min(y, max_y)))
        self.setWindowOpacity(max(0.35, min(1.0, self.settings.overlay_opacity)))
