from __future__ import annotations


def stylesheet(theme: str, ui_size: str = "medium") -> str:
    if theme == "system":
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            theme = "dark" if app and app.palette().window().color().lightness() < 128 else "light"
        except Exception:
            theme = "dark"

    # The former "large" size is now the recommended medium size. Large adds a
    # further step while scroll areas keep every control reachable.
    scales = {"small": 1.22, "medium": 1.72, "large": 1.92}
    scale = scales.get(ui_size, scales["medium"])
    px = lambda value: max(1, round(value * scale))

    dark = theme != "light"
    bg = "#080D1A" if dark else "#F3F6FB"
    sidebar = "#0D1425" if dark else "#FFFFFF"
    panel = "#111A2D" if dark else "#FFFFFF"
    panel_alt = "#17233B" if dark else "#EDF2FA"
    panel_hover = "#1B2945" if dark else "#E5ECF7"
    text = "#F6F8FC" if dark else "#172033"
    muted = "#96A5BF" if dark else "#66738A"
    border = "#243453" if dark else "#D8E0EC"
    subtle_border = "#1B2944" if dark else "#E2E8F1"
    accent = "#6C8CFF"
    accent_hover = "#7C9AFF"
    accent2 = "#9A6CFF"
    danger = "#FF5C75"
    success = "#35D3A7"
    warning = "#FFB84D"

    return f"""
    * {{
        font-family: 'Segoe UI Variable', 'Segoe UI', 'Noto Sans', sans-serif;
        font-size: {px(13)}px;
        color: {text};
    }}
    QMainWindow, QDialog, QWidget#Root, QWidget#DashboardContent {{ background: {bg}; }}
    QScrollArea#DashboardScroll, QScrollArea#DashboardScroll > QWidget > QWidget {{ background: {bg}; border: none; }}
    QWidget#Sidebar {{ background: {sidebar}; border-right: 1px solid {subtle_border}; }}

    QFrame#BrandCard {{
        background: {panel};
        border: 1px solid {border};
        border-radius: {px(17)}px;
    }}
    QLabel#BrandMark {{
        min-width: {px(43)}px; max-width: {px(43)}px;
        min-height: {px(43)}px; max-height: {px(43)}px;
        border-radius: {px(14)}px;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {accent},stop:1 {accent2});
        color: white; font-size: {px(14)}px; font-weight: 900;
    }}
    QLabel#AppTitle {{ font-size: {px(20)}px; font-weight: 850; }}
    QLabel#Subtitle, QLabel#Muted, QLabel#StatusDetail {{ color: {muted}; }}
    QLabel#PageTitle {{ font-size: {px(27)}px; font-weight: 850; }}
    QLabel#SectionTitle {{ font-size: {px(23)}px; font-weight: 800; }}
    QLabel#SectionHeading {{ font-size: {px(15)}px; font-weight: 800; color: {text}; padding-top: {px(2)}px; }}
    QLabel#CardTitle {{ font-size: {px(16)}px; font-weight: 750; }}
    QLabel#BigValue {{ font-size: {px(24)}px; font-weight: 850; }}

    QPushButton#NavButton {{
        text-align: left;
        padding: {px(12)}px {px(14)}px;
        border: 1px solid transparent;
        border-radius: {px(12)}px;
        background: transparent;
        color: {muted};
        font-weight: 650;
    }}
    QPushButton#NavButton:hover {{ background: {panel}; color: {text}; border-color: {subtle_border}; }}
    QPushButton#NavButton:checked {{
        background: {panel_alt}; color: {text}; border-color: {border};
        border-left: {px(3)}px solid {accent};
    }}
    QLabel#PrivacyBadge {{
        background: {panel}; border: 1px solid {subtle_border}; border-radius: {px(12)}px;
        padding: {px(10)}px {px(11)}px; color: {muted};
    }}

    QLabel#StatusPill {{
        background: {panel}; border: 1px solid {border}; border-radius: {px(15)}px;
        padding: {px(8)}px {px(13)}px; font-weight: 750;
    }}

    QFrame#HeroCard {{
        min-height: {px(220)}px;
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #365FD8, stop:0.48 {accent}, stop:1 {accent2});
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: {px(26)}px;
    }}
    QLabel#HeroBadge {{
        background: rgba(6,13,30,0.23); color: white;
        border: 1px solid rgba(255,255,255,0.20);
        border-radius: {px(12)}px; padding: {px(6)}px {px(10)}px; font-weight: 700;
    }}
    QLabel#HeroTitle {{ color: white; font-size: {px(29)}px; font-weight: 900; }}
    QLabel#HeroText {{ color: rgba(255,255,255,0.88); font-size: {px(15)}px; }}
    QLabel#HeroMode {{ color: rgba(255,255,255,0.86); font-weight: 650; }}
    QPushButton#VoiceOrb {{
        min-width: {px(150)}px; max-width: {px(150)}px;
        min-height: {px(150)}px; max-height: {px(150)}px;
        border-radius: {px(75)}px;
        background: rgba(255,255,255,0.13);
        border: {px(6)}px solid rgba(255,255,255,0.13);
        color: white; font-size: {px(43)}px; font-weight: 900;
    }}
    QPushButton#VoiceOrb:hover {{ background: rgba(255,255,255,0.20); border-color: rgba(255,255,255,0.24); }}
    QPushButton#PrimaryLarge {{
        background: white; color: #22345F; border: none; border-radius: {px(13)}px;
        padding: {px(12)}px {px(18)}px; font-size: {px(14)}px; font-weight: 850;
    }}
    QPushButton#PrimaryLarge:hover {{ background: #F1F4FF; }}
    QPushButton#HeroSecondary {{
        background: rgba(7,15,35,0.23); color: white;
        border: 1px solid rgba(255,255,255,0.25); border-radius: {px(13)}px;
        padding: {px(12)}px {px(17)}px; font-weight: 750;
    }}
    QPushButton#HeroSecondary:hover {{ background: rgba(7,15,35,0.36); }}

    QPushButton#QuickAction {{
        min-height: {px(67)}px;
        background: {panel}; border: 1px solid {border}; border-radius: {px(16)}px;
        padding: {px(10)}px {px(13)}px; font-weight: 750;
    }}
    QPushButton#QuickAction:hover {{ background: {panel_hover}; border-color: {accent}; }}

    QFrame#StatusCard, QFrame#TranscriptCard, QFrame#Card {{
        background: {panel}; border: 1px solid {border}; border-radius: {px(18)}px;
    }}
    QFrame#StatusCard[status="ok"] {{ border-left: {px(3)}px solid {success}; }}
    QFrame#StatusCard[status="warning"] {{ border-left: {px(3)}px solid {warning}; }}
    QFrame#StatusCard[status="neutral"] {{ border-left: {px(3)}px solid {muted}; }}
    QLabel#StatusIcon {{
        min-width: {px(43)}px; max-width: {px(43)}px;
        min-height: {px(43)}px; max-height: {px(43)}px;
        border-radius: {px(13)}px; background: {panel_alt}; color: {accent};
        font-size: {px(19)}px; font-weight: 850;
    }}
    QLabel#StatusTitle {{ color: {muted}; font-weight: 700; }}
    QLabel#StatusValue {{ font-size: {px(15)}px; font-weight: 820; }}
    QLabel#LastText {{ color: {text}; font-size: {px(15)}px; padding: {px(8)}px 0; }}

    QPushButton {{
        background: {panel_alt}; border: 1px solid {border}; border-radius: {px(11)}px;
        padding: {px(10)}px {px(15)}px; font-weight: 700;
    }}
    QPushButton:hover {{ background: {panel_hover}; border-color: {accent}; }}
    QPushButton:pressed {{ padding-top: {px(11)}px; padding-bottom: {px(9)}px; }}
    QPushButton#Primary {{ background: {accent}; border-color: {accent}; color: white; }}
    QPushButton#Primary:hover {{ background: {accent_hover}; }}
    QPushButton#SoftPrimary {{ background: rgba(108,140,255,0.13); color: {text}; border-color: rgba(108,140,255,0.45); }}
    QPushButton#Danger {{ background: {danger}; border-color: {danger}; color: white; }}

    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QKeySequenceEdit, QTextEdit {{
        min-height: {px(24)}px;
        background: {panel_alt}; border: 1px solid {border}; border-radius: {px(11)}px;
        padding: {px(9)}px {px(11)}px; selection-background-color: {accent};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QKeySequenceEdit:focus, QTextEdit:focus {{ border-color: {accent}; }}
    QComboBox::drop-down {{ border: none; width: {px(31)}px; }}
    QWidget#SpinControl {{ background: transparent; }}
    QToolButton#StepButton {{
        min-width: {px(35)}px; max-width: {px(35)}px;
        min-height: {px(35)}px; max-height: {px(35)}px;
        background: {panel_alt}; border: 1px solid {border}; border-radius: {px(10)}px;
        font-size: {px(18)}px; font-weight: 850;
    }}
    QToolButton#StepButton:hover {{ background: {panel_hover}; border-color: {accent}; }}

    QCheckBox {{ spacing: {px(9)}px; }}
    QCheckBox::indicator {{ width: {px(19)}px; height: {px(19)}px; border: 1px solid {border}; border-radius: {px(6)}px; background: {panel_alt}; }}
    QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}

    QTabWidget::pane {{ border: 1px solid {border}; border-radius: {px(15)}px; background: {panel}; top: -1px; }}
    QTabBar::tab {{ background: transparent; color: {muted}; padding: {px(11)}px {px(16)}px; margin-right: {px(4)}px; }}
    QTabBar::tab:selected {{ color: {text}; background: {panel_alt}; border-radius: {px(10)}px; }}
    QListWidget, QTableWidget {{ background: {panel}; alternate-background-color: {panel_alt}; border: 1px solid {border}; border-radius: {px(13)}px; gridline-color: {border}; }}
    QListWidget::item {{ padding: {px(8)}px; border-radius: {px(8)}px; }}
    QListWidget::item:hover {{ background: {panel_hover}; }}
    QHeaderView::section {{ background: {panel_alt}; border: none; border-bottom: 1px solid {border}; padding: {px(9)}px; font-weight: 750; }}
    QProgressBar {{ background: {panel_alt}; border: 1px solid {border}; border-radius: {px(6)}px; min-height: {px(12)}px; max-height: {px(12)}px; text-align: center; }}
    QProgressBar::chunk {{ background: {success}; border-radius: {px(5)}px; }}

    QScrollBar:vertical {{ background: transparent; width: {px(11)}px; margin: {px(4)}px; }}
    QScrollBar::handle:vertical {{ background: {border}; border-radius: {px(5)}px; min-height: {px(34)}px; }}
    QScrollBar::handle:vertical:hover {{ background: {accent}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QToolTip {{ background: {panel_alt}; color: {text}; border: 1px solid {border}; padding: {px(7)}px; }}
    """
