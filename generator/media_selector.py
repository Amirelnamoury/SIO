"""Selection pure et deterministe des medias d'un rendu Site Vitrine V3."""
from collections import Counter
from hashlib import sha256


MEDIA_USAGES = ("hero", "gallery", "about", "featured_project", "before_after")
USAGE_COUNTS = {"hero": 1, "gallery": 6, "about": 1, "featured_project": 1, "before_after": 2}
USAGE_CATEGORIES = {
    "hero": ("realisation", "chantier", "atelier", "equipe", "vehicule", "autre"),
    "gallery": ("realisation", "chantier", "equipe", "atelier", "vehicule", "avant", "apres", "autre"),
    "about": ("equipe", "atelier", "vehicule", "autre"),
    "featured_project": ("realisation", "chantier", "avant", "apres"),
    "before_after": ("avant", "apres"),
}
METIER_ALIASES = {
    "plombier": {"plombier", "plomberie", "chauffage", "renovation"},
    "electricien": {"electricien", "electricite", "renovation"},
    "peintre": {"peintre", "peinture", "renovation"},
    "macon": {"macon", "maconnerie", "renovation"},
    "general": {"general", "renovation"},
    "menuisier": {"menuisier", "menuiserie", "renovation"},
    "renovateur": {"renovateur", "renovation"},
}


def _stable_rank(seed: str, usage: str, identifier: object) -> str:
    return sha256(f"{seed}|{usage}|{identifier}".encode("utf-8")).hexdigest()


def _compatible_library(media: dict, metier: str, usage: str) -> bool:
    aliases = METIER_ALIASES.get(metier, {metier, "renovation"})
    usages = set(media.get("usage_recommande") or ())
    return media.get("actif", True) and media.get("metier") in aliases and usage in usages


def _artisan_candidates(artisan_media: list[dict], usage: str, seed: str) -> list[dict]:
    categories = USAGE_CATEGORIES[usage]
    rank = {category: index for index, category in enumerate(categories)}
    candidates = [
        media for media in artisan_media
        if media.get("actif", True) and media.get("type_media") == "photo" and media.get("categorie") in rank
    ]
    if usage == "before_after":
        if not any(m.get("categorie") == "avant" for m in candidates) or not any(m.get("categorie") == "apres" for m in candidates):
            return []
    return sorted(
        candidates,
        key=lambda media: (
            rank[media.get("categorie")],
            media.get("ordre", 0),
            _stable_rank(seed, usage, media.get("id")),
        ),
    )


def select_site_media(
    context: dict,
    artisan_media: list[dict],
    library_media: list[dict],
    usage_history: list[dict],
) -> list[dict]:
    """Retourne un media profile sans effectuer aucune lecture/ecriture.

    Priorite stricte par usage : photos artisan compatibles, puis registre
    metier licencie, puis fallback graphique. L'historique ne bloque jamais
    definitivement un media : il place simplement les moins utilises devant.
    """
    seed = str(context.get("slug") or context.get("artisan_id") or "artisan")
    metier = str(context.get("metier") or "general")
    usage_counts = Counter((item.get("library_media_id"), item.get("usage")) for item in usage_history)
    used_artisan: set[int] = set()
    used_library: set[int] = set()
    result: list[dict] = []

    for usage in MEDIA_USAGES:
        desired = USAGE_COUNTS[usage]
        artisan_candidates = _artisan_candidates(artisan_media, usage, seed)
        artisan_available = [m for m in artisan_candidates if m.get("id") not in used_artisan]
        chosen_artisan = (artisan_available or artisan_candidates)[:desired]
        if chosen_artisan:
            for position, media in enumerate(chosen_artisan):
                media_id = int(media["id"])
                used_artisan.add(media_id)
                result.append({"usage": usage, "position": position, "source": "artisan", "site_media_id": media_id})
            continue

        library_candidates = [media for media in library_media if _compatible_library(media, metier, usage) and media.get("id") not in used_library]
        library_candidates.sort(key=lambda media: (
            usage_counts[(media.get("id"), usage)],
            _stable_rank(seed, usage, media.get("media_id") or media.get("id")),
        ))
        chosen_library = library_candidates[:desired]
        if chosen_library:
            for position, media in enumerate(chosen_library):
                library_id = int(media["id"])
                used_library.add(library_id)
                result.append({"usage": usage, "position": position, "source": "bibliotheque", "library_media_id": library_id})
            continue

        result.append({"usage": usage, "position": 0, "source": "fallback"})

    return result
