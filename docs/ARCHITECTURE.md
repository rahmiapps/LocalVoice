# LocalVoice 2.1.1 – Architektur

## Oberfläche

PySide6 stellt Onboarding, Hauptfenster, Dialog-/Tab-System, Verlauf, Statistiken, Wörterbuch, Profile, Modellmanager, Einstellungen, Datenschutz/Hilfe/Info und das Always-on-top-Aufnahme-Pop-up bereit. UI-Texte kommen aus sechs vollständigen Übersetzungstabellen.

## Aufnahme

`AudioRecorder` schreibt 16-kHz-Mono-Blöcke in eine temporäre WAV-Datei, statt die gesamte Sitzung im RAM zu halten. Pegel, Stille und Zeitlimit werden laufend ausgewertet. `AudioProcessor` bearbeitet Dateien blockweise mit Verstärkung, DC-/Hochpassbereinigung, Noise Gate und Normalisierung.

## Steuerung

`GlobalHotkeyService` verwaltet Halten/Umschalten, primäre/sekundäre und Profilhotkeys. Windows/X11 nutzen pynput-basierte Hooks; Wayland-Tastaturkürzel verwenden das XDG Global Shortcuts Portal. `SingleInstance` akzeptiert nur erlaubte lokale Start-/Stop-/Toggle-/Show-Befehle.

## Spracherkennung

`WhisperEngine` löst ausschließlich einen vorhandenen lokalen Modellordner auf und startet `faster-whisper`. Automatische Erkennung kann bei geringer Sicherheit bevorzugte Sprachen erneut bewerten. Der Modellmanager ist die einzige ausdrückliche Downloadoberfläche. Verwaltete Modelle besitzen ein Hashmanifest.

## Text und Übersetzung

`TextPostProcessor` verarbeitet Satzzeichen, Befehle, Wiederholungen, Füllwörter, Zahlen, Stil und Wörterbuch. `LocalTranslator` nutzt lokal installierte Argos-Routen direkt oder über eine begrenzte Zwischensprachenroute. Nicht zu übersetzende Wörterbuchbegriffe werden während der Übersetzung geschützt.

## Profile

Ein Profil überlagert eine Kopie der globalen Einstellungen. Programmzuordnung und manuelle Profilhotkeys wählen Sprache, Ausgabe, Textbearbeitung, Audio, Modell und Datenschutz, ohne die globalen Werte dauerhaft zu verändern.

## Ausgabe

`TextInjector` kopiert Text, stellt soweit möglich das zuvor aktive Fenster wieder her und fügt ein. Auto-Enter, zeitgesteuertes Leeren und Restore der vorherigen Text-Zwischenablage laufen über Qt-Timer. Bei fehlender direkter Eingabemöglichkeit bleibt der Text kopiert.

## Daten und Sicherheit

SQLite speichert IDs und notwendige Metadaten. Sensible Texte, Zielprogramme, Wörterbuch und Profile sind einzeln AES-GCM-verschlüsselt. Audio kann als verschlüsselte `.lva`-Datei gespeichert werden. `SecureStore` verwaltet Masterkey, DPAPI/Keyring/Fallback und optionales Scrypt-PIN-Wrapping. Aufbewahrung wird an vier Stellen erzwungen.

## Plattform/Build

Die Anwendung teilt den Python-Code. Native Unterschiede liegen in aktiven Fenstern, Hotkeys, Einfügen, Autostart, Tray, Schlüsselablage und Paketierung. Windows verwendet PyInstaller/Inno Setup; Linux PyInstaller/AppImage/DEB/TAR. Windows- und Linux-Virtualenvs sind getrennt; Build-All orchestriert Linux via WSL.
