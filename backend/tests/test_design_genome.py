from dataclasses import replace
import ast
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.design_genome import DesignGenome, DesignInput, MediaInventory, SiteDNA, generate_site_dna
from generator.design_genome.archetypes import ARCHETYPES
from generator.design_genome.compatibility import evaluate_component
from generator.design_genome.component_relationships import component_pair_affinity, sequence_affinity
from generator.design_genome.data.color_systems import COLOR_SYSTEMS, contrast_ratio
from generator.design_genome.data.components import ALL_COMPONENTS, COMPONENT_REGISTRIES
from generator.design_genome.data.grids import GRID_SYSTEMS
from generator.design_genome.data.foundations import GEOMETRY_SYSTEMS, SPACING_SYSTEMS
from generator.design_genome.data.page_silhouettes import PAGE_SILHOUETTES
from generator.design_genome.data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from generator.design_genome.data.trade_grammar import TRADE_GRAMMARS
from generator.design_genome.data.typography_systems import TYPOGRAPHY_SYSTEMS
from generator.design_genome.data_truth import TruthClass, can_render_claim, can_use_media_wording, classify_claim
from generator.design_genome.linter import lint_dna
from generator.design_genome.photo_direction import PHOTO_DIRECTIONS
from generator.design_genome.quality import evaluate_quality
from generator.design_genome.rhythm import evaluate_rhythm
from generator.design_genome.similarity import compare_dna
from generator.design_genome.scripts.audit_component_semantics import audit_all


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


def test_component_factory_never_branches_on_component_id_text():
    path = REPO_ROOT / "generator" / "design_genome" / "data" / "components" / "_factory.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        names = {child.id for child in ast.walk(node.test) if isinstance(child, ast.Name)}
        text_constants = {child.value for child in ast.walk(node.test) if isinstance(child, ast.Constant) and isinstance(child.value, str)}
        assert not (({"component_id", "identifier"} & names) and text_constants), ast.unparse(node.test)


def test_all_260_components_pass_semantic_audit_and_structural_contract():
    rows = audit_all()
    assert len(rows) == 260
    assert not [row for row in rows if row.issues]
    valid_energies = {"quiet", "medium", "strong", "heroic"}
    for component in ALL_COMPONENTS.values():
        assert component.id.replace("_", "").isalnum()
        assert component.category in COMPONENT_REGISTRIES
        assert component.profile and component.traits and component.content_zones
        assert 1 <= component.density <= 5
        assert 1 <= component.visual_weight <= 5
        assert component.section_energy in valid_energies
        assert component.mobile_variant
        spec = component.blueprint_spec
        assert spec and spec.schema_version == "component-blueprint-1.1"
        assert spec.layout_model and spec.desktop_spec and spec.mobile_spec
        assert spec.media_spec and spec.content_spec and spec.behavior_spec and spec.fallback_strategy
        assert not (component.required_data & component.required_any_data)
        assert not (component.required_media & component.required_any_media)


def test_all_hero_specs_are_renderer_ready_structural_plans():
    desktop = {"grid_columns", "content_span", "media_span", "desktop_order", "min_height_behavior", "section_padding_behavior", "overlap_behavior"}
    mobile = {"mobile_order", "media_behavior", "title_behavior", "min_height_behavior"}
    media = {"media_layout", "media_count_min", "media_count_max", "preferred_orientations", "image_crop_behavior", "media_span", "overlay_behavior", "background_behavior", "supports_no_media", "supports_stock_media", "supports_artisan_media"}
    content = {"title_position", "cta_position", "supporting_copy_position", "eyebrow_position", "max_title_width_ch", "title_scale"}
    for hero in COMPONENT_REGISTRIES["hero"].values():
        spec = hero.blueprint_spec
        assert desktop <= set(spec.desktop_spec), hero.id
        assert mobile <= set(spec.mobile_spec), hero.id
        assert media <= set(spec.media_spec), hero.id
        assert content <= set(spec.content_spec), hero.id
        assert "motion_capabilities" in spec.behavior_spec


@pytest.mark.parametrize("component_id", ("horizontal_rail_preview", "floating_image_statement", "centered_statement_quiet", "architectural_void_statement"))
def test_known_substring_regressions_do_not_create_false_requirements(component_id):
    component = ALL_COMPONENTS[component_id]
    assert "reviews" not in component.required_data
    assert "statistics" not in component.required_data


@pytest.mark.parametrize("component_id", ("no_image_typographic_signal", "no_image_editorial_manifesto", "no_image_local_conversion"))
def test_known_no_image_heroes_really_support_zero_media(component_id):
    component = ALL_COMPONENTS[component_id]
    assert not component.required_media and not component.required_any_media
    assert component.image_dependency == 0
    assert component.blueprint_spec.media_spec["supports_no_media"] is True


def test_color_systems_cover_all_required_accessible_pairs_and_are_individualized():
    canvas_alternates = set()
    surfaces = set()
    for color in COLOR_SYSTEMS.values():
        tokens = color.tokens
        canvas_alternates.add(tokens["canvas_alt"])
        surfaces.add(tokens["surface"])
        pairs = (
            ("text_primary", "canvas", 4.5), ("text_secondary", "canvas", 4.5),
            ("text_muted", "canvas", 4.5), ("text_inverse", "surface_inverse", 4.5),
            ("brand_text", "brand", 4.5), ("brand_hover_text", "brand_hover", 4.5),
            ("brand_active_text", "brand_active", 4.5), ("focus", "canvas", 3.0),
        )
        for foreground, background, minimum in pairs:
            assert contrast_ratio(tokens[foreground], tokens[background]) >= minimum, (color.id, foreground, background)
        assert color.material_inspiration and color.bad_combinations
    assert len(canvas_alternates) >= 30
    assert len(surfaces) >= 30


def test_typography_systems_are_portable_and_structurally_distinct():
    scales = set()
    for typography in TYPOGRAPHY_SYSTEMS.values():
        scales.add(typography.size_scale)
        assert typography.readability_score >= .8
        assert typography.hero_size_range[0] < typography.hero_size_range[1]
        assert 0.5 <= typography.mobile_scale <= .85
        assert typography.fallback_stack
        assert typography.availability in {"system_safe", "platform_limited", "webfont_required"}
        assert typography.max_font_count <= 3
        assert typography.letter_spacing_scale == (0.0,)
    assert len(scales) >= 20


def test_structured_foundations_avoid_nested_card_geometry():
    assert len(SPACING_SYSTEMS) == 5 and len(GEOMETRY_SYSTEMS) == 5
    assert all(item.section_padding[0] > item.component_gap > item.text_gap for item in SPACING_SYSTEMS.values())
    assert all("nested" not in item.card_shape or "no_nested" in item.card_shape for item in GEOMETRY_SYSTEMS.values())


def test_component_pair_golden_cases_are_explainable():
    editorial = component_pair_affinity(ALL_COMPONENTS["editorial_photo_collage"], ALL_COMPONENTS["editorial_service_rows"], frozenset({"editorial"}))
    cinematic_dense = component_pair_affinity(ALL_COMPONENTS["cinematic_overlay_story"], ALL_COMPONENTS["service_bento"])
    emergency = component_pair_affinity(ALL_COMPONENTS["phone_first_problem_solution"], ALL_COMPONENTS["conversion_service_selector"], frozenset({"conversion_led"}))
    quiet_bold = component_pair_affinity(ALL_COMPONENTS["centered_statement_quiet"], ALL_COMPONENTS["cinematic_service_reveal"], frozenset({"quiet"}))
    assert editorial.score >= .85
    assert cinematic_dense.score <= .35
    assert emergency.score >= .85
    assert quiet_bold.score <= .35
    assert cinematic_dense.reasons and quiet_bold.reasons


def test_sequence_affinity_penalizes_repeated_heavy_energy():
    strong = tuple(ALL_COMPONENTS[item] for item in ("full_bleed_photo_cover", "cinematic_service_reveal", "full_bleed_image_sequence"))
    varied = tuple(ALL_COMPONENTS[item] for item in ("centered_statement_quiet", "quiet_service_chapters", "documented_process_proof"))
    assert sequence_affinity(strong).score < sequence_affinity(varied).score


def test_structured_truth_requirements_and_media_wording_are_authoritative():
    assert not can_render_claim("insurance", {})
    assert can_render_claim("insurance", {"insurance": "verified"})
    assert not can_render_claim("emergency_service", {"emergency_service": False})
    assert can_render_claim("emergency_service", {"emergency_service": True})
    assert not can_use_media_wording("stock", "stock_photo", "selected_project")
    assert can_use_media_wording("artisan", "artisan_project", "selected_project")


def test_decision_trace_explains_selection_and_rejections():
    source = design_input(seed="trace")
    genome = DesignGenome(candidate_count=40)
    first = genome.generate_with_trace(source)
    second = genome.generate_with_trace(source, (first.dna,))
    assert {item.field for item in first.trace.decisions} >= {"site_archetype", "hero_component", "color_system", "page_silhouette"}
    assert all(item.reasons for item in first.trace.decisions)
    assert second.trace.attempts > 1
    assert second.trace.similarity_rejections >= 1
    assert any(item["reason"] == "similarity" for item in second.trace.rejected_candidates)


def test_design_signature_uses_visual_dimensions_only():
    dna = generate_site_dna(design_input(seed="signature"))
    non_visual_change = replace(dna, seed="different-non-visual-seed")
    assert SiteDNA.signature_for(non_visual_change.to_dict()) == dna.design_signature
    other_color = next(color for color in COLOR_SYSTEMS if color != dna.color_system)
    visual_change = replace(dna, color_system=other_color)
    assert SiteDNA.signature_for(visual_change.to_dict()) != dna.design_signature


def test_machine_export_is_versioned_and_contains_resolved_blueprints():
    payload = json.loads((REPO_ROOT / "docs" / "design-encyclopedia" / "encyclopedia.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.1"
    assert sum(payload["counts"].values()) == 260
    assert payload["registries"]["hero"]["editorial_photo_collage"]["blueprint_spec"]["layout_model"]
    assert payload["systems"]["spacing"] and payload["compatibility"]["trait_pair_affinity"]


def test_deep_research_and_sample_outputs_preserve_inspection_boundaries():
    docs = REPO_ROOT / "docs" / "design-encyclopedia"
    gold = (docs / "gold-standards.md").read_text(encoding="utf-8")
    assert gold.count("**MOBILE OBSERVATIONS:** mobile not inspected.") == 30
    assert len(list((docs / "sample-dna").glob("plombier-*.md"))) == 10
    assert len([path for path in (docs / "sample-dna").glob("*.md") if path.name != "README.md"]) == 30
    status = json.loads((docs / "deep-reference-status.json").read_text(encoding="utf-8"))
    assert status["counts"]["total"] == 20
    assert all(not item["visual_inspected"] and not item["mobile_inspected"] for item in status["references"])


def test_committed_simulation_uses_public_pipeline_and_records_required_cohorts():
    payload = json.loads((REPO_ROOT / "docs" / "design-encyclopedia" / "genome-simulation.json").read_text(encoding="utf-8"))
    assert payload["pipeline"].startswith("DesignGenome.generate ")
    assert payload["main_simulation"]["generated"] == 10_000
    assert payload["main_simulation"]["failed"] == 0
    assert payload["plumber_100"]["unique_signatures"] == 100
    assert payload["same_input_plumber_50"]["unique_signatures"] == 50
