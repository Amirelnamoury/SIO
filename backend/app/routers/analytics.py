from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_active_subscription
from app.models import Artisan, Client, Devis, Facture, Paiement
from app.schemas import AnalyticsMois, AnalyticsOut

router = APIRouter(prefix="/analytics", tags=["analytics"])

DEVIS_STATUTS_FINAUX = ("signe", "perdu", "expire")


@router.get("", response_model=AnalyticsOut)
def obtenir_analytics(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Statistiques de pilotage. Fonction payante : necessite un abonnement actif."""
    aujourdhui = date.today()

    # ---------- CA par mois (12 derniers mois) ----------
    depuis_12_mois = date(aujourdhui.year, aujourdhui.month, 1) - timedelta(days=365)
    paiements = (
        db.query(Paiement.date_paiement, Paiement.montant)
        .join(Facture, Paiement.facture_id == Facture.id)
        .filter(Facture.artisan_id == artisan.id, Paiement.date_paiement >= depuis_12_mois)
        .all()
    )
    ca_par_mois_dict = defaultdict(float)
    for date_paiement, montant in paiements:
        cle = date_paiement.strftime("%Y-%m")
        ca_par_mois_dict[cle] += montant
    ca_par_mois = [AnalyticsMois(mois=k, ca=round(v, 2)) for k, v in sorted(ca_par_mois_dict.items())]

    # ---------- Devis ----------
    devis_total = db.query(Devis).filter(Devis.artisan_id == artisan.id).count()
    devis_signes = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut == "signe").count()
    devis_decides = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_FINAUX)).count()
    taux_acceptation = round((devis_signes / devis_decides) * 100, 1) if devis_decides else 0.0

    devis_signes_avec_lignes = (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.artisan_id == artisan.id, Devis.statut == "signe")
        .all()
    )
    montants_signes = [d.montant_ttc for d in devis_signes_avec_lignes if d.montant_ttc]
    panier_moyen = round(sum(montants_signes) / len(montants_signes), 2) if montants_signes else 0.0

    devis_ouverts = (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.notin_(DEVIS_STATUTS_FINAUX))
        .all()
    )
    valeur_pipeline = round(sum(d.montant_ttc or 0 for d in devis_ouverts), 2)

    # ---------- Delai moyen de paiement ----------
    factures_payees = (
        db.query(Facture)
        .options(joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut == "payee")
        .all()
    )
    delais = []
    for f in factures_payees:
        if not f.paiements:
            continue
        derniere_date = max(p.date_paiement for p in f.paiements)
        delais.append((derniere_date - f.date_emission).days)
    delai_moyen = round(sum(delais) / len(delais), 1) if delais else None

    # ---------- Clients ----------
    nb_clients_acquis = db.query(Client).filter(Client.artisan_id == artisan.id, Client.statut == "gagne").count()

    clients_avec_signatures = (
        db.query(Devis.client_id)
        .filter(Devis.artisan_id == artisan.id, Devis.statut == "signe")
        .all()
    )
    compteur_par_client = defaultdict(int)
    for (client_id,) in clients_avec_signatures:
        compteur_par_client[client_id] += 1
    nb_clients_recurrents = sum(1 for count in compteur_par_client.values() if count > 1)

    # ---------- Impayes ----------
    factures_actives = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.in_(("envoyee", "partiellement_payee", "en_retard")))
        .all()
    )
    montant_impayes = round(sum(f.montant_restant for f in factures_actives), 2)

    return AnalyticsOut(
        ca_par_mois=ca_par_mois, nb_devis_total=devis_total, nb_devis_signes=devis_signes,
        taux_acceptation=taux_acceptation, panier_moyen=panier_moyen,
        delai_moyen_paiement_jours=delai_moyen, nb_clients_acquis=nb_clients_acquis,
        nb_clients_recurrents=nb_clients_recurrents, montant_impayes=montant_impayes,
        valeur_pipeline=valeur_pipeline,
    )
