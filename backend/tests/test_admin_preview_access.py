from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import storage as storage_module
from app.database import SessionLocal
from app.main import app
from app.models import AdminUser, Artisan, Client, EmailLog, Notification
from app.security import create_access_token
from app.storage import LocalFilesystemStorage


def test_preview_locale_utilise_un_handoff_limite_et_ne_cree_aucun_prospect(tmp_path, monkeypatch):
    monkeypatch.setattr(storage_module, "_storage", LocalFilesystemStorage(str(tmp_path)))
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        admin = AdminUser(
            email=f"admin-preview-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            nom="Admin Preview",
            actif=True,
        )
        artisan = Artisan(
            slug=f"artisan-preview-{suffixe}",
            nom_entreprise="Artisan Preview",
            metier="plombier",
            email=f"artisan-preview-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
        )
        autre_artisan = Artisan(
            slug=f"autre-preview-{suffixe}",
            nom_entreprise="Autre Preview",
            metier="plombier",
            email=f"autre-preview-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
        )
        db.add_all([admin, artisan, autre_artisan])
        db.commit()
        db.refresh(admin)
        db.refresh(artisan)
        db.refresh(autre_artisan)
        admin_id = admin.id
        artisan_id = artisan.id
        autre_artisan_id = autre_artisan.id
        slug = artisan.slug
    finally:
        db.close()

    headers = {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}
    with TestClient(app) as client:
        generation = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert generation.status_code == 200, generation.text
        assert generation.json()["preview_disponible"] is True

        sans_auth = client.get(f"/admin/api/artisans/{artisan_id}/site/preview")
        assert sans_auth.status_code == 401

        session = client.post(
            f"/admin/api/artisans/{artisan_id}/site/preview-session",
            headers=headers,
        )
        assert session.status_code == 200, session.text
        ouverture_url = session.json()["url"]
        assert ouverture_url.startswith(f"/admin/api/artisans/{artisan_id}/site/preview/open?token=")
        preview_token = parse_qs(urlparse(ouverture_url).query)["token"][0]

        ouverture = client.get(ouverture_url, follow_redirects=False)
        assert ouverture.status_code == 303
        assert ouverture.headers["location"] == f"/admin/api/artisans/{artisan_id}/site/preview"
        assert "suite_artisan_admin_preview=" in ouverture.headers["set-cookie"]
        assert "HttpOnly" in ouverture.headers["set-cookie"]

        preview = client.get(ouverture.headers["location"])
        assert preview.status_code == 200, preview.text
        assert 'var API_BASE = "/admin/preview-api"' in preview.text
        assert preview.headers["cache-control"] == "no-store"

        autre_preview = client.get(f"/admin/api/artisans/{autre_artisan_id}/site/preview")
        assert autre_preview.status_code == 403

        with patch("app.routers.public.email_service.send_nouvelle_demande_devis") as envoi_email:
            faux_envoi = client.post(
                f"/admin/preview-api/pub/{slug}/demande-devis",
                json={"nom": "Ne doit pas être créé"},
            )
            envoi_email.assert_not_called()
        assert faux_envoi.status_code == 200, faux_envoi.text
        assert "aucune demande n'a ete creee" in faux_envoi.json()["detail"]

        acces_admin_interdit = client.get(
            "/admin/api/dashboard",
            headers={"Authorization": f"Bearer {preview_token}"},
        )
        assert acces_admin_interdit.status_code == 403

    db = SessionLocal()
    try:
        assert db.query(Client).filter(Client.artisan_id == artisan_id).count() == 0
        assert db.query(Notification).filter(Notification.artisan_id == artisan_id).count() == 0
        assert db.query(EmailLog).filter(EmailLog.artisan_id == artisan_id).count() == 0
    finally:
        db.close()
