import tempfile
import unittest
from pathlib import Path
from localvoice.core.security import SecureStore


class SecurityTests(unittest.TestCase):
    def test_encrypt_pin_lock_unlock(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "security.json"
            store = SecureStore(path)
            encrypted = store.encrypt("Grüße aus LocalVoice")
            self.assertEqual(store.decrypt(encrypted), "Grüße aus LocalVoice")
            store.enable_pin("1234")
            store.lock()
            self.assertFalse(store.unlock("9999"))
            self.assertTrue(store.unlock("1234"))
            self.assertEqual(store.decrypt(encrypted), "Grüße aus LocalVoice")
            self.assertFalse(store.disable_pin("9999"))
            self.assertTrue(store.disable_pin("1234"))


if __name__ == "__main__":
    unittest.main()
