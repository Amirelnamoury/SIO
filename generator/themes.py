"""Identite visuelle par metier : chaque metier a sa propre palette de
couleurs, sa police, son icone et ses textes par defaut. C'est ce qui evite
que tous les sites generes se ressemblent."""

THEMES = {
    "plombier": {
        "label": "Plombier",
        "primary": "#0077b6",
        "primary_dark": "#023e8a",
        "secondary": "#90e0ef",
        "accent": "#00b4d8",
        "background": "#f0faff",
        "text": "#03045e",
        "font": "'Poppins', sans-serif",
        "icon": "\U0001F6BF",  # 🚿
        "tagline": "Votre plombier de confiance, intervention rapide",
        "hero_style": "wave",
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
        "primary": "#050505",
        "primary_dark": "#000000",
        "secondary": "#ffd60a",
        "accent": "#ff9500",
        "background": "#ffffff",
        "text": "#111111",
        "font": "'Rajdhani', sans-serif",
        "icon": "⚡",  # ⚡
        "tagline": "Electricien certifie, intervention rapide et aux normes",
        "hero_style": "bolt",
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
        "primary": "#c1440e",
        "primary_dark": "#8a300a",
        "secondary": "#8d8d8d",
        "accent": "#e0a458",
        "background": "#f5f1ea",
        "text": "#2b2b2b",
        "font": "'Archivo', sans-serif",
        "icon": "\U0001F9F1",  # 🧱
        "tagline": "Maconnerie et gros oeuvre : du solide, du durable",
        "hero_style": "brick",
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
        "primary": "#457b9d",
        "primary_dark": "#1d3557",
        "secondary": "#f1c40f",
        "accent": "#e76f51",
        "background": "#fdfdfd",
        "text": "#1d1d1d",
        "font": "'Fredoka', sans-serif",
        "icon": "\U0001F3A8",  # 🎨
        "tagline": "Peinture interieure & exterieure, un rendu impeccable",
        "hero_style": "palette",
        "palette_colors": ["#e63946", "#f1c40f", "#2a9d8f", "#457b9d", "#e76f51"],
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
        "primary": "#1d3557",
        "primary_dark": "#14263e",
        "secondary": "#457b9d",
        "accent": "#e63946",
        "background": "#f8f9fa",
        "text": "#1d1d1d",
        "font": "'Inter', sans-serif",
        "icon": "\U0001F6E0️",  # 🛠️
        "tagline": "Artisan du BTP : qualite, serieux et devis gratuit",
        "hero_style": "plain",
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


def get_theme(metier: str) -> dict:
    return THEMES.get(metier, THEMES["general"])
