from __future__ import annotations

from pathlib import Path
from platformdirs import PlatformDirs


dirs = PlatformDirs("LocalVoice", "Rahmi Apps", roaming=True)

CONFIG_DIR = Path(dirs.user_config_dir)
DATA_DIR = Path(dirs.user_data_dir)
CACHE_DIR = Path(dirs.user_cache_dir)
LOG_DIR = Path(dirs.user_log_dir)
MODELS_DIR = DATA_DIR / "models"
TRANSLATION_MODELS_DIR = DATA_DIR / "translation-models"
TEMP_DIR = CACHE_DIR / "recordings"
EXPORT_DIR = DATA_DIR / "exports"


def ensure_directories() -> None:
    for directory in (
        CONFIG_DIR,
        DATA_DIR,
        CACHE_DIR,
        LOG_DIR,
        MODELS_DIR,
        TRANSLATION_MODELS_DIR,
        TEMP_DIR,
        EXPORT_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
        try:
            directory.chmod(0o700)
        except OSError:
            pass
