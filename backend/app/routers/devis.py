from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Devis
from app.schemas import DevisCreate, DevisOut, DevisUpdate

router = APIRouter(prefix="/devis", tags=["devis"])

# Cycle de relance : depuis quel statut, et combien de jours apres l'envoi
# la relance suivante devient due. Une fois "relance_j15" atteint, il n'y a
# plus de relance automatique : l'artisan doit marquer signe/perdu a la main.
STATUT_SUIVANT = {"envoye": "relance_j3", "relance_j3": "relance_j7", "relance_j7": "relance_j15"}
JOURS_SEUIL = {"envoye": 3, "relance_j3": 7, "relance_j7": 15}


def relance_due(devis: Devis) -> bool:
    if devis.statut not in JOURS_SEUIL or devis.date_envoi is None:
        return False
    echeance = devis.date_envoi + timedelta(days=JOURS_SEUIL[devis.statut])
    now = datetime.now(timezone.utc)
    if echeance.tzinfo is None:
        echeance = echeance.replace(tzinfo=timezone.utc)
    return now >= echeance


def _get_devis_or_404(db: Session, artisan: Artisan, devis_id: int) -> Devis:
    devis = (
        db.query(Devis)
        .filter(Devis.id == devis_id, Devis.artisan_id == artisan.id)
        .first()
    )
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    return devis


@router.get("", response_model=list[DevisOut])
def lister_devis(
    statut: Optional[str] = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = db.query(Devis).filter(Devis.artisan_id == artisan.id)
    if statut:
        query = query.filter(Devis.statut == statut)
    return query.order_by(Devis.created_at.desc()).all()


@router.get("/a-relancer", response_model=list[DevisOut])
def devis_a_relancer(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Devis dont la prochaine relance (J+3 / J+7 / J+15) est due aujourd'hui."""
    candidats = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL.keys()))
        .all()
    )
    return [d for d in candidats if relance_due(d)]


@router.post("", response_model=DevisOut, status_code=status.HTTP_201_CREATED)
def creer_devis(
    payload: DevisCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = Devis(artisan_id=artisan.id, statut="nouveau", source="manuel", **payload.model_dump())
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return devis


@router.get("/{devis_id}", response_model=DevisOut)
def obtenir_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return _get_devis_or_404(db, artisan, devis_id)


@router.patch("/{devis_id}", response_model=DevisOut)
def modifier_devis(
    devis_id: int,
    payload: DevisUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(devis, field, value)
    db.commit()
    db.refresh(devis)
    return devis


@router.post("/{devis_id}/envoyer", response_model=DevisOut)
def envoyer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Marque le devis comme envoye au client : demarre le cycle de relance."""
    devis = _get_devis_or_404(db, artisan, devis_id)
    if devis.montant_ht is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Renseignez un montant avant l'envoi")
    devis.statut = "envoye"
    devis.date_envoi = datetime.now(timezone.utc)
    db.commit()
    db.refresh(devis)
    return devis


@router.post("/{devis_id}/relancer", response_model=DevisOut)
def relancer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Passe le devis a l'etape de relance suivante (envoye -> J+3 -> J+7 -> J+15)."""
    devis = _get_devis_or_404(db, artisan, devis_id)
    if devis.statut not in STATUT_SUIVANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pas de relance possible depuis le statut '{devis.statut}'",
        )
    devis.statut = STATUT_SUIVANT[devis.statut]
    devis.date_derniere_relance = datetime.now(timezone.utc)
    devis.nb_relances += 1
    db.commit()
    db.refresh(devis)
    return devis


@router.delete("/{devis_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    db.delete(devis)
    db.commit()
