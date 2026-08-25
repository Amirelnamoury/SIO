from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import generate_unique_slug, get_current_artisan
from app.models import Artisan
from app.schemas import ArtisanCreate, ArtisanLogin, ArtisanOut, Token
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: ArtisanCreate, db: Session = Depends(get_db)):
    existing = db.query(Artisan).filter(Artisan.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un compte existe deja avec cet email")

    slug = payload.slug.strip().lower() if payload.slug else None
    if slug:
        if db.query(Artisan).filter(Artisan.slug == slug).first() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce slug est deja pris")
    else:
        slug = generate_unique_slug(db, payload.nom_entreprise)

    artisan = Artisan(
        slug=slug,
        nom_entreprise=payload.nom_entreprise,
        metier=payload.metier,
        email=payload.email,
        password_hash=hash_password(payload.password),
        telephone=payload.telephone,
        ville=payload.ville,
        code_postal=payload.code_postal,
        siret=payload.siret,
        assurance_decennale_nom=payload.assurance_decennale_nom,
    )
    db.add(artisan)
    db.commit()
    db.refresh(artisan)

    token = create_access_token(artisan.id)
    return Token(access_token=token, artisan=ArtisanOut.model_validate(artisan))


@router.post("/login", response_model=Token)
def login(payload: ArtisanLogin, db: Session = Depends(get_db)):
    artisan = db.query(Artisan).filter(Artisan.email == payload.email).first()
    if artisan is None or not verify_password(payload.password, artisan.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    token = create_access_token(artisan.id)
    return Token(access_token=token, artisan=ArtisanOut.model_validate(artisan))


@router.get("/me", response_model=ArtisanOut)
def me(current_artisan: Artisan = Depends(get_current_artisan)):
    # ArtisanOut n'a pas de champ password_hash : meme si on passait le modele
    # SQLAlchemy complet, Pydantic ignore les champs non declares dans le schema.
    return ArtisanOut.model_validate(current_artisan)
