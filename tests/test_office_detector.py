import unittest
from unittest import mock

from excelmerger.engines import detector as office_detector


class OfficeDetectorTests(unittest.TestCase):
    def test_detect_excel_on_macos_checks_app_path(self):
        with mock.patch("excelmerger.engines.detector.sys.platform", "darwin"), mock.patch(
            "excelmerger.engines.detector.os.path.exists",
            return_value=True,
        ):
            result = office_detector.detect_excel()
        self.assertTrue(result["available"])
        self.assertIn("Microsoft Excel", result["detail"])

    def test_detect_libreoffice_prefers_which(self):
        with mock.patch(
            "excelmerger.engines.detector.shutil.which",
            return_value="/usr/bin/soffice",
        ), mock.patch(
            "excelmerger.engines.detector.os.path.exists",
            return_value=True,
        ):
            result = office_detector.detect_libreoffice()
        self.assertTrue(result["available"])
        self.assertEqual(result["path"], "/usr/bin/soffice")

    def test_detect_jpype_reports_missing_jars(self):
        with mock.patch(
            "excelmerger.engines.detector._missing_poi_jars",
            return_value=["poi-5.3.0.jar"],
        ):
            result = office_detector.detect_jpype()
        self.assertFalse(result["available"])
        self.assertIn("poi-5.3.0.jar", result["detail"])


if __name__ == "__main__":
    unittest.main()
