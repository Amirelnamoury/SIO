from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artisan, Client
from app.schemas import ClientPublicCreate

router = APIRouter(prefix="/pub", tags=["public"])


@router.post("/{slug}/demande-devis", status_code=status.HTTP_201_CREATED)
def demande_devis(
    slug: str,
    payload: ClientPublicCreate,
    db: Session = Depends(get_db),
):
    """Endpoint PUBLIC (pas d'authentification) appele par le formulaire du
    site vitrine de l'artisan. Un visiteur qui demande un devis devient un
    PROSPECT dans le pipeline commercial de l'artisan (pas un devis direct :
    c'est l'artisan qui qualifie puis chiffre). Identifie l'artisan par son slug."""
    artisan = db.query(Artisan).filter(Artisan.slug == slug).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")

    client = Client(
        artisan_id=artisan.id,
        nom=payload.nom,
        email=payload.email,
        telephone=payload.telephone,
        notes=payload.message,
        statut="nouveau",
        source="site_vitrine",
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"message": "Demande envoyee avec succes", "client_id": client.id}
