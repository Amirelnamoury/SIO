from dataclasses import replace
import ast
from pathlib import Path

import pytest

from generator.design_genome.blueprints import (
    blueprint_fingerprint, blueprint_structural_distance, differentiation_summary,
)
from generator.design_genome.composition import (
    composition_report, composition_report_markdown, composition_signature_for,
    visual_diversity_report,
)
from generator.design_genome.data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES
from generator.design_genome.generator import DesignGenome
from generator.design_genome.golden_compositions import (
    GOLDEN_COMPOSITION_CASES, GoldenCompositionCase, score_golden_composition,
)
from generator.design_genome.models import DesignInput, MediaInventory
from generator.design_genome.rhythm import evaluate_rhythm
from generator.design_genome.scripts.check_renderer_readiness import check as check_renderer_readiness
from generator.design_genome.similarity import compare_dna


REPO_ROOT = Path(__file__).resolve().parents[2]


def rich_input(seed: str = "blueprint") -> DesignInput:
    return DesignInput(
        trade="plombier", seed=seed, city="Lyon", business_intent="premium_residential",
        services=("Dépannage", "Salle de bains", "Chauffage"),
        facts={"phone": "verified", "email": "verified", "process": ("one", "two"), "verified_facts": ("fact",)},
        media=MediaInventory(artisan_photos=5, stock_photos=4, project_photos=5, portrait_photos=1, landscape_photos=1, has_logo=True),
    )


def structural_clone(component, **changes):
    return replace(component, **changes)


def test_fingerprint_uses_structure_not_identity_or_notes():
    component = ALL_COMPONENTS["full_bleed_photo_cover"]
    assert blueprint_fingerprint(component) == blueprint_fingerprint(structural_clone(component, id="opaque_key", notes="changed", family_id="renamed.family", variant_id="renamed"))


@pytest.mark.parametrize(
    "mutation",
    (
        lambda spec: replace(spec, layout_pattern="different_pattern"),
        lambda spec: replace(spec, edge_behavior="floating"),
        lambda spec: replace(spec, media_intensity=max(0, spec.media_intensity - 1)),
        lambda spec: replace(spec, media_spec={**spec.media_spec, "media_layout": "different_placement"}),
        lambda spec: replace(spec, mobile_spec={**spec.mobile_spec, "mobile_order": ("media", "title", "actions")}),
    ),
)
def test_fingerprint_changes_for_renderer_visible_structure(mutation):
    component = ALL_COMPONENTS["full_bleed_photo_cover"]
    changed = structural_clone(component, blueprint_spec=mutation(component.blueprint_spec))
    assert blueprint_fingerprint(component) != blueprint_fingerprint(changed)


def test_all_components_have_unique_structural_fingerprints_without_aliases():
    for category, registry in COMPONENT_REGISTRIES.items():
        summary = differentiation_summary(registry.values())
        assert summary["unique_fingerprints"] == len(registry), category
        assert not summary["exact_duplicates"]
        assert all(not component.is_alias and component.alias_of is None for component in registry.values())


def test_every_multi_variant_family_has_meaningful_intra_family_distance():
    for registry in COMPONENT_REGISTRIES.values():
        summary = differentiation_summary(registry.values())
        for family, distance in summary["minimum_intra_family_distance"].items():
            if distance is not None:
                assert .15 <= distance <= .40, (family, distance)


def test_structural_distance_is_explainable_and_bounded():
    same = ALL_COMPONENTS["full_bleed_photo_cover"]
    variant = ALL_COMPONENTS["centered_image_frame"]
    other = ALL_COMPONENTS["no_image_typographic_signal"]
    assert blueprint_structural_distance(same, same).distance == 0
    related = blueprint_structural_distance(same, variant)
    distinct = blueprint_structural_distance(same, other)
    assert .15 <= related.distance <= .40
    assert distinct.distance > related.distance
    assert related.reasons


def test_composition_signature_excludes_seed_and_palette_but_tracks_structure():
    dna = DesignGenome().generate(rich_input())
    payload = dna.to_dict()
    payload["seed"] = "another-seed"
    payload["color_system"] = "another-color"
    assert composition_signature_for(payload) == dna.composition_signature
    replacement = next(key for key in COMPONENT_REGISTRIES["hero"] if key != dna.hero_component)
    payload["hero_component"] = replacement
    assert composition_signature_for(payload) != dna.composition_signature


def test_composition_report_is_readable_and_structural():
    dna = DesignGenome().generate(rich_input("report"))
    report = composition_report(dna)
    text = composition_report_markdown(dna)
    assert report.composition_signature == dna.composition_signature
    assert report.components and report.transitions
    assert "PAGE RHYTHM" not in text  # heading uses normal title case, data remains machine-readable
    assert "## Page rhythm" in text and "fingerprint" in text


def test_similarity_is_structure_first_under_color_type_ablation():
    left = DesignGenome().generate(rich_input("similarity"))
    recolored = replace(left, color_system="opaque-color", typography_system="opaque-type", design_signature="changed")
    assert compare_dna(left, recolored).overall_visual_similarity >= .88
    assert compare_dna(left, recolored, include_color=False, include_typography=False).overall_visual_similarity == 1.0
    changed_payload = left.to_dict()
    changed_payload["hero_component"] = next(key for key in COMPONENT_REGISTRIES["hero"] if key != left.hero_component)
    changed_payload["services_component"] = next(key for key in COMPONENT_REGISTRIES["services"] if key != left.services_component)
    changed_payload["composition_signature"] = composition_signature_for(changed_payload)
    structurally_changed = type(left).from_dict(changed_payload)
    assert compare_dna(left, structurally_changed).blueprint_distance > 0


def test_different_component_id_with_same_blueprint_is_a_near_clone(monkeypatch):
    left = DesignGenome().generate(rich_input("alias"))
    original = ALL_COMPONENTS[left.hero_component]
    alias = replace(original, id="opaque_alias_for_test")
    monkeypatch.setitem(ALL_COMPONENTS, alias.id, alias)
    payload = left.to_dict()
    payload["hero_component"] = alias.id
    payload["composition_signature"] = composition_signature_for(payload)
    right = type(left).from_dict(payload)
    report = compare_dna(left, right)
    assert report.blueprint_distance == 0
    assert report.overall_visual_similarity >= .95


def test_rhythm_detects_repeated_patterns_media_and_type_roles():
    base = ALL_COMPONENTS["full_bleed_photo_cover"]
    repeated = tuple(replace(base, id=f"repeat-{index}") for index in range(4))
    report = evaluate_rhythm(repeated)
    assert any("three_repeated_pattern" in issue for issue in report.issues)
    assert any("three_repeated_media" in issue for issue in report.issues)
    assert report.patterns and report.media_intensities and report.type_scale_roles


def test_rhythm_detects_same_pattern_across_different_families_and_ids():
    components = tuple(ALL_COMPONENTS[component_id] for component_id in (
        "phone_first_problem_solution", "founder_story_split", "split_project_cta",
    ))
    assert len({component.id for component in components}) == 3
    assert len({component.family_id for component in components}) == 3
    assert {component.blueprint_spec.layout_pattern for component in components} == {"split"}
    assert any("three_repeated_pattern:split" in issue for issue in evaluate_rhythm(components).issues)


def test_selection_code_never_infers_semantics_from_any_id_text():
    files = list((REPO_ROOT / "generator" / "design_genome").rglob("*.py"))
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            has_id_attribute = any(isinstance(item, ast.Attribute) and item.attr == "id" for item in operands)
            has_literal = any(isinstance(item, ast.Constant) and isinstance(item.value, str) for item in operands)
            uses_membership = any(isinstance(operator, (ast.In, ast.NotIn)) for operator in node.ops)
            assert not (has_id_attribute and has_literal and uses_membership), (path, ast.unparse(node))


def test_visual_diversity_report_and_ablation_remain_structural():
    genome = DesignGenome(candidate_count=40)
    history = []
    for index in range(20):
        history.append(genome.generate(rich_input(f"cohort-{index}"), tuple(history)))
    report = visual_diversity_report(history)
    assert report["unique_design_signatures"] == 20
    assert report["unique_composition_signatures"] >= 16
    assert report["unique_blueprint_fingerprints"] > report["unique_colors"]


def test_twelve_golden_cases_and_compatible_scoring():
    assert len(GOLDEN_COMPOSITION_CASES) == 12
    dna = DesignGenome().generate(rich_input("golden"))
    report = composition_report(dna)
    compatible = GoldenCompositionCase(
        "runtime-compatible",
        tuple(item.family_id.split(".")[-1] for item in report.components[:3]),
        report.layout_rhythm[:2], "measured", "honest", ("impossible_marker",),
    )
    score, reasons = score_golden_composition(dna, compatible)
    assert score >= .85
    assert reasons


def test_renderer_readiness_covers_every_component_without_missing_contracts():
    issues, summaries = check_renderer_readiness()
    assert not issues
    assert sum(summary["components"] for summary in summaries.values()) == 260
    assert all(not summary["exact_duplicates"] for summary in summaries.values())
