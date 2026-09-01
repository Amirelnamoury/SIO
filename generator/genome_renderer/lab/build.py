"""Generate the portable Design Genome renderer visual laboratory."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from generator.design_genome.generator import DesignGenome
from generator.design_genome.models import SiteDNA

from ..adapter import design_input_from_payload, render_payload_with_genome
from .fixtures import LAB_FIXTURES


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "genome-renderer-lab"
MEDIA_SOURCE = REPO_ROOT / "backend" / "uploads" / "site-media-library" / "pexels"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _component_manifest(dna: SiteDNA) -> dict[str, str | None]:
    return {
        "header": dna.header_component,
        "hero": dna.hero_component,
        "services": dna.services_component,
        "gallery": dna.gallery_component,
        "about": dna.about_component,
        "trust": dna.trust_component,
        "cta": dna.cta_component,
        "contact": dna.contact_component,
        "footer": dna.footer_component,
        "form": dna.form_component,
    }


def _media_summary(fixture: dict[str, Any]) -> dict[str, Any]:
    media = fixture["selected_media"]
    return {
        "count": len(media),
        "sources": dict(Counter(item["source"] for item in media)),
        "roles": dict(Counter(item["role"] for item in media)),
        "synthetic_fixture": True,
        "claim_policy": "stock media is rendered only as ambiance or material",
    }


def _review(fixture: dict[str, Any], dna: SiteDNA) -> dict[str, Any]:
    return {
        "fixture_id": fixture["fixture_id"],
        "design_signature": dna.design_signature,
        "aesthetic_status": "NOT_REVIEWED",
        "desktop_status": "NOT_REVIEWED",
        "mobile_status": "NOT_REVIEWED",
        "dimensions": (
            "identity", "composition", "typography", "color", "media",
            "hierarchy", "conversion", "mobile", "originality", "coherence",
        ),
        "notes": "",
    }


def _lab_index(items: list[dict[str, Any]]) -> str:
    rows = []
    for item in items:
        rows.append(f'''<tr>
<td><strong>{html.escape(item["fixture_id"])}</strong><span>{html.escape(item["name"])}</span></td>
<td>{html.escape(item["trade"])}</td><td>{html.escape(item["business_intent"])}</td>
<td>{html.escape(item["hero"] or "omitted")}</td><td>{html.escape(item["page_silhouette"])}</td>
<td>{html.escape(item["palette"])}</td><td>{html.escape(item["typography"])}</td>
<td class="links"><a href="sites/{item['fixture_id']}/">Open site</a><a href="sites/{item['fixture_id']}/dna.json">DNA</a><a href="sites/{item['fixture_id']}/review.json">Review</a></td>
</tr>''')
    return '''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Design Genome Renderer — Visual Lab</title><meta name="robots" content="noindex,nofollow"><style>
*{box-sizing:border-box}body{margin:0;background:#f4f4f1;color:#181816;font:14px/1.5 Arial,sans-serif;letter-spacing:0}header{padding:34px clamp(16px,4vw,56px);border-bottom:1px solid #aaa}h1{margin:0;font-size:32px;letter-spacing:0}p{max-width:72ch;margin:8px 0 0;color:#595955}.status{display:inline-block;margin-top:18px;padding:5px 8px;border:1px solid #181816;font-size:11px;text-transform:uppercase}main{overflow:auto;padding:24px clamp(16px,4vw,56px) 60px}table{width:100%;min-width:1180px;border-collapse:collapse;background:#fff}th,td{text-align:left;vertical-align:top;padding:14px 12px;border-bottom:1px solid #d5d5d0}th{font-size:11px;text-transform:uppercase;background:#e8e8e3;position:sticky;top:0}td strong,td span{display:block}.links{white-space:nowrap}.links a{display:inline-block;margin-right:12px;color:#064f9c;text-underline-offset:3px}:focus-visible{outline:3px solid #005fcc;outline-offset:3px}
</style></head><body><header><h1>Design Genome Renderer V0.1</h1><p>Comparaison de 12 fixtures synthétiques. Ce laboratoire sert à la revue humaine; aucun statut esthétique n’est calculé automatiquement.</p><span class="status">Not reviewed</span></header><main><table><thead><tr><th>Fixture</th><th>Métier</th><th>Intent</th><th>Hero</th><th>Silhouette</th><th>Palette</th><th>Typographie</th><th>Actions</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></main></body></html>'''


def build_visual_lab(output: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    (output / "sites").mkdir(exist_ok=True)
    (output / "review" / "desktop").mkdir(parents=True, exist_ok=True)
    (output / "review" / "mobile").mkdir(parents=True, exist_ok=True)
    (output / "review" / "dna").mkdir(parents=True, exist_ok=True)

    history: list[SiteDNA] = []
    manifest: list[dict[str, Any]] = []
    review_manifest: list[dict[str, Any]] = []
    for fixture in LAB_FIXTURES:
        for media in fixture["selected_media"]:
            source = MEDIA_SOURCE / f'{media["provider_asset_id"]}.webp'
            if not source.is_file():
                raise FileNotFoundError(f"Missing lab media: {source}")
            shutil.copy2(source, output / "assets" / source.name)

        design_input = design_input_from_payload(fixture, seed=fixture["seed"])
        dna = DesignGenome().generate(design_input, tuple(history))
        rendered, _ = render_payload_with_genome(fixture, "", site_dna=dna, lab_mode=True)
        history.append(dna)

        site_dir = output / "sites" / fixture["fixture_id"]
        site_dir.mkdir(exist_ok=True)
        site_dir.joinpath("index.html").write_text(rendered, encoding="utf-8")
        _write_json(site_dir / "dna.json", dna.to_dict())
        review = _review(fixture, dna)
        _write_json(site_dir / "review.json", review)
        _write_json(output / "review" / "dna" / f'{fixture["fixture_id"]}.json', dna.to_dict())
        review_manifest.append(review)

        item = {
            "fixture_id": fixture["fixture_id"],
            "name": fixture["nom_entreprise"],
            "trade": fixture["metier"],
            "business_intent": fixture["business_intent"],
            "seed": fixture["seed"],
            "synthetic_fixture": True,
            "design_signature": dna.design_signature,
            "composition_signature": dna.composition_signature,
            "site_archetype": dna.site_archetype,
            "art_direction": dna.art_direction,
            "page_silhouette": dna.page_silhouette,
            **_component_manifest(dna),
            "palette": dna.color_system,
            "typography": dna.typography_system,
            "grid": dna.grid_system,
            "spacing": dna.spacing_system,
            "geometry": dna.geometry_system,
            "media_provenance": _media_summary(fixture),
            "aesthetic_status": "NOT_REVIEWED",
        }
        manifest.append(item)

    _write_json(output / "manifest.json", {
        "renderer": "design-genome-renderer-0.1",
        "fixture_policy": "synthetic fixtures restricted to the visual lab",
        "aesthetic_status": "NOT_REVIEWED",
        "fixtures": manifest,
    })
    desktop_captured = all(
        (output / "review" / "desktop" / f'{fixture["fixture_id"]}.jpg').is_file()
        for fixture in LAB_FIXTURES
    )
    mobile_captured = all(
        (output / "review" / "mobile" / f'{fixture["fixture_id"]}.jpg').is_file()
        for fixture in LAB_FIXTURES
    )
    _write_json(output / "review" / "manifest.json", {
        "aesthetic_status": "NOT_REVIEWED",
        "figma_upload": False,
        "desktop_screenshots": "CAPTURED" if desktop_captured else "SCREENSHOTS_UNAVAILABLE",
        "mobile_screenshots": "CAPTURED" if mobile_captured else "SCREENSHOTS_UNAVAILABLE",
        "sites": review_manifest,
    })
    output.joinpath("index.html").write_text(_lab_index(manifest), encoding="utf-8")
    output.joinpath("vercel.json").write_text('{"cleanUrls":true,"trailingSlash":true}\n', encoding="utf-8")
    output.joinpath("README.md").write_text(
        "# Design Genome Renderer Visual Lab\n\n"
        "Static, portable review package containing 12 explicitly synthetic fixtures. "
        "Run `python -m generator.genome_renderer.lab.build` from the repository root to rebuild it.\n\n"
        "All aesthetic statuses start at `NOT_REVIEWED`. The forms are disabled, no provider is "
        "called at runtime, and this directory can be selected as an isolated Vercel project root.\n",
        encoding="utf-8",
    )
    output.joinpath("VERCEL_PREVIEW_NOT_DEPLOYED_BY_CODEX").write_text(
        "Portable static lab prepared; no preview URL was created.\n", encoding="utf-8"
    )
    screenshot_marker = output / "review" / "SCREENSHOTS_UNAVAILABLE"
    if desktop_captured and mobile_captured:
        screenshot_marker.unlink(missing_ok=True)
    else:
        screenshot_marker.write_text(
            "Generated only when a real browser capture succeeds.\n", encoding="utf-8"
        )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Design Genome Renderer visual lab")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generated = build_visual_lab(args.output)
    print(f"Generated {len(generated)} lab sites in {args.output}")
