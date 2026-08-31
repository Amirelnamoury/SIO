"""Refonte Admin (Lot 5) : signaux "a traiter" exposes par les listes Admin
(media_manquant, alternative_en_attente sur AdminArtisanListItem).

Invariant teste : ces signaux reposent uniquement sur des donnees reelles
(medias actifs en base, candidate_design_profile persiste) - jamais sur un
etat invente. Voir backend/app/routers/admin.py::_list_item/_query_artisans.
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
    assert item["alternative_en_attente"] is False


def test_site_genere_sans_media_est_signale():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)
    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Depannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)

    items = client.get("/admin/api/artisans", headers=headers).json()["items"]
    item = _item(items, artisan_id)
    assert item["site_statut"] == "genere"
    assert item["media_manquant"] is True, "un site genere sans aucun media actif doit etre signale"


def test_ajouter_un_logo_actif_leve_le_signal_media_manquant():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)
    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Depannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)

    client.post(
        f"/admin/api/artisans/{artisan_id}/site/media/logo",
        headers=headers,
        files={"file": ("logo.png", _png_bytes(), "image/png")},
    )

    items = client.get("/admin/api/artisans", headers=headers).json()["items"]
    item = _item(items, artisan_id)
    assert item["media_manquant"] is False, "un logo actif reel doit lever le signal, pas une valeur figee"


def test_alternative_en_attente_reflete_la_presence_reelle_d_une_candidate():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)
    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Depannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)

    items_avant = client.get("/admin/api/artisans", headers=headers).json()["items"]
    assert _item(items_avant, artisan_id)["alternative_en_attente"] is False

    client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
    items_apres = client.get("/admin/api/artisans", headers=headers).json()["items"]
    assert _item(items_apres, artisan_id)["alternative_en_attente"] is True

    client.delete(f"/admin/api/artisans/{artisan_id}/site/design/candidate", headers=headers)
    items_abandon = client.get("/admin/api/artisans", headers=headers).json()["items"]
    assert _item(items_abandon, artisan_id)["alternative_en_attente"] is False, "abandonner doit retirer le signal"


def test_les_signaux_sont_aussi_exposes_sur_la_liste_des_sites():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)
    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Depannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)

    items = client.get("/admin/api/sites", headers=headers).json()["items"]
    item = _item(items, artisan_id)
    assert item["media_manquant"] is True
