# LocalVoice 2.1.1 – Funktionsaudit

## Aufnahme und Audio

- Gedrückthalten und Umschaltmodus sind getrennt verdrahtet.
- Aufnahme wird blockweise in eine private temporäre WAV-Datei geschrieben.
- Native Mikrofon-Samplerate wird geprüft.
- Lange Aufnahmen werden nicht vollständig im Arbeitsspeicher gehalten.
- Freier Datenträger wird überwacht.
- Manuelle Verstärkung, Normalisierung und neue automatische Sprachpegel-Verstärkung werden im echten Verarbeitungsweg verwendet.

## Erkennung und Geschwindigkeit

- Normales Diktieren lädt niemals heimlich ein Modell herunter.
- Schnell/Ausgewogen/Genau steuern Dekodierungsaufwand und Wiederholungsprüfungen.
- Ausgewogen verarbeitet normale Push-to-talk-Aufnahmen ohne VAD in einem Hauptdurchlauf.
- Kurze mehrdeutige Aufnahmen können genau einmal mit der ersten bevorzugten Sprache verglichen werden.
- Genau darf zusätzliche Kandidaten und einen VAD-Rettungsdurchlauf verwenden.
- Modell-Vorladen verkürzt die erste Transkription, sofern ein lokales Modell installiert ist.

## Textausgabe

- Das vor Aufnahme aktive Programm wird gespeichert.
- Ein maximiertes Windows-Zielfenster wird beim erneuten Aktivieren nicht auf Normalgröße gesetzt.
- Zwischenablage, direktes Einfügen, Vorschau und LocalVoice-only sind verdrahtet.
- Vorherige Zwischenablage kann wiederhergestellt werden.

## Oberfläche

- Klein, Mittel und Groß sind vorhanden.
- Mittel entspricht der bisherigen großen Darstellung.
- Groß ist eine neue zusätzliche größere Darstellung.
- Alte Groß-Einstellungen werden über eine Schema-Migration einmalig Mittel zugeordnet.
- Bevorzugte Sprachen können als Codes oder über ein suchbares Pop-up gewählt werden.
- Automatische Mikrofonverstärkung und Primärsprachen-Gewichtung sind in App- und Profileinstellungen verfügbar.

## Plattformen

- Windows: portable Ausgabe und Inno-Setup-Installer.
- Linux: AppImage-, DEB- und TAR.GZ-Struktur.
- Windows-, X11- und Wayland-Hotkeypfade bleiben getrennt.
