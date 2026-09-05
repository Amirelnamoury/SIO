from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app import storage as storage_module
from app.database import SessionLocal
from app.main import app
from app.models import Artisan
from app.security import create_access_token
from app.storage import LocalFilesystemStorage


def image_bytes(color=(180, 120, 70), format_name="PNG"):
    output = BytesIO()
    Image.new("RGB", (180, 140), color).save(output, format=format_name)
    return output.getvalue()


def create_artisan(label):
    suffix = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"profil-{label}-{suffix}",
            nom_entreprise=f"Profil {label}",
            metier="plombier",
            email=f"profil-{label}-{suffix}@test.fr",
            password_hash="x",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


def headers(artisan_id):
    return {"Authorization": f"Bearer {create_access_token(artisan_id, 'artisan')}"}


def upload(client, artisan_id, content, name="profil.png", mime="image/png"):
    return client.post(
        "/auth/me/photo-profil",
        headers=headers(artisan_id),
        files={"file": (name, content, mime)},
    )


def test_photo_profil_upload_remplacement_suppression_et_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module, "_storage", LocalFilesystemStorage(str(tmp_path)))
    artisan_a = create_artisan("a")
    artisan_b = create_artisan("b")

    with TestClient(app) as client:
        assert client.get("/auth/me/photo-profil", headers=headers(artisan_a)).status_code == 404

        first = upload(client, artisan_a, image_bytes())
        assert first.status_code == 200, first.text
        assert first.json()["photo_profil_url"] == "/auth/me/photo-profil"

        db = SessionLocal()
        try:
            first_key = db.get(Artisan, artisan_a).photo_profil_key
        finally:
            db.close()
        assert first_key
        assert (tmp_path / first_key).is_file()

        content = client.get("/auth/me/photo-profil", headers=headers(artisan_a))
        assert content.status_code == 200
        assert content.headers["content-type"] == "image/webp"
        with Image.open(BytesIO(content.content)) as image:
            assert image.format == "WEBP"
            assert max(image.size) <= 480

        assert client.get("/auth/me/photo-profil", headers=headers(artisan_b)).status_code == 404

        second = upload(client, artisan_a, image_bytes((40, 100, 160)))
        assert second.status_code == 200, second.text
        db = SessionLocal()
        try:
            second_key = db.get(Artisan, artisan_a).photo_profil_key
        finally:
            db.close()
        assert second_key != first_key
        assert not (tmp_path / first_key).exists()
        assert (tmp_path / second_key).is_file()

        invalid = upload(client, artisan_a, b"pas une image")
        assert invalid.status_code == 400
        assert (tmp_path / second_key).is_file()

        deleted = client.delete("/auth/me/photo-profil", headers=headers(artisan_a))
        assert deleted.status_code == 204
        assert not (tmp_path / second_key).exists()
        me = client.get("/auth/me", headers=headers(artisan_a))
        assert me.status_code == 200
        assert me.json()["photo_profil_url"] is None
