from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import UtilisateurActif, get_current_artisan, require_equipe_admin
from app.models import Artisan, Membre
from app.schemas import MembreCreate, MembreOut, MembreUpdate
from app.security import hash_password

router = APIRouter(prefix="/equipe", tags=["equipe"])


@router.get("", response_model=list[MembreOut])
def lister_equipe(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Visible par tous les membres de l'equipe (proprietaire, administrateur
    ou salarie) : seule la gestion (creer/modifier/supprimer) est reservee
    aux administrateurs, voir les autres routes de ce fichier."""
    return db.query(Membre).filter(Membre.artisan_id == artisan.id).order_by(Membre.created_at).all()


@router.post("", response_model=MembreOut, status_code=status.HTTP_201_CREATED)
def creer_membre(
    payload: MembreCreate,
    db: Session = Depends(get_db),
    utilisateur: UtilisateurActif = Depends(require_equipe_admin),
):
    existing = db.query(Artisan).filter(Artisan.email == payload.email).first()
    existing_membre = db.query(Membre).filter(Membre.email == payload.email).first()
    if existing is not None or existing_membre is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email")

    membre = Membre(
        artisan_id=utilisateur.artisan.id, nom=payload.nom, email=payload.email,
        password_hash=hash_password(payload.password), role=payload.role,
    )
    db.add(membre)
    db.commit()
    db.refresh(membre)
    return membre


@router.patch("/{membre_id}", response_model=MembreOut)
def modifier_membre(
    membre_id: int,
    payload: MembreUpdate,
    db: Session = Depends(get_db),
    utilisateur: UtilisateurActif = Depends(require_equipe_admin),
):
    membre = db.query(Membre).filter(Membre.id == membre_id, Membre.artisan_id == utilisateur.artisan.id).first()
    if membre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable")
    if utilisateur.membre is not None and utilisateur.membre.id == membre.id and payload.actif is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous desactiver vous-meme")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(membre, field, value)
    db.commit()
    db.refresh(membre)
    return membre


@router.delete("/{membre_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_membre(
    membre_id: int,
    db: Session = Depends(get_db),
    utilisateur: UtilisateurActif = Depends(require_equipe_admin),
):
    membre = db.query(Membre).filter(Membre.id == membre_id, Membre.artisan_id == utilisateur.artisan.id).first()
    if membre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable")
    if utilisateur.membre is not None and utilisateur.membre.id == membre.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas vous supprimer vous-meme")
    db.delete(membre)
    db.commit()
