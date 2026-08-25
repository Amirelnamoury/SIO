from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, ConformiteItem
from app.schemas import ConformiteCreate, ConformiteOut, ConformiteUpdate

router = APIRouter(prefix="/conformite", tags=["conformite"])

SEUIL_ALERTE_JOURS = 30


def _to_out(item: ConformiteItem) -> ConformiteOut:
    jours_restants = (item.date_expiration - date.today()).days
    return ConformiteOut(
        id=item.id,
        artisan_id=item.artisan_id,
        type=item.type,
        libelle=item.libelle,
        date_expiration=item.date_expiration,
        document_url=item.document_url,
        created_at=item.created_at,
        alerte=jours_restants < SEUIL_ALERTE_JOURS,
        jours_restants=jours_restants,
    )


def _get_item_or_404(db: Session, artisan: Artisan, item_id: int) -> ConformiteItem:
    item = (
        db.query(ConformiteItem)
        .filter(ConformiteItem.id == item_id, ConformiteItem.artisan_id == artisan.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element de conformite introuvable")
    return item


@router.get("", response_model=list[ConformiteOut])
def lister_conformite(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    items = db.query(ConformiteItem).filter(ConformiteItem.artisan_id == artisan.id).all()
    return [_to_out(i) for i in items]


@router.get("/alertes", response_model=list[ConformiteOut])
def alertes_conformite(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Echeances dans moins de 30 jours (ou deja depassees)."""
    seuil = date.today() + timedelta(days=SEUIL_ALERTE_JOURS)
    items = (
        db.query(ConformiteItem)
        .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil)
        .all()
    )
    return [_to_out(i) for i in items]


@router.post("", response_model=ConformiteOut, status_code=status.HTTP_201_CREATED)
def creer_conformite(
    payload: ConformiteCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    item = ConformiteItem(artisan_id=artisan.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(item)


@router.patch("/{item_id}", response_model=ConformiteOut)
def modifier_conformite(
    item_id: int,
    payload: ConformiteUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    item = _get_item_or_404(db, artisan, item_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _to_out(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_conformite(
    item_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    item = _get_item_or_404(db, artisan, item_id)
    db.delete(item)
    db.commit()
