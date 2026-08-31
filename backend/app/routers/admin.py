from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.admin_schemas import (
    AdminArtisanDetail,
    AdminArtisanListItem,
    AdminArtisanListOut,
    AdminArtisanUpdate,
    AdminDashboardOut,
    AdminIdentityOut,
    AdminLogin,
    AdminPreviewSessionOut,
    AdminSiteListOut,
    AdminTokenOut,
    DesignCandidateGenerateRequest,
    DesignCandidateOut,
    DesignPreferencesUpdate,
    SiteVitrineOut,
    SiteVitrineUpdate,
)
from app.admin_service import (
    abandon_design_candidate,
    adopt_design_candidate,
    candidate_preview_storage_key,
    default_site_config,
    generate_candidate_preview,
    generate_design_candidate,
    generate_site_preview,
    merged_site_config,
    preview_storage_key,
    sections_availability,
    validate_design_preferences,
    validate_site_variants,
)
from app.config import settings
from app.database import get_db
from app.deps import ADMIN_COOKIE_NAME, bearer_scheme, require_admin
from app.media_processing import MediaValidationError
from app.models import AdminUser, Artisan, Client, Devis, Facture, Membre, SiteMedia, SiteMediaLibrary, SiteVitrine, utcnow
from app.rate_limit import rate_limiter
from app.security import create_access_token, decode_access_token, verify_password
from app.site_media_schemas import (
    SITE_MEDIA_CATEGORIES,
    AdminMediaSelectionIn,
    SiteMediaLibraryOut,
    SiteMediaOut,
    SiteMediaSelectionOut,
)
from app.site_media_selection_service import (
    media_overview_dict,
    media_profile_dict,
    remove_media_selection,
    selection_to_dict,
    set_media_selection,
)
from app.site_media_service import delete_site_media, media_to_dict, save_uploaded_media
from app.storage import get_storage

router = APIRouter(tags=["admin"])
FRONTEND_ADMIN_DIR = Path(__file__).resolve().parents[3] / "frontend" / "admin"
ADMIN_PREVIEW_COOKIE_NAME = "suite_artisan_admin_preview"
ADMIN_PREVIEW_SESSION_MINUTES = 10


def _require_admin_or_preview(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> tuple[AdminUser, int | None]:
    """Autorise un admin complet ou une session limitee a une preview.

    Le cookie de preview ne peut servir que sur les deux routes qui utilisent
    explicitement cette dependance. Toutes les autres API Admin continuent de
    passer exclusivement par require_admin.
    """
    try:
        return require_admin(request, credentials, db), None
    except HTTPException as admin_error:
        token = request.cookies.get(ADMIN_PREVIEW_COOKIE_NAME)
        resultat = decode_access_token(token) if token else None
        if resultat is None:
            raise admin_error
        admin_id, subject_type = resultat
        prefix = "admin_preview:"
        if not subject_type.startswith(prefix):
            raise admin_error
        try:
            artisan_id = int(subject_type.removeprefix(prefix))
        except ValueError:
            raise admin_error
        admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.actif.is_(True)).first()
        if admin is None:
            raise admin_error
        return admin, artisan_id


def _artisan_or_404(db: Session, artisan_id: int) -> Artisan:
    artisan = db.query(Artisan).filter(Artisan.id == artisan_id).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")
    return artisan


async def _read_media_upload(file: UploadFile) -> tuple[bytes, str]:
    max_bytes = settings.site_media_max_upload_mo * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image trop volumineuse (maximum {settings.site_media_max_upload_mo} Mo)",
        )
    filename = (file.filename or "image").replace("\\", "/").split("/")[-1][:255]
    return content, filename


def _save_admin_media(db: Session, artisan: Artisan, **kwargs) -> SiteMedia:
    try:
        return save_uploaded_media(db, artisan, **kwargs)
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def _admin_image_response(content: bytes, *, public: bool = False) -> Response:
    return Response(
        content=content,
        media_type="image/webp",
        headers={
            "Cache-Control": "public, max-age=3600" if public else "private, max-age=300",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _site_out(db: Session, artisan: Artisan, site: SiteVitrine | None) -> SiteVitrineOut:
    if site is None:
        return SiteVitrineOut(
            artisan_id=artisan.id,
            statut="non_cree",
            config=default_site_config(artisan),
            media_profile=media_profile_dict(db, artisan, None, admin=True),
            preview_disponible=False,
        )
    expected_key = preview_storage_key(artisan.id)
    preview_disponible = bool(
        site.storage_key == expected_key and get_storage().exists(expected_key)
    )
    candidate_preview_disponible = bool(
        site.candidate_design_profile and get_storage().exists(candidate_preview_storage_key(artisan.id))
    )
    return SiteVitrineOut(
        id=site.id,
        artisan_id=artisan.id,
        statut=site.statut,
        domaine=site.domaine,
        url_publique=site.url_publique,
        storage_key=site.storage_key,
        config=merged_site_config(artisan, site),
        design_profile=site.design_profile,
        design_preferences=site.design_preferences,
        candidate_design_profile=site.candidate_design_profile,
        candidate_preview_disponible=candidate_preview_disponible,
        sections_disponibles=sections_availability(db, artisan, site),
        media_profile=media_profile_dict(db, artisan, site, admin=True),
        date_generation=site.date_generation,
        date_publication=site.date_publication,
        created_at=site.created_at,
        updated_at=site.updated_at,
        preview_disponible=preview_disponible,
    )


def _list_item(artisan: Artisan, site: SiteVitrine | None, artisans_avec_media: set[int]) -> AdminArtisanListItem:
    site_existe = site is not None and site.statut != "non_cree"
    return AdminArtisanListItem(
        id=artisan.id,
        nom_entreprise=artisan.nom_entreprise,
        metier=artisan.metier,
        ville=artisan.ville,
        email=artisan.email,
        plan=artisan.plan,
        subscription_status=artisan.subscription_status,
        slug=artisan.slug,
        site_statut=site.statut if site else "non_cree",
        domaine=site.domaine if site else None,
        url_publique=site.url_publique if site else None,
        created_at=artisan.created_at,
        media_manquant=bool(site) and site_existe and artisan.id not in artisans_avec_media,
        alternative_en_attente=bool(site and site.candidate_design_profile),
    )


@router.get("/admin/login", include_in_schema=False)
def admin_login_page():
    return FileResponse(FRONTEND_ADMIN_DIR / "login.html")


@router.get("/admin/assets/admin.css", include_in_schema=False)
def admin_css():
    return FileResponse(FRONTEND_ADMIN_DIR / "admin.css", media_type="text/css")


@router.get("/admin/assets/admin.js", include_in_schema=False)
def admin_js():
    return FileResponse(FRONTEND_ADMIN_DIR / "admin.js", media_type="application/javascript")


@router.get("/admin", include_in_schema=False)
def admin_page(_admin: AdminUser = Depends(require_admin)):
    return FileResponse(FRONTEND_ADMIN_DIR / "index.html")


@router.post(
    "/admin/auth/login",
    response_model=AdminTokenOut,
    dependencies=[Depends(rate_limiter(8, 60))],
)
def admin_login(payload: AdminLogin, response: Response, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.email == payload.email.lower(), AdminUser.actif.is_(True)).first()
    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants admin incorrects")
    token = create_access_token(admin.id, "admin")
    admin.last_login_at = utcnow()
    db.commit()
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.admin_cookie_secure,
        samesite="strict",
        path="/admin",
    )
    return AdminTokenOut(access_token=token, admin=AdminIdentityOut.model_validate(admin))


@router.post("/admin/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def admin_logout(response: Response, _admin: AdminUser = Depends(require_admin)):
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/admin", secure=settings.admin_cookie_secure, samesite="strict")


@router.get("/admin/api/me", response_model=AdminIdentityOut)
def admin_me(admin: AdminUser = Depends(require_admin)):
    return AdminIdentityOut.model_validate(admin)


@router.get("/admin/api/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(db: Session = Depends(get_db), _admin: AdminUser = Depends(require_admin)):
    plans = {plan: 0 for plan in ("gratuit", "essentiel", "pro", "business")}
    for plan, total in db.query(Artisan.plan, func.count(Artisan.id)).group_by(Artisan.plan).all():
        plans[plan or "gratuit"] = total
    sites = dict(db.query(SiteVitrine.statut, func.count(SiteVitrine.id)).group_by(SiteVitrine.statut).all())
    return AdminDashboardOut(
        artisans_total=db.query(Artisan).count(),
        artisans_actifs=db.query(Artisan).filter(Artisan.subscription_status == "active").count(),
        plans=plans,
        sites_total=db.query(SiteVitrine).count(),
        sites_brouillon=sites.get("brouillon", 0),
        sites_generes=sites.get("genere", 0),
        sites_prets=sites.get("pret", 0),
        sites_publies=sites.get("publie", 0),
    )


def _query_artisans(db: Session, q: str | None, sites_only: bool, limit: int, offset: int):
    query = db.query(Artisan, SiteVitrine).outerjoin(SiteVitrine, SiteVitrine.artisan_id == Artisan.id)
    if sites_only:
        query = query.filter(SiteVitrine.id.isnot(None))
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(or_(
            Artisan.nom_entreprise.ilike(pattern),
            Artisan.email.ilike(pattern),
            Artisan.ville.ilike(pattern),
            Artisan.slug.ilike(pattern),
            SiteVitrine.domaine.ilike(pattern),
            SiteVitrine.url_publique.ilike(pattern),
        ))
    total = query.count()
    rows = query.order_by(Artisan.created_at.desc()).offset(offset).limit(limit).all()
    artisan_ids = [artisan.id for artisan, _site in rows]
    artisans_avec_media = set()
    if artisan_ids:
        artisans_avec_media = {
            artisan_id for (artisan_id,) in db.query(SiteMedia.artisan_id)
            .filter(SiteMedia.artisan_id.in_(artisan_ids), SiteMedia.actif.is_(True))
            .distinct()
        }
    return [_list_item(artisan, site, artisans_avec_media) for artisan, site in rows], total


@router.get("/admin/api/artisans", response_model=AdminArtisanListOut)
def admin_artisans(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    items, total = _query_artisans(db, q, False, limit, offset)
    return AdminArtisanListOut(items=items, total=total)


@router.get("/admin/api/sites", response_model=AdminSiteListOut)
def admin_sites(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    items, total = _query_artisans(db, q, True, limit, offset)
    return AdminSiteListOut(items=items, total=total)


@router.get("/admin/api/artisans/{artisan_id}", response_model=AdminArtisanDetail)
def admin_artisan_detail(artisan_id: int, db: Session = Depends(get_db), _admin: AdminUser = Depends(require_admin)):
    artisan = _artisan_or_404(db, artisan_id)
    return AdminArtisanDetail(
        id=artisan.id,
        nom_entreprise=artisan.nom_entreprise,
        metier=artisan.metier,
        email=artisan.email,
        telephone=artisan.telephone,
        ville=artisan.ville,
        code_postal=artisan.code_postal,
        adresse=artisan.adresse,
        siret=artisan.siret,
        assurance_decennale_nom=artisan.assurance_decennale_nom,
        plan=artisan.plan,
        subscription_status=artisan.subscription_status,
        slug=artisan.slug,
        created_at=artisan.created_at,
        clients_total=db.query(Client).filter(Client.artisan_id == artisan.id).count(),
        devis_total=db.query(Devis).filter(Devis.artisan_id == artisan.id).count(),
        factures_total=db.query(Facture).filter(Facture.artisan_id == artisan.id).count(),
        site=_site_out(db, artisan, artisan.site_vitrine),
        media=media_overview_dict(db, artisan, admin=True),
    )


@router.patch("/admin/api/artisans/{artisan_id}", response_model=AdminArtisanDetail)
def admin_artisan_update(
    artisan_id: int,
    payload: AdminArtisanUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] != artisan.email:
        email = str(updates["email"]).lower()
        collision = db.query(Artisan).filter(Artisan.email == email, Artisan.id != artisan.id).first()
        collision = collision or db.query(Membre).filter(Membre.email == email).first()
        collision = collision or db.query(AdminUser).filter(AdminUser.email == email, AdminUser.id != admin.id).first()
        if collision is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cet email")
        updates["email"] = email
    changed = {field: value for field, value in updates.items() if getattr(artisan, field) != value}
    for field, value in changed.items():
        setattr(artisan, field, value)
    if changed and artisan.site_vitrine and artisan.site_vitrine.date_generation:
        artisan.site_vitrine.statut = "brouillon"
        artisan.site_statut = "en_cours"
    db.commit()
    return admin_artisan_detail(artisan_id, db, admin)


@router.get("/admin/api/artisans/{artisan_id}/site", response_model=SiteVitrineOut)
def admin_site_detail(artisan_id: int, db: Session = Depends(get_db), _admin: AdminUser = Depends(require_admin)):
    artisan = _artisan_or_404(db, artisan_id)
    return _site_out(db, artisan, artisan.site_vitrine)


@router.patch("/admin/api/artisans/{artisan_id}/site", response_model=SiteVitrineOut)
def admin_site_update(
    artisan_id: int,
    payload: SiteVitrineUpdate,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None:
        site = SiteVitrine(artisan_id=artisan.id, statut="brouillon", config=default_site_config(artisan))
        db.add(site)
        db.flush()

    updates = payload.model_dump(exclude_unset=True)
    if "url_publique" in updates:
        updates["url_publique"] = str(updates["url_publique"]) if updates["url_publique"] is not None else None
    config_fields = {"tagline", "services", "stats", "variante_couleur", "variante_motif"}
    config_updates = {key: value for key, value in updates.items() if key in config_fields}
    if "stats" in config_updates and config_updates["stats"] is not None:
        config_updates["stats"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in config_updates["stats"]]
    current_config = merged_site_config(artisan, site)
    new_config = {**current_config, **config_updates}
    try:
        validate_site_variants(artisan, new_config)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    site.config = new_config
    if "domaine" in updates:
        site.domaine = updates["domaine"]
    if "url_publique" in updates:
        site.url_publique = updates["url_publique"]
    if new_config != current_config and site.date_generation:
        site.statut = "brouillon"
        artisan.site_statut = "en_cours"
    db.commit()
    db.refresh(site)
    return _site_out(db, artisan, site)


@router.post("/admin/api/artisans/{artisan_id}/site/generate", response_model=SiteVitrineOut)
def admin_site_generate(
    artisan_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None:
        site = SiteVitrine(artisan_id=artisan.id, statut="brouillon", config=default_site_config(artisan))
        db.add(site)
        db.flush()
    try:
        generate_site_preview(db, artisan, site)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _site_out(db, artisan, site)


def _site_with_design_or_409(db: Session, artisan_id: int) -> tuple[Artisan, SiteVitrine]:
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None or not site.design_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Générez une preview du site avant de configurer son design",
        )
    return artisan, site


@router.patch("/admin/api/artisans/{artisan_id}/site/design/preferences", response_model=SiteVitrineOut)
def admin_site_design_preferences(
    artisan_id: int,
    payload: DesignPreferencesUpdate,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Preferences Admin (Niveau 1) - orientent une future generation
    d'alternative, ne touchent jamais au design actuel (Lot 4)."""
    artisan, site = _site_with_design_or_409(db, artisan_id)
    site.design_preferences = validate_design_preferences(payload.model_dump())
    db.commit()
    db.refresh(site)
    return _site_out(db, artisan, site)


def _generate_candidate_response(
    db: Session, artisan: Artisan, site: SiteVitrine, payload: DesignCandidateGenerateRequest, *, avoid_previous: bool,
) -> DesignCandidateOut:
    preferred_family = site.design_profile["design_family"] if payload.keep_current_family else payload.preferred_family
    try:
        candidate, distinct = generate_design_candidate(
            db, artisan, site,
            preferred_family=preferred_family,
            density=payload.density,
            overrides=payload.overrides,
            avoid_previous_candidate=avoid_previous,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DesignCandidateOut(profile=candidate, distinct=distinct)


@router.post("/admin/api/artisans/{artisan_id}/site/design/candidate", response_model=DesignCandidateOut)
def admin_site_design_candidate_generate(
    artisan_id: int,
    payload: DesignCandidateGenerateRequest = DesignCandidateGenerateRequest(),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Genere une alternative de design (Lot 4). Ne touche JAMAIS au design
    actuel du site ni au site publie - voir generate_design_candidate."""
    artisan, site = _site_with_design_or_409(db, artisan_id)
    return _generate_candidate_response(db, artisan, site, payload, avoid_previous=False)


@router.post("/admin/api/artisans/{artisan_id}/site/design/candidate/regenerate", response_model=DesignCandidateOut)
def admin_site_design_candidate_regenerate(
    artisan_id: int,
    payload: DesignCandidateGenerateRequest = DesignCandidateGenerateRequest(),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Remplace l'alternative en cours par une nouvelle, differente de la
    precedente (anti-repetition, voir le brief section 20)."""
    artisan, site = _site_with_design_or_409(db, artisan_id)
    if not site.candidate_design_profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aucune alternative à régénérer, générez-en une d'abord")
    return _generate_candidate_response(db, artisan, site, payload, avoid_previous=True)


@router.delete("/admin/api/artisans/{artisan_id}/site/design/candidate", response_model=SiteVitrineOut)
def admin_site_design_candidate_abandon(
    artisan_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Abandonne l'alternative en cours - ne modifie jamais le design actuel
    ni le site publié (Lot 4, brief section 19)."""
    artisan, site = _site_with_design_or_409(db, artisan_id)
    abandon_design_candidate(db, artisan, site)
    return _site_out(db, artisan, site)


@router.post("/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", response_model=SiteVitrineOut)
def admin_site_design_candidate_adopt(
    artisan_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    """Adopte l'alternative en cours comme nouveau design actuel. Ne publie
    JAMAIS automatiquement : la regeneration qui suit remet le site a l'etat
    "généré" (voir adopt_design_candidate) - l'Admin doit explicitement
    remarquer le site prêt puis le republier si besoin (Lot 4, sections
    17-18)."""
    artisan, site = _site_with_design_or_409(db, artisan_id)
    try:
        adopt_design_candidate(db, artisan, site)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _site_out(db, artisan, site)


@router.get("/admin/api/artisans/{artisan_id}/site/preview/candidate", response_class=HTMLResponse)
def admin_site_preview_candidate(
    artisan_id: int,
    db: Session = Depends(get_db),
    preview_access: tuple[AdminUser, int | None] = Depends(_require_admin_or_preview),
):
    """Preview HTML de l'alternative - meme isolation que la preview
    courante (jamais de vrai prospect, jamais de fuite cross-tenant)."""
    if preview_access[1] is not None and preview_access[1] != artisan_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette session ne donne pas accès à cette preview")
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None or not site.candidate_design_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune alternative à prévisualiser")
    key = candidate_preview_storage_key(artisan.id)
    content = get_storage().read(key)
    if content is None:
        content = generate_candidate_preview(db, artisan, site).encode("utf-8")
    return HTMLResponse(content=content)


@router.post(
    "/admin/api/artisans/{artisan_id}/site/preview-session/candidate",
    response_model=AdminPreviewSessionOut,
)
def admin_site_preview_session_candidate(
    artisan_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None or not site.candidate_design_profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aucune alternative à prévisualiser")
    token = create_access_token(
        admin.id, f"admin_preview:{artisan.id}", expires_minutes=ADMIN_PREVIEW_SESSION_MINUTES,
    )
    return AdminPreviewSessionOut(
        url=f"/admin/api/artisans/{artisan.id}/site/preview/open?token={token}&candidate=1"
    )


@router.post(
    "/admin/api/artisans/{artisan_id}/site/media/logo",
    response_model=SiteMediaOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_site_media_logo_upload(
    artisan_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    content, filename = await _read_media_upload(file)
    media = _save_admin_media(
        db,
        artisan,
        content=content,
        filename=filename,
        declared_mime=file.content_type,
        type_media="logo",
        alt_text=alt_text,
    )
    return media_to_dict(media, admin_artisan_id=artisan.id)


@router.delete("/admin/api/artisans/{artisan_id}/site/media/logo", status_code=status.HTTP_204_NO_CONTENT)
def admin_site_media_logo_delete(
    artisan_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    logo = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan.id,
        SiteMedia.type_media == "logo",
    ).first()
    if logo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logo introuvable")
    delete_site_media(db, logo)


@router.post(
    "/admin/api/artisans/{artisan_id}/site/media/photos",
    response_model=SiteMediaOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_site_media_photo_upload(
    artisan_id: int,
    file: UploadFile = File(...),
    categorie: str = Form("autre"),
    alt_text: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    if categorie not in SITE_MEDIA_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categorie photo invalide")
    artisan = _artisan_or_404(db, artisan_id)
    content, filename = await _read_media_upload(file)
    media = _save_admin_media(
        db,
        artisan,
        content=content,
        filename=filename,
        declared_mime=file.content_type,
        type_media="photo",
        categorie=categorie,
        alt_text=alt_text,
    )
    return media_to_dict(media, admin_artisan_id=artisan.id)


@router.get("/admin/api/artisans/{artisan_id}/site/media/library", response_model=list[SiteMediaLibraryOut])
def admin_site_media_library(
    artisan_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    medias = db.query(SiteMediaLibrary).filter(
        SiteMediaLibrary.actif.is_(True),
    ).order_by(SiteMediaLibrary.metier, SiteMediaLibrary.media_id).all()
    return [
        {
            **{
                field: getattr(media, field)
                for field in (
                    "id", "media_id", "metier", "sous_categorie", "mime_type", "largeur", "hauteur",
                    "orientation", "usage_recommande", "licence", "source_nom", "credit", "actif",
                )
            },
            "thumbnail_url": f"/admin/api/artisans/{artisan.id}/site/media/library/{media.id}/content?variant=thumbnail",
        }
        for media in medias
    ]


@router.get("/admin/api/artisans/{artisan_id}/site/media/{media_id}/content")
def admin_site_media_content(
    artisan_id: int,
    media_id: int,
    variant: str = Query(default="web", pattern="^(web|thumbnail)$"),
    db: Session = Depends(get_db),
    preview_access: tuple[AdminUser, int | None] = Depends(_require_admin_or_preview),
):
    if preview_access[1] is not None and preview_access[1] != artisan_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette session ne donne pas acces a ce media")
    _artisan_or_404(db, artisan_id)
    media = db.query(SiteMedia).filter(
        SiteMedia.id == media_id,
        SiteMedia.artisan_id == artisan_id,
    ).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")
    key = media.thumbnail_key if variant == "thumbnail" else media.storage_key
    content = get_storage().read(key)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier media introuvable")
    return _admin_image_response(content)


@router.get("/admin/api/artisans/{artisan_id}/site/media/library/{library_media_id}/content")
def admin_site_library_media_content(
    artisan_id: int,
    library_media_id: int,
    variant: str = Query(default="web", pattern="^(web|thumbnail)$"),
    db: Session = Depends(get_db),
    preview_access: tuple[AdminUser, int | None] = Depends(_require_admin_or_preview),
):
    if preview_access[1] is not None and preview_access[1] != artisan_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette session ne donne pas acces a ce media")
    artisan = _artisan_or_404(db, artisan_id)
    media = db.query(SiteMediaLibrary).filter(
        SiteMediaLibrary.id == library_media_id,
        SiteMediaLibrary.actif.is_(True),
    ).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media de bibliotheque introuvable")
    if preview_access[1] is not None:
        selected = (
            db.query(SiteMediaSelection)
            .join(SiteVitrine, SiteVitrine.id == SiteMediaSelection.site_vitrine_id)
            .filter(
                SiteVitrine.artisan_id == artisan.id,
                SiteMediaSelection.library_media_id == media.id,
            )
            .first()
        )
        if selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media de bibliotheque introuvable")
    key = media.thumbnail_key if variant == "thumbnail" and media.thumbnail_key else media.storage_key
    content = get_storage().read(key)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier media introuvable")
    return _admin_image_response(content)


@router.put(
    "/admin/api/artisans/{artisan_id}/site/media/selections/{usage}",
    response_model=SiteMediaSelectionOut,
)
def admin_site_media_selection_set(
    artisan_id: int,
    usage: str,
    payload: AdminMediaSelectionIn,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Le site doit etre cree avant de choisir ses medias")
    try:
        selection = set_media_selection(
            db,
            artisan,
            site,
            usage=usage,
            position=payload.position,
            source=payload.source,
            site_media_id=payload.site_media_id,
            library_media_id=payload.library_media_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return selection_to_dict(selection, admin_artisan_id=artisan.id)


@router.delete(
    "/admin/api/artisans/{artisan_id}/site/media/selections/{selection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def admin_site_media_selection_delete(
    artisan_id: int,
    selection_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    if artisan.site_vitrine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selection media introuvable")
    try:
        remove_media_selection(db, artisan, artisan.site_vitrine, selection_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/admin/api/artisans/{artisan_id}/site/preview", response_class=HTMLResponse)
def admin_site_preview(
    artisan_id: int,
    db: Session = Depends(get_db),
    preview_access: tuple[AdminUser, int | None] = Depends(_require_admin_or_preview),
):
    if preview_access[1] is not None and preview_access[1] != artisan_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette session ne donne pas accès à cette preview")
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    expected_key = preview_storage_key(artisan.id)
    if site is None or site.storage_key != expected_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview introuvable")
    content = get_storage().read(expected_key)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview introuvable")
    return HTMLResponse(content=content.decode("utf-8"), headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})


@router.post(
    "/admin/api/artisans/{artisan_id}/site/preview-session",
    response_model=AdminPreviewSessionOut,
)
def admin_site_preview_session(
    artisan_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    artisan = _artisan_or_404(db, artisan_id)
    expected_key = preview_storage_key(artisan.id)
    if artisan.site_vitrine is None or artisan.site_vitrine.storage_key != expected_key or not get_storage().exists(expected_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview introuvable")
    token = create_access_token(
        admin.id,
        f"admin_preview:{artisan.id}",
        expires_minutes=ADMIN_PREVIEW_SESSION_MINUTES,
    )
    return AdminPreviewSessionOut(
        url=f"/admin/api/artisans/{artisan.id}/site/preview/open?token={token}"
    )


@router.get("/admin/api/artisans/{artisan_id}/site/preview/open", include_in_schema=False)
def admin_site_preview_open(artisan_id: int, token: str, candidate: int = 0, db: Session = Depends(get_db)):
    resultat = decode_access_token(token)
    if resultat is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session de preview invalide ou expirée")
    admin_id, subject_type = resultat
    if subject_type != f"admin_preview:{artisan_id}":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session de preview invalide")
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id, AdminUser.actif.is_(True)).first()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte admin introuvable ou désactivé")
    _artisan_or_404(db, artisan_id)

    target = "preview/candidate" if candidate else "preview"
    response = RedirectResponse(
        url=f"/admin/api/artisans/{artisan_id}/site/{target}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.set_cookie(
        key=ADMIN_PREVIEW_COOKIE_NAME,
        value=token,
        max_age=ADMIN_PREVIEW_SESSION_MINUTES * 60,
        httponly=True,
        secure=settings.admin_cookie_secure,
        samesite="strict",
        path="/admin",
    )
    return response


@router.post("/admin/api/artisans/{artisan_id}/site/ready", response_model=SiteVitrineOut)
def admin_site_ready(artisan_id: int, db: Session = Depends(get_db), _admin: AdminUser = Depends(require_admin)):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None or site.statut != "genere" or not site.date_generation:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Generez une preview avant de marquer le site pret")
    site.statut = "pret"
    db.commit()
    db.refresh(site)
    return _site_out(db, artisan, site)


@router.post("/admin/api/artisans/{artisan_id}/site/publish", response_model=SiteVitrineOut)
def admin_site_publish(artisan_id: int, db: Session = Depends(get_db), _admin: AdminUser = Depends(require_admin)):
    artisan = _artisan_or_404(db, artisan_id)
    site = artisan.site_vitrine
    if site is None or site.statut != "pret":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Le site doit etre pret avant d'etre marque publie")
    if not site.domaine or not site.url_publique:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Renseignez le domaine et l'URL publique avant publication")
    site.statut = "publie"
    site.date_publication = utcnow()
    artisan.site_statut = "livre"
    artisan.site_url = site.url_publique
    db.commit()
    db.refresh(site)
    return _site_out(db, artisan, site)


@router.post("/admin/preview-api/pub/{slug}/demande-devis")
def admin_preview_lead_sink(
    slug: str,
    db: Session = Depends(get_db),
    preview_access: tuple[AdminUser, int | None] = Depends(_require_admin_or_preview),
):
    """Confirme visuellement le formulaire sans jamais ecrire un prospect."""
    if preview_access[1] is not None:
        artisan = db.query(Artisan).filter(Artisan.id == preview_access[1], Artisan.slug == slug).first()
        if artisan is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette session ne donne pas accès à cette preview")
    return {"detail": f"Mode preview : aucune demande n'a ete creee pour {slug}."}
