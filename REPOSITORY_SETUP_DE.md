# GitHub-Repository anlegen

Trage auf der GitHub-Seite folgende Werte ein:

## General

**Repository name**

```text
LocalVoice
```

**Description**

```text
Private offline speech-to-text and local translation for Windows and Linux — no account, no ads, no API fees.
```

## Configuration

- Visibility: **Public**
- Add README: **Off**
- Add .gitignore: **No .gitignore**
- Add license: **No license**

README, `.gitignore` und MIT-Lizenz sind bereits im vorbereiteten Ordner enthalten.

## Empfohlene Topics

```text
speech-to-text
offline
whisper
dictation
voice-recognition
transcription
translation
privacy
windows
linux
python
pyside6
faster-whisper
local-first
open-source
```

## Nach dem Erstellen hochladen

PowerShell im vorbereiteten Repository-Ordner öffnen:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial public release of LocalVoice"
git remote add origin https://github.com/rahmiapps/LocalVoice.git
git push -u origin main
```

Falls Git nach Name und E-Mail fragt:

```powershell
git config --global user.name "Rahmi Apps"
git config --global user.email "DEINE_GITHUB_EMAIL"
```

## EXE später hinzufügen

Die EXE nicht in den normalen Repository-Ordner kopieren. Erstelle stattdessen unter GitHub einen **Release** und lade dort die Datei hoch. Siehe `docs/RELEASING.md`.
