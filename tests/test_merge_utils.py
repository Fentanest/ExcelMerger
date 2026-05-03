import unittest

from excelmerger.engines.utils import build_output_sheet_name, has_macro_source


class MergeUtilsTests(unittest.TestCase):
    def test_build_output_sheet_name_deduplicates_and_sanitizes(self):
        name = build_output_sheet_name(
            "very_long_file_name.xlsx",
            "bad/name*sheet",
            "OriginalBoth",
            {"very_long_file_name_bad_name_sh"},
        )
        self.assertNotIn("/", name)
        self.assertNotIn("*", name)
        self.assertLessEqual(len(name), 31)

    def test_has_macro_source_detects_xlsm(self):
        file_info = {
            "a.xlsx": {"original_path": "/tmp/a.xlsx"},
            "b.xlsm": {"original_path": "/tmp/b.xlsm"},
        }
        self.assertTrue(has_macro_source(file_info))
        self.assertFalse(has_macro_source({"a.xlsx": {"original_path": "/tmp/a.xlsx"}}))


if __name__ == "__main__":
    unittest.main()
