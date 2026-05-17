import pathlib
import tempfile
import unittest

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - test environment without openpyxl
    Workbook = None

from excelmerger.file_handler import FileHandler


class _LogOutput:
    def __init__(self):
        self.messages = []

    def append(self, message):
        self.messages.append(message)


class _MergerPoiStub:
    def __init__(self):
        self.calls = []

    def is_available(self):
        return True

    def get_sheet_names(self, file_path):
        self.calls.append(file_path)
        return ["Sheet1"]


class _MainWindowStub:
    def __init__(self):
        self.txtLogOutput = _LogOutput()
        self.merger_poi = _MergerPoiStub()


class FileHandlerTests(unittest.TestCase):
    @unittest.skipUnless(Workbook is not None, "openpyxl not installed")
    def test_get_sheet_names_uses_openpyxl_for_xlsx_without_starting_poi(self):
        main_window = _MainWindowStub()
        handler = FileHandler(main_window)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = pathlib.Path(tmpdir) / "source.xlsx"
            workbook = Workbook()
            workbook.active.title = "Sheet1"
            workbook.save(source_path)

            sheet_names, processed_path = handler.get_sheet_names(str(source_path))

            self.assertEqual(["Sheet1"], sheet_names)
            self.assertEqual(str(source_path), processed_path)
            self.assertEqual([], main_window.merger_poi.calls)


if __name__ == "__main__":
    unittest.main()
