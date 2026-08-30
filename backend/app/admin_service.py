import html
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.design_schemas import DesignProfileOut
from app.models import AdminUser, Artisan, Avis, SiteVitrine, utcnow
from app.security import hash_password
from app.storage import get_storage

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.site_generator import generate_site  # noqa: E402
from generator.themes import HERO_MOTIFS, PALETTE_VARIANTS, get_theme  # noqa: E402
from generator.design_selector import select_design_profile  # noqa: E402

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


def _design_profile_artisan_payload(artisan: Artisan) -> dict:
    """Contexte transmis au selecteur de design (voir
    generator/design_selector.py::select_design_profile). Volontairement
    reduit aux champs qui influencent reellement la graine stable."""
    return {"slug": artisan.slug, "siret": artisan.siret, "nom_entreprise": artisan.nom_entreprise, "metier": artisan.metier}


def _valid_stored_profile(site: SiteVitrine) -> dict | None:
    """Un design_profile deja persiste est reutilise TEL QUEL (jamais
    recalcule au hasard) - mais seulement s'il est encore valide contre le
    registre actuel (voir app/design_schemas.py::DesignProfileOut). Un
    profil corrompu ou issu d'un registre incompatible est traite comme
    absent plutot que de faire planter la generation."""
    if not site.design_profile:
        return None
    try:
        return DesignProfileOut(**site.design_profile).model_dump()
    except Exception:
        logger.warning("design_profile invalide pour le site %s : regeneration", site.id)
        return None


def ensure_design_profile(db: Session, artisan: Artisan, site: SiteVitrine) -> dict:
    """Garantit que ce site a un design_profile, sans jamais en recalculer un
    nouveau s'il en a deja un valide (voir le brief : "Une nouvelle
    generation de preview ne doit pas changer cela. Le profil n'est genere
    automatiquement que lorsqu'il n'existe pas encore. Il doit ensuite rester
    stable.").

    Quand un profil doit etre choisi, compare aux profils deja persistes des
    AUTRES sites (anti-clonage, voir select_design_profile) - jamais a celui
    du site en cours (il n'en a justement pas encore)."""
    existing = _valid_stored_profile(site)
    if existing is not None:
        return existing

    autres_profils = [
        profil for (profil,) in db.query(SiteVitrine.design_profile).filter(
            SiteVitrine.id != (site.id or -1), SiteVitrine.design_profile.isnot(None),
        ).order_by(SiteVitrine.id.desc()).limit(50).all()
        if profil
    ]
    profile = select_design_profile(_design_profile_artisan_payload(artisan), autres_profils)
    profile = DesignProfileOut(**profile).model_dump()

    site.design_profile = profile
    db.commit()
    db.refresh(site)
    return profile


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
    # Assure un design_profile stable AVANT de generer (voir
    # ensure_design_profile) : cree une fois si absent, jamais recalcule au
    # hasard ensuite. Le rendu V1 (generate_site ci-dessous) reste inchange
    # dans ce lot - voir la note de compatibilite du Lot 1.
    ensure_design_profile(db, artisan, site)
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
