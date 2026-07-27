# Building LocalVoice

## Windows

### Requirements

- Windows 10/11 x64
- Python 3.12 x64
- Inno Setup 6
- PowerShell

### Build

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Build-Windows.ps1
```

The script creates a virtual environment, installs dependencies, runs tests and security checks, creates the portable application and builds the Inno Setup installer.

Expected outputs:

```text
dist\LocalVoice\LocalVoice.exe
release\windows\LocalVoice-Setup-Windows-x64.exe
release\windows\LocalVoice-Windows-x64-Portable.zip
```

## Linux

Install the system packages required by Python, Qt, PortAudio and the chosen packaging format, then run:

```bash
bash scripts/Build-Linux.sh
```

Expected outputs may include AppImage, DEB and portable TAR.GZ packages.

## Important native tests

Before a public release, test on real systems:

- Microphone recording and level meter
- Hold and toggle hotkeys
- Windows, X11 and Wayland behavior
- Text insertion into common applications
- Small, Medium and Large speech models
- CPU and supported GPU paths
- Installer, update and uninstall behavior
- All six interface languages
