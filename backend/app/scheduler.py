"""Moteur d'automatisation : EVENT -> WAIT -> CONDITION -> ACTION -> LOG.

Tourne en tache de fond (APScheduler, demarre au boot de l'API dans
main.py), independamment de toute connexion utilisateur. Chaque passage
(run_automation_cycle) est journalise dans AutomationRun pour l'observabilite.

Idempotence : on ne fait JAMAIS confiance a "je n'ai pas encore envoye" sans
verifier l'etat reel.
- Devis/Facture : l'action (email reussi) fait avancer un etat persiste
  (statut, date_derniere_relance, nb_relances) qui rend la condition de
  declenchement fausse au prochain passage. Rejouer le cycle est donc sans
  danger : un devis/facture deja relance ne peut pas etre re-relance avant
  le prochain seuil.
- Cas "email non configure"/"echec" : comme aucune action reelle n'a eu
  lieu, on NE FAIT PAS avancer l'etat (sinon on mentirait sur un envoi qui
  n'a jamais eu lieu). Pour eviter de re-tenter (et re-logger) a chaque
  passage tant que ce n'est pas configure, on verifie qu'aucune tentative
  recente identique n'existe deja (voir _tentative_recente).
"""
import logging
import secrets
from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import SessionLocal
from app import email_service
from app.models import Artisan, AutomationRun, ConformiteItem, Contrat, Devis, EmailLog, Facture
from app.routers.conformite import SEUIL_ALERTE_JOURS
from app.routers.contrats import generer_facture_pour_contrat
from app.routers.devis import JOURS_SEUIL_STATUTS, STATUT_SUIVANT, relance_due
from app.routers.factures import relance_facture_due

logger = logging.getLogger("suite_artisan.scheduler")

# En dessous de ce delai, on ne retente pas une notification qui a deja
# echoue/ete non-configuree pour la meme cible : evite de spammer EmailLog
# a chaque passage du scheduler tant que rien n'a change.
DELAI_RETENTATIVE_HEURES = 20

_scheduler: BackgroundScheduler | None = None


def _tentative_recente(db: Session, *, type_: str, devis_id: int | None = None, facture_id: int | None = None, conformite_libelle: str | None = None) -> bool:
    seuil = datetime.now(timezone.utc) - timedelta(hours=DELAI_RETENTATIVE_HEURES)
    query = db.query(EmailLog).filter(
        EmailLog.type == type_,
        EmailLog.statut.in_(("non_configure", "echec", "sans_destinataire")),
        EmailLog.created_at >= seuil,
    )
    if devis_id is not None:
        query = query.filter(EmailLog.devis_id == devis_id)
    if facture_id is not None:
        query = query.filter(EmailLog.facture_id == facture_id)
    if conformite_libelle is not None:
        query = query.filter(EmailLog.objet.like(f"%{conformite_libelle}%"))
    return db.query(query.exists()).scalar()


def _palier_devis(statut: str) -> int:
    return {"envoye": 1, "consulte": 1, "relance_j3": 2, "relance_j7": 3}.get(statut, 1)


def _traiter_devis(db: Session, artisan: Artisan, run: AutomationRun) -> None:
    # Les relances automatiques sont une fonction payante, comme leur
    # equivalent manuel (POST /devis/{id}/relancer) : meme frontiere.
    if artisan.subscription_status != "active":
        return
    candidats = (
        db.query(Devis)
        .options(joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS))
        .all()
    )
    for devis in candidats:
        if not relance_due(devis, artisan):
            continue
        if _tentative_recente(db, type_="relance_devis", devis_id=devis.id):
            continue

        if not devis.token:
            devis.token = secrets.token_urlsafe(24)
            db.commit()
        url = f"{settings.app_base_url}/devis-public.html?t={devis.token}"
        log = email_service.send_relance_devis(db, devis, artisan, url, _palier_devis(devis.statut))

        if log.statut == "envoye":
            devis.statut = STATUT_SUIVANT[devis.statut]
            devis.date_derniere_relance = datetime.now(timezone.utc)
            devis.nb_relances += 1
            db.commit()
            run.nb_devis_relances += 1
            run.nb_emails_envoyes += 1
        elif log.statut == "non_configure":
            run.nb_emails_non_configures += 1
        elif log.statut == "echec":
            run.nb_erreurs += 1


def _traiter_factures(db: Session, artisan: Artisan, run: AutomationRun) -> None:
    # Contrairement aux devis, la relance facture manuelle est gratuite
    # aujourd'hui (POST /factures/{id}/relancer n'exige pas d'abonnement) :
    # on garde la meme frontiere pour l'automatisation, par coherence.
    factures = (
        db.query(Facture)
        .options(joinedload(Facture.client), joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.notin_(("brouillon", "annulee", "payee")))
        .all()
    )
    for facture in factures:
        if not relance_facture_due(facture, artisan):
            continue
        if _tentative_recente(db, type_="relance_facture", facture_id=facture.id):
            continue

        if not facture.token:
            facture.token = secrets.token_urlsafe(24)
            db.commit()
        url = f"{settings.app_base_url}/facture-public.html?t={facture.token}"
        log = email_service.send_relance_facture(db, facture, artisan, url)

        if log.statut == "envoye":
            facture.date_derniere_relance = datetime.now(timezone.utc)
            facture.nb_relances += 1
            db.commit()
            run.nb_factures_relancees += 1
            run.nb_emails_envoyes += 1
        elif log.statut == "non_configure":
            run.nb_emails_non_configures += 1
        elif log.statut == "echec":
            run.nb_erreurs += 1


def _traiter_conformite(db: Session, artisan: Artisan, run: AutomationRun) -> None:
    seuil = date.today() + timedelta(days=SEUIL_ALERTE_JOURS)
    items = db.query(ConformiteItem).filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil).all()
    for item in items:
        # Pas de champ d'etat sur ConformiteItem : le throttle repose entierement
        # sur l'historique EmailLog (une notification "envoye" par item toutes les
        # DELAI_RETENTATIVE_HEURES suffit, meme logique que les relances).
        if _tentative_recente(db, type_="conformite_alerte", conformite_libelle=item.libelle):
            continue
        recent_envoi = (
            db.query(EmailLog)
            .filter(
                EmailLog.type == "conformite_alerte", EmailLog.statut == "envoye",
                EmailLog.objet.like(f"%{item.libelle}%"),
                EmailLog.created_at >= datetime.now(timezone.utc) - timedelta(days=7),
            )
            .first()
        )
        if recent_envoi:
            continue
        log = email_service.send_conformite_alerte(db, artisan, item)
        if log.statut == "envoye":
            run.nb_alertes_conformite += 1
            run.nb_emails_envoyes += 1
        elif log.statut == "non_configure":
            run.nb_emails_non_configures += 1
        elif log.statut == "echec":
            run.nb_erreurs += 1


def _traiter_contrats(db: Session, artisan: Artisan, run: AutomationRun) -> None:
    """Facturation recurrente : un contrat actif dont l'echeance est arrivee
    genere et envoie sa facture automatiquement. Idempotent par construction
    (pas besoin de _tentative_recente) : generer_facture_pour_contrat avance
    prochaine_echeance dans la meme transaction, ce qui rend la condition
    fausse au prochain passage - un contrat en retard de plusieurs periodes
    rattrape une periode par passage, jusqu'a etre a jour."""
    if artisan.subscription_status != "active":
        return
    contrats = (
        db.query(Contrat)
        .filter(Contrat.artisan_id == artisan.id, Contrat.statut == "actif", Contrat.prochaine_echeance <= date.today())
        .all()
    )
    for contrat in contrats:
        _, log = generer_facture_pour_contrat(db, artisan, contrat)
        run.nb_contrats_factures += 1
        if log.statut == "envoye":
            run.nb_emails_envoyes += 1
        elif log.statut == "non_configure":
            run.nb_emails_non_configures += 1
        elif log.statut == "echec":
            run.nb_erreurs += 1


def run_automation_cycle() -> AutomationRun:
    """Un passage complet du moteur d'automatisation, pour tous les artisans.
    Fonction pure (pas de dependance FastAPI) : appelable directement par les
    tests sans attendre l'intervalle reel du scheduler."""
    db: Session = SessionLocal()
    run = AutomationRun(started_at=datetime.now(timezone.utc))
    db.add(run)
    db.commit()
    try:
        artisans = db.query(Artisan).all()
        for artisan in artisans:
            _traiter_devis(db, artisan, run)
            _traiter_factures(db, artisan, run)
            _traiter_conformite(db, artisan, run)
            _traiter_contrats(db, artisan, run)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            "Cycle d'automatisation termine : %s devis relances, %s factures relancees, "
            "%s alertes conformite, %s factures de contrats generees, %s emails envoyes, %s non configures, %s erreurs",
            run.nb_devis_relances, run.nb_factures_relancees, run.nb_alertes_conformite,
            run.nb_contrats_factures, run.nb_emails_envoyes, run.nb_emails_non_configures, run.nb_erreurs,
        )
    except Exception as exc:  # le scheduler ne doit jamais mourir silencieusement
        logger.exception("Cycle d'automatisation interrompu par une erreur")
        run.finished_at = datetime.now(timezone.utc)
        run.erreur = str(exc)[:2000]
        db.commit()
    finally:
        db.close()
    return run


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        run_automation_cycle, "interval", minutes=settings.automation_interval_minutes,
        id="automation_cycle", max_instances=1, coalesce=True, next_run_time=datetime.now(timezone.utc) + timedelta(seconds=10),
    )
    _scheduler.start()
    logger.info("Scheduler d'automatisation demarre (intervalle : %s min)", settings.automation_interval_minutes)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
