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
from app.models import AdminUser, Artisan, SiteMedia, SiteMediaLibrary, SiteMediaSelection, SiteVitrine
from app.security import create_access_token
from app.storage import LocalFilesystemStorage, valider_cle_relative
from generator.media_selector import select_site_media


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


def test_selecteur_priorite_fallback_et_anti_repetition():
    context = {"artisan_id": 1, "slug": "dupont", "metier": "plombier"}
    library = [
        {"id": 10, "media_id": "plomberie-1", "metier": "plomberie", "usage_recommande": ["hero"], "actif": True},
        {"id": 11, "media_id": "plomberie-2", "metier": "plomberie", "usage_recommande": ["hero"], "actif": True},
    ]
    artisan_result = select_site_media(
        context,
        [{"id": 7, "type_media": "photo", "categorie": "realisation", "ordre": 0, "actif": True}],
        library,
        [],
    )
    assert next(item for item in artisan_result if item["usage"] == "hero")["source"] == "artisan"

    library_result = select_site_media(
        context, [], library,
        [{"library_media_id": 10, "usage": "hero"}] * 4,
    )
    hero = next(item for item in library_result if item["usage"] == "hero")
    assert hero["source"] == "bibliotheque"
    assert hero["library_media_id"] == 11
    first_site = select_site_media(context, [], library, [])
    first_hero = next(item for item in first_site if item["usage"] == "hero")
    second_site = select_site_media(
        {**context, "artisan_id": 2, "slug": "martin"},
        [],
        library,
        [{"library_media_id": first_hero["library_media_id"], "usage": "hero"}],
    )
    second_hero = next(item for item in second_site if item["usage"] == "hero")
    assert second_hero["library_media_id"] != first_hero["library_media_id"]
    fallback = select_site_media(context, [], [], [])
    assert all(item["source"] == "fallback" for item in fallback)


def test_selection_persistante_preview_design_et_acces_public(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module, "_storage", LocalFilesystemStorage(str(tmp_path)))
    artisan_id, _, admin_id = create_accounts()
    headers = artisan_headers(artisan_id)
    admin_auth = admin_headers(admin_id)

    with TestClient(app) as client:
        photo = upload(client, "/site-media/photos", headers, data={"categorie": "realisation"})
        assert photo.status_code == 201, photo.text
        generated = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=admin_auth)
        assert generated.status_code == 200, generated.text
        first_profile = generated.json()["media_profile"]["selections"]
        first_design = generated.json()["design_profile"]
        assert next(item for item in first_profile if item["usage"] == "hero")["site_media_id"] == photo.json()["id"]

        added = upload(client, "/site-media/photos", headers, name="nouvelle.jpg", data={"categorie": "chantier"})
        assert added.status_code == 201
        regenerated = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=admin_auth)
        assert regenerated.status_code == 200, regenerated.text
        assert regenerated.json()["media_profile"]["selections"] == first_profile
        assert regenerated.json()["design_profile"] == first_design

        private_media = client.get(f"/pub/media-a-inexistant/site-media/{photo.json()['id']}")
        assert private_media.status_code == 404

    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.id == artisan_id).one()
        artisan.site_vitrine.statut = "publie"
        db.commit()
        slug = artisan.slug
    finally:
        db.close()

    with TestClient(app) as client:
        public_media = client.get(f"/pub/{slug}/site-media/{photo.json()['id']}")
        assert public_media.status_code == 200
        assert public_media.headers["content-type"] == "image/webp"
        assert public_media.headers["x-content-type-options"] == "nosniff"


def test_bibliotheque_persistante_et_admin_peut_retirer_selection(tmp_path, monkeypatch):
    storage = LocalFilesystemStorage(str(tmp_path))
    monkeypatch.setattr(storage_module, "_storage", storage)
    artisan_id, _, admin_id = create_accounts()
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.id == artisan_id).one()
        site = SiteVitrine(artisan_id=artisan.id, statut="brouillon", config={})
        library = SiteMediaLibrary(
            media_id=f"licensed-{uuid4().hex}", metier="plomberie", sous_categorie="salle_de_bain",
            storage_key=f"library/{uuid4().hex}.webp", thumbnail_key=f"library/{uuid4().hex}-thumb.webp",
            mime_type="image/webp", largeur=96, hauteur=72, orientation="paysage",
            usage_recommande=["hero", "gallery", "about", "featured_project", "before_after"],
            licence="fixture-test", source_nom="Fixture locale", credit="Test", actif=True,
        )
        db.add_all([site, library])
        db.commit()
        db.refresh(library)
        storage.save(library.storage_key, image_bytes("WEBP"))
        storage.save(library.thumbnail_key, image_bytes("WEBP", size=(48, 36)))
        library_id = library.id
    finally:
        db.close()

    auth = admin_headers(admin_id)
    with TestClient(app) as client:
        generated = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=auth)
        assert generated.status_code == 200, generated.text
        hero = next(item for item in generated.json()["media_profile"]["selections"] if item["usage"] == "hero")
        assert hero["source"] == "bibliotheque"
        assert hero["library_media_id"] == library_id
        image = client.get(hero["thumbnail_url"], headers=auth)
        assert image.status_code == 200
        removed = client.delete(
            f"/admin/api/artisans/{artisan_id}/site/media/selections/{hero['id']}",
            headers=auth,
        )
        assert removed.status_code == 204

    db = SessionLocal()
    try:
        assert db.query(SiteMediaSelection).filter(SiteMediaSelection.id == hero["id"]).first() is None
    finally:
        db.close()
