from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_brand_assets_exist_and_are_packaged():
    required = [
        ROOT / "resources/localvoice.ico",
        ROOT / "resources/localvoice.png",
        ROOT / "resources/localvoice.svg",
        ROOT / "resources/localvoice-logo-full.png",
        ROOT / "resources/localvoice-mark.png",
        ROOT / "resources/hero-logo.png",
        ROOT / "resources/installer-wizard.bmp",
        ROOT / "resources/installer-small.bmp",
    ]
    assert all(path.is_file() and path.stat().st_size > 100 for path in required)
    spec = (ROOT / "LocalVoice.spec").read_text(encoding="utf-8")
    assert "resources" in spec and "localvoice.ico" in spec


def test_branding_is_wired_into_ui_and_installer():
    main_window = (ROOT / "localvoice/ui/main_window.py").read_text(encoding="utf-8")
    app = (ROOT / "localvoice/app.py").read_text(encoding="utf-8")
    installer = (ROOT / "installer/windows/LocalVoice.iss").read_text(encoding="utf-8")
    assert 'hero-logo.png' in main_window
    assert 'self.brand_icon.setPixmap' in main_window
    assert 'self.mic_button.setIcon(self.voice_icon)' in main_window
    assert 'resources/localvoice.png' in app
    assert 'SetupIconFile=' in installer
    assert 'WizardImageFile=' in installer
    assert 'WizardSmallImageFile=' in installer
