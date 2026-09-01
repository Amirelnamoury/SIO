import tempfile
import unittest
from pathlib import Path

from app.admin_service import preview_storage_key
from app.storage import LocalFilesystemStorage


class AdminSiteServiceTests(unittest.TestCase):
    def test_preview_key_is_server_controlled(self):
        self.assertEqual(preview_storage_key(42), "admin-site-previews/42/index.html")
        with self.assertRaises(ValueError):
            preview_storage_key(0)

    def test_storage_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            storage = LocalFilesystemStorage(root)
            with self.assertRaises(ValueError):
                storage.read("../secret.txt")
            with self.assertRaises(ValueError):
                storage.save("nested/../../../secret.txt", b"no")
            self.assertFalse(Path(root).parent.joinpath("secret.txt").exists())

    def test_regeneration_overwrites_same_key(self):
        with tempfile.TemporaryDirectory() as root:
            storage = LocalFilesystemStorage(root)
            key = preview_storage_key(7)
            storage.save(key, b"version-1")
            storage.save(key, b"version-2")
            self.assertEqual(storage.read(key), b"version-2")
            self.assertEqual(len(list(Path(root).rglob("index.html"))), 1)

if __name__ == "__main__":
    unittest.main()
