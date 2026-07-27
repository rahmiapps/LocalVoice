# LocalVoice 2.1.1 – Bedrohungsmodell

## Schutzwerte

- Mikrofonaufnahmen und optionale gespeicherte Audiodateien
- Original-/Endtranskriptionen und Übersetzungen
- Zielprogramme, Wörterbuch und Profile
- Masterkey, PIN-Wrapping und Lockout-Zustand
- lokale Sprach-/Übersetzungsmodelle
- Zwischenablage und Klartextexporte

## Bedrohungen und Gegenmaßnahmen

### Manipulierte lokale Konfiguration/Daten

Atomare Einstellungen, Allowlisten, Längenlimits, authentifizierte AES-GCM-Verschlüsselung, sichere Fehlermeldungen, keine stille Neuerstellung beschädigter Schlüsseldateien und SQLite-Härtung.

### Modell-/Archivmanipulation

Verwaltete Modelle werden vollständig gehasht. Nicht verifizierte vorhandene Ordner werden nicht nachträglich vertraut. Archive/Verzeichnisse werden gegen Traversal, Symlinks, Sonderdateien, übergroße Dateien und Dateimengen geprüft.

### Verdeckter Netzwerkzugriff

Der Diktierpfad fordert lokale Modellauflösung an. Downloads sind auf ausdrücklich gestartete Modellmanager-Aktionen begrenzt. Der statische Audit sucht nach unerlaubten Netzwerk-/Downloadpfaden.

### Bösartige Sprache/Texte/Konfiguration

Gesprochener Text wird nicht als Code ausgeführt. SQL ist parametrisiert, App-Wildcards sind begrenzt, Wörterbuchersetzung escaped reguläre Ausdrücke, Exporte schützen vor Tabellenformeln und Hotkeys/Sprachen/Pfade werden normalisiert.

### Lokaler IPC-/Mehrfachstart-Missbrauch

Benutzerbezogene Einzelinstanzkennung, kleine Befehls-Allowlist, Payload-Grenze und keine freie Befehlsausführung.

### Versehentliche Datenweitergabe

Audio standardmäßig löschen, privater Modus, verschlüsselte optionale Speicherung, Aufbewahrungsfristen, Zwischenablage-Restore/-Clear und bewusste Klartextexporte.

### Thread-/Shutdown-Fehler

Gebundene Hintergrundjobs, Qt-Hauptthread-Signale/-Timer, kontrollierter Shutdown, temporäre Dateibereinigung und Abbruchpfade.

## Vertrauensannahmen

- Betriebssystem, Python/Qt, Audiotreiber und installierte Abhängigkeiten sind nicht kompromittiert.
- Der Benutzer wählt vertrauenswürdige Modelle/Übersetzungspakete und schützt Klartextexporte.
- Betriebssystem-Dateirechte und – für starken Schutz bei ausgeschaltetem Gerät – Vollverschlüsselung funktionieren.

## Nicht vollständig abdeckbar

- Administrator/root, Kernel-/Treiberkompromittierung oder Malware im Benutzerkonto
- Physischer Zugriff auf einen entsperrten oder unverschlüsselten Rechner
- Screen-/Keylogger, bösartige Zielanwendung oder Zwischenablageüberwachung
- Lieferkettenkompromittierung externer Python-, Qt-, Whisper-, Hugging-Face-, Argos- oder OS-Pakete
- Fehlerhafte Erkennung/Übersetzung; Ergebnisse benötigen bei wichtigen Inhalten menschliche Prüfung
- Metadaten wie Zeitpunkt, Dauer, Sprache und Wortanzahl
- Wayland-Funktionen, die die Desktopumgebung absichtlich nicht freigibt
- Absolute Null-Fehler- oder Null-Risiko-Garantie
