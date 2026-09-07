from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan, plan_allows
from app.models import AlerteReportee, Artisan, ConformiteItem, Devis, Facture, Message, Notification
from app.routers.conformite import SEUIL_ALERTE_JOURS
from app.routers.devis import JOURS_SEUIL_STATUTS, relance_due
from app.routers.factures import relance_facture_due
from app.schemas import ALERTES_REPORTABLES, NotificationOut, ReporterAlerteIn

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def lister_notifications(
    historique: bool = False,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Centre de notifications : regroupe en un seul flux tout ce qui merite
    l'attention de l'artisan (devis a relancer, factures impayees, echeances
    de conformite), sans dupliquer la logique metier de chaque module.

    Deux natures cohabitent ici, et c'est voulu : des evenements PERSISTANTS
    (table notifications, marquables comme lus) et des alertes CALCULEES a
    chaque appel. Ce que le contrat dit desormais explicitement :

      - `historique=false` (defaut) : le flux courant. Les evenements deja lus
        et les alertes reportees a plus tard en sont absents.
      - `historique=true` : tout, y compris ce qui a ete lu ou repousse. Un
        evenement marque lu disparaissait sinon pour toujours, sans aucun
        moyen d'y revenir.
    """
    notifications: list[NotificationOut] = []
    aujourdhui = date.today()

    # Les alertes calculees repoussees a plus tard. Reporter n'efface rien :
    # la facture reste en retard, elle reparait le jour dit.
    reports = {
        (a.type, a.reference_id): a.jusqu_au
        for a in db.query(AlerteReportee).filter(AlerteReportee.artisan_id == artisan.id).all()
    }

    def report_actif(type_alerte: str, reference_id: int):
        """La date jusqu'a laquelle l'alerte est repoussee, ou None."""
        jusqu_au = reports.get((type_alerte, reference_id))
        return jusqu_au if jusqu_au and jusqu_au > aujourdhui else None

    query_internes = db.query(Notification).filter(Notification.artisan_id == artisan.id)
    if not historique:
        query_internes = query_internes.filter(Notification.lu.is_(False))
    evenements_internes = query_internes.order_by(Notification.created_at.desc()).all()
    for evenement in evenements_internes:
        notifications.append(NotificationOut(
            type=evenement.type,
            id=evenement.client_id or evenement.id,
            notification_id=evenement.id,
            client_id=evenement.client_id,
            titre=evenement.titre,
            sous_titre=evenement.message,
            urgent=False,
            date=evenement.created_at,
            view=evenement.view,
            lu=evenement.lu,
        ))

    devis_candidats = (
        db.query(Devis)
        .options(joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS))
        .all()
    )
    for d in devis_candidats:
        if relance_due(d, artisan):
            reporte = report_actif("devis_relance", d.id)
            if reporte and not historique:
                continue
            notifications.append(NotificationOut(
                type="devis_relance", id=d.id, reportable=True, reportee_jusqu_au=reporte,
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
            reporte = report_actif("facture_relance", f.id)
            if reporte and not historique:
                continue
            notifications.append(NotificationOut(
                type="facture_relance", id=f.id, reportable=True, reportee_jusqu_au=reporte,
                titre=f"Impaye : {f.client.nom}",
                sous_titre=f"{f.numero} · {f.montant_restant} EUR restant",
                urgent=True,
                date=datetime.combine(f.date_echeance, datetime.min.time(), tzinfo=timezone.utc) if f.date_echeance else f.created_at,
                view="factures",
            ))

    if plan_allows(artisan.plan, "essentiel"):
        seuil = date.today() + timedelta(days=SEUIL_ALERTE_JOURS)
        conformite_items = (
            db.query(ConformiteItem)
            .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil)
            .all()
        )
        for c in conformite_items:
            reporte = report_actif("conformite", c.id)
            if reporte and not historique:
                continue
            jours_restants = (c.date_expiration - date.today()).days
            notifications.append(NotificationOut(
                type="conformite", id=c.id, reportable=True, reportee_jusqu_au=reporte,
                titre=c.libelle,
                sous_titre=f"Expire dans {jours_restants} j" if jours_restants >= 0 else f"Expire depuis {-jours_restants} j",
                urgent=jours_restants < 0,
                date=datetime.combine(c.date_expiration, datetime.min.time(), tzinfo=timezone.utc),
                view="entreprise",
            ))

    messages_non_lus = (
        db.query(Message)
        .options(joinedload(Message.client))
        .filter(Message.artisan_id == artisan.id, Message.expediteur == "client", Message.lu.is_(False))
        .all()
    )
    for m in messages_non_lus:
        notifications.append(NotificationOut(
            # client_id etait laisse vide : le front ne pouvait donc pas ouvrir
            # la conversation et deposait l'artisan sur la liste des clients.
            # Champ deja declare (Optional) dans NotificationOut - on le
            # renseigne, le contrat ne change pas.
            type="message_client", id=m.id, client_id=m.client_id,
            titre=f"Message de {m.client.nom}",
            sous_titre=m.texte[:80],
            urgent=False,
            date=m.created_at,
            view="prospects",
        ))

    notifications.sort(key=lambda n: (
        not n.urgent,
        n.date if n.date.tzinfo is not None else n.date.replace(tzinfo=timezone.utc),
    ))
    return notifications


@router.patch("/{notification_id}/lire", status_code=status.HTTP_204_NO_CONTENT)
def marquer_notification_lue(
    notification_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.artisan_id == artisan.id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification introuvable")
    notification.lu = True
    db.commit()


@router.post("/reporter", status_code=status.HTTP_204_NO_CONTENT)
def reporter_alerte(
    payload: ReporterAlerteIn,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Repousser une alerte calculee a une date.

    Elle n'a pas d'identifiant propre - elle est recalculee a chaque appel -
    donc on la designe par son type et la piece qu'elle vise. On NE VERIFIE
    PAS que l'alerte est actuellement levee : reporter une facture qui vient
    d'etre reglee ne fait de mal a personne, et la verifier obligerait a
    rejouer ici toute la logique de chaque module.

    Reporter n'efface rien. La facture reste en retard, le devis attend
    toujours sa reponse : l'alerte reparait le jour dit.
    """
    report = (
        db.query(AlerteReportee)
        .filter(
            AlerteReportee.artisan_id == artisan.id,
            AlerteReportee.type == payload.type,
            AlerteReportee.reference_id == payload.reference_id,
        )
        .first()
    )
    # Reporter deux fois la meme alerte DEPLACE l'echeance : c'est la contrainte
    # d'unicite qui le dit, et le comportement attendu.
    if report is None:
        report = AlerteReportee(
            artisan_id=artisan.id, type=payload.type,
            reference_id=payload.reference_id, jusqu_au=payload.jusqu_au,
        )
        db.add(report)
    else:
        report.jusqu_au = payload.jusqu_au
    db.commit()


@router.delete("/reporter/{type_alerte}/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
def annuler_report(
    type_alerte: str,
    reference_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Ramener une alerte reportee dans le flux courant, avant sa date."""
    if type_alerte not in ALERTES_REPORTABLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type d'alerte inconnu")
    report = (
        db.query(AlerteReportee)
        .filter(
            AlerteReportee.artisan_id == artisan.id,
            AlerteReportee.type == type_alerte,
            AlerteReportee.reference_id == reference_id,
        )
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cette alerte n'est pas reportee")
    db.delete(report)
    db.commit()
