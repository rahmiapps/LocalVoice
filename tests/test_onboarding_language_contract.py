from pathlib import Path


def test_onboarding_persists_combo_current_data() -> None:
    source = Path('localvoice/ui/dialogs.py').read_text(encoding='utf-8')
    commit = source[source.index('    def _commit(self) -> bool:'):source.index('\n\n\nclass SettingsDialog')]
    assert 'selected_language = self.ui_language_combo.currentData()' in commit
    assert 'self.store.save(self.settings)' in commit
    assert commit.index('selected_language = self.ui_language_combo.currentData()') < commit.index('selected_language = self._selected_ui_language')


def test_default_ui_language_is_german() -> None:
    source = Path('localvoice/core/models.py').read_text(encoding='utf-8')
    assert 'ui_language: str = "de"' in source


def test_onboarding_marks_language_as_confirmed_and_verifies_it() -> None:
    source = Path("localvoice/ui/dialogs.py").read_text(encoding="utf-8")
    assert "self.settings.ui_language_confirmed = True" in source
    assert "self.store.confirm_ui_language(self.language)" in source


def test_onboarding_precedes_main_window() -> None:
    source = Path("localvoice/app.py").read_text(encoding="utf-8")
    assert source.index("OnboardingDialog(store, None)") < source.index("MainWindow(")
