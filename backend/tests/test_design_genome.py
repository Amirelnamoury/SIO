from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.design_genome import DesignGenome, DesignInput, MediaInventory, generate_site_dna
from generator.design_genome.archetypes import ARCHETYPES
from generator.design_genome.compatibility import evaluate_component
from generator.design_genome.data.color_systems import COLOR_SYSTEMS, contrast_ratio
from generator.design_genome.data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES
from generator.design_genome.data.grids import GRID_SYSTEMS
from generator.design_genome.data.page_silhouettes import PAGE_SILHOUETTES
from generator.design_genome.data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from generator.design_genome.data.trade_grammar import TRADE_GRAMMARS
from generator.design_genome.data.typography_systems import TYPOGRAPHY_SYSTEMS
from generator.design_genome.data_truth import TruthClass, classify_claim
from generator.design_genome.linter import lint_dna
from generator.design_genome.photo_direction import PHOTO_DIRECTIONS
from generator.design_genome.quality import evaluate_quality
from generator.design_genome.rhythm import evaluate_rhythm
from generator.design_genome.similarity import compare_dna


def design_input(trade="plombier", seed="test", *, project_photos=3, stock_photos=2, facts=None):
    return DesignInput(
        trade=trade,
        seed=seed,
        city="Lyon",
        business_intent="quote",
        services=("Service principal", "Service secondaire"),
        facts=facts or {"phone": "0102030405", "email": "artisan@example.test", "process": ("Échange", "Réalisation")},
        media=MediaInventory(
            artisan_photos=project_photos,
            project_photos=project_photos,
            stock_photos=stock_photos,
            landscape_photos=1 if project_photos or stock_photos else 0,
        ),
    )


def test_encyclopedia_registry_minimums_and_exact_component_counts():
    assert len(COLOR_SYSTEMS) == 40
    assert len(TYPOGRAPHY_SYSTEMS) == 30
    assert len(GRID_SYSTEMS) == 20
    assert len(PAGE_SILHOUETTES) == 30
    assert len(ARCHETYPES) == 20
    assert len(TRADE_GRAMMARS) == 6
    assert len(PHOTO_DIRECTIONS) == 6 * 8 * 4
    assert len(MOTION_SYSTEMS) == 12
    assert len(SPATIAL_SYSTEMS) == 9
    assert len(MOBILE_PERSONALITIES) == 12
    assert {key: len(value) for key, value in COMPONENT_REGISTRIES.items()} == {
        "header": 25, "hero": 50, "services": 35, "gallery": 30, "about": 20,
        "trust": 20, "cta": 25, "contact": 20, "footer": 20, "form": 15,
    }
    assert len(ALL_COMPONENTS) == 260


def test_all_semantic_color_systems_pass_core_wcag_aa_contrast():
    for color in COLOR_SYSTEMS.values():
        assert color.contrast_score >= 4.5, color.id
        assert contrast_ratio(color.tokens["text_primary"], color.tokens["canvas"]) >= 4.5
        assert contrast_ratio(color.tokens["text_inverse"], color.tokens["surface_inverse"]) >= 4.5


def test_site_dna_is_deterministic_serializable_and_signed():
    source = design_input()
    left = generate_site_dna(source)
    right = generate_site_dna(source)
    assert left == right
    assert left.design_signature == left.signature_for(left.to_dict())
    assert type(left).from_dict(json.loads(left.to_json())) == left


@pytest.mark.parametrize("trade", tuple(TRADE_GRAMMARS))
def test_each_trade_generates_valid_linted_dna(trade):
    source = design_input(trade, f"seed-{trade}")
    dna = generate_site_dna(source)
    assert dna.version == "design-genome-1"
    assert dna.art_direction in TRADE_GRAMMARS[trade].compatible_directions
    assert not [issue for issue in lint_dna(dna, source) if issue.severity == "error"]


def test_missing_media_omits_gallery_instead_of_inventing_projects():
    source = design_input(project_photos=0, stock_photos=0)
    dna = generate_site_dna(source)
    assert dna.gallery_component is None
    assert "gallery" not in dna.section_order


def test_stock_media_never_satisfies_artisan_project_evidence():
    component = ALL_COMPONENTS["artisan_project_evidence"]
    source = design_input(project_photos=0, stock_photos=8)
    result = evaluate_component(component, source, ARCHETYPES["project_portfolio"], "editorial_luxury")
    assert not result.allowed
    assert any("artisan_project" in failure for failure in result.hard_failures)


def test_before_after_never_accepts_stock_only_media():
    component = ALL_COMPONENTS["before_after_transformation_pairs"]
    source = design_input(project_photos=0, stock_photos=8)
    result = evaluate_component(component, source, ARCHETYPES["luxury_renovation"], "cinematic_luxury")
    assert not result.allowed
    assert component.allowed_media_sources == frozenset({"artisan"})


def test_missing_verified_facts_omits_trust_section():
    source = design_input(project_photos=0, stock_photos=2, facts={"phone": "0102030405"})
    dna = generate_site_dna(source)
    assert dna.trust_component is None
    assert "trust" not in dna.section_order


def test_missing_contact_channel_omits_conversion_contact_and_form():
    source = design_input(project_photos=2, facts={"process": ("Échange", "Réalisation")})
    dna = generate_site_dna(source)
    assert dna.cta_component is None
    assert dna.contact_component is None
    assert dna.form_component is None


@pytest.mark.parametrize(
    ("claim", "facts", "expected"),
    (
        ("15 ans d'expérience", {}, TruthClass.FORBIDDEN_INVENTION),
        ("15 ans d'expérience", {"years_experience": 15}, TruthClass.FACT),
        ("Assurance décennale", {}, TruthClass.FORBIDDEN_INVENTION),
        ("Intervention sous 24h", {}, TruthClass.FORBIDDEN_INVENTION),
        ("Parlons de votre projet", {}, TruthClass.SAFE_GENERIC_COPY),
    ),
)
def test_truth_model_blocks_unsupported_claims(claim, facts, expected):
    assert classify_claim(claim, facts).classification == expected


def test_rhythm_detects_three_heavy_sections():
    components = tuple(ALL_COMPONENTS[item] for item in (
        "full_bleed_photo_cover", "cinematic_service_reveal", "full_bleed_image_sequence"
    ))
    report = evaluate_rhythm(components)
    assert any(issue.startswith("three_heavy_sections") for issue in report.issues)
    assert report.score < .7


def test_similarity_is_explainable_and_exact_for_same_dna():
    left = generate_site_dna(design_input(seed="left"))
    same = compare_dna(left, left)
    other = generate_site_dna(design_input("menuisier", "other"))
    different = compare_dna(left, other)
    assert same.overall_visual_similarity == 1.0
    assert different.overall_visual_similarity < 1.0
    assert 0 <= different.structural_distance <= 1


def test_anti_clone_history_returns_a_distinct_candidate():
    source = design_input(seed="anti-clone")
    first = generate_site_dna(source)
    second = DesignGenome(candidate_count=40).generate(source, (first,))
    assert second.design_signature != first.design_signature
    assert compare_dna(first, second).overall_visual_similarity < .84


def test_quality_score_is_bounded_and_exposes_risks():
    source = design_input()
    report = evaluate_quality(generate_site_dna(source), source)
    assert 0 <= report.total <= 100
    assert 0 <= report.overdesign_risk <= 1
    assert 0 <= report.underdesign_risk <= 1


def test_linter_rejects_contact_component_without_contact_data():
    with_contact = design_input()
    dna = generate_site_dna(with_contact)
    without_contact = replace(with_contact, facts={"process": ("Échange", "Réalisation")})
    issues = lint_dna(dna, without_contact)
    assert any(issue.code == "missing_contact" and issue.severity == "error" for issue in issues)


def test_photo_director_has_no_stock_project_or_before_after_role():
    assert PHOTO_DIRECTIONS
    for direction in PHOTO_DIRECTIONS.values():
        assert "project" not in direction.allowed_roles
        assert "before_after" not in direction.allowed_roles
        assert "stock image presented as our project" in direction.avoid


def test_section_order_keeps_header_hero_and_footer_boundaries():
    dna = generate_site_dna(design_input())
    assert dna.section_order[:2] == ("header", "hero")
    assert dna.section_order[-1] == "footer"
    assert len(dna.section_order) == len(set(dna.section_order))


def test_reference_atlas_records_150_plus_and_separates_failures():
    atlas = json.loads((REPO_ROOT / "docs" / "design-encyclopedia" / "reference-atlas.json").read_text(encoding="utf-8"))
    assert atlas["counts"]["total"] >= 150
    assert atlas["counts"]["gold_standards"] >= 30
    assert atlas["counts"]["accessible"] >= 20
    assert atlas["counts"]["failed_or_inaccessible"] >= 1
    assert len(atlas["references"]) == atlas["counts"]["total"]


def test_design_genome_is_not_imported_by_production_generator():
    production_files = [REPO_ROOT / "generator" / "site_generator.py", *sorted((REPO_ROOT / "generator" / "v3").glob("*.py"))]
    assert production_files
    for path in production_files:
        assert "design_genome" not in path.read_text(encoding="utf-8"), path


def test_design_genome_has_no_provider_or_llm_runtime_dependency():
    source = "\n".join(path.read_text(encoding="utf-8") for path in (REPO_ROOT / "generator" / "design_genome").rglob("*.py"))
    for forbidden in ("openai", "anthropic", "pexels.com", "pixabay.com", "resend", "stripe"):
        assert forbidden not in source.lower()
