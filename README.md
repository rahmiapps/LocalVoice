# LocalVoice 2.0.0

## New in 2.0.0

- The new LocalVoice logo is integrated into the app, installer, EXE, taskbar, tray, desktop, Start menu, and Linux packages.
- The dashboard recording orb and sidebar mark now use the real logo.


## New in 1.9.0

- durable UI-language recovery rejects poisoned legacy Chinese confirmations
- German is preselected on German Windows and stored with confirmation schema 3
- reinstallations preserve only a verifiable explicit user choice
- non-destructive Windows PowerShell language repair command
- true incremental dictation: overlapping chunks are decoded while you speak
- live text in the recording overlay; only finalized text is inserted after Stop
- Medium/Large stay resident in memory and use more suitable physical CPU cores
- installed and RAM-loaded model states are shown separately
- the successful live path finalizes only the remaining tail after Stop
- the complete original recording remains a lossless fallback
- phase timings for streaming, audio, transcription, post-processing and translation

**Important:** This greatly reduces post-stop latency for longer dictations, but Medium cannot be guaranteed to finish within one or two seconds on every CPU.

**Private speech. Instant text.**

LocalVoice is a free, ad-free and account-free local dictation and translation application for Windows and Linux. After the user explicitly installs speech and translation models, recording, transcription, post-processing, translation, profiles, vocabulary and history work locally without paid APIs or a cloud account.

## Core workflow

- **Hold mode:** hold the selected hotkey while speaking and release it to stop.
- **Toggle mode:** press once to start and press again to stop.
- Configurable primary/secondary keyboard hotkeys and supported mouse buttons.
- Persistent always-on-top recording overlay with pulsing red indicator, red bar, timer, audio level, detected language and stop/cancel controls.
- Output to the active application, clipboard, preview or LocalVoice only.

## Main capabilities

- Six complete UI languages: German, English, French, Italian, Spanish and Simplified Chinese.
- Full multilingual Whisper language list for automatic, fixed and preferred speech recognition.
- Fixed target language or source-to-target rules; optional original plus translation.
- Local `faster-whisper` transcription and explicitly installed local Argos Translate routes.
- Microphone selection/test, gain, noise gate, normalization, silence stop, unlimited option and streaming long recordings.
- Automatic punctuation, spoken commands, filler/duplicate cleanup, multilingual number conversion and encrypted personal vocabulary.
- Per-application profiles covering hotkeys, languages, translation, output, audio, model and privacy settings.
- Encrypted searchable/editable history, statistics, retention, optional encrypted audio, exports and private mode.
- AES-256-GCM, Scrypt PIN lockout, DPAPI/keyring integration, hardened SQLite, safe archives/model paths and no hidden model downloads in normal dictation.
- Dark/light/system themes, tray, autostart, onboarding, model manager and separate Windows/Linux build pipelines.

See `README_DE.md`, `docs/FEATURES.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `SECURITY.md`, `SECURITY_REVIEW.md` and `BUILD_STATUS.md` for the complete scope and honest verification status.

The source package passed 87 automated tests plus syntax, translation and static-security checks in this environment. Native GUI, microphone, hotkey, model, GPU and installer testing still has to be performed on real Windows and Linux targets before public release.
