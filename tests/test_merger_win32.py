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
        self.options = {
            "sheet_name_rule": "OriginalBoth",
            "only_value_copy": False,
            "sheet_trim_value": 0,
            "sheet_trim_rows": False,
            "sheet_trim_cols": False,
        }
        self.txtLogOutput = type("Log", (), {"append": lambda self, message: None})()
        self.debug_mode = False
        self.file_passwords = {}


class _SheetCollection:
    def __init__(self, workbook):
        self.workbook = workbook

    @property
    def Count(self):
        return len(self.workbook.sheets)

    def __call__(self, key):
        if isinstance(key, int):
            return self.workbook.sheets[key - 1]
        for sheet in self.workbook.sheets:
            if sheet.Name == key:
                return sheet
        raise KeyError(key)

    def __iter__(self):
        return iter(self.workbook.sheets)


class _MergedSheetStub:
    def __init__(self, workbook, name):
        self.workbook = workbook
        self._name = name

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        self._name = value

    def Delete(self):
        self.workbook.sheets = [sheet for sheet in self.workbook.sheets if sheet is not self]


class _MergedWorkbookStub:
    def __init__(self):
        self.sheets = [_MergedSheetStub(self, "Sheet1")]
        self.Worksheets = _SheetCollection(self)

    def Close(self, SaveChanges=False):
        return None


class _SourceWorkbookStub:
    def __init__(self, excel, name):
        self.excel = excel
        self.sheet = _SourceSheetStub(excel, name)
        self.Worksheets = lambda key: self.sheet if key == name else None

    def Close(self, SaveChanges=False):
        return None


class _SourceSheetStub:
    def __init__(self, excel, name):
        self.excel = excel
        self._name = name
        self.Application = excel

    def Copy(self, After=None):
        copied = _MergedSheetStub(After.workbook, self._name)
        insert_at = After.workbook.sheets.index(After) + 1
        After.workbook.sheets.insert(insert_at, copied)
        self.excel.ActiveSheet = copied


class _ExcelAppStub:
    def __init__(self):
        self.Visible = False
        self.DisplayAlerts = False
        self.ActiveSheet = None
        self.Application = self
        self.created_workbook = None
        self.Workbooks = type("Workbooks", (), {})()
        self.Workbooks.Add = self._add

    def _add(self):
        self.created_workbook = _MergedWorkbookStub()
        return self.created_workbook

    def Quit(self):
        return None


class _Win32DispatchStub:
    def __init__(self, excel):
        self.excel = excel

    def Dispatch(self, _name):
        return self.excel


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

    def test_merge_as_sheets_preserves_requested_sheet_order(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        main_window.file_info = {
            "fileA": {"processed_path": "/tmp/a.xlsx", "original_path": "/tmp/a.xlsx"},
            "fileB": {"processed_path": "/tmp/b.xlsx", "original_path": "/tmp/b.xlsx"},
        }

        excel = _ExcelAppStub()
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))
        merger._open_source_workbook = lambda _excel, info, file_name: _SourceWorkbookStub(
            excel,
            "SheetA" if file_name == "fileA" else "SheetB",
        )
        merger.perform_sheet_trim_win32 = lambda workbook, excel_app: None
        captured_orders = []
        merger._save_workbook = lambda workbook, save_path: captured_orders.append(
            [sheet.Name for sheet in workbook.sheets]
        )

        merger.merge_as_sheets_win32(
            ["fileA/SheetA", "fileB/SheetB"],
            "/tmp/output.xlsx",
        )

        self.assertEqual([["a_SheetA", "b_SheetB"]], captured_orders)


if __name__ == "__main__":
    unittest.main()
