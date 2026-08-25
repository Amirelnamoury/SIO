from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Prestation
from app.schemas import PrestationCreate, PrestationOut, PrestationUpdate

router = APIRouter(prefix="/prestations", tags=["prestations"])


@router.get("", response_model=list[PrestationOut])
def lister_prestations(
    q: str | None = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Catalogue de l'artisan. q filtre sur la description ou la categorie
    (recherche rapide utilisee depuis l'editeur de lignes de devis)."""
    query = db.query(Prestation).filter(Prestation.artisan_id == artisan.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Prestation.description.ilike(like)) | (Prestation.categorie.ilike(like))
        )
    return query.order_by(Prestation.categorie, Prestation.description).all()


@router.post("", response_model=PrestationOut, status_code=status.HTTP_201_CREATED)
def creer_prestation(
    payload: PrestationCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    prestation = Prestation(artisan_id=artisan.id, **payload.model_dump())
    db.add(prestation)
    db.commit()
    db.refresh(prestation)
    return prestation


def _get_prestation_or_404(db: Session, artisan: Artisan, prestation_id: int) -> Prestation:
    prestation = (
        db.query(Prestation)
        .filter(Prestation.id == prestation_id, Prestation.artisan_id == artisan.id)
        .first()
    )
    if prestation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prestation introuvable")
    return prestation


@router.patch("/{prestation_id}", response_model=PrestationOut)
def modifier_prestation(
    prestation_id: int,
    payload: PrestationUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    prestation = _get_prestation_or_404(db, artisan, prestation_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(prestation, field, value)
    db.commit()
    db.refresh(prestation)
    return prestation


@router.delete("/{prestation_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_prestation(
    prestation_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    prestation = _get_prestation_or_404(db, artisan, prestation_id)
    db.delete(prestation)
    db.commit()
