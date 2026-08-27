import html
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AdminUser, Artisan, Avis, SiteVitrine, utcnow
from app.security import hash_password
from app.storage import get_storage

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.site_generator import generate_site  # noqa: E402
from generator.themes import HERO_MOTIFS, PALETTE_VARIANTS, get_theme  # noqa: E402

logger = logging.getLogger("suite_artisan.admin")


def ensure_bootstrap_admin(db: Session) -> None:
    """Cree le premier compte admin depuis l'environnement, une seule fois."""
    if not settings.admin_email and not settings.admin_password:
        return
    if not settings.admin_email or not settings.admin_password:
        logger.error("ADMIN_EMAIL et ADMIN_PASSWORD doivent etre definis ensemble")
        return
    if len(settings.admin_password) < 12:
        raise RuntimeError("ADMIN_PASSWORD doit contenir au moins 12 caracteres")
    email = settings.admin_email.strip().lower()
    if db.query(AdminUser).filter(AdminUser.email == email).first() is not None:
        return
    db.add(AdminUser(email=email, password_hash=hash_password(settings.admin_password), nom=settings.admin_name, actif=True))
    db.commit()
    logger.info("Compte Admin Suite Artisan initialise pour %s", email)


def default_site_config(artisan: Artisan) -> dict:
    theme = get_theme(artisan.metier)
    return {
        "tagline": theme["tagline"],
        "services": list(theme["services"]),
        "stats": [],
        "variante_couleur": None,
        "variante_motif": None,
    }


def merged_site_config(artisan: Artisan, site: SiteVitrine | None) -> dict:
    config = default_site_config(artisan)
    if site and site.config:
        config.update(site.config)
    return config


def validate_site_variants(artisan: Artisan, config: dict) -> None:
    couleur = config.get("variante_couleur")
    palettes = PALETTE_VARIANTS.get(artisan.metier, PALETTE_VARIANTS["general"])
    if couleur is not None and (not isinstance(couleur, int) or couleur < 0 or couleur >= len(palettes)):
        raise ValueError("Variante couleur incompatible avec ce metier")
    motif = config.get("variante_motif")
    motifs = HERO_MOTIFS.get(artisan.metier, HERO_MOTIFS["general"])
    if motif is not None and motif not in motifs:
        raise ValueError("Variante motif incompatible avec ce metier")


def preview_storage_key(artisan_id: int) -> str:
    if artisan_id <= 0:
        raise ValueError("Identifiant artisan invalide")
    return f"admin-site-previews/{artisan_id}/index.html"


def _safe_text(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def build_generator_payload(db: Session, artisan: Artisan, config: dict) -> dict:
    validate_site_variants(artisan, config)
    avis = db.query(Avis).filter(Avis.artisan_id == artisan.id, Avis.publie_site.is_(True)).all()
    return {
        "nom_entreprise": _safe_text(artisan.nom_entreprise),
        "metier": artisan.metier,
        "slug": artisan.slug,
        "ville": _safe_text(artisan.ville),
        "code_postal": _safe_text(artisan.code_postal),
        "telephone": _safe_text(artisan.telephone),
        "email": _safe_text(artisan.email),
        "adresse": _safe_text(artisan.adresse),
        "siret": _safe_text(artisan.siret),
        "assurance_decennale_nom": _safe_text(artisan.assurance_decennale_nom),
        "tagline": _safe_text(config.get("tagline")),
        "services": [_safe_text(item) for item in config.get("services") or []],
        "stats": [
            {"valeur": _safe_text(item.get("valeur")), "label": _safe_text(item.get("label"))}
            for item in config.get("stats") or []
        ],
        "variante_couleur": config.get("variante_couleur"),
        "variante_motif": config.get("variante_motif"),
        "avis": [
            {"note": item.note, "commentaire": _safe_text(item.commentaire), "nom_auteur": _safe_text(item.nom_auteur)}
            for item in avis
        ],
    }


def generate_site_preview(db: Session, artisan: Artisan, site: SiteVitrine) -> str:
    config = merged_site_config(artisan, site)
    payload = build_generator_payload(db, artisan, config)
    generated_html = generate_site(payload, api_base_url="/admin/preview-api")
    storage_key = preview_storage_key(artisan.id)
    get_storage().save(storage_key, generated_html.encode("utf-8"))
    site.storage_key = storage_key
    site.statut = "genere"
    site.date_generation = utcnow()
    artisan.site_statut = "en_cours"
    db.commit()
    db.refresh(site)
    return generated_html
