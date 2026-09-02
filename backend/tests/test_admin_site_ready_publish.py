"""Micro-lot "nettoyer le workflow admin des sites vitrines".

Le moteur de generation automatique n'existe plus : POST .../site/ready ne
doit donc plus exiger un site "genere" avec une date_generation - un site
peut desormais avoir ete realise entierement en dehors de Suite Artisan, qui
se contente d'enregistrer son existence. "genere" reste une valeur technique
historique acceptee pour les sites crees avant le retrait du moteur, mais
n'est plus une etape requise ni produite par quoi que ce soit aujourd'hui.
"""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AdminUser, Artisan, SiteVitrine
from app.security import create_access_token


def _admin_headers() -> dict:
    db = SessionLocal()
    try:
        suffixe = uuid4().hex
        admin = AdminUser(
            email=f"ready-admin-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            nom="Admin Ready",
            actif=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}


def _creer_artisan(metier: str = "plombier") -> int:
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"ready-{suffixe}",
            nom_entreprise=f"Ready {suffixe}",
            metier=metier,
            email=f"ready-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            ville="Lyon",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


def _installer_site_legacy_genere(artisan_id: int) -> None:
    """Simule un site cree par l'ancien moteur avant son retrait : statut
    "genere" en base, sans date_generation (le champ reste optionnel - voir
    le modele - et ne doit plus etre une condition de ready)."""
    db = SessionLocal()
    try:
        db.add(SiteVitrine(artisan_id=artisan_id, statut="genere", config={}))
        db.commit()
    finally:
        db.close()


def test_ready_refuse_si_aucun_site_n_existe():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)

    reponse = client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
    assert reponse.status_code == 409


def test_brouillon_vers_pret_fonctionne_sans_generation():
    """Point 1 + 4 du checklist : un site "brouillon" (nouveau, sans aucune
    generation) peut etre marque pret ; date_generation n'est jamais requis."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)

    site_avant = client.patch(
        f"/admin/api/artisans/{artisan_id}/site",
        json={"services": ["Dépannage"]},
        headers=headers,
    ).json()
    assert site_avant["statut"] == "brouillon"
    assert site_avant["date_generation"] is None

    pret = client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
    assert pret.status_code == 200, pret.text
    assert pret.json()["statut"] == "pret"
    assert pret.json()["date_generation"] is None, "ready ne doit jamais inventer une date_generation"


def test_genere_vers_pret_fonctionne_encore_pour_legacy():
    """Point 2 du checklist : compatibilite ascendante avec les sites deja
    "genere" avant le retrait du moteur."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    _installer_site_legacy_genere(artisan_id)
    client = TestClient(app)

    pret = client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
    assert pret.status_code == 200, pret.text
    assert pret.json()["statut"] == "pret"


def test_publie_vers_pret_est_refuse():
    """Point 3 du checklist : un site deja publie n'est pas une transition
    valide vers "pret" (ni aucune transition incoherente)."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)

    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Dépannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
    client.patch(
        f"/admin/api/artisans/{artisan_id}/site",
        json={"domaine": "ready-publish.test", "url_publique": "https://ready-publish.test"},
        headers=headers,
    )
    publie = client.post(f"/admin/api/artisans/{artisan_id}/site/publish", headers=headers)
    assert publie.status_code == 200, publie.text
    assert publie.json()["statut"] == "publie"

    retour_pret = client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
    assert retour_pret.status_code == 409

    # Une fois publie, un deuxieme "ready" est refuse pour la meme raison :
    # "pret" (deja atteint puis quitte) n'est plus dans les statuts source
    # acceptes par la transition.
    assert client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()["statut"] == "publie"


def test_publish_exige_toujours_domaine_et_url_publique():
    """Point 5 du checklist : la regle de publish n'a pas change - seul
    "ready" a ete assoupli."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    client = TestClient(app)

    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"services": ["Dépannage"]}, headers=headers)
    client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)

    sans_domaine = client.post(f"/admin/api/artisans/{artisan_id}/site/publish", headers=headers)
    assert sans_domaine.status_code == 409
    assert "domaine" in sans_domaine.json()["detail"].lower()

    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"domaine": "avec-url.test"}, headers=headers)
    sans_url = client.post(f"/admin/api/artisans/{artisan_id}/site/publish", headers=headers)
    assert sans_url.status_code == 409

    client.patch(f"/admin/api/artisans/{artisan_id}/site", json={"url_publique": "https://avec-url.test"}, headers=headers)
    avec_les_deux = client.post(f"/admin/api/artisans/{artisan_id}/site/publish", headers=headers)
    assert avec_les_deux.status_code == 200, avec_les_deux.text
    assert avec_les_deux.json()["statut"] == "publie"
