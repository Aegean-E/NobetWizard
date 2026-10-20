import json
import tempfile
import unittest
from pathlib import Path

from storage import atomic_write_json


class AtomicWriteJsonTest(unittest.TestCase):
    def test_writes_and_overwrites_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            atomic_write_json(path, {"first": 1})
            atomic_write_json(path, {"second": [1, 2]})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"second": [1, 2]})

    def test_leaves_no_temporary_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            atomic_write_json(path, {"ok": True})

            self.assertEqual([p.name for p in Path(folder).iterdir()], ["data.json"])

    def test_creates_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested" / "data.json"
            atomic_write_json(path, {"ok": True})

            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
