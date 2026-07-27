# LocalVoice 2.0.0 – verbindlicher Testplan vor Veröffentlichung

## Automatische Quellprüfung

```bash
python scripts/Run-Checks.py
```

Aktuell enthalten:

- Python-Syntaxprüfung
- 71 bestandene Tests, ein optionaler PySide6-GUI-Test
- sechs UI-Sprachen mit jeweils 319 Schlüsseln
- statischer Sicherheits-Audit
- GUI-Smoke-Test, sobald PySide6 verfügbar ist

Zusätzlich separat:

```bash
python -m compileall -q localvoice tests scripts
python scripts/Audit-Security.py
python -m pytest -q
```

In Release-Builds müssen außerdem `pip check`, `pip-audit`, PyInstaller, GUI-/Paket-Smoke, Paketexistenzprüfung, Dependency-Bericht und SHA-256-Prüfsummen bestehen.

## Windows 10/11

1. Installation, Upgrade, Reparatur und Deinstallation als Standardbenutzer.
2. Signatur/unsignierten Status und SmartScreen dokumentieren.
3. Onboarding und sämtliche Dialoge in allen sechs UI-Sprachen; Umlaute/CJK prüfen.
4. Notebook-, USB-, Bluetooth-, Webcam- und wechselnde Mikrofone.
5. Halten/Umschalten mit Funktionstaste, NumPad, Kombination, zweitem Hotkey und Maus 4/5.
6. Hotkey-Test, Unterdrückung, Deaktivierung, App-Ein-/Ausschluss und Konflikte.
7. Pop-up auf einem, zwei und drei Monitoren; aktive/feste Anzeige und alle Positionen.
8. Pegel, pulsierender Punkt/Balken, Zeit, erkannte Sprache, Stoppen/Abbrechen und alle Statuszustände.
9. Stille-Stopp, Schwellenwerte, unbegrenzt, Zeitlimit, Gain, Noise Gate, Normalisierung, Töne.
10. Mehrstündige Aufnahme sowie viele kurze Aufnahmen auf Speicher-, Datei- und Threadlecks.
11. Einfügen in Notepad, Word/LibreOffice, Browser, Chat, Mail und Codeeditor.
12. Vorschau, App-only, Clipboard, Restore, Clear und Auto-Enter.
13. Tiny/Base/Small/Medium/Large-Konfiguration auf CPU; mindestens ein GPU-Pfad.
14. Automatische/feste/bevorzugte Sprache DE/EN/FR/IT/ES/ZH plus weitere Whisper-Sprachen.
15. Erkennungsschwelle, Dialekte, Hintergrundgeräusch, Fachbegriffe und Mischsprache dokumentieren.
16. Direkte und mehrstufige Argos-Routen, Sprachregeln und Original+Übersetzung.
17. Satzzeichen, Großschreibung, Befehle, Zahlen, Füllwörter, Duplikate, Stile und Wörterbuch.
18. Manuelle Profile, Profilhotkeys und automatische Profilumschaltung.
19. Verlauf suchen/bearbeiten/kopieren/exportieren/löschen; Statistik und Aufbewahrung.
20. Sechs-Stunden-Aufbewahrung durch verkürzten Testtimer simulieren.
21. Audio speichern/exportieren/löschen; `.lva` manipulieren und Fehler prüfen.
22. Privater Modus: keine History-/Audiozeile und keine verwaiste Datei.
23. PIN, fünf Fehlversuche, Neustart, Lockout, richtiger PIN und PIN-Entfernung.
24. DPAPI mit unterschiedlichen Windows-Benutzern.
25. Tray, Autostart, minimierter Start, Close-to-Tray und Einzelinstanzbefehle.

## Linux

Mindestens Ubuntu 24.04 sowie eine zweite aktuelle Distribution.

### X11

- Tastatur- und Maus-Hotkeys, Unterdrückung, aktive App, Einfügen und Zwischenablage
- Tray, Autostart, Profile und mehrere Monitore
- AppImage, DEB und Portable-TAR auf frischem Benutzerkonto

### Wayland – GNOME und KDE

- XDG Global Shortcuts Portal: Genehmigung, Neustartbindung, Aktivierung/Deaktivierung
- Halten/Umschalten für Tastaturhotkeys
- Ablehnung/Widerruf der Portalberechtigung und klarer Fallback
- Desktop-Shortcuts für `--start`, `--stop`, `--toggle`
- Keine Behauptung von Maus-Hotkey-Unterstützung über das Standardportal
- Clipboard-Fallback und optionale direkte Eingabe über korrekt eingerichtetes Tool
- Automatische Profile nur dort, wo aktives Fremdfenster verfügbar ist
- Keine falsche „eingefügt“-Meldung bei fehlender Berechtigung

## Sicherheits-/Negativtests

- Beschädigte/abgeschnittene Einstellungen, Sicherheitsdatei, Datenbank, Modellmanifest und Audio
- Modellordner/Archive mit Traversal, Symlink, übergroßen Dateien, vielen Dateien und Hashänderung
- Manipulierte Ciphertexte, falscher Schlüssel und beschädigte `.lva`
- Sehr lange Texte, Unicode, CJK, ungültige Hotkeys, Programmmuster und Sprachregeln
- CSV-Formelanfänge und Klartext-Exportwarnungen
- Parallelstart, nicht erlaubte IPC-Befehle, übergroße Payload und veraltete Socketdatei
- Abbruch/Shutdown während Aufnahme, DSP, Transkription, Übersetzung und Modellinstallation
- Berechtigungen von DB, Schlüssel-, Audio-, Log- und Exportdateien
- Dependency-Audit und manuelle Prüfung aller Findings

Ein Release darf erst nach dokumentiert bestandenen nativen Tests als produktionsbereit bezeichnet werden.

## Zusätzliche 1.9.0-Prüfungen

- kurze deutsche Aufnahme mit englischer Auto-Fehlerhypothese
- langer VAD-Fragmentfall mit automatischer Wiederholung
- Erhalt leiser Sprachenergie nach Rauschminderung
- schnelle Standardparameter und Sprachsegmentprüfung
- UI-Skalierung Mittel/Groß

## Zusätzliche 1.9.0-Prüfungen

1. Medium installieren, Modellvorladen aktivieren und warten, bis „Im Arbeitsspeicher geladen“ angezeigt wird.
2. Eine 15-Sekunden-Aufnahme sprechen und beobachten, ob währenddessen Teiltext im Pop-up erscheint.
3. Nach Stop die angezeigte Restzeit und den Hinweis „live verarbeitet“ prüfen.
4. Im Tooltip der letzten Verarbeitung die Phasenzeiten kontrollieren.
5. CPU-Test und CUDA-Test getrennt durchführen; Real-Time-Faktor und Wortgenauigkeit dokumentieren.
6. Live-Transkription deaktivieren und den vollständigen Fallbackpfad prüfen.
7. Live-Queue künstlich überlasten und sicherstellen, dass die komplette WAV-Aufnahme weiterhin final transkribiert wird.
