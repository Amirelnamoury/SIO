import html
import logging
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.design_schemas import DesignProfileOut, validate_design_profile
from app.models import AdminUser, Artisan, Avis, SiteVitrine, utcnow
from app.security import hash_password
from app.site_media_selection_service import ensure_media_profile, media_overview_dict, media_profile_dict
from app.storage import get_storage

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.site_generator import generate_site  # noqa: E402
from generator.themes import HERO_MOTIFS, PALETTE_VARIANTS, THEMES, get_theme  # noqa: E402
from generator.design_registry import DESIGN_FAMILIES, SECTION_CATALOG, SPACING_STYLES  # noqa: E402
from generator.design_selector import (  # noqa: E402
    SIMILARITY_THRESHOLD,
    build_design_signature,
    select_candidate_design_profile,
    select_design_profile,
    similarity_score,
)
from generator.v3.grammar import AMBIENCES, ART_DIRECTIONS, CONTENT_DENSITIES, PROFILE_VALUES as V3_PROFILE_VALUES  # noqa: E402
from generator.v3.selector import (  # noqa: E402
    build_design_signature as build_v3_signature,
    select_design_grammar,
    similarity_score as v3_similarity_score,
)

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
        stored = dict(site.config)
        stale_default = any(
            metier != artisan.metier
            and stored.get("tagline") == theme.get("tagline")
            and stored.get("services") == theme.get("services")
            for metier, theme in THEMES.items()
        )
        if stale_default:
            stored.pop("tagline", None)
            stored.pop("services", None)
        config.update(stored)
    return config


def site_content_warnings(artisan: Artisan, site: SiteVitrine | None) -> list[str]:
    if not site or not site.config:
        return []
    stored = dict(site.config)
    stale_default = any(
        metier != artisan.metier
        and stored.get("tagline") == theme.get("tagline")
        and stored.get("services") == theme.get("services")
        for metier, theme in THEMES.items()
    )
    return ["Les anciens textes par défaut d’un autre métier ont été écartés du rendu. Vérifiez puis enregistrez le contenu actuel."] if stale_default else []


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
        return validate_design_profile(site.design_profile)
    except Exception:
        logger.warning("design_profile invalide pour le site %s : regeneration", site.id)
        return None


def _autres_profils(db: Session, site: SiteVitrine) -> list[dict]:
    """Profils design deja persistes d'AUTRES sites, les plus recents
    d'abord - utilise pour l'anti-clonage (voir select_design_profile /
    select_candidate_design_profile). Jamais le profil du site en cours."""
    return [
        profil for (profil,) in db.query(SiteVitrine.design_profile).filter(
            SiteVitrine.id != (site.id or -1), SiteVitrine.design_profile.isnot(None),
        ).order_by(SiteVitrine.id.desc()).limit(50).all()
        if profil
    ]


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

    if (site.design_preferences or {}).get("engine_version") == "v3":
        profile, _distinct = select_design_grammar(_design_profile_artisan_payload(artisan), _autres_profils(db, site))
        profile = validate_design_profile(profile)
    else:
        profile = select_design_profile(_design_profile_artisan_payload(artisan), _autres_profils(db, site))
        profile = DesignProfileOut(**profile).model_dump()

    site.design_profile = profile
    db.commit()
    db.refresh(site)
    return profile


# ---------- Configurateur Admin (Lot 4) : preferences, candidate, adopt/abandon ----------

DENSITY_VALUES = set(SPACING_STYLES) | set(CONTENT_DENSITIES)
# Sous-ensemble d'axes qu'un Admin peut fixer explicitement en "reglages
# avances" (Niveau 2, voir le brief). design_family n'y figure pas
# volontairement : le choix de famille passe par preferred_family, qui
# pilote aussi la compatibilite des axes structurels tires par le moteur -
# un override direct de design_family court-circuiterait ce mecanisme.
CANDIDATE_OVERRIDE_FIELDS = {
    "header_variant", "hero_variant", "services_variant", "gallery_variant",
    "about_variant", "reviews_variant", "cta_variant", "footer_variant",
    "palette", "font_pair", "radius_style", "spacing_style", "image_treatment",
    "section_order",
}
CANDIDATE_OVERRIDE_FIELDS.update(V3_PROFILE_VALUES)


def validate_design_preferences(payload: dict) -> dict:
    """Valide des preferences Admin (Niveau 1) contre le registre - jamais de
    confiance aveugle envers le frontend (voir le brief, section 33)."""
    preferred_family = payload.get("preferred_family")
    if preferred_family is not None and preferred_family not in DESIGN_FAMILIES:
        raise ValueError(f"preferred_family doit etre l'une de : {sorted(DESIGN_FAMILIES)}")
    density = payload.get("density")
    if density is not None and density not in DENSITY_VALUES:
        raise ValueError(f"density doit etre l'une de : {sorted(DENSITY_VALUES)}")
    engine_version = payload.get("engine_version")
    if engine_version is not None and engine_version not in {"v2", "v3"}:
        raise ValueError("engine_version doit etre v2 ou v3")
    preferred_direction = payload.get("preferred_direction")
    if preferred_direction is not None and preferred_direction not in ART_DIRECTIONS:
        raise ValueError(f"preferred_direction doit etre l'une de : {sorted(ART_DIRECTIONS)}")
    ambience = payload.get("ambience")
    if ambience is not None and ambience not in AMBIENCES:
        raise ValueError(f"ambience doit etre l'une de : {sorted(AMBIENCES)}")
    result = {"preferred_family": preferred_family, "density": density}
    if engine_version is not None:
        result["engine_version"] = engine_version
    if preferred_direction is not None:
        result["preferred_direction"] = preferred_direction
    if ambience is not None:
        result["ambience"] = ambience
    return result


def _apply_candidate_overrides(candidate: dict, overrides: dict | None) -> dict:
    """Applique des reglages avances (Niveau 2) sur une candidate deja
    generee par le moteur, puis revalide integralement le resultat contre
    DesignProfileOut (jamais confiance en une valeur venue du frontend) et
    recalcule design_signature en consequence - une candidate avec overrides
    reste donc toujours un design_profile valide et coherent."""
    if not overrides:
        return candidate
    inconnues = set(overrides) - CANDIDATE_OVERRIDE_FIELDS
    if inconnues:
        raise ValueError(f"Reglages avances inconnus : {sorted(inconnues)}")
    merged = {**candidate, **overrides}
    merged["design_signature"] = "temp"
    merged = validate_design_profile(merged)
    merged["design_signature"] = build_v3_signature(merged) if str(merged["design_engine_version"]).startswith("v3") else build_design_signature(merged)
    return merged


def candidate_preview_storage_key(artisan_id: int) -> str:
    if artisan_id <= 0:
        raise ValueError("Identifiant artisan invalide")
    return f"admin-site-previews/{artisan_id}/candidate.html"


def generate_design_candidate(
    db: Session,
    artisan: Artisan,
    site: SiteVitrine,
    *,
    preferred_family: str | None = None,
    density: str | None = None,
    overrides: dict | None = None,
    avoid_previous_candidate: bool = False,
    engine_version: str | None = None,
    preferred_direction: str | None = None,
    ambience: str | None = None,
) -> tuple[dict, bool]:
    """Genere (ou remplace) l'alternative de design d'un site - NE TOUCHE
    JAMAIS a site.design_profile (le "current" reste stable tant que
    l'Admin n'a pas explicitement adopte, voir adopt_design_candidate).

    Retourne (candidate, distinct) : distinct=False si aucune tentative
    n'etait suffisamment differente du current (reponse honnete, voir le
    brief - jamais un echec silencieux ni une fausse distinction)."""
    current = _valid_stored_profile(site)
    if current is None:
        raise ValueError("Le site doit avoir un design actuel avant de generer une alternative")

    exclude = set()
    exclude.add(current.get("design_signature") or "")
    if avoid_previous_candidate:
        previous = _valid_stored_profile_field(site, "candidate_design_profile")
        if previous is not None:
            exclude.add(previous.get("design_signature") or "")

    current_is_v3 = str(current.get("design_engine_version") or "").startswith("v3")
    legacy_overrides = bool(overrides and set(overrides) - set(V3_PROFILE_VALUES))
    use_v3 = engine_version == "v3" or preferred_direction is not None or (engine_version is None and preferred_family is None and current_is_v3 and not legacy_overrides)
    if use_v3:
        v3_density = density if density in CONTENT_DENSITIES else ({"comfortable": "balanced", "spacious": "airy"}.get(density, density))
        candidate, distinct = select_design_grammar(
            _design_profile_artisan_payload(artisan), _autres_profils(db, site),
            direction=preferred_direction, ambience=ambience, density=v3_density,
            exclude_signatures=exclude,
        )
        candidate = validate_design_profile(candidate)
    else:
        candidate, distinct = select_candidate_design_profile(
            _design_profile_artisan_payload(artisan), current, _autres_profils(db, site),
            preferred_family=preferred_family, exclude_signatures=exclude, spacing_override=density,
        )
        candidate = DesignProfileOut(**candidate).model_dump()
    candidate = _apply_candidate_overrides(candidate, overrides)
    if overrides:
        # Un override explicite peut legitimement rapprocher la candidate du
        # current (l'Admin sait ce qu'il fait en reglages avances) : on
        # rapporte honnetement la distance reelle plutot que de la masquer.
        distinct = (v3_similarity_score(candidate, current) < .58) if str(candidate.get("design_engine_version")).startswith("v3") and str(current.get("design_engine_version")).startswith("v3") else (similarity_score(candidate, current) < SIMILARITY_THRESHOLD)

    site.candidate_design_profile = candidate
    db.commit()
    db.refresh(site)
    generate_candidate_preview(db, artisan, site)
    return candidate, distinct


def _valid_stored_profile_field(site: SiteVitrine, field: str) -> dict | None:
    value = getattr(site, field, None)
    if not value:
        return None
    try:
        return validate_design_profile(value)
    except Exception:
        return None


def abandon_design_candidate(db: Session, artisan: Artisan, site: SiteVitrine) -> None:
    """Supprime l'alternative en cours sans jamais toucher au current ni au
    site publie (voir le brief, section 19)."""
    site.candidate_design_profile = None
    db.commit()
    storage_key = candidate_preview_storage_key(artisan.id)
    storage = get_storage()
    if storage.exists(storage_key):
        storage.delete(storage_key)


def adopt_design_candidate(db: Session, artisan: Artisan, site: SiteVitrine) -> dict:
    """Le candidate devient le nouveau current - seule action de ce lot qui
    modifie design_profile. Ne publie JAMAIS automatiquement : la
    regeneration qui suit (generate_site_preview) remet le site a l'etat
    "genere", exactement comme n'importe quel autre changement de
    configuration suivi d'une regeneration (voir admin_site_update) - un
    site "pret" ou "publie" doit donc explicitement repasser par "pret" puis
    "publie" apres adoption (voir le brief, sections 17-18)."""
    candidate = _valid_stored_profile_field(site, "candidate_design_profile")
    if candidate is None:
        raise ValueError("Aucune alternative a adopter")
    site.design_profile = candidate
    site.candidate_design_profile = None
    db.commit()
    db.refresh(site)
    abandon_design_candidate(db, artisan, site)  # nettoie le fichier de preview candidate devenu obsolete
    generate_site_preview(db, artisan, site)
    return candidate


def generate_candidate_preview(db: Session, artisan: Artisan, site: SiteVitrine) -> str:
    """Rendu HTML de l'alternative, isole du current : n'ecrit jamais dans
    site.design_profile ni site.storage_key (voir le brief, section 14).
    Reutilise le meme pipeline de rendu (generate_site) et la meme API de
    preview isolee (/admin/preview-api) que la preview courante."""
    candidate = _valid_stored_profile_field(site, "candidate_design_profile")
    if candidate is None:
        raise ValueError("Aucune alternative a previsualiser")
    ensure_media_profile(db, artisan, site)
    config = merged_site_config(artisan, site)
    payload = build_generator_payload(db, artisan, config, site)
    payload["design_profile"] = candidate
    generated_html = generate_site(payload, api_base_url="/admin/preview-api")
    get_storage().save(candidate_preview_storage_key(artisan.id), generated_html.encode("utf-8"))
    return generated_html


def sections_availability(db: Session, artisan: Artisan, site: SiteVitrine) -> list[dict]:
    """Pour chaque section du catalogue (voir generator/design_registry.py
    ::SECTION_CATALOG), indique si elle pourra reellement apparaitre pour cet
    artisan et pourquoi - utile pour comprendre pourquoi une preview parait
    courte (voir le brief, section 24). Jamais de contenu invente : une
    section sans donnee reelle est honnetement marquee indisponible."""
    config = merged_site_config(artisan, site)
    media = media_profile_dict(db, artisan, site, admin=True)
    disponible = {
        "assurance_decennale_nom": bool(artisan.assurance_decennale_nom),
        "services": bool(config.get("services")),
        "realisations": media.get("has_gallery") or bool(artisan.assurance_decennale_nom),
        "photos": media.get("has_gallery", False),
        "avis": db.query(Avis).filter(Avis.artisan_id == artisan.id, Avis.publie_site.is_(True)).count() > 0,
        "ville": bool(artisan.ville),
        "stats": bool(config.get("stats")),
        "photos_avant_apres": media.get("has_before_after", False),
    }
    labels = {
        "hero": "Hero", "trust": "Assurance décennale", "services": "Prestations",
        "featured_project": "Réalisation en avant", "about": "À propos",
        "gallery": "Galerie photo", "reviews": "Avis clients", "service_area": "Zone d'intervention",
        "cta": "Appel à l'action", "stats": "Chiffres clés", "process": "Étapes",
        "before_after": "Avant / après", "reasons": "Nos engagements", "contact": "Formulaire de contact",
    }
    result = []
    for section, meta in SECTION_CATALOG.items():
        requires = meta.get("requires") or []
        ok = all(disponible.get(key) for key in requires)
        raison = None if ok else "Cette section n'apparaît pas car aucune donnée n'est disponible."
        result.append({"section": section, "label": labels.get(section, section), "disponible": ok, "raison": raison})
    return result


def preview_storage_key(artisan_id: int) -> str:
    if artisan_id <= 0:
        raise ValueError("Identifiant artisan invalide")
    return f"admin-site-previews/{artisan_id}/index.html"


def _safe_text(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def build_generator_payload(
    db: Session,
    artisan: Artisan,
    config: dict,
    site: SiteVitrine | None = None,
) -> dict:
    validate_site_variants(artisan, config)
    avis = db.query(Avis).filter(Avis.artisan_id == artisan.id, Avis.publie_site.is_(True)).all()
    media_overview = media_overview_dict(db, artisan, admin=True)
    media_profile = media_overview["profile"]
    return {
        "_content_escaped": True,
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
        "has_logo": media_profile["has_logo"],
        "artisan_photo_count": media_profile["artisan_photo_count"],
        "has_gallery": media_profile["has_gallery"],
        "has_before_after": media_profile["has_before_after"],
        "selected_media": media_profile["selections"],
        "logo": media_overview["logo"],
        "design_profile": dict(site.design_profile) if site and site.design_profile else None,
        "url_publique": _safe_text(site.url_publique) if site else "",
    }


def generate_site_preview(db: Session, artisan: Artisan, site: SiteVitrine) -> str:
    # Assure un design_profile stable AVANT de generer (voir
    # ensure_design_profile) : cree une fois si absent, jamais recalcule au
    # hasard ensuite. Le rendu V1 (generate_site ci-dessous) reste inchange
    # dans ce lot - voir la note de compatibilite du Lot 1.
    ensure_design_profile(db, artisan, site)
    ensure_media_profile(db, artisan, site)
    config = merged_site_config(artisan, site)
    payload = build_generator_payload(db, artisan, config, site)
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
