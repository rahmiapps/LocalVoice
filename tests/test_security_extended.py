import json
import tempfile
import unittest
from pathlib import Path

from localvoice.core.security import SecureStore, SecurityError


class ExtendedSecurityTests(unittest.TestCase):
    def test_tampered_ciphertext_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SecureStore(Path(directory) / "security.json")
            token = store.encrypt("secret")
            tampered = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
            with self.assertRaises(SecurityError):
                store.decrypt(tampered)

    def test_corrupt_security_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "security.json"
            original = b"{broken"
            path.write_bytes(original)
            with self.assertRaises(SecurityError):
                SecureStore(path)
            self.assertEqual(path.read_bytes(), original)

    def test_streaming_audio_encryption_roundtrip_and_authentication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = SecureStore(root / "security.json")
            source = root / "voice.wav"
            source.write_bytes((b"RIFF-localvoice-audio" * 10000))
            encrypted = root / "voice.lva"
            restored = root / "restored.wav"
            store.encrypt_file(source, encrypted)
            self.assertNotIn(b"localvoice-audio", encrypted.read_bytes())
            store.decrypt_file(encrypted, restored)
            self.assertEqual(restored.read_bytes(), source.read_bytes())
            payload = bytearray(encrypted.read_bytes())
            payload[len(payload) // 2] ^= 1
            encrypted.write_bytes(payload)
            with self.assertRaises(SecurityError):
                store.decrypt_file(encrypted, root / "tampered.wav")


if __name__ == "__main__":
    unittest.main()
