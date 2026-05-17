import pathlib
import tempfile
import unittest

try:
    from openpyxl import Workbook, load_workbook
except ImportError:  # pragma: no cover - test environment without openpyxl
    Workbook = None
    load_workbook = None

from excelmerger.engines.detector import detect_jpype
from excelmerger.engines.poi import MergerPOI


class _Log:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)


class _Bar:
    def setValue(self, value):
        self.value = value


class _Label:
    def setText(self, text):
        self.text = text


class _MainWindowStub:
    def __init__(self, file_info):
        self.file_info = file_info
        self.options = {
            "sheet_name_rule": "OriginalBoth",
            "only_value_copy": False,
            "sheet_trim_value": 0,
            "sheet_trim_rows": False,
            "sheet_trim_cols": False,
        }
        self.txtLogOutput = _Log()
        self.progressBar = _Bar()
        self.lblCurrentFile = _Label()


@unittest.skipUnless(detect_jpype()["available"] and Workbook is not None, "JPype/POI runtime unavailable")
class MergerPOITests(unittest.TestCase):
    def test_merge_as_sheets_preserves_formula(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = pathlib.Path(tmpdir) / "formula.xlsx"
            output_path = pathlib.Path(tmpdir) / "merged.xlsx"

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Sheet1"
            sheet["A1"] = 1
            sheet["A2"] = 2
            sheet["A3"] = "=SUM(A1:A2)"
            workbook.save(source_path)

            file_info = {
                "formula.xlsx": {
                    "processed_path": str(source_path),
                }
            }
            merger = MergerPOI(_MainWindowStub(file_info))
            merger.merge_as_sheets(["formula.xlsx/Sheet1"], str(output_path))

            merged = load_workbook(output_path, data_only=False)
            self.assertEqual("=SUM(A1:A2)", merged["formula_Sheet1"]["A3"].value)
            merged.close()


if __name__ == "__main__":
    unittest.main()
