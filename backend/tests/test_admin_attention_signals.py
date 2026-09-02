"""Refonte Admin (Lot 5) : signal "a traiter" expose par les listes Admin
(media_manquant sur AdminArtisanListItem).

Invariant teste : ce signal repose uniquement sur des donnees reelles (medias
actifs en base) - jamais sur un etat invente. Voir
backend/app/routers/admin.py::_list_item/_query_artisans.

Le moteur de generation automatique de site (et le signal "alternative_en_attente"
qui accompagnait son workflow de candidate de design) a ete retire depuis :
ce fichier n'utilise donc plus POST .../site/generate pour amener un site a
l'existence, mais PATCH .../site (toujours actif), et l'upload de media passe
desormais par l'espace artisan (/site-media), plus par l'ancien upload Admin.
"""
from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app.database import SessionLocal
from app.main import app
from app.models import AdminUser, Artisan
from app.security import create_access_token


def _admin_headers() -> dict:
    db = SessionLocal()
    try:
        suffixe = uuid4().hex
        admin_row = AdminUser(
            email=f"attention-admin-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            nom="Admin Attention",
            actif=True,
        )
        db.add(admin_row)
        db.commit()
        db.refresh(admin_row)
        admin_id = admin_row.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}


def _creer_artisan(metier: str = "plombier") -> int:
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"attention-{suffixe}",
            nom_entreprise=f"Attention {suffixe}",
            metier=metier,
            email=f"attention-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            ville="Lyon",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


def _artisan_headers(artisan_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(artisan_id, 'artisan')}"}


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color=(10, 120, 90)).save(buffer, format="PNG")
    return buffer.getvalue()


def _item(items: list[dict], artisan_id: int) -> dict:
    for item in items:
        if item["id"] == artisan_id:
            return item
    raise AssertionError(f"artisan {artisan_id} absent de la liste")


def test_artisan_sans_site_n_est_jamais_signale_media_manquant():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)

    items = client.get("/admin/api/artisans", headers=headers).json()["items"]
    item = _item(items, artisan_id)
    assert item["site_statut"] == "non_cree"
    assert item["media_manquant"] is False, "un artisan sans site n'a rien a completer : pas de faux signal"


def test_site_sans_media_est_signale_puis_le_signal_se_leve_avec_un_logo_reel():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)
    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Depannage"]}, headers=headers)

    items = client.get("/admin/api/artisans", headers=headers).json()["items"]
    item = _item(items, artisan_id)
    assert item["site_statut"] == "brouillon"
    assert item["media_manquant"] is True, "un site sans aucun media actif doit etre signale"

    client.post(
        "/site-media/logo",
        headers=_artisan_headers(artisan_id),
        files={"file": ("logo.png", _png_bytes(), "image/png")},
    )

    items_apres = client.get("/admin/api/artisans", headers=headers).json()["items"]
    assert _item(items_apres, artisan_id)["media_manquant"] is False, "un logo actif reel doit lever le signal, pas une valeur figee"

    items_sites = client.get("/admin/api/sites", headers=headers).json()["items"]
    assert _item(items_sites, artisan_id)["media_manquant"] is False, "le signal doit etre coherent entre les listes Artisans et Sites"
