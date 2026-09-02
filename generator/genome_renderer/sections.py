"""Section renderers that materialize an already-resolved ``SectionPlan``.

V0.2.1: these functions no longer make structural decisions (renderability,
duplicate-copy handling, which media to show, hero recomposition, the
contact fallback). All of that is decided exactly once, in
``render_plan.build_render_plan``, walking sections in their real render
order. What is left here is presentation only: given a ``SectionPlan`` that
already says "full narrative" or "reduced fact-strip" or "omitted", turn
that decision -- plus the artisan's raw content (business name, service
names, ...) -- into markup. A few small helpers (``_trust_items``,
``_actions_available``) are pure functions of ``ctx`` with no hidden state;
they are shared verbatim between plan-building and rendering rather than
reimplemented twice, so they cannot drift (see the V0.2.1 doc, "no double
logic").
"""

from __future__ import annotations

import html
from datetime import date
from typing import TYPE_CHECKING

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition

from .context import RenderContext, safe_url
from .families import render_hero_family, render_services_family
from .primitives import actions_html, component_attributes, image, layout_regions

if TYPE_CHECKING:
    from .render_plan import SectionPlan


SECTION_LABELS = {
    "services": "Prestations",
    "gallery": "Images",
    "about": "À propos",
    "trust": "Repères",
    "cta": "Votre projet",
    "contact": "Contact",
}


def _component(component_id: str | None) -> ComponentDefinition | None:
    return ALL_COMPONENTS.get(component_id or "")


def _brand(ctx: RenderContext) -> str:
    logo = ctx.logo()
    visual = image(logo, f"Logo {ctx.plain('nom_entreprise')}", eager=True, class_name="brand-logo") if logo else ctx.business_name
    return f'<a class="brand" href="#accueil" aria-label="Accueil — {ctx.business_name}">{visual}</a>'


def _nav_links(order: tuple[str, ...]) -> list[tuple[str, str]]:
    return [(name, SECTION_LABELS[name]) for name in order if name in SECTION_LABELS]


def _actions_available(ctx: RenderContext) -> bool:
    """Pure predicate, no state -- shared as-is by plan-building and rendering."""
    return bool(actions_html(ctx))


def render_header(ctx: RenderContext, rendered_order: tuple[str, ...]) -> str:
    component = _component(ctx.dna.header_component)
    links = _nav_links(rendered_order)
    midpoint = (len(links) + 1) // 2

    def nav(values: list[tuple[str, str]], label: str) -> str:
        body = "".join(f'<a href="#{name}">{text}</a>' for name, text in values)
        return f'<nav class="header-nav" aria-label="{label}">{body}</nav>' if body else ""

    action = ""
    if ctx.phone_href:
        action = f'<a class="header-action" href="tel:{ctx.phone_href}">{ctx.text("telephone")}</a>'
    elif ctx.plain("email"):
        action = f'<a class="header-action" href="mailto:{ctx.text("email")}">Écrire</a>'
    elif "contact" in rendered_order:
        action = '<a class="header-action" href="#contact">Demander un devis</a>'

    spec = component.blueprint_spec
    if spec.desktop_spec.get("alignment_anchor") == "central_baseline":
        inner = f'{nav(links[:midpoint], "Navigation principale gauche")}{_brand(ctx)}{nav(links[midpoint:], "Navigation principale droite")}{action}'
        structure = "split-brand-axis"
    elif "rail" in spec.layout_pattern or "rail" in str(spec.desktop_spec.get("alignment_anchor")):
        inner = f'<div class="header-rail-mark">01</div>{_brand(ctx)}{nav(links, "Navigation principale")}{action}'
        structure = "side-rail"
    elif spec.desktop_spec.get("flow_direction") == "vertical_chapters":
        location = f'<div class="header-utility">{ctx.location}</div>' if ctx.location else ""
        inner = f'{location}<div class="header-main">{_brand(ctx)}{nav(links, "Navigation principale")}{action}</div>'
        structure = "two-row"
    else:
        inner = f'{_brand(ctx)}{nav(links, "Navigation principale")}{action}'
        structure = "linear"
    mobile_links = nav(links, "Navigation mobile")
    mobile = f'<details class="mobile-menu"><summary aria-label="Ouvrir le menu">Menu</summary>{mobile_links}{action}</details>'
    return f'<header class="site-header header-{structure}" {component_attributes(component)}><div class="header-inner">{inner}{mobile}</div></header>'


def render_hero(ctx: RenderContext, plan: "SectionPlan") -> str:
    component = _component(plan.component_id)
    media = ctx.media_by_ids(plan.resolved_media)

    family_rendered = render_hero_family(ctx, component, plan.resolved_mode, media, plan.fallback_reason)
    if family_rendered is not None:
        return family_rendered

    visuals = "".join(image(item, f"Ambiance {ctx.trade_label.lower()}", eager=index == 0, class_name="hero-image") for index, item in enumerate(media))
    location = f'<span class="hero-location">{ctx.location}</span>' if ctx.location else ""
    tagline = f'<p class="hero-lead">{ctx.text("tagline")}</p>' if ctx.plain("tagline") else ""
    copy = f'<p class="eyebrow">{ctx.trade_label}{location}</p><h1>{ctx.business_name}</h1>{tagline}{actions_html(ctx)}'
    fallback = '<div class="graphic-fallback" aria-hidden="true"><span></span><span></span><i></i></div>'
    body = layout_regions(component, copy, visuals or fallback)
    return f'<section id="accueil" class="section hero" {component_attributes(component)} data-hero-mode="{html.escape(plan.resolved_mode, quote=True)}">{body}</section>'


def render_services(ctx: RenderContext, plan: "SectionPlan") -> str:
    component = _component(plan.component_id)
    services = ctx.list("services")
    if plan.renderability == "omitted" or not services:
        return ""
    return render_services_family(ctx, component, services)


def render_gallery(ctx: RenderContext, plan: "SectionPlan") -> str:
    component = _component(plan.component_id)
    values = ctx.media_by_ids(plan.resolved_media)
    if plan.renderability == "omitted" or not values:
        return ""
    project_media = all(item.source_class == "artisan" and item.role in {"artisan_project", "before_after"} for item in values)
    heading = "Réalisations" if project_media else "Inspirations et matières"
    figures = "".join(
        f'<figure class="gallery-item">{image(item, "Image d’ambiance", class_name="gallery-image")}<figcaption>{html.escape(item.alt or item.credit or "Ambiance visuelle", quote=True)}</figcaption></figure>'
        for item in values
    )
    copy = f'<div class="section-heading"><p class="eyebrow">Sélection visuelle</p><h2>{heading}</h2></div>'
    body = layout_regions(component, copy, "", f'<div class="gallery-list">{figures}</div>')
    return f'<section id="gallery" class="section gallery" {component_attributes(component)} data-media-provenance="{"artisan" if project_media else "stock-ambient"}">{body}</section>'


def render_about(ctx: RenderContext, plan: "SectionPlan") -> str:
    if plan.renderability == "omitted":
        return ""
    component = _component(plan.component_id)
    facts = []
    if ctx.location:
        facts.append(f'<li><span>Implantation</span><strong>{ctx.location}</strong></li>')
    if ctx.plain("assurance_decennale_nom"):
        facts.append(f'<li><span>Assurance déclarée</span><strong>{ctx.text("assurance_decennale_nom")}</strong></li>')

    if plan.resolved_mode == "fact_strip":
        # The narrative was a verbatim repeat of copy a higher-priority
        # section already showed (decided once, in build_render_plan) --
        # reduced to a compact identity strip, real facts only.
        copy = (
            f'<div class="section-heading section-heading--micro"><p class="eyebrow">L’entreprise</p>'
            f'<h2>{ctx.business_name}</h2></div><ul class="fact-list fact-list--micro">{"".join(facts)}</ul>'
        )
        return f'<section id="about" class="section about about--micro" {component_attributes(component)}>{copy}</section>'

    narrative = ctx.plain("about") or ctx.plain("tagline")
    text = f'<p>{html.escape(narrative, quote=True)}</p>' if narrative else ""
    copy = f'<div class="section-heading"><p class="eyebrow">L’entreprise</p><h2>{ctx.business_name}</h2></div>{text}<ul class="fact-list">{"".join(facts)}</ul>'
    values = ctx.media_by_ids(plan.resolved_media)
    visuals = "".join(image(item, "Ambiance de travail", class_name="about-image") for item in values)
    return f'<section id="about" class="section about" {component_attributes(component)}>{layout_regions(component, copy, visuals)}</section>'


def _trust_items(ctx: RenderContext, component: ComponentDefinition) -> tuple[str, ...]:
    """Pure function of (ctx, component) -- shared verbatim between
    build_render_plan (to decide renderability) and render_trust (to build
    the markup), so the two cannot disagree."""
    profile = component.profile
    items: list[str] = []
    if profile == "insurance" and ctx.fact("insurance"):
        items.append(f'<li><strong>Assurance</strong><span>{html.escape(str(ctx.fact("insurance")), quote=True)}</span></li>')
    elif profile == "certifications" and ctx.fact("certifications"):
        items.extend(f'<li><strong>Certification</strong><span>{html.escape(str(value), quote=True)}</span></li>' for value in ctx.fact("certifications"))
    elif profile == "reviews" and ctx.fact("reviews"):
        for value in ctx.fact("reviews"):
            if isinstance(value, dict) and value.get("commentaire"):
                author = html.escape(str(value.get("nom_auteur") or "Client identifié"), quote=True)
                items.append(f'<li><blockquote>{html.escape(str(value["commentaire"]), quote=True)}</blockquote><cite>{author}</cite></li>')
    elif profile == "statistics" and ctx.fact("statistics"):
        for value in ctx.fact("statistics"):
            if isinstance(value, dict) and value.get("valeur") and value.get("label"):
                items.append(f'<li><strong>{html.escape(str(value["valeur"]), quote=True)}</strong><span>{html.escape(str(value["label"]), quote=True)}</span></li>')
    elif profile == "area" and ctx.fact("service_areas"):
        items.extend(f'<li><span>{html.escape(str(value), quote=True)}</span></li>' for value in ctx.fact("service_areas"))
    elif profile == "process" and ctx.fact("process"):
        items.extend(f'<li><span>{html.escape(str(value), quote=True)}</span></li>' for value in ctx.fact("process"))
    elif profile == "facts" and ctx.fact("verified_facts"):
        items.extend(f'<li><span>{html.escape(str(value), quote=True)}</span></li>' for value in ctx.fact("verified_facts"))
    return tuple(items)


def render_trust(ctx: RenderContext, plan: "SectionPlan") -> str:
    if plan.renderability == "omitted":
        return ""
    component = _component(plan.component_id)
    items = _trust_items(ctx, component)
    if not items:
        return ""
    if component.profile == "process":
        # A process narrative ("Échange sur le besoin", "Préparation"...) is
        # a workflow, not evidence -- rule AB explicitly forbids labeling it
        # "verified" the way an insurance or certification fact genuinely is.
        heading = '<div class="section-heading"><p class="eyebrow">Notre méthode</p><h2>Déroulé du projet</h2></div>'
    else:
        heading = '<div class="section-heading"><p class="eyebrow">Éléments vérifiés</p><h2>Repères utiles</h2></div>'
    body = layout_regions(component, heading, "", f'<ul class="trust-list">{"".join(items)}</ul>')
    return f'<section id="trust" class="section trust" {component_attributes(component)} data-trust-profile="{html.escape(component.profile, quote=True)}">{body}</section>'


def render_cta(ctx: RenderContext, plan: "SectionPlan") -> str:
    if plan.renderability == "omitted":
        return ""
    component = _component(plan.component_id)
    actions = actions_html(ctx)
    if not actions:
        return ""
    copy = f'<p class="eyebrow">Votre projet</p><h2>Échangeons sur votre besoin.</h2>{actions}'
    return f'<section id="cta" class="section cta" {component_attributes(component)}>{layout_regions(component, copy)}</section>'


def _form(ctx: RenderContext) -> str:
    if not (ctx.dna.form_component or ctx.plain("slug")):
        return ""
    disabled = " disabled" if ctx.lab_mode else ""
    label = "Formulaire désactivé dans le lab" if ctx.lab_mode else "Envoyer la demande"
    synthetic = ' data-synthetic-form="true"' if ctx.lab_mode else ""
    return f'''<form id="devis-form" class="quote-form"{synthetic}>
<label for="client_nom">Nom et prénom *</label><input id="client_nom" autocomplete="name" required{disabled}>
<div class="form-pair"><div><label for="client_telephone">Téléphone</label><input id="client_telephone" type="tel" autocomplete="tel"{disabled}></div><div><label for="client_email">Email</label><input id="client_email" type="email" autocomplete="email"{disabled}></div></div>
<label for="description">Votre projet</label><textarea id="description" rows="5"{disabled}></textarea>
<button id="devis-submit" class="button button-primary" type="submit"{disabled}>{label}</button><div id="form-message" class="form-message" role="status" aria-live="polite"></div>
</form>'''


def render_contact(ctx: RenderContext, plan: "SectionPlan") -> str:
    if plan.renderability == "omitted":
        return ""
    if plan.resolved_mode == "form_only":
        # No contact/form component was assigned -- typically because the
        # Design Genome never saw a verified phone or email to build a
        # contact blueprint around. That is not the same as the real quote
        # contract being unavailable: a real slug means /pub/{slug}/demande-devis
        # (rule AE) is real and working, and a page left with no conversion
        # path anywhere is a worse, silent failure than one honest,
        # minimal quote-only section. Decided once in build_render_plan.
        form = _form(ctx)
        if not form:
            return ""
        copy = '<div class="section-heading"><p class="eyebrow">Contact</p><h2>Commençons par en parler.</h2></div>'
        return (
            '<section id="contact" class="section contact contact--form-only" '
            'data-component="generic_quote_form" data-family="contact.generic" data-fallback="no-contact-component-assigned">'
            f'<div class="g-layout g-layout--stack g-layout--no-media"><div class="g-copy">{copy}{form}</div></div></section>'
        )
    component = _component(plan.component_id)
    channels = []
    if ctx.phone_href:
        channels.append(f'<a href="tel:{ctx.phone_href}"><span>Téléphone</span><strong>{ctx.text("telephone")}</strong></a>')
    if ctx.plain("email"):
        channels.append(f'<a href="mailto:{ctx.text("email")}"><span>Email</span><strong>{ctx.text("email")}</strong></a>')
    if ctx.plain("adresse"):
        channels.append(f'<div><span>Adresse</span><strong>{ctx.text("adresse")}</strong></div>')
    form = _form(ctx)
    if not channels and not form:
        return ""
    copy = f'<div class="section-heading"><p class="eyebrow">Contact</p><h2>Commençons par en parler.</h2></div><div class="contact-channels">{"".join(channels)}</div>'
    body = layout_regions(component, copy, "", form)
    return f'<section id="contact" class="section contact" {component_attributes(component)}>{body}</section>'


def render_footer(ctx: RenderContext, rendered_order: tuple[str, ...]) -> str:
    component = _component(ctx.dna.footer_component)
    links = "".join(f'<a href="#{name}">{label}</a>' for name, label in _nav_links(rendered_order))
    legal = []
    if ctx.plain("siret"):
        legal.append(f'<span>SIRET {ctx.text("siret")}</span>')
    if ctx.plain("assurance_decennale_nom"):
        legal.append(f'<span>Assurance : {ctx.text("assurance_decennale_nom")}</span>')
    credits = []
    seen = set()
    for item in ctx.media:
        key = (item.credit, item.source_url)
        if not item.credit or key in seen:
            continue
        seen.add(key)
        source_url = safe_url(item.source_url)
        credits.append(f'<a href="{source_url}" rel="noopener noreferrer">{html.escape(item.credit, quote=True)}</a>' if source_url else f'<span>{html.escape(item.credit, quote=True)}</span>')
    return f'''<footer class="site-footer" {component_attributes(component)}>
<div class="footer-main">{_brand(ctx)}<nav aria-label="Navigation de pied de page">{links}</nav></div>
<div class="footer-meta">{"".join(legal)}<div class="media-credits">{"".join(credits)}</div><span>© {date.today().year}</span></div>
</footer>'''


SECTION_RENDERERS = {
    "hero": render_hero,
    "services": render_services,
    "gallery": render_gallery,
    "about": render_about,
    "trust": render_trust,
    "cta": render_cta,
    "contact": render_contact,
}
