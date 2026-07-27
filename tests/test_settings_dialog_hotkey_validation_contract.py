from pathlib import Path


def test_unrelated_settings_save_is_not_blocked_by_existing_profile_hotkey_conflict() -> None:
    source = Path('localvoice/ui/dialogs.py').read_text(encoding='utf-8')
    start = source.index('    def _save(self) -> None:')
    end = source.index('\n\n\nclass StatisticsDialog', start)
    save_method = source[start:end]
    assert 'hotkeys_changed = primary != original_primary or secondary != original_secondary' in save_method
    assert 'profile_switching_just_enabled' in save_method
    assert 'if self.database is not None and (hotkeys_changed or profile_switching_just_enabled):' in save_method
