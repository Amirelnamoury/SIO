"""Semantic section renderers driven by component blueprints."""

from __future__ import annotations

import html
from datetime import date

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition

from .context import RenderContext, RenderMedia, safe_url
from .families import render_hero_family, render_services_family
from .media_plan import HeroResolution
from .primitives import actions_html, component_attributes, image, layout_regions


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


def render_header(ctx: RenderContext) -> str:
    component = _component(ctx.dna.header_component)
    links = _nav_links(ctx.dna.section_order)
    midpoint = (len(links) + 1) // 2

    def nav(values: list[tuple[str, str]], label: str) -> str:
        body = "".join(f'<a href="#{name}">{text}</a>' for name, text in values)
        return f'<nav class="header-nav" aria-label="{label}">{body}</nav>' if body else ""

    action = ""
    if ctx.phone_href:
        action = f'<a class="header-action" href="tel:{ctx.phone_href}">{ctx.text("telephone")}</a>'
    elif ctx.plain("email"):
        action = f'<a class="header-action" href="mailto:{ctx.text("email")}">Écrire</a>'
    elif ctx.plain("slug") and (ctx.dna.contact_component or ctx.dna.form_component):
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


def render_hero(ctx: RenderContext) -> str:
    resolution = ctx.hero_resolution
    if resolution is None:
        # Defensive path for direct calls that skip resolved_for_rendering()
        # (e.g. a unit test rendering a bare context). Production rendering
        # always goes through render_site_genome, which resolves first.
        component = _component(ctx.dna.hero_component)
        declared_max = component.blueprint_spec.media_spec.get("media_count_max", 1)
        media = ctx.media_for(component, limit=declared_max)
        resolution = HeroResolution(
            media, "media" if media else "abstract_fallback",
            "direct render_hero call without a resolved plan", component,
        )

    family_rendered = render_hero_family(ctx, resolution)
    if family_rendered is not None:
        return family_rendered

    component = resolution.component
    media = resolution.media
    visuals = "".join(image(item, f"Ambiance {ctx.trade_label.lower()}", eager=index == 0, class_name="hero-image") for index, item in enumerate(media))
    location = f'<span class="hero-location">{ctx.location}</span>' if ctx.location else ""
    tagline = f'<p class="hero-lead">{ctx.text("tagline")}</p>' if ctx.plain("tagline") else ""
    copy = f'<p class="eyebrow">{ctx.trade_label}{location}</p><h1>{ctx.business_name}</h1>{tagline}{actions_html(ctx)}'
    fallback = '<div class="graphic-fallback" aria-hidden="true"><span></span><span></span><i></i></div>'
    body = layout_regions(component, copy, visuals or fallback)
    return f'<section id="accueil" class="section hero" {component_attributes(component)} data-hero-mode="{html.escape(resolution.mode, quote=True)}">{body}</section>'


def render_services(ctx: RenderContext) -> str:
    component = _component(ctx.dna.services_component)
    services = ctx.list("services")
    if not component or not services:
        return ""
    return render_services_family(ctx, component, services)


def render_gallery(ctx: RenderContext) -> str:
    component = _component(ctx.dna.gallery_component)
    if not component:
        return ""
    values = ctx.media_for_section("gallery", component, limit=12)
    if not values:
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


def render_about(ctx: RenderContext) -> str:
    component = _component(ctx.dna.about_component)
    if not component:
        return ""
    narrative = ctx.plain("about") or ctx.plain("tagline")
    facts = []
    if ctx.location:
        facts.append(f'<li><span>Implantation</span><strong>{ctx.location}</strong></li>')
    if ctx.plain("assurance_decennale_nom"):
        facts.append(f'<li><span>Assurance déclarée</span><strong>{ctx.text("assurance_decennale_nom")}</strong></li>')
    if not narrative and not facts:
        return ""

    if narrative and ctx.is_duplicate_copy(narrative):
        # The only "narrative" available is a verbatim repeat of copy the
        # hero already showed (rule Z/AA): a second identical paragraph adds
        # nothing, so this reduces to a compact identity strip -- real facts
        # only, no invented replacement copy -- rather than a large, mostly
        # empty section repeating the same sentence.
        if not facts:
            return ""
        copy = (
            f'<div class="section-heading section-heading--micro"><p class="eyebrow">L’entreprise</p>'
            f'<h2>{ctx.business_name}</h2></div><ul class="fact-list fact-list--micro">{"".join(facts)}</ul>'
        )
        return f'<section id="about" class="section about about--micro" {component_attributes(component)}>{copy}</section>'

    text = f'<p>{html.escape(narrative, quote=True)}</p>' if narrative else ""
    copy = f'<div class="section-heading"><p class="eyebrow">L’entreprise</p><h2>{ctx.business_name}</h2></div>{text}<ul class="fact-list">{"".join(facts)}</ul>'
    media_relationship = component.blueprint_spec.media_spec.get("relationship")
    values = () if media_relationship == "none" else ctx.media_for_section("about", component, limit=2)
    visuals = "".join(image(item, "Ambiance de travail", class_name="about-image") for item in values)
    return f'<section id="about" class="section about" {component_attributes(component)}>{layout_regions(component, copy, visuals)}</section>'


def _trust_items(ctx: RenderContext, component: ComponentDefinition) -> tuple[str, ...]:
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


def render_trust(ctx: RenderContext) -> str:
    component = _component(ctx.dna.trust_component)
    if not component:
        return ""
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


def render_cta(ctx: RenderContext) -> str:
    component = _component(ctx.dna.cta_component)
    if not component:
        return ""
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


def render_contact(ctx: RenderContext) -> str:
    component = _component(ctx.dna.contact_component) or _component(ctx.dna.form_component)
    if not component:
        # No contact/form component was assigned -- typically because the
        # Design Genome never saw a verified phone or email to build a
        # contact blueprint around. That is not the same as the real quote
        # contract being unavailable: when a slug exists, the existing
        # /pub/{slug}/demande-devis endpoint (rule AE) is real and working,
        # and a page left with no conversion path anywhere is a worse,
        # silent failure than one honest, minimal quote-only section.
        if not ctx.plain("slug"):
            return ""
        form = _form(ctx)
        if not form:
            return ""
        copy = '<div class="section-heading"><p class="eyebrow">Contact</p><h2>Commençons par en parler.</h2></div>'
        return (
            '<section id="contact" class="section contact contact--form-only" '
            'data-component="generic_quote_form" data-family="contact.generic" data-fallback="no-contact-component-assigned">'
            f'<div class="g-layout g-layout--stack g-layout--no-media"><div class="g-copy">{copy}{form}</div></div></section>'
        )
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


def render_footer(ctx: RenderContext) -> str:
    component = _component(ctx.dna.footer_component)
    links = "".join(f'<a href="#{name}">{label}</a>' for name, label in _nav_links(ctx.dna.section_order))
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
