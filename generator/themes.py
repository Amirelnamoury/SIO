"""Identite visuelle des sites generes.

Le rendu de chaque site combine deux choses :
1. Le METIER de l'artisan (plombier, electricien, macon, peintre, general)
   qui determine la famille de couleurs, la police, les textes et icones
   par defaut : un plombier reste toujours "bleu/eau", un electricien
   toujours "noir/jaune energie", etc. C'est ce qui rend chaque site
   credible pour son metier.
2. Une VARIANTE choisie automatiquement (couleur + motif visuel du hero),
   determinee de facon stable a partir du slug/SIRET de l'artisan (deux
   artisans differents obtiennent presque toujours une combinaison
   differente, un meme artisan garde toujours la meme identite si on
   regenere son site). On peut aussi forcer une variante a la main avec
   artisan["variante_couleur"] (index) et artisan["variante_motif"] (cle).

Avec 3 palettes x 2 motifs par metier, ca fait 6 combinaisons visuelles
par metier (30 au total) : largement de quoi eviter que deux clients d'une
meme ville aient exactement le meme rendu, sans pour autant construire un
moteur de design generatif disproportionne pour un produit vendu one-shot.
"""

import hashlib

# ---------- Contenu par metier (texte, police, prestations par defaut) ----------

THEMES = {
    "plombier": {
        "label": "Plombier",
        "font": "'Poppins', sans-serif",
        "tagline": "Votre plombier de confiance, intervention rapide",
        "services": [
            "Depannage fuite d'eau",
            "Installation sanitaire",
            "Chauffe-eau & chaudiere",
            "Debouchage de canalisation",
            "Renovation de salle de bain",
        ],
    },
    "electricien": {
        "label": "Electricien",
        "font": "'Rajdhani', sans-serif",
        "tagline": "Electricien certifie, intervention rapide et aux normes",
        "services": [
            "Mise aux normes electriques",
            "Installation de tableau electrique",
            "Depannage electrique urgent",
            "Domotique & eclairage connecte",
            "Prises, interrupteurs & eclairage",
        ],
    },
    "macon": {
        "label": "Macon",
        "font": "'Archivo', sans-serif",
        "tagline": "Maconnerie et gros oeuvre : du solide, du durable",
        "services": [
            "Fondations & gros oeuvre",
            "Extension de maison",
            "Renovation de facade",
            "Dalle beton & terrasse",
            "Ouverture de mur porteur",
        ],
    },
    "peintre": {
        "label": "Peintre",
        "font": "'Fredoka', sans-serif",
        "tagline": "Peinture interieure & exterieure, un rendu impeccable",
        "services": [
            "Peinture interieure",
            "Peinture de facade exterieure",
            "Pose de papier peint",
            "Enduits decoratifs",
            "Ravalement de facade",
        ],
    },
    "general": {
        "label": "Artisan du BTP",
        "font": "'Inter', sans-serif",
        "tagline": "Artisan du BTP : qualite, serieux et devis gratuit",
        "services": [
            "Travaux de renovation",
            "Petits travaux du quotidien",
            "Entretien du batiment",
            "Devis gratuit sous 48h",
        ],
    },
}

GOOGLE_FONTS = {
    "'Poppins', sans-serif": "Poppins:wght@400;600;700",
    "'Rajdhani', sans-serif": "Rajdhani:wght@500;600;700",
    "'Archivo', sans-serif": "Archivo:wght@400;600;800",
    "'Fredoka', sans-serif": "Fredoka:wght@400;500;600",
    "'Inter', sans-serif": "Inter:wght@400;600;700",
}

# ---------- Palettes (3 variantes par metier, memes familles de couleurs) ----------

PALETTE_VARIANTS = {
    "plombier": [
        {"nom": "Ocean", "primary": "#0077b6", "primary_dark": "#023e8a", "secondary": "#90e0ef",
         "accent": "#00b4d8", "background": "#f0faff", "text": "#03045e"},
        {"nom": "Turquoise", "primary": "#0f8b8d", "primary_dark": "#0b5e60", "secondary": "#a8e6cf",
         "accent": "#1abc9c", "background": "#f1fbfa", "text": "#0b3d3d"},
        {"nom": "Steel", "primary": "#2b6cb0", "primary_dark": "#1a365d", "secondary": "#bee3f8",
         "accent": "#4299e1", "background": "#f4f9fd", "text": "#1a202c"},
    ],
    "electricien": [
        {"nom": "Classic", "primary": "#050505", "primary_dark": "#000000", "secondary": "#ffd60a",
         "accent": "#ff9500", "background": "#ffffff", "text": "#111111"},
        {"nom": "Charcoal Amber", "primary": "#1c1c1e", "primary_dark": "#000000", "secondary": "#ffb703",
         "accent": "#fb8500", "background": "#fafafa", "text": "#1c1c1e"},
        {"nom": "Graphite Lime", "primary": "#14161a", "primary_dark": "#000000", "secondary": "#d4f512",
         "accent": "#9ae600", "background": "#fbfff2", "text": "#14161a"},
    ],
    "macon": [
        {"nom": "Terracotta", "primary": "#c1440e", "primary_dark": "#8a300a", "secondary": "#8d8d8d",
         "accent": "#e0a458", "background": "#f5f1ea", "text": "#2b2b2b"},
        {"nom": "Taupe", "primary": "#a9744f", "primary_dark": "#6f4b30", "secondary": "#d8cdbf",
         "accent": "#c98a4b", "background": "#faf6f0", "text": "#3a2e22"},
        {"nom": "Concrete Copper", "primary": "#495057", "primary_dark": "#212529", "secondary": "#ced4da",
         "accent": "#d68a4c", "background": "#f6f6f7", "text": "#212529"},
    ],
    "peintre": [
        {"nom": "Coastal", "primary": "#457b9d", "primary_dark": "#1d3557", "secondary": "#f1c40f",
         "accent": "#e76f51", "background": "#fdfdfd", "text": "#1d1d1d",
         "palette_colors": ["#e63946", "#f1c40f", "#2a9d8f", "#457b9d", "#e76f51"]},
        {"nom": "Sunset", "primary": "#e76f51", "primary_dark": "#9c3d26", "secondary": "#f4a261",
         "accent": "#2a9d8f", "background": "#fffaf5", "text": "#2b2118",
         "palette_colors": ["#e76f51", "#f4a261", "#e9c46a", "#2a9d8f", "#264653"]},
        {"nom": "Violet Pastel", "primary": "#7b2cbf", "primary_dark": "#4a1a72", "secondary": "#f8c8dc",
         "accent": "#ff9770", "background": "#fdf9ff", "text": "#2d1a3a",
         "palette_colors": ["#7b2cbf", "#ff9770", "#ffd670", "#70d6ff", "#e9ff70"]},
    ],
    "general": [
        {"nom": "Navy", "primary": "#1d3557", "primary_dark": "#14263e", "secondary": "#457b9d",
         "accent": "#e63946", "background": "#f8f9fa", "text": "#1d1d1d"},
        {"nom": "Slate Teal", "primary": "#34495e", "primary_dark": "#212f3c", "secondary": "#5dade2",
         "accent": "#16a085", "background": "#f7f9fa", "text": "#212f3c"},
        {"nom": "Forest Gold", "primary": "#2d3a2e", "primary_dark": "#1a231b", "secondary": "#c8a951",
         "accent": "#6b8e4e", "background": "#f8f7f2", "text": "#22281f"},
    ],
}

# ---------- Motifs decoratifs du hero (2 par metier, generiques en CSS) ----------

HERO_MOTIFS = {
    "plombier": ["wave-gradient", "gradient-mesh"],
    "electricien": ["diagonal-stripes", "dot-grid"],
    "macon": ["brick-rows", "dot-grid"],
    "peintre": ["gradient-mesh", "wave-gradient"],
    "general": ["wave-gradient", "gradient-mesh"],
}

# ---------- Icones (SVG inline, aucune dependance externe) ----------
# Icones "de marque" (metier) : forme pleine (fill), utilisees dans le logo et le hero.
TRADE_ICON_PATHS = {
    "plombier": '<path d="M12 3c3 4 5 6.8 5 9.5A5 5 0 0112 18a5 5 0 01-5-5.5C7 9.8 9 7 12 3z"/>',
    "electricien": '<polygon points="13,2 4,14 11,14 10,22 20,10 13,10"/>',
    "macon": '<rect x="3" y="6" width="8" height="5"/><rect x="13" y="6" width="8" height="5"/>'
             '<rect x="8" y="13" width="8" height="5"/>',
    "peintre": '<rect x="4" y="4" width="14" height="6" rx="1.5"/><rect x="9" y="10" width="4" height="7"/>'
               '<rect x="8" y="17" width="6" height="4" rx="1"/>',
    "general": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1'
               'M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" stroke="currentColor" '
               'stroke-width="1.8" fill="none" stroke-linecap="round"/>',
}

# Icones "d'interface" : style trait (stroke), utilisees dans le contenu (cartes, listes...).
UI_ICON_PATHS = {
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9"/>',
    "shield": '<path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6l7-3z"/>',
    "document": '<path d="M7 2h7l5 5v15H7z"/><path d="M14 2v5h5"/><path d="M9.5 12h5M9.5 15.5h5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "phone": '<path d="M6.5 3h3l1.8 4.5-2.3 1.8a13 13 0 006.7 6.7l1.8-2.3L21.5 15v3a2 2 0 01-2 2'
             'C10.6 20 4 13.4 4 5.5a2 2 0 012-2.5z"/>',
}


def _seed(artisan: dict) -> str:
    return str(artisan.get("slug") or artisan.get("siret") or artisan.get("nom_entreprise") or "artisan")


def _stable_index(seed: str, salt: str, modulo: int) -> int:
    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).hexdigest()
    return int(digest, 16) % modulo


def get_theme(metier: str) -> dict:
    return THEMES.get(metier, THEMES["general"])


def get_palette(metier: str, artisan: dict) -> dict:
    """Choisit une des 3 palettes du metier. Stable pour un artisan donne
    (meme slug -> toujours la meme palette), sauf si artisan['variante_couleur']
    force un index explicitement."""
    variants = PALETTE_VARIANTS.get(metier, PALETTE_VARIANTS["general"])

    override = artisan.get("variante_couleur")
    if isinstance(override, int) and 0 <= override < len(variants):
        return variants[override]

    index = _stable_index(_seed(artisan), "couleur", len(variants))
    return variants[index]


def get_hero_motif(metier: str, artisan: dict) -> str:
    """Choisit un des motifs decoratifs du hero. Stable pour un artisan
    donne, sauf si artisan['variante_motif'] force une valeur explicitement."""
    motifs = HERO_MOTIFS.get(metier, HERO_MOTIFS["general"])

    override = artisan.get("variante_motif")
    if override in motifs:
        return override

    index = _stable_index(_seed(artisan), "motif", len(motifs))
    return motifs[index]


def trade_icon_svg(metier: str, size: int = 32, extra_class: str = "") -> str:
    path = TRADE_ICON_PATHS.get(metier, TRADE_ICON_PATHS["general"])
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="currentColor" '
        f'class="icon {extra_class}">{path}</svg>'
    )


def ui_icon_svg(name: str, size: int = 22, extra_class: str = "") -> str:
    path = UI_ICON_PATHS.get(name, UI_ICON_PATHS["check"])
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        f'class="icon {extra_class}">{path}</svg>'
    )
