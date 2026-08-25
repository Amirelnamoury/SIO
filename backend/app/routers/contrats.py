import calendar
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.deps import require_active_subscription
from app import email_service
from app.models import Artisan, Client, Contrat, Facture, LigneFacture
from app.routers.factures import _generer_numero as _generer_numero_facture
from app.schemas import ContratCreate, ContratOut, ContratUpdate

router = APIRouter(prefix="/contrats", tags=["contrats"])

FREQUENCE_MOIS = {"mensuel": 1, "trimestriel": 3, "annuel": 12}
FREQUENCE_LABELS = {"mensuel": "mensuelle", "trimestriel": "trimestrielle", "annuel": "annuelle"}


def _ajouter_mois(d: date, mois: int) -> date:
    """Ajoute un nombre de mois a une date en gerant le dernier jour du mois
    (ex: 31 janvier + 1 mois -> 28/29 fevrier, pas une exception)."""
    mois_total = d.month - 1 + mois
    annee = d.year + mois_total // 12
    mois_resultat = mois_total % 12 + 1
    jour = min(d.day, calendar.monthrange(annee, mois_resultat)[1])
    return date(annee, mois_resultat, jour)


def _to_out(contrat: Contrat) -> ContratOut:
    return ContratOut(
        id=contrat.id, client_id=contrat.client_id, client_nom=contrat.client.nom,
        titre=contrat.titre, montant_ht=contrat.montant_ht, taux_tva=contrat.taux_tva,
        frequence=contrat.frequence, statut=contrat.statut,
        prochaine_echeance=contrat.prochaine_echeance, derniere_generation=contrat.derniere_generation,
        nb_factures_generees=len(contrat.factures), created_at=contrat.created_at,
    )


def _get_contrat_or_404(db: Session, artisan: Artisan, contrat_id: int) -> Contrat:
    contrat = (
        db.query(Contrat)
        .options(joinedload(Contrat.client), joinedload(Contrat.factures))
        .filter(Contrat.id == contrat_id, Contrat.artisan_id == artisan.id)
        .first()
    )
    if contrat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat introuvable")
    return contrat


def generer_facture_pour_contrat(db: Session, artisan: Artisan, contrat: Contrat):
    """Genere et envoie reellement la facture d'echeance d'un contrat recurrent,
    puis avance prochaine_echeance selon la frequence. Appele soit par le
    planificateur d'automatisation (scheduler.py), soit manuellement via
    POST /contrats/{id}/generer - meme fonction, un seul chemin de verite.

    La facture est creee et prochaine_echeance avancee que l'email parte ou
    non : l'echeance de facturation est un fait reel independant de la
    disponibilite du fournisseur d'email (meme logique que la facture finale
    de cloturer_chantier). Renvoie (facture, email_log) pour que l'appelant
    puisse suivre honnetement ce qui a reellement ete envoye."""
    facture = Facture(
        artisan_id=artisan.id, client_id=contrat.client_id, contrat_id=contrat.id, statut="envoyee",
        type="standard", taux_tva=contrat.taux_tva,
        numero=_generer_numero_facture(db, artisan), token=secrets.token_urlsafe(24),
        date_echeance=date.today() + timedelta(days=30), date_envoi=datetime.now(timezone.utc),
    )
    db.add(facture)
    db.flush()
    db.add(LigneFacture(
        facture_id=facture.id, ordre=0,
        description=f"{contrat.titre} - facturation {FREQUENCE_LABELS.get(contrat.frequence, contrat.frequence)}",
        quantite=1, unite="forfait", prix_unitaire_ht=float(contrat.montant_ht),
    ))
    contrat.derniere_generation = date.today()
    contrat.prochaine_echeance = _ajouter_mois(contrat.prochaine_echeance, FREQUENCE_MOIS[contrat.frequence])
    db.commit()

    facture = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.id == facture.id)
        .first()
    )
    url = f"{settings.app_base_url}/facture-public.html?t={facture.token}"
    log = email_service.send_facture(db, facture, artisan, url)
    return facture, log


@router.get("", response_model=list[ContratOut])
def lister_contrats(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    contrats = (
        db.query(Contrat)
        .options(joinedload(Contrat.client), joinedload(Contrat.factures))
        .filter(Contrat.artisan_id == artisan.id)
        .order_by(Contrat.prochaine_echeance)
        .all()
    )
    return [_to_out(c) for c in contrats]


@router.post("", response_model=ContratOut, status_code=status.HTTP_201_CREATED)
def creer_contrat(
    payload: ContratCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    contrat = Contrat(artisan_id=artisan.id, **payload.model_dump())
    db.add(contrat)
    db.commit()
    contrat = _get_contrat_or_404(db, artisan, contrat.id)
    return _to_out(contrat)


@router.patch("/{contrat_id}", response_model=ContratOut)
def modifier_contrat(
    contrat_id: int,
    payload: ContratUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    contrat = _get_contrat_or_404(db, artisan, contrat_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(contrat, field, value)
    db.commit()
    contrat = _get_contrat_or_404(db, artisan, contrat_id)
    return _to_out(contrat)


@router.delete("/{contrat_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_contrat(
    contrat_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    contrat = _get_contrat_or_404(db, artisan, contrat_id)
    db.delete(contrat)
    db.commit()


@router.post("/{contrat_id}/generer", response_model=ContratOut)
def generer_maintenant(
    contrat_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Force la generation de la facture d'echeance des maintenant, sans
    attendre le prochain passage du planificateur (utile pour tester ou pour
    facturer en avance)."""
    contrat = _get_contrat_or_404(db, artisan, contrat_id)
    if contrat.statut != "actif":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un contrat actif peut generer une facture")
    generer_facture_pour_contrat(db, artisan, contrat)
    contrat = _get_contrat_or_404(db, artisan, contrat_id)
    return _to_out(contrat)
