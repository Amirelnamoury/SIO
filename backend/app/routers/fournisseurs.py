from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Fournisseur
from app.schemas import FournisseurCreate, FournisseurOut, FournisseurUpdate

router = APIRouter(prefix="/fournisseurs", tags=["fournisseurs"])


@router.get("", response_model=list[FournisseurOut])
def lister_fournisseurs(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return (
        db.query(Fournisseur)
        .options(joinedload(Fournisseur.depenses))
        .filter(Fournisseur.artisan_id == artisan.id)
        .order_by(Fournisseur.nom)
        .all()
    )


@router.post("", response_model=FournisseurOut, status_code=status.HTTP_201_CREATED)
def creer_fournisseur(
    payload: FournisseurCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    fournisseur = Fournisseur(artisan_id=artisan.id, **payload.model_dump())
    db.add(fournisseur)
    db.commit()
    db.refresh(fournisseur)
    return fournisseur


def _get_fournisseur_or_404(db: Session, artisan: Artisan, fournisseur_id: int) -> Fournisseur:
    fournisseur = (
        db.query(Fournisseur)
        .options(joinedload(Fournisseur.depenses))
        .filter(Fournisseur.id == fournisseur_id, Fournisseur.artisan_id == artisan.id)
        .first()
    )
    if fournisseur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fournisseur introuvable")
    return fournisseur


@router.patch("/{fournisseur_id}", response_model=FournisseurOut)
def modifier_fournisseur(
    fournisseur_id: int,
    payload: FournisseurUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    fournisseur = _get_fournisseur_or_404(db, artisan, fournisseur_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(fournisseur, field, value)
    db.commit()
    db.refresh(fournisseur)
    return fournisseur


@router.delete("/{fournisseur_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_fournisseur(
    fournisseur_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    fournisseur = _get_fournisseur_or_404(db, artisan, fournisseur_id)
    db.delete(fournisseur)
    db.commit()
