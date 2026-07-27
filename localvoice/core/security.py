from __future__ import annotations

import base64
import ctypes
import json
import os
import platform
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .paths import CONFIG_DIR, ensure_directories


class SecurityError(RuntimeError):
    pass


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[_DATA_BLOB, Any]:
    buffer = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def _windows_protect(data: bytes) -> bytes:
    if platform.system() != "Windows":
        raise SecurityError("DPAPI is only available on Windows.")
    in_blob, in_buffer = _blob(data)
    entropy_blob, entropy_buffer = _blob(b"LocalVoice-device-key-v2")
    out_blob = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    # CRYPTPROTECT_UI_FORBIDDEN prevents unexpected UI prompts in background mode.
    if not crypt32.CryptProtectData(
        ctypes.byref(in_blob), "LocalVoice", ctypes.byref(entropy_blob), None, None,
        0x1, ctypes.byref(out_blob),
    ):
        raise SecurityError(f"Windows DPAPI protection failed: {ctypes.GetLastError()}")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)
        del in_buffer, entropy_buffer


def _windows_unprotect(data: bytes) -> bytes:
    if platform.system() != "Windows":
        raise SecurityError("DPAPI is only available on Windows.")
    in_blob, in_buffer = _blob(data)
    entropy_blob, entropy_buffer = _blob(b"LocalVoice-device-key-v2")
    out_blob = _DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    if not crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, ctypes.byref(entropy_blob), None, None,
        0x1, ctypes.byref(out_blob),
    ):
        raise SecurityError("The LocalVoice device key could not be unlocked for this Windows user.")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)
        del in_buffer, entropy_buffer


class SecureStore:
    """Encrypt local text using AES-256-GCM and protect its master key.

    Windows device mode uses DPAPI bound to the current Windows user. On Linux,
    the key is stored in a permission-restricted file (0600); enabling a PIN
    wraps it with Scrypt + AES-GCM on every platform.
    """

    MAX_RECORD_BYTES = 64 * 1024
    MAX_TOKEN_BYTES = 16 * 1024 * 1024
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_SECONDS = 30

    def __init__(self, path: Path | None = None) -> None:
        ensure_directories()
        self._uses_default_path = path is None
        self.path = path or CONFIG_DIR / "security.json"
        self._master_key: bytes | None = None
        self._failed_attempts = 0
        self._locked_until = 0.0
        self._lockout_count = 0
        self._record = self._load_or_create()
        self._failed_attempts = max(0, min(int(self._record.get("failed_attempts", 0) or 0), self.MAX_FAILED_ATTEMPTS))
        self._locked_until = max(0.0, float(self._record.get("lockout_until", 0.0) or 0.0))
        self._lockout_count = max(0, min(int(self._record.get("lockout_count", 0) or 0), 10))
        self._load_device_key_if_possible()

    @property
    def has_pin(self) -> bool:
        return self._record.get("mode") == "pin"

    @property
    def is_locked(self) -> bool:
        return self._master_key is None

    @property
    def keyring_cleanup_pending(self) -> bool:
        return bool(self._record.get("keyring_cleanup_pending", False))

    @property
    def lockout_seconds_remaining(self) -> int:
        return max(0, int(self._locked_until - time.time() + 0.999))

    @staticmethod
    def _keyring_account() -> str:
        uid = str(getattr(os, "getuid", lambda: os.environ.get("USERNAME", "user"))())
        return f"localvoice-master-key-{uid}"

    @classmethod
    def _keyring_set(cls, key: bytes) -> bool:
        try:
            import keyring
            backend = keyring.get_keyring()
            if float(getattr(backend, "priority", 0) or 0) <= 0:
                return False
            keyring.set_password("LocalVoice", cls._keyring_account(), base64.b64encode(key).decode("ascii"))
            return True
        except Exception:
            return False

    @classmethod
    def _keyring_get(cls) -> bytes:
        try:
            import keyring
            value = keyring.get_password("LocalVoice", cls._keyring_account())
            if not value:
                raise SecurityError("The Linux desktop keyring does not contain the LocalVoice key.")
            key = base64.b64decode(value, validate=True)
            if len(key) != 32:
                raise SecurityError("The Linux desktop keyring returned an invalid LocalVoice key.")
            return key
        except SecurityError:
            raise
        except Exception as exc:
            raise SecurityError("The Linux desktop keyring is unavailable or locked.") from exc

    @classmethod
    def _retire_keyring_secret(cls, previous_key: bytes) -> bool:
        """Ensure a pre-PIN raw master key no longer remains in the Linux keyring."""
        previous = base64.b64encode(previous_key).decode("ascii")
        try:
            import keyring
            backend = keyring.get_keyring()
            if float(getattr(backend, "priority", 0) or 0) <= 0:
                return False
            # Overwrite first. Even if deletion later fails, the old master key is gone.
            replacement = "retired:" + base64.b64encode(os.urandom(32)).decode("ascii")
            keyring.set_password("LocalVoice", cls._keyring_account(), replacement)
            try:
                keyring.delete_password("LocalVoice", cls._keyring_account())
            except Exception:
                # Some backends cannot delete but can overwrite. Verify that the old key is gone.
                pass
            remaining = keyring.get_password("LocalVoice", cls._keyring_account())
            return remaining != previous
        except Exception:
            return False

    def _device_record_for_key(self, key: bytes) -> dict[str, Any]:
        if platform.system() == "Windows":
            return {
                "version": 3,
                "mode": "device-dpapi",
                "protected_key": base64.b64encode(_windows_protect(key)).decode("ascii"),
            }
        if self._uses_default_path and self._keyring_set(key):
            return {"version": 3, "mode": "device-keyring"}
        return {
            "version": 3,
            "mode": "device-file",
            "key": base64.b64encode(key).decode("ascii"),
        }

    def _persist_auth_state(self) -> None:
        if not self.has_pin:
            return
        self._record["failed_attempts"] = int(self._failed_attempts)
        self._record["lockout_until"] = float(self._locked_until)
        self._record["lockout_count"] = int(self._lockout_count)
        self._write(self._record)

    def _load_or_create(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                if self.path.stat().st_size > self.MAX_RECORD_BYTES:
                    raise SecurityError("The LocalVoice security file is unexpectedly large.")
                record = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(record, dict) or "mode" not in record:
                    raise SecurityError("The LocalVoice security file is invalid.")
                return record
            except SecurityError:
                raise
            except (OSError, json.JSONDecodeError, UnicodeError) as exc:
                raise SecurityError(
                    "The LocalVoice security file is damaged. It was not replaced, because doing so would make existing encrypted history unreadable."
                ) from exc
        key = AESGCM.generate_key(bit_length=256)
        record = self._device_record_for_key(key)
        self._write(record)
        return record

    def _load_device_key_if_possible(self) -> None:
        mode = self._record.get("mode")
        try:
            if mode == "device-dpapi":
                protected = self._b64("protected_key", minimum=16, maximum=4096)
                self._master_key = _windows_unprotect(protected)
            elif mode == "device-keyring":
                self._master_key = self._keyring_get()
            elif mode in {"device-file", "device"}:  # "device" is v1 compatibility.
                self._master_key = self._b64("key", minimum=32, maximum=64)
                if len(self._master_key) != 32:
                    raise SecurityError("The LocalVoice device key has an invalid length.")
                if mode == "device" and platform.system() == "Windows":
                    self._migrate_device_record()
            elif mode == "pin":
                self._master_key = None
            else:
                raise SecurityError("The LocalVoice security mode is unsupported.")
        except (KeyError, ValueError, TypeError, base64.binascii.Error) as exc:
            raise SecurityError("The LocalVoice security key is invalid.") from exc

    def _migrate_device_record(self) -> None:
        if self._master_key is None:
            return
        record = {
            "version": 2,
            "mode": "device-dpapi",
            "protected_key": base64.b64encode(_windows_protect(self._master_key)).decode("ascii"),
        }
        self._record = record
        self._write(record)

    def _b64(self, key: str, *, minimum: int, maximum: int) -> bytes:
        value = self._record.get(key)
        if not isinstance(value, str) or len(value) > maximum * 2:
            raise SecurityError(f"Invalid security field: {key}")
        decoded = base64.b64decode(value, validate=True)
        if not minimum <= len(decoded) <= maximum:
            raise SecurityError(f"Invalid security field length: {key}")
        return decoded

    def _write(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        temp = self.path.with_suffix(".tmp")
        payload = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
        with temp.open("wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        temp.replace(self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    @staticmethod
    def _derive_key_scrypt(pin: str, salt: bytes) -> bytes:
        if len(pin) < 4 or len(pin) > 256:
            raise SecurityError("PIN must contain between 4 and 256 characters.")
        kdf = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1)
        return kdf.derive(pin.encode("utf-8"))

    @staticmethod
    def _derive_key_pbkdf2(pin: str, salt: bytes) -> bytes:
        if len(pin) < 4 or len(pin) > 256:
            raise SecurityError("PIN must contain between 4 and 256 characters.")
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=400_000)
        return kdf.derive(pin.encode("utf-8"))

    def enable_pin(self, pin: str) -> None:
        if self._master_key is None:
            raise SecurityError("Secure store is locked.")
        previous_mode = str(self._record.get("mode", ""))
        master_key = self._master_key
        salt = os.urandom(16)
        nonce = os.urandom(12)
        wrapping_key = self._derive_key_scrypt(pin, salt)
        wrapped = AESGCM(wrapping_key).encrypt(nonce, master_key, b"LocalVoiceKey-v2")
        record = {
            "version": 3,
            "mode": "pin",
            "kdf": "scrypt",
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "wrapped": base64.b64encode(wrapped).decode("ascii"),
            "failed_attempts": 0,
            "lockout_until": 0.0,
            "lockout_count": 0,
        }
        if previous_mode == "device-keyring":
            record["keyring_cleanup_pending"] = True
        self._record = record
        self._write(record)
        if previous_mode == "device-keyring" and self._retire_keyring_secret(master_key):
            self._record.pop("keyring_cleanup_pending", None)
            self._write(self._record)
        self._failed_attempts = 0
        self._locked_until = 0.0
        self._lockout_count = 0

    def unlock(self, pin: str) -> bool:
        if not self.has_pin:
            return True
        if time.time() < self._locked_until:
            return False
        try:
            salt = self._b64("salt", minimum=16, maximum=64)
            nonce = self._b64("nonce", minimum=12, maximum=12)
            wrapped = self._b64("wrapped", minimum=48, maximum=256)
            if self._record.get("kdf") == "scrypt" or int(self._record.get("version", 1)) >= 2:
                wrapping_key = self._derive_key_scrypt(pin, salt)
                associated_data = b"LocalVoiceKey-v2"
            else:
                wrapping_key = self._derive_key_pbkdf2(pin, salt)
                associated_data = b"LocalVoiceKey"
            key = AESGCM(wrapping_key).decrypt(nonce, wrapped, associated_data)
            if len(key) != 32:
                raise SecurityError("Invalid unwrapped key length.")
            self._master_key = key
            self._failed_attempts = 0
            self._locked_until = 0.0
            self._lockout_count = 0
            self._persist_auth_state()
            if bool(self._record.get("keyring_cleanup_pending", False)):
                if self._retire_keyring_secret(key):
                    self._record.pop("keyring_cleanup_pending", None)
                    self._write(self._record)
            if int(self._record.get("version", 1)) < 2:
                # Transparently upgrade a successful v1 PIN record to Scrypt.
                self.enable_pin(pin)
            return True
        except (InvalidTag, SecurityError, ValueError, TypeError, KeyError, base64.binascii.Error):
            self._master_key = None
            self._failed_attempts += 1
            if self._failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                self._lockout_count = min(10, self._lockout_count + 1)
                delay = min(15 * 60, self.LOCKOUT_SECONDS * (2 ** max(0, self._lockout_count - 1)))
                self._locked_until = time.time() + delay
                self._failed_attempts = 0
            self._persist_auth_state()
            return False

    def lock(self) -> None:
        if self.has_pin:
            self._master_key = None

    def disable_pin(self, pin: str) -> bool:
        if not self.has_pin:
            return True
        current_key = self._master_key
        self._master_key = None
        if not self.unlock(pin):
            self._master_key = current_key
            return False
        if self._master_key is None:
            return False
        record = self._device_record_for_key(self._master_key)
        self._record = record
        self._write(record)
        return True

    def encrypt(self, text: str) -> str:
        if self._master_key is None:
            raise SecurityError("Secure store is locked.")
        encoded = text.encode("utf-8")
        if len(encoded) > self.MAX_TOKEN_BYTES:
            raise SecurityError("Text is too large to encrypt safely.")
        nonce = os.urandom(12)
        encrypted = AESGCM(self._master_key).encrypt(nonce, encoded, b"LocalVoiceData-v2")
        return "v2:" + base64.b64encode(nonce + encrypted).decode("ascii")

    def decrypt(self, token: str) -> str:
        if self._master_key is None:
            raise SecurityError("Secure store is locked.")
        if not isinstance(token, str) or len(token) > self.MAX_TOKEN_BYTES * 2:
            raise SecurityError("Encrypted entry is invalid or too large.")
        try:
            if token.startswith("v2:"):
                raw = base64.b64decode(token[3:], validate=True)
                associated_data = b"LocalVoiceData-v2"
            else:  # v1 compatibility
                raw = base64.b64decode(token, validate=True)
                associated_data = b"LocalVoiceData"
            if len(raw) < 12 + 16:
                raise SecurityError("Encrypted entry is truncated.")
            nonce, encrypted = raw[:12], raw[12:]
            return AESGCM(self._master_key).decrypt(nonce, encrypted, associated_data).decode("utf-8")
        except (InvalidTag, ValueError, UnicodeDecodeError, base64.binascii.Error) as exc:
            raise SecurityError("Encrypted entry authentication failed.") from exc

    def encrypt_file(self, source: Path, destination: Path) -> None:
        """Encrypt a potentially large local file using streaming AES-256-GCM."""
        if self._master_key is None:
            raise SecurityError("Secure store is locked.")
        source = source.expanduser().resolve()
        destination = destination.expanduser().resolve()
        if not source.is_file():
            raise SecurityError("The source audio file does not exist.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        nonce = os.urandom(12)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        encryptor = Cipher(algorithms.AES(self._master_key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(b"LocalVoiceAudio-v1")
        try:
            with source.open("rb") as input_file, temporary.open("wb") as output_file:
                output_file.write(b"LVA1" + nonce)
                while True:
                    chunk = input_file.read(1024 * 1024)
                    if not chunk:
                        break
                    output_file.write(encryptor.update(chunk))
                output_file.write(encryptor.finalize())
                output_file.write(encryptor.tag)
                output_file.flush()
                os.fsync(output_file.fileno())
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            temporary.replace(destination)
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def decrypt_file(self, source: Path, destination: Path) -> None:
        """Decrypt and authenticate a LocalVoice audio container."""
        if self._master_key is None:
            raise SecurityError("Secure store is locked.")
        source = source.expanduser().resolve()
        destination = destination.expanduser().resolve()
        if not source.is_file() or source.stat().st_size < 32:
            raise SecurityError("Encrypted audio is missing or truncated.")
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            with source.open("rb") as input_file:
                header = input_file.read(16)
                if len(header) != 16 or header[:4] != b"LVA1":
                    raise SecurityError("Unsupported encrypted audio format.")
                nonce = header[4:]
                total_size = source.stat().st_size
                ciphertext_size = total_size - 16 - 16
                input_file.seek(total_size - 16)
                tag = input_file.read(16)
                input_file.seek(16)
                decryptor = Cipher(algorithms.AES(self._master_key), modes.GCM(nonce, tag)).decryptor()
                decryptor.authenticate_additional_data(b"LocalVoiceAudio-v1")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with temporary.open("wb") as output_file:
                    remaining = ciphertext_size
                    while remaining > 0:
                        chunk = input_file.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise SecurityError("Encrypted audio is truncated.")
                        remaining -= len(chunk)
                        output_file.write(decryptor.update(chunk))
                    output_file.write(decryptor.finalize())
                    output_file.flush()
                    os.fsync(output_file.fileno())
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            temporary.replace(destination)
        except InvalidTag as exc:
            temporary.unlink(missing_ok=True)
            raise SecurityError("Encrypted audio authentication failed.") from exc
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
