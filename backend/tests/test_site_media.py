from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import storage as storage_module
from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.media_processing import MediaValidationError, process_site_image
from app.models import AdminUser, Artisan
from app.security import create_access_token
from app.storage import LocalFilesystemStorage, valider_cle_relative


def image_bytes(format_name="JPEG", size=(96, 72), color=(30, 110, 160)):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format=format_name)
    return output.getvalue()


def create_accounts():
    suffix = uuid4().hex
    db = SessionLocal()
    try:
        artisan_a = Artisan(
            slug=f"media-a-{suffix}", nom_entreprise="Media A", metier="plombier",
            email=f"media-a-{suffix}@test.fr", password_hash="x",
        )
        artisan_b = Artisan(
            slug=f"media-b-{suffix}", nom_entreprise="Media B", metier="plombier",
            email=f"media-b-{suffix}@test.fr", password_hash="x",
        )
        admin = AdminUser(email=f"media-admin-{suffix}@test.fr", password_hash="x", nom="Admin", actif=True)
        db.add_all([artisan_a, artisan_b, admin])
        db.commit()
        db.refresh(artisan_a)
        db.refresh(artisan_b)
        db.refresh(admin)
        return artisan_a.id, artisan_b.id, admin.id
    finally:
        db.close()


def artisan_headers(artisan_id):
    return {"Authorization": f"Bearer {create_access_token(artisan_id, 'artisan')}"}


def admin_headers(admin_id):
    return {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}


def upload(client, path, headers, *, name="photo.jpg", mime="image/jpeg", content=None, data=None):
    return client.post(
        path,
        headers=headers,
        files={"file": (name, content if content is not None else image_bytes(), mime)},
        data=data or {},
    )


def test_validation_reelle_et_optimisation_image(monkeypatch):
    processed = process_site_image(image_bytes(size=(3200, 1200)), "chantier.jpg", "image/jpeg")
    assert processed.mime_type == "image/webp"
    assert max(processed.width, processed.height) == settings.site_media_web_max_dimension
    with Image.open(BytesIO(processed.web)) as result:
        assert result.format == "WEBP"
    with pytest.raises(MediaValidationError, match="corrompu|illisible"):
        process_site_image(b"pas une image", "fausse.jpg", "image/jpeg")
    with pytest.raises(MediaValidationError, match="extension"):
        process_site_image(image_bytes("PNG"), "photo.jpg", "image/png")
    with pytest.raises(MediaValidationError, match="MIME"):
        process_site_image(image_bytes(), "photo.jpg", "image/png")
    with pytest.raises(MediaValidationError, match="Format non autorise"):
        process_site_image(image_bytes(), "photo.svg", "image/svg+xml")
    monkeypatch.setattr(settings, "site_media_max_source_dimension", 40)
    with pytest.raises(MediaValidationError, match="Dimensions trop grandes"):
        process_site_image(image_bytes(size=(64, 64)), "grand.jpg", "image/jpeg")


@pytest.mark.parametrize("key", ["../secret.webp", "/tmp/image.webp", r"C:\\temp\\image.webp", "a//b.webp"])
def test_storage_media_refuse_les_cles_non_sures(key):
    with pytest.raises(ValueError):
        valider_cle_relative(key)


def test_logo_photos_limite_ordre_et_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module, "_storage", LocalFilesystemStorage(str(tmp_path)))
    artisan_a, artisan_b, admin_id = create_accounts()
    headers_a = artisan_headers(artisan_a)
    headers_b = artisan_headers(artisan_b)

    with TestClient(app) as client:
        logo_a_1 = upload(client, "/site-media/logo", headers_a, name="logo.png", mime="image/png", content=image_bytes("PNG"))
        assert logo_a_1.status_code == 201, logo_a_1.text
        first_key = next(tmp_path.rglob("*.webp"))
        logo_b = upload(client, "/site-media/logo", headers_b, name="logo-b.webp", mime="image/webp", content=image_bytes("WEBP"))
        assert logo_b.status_code == 201, logo_b.text
        logo_a_2 = upload(client, "/site-media/logo", headers_a, name="logo-2.jpg")
        assert logo_a_2.status_code == 201, logo_a_2.text
        assert logo_a_2.json()["id"] != logo_a_1.json()["id"]
        assert not first_key.exists()

        photo_1 = upload(client, "/site-media/photos", headers_a, data={"categorie": "chantier"})
        photo_2 = upload(client, "/site-media/photos", headers_a, name="equipe.jpg", data={"categorie": "equipe"})
        assert photo_1.status_code == photo_2.status_code == 201
        assert photo_1.json()["ordre"] == 0
        assert photo_2.json()["ordre"] == 1

        changed = client.patch(
            f"/site-media/{photo_1.json()['id']}", headers=headers_a,
            json={"categorie": "avant", "actif": False, "alt_text": "Avant travaux"},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["categorie"] == "avant"
        assert changed.json()["actif"] is False

        ordered = client.put(
            "/site-media/photos/order", headers=headers_a,
            json={"media_ids": [photo_2.json()["id"], photo_1.json()["id"]]},
        )
        assert ordered.status_code == 200, ordered.text
        assert [item["id"] for item in ordered.json()] == [photo_2.json()["id"], photo_1.json()["id"]]

        assert client.get(f"/site-media/{photo_1.json()['id']}/content", headers=headers_b).status_code == 404
        assert client.patch(f"/site-media/{photo_1.json()['id']}", headers=headers_b, json={"actif": True}).status_code == 404
        assert client.delete(f"/site-media/{photo_1.json()['id']}", headers=headers_b).status_code == 404

        monkeypatch.setattr(settings, "site_media_max_photos", 2)
        limit = upload(client, "/site-media/photos", headers_a, name="trop.jpg", data={"categorie": "autre"})
        assert limit.status_code == 409
        assert "Limite atteinte" in limit.json()["detail"]

        detail = client.get(f"/admin/api/artisans/{artisan_a}", headers=admin_headers(admin_id))
        assert detail.status_code == 200, detail.text
        assert detail.json()["media"]["logo"]["id"] == logo_a_2.json()["id"]
        assert len(detail.json()["media"]["photos"]) == 2

        assert client.delete("/site-media/logo", headers=headers_a).status_code == 204
        overview_b = client.get("/site-media", headers=headers_b)
        assert overview_b.json()["logo"]["id"] == logo_b.json()["id"]


def test_upload_rejette_faux_mime_corruption_et_taille(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module, "_storage", LocalFilesystemStorage(str(tmp_path)))
    artisan_id, _, _ = create_accounts()
    headers = artisan_headers(artisan_id)
    with TestClient(app) as client:
        fake = upload(client, "/site-media/photos", headers, content=b"texte", data={"categorie": "autre"})
        assert fake.status_code == 400
        mismatch = upload(client, "/site-media/photos", headers, name="photo.jpg", mime="image/png")
        assert mismatch.status_code == 400
        corrupt = upload(client, "/site-media/photos", headers, content=b"\xff\xd8\xff\x00incomplet")
        assert corrupt.status_code == 400
        monkeypatch.setattr(settings, "site_media_max_upload_mo", 1)
        too_large = upload(client, "/site-media/photos", headers, content=b"x" * (1024 * 1024 + 1))
        assert too_large.status_code == 413

