"""Admin V3-only workflow, including explicit migration of historical V2 sites."""

from copy import deepcopy
from uuid import uuid4

from fastapi.testclient import TestClient

from app.admin_service import default_site_config, preview_storage_key
from app.database import SessionLocal
from app.main import app
from app.models import AdminUser, Artisan, SiteVitrine, utcnow
from app.security import create_access_token
from app.storage import get_storage
from generator.v3.grammar import ART_DIRECTIONS
from tests.test_site_v3_only import OLD_V2_PROFILE


def _admin_headers() -> dict:
    db = SessionLocal()
    try:
        suffix = uuid4().hex
        admin = AdminUser(
            email=f"v3-only-admin-{suffix}@test.fr",
            password_hash="unused",
            nom="Admin V3",
            actif=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return {"Authorization": f"Bearer {create_access_token(admin.id, 'admin')}"}
    finally:
        db.close()


def _artisan(metier: str = "plombier") -> int:
    db = SessionLocal()
    try:
        suffix = uuid4().hex
        artisan = Artisan(
            slug=f"v3-only-{suffix}",
            nom_entreprise=f"Entreprise {suffix}",
            metier=metier,
            email=f"artisan-{suffix}@test.fr",
            password_hash="unused",
            ville="Lyon",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


def _install_historical_v2_site(artisan_id: int, *, published: bool = False) -> dict:
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.id == artisan_id).one()
        site = SiteVitrine(
            artisan_id=artisan.id,
            statut="publie" if published else "genere",
            config=default_site_config(artisan),
            design_profile=deepcopy(OLD_V2_PROFILE),
            design_preferences={"engine_version": "v2", "preferred_family": "atelier"},
            storage_key=preview_storage_key(artisan.id),
            domaine="historique.example" if published else None,
            url_publique="https://historique.example" if published else None,
            date_generation=utcnow(),
            date_publication=utcnow() if published else None,
        )
        db.add(site)
        db.commit()
        get_storage().save(site.storage_key, b"<html>livraison-v2-intacte</html>")
        return deepcopy(site.design_profile)
    finally:
        db.close()


def test_nouveau_site_expose_v3_sans_preference_moteur():
    artisan_id = _artisan()
    headers = _admin_headers()
    with TestClient(app) as client:
        before = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers)
        assert before.status_code == 200
        assert before.json()["design_profile"] is None

        generated = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert generated.status_code == 200, generated.text
        body = generated.json()
        assert body["design_profile"]["design_engine_version"].startswith("v3")
        assert body["design_profile"]["art_direction"] in ART_DIRECTIONS
        assert body["design_preferences"] == {}

        preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview", headers=headers)
        assert preview.status_code == 200
        assert 'data-design-engine="v3.0"' in preview.text


def test_preferences_v3_peuvent_etre_sauvees_avant_premiere_generation():
    artisan_id = _artisan("menuisier")
    headers = _admin_headers()
    direction = ART_DIRECTIONS[0]
    with TestClient(app) as client:
        saved = client.patch(
            f"/admin/api/artisans/{artisan_id}/site/design/preferences",
            json={"preferred_direction": direction, "ambience": "warm", "density": "airy"},
            headers=headers,
        )
        assert saved.status_code == 200, saved.text
        generated = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert generated.json()["design_profile"]["art_direction"] == direction


def test_api_normale_ne_permet_plus_de_selectionner_v2():
    artisan_id = _artisan()
    headers = _admin_headers()
    with TestClient(app) as client:
        preference = client.patch(
            f"/admin/api/artisans/{artisan_id}/site/design/preferences",
            json={"engine_version": "v2", "preferred_family": "atelier"},
            headers=headers,
        )
        assert preference.status_code == 422

        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        candidate = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"engine_version": "v2"},
            headers=headers,
        )
        assert candidate.status_code == 422

        legacy_controls = client.patch(
            f"/admin/api/artisans/{artisan_id}/site",
            json={"variante_couleur": 1, "variante_motif": "gradient-mesh"},
            headers=headers,
        )
        assert legacy_controls.status_code == 422


def test_site_v2_produit_une_candidate_v3_sans_modifier_l_actif_publie():
    artisan_id = _artisan()
    original = _install_historical_v2_site(artisan_id, published=True)
    original_html = get_storage().read(preview_storage_key(artisan_id))
    headers = _admin_headers()

    with TestClient(app) as client:
        direct = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert direct.status_code == 422
        assert "alternative V3" in direct.json()["detail"]

        candidate = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_direction": "minimal_architecture"},
            headers=headers,
        )
        assert candidate.status_code == 200, candidate.text
        assert candidate.json()["profile"]["design_engine_version"].startswith("v3")

        current = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        assert current["design_profile"] == original
        assert current["design_preferences"] == {}
        assert current["statut"] == "publie"
        assert current["url_publique"] == "https://historique.example"
        assert get_storage().read(preview_storage_key(artisan_id)) == original_html

        preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate", headers=headers)
        assert preview.status_code == 200
        assert 'data-design-engine="v3.0"' in preview.text
        assert 'var API_BASE = "/admin/preview-api"' in preview.text


def test_site_v2_abandon_preserve_tout_l_etat_actif():
    artisan_id = _artisan()
    original = _install_historical_v2_site(artisan_id, published=True)
    original_html = get_storage().read(preview_storage_key(artisan_id))
    headers = _admin_headers()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        abandoned = client.delete(f"/admin/api/artisans/{artisan_id}/site/design/candidate", headers=headers)
        body = abandoned.json()
        assert body["design_profile"] == original
        assert body["candidate_design_profile"] is None
        assert body["statut"] == "publie"
        assert get_storage().read(preview_storage_key(artisan_id)) == original_html


def test_site_v2_adoption_active_v3_sans_publication_automatique():
    artisan_id = _artisan()
    _install_historical_v2_site(artisan_id, published=True)
    headers = _admin_headers()
    with TestClient(app) as client:
        candidate = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_direction": "cinematic_luxury"},
            headers=headers,
        ).json()["profile"]
        adopted = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", headers=headers)
        assert adopted.status_code == 200, adopted.text
        body = adopted.json()
        assert body["design_profile"] == candidate
        assert body["design_profile"]["design_engine_version"].startswith("v3")
        assert body["candidate_design_profile"] is None
        assert body["statut"] == "genere"
        assert body["date_publication"] is not None


def test_candidate_preview_reste_authentifiee_et_isolee_par_artisan():
    headers = _admin_headers()
    artisan_a = _artisan()
    artisan_b = _artisan("peintre")
    with TestClient(app) as client:
        for artisan_id in (artisan_a, artisan_b):
            client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
            client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)

        assert client.get(f"/admin/api/artisans/{artisan_a}/site/preview/candidate").status_code == 401
        session = client.post(f"/admin/api/artisans/{artisan_a}/site/preview-session/candidate", headers=headers)
        token = session.json()["url"].split("token=")[1].split("&")[0]
        client.cookies.clear()
        opened = client.get(
            f"/admin/api/artisans/{artisan_a}/site/preview/open?token={token}&candidate=1",
            follow_redirects=False,
        )
        assert opened.status_code in (200, 303)
        assert client.get(f"/admin/api/artisans/{artisan_b}/site/preview/candidate").status_code == 403
