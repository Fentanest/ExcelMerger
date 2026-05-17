import unittest

from excelmerger.file_registry import build_display_name, source_already_added


class FileRegistryTests(unittest.TestCase):
    def test_build_display_name_disambiguates_duplicate_basenames(self):
        existing = {
            "report.xlsx": {
                "original_path": "/tmp/a/report.xlsx",
            }
        }
        display_name = build_display_name("/tmp/b/report.xlsx", existing)
        self.assertNotEqual("report.xlsx", display_name)
        self.assertIn("report.xlsx", display_name)

    def test_source_already_added_uses_full_path(self):
        existing = {
            "report.xlsx": {
                "original_path": "/tmp/a/report.xlsx",
            }
        }
        self.assertTrue(source_already_added("/tmp/a/report.xlsx", existing))
        self.assertFalse(source_already_added("/tmp/b/report.xlsx", existing))


if __name__ == "__main__":
    unittest.main()
