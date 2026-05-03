import os
import tempfile
import unittest
from unittest import mock

from excelmerger import updater


class UpdaterTests(unittest.TestCase):
    def test_compare_versions_uses_numeric_order(self):
        self.assertTrue(updater.compare_versions("1.3.0", "2.0.0"))
        self.assertTrue(updater.compare_versions("1.9.9", "1.10.0"))
        self.assertFalse(updater.compare_versions("2.0.0", "2.0.0"))

    def test_select_release_asset_matches_runtime_fragment(self):
        assets = [
            {"name": "ExcelMerger-2.0.0-Windows-x64.zip"},
            {"name": "ExcelMerger-2.0.0-Windows-x64-jre.zip"},
        ]
        with mock.patch("excelmerger.updater._runtime_asset_fragment", return_value="Windows-x64-jre"):
            asset = updater.select_release_asset(assets)
        self.assertEqual(asset["name"], "ExcelMerger-2.0.0-Windows-x64-jre.zip")

    def test_apply_update_returns_manual_in_dev_environment(self):
        update_info = {
            "asset": {"name": "ExcelMerger.zip", "browser_download_url": "https://example.com/ExcelMerger.zip"},
            "html_url": "https://example.com/release",
        }
        with mock.patch("excelmerger.updater.is_packaged_app", return_value=False):
            result = updater.apply_update(update_info)
        self.assertEqual(result["status"], "manual")
        self.assertIn("개발 실행 환경", result["reason"])

    def test_apply_update_prepares_script_in_packaged_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = os.path.join(temp_dir, "ExcelMerger")
            with open(payload_path, "w", encoding="utf-8") as payload_stream:
                payload_stream.write("binary")

            update_info = {
                "asset": {
                    "name": "ExcelMerger-2.0.0-Linux-x64.tar.gz",
                    "browser_download_url": "https://example.com/ExcelMerger.tar.gz",
                },
                "html_url": "https://example.com/release",
            }

            with mock.patch("excelmerger.updater.is_packaged_app", return_value=True), mock.patch(
                "excelmerger.updater.tempfile.mkdtemp",
                return_value=temp_dir,
            ), mock.patch("excelmerger.updater._download_asset"), mock.patch(
                "excelmerger.updater._extract_downloaded_asset",
                return_value=payload_path,
            ), mock.patch("excelmerger.updater._launch_script") as mock_launch, mock.patch(
                "excelmerger.updater.platform.system",
                return_value="Linux",
            ):
                result = updater.apply_update(update_info)

            self.assertEqual(result["status"], "ready")
            self.assertTrue(os.path.exists(result["script_path"]))
            mock_launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
