# LocalVoice 2.0.0

## Neu in 2.0.0

- Neues LocalVoice-Logo vollständig in App, Installer, EXE, Taskleiste, Tray, Desktop, Startmenü und Linux-Pakete integriert.
- Dashboard-Aufnahmekreis und Seitenleisten-Marke verwenden jetzt das echte Logo.


## Neu in 1.9.0

- dauerhafte Sprachreparatur: alte fehlerhafte chinesische Bestätigungen werden verworfen
- Deutsch wird auf deutschem Windows vorausgewählt und im neuen Schema 3 bestätigt
- Deinstallation und Neuinstallation übernehmen nur eine nachweislich explizite Sprachwahl
- zusätzlicher nicht-destruktiver PowerShell-Reparaturbefehl ohne Löschen von Modellen oder Verlauf
- echtes fortlaufendes Diktat: LocalVoice transkribiert überlappende Abschnitte bereits während des Sprechens
- Live-Text im Aufnahme-Pop-up; finaler Text wird erst nach Stop sicher in das Zielprogramm eingefügt
- Medium-/Large-Modelle bleiben dauerhaft im Arbeitsspeicher und nutzen automatisch mehr geeignete CPU-Kerne
- installierter und im RAM geladener Modellstatus werden sichtbar unterschieden
- nach Stop wird bei erfolgreichem Live-Pfad nur der letzte Restabschnitt finalisiert
- vollständige Originalaufnahme bleibt als verlustfreier Fallback erhalten
- genaue Laufzeitmessung für Stream, Audio, Transkription, Nachbearbeitung und Übersetzung

**Wichtig:** Die neue Architektur reduziert besonders bei längeren Diktaten die Wartezeit nach Stop. Medium kann auf schwächeren CPUs dennoch nicht garantiert in ein bis zwei Sekunden arbeiten. Das Pop-up zeigt an, wenn die lokale Hardware aufholt.

**Private Sprache. Sofortiger Text.**

LocalVoice ist eine kostenlose, werbefreie und kontofreie Diktier- und Übersetzungs-App für Windows und Linux. Sprachaufnahmen, Transkription, Textbearbeitung, Übersetzung, Wörterbuch, Profile und Verlauf werden lokal verarbeitet. Es gibt keine bezahlte API, kein Abonnement und keinen Cloud-Zwang.

Modelle werden wegen ihrer Größe nicht mit dem Quellarchiv ausgeliefert. Der Nutzer installiert sie ausdrücklich im Modellmanager oder wählt einen vorhandenen lokalen Modellordner. Der normale Diktierablauf darf kein Modell heimlich herunterladen.

## Aufnahme

LocalVoice unterstützt zwei frei wählbare Betriebsarten:

- **Gedrückt halten:** Hotkey halten, sprechen, zum Stoppen loslassen.
- **Umschalten:** Hotkey einmal zum Starten und erneut zum Stoppen drücken.

Der primäre und ein optionaler zweiter globale Hotkey können Tastaturtasten, NumPad-Tasten, Funktionstasten, Kombinationen und – auf unterstützten Plattformen – zusätzliche Maustasten verwenden. Hotkeys können getestet, vorübergehend deaktiviert und auf Programme begrenzt beziehungsweise aus Programmen ausgeschlossen werden.

Während der Aufnahme bleibt ein Always-on-top-Pop-up sichtbar. Es enthält einen pulsierenden roten Punkt, roten Statusbalken, Aufnahmezeit, Audiopegel/Wellenform, erkannte Sprache sowie Stoppen und Abbrechen. Danach zeigt es Verarbeitung, Modellladen, Übersetzung, Einfügen, Kopieren, Abbruch oder Fehler und blendet sich anschließend aus. Monitor, Position, Größe, Transparenz und Verarbeitungssichtbarkeit sind einstellbar.

## Sprachen und Übersetzung

Die komplette Oberfläche ist verfügbar in:

- Deutsch, einschließlich korrekter Umlaute
- Englisch
- Französisch
- Italienisch
- Spanisch
- Vereinfachtem Chinesisch

Die Oberflächensprache wird beim ersten Start gewählt und bleibt unabhängig von Eingabe- und Ausgabesprache.

Die Spracherkennung unterstützt die vollständige mehrsprachige Whisper-Sprachliste. Als Eingabe kann automatisch, fest oder mit bevorzugten Sprachen gearbeitet werden. Die Ausgabe kann in der Originalsprache bleiben, in eine feste Zielsprache übersetzt werden oder Regeln wie `Englisch → Deutsch`, `Französisch → Italienisch` und `Deutsch → Englisch` verwenden. Original und Übersetzung können gemeinsam ausgegeben werden.

Transkription erfolgt lokal über `faster-whisper`. Freie Sprachpaare werden lokal über ausdrücklich installierte Argos-Translate-Pakete direkt oder über eine konfigurierte Zwischensprache übersetzt.

## Textausgabe und Bearbeitung

- Direkt in das zuvor aktive Programm einfügen
- Nur in die Zwischenablage kopieren
- Vorschau vor dem Einfügen
- Nur in LocalVoice behalten
- Optional Enter nach dem Einfügen
- Vorherige Text-Zwischenablage wiederherstellen oder zeitgesteuert leeren
- Automatische Satzzeichen und Großschreibung
- Zahlen als Ziffern, einschließlich größerer gesprochener Zahlen in DE/EN/FR/IT/ES/ZH
- Füllwörter und unmittelbare Wortwiederholungen optional entfernen
- Gesprochene Befehle für Punkt, Komma, Fragezeichen, Zeile, Absatz, Anführungszeichen und letzten Satz löschen
- Persönliches verschlüsseltes Wörterbuch mit gewünschter Schreibweise, Sprache, Groß-/Kleinschreibung und Nicht-übersetzen-Regel
- Schreibstile für neutralen Text, Chat und E-Mail

## Mikrofon, Modelle und Leistung

- Mikrofonwahl, Pegeltest und Testaufnahme
- Manuelle und automatische Mikrofonverstärkung für leise/weiter entfernte Sprache
- Lokale sanfte Rauschminderung und Normalisierung mit Peak-Limiter
- Automatischer Stille-Stopp mit Schwellenwert und Dauer
- Einstellbare maximale Aufnahmezeit oder unbegrenzt
- Start-/Stoppton
- Blockweise Aufnahme auf Datenträger und blockweise Audioverarbeitung für lange Aufnahmen
- Automatischer Sicherheitsstopp, bevor die Systemplatte vollständig gefüllt wird
- Modellgrößen/Qualitätsstufen, Erkennungsmodus, Beam Size, CPU/GPU und Compute Type
- Schneller Standardpfad mit einem Hauptdurchlauf für normale Push-to-talk-Aufnahmen
- Benutzerdefinierter lokaler Modellordner
- Manipulationserkennung verwalteter Modelle

## Profile

Manuelle oder automatisch programmbasierte Profile können separat festlegen:

- Programme und Aktivierung
- Primären/sekundären Hotkey und Halten/Umschalten
- Mikrofon
- Eingabe-, bevorzugte und Zielsprachen
- Sprach-Zielregeln und Zwischensprache
- Übersetzung und Original+Übersetzung
- Ausgabemodus, Auto-Enter und Zwischenablageverhalten
- Textbefehle, Satzzeichen, Füllwörter, Zahlen und Stil
- Modell, lokaler Modellordner, CPU/GPU, Compute Type und Beam Size
- Rauschminderung, Normalisierung, Verstärkung, Stille-Stopp und Zeitlimit
- Verlauf, Audioablage und privater Modus

## Datenschutz und Sicherheit

- Standardmäßig wird bearbeitetes Audio gelöscht
- Optional verschlüsselte Audioablage als authentifizierte `.lva`-Datei
- Verschlüsselter Verlauf mit Suche, Bearbeitung, Kopieren, CSV-/JSON-Export, Audioexport, Einzel-/Gesamtlöschung und Statistiken
- Aufbewahrungsfristen und Maximalzahl werden beim Start, nach Diktaten, nach Einstellungsänderungen und im Dauerbetrieb alle sechs Stunden angewendet
- Privater Modus ohne Verlauf und Audioablage
- AES-256-GCM für sensible Inhalte und Manipulationserkennung
- Optionaler PIN mit Scrypt und über Neustarts anhaltender Fehlversuchsbegrenzung
- Windows-DPAPI für den lokalen Schlüssel; Linux-Keyring, soweit verfügbar, sonst geschützte Benutzerdatei
- SQLite mit Fremdschlüsseln, deaktiviertem vertrauenswürdigem Schema, Secure Delete und temporären Daten im Speicher
- Parametrisiertes SQL, Größenlimits, Pfad-/Symlink-/Archivschutz und sicherer CSV-Export
- Einzelinstanzschutz und kleine, erlaubte lokale Befehlsliste
- Kein versteckter Netzwerkdownload im Diktierpfad

Das genaue Bedrohungsmodell steht in `docs/THREAT_MODEL.md` und der Sicherheitsbericht in `SECURITY_REVIEW.md`.

## Oberfläche

LocalVoice verwendet ein modernes Pop-up-/Dialogsystem mit wenig Scrollen, Dark/Light/System-Design, System-Tray, optionalem Autostart, minimiertem Start, Minimieren/Schließen in den Tray, Hauptübersicht, Verlauf, Statistiken, Wörterbuch, Profile, Modellmanager, Einstellungen, Datenschutz, Hilfe und Info.

## Windows starten

Unterstützte Release-Python-Versionen: 3.11 oder 3.12.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Setup-Windows.ps1
.\scripts\Start-Windows.ps1
```

Alternativ `START_LOCALVOICE_WINDOWS.bat` doppelt anklicken.

## Windows-Pakete bauen

Zusätzlich wird Inno Setup 6 benötigt:

```powershell
.\scripts\Build-Windows.ps1
```

Zielausgaben:

- `release\windows\LocalVoice-Setup-Windows-x64.exe`
- `release\windows\LocalVoice-Windows-x64-Portable.zip`
- SHA-256-Prüfsummen, Abhängigkeitsbericht und Signaturstatus

Öffentliche Installer sollten mit einem vertrauenswürdigen Code-Signing-Zertifikat signiert werden. Das Buildskript kennzeichnet unsignierte Pakete.

## Linux starten und bauen

```bash
chmod +x scripts/*.sh installer/linux/*.sh installer/linux/AppRun
./scripts/Setup-Linux.sh
./scripts/Start-Linux.sh
./scripts/Build-Linux.sh
```

Zielausgaben:

- `release/linux/LocalVoice-Linux-x86_64.AppImage`
- `release/linux/LocalVoice-Linux-amd64.deb`
- `release/linux/LocalVoice-Linux-x64-Portable.tar.gz`
- SHA-256-Prüfsummen und Abhängigkeitsbericht

Von Windows aus kann PowerShell den Linux-Build über WSL starten:

```powershell
.\scripts\Build-All.ps1
```

Windows und Linux benötigen getrennte Pakete; eine EXE ist kein Linux-Installer.

## Linux X11 und Wayland

Unter X11 sind globale Tastatur-/Maus-Hotkeys und direkte Texteingabe über die vorgesehenen Werkzeuge möglich. Unter Wayland verwendet LocalVoice für Tastaturkürzel das standardisierte XDG Global Shortcuts Portal und bietet zusätzlich die lokalen Befehle `--start`, `--stop` und `--toggle` für Desktop-Verknüpfungen. Das standardisierte Portal definiert Tastatur-, aber keine Maus-Hotkeys. Direkte Texteingabe kann je nach Desktop zusätzliche Werkzeuge/Berechtigungen benötigen; die Zwischenablage bleibt der sichere Fallback. Automatische Programmprofile sind auf reinem Wayland eingeschränkt, wenn der Desktop das aktive Fremdfenster nicht bereitstellt.

## Ehrlicher Prüfstatus

Im mitgelieferten Quellordner wurden 71 automatisierte Tests, Syntaxprüfung, Übersetzungsprüfung, statischer Sicherheitscheck, Shell-Syntaxprüfung und Workflow-Parsing bestanden. Ein Qt-GUI-Smoke-Test wurde in der aktuellen Prüfumgebung übersprungen, weil PySide6 dort nicht verfügbar ist.

Nicht in dieser Umgebung praktisch geprüft wurden echte Mikrofone, globale Betriebssystem-Hooks, reale Whisper-/Argos-Modelle, GPU, Windows-DPAPI, Desktop-Keyrings, fertige EXE/AppImage/DEB und Zielprogramme. Vor einer öffentlichen Veröffentlichung müssen die nativen Tests aus `docs/TESTING.md` auf echten Windows- und Linux-Systemen durchgeführt werden. Es wird keine Null-Fehler-Garantie behauptet.

## Dauerhafte Reparatur der Oberflächensprache

LocalVoice 1.9.0 vertraut alten Sprachbestätigungen aus fehlerhaften Vorgängerversionen nicht mehr. Auf einem deutschen Windows wird Deutsch vorausgewählt und nach der einmaligen Bestätigung im neuen Schema 3 gespeichert. Diese Wahl bleibt bei späteren Updates und Neuinstallationen erhalten.

Nicht-destruktive Reparatur unter Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Fix-Language-Windows.ps1 -Language de
```
