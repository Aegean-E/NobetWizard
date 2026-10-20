import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from exports import download_font, escape_ics_text, generate_ics


class IcsEscapingTest(unittest.TestCase):
    def test_escapes_text_separators_and_newlines(self):
        self.assertEqual(
            escape_ics_text("A, B; C\\ D\nE"),
            "A\\, B\\; C\\\\ D\\nE",
        )

    def test_generated_event_escapes_personnel_names(self):
        schedule = {date(2026, 2, 1): [{"name": "Ada, M\nBEGIN:VEVENT"}]}

        payload = generate_ics(schedule).decode("utf-8")

        self.assertIn("SUMMARY:Duty Roster: Ada\\, M\\nBEGIN:VEVENT", payload)
        self.assertEqual(payload.count("\nBEGIN:VEVENT"), 1)


class DownloadFontTest(unittest.TestCase):
    def test_existing_font_is_not_downloaded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            path.write_bytes(b"cached")

            with mock.patch("exports.urllib.request.urlopen") as urlopen:
                download_font("https://example.invalid/font.ttf", path)

            urlopen.assert_not_called()
            self.assertEqual(path.read_bytes(), b"cached")

    def test_download_uses_a_timeout_and_replaces_the_target(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"font-bytes"

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            with mock.patch("exports.urllib.request.urlopen", return_value=Response()) as urlopen:
                download_font("https://example.invalid/font.ttf", path)

            urlopen.assert_called_once_with("https://example.invalid/font.ttf", timeout=10)
            self.assertEqual(path.read_bytes(), b"font-bytes")
            self.assertFalse(Path(str(path) + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
