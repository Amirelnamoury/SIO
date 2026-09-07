"""La serie mensuelle du CA doit couvrir la fenetre entiere.

Avant, `ca_par_mois` etait construit a partir des seuls mois AYANT recu un
paiement : un artisan encaissant en janvier, en fevrier puis en septembre
recevait trois points, que le graphique dessinait cote a cote comme trois
mois consecutifs en progression. Les six mois vides entre les deux
n'existaient nulle part dans la reponse - impossible, pour le client, de
distinguer « pas de paiement ce mois-la » de « ce mois n'a pas ete renvoye ».

Le debut de fenetre etait par ailleurs calcule en retirant 365 jours au
premier du mois courant : il tombait au milieu du mois, et le premier mois
de la serie etait donc tronque sans que rien ne le signale.
"""
from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan
from app.routers.analytics import NB_MOIS_FENETRE, _decaler_mois


def _artisan_abonne(client: TestClient) -> dict:
    email = f"analytics-{uuid4().hex}@e2e-test.fr"
    inscription = client.post("/auth/register", json={
        "nom_entreprise": "Analytics", "metier": "plombier",
        "email": email, "password": "TestPass123!",
    })
    assert inscription.status_code == 201, inscription.text
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.email == email).one()
        artisan.plan = "pro"
        artisan.subscription_status = "active"
        db.commit()
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}


def _facture_payee(client: TestClient, headers: dict, montant: float, jour_paiement: date) -> None:
    contact = client.post("/clients", headers=headers, json={"nom": f"Client {uuid4().hex[:6]}"})
    assert contact.status_code == 201, contact.text
    facture = client.post("/factures", headers=headers, json={
        "client_id": contact.json()["id"], "taux_tva": 20,
        "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": montant}],
    })
    assert facture.status_code == 201, facture.text
    paiement = client.post(f"/factures/{facture.json()['id']}/paiements", headers=headers, json={
        "montant": facture.json()["montant_ttc"], "date_paiement": jour_paiement.isoformat(), "moyen": "virement",
    })
    assert paiement.status_code == 201, paiement.text


def test_la_serie_couvre_douze_mois_pleins_meme_sans_paiement():
    with TestClient(app) as client:
        headers = _artisan_abonne(client)
        mois_courant = date.today().replace(day=1)
        # Un paiement au tout DEBUT d'un mois ancien : avec l'ancienne fenetre
        # a -365 jours, il tombait avant le debut et disparaissait du graphique.
        mois_ancien = _decaler_mois(mois_courant, -(NB_MOIS_FENETRE - 1))
        _facture_payee(client, headers, 1000, mois_ancien)
        _facture_payee(client, headers, 500, mois_courant)

        serie = client.get("/analytics", headers=headers).json()["ca_par_mois"]
        assert len(serie) == NB_MOIS_FENETRE, "la serie doit couvrir toute la fenetre, mois vides compris"

        mois = [point["mois"] for point in serie]
        attendus = [_decaler_mois(mois_ancien, i).strftime("%Y-%m") for i in range(NB_MOIS_FENETRE)]
        assert mois == attendus, "les mois doivent se suivre sans trou et dans l'ordre"

        par_mois = {point["mois"]: point["ca"] for point in serie}
        assert par_mois[mois_ancien.strftime("%Y-%m")] > 0, "un paiement du 1er du mois le plus ancien doit compter"
        assert par_mois[mois_courant.strftime("%Y-%m")] > 0

        vides = [m for m in mois if par_mois[m] == 0]
        assert vides, "les mois sans encaissement doivent etre presents, a zero"


def test_un_compte_sans_aucun_paiement_recoit_quand_meme_la_fenetre():
    # Douze zeros disent « aucun encaissement sur l'annee ». Une liste vide
    # laisse le client deviner s'il n'y a rien ou si la donnee manque.
    with TestClient(app) as client:
        headers = _artisan_abonne(client)
        serie = client.get("/analytics", headers=headers).json()["ca_par_mois"]
        assert len(serie) == NB_MOIS_FENETRE
        assert all(point["ca"] == 0 for point in serie)
