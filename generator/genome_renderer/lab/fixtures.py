"""Synthetic, lab-only inputs used to exercise the Genome renderer."""

from __future__ import annotations


ASSET_IDS = (
    "10473013", "11377606", "13724794", "14953886", "15409476", "1599",
    "18541264", "19666087", "19916724", "19916732", "240312", "248850",
    "27259668", "27629444", "29226620", "33203990", "35189677", "35189678",
    "35868666", "36077586", "36077593", "36077602", "36121721", "36585045",
)


def _media(first: int) -> list[dict[str, object]]:
    values = []
    for offset, role in enumerate(("hero", "gallery")):
        asset_id = ASSET_IDS[first + offset]
        values.append({
            "id": f"pexels-{asset_id}",
            "url": f"../../assets/{asset_id}.webp",
            "role": role,
            "source": "pexels",
            "provider": "pexels",
            "provider_asset_id": asset_id,
            "credit": "Photo Pexels",
            "source_url": f"https://www.pexels.com/photo/{asset_id}/",
            "alt": "Ambiance et matière du métier",
        })
    return values


_CASES = (
    ("site-01", "plombier", "local_conversion", "Plomberie Rive Gauche", "Lyon", ("Dépannage plomberie", "Installation sanitaire", "Rénovation de salle de bain"), "Une approche directe pour vos projets de plomberie."),
    ("site-02", "plombier", "premium_residential_bathroom", "Maison Eau", "Annecy", ("Salle de bain", "Robinetterie", "Installation sanitaire"), "Des espaces d’eau pensés avec soin."),
    ("site-03", "plombier", "technical_expertise", "Flux Technique", "Grenoble", ("Réseaux sanitaires", "Recherche de fuite", "Mise en conformité"), "La plomberie abordée avec précision."),
    ("site-04", "peintre", "editorial_residential", "Nuance Habitat", "Bordeaux", ("Peinture intérieure", "Préparation des supports", "Finitions murales"), "Couleurs, lumière et équilibre intérieur."),
    ("site-05", "peintre", "warm_craft", "Atelier des Teintes", "Nantes", ("Peinture décorative", "Enduits", "Boiseries"), "Le geste et la matière au service des intérieurs."),
    ("site-06", "macon", "architectural_contracting", "Trame Maçonnerie", "Montpellier", ("Maçonnerie générale", "Extensions", "Ouvertures"), "Construire des volumes lisibles et durables."),
    ("site-07", "macon", "project_led", "Ligne Porteuse", "Dijon", ("Rénovation structurelle", "Murs et dalles", "Aménagement extérieur"), "Chaque intervention part du bâti existant."),
    ("site-08", "electricien", "technical_systems", "Circuit Atelier", "Toulouse", ("Tableaux électriques", "Rénovation électrique", "Éclairage"), "Des installations structurées pour les usages réels."),
    ("site-09", "electricien", "local_trust", "Électricité des Dômes", "Clermont-Ferrand", ("Installation électrique", "Diagnostic", "Éclairage intérieur"), "Un interlocuteur local pour vos installations."),
    ("site-10", "menuisier", "material_craft", "Bois de Ligne", "Rennes", ("Agencement intérieur", "Mobilier sur mesure", "Menuiseries bois"), "Le bois, les proportions et l’usage."),
    ("site-11", "renovateur", "premium_residential", "Volume Intérieur", "Aix-en-Provence", ("Rénovation intérieure", "Redistribution des espaces", "Finitions"), "Transformer l’habitat avec une vision d’ensemble."),
    ("site-12", "renovateur", "cinematic_project_led", "Séquence Rénovation", "Paris", ("Rénovation complète", "Coordination de chantier", "Aménagement intérieur"), "Du lieu existant au nouvel espace."),
)


LAB_FIXTURES = tuple(
    {
        "fixture_id": fixture_id,
        "synthetic_fixture": True,
        "nom_entreprise": name,
        "metier": trade,
        "business_intent": intent,
        "seed": f"genome-lab-0.1:{fixture_id}:{intent}",
        "slug": f"lab-{fixture_id}",
        "ville": city,
        "code_postal": "",
        "telephone": "",
        "email": "",
        "adresse": "",
        "siret": "",
        "tagline": tagline,
        "about": tagline,
        "services": list(services),
        "facts": {"process": ("Échange sur le besoin", "Préparation du projet", "Réalisation")},
        "selected_media": _media(index * 2),
    }
    for index, (fixture_id, trade, intent, name, city, services, tagline) in enumerate(_CASES)
)


assert len(LAB_FIXTURES) == 12
assert all(item["synthetic_fixture"] is True for item in LAB_FIXTURES)
