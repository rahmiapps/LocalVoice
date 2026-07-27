# LocalVoice 2.1.1 – Build- und Prüfstatus

## Veröffentlichungsreife Sprachinitialisierung

- Die Sprachauswahl wird vor dem Hauptfenster ausgeführt.
- Alle Sprachbestätigungen aus Versionen vor 1.9.0 werden genau einmal verworfen.
- Windows-Systemsprache wird über `GetUserDefaultLocaleName` erkannt.
- Nur eine ausdrücklich bestätigte Auswahl wird im neuen Schema 3 gespeichert.
- Eine bestätigte Auswahl bleibt bei Updates und Neuinstallationen erhalten.
- Bei beschädigten oder widersprüchlichen Sprachdaten erscheint automatisch die Auswahl; es wird niemals still auf Chinesisch zurückgefallen.
- Endnutzer benötigen keinen PowerShell-Befehl.

## In dieser Umgebung ausgeführt

- Python-Kompilierung bestanden
- 100 Tests bestanden
- 1 nativer GUI-Test übersprungen, da PySide6 in dieser Umgebung fehlt
- statischer Sicherheits-Audit bestanden
- sechs UI-Sprachen und 341 Übersetzungsschlüssel geprüft
- alte Schema-1- und Schema-2-Sprachdateien als nicht vertrauenswürdig getestet
- bestätigte Schema-3-Auswahl bei simulierter Neuinstallation getestet
- Reihenfolge geprüft: Sprachauswahl vor Konstruktion des Hauptfensters

## Noch auf echtem Windows zu prüfen

Der Buildprozess führt zusätzlich den nativen Paket-Smoke-Test aus. Vor Veröffentlichung sollte der fertige Installer auf einem sauberen Windows-Benutzerkonto einmal in jeder der sechs Sprachen durchgeklickt werden.

## Branding-Integration 2.1.1

- Neues Original-Logo als Multi-Resolution-Windows-ICO, PNG und Linux-SVG eingebunden.
- App-Fenster, Taskleiste, System-Tray, EXE, Desktop- und Startmenü-Verknüpfungen verwenden das neue Logo.
- Windows-Installer verwendet eigene große und kleine LocalVoice-Wizardgrafiken.
- Seitenleisten-Platzhalter „LV“ und Dashboard-Punkt wurden durch die Logo-Grafik ersetzt.
- 102 Tests bestanden; ein nativer Qt-GUI-Smoke-Test wurde in dieser Umgebung mangels PySide6 übersprungen.
