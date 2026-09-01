"""Curated V1.1 deep-reference scope for offline encyclopedia authoring.

The Gold observations come from the manual desktop review recorded in
``docs/design-bible-v3.md``. Additional references were selected for their
transferable design-system patterns and HTML-checked separately; they are not
promoted to visually inspected Gold Standards by this module.
"""

from __future__ import annotations


ADDITIONAL_DEEP_REFERENCES = (
    ("Vitra", "https://www.vitra.com/en-us/product", "furniture", "catalogue taxonomy and object hierarchy"),
    ("Muuto", "https://www.muuto.com/products/", "furniture", "calm product system and category navigation"),
    ("FRAMA", "https://framacph.com/", "furniture", "material-led editorial commerce"),
    ("USM", "https://www.usm.com/", "furniture", "modular product grammar"),
    ("Flos", "https://flos.com/en/us/", "lighting", "light-led narrative and category rhythm"),
    ("Artemide", "https://www.artemide.com/", "lighting", "technical product storytelling"),
    ("Gaggenau", "https://www.gaggenau.com/", "appliances", "premium technical restraint"),
    ("Bang & Olufsen", "https://www.bang-olufsen.com/", "technology", "object photography and controlled conversion"),
    ("Aman", "https://www.aman.com/hotels-and-resorts", "hospitality", "immersive place-led arrival"),
    ("Six Senses", "https://www.sixsenses.com/", "hospitality", "location narrative and booking clarity"),
    ("Ace Hotel", "https://acehotel.com/", "hospitality", "local identity across a multi-property system"),
    ("Habitas", "https://www.ourhabitas.com/", "hospitality", "chapter-led experiential narrative"),
    ("Pentagram", "https://www.pentagram.com/", "design_studio", "dense but navigable portfolio taxonomy"),
    ("COLLINS", "https://www.wearecollins.com/", "design_studio", "case-study pacing and typographic identity"),
    ("Koto", "https://koto.studio/", "design_studio", "project framing and bold editorial hierarchy"),
    ("Build in Amsterdam", "https://www.buildinamsterdam.com/", "design_studio", "commerce case-study sequencing"),
    ("Locomotive", "https://locomotive.ca/", "design_studio", "motion used as narrative transition"),
    ("Aesop", "https://www.aesop.com/", "ecommerce", "material restraint and readable commerce"),
    ("Fantastic Frank", "https://www.fantasticfrank.com/", "real_estate", "image-led property catalogue"),
    ("Airbnb Design", "https://airbnb.design/", "editorial", "article hierarchy and design-system communication"),
)


SECTOR_REVIEW_GUIDANCE = {
    "architecture": {
        "business_clarity": "Project discovery dominates; direct artisan conversion must remain clearer.",
        "good_fit": "menuisier, macon, renovateur with verified project photography",
        "poor_fit": "emergency plumber or electrician without strong imagery",
        "caution": "Do not import portfolio scale, awards, or architectural claims.",
    },
    "construction": {
        "business_clarity": "Capability and proof can sit close to the opening action.",
        "good_fit": "macon, renovateur, technical electrician",
        "poor_fit": "quiet craft portfolios with little technical evidence",
        "caution": "Every certification, guarantee and statistic still requires explicit evidence.",
    },
    "ecommerce": {
        "business_clarity": "Strong category and action hierarchy, but retail mechanics are not the artisan journey.",
        "good_fit": "menuisier or peintre with material-rich work",
        "poor_fit": "urgent local service journeys",
        "caution": "Do not turn services into products or copy purchase patterns.",
    },
    "furniture": {
        "business_clarity": "Material and object hierarchy can clarify craft without retail imitation.",
        "good_fit": "menuisier, peintre, premium renovateur",
        "poor_fit": "emergency and highly technical service flows",
        "caution": "Stock objects must not be presented as artisan work.",
    },
    "real_estate": {
        "business_clarity": "A clear image sequence supports discovery before contact.",
        "good_fit": "renovateur and premium residential trades",
        "poor_fit": "low-media emergency services",
        "caution": "Do not imply properties, locations, or projects absent from source data.",
    },
    "interactive": {
        "business_clarity": "Experience-led openings need an accessible content and action fallback.",
        "good_fit": "select premium portfolios with strong media",
        "poor_fit": "urgent, accessibility-sensitive local conversion",
        "caution": "No blocking preload, mandatory sound, or navigation dependent on animation.",
    },
}


def sector_guidance(sector: str) -> dict[str, str]:
    key = sector.split("/")[0].strip().lower()
    return SECTOR_REVIEW_GUIDANCE.get(key, {
        "business_clarity": "Business clarity must be re-established for an artisan service journey.",
        "good_fit": "trade fit requires human review",
        "poor_fit": "trade mismatch not established",
        "caution": "Transfer structure only; never copy identity or unsupported claims.",
    })
