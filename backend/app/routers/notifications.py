from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, ConformiteItem, Devis, Facture
from app.routers.conformite import SEUIL_ALERTE_JOURS
from app.routers.devis import JOURS_SEUIL_STATUTS, relance_due
from app.routers.factures import relance_facture_due
from app.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def lister_notifications(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Centre de notifications : regroupe en un seul flux tout ce qui merite
    l'attention de l'artisan (devis a relancer, factures impayees, echeances
    de conformite), sans dupliquer la logique metier de chaque module."""
    notifications: list[NotificationOut] = []

    devis_candidats = (
        db.query(Devis)
        .options(joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS))
        .all()
    )
    for d in devis_candidats:
        if relance_due(d, artisan):
            notifications.append(NotificationOut(
                type="devis_relance", id=d.id,
                titre=f"Relancer {d.client.nom}",
                sous_titre=d.titre or d.numero,
                urgent=d.statut == "relance_j7",
                date=d.date_envoi,
                view="devis",
            ))

    factures_ouvertes = (
        db.query(Facture)
        .options(joinedload(Facture.paiements), joinedload(Facture.lignes), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.notin_(("brouillon", "annulee", "payee")))
        .all()
    )
    for f in factures_ouvertes:
        if relance_facture_due(f, artisan):
            notifications.append(NotificationOut(
                type="facture_relance", id=f.id,
                titre=f"Impaye : {f.client.nom}",
                sous_titre=f"{f.numero} · {f.montant_restant} EUR restant",
                urgent=True,
                date=datetime.combine(f.date_echeance, datetime.min.time(), tzinfo=timezone.utc) if f.date_echeance else f.created_at,
                view="factures",
            ))

    if artisan.subscription_status == "active":
        seuil = date.today() + timedelta(days=SEUIL_ALERTE_JOURS)
        conformite_items = (
            db.query(ConformiteItem)
            .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil)
            .all()
        )
        for c in conformite_items:
            jours_restants = (c.date_expiration - date.today()).days
            notifications.append(NotificationOut(
                type="conformite", id=c.id,
                titre=c.libelle,
                sous_titre=f"Expire dans {jours_restants} j" if jours_restants >= 0 else f"Expire depuis {-jours_restants} j",
                urgent=jours_restants < 0,
                date=datetime.combine(c.date_expiration, datetime.min.time(), tzinfo=timezone.utc),
                view="entreprise",
            ))

    notifications.sort(key=lambda n: (not n.urgent, n.date))
    return notifications
