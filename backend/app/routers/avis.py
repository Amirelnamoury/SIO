import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Avis, Client
from app.schemas import AvisCreate, AvisOut, DemandeAvisOut

router = APIRouter(tags=["avis"])


def _to_out(avis: Avis) -> AvisOut:
    return AvisOut(
        id=avis.id, artisan_id=avis.artisan_id, client_id=avis.client_id,
        client_nom=avis.client.nom if avis.client else avis.nom_auteur,
        note=avis.note, commentaire=avis.commentaire, nom_auteur=avis.nom_auteur,
        source=avis.source, created_at=avis.created_at,
    )


@router.get("/avis", response_model=list[AvisOut])
def lister_avis(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    avis = (
        db.query(Avis)
        .options(joinedload(Avis.client))
        .filter(Avis.artisan_id == artisan.id)
        .order_by(Avis.created_at.desc())
        .all()
    )
    return [_to_out(a) for a in avis]


@router.post("/avis", response_model=AvisOut, status_code=status.HTTP_201_CREATED)
def creer_avis(
    payload: AvisCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Saisie manuelle par l'artisan (avis recu par telephone, Google, en personne...)."""
    if payload.client_id is not None:
        client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    avis = Avis(artisan_id=artisan.id, source="manuel", **payload.model_dump())
    db.add(avis)
    db.commit()
    avis = db.query(Avis).options(joinedload(Avis.client)).filter(Avis.id == avis.id).first()
    return _to_out(avis)


@router.delete("/avis/{avis_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_avis(
    avis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    avis = db.query(Avis).filter(Avis.id == avis_id, Avis.artisan_id == artisan.id).first()
    if avis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avis introuvable")
    db.delete(avis)
    db.commit()


@router.post("/clients/{client_id}/demande-avis", response_model=DemandeAvisOut)
def demander_avis(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Genere (ou reutilise) le lien public a envoyer au client pour lui demander un avis."""
    client = db.query(Client).filter(Client.id == client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    if client.token_avis is None:
        client.token_avis = secrets.token_urlsafe(24)
        db.commit()
    return DemandeAvisOut(token_avis=client.token_avis)
