import configparser
import os
import tempfile
import unittest

from excelmerger.settings import SettingsManager

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


class SettingsManagerTests(unittest.TestCase):
    def test_save_and_load_base64_passwords(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = os.path.join(temp_dir, "config.ini")
            manager = SettingsManager(settings_file=settings_path)

            manager.save_settings(
                {
                    "global_password": "test123",
                    "use_global_password": True,
                    "output_encryption_password": "secret456",
                    "encrypt_output": True,
                    "options": {"merge_engine": "excel"},
                    "debug_mode": True,
                    "last_save_path": "/tmp/out.xlsx",
                }
            )

            loaded = manager.load_settings()
            self.assertEqual(loaded["global_password"], "test123")
            self.assertEqual(loaded["output_encryption_password"], "secret456")
            self.assertEqual(loaded["options"]["merge_engine"], "excel")
            self.assertTrue(loaded["debug_mode"])

    @unittest.skipUnless(Fernet is not None, "cryptography not installed")
    def test_load_settings_migrates_legacy_secret_key(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = os.path.join(temp_dir, "config.ini")
            key_path = os.path.join(temp_dir, "secret.key")
            key = Fernet.generate_key()
            cipher = Fernet(key)

            with open(key_path, "wb") as key_stream:
                key_stream.write(key)

            config = configparser.ConfigParser()
            config["Passwords"] = {
                "global_password": cipher.encrypt(b"legacy-pass").decode("utf-8"),
                "use_global_password": "True",
                "output_encryption_password": "",
                "encrypt_output": "False",
            }
            config["Options"] = {"use_win32_mode": "True"}
            with open(settings_path, "w", encoding="utf-8") as config_stream:
                config.write(config_stream)

            manager = SettingsManager(settings_file=settings_path, key_file=key_path)
            loaded = manager.load_settings()

            self.assertEqual(loaded["global_password"], "legacy-pass")
            self.assertEqual(loaded["options"]["merge_engine"], "excel")
            self.assertFalse(os.path.exists(key_path))


if __name__ == "__main__":
    unittest.main()
