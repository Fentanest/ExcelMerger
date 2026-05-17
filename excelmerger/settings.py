import base64
import binascii
import configparser
import os
import sys

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
    def __init__(self, settings_file=None, key_file=None):
        default_dir = self._default_settings_dir()
        self.settings_file = settings_file or os.path.join(default_dir, "config.ini")
        self.key_file = key_file or os.path.join(default_dir, "secret.key")
        self._legacy_settings_file = (
            os.path.abspath("config.ini") if settings_file is None else None
        )
        self._legacy_key_file = (
            os.path.abspath("secret.key") if key_file is None else None
        )
        self._legacy_cipher = None

    def _default_settings_dir(self):
        if sys.platform == "win32":
            base_dir = os.environ.get("APPDATA") or os.path.expanduser("~/AppData/Roaming")
            return os.path.join(base_dir, "ExcelMerger")
        if sys.platform == "darwin":
            return os.path.join(
                os.path.expanduser("~/Library/Application Support"),
                "ExcelMerger",
            )
        base_dir = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"),
            ".config",
        )
        return os.path.join(base_dir, "excelmerger")

    def _settings_candidates(self):
        candidates = [(self.settings_file, self.key_file)]
        if (
            self._legacy_settings_file
            and self._legacy_settings_file != self.settings_file
            and os.path.exists(self._legacy_settings_file)
        ):
            candidates.append(
                (
                    self._legacy_settings_file,
                    self._legacy_key_file or self.key_file,
                )
            )
        return candidates

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
        loaded_from = self.settings_file
        legacy_key_file = self.key_file

        for candidate_settings, candidate_key in self._settings_candidates():
            if os.path.exists(candidate_settings):
                config.read(candidate_settings)
                loaded_from = candidate_settings
                legacy_key_file = candidate_key
                if candidate_settings != self.settings_file:
                    needs_resave = True
                break

        if config.sections():
            self.key_file = legacy_key_file

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
            if loaded_from != self.settings_file and os.path.exists(loaded_from):
                try:
                    os.remove(loaded_from)
                except OSError:
                    pass
            if legacy_key_file != self.key_file and legacy_key_file and os.path.exists(legacy_key_file):
                try:
                    os.remove(legacy_key_file)
                except OSError:
                    pass

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

        settings_dir = os.path.dirname(self.settings_file)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)

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
