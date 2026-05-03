import unittest

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
    def test_get_sheet_names_converts_xlsb_before_poi(self):
        main_window = _MainWindowStub()
        handler = FileHandler(main_window)

        converted_path = "/tmp/converted.xlsx"
        handler.convert_to_xlsx = lambda path: converted_path

        sheet_names, processed_path = handler.get_sheet_names("/tmp/source.xlsb")

        self.assertEqual(["Sheet1"], sheet_names)
        self.assertEqual(converted_path, processed_path)
        self.assertEqual([converted_path], main_window.merger_poi.calls)


if __name__ == "__main__":
    unittest.main()
