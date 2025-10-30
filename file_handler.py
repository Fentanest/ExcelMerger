import os
import io
import tempfile
import msoffcrypto
import openpyxl
import xlrd
from dialogs import PasswordDialog

class FileHandler:
    def __init__(self, main_window):
        self.main_window = main_window

    def _open_workbook(self, file_path, file_name, data_only=False):
        try:
            if file_path.endswith('.xlsx'):
                return openpyxl.load_workbook(file_path, read_only=False, data_only=data_only)
            elif file_path.endswith('.xls'):
                return xlrd.open_workbook(file_path, formatting_info=True)
        except Exception as e:
            self.main_window.txtLogOutput.append(f"파일 열기 오류 {file_name}: {e}")
            return None
        return None

    def get_sheet_names(self, file_path):
        file_name = os.path.basename(file_path)
        workbook = self._open_workbook(file_path, file_name)
        
        original_file_path = file_path
        processed_file_path = original_file_path

        if workbook is None:
            decrypted_temp_path = self.handle_encrypted_file(original_file_path)
            if decrypted_temp_path:
                workbook = self._open_workbook(decrypted_temp_path, file_name)
                processed_file_path = decrypted_temp_path
                if workbook is None:
                    self.main_window.txtLogOutput.append(f"암호 해독된 파일 열기 실패: {file_name}")
                    return None, None
            else:
                self.main_window.txtLogOutput.append(f"파일을 열 수 없습니다 (암호화 문제 또는 사용자 취소): {file_name}")
                return None, None

        if workbook:
            try:
                if processed_file_path.endswith('.xlsx'):
                    return workbook.sheetnames, processed_file_path
                elif processed_file_path.endswith('.xls'):
                    return workbook.sheet_names(), processed_file_path
            except Exception as e:
                self.main_window.txtLogOutput.append(f"시트 이름 가져오기 오류 {file_name}: {e}")
                return None, None
        return None, None

    def handle_encrypted_file(self, file_path):
        if self.main_window.stop_asking_for_passwords:
            self.main_window.txtLogOutput.append(f"비밀번호 입력을 중단하여 파일을 건너뜁니다: {os.path.basename(file_path)}")
            if self.main_window.debug_mode:
                self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (stopped asking).")
            return None

        self.main_window.txtLogOutput.append(f"암호화된 파일 감지: {os.path.basename(file_path)}")
        password = None
        decrypted_file_buffer = None
        basename = os.path.basename(file_path)
        temp_decrypted_path = None

        if basename in self.main_window.file_passwords:
            try:
                self.main_window.txtLogOutput.append(f'{basename}에 대해 기억된 비밀번호로 열기 시도...')
                decrypted_file_buffer = io.BytesIO()
                with open(file_path, 'rb') as f:
                    office_file = msoffcrypto.OfficeFile(f)
                    office_file.load_key(password=self.main_window.file_passwords[basename])
                    office_file.decrypt(decrypted_file_buffer)
                password = self.main_window.file_passwords[basename]
                self.main_window.txtLogOutput.append("기억된 비밀번호로 열기 성공.")
            except Exception:
                self.main_window.txtLogOutput.append("기억된 비밀번호 실패.")
                decrypted_file_buffer = None

        if not password and self.main_window.use_global_password and self.main_window.global_password:
            try:
                self.main_window.txtLogOutput.append("전역 비밀번호로 열기 시도...")
                decrypted_file_buffer = io.BytesIO()
                with open(file_path, 'rb') as f:
                    office_file = msoffcrypto.OfficeFile(f)
                    office_file.load_key(password=self.main_window.global_password)
                    office_file.decrypt(decrypted_file_buffer)
                password = self.main_window.global_password
                self.main_window.file_passwords[basename] = self.main_window.global_password
                self.main_window.txtLogOutput.append("전역 비밀번호로 열기 성공.")
            except Exception as e:
                self.main_window.txtLogOutput.append(f"전역 비밀번호 실패: {e}")
                decrypted_file_buffer = None

        if not password:
            if self.main_window.debug_mode:
                self.main_window.txtLogOutput.append(f"DEBUG: Showing PasswordDialog for {basename}.")
            dialog = PasswordDialog(basename, self.main_window)
            result = dialog.exec()

            if dialog.stopped:
                self.main_window.stop_asking_for_passwords = True
                self.main_window.txtLogOutput.append("사용자가 중단하여 이후 암호 입력을 건너뜁니다.")
                if self.main_window.debug_mode:
                    self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (dialog stopped).")
                return None

            if result:
                user_password = dialog.lineEditKeepPassword.text()
                if user_password:
                    try:
                        self.main_window.txtLogOutput.append("사용자 입력 비밀번호로 열기 시도...")
                        decrypted_file_buffer = io.BytesIO()
                        with open(file_path, 'rb') as f:
                            office_file = msoffcrypto.OfficeFile(f)
                            office_file.load_key(password=user_password)
                            office_file.decrypt(decrypted_file_buffer)
                        password = user_password
                        self.main_window.txtLogOutput.append("사용자 입력 비밀번호로 열기 성공.")
                        self.main_window.file_passwords[basename] = user_password
                        if dialog.chkKeepPassword.isChecked():
                            self.main_window.global_password = user_password
                            self.main_window.use_global_password = True
                    except Exception as e:
                        self.main_window.txtLogOutput.append(f"사용자 입력 비밀번호 실패: {e}")
                        if self.main_window.debug_mode:
                            self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (user password failed).")
                        return None
                else:
                    self.main_window.txtLogOutput.append("비밀번호가 입력되지 않아 파일을 건너뜁니다.")
                    if self.main_window.debug_mode:
                        self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (empty user password).")
                    return None
            else:
                self.main_window.txtLogOutput.append("사용자가 취소하여 파일을 건너뜁니다.")
                if self.main_window.debug_mode:
                    self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (dialog cancelled).")
                return None

        if password and decrypted_file_buffer:
            fd, temp_decrypted_path = tempfile.mkstemp(suffix=os.path.splitext(file_path)[1], prefix='decrypted_')
            os.close(fd)
            with open(temp_decrypted_path, 'wb') as tmp_f:
                tmp_f.write(decrypted_file_buffer.getbuffer())
            self.main_window.temp_files.append(temp_decrypted_path)
            if self.main_window.debug_mode:
                self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning decrypted path: {temp_decrypted_path}")
            return temp_decrypted_path
        
        if self.main_window.debug_mode:
            self.main_window.txtLogOutput.append(f"DEBUG: handle_encrypted_file returning None (no password worked).")
        return None
