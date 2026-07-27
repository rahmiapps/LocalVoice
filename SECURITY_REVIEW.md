# LocalVoice 2.0.0 – Sicherheitsprüfung

- Sprachcodes werden ausschließlich über eine feste Allowlist akzeptiert.
- Alte, potentiell vergiftete Sprachbestätigungen werden nicht vertraut.
- Sprachdateien werden atomar geschrieben und auf Größe, Schema, Generation, Quelle und Bestätigungsstatus geprüft.
- Beschädigte Hauptsettings werden gesichert und durch validierte Einstellungen ersetzt.
- Die Sprachmigration löscht keine Modelle oder persönlichen Daten.
- Der statische Audit fand keine blockierten Muster für unsichere Deserialisierung, `eval`/`exec`, `shell=True`, eingebettete Secrets oder versteckte Downloads.

Eine absolute Sicherheitsgarantie ist nicht möglich; native Installer-, Mikrofon- und Desktopintegration müssen zusätzlich auf echten Zielsystemen getestet werden.

## Branding-Assets 2.0.0

Alle eingebundenen Bilddateien sind lokale statische Ressourcen. Es werden keine externen URLs, Skripte oder dynamisch geladenen Bildinhalte verwendet.
