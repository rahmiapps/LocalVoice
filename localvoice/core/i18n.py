from __future__ import annotations

from .languages import WHISPER_LANGUAGE_NAMES



LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
    "fr": "Français",
    "it": "Italiano",
    "es": "Español",
    "zh": "简体中文",
}

SPEECH_LANGUAGES = {"auto": "Auto", **WHISPER_LANGUAGE_NAMES}


_EN = {
    "app_subtitle": "Private speech. Instant text.",
    "start": "Start",
    "stop": "Stop",
    "cancel": "Cancel",
    "save": "Save",
    "close": "Close",
    "back": "Back",
    "next": "Next",
    "finish": "Finish",
    "add": "Add",
    "edit": "Edit",
    "delete": "Delete",
    "copy": "Copy",
    "export": "Export",
    "search": "Search",
    "refresh": "Refresh",
    "install": "Install",
    "remove": "Remove",
    "test": "Test",
    "enabled": "Enabled",
    "disabled": "Disabled",
    "yes": "Yes",
    "no": "No",
    "dashboard": "Dashboard",
    "history": "History",
    "dictionary": "Dictionary",
    "profiles": "Profiles",
    "models": "Models",
    "settings": "Settings",
    "privacy": "Privacy",
    "help": "Help",
    "about": "About LocalVoice",
    "ready": "Ready",
    "recording": "Recording",
    "recording_running": "Recording in progress",
    "processing": "Recognizing speech…",
    "translating": "Translating text…",
    "inserted": "Text inserted",
    "copied": "Text copied",
    "cancelled": "Recording cancelled",
    "error": "Error",
    "microphone_error": "The microphone could not be opened.",
    "model_missing": "The selected speech model is not available yet.",
    "translation_model_missing": "No local translation model is installed for this language pair.",
    "active_hotkey": "Active hotkey",
    "hotkey_enabled": "Enable global recording hotkey",
    "suppress_hotkey": "Prevent the recording key from typing in the active application",
    "secondary_hotkey": "Alternative hotkey",
    "hotkey_include_apps": "Hotkey only in these applications",
    "hotkey_exclude_apps": "Exclude these applications",
    "recording_mode": "Recording mode",
    "hold_mode": "Hold the key",
    "toggle_mode": "Press once to start, press again to stop",
    "input_language": "Spoken language",
    "auto_detect": "Detect automatically",
    "preferred_languages": "Preferred languages",
    "target_language": "Written language",
    "same_as_spoken": "Same as spoken",
    "show_original_translation": "Show original and translation",
    "output_mode": "Text output",
    "insert_active_app": "Insert into the active application",
    "clipboard_only": "Copy to clipboard only",
    "preview_first": "Show preview before inserting",
    "localvoice_only": "Keep inside LocalVoice",
    "auto_enter": "Press Enter after inserting",
    "microphone": "Microphone",
    "microphone_test": "Microphone test",
    "level": "Level",
    "audio": "Audio",
    "noise_reduction": "Noise reduction",
    "normalize_audio": "Normalize volume",
    "microphone_gain": "Microphone amplification",
    "silence_stop": "Stop automatically after silence",
    "silence_seconds": "Seconds of silence",
    "max_duration": "Maximum recording duration",
    "start_stop_sound": "Start and stop sounds",
    "speech": "Speech recognition",
    "model_quality": "Model quality",
    "local_model_path": "Local model path",
    "translation_enabled": "Enable local translation",
    "detection_threshold": "Language-detection preview threshold",
    "very_fast": "Very fast",
    "balanced": "Balanced",
    "accurate": "Accurate",
    "maximum_accuracy": "Maximum accuracy",
    "compute_device": "Processing device",
    "automatic": "Automatic",
    "cpu": "CPU",
    "gpu": "GPU",
    "spoken_commands": "Recognize spoken punctuation and commands",
    "remove_fillers": "Remove filler words",
    "numbers_digits": "Write spoken numbers as digits",
    "personal_dictionary": "Personal dictionary",
    "spoken_form": "Spoken form",
    "written_form": "Written form",
    "never_translate": "Never translate",
    "case_sensitive": "Case-sensitive",
    "profile_name": "Profile name",
    "writing_style": "Writing style",
    "neutral": "Neutral",
    "email_mode": "E-mail",
    "chat_mode": "Chat",
    "code_mode": "Programming",
    "applications": "Applications",
    "app_profiles_hint": "Comma-separated executable names, for example: chrome.exe, code",
    "auto_profile": "Switch profiles automatically for applications",
    "new_profile": "New profile",
    "default_profile": "Default profile",
    "overlay": "Recording pop-up",
    "overlay_screen": "Monitor",
    "active_monitor": "Active monitor",
    "primary_monitor": "Primary monitor",
    "overlay_position": "Position",
    "bottom_right": "Bottom right",
    "bottom_center": "Bottom center",
    "top_right": "Top right",
    "near_cursor": "Near mouse pointer",
    "custom_position": "Custom position",
    "opacity": "Opacity",
    "size": "Size",
    "appearance": "Appearance",
    "theme": "Theme",
    "dark": "Dark",
    "light": "Light",
    "system": "System",
    "app_language": "Application language",
    "startup": "Startup",
    "autostart": "Start LocalVoice with the computer",
    "start_minimized": "Start minimized",
    "minimize_tray": "Minimize to system tray",
    "close_tray": "Keep running in tray when the window is closed",
    "storage": "Storage",
    "save_history": "Save transcription history locally",
    "save_audio": "Keep audio recordings",
    "private_mode": "Private mode: save nothing",
    "retention": "Automatically delete history after",
    "never": "Never",
    "days": "days",
    "clipboard_clear": "Clear clipboard after",
    "seconds": "seconds",
    "pin_protection": "PIN protection",
    "set_pin": "Set PIN",
    "remove_pin": "Remove PIN",
    "unlock": "Unlock",
    "pin": "PIN",
    "confirm_pin": "Confirm PIN",
    "wrong_pin": "The PIN is incorrect.",
    "pin_mismatch": "The PIN entries do not match.",
    "local_only": "All speech, text, history and models stay on this device.",
    "no_api": "No account, no API fees, no advertising and no Pro version.",
    "first_language_title": "Choose your application language",
    "first_language_text": "Every menu, pop-up and message will use this language.",
    "onboarding_privacy_title": "Your voice stays private",
    "onboarding_privacy_text": "LocalVoice processes recordings locally. Audio is deleted after transcription unless you explicitly enable storage.",
    "onboarding_microphone_title": "Choose your microphone",
    "onboarding_hotkey_title": "Choose how recording starts",
    "onboarding_language_title": "Choose speech and output languages",
    "onboarding_output_title": "Choose where text appears",
    "onboarding_model_title": "Choose local recognition quality",
    "onboarding_done_title": "LocalVoice is ready",
    "onboarding_done_text": "Use your selected key anywhere to dictate privately.",
    "record_now": "Record now",
    "last_transcription": "Last transcription",
    "words": "words",
    "detected_language": "Detected language",
    "language_probability": "Language confidence",
    "duration": "Duration",
    "date": "Date",
    "target_app": "Target application",
    "original": "Original",
    "translation": "Translation",
    "no_history": "No transcriptions have been saved yet.",
    "delete_selected": "Delete selected",
    "delete_all": "Delete all",
    "confirm_delete_all": "Delete the complete local history?",
    "export_complete": "Export completed.",
    "model_manager": "Local model manager",
    "whisper_models": "Speech recognition models",
    "translation_models": "Translation models",
    "download_on_use": "The selected model is downloaded once and then works offline.",
    "installed": "Installed",
    "not_installed": "Not installed",
    "source_language": "Source language",
    "destination_language": "Destination language",
    "install_pair": "Install language pair",
    "translation_route_hint": "When no direct model exists, LocalVoice can translate through an installed intermediate language such as English.",
    "wayland_warning": "On some Linux Wayland desktops, automatic pasting requires ydotool. Clipboard output always remains available.",
    "hotkey_hint": "Function keys such as F8 or F9 are recommended because they do not type a visible character.",
    "test_recording": "Test recording",
    "test_success": "The microphone is working.",
    "open_data_folder": "Open local data folder",
    "reset_settings": "Reset settings",
    "version": "Version",
    "license": "Free and open source",
    "about_text": "LocalVoice turns speech into text and can translate it locally on Windows and Linux.",
    "help_hold": "Hold mode: keep the hotkey pressed while speaking and release it to finish.",
    "help_toggle": "Toggle mode: press once to begin and press the same key again to finish.",
    "help_commands": "Examples: say 'period', 'comma', 'new line' or their equivalent in your spoken language.",
    "status_model_loading": "Loading local model…",
    "status_no_speech": "No speech was detected.",
    "status_saved": "Saved locally",
    "preview": "Preview",
    "insert": "Insert",
    "apply": "Apply",
    "language_pair_installed": "The local translation model was installed.",
    "download_failed": "The download or installation failed.",
    "hotkey_conflict": "This hotkey is already being used by LocalVoice.",
    "recording_too_short": "The recording was too short.",
    "translation_disabled": "Translation is disabled in settings.",
}

_DE = {
    "app_subtitle": "Private Sprache. Sofortiger Text.", "start": "Start", "stop": "Stopp", "cancel": "Abbrechen", "save": "Speichern", "close": "Schließen", "back": "Zurück", "next": "Weiter", "finish": "Fertigstellen", "add": "Hinzufügen", "edit": "Bearbeiten", "delete": "Löschen", "copy": "Kopieren", "export": "Exportieren", "search": "Suchen", "refresh": "Aktualisieren", "install": "Installieren", "remove": "Entfernen", "test": "Testen", "enabled": "Aktiviert", "disabled": "Deaktiviert", "yes": "Ja", "no": "Nein",
    "dashboard": "Start", "history": "Verlauf", "dictionary": "Wörterbuch", "profiles": "Profile", "models": "Modelle", "settings": "Einstellungen", "privacy": "Datenschutz", "help": "Hilfe", "about": "Über LocalVoice", "ready": "Bereit", "recording": "Aufnahme", "recording_running": "Aufnahme läuft", "processing": "Sprache wird erkannt …", "translating": "Text wird übersetzt …", "inserted": "Text eingefügt", "copied": "Text kopiert", "cancelled": "Aufnahme abgebrochen", "error": "Fehler", "microphone_error": "Das Mikrofon konnte nicht geöffnet werden.", "model_missing": "Das ausgewählte Sprachmodell ist noch nicht verfügbar.", "translation_model_missing": "Für dieses Sprachpaar ist kein lokales Übersetzungsmodell installiert.",
    "active_hotkey": "Aktive Aufnahmetaste", "secondary_hotkey": "Alternative Aufnahmetaste", "hotkey_include_apps": "Hotkey nur in diesen Programmen", "hotkey_exclude_apps": "Diese Programme ausschließen", "recording_mode": "Aufnahmemodus", "hold_mode": "Taste gedrückt halten", "toggle_mode": "Einmal drücken zum Starten, erneut drücken zum Stoppen", "input_language": "Gesprochene Sprache", "auto_detect": "Automatisch erkennen", "preferred_languages": "Bevorzugte Sprachen", "target_language": "Geschriebene Sprache", "same_as_spoken": "Wie gesprochen", "show_original_translation": "Original und Übersetzung anzeigen", "output_mode": "Textausgabe", "insert_active_app": "In das aktive Programm einfügen", "clipboard_only": "Nur in die Zwischenablage kopieren", "preview_first": "Vor dem Einfügen Vorschau zeigen", "localvoice_only": "Nur in LocalVoice behalten", "auto_enter": "Nach dem Einfügen Enter drücken",
    "microphone": "Mikrofon", "microphone_test": "Mikrofontest", "level": "Pegel", "audio": "Audio", "noise_reduction": "Rauschunterdrückung", "normalize_audio": "Lautstärke normalisieren", "silence_stop": "Nach Stille automatisch stoppen", "silence_seconds": "Sekunden Stille", "max_duration": "Maximale Aufnahmedauer", "start_stop_sound": "Start- und Stoppton", "speech": "Spracherkennung", "model_quality": "Modellqualität", "local_model_path": "Lokaler Modellpfad", "translation_enabled": "Lokale Übersetzung aktivieren", "detection_threshold": "Vorschaugrenze der Spracherkennung", "very_fast": "Sehr schnell", "balanced": "Ausgewogen", "accurate": "Genau", "maximum_accuracy": "Maximale Genauigkeit", "compute_device": "Verarbeitungsgerät", "automatic": "Automatisch", "cpu": "CPU", "gpu": "GPU", "spoken_commands": "Gesprochene Satzzeichen und Befehle erkennen", "remove_fillers": "Füllwörter entfernen", "numbers_digits": "Gesprochene Zahlen als Ziffern schreiben",
    "personal_dictionary": "Persönliches Wörterbuch", "spoken_form": "Gesprochene Form", "written_form": "Gewünschte Schreibweise", "never_translate": "Nie übersetzen", "case_sensitive": "Groß-/Kleinschreibung beachten", "profile_name": "Profilname", "writing_style": "Schreibstil", "neutral": "Neutral", "email_mode": "E-Mail", "chat_mode": "Chat", "code_mode": "Programmierung", "applications": "Programme", "app_profiles_hint": "Kommagetrennte Programmnamen, zum Beispiel: chrome.exe, code", "auto_profile": "Profile automatisch für Programme wechseln", "new_profile": "Neues Profil", "default_profile": "Standardprofil",
    "overlay": "Aufnahme-Pop-up", "overlay_screen": "Monitor", "active_monitor": "Aktiver Monitor", "primary_monitor": "Hauptmonitor", "overlay_position": "Position", "bottom_right": "Unten rechts", "bottom_center": "Unten mittig", "top_right": "Oben rechts", "near_cursor": "In der Nähe des Mauszeigers", "custom_position": "Eigene Position", "opacity": "Transparenz", "size": "Größe", "appearance": "Darstellung", "theme": "Design", "dark": "Dunkel", "light": "Hell", "system": "System", "app_language": "App-Sprache", "startup": "Systemstart", "autostart": "LocalVoice mit dem Computer starten", "start_minimized": "Minimiert starten", "minimize_tray": "In den Infobereich minimieren", "close_tray": "Beim Schließen im Infobereich weiterlaufen",
    "storage": "Speicherung", "save_history": "Transkriptionsverlauf lokal speichern", "save_audio": "Audioaufnahmen behalten", "private_mode": "Privater Modus: nichts speichern", "retention": "Verlauf automatisch löschen nach", "never": "Nie", "days": "Tagen", "clipboard_clear": "Zwischenablage leeren nach", "seconds": "Sekunden", "pin_protection": "PIN-Schutz", "set_pin": "PIN festlegen", "remove_pin": "PIN entfernen", "unlock": "Entsperren", "pin": "PIN", "confirm_pin": "PIN bestätigen", "wrong_pin": "Die PIN ist falsch.", "pin_mismatch": "Die PIN-Eingaben stimmen nicht überein.", "local_only": "Alle Sprachaufnahmen, Texte, Verläufe und Modelle bleiben auf diesem Gerät.", "no_api": "Kein Konto, keine API-Kosten, keine Werbung und keine Pro-Version.",
    "first_language_title": "Wähle deine App-Sprache", "first_language_text": "Alle Menüs, Pop-ups und Meldungen werden vollständig in dieser Sprache angezeigt.", "onboarding_privacy_title": "Deine Stimme bleibt privat", "onboarding_privacy_text": "LocalVoice verarbeitet Aufnahmen lokal. Audio wird nach der Transkription gelöscht, sofern du die Speicherung nicht ausdrücklich aktivierst.", "onboarding_microphone_title": "Wähle dein Mikrofon", "onboarding_hotkey_title": "Lege fest, wie die Aufnahme startet", "onboarding_language_title": "Wähle Sprach- und Ausgabesprache", "onboarding_output_title": "Lege fest, wo der Text erscheint", "onboarding_model_title": "Wähle die lokale Erkennungsqualität", "onboarding_done_title": "LocalVoice ist bereit", "onboarding_done_text": "Nutze deine gewählte Taste überall, um privat zu diktieren.",
    "record_now": "Jetzt aufnehmen", "last_transcription": "Letzte Transkription", "words": "Wörter", "detected_language": "Erkannte Sprache", "language_probability": "Spracherkennungs-Sicherheit", "duration": "Dauer", "date": "Datum", "target_app": "Zielprogramm", "original": "Original", "translation": "Übersetzung", "no_history": "Es wurden noch keine Transkriptionen gespeichert.", "delete_selected": "Ausgewählte löschen", "delete_all": "Alles löschen", "confirm_delete_all": "Den vollständigen lokalen Verlauf löschen?", "export_complete": "Export abgeschlossen.",
    "model_manager": "Lokaler Modellmanager", "whisper_models": "Spracherkennungsmodelle", "translation_models": "Übersetzungsmodelle", "download_on_use": "Das ausgewählte Modell wird einmal heruntergeladen und funktioniert danach offline.", "installed": "Installiert", "not_installed": "Nicht installiert", "source_language": "Ausgangssprache", "destination_language": "Zielsprache", "install_pair": "Sprachpaar installieren", "translation_route_hint": "Wenn kein direktes Modell existiert, kann LocalVoice über eine installierte Zwischensprache wie Englisch übersetzen.", "wayland_warning": "Unter einigen Linux-Wayland-Oberflächen benötigt das automatische Einfügen ydotool. Die Zwischenablage funktioniert immer.", "hotkey_hint": "Funktionstasten wie F8 oder F9 werden empfohlen, weil sie kein sichtbares Zeichen schreiben.", "test_recording": "Testaufnahme", "test_success": "Das Mikrofon funktioniert.", "open_data_folder": "Lokalen Datenordner öffnen", "reset_settings": "Einstellungen zurücksetzen", "version": "Version", "license": "Kostenlos und Open Source", "about_text": "LocalVoice wandelt Sprache lokal unter Windows und Linux in Text um und kann sie offline übersetzen.", "help_hold": "Halten-Modus: Taste beim Sprechen gedrückt halten und zum Beenden loslassen.", "help_toggle": "Umschaltmodus: einmal zum Starten und dieselbe Taste erneut zum Stoppen drücken.", "help_commands": "Beispiele: Sage „Punkt“, „Komma“, „neue Zeile“ oder den entsprechenden Befehl in deiner Sprache.", "status_model_loading": "Lokales Modell wird geladen …", "status_no_speech": "Es wurde keine Sprache erkannt.", "status_saved": "Lokal gespeichert", "preview": "Vorschau", "insert": "Einfügen", "apply": "Übernehmen", "language_pair_installed": "Das lokale Übersetzungsmodell wurde installiert.", "download_failed": "Download oder Installation fehlgeschlagen.", "hotkey_conflict": "Diese Aufnahmetaste wird bereits von LocalVoice verwendet.", "recording_too_short": "Die Aufnahme war zu kurz.", "translation_disabled": "Die Übersetzung ist in den Einstellungen deaktiviert."
}

# The remaining interface languages intentionally contain every visible key. Wording is concise to keep the UI compact.
_FR = {key: value for key, value in _EN.items()}
_FR.update({
    "app_subtitle":"Voix privée. Texte instantané.","start":"Démarrer","stop":"Arrêter","cancel":"Annuler","save":"Enregistrer","close":"Fermer","back":"Retour","next":"Suivant","finish":"Terminer","add":"Ajouter","edit":"Modifier","delete":"Supprimer","copy":"Copier","export":"Exporter","search":"Rechercher","refresh":"Actualiser","install":"Installer","remove":"Retirer","test":"Tester","enabled":"Activé","disabled":"Désactivé","yes":"Oui","no":"Non","dashboard":"Accueil","history":"Historique","dictionary":"Dictionnaire","profiles":"Profils","models":"Modèles","settings":"Paramètres","privacy":"Confidentialité","help":"Aide","about":"À propos de LocalVoice","ready":"Prêt","recording":"Enregistrement","recording_running":"Enregistrement en cours","processing":"Reconnaissance de la parole…","translating":"Traduction du texte…","inserted":"Texte inséré","copied":"Texte copié","cancelled":"Enregistrement annulé","error":"Erreur","microphone_error":"Impossible d’ouvrir le microphone.","active_hotkey":"Touche d’enregistrement","recording_mode":"Mode d’enregistrement","hold_mode":"Maintenir la touche","toggle_mode":"Appuyer une fois pour démarrer, puis à nouveau pour arrêter","input_language":"Langue parlée","auto_detect":"Détection automatique","preferred_languages":"Langues préférées","target_language":"Langue écrite","same_as_spoken":"Identique à la langue parlée","show_original_translation":"Afficher l’original et la traduction","output_mode":"Sortie du texte","insert_active_app":"Insérer dans l’application active","clipboard_only":"Copier uniquement dans le presse-papiers","preview_first":"Afficher un aperçu avant insertion","localvoice_only":"Conserver uniquement dans LocalVoice","auto_enter":"Appuyer sur Entrée après insertion","microphone":"Microphone","microphone_test":"Test du microphone","audio":"Audio","noise_reduction":"Réduction du bruit","normalize_audio":"Normaliser le volume","silence_stop":"Arrêter automatiquement après un silence","speech":"Reconnaissance vocale","model_quality":"Qualité du modèle","very_fast":"Très rapide","balanced":"Équilibré","accurate":"Précis","maximum_accuracy":"Précision maximale","automatic":"Automatique","spoken_commands":"Reconnaître la ponctuation et les commandes vocales","remove_fillers":"Supprimer les mots de remplissage","personal_dictionary":"Dictionnaire personnel","spoken_form":"Forme prononcée","written_form":"Orthographe souhaitée","profile_name":"Nom du profil","applications":"Applications","new_profile":"Nouveau profil","overlay":"Fenêtre d’enregistrement","overlay_screen":"Écran","active_monitor":"Écran actif","primary_monitor":"Écran principal","overlay_position":"Position","bottom_right":"En bas à droite","bottom_center":"En bas au centre","top_right":"En haut à droite","near_cursor":"Près du pointeur","appearance":"Apparence","theme":"Thème","dark":"Sombre","light":"Clair","system":"Système","app_language":"Langue de l’application","startup":"Démarrage","autostart":"Lancer LocalVoice avec l’ordinateur","storage":"Stockage","save_history":"Enregistrer l’historique localement","save_audio":"Conserver les enregistrements audio","private_mode":"Mode privé : ne rien enregistrer","pin_protection":"Protection par code PIN","set_pin":"Définir un PIN","remove_pin":"Supprimer le PIN","unlock":"Déverrouiller","pin":"PIN","confirm_pin":"Confirmer le PIN","wrong_pin":"Le PIN est incorrect.","local_only":"La voix, les textes, l’historique et les modèles restent sur cet appareil.","no_api":"Aucun compte, aucun coût d’API, aucune publicité et aucune version Pro.","record_now":"Enregistrer maintenant","last_transcription":"Dernière transcription","words":"mots","detected_language":"Langue détectée","original":"Original","translation":"Traduction","model_manager":"Gestionnaire de modèles locaux","installed":"Installé","not_installed":"Non installé","source_language":"Langue source","destination_language":"Langue cible","install_pair":"Installer la paire de langues","preview":"Aperçu","insert":"Insérer","apply":"Appliquer"
})

_IT = {key: value for key, value in _EN.items()}
_IT.update({
    "app_subtitle":"Voce privata. Testo immediato.","start":"Avvia","stop":"Ferma","cancel":"Annulla","save":"Salva","close":"Chiudi","back":"Indietro","next":"Avanti","finish":"Fine","add":"Aggiungi","edit":"Modifica","delete":"Elimina","copy":"Copia","export":"Esporta","search":"Cerca","refresh":"Aggiorna","install":"Installa","remove":"Rimuovi","test":"Prova","enabled":"Attivato","disabled":"Disattivato","yes":"Sì","no":"No","dashboard":"Home","history":"Cronologia","dictionary":"Dizionario","profiles":"Profili","models":"Modelli","settings":"Impostazioni","privacy":"Privacy","help":"Aiuto","about":"Informazioni su LocalVoice","ready":"Pronto","recording":"Registrazione","recording_running":"Registrazione in corso","processing":"Riconoscimento vocale…","translating":"Traduzione del testo…","inserted":"Testo inserito","copied":"Testo copiato","cancelled":"Registrazione annullata","error":"Errore","microphone_error":"Impossibile aprire il microfono.","active_hotkey":"Tasto di registrazione","recording_mode":"Modalità di registrazione","hold_mode":"Tieni premuto il tasto","toggle_mode":"Premi una volta per iniziare e di nuovo per fermare","input_language":"Lingua parlata","auto_detect":"Rileva automaticamente","preferred_languages":"Lingue preferite","target_language":"Lingua scritta","same_as_spoken":"Uguale alla lingua parlata","show_original_translation":"Mostra originale e traduzione","output_mode":"Uscita testo","insert_active_app":"Inserisci nell’app attiva","clipboard_only":"Copia solo negli appunti","preview_first":"Mostra anteprima prima di inserire","localvoice_only":"Conserva solo in LocalVoice","auto_enter":"Premi Invio dopo l’inserimento","microphone":"Microfono","microphone_test":"Test microfono","audio":"Audio","noise_reduction":"Riduzione del rumore","normalize_audio":"Normalizza volume","silence_stop":"Ferma automaticamente dopo il silenzio","speech":"Riconoscimento vocale","model_quality":"Qualità modello","very_fast":"Molto veloce","balanced":"Bilanciato","accurate":"Preciso","maximum_accuracy":"Massima precisione","automatic":"Automatico","spoken_commands":"Riconosci punteggiatura e comandi vocali","remove_fillers":"Rimuovi parole riempitive","personal_dictionary":"Dizionario personale","spoken_form":"Forma pronunciata","written_form":"Forma scritta","profile_name":"Nome profilo","applications":"Applicazioni","new_profile":"Nuovo profilo","overlay":"Pop-up registrazione","overlay_screen":"Monitor","active_monitor":"Monitor attivo","primary_monitor":"Monitor principale","overlay_position":"Posizione","bottom_right":"In basso a destra","bottom_center":"In basso al centro","top_right":"In alto a destra","near_cursor":"Vicino al puntatore","appearance":"Aspetto","theme":"Tema","dark":"Scuro","light":"Chiaro","system":"Sistema","app_language":"Lingua dell’app","startup":"Avvio","autostart":"Avvia LocalVoice con il computer","storage":"Archiviazione","save_history":"Salva cronologia localmente","save_audio":"Conserva registrazioni audio","private_mode":"Modalità privata: non salvare nulla","pin_protection":"Protezione PIN","set_pin":"Imposta PIN","remove_pin":"Rimuovi PIN","unlock":"Sblocca","pin":"PIN","confirm_pin":"Conferma PIN","wrong_pin":"Il PIN non è corretto.","local_only":"Voce, testi, cronologia e modelli restano su questo dispositivo.","no_api":"Nessun account, nessun costo API, nessuna pubblicità e nessuna versione Pro.","record_now":"Registra ora","last_transcription":"Ultima trascrizione","words":"parole","detected_language":"Lingua rilevata","original":"Originale","translation":"Traduzione","model_manager":"Gestore modelli locali","installed":"Installato","not_installed":"Non installato","source_language":"Lingua sorgente","destination_language":"Lingua di destinazione","install_pair":"Installa coppia linguistica","preview":"Anteprima","insert":"Inserisci","apply":"Applica"
})

_ES = {key: value for key, value in _EN.items()}
_ES.update({
    "app_subtitle":"Voz privada. Texto instantáneo.","start":"Iniciar","stop":"Detener","cancel":"Cancelar","save":"Guardar","close":"Cerrar","back":"Atrás","next":"Siguiente","finish":"Finalizar","add":"Añadir","edit":"Editar","delete":"Eliminar","copy":"Copiar","export":"Exportar","search":"Buscar","refresh":"Actualizar","install":"Instalar","remove":"Quitar","test":"Probar","enabled":"Activado","disabled":"Desactivado","yes":"Sí","no":"No","dashboard":"Inicio","history":"Historial","dictionary":"Diccionario","profiles":"Perfiles","models":"Modelos","settings":"Ajustes","privacy":"Privacidad","help":"Ayuda","about":"Acerca de LocalVoice","ready":"Listo","recording":"Grabación","recording_running":"Grabación en curso","processing":"Reconociendo voz…","translating":"Traduciendo texto…","inserted":"Texto insertado","copied":"Texto copiado","cancelled":"Grabación cancelada","error":"Error","microphone_error":"No se pudo abrir el micrófono.","active_hotkey":"Tecla de grabación","recording_mode":"Modo de grabación","hold_mode":"Mantener pulsada la tecla","toggle_mode":"Pulsar una vez para iniciar y otra para detener","input_language":"Idioma hablado","auto_detect":"Detectar automáticamente","preferred_languages":"Idiomas preferidos","target_language":"Idioma escrito","same_as_spoken":"Igual que el hablado","show_original_translation":"Mostrar original y traducción","output_mode":"Salida de texto","insert_active_app":"Insertar en la aplicación activa","clipboard_only":"Copiar solo al portapapeles","preview_first":"Mostrar vista previa antes de insertar","localvoice_only":"Conservar solo en LocalVoice","auto_enter":"Pulsar Intro después de insertar","microphone":"Micrófono","microphone_test":"Prueba de micrófono","audio":"Audio","noise_reduction":"Reducción de ruido","normalize_audio":"Normalizar volumen","silence_stop":"Detener automáticamente tras silencio","speech":"Reconocimiento de voz","model_quality":"Calidad del modelo","very_fast":"Muy rápido","balanced":"Equilibrado","accurate":"Preciso","maximum_accuracy":"Máxima precisión","automatic":"Automático","spoken_commands":"Reconocer puntuación y comandos de voz","remove_fillers":"Eliminar muletillas","personal_dictionary":"Diccionario personal","spoken_form":"Forma hablada","written_form":"Forma escrita","profile_name":"Nombre del perfil","applications":"Aplicaciones","new_profile":"Nuevo perfil","overlay":"Ventana de grabación","overlay_screen":"Monitor","active_monitor":"Monitor activo","primary_monitor":"Monitor principal","overlay_position":"Posición","bottom_right":"Abajo a la derecha","bottom_center":"Abajo al centro","top_right":"Arriba a la derecha","near_cursor":"Cerca del puntero","appearance":"Apariencia","theme":"Tema","dark":"Oscuro","light":"Claro","system":"Sistema","app_language":"Idioma de la aplicación","startup":"Inicio","autostart":"Iniciar LocalVoice con el equipo","storage":"Almacenamiento","save_history":"Guardar historial localmente","save_audio":"Conservar grabaciones de audio","private_mode":"Modo privado: no guardar nada","pin_protection":"Protección con PIN","set_pin":"Establecer PIN","remove_pin":"Quitar PIN","unlock":"Desbloquear","pin":"PIN","confirm_pin":"Confirmar PIN","wrong_pin":"El PIN es incorrecto.","local_only":"La voz, los textos, el historial y los modelos permanecen en este dispositivo.","no_api":"Sin cuenta, sin costes de API, sin publicidad y sin versión Pro.","record_now":"Grabar ahora","last_transcription":"Última transcripción","words":"palabras","detected_language":"Idioma detectado","original":"Original","translation":"Traducción","model_manager":"Gestor de modelos locales","installed":"Instalado","not_installed":"No instalado","source_language":"Idioma de origen","destination_language":"Idioma de destino","install_pair":"Instalar par de idiomas","preview":"Vista previa","insert":"Insertar","apply":"Aplicar"
})

_ZH = {key: value for key, value in _EN.items()}
_ZH.update({
    "app_subtitle":"私人语音，即时文字。","start":"开始","stop":"停止","cancel":"取消","save":"保存","close":"关闭","back":"返回","next":"下一步","finish":"完成","add":"添加","edit":"编辑","delete":"删除","copy":"复制","export":"导出","search":"搜索","refresh":"刷新","install":"安装","remove":"移除","test":"测试","enabled":"已启用","disabled":"已停用","yes":"是","no":"否","dashboard":"主页","history":"历史记录","dictionary":"词典","profiles":"配置文件","models":"模型","settings":"设置","privacy":"隐私","help":"帮助","about":"关于 LocalVoice","ready":"就绪","recording":"录音","recording_running":"正在录音","processing":"正在识别语音…","translating":"正在翻译文字…","inserted":"文字已插入","copied":"文字已复制","cancelled":"录音已取消","error":"错误","microphone_error":"无法打开麦克风。","active_hotkey":"录音快捷键","recording_mode":"录音模式","hold_mode":"按住按键录音","toggle_mode":"按一次开始，再按一次停止","input_language":"口语语言","auto_detect":"自动检测","preferred_languages":"首选语言","target_language":"输出语言","same_as_spoken":"与口语相同","show_original_translation":"同时显示原文和译文","output_mode":"文字输出","insert_active_app":"插入当前应用","clipboard_only":"仅复制到剪贴板","preview_first":"插入前显示预览","localvoice_only":"仅保存在 LocalVoice 中","auto_enter":"插入后按回车","microphone":"麦克风","microphone_test":"麦克风测试","audio":"音频","noise_reduction":"降噪","normalize_audio":"音量标准化","silence_stop":"静音后自动停止","speech":"语音识别","model_quality":"模型质量","very_fast":"非常快","balanced":"均衡","accurate":"精确","maximum_accuracy":"最高精度","automatic":"自动","spoken_commands":"识别口述标点和命令","remove_fillers":"删除语气词","personal_dictionary":"个人词典","spoken_form":"口述形式","written_form":"目标写法","profile_name":"配置名称","applications":"应用程序","new_profile":"新建配置","overlay":"录音浮窗","overlay_screen":"显示器","active_monitor":"当前显示器","primary_monitor":"主显示器","overlay_position":"位置","bottom_right":"右下角","bottom_center":"底部居中","top_right":"右上角","near_cursor":"鼠标附近","appearance":"外观","theme":"主题","dark":"深色","light":"浅色","system":"跟随系统","app_language":"应用语言","startup":"启动","autostart":"开机启动 LocalVoice","storage":"存储","save_history":"在本地保存转写历史","save_audio":"保留录音文件","private_mode":"隐私模式：不保存任何内容","pin_protection":"PIN 保护","set_pin":"设置 PIN","remove_pin":"移除 PIN","unlock":"解锁","pin":"PIN","confirm_pin":"确认 PIN","wrong_pin":"PIN 不正确。","local_only":"语音、文字、历史记录和模型全部保存在本设备。","no_api":"无需账户、无 API 费用、无广告、无专业版。","record_now":"立即录音","last_transcription":"最近转写","words":"个词","detected_language":"检测到的语言","original":"原文","translation":"译文","model_manager":"本地模型管理器","installed":"已安装","not_installed":"未安装","source_language":"源语言","destination_language":"目标语言","install_pair":"安装语言对","preview":"预览","insert":"插入","apply":"应用"
})


_FR.update({
"model_missing":"Le modèle vocal sélectionné n’est pas encore disponible.","translation_model_missing":"Aucun modèle de traduction local n’est installé pour cette paire de langues.","secondary_hotkey":"Touche alternative","hotkey_include_apps":"Raccourci actif uniquement dans ces applications","hotkey_exclude_apps":"Exclure ces applications","level":"Niveau","silence_seconds":"Secondes de silence","max_duration":"Durée maximale d’enregistrement","start_stop_sound":"Sons de début et de fin","compute_device":"Périphérique de calcul","cpu":"Processeur","gpu":"Carte graphique","numbers_digits":"Écrire les nombres prononcés en chiffres","never_translate":"Ne jamais traduire","case_sensitive":"Respecter la casse","writing_style":"Style d’écriture","neutral":"Neutre","email_mode":"E-mail","chat_mode":"Discussion","code_mode":"Programmation","app_profiles_hint":"Noms d’exécutables séparés par des virgules, par exemple : chrome.exe, code","auto_profile":"Changer automatiquement de profil selon l’application","default_profile":"Profil par défaut","overlay_position":"Position","custom_position":"Position personnalisée","opacity":"Opacité","size":"Taille","start_minimized":"Démarrer réduit","minimize_tray":"Réduire dans la zone de notification","close_tray":"Continuer à fonctionner dans la zone de notification à la fermeture","retention":"Supprimer automatiquement l’historique après","never":"Jamais","days":"jours","clipboard_clear":"Vider le presse-papiers après","seconds":"secondes","pin_mismatch":"Les codes PIN ne correspondent pas.","first_language_title":"Choisissez la langue de l’application","first_language_text":"Tous les menus, fenêtres et messages utiliseront cette langue.","onboarding_privacy_title":"Votre voix reste privée","onboarding_privacy_text":"LocalVoice traite les enregistrements localement. L’audio est supprimé après la transcription sauf si vous activez explicitement sa conservation.","onboarding_microphone_title":"Choisissez votre microphone","onboarding_hotkey_title":"Choisissez comment démarrer l’enregistrement","onboarding_language_title":"Choisissez les langues de parole et de sortie","onboarding_output_title":"Choisissez où le texte apparaît","onboarding_model_title":"Choisissez la qualité de reconnaissance locale","onboarding_done_title":"LocalVoice est prêt","onboarding_done_text":"Utilisez la touche choisie dans n’importe quelle application pour dicter en privé.","language_probability":"Confiance de détection","duration":"Durée","date":"Date","target_app":"Application cible","no_history":"Aucune transcription n’a encore été enregistrée.","delete_selected":"Supprimer la sélection","delete_all":"Tout supprimer","confirm_delete_all":"Supprimer tout l’historique local ?","export_complete":"Exportation terminée.","whisper_models":"Modèles de reconnaissance vocale","translation_models":"Modèles de traduction","download_on_use":"Le modèle choisi est téléchargé une seule fois puis fonctionne hors ligne.","translation_route_hint":"Lorsqu’aucun modèle direct n’existe, LocalVoice peut traduire via une langue intermédiaire installée, comme l’anglais.","wayland_warning":"Sur certains bureaux Linux Wayland, le collage automatique nécessite ydotool. La sortie vers le presse-papiers reste toujours disponible.","hotkey_hint":"Les touches de fonction telles que F8 ou F9 sont recommandées car elles ne saisissent aucun caractère visible.","test_recording":"Enregistrement de test","test_success":"Le microphone fonctionne.","open_data_folder":"Ouvrir le dossier de données locales","reset_settings":"Réinitialiser les paramètres","license":"Gratuit et open source","about_text":"LocalVoice transforme localement la voix en texte et peut la traduire hors ligne sous Windows et Linux.","help_hold":"Mode maintien : gardez la touche enfoncée pendant que vous parlez et relâchez-la pour terminer.","help_toggle":"Mode bascule : appuyez une fois pour commencer puis de nouveau sur la même touche pour terminer.","help_commands":"Exemples : dites « point », « virgule », « nouvelle ligne » ou l’équivalent dans votre langue.","status_model_loading":"Chargement du modèle local…","status_no_speech":"Aucune parole n’a été détectée.","status_saved":"Enregistré localement","language_pair_installed":"Le modèle de traduction local a été installé.","download_failed":"Le téléchargement ou l’installation a échoué.","hotkey_conflict":"Cette touche est déjà utilisée par LocalVoice.","recording_too_short":"L’enregistrement était trop court.","translation_disabled":"La traduction est désactivée dans les paramètres.","local_model_path":"Chemin du modèle local","translation_enabled":"Activer la traduction locale","detection_threshold":"Seuil d’aperçu de détection de langue","microphone_gain":"Amplification du microphone"
})
_IT.update({
"no":"No","privacy":"Privacy","model_missing":"Il modello vocale selezionato non è ancora disponibile.","translation_model_missing":"Non è installato alcun modello di traduzione locale per questa coppia di lingue.","secondary_hotkey":"Tasto alternativo","hotkey_include_apps":"Usa il tasto solo in queste applicazioni","hotkey_exclude_apps":"Escludi queste applicazioni","level":"Livello","silence_seconds":"Secondi di silenzio","max_duration":"Durata massima registrazione","start_stop_sound":"Suoni di avvio e arresto","compute_device":"Dispositivo di elaborazione","cpu":"Processore","gpu":"Scheda grafica","numbers_digits":"Scrivi i numeri pronunciati come cifre","never_translate":"Non tradurre mai","case_sensitive":"Distingui maiuscole e minuscole","writing_style":"Stile di scrittura","neutral":"Neutro","email_mode":"E-mail","chat_mode":"Chat","code_mode":"Programmazione","app_profiles_hint":"Nomi degli eseguibili separati da virgole, per esempio: chrome.exe, code","auto_profile":"Cambia automaticamente profilo in base all’applicazione","default_profile":"Profilo predefinito","overlay_screen":"Monitor","custom_position":"Posizione personalizzata","opacity":"Opacità","size":"Dimensione","start_minimized":"Avvia ridotto a icona","minimize_tray":"Riduci nell’area di notifica","close_tray":"Continua nell’area di notifica quando la finestra viene chiusa","retention":"Elimina automaticamente la cronologia dopo","never":"Mai","days":"giorni","clipboard_clear":"Svuota gli appunti dopo","seconds":"secondi","pin_mismatch":"I PIN non corrispondono.","first_language_title":"Scegli la lingua dell’app","first_language_text":"Tutti i menu, i pop-up e i messaggi useranno questa lingua.","onboarding_privacy_title":"La tua voce resta privata","onboarding_privacy_text":"LocalVoice elabora le registrazioni localmente. L’audio viene eliminato dopo la trascrizione, salvo attivazione esplicita del salvataggio.","onboarding_microphone_title":"Scegli il microfono","onboarding_hotkey_title":"Scegli come avviare la registrazione","onboarding_language_title":"Scegli la lingua parlata e quella di uscita","onboarding_output_title":"Scegli dove deve apparire il testo","onboarding_model_title":"Scegli la qualità del riconoscimento locale","onboarding_done_title":"LocalVoice è pronto","onboarding_done_text":"Usa il tasto scelto in qualsiasi applicazione per dettare in modo privato.","language_probability":"Affidabilità rilevamento lingua","duration":"Durata","date":"Data","target_app":"Applicazione di destinazione","no_history":"Non è stata ancora salvata alcuna trascrizione.","delete_selected":"Elimina selezionati","delete_all":"Elimina tutto","confirm_delete_all":"Eliminare tutta la cronologia locale?","export_complete":"Esportazione completata.","whisper_models":"Modelli di riconoscimento vocale","translation_models":"Modelli di traduzione","download_on_use":"Il modello selezionato viene scaricato una sola volta e poi funziona offline.","translation_route_hint":"Se non esiste un modello diretto, LocalVoice può tradurre tramite una lingua intermedia installata, come l’inglese.","wayland_warning":"Su alcuni desktop Linux Wayland, l’incollaggio automatico richiede ydotool. Gli appunti restano sempre disponibili.","hotkey_hint":"Sono consigliati tasti funzione come F8 o F9 perché non digitano caratteri visibili.","test_recording":"Registrazione di prova","test_success":"Il microfono funziona.","open_data_folder":"Apri cartella dati locale","reset_settings":"Ripristina impostazioni","license":"Gratuito e open source","about_text":"LocalVoice trasforma localmente la voce in testo e può tradurla offline su Windows e Linux.","help_hold":"Modalità pressione: tieni premuto il tasto mentre parli e rilascialo per terminare.","help_toggle":"Modalità interruttore: premi una volta per iniziare e di nuovo lo stesso tasto per terminare.","help_commands":"Esempi: pronuncia «punto», «virgola», «nuova riga» o il comando equivalente nella tua lingua.","status_model_loading":"Caricamento del modello locale…","status_no_speech":"Non è stata rilevata alcuna voce.","status_saved":"Salvato localmente","language_pair_installed":"Il modello di traduzione locale è stato installato.","download_failed":"Download o installazione non riusciti.","hotkey_conflict":"Questo tasto è già utilizzato da LocalVoice.","recording_too_short":"La registrazione era troppo breve.","translation_disabled":"La traduzione è disattivata nelle impostazioni.","local_model_path":"Percorso del modello locale","translation_enabled":"Attiva traduzione locale","detection_threshold":"Soglia di anteprima del rilevamento lingua","microphone_gain":"Amplificazione del microfono"
})
_ES.update({
"no":"No","error":"Error","model_missing":"El modelo de voz seleccionado todavía no está disponible.","translation_model_missing":"No hay ningún modelo de traducción local instalado para este par de idiomas.","secondary_hotkey":"Tecla alternativa","hotkey_include_apps":"Usar la tecla solo en estas aplicaciones","hotkey_exclude_apps":"Excluir estas aplicaciones","level":"Nivel","silence_seconds":"Segundos de silencio","max_duration":"Duración máxima de grabación","start_stop_sound":"Sonidos de inicio y parada","compute_device":"Dispositivo de procesamiento","cpu":"Procesador","gpu":"Tarjeta gráfica","numbers_digits":"Escribir los números hablados como cifras","never_translate":"No traducir nunca","case_sensitive":"Distinguir mayúsculas y minúsculas","writing_style":"Estilo de escritura","neutral":"Neutro","email_mode":"Correo electrónico","chat_mode":"Chat","code_mode":"Programación","app_profiles_hint":"Nombres de ejecutables separados por comas, por ejemplo: chrome.exe, code","auto_profile":"Cambiar automáticamente de perfil según la aplicación","default_profile":"Perfil predeterminado","overlay_screen":"Monitor","custom_position":"Posición personalizada","opacity":"Opacidad","size":"Tamaño","start_minimized":"Iniciar minimizado","minimize_tray":"Minimizar al área de notificación","close_tray":"Seguir funcionando en el área de notificación al cerrar","retention":"Eliminar automáticamente el historial después de","never":"Nunca","days":"días","clipboard_clear":"Vaciar el portapapeles después de","seconds":"segundos","pin_mismatch":"Los PIN no coinciden.","first_language_title":"Elige el idioma de la aplicación","first_language_text":"Todos los menús, ventanas y mensajes usarán este idioma.","onboarding_privacy_title":"Tu voz permanece privada","onboarding_privacy_text":"LocalVoice procesa las grabaciones localmente. El audio se elimina tras la transcripción salvo que actives expresamente su almacenamiento.","onboarding_microphone_title":"Elige el micrófono","onboarding_hotkey_title":"Elige cómo iniciar la grabación","onboarding_language_title":"Elige el idioma hablado y el de salida","onboarding_output_title":"Elige dónde aparece el texto","onboarding_model_title":"Elige la calidad del reconocimiento local","onboarding_done_title":"LocalVoice está listo","onboarding_done_text":"Usa la tecla elegida en cualquier aplicación para dictar de forma privada.","language_probability":"Confianza de detección del idioma","duration":"Duración","date":"Fecha","target_app":"Aplicación de destino","original":"Original","no_history":"Todavía no se ha guardado ninguna transcripción.","delete_selected":"Eliminar seleccionados","delete_all":"Eliminar todo","confirm_delete_all":"¿Eliminar todo el historial local?","export_complete":"Exportación completada.","whisper_models":"Modelos de reconocimiento de voz","translation_models":"Modelos de traducción","download_on_use":"El modelo seleccionado se descarga una sola vez y después funciona sin conexión.","translation_route_hint":"Cuando no existe un modelo directo, LocalVoice puede traducir mediante un idioma intermedio instalado, como el inglés.","wayland_warning":"En algunos escritorios Linux Wayland, el pegado automático requiere ydotool. La salida al portapapeles siempre permanece disponible.","hotkey_hint":"Se recomiendan teclas de función como F8 o F9 porque no escriben ningún carácter visible.","test_recording":"Grabación de prueba","test_success":"El micrófono funciona.","open_data_folder":"Abrir carpeta de datos locales","reset_settings":"Restablecer ajustes","license":"Gratis y de código abierto","about_text":"LocalVoice convierte localmente la voz en texto y puede traducirla sin conexión en Windows y Linux.","help_hold":"Modo mantener: mantén pulsada la tecla mientras hablas y suéltala para terminar.","help_toggle":"Modo alternar: pulsa una vez para comenzar y vuelve a pulsar la misma tecla para terminar.","help_commands":"Ejemplos: di «punto», «coma», «nueva línea» o el comando equivalente en tu idioma.","status_model_loading":"Cargando modelo local…","status_no_speech":"No se detectó ninguna voz.","status_saved":"Guardado localmente","language_pair_installed":"El modelo de traducción local se ha instalado.","download_failed":"La descarga o la instalación han fallado.","hotkey_conflict":"Esta tecla ya está siendo utilizada por LocalVoice.","recording_too_short":"La grabación era demasiado corta.","translation_disabled":"La traducción está desactivada en los ajustes.","local_model_path":"Ruta del modelo local","translation_enabled":"Activar traducción local","detection_threshold":"Umbral de vista previa de detección de idioma","microphone_gain":"Amplificación del micrófono"
})
_ZH.update({
"model_missing":"所选语音模型尚不可用。","translation_model_missing":"尚未为此语言对安装本地翻译模型。","secondary_hotkey":"备用快捷键","hotkey_include_apps":"快捷键仅在这些应用中生效","hotkey_exclude_apps":"排除这些应用","level":"电平","silence_seconds":"静音秒数","max_duration":"最长录音时间","start_stop_sound":"开始和停止提示音","compute_device":"处理设备","cpu":"处理器","gpu":"显卡","numbers_digits":"将口述数字写成阿拉伯数字","never_translate":"永不翻译","case_sensitive":"区分大小写","writing_style":"写作风格","neutral":"中性","email_mode":"电子邮件","chat_mode":"聊天","code_mode":"编程","app_profiles_hint":"用逗号分隔可执行文件名，例如：chrome.exe, code","auto_profile":"根据应用自动切换配置","default_profile":"默认配置","custom_position":"自定义位置","opacity":"透明度","size":"大小","start_minimized":"最小化启动","minimize_tray":"最小化到系统托盘","close_tray":"关闭窗口后继续在托盘运行","retention":"在以下时间后自动删除历史记录","never":"从不","days":"天","clipboard_clear":"在以下时间后清空剪贴板","seconds":"秒","pin_mismatch":"两次输入的 PIN 不一致。","first_language_title":"选择应用语言","first_language_text":"所有菜单、浮窗和消息都将使用此语言。","onboarding_privacy_title":"你的语音保持私密","onboarding_privacy_text":"LocalVoice 在本地处理录音。除非你明确启用保存，否则转写后会删除音频。","onboarding_microphone_title":"选择麦克风","onboarding_hotkey_title":"选择录音启动方式","onboarding_language_title":"选择口语语言和输出语言","onboarding_output_title":"选择文字显示位置","onboarding_model_title":"选择本地识别质量","onboarding_done_title":"LocalVoice 已就绪","onboarding_done_text":"在任何应用中使用所选按键进行私密听写。","language_probability":"语言检测置信度","duration":"时长","date":"日期","target_app":"目标应用","no_history":"尚未保存任何转写记录。","delete_selected":"删除所选项","delete_all":"全部删除","confirm_delete_all":"删除全部本地历史记录吗？","export_complete":"导出完成。","whisper_models":"语音识别模型","translation_models":"翻译模型","download_on_use":"所选模型只需下载一次，之后即可离线工作。","translation_route_hint":"没有直接模型时，LocalVoice 可以通过已安装的中间语言（例如英语）进行翻译。","wayland_warning":"在某些 Linux Wayland 桌面上，自动粘贴需要 ydotool。剪贴板输出始终可用。","hotkey_hint":"建议使用 F8 或 F9 等功能键，因为它们不会输入可见字符。","test_recording":"测试录音","test_success":"麦克风工作正常。","open_data_folder":"打开本地数据文件夹","reset_settings":"重置设置","license":"免费且开源","about_text":"LocalVoice 可在 Windows 和 Linux 上将语音本地转换为文字，并进行离线翻译。","help_hold":"按住模式：说话时保持按键，松开即可结束。","help_toggle":"切换模式：按一次开始，再按同一按键结束。","help_commands":"示例：说“句号”“逗号”“换行”或你所用语言中的对应命令。","status_model_loading":"正在加载本地模型…","status_no_speech":"未检测到语音。","status_saved":"已保存在本地","language_pair_installed":"本地翻译模型已安装。","download_failed":"下载或安装失败。","hotkey_conflict":"此快捷键已被 LocalVoice 使用。","recording_too_short":"录音时间太短。","translation_disabled":"设置中已关闭翻译。","local_model_path":"本地模型路径","translation_enabled":"启用本地翻译","detection_threshold":"语言检测预览阈值","microphone_gain":"麦克风增益"
})

_DE["microphone_gain"] = "Mikrofonverstärkung"
_DE["hotkey_enabled"] = "Globale Aufnahmetaste aktivieren"
_DE["suppress_hotkey"] = "Verhindern, dass die Aufnahmetaste im aktiven Programm geschrieben wird"
_FR["hotkey_enabled"] = "Activer le raccourci global d’enregistrement"
_FR["suppress_hotkey"] = "Empêcher la touche d’enregistrement d’être saisie dans l’application active"
_IT["hotkey_enabled"] = "Attiva il tasto globale di registrazione"
_IT["suppress_hotkey"] = "Impedisci che il tasto di registrazione venga digitato nell’applicazione attiva"
_ES["hotkey_enabled"] = "Activar la tecla global de grabación"
_ES["suppress_hotkey"] = "Evitar que la tecla de grabación se escriba en la aplicación activa"
_ZH["hotkey_enabled"] = "启用全局录音快捷键"
_ZH["suppress_hotkey"] = "防止录音键在当前应用中输入字符"
_FR["microphone_gain"] = "Amplification du microphone"
_IT["microphone_gain"] = "Amplificazione del microfono"
_ES["microphone_gain"] = "Amplificación del micrófono"
_ZH["microphone_gain"] = "麦克风增益"

_TRANSLATIONS = {"en": _EN, "de": _DE, "fr": _FR, "it": _IT, "es": _ES, "zh": _ZH}


def tr(language: str, key: str, **values: object) -> str:
    table = _TRANSLATIONS.get(language, _EN)
    text = table.get(key, _EN.get(key, key))
    try:
        return text.format(**values)
    except (KeyError, ValueError):
        return text


def validate_translations() -> dict[str, list[str]]:
    required = set(_EN)
    return {language: sorted(required - set(table)) for language, table in _TRANSLATIONS.items()}

# Additional security/completeness strings introduced by the full feature audit.
_EN.update({
    "restore_clipboard": "Restore the previous clipboard after inserting",
    "audio_retention": "Automatically delete saved audio after",
    "max_history": "Maximum history entries",
    "compute_type": "Computation precision",
    "translation_bridge": "Preferred intermediate language",
    "edit_history": "Edit transcription",
    "original_text": "Original text",
    "final_text": "Final text",
    "plaintext_export_warning": "Exports are readable, unencrypted files. Save them only in a trusted location.",
    "single_instance": "LocalVoice is already running.",
    "security_file_error": "LocalVoice could not open its security storage. Existing encrypted data was not overwritten.",
    "pin_locked": "Too many incorrect PIN attempts. Try again in {seconds} seconds.",
    "model_offline_required": "Install the selected speech model in the model manager before dictating. Dictation never downloads models automatically.",
    "remove_model": "Remove local model",
    "profile_translation": "Profile translation settings",
    "preferred_languages_hint": "Comma-separated language codes, for example: de, en, fr",
    "audio_saved": "Audio saved locally",
    "history_updated": "History entry updated",
    "clear_audio": "Delete saved audio",
    "confirm_clear_audio": "Delete all locally saved audio recordings?",
    "no_microphones": "No input microphone was found.",
    "invalid_hotkey": "The selected hotkey is invalid.",
    "profile_hotkey_conflict": "This hotkey conflicts with another enabled LocalVoice profile.",
    "export_warning_title": "Unencrypted export",
    "model_installed": "The speech model is installed and ready for offline use.",
    "model_removed": "The local speech model was removed.",
    "translation_package_unavailable": "No downloadable offline translation package is available for this language pair.",
})
_DE.update({
    "restore_clipboard": "Vorherigen Zwischenablageninhalt nach dem Einfügen wiederherstellen",
    "audio_retention": "Gespeicherte Audiodateien automatisch löschen nach",
    "max_history": "Maximale Anzahl Verlaufseinträge",
    "compute_type": "Berechnungsgenauigkeit",
    "translation_bridge": "Bevorzugte Zwischensprache",
    "edit_history": "Transkription bearbeiten",
    "original_text": "Originaltext",
    "final_text": "Endgültiger Text",
    "plaintext_export_warning": "Exporte sind lesbare, unverschlüsselte Dateien. Speichere sie nur an einem vertrauenswürdigen Ort.",
    "single_instance": "LocalVoice wird bereits ausgeführt.",
    "security_file_error": "LocalVoice konnte den Sicherheitsspeicher nicht öffnen. Vorhandene verschlüsselte Daten wurden nicht überschrieben.",
    "pin_locked": "Zu viele falsche PIN-Versuche. Versuche es in {seconds} Sekunden erneut.",
    "model_offline_required": "Installiere das ausgewählte Sprachmodell vor dem Diktieren im Modellmanager. Beim Diktieren werden niemals automatisch Modelle heruntergeladen.",
    "remove_model": "Lokales Modell entfernen",
    "profile_translation": "Übersetzungseinstellungen des Profils",
    "preferred_languages_hint": "Sprachcodes durch Kommas trennen, zum Beispiel: de, en, fr",
    "audio_saved": "Audio lokal gespeichert",
    "history_updated": "Verlaufseintrag aktualisiert",
    "clear_audio": "Gespeicherte Audiodateien löschen",
    "confirm_clear_audio": "Alle lokal gespeicherten Audioaufnahmen löschen?",
    "no_microphones": "Es wurde kein Eingabemikrofon gefunden.",
    "invalid_hotkey": "Die ausgewählte Tastenkombination ist ungültig.",
    "profile_hotkey_conflict": "Diese Tastenkombination kollidiert mit einem anderen aktivierten LocalVoice-Profil.",
    "export_warning_title": "Unverschlüsselter Export",
    "model_installed": "Das Sprachmodell ist installiert und für die Offline-Nutzung bereit.",
    "model_removed": "Das lokale Sprachmodell wurde entfernt.",
    "translation_package_unavailable": "Für dieses Sprachpaar ist kein herunterladbares Offline-Übersetzungspaket verfügbar.",
})
_FR.update({
    "restore_clipboard": "Restaurer le presse-papiers précédent après l’insertion",
    "audio_retention": "Supprimer automatiquement les fichiers audio enregistrés après",
    "max_history": "Nombre maximal d’entrées d’historique",
    "compute_type": "Précision de calcul",
    "translation_bridge": "Langue intermédiaire préférée",
    "edit_history": "Modifier la transcription",
    "original_text": "Texte original",
    "final_text": "Texte final",
    "plaintext_export_warning": "Les exports sont des fichiers lisibles et non chiffrés. Enregistrez-les uniquement dans un emplacement fiable.",
    "single_instance": "LocalVoice est déjà en cours d’exécution.",
    "security_file_error": "LocalVoice n’a pas pu ouvrir son stockage sécurisé. Les données chiffrées existantes n’ont pas été remplacées.",
    "pin_locked": "Trop de tentatives de code PIN incorrectes. Réessayez dans {seconds} secondes.",
    "model_offline_required": "Installez le modèle vocal sélectionné dans le gestionnaire avant de dicter. La dictée ne télécharge jamais de modèle automatiquement.",
    "remove_model": "Supprimer le modèle local",
    "profile_translation": "Paramètres de traduction du profil",
    "preferred_languages_hint": "Codes de langue séparés par des virgules, par exemple : de, en, fr",
    "audio_saved": "Audio enregistré localement",
    "history_updated": "Entrée d’historique mise à jour",
    "clear_audio": "Supprimer les fichiers audio enregistrés",
    "confirm_clear_audio": "Supprimer tous les enregistrements audio locaux ?",
    "no_microphones": "Aucun microphone d’entrée n’a été trouvé.",
    "invalid_hotkey": "Le raccourci sélectionné est invalide.",
    "profile_hotkey_conflict": "Ce raccourci est en conflit avec un autre profil LocalVoice activé.",
    "export_warning_title": "Export non chiffré",
    "model_installed": "Le modèle vocal est installé et prêt pour une utilisation hors ligne.",
    "model_removed": "Le modèle vocal local a été supprimé.",
    "translation_package_unavailable": "Aucun paquet de traduction hors ligne téléchargeable n’est disponible pour cette paire de langues.",
})
_IT.update({
    "restore_clipboard": "Ripristina gli appunti precedenti dopo l’inserimento",
    "audio_retention": "Elimina automaticamente i file audio salvati dopo",
    "max_history": "Numero massimo di voci della cronologia",
    "compute_type": "Precisione di calcolo",
    "translation_bridge": "Lingua intermedia preferita",
    "edit_history": "Modifica trascrizione",
    "original_text": "Testo originale",
    "final_text": "Testo finale",
    "plaintext_export_warning": "Le esportazioni sono file leggibili e non crittografati. Salvale solo in una posizione attendibile.",
    "single_instance": "LocalVoice è già in esecuzione.",
    "security_file_error": "LocalVoice non ha potuto aprire l’archivio di sicurezza. I dati crittografati esistenti non sono stati sovrascritti.",
    "pin_locked": "Troppi tentativi PIN errati. Riprova tra {seconds} secondi.",
    "model_offline_required": "Installa il modello vocale selezionato nel gestore modelli prima di dettare. La dettatura non scarica mai modelli automaticamente.",
    "remove_model": "Rimuovi modello locale",
    "profile_translation": "Impostazioni di traduzione del profilo",
    "preferred_languages_hint": "Codici lingua separati da virgole, ad esempio: de, en, fr",
    "audio_saved": "Audio salvato localmente",
    "history_updated": "Voce della cronologia aggiornata",
    "clear_audio": "Elimina audio salvati",
    "confirm_clear_audio": "Eliminare tutte le registrazioni audio salvate localmente?",
    "no_microphones": "Non è stato trovato alcun microfono di ingresso.",
    "invalid_hotkey": "Il tasto rapido selezionato non è valido.",
    "profile_hotkey_conflict": "Questo tasto rapido è in conflitto con un altro profilo LocalVoice attivo.",
    "export_warning_title": "Esportazione non crittografata",
    "model_installed": "Il modello vocale è installato e pronto per l’uso offline.",
    "model_removed": "Il modello vocale locale è stato rimosso.",
    "translation_package_unavailable": "Non è disponibile alcun pacchetto di traduzione offline scaricabile per questa coppia di lingue.",
})
_ES.update({
    "restore_clipboard": "Restaurar el portapapeles anterior después de insertar",
    "audio_retention": "Eliminar automáticamente el audio guardado después de",
    "max_history": "Número máximo de entradas del historial",
    "compute_type": "Precisión de cálculo",
    "translation_bridge": "Idioma intermedio preferido",
    "edit_history": "Editar transcripción",
    "original_text": "Texto original",
    "final_text": "Texto final",
    "plaintext_export_warning": "Las exportaciones son archivos legibles y sin cifrar. Guárdalas solo en una ubicación de confianza.",
    "single_instance": "LocalVoice ya se está ejecutando.",
    "security_file_error": "LocalVoice no pudo abrir su almacenamiento de seguridad. Los datos cifrados existentes no se sobrescribieron.",
    "pin_locked": "Demasiados intentos de PIN incorrectos. Vuelve a intentarlo en {seconds} segundos.",
    "model_offline_required": "Instala el modelo de voz seleccionado en el gestor antes de dictar. El dictado nunca descarga modelos automáticamente.",
    "remove_model": "Eliminar modelo local",
    "profile_translation": "Ajustes de traducción del perfil",
    "preferred_languages_hint": "Códigos de idioma separados por comas, por ejemplo: de, en, fr",
    "audio_saved": "Audio guardado localmente",
    "history_updated": "Entrada del historial actualizada",
    "clear_audio": "Eliminar audio guardado",
    "confirm_clear_audio": "¿Eliminar todas las grabaciones de audio guardadas localmente?",
    "no_microphones": "No se encontró ningún micrófono de entrada.",
    "invalid_hotkey": "La tecla rápida seleccionada no es válida.",
    "profile_hotkey_conflict": "Esta tecla rápida entra en conflicto con otro perfil LocalVoice habilitado.",
    "export_warning_title": "Exportación sin cifrar",
    "model_installed": "El modelo de voz está instalado y listo para usar sin conexión.",
    "model_removed": "Se eliminó el modelo de voz local.",
    "translation_package_unavailable": "No hay ningún paquete de traducción sin conexión descargable para este par de idiomas.",
})
_ZH.update({
    "restore_clipboard": "插入后恢复之前的剪贴板内容",
    "audio_retention": "在以下时间后自动删除已保存的音频",
    "max_history": "历史记录最大条数",
    "compute_type": "计算精度",
    "translation_bridge": "首选中间语言",
    "edit_history": "编辑转写",
    "original_text": "原始文本",
    "final_text": "最终文本",
    "plaintext_export_warning": "导出文件可直接读取且未加密。请只保存到可信位置。",
    "single_instance": "LocalVoice 已在运行。",
    "security_file_error": "LocalVoice 无法打开安全存储。现有加密数据未被覆盖。",
    "pin_locked": "PIN 错误次数过多。请在 {seconds} 秒后重试。",
    "model_offline_required": "请先在模型管理器中安装所选语音模型。听写时绝不会自动下载模型。",
    "remove_model": "删除本地模型",
    "profile_translation": "配置文件翻译设置",
    "preferred_languages_hint": "使用逗号分隔语言代码，例如：de, en, fr",
    "audio_saved": "音频已保存在本地",
    "history_updated": "历史记录已更新",
    "clear_audio": "删除已保存的音频",
    "confirm_clear_audio": "删除所有本地保存的录音吗？",
    "no_microphones": "未找到输入麦克风。",
    "invalid_hotkey": "所选快捷键无效。",
    "profile_hotkey_conflict": "此快捷键与另一个已启用的 LocalVoice 配置冲突。",
    "export_warning_title": "未加密导出",
    "model_installed": "语音模型已安装，可离线使用。",
    "model_removed": "本地语音模型已删除。",
    "translation_package_unavailable": "此语言对没有可下载的离线翻译包。",
})

_SPEECH_NAMES = {
    "en": {
        "auto":"Automatic", "de":"German", "en":"English", "fr":"French", "it":"Italian", "es":"Spanish", "zh":"Chinese",
        "tr":"Turkish", "ar":"Arabic", "pt":"Portuguese", "nl":"Dutch", "pl":"Polish", "ru":"Russian", "ja":"Japanese", "ko":"Korean",
        "uk":"Ukrainian", "sv":"Swedish", "cs":"Czech", "el":"Greek", "hi":"Hindi", "da":"Danish", "fi":"Finnish", "no":"Norwegian",
        "he":"Hebrew", "id":"Indonesian", "vi":"Vietnamese", "th":"Thai", "ro":"Romanian", "hu":"Hungarian",
    },
    "de": {
        "auto":"Automatisch", "de":"Deutsch", "en":"Englisch", "fr":"Französisch", "it":"Italienisch", "es":"Spanisch", "zh":"Chinesisch",
        "tr":"Türkisch", "ar":"Arabisch", "pt":"Portugiesisch", "nl":"Niederländisch", "pl":"Polnisch", "ru":"Russisch", "ja":"Japanisch", "ko":"Koreanisch",
        "uk":"Ukrainisch", "sv":"Schwedisch", "cs":"Tschechisch", "el":"Griechisch", "hi":"Hindi", "da":"Dänisch", "fi":"Finnisch", "no":"Norwegisch",
        "he":"Hebräisch", "id":"Indonesisch", "vi":"Vietnamesisch", "th":"Thailändisch", "ro":"Rumänisch", "hu":"Ungarisch",
    },
    "fr": {
        "auto":"Automatique", "de":"Allemand", "en":"Anglais", "fr":"Français", "it":"Italien", "es":"Espagnol", "zh":"Chinois",
        "tr":"Turc", "ar":"Arabe", "pt":"Portugais", "nl":"Néerlandais", "pl":"Polonais", "ru":"Russe", "ja":"Japonais", "ko":"Coréen",
        "uk":"Ukrainien", "sv":"Suédois", "cs":"Tchèque", "el":"Grec", "hi":"Hindi", "da":"Danois", "fi":"Finnois", "no":"Norvégien",
        "he":"Hébreu", "id":"Indonésien", "vi":"Vietnamien", "th":"Thaï", "ro":"Roumain", "hu":"Hongrois",
    },
    "it": {
        "auto":"Automatico", "de":"Tedesco", "en":"Inglese", "fr":"Francese", "it":"Italiano", "es":"Spagnolo", "zh":"Cinese",
        "tr":"Turco", "ar":"Arabo", "pt":"Portoghese", "nl":"Olandese", "pl":"Polacco", "ru":"Russo", "ja":"Giapponese", "ko":"Coreano",
        "uk":"Ucraino", "sv":"Svedese", "cs":"Ceco", "el":"Greco", "hi":"Hindi", "da":"Danese", "fi":"Finlandese", "no":"Norvegese",
        "he":"Ebraico", "id":"Indonesiano", "vi":"Vietnamita", "th":"Tailandese", "ro":"Rumeno", "hu":"Ungherese",
    },
    "es": {
        "auto":"Automático", "de":"Alemán", "en":"Inglés", "fr":"Francés", "it":"Italiano", "es":"Español", "zh":"Chino",
        "tr":"Turco", "ar":"Árabe", "pt":"Portugués", "nl":"Neerlandés", "pl":"Polaco", "ru":"Ruso", "ja":"Japonés", "ko":"Coreano",
        "uk":"Ucraniano", "sv":"Sueco", "cs":"Checo", "el":"Griego", "hi":"Hindi", "da":"Danés", "fi":"Finés", "no":"Noruego",
        "he":"Hebreo", "id":"Indonesio", "vi":"Vietnamita", "th":"Tailandés", "ro":"Rumano", "hu":"Húngaro",
    },
    "zh": {
        "auto":"自动", "de":"德语", "en":"英语", "fr":"法语", "it":"意大利语", "es":"西班牙语", "zh":"中文",
        "tr":"土耳其语", "ar":"阿拉伯语", "pt":"葡萄牙语", "nl":"荷兰语", "pl":"波兰语", "ru":"俄语", "ja":"日语", "ko":"韩语",
        "uk":"乌克兰语", "sv":"瑞典语", "cs":"捷克语", "el":"希腊语", "hi":"印地语", "da":"丹麦语", "fi":"芬兰语", "no":"挪威语",
        "he":"希伯来语", "id":"印度尼西亚语", "vi":"越南语", "th":"泰语", "ro":"罗马尼亚语", "hu":"匈牙利语",
    },
}


def speech_language_name(ui_language: str, code: str) -> str:
    if code == "same":
        return tr(ui_language, "same_as_spoken")
    return _SPEECH_NAMES.get(ui_language, _SPEECH_NAMES["en"]).get(code, SPEECH_LANGUAGES.get(code, code))

# Generic dictionary scope label used by the personal vocabulary editor.
_EN["all"] = "All languages"
_DE["all"] = "Alle Sprachen"
_FR["all"] = "Toutes les langues"
_IT["all"] = "Tutte le lingue"
_ES["all"] = "Todos los idiomas"
_ZH["all"] = "所有语言"

_EN.update({
    "language_target_rules": "Automatic language routes",
    "language_target_rules_hint": "Optional source:target rules, for example en:de, fr:de, de:en. A matching rule overrides the fixed written language.",
    "hotkey_test": "Test recording hotkey",
    "hotkey_test_hint": "Press the configured hotkey now. No recording will start during this test.",
    "hotkey_test_success": "The recording hotkey was detected correctly.",
})
_DE.update({
    "language_target_rules": "Automatische Sprachwege",
    "language_target_rules_hint": "Optionale Regeln im Format Quelle:Ziel, zum Beispiel en:de, fr:de, de:en. Eine passende Regel überschreibt die feste Ausgabesprache.",
    "hotkey_test": "Aufnahmetaste testen",
    "hotkey_test_hint": "Drücke jetzt die eingestellte Aufnahmetaste. Während des Tests startet keine Aufnahme.",
    "hotkey_test_success": "Die Aufnahmetaste wurde korrekt erkannt.",
})
_FR.update({
    "language_target_rules": "Routage automatique des langues",
    "language_target_rules_hint": "Règles facultatives source:cible, par exemple en:de, fr:de, de:en. Une règle correspondante remplace la langue écrite fixe.",
    "hotkey_test": "Tester la touche d’enregistrement",
    "hotkey_test_hint": "Appuyez maintenant sur la touche configurée. Aucun enregistrement ne démarre pendant le test.",
    "hotkey_test_success": "La touche d’enregistrement a été détectée correctement.",
})
_IT.update({
    "language_target_rules": "Percorsi linguistici automatici",
    "language_target_rules_hint": "Regole facoltative sorgente:destinazione, ad esempio en:de, fr:de, de:en. Una regola corrispondente sostituisce la lingua scritta fissa.",
    "hotkey_test": "Prova il tasto di registrazione",
    "hotkey_test_hint": "Premi ora il tasto configurato. Durante il test non inizierà alcuna registrazione.",
    "hotkey_test_success": "Il tasto di registrazione è stato rilevato correttamente.",
})
_ES.update({
    "language_target_rules": "Rutas automáticas de idioma",
    "language_target_rules_hint": "Reglas opcionales origen:destino, por ejemplo en:de, fr:de, de:en. Una regla coincidente sustituye el idioma escrito fijo.",
    "hotkey_test": "Probar la tecla de grabación",
    "hotkey_test_hint": "Pulsa ahora la tecla configurada. Durante la prueba no se iniciará ninguna grabación.",
    "hotkey_test_success": "La tecla de grabación se detectó correctamente.",
})
_ZH.update({
    "language_target_rules": "自动语言路由",
    "language_target_rules_hint": "可选的源语言:目标语言规则，例如 en:de、fr:de、de:en。匹配的规则会覆盖固定输出语言。",
    "hotkey_test": "测试录音快捷键",
    "hotkey_test_hint": "现在按下已配置的快捷键。测试期间不会开始录音。",
    "hotkey_test_success": "已正确检测到录音快捷键。",
})

_EN.update({
    "word_count": "Words",
    "translated_status": "Translated",
    "audio": "Audio",
    "export_audio": "Export audio",
    "no_saved_audio": "No saved audio is available for this entry.",
    "beam_size": "Recognition search width",
    "monitor_label": "Monitor",
    "coordinate_x": "Horizontal position (X)",
    "coordinate_y": "Vertical position (Y)",
})
_DE.update({
    "word_count": "Wörter",
    "translated_status": "Übersetzt",
    "audio": "Audio",
    "export_audio": "Audio exportieren",
    "no_saved_audio": "Für diesen Eintrag ist keine gespeicherte Audioaufnahme verfügbar.",
    "beam_size": "Suchbreite der Erkennung",
    "monitor_label": "Monitor",
    "coordinate_x": "Horizontale Position (X)",
    "coordinate_y": "Vertikale Position (Y)",
})
_FR.update({
    "word_count": "Mots",
    "translated_status": "Traduit",
    "audio": "Audio",
    "export_audio": "Exporter l’audio",
    "no_saved_audio": "Aucun enregistrement audio n’est disponible pour cette entrée.",
    "beam_size": "Largeur de recherche de reconnaissance",
    "monitor_label": "Écran",
    "coordinate_x": "Position horizontale (X)",
    "coordinate_y": "Position verticale (Y)",
})
_IT.update({
    "word_count": "Parole",
    "translated_status": "Tradotto",
    "audio": "Audio",
    "export_audio": "Esporta audio",
    "no_saved_audio": "Non è disponibile alcuna registrazione audio per questa voce.",
    "beam_size": "Ampiezza di ricerca del riconoscimento",
    "monitor_label": "Monitor",
    "coordinate_x": "Posizione orizzontale (X)",
    "coordinate_y": "Posizione verticale (Y)",
})
_ES.update({
    "word_count": "Palabras",
    "translated_status": "Traducido",
    "audio": "Audio",
    "export_audio": "Exportar audio",
    "no_saved_audio": "No hay ninguna grabación de audio guardada para esta entrada.",
    "beam_size": "Amplitud de búsqueda del reconocimiento",
    "monitor_label": "Monitor",
    "coordinate_x": "Posición horizontal (X)",
    "coordinate_y": "Posición vertical (Y)",
})
_ZH.update({
    "word_count": "字词数",
    "translated_status": "已翻译",
    "audio": "音频",
    "export_audio": "导出音频",
    "no_saved_audio": "此条目没有可用的已保存录音。",
    "beam_size": "识别搜索宽度",
    "monitor_label": "显示器",
    "coordinate_x": "水平位置 (X)",
    "coordinate_y": "垂直位置 (Y)",
})

_EN["wayland_shortcut_command"] = "Wayland fallback: bind the desktop shortcut command 'LocalVoice --toggle' in your Linux system settings. The command securely controls the already running LocalVoice instance."
_DE["wayland_shortcut_command"] = "Wayland-Ausweichlösung: Hinterlege in den Linux-Systemeinstellungen den globalen Befehl „LocalVoice --toggle“. Der Befehl steuert sicher die bereits laufende LocalVoice-Instanz."
_FR["wayland_shortcut_command"] = "Solution Wayland : associez la commande globale « LocalVoice --toggle » dans les paramètres Linux. Elle contrôle en toute sécurité l’instance LocalVoice déjà ouverte."
_IT["wayland_shortcut_command"] = "Alternativa Wayland: assegna il comando globale « LocalVoice --toggle » nelle impostazioni Linux. Il comando controlla in modo sicuro l’istanza LocalVoice già in esecuzione."
_ES["wayland_shortcut_command"] = "Alternativa para Wayland: asigna el comando global « LocalVoice --toggle » en los ajustes de Linux. El comando controla de forma segura la instancia de LocalVoice que ya está abierta."
_ZH["wayland_shortcut_command"] = "Wayland 备用方案：在 Linux 系统设置中绑定全局命令“LocalVoice --toggle”。该命令会安全控制已经运行的 LocalVoice 实例。"

_EN.update({
    "pin_length": "The PIN must contain between 4 and 256 characters.",
    "microphone_no_signal": "The microphone opened, but no usable input signal was detected.",
    "open_model_manager_question": "Open the local model manager now?",
})
_DE.update({
    "pin_length": "Die PIN muss zwischen 4 und 256 Zeichen enthalten.",
    "microphone_no_signal": "Das Mikrofon wurde geöffnet, aber es wurde kein verwertbares Eingangssignal erkannt.",
    "open_model_manager_question": "Jetzt den lokalen Modellmanager öffnen?",
})
_FR.update({
    "pin_length": "Le code PIN doit contenir entre 4 et 256 caractères.",
    "microphone_no_signal": "Le microphone a été ouvert, mais aucun signal d’entrée exploitable n’a été détecté.",
    "open_model_manager_question": "Ouvrir maintenant le gestionnaire de modèles locaux ?",
})
_IT.update({
    "pin_length": "Il PIN deve contenere da 4 a 256 caratteri.",
    "microphone_no_signal": "Il microfono è stato aperto, ma non è stato rilevato alcun segnale di ingresso utilizzabile.",
    "open_model_manager_question": "Aprire ora il gestore dei modelli locali?",
})
_ES.update({
    "pin_length": "El PIN debe contener entre 4 y 256 caracteres.",
    "microphone_no_signal": "El micrófono se abrió, pero no se detectó ninguna señal de entrada utilizable.",
    "open_model_manager_question": "¿Abrir ahora el gestor de modelos locales?",
})
_ZH.update({
    "pin_length": "PIN 必须包含 4 到 256 个字符。",
    "microphone_no_signal": "麦克风已打开，但未检测到可用的输入信号。",
    "open_model_manager_question": "现在打开本地模型管理器吗？",
})

# Model downloads are always explicit and never start during normal dictation.
_EN["download_on_use"] = "Install the selected model once in the model manager; it then works offline."
_DE["download_on_use"] = "Installiere das ausgewählte Modell einmal ausdrücklich im Modellmanager; danach funktioniert es offline."
_FR["download_on_use"] = "Installez une fois le modèle choisi dans le gestionnaire ; il fonctionnera ensuite hors ligne."
_IT["download_on_use"] = "Installa una volta il modello scelto nel gestore; in seguito funzionerà offline."
_ES["download_on_use"] = "Instala una vez el modelo elegido en el gestor; después funcionará sin conexión."
_ZH["download_on_use"] = "请在模型管理器中明确安装一次所选模型；之后即可离线使用。"

_EN.update({
    "statistics": "Statistics",
    "transcriptions": "Transcriptions",
    "total_words": "Total words",
    "recording_time": "Recording time",
    "translations": "Translations",
    "saved_recordings": "Saved recordings",
})
_DE.update({
    "statistics": "Statistiken",
    "transcriptions": "Transkriptionen",
    "total_words": "Wörter insgesamt",
    "recording_time": "Aufnahmezeit",
    "translations": "Übersetzungen",
    "saved_recordings": "Gespeicherte Aufnahmen",
})
_FR.update({
    "statistics": "Statistiques",
    "transcriptions": "Transcriptions",
    "total_words": "Total des mots",
    "recording_time": "Durée d’enregistrement",
    "translations": "Traductions",
    "saved_recordings": "Enregistrements sauvegardés",
})
_IT.update({
    "statistics": "Statistiche",
    "transcriptions": "Trascrizioni",
    "total_words": "Parole totali",
    "recording_time": "Tempo di registrazione",
    "translations": "Traduzioni",
    "saved_recordings": "Registrazioni salvate",
})
_ES.update({
    "statistics": "Estadísticas",
    "transcriptions": "Transcripciones",
    "total_words": "Palabras totales",
    "recording_time": "Tiempo de grabación",
    "translations": "Traducciones",
    "saved_recordings": "Grabaciones guardadas",
})
_ZH.update({
    "statistics": "统计",
    "transcriptions": "转写次数",
    "total_words": "总字词数",
    "recording_time": "录音时长",
    "translations": "翻译次数",
    "saved_recordings": "已保存录音",
})

_EN["model_install_in_progress"] = "A local model installation is still running. Keep this window open until it finishes."
_DE["model_install_in_progress"] = "Eine lokale Modellinstallation läuft noch. Lass dieses Fenster bis zum Abschluss geöffnet."
_FR["model_install_in_progress"] = "Une installation de modèle local est encore en cours. Gardez cette fenêtre ouverte jusqu’à la fin."
_IT["model_install_in_progress"] = "È ancora in corso l’installazione di un modello locale. Mantieni aperta questa finestra fino al termine."
_ES["model_install_in_progress"] = "Todavía hay una instalación de modelo local en curso. Mantén esta ventana abierta hasta que termine."
_ZH["model_install_in_progress"] = "本地模型仍在安装中。请保持此窗口打开，直到安装完成。"

# LocalVoice 1.2 completeness and safety audit strings.
_EN.update({
    "automatic_punctuation": "Automatic capitalization and punctuation",
    "unlimited": "Unlimited",
    "overlay_processing": "Keep the status popup visible while recognizing and translating",
    "profile_audio": "Audio and recognition",
    "profile_output": "Output",
    "profile_privacy": "Privacy",
    "profile_language": "Language and text",
    "max_duration_hint": "Set to 0 for unlimited recording. Long recordings are streamed to disk instead of being kept in memory.",
    "keyring_fallback": "On Linux, the desktop keyring is used when available; otherwise the local key file is protected with user-only permissions.",
})
_DE.update({
    "automatic_punctuation": "Automatische Großschreibung und Satzzeichen",
    "unlimited": "Unbegrenzt",
    "overlay_processing": "Status-Pop-up während Erkennung und Übersetzung sichtbar lassen",
    "profile_audio": "Audio und Erkennung",
    "profile_output": "Ausgabe",
    "profile_privacy": "Datenschutz",
    "profile_language": "Sprache und Text",
    "max_duration_hint": "0 bedeutet unbegrenzt. Lange Aufnahmen werden direkt auf den Datenträger geschrieben und nicht vollständig im Arbeitsspeicher gehalten.",
    "keyring_fallback": "Unter Linux wird nach Möglichkeit der Desktop-Schlüsselbund verwendet; andernfalls ist die lokale Schlüsseldatei nur für den Benutzer zugänglich.",
})
_FR.update({
    "automatic_punctuation": "Majuscules et ponctuation automatiques",
    "unlimited": "Illimitée",
    "overlay_processing": "Garder la fenêtre d’état visible pendant la reconnaissance et la traduction",
    "profile_audio": "Audio et reconnaissance",
    "profile_output": "Sortie",
    "profile_privacy": "Confidentialité",
    "profile_language": "Langue et texte",
    "max_duration_hint": "0 signifie illimité. Les longs enregistrements sont écrits directement sur le disque plutôt que conservés entièrement en mémoire.",
    "keyring_fallback": "Sous Linux, le trousseau du bureau est utilisé s’il est disponible ; sinon le fichier de clé local est réservé à l’utilisateur.",
})
_IT.update({
    "automatic_punctuation": "Maiuscole e punteggiatura automatiche",
    "unlimited": "Illimitata",
    "overlay_processing": "Mantieni visibile il popup di stato durante riconoscimento e traduzione",
    "profile_audio": "Audio e riconoscimento",
    "profile_output": "Uscita",
    "profile_privacy": "Privacy",
    "profile_language": "Lingua e testo",
    "max_duration_hint": "0 significa illimitata. Le registrazioni lunghe vengono scritte direttamente sul disco e non mantenute interamente in memoria.",
    "keyring_fallback": "Su Linux viene usato il portachiavi del desktop quando disponibile; altrimenti il file della chiave locale è accessibile solo all’utente.",
})
_ES.update({
    "automatic_punctuation": "Mayúsculas y puntuación automáticas",
    "unlimited": "Ilimitada",
    "overlay_processing": "Mantener visible el aviso de estado durante el reconocimiento y la traducción",
    "profile_audio": "Audio y reconocimiento",
    "profile_output": "Salida",
    "profile_privacy": "Privacidad",
    "profile_language": "Idioma y texto",
    "max_duration_hint": "0 significa ilimitada. Las grabaciones largas se escriben directamente en el disco y no se guardan por completo en la memoria.",
    "keyring_fallback": "En Linux se usa el llavero del escritorio cuando está disponible; de lo contrario, el archivo de clave local queda accesible solo para el usuario.",
})
_ZH.update({
    "automatic_punctuation": "自动大写和标点",
    "unlimited": "无限制",
    "overlay_processing": "识别和翻译期间保持状态浮窗可见",
    "profile_audio": "音频和识别",
    "profile_output": "输出",
    "profile_privacy": "隐私",
    "profile_language": "语言和文本",
    "max_duration_hint": "设为 0 表示不限制。长录音会直接写入磁盘，而不会全部保存在内存中。",
    "keyring_fallback": "在 Linux 上会优先使用桌面密钥环；不可用时，本地密钥文件仅允许当前用户访问。",
})

# LocalVoice 1.2 runtime diagnostics and precise error messages.
_EN.update({
    "audio_write_error": "The recording could not be written safely. Check available disk space and folder permissions.",
    "wayland_hotkey_status": "On Wayland, desktop-wide shortcuts depend on the desktop portal or a shortcut configured in the system settings. LocalVoice never claims that a shortcut worked when the backend rejected it.",
})
_DE.update({
    "audio_write_error": "Die Aufnahme konnte nicht sicher gespeichert werden. Prüfe freien Speicherplatz und Ordnerberechtigungen.",
    "wayland_hotkey_status": "Unter Wayland hängen systemweite Tastenkürzel vom Desktop-Portal oder einem in den Systemeinstellungen eingerichteten Kürzel ab. LocalVoice meldet niemals fälschlich, ein Kürzel habe funktioniert, wenn das System es abgelehnt hat.",
})
_FR.update({
    "audio_write_error": "L’enregistrement n’a pas pu être écrit en toute sécurité. Vérifiez l’espace disque et les autorisations du dossier.",
    "wayland_hotkey_status": "Sous Wayland, les raccourcis globaux dépendent du portail du bureau ou d’un raccourci configuré dans le système. LocalVoice ne prétend jamais qu’un raccourci a fonctionné si le système l’a refusé.",
})
_IT.update({
    "audio_write_error": "Non è stato possibile scrivere la registrazione in modo sicuro. Controlla lo spazio disponibile e i permessi della cartella.",
    "wayland_hotkey_status": "Su Wayland, le scorciatoie globali dipendono dal portale del desktop o da una scorciatoia configurata nel sistema. LocalVoice non indica mai falsamente che una scorciatoia ha funzionato se il sistema l’ha rifiutata.",
})
_ES.update({
    "audio_write_error": "No se pudo guardar la grabación de forma segura. Comprueba el espacio libre y los permisos de la carpeta.",
    "wayland_hotkey_status": "En Wayland, los atajos globales dependen del portal del escritorio o de un atajo configurado en el sistema. LocalVoice nunca afirma que un atajo funcionó cuando el sistema lo rechazó.",
})
_ZH.update({
    "audio_write_error": "无法安全写入录音。请检查可用磁盘空间和文件夹权限。",
    "wayland_hotkey_status": "在 Wayland 下，系统级快捷键依赖桌面门户或系统设置中配置的快捷键。若系统拒绝快捷键，LocalVoice 不会错误地显示其已生效。",
})

_EN["keyring_cleanup_warning"] = "The PIN is active, but an older Linux keyring entry could not yet be removed. Unlock the desktop keyring and restart LocalVoice so it can finish the cleanup."
_DE["keyring_cleanup_warning"] = "Die PIN ist aktiv, aber ein älterer Linux-Schlüsselbund-Eintrag konnte noch nicht entfernt werden. Entsperre den Desktop-Schlüsselbund und starte LocalVoice neu, damit die Bereinigung abgeschlossen werden kann."
_FR["keyring_cleanup_warning"] = "Le code PIN est actif, mais une ancienne entrée du trousseau Linux n’a pas encore pu être supprimée. Déverrouillez le trousseau du bureau et redémarrez LocalVoice."
_IT["keyring_cleanup_warning"] = "Il PIN è attivo, ma non è stato ancora possibile rimuovere una vecchia voce del portachiavi Linux. Sblocca il portachiavi del desktop e riavvia LocalVoice."
_ES["keyring_cleanup_warning"] = "El PIN está activo, pero todavía no se pudo eliminar una entrada antigua del llavero de Linux. Desbloquea el llavero del escritorio y reinicia LocalVoice."
_ZH["keyring_cleanup_warning"] = "PIN 已启用，但旧的 Linux 密钥环条目尚未成功删除。请解锁桌面密钥环并重启 LocalVoice，以完成清理。"

# Wayland portal status messages (kept together so all six UI locales stay in sync).
_EN.update({
    "wayland_portal_active": "The Wayland global shortcut is active through the desktop portal.",
    "wayland_portal_failed": "The Wayland desktop did not activate the requested global shortcut.",
})
_DE.update({
    "wayland_portal_active": "Das globale Wayland-Tastenkürzel ist über das Desktop-Portal aktiv.",
    "wayland_portal_failed": "Die Wayland-Oberfläche hat das gewünschte globale Tastenkürzel nicht aktiviert.",
})
_FR.update({
    "wayland_portal_active": "Le raccourci global Wayland est actif via le portail du bureau.",
    "wayland_portal_failed": "Le bureau Wayland n’a pas activé le raccourci global demandé.",
})
_IT.update({
    "wayland_portal_active": "La scorciatoia globale Wayland è attiva tramite il portale del desktop.",
    "wayland_portal_failed": "Il desktop Wayland non ha attivato la scorciatoia globale richiesta.",
})
_ES.update({
    "wayland_portal_active": "El atajo global de Wayland está activo mediante el portal del escritorio.",
    "wayland_portal_failed": "El escritorio Wayland no activó el atajo global solicitado.",
})
_ZH.update({
    "wayland_portal_active": "Wayland 全局快捷键已通过桌面门户启用。",
    "wayland_portal_failed": "Wayland 桌面未启用所请求的全局快捷键。",
})


_EN["audio_requires_history"] = "Saved audio is attached to encrypted history entries. Private mode or disabled history therefore also disables audio storage."
_DE["audio_requires_history"] = "Gespeicherte Audiodateien werden verschlüsselten Verlaufseinträgen zugeordnet. Der private Modus oder ein deaktivierter Verlauf schaltet deshalb auch die Audiospeicherung aus."
_FR["audio_requires_history"] = "L’audio conservé est associé aux entrées chiffrées de l’historique. Le mode privé ou l’historique désactivé désactive donc aussi la conservation audio."
_IT["audio_requires_history"] = "L’audio salvato è collegato alle voci cifrate della cronologia. La modalità privata o la cronologia disattivata disabilitano quindi anche il salvataggio audio."
_ES["audio_requires_history"] = "El audio guardado se vincula a entradas cifradas del historial. Por ello, el modo privado o el historial desactivado también desactivan el almacenamiento de audio."
_ZH["audio_requires_history"] = "保存的音频会关联到加密历史记录。因此，私密模式或关闭历史记录时也会关闭音频保存。"


# UI size controls
_EN.update({"ui_size":"Interface size","ui_size_small":"Small","ui_size_medium":"Medium (recommended)","ui_size_large":"Large"})
_DE.update({"ui_size":"UI-Größe","ui_size_small":"Klein","ui_size_medium":"Mittel (Standard)","ui_size_large":"Groß"})
_FR.update({"ui_size":"Taille de l’interface","ui_size_small":"Petite","ui_size_medium":"Moyenne (standard)","ui_size_large":"Grande"})
_IT.update({"ui_size":"Dimensione interfaccia","ui_size_small":"Piccola","ui_size_medium":"Media (standard)","ui_size_large":"Grande"})
_ES.update({"ui_size":"Tamaño de la interfaz","ui_size_small":"Pequeño","ui_size_medium":"Mediano (predeterminado)","ui_size_large":"Grande"})
_ZH.update({"ui_size":"界面大小","ui_size_small":"小","ui_size_medium":"中（默认）","ui_size_large":"大"})

# LocalVoice 1.3 modern dashboard, diagnostics and guided language selection.
_EN.update({
    "choose_languages": "Choose languages…",
    "search_languages": "Search languages or codes",
    "select_common_languages": "Select common languages",
    "clear_selection": "Clear selection",
    "languages_selected": "{count} selected",
    "microphone_test_explainer": "Speak normally for five seconds. The meter should react to your voice.",
    "quick_actions": "Quick actions",
    "record_button": "Start recording",
    "stop_recording_button": "Stop recording",
    "dashboard_greeting": "Your private voice workspace",
    "dashboard_intro": "Record, transcribe and translate locally. Nothing leaves this device.",
    "device_status": "System status",
    "speech_model": "Speech model",
    "model_ready": "Installed and ready",
    "model_required": "Install a model before dictating",
    "install_model_now": "Install speech model",
    "microphone_ready": "Microphone detected",
    "microphone_missing": "No microphone detected",
    "hotkey_status": "Global hotkey",
    "hotkey_active": "Active: {hotkey}",
    "hotkey_unavailable": "Hotkey backend unavailable",
    "hotkey_backend": "Backend: {backend}",
    "quick_microphone_test": "Test microphone",
    "quick_models": "Manage models",
    "quick_settings": "Open settings",
    "privacy_badge": "100% local · no account · no API fees",
    "status_attention": "Action required",
    "system_check": "System check",
    "system_check_title": "LocalVoice system check",
    "system_check_ok": "All essential checks passed.",
    "system_check_issue": "Some items need attention.",
    "check_data_folder": "Local data folder",
    "check_model": "Speech model",
    "check_microphone": "Microphone",
    "check_hotkey": "Global hotkey",
    "check_disk": "Free disk space",
})
_DE.update({
    "choose_languages": "Sprachen auswählen…",
    "search_languages": "Sprachen oder Kürzel suchen",
    "select_common_languages": "Häufige Sprachen auswählen",
    "clear_selection": "Auswahl löschen",
    "languages_selected": "{count} ausgewählt",
    "microphone_test_explainer": "Sprich fünf Sekunden lang normal. Der Pegel muss auf deine Stimme reagieren.",
    "quick_actions": "Schnellzugriff",
    "record_button": "Aufnahme starten",
    "stop_recording_button": "Aufnahme stoppen",
    "dashboard_greeting": "Dein privater Sprach-Arbeitsbereich",
    "dashboard_intro": "Aufnehmen, transkribieren und übersetzen – vollständig lokal auf diesem Gerät.",
    "device_status": "Systemstatus",
    "speech_model": "Sprachmodell",
    "model_ready": "Installiert und bereit",
    "model_required": "Vor dem Diktieren ein Modell installieren",
    "install_model_now": "Sprachmodell installieren",
    "microphone_ready": "Mikrofon erkannt",
    "microphone_missing": "Kein Mikrofon erkannt",
    "hotkey_status": "Globale Aufnahmetaste",
    "hotkey_active": "Aktiv: {hotkey}",
    "hotkey_unavailable": "Hotkey-Dienst nicht verfügbar",
    "hotkey_backend": "Technik: {backend}",
    "quick_microphone_test": "Mikrofon testen",
    "quick_models": "Modelle verwalten",
    "quick_settings": "Einstellungen öffnen",
    "privacy_badge": "100 % lokal · kein Konto · keine API-Kosten",
    "status_attention": "Aktion erforderlich",
    "system_check": "Systemprüfung",
    "system_check_title": "LocalVoice-Systemprüfung",
    "system_check_ok": "Alle wichtigen Prüfungen wurden bestanden.",
    "system_check_issue": "Einige Punkte benötigen Aufmerksamkeit.",
    "check_data_folder": "Lokaler Datenordner",
    "check_model": "Sprachmodell",
    "check_microphone": "Mikrofon",
    "check_hotkey": "Globale Aufnahmetaste",
    "check_disk": "Freier Speicherplatz",
})
_FR.update({
    "choose_languages": "Choisir les langues…",
    "search_languages": "Rechercher une langue ou un code",
    "select_common_languages": "Sélectionner les langues courantes",
    "clear_selection": "Effacer la sélection",
    "languages_selected": "{count} sélectionnées",
    "microphone_test_explainer": "Parlez normalement pendant cinq secondes. Le niveau doit réagir à votre voix.",
    "quick_actions": "Actions rapides",
    "record_button": "Démarrer l’enregistrement",
    "stop_recording_button": "Arrêter l’enregistrement",
    "dashboard_greeting": "Votre espace vocal privé",
    "dashboard_intro": "Enregistrez, transcrivez et traduisez localement. Rien ne quitte cet appareil.",
    "device_status": "État du système",
    "speech_model": "Modèle vocal",
    "model_ready": "Installé et prêt",
    "model_required": "Installez un modèle avant de dicter",
    "install_model_now": "Installer le modèle vocal",
    "microphone_ready": "Microphone détecté",
    "microphone_missing": "Aucun microphone détecté",
    "hotkey_status": "Raccourci global",
    "hotkey_active": "Actif : {hotkey}",
    "hotkey_unavailable": "Service de raccourci indisponible",
    "hotkey_backend": "Moteur : {backend}",
    "quick_microphone_test": "Tester le microphone",
    "quick_models": "Gérer les modèles",
    "quick_settings": "Ouvrir les paramètres",
    "privacy_badge": "100 % local · sans compte · sans frais API",
    "status_attention": "Action requise",
    "system_check": "Vérification du système",
    "system_check_title": "Vérification système LocalVoice",
    "system_check_ok": "Tous les contrôles essentiels ont réussi.",
    "system_check_issue": "Certains éléments nécessitent votre attention.",
    "check_data_folder": "Dossier de données local",
    "check_model": "Modèle vocal",
    "check_microphone": "Microphone",
    "check_hotkey": "Raccourci global",
    "check_disk": "Espace disque libre",
})
_IT.update({
    "choose_languages": "Scegli lingue…",
    "search_languages": "Cerca lingue o codici",
    "select_common_languages": "Seleziona lingue comuni",
    "clear_selection": "Cancella selezione",
    "languages_selected": "{count} selezionate",
    "microphone_test_explainer": "Parla normalmente per cinque secondi. Il livello deve reagire alla voce.",
    "quick_actions": "Azioni rapide",
    "record_button": "Avvia registrazione",
    "stop_recording_button": "Ferma registrazione",
    "dashboard_greeting": "Il tuo spazio vocale privato",
    "dashboard_intro": "Registra, trascrivi e traduci localmente. Nulla lascia questo dispositivo.",
    "device_status": "Stato del sistema",
    "speech_model": "Modello vocale",
    "model_ready": "Installato e pronto",
    "model_required": "Installa un modello prima di dettare",
    "install_model_now": "Installa modello vocale",
    "microphone_ready": "Microfono rilevato",
    "microphone_missing": "Nessun microfono rilevato",
    "hotkey_status": "Tasto globale",
    "hotkey_active": "Attivo: {hotkey}",
    "hotkey_unavailable": "Servizio tasti non disponibile",
    "hotkey_backend": "Motore: {backend}",
    "quick_microphone_test": "Prova microfono",
    "quick_models": "Gestisci modelli",
    "quick_settings": "Apri impostazioni",
    "privacy_badge": "100% locale · nessun account · nessun costo API",
    "status_attention": "Azione richiesta",
    "system_check": "Controllo sistema",
    "system_check_title": "Controllo sistema LocalVoice",
    "system_check_ok": "Tutti i controlli essenziali sono riusciti.",
    "system_check_issue": "Alcuni elementi richiedono attenzione.",
    "check_data_folder": "Cartella dati locale",
    "check_model": "Modello vocale",
    "check_microphone": "Microfono",
    "check_hotkey": "Tasto globale",
    "check_disk": "Spazio libero",
})
_ES.update({
    "choose_languages": "Elegir idiomas…",
    "search_languages": "Buscar idiomas o códigos",
    "select_common_languages": "Seleccionar idiomas comunes",
    "clear_selection": "Borrar selección",
    "languages_selected": "{count} seleccionados",
    "microphone_test_explainer": "Habla con normalidad durante cinco segundos. El nivel debe reaccionar a tu voz.",
    "quick_actions": "Acciones rápidas",
    "record_button": "Iniciar grabación",
    "stop_recording_button": "Detener grabación",
    "dashboard_greeting": "Tu espacio de voz privado",
    "dashboard_intro": "Graba, transcribe y traduce localmente. Nada sale de este dispositivo.",
    "device_status": "Estado del sistema",
    "speech_model": "Modelo de voz",
    "model_ready": "Instalado y listo",
    "model_required": "Instala un modelo antes de dictar",
    "install_model_now": "Instalar modelo de voz",
    "microphone_ready": "Micrófono detectado",
    "microphone_missing": "No se detectó micrófono",
    "hotkey_status": "Tecla global",
    "hotkey_active": "Activa: {hotkey}",
    "hotkey_unavailable": "Servicio de atajos no disponible",
    "hotkey_backend": "Motor: {backend}",
    "quick_microphone_test": "Probar micrófono",
    "quick_models": "Gestionar modelos",
    "quick_settings": "Abrir ajustes",
    "privacy_badge": "100 % local · sin cuenta · sin costes API",
    "status_attention": "Acción necesaria",
    "system_check": "Comprobación del sistema",
    "system_check_title": "Comprobación del sistema LocalVoice",
    "system_check_ok": "Todas las comprobaciones esenciales se superaron.",
    "system_check_issue": "Algunos elementos requieren atención.",
    "check_data_folder": "Carpeta de datos local",
    "check_model": "Modelo de voz",
    "check_microphone": "Micrófono",
    "check_hotkey": "Tecla global",
    "check_disk": "Espacio libre",
})
_ZH.update({
    "choose_languages": "选择语言…",
    "search_languages": "搜索语言或代码",
    "select_common_languages": "选择常用语言",
    "clear_selection": "清除选择",
    "languages_selected": "已选择 {count} 种",
    "microphone_test_explainer": "请正常说话五秒钟，电平应随声音变化。",
    "quick_actions": "快捷操作",
    "record_button": "开始录音",
    "stop_recording_button": "停止录音",
    "dashboard_greeting": "你的私密语音工作区",
    "dashboard_intro": "在本机录音、转写和翻译，任何内容都不会离开此设备。",
    "device_status": "系统状态",
    "speech_model": "语音模型",
    "model_ready": "已安装并就绪",
    "model_required": "听写前请先安装模型",
    "install_model_now": "安装语音模型",
    "microphone_ready": "已检测到麦克风",
    "microphone_missing": "未检测到麦克风",
    "hotkey_status": "全局快捷键",
    "hotkey_active": "已启用：{hotkey}",
    "hotkey_unavailable": "快捷键服务不可用",
    "hotkey_backend": "后端：{backend}",
    "quick_microphone_test": "测试麦克风",
    "quick_models": "管理模型",
    "quick_settings": "打开设置",
    "privacy_badge": "100% 本地 · 无需账户 · 无 API 费用",
    "status_attention": "需要操作",
    "system_check": "系统检查",
    "system_check_title": "LocalVoice 系统检查",
    "system_check_ok": "所有关键检查均已通过。",
    "system_check_issue": "部分项目需要处理。",
    "check_data_folder": "本地数据文件夹",
    "check_model": "语音模型",
    "check_microphone": "麦克风",
    "check_hotkey": "全局快捷键",
    "check_disk": "可用磁盘空间",
})

# LocalVoice 1.8.0 diagnostics and global-hotkey test text.
_EN.update({"status_starting":"Starting…", "hotkey_test_waiting":"Global listener active ({backend}). Press the configured key now."})
_DE.update({"status_starting":"Wird gestartet…", "hotkey_test_waiting":"Globaler Listener aktiv ({backend}). Drücke jetzt die eingestellte Taste."})
_FR.update({"status_starting":"Démarrage…", "hotkey_test_waiting":"Écoute globale active ({backend}). Appuyez maintenant sur la touche configurée."})
_IT.update({"status_starting":"Avvio…", "hotkey_test_waiting":"Ascolto globale attivo ({backend}). Premi ora il tasto configurato."})
_ES.update({"status_starting":"Iniciando…", "hotkey_test_waiting":"Escucha global activa ({backend}). Pulsa ahora la tecla configurada."})
_ZH.update({"status_starting":"正在启动…", "hotkey_test_waiting":"全局监听已启用（{backend}）。现在按下已配置的按键。"})

_EN.update({"model_required_close_warning":"No speech model is installed. Dictation and the global recording key cannot work until a model is installed. Close anyway?"})
_DE.update({"model_required_close_warning":"Es ist kein Sprachmodell installiert. Diktieren und die globale Aufnahmetaste funktionieren erst nach der Installation eines Modells. Trotzdem schließen?"})
_FR.update({"model_required_close_warning":"Aucun modèle vocal n’est installé. La dictée et le raccourci global ne fonctionneront qu’après l’installation d’un modèle. Fermer quand même ?"})
_IT.update({"model_required_close_warning":"Non è installato alcun modello vocale. La dettatura e il tasto globale funzioneranno solo dopo l’installazione di un modello. Chiudere comunque?"})
_ES.update({"model_required_close_warning":"No hay ningún modelo de voz instalado. El dictado y la tecla global solo funcionarán después de instalar un modelo. ¿Cerrar de todos modos?"})
_ZH.update({"model_required_close_warning":"尚未安装语音模型。安装模型之前，听写和全局录音快捷键无法工作。仍要关闭吗？"})

# LocalVoice 1.8.0 recognition-performance controls.
_EN.update({
    "recognition_mode": "Recognition speed and accuracy",
    "recognition_fast": "Fast",
    "recognition_balanced": "Balanced (recommended)",
    "recognition_accurate": "Accurate",
    "recognition_mode_hint": "Balanced uses fast decoding and smarter preferred-language checks. Accurate needs more processing time.",
    "preload_model": "Preload the installed speech model after LocalVoice starts",
})
_DE.update({
    "recognition_mode": "Erkennungsgeschwindigkeit und Genauigkeit",
    "recognition_fast": "Schnell",
    "recognition_balanced": "Ausgewogen (empfohlen)",
    "recognition_accurate": "Genau",
    "recognition_mode_hint": "Ausgewogen arbeitet schneller und prüft bevorzugte Sprachen intelligenter. Genau benötigt mehr Verarbeitungszeit.",
    "preload_model": "Installiertes Sprachmodell nach dem Start vorladen",
})
_FR.update({
    "recognition_mode": "Vitesse et précision de reconnaissance",
    "recognition_fast": "Rapide",
    "recognition_balanced": "Équilibré (recommandé)",
    "recognition_accurate": "Précis",
    "recognition_mode_hint": "Le mode équilibré accélère le décodage et vérifie intelligemment les langues préférées. Le mode précis demande plus de temps.",
    "preload_model": "Précharger le modèle vocal installé au démarrage",
})
_IT.update({
    "recognition_mode": "Velocità e precisione del riconoscimento",
    "recognition_fast": "Veloce",
    "recognition_balanced": "Bilanciato (consigliato)",
    "recognition_accurate": "Preciso",
    "recognition_mode_hint": "Bilanciato usa una decodifica più rapida e controlla meglio le lingue preferite. Preciso richiede più tempo.",
    "preload_model": "Precarica il modello vocale installato all’avvio",
})
_ES.update({
    "recognition_mode": "Velocidad y precisión del reconocimiento",
    "recognition_fast": "Rápido",
    "recognition_balanced": "Equilibrado (recomendado)",
    "recognition_accurate": "Preciso",
    "recognition_mode_hint": "Equilibrado usa una decodificación más rápida y comprueba mejor los idiomas preferidos. Preciso tarda más.",
    "preload_model": "Precargar el modelo de voz instalado al iniciar",
})
_ZH.update({
    "recognition_mode": "识别速度与准确度",
    "recognition_fast": "快速",
    "recognition_balanced": "平衡（推荐）",
    "recognition_accurate": "精准",
    "recognition_mode_hint": "平衡模式使用更快的解码并智能检查首选语言；精准模式需要更长处理时间。",
    "preload_model": "LocalVoice 启动后预加载已安装的语音模型",
})

# LocalVoice 1.8.0 distant-microphone and smart-language controls.
_EN.update({
    "auto_microphone_gain": "Automatically amplify quiet/distant speech",
    "auto_microphone_gain_hint": "Uses a bounded speech-level analysis. It raises quiet voices without using steady room noise as the reference.",
    "prefer_primary_language": "Give the first preferred language extra weight",
    "prefer_primary_language_hint": "Keeps automatic language detection, but reduces short German/English mix-ups. Disable it for completely neutral detection.",
})
_DE.update({
    "auto_microphone_gain": "Leise oder weiter entfernte Sprache automatisch verstärken",
    "auto_microphone_gain_hint": "Analysiert den Sprachpegel begrenzt und hebt leise Stimmen an, ohne gleichmäßiges Raumrauschen als Maßstab zu verwenden.",
    "prefer_primary_language": "Erste bevorzugte Sprache stärker gewichten",
    "prefer_primary_language_hint": "Die automatische Spracherkennung bleibt aktiv, kurze Verwechslungen zwischen Deutsch und Englisch werden jedoch seltener. Für völlig neutrale Erkennung deaktivieren.",
})
_FR.update({
    "auto_microphone_gain": "Amplifier automatiquement la parole faible ou éloignée",
    "auto_microphone_gain_hint": "Analyse le niveau de la voix avec une limite sûre, sans prendre le bruit ambiant continu comme référence.",
    "prefer_primary_language": "Donner plus de poids à la première langue préférée",
    "prefer_primary_language_hint": "La détection automatique reste active, mais les confusions courtes entre langues sont réduites.",
})
_IT.update({
    "auto_microphone_gain": "Amplifica automaticamente la voce debole o distante",
    "auto_microphone_gain_hint": "Analizza il livello della voce con limiti sicuri senza usare il rumore ambientale costante come riferimento.",
    "prefer_primary_language": "Dai più peso alla prima lingua preferita",
    "prefer_primary_language_hint": "Il rilevamento automatico resta attivo, ma diminuiscono le brevi confusioni tra lingue.",
})
_ES.update({
    "auto_microphone_gain": "Amplificar automáticamente la voz baja o distante",
    "auto_microphone_gain_hint": "Analiza el nivel de voz con límites seguros sin usar el ruido ambiental constante como referencia.",
    "prefer_primary_language": "Dar más peso al primer idioma preferido",
    "prefer_primary_language_hint": "La detección automática sigue activa, pero reduce confusiones breves entre idiomas.",
})
_ZH.update({
    "auto_microphone_gain": "自动增强较轻或较远的语音",
    "auto_microphone_gain_hint": "在安全范围内分析语音电平，不会把持续的环境噪声作为增益基准。",
    "prefer_primary_language": "提高第一首选语言的权重",
    "prefer_primary_language_hint": "仍然自动识别语言，但会减少短句中的语言混淆。",
})

# LocalVoice 1.8.0 durable language recovery.
_LANGUAGE_SAVE_FAILED = {
    "de": "Die ausgewählte Sprache konnte nicht sicher gespeichert werden. Bitte versuche es erneut.",
    "en": "The selected language could not be saved safely. Please try again.",
    "fr": "La langue sélectionnée n’a pas pu être enregistrée de manière sûre. Réessayez.",
    "it": "Non è stato possibile salvare in modo sicuro la lingua selezionata. Riprova.",
    "es": "No se pudo guardar de forma segura el idioma seleccionado. Inténtalo de nuevo.",
    "zh": "无法安全保存所选语言。请重试。",
}
for _locale_code, _locale_table in _TRANSLATIONS.items():
    _locale_table["language_save_failed"] = _LANGUAGE_SAVE_FAILED[_locale_code]

# LocalVoice 1.8.0 live transcription and performance visibility.
_EN.update({
    "live_transcription": "Transcribe continuously while recording",
    "live_preview": "Show live text in the recording pop-up",
    "live_chunk_seconds": "Live processing interval",
    "live_transcription_hint": "LocalVoice decodes overlapping chunks while you speak. After Stop, only the remaining tail is finalized. On a slower CPU, Medium may still fall behind; no audio is lost because the complete recording remains available as a fallback.",
    "live_listening": "Listening and transcribing live…",
    "live_behind": "Live recognition is catching up…",
    "model_loaded_memory": "Loaded in memory",
    "model_installed_disk": "Installed · not loaded yet",
    "processing_time": "ready in {seconds:.1f}s",
    "streaming_result": "live",
    "full_pass_result": "final pass",
})
_DE.update({
    "live_transcription": "Während der Aufnahme fortlaufend transkribieren",
    "live_preview": "Live-Text im Aufnahme-Pop-up anzeigen",
    "live_chunk_seconds": "Live-Verarbeitungsintervall",
    "live_transcription_hint": "LocalVoice verarbeitet während des Sprechens überlappende Abschnitte. Nach Stop wird nur noch das letzte Reststück abgeschlossen. Auf einer langsameren CPU kann Medium trotzdem hinterherhinken; die vollständige Aufnahme bleibt als sichere Rückfallebene erhalten.",
    "live_listening": "Hört zu und schreibt bereits mit …",
    "live_behind": "Live-Erkennung holt auf …",
    "model_loaded_memory": "Im Arbeitsspeicher geladen",
    "model_installed_disk": "Installiert · noch nicht geladen",
    "processing_time": "fertig in {seconds:.1f}s",
    "streaming_result": "live verarbeitet",
    "full_pass_result": "vollständig verarbeitet",
})
_FR.update({
    "live_transcription": "Transcrire en continu pendant l’enregistrement",
    "live_preview": "Afficher le texte en direct dans la fenêtre d’enregistrement",
    "live_chunk_seconds": "Intervalle de traitement en direct",
    "live_transcription_hint": "LocalVoice traite des segments qui se chevauchent pendant que vous parlez. Après l’arrêt, seule la fin restante est finalisée.",
    "live_listening": "Écoute et transcription en direct…",
    "live_behind": "La reconnaissance en direct rattrape son retard…",
    "model_loaded_memory": "Chargé en mémoire",
    "model_installed_disk": "Installé · pas encore chargé",
    "processing_time": "prêt en {seconds:.1f}s",
    "streaming_result": "traité en direct",
    "full_pass_result": "traitement complet",
})
_IT.update({
    "live_transcription": "Trascrivi continuamente durante la registrazione",
    "live_preview": "Mostra il testo live nel pop-up di registrazione",
    "live_chunk_seconds": "Intervallo di elaborazione live",
    "live_transcription_hint": "LocalVoice elabora segmenti sovrapposti mentre parli. Dopo lo stop viene finalizzata solo la parte restante.",
    "live_listening": "Ascolto e trascrizione live…",
    "live_behind": "Il riconoscimento live sta recuperando…",
    "model_loaded_memory": "Caricato in memoria",
    "model_installed_disk": "Installato · non ancora caricato",
    "processing_time": "pronto in {seconds:.1f}s",
    "streaming_result": "elaborato live",
    "full_pass_result": "elaborazione completa",
})
_ES.update({
    "live_transcription": "Transcribir continuamente durante la grabación",
    "live_preview": "Mostrar texto en directo en la ventana de grabación",
    "live_chunk_seconds": "Intervalo de procesamiento en directo",
    "live_transcription_hint": "LocalVoice procesa fragmentos solapados mientras hablas. Al detener, solo se finaliza la parte restante.",
    "live_listening": "Escuchando y transcribiendo en directo…",
    "live_behind": "El reconocimiento en directo se está poniendo al día…",
    "model_loaded_memory": "Cargado en memoria",
    "model_installed_disk": "Instalado · aún no cargado",
    "processing_time": "listo en {seconds:.1f}s",
    "streaming_result": "procesado en directo",
    "full_pass_result": "procesamiento completo",
})
_ZH.update({
    "live_transcription": "录音时持续转写",
    "live_preview": "在录音浮窗中显示实时文字",
    "live_chunk_seconds": "实时处理间隔",
    "live_transcription_hint": "LocalVoice 会在您说话时处理重叠音频片段。停止后只需完成最后一段。",
    "live_listening": "正在聆听并实时转写…",
    "live_behind": "实时识别正在追赶…",
    "model_loaded_memory": "已加载到内存",
    "model_installed_disk": "已安装 · 尚未加载",
    "processing_time": "{seconds:.1f} 秒完成",
    "streaming_result": "实时处理",
    "full_pass_result": "完整处理",
})
