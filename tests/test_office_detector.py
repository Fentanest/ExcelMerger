import unittest
from unittest import mock

from excelmerger.engines import detector as office_detector


class OfficeDetectorTests(unittest.TestCase):
    def test_detect_excel_on_macos_reports_unavailable_without_win32_engine(self):
        with mock.patch("excelmerger.engines.detector.sys.platform", "darwin"), mock.patch(
            "excelmerger.engines.detector.os.path.exists",
            return_value=True,
        ):
            result = office_detector.detect_excel()
        self.assertFalse(result["available"])
        self.assertIn("Windows COM", result["detail"])

    def test_detect_libreoffice_requires_pyuno(self):
        with mock.patch(
            "excelmerger.engines.detector.shutil.which",
            return_value="/usr/bin/soffice",
        ), mock.patch(
            "excelmerger.engines.detector.os.path.exists",
            return_value=True,
        ), mock.patch(
            "excelmerger.engines.detector._pyuno_detail",
            return_value="PyUNO 브리지가 없어 LibreOffice 엔진을 직접 실행할 수 없습니다.",
        ):
            result = office_detector.detect_libreoffice()
        self.assertFalse(result["available"])
        self.assertEqual(result["path"], "/usr/bin/soffice")

    def test_detect_jpype_reports_missing_jars(self):
        with mock.patch(
            "excelmerger.engines.detector._missing_poi_jars",
            return_value=["poi-5.3.0.jar"],
        ):
            result = office_detector.detect_jpype()
        self.assertFalse(result["available"])
        self.assertIn("poi-5.3.0.jar", result["detail"])

    def test_detect_standard_reports_missing_openpyxl(self):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "openpyxl":
                raise ImportError("missing openpyxl")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            result = office_detector.detect_standard()
        self.assertFalse(result["available"])
        self.assertIn("openpyxl", result["detail"])


if __name__ == "__main__":
    unittest.main()
