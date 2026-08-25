from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_active_subscription
from app.models import Artisan, Chantier, ChantierNote, Client, Depense
from app.schemas import (
    ChantierCreate,
    ChantierNoteCreate,
    ChantierNoteOut,
    ChantierOut,
    ChantierUpdate,
    DepenseCreate,
    DepenseOut,
)

router = APIRouter(prefix="/chantiers", tags=["chantiers"])


def _get_chantier_or_404(db: Session, artisan: Artisan, chantier_id: int) -> Chantier:
    chantier = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes), joinedload(Chantier.depenses), joinedload(Chantier.client))
        .filter(Chantier.id == chantier_id, Chantier.artisan_id == artisan.id)
        .first()
    )
    if chantier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chantier introuvable")
    return chantier


def _to_out(chantier: Chantier) -> ChantierOut:
    return ChantierOut(
        id=chantier.id, artisan_id=chantier.artisan_id, client_id=chantier.client_id,
        client_nom=chantier.client.nom, devis_id=chantier.devis_id, titre=chantier.titre,
        adresse=chantier.adresse, statut=chantier.statut, date_debut=chantier.date_debut,
        date_fin_prevue=chantier.date_fin_prevue, budget=chantier.budget,
        total_depenses=chantier.total_depenses, marge_estimee=chantier.marge_estimee,
        created_at=chantier.created_at, notes=chantier.notes, depenses=chantier.depenses,
    )


@router.get("", response_model=list[ChantierOut])
def lister_chantiers(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantiers = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes), joinedload(Chantier.depenses), joinedload(Chantier.client))
        .filter(Chantier.artisan_id == artisan.id)
        .order_by(Chantier.created_at.desc())
        .all()
    )
    return [_to_out(c) for c in chantiers]


@router.post("", response_model=ChantierOut, status_code=status.HTTP_201_CREATED)
def creer_chantier(
    payload: ChantierCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    chantier = Chantier(artisan_id=artisan.id, **payload.model_dump())
    db.add(chantier)
    db.commit()
    chantier = _get_chantier_or_404(db, artisan, chantier.id)
    return _to_out(chantier)


@router.get("/{chantier_id}", response_model=ChantierOut)
def obtenir_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    return _to_out(_get_chantier_or_404(db, artisan, chantier_id))


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
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    return _to_out(chantier)


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


@router.post("/{chantier_id}/depenses", response_model=DepenseOut, status_code=status.HTTP_201_CREATED)
def ajouter_depense(
    chantier_id: int,
    payload: DepenseCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Ajoute une depense (materiaux, sous-traitance...) pour suivre la marge du chantier."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    depense = Depense(chantier_id=chantier.id, **payload.model_dump())
    db.add(depense)
    db.commit()
    db.refresh(depense)
    return depense
