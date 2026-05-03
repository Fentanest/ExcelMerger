import unittest

from excelmerger.engines.win32 import MergerWin32


class _WorkbookStub:
    def __init__(self):
        self.calls = []

    def SaveAs(self, path, FileFormat):
        self.calls.append((path, FileFormat))


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

        merger._save_workbook(workbook, "/tmp/output.xlsm")

        self.assertEqual(52, workbook.calls[0][1])

    def test_save_workbook_uses_xlsx_format_when_macro_source_missing(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsx"), win32=None)
        workbook = _WorkbookStub()

        merger._save_workbook(workbook, "/tmp/output.xlsx")

        self.assertEqual(51, workbook.calls[0][1])


if __name__ == "__main__":
    unittest.main()
