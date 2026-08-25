from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artisan, Devis
from app.schemas import DevisPublicCreate

router = APIRouter(prefix="/pub", tags=["public"])


@router.post("/{slug}/demande-devis", status_code=status.HTTP_201_CREATED)
def demande_devis(
    slug: str,
    payload: DevisPublicCreate,
    db: Session = Depends(get_db),
):
    """Endpoint PUBLIC (pas d'authentification) appele par le formulaire du
    site vitrine de l'artisan. Cree une demande de devis directement dans le
    tableau de bord de l'artisan identifie par son slug."""
    artisan = db.query(Artisan).filter(Artisan.slug == slug).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")

    devis = Devis(
        artisan_id=artisan.id,
        statut="nouveau",
        source="site_vitrine",
        **payload.model_dump(),
    )
    db.add(devis)
    db.commit()
    db.refresh(devis)
    return {"message": "Demande envoyee avec succes", "devis_id": devis.id}
