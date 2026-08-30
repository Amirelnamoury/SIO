"""Registre central du moteur de design V2 des sites vitrines (Lot 1).

Objectif : que deux artisans du meme metier obtiennent des sites reellement
differents (structure, hero, composition, palette, police...) plutot que des
clones les uns des autres - sans jamais inventer de donnees (annees
d'experience, avis, certifications...) pour "remplir" une section.

Ce module ne fait QUE definir le vocabulaire autorise (familles, variantes,
palettes, gabarits d'ordre de sections) et les regles pures qui en decoulent
(coherence d'une famille, ce qu'une section necessite reellement pour
s'afficher). Il ne genere aucun HTML : voir generator/design_selector.py
pour la selection d'un profil, et generator/site_generator.py pour le rendu
(inchange dans ce lot - voir sa docstring).

Toutes les valeurs utilisees ailleurs dans le projet DOIVENT venir d'ici :
aucune chaine magique dispersee dans le reste du code.
"""

import hashlib

# ---------- Version du moteur (trace quelle logique a produit un profil) ----------

DESIGN_ENGINE_VERSION = "v2.0"

# ---------- Familles de design ----------
# Chaque famille est une "intention" coherente : elle fixe les variantes de
# structure (header/hero/services/gallery/about/reviews/cta/footer) pour que
# le rendu reste toujours cohesif. La diversite entre deux artisans de la
# MEME famille vient des axes "libres" (palette, police, rayons, espacements,
# ordre des sections) - voir design_selector.py.

DESIGN_FAMILIES = ["atelier", "architecture", "impact", "technique", "local", "signature"]

# ---------- Registre des variantes (par section) ----------

HEADER_VARIANTS = ["classic", "minimal", "centered", "compact"]
HERO_VARIANTS = ["fullscreen", "split", "asymmetric", "compact", "editorial", "card"]
SERVICES_VARIANTS = ["cards", "editorial", "list", "grid", "alternating"]
GALLERY_VARIANTS = ["grid", "masonry", "featured", "horizontal"]
ABOUT_VARIANTS = ["classic", "editorial", "split", "compact"]
REVIEWS_VARIANTS = ["cards", "featured", "minimal"]
CTA_VARIANTS = ["banner", "floating", "split", "minimal"]
FOOTER_VARIANTS = ["simple", "columns", "centered", "map"]

RADIUS_STYLES = ["sharp", "soft", "rounded", "pill"]
SPACING_STYLES = ["compact", "comfortable", "spacious"]
# Prepare uniquement le vocabulaire (Lot 2 branchera le traitement reel des
# images - upload, compression, AVIF/WebP - voir le brief : hors scope ici).
IMAGE_TREATMENTS = ["flat", "duotone", "framed", "overlay"]

# Paires de polices (identite typographique). Volontairement decouple des
# polices par metier de themes.py (THEMES[metier]["font"]) : ce registre
# prepare le rendu V2, il ne remplace pas le rendu V1 dans ce lot (voir
# ADMIN_COMPAT dans le rapport de la mission).
FONT_PAIRS = [
    {"id": "poppins-inter", "heading": "'Poppins', sans-serif", "body": "'Inter', sans-serif"},
    {"id": "archivo-inter", "heading": "'Archivo', sans-serif", "body": "'Inter', sans-serif"},
    {"id": "fredoka-inter", "heading": "'Fredoka', sans-serif", "body": "'Inter', sans-serif"},
    {"id": "rajdhani-inter", "heading": "'Rajdhani', sans-serif", "body": "'Inter', sans-serif"},
]
FONT_PAIR_IDS = [pair["id"] for pair in FONT_PAIRS]

# Emplacements de palette (identifiants symboliques persistes). Le rendu V1
# actuel choisit deja une palette parmi 3 par metier (voir
# generator/themes.py::PALETTE_VARIANTS, index 0-2) : ces 3 slots reutilisent
# exactement ce meme index, sans dupliquer les valeurs hexadecimales - la
# palette effective reste celle de themes.py, ce registre nomme juste le slot.
PALETTE_SLOTS = ["palette-1", "palette-2", "palette-3"]


def palette_slot_index(slot: str) -> int:
    """Convertit un identifiant de slot ('palette-1'...) vers l'index 0-2
    utilise par generator/themes.py::PALETTE_VARIANTS."""
    return PALETTE_SLOTS.index(slot)


# ---------- Catalogue des sections ----------
# "requires" liste les cles de disponibilite reelle (voir available_data
# dans resolve_visible_sections) necessaires pour qu'une section ait un sens.
# Une section sans "requires" peut toujours s'afficher avec du contenu
# generique honnete (jamais une donnee inventee). "hero" est le seul bloc
# jamais omis (identite minimale du site).
SECTION_CATALOG = {
    "hero": {"requires": []},
    "trust": {"requires": ["assurance_decennale_nom"]},
    "services": {"requires": ["services"]},
    "featured_project": {"requires": ["realisations"]},
    "about": {"requires": []},
    "gallery": {"requires": ["photos"]},
    "reviews": {"requires": ["avis"]},
    "service_area": {"requires": ["ville"]},
    "cta": {"requires": []},
    "stats": {"requires": ["stats"]},
    "process": {"requires": []},
    "before_after": {"requires": ["photos_avant_apres"]},
    "reasons": {"requires": []},
    "contact": {"requires": []},
}

# Gabarits d'ordre de sections (3 exemples du brief). Un seul est choisi par
# profil (voir design_selector.py) - le moteur ne les combine pas.
SECTION_ORDER_TEMPLATES = {
    "trust_led": [
        "hero", "trust", "services", "featured_project", "about",
        "gallery", "reviews", "service_area", "cta",
    ],
    "process_led": [
        "hero", "services", "before_after", "reasons", "gallery",
        "process", "reviews", "contact",
    ],
    "stats_led": [
        "hero", "about", "stats", "gallery", "services",
        "service_area", "reviews", "cta",
    ],
}
SECTION_ORDER_TEMPLATE_IDS = list(SECTION_ORDER_TEMPLATES.keys())


def resolve_visible_sections(section_order_template: str, available_data: dict) -> list[str]:
    """Filtre un gabarit d'ordre de sections selon les donnees reellement
    disponibles pour cet artisan. Ne fabrique jamais de contenu : une section
    dont les donnees requises manquent est simplement omise (jamais remplie
    avec des valeurs inventees). 'hero' est toujours conserve.

    available_data : dict de booleens, ex. {"services": True, "avis": False,
    "stats": True, "ville": True, "assurance_decennale_nom": False,
    "photos": False, "realisations": False, "photos_avant_apres": False}."""
    template = SECTION_ORDER_TEMPLATES.get(section_order_template, SECTION_ORDER_TEMPLATES[SECTION_ORDER_TEMPLATE_IDS[0]])
    visible = []
    for section in template:
        if section == "hero":
            visible.append(section)
            continue
        requires = SECTION_CATALOG.get(section, {}).get("requires", [])
        if all(available_data.get(key) for key in requires):
            visible.append(section)
    return visible


# ---------- Regles par famille (Lot 1.1) ----------
# Une famille est une DIRECTION ARTISTIQUE (un ensemble de contraintes), pas
# un template fige : pour chaque axe structurel, elle liste les variantes
# COMPATIBLES avec sa personnalite, avec un poids (plus un poids est eleve,
# plus cette variante est frequente pour cette famille - jamais exclusif).
# C'est ce qui garantit qu'un site "architecture" reste toujours credible
# visuellement (jamais "impact" avec un CTA minimaliste), tout en permettant
# a deux artisans "architecture" d'avoir des structures reellement
# differentes (header/hero/services/gallery/about/reviews/cta/footer
# selectionnes chacun independamment - voir select_design_profile).
#
# Personnalite visee par famille (guide les poids ci-dessous) :
#   atelier      -> chaleureux, artisanal
#   architecture -> premium, minimal, editorial
#   impact       -> fort, dynamique, gros CTA
#   technique    -> structure, precis
#   local        -> proximite, confiance
#   signature    -> haut de gamme, photographique
#
# Chaque valeur du Lot 1 (celle qui avait le plus de poids visuel avant ce
# lot) reste le choix DOMINANT (poids le plus eleve) de sa famille : un
# design_profile deja persiste reste donc pleinement coherent avec ce
# registre, meme si nous ne le recalculons jamais (voir ensure_design_profile).
DESIGN_FAMILY_RULES = {
    "atelier": {
        "header_variant": {"minimal": 3, "centered": 2, "compact": 1},
        "hero_variant": {"asymmetric": 3, "compact": 2, "editorial": 1},
        "services_variant": {"alternating": 3, "list": 2, "grid": 1},
        "gallery_variant": {"grid": 3, "horizontal": 2, "masonry": 1},
        "about_variant": {"compact": 3, "classic": 2, "editorial": 1},
        "reviews_variant": {"minimal": 3, "cards": 2},
        "cta_variant": {"minimal": 3, "floating": 2},
        "footer_variant": {"simple": 3, "centered": 2},
    },
    "architecture": {
        "header_variant": {"classic": 3, "minimal": 2, "centered": 1},
        "hero_variant": {"split": 3, "editorial": 3, "asymmetric": 2, "card": 1},
        "services_variant": {"editorial": 3, "grid": 2, "list": 1},
        "gallery_variant": {"masonry": 3, "featured": 2, "grid": 1},
        "about_variant": {"split": 3, "editorial": 2, "classic": 1},
        "reviews_variant": {"featured": 3, "cards": 2},
        "cta_variant": {"split": 3, "banner": 2},
        "footer_variant": {"columns": 3, "map": 2},
    },
    "impact": {
        "header_variant": {"compact": 3, "classic": 2, "minimal": 1},
        "hero_variant": {"fullscreen": 3, "card": 2, "split": 1},
        "services_variant": {"cards": 3, "grid": 2, "alternating": 1},
        "gallery_variant": {"featured": 3, "grid": 2, "masonry": 1},
        "about_variant": {"classic": 3, "compact": 2},
        "reviews_variant": {"cards": 3, "featured": 2},
        "cta_variant": {"banner": 3, "floating": 2},
        "footer_variant": {"columns": 3, "simple": 2},
    },
    "technique": {
        "header_variant": {"classic": 3, "compact": 2, "centered": 1},
        "hero_variant": {"compact": 3, "split": 2, "asymmetric": 1},
        "services_variant": {"list": 3, "grid": 2, "editorial": 1},
        "gallery_variant": {"horizontal": 3, "grid": 2},
        "about_variant": {"classic": 3, "split": 2},
        "reviews_variant": {"minimal": 3, "cards": 2},
        "cta_variant": {"floating": 3, "minimal": 2},
        "footer_variant": {"simple": 3, "columns": 2},
    },
    "local": {
        "header_variant": {"centered": 3, "classic": 2, "minimal": 1},
        "hero_variant": {"editorial": 3, "compact": 2, "split": 1},
        "services_variant": {"grid": 3, "list": 2, "alternating": 1},
        "gallery_variant": {"grid": 3, "horizontal": 2},
        "about_variant": {"editorial": 3, "classic": 2},
        "reviews_variant": {"cards": 3, "minimal": 2},
        "cta_variant": {"banner": 3, "split": 2},
        "footer_variant": {"centered": 3, "simple": 2},
    },
    "signature": {
        "header_variant": {"centered": 3, "minimal": 2, "classic": 1},
        "hero_variant": {"card": 3, "editorial": 3, "split": 2, "fullscreen": 1},
        "services_variant": {"editorial": 3, "cards": 2, "grid": 1},
        "gallery_variant": {"featured": 3, "masonry": 2, "grid": 1},
        "about_variant": {"split": 3, "editorial": 2},
        "reviews_variant": {"featured": 3, "cards": 2},
        "cta_variant": {"split": 3, "banner": 2},
        "footer_variant": {"map": 3, "columns": 2},
    },
}
# Les 8 axes structurels controles par DESIGN_FAMILY_RULES (dans cet ordre,
# reutilise par design_selector.py::_candidate_profile).
STRUCTURAL_AXES = [
    "header_variant", "hero_variant", "services_variant", "gallery_variant",
    "about_variant", "reviews_variant", "cta_variant", "footer_variant",
]


def _stable_index(seed: str, salt: str, modulo: int) -> int:
    """Meme mecanisme que generator/themes.py::_stable_index (duplique
    volontairement ici plutot qu'importe, pour ne jamais coupler le moteur V2
    au module V1 - voir la note de compatibilite dans le rapport)."""
    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).hexdigest()
    return int(digest, 16) % modulo


def _stable_fraction(seed: str, salt: str) -> float:
    """Meme principe que _stable_index, mais renvoie un flottant stable dans
    [0, 1) - utilise pour un tirage pondere deterministe (voir
    weighted_stable_choice)."""
    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).hexdigest()
    return (int(digest, 16) % 10_000_000) / 10_000_000


def weighted_stable_choice(seed: str, salt: str, weighted_options: dict) -> str:
    """Choisit une variante parmi les options AUTORISEES par la famille pour
    cet axe, en respectant leurs poids relatifs, de facon 100% deterministe
    (meme seed+salt -> toujours le meme choix). Jamais de valeur hors de
    weighted_options : une famille garde ainsi sa personnalite (pas de
    cascade de if, juste ce registre)."""
    total = sum(weighted_options.values())
    threshold = _stable_fraction(seed, salt) * total
    cumulative = 0
    for value, weight in weighted_options.items():
        cumulative += weight
        if threshold < cumulative:
            return value
    return next(iter(weighted_options))  # filet de securite (arrondi flottant)


# ---------- Points d'extension pour de futures ponderations metier ----------
# Volontairement vide dans ce lot : prepare seulement la ou brancher plus
# tard des ponderations (metier, nombre de prestations, presence d'avis, de
# realisations, de chiffres cles, de photos/logo...) sans devoir reprendre
# l'architecture. select_design_profile() accepte deja un dict de contexte
# ouvert (voir design_selector.py) pour cette raison.
WEIGHTING_HOOKS: dict = {}
