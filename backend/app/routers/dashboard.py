from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Client, ConformiteItem, Devis, Evenement, Facture, Paiement, Tache
from app.routers.conformite import SEUIL_ALERTE_JOURS, _to_out as conformite_to_out
from app.routers.devis import JOURS_SEUIL, relance_due, _to_out as devis_to_out
from app.routers.factures import _to_out as facture_to_out
from app.schemas import DashboardAujourdhui, DashboardCommercial, DashboardFinances, DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DEVIS_STATUTS_EN_ATTENTE = ("envoye", "consulte", "relance_j3", "relance_j7", "relance_j15")
DEVIS_STATUTS_FINAUX = ("signe", "perdu", "expire")


@router.get("", response_model=DashboardOut)
def obtenir_dashboard(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    aujourdhui = date.today()
    maintenant = datetime.now(timezone.utc)
    il_y_a_7j = maintenant - timedelta(days=7)
    il_y_a_30j = maintenant - timedelta(days=30)
    debut_mois = date(aujourdhui.year, aujourdhui.month, 1)
    debut_annee = date(aujourdhui.year, 1, 1)

    # ---------- Aujourd'hui ----------
    taches_jour = (
        db.query(Tache)
        .filter(Tache.artisan_id == artisan.id, Tache.statut == "a_faire", Tache.echeance == aujourdhui)
        .all()
    )
    evenements_jour = (
        db.query(Evenement)
        .filter(
            Evenement.artisan_id == artisan.id,
            Evenement.date_debut >= datetime.combine(aujourdhui, datetime.min.time(), tzinfo=timezone.utc),
            Evenement.date_debut < datetime.combine(aujourdhui + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
        )
        .all()
    )
    devis_candidats = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL.keys()))
        .all()
    )
    devis_a_relancer = [devis_to_out(d) for d in devis_candidats if relance_due(d)]

    factures_ouvertes = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.notin_(("brouillon", "annulee", "payee")))
        .all()
    )
    factures_en_retard = [facture_to_out(f) for f in factures_ouvertes if f.est_en_retard]

    aujourdhui_out = DashboardAujourdhui(
        taches=taches_jour, evenements=evenements_jour,
        devis_a_relancer=devis_a_relancer, factures_en_retard=factures_en_retard,
    )

    # ---------- Commercial ----------
    nouveaux_prospects_7j = (
        db.query(Client)
        .filter(Client.artisan_id == artisan.id, Client.created_at >= il_y_a_7j)
        .count()
    )
    devis_en_attente = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_EN_ATTENTE))
        .count()
    )
    devis_acceptes_30j = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut == "signe", Devis.date_signature >= il_y_a_30j)
        .count()
    )
    devis_decides = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_FINAUX)).count()
    devis_signes_total = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut == "signe").count()
    taux_transformation = round((devis_signes_total / devis_decides) * 100, 1) if devis_decides else 0.0

    devis_ouverts = (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.notin_(DEVIS_STATUTS_FINAUX))
        .all()
    )
    valeur_pipeline = round(sum(d.montant_ttc or 0 for d in devis_ouverts), 2)

    commercial_out = DashboardCommercial(
        nouveaux_prospects_7j=nouveaux_prospects_7j, devis_en_attente=devis_en_attente,
        devis_acceptes_30j=devis_acceptes_30j, taux_transformation=taux_transformation,
        valeur_pipeline=valeur_pipeline,
    )

    # ---------- Finances ----------
    def somme_paiements(depuis: date) -> float:
        montants = (
            db.query(Paiement.montant)
            .join(Facture, Paiement.facture_id == Facture.id)
            .filter(Facture.artisan_id == artisan.id, Paiement.date_paiement >= depuis)
            .all()
        )
        return round(sum(m[0] for m in montants), 2)

    ca_mois = somme_paiements(debut_mois)
    ca_annee = somme_paiements(debut_annee)

    factures_actives = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.in_(("envoyee", "partiellement_payee", "en_retard")))
        .all()
    )
    a_encaisser = round(sum(f.montant_restant for f in factures_actives), 2)
    montant_en_retard = round(sum(f.montant_restant for f in factures_actives if f.est_en_retard), 2)

    paiements_recents = (
        db.query(Paiement)
        .join(Facture, Paiement.facture_id == Facture.id)
        .filter(Facture.artisan_id == artisan.id)
        .order_by(Paiement.created_at.desc())
        .limit(5)
        .all()
    )

    finances_out = DashboardFinances(
        ca_mois=ca_mois, ca_annee=ca_annee, a_encaisser=a_encaisser,
        montant_en_retard=montant_en_retard, paiements_recents=paiements_recents,
    )

    # ---------- Alertes conformite ----------
    seuil = aujourdhui + timedelta(days=SEUIL_ALERTE_JOURS)
    conformite_items = (
        db.query(ConformiteItem)
        .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil)
        .all()
    )

    return DashboardOut(
        aujourdhui=aujourdhui_out, commercial=commercial_out, finances=finances_out,
        alertes_conformite=[conformite_to_out(i) for i in conformite_items],
    )
