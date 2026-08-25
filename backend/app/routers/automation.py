from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan
from app import email_service
from app.models import Artisan, AutomationRun, EmailLog
from app.schemas import AutomationStatutOut, EmailLogOut

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/status", response_model=AutomationStatutOut)
def statut_automation(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Etat du moteur d'automatisation. Volontairement global (pas de donnee
    d'un autre artisan) : configuration email et derniere execution du
    scheduler sont des informations systeme, pas des donnees de tenant."""
    dernier_run = db.query(AutomationRun).order_by(AutomationRun.started_at.desc()).first()
    resume = None
    prochaine = None
    if dernier_run is not None and dernier_run.finished_at is not None:
        resume = (
            f"{dernier_run.nb_devis_relances} devis relances, {dernier_run.nb_factures_relancees} factures relancees, "
            f"{dernier_run.nb_emails_envoyes} emails envoyes, {dernier_run.nb_emails_non_configures} non configures, "
            f"{dernier_run.nb_erreurs} erreurs"
        )
        prochaine = dernier_run.started_at + timedelta(minutes=settings.automation_interval_minutes)
    return AutomationStatutOut(
        email_configure=email_service.is_configured(), fournisseur="Resend",
        intervalle_minutes=settings.automation_interval_minutes,
        derniere_execution=dernier_run.finished_at if dernier_run else None,
        derniere_execution_resume=resume,
        prochaine_execution_estimee=prochaine,
    )


@router.get("/emails", response_model=list[EmailLogOut])
def historique_emails(
    limit: int = 50,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Historique des emails transactionnels de CET artisan (envoyes, echoues
    ou jamais partis faute de configuration) - jamais de faux "envoye"."""
    limit = max(1, min(limit, 200))
    logs = (
        db.query(EmailLog)
        .filter(EmailLog.artisan_id == artisan.id)
        .order_by(EmailLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs
