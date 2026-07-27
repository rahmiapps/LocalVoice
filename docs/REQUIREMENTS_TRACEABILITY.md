# Vollständige Anforderungszuordnung 2.1.1

| Anforderung | Umsetzung | Hauptstellen | aktueller Prüfstatus |
|---|---|---|---|
| Name LocalVoice | App-/Paketname und Ressourcen | `localvoice/__init__.py`, Installer, Ressourcen | Quellprüfung |
| Kostenlos, werbefrei, ohne Konto/API/Pro | Keine Billing-/Login-/Cloud-Schicht | gesamte Codebasis, README | Quell-/Auditprüfung |
| Windows und Linux | Gemeinsamer PySide6-Code, getrennte native Pakete | `scripts/`, `installer/`, Workflow | Skriptprüfung; native Pakete offen |
| Halten oder Umschalten | Zustandsautomat je App/Profil | `models.py`, `hotkeys.py`, `controller.py` | Unit-/Vertragsprüfung |
| Frei wählbarer globaler Hotkey | Erfassung/Normalisierung, Tastatur/NumPad/F1–F24/Maus | `dialogs.py`, `validation.py`, `hotkeys.py` | Unit; echte OS-Hooks offen |
| Zweiter Hotkey/Test/Deaktivierung | Primär/sekundär, Aktivierung und echter globaler Backend-Test | `models.py`, `dialogs.py`, `hotkeys.py` | Unit-/Vertragsprüfung; echter OS-Hook offen |
| App-Ein-/Ausschluss | Begrenzte sichere Wildcards und aktive App | `validation.py`, `system.py`, `controller.py` | Unit; Wayland aktiv-App offen |
| Aufnahme-Pop-up sichtbar | Always-on-top, roter Punkt/Balken, Zeit, Pegel | `overlay.py`, `main_window.py` | Vertragsprüfung; native GUI offen |
| Stoppen/Abbrechen/Status | Buttons und alle Verarbeitungszustände | `overlay.py`, `controller.py` | Vertragsprüfung |
| Mehrmonitor/Position/Skala/Transparenz | aktiv/primär/index, fünf Positionen | `overlay.py`, `dialogs.py` | Quellprüfung; echte Monitore offen |
| Mikrofonwahl/Test | Geräteabfrage, unterstützte native Sample-Rate und Qt-freier Pegel-Polling-Test | `audio.py`, `dialogs.py` | Unit-/Vertragsprüfung; Hardware offen |
| Gain/Rauschminderung/Normalisierung | blockweise lokale DSP mit begrenzter automatischer Sprachverstärkung | `audio.py` | Unitprüfung |
| Stille-Stopp/Zeitlimit/unbegrenzt/Töne | Recorderlogik und UI | `audio.py`, `models.py`, `main_window.py` | Unit-/Vertragsprüfung |
| Lange Aufnahmen | Streaming-WAV, blockweise Verarbeitung und Low-Disk-Sicherheitsstopp | `audio.py` | Unitprüfung; Dauerlast offen |
| Auto/feste/bevorzugte Sprache | lokale Whisper-Erkennung | `transcription.py`, `languages.py`, UI | Unitpfade; reale Modelle offen |
| Viele Sprachen | vollständige Whisper-Liste zentral | `languages.py`, `validation.py`, `i18n.py` | Unit-/Quellprüfung |
| Englisch sprechen, Deutsch schreiben | Zielsprache und Quell→Ziel-Regeln | `translation.py`, `controller.py`, UI | Unit mit Test-Doubles; reale Pakete offen |
| Original + Übersetzung | gemeinsame formatierte Ausgabe | `controller.py` | Quellprüfung |
| UI DE/EN/FR/IT/ES/ZH | sechs Tabellen, Onboarding | `i18n.py`, `dialogs.py` | 329 Schlüssel je Sprache; GUI offen |
| Deutsch mit Umlauten | UTF-8-Tabellen/Schriften | `i18n.py`, UI | Übersetzungsprüfung; Rendering offen |
| Direkte Eingabe | aktives Fenster + Zwischenablage/Paste; maximierte Windows-Fenster bleiben maximiert | `system.py`, `window_activation.py`, `controller.py` | Unit-/Quellprüfung; Zielprogramme offen |
| Clipboard/Vorschau/App-only | vier Ausgabemodi | `dialogs.py`, `controller.py`, `main_window.py` | Vertragsprüfung |
| Auto-Enter/Clipboard Restore/Clear | Ausgabeoptionen und Qt-Timer | `system.py` | Quellprüfung; native Apps offen |
| Satzzeichen/Großschreibung | optionale Postverarbeitung | `postprocess.py`, UI | Unitprüfung |
| Sprachbefehle/letzten Satz löschen | mehrsprachige Befehle | `postprocess.py` | Unitprüfung |
| Füllwörter/Duplikate/Zahlen | lokale Textverarbeitung | `postprocess.py` | Unitprüfung |
| Persönliches Wörterbuch | verschlüsselte CRUD-Daten | `database.py`, `dialogs.py`, `postprocess.py` | Unitprüfung |
| Schreibstile | neutral/chat/email | `models.py`, `postprocess.py`, UI | Vertragsprüfung |
| Profile | vollständig verschlüsselte Profilfelder | `models.py`, `database.py`, `dialogs.py`, `controller.py` | Roundtrip-/Vertragsprüfung |
| Modellqualität/CPU/GPU/Beam | lokale Engine-Einstellungen | `transcription.py`, UI | Quellprüfung; echte Hardware offen |
| Modellmanager | ausdrückliche Installation/Entfernung | `dialogs.py`, `transcription.py`, `translation.py` | Integritäts-Unit; Netzwerkdownload offen |
| Keine heimlichen Downloads | `local_files_only`, Download nur Manager | `transcription.py`, `controller.py`, Audit | Vertrags-/Auditprüfung |
| Verlauf/Suche/Bearbeitung | verschlüsselte History und Dialog | `database.py`, `dialogs.py` | Unitprüfung |
| Export/Audioexport/Löschen | CSV/JSON/WAV und CRUD | `database.py`, `dialogs.py` | Unitprüfung |
| Statistiken | lokale Aggregationen | `database.py`, `StatisticsDialog` | Unitprüfung |
| Audio standardmäßig löschen | Processing-Cleanup | `controller.py`, `audio.py` | Unit-/Quellprüfung |
| Audio optional verschlüsselt | `.lva`, AES-GCM, Export | `security.py`, `database.py` | Unitprüfung |
| Privater Modus | erzwingt Verlauf/Audio aus | `models.py`, `controller.py`, UI | Vertragsprüfung |
| PIN/Verschlüsselung | AES-GCM, Scrypt, Lockout, DPAPI/Keyring | `security.py` | Unit; native OS-Backends offen |
| Aufbewahrung/Maximalverlauf | Start, Diktat, Einstellungen, 6h-Timer | `app.py`, `controller.py`, `main_window.py`, `database.py` | Vertrags-/Unitprüfung |
| Dark/Light/System | Stylesheet und Einstellungen | `theme.py`, UI | Quellprüfung; GUI offen |
| Tray/Autostart/minimiert | Systemintegration und Window Events | `main_window.py`, `system.py` | Quellprüfung; native Desktops offen |
| Pop-up-System/wenig Scroll | moderne responsive Startseite, Dialoge, Schnellaktionen und Statuskarten | `dialogs.py`, `main_window.py`, `theme.py` | Quell-/Vertragsprüfung; GUI offen |
| UI-Größe Klein/Mittel/Groß | Mittel auf frühere Groß-Skalierung angehoben; große Zusatzstufe | `models.py`, `dialogs.py`, `theme.py`, `main_window.py` | Vertragsprüfung; Rendering offen |
| Bevorzugte Sprachen ohne Codekenntnis | manuelle Codes plus durchsuchbares Auswahl-Pop-up mit bestehenden Auswahlwerten | `dialogs.py`, `languages.py` | Vertragsprüfung; GUI offen |
| Zuverlässige Zahlenfelder | explizite Minus-/Plus-Schaltflächen statt fehleranfälliger nativer Pfeile | `dialogs.py`, `theme.py` | Vertragsprüfung; GUI offen |
| Einzelinstanz | Benutzer-ID, Befehls-Allowlist, Payloadlimit | `single_instance.py`, `app.py` | Unitprüfung |
| Wayland-Hotkey | XDG Global Shortcuts Portal | `hotkeys.py` | Quell-/Unitpfad; GNOME/KDE offen |
| Wayland-Fallback | `--start/--stop/--toggle`, Clipboard | `app.py`, `system.py`, Desktop-Datei | Quellprüfung; Desktop offen |
| Sichere Datenbank | SQL-Parameter, Secure Delete, Temp Memory | `database.py` | Vertrags-/Unitprüfung |
| Sichere Modelle/Archive | Hash, Pfad, Symlink, Größe, Anzahl | `transcription.py`, `translation.py` | Negativtests |
| Sichere Exporte | CSV-Formelschutz, bewusster Klartext | `database.py`, UI | Unitprüfung |
| Sichere Threads/Shutdown | Qt-Signale/Timer, Jobhaltung, Cleanup | `controller.py`, `dialogs.py`, `main_window.py` | Quellprüfung; GUI-Stress offen |
| Windows Installer/Portable | PyInstaller + Inno Setup | `Build-Windows.ps1`, `LocalVoice.spec` | Skriptvertrag; nativer Build offen |
| Linux AppImage/DEB/TAR | PyInstaller + Paketwerkzeuge | `Build-Linux.sh`, `installer/linux/` | Skriptvertrag; nativer Build offen |
| Build-All via PowerShell/WSL | getrennte Umgebungen | `Build-All.ps1` | Skriptprüfung |
| Sicherheitsprüfung | Tests, AST-Audit, pip-audit, Prüfsummen | `tests/`, `scripts/` | lokal bestanden; native Release offen |

## Ergänzungen 1.9.0 – Aufnahmequalität, Geschwindigkeit und Fensterzustand

| Anforderung | Umsetzung | Prüfung |
|---|---|---|
| Leise/entfernte Stimme besser erfassen | sprachbasierte automatische Verstärkung bis zum sicheren Peak-Limit | `tests/test_audio.py::test_automatic_gain_lifts_quiet_speech_without_clipping` |
| Maximiertes Zielprogramm nicht verkleinern | `SW_RESTORE` nur für tatsächlich minimierte Fenster | `tests/test_completeness.py::test_windows_activation_does_not_restore_a_maximized_window` |
| Deutsche Kurzsätze nicht als Englisch übernehmen | optionale Primärsprachen-Gewichtung und kurzer Einzelvergleich | `tests/test_transcription_quality.py::test_short_auto_dictation_compares_first_preferred_language` |
| Längere Standarddiktate schneller einfügen | Balanced nutzt einen Hauptdurchlauf ohne VAD/Mehrfachvergleich | `tests/test_transcription_quality.py::test_balanced_long_recording_uses_one_non_vad_pass_for_speed` |
| Genau-Modus kann VAD-Fehler retten | begrenzter zweiter Durchlauf nur bei leerem/fragmentiertem Ergebnis | `tests/test_transcription_quality.py::test_accurate_mode_recovers_empty_or_fragmented_vad_result` |
| Mittel = bisher Groß; neues Groß größer | Theme 1.72/1.92 und Fensterdimensionen 400/455 px | `tests/test_requirements_contract.py` |
| Größenmigration nur einmal | Schema-Version 5 ordnet alte Groß-Auswahl einmal Mittel zu | `tests/test_settings.py::test_pre_15_large_ui_is_migrated_once_to_new_medium` |

## Ergänzungen 1.9.0 – Medium-Latenz und Live-Transkription

| Anforderung | Umsetzung | Prüfung |
|---|---|---|
| Modell nicht pro Satz neu laden | eine zentrale `WhisperEngine`, Signaturprüfung und Wiederverwendung von `self._model` | `test_model_instance_is_reused_for_identical_signature` |
| während des Sprechens bereits schreiben | `LiveTranscriptionSession`, überlappende 3-Sekunden-Chunks und Teiltextsignal zum Aufnahme-Pop-up | `test_live_session_processes_during_recording_and_merges_tail` |
| nach Stop nur Rest finalisieren | bereits dekodierte Chunks werden zusammengeführt; nur Tailchunk bleibt | Streaming-Session-Test und Controller-Vertrag |
| Medium auf CPU besser auslasten | automatische Auswahl geeigneter physischer Kerne bis 16, Int8 | Modell-Wiederverwendungstest |
| vollständige Aufnahme darf nicht verloren gehen | separate begrenzte Live-Queue; WAV-Writer bleibt Primärpfad; Fallback bei Drop/Fehler | Audioqueue-Test und Sicherheitsprüfung |
| sichtbarer Lade-/Leistungsstatus | Modellkarte zeigt RAM/CPU/CUDA; Ergebnis zeigt Gesamtzeit und Live-/Fallback-Pfad | Quellvertrag und i18n-Prüfung |
