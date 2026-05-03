import unittest
from unittest import mock

from excelmerger.engines import standard as merger
from excelmerger.engines.standard import Merger


class MergerAvailabilityTests(unittest.TestCase):
    def test_is_available_reflects_openpyxl_presence(self):
        with mock.patch.object(merger, "openpyxl", new=object()):
            self.assertTrue(Merger(main_window=None).is_available())
        with mock.patch.object(merger, "openpyxl", new=None):
            self.assertFalse(Merger(main_window=None).is_available())

    def test_merge_as_sheets_requires_openpyxl(self):
        with mock.patch.object(merger, "openpyxl", new=None):
            with self.assertRaises(RuntimeError):
                Merger(main_window=None).merge_as_sheets([], "/tmp/out.xlsx")


if __name__ == "__main__":
    unittest.main()
