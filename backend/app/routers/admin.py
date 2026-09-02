from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
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
    AdminSiteListOut,
    AdminTokenOut,
    SiteVitrineOut,
    SiteVitrineUpdate,
)
from app.admin_service import default_site_config, merged_site_config, site_content_warnings
from app.config import settings
from app.database import get_db
from app.deps import ADMIN_COOKIE_NAME, require_admin
from app.models import AdminUser, Artisan, Client, Devis, Facture, Membre, SiteMedia, SiteVitrine, utcnow
from app.rate_limit import rate_limiter
from app.security import create_access_token, verify_password
from app.site_media_selection_service import media_overview_dict, media_profile_dict

router = APIRouter(tags=["admin"])
FRONTEND_ADMIN_DIR = Path(__file__).resolve().parents[3] / "frontend" / "admin"


def _artisan_or_404(db: Session, artisan_id: int) -> Artisan:
    artisan = db.query(Artisan).filter(Artisan.id == artisan_id).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")
    return artisan


def _site_out(db: Session, artisan: Artisan, site: SiteVitrine | None) -> SiteVitrineOut:
    if site is None:
        return SiteVitrineOut(
            artisan_id=artisan.id,
            statut="non_cree",
            config=default_site_config(artisan),
            media_profile=media_profile_dict(db, artisan, None, admin=True),
        )
    return SiteVitrineOut(
        id=site.id,
        artisan_id=artisan.id,
        statut=site.statut,
        domaine=site.domaine,
        url_publique=site.url_publique,
        config=merged_site_config(artisan, site),
        media_profile=media_profile_dict(db, artisan, site, admin=True),
        date_generation=site.date_generation,
        date_publication=site.date_publication,
        created_at=site.created_at,
        updated_at=site.updated_at,
        content_warnings=site_content_warnings(artisan, site),
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
        site = SiteVitrine(artisan_id=artisan.id, statut="brouillon", config=default_site_config(artisan), design_preferences={})
        db.add(site)
        db.flush()

    updates = payload.model_dump(exclude_unset=True)
    if "url_publique" in updates:
        updates["url_publique"] = str(updates["url_publique"]) if updates["url_publique"] is not None else None
    config_fields = {"tagline", "services", "stats"}
    config_updates = {key: value for key, value in updates.items() if key in config_fields}
    if "stats" in config_updates and config_updates["stats"] is not None:
        config_updates["stats"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in config_updates["stats"]]
    current_config = merged_site_config(artisan, site)
    new_config = {**current_config, **config_updates}
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
