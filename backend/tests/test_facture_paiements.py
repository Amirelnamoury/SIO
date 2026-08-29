from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan


def test_paiements_ne_peuvent_jamais_depasser_le_solde_restant():
    with TestClient(app) as client:
        email = f"facture-paiements-{uuid4().hex}@e2e-test.fr"
        inscription = client.post("/auth/register", json={
            "nom_entreprise": "Test paiements facture",
            "metier": "plombier",
            "email": email,
            "password": "TestPass123!",
        })
        assert inscription.status_code == 201, inscription.text
        token = inscription.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        db = SessionLocal()
        try:
            artisan = db.query(Artisan).filter(Artisan.email == email).one()
            artisan.plan = "essentiel"
            artisan.subscription_status = "inactive"
            db.commit()
        finally:
            db.close()

        contact = client.post("/clients", headers=headers, json={"nom": "Client paiement"})
        assert contact.status_code == 201, contact.text
        facture = client.post("/factures", headers=headers, json={
            "client_id": contact.json()["id"],
            "type": "standard",
            "taux_tva": 20,
            "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": 900}],
        })
        assert facture.status_code == 201, facture.text
        facture_id = facture.json()["id"]
        assert facture.json()["montant_ttc"] == 1080

        envoyee = client.patch(f"/factures/{facture_id}", headers=headers, json={"statut": "envoyee"})
        assert envoyee.status_code == 200, envoyee.text

        def payer(montant):
            return client.post(f"/factures/{facture_id}/paiements", headers=headers, json={
                "montant": montant,
                "date_paiement": "2026-08-29",
                "moyen": "virement",
            })

        for montant in (None, 0, -1):
            refus = payer(montant)
            assert refus.status_code == 422, refus.text

        premier = payer(500)
        assert premier.status_code == 201, premier.text
        assert premier.json()["montant_restant"] == 580
        assert premier.json()["statut"] == "partiellement_payee"

        second = payer(500)
        assert second.status_code == 201, second.text
        assert second.json()["montant_paye"] == 1000
        assert second.json()["montant_restant"] == 80

        for montant in (81, 100):
            refus = payer(montant)
            assert refus.status_code == 400, refus.text
            assert refus.json()["detail"] == "Le montant du paiement dépasse le solde restant de la facture."

        solde = payer(80)
        assert solde.status_code == 201, solde.text
        assert solde.json()["montant_paye"] == 1080
        assert solde.json()["montant_restant"] == 0
        assert solde.json()["statut"] == "payee"

        deja_payee = payer(1)
        assert deja_payee.status_code == 400, deja_payee.text
        finale = client.get(f"/factures/{facture_id}", headers=headers)
        assert finale.status_code == 200, finale.text
        assert finale.json()["montant_paye"] == 1080
        assert finale.json()["montant_restant"] == 0


def test_facture_sans_ligne_ne_fait_pas_planter_le_listing():
    """Regression : Facture.montant_ht renvoyait un float (0.0) quand la
    facture n'a aucune ligne, alors que le calcul normal (et taux_tva) sont
    en Decimal (colonnes MONTANT) - montant_ttc plantait alors avec
    TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'
    des qu'une facture sans ligne existait (POST /factures avec lignes=[],
    ou GET /factures/{id} et GET /factures qui la listent)."""
    with TestClient(app) as client:
        email = f"facture-vide-{uuid4().hex}@e2e-test.fr"
        inscription = client.post("/auth/register", json={
            "nom_entreprise": "Test facture vide",
            "metier": "plombier",
            "email": email,
            "password": "TestPass123!",
        })
        assert inscription.status_code == 201, inscription.text
        token = inscription.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        db = SessionLocal()
        try:
            artisan = db.query(Artisan).filter(Artisan.email == email).one()
            artisan.plan = "essentiel"
            db.commit()
        finally:
            db.close()

        contact = client.post("/clients", headers=headers, json={"nom": "Client facture vide"})
        assert contact.status_code == 201, contact.text

        facture = client.post("/factures", headers=headers, json={
            "client_id": contact.json()["id"], "type": "standard", "taux_tva": 20, "lignes": [],
        })
        assert facture.status_code == 201, facture.text
        assert facture.json()["montant_ht"] == 0
        assert facture.json()["montant_ttc"] == 0
        facture_id = facture.json()["id"]

        detail = client.get(f"/factures/{facture_id}", headers=headers)
        assert detail.status_code == 200, detail.text

        liste = client.get("/factures", headers=headers)
        assert liste.status_code == 200, liste.text
        assert any(f["id"] == facture_id for f in liste.json())
