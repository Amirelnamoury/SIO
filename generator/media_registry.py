"""Taxonomie extensible de la future bibliotheque d'images licenciees.

Le manifest reste volontairement vide tant qu'aucun asset avec licence et
credit verifies n'est livre. Les enregistrements de production vivent dans
site_media_library ; les tests peuvent l'alimenter avec des fixtures locales.
"""

LIBRARY_TAXONOMY = {
    "plomberie": ("salle_de_bain", "chauffage", "depannage", "canalisation"),
    "electricite": ("tableau", "eclairage", "renovation", "depannage"),
    "peinture": ("interieur", "facade", "finition"),
    "maconnerie": ("gros_oeuvre", "extension", "facade"),
    "menuiserie": ("interieur", "exterieur", "agencement"),
    "couverture": ("toiture", "zinguerie", "isolation"),
    "chauffage": ("chaudiere", "pompe_a_chaleur", "entretien"),
    "climatisation": ("installation", "entretien", "depannage"),
    "carrelage": ("sol", "salle_de_bain", "terrasse"),
    "paysage": ("jardin", "terrasse", "entretien"),
    "renovation": ("interieur", "exterieur", "chantier"),
}

LIBRARY_MANIFEST: tuple[dict, ...] = ()
