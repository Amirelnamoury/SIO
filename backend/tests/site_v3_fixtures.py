"""Eighteen deterministic acceptance fixtures for the V3 visual protocol."""

from generator.v3.selector import select_design_grammar

TRADES = ("plombier", "peintre", "macon", "menuisier", "electricien", "renovateur")


def build_fixtures() -> list[dict]:
    history = []
    fixtures = []
    for trade in TRADES:
        trade_history = []
        for index in range(3):
            slug = f"v3-{trade}-{index + 1}"
            profile, _ = select_design_grammar({"slug": slug, "metier": trade}, trade_history)
            trade_history.append(profile)
            history.append(profile)
            fixtures.append({
                "nom_entreprise": f"Atelier {trade.title()} {index + 1}", "metier": trade,
                "slug": slug, "ville": "Lyon", "code_postal": "69002",
                "telephone": "04 00 00 00 00", "email": f"contact-{index}@example.test",
                "tagline": "", "services": [], "stats": [], "avis": [],
                "process_steps": [], "reasons": [], "selected_media": [], "design_profile": profile,
            })
    return fixtures


SITE_V3_FIXTURES = build_fixtures()
