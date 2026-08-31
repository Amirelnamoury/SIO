"""Nine explicit visual fixtures for V2 tests. Never imported by production code."""

from __future__ import annotations

from copy import deepcopy

from generator.design_registry import DESIGN_ENGINE_VERSION


def profile(family, header, hero, services, gallery, about, reviews, cta, footer, order, palette, font, radius, spacing, treatment, signature):
    return {
        "design_family": family,
        "header_variant": header,
        "hero_variant": hero,
        "services_variant": services,
        "gallery_variant": gallery,
        "about_variant": about,
        "reviews_variant": reviews,
        "cta_variant": cta,
        "footer_variant": footer,
        "section_order": order,
        "palette": palette,
        "font_pair": font,
        "radius_style": radius,
        "spacing_style": spacing,
        "image_treatment": treatment,
        "design_engine_version": DESIGN_ENGINE_VERSION,
        "design_signature": signature,
    }


def media(usage, name, position=0):
    return {
        "usage": usage,
        "position": position,
        "source": "artisan",
        "media_id": name,
        "content_url": f"/visual-assets/{name}.webp",
        "largeur": 1400,
        "hauteur": 930,
        "alt_text": f"Fixture visuelle {name}",
    }


TEST_SITE_V2_FIXTURES = [
    {
        "nom_entreprise": "FIXTURE TEST - Plomberie Horizon",
        "metier": "plombier", "slug": "fixture-plomberie-horizon", "ville": "Lyon", "code_postal": "69003",
        "telephone": "04 00 00 00 01", "email": "horizon@example.test", "tagline": "Installation et dépannage de plomberie",
        "services": ["Recherche de fuite", "Installation sanitaire", "Dépannage plomberie"],
        "avis": [{"note": 5, "commentaire": "Intervention conforme au devis.", "nom_auteur": "Client test A"}],
        "assurance_decennale_nom": "Assureur fixture A", "selected_media": [media("hero", "plomberie-1"), media("gallery", "plomberie-2")],
        "logo": {"content_url": "/visual-assets/logo-1.webp", "alt_text": "Logo fixture 1", "largeur": 420, "hauteur": 160},
        "design_profile": profile("impact", "classic", "fullscreen", "cards", "grid", "classic", "cards", "banner", "columns", ["hero", "trust", "services", "gallery", "reviews", "about", "cta"], "palette-1", "poppins-inter", "sharp", "compact", "overlay", "fixture-impact-fullscreen"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Atelier du Cuivre",
        "metier": "plombier", "slug": "fixture-atelier-cuivre", "ville": "Annecy", "code_postal": "74000",
        "telephone": "04 00 00 00 02", "email": "cuivre@example.test", "services": ["Rénovation de salle de bain", "Réseaux d’eau"],
        "stats": [{"valeur": "24 h", "label": "délai fixture déclaré"}], "avis": [], "selected_media": [],
        "design_profile": profile("technique", "compact", "compact", "list", "horizontal", "compact", "minimal", "floating", "simple", ["hero", "services", "stats", "service_area", "about", "contact"], "palette-2", "rajdhani-inter", "soft", "compact", "flat", "fixture-technique-compact"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Eau de Quartier",
        "metier": "plombier", "slug": "fixture-eau-quartier", "ville": "Nantes", "telephone": "02 00 00 00 03",
        "email": "quartier@example.test", "services": ["Entretien plomberie", "Remplacement de robinetterie", "Débouchage"], "avis": [],
        "selected_media": [media("hero", "plomberie-3")],
        "design_profile": profile("local", "centered", "editorial", "grid", "grid", "editorial", "minimal", "split", "centered", ["hero", "services", "service_area", "about", "cta"], "palette-3", "fredoka-inter", "pill", "comfortable", "duotone", "fixture-local-editorial"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Nuance & Matière",
        "metier": "peintre", "slug": "fixture-nuance-matiere", "ville": "Rennes", "telephone": "02 00 00 00 04", "email": "nuance@example.test",
        "adresse": "12 rue de la Fixture", "services": ["Peinture intérieure", "Enduits décoratifs", "Préparation des supports"],
        "avis": [{"note": 4, "commentaire": "Finitions soignées sur notre fixture.", "nom_auteur": "Client test B"}],
        "selected_media": [media("hero", "peinture-1"), media("about", "peinture-2"), media("gallery", "peinture-3")],
        "design_profile": profile("atelier", "minimal", "asymmetric", "alternating", "masonry", "split", "minimal", "minimal", "simple", ["hero", "about", "services", "gallery", "reviews", "contact"], "palette-2", "fredoka-inter", "rounded", "comfortable", "framed", "fixture-atelier-asymmetric"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Ligne Chromatique",
        "metier": "peintre", "slug": "fixture-ligne-chromatique", "ville": "Bordeaux", "telephone": "05 00 00 00 05", "email": "ligne@example.test",
        "services": ["Peinture de façade", "Mise en couleur", "Revêtements muraux"], "avis": [],
        "selected_media": [media("hero", "peinture-4"), media("gallery", "peinture-5"), media("gallery", "peinture-6", 1)],
        "logo": {"content_url": "/visual-assets/logo-2.webp", "alt_text": "Logo fixture 2", "largeur": 420, "hauteur": 160},
        "design_profile": profile("architecture", "classic", "split", "editorial", "featured", "editorial", "featured", "split", "columns", ["hero", "services", "gallery", "service_area", "about", "cta"], "palette-1", "archivo-inter", "sharp", "spacious", "flat", "fixture-architecture-split"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Studio Pigment",
        "metier": "peintre", "slug": "fixture-studio-pigment", "ville": "Paris", "code_postal": "75011", "telephone": "01 00 00 00 06", "email": "pigment@example.test",
        "services": ["Décoration murale", "Laques et boiseries"], "avis": [{"note": 5, "commentaire": "Le rendu correspond exactement au choix validé.", "nom_auteur": "Client test C"}],
        "selected_media": [media("hero", "peinture-7"), media("featured_project", "peinture-8")],
        "design_profile": profile("signature", "centered", "card", "editorial", "featured", "split", "featured", "split", "map", ["hero", "featured_project", "services", "reviews", "about", "contact"], "palette-3", "poppins-inter", "soft", "spacious", "overlay", "fixture-signature-card"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Maçonnerie Trait Pur",
        "metier": "macon", "slug": "fixture-macon-trait-pur", "ville": "Montpellier", "telephone": "04 00 00 00 07", "email": "trait@example.test",
        "services": ["Ouverture de mur", "Maçonnerie générale", "Dalle béton"], "avis": [], "selected_media": [],
        "design_profile": profile("architecture", "minimal", "editorial", "grid", "masonry", "compact", "minimal", "minimal", "columns", ["hero", "about", "services", "service_area", "contact"], "palette-2", "archivo-inter", "sharp", "spacious", "flat", "fixture-architecture-editorial"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Bâti Direct",
        "metier": "macon", "slug": "fixture-bati-direct", "ville": "Toulouse", "telephone": "05 00 00 00 08", "email": "bati@example.test",
        "services": ["Extension de maison", "Fondations", "Mur de clôture", "Rénovation structurelle"],
        "avis": [{"note": 5, "commentaire": "Planning et réalisation conformes.", "nom_auteur": "Client test D"}],
        "selected_media": [media("hero", "maconnerie-1"), media("gallery", "maconnerie-2")],
        "design_profile": profile("impact", "compact", "split", "cards", "grid", "classic", "cards", "banner", "simple", ["hero", "services", "reviews", "gallery", "cta"], "palette-1", "rajdhani-inter", "rounded", "compact", "duotone", "fixture-impact-split"),
    },
    {
        "nom_entreprise": "FIXTURE TEST - Structure Carrée",
        "metier": "macon", "slug": "fixture-structure-carree", "ville": "Dijon", "telephone": "03 00 00 00 09", "email": "structure@example.test",
        "services": ["Rénovation de maçonnerie", "Création d’ouvertures"], "avis": [],
        "selected_media": [media("hero", "maconnerie-3"), media("gallery", "maconnerie-4"), media("gallery", "maconnerie-5", 1)],
        "logo": {"content_url": "/visual-assets/logo-3.webp", "alt_text": "Logo fixture 3", "largeur": 420, "hauteur": 160},
        "design_profile": profile("technique", "classic", "asymmetric", "list", "horizontal", "classic", "minimal", "floating", "columns", ["hero", "services", "gallery", "service_area", "about", "contact"], "palette-3", "rajdhani-inter", "soft", "comfortable", "framed", "fixture-technique-asymmetric"),
    },
]


def visual_fixtures():
    return deepcopy(TEST_SITE_V2_FIXTURES)
