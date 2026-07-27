from __future__ import annotations

import csv
import json
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .models import Profile, TranscriptionResult
from .postprocess import count_words
from .paths import DATA_DIR, ensure_directories
from .security import SecureStore, SecurityError
from .validation import normalize_language, safe_text


class LocalDatabase:
    MAX_HISTORY_TEXT = 2_000_000
    MAX_VOCABULARY_TEXT = 500

    def __init__(self, secure_store: SecureStore, path: Path | None = None) -> None:
        ensure_directories()
        self.path = path or DATA_DIR / "localvoice.db"
        self.secure_store = secure_store
        self._lock = threading.RLock()
        self._initialize()
        self._migrate_sensitive_plaintext()
        self._cleanup_audio_storage()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA secure_delete=ON")
        connection.execute("PRAGMA temp_store=MEMORY")
        try:
            connection.execute("PRAGMA trusted_schema=OFF")
        except sqlite3.DatabaseError:
            pass
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    final_text TEXT NOT NULL,
                    detected_language TEXT NOT NULL,
                    language_probability REAL NOT NULL DEFAULT 0,
                    translated INTEGER NOT NULL DEFAULT 0,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    word_count INTEGER NOT NULL DEFAULT 0,
                    target_application TEXT NOT NULL DEFAULT '',
                    audio_path TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC);

                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spoken_form TEXT NOT NULL,
                    written_form TEXT NOT NULL,
                    language TEXT NOT NULL DEFAULT 'all',
                    never_translate INTEGER NOT NULL DEFAULT 0,
                    case_sensitive INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_vocabulary_spoken ON vocabulary(spoken_form COLLATE NOCASE);

                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            columns = {row[1] for row in db.execute("PRAGMA table_info(history)").fetchall()}
            if "audio_path" not in columns:
                db.execute("ALTER TABLE history ADD COLUMN audio_path TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def _csv_safe(value: object) -> object:
        if isinstance(value, str) and value and value[0] in {"=", "+", "-", "@"}:
            return "'" + value
        return value

    @staticmethod
    def _audio_reference(value: object) -> str:
        """Store only a safe filename so the database never exposes a user path."""
        name = Path(str(value or "")).name
        if not name or Path(name).suffix.lower() not in {".lva", ".wav"}:
            return ""
        if not name.startswith("recording-") or len(name) > 180:
            return ""
        return name

    @staticmethod
    def _resolve_audio_reference(value: object) -> Path | None:
        reference = LocalDatabase._audio_reference(value)
        if not reference:
            return None
        root = (DATA_DIR / "audio").resolve()
        candidate = (root / reference).resolve()
        return candidate if candidate.parent == root else None

    def _decode_sensitive_text(self, value: object, *, fallback: str = "") -> str:
        text = str(value or "")
        if not text:
            return fallback
        if text.startswith("v2:"):
            try:
                return self.secure_store.decrypt(text)
            except SecurityError:
                return "🔒"
        # Backward compatibility for databases created before all sensitive
        # fields were encrypted. Existing plaintext is migrated at startup.
        return text

    def _migrate_sensitive_plaintext(self) -> None:
        """Encrypt legacy plaintext vocabulary, profiles and target app values."""
        if self.secure_store.is_locked:
            return
        with self._lock, self._connect() as db:
            for row in db.execute("SELECT id, target_application, audio_path FROM history").fetchall():
                value = str(row["target_application"] or "")
                target_value = value if not value or value.startswith("v2:") else self.secure_store.encrypt(safe_text(value, maximum=180))
                audio_reference = self._audio_reference(row["audio_path"])
                legacy_audio = self._resolve_audio_reference(audio_reference)
                if legacy_audio is not None and legacy_audio.suffix.lower() == ".wav" and legacy_audio.is_file():
                    encrypted_audio = legacy_audio.with_suffix(".lva")
                    try:
                        self.secure_store.encrypt_file(legacy_audio, encrypted_audio)
                        legacy_audio.unlink(missing_ok=True)
                        audio_reference = encrypted_audio.name
                    except (OSError, SecurityError):
                        # Keep the legacy reference intact rather than risking data loss.
                        audio_reference = legacy_audio.name
                if target_value != value or audio_reference != str(row["audio_path"] or ""):
                    db.execute(
                        "UPDATE history SET target_application = ?, audio_path = ? WHERE id = ?",
                        (target_value, audio_reference, int(row["id"])),
                    )
            for row in db.execute("SELECT id, spoken_form, written_form FROM vocabulary").fetchall():
                spoken = str(row["spoken_form"] or "")
                written = str(row["written_form"] or "")
                updates: list[object] = []
                if not spoken.startswith("v2:"):
                    updates.append(self.secure_store.encrypt(safe_text(spoken, maximum=self.MAX_VOCABULARY_TEXT)))
                else:
                    updates.append(spoken)
                if not written.startswith("v2:"):
                    updates.append(self.secure_store.encrypt(safe_text(written, maximum=self.MAX_VOCABULARY_TEXT)))
                else:
                    updates.append(written)
                db.execute(
                    "UPDATE vocabulary SET spoken_form = ?, written_form = ? WHERE id = ?",
                    (updates[0], updates[1], int(row["id"])),
                )
            for row in db.execute("SELECT id, name, data_json FROM profiles").fetchall():
                name = str(row["name"] or "")
                payload = str(row["data_json"] or "")
                encrypted_name = name if name.startswith("v2:") else self.secure_store.encrypt(safe_text(name, maximum=120))
                encrypted_payload = payload if payload.startswith("v2:") else self.secure_store.encrypt(safe_text(payload, maximum=self.MAX_HISTORY_TEXT, strip=False))
                db.execute(
                    "UPDATE profiles SET name = ?, data_json = ? WHERE id = ?",
                    (encrypted_name, encrypted_payload, int(row["id"])),
                )

    def _cleanup_audio_storage(self) -> None:
        """Remove orphaned recordings and clear database references to missing files."""
        audio_root = DATA_DIR / "audio"
        with self._lock, self._connect() as db:
            referenced: set[str] = set()
            for row in db.execute("SELECT id, audio_path FROM history WHERE audio_path <> ''").fetchall():
                reference = self._audio_reference(row["audio_path"])
                path = self._resolve_audio_reference(reference)
                if not reference or path is None or not path.is_file():
                    db.execute("UPDATE history SET audio_path = '' WHERE id = ?", (int(row["id"]),))
                else:
                    referenced.add(reference)
        if not audio_root.exists():
            return
        for path in list(audio_root.glob("recording-*.lva")) + list(audio_root.glob("recording-*.wav")):
            if path.name in referenced:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue

    def purge_saved_audio(self, retention_days: int) -> int:
        """Delete expired saved recordings and atomically clear their history references."""
        if retention_days <= 0:
            self._cleanup_audio_storage()
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=min(int(retention_days), 3650))
        removed = 0
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT id, audio_path FROM history WHERE audio_path <> ''").fetchall()
            for row in rows:
                path = self._resolve_audio_reference(row["audio_path"])
                expired = path is None or not path.is_file()
                if not expired and path is not None:
                    try:
                        expired = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < cutoff
                    except OSError:
                        expired = True
                if not expired:
                    continue
                if path is not None:
                    try:
                        if path.exists():
                            path.unlink()
                            removed += 1
                    except OSError:
                        continue
                db.execute("UPDATE history SET audio_path = '' WHERE id = ?", (int(row["id"]),))
        self._cleanup_audio_storage()
        return removed

    def add_history(self, result: TranscriptionResult) -> int | None:
        if self.secure_store.is_locked:
            return None
        original = safe_text(result.original_text, maximum=self.MAX_HISTORY_TEXT, strip=False)
        final = safe_text(result.final_text, maximum=self.MAX_HISTORY_TEXT, strip=False)
        if not final.strip():
            return None
        with self._lock, self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO history (
                    created_at, original_text, final_text, detected_language,
                    language_probability, translated, duration_seconds,
                    word_count, target_application, audio_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    self.secure_store.encrypt(original),
                    self.secure_store.encrypt(final),
                    normalize_language(result.detected_language, allow_auto=False, default="unknown"),
                    max(0.0, min(1.0, float(result.language_probability))),
                    1 if result.translated else 0,
                    max(0.0, min(float(result.duration_seconds), 86_400.0)),
                    max(0, min(int(result.word_count), 5_000_000)),
                    self.secure_store.encrypt(safe_text(result.target_application, maximum=180)),
                    self._audio_reference(result.audio_path),
                ),
            )
            return int(cursor.lastrowid)

    def _decode_row(self, row: sqlite3.Row) -> dict[str, object]:
        try:
            original = self.secure_store.decrypt(row["original_text"])
            final = self.secure_store.decrypt(row["final_text"])
        except SecurityError:
            original = final = "🔒"
        except Exception:
            original = final = "[Unreadable encrypted entry]"
        item = dict(row)
        item["original_text"] = original
        item["final_text"] = final
        item["target_application"] = self._decode_sensitive_text(row["target_application"])
        return item

    def list_history(self, search: str = "", limit: int = 500) -> list[dict[str, object]]:
        limit = max(1, min(int(limit), 100_000))
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        needle = safe_text(search, maximum=500).casefold()
        items: list[dict[str, object]] = []
        for row in rows:
            item = self._decode_row(row)
            if needle and needle not in f"{item['original_text']} {item['final_text']}".casefold():
                continue
            items.append(item)
        return items

    def get_history(self, entry_id: int) -> dict[str, object] | None:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT * FROM history WHERE id = ?", (int(entry_id),)).fetchone()
        return self._decode_row(row) if row else None

    def history_statistics(self) -> dict[str, object]:
        """Return aggregate local usage statistics without decrypting transcript text."""
        with self._lock, self._connect() as db:
            summary = db.execute(
                """
                SELECT COUNT(*) AS total_items,
                       COALESCE(SUM(word_count), 0) AS total_words,
                       COALESCE(SUM(duration_seconds), 0) AS total_seconds,
                       COALESCE(SUM(translated), 0) AS translated_items,
                       COALESCE(SUM(CASE WHEN audio_path <> '' THEN 1 ELSE 0 END), 0) AS audio_items
                FROM history
                """
            ).fetchone()
            languages = db.execute(
                """
                SELECT detected_language, COUNT(*) AS item_count,
                       COALESCE(SUM(word_count), 0) AS word_count
                FROM history
                GROUP BY detected_language
                ORDER BY item_count DESC, detected_language ASC
                LIMIT 100
                """
            ).fetchall()
        return {
            "total_items": int(summary["total_items"] or 0),
            "total_words": int(summary["total_words"] or 0),
            "total_seconds": float(summary["total_seconds"] or 0.0),
            "translated_items": int(summary["translated_items"] or 0),
            "audio_items": int(summary["audio_items"] or 0),
            "languages": [dict(row) for row in languages],
        }

    def update_history_text(self, entry_id: int, original_text: str, final_text: str) -> bool:
        if self.secure_store.is_locked:
            return False
        original = safe_text(original_text, maximum=self.MAX_HISTORY_TEXT, strip=False)
        final = safe_text(final_text, maximum=self.MAX_HISTORY_TEXT, strip=False)
        if not final.strip():
            return False
        with self._lock, self._connect() as db:
            cursor = db.execute(
                "UPDATE history SET original_text = ?, final_text = ?, word_count = ? WHERE id = ?",
                (
                    self.secure_store.encrypt(original),
                    self.secure_store.encrypt(final),
                    count_words(final),
                    int(entry_id),
                ),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _delete_audio_files(paths: Iterable[str]) -> None:
        for value in paths:
            path = LocalDatabase._resolve_audio_reference(value)
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue

    def discard_saved_audio(self, reference: str) -> bool:
        """Delete an encrypted audio item that was not committed to history.

        References are resolved through the same path-confinement logic used by
        history deletion, so callers cannot remove arbitrary files.
        """
        path = self._resolve_audio_reference(reference)
        if path is None:
            return False
        try:
            existed = path.is_file()
            path.unlink(missing_ok=True)
            return existed
        except OSError:
            return False

    def delete_history(self, ids: Iterable[int]) -> None:
        values: list[int] = []
        for value in ids:
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            if number > 0 and number not in values:
                values.append(number)
        if not values:
            return
        placeholders = ",".join("?" for _ in values)
        with self._lock, self._connect() as db:
            paths = [str(row[0]) for row in db.execute(f"SELECT audio_path FROM history WHERE id IN ({placeholders})", values)]
            db.execute(f"DELETE FROM history WHERE id IN ({placeholders})", values)
        self._delete_audio_files(paths)

    def delete_all_history(self) -> None:
        with self._lock, self._connect() as db:
            paths = [str(row[0]) for row in db.execute("SELECT audio_path FROM history")]
            db.execute("DELETE FROM history")
        self._delete_audio_files(paths)

    def purge_history(self, retention_days: int) -> int:
        if retention_days <= 0:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=min(retention_days, 3650))
        with self._lock, self._connect() as db:
            paths = [str(row[0]) for row in db.execute("SELECT audio_path FROM history WHERE created_at < ?", (cutoff.isoformat(),))]
            cursor = db.execute("DELETE FROM history WHERE created_at < ?", (cutoff.isoformat(),))
            count = cursor.rowcount
        self._delete_audio_files(paths)
        return count

    def prune_history(self, maximum_items: int) -> int:
        maximum_items = max(100, min(int(maximum_items), 1_000_000))
        with self._lock, self._connect() as db:
            paths = [str(row[0]) for row in db.execute(
                "SELECT audio_path FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY created_at DESC LIMIT ?)",
                (maximum_items,),
            )]
            cursor = db.execute(
                """
                DELETE FROM history
                WHERE id NOT IN (SELECT id FROM history ORDER BY created_at DESC LIMIT ?)
                """,
                (maximum_items,),
            )
            count = cursor.rowcount
        self._delete_audio_files(paths)
        return count

    def export_history(self, path: Path, file_format: str = "json") -> None:
        rows = self.list_history(limit=100_000)
        path = path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_format = file_format.lower()
        if file_format == "csv":
            fields = list(rows[0].keys()) if rows else ["id", "created_at", "final_text"]
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow({key: self._csv_safe(value) for key, value in row.items()})
        elif file_format == "txt":
            with path.open("w", encoding="utf-8") as file:
                for row in rows:
                    file.write(f"[{row['created_at']}] {row['final_text']}\n\n")
        else:
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

    def export_history_audio(self, entry_id: int, destination: Path) -> bool:
        row = self.get_history(entry_id)
        if not row or not row.get("audio_path"):
            return False
        source = self._resolve_audio_reference(row["audio_path"])
        if source is None or not source.is_file():
            return False
        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".lva":
            self.secure_store.decrypt_file(source, destination)
        else:
            shutil.copy2(source, destination)
        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
        return True

    def clear_saved_audio(self) -> int:
        with self._lock, self._connect() as db:
            paths = [str(row[0]) for row in db.execute("SELECT audio_path FROM history WHERE audio_path <> ''")]
            db.execute("UPDATE history SET audio_path = '' WHERE audio_path <> ''")
        self._delete_audio_files(paths)
        audio_root = DATA_DIR / "audio"
        removed = len(paths)
        if audio_root.exists():
            for path in list(audio_root.glob("recording-*.lva")) + list(audio_root.glob("recording-*.wav")):
                try:
                    path.unlink(missing_ok=True)
                    removed += 1
                except OSError:
                    continue
        return removed

    def list_vocabulary(self) -> list[dict[str, object]]:
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT * FROM vocabulary").fetchall()
        entries: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            item["spoken_form"] = self._decode_sensitive_text(row["spoken_form"])
            item["written_form"] = self._decode_sensitive_text(row["written_form"])
            entries.append(item)
        return sorted(entries, key=lambda item: str(item["spoken_form"]).casefold())

    def add_vocabulary(
        self,
        spoken_form: str,
        written_form: str,
        language: str = "all",
        never_translate: bool = False,
        case_sensitive: bool = False,
    ) -> int:
        spoken = safe_text(spoken_form, maximum=self.MAX_VOCABULARY_TEXT)
        written = safe_text(written_form, maximum=self.MAX_VOCABULARY_TEXT)
        if not spoken or not written:
            raise ValueError("Vocabulary terms must not be empty.")
        lang = "all" if language == "all" else normalize_language(language, allow_auto=False, default="all")
        with self._lock, self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO vocabulary (
                    spoken_form, written_form, language, never_translate,
                    case_sensitive, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    self.secure_store.encrypt(spoken),
                    self.secure_store.encrypt(written),
                    lang,
                    1 if never_translate else 0,
                    1 if case_sensitive else 0,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def update_vocabulary(self, entry_id: int, **changes: object) -> None:
        allowed: dict[str, object] = {}
        if "spoken_form" in changes:
            value = safe_text(changes["spoken_form"], maximum=self.MAX_VOCABULARY_TEXT)
            if value:
                allowed["spoken_form"] = self.secure_store.encrypt(value)
        if "written_form" in changes:
            value = safe_text(changes["written_form"], maximum=self.MAX_VOCABULARY_TEXT)
            if value:
                allowed["written_form"] = self.secure_store.encrypt(value)
        if "language" in changes:
            value = str(changes["language"])
            allowed["language"] = "all" if value == "all" else normalize_language(value, allow_auto=False, default="all")
        for key in ("never_translate", "case_sensitive"):
            if key in changes:
                allowed[key] = 1 if bool(changes[key]) else 0
        if not allowed:
            return
        assignments = ", ".join(f"{key} = ?" for key in allowed)
        values = list(allowed.values()) + [int(entry_id)]
        with self._lock, self._connect() as db:
            db.execute(f"UPDATE vocabulary SET {assignments} WHERE id = ?", values)

    def delete_vocabulary(self, entry_id: int) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM vocabulary WHERE id = ?", (int(entry_id),))

    def list_profiles(self) -> list[Profile]:
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT * FROM profiles").fetchall()
        profiles: list[Profile] = []
        for row in rows:
            try:
                decoded_name = self._decode_sensitive_text(row["name"])
                decoded_payload = self._decode_sensitive_text(row["data_json"])
                if decoded_name == "🔒" or decoded_payload == "🔒":
                    continue
                data = json.loads(decoded_payload)
                data["id"] = row["id"]
                data["name"] = decoded_name or data.get("name", "")
                profiles.append(Profile.from_dict(data))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        return sorted(profiles, key=lambda profile: profile.name.casefold())

    def save_profile(self, profile: Profile) -> int:
        sanitized = Profile.from_dict(profile.to_dict())
        now = datetime.now(timezone.utc).isoformat()
        data = sanitized.to_dict()
        data.pop("id", None)
        with self._lock, self._connect() as db:
            if profile.id is None:
                cursor = db.execute(
                    "INSERT INTO profiles (name, data_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (self.secure_store.encrypt(sanitized.name), self.secure_store.encrypt(json.dumps(data, ensure_ascii=False)), now, now),
                )
                profile.id = int(cursor.lastrowid)
            else:
                db.execute(
                    "UPDATE profiles SET name = ?, data_json = ?, updated_at = ? WHERE id = ?",
                    (self.secure_store.encrypt(sanitized.name), self.secure_store.encrypt(json.dumps(data, ensure_ascii=False)), now, int(profile.id)),
                )
            return int(profile.id)

    def delete_profile(self, profile_id: int) -> None:
        with self._lock, self._connect() as db:
            db.execute("DELETE FROM profiles WHERE id = ?", (int(profile_id),))
