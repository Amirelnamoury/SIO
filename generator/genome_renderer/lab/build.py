"""Generate the portable Design Genome renderer visual laboratory (V0.2).

V0.1's screenshots and rendered sites are treated as a frozen historical
baseline once preserved (see ``artifacts/genome-renderer-lab/sites-v0.1/``
and ``review/v0.1/``) -- this script never writes into those paths again.
Everything it produces from here on is the *current* engine's output, filed
under ``sites/`` (kept, as before, as the live working copy) and
``review/v0.2/`` (desktop/mobile screenshots once captured, DNA, RenderPlan
and VisualCompletenessReport summaries for the human/Figma review package).
"""

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
from ..context import RenderContext
from ..render_plan import build_render_plan
from ..visual_completeness import assess
from .fixtures import LAB_FIXTURES


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "genome-renderer-lab"
MEDIA_SOURCE = REPO_ROOT / "backend" / "uploads" / "site-media-library" / "pexels"
RENDERER_VERSION = "design-genome-renderer-0.2"


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
        vc = item["visual_completeness"]
        low_dims = ", ".join(k for k, v in vc.items() if isinstance(v, dict) and v.get("score", 1) < 0.85) or "—"
        recomposed = (
            f'{html.escape(item["initial_hero_component"])} → {html.escape(item["resolved_hero_component"])}'
            if item["initial_hero_component"] != item["resolved_hero_component"] else "—"
        )
        rows.append(f'''<tr>
<td><strong>{html.escape(item["fixture_id"])}</strong><span>{html.escape(item["name"])}</span></td>
<td>{html.escape(item["trade"])}</td><td>{html.escape(item["business_intent"])}</td>
<td>{html.escape(item["hero"] or "omitted")}</td><td>{html.escape(item["page_silhouette"])}</td>
<td>{recomposed}</td>
<td>{html.escape(low_dims)}</td>
<td class="compare">
  <div class="compare-pair"><span>V0.1</span><img loading="lazy" src="review/v0.1/desktop/{item['fixture_id']}.jpg" alt="V0.1 desktop {html.escape(item['fixture_id'])}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{{textContent:'no capture',className:'missing'}}))"></div>
  <div class="compare-pair"><span>V0.2</span><img loading="lazy" src="review/v0.2/desktop/{item['fixture_id']}.jpg" alt="V0.2 desktop {html.escape(item['fixture_id'])}" onerror="this.replaceWith(Object.assign(document.createElement('span'),{{textContent:'no capture',className:'missing'}}))"></div>
</td>
<td class="links"><a href="sites/{item['fixture_id']}/">Open V0.2</a><a href="sites-v0.1/{item['fixture_id']}/">Open V0.1</a><a href="sites/{item['fixture_id']}/dna.json">DNA</a><a href="sites/{item['fixture_id']}/render-plan.json">RenderPlan</a><a href="sites/{item['fixture_id']}/visual-completeness.json">Completeness</a></td>
</tr>''')
    return '''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Design Genome Renderer — Visual Lab (V0.1 / V0.2)</title><meta name="robots" content="noindex,nofollow"><style>
*{box-sizing:border-box}body{margin:0;background:#f4f4f1;color:#181816;font:14px/1.5 Arial,sans-serif;letter-spacing:0}header{padding:34px clamp(16px,4vw,56px);border-bottom:1px solid #aaa}h1{margin:0;font-size:32px;letter-spacing:0}p{max-width:72ch;margin:8px 0 0;color:#595955}.status{display:inline-block;margin-top:18px;padding:5px 8px;border:1px solid #181816;font-size:11px;text-transform:uppercase}main{overflow:auto;padding:24px clamp(16px,4vw,56px) 60px}table{width:100%;min-width:1500px;border-collapse:collapse;background:#fff}th,td{text-align:left;vertical-align:top;padding:14px 12px;border-bottom:1px solid #d5d5d0}th{font-size:11px;text-transform:uppercase;background:#e8e8e3;position:sticky;top:0}td strong,td span{display:block}.links{white-space:nowrap}.links a{display:block;margin-bottom:6px;color:#064f9c;text-underline-offset:3px}.compare{display:flex;gap:10px}.compare-pair{display:grid;gap:4px;font-size:10px;text-transform:uppercase;color:#595955}.compare-pair img{width:160px;height:110px;object-fit:cover;object-position:top;border:1px solid #ccc;background:#eee}.compare-pair .missing{display:flex;align-items:center;justify-content:center;width:160px;height:110px;border:1px dashed #ccc;color:#999;font-size:10px}:focus-visible{outline:3px solid #005fcc;outline-offset:3px}
</style></head><body><header><h1>Design Genome Renderer — V0.1 vs V0.2</h1><p>Comparaison des 12 fixtures synthétiques identiques, avant/après la passe de réalisation visuelle. Ce laboratoire sert à la revue humaine ; aucun statut esthétique n'est calculé automatiquement.</p><span class="status">Not reviewed</span></header><main><table><thead><tr><th>Fixture</th><th>Métier</th><th>Intent</th><th>Hero (V0.2)</th><th>Silhouette</th><th>Recomposition DNA</th><th>Dimensions faibles</th><th>Desktop V0.1 / V0.2</th><th>Actions</th></tr></thead><tbody>''' + "".join(rows) + '''</tbody></table></main></body></html>'''


def build_visual_lab(output: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    (output / "sites").mkdir(exist_ok=True)
    (output / "review" / "v0.2" / "desktop").mkdir(parents=True, exist_ok=True)
    (output / "review" / "v0.2" / "mobile").mkdir(parents=True, exist_ok=True)
    (output / "review" / "v0.2" / "dna").mkdir(parents=True, exist_ok=True)
    (output / "review" / "v0.2" / "render-plan").mkdir(parents=True, exist_ok=True)
    (output / "review" / "v0.2" / "visual-completeness").mkdir(parents=True, exist_ok=True)

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

        ctx = RenderContext.from_payload(fixture, dna, "", lab_mode=True)
        plan = build_render_plan(ctx, fixture["fixture_id"])
        completeness = assess(plan)

        site_dir = output / "sites" / fixture["fixture_id"]
        site_dir.mkdir(exist_ok=True)
        site_dir.joinpath("index.html").write_text(rendered, encoding="utf-8")
        _write_json(site_dir / "dna.json", dna.to_dict())
        _write_json(site_dir / "render-plan.json", plan.to_dict())
        _write_json(site_dir / "visual-completeness.json", completeness.to_dict())
        review = _review(fixture, dna)
        _write_json(site_dir / "review.json", review)
        _write_json(output / "review" / "v0.2" / "dna" / f'{fixture["fixture_id"]}.json', dna.to_dict())
        _write_json(output / "review" / "v0.2" / "render-plan" / f'{fixture["fixture_id"]}.json', plan.to_dict())
        _write_json(output / "review" / "v0.2" / "visual-completeness" / f'{fixture["fixture_id"]}.json', completeness.to_dict())
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
            "initial_hero_component": plan.initial_hero_component,
            "resolved_hero_component": plan.resolved_hero_component,
            "palette": dna.color_system,
            "typography": dna.typography_system,
            "grid": dna.grid_system,
            "spacing": dna.spacing_system,
            "geometry": dna.geometry_system,
            "media_provenance": _media_summary(fixture),
            "visual_completeness": completeness.to_dict(),
            "aesthetic_status": "NOT_REVIEWED",
        }
        manifest.append(item)

    _write_json(output / "manifest.json", {
        "renderer": RENDERER_VERSION,
        "fixture_policy": "synthetic fixtures restricted to the visual lab",
        "aesthetic_status": "NOT_REVIEWED",
        "baseline": "v0.1 preserved under sites-v0.1/ and review/v0.1/ -- never overwritten by this script",
        "fixtures": manifest,
    })
    desktop_captured = all(
        (output / "review" / "v0.2" / "desktop" / f'{fixture["fixture_id"]}.jpg').is_file()
        for fixture in LAB_FIXTURES
    )
    mobile_captured = all(
        (output / "review" / "v0.2" / "mobile" / f'{fixture["fixture_id"]}.jpg').is_file()
        for fixture in LAB_FIXTURES
    )
    _write_json(output / "review" / "manifest.json", {
        "aesthetic_status": "NOT_REVIEWED",
        "figma_upload": False,
        "renderer": RENDERER_VERSION,
        "v0_1_desktop_screenshots": "PRESERVED" if (output / "review" / "v0.1" / "desktop").is_dir() else "NOT_FOUND",
        "v0_1_mobile_screenshots": "PRESERVED" if (output / "review" / "v0.1" / "mobile").is_dir() else "NOT_FOUND",
        "v0_2_desktop_screenshots": "CAPTURED" if desktop_captured else "SCREENSHOTS_UNAVAILABLE",
        "v0_2_mobile_screenshots": "CAPTURED" if mobile_captured else "SCREENSHOTS_UNAVAILABLE",
        "sites": review_manifest,
    })
    output.joinpath("index.html").write_text(_lab_index(manifest), encoding="utf-8")
    output.joinpath("vercel.json").write_text('{"cleanUrls":true,"trailingSlash":true}\n', encoding="utf-8")
    output.joinpath("README.md").write_text(
        "# Design Genome Renderer Visual Lab\n\n"
        "Static, portable review package containing 12 explicitly synthetic fixtures, "
        "rendered by both the preserved V0.1 baseline (`sites-v0.1/`, `review/v0.1/`) and "
        "the current V0.2 engine (`sites/`, `review/v0.2/`). "
        "Run `python -m generator.genome_renderer.lab.build` from the repository root to "
        "rebuild the V0.2 side; V0.1 is a frozen historical snapshot and is never regenerated.\n\n"
        "All aesthetic statuses start at `NOT_REVIEWED`. The forms are disabled, no provider is "
        "called at runtime, and this directory can be selected as an isolated Vercel project root.\n",
        encoding="utf-8",
    )
    # The V0.1 marker (VERCEL_PREVIEW_NOT_DEPLOYED_BY_CODEX) was written by
    # the session that built that baseline and is left as-is, historically
    # accurate. This V0.2 pass was not deployed to Vercel either -- say so
    # under the correct attribution rather than editing the old one.
    output.joinpath("VERCEL_PREVIEW_NOT_DEPLOYED_BY_CLAUDE_CODE").write_text(
        "Portable static lab prepared (V0.2); no preview URL was created by Claude Code in this session.\n",
        encoding="utf-8",
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
