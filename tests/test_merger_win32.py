import os
import tempfile
import unittest

from excelmerger.engines.win32 import MergerWin32


class _WorkbookStub:
    def __init__(self, *, writes_on_saveas=True, writes_on_savecopy=False):
        self.calls = []
        self.writes_on_saveas = writes_on_saveas
        self.writes_on_savecopy = writes_on_savecopy
        self.Saved = False

    def SaveAs(self, path, FileFormat, **kwargs):
        self.calls.append(("SaveAs", path, FileFormat, kwargs))
        if self.writes_on_saveas:
            with open(path, "wb") as stream:
                stream.write(b"saved")

    def SaveCopyAs(self, path):
        self.calls.append(("SaveCopyAs", path))
        if self.writes_on_savecopy:
            with open(path, "wb") as stream:
                stream.write(b"copy")


class _MainWindowStub:
    def __init__(self, original_path):
        self.file_info = {
            "source": {
                "original_path": original_path,
            }
        }


class MergerWin32Tests(unittest.TestCase):
    def test_save_workbook_uses_xlsm_format_when_macro_source_exists(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsm"), win32=None)
        workbook = _WorkbookStub()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsm")
            merger._save_workbook(workbook, output_path)
            self.assertTrue(os.path.exists(output_path))

        self.assertEqual(52, workbook.calls[0][2])

    def test_save_workbook_uses_xlsx_format_when_macro_source_missing(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsx"), win32=None)
        workbook = _WorkbookStub()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsx")
            merger._save_workbook(workbook, output_path)
            self.assertTrue(os.path.exists(output_path))

        self.assertEqual(51, workbook.calls[0][2])

    def test_save_workbook_falls_back_to_savecopyas_when_saveas_does_not_create_file(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsx"), win32=None)
        workbook = _WorkbookStub(writes_on_saveas=False, writes_on_savecopy=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsx")
            merger._save_workbook(workbook, output_path)

            self.assertTrue(any(call[0] == "SaveCopyAs" for call in workbook.calls))
            self.assertTrue(os.path.exists(output_path))


if __name__ == "__main__":
    unittest.main()
