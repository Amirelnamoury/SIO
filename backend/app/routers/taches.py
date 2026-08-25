from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Tache
from app.schemas import TacheCreate, TacheOut, TacheUpdate

router = APIRouter(prefix="/taches", tags=["taches"])


def _get_tache_or_404(db: Session, artisan: Artisan, tache_id: int) -> Tache:
    tache = db.query(Tache).filter(Tache.id == tache_id, Tache.artisan_id == artisan.id).first()
    if tache is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tache introuvable")
    return tache


@router.get("", response_model=list[TacheOut])
def lister_taches(
    statut: str | None = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = db.query(Tache).filter(Tache.artisan_id == artisan.id)
    if statut:
        query = query.filter(Tache.statut == statut)
    return query.order_by(Tache.echeance.is_(None), Tache.echeance.asc()).all()


@router.post("", response_model=TacheOut, status_code=status.HTTP_201_CREATED)
def creer_tache(
    payload: TacheCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    tache = Tache(artisan_id=artisan.id, statut="a_faire", **payload.model_dump())
    db.add(tache)
    db.commit()
    db.refresh(tache)
    return tache


@router.patch("/{tache_id}", response_model=TacheOut)
def modifier_tache(
    tache_id: int,
    payload: TacheUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    tache = _get_tache_or_404(db, artisan, tache_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(tache, field, value)
    db.commit()
    db.refresh(tache)
    return tache


@router.delete("/{tache_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_tache(
    tache_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    tache = _get_tache_or_404(db, artisan, tache_id)
    db.delete(tache)
    db.commit()
