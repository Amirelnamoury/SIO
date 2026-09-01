"""Compatibility adapter from the existing Site Vitrine payload contract."""

from __future__ import annotations

from collections.abc import Mapping

from generator.design_genome.generator import DesignGenome
from generator.design_genome.models import DesignInput, MediaInventory, SiteDNA

from .context import RenderContext, media_semantic_role, media_source_class
from .renderer import render_site_genome


def design_input_from_payload(payload: Mapping, *, seed: str | None = None) -> DesignInput:
    selected = tuple(item for item in payload.get("selected_media") or () if isinstance(item, Mapping))
    facts = dict(payload.get("facts") or {})
    for key, source in (("phone", "telephone"), ("email", "email"), ("insurance", "assurance_decennale_nom")):
        if payload.get(source):
            facts.setdefault(key, payload[source])
    if payload.get("process_steps"):
        facts.setdefault("process", tuple(payload["process_steps"]))
    if payload.get("avis"):
        facts.setdefault("reviews", tuple(payload["avis"]))
    if payload.get("stats"):
        facts.setdefault("statistics", tuple(payload["stats"]))
    if payload.get("ville"):
        facts.setdefault("service_areas", (payload["ville"],))
    return DesignInput(
        trade=str(payload.get("metier") or "renovateur"),
        seed=seed or f"site-genome:{payload.get('slug') or payload.get('nom_entreprise') or 'artisan'}",
        city=str(payload.get("ville") or ""),
        business_intent=str(payload.get("business_intent") or "balanced"),
        services=tuple(str(value) for value in payload.get("services") or () if value),
        facts=facts,
        media=MediaInventory(
            artisan_photos=sum(1 for item in selected if media_source_class(item) == "artisan"),
            stock_photos=sum(
                1
                for item in selected
                if media_source_class(item) == "stock"
            ),
            project_photos=sum(
                1 for item in selected
                if media_source_class(item) == "artisan" and media_semantic_role(item) == "artisan_project"
            ),
            before_after_pairs=sum(
                1 for item in selected
                if media_source_class(item) == "artisan" and media_semantic_role(item) == "before_after"
            ) // 2,
            portrait_photos=sum(
                1 for item in selected if media_semantic_role(item) == "portrait"
            ),
            landscape_photos=sum(
                1
                for item in selected
                if media_semantic_role(item) in {"hero", "gallery", "landscape", "artisan_project"}
            ),
            has_logo=bool(payload.get("logo")),
        ),
    )


def render_payload_with_genome(
    payload: Mapping,
    api_base_url: str,
    *,
    site_dna: SiteDNA | Mapping | None = None,
    lab_mode: bool = False,
) -> tuple[str, SiteDNA]:
    if isinstance(site_dna, Mapping):
        site_dna = SiteDNA.from_dict(site_dna)
    dna = site_dna or DesignGenome().generate(design_input_from_payload(payload))
    context = RenderContext.from_payload(payload, dna, api_base_url, lab_mode=lab_mode)
    return render_site_genome(context), dna
