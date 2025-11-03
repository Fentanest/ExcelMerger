import os
import configparser
from cryptography.fernet import Fernet

class SettingsManager:
    def __init__(self, settings_file='config.ini'):
        self.settings_file = settings_file
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)

    def load_or_create_key(self):
        key_file = 'secret.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def load_settings(self):
        config = configparser.ConfigParser()
        settings = {
            'global_password': "",
            'use_global_password': False,
            'output_encryption_password': "",
            'encrypt_output': False,
            'options': {
                'merge_type': 'Sheet',
                'sheet_name_rule': 'OriginalBoth',
                'sheet_trim_value': 0,
                'sheet_trim_rows': False,
                'sheet_trim_cols': False,
                'only_value_copy': False,
                'use_win32_mode': True
            },
            'debug_mode': False,
            'last_save_path': ""
        }

        if os.path.exists(self.settings_file):
            config.read(self.settings_file)
            if 'Passwords' in config:
                if 'global_password' in config['Passwords'] and config['Passwords']['global_password']:
                    try:
                        decrypted_pass = self.cipher.decrypt(config['Passwords']['global_password'].encode()).decode()
                        settings['global_password'] = decrypted_pass
                    except:
                        settings['global_password'] = ""
                settings['use_global_password'] = config['Passwords'].getboolean('use_global_password', False)

                if 'output_encryption_password' in config['Passwords'] and config['Passwords']['output_encryption_password']:
                    try:
                        decrypted_pass = self.cipher.decrypt(config['Passwords']['output_encryption_password'].encode()).decode()
                        settings['output_encryption_password'] = decrypted_pass
                    except:
                        settings['output_encryption_password'] = ""
                settings['encrypt_output'] = config['Passwords'].getboolean('encrypt_output', False)

            if 'Options' in config:
                settings['options']['merge_type'] = config['Options'].get('merge_type', 'Sheet')
                settings['options']['sheet_name_rule'] = config['Options'].get('sheet_name_rule', 'OriginalBoth')
                settings['options']['sheet_trim_value'] = config['Options'].getint('sheet_trim_value', 0)
                settings['options']['sheet_trim_rows'] = config['Options'].getboolean('sheet_trim_rows', False)
                settings['options']['sheet_trim_cols'] = config['Options'].getboolean('sheet_trim_cols', False)
                settings['options']['only_value_copy'] = config['Options'].getboolean('only_value_copy', False)
                settings['debug_mode'] = config['Options'].getboolean('debug_mode', False)

            if 'Paths' in config and 'last_save_path' in config['Paths']:
                settings['last_save_path'] = config['Paths']['last_save_path']
        
        return settings

    def save_settings(self, settings):
        config = configparser.ConfigParser()
        config.read(self.settings_file)

        if not config.has_section('Passwords'):
            config.add_section('Passwords')
        encrypted_global_pass = self.cipher.encrypt(settings['global_password'].encode()).decode() if settings['global_password'] else ""
        config.set('Passwords', 'global_password', encrypted_global_pass)
        config.set('Passwords', 'use_global_password', str(settings['use_global_password']))
        encrypted_output_pass = self.cipher.encrypt(settings['output_encryption_password'].encode()).decode() if settings['output_encryption_password'] else ""
        config.set('Passwords', 'output_encryption_password', encrypted_output_pass)
        config.set('Passwords', 'encrypt_output', str(settings['encrypt_output']))

        if not config.has_section('Options'):
            config.add_section('Options')
        for key, value in settings['options'].items():
            config.set('Options', key, str(value))
        config.set('Options', 'debug_mode', str(settings['debug_mode']))

        if not config.has_section('Paths'):
            config.add_section('Paths')
        config.set('Paths', 'last_save_path', settings['last_save_path'])

        with open(self.settings_file, 'w') as configfile:
            config.write(configfile)
