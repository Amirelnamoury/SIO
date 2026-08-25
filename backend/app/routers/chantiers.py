from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_active_subscription
from app.models import Artisan, Chantier, ChantierNote
from app.schemas import ChantierCreate, ChantierNoteCreate, ChantierNoteOut, ChantierOut, ChantierUpdate

router = APIRouter(prefix="/chantiers", tags=["chantiers"])


def _get_chantier_or_404(db: Session, artisan: Artisan, chantier_id: int) -> Chantier:
    chantier = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes))
        .filter(Chantier.id == chantier_id, Chantier.artisan_id == artisan.id)
        .first()
    )
    if chantier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chantier introuvable")
    return chantier


@router.get("", response_model=list[ChantierOut])
def lister_chantiers(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    return (
        db.query(Chantier)
        .options(joinedload(Chantier.notes))
        .filter(Chantier.artisan_id == artisan.id)
        .order_by(Chantier.created_at.desc())
        .all()
    )


@router.post("", response_model=ChantierOut, status_code=status.HTTP_201_CREATED)
def creer_chantier(
    payload: ChantierCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = Chantier(artisan_id=artisan.id, **payload.model_dump())
    db.add(chantier)
    db.commit()
    db.refresh(chantier)
    return chantier


@router.get("/{chantier_id}", response_model=ChantierOut)
def obtenir_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    return _get_chantier_or_404(db, artisan, chantier_id)


@router.patch("/{chantier_id}", response_model=ChantierOut)
def modifier_chantier(
    chantier_id: int,
    payload: ChantierUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(chantier, field, value)
    db.commit()
    db.refresh(chantier)
    return chantier


@router.delete("/{chantier_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    db.delete(chantier)
    db.commit()


@router.post("/{chantier_id}/notes", response_model=ChantierNoteOut, status_code=status.HTTP_201_CREATED)
def ajouter_note(
    chantier_id: int,
    payload: ChantierNoteCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Ajoute une note/photo de compte-rendu (avant/pendant/apres) a un chantier."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    note = ChantierNote(chantier_id=chantier.id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
