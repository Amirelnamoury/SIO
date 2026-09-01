"""Run deterministic diversity experiments and publish machine-readable evidence."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from ..generator import _build_candidate
from ..models import DesignInput, MediaInventory, SiteDNA
from ..similarity import compare_dna
from ..taxonomy import TRADES


INTENTS = ("balanced", "quote", "residential", "technical", "projects", "craft", "local")
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
    facts = {"phone": "0100000000", "email": "contact@example.test", "process": ("Échange", "Réalisation")}
    if rng.random() < .42:
        facts["reviews"] = ({"rating": 5, "text": "Donnée de simulation"},)
    if rng.random() < .26:
        facts["insurance"] = "verified-simulation-value"
    if rng.random() < .22:
        facts["service_areas"] = (city or "Zone test",)
    if rng.random() < .18:
        facts["verified_facts"] = ("fact-simulation",)
    return DesignInput(
        trade=trade,
        seed=f"simulation-{index}-{trade}-{city}",
        city=city,
        business_intent=rng.choice(INTENTS),
        services=SERVICES[trade][:rng.randint(1, 3)],
        facts=facts,
        media=MediaInventory(
            artisan_photos=project_photos,
            stock_photos=stock_photos,
            project_photos=project_photos,
            before_after_pairs=1 if project_photos >= 4 and rng.random() < .3 else 0,
            portrait_photos=1 if project_photos and rng.random() < .4 else 0,
            landscape_photos=1 if project_photos or stock_photos else 0,
            has_logo=rng.random() < .7,
        ),
    )


def distribution(dnas: list[SiteDNA], field: str) -> dict[str, int]:
    return dict(Counter(str(getattr(dna, field)) for dna in dnas).most_common())


def cohort(count: int, trade_selector, city: str = "") -> list[SiteDNA]:
    inputs = [make_input(index, trade_selector(index), city) for index in range(count)]
    return [_build_candidate(item, f"{item.seed}:audit") for item in inputs]


def collision_estimate(signatures: Counter[str]) -> dict[str, int | float | str]:
    sample_size = sum(signatures.values())
    collision_pairs = sum(count * (count - 1) // 2 for count in signatures.values())
    if collision_pairs == 0:
        estimate = sample_size * (sample_size - 1) // 2
        qualifier = "lower_bound_under_zero_observed_collisions"
    else:
        estimate = round(sample_size * (sample_size - 1) / (2 * collision_pairs))
        qualifier = "uniform_birthday_collision_estimate"
    return {"sample_size": sample_size, "unique": len(signatures), "collision_pairs": collision_pairs, "effective_space_estimate": estimate, "method": qualifier}


def run(count: int) -> dict:
    all_dnas = cohort(count, lambda index: TRADES[index % len(TRADES)])
    plumber_dnas = cohort(100, lambda _index: "plombier")
    same_city = cohort(120, lambda index: TRADES[index % len(TRADES)], "Lyon")

    signatures = Counter(dna.design_signature for dna in all_dnas)
    sampled_similarities = []
    for index in range(0, min(len(all_dnas) - 1, 3000), 2):
        sampled_similarities.append(compare_dna(all_dnas[index], all_dnas[index + 1]).overall_visual_similarity)

    by_trade: dict[str, list[SiteDNA]] = defaultdict(list)
    for dna, trade in zip(all_dnas, (TRADES[index % len(TRADES)] for index in range(count))):
        by_trade[trade].append(dna)

    return {
        "schema_version": 1,
        "generator": "design-genome-1",
        "main_simulation": {
            **collision_estimate(signatures),
            "max_signature_frequency": max(signatures.values()),
            "sampled_pair_similarity": {
                "count": len(sampled_similarities),
                "mean": round(sum(sampled_similarities) / max(1, len(sampled_similarities)), 4),
                "max": max(sampled_similarities, default=0.0),
            },
            "distributions": {
                field: distribution(all_dnas, field)
                for field in ("site_archetype", "art_direction", "page_silhouette", "hero_component", "color_system", "typography_system")
            },
        },
        "plumber_100": {
            "unique_signatures": len({dna.design_signature for dna in plumber_dnas}),
            "archetypes": distribution(plumber_dnas, "site_archetype"),
            "heroes": distribution(plumber_dnas, "hero_component"),
            "silhouettes": distribution(plumber_dnas, "page_silhouette"),
            "colors": distribution(plumber_dnas, "color_system"),
        },
        "same_city_lyon": {
            "count": len(same_city),
            "unique_signatures": len({dna.design_signature for dna in same_city}),
            "by_trade": dict(Counter(TRADES[index % len(TRADES)] for index in range(len(same_city)))),
            "directions": distribution(same_city, "art_direction"),
        },
        "different_trades": {
            trade: {
                "count": len(items),
                "archetypes": distribution(items, "site_archetype"),
                "directions": distribution(items, "art_direction"),
                "colors": distribution(items, "color_system"),
            }
            for trade, items in by_trade.items()
        },
        "limitations": [
            "The effective-space figure is a collision estimate, not a count of visually reviewed pages.",
            "SiteDNA is a knowledge contract and does not prove rendered aesthetic quality.",
            "Simulation values are synthetic and are never production artisan claims.",
        ],
    }


def markdown(payload: dict) -> str:
    main = payload["main_simulation"]
    plumber = payload["plumber_100"]
    city = payload["same_city_lyon"]
    return f"""# Design Genome simulation report

Generated from deterministic knowledge-engine simulations. This report evaluates combinatorial diversity, not rendered aesthetic quality.

## 10,000 SiteDNA cohort

- Samples: {main['sample_size']:,}
- Unique signatures: {main['unique']:,}
- Collision pairs: {main['collision_pairs']:,}
- Effective compatible space estimate: {main['effective_space_estimate']:,}
- Estimation method: `{main['method']}`
- Mean sampled visual similarity: {main['sampled_pair_similarity']['mean']}
- Maximum sampled visual similarity: {main['sampled_pair_similarity']['max']}

## 100 plumbers

- Unique signatures: {plumber['unique_signatures']} / 100
- Archetypes used: {len(plumber['archetypes'])}
- Heroes used: {len(plumber['heroes'])}
- Silhouettes used: {len(plumber['silhouettes'])}
- Color systems used: {len(plumber['colors'])}

## Same city

The Lyon cohort produced {city['unique_signatures']} unique signatures across {city['count']} inputs and all six trade grammars.

## Interpretation boundary

The estimate is useful as an anti-clone engineering signal. It is not a claim that every combination is aesthetically excellent; visual review remains required before production integration.
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
