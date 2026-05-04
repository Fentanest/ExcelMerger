import base64
import binascii
import configparser
import os

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


DEFAULT_OPTIONS = {
    "merge_type": "Sheet",
    "sheet_name_rule": "OriginalBoth",
    "sheet_trim_value": 0,
    "sheet_trim_rows": False,
    "sheet_trim_cols": False,
    "only_value_copy": False,
    "merge_engine": "auto",
}


class SettingsManager:
    def __init__(self, settings_file="config.ini", key_file="secret.key"):
        self.settings_file = settings_file
        self.key_file = key_file
        self._legacy_cipher = None

    def load_settings(self):
        config = configparser.ConfigParser()
        settings = {
            "global_password": "",
            "use_global_password": False,
            "output_encryption_password": "",
            "encrypt_output": False,
            "options": dict(DEFAULT_OPTIONS),
            "debug_mode": False,
            "last_save_path": "",
        }
        needs_resave = False

        if os.path.exists(self.settings_file):
            config.read(self.settings_file)

            if "Passwords" in config:
                global_password, migrated_global = self._decode_password(
                    config["Passwords"].get("global_password", "")
                )
                output_password, migrated_output = self._decode_password(
                    config["Passwords"].get("output_encryption_password", "")
                )
                settings["global_password"] = global_password
                settings["output_encryption_password"] = output_password
                settings["use_global_password"] = config["Passwords"].getboolean(
                    "use_global_password",
                    False,
                )
                settings["encrypt_output"] = config["Passwords"].getboolean(
                    "encrypt_output",
                    False,
                )
                needs_resave = needs_resave or migrated_global or migrated_output

            if "Options" in config:
                options_section = config["Options"]
                for key, default_value in DEFAULT_OPTIONS.items():
                    if key == "sheet_trim_value":
                        settings["options"][key] = options_section.getint(key, default_value)
                    elif isinstance(default_value, bool):
                        settings["options"][key] = options_section.getboolean(key, default_value)
                    else:
                        settings["options"][key] = options_section.get(key, default_value)

                if "merge_engine" not in options_section:
                    legacy_win32 = options_section.getboolean("use_win32_mode", False)
                    settings["options"]["merge_engine"] = "excel" if legacy_win32 else "auto"
                    needs_resave = True

                settings["debug_mode"] = options_section.getboolean("debug_mode", False)

            if "Paths" in config:
                settings["last_save_path"] = config["Paths"].get("last_save_path", "")

        if needs_resave:
            self.save_settings(settings)
            self._remove_legacy_key()

        return settings

    def save_settings(self, settings):
        config = configparser.ConfigParser()

        config["Passwords"] = {
            "global_password": self._encode_password(settings.get("global_password", "")),
            "use_global_password": str(settings.get("use_global_password", False)),
            "output_encryption_password": self._encode_password(
                settings.get("output_encryption_password", "")
            ),
            "encrypt_output": str(settings.get("encrypt_output", False)),
        }

        config["Options"] = {}
        for key, default_value in DEFAULT_OPTIONS.items():
            value = settings.get("options", {}).get(key, default_value)
            config["Options"][key] = str(value)
        config["Options"]["debug_mode"] = str(settings.get("debug_mode", False))

        config["Paths"] = {"last_save_path": settings.get("last_save_path", "")}

        with open(self.settings_file, "w", encoding="utf-8") as configfile:
            config.write(configfile)

        self._remove_legacy_key()

    def _encode_password(self, password):
        if not password:
            return ""
        return base64.b64encode(password.encode("utf-8")).decode("utf-8")

    def _decode_password(self, encoded_password):
        if not encoded_password:
            return "", False

        try:
            decoded = base64.b64decode(encoded_password.encode("utf-8"), validate=True)
            return decoded.decode("utf-8"), False
        except (ValueError, binascii.Error, UnicodeDecodeError):
            legacy_value = self._decode_legacy_password(encoded_password)
            if legacy_value is not None:
                return legacy_value, True
            return "", False

    def _decode_legacy_password(self, encrypted_password):
        cipher = self._load_legacy_cipher()
        if cipher is None:
            return None

        try:
            return cipher.decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
        except Exception:
            return None

    def _load_legacy_cipher(self):
        if self._legacy_cipher is not None:
            return self._legacy_cipher

        if Fernet is None or not os.path.exists(self.key_file):
            return None

        try:
            with open(self.key_file, "rb") as key_stream:
                self._legacy_cipher = Fernet(key_stream.read())
        except Exception:
            self._legacy_cipher = None

        return self._legacy_cipher

    def _remove_legacy_key(self):
        if os.path.exists(self.key_file):
            try:
                os.remove(self.key_file)
            except OSError:
                pass
