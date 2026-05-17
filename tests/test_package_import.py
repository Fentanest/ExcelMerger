import unittest


class PackageImportTests(unittest.TestCase):
    def test_package_import_does_not_require_gui_runtime(self):
        import excelmerger

        self.assertTrue(callable(excelmerger.main))
        self.assertTrue(hasattr(excelmerger, "__version__"))


if __name__ == "__main__":
    unittest.main()
