"""Export human-readable, claim-free SiteDNA review cards."""

from __future__ import annotations

from collections import deque
from pathlib import Path

from ..generator import DesignGenome
from ..models import DesignInput, MediaInventory, SiteDNA


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "docs" / "design-encyclopedia" / "sample-dna"
SERVICES = {
    "plombier": ("Dépannage", "Salle de bains", "Chauffage"),
    "peintre": ("Peinture intérieure", "Façade", "Finitions"),
    "macon": ("Maçonnerie", "Extension", "Façade"),
    "electricien": ("Installation", "Mise aux normes", "Éclairage"),
    "menuisier": ("Agencement", "Mobilier", "Restauration"),
    "renovateur": ("Rénovation globale", "Coordination", "Aménagement"),
}
SPECS = {
    "plombier": ("emergency", "local_quote", "premium_residential", "technical_expertise", "trust_first", "balanced", "renovation_project", "commercial_b2b", "craft", "portfolio"),
    "peintre": ("premium_residential", "portfolio", "craft", "local_quote", "balanced"),
    "macon": ("technical_expertise", "renovation_project", "commercial_b2b", "trust_first", "portfolio"),
    "electricien": ("emergency", "technical_expertise", "commercial_b2b", "trust_first"),
    "menuisier": ("craft", "portfolio", "premium_residential"),
    "renovateur": ("renovation_project", "premium_residential", "balanced"),
}


def sample_input(trade: str, intent: str, index: int) -> DesignInput:
    project_photos = (0, 2, 5, 8)[index % 4]
    stock_photos = (0, 3, 5)[index % 3]
    facts = {"phone": "verified-capability-token", "email": "verified-capability-token", "process": ("verified-step-a", "verified-step-b")}
    if index % 3 == 0:
        facts["verified_facts"] = ("verified-evidence-token",)
    return DesignInput(
        trade=trade, seed=f"sample-{trade}-{index:02d}", city="verified-locality-token",
        business_intent=intent, services=SERVICES[trade], facts=facts,
        media=MediaInventory(
            artisan_photos=project_photos, project_photos=project_photos, stock_photos=stock_photos,
            landscape_photos=1 if project_photos or stock_photos else 0,
            portrait_photos=1 if project_photos >= 5 else 0, has_logo=index % 2 == 0,
        ),
    )


def card(trade: str, intent: str, index: int, dna: SiteDNA, why: list[str]) -> str:
    components = (
        dna.header_component, dna.hero_component, dna.services_component, dna.gallery_component,
        dna.about_component, dna.trust_component, dna.cta_component, dna.contact_component,
        dna.form_component, dna.footer_component,
    )
    return f"""# Sample DNA: {trade} {index:02d}

This is a structural review fixture. Capability tokens express available input types; they are not artisan claims and must never be rendered as copy.

- **Business intent:** `{intent}`
- **Archetype:** `{dna.site_archetype}`
- **Art direction:** `{dna.art_direction}`
- **Silhouette:** `{dna.page_silhouette}`
- **Palette:** `{dna.color_system}`
- **Typography:** `{dna.typography_system}`
- **Grid / spacing / geometry:** `{dna.grid_system}` / `{dna.spacing_system}` / `{dna.geometry_system}`
- **Components:** {', '.join(f'`{item}`' for item in components if item)}
- **Section order:** {' -> '.join(dna.section_order)}
- **Photo direction:** `{dna.photo_direction}`
- **Mobile / motion / spatial:** `{dna.mobile_personality}` / `{dna.motion_system}` / `{dna.spatial_system}`
- **Visual signature:** `{dna.design_signature}`

## Why this DNA
{chr(10).join(f'- {reason}' for reason in why)}

Human desktop/mobile rendering review is still required.
"""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    genome = DesignGenome(candidate_count=40)
    history: deque[SiteDNA] = deque(maxlen=32)
    records = []
    for trade, intents in SPECS.items():
        for index, intent in enumerate(intents, 1):
            source = sample_input(trade, intent, index)
            result = genome.generate_with_trace(source, tuple(history))
            history.append(result.dna)
            why = [reason for decision in result.trace.decisions for reason in decision.reasons[:1]]
            filename = f"{trade}-{index:02d}.md"
            (OUTPUT / filename).write_text(card(trade, intent, index, result.dna, why), encoding="utf-8")
            records.append((trade, index, intent, result.dna, filename))

    index_lines = ["# 30 sample SiteDNA cards", "", "Generated through `DesignGenome.generate_with_trace()` for human architecture review. These are knowledge contracts, not rendered sites or fictitious artisan profiles.", ""]
    for trade, index, intent, dna, filename in records:
        index_lines.append(f"- [{trade} {index:02d}](./{filename}) — `{intent}` / `{dna.site_archetype}` / `{dna.page_silhouette}`")
    (OUTPUT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    plumbers = [record for record in records if record[0] == "plombier"]
    lines = ["# Ten plumber DNA narratives", "", "The same trade is deliberately expressed through distinct business stories. Values below are structural choices, not rendered quality claims.", "", "| # | Intent | Archetype | Direction | Silhouette | Hero | Type | Palette | Sections |", "|---:|---|---|---|---|---|---|---|---|"]
    for _trade, index, intent, dna, filename in plumbers:
        lines.append(f"| [{index}](sample-dna/{filename}) | `{intent}` | `{dna.site_archetype}` | `{dna.art_direction}` | `{dna.page_silhouette}` | `{dna.hero_component}` | `{dna.typography_system}` | `{dna.color_system}` | {' → '.join(dna.section_order)} |")
    (OUTPUT.parent / "sample-plumbers.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Exported {len(records)} SiteDNA cards")


if __name__ == "__main__":
    main()
