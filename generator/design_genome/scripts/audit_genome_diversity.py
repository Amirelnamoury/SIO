"""Run diversity experiments through the public Design Genome pipeline."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict, deque
from dataclasses import replace
from pathlib import Path
from statistics import mean

from ..generator import DesignGenome
from ..blueprints import blueprint_fingerprint
from ..composition import composition_report, visual_diversity_report
from ..data.components import ALL_COMPONENTS
from ..models import DesignDecisionTrace, DesignInput, MediaInventory, SiteDNA
from ..similarity import compare_dna
from ..taxonomy import TRADES


INTENTS = (
    "balanced", "local_quote", "premium_residential", "renovation_project",
    "technical_expertise", "portfolio", "craft", "commercial_b2b", "trust_first",
)
SERVICES = {
    "plombier": ("Dépannage", "Salle de bains", "Chauffage"),
    "peintre": ("Peinture intérieure", "Façade", "Finitions"),
    "macon": ("Maçonnerie", "Extension", "Façade"),
    "electricien": ("Installation", "Dépannage", "Éclairage"),
    "menuisier": ("Agencement", "Mobilier", "Restauration"),
    "renovateur": ("Rénovation globale", "Coordination", "Aménagement"),
}


def make_input(index: int, trade: str, city: str = "") -> DesignInput:
    rng = random.Random(f"genome:{trade}:{city}:{index}")
    project_photos = rng.choice((0, 0, 2, 4, 8))
    stock_photos = rng.choice((0, 2, 4, 6))
    facts = {"phone": "verified-simulation-channel", "email": "verified-simulation-channel", "process": ("phase-1", "phase-2")}
    if rng.random() < .42:
        facts["reviews"] = ({"rating": 5, "text": "verified-simulation-fact"},)
    if rng.random() < .26:
        facts["insurance"] = "verified-simulation-fact"
    if rng.random() < .22:
        facts["service_areas"] = (city or "verified-simulation-area",)
    if rng.random() < .18:
        facts["verified_facts"] = ("verified-simulation-fact",)
    return DesignInput(
        trade=trade, seed=f"simulation-{index}-{trade}-{city}", city=city,
        business_intent=rng.choice(INTENTS), services=SERVICES[trade][:rng.randint(1, 3)],
        facts=facts,
        media=MediaInventory(
            artisan_photos=project_photos, stock_photos=stock_photos, project_photos=project_photos,
            before_after_pairs=1 if project_photos >= 4 and rng.random() < .3 else 0,
            portrait_photos=1 if project_photos and rng.random() < .4 else 0,
            landscape_photos=1 if project_photos or stock_photos else 0, has_logo=rng.random() < .7,
        ),
    )


def same_plumber_input(index: int) -> DesignInput:
    base = DesignInput(
        trade="plombier", seed="same-input", city="Lyon", business_intent="premium_residential",
        services=SERVICES["plombier"],
        facts={"phone": "verified-simulation-channel", "email": "verified-simulation-channel", "process": ("phase-1", "phase-2")},
        media=MediaInventory(artisan_photos=4, stock_photos=4, project_photos=4, portrait_photos=1, landscape_photos=1, has_logo=True),
    )
    return replace(base, seed=f"same-input-plumber-{index}")


def distribution(dnas: list[SiteDNA], field: str) -> dict[str, int]:
    return dict(Counter(str(getattr(dna, field)) for dna in dnas).most_common())


def generate_cohort(inputs: list[DesignInput], history_limit: int = 32, history_by_trade: bool = False) -> tuple[list[SiteDNA], dict]:
    genome = DesignGenome(candidate_count=32)
    histories: dict[str, deque[SiteDNA]] = defaultdict(lambda: deque(maxlen=history_limit))
    all_history: deque[SiteDNA] = deque(maxlen=history_limit)
    dnas: list[SiteDNA] = []
    traces: list[DesignDecisionTrace] = []
    failures: list[str] = []
    for item in inputs:
        history = histories[item.trade] if history_by_trade else all_history
        try:
            dna = genome.generate(item, tuple(history), traces)
        except RuntimeError as error:
            failures.append(str(error))
            continue
        dnas.append(dna)
        history.append(dna)
    metrics = {
        "requested": len(inputs), "generated": len(dnas), "failed": len(failures),
        "unique": len({item.design_signature for item in dnas}),
        "unique_composition_signatures": len({item.composition_signature for item in dnas}),
        "rejected_by_similarity": sum(item.similarity_rejections for item in traces),
        "rejected_by_linter": sum(item.linter_rejections for item in traces),
        "rejected_by_quality": sum(item.quality_rejections for item in traces),
        "rejected_structural_duplicates": sum(item.structural_duplicate_rejections for item in traces),
        "mean_attempts": round(mean(item.attempts for item in traces), 4) if traces else 0,
        "max_attempts": max((item.attempts for item in traces), default=0),
        "failure_examples": failures[:3],
    }
    return dnas, metrics


def maximum_cohort_similarity(dnas: list[SiteDNA]) -> float:
    return max((compare_dna(left, right).overall_visual_similarity for index, left in enumerate(dnas) for right in dnas[index + 1:]), default=0.0)


def cohort_detail(dnas: list[SiteDNA]) -> dict:
    fields = (
        "site_archetype", "art_direction", "page_silhouette", "hero_component",
        "header_component", "services_component", "color_system", "typography_system",
        "grid_system", "photo_direction", "section_order",
    )
    heroes = [ALL_COMPONENTS[dna.hero_component] for dna in dnas]
    reports = [composition_report(dna) for dna in dnas]
    ablation_similarities = [
        compare_dna(left, right, include_color=False, include_typography=False).overall_visual_similarity
        for index, left in enumerate(dnas)
        for right in dnas[index + 1:]
    ]
    return {
        "unique_signatures": len({dna.design_signature for dna in dnas}),
        "unique_composition_signatures": len({dna.composition_signature for dna in dnas}),
        "maximum_pair_similarity": maximum_cohort_similarity(dnas),
        "ablation_without_color_typography": {
            "maximum_pair_similarity": max(ablation_similarities, default=0.0),
            "unique_composition_signatures": len({dna.composition_signature for dna in dnas}),
            "unique_layout_rhythms": len({report.layout_rhythm for report in reports}),
        },
        "visual_diversity": visual_diversity_report(dnas),
        "hero_families": dict(Counter(item.family_id for item in heroes)),
        "hero_variants": dict(Counter(f"{item.family_id}:{item.variant_id}" for item in heroes)),
        "hero_fingerprints": dict(Counter(blueprint_fingerprint(item) for item in heroes)),
        "header_fingerprints": len({blueprint_fingerprint(ALL_COMPONENTS[dna.header_component]) for dna in dnas}),
        "services_fingerprints": len({blueprint_fingerprint(ALL_COMPONENTS[dna.services_component]) for dna in dnas}),
        "gallery_fingerprints": len({blueprint_fingerprint(ALL_COMPONENTS[dna.gallery_component]) for dna in dnas if dna.gallery_component}),
        "layout_rhythms": len({report.layout_rhythm for report in reports}),
        "distributions": {field: distribution(dnas, field) for field in fields},
    }


def collision_estimate(signatures: Counter[str]) -> dict[str, int | str]:
    sample_size = sum(signatures.values())
    collision_pairs = sum(count * (count - 1) // 2 for count in signatures.values())
    estimate = sample_size * (sample_size - 1) // 2 if collision_pairs == 0 else round(sample_size * (sample_size - 1) / (2 * collision_pairs))
    method = "lower_bound_under_zero_observed_collisions" if collision_pairs == 0 else "uniform_birthday_collision_estimate"
    return {"sample_size": sample_size, "collision_pairs": collision_pairs, "effective_space_estimate": estimate, "method": method}


def run(count: int) -> dict:
    main_inputs = [make_input(index, TRADES[index % len(TRADES)]) for index in range(count)]
    all_dnas, main_metrics = generate_cohort(main_inputs, history_limit=24, history_by_trade=True)
    plumber_dnas, plumber_metrics = generate_cohort([make_input(index, "plombier", "Lyon") for index in range(100)], history_limit=100)
    same_dnas, same_metrics = generate_cohort([same_plumber_input(index) for index in range(50)], history_limit=50)
    signatures = Counter(dna.design_signature for dna in all_dnas)
    sampled_similarities = [compare_dna(all_dnas[index], all_dnas[index + 1]).overall_visual_similarity for index in range(0, min(len(all_dnas) - 1, 4_000), 2)]
    return {
        "schema_version": 3,
        "pipeline": "DesignGenome.generate with audit trace collection",
        "history_policy": "bounded recent visual history; 24 per trade for main cohort, full prior cohort for focused tests",
        "main_simulation": {
            **main_metrics, **collision_estimate(signatures),
            "sampled_pair_similarity": {"count": len(sampled_similarities), "mean": round(mean(sampled_similarities), 4) if sampled_similarities else 0, "max": max(sampled_similarities, default=0.0)},
            "visual_diversity": visual_diversity_report(all_dnas),
            "distributions": {field: distribution(all_dnas, field) for field in ("site_archetype", "art_direction", "page_silhouette", "hero_component", "color_system", "typography_system")},
        },
        "plumber_100": {**plumber_metrics, **cohort_detail(plumber_dnas)},
        "same_input_plumber_50": {**same_metrics, **cohort_detail(same_dnas)},
        "limitations": [
            "The effective-space figure is a collision estimate, not a count of visually reviewed pages.",
            "SiteDNA diversity and heuristic quality do not prove rendered aesthetic quality.",
            "Simulation facts are typed capability placeholders and never production artisan claims.",
        ],
    }


def markdown(payload: dict) -> str:
    main, plumber, same = payload["main_simulation"], payload["plumber_100"], payload["same_input_plumber_50"]
    return f"""# Design Genome simulation report

All cohorts use the public generation pipeline with linting, heuristic quality scoring, bounded history and anti-clone rejection. This is combinatorial evidence, not rendered aesthetic approval.

## Main cohort
- Requested: {main['sample_size'] + main['failed']:,}
- Generated / failed / unique: {main['generated']:,} / {main['failed']:,} / {main['unique']:,}
- Similarity / linter / quality / structural duplicate rejections: {main['rejected_by_similarity']:,} / {main['rejected_by_linter']:,} / {main['rejected_by_quality']:,} / {main['rejected_structural_duplicates']:,}
- Unique design / composition signatures: {main['unique']:,} / {main['unique_composition_signatures']:,}
- Mean / maximum attempts: {main['mean_attempts']} / {main['max_attempts']}
- Sampled mean / maximum pair similarity: {main['sampled_pair_similarity']['mean']} / {main['sampled_pair_similarity']['max']}
- Collision pairs: {main['collision_pairs']:,}; effective-space estimate: {main['effective_space_estimate']:,} (`{main['method']}`)

## 100 plumbers with shared history
- Generated / failed / unique: {plumber['generated']} / {plumber['failed']} / {plumber['unique_signatures']}
- Unique composition signatures / hero fingerprints / layout rhythms: {plumber['unique_composition_signatures']} / {len(plumber['hero_fingerprints'])} / {plumber['layout_rhythms']}
- Maximum pair similarity: {plumber['maximum_pair_similarity']}
- Distinct silhouettes / heroes / palettes / typography: {len(plumber['distributions']['page_silhouette'])} / {len(plumber['distributions']['hero_component'])} / {len(plumber['distributions']['color_system'])} / {len(plumber['distributions']['typography_system'])}

## 50 identical-input plumbers
Only the artisan seed changes. Generated / failed / unique: {same['generated']} / {same['failed']} / {same['unique_signatures']}. Unique composition signatures: {same['unique_composition_signatures']}.
Distinct silhouettes / heroes / palettes / section compositions: {len(same['distributions']['page_silhouette'])} / {len(same['distributions']['hero_component'])} / {len(same['distributions']['color_system'])} / {len(same['distributions']['section_order'])}. Maximum pair similarity: {same['maximum_pair_similarity']}.

## Color/type ablation
With color and typography removed from comparison, the 100-plumber cohort retains {plumber['ablation_without_color_typography']['unique_composition_signatures']} composition signatures and {plumber['ablation_without_color_typography']['unique_layout_rhythms']} layout rhythms. Maximum pair similarity is {plumber['ablation_without_color_typography']['maximum_pair_similarity']}.

## Interpretation boundary
The Design Genome is a knowledge contract. Human desktop/mobile rendering review remains mandatory before any production integration.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10_000)
    parser.add_argument("--json", type=Path, default=Path("docs/design-encyclopedia/genome-simulation.json"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/design-encyclopedia/genome-simulation.md"))
    args = parser.parse_args()
    payload = run(args.count)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(payload), encoding="utf-8")
    print(json.dumps(payload["main_simulation"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
