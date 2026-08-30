"""Selection du design_profile d'un artisan (moteur de design V2).

Strategie retenue (simple, explicable, deterministe/testable, sans service
externe, sans IA - voir le brief "ANTI-CLONAGE / DESIGN SIGNATURE") :

1. Un profil "candidat" est derive de facon 100% deterministe d'une graine
   stable (slug/siret/nom de l'artisan) : un meme artisan obtient toujours le
   meme candidat de base, un artisan different obtient presque toujours un
   candidat different (hachage SHA-256 par axe, comme generator/themes.py).
   Depuis le Lot 1.1, la famille ne fixe plus UNE variante par axe : elle
   liste les variantes COMPATIBLES avec sa personnalite (avec un poids), et
   chaque axe structurel (header/hero/services/gallery/about/reviews/cta/
   footer) est tire INDEPENDAMMENT avec son propre sel de hachage - deux
   artisans de la meme famille peuvent donc avoir des structures reellement
   differentes, tout en restant coherents avec leur famille (voir
   generator/design_registry.py::DESIGN_FAMILY_RULES).
2. On compare ce candidat aux profils deja persistes des autres sites : s'il
   est trop proche d'un profil existant (score de similarite PONDERE, voir
   similarity_score, superieur a SIMILARITY_THRESHOLD), on retente avec une
   graine legerement perturbee ("|attempt=N"), jusqu'a MAX_ATTEMPTS tentatives.
3. On ne demande pas une unicite mathematique : si aucune tentative n'est
   suffisamment distincte (beaucoup de sites deja generes, ou toutes les
   combinaisons d'une famille deja utilisees), on garde le candidat le moins
   similaire trouve plutot que d'echouer la generation.

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
    STRUCTURAL_AXES,
    _stable_index,
    weighted_stable_choice,
)

MAX_ATTEMPTS = 6
# Nombre de profils existants les plus recents compares (borne le cout, une
# diversite "raisonnable" n'exige pas de comparer tout l'historique - voir
# le brief : "Je ne demande PAS une unicite mathematique eternelle").
RECENT_PROFILES_WINDOW = 20

# ---------- Score de similarite (anti-clonage, Lot 1.1) ----------
# Chaque axe compte pour un poids different - les elements les plus
# perceptuellement importants comptent davantage (voir le brief) :
#   3 : design_family, hero_variant, services_variant, gallery_variant,
#       section_order (structure et direction artistique globales)
#   2 : palette (tres visible, mais un seul aspect coloristique)
#   1 : header_variant, about_variant, reviews_variant, cta_variant,
#       footer_variant, font_pair (details qui affinent une structure deja
#       proche, sans a eux seuls constituer un "clone")
# similarite = somme des poids qui matchent / somme totale des poids.
SIMILARITY_WEIGHTS = {
    "design_family": 3,
    "header_variant": 1,
    "hero_variant": 3,
    "services_variant": 3,
    "gallery_variant": 3,
    "about_variant": 1,
    "reviews_variant": 1,
    "cta_variant": 1,
    "footer_variant": 1,
    "section_order": 3,
    "palette": 2,
    "font_pair": 1,
}
_TOTAL_SIMILARITY_WEIGHT = sum(SIMILARITY_WEIGHTS.values())
# "Trop proche" : environ les 5 axes les plus lourds (famille, hero,
# services, gallery, section_order - poids 3 chacun = 15/23) deja identiques
# suffit a declencher une nouvelle tentative, sans exiger une identite totale
# improbable une fois les axes tires independamment.
SIMILARITY_THRESHOLD = 0.6


def _seed(artisan: dict) -> str:
    """Meme notion de graine stable que generator/themes.py::_seed."""
    return str(artisan.get("slug") or artisan.get("siret") or artisan.get("nom_entreprise") or "artisan")


def _candidate_profile(seed: str, attempt: int) -> dict:
    """Construit un profil 100% deterministe pour (seed, attempt).

    La famille fixe seulement quelles variantes sont COMPATIBLES par axe
    (voir DESIGN_FAMILY_RULES) ; chaque axe structurel (header/hero/
    services/gallery/about/reviews/cta/footer) est ensuite tire
    independamment, avec son propre sel de hachage, parmi les variantes
    autorisees pour cette famille - c'est ce qui permet a deux artisans de la
    meme famille d'avoir des structures differentes tout en restant
    coherents. Les axes libres (palette, police, rayons, espacements, ordre
    des sections) varient eux aussi independamment, sans contrainte de
    famille."""
    salt_suffix = "" if attempt == 0 else f"|attempt={attempt}"

    family = DESIGN_FAMILIES[_stable_index(seed, f"family{salt_suffix}", len(DESIGN_FAMILIES))]
    rules = DESIGN_FAMILY_RULES[family]

    structural = {
        axis: weighted_stable_choice(seed, f"{axis}{salt_suffix}", rules[axis])
        for axis in STRUCTURAL_AXES
    }

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
        **structural,
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


def similarity_score(profile_a: dict, profile_b: dict) -> float:
    """Score de similarite PONDERE (0..1) entre deux profils - voir
    SIMILARITY_WEIGHTS. section_order est compare comme une liste (l'ordre
    compte), les autres axes comme des valeurs simples."""
    total = 0
    for axis, weight in SIMILARITY_WEIGHTS.items():
        if axis == "section_order":
            match = (profile_a.get("section_order") or []) == (profile_b.get("section_order") or [])
        else:
            a, b = profile_a.get(axis), profile_b.get(axis)
            match = a is not None and a == b
        if match:
            total += weight
    return total / _TOTAL_SIMILARITY_WEIGHT


def build_design_signature(profile: dict) -> str:
    """Chaine compacte representant les elements majeurs qui influencent la
    perception du site (voir le brief : "architecture|split|editorial|
    masonry|minimal|palette-3|..."). Inclut tous les axes structurels : deux
    profils de la meme famille mais avec des heroes/services/gallery
    differents n'ont donc jamais la meme signature."""
    fields = [
        "design_family", *STRUCTURAL_AXES, "palette", "font_pair", "radius_style", "spacing_style",
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
