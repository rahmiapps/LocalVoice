# LocalVoice – vollständiger Funktionsumfang 2.1.1

## Grundprinzip

- Kostenlos, werbefrei, ohne Konto, ohne Pro-Version und ohne bezahlte API
- Gemeinsame Windows-/Linux-Codebasis mit getrennten nativen Paketen
- Lokal/offline nach ausdrücklicher Modellinstallation
- Keine verdeckten Downloads während des normalen Diktierens

## Aufnahme und globale Steuerung

- Halten: drücken, sprechen, loslassen
- Umschalten: einmal starten, erneut stoppen
- Primärer und sekundärer Hotkey
- Funktionstasten F1–F24, NumPad, Modifier-Kombinationen und unterstützte Maustasten
- Hotkey aktiv/deaktiv, Test/Erfassung, Unterdrückung soweit Plattform erlaubt
- Ein-/Ausschlusslisten für Programme
- Manuelle Start-/Stop-/Toggle-Schaltflächen und lokale CLI-Befehle
- Automatischer Stille-Stopp, Zeitlimit oder unbegrenzt
- Start-/Stoppton
- Blockweises Audioschreiben und blockweise Nachbearbeitung
- Reservierter freier Speicherplatz; automatischer Stopp vor voller Platte

## Aufnahme-Pop-up

- Always-on-top während der Aufnahme
- Pulsierender roter Punkt und roter Statusbalken
- Aufnahmezeit, Audiopegel/Wellenform, erkannte Sprache
- Stoppen und Abbrechen
- Zustände: Aufnahme, Modellladen, Verarbeitung, Übersetzung, Einfügen, Kopieren, Abbruch, Fehler
- Automatisches Ausblenden nach Abschluss
- Aktiver, primärer oder fester Monitor
- Unten rechts, unten Mitte, oben rechts, am Cursor oder benutzerdefiniert
- Skalierung, Transparenz und Verarbeitungssichtbarkeit

## Sprache

- UI: Deutsch, Englisch, Französisch, Italienisch, Spanisch, vereinfachtes Chinesisch
- Erstauswahl der UI-Sprache
- Vollständige mehrsprachige Whisper-Sprachliste
- Automatische Erkennung
- Feste Eingabesprache
- Bevorzugte Sprachen, optionale stärkere Gewichtung der ersten Sprache und Erkennungsschwelle
- Feste Zielsprache
- Sprach-Zielregeln pro erkannter Eingabesprache
- Original plus Übersetzung
- Konfigurierbare Zwischensprache für lokale Übersetzungsrouten

## Textverarbeitung

- Automatische Satzzeichen/Großschreibung optional
- Gesprochene Satzzeichen, Zeile, Absatz, Anführungszeichen und letzten Satz löschen
- Füllwörter optional entfernen
- Unmittelbare doppelte Wörter bereinigen
- Zahlen als Ziffern, einschließlich größerer Zahlen in DE/EN/FR/IT/ES/ZH
- Neutraler, Chat- und E-Mail-Stil
- Verschlüsseltes persönliches Wörterbuch
- Gewünschte Schreibweise, Sprache, Groß-/Kleinschreibung und Nicht-übersetzen-Regel

## Ausgabe

- In das aktive Programm einfügen, ohne den maximierten Windows-Fensterzustand zu verändern
- Nur Zwischenablage
- Vorschau und Bearbeitung vor Ausgabe
- Nur innerhalb LocalVoice
- Optional Enter senden
- Vorherige Text-Zwischenablage wiederherstellen
- Zeitgesteuertes Leeren
- Sicherer Zwischenablage-Fallback, wenn direkte Eingabe nicht möglich ist

## Audio und Modelle

- Mikrofonwahl, Pegeltest und Testaufnahme
- Manuelle und automatische Verstärkung, Normalisierung, DC-Korrektur und sanfte Rauschabsenkung
- Tiny/Base/Small/Medium/Large/Turbo-Qualitätsstufen laut Konfiguration
- Schnell/Ausgewogen/Genau; Ausgewogen nutzt für normale Push-to-talk-Aufnahmen einen Hauptdurchlauf
- CPU/GPU, Compute Type und Beam Size
- Verwaltete lokale Modelle oder benutzerdefinierter Modellordner
- Vollständige Dateihashes verwalteter Modelle
- Explizite Installation/Entfernung im Modellmanager
- Lokale Argos-Translate-Pakete und direkte/mehrstufige Routen

## Profile

- Beliebig viele lokale Profile
- Manueller Hotkey oder automatische Programmzuordnung
- Alle relevanten Sprach-, Ausgabe-, Text-, Audio-, Modell- und Datenschutzeinstellungen pro Profil
- Verschlüsselte Profildaten

## Verlauf und Datenschutz

- Verschlüsselte Transkriptionen und Zielprogramme
- Suche, Kopieren, Bearbeiten, Einzel-/Gesamtlöschung
- CSV/JSON-Export und entschlüsselter Audioexport
- Lokale Statistiken
- Maximalzahl, Text-Aufbewahrung und Audio-Aufbewahrung
- Prüfung beim Start, nach Diktaten, nach Einstellungen und alle sechs Stunden
- Optionale verschlüsselte `.lva`-Audioablage
- Audio standardmäßig nach Verarbeitung löschen
- Privater Modus ohne Verlauf/Audio
- Optionaler PIN mit Fehlversuchsbegrenzung

## Oberfläche und Plattform

- Pop-up-/Dialogsystem mit wenig Scrollen
- Dark, Light oder System
- System-Tray, Autostart, minimierter Start, Minimieren/Schließen in Tray
- Einzelinstanzschutz
- Windows X64 Installer und Portable ZIP
- Linux X64 AppImage, DEB und Portable TAR.GZ
- Build-All via PowerShell + WSL
- X11-Hotkeys und Wayland-XDG-Portal für Tastaturkürzel

## Qualität und Sicherheit

- Validierung aller Einstellungen, Sprachen, Pfade, Archive, Modelle, Hotkeys und Programmmuster
- AES-256-GCM, Scrypt, DPAPI/Keyring/Fallbackdatei
- Parametrisiertes SQL und gehärtete SQLite-Pragmas
- CSV-Formel-Injektionsschutz
- Größen-/Dateianzahl-/Symlink-/Pfadtraversal-Schutz
- Keine gefährliche Shellausführung oder unsichere Deserialisierung
- Dependency-Audit und Checksummen im Release-Build
- 71 bestandene automatisierte Tests; nativer GUI-/Hardware-/Installer-Test auf Zielsystemen weiterhin verpflichtend
