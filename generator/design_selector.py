"""Selection du design_profile d'un artisan (Lot 1 - moteur de design V2).

Strategie retenue (simple, explicable, deterministe/testable, sans service
externe, sans IA - voir le brief "ANTI-CLONAGE / DESIGN SIGNATURE") :

1. Un profil "candidat" est derive de facon 100% deterministe d'une graine
   stable (slug/siret/nom de l'artisan) : un meme artisan obtient toujours le
   meme candidat de base, un artisan different obtient presque toujours un
   candidat different (hachage SHA-256 par axe, comme generator/themes.py).
2. On compare ce candidat aux profils deja persistes des autres sites : s'il
   est trop proche d'un profil existant (meme famille, meme hero, meme
   services, meme gallery, meme ordre de sections ET meme palette - le score
   de similarite depasse SIMILARITY_THRESHOLD), on retente avec une graine
   legerement perturbee ("|attempt=N"), jusqu'a MAX_ATTEMPTS tentatives.
3. On ne demande pas une unicite mathematique : si aucune tentative n'est
   suffisamment distincte (beaucoup de sites deja generes), on garde le
   candidat le moins similaire trouve plutot que d'echouer la generation.

Chaque tentative reste elle-meme deterministe (memes profils existants en
entree -> meme resultat en sortie), donc testable sans alea reel.
"""

from generator.design_registry import (
    DESIGN_ENGINE_VERSION,
    DESIGN_FAMILIES,
    DESIGN_FAMILY_RULES,
    FONT_PAIR_IDS,
    PALETTE_SLOTS,
    RADIUS_STYLES,
    SECTION_ORDER_TEMPLATE_IDS,
    SECTION_ORDER_TEMPLATES,
    SPACING_STYLES,
    _stable_index,
)

MAX_ATTEMPTS = 6
# Compare sur : design_family, hero_variant, services_variant, gallery_variant,
# section_order (tuple), palette - voir build_design_signature(). "Trop proche"
# = au moins 5 des 6 axes identiques.
SIMILARITY_THRESHOLD = 5 / 6
# Nombre de profils existants les plus recents compares (borne le cout, une
# diversite "raisonnable" n'exige pas de comparer tout l'historique - voir
# le brief : "Je ne demande PAS une unicite mathematique eternelle").
RECENT_PROFILES_WINDOW = 20


def _seed(artisan: dict) -> str:
    """Meme notion de graine stable que generator/themes.py::_seed."""
    return str(artisan.get("slug") or artisan.get("siret") or artisan.get("nom_entreprise") or "artisan")


def _candidate_profile(seed: str, attempt: int) -> dict:
    """Construit un profil 100% deterministe pour (seed, attempt). Les
    variantes structurelles (header/hero/services/gallery/about/reviews/cta/
    footer) sont fixees par la famille choisie (coherence visuelle) ; les
    axes libres (palette, police, rayons, espacements, ordre des sections)
    varient independamment - c'est principalement de la que vient la
    diversite entre deux artisans d'une meme famille."""
    salt_suffix = "" if attempt == 0 else f"|attempt={attempt}"

    family = DESIGN_FAMILIES[_stable_index(seed, f"family{salt_suffix}", len(DESIGN_FAMILIES))]
    rules = DESIGN_FAMILY_RULES[family]

    palette = PALETTE_SLOTS[_stable_index(seed, f"palette{salt_suffix}", len(PALETTE_SLOTS))]
    font_pair = FONT_PAIR_IDS[_stable_index(seed, f"font{salt_suffix}", len(FONT_PAIR_IDS))]
    radius_style = RADIUS_STYLES[_stable_index(seed, f"radius{salt_suffix}", len(RADIUS_STYLES))]
    spacing_style = SPACING_STYLES[_stable_index(seed, f"spacing{salt_suffix}", len(SPACING_STYLES))]
    section_order_template_id = SECTION_ORDER_TEMPLATE_IDS[
        _stable_index(seed, f"section_order{salt_suffix}", len(SECTION_ORDER_TEMPLATE_IDS))
    ]
    # section_order persiste la LISTE resolue (identite structurelle stable),
    # pas seulement l'id du gabarit : l'omission d'une section faute de
    # donnees (voir resolve_visible_sections) se calcule a part, au moment du
    # rendu, sans jamais alterer ce profil persiste.
    section_order = list(SECTION_ORDER_TEMPLATES[section_order_template_id])

    return {
        "design_family": family,
        "header_variant": rules["header_variant"],
        "hero_variant": rules["hero_variant"],
        "services_variant": rules["services_variant"],
        "gallery_variant": rules["gallery_variant"],
        "about_variant": rules["about_variant"],
        "reviews_variant": rules["reviews_variant"],
        "cta_variant": rules["cta_variant"],
        "footer_variant": rules["footer_variant"],
        "section_order": section_order,
        "palette": palette,
        "font_pair": font_pair,
        "radius_style": radius_style,
        "spacing_style": spacing_style,
        # image_treatment prepare le Lot 2 (pas encore utilise par un rendu -
        # voir generator/design_registry.py::IMAGE_TREATMENTS) : une valeur
        # neutre stable suffit pour ce lot, jamais recalculee au hasard.
        "image_treatment": "flat",
    }


def _comparable_tuple(profile: dict) -> tuple:
    """Les 6 axes compares pour juger si deux profils sont "trop proches"
    (voir le brief : meme famille, meme hero, meme services, meme gallery,
    meme ordre de sections, meme palette)."""
    return (
        profile.get("design_family"),
        profile.get("hero_variant"),
        profile.get("services_variant"),
        profile.get("gallery_variant"),
        tuple(profile.get("section_order") or ()),
        profile.get("palette"),
    )


def similarity_score(profile_a: dict, profile_b: dict) -> float:
    """Fraction des 6 axes compares identiques entre deux profils (0..1)."""
    a, b = _comparable_tuple(profile_a), _comparable_tuple(profile_b)
    matches = sum(1 for x, y in zip(a, b) if x is not None and x == y)
    return matches / len(a)


def build_design_signature(profile: dict) -> str:
    """Chaine compacte representant les elements majeurs qui influencent la
    perception du site (voir le brief : "architecture|split|editorial|
    masonry|minimal|palette-3|...")."""
    fields = [
        "design_family", "header_variant", "hero_variant", "services_variant",
        "gallery_variant", "about_variant", "reviews_variant", "cta_variant",
        "footer_variant", "palette", "font_pair", "radius_style", "spacing_style",
    ]
    parts = [str(profile.get(field, "")) for field in fields]
    parts.append("+".join(profile.get("section_order") or ()))
    return "|".join(parts)


def select_design_profile(
    artisan: dict,
    existing_profiles: list[dict],
    *,
    exclude_signatures: set[str] | None = None,
) -> dict:
    """Choisit un design_profile pour cet artisan.

    artisan : dict avec au moins "slug" (et optionnellement "siret",
    "nom_entreprise", "metier" - metier n'influence pas encore la selection
    dans ce lot, voir generator/design_registry.py::WEIGHTING_HOOKS pour le
    point d'extension prevu).
    existing_profiles : profils deja persistes d'AUTRES sites (les plus
    recents suffisent, voir RECENT_PROFILES_WINDOW), pour l'anti-clonage.
    exclude_signatures : signatures a eviter explicitement en plus des
    profils existants - le point d'entree prevu pour une future fonction
    "regenerer une variante" (exclude_current_profile / generate_alternative)
    sans casser le profil actif tant que l'alternative n'est pas acceptee.

    Deterministe : memes arguments -> toujours le meme resultat (aucun alea
    non reproductible)."""
    seed = _seed(artisan)
    recent = existing_profiles[-RECENT_PROFILES_WINDOW:]
    exclude_signatures = exclude_signatures or set()

    best_candidate = None
    best_score = None
    for attempt in range(MAX_ATTEMPTS):
        candidate = _candidate_profile(seed, attempt)
        signature = build_design_signature(candidate)
        if signature in exclude_signatures:
            continue
        worst_similarity = max((similarity_score(candidate, existing) for existing in recent), default=0.0)
        if worst_similarity < SIMILARITY_THRESHOLD:
            candidate["design_engine_version"] = DESIGN_ENGINE_VERSION
            candidate["design_signature"] = signature
            return candidate
        if best_score is None or worst_similarity < best_score:
            best_candidate, best_score = candidate, worst_similarity

    # Aucune tentative suffisamment distincte (diversite "raisonnable", pas
    # une unicite garantie - voir le brief) : on garde la moins similaire.
    if best_candidate is None:
        best_candidate = _candidate_profile(seed, 0)
    best_candidate["design_engine_version"] = DESIGN_ENGINE_VERSION
    best_candidate["design_signature"] = build_design_signature(best_candidate)
    return best_candidate
