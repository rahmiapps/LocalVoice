# LocalVoice 2.0.0 – Funktionsaudit

## Sprachstart und Neuinstallation

1. Frische Installation ohne Benutzerdaten: Systemsprachen-Vorauswahl, ausdrückliche Bestätigung erforderlich.
2. Update von 1.8.x mit fehlerhaft bestätigtem `zh`: alte Bestätigung wird verworfen, Auswahl erscheint vor dem Hauptfenster.
3. Neuinstallation mit bestätigter 1.9.0-Auswahl: dieselbe Sprache wird übernommen.
4. Beschädigte oder ungültige Sprachdatei: sichere Auswahl statt stiller Fallback auf Chinesisch.
5. `--choose-language`: erneute Auswahl ohne Löschen von Modellen, Verlauf, Wörterbuch oder Profilen.
6. Unterstützte UI-Sprachen: Deutsch, Englisch, Französisch, Italienisch, Spanisch und vereinfachtes Chinesisch.

Die übrigen Funktionen des vollständigen 1.8.0-Funktionsumfangs bleiben enthalten.

## Branding 2.0.0

Das Logo ist an App-, Installer-, Desktop-, Startmenü-, Tray-, Seitenleisten- und Dashboard-Stellen verdrahtet. Automatische Tests prüfen alle erforderlichen Assets und Verweise.
