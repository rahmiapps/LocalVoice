# Sicherheit von LocalVoice

## Sicherheitsmeldungen

Bitte veröffentliche mögliche Sicherheitslücken nicht sofort mit ausnutzbaren Details. Melde sie dem Projektbetreiber mit Version, Betriebssystem, reproduzierbaren Schritten, Auswirkungen und – sofern möglich – einem minimalen Nachweis. Geheimnisse, echte Sprachaufnahmen und persönliche Transkriptionen sollen dabei entfernt werden.

## Sicherheitsprinzipien

- Lokal und offline nach ausdrücklicher Modellinstallation
- Minimale Datenhaltung und Audio standardmäßig löschen
- Authentifizierte Verschlüsselung sensibler Inhalte
- Privater Modus ohne Verlauf/Audio
- Validierte Konfigurationen, Pfade, Archive, Modelle und Befehle
- Keine impliziten Downloads im Diktierpfad
- Abbruch statt Weiterbau bei fehlgeschlagenen Release-Prüfungen

## Verantwortungsgrenze

LocalVoice schützt nicht vor Administrator/root, kompromittiertem Betriebssystem, Malware im Benutzerkonto, physischem Zugriff auf einen unverschlüsselten Datenträger oder bewusstem Export/Einfügen in fremde Anwendungen. Für sensible Geräte sind Betriebssystemupdates, Vollverschlüsselung, sicherer Benutzerzugang und signierte Releases erforderlich.

Ausführliche Informationen stehen in `SECURITY_REVIEW.md` und `docs/THREAT_MODEL.md`.
