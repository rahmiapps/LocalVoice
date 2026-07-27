# LocalVoice – Änderungsverlauf

## 2.1.1 – 2026-07-27

- Neues LocalVoice-Logo vollständig in App, EXE, Taskleiste, Tray, Installer, Desktop-/Startmenü-Verknüpfungen und Linux-Pakete integriert.
- Das LV-Platzhalterbild in der Seitenleiste wurde durch das echte Logo ersetzt.
- Der Aufnahmebereich im Dashboard verwendet jetzt das Logo anstelle des weißen Punkts.
- Eigene Installer-Grafiken für den Windows-Installationsassistenten ergänzt.

## 1.9.0 – 2026-07-27

- Publication-ready language bootstrap: the chooser runs before the main window exists.
- All pre-1.9 language confirmations are ignored exactly once.
- Windows display-language detection now uses GetUserDefaultLocaleName.
- Confirmed choices are stored in schema/generation 3 and survive reinstallations.
- No end user needs PowerShell to select or repair the interface language.


## 1.8.0 – 2026-07-26

- alte fehlerhafte Sprachbestätigungen im Schema 1 werden nicht mehr übernommen
- deutsches Windows wählt Deutsch vor und zeigt die Sprachauswahl einmal erneut
- bestätigte Sprache wird atomar im neuen Schema 2 gespeichert und bei jedem Start validiert
- Neuinstallation mit beibehaltenen App-Daten übernimmt nur eine nachweislich explizite Nutzerwahl
- nicht-destruktiver Windows-Reparaturbefehl für die Oberfläche hinzugefügt
- Live-Transkription und Medium-Schnellpfad aus 1.7 bleiben vollständig enthalten
- 97 automatisierte Tests

## 1.6.0 – 2026-07-26

- dauerhafte Reparatur der Oberflächensprache und Neuinstallationslogik
- automatische Mikrofonverstärkung, Fensterzustandsschutz und UI-Größenmigration
