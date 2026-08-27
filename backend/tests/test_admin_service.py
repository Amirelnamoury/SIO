import tempfile
import unittest
from pathlib import Path

from app.admin_service import default_site_config, preview_storage_key, validate_site_variants
from app.models import Artisan
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

    def test_only_generator_supported_variants_are_accepted(self):
        artisan = Artisan(id=1, slug="dupont", nom_entreprise="Dupont", metier="plombier", email="x@example.test", password_hash="x")
        config = default_site_config(artisan)
        config.update({"variante_couleur": 2, "variante_motif": "wave-gradient"})
        validate_site_variants(artisan, config)
        config["variante_motif"] = "brick-rows"
        with self.assertRaises(ValueError):
            validate_site_variants(artisan, config)


if __name__ == "__main__":
    unittest.main()
