from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import UtilisateurActif, generate_unique_slug, get_current_artisan, get_utilisateur_actif
from app.media_processing import MediaValidationError
from app.models import Artisan, Membre
from app.profile_photo_service import delete_profile_photo, read_profile_photo, save_profile_photo
from app.schemas import ArtisanCreate, ArtisanLogin, ArtisanOut, ArtisanUpdate, MoiOut, PasswordChange, Token
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: ArtisanCreate, db: Session = Depends(get_db)):
    existing = db.query(Artisan).filter(Artisan.email == payload.email).first()
    existing_membre = db.query(Membre).filter(Membre.email == payload.email).first()
    if existing is not None or existing_membre is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email")

    slug = payload.slug.strip().lower() if payload.slug else None
    if slug:
        if db.query(Artisan).filter(Artisan.slug == slug).first() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce slug est déjà pris")
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
    """Connexion unifiee : essaie d'abord le proprietaire (Artisan), puis un
    membre d'equipe (Membre) - les deux se connectent avec le meme
    formulaire, l'email suffit a savoir de qui il s'agit."""
    artisan = db.query(Artisan).filter(Artisan.email == payload.email).first()
    if artisan is not None and verify_password(payload.password, artisan.password_hash):
        token = create_access_token(artisan.id, "artisan")
        return Token(access_token=token, artisan=ArtisanOut.model_validate(artisan))

    membre = db.query(Membre).filter(Membre.email == payload.email).first()
    if membre is not None and membre.actif and verify_password(payload.password, membre.password_hash):
        artisan = db.query(Artisan).filter(Artisan.id == membre.artisan_id).first()
        token = create_access_token(membre.id, "membre")
        return Token(access_token=token, artisan=ArtisanOut.model_validate(artisan))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")


@router.get("/me", response_model=ArtisanOut)
def me(current_artisan: Artisan = Depends(get_current_artisan)):
    # ArtisanOut n'a pas de champ password_hash : meme si on passait le modele
    # SQLAlchemy complet, Pydantic ignore les champs non declares dans le schema.
    return ArtisanOut.model_validate(current_artisan)


@router.get("/moi", response_model=MoiOut)
def moi(utilisateur: UtilisateurActif = Depends(get_utilisateur_actif)):
    """Identite precise de la personne connectee (par opposition a /auth/me,
    qui renvoie toujours les infos de l'entreprise) : son role determine ce
    qu'elle peut voir/faire, notamment pour la gestion d'equipe."""
    return MoiOut(
        role=utilisateur.role, nom=utilisateur.nom, email=utilisateur.email,
        membre_id=utilisateur.membre.id if utilisateur.membre else None,
    )


@router.patch("/me", response_model=ArtisanOut)
def modifier_profil(
    payload: ArtisanUpdate,
    db: Session = Depends(get_db),
    current_artisan: Artisan = Depends(get_current_artisan),
):
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_artisan, field, value)
    db.commit()
    db.refresh(current_artisan)
    return ArtisanOut.model_validate(current_artisan)


@router.post("/me/photo-profil", response_model=ArtisanOut)
async def ajouter_photo_profil(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_artisan: Artisan = Depends(get_current_artisan),
):
    max_bytes = settings.site_media_max_upload_mo * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image trop volumineuse (maximum {settings.site_media_max_upload_mo} Mo)",
        )
    filename = (file.filename or "photo").replace("\\", "/").split("/")[-1][:255]
    try:
        artisan = save_profile_photo(
            db,
            current_artisan,
            content=content,
            filename=filename,
            declared_mime=file.content_type,
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ArtisanOut.model_validate(artisan)


@router.get("/me/photo-profil")
def obtenir_photo_profil(current_artisan: Artisan = Depends(get_current_artisan)):
    content = read_profile_photo(current_artisan)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo de profil introuvable")
    return Response(
        content=content,
        media_type="image/webp",
        headers={"Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/me/photo-profil", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_photo_profil(
    db: Session = Depends(get_db),
    current_artisan: Artisan = Depends(get_current_artisan),
):
    try:
        delete_profile_photo(db, current_artisan)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def changer_mot_de_passe(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    utilisateur: UtilisateurActif = Depends(get_utilisateur_actif),
):
    """Marche pour le proprietaire comme pour un membre de l'equipe (chacun
    a ses propres identifiants). Le mot de passe actuel est toujours requis
    - jamais de changement de mot de passe sans le prouver, meme en etant
    deja connecte (un JWT vole ne doit pas suffire a prendre le compte).

    400 et non 401 pour un mot de passe actuel incorrect : le token JWT de
    la requete, lui, reste parfaitement valide (l'utilisateur EST bien
    connecte). Renvoyer 401 declencherait la deconnexion forcee globale
    cote frontend (apiFetch traite tout 401 comme "session expiree"),
    ce qui serait un comportement absurde pour une simple erreur de saisie."""
    cible = utilisateur.membre if utilisateur.membre is not None else utilisateur.artisan
    if not verify_password(payload.current_password, cible.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
    cible.password_hash = hash_password(payload.new_password)
    db.commit()
