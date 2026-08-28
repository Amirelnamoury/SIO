"""Tests de l'abstraction Storage (section Production Readiness).

Local : sur disque reel (tmp_path), aucun mock necessaire.
S3 : boto3 entierement mocke (unittest.mock) - AUCUN appel reseau reel vers
AWS ou Cloudflare n'est jamais effectue par ces tests.
"""
from unittest.mock import MagicMock, patch

import pytest

import app.storage as storage_module
from app.storage import LocalFilesystemStorage, S3CompatibleStorage, get_storage


@pytest.fixture(autouse=True)
def _reset_storage_singleton():
    """get_storage() cache son resultat au niveau module : on le remet a
    None avant/apres chaque test pour que la config de storage_backend du
    test precedent ne fuite jamais dans le suivant."""
    storage_module._storage = None
    yield
    storage_module._storage = None


# ---------- LocalFilesystemStorage ----------


def test_local_save_read_exists_delete(tmp_path):
    s = LocalFilesystemStorage(str(tmp_path))
    assert s.exists("a/b.txt") is False
    assert s.read("a/b.txt") is None

    s.save("a/b.txt", b"contenu")
    assert s.exists("a/b.txt") is True
    assert s.read("a/b.txt") == b"contenu"

    s.delete("a/b.txt")
    assert s.exists("a/b.txt") is False
    assert s.read("a/b.txt") is None


def test_local_delete_fichier_inexistant_ne_leve_pas(tmp_path):
    s = LocalFilesystemStorage(str(tmp_path))
    s.delete("jamais-cree.txt")  # ne doit pas lever


def test_local_traversal_refuse(tmp_path):
    s = LocalFilesystemStorage(str(tmp_path))
    with pytest.raises(ValueError):
        s.save("../../etc/passwd", b"x")
    with pytest.raises(ValueError):
        s.read("../../../etc/passwd")


def test_local_chemin_absolu_refuse(tmp_path):
    s = LocalFilesystemStorage(str(tmp_path))
    with pytest.raises(ValueError):
        s.save("/etc/passwd", b"x")


# ---------- get_storage() dispatch ----------


def test_get_storage_local_par_defaut(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_module.settings, "storage_backend", "local")
    monkeypatch.setattr(storage_module.settings, "uploads_dir", str(tmp_path / "uploads"))
    s = get_storage()
    assert isinstance(s, LocalFilesystemStorage)


def test_get_storage_s3_incomplet_leve_sans_fallback(monkeypatch):
    monkeypatch.setattr(storage_module.settings, "storage_backend", "s3")
    monkeypatch.setattr(storage_module.settings, "s3_endpoint_url", None)
    monkeypatch.setattr(storage_module.settings, "s3_access_key_id", None)
    monkeypatch.setattr(storage_module.settings, "s3_secret_access_key", None)
    monkeypatch.setattr(storage_module.settings, "s3_bucket_name", None)
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND=s3"):
        get_storage()
    # jamais de fallback silencieux : le singleton ne doit pas avoir ete
    # rempli avec un LocalFilesystemStorage a la place.
    assert storage_module._storage is None


def test_get_storage_backend_invalide_leve():
    storage_module.settings.storage_backend = "ftp"
    try:
        with pytest.raises(RuntimeError, match="'local' ou 's3'"):
            get_storage()
    finally:
        storage_module.settings.storage_backend = "local"


# ---------- S3CompatibleStorage (boto3 entierement mocke) ----------


def _s3_storage_avec_client_mock():
    with patch("boto3.client") as boto3_client:
        client = MagicMock()
        boto3_client.return_value = client
        s = S3CompatibleStorage(
            endpoint_url="https://abc123.r2.cloudflarestorage.com",
            access_key_id="AKIAEXEMPLE",
            secret_access_key="secret-exemple",
            bucket_name="suite-artisan-documents",
            region="auto",
        )
        return s, client, boto3_client


def test_s3_save_appelle_put_object():
    s, client, boto3_client = _s3_storage_avec_client_mock()
    s.save("3/abc.pdf", b"contenu")
    client.put_object.assert_called_once_with(Bucket="suite-artisan-documents", Key="3/abc.pdf", Body=b"contenu")
    # aucun appel reseau reel : boto3.client() lui-meme a ete mocke
    boto3_client.assert_called_once()


def test_s3_read_retourne_le_contenu():
    s, client, _ = _s3_storage_avec_client_mock()
    body = MagicMock()
    body.read.return_value = b"contenu-lu"
    client.get_object.return_value = {"Body": body}
    assert s.read("3/abc.pdf") == b"contenu-lu"
    client.get_object.assert_called_once_with(Bucket="suite-artisan-documents", Key="3/abc.pdf")


def test_s3_read_fichier_inexistant_retourne_none():
    from botocore.exceptions import ClientError

    s, client, _ = _s3_storage_avec_client_mock()
    client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
    assert s.read("absent.pdf") is None


def test_s3_delete_appelle_delete_object():
    s, client, _ = _s3_storage_avec_client_mock()
    s.delete("3/abc.pdf")
    client.delete_object.assert_called_once_with(Bucket="suite-artisan-documents", Key="3/abc.pdf")


def test_s3_exists_true_et_false():
    from botocore.exceptions import ClientError

    s, client, _ = _s3_storage_avec_client_mock()
    client.head_object.return_value = {}
    assert s.exists("3/abc.pdf") is True

    client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
    assert s.exists("absent.pdf") is False
