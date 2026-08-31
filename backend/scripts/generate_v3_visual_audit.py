"""Generate V3 visual-review HTML outside the repository.

Usage: python backend/scripts/generate_v3_visual_audit.py OUTPUT_DIR
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from generator.site_generator import generate_site  # noqa: E402
from tests.site_v3_fixtures import SITE_V3_FIXTURES  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Output directory required")
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for index, fixture in enumerate(SITE_V3_FIXTURES, 1):
        name = f"{index:02d}-{fixture['metier']}-{fixture['slug'].rsplit('-', 1)[-1]}"
        html = generate_site(fixture, "http://localhost:18000")
        (output / f"{name}.html").write_text(html, encoding="utf-8")
        profile = fixture["design_profile"]
        manifest.append({
            "name": name, "trade": fixture["metier"], "url": f"/{name}.html",
            "signature": profile["design_signature"], "direction": profile["art_direction"],
            "silhouette": profile["page_silhouette"], "hero": profile["hero_system"],
            "typography": profile["typography_system"], "image_treatment": profile["image_treatment"],
            "provider": "fallback_graphique", "hero_asset_id": None, "query": None,
        })
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(manifest)} V3 audit pages in {output}")


if __name__ == "__main__":
    main()
