<p align="center">
  <img src="assets/localvoice-logo.png" alt="LocalVoice logo" width="220">
</p>

<h1 align="center">LocalVoice</h1>

<p align="center">
  <strong>Private offline speech-to-text and local translation for Windows and Linux.</strong><br>
  No account. No advertising. No paid API. Your voice stays on your device.
</p>

<p align="center">
  <a href="README_DE.md">Deutsch</a> ·
  <a href="#download">Download</a> ·
  <a href="#features">Features</a> ·
  <a href="#build-from-source">Build from source</a> ·
  <a href="SECURITY.md">Security</a>
</p>

<p align="center">
  <img alt="Windows" src="https://img.shields.io/badge/Windows-10%20%7C%2011-2672EC?logo=windows11&logoColor=white">
  <img alt="Linux" src="https://img.shields.io/badge/Linux-Desktop-FCC624?logo=linux&logoColor=black">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-7B61FF">
  <img alt="Offline" src="https://img.shields.io/badge/Processing-Local%20%26%20Offline-00C2FF">
  <img alt="Version" src="https://img.shields.io/badge/Version-2.1.1-8B5CF6">
</p>

## Overview

LocalVoice is a free and open-source desktop application that converts speech into text locally. Hold a configurable hotkey while speaking, or press once to start and again to stop. The recognized text can be inserted into the active application, copied to the clipboard, previewed, or saved locally.

Speech recognition and optional translation run on the user's computer after the required models have been installed. LocalVoice does not require an account, subscription, cloud service, or paid API.

## Screenshots

### Dashboard

![LocalVoice dashboard](assets/screenshots/dashboard.png)

<details>
<summary><strong>More screenshots</strong></summary>

### Recording settings

![Recording settings](assets/screenshots/recording-settings.png)

### Speech recognition and translation

![Speech recognition settings](assets/screenshots/speech-recognition-settings.png)

### Privacy and local data

![Privacy settings](assets/screenshots/privacy-settings.png)

</details>

## Download

The Windows installer and Linux packages will be published under **GitHub Releases**.

> The first public installer can be uploaded later without changing the repository contents. See [`docs/RELEASING.md`](docs/RELEASING.md).

### Planned release files

- `LocalVoice-Setup-Windows-x64.exe`
- `LocalVoice-Windows-x64-Portable.zip`
- `LocalVoice-Linux-x86_64.AppImage`
- `LocalVoice-Linux-amd64.deb`
- `LocalVoice-Linux-x64.tar.gz`
- `SHA256SUMS.txt`

## Features

### Dictation

- Two recording modes: hold-to-record or press-to-start/press-to-stop
- Configurable global primary and secondary hotkeys
- Visible recording pop-up with timer, level meter, status and controls
- Direct insertion into the active application
- Clipboard, preview and LocalVoice-only output modes
- Microphone selection, testing, gain, normalization and optional noise reduction
- Automatic amplification for quiet or distant speech
- Long-recording support and live partial transcription

### Languages and translation

- Automatic language detection
- Fixed input language and preferred-language weighting
- Local multilingual Whisper speech recognition
- Fixed target language or automatic source-to-target rules
- Optional original text plus translation
- Six complete interface languages:
  - German
  - English
  - French
  - Italian
  - Spanish
  - Simplified Chinese

### Productivity

- Personal vocabulary and custom replacements
- Per-application profiles
- Automatic punctuation and spoken editing commands
- Local searchable and editable history
- Statistics, export and retention controls
- System tray, autostart, dark/light/system themes and UI scaling

### Privacy and security

- Local-first processing
- No account, ads, subscription or hidden API calls
- Encrypted history, profiles, vocabulary and optional audio storage
- AES-256-GCM protected local data
- Optional PIN protection with Scrypt-based key derivation
- Windows DPAPI and Linux keyring integration where available
- Private mode that stores nothing
- Explicit model downloads only through the model manager

## How it works

1. Install LocalVoice.
2. Select the interface language.
3. Choose and test a microphone.
4. Install a speech-recognition model in the model manager.
5. Select a hotkey and recording mode.
6. Press the hotkey, speak, and stop recording.
7. LocalVoice transcribes locally and inserts the text into the active application.

## Model guidance

| Model | Typical use | Speed | Accuracy |
|---|---|---:|---:|
| Small | Most PCs and quick dictation | Fast | Good |
| Medium | Better recognition on capable hardware | Medium | Very good |
| Large | Maximum accuracy on powerful hardware | Slowest | Highest |

Actual speed depends on CPU, GPU, microphone quality, recording length and selected recognition settings.

## Build from source

### Windows

Requirements:

- Windows 10 or 11, 64-bit
- Python 3.12, 64-bit
- Inno Setup 6
- PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Build-Windows.ps1
```

Outputs:

```text
dist\LocalVoice\LocalVoice.exe
release\windows\LocalVoice-Setup-Windows-x64.exe
```

### Linux

```bash
bash scripts/Build-Linux.sh
```

See [`docs/BUILDING.md`](docs/BUILDING.md) for detailed instructions.

## Repository structure

```text
localvoice/          Application source
resources/           Icons and installer assets
installer/           Windows and Linux package definitions
scripts/             Build, test and packaging scripts
tests/               Automated tests
docs/                Documentation and release instructions
assets/screenshots/   GitHub screenshots
.github/              CI, issue and pull-request templates
```

## Security and privacy

Please read [`SECURITY.md`](SECURITY.md) before reporting a vulnerability. Do not publish security-sensitive details in a public issue.

## Contributing

Contributions are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

## License

LocalVoice is released under the [MIT License](LICENSE).

Copyright © 2026 Rahmi Apps.
