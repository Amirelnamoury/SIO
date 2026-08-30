from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import Artisan, EmailLog


def _artisan(client: TestClient, plan: str, prefix: str) -> tuple[dict, int]:
    email = f"{prefix}-{uuid4().hex}@e2e-test.fr"
    inscription = client.post("/auth/register", json={
        "nom_entreprise": prefix,
        "metier": "plombier",
        "email": email,
        "password": "TestPass123!",
    })
    assert inscription.status_code == 201, inscription.text
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.email == email).one()
        artisan.plan = plan
        artisan.subscription_status = "inactive"
        db.commit()
        artisan_id = artisan.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}, artisan_id


def _devis_envoye(client: TestClient, headers: dict, suffixe: str = "") -> dict:
    contact = client.post("/clients", headers=headers, json={
        "nom": f"Client devis {suffixe}",
        "email": f"client-{uuid4().hex}@e2e-test.fr",
    })
    assert contact.status_code == 201, contact.text
    devis = client.post("/devis", headers=headers, json={
        "client_id": contact.json()["id"],
        "titre": f"Devis à relancer {suffixe}",
        "taux_tva": 20,
        "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": 100}],
    })
    assert devis.status_code == 201, devis.text
    envoi = client.post(f"/devis/{devis.json()['id']}/envoyer", headers=headers)
    assert envoi.status_code == 200, envoi.text
    return envoi.json()


@patch("app.routers.devis.email_service.send_relance_devis", return_value=SimpleNamespace(statut="envoye"))
def test_relance_manuelle_respecte_la_matrice_des_plans(send_email):
    with TestClient(app) as client:
        for plan, statut_attendu in (("gratuit", 402), ("essentiel", 200), ("pro", 200), ("business", 200)):
            headers, _ = _artisan(client, plan, f"relance-{plan}")
            devis = _devis_envoye(client, headers, plan)
            reponse = client.post(f"/devis/{devis['id']}/relancer", headers=headers)
            assert reponse.status_code == statut_attendu, reponse.text
            if statut_attendu == 200:
                assert reponse.json()["email_statut"] == "envoye"
                assert reponse.json()["nb_relances"] == 1
                assert reponse.json()["statut"] == "relance_j3"
    assert send_email.call_count == 3


@patch("app.routers.devis.email_service.send_relance_devis", return_value=SimpleNamespace(statut="envoye"))
def test_essentiel_peut_relancer_un_devis_consulte_et_conserve_son_token(_send_email):
    with TestClient(app) as client:
        headers, _ = _artisan(client, "essentiel", "relance-consulte")
        devis = _devis_envoye(client, headers, "consulte")
        token = devis["token"]
        consultation = client.get(f"/pub/devis/{token}")
        assert consultation.status_code == 200, consultation.text
        assert consultation.json()["statut"] == "consulte"

        reponse = client.post(f"/devis/{devis['id']}/relancer", headers=headers)
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["token"] == token
        assert client.get(f"/pub/devis/{token}").status_code == 200


@patch("app.routers.devis.email_service.send_relance_devis", return_value=SimpleNamespace(statut="envoye"))
def test_statuts_non_eligibles_ne_peuvent_pas_etre_relances(_send_email):
    with TestClient(app) as client:
        headers, _ = _artisan(client, "essentiel", "relance-statuts")
        contact = client.post("/clients", headers=headers, json={"nom": "Client statuts"}).json()
        nouveau = client.post("/devis", headers=headers, json={
            "client_id": contact["id"], "titre": "Nouveau", "taux_tva": 20,
            "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": 100}],
        }).json()
        assert client.post(f"/devis/{nouveau['id']}/relancer", headers=headers).status_code == 400

        for statut in ("signe", "perdu", "expire", "relance_j15"):
            devis = _devis_envoye(client, headers, statut)
            edition = client.patch(f"/devis/{devis['id']}", headers=headers, json={"statut": statut})
            assert edition.status_code == 200, edition.text
            refus = client.post(f"/devis/{devis['id']}/relancer", headers=headers)
            assert refus.status_code == 400, refus.text

        archive = _devis_envoye(client, headers, "archive")
        assert client.delete(f"/devis/{archive['id']}", headers=headers).status_code == 204
        refus_archive = client.post(f"/devis/{archive['id']}/relancer", headers=headers)
        assert refus_archive.status_code == 400, refus_archive.text


@patch("app.routers.devis.email_service.send_relance_devis", return_value=SimpleNamespace(statut="envoye"))
def test_isolation_tenant_interdit_de_relancer_le_devis_d_un_autre_artisan(_send_email):
    with TestClient(app) as client:
        artisan_a, _ = _artisan(client, "essentiel", "relance-tenant-a")
        artisan_b, _ = _artisan(client, "essentiel", "relance-tenant-b")
        devis_b = _devis_envoye(client, artisan_b, "tenant-b")
        intrusion = client.post(f"/devis/{devis_b['id']}/relancer", headers=artisan_a)
        assert intrusion.status_code == 404, intrusion.text


def test_tentative_sans_email_configure_est_honnete_persistante_et_protegee(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", None)
    with TestClient(app) as client:
        headers, artisan_id = _artisan(client, "essentiel", "relance-cooldown")
        devis = _devis_envoye(client, headers, "cooldown")
        token = devis["token"]

        premiere = client.post(f"/devis/{devis['id']}/relancer", headers=headers)
        assert premiere.status_code == 200, premiere.text
        resultat = premiere.json()
        assert resultat["email_statut"] == "non_configure"
        assert "non envoyée" in resultat["message"]
        assert resultat["statut"] == "envoye"
        assert resultat["nb_relances"] == 0
        assert resultat["relance_manuelle_possible"] is False
        assert resultat["relance_manuelle_disponible_le"] is not None

        seconde = client.post(f"/devis/{devis['id']}/relancer", headers=headers)
        assert seconde.status_code == 429, seconde.text
        assert int(seconde.headers["retry-after"]) > 0

        liste = client.get("/devis", headers=headers)
        devis_liste = next(item for item in liste.json() if item["id"] == devis["id"])
        assert devis_liste["relance_manuelle_possible"] is False
        assert devis_liste["token"] == token
        assert client.get(f"/pub/devis/{token}").status_code == 200

        db = SessionLocal()
        try:
            logs = db.query(EmailLog).filter(
                EmailLog.artisan_id == artisan_id,
                EmailLog.devis_id == devis["id"],
                EmailLog.type == "relance_devis",
            ).all()
            assert len(logs) == 1
            assert logs[0].statut == "non_configure"
        finally:
            db.close()


def test_relance_manuelle_facture_essentiel_reste_fonctionnelle():
    with TestClient(app) as client:
        headers, _ = _artisan(client, "essentiel", "relance-facture-regression")
        contact = client.post("/clients", headers=headers, json={"nom": "Client facture"}).json()
        facture = client.post("/factures", headers=headers, json={
            "client_id": contact["id"], "type": "standard", "taux_tva": 20,
            "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": 100}],
        })
        assert facture.status_code == 201, facture.text
        facture_id = facture.json()["id"]
        assert client.patch(f"/factures/{facture_id}", headers=headers, json={"statut": "envoyee"}).status_code == 200
        relance = client.post(f"/factures/{facture_id}/relancer", headers=headers)
        assert relance.status_code == 200, relance.text
        assert relance.json()["nb_relances"] == 1
