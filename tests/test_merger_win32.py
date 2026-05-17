import os
import tempfile
import unittest
import zipfile

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
            self._write_workbook_file(path)

    def SaveCopyAs(self, path):
        self.calls.append(("SaveCopyAs", path))
        if self.writes_on_savecopy:
            self._write_workbook_file(path)

    def _write_workbook_file(self, path):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("xl/workbook.xml", "<workbook/>")


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
        self.pastes = []

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        self._name = value

    def Cells(self, row, column):
        return _CellDestinationStub(self, row, column)

    def Paste(self, Destination=None):
        copied_range = self.workbook.excel.clipboard_range
        if copied_range is None:
            raise RuntimeError("Clipboard is empty")
        Destination.sheet.pastes.append(
            ("paste", copied_range.label, Destination.row, Destination.column, copied_range.Rows.Count, copied_range.Columns.Count)
        )

    def Activate(self):
        return None

    def Delete(self):
        self.workbook.sheets = [sheet for sheet in self.workbook.sheets if sheet is not self]


class _MergedWorkbookStub:
    def __init__(self, excel=None):
        self.excel = excel
        self.sheets = [_MergedSheetStub(self, "Sheet1")]
        self.Worksheets = _SheetCollection(self)
        self.Worksheets.Add = self._add_sheet

    def _add_sheet(self, Before=None, After=None):
        if Before is not None:
            sheet = _MergedSheetStub(self, f"Sheet{len(self.sheets) + 1}")
            insert_at = self.sheets.index(Before)
            self.sheets.insert(insert_at, sheet)
            return sheet
        if After is None:
            sheet = _MergedSheetStub(self, f"Sheet{len(self.sheets) + 1}")
            self.sheets.append(sheet)
            return sheet
        sheet = _MergedSheetStub(self, f"Sheet{len(self.sheets) + 1}")
        insert_at = self.sheets.index(After) + 1
        self.sheets.insert(insert_at, sheet)
        return sheet

    def Close(self, SaveChanges=False):
        return None


class _SourceWorkbookStub:
    def __init__(self, excel, name):
        self.excel = excel
        self.sheet = _SourceSheetStub(excel, name)
        self.Worksheets = lambda key: self.sheet if key == name else None

    def Close(self, SaveChanges=False):
        return None

    def Activate(self):
        return None


class _SourceSheetStub:
    def __init__(self, excel, name):
        self.excel = excel
        self._name = name
        self.Application = excel

    @property
    def Name(self):
        return self._name

    def Activate(self):
        return None

    def Copy(self, Before=None, After=None):
        anchor = Before or After
        copied = _MergedSheetStub(anchor.workbook, self._name)
        if Before is not None:
            insert_at = anchor.workbook.sheets.index(anchor)
        else:
            insert_at = anchor.workbook.sheets.index(anchor) + 1
        anchor.workbook.sheets.insert(insert_at, copied)
        self.excel.ActiveSheet = anchor.workbook.sheets[0]


class _FailingSourceSheetStub(_SourceSheetStub):
    def Copy(self, Before=None, After=None):
        raise RuntimeError("Copy method failed")


class _FailingSourceWorkbookStub(_SourceWorkbookStub):
    def __init__(self, excel, name):
        self.excel = excel
        self.sheet = _FailingSourceSheetStub(excel, name)
        self.Worksheets = lambda key: self.sheet if key == name else None


class _ExcelAppStub:
    def __init__(self):
        self.Visible = False
        self.DisplayAlerts = False
        self.ActiveSheet = None
        self.Application = self
        self.CutCopyMode = False
        self.clipboard_range = None
        self.created_workbook = None
        self.Workbooks = type("Workbooks", (), {})()
        self.Workbooks.Add = self._add

    def _add(self):
        self.created_workbook = _MergedWorkbookStub(self)
        return self.created_workbook

    def Quit(self):
        return None


class _Win32DispatchStub:
    def __init__(self, excel):
        self.excel = excel

    def Dispatch(self, _name):
        return self.excel


class _CellDestinationStub:
    def __init__(self, sheet, row, column):
        self.sheet = sheet
        self.row = row
        self.column = column


class _CountStub:
    def __init__(self, count):
        self.Count = count


class _AxisRangeStub:
    def __init__(self, excel, label, rows, columns, *, fail_direct_destination=False):
        self.excel = excel
        self.label = label
        self.Rows = _CountStub(rows)
        self.Columns = _CountStub(columns)
        self.fail_direct_destination = fail_direct_destination

    def Copy(self, Destination=None):
        if Destination is not None:
            if self.fail_direct_destination:
                raise RuntimeError("Direct destination copy failed")
            Destination.sheet.pastes.append(
                ("direct", self.label, Destination.row, Destination.column, self.Rows.Count, self.Columns.Count)
            )
            return None
        self.excel.clipboard_range = self
        return None


class _AxisSourceSheetStub(_SourceSheetStub):
    def __init__(self, excel, name, rows, columns, *, fail_direct_destination=False):
        super().__init__(excel, name)
        self.UsedRange = _AxisRangeStub(
            excel,
            name,
            rows,
            columns,
            fail_direct_destination=fail_direct_destination,
        )


class _AxisSourceWorkbookStub(_SourceWorkbookStub):
    def __init__(self, excel, name, rows, columns, *, fail_direct_destination=False):
        self.excel = excel
        self.sheet = _AxisSourceSheetStub(
            excel,
            name,
            rows,
            columns,
            fail_direct_destination=fail_direct_destination,
        )
        self.Worksheets = lambda key: self.sheet if key == name else None


class MergerWin32Tests(unittest.TestCase):
    def test_save_workbook_uses_xlsm_format_when_macro_source_exists(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsm"), win32=None)
        workbook = _WorkbookStub()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsm")
            staged_path = merger._save_workbook(workbook, output_path)
            self.assertTrue(os.path.exists(staged_path))
            merger._finalize_saved_workbook(staged_path, output_path)
            self.assertTrue(os.path.exists(output_path))

        self.assertEqual(52, workbook.calls[0][2])

    def test_save_workbook_uses_xlsx_format_when_macro_source_missing(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsx"), win32=None)
        workbook = _WorkbookStub()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsx")
            staged_path = merger._save_workbook(workbook, output_path)
            self.assertTrue(os.path.exists(staged_path))
            merger._finalize_saved_workbook(staged_path, output_path)
            self.assertTrue(os.path.exists(output_path))

        self.assertEqual(51, workbook.calls[0][2])

    def test_save_workbook_falls_back_to_savecopyas_when_saveas_does_not_create_file(self):
        merger = MergerWin32(_MainWindowStub("/tmp/source.xlsx"), win32=None)
        workbook = _WorkbookStub(writes_on_saveas=False, writes_on_savecopy=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.xlsx")
            staged_path = merger._save_workbook(workbook, output_path)
            merger._finalize_saved_workbook(staged_path, output_path)

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
        ) or "/tmp/staged.xlsx"
        merger._finalize_saved_workbook = lambda staged_path, save_path: save_path

        merger.merge_as_sheets_win32(
            ["fileA/SheetA", "fileB/SheetB"],
            "/tmp/output.xlsx",
        )

        self.assertEqual([["a_SheetA", "b_SheetB"]], captured_orders)

    def test_merge_as_sheets_falls_back_when_direct_copy_fails(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        main_window.file_info = {
            "fileA": {"processed_path": "/tmp/a.xlsx", "original_path": "/tmp/a.xlsx"},
        }

        excel = _ExcelAppStub()
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))
        merger._open_source_workbook = lambda _excel, info, file_name: _FailingSourceWorkbookStub(
            excel,
            "SheetA",
        )
        merger.perform_sheet_trim_win32 = lambda workbook, excel_app: None
        fallback_calls = []
        merger._copy_sheet_contents_fallback = lambda source_sheet, merged_workbook, excel_app: (
            fallback_calls.append(source_sheet.Name) or merged_workbook.Worksheets.Add(
                Before=merged_workbook.Worksheets(1)
            )
        )
        captured_orders = []
        merger._save_workbook = lambda workbook, save_path: captured_orders.append(
            [sheet.Name for sheet in workbook.sheets]
        ) or "/tmp/staged.xlsx"
        merger._finalize_saved_workbook = lambda staged_path, save_path: save_path

        merger.merge_as_sheets_win32(
            ["fileA/SheetA"],
            "/tmp/output.xlsx",
        )

        self.assertEqual(["SheetA"], fallback_calls)
        self.assertEqual([["a_SheetA"]], captured_orders)

    def test_merge_by_axis_uses_single_default_sheet(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        excel = _ExcelAppStub()
        workbook = _MergedWorkbookStub()
        workbook.sheets.extend([
            _MergedSheetStub(workbook, "Sheet2"),
            _MergedSheetStub(workbook, "Sheet3"),
        ])
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))

        default_name = merger._ensure_single_sheet_workbook(workbook)

        self.assertEqual("Sheet1", default_name)
        self.assertEqual(["Sheet1"], [sheet.Name for sheet in workbook.sheets])

    def test_copy_range_to_destination_falls_back_to_paste(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        excel = _ExcelAppStub()
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))
        source_workbook = _AxisSourceWorkbookStub(
            excel,
            "SheetA",
            3,
            2,
            fail_direct_destination=True,
        )
        source_sheet = source_workbook.Worksheets("SheetA")
        output_workbook = _MergedWorkbookStub(excel)
        output_sheet = output_workbook.Worksheets(1)
        destination_range = output_sheet.Cells(1, 1)

        merger._copy_range_to_destination(
            excel,
            source_workbook,
            source_sheet,
            source_sheet.UsedRange,
            output_sheet,
            destination_range,
            item="fileA/SheetA",
        )

        self.assertEqual(
            [("paste", "SheetA", 1, 1, 3, 2)],
            output_sheet.pastes,
        )

    def test_merge_horizontally_preserves_requested_sheet_order(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        main_window.file_info = {
            "fileA": {"processed_path": "/tmp/a.xlsx", "original_path": "/tmp/a.xlsx"},
            "fileB": {"processed_path": "/tmp/b.xlsx", "original_path": "/tmp/b.xlsx"},
        }
        excel = _ExcelAppStub()
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))
        merger._open_source_workbook = lambda _excel, info, file_name: (
            _AxisSourceWorkbookStub(excel, "SheetA", 4, 2)
            if file_name == "fileA"
            else _AxisSourceWorkbookStub(excel, "SheetB", 4, 3)
        )
        merger.perform_sheet_trim_win32 = lambda workbook, excel_app: None
        captured_pastes = []
        merger._save_workbook = lambda workbook, save_path: (
            captured_pastes.extend(workbook.Worksheets(1).pastes) or "/tmp/staged.xlsx"
        )
        merger._finalize_saved_workbook = lambda staged_path, save_path: save_path

        merger.merge_horizontally_win32(
            ["fileA/SheetA", "fileB/SheetB"],
            "/tmp/output.xlsx",
        )

        self.assertEqual(
            [
                ("direct", "SheetA", 1, 1, 4, 2),
                ("direct", "SheetB", 1, 3, 4, 3),
            ],
            captured_pastes,
        )

    def test_merge_vertically_preserves_requested_sheet_order(self):
        main_window = _MainWindowStub("/tmp/source.xlsx")
        main_window.file_info = {
            "fileA": {"processed_path": "/tmp/a.xlsx", "original_path": "/tmp/a.xlsx"},
            "fileB": {"processed_path": "/tmp/b.xlsx", "original_path": "/tmp/b.xlsx"},
        }
        excel = _ExcelAppStub()
        merger = MergerWin32(main_window, win32=_Win32DispatchStub(excel))
        merger._open_source_workbook = lambda _excel, info, file_name: (
            _AxisSourceWorkbookStub(excel, "SheetA", 2, 5)
            if file_name == "fileA"
            else _AxisSourceWorkbookStub(excel, "SheetB", 3, 5)
        )
        merger.perform_sheet_trim_win32 = lambda workbook, excel_app: None
        captured_pastes = []
        merger._save_workbook = lambda workbook, save_path: (
            captured_pastes.extend(workbook.Worksheets(1).pastes) or "/tmp/staged.xlsx"
        )
        merger._finalize_saved_workbook = lambda staged_path, save_path: save_path

        merger.merge_vertically_win32(
            ["fileA/SheetA", "fileB/SheetB"],
            "/tmp/output.xlsx",
        )

        self.assertEqual(
            [
                ("direct", "SheetA", 1, 1, 2, 5),
                ("direct", "SheetB", 3, 1, 3, 5),
            ],
            captured_pastes,
        )


if __name__ == "__main__":
    unittest.main()
