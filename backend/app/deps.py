import re
import unicodedata

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artisan
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_artisan(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Artisan:
    """Extrait l'artisan (tenant) courant depuis le token JWT.
    Toutes les routes protegees filtrent leurs requetes par artisan_id == artisan.id,
    ce qui garantit l'isolation stricte entre tenants."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifie")

    artisan_id = decode_access_token(credentials.credentials)
    if artisan_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expire")

    artisan = db.query(Artisan).filter(Artisan.id == artisan_id).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan introuvable")

    return artisan


def require_active_subscription(
    artisan: Artisan = Depends(get_current_artisan),
) -> Artisan:
    """A utiliser sur les routes reservees aux 3 fonctions payantes de Suite
    Artisan (relances automatiques, chantiers, conformite). La gestion des
    devis reste gratuite : c'est la porte d'entree qui donne envie de
    s'abonner, elle ne doit jamais etre verrouillee."""

    if artisan.subscription_status != "active":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Cette fonctionnalite fait partie de l'abonnement Suite Artisan. Abonnez-vous pour la debloquer.",
        )
    return artisan


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "artisan"


def generate_unique_slug(db: Session, base_text: str) -> str:
    base_slug = slugify(base_text)
    slug = base_slug
    counter = 2
    while db.query(Artisan).filter(Artisan.slug == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
