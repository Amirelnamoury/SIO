"""Family- and component-specific realizations (V0.2).

V0.1 had exactly one renderer per section category (``render_hero``,
``render_services``, ...). Every family and variant funnelled through the
same markup, and only ``layout_regions``' choice of wrapper shape plus a
handful of CSS attribute selectors ever changed -- so ``service_bento``,
``conversion_service_selector`` and ``editorial_service_folio`` all emitted
the identical ``<ol class="service-list">01/02/03</ol>``. A component being
technically reachable (its id makes it into the DOM as a data attribute) is
not the same as its visual promise being realized; this module is where that
promise gets a real, distinct mechanism.

Scope, deliberately: the components and families actually used by the 12 lab
fixtures come first (rule AM of the brief). Nothing here inspects a fixture
id or trade; every dispatch key is a component id or a family id already
present in ``design_genome`` -- the same component, wherever it is chosen for
any artisan, gets the same treatment.
"""

from __future__ import annotations

import html

from .context import RenderContext, RenderMedia
from .media_plan import HeroResolution
from .primitives import actions_html, component_attributes, image


# ---------------------------------------------------------------------------
# Hero: typographic no-image compositions (rule X/Y)
# ---------------------------------------------------------------------------
#
# Every no-image hero used to collapse into one generic split/typographic
# wrapper. Real no-image identities differ a lot in intent (a manifesto reads
# nothing like a brutalist block); the variant id already encodes which one
# was meant, so a small explicit dispatch table -- not a guess from a hash or
# a fixture id -- is enough to make each one distinct.

def _hero_copy_parts(ctx: RenderContext) -> dict[str, str]:
    return {
        "eyebrow": ctx.trade_label,
        "location": ctx.location,
        "name": ctx.business_name,
        "tagline": ctx.text("tagline") if ctx.plain("tagline") else "",
        "actions": actions_html(ctx),
    }


def _typographic_oversized(parts: dict[str, str]) -> str:
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--oversized"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1 class="hero-type-statement">{parts["name"]}</h1>{tagline}{parts["actions"]}</div>'
    )


def _typographic_quiet_centered(parts: dict[str, str]) -> str:
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--quiet"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1>{parts["name"]}</h1>{tagline}{parts["actions"]}</div>'
    )


def _typographic_manifesto_columns(parts: dict[str, str]) -> str:
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead hero-manifesto-column">{parts["tagline"]}</p>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--manifesto"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1>{parts["name"]}</h1><div class="hero-manifesto-columns">{tagline}</div>{parts["actions"]}</div>'
    )


def _typographic_editorial_index(ctx: RenderContext, parts: dict[str, str]) -> str:
    services = ctx.list("services")[:4]
    index = "".join(
        f'<li><span class="hero-index-mark">{index_no:02d}</span>{html.escape(str(value), quote=True)}</li>'
        for index_no, value in enumerate(services, 1)
    )
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    index_html = f'<ol class="hero-editorial-index">{index}</ol>' if index else ""
    return (
        f'<div class="hero-type hero-type--editorial-index"><div class="hero-editorial-main">'
        f'<p class="eyebrow">{parts["eyebrow"]}{location}</p><h1>{parts["name"]}</h1>{tagline}{parts["actions"]}</div>'
        f'{index_html}</div>'
    )


def _typographic_architectural_void(parts: dict[str, str]) -> str:
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--void"><div class="hero-void-mark" aria-hidden="true"></div>'
        f'<div class="hero-void-copy"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1>{parts["name"]}</h1>{tagline}{parts["actions"]}</div></div>'
    )


def _typographic_brutalist_block(parts: dict[str, str]) -> str:
    location = f'<div class="hero-block">{parts["location"]}</div>' if parts["location"] else ""
    tagline = f'<div class="hero-block hero-block--lead">{parts["tagline"]}</div>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--brutalist"><div class="hero-block hero-block--eyebrow">{parts["eyebrow"]}</div>'
        f'<div class="hero-block hero-block--title"><h1>{parts["name"]}</h1></div>{tagline}{location}'
        f'<div class="hero-block hero-block--actions">{parts["actions"]}</div></div>'
    )


def _typographic_local_conversion(parts: dict[str, str]) -> str:
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    return (
        f'<div class="hero-type hero-type--local-conversion"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1>{parts["name"]}</h1>{tagline}<div class="hero-conversion-dock">{parts["actions"]}</div></div>'
    )


_TYPOGRAPHIC_TREATMENTS: dict[str, str] = {
    "oversized_type_local": "oversized",
    "no_image_typographic_signal": "oversized",
    "centered_statement_quiet": "quiet",
    "editorial_columns_manifesto": "manifesto",
    "no_image_editorial_manifesto": "manifesto",
    "editorial_title_index": "editorial_index",
    "architectural_void_statement": "void",
    "brutalist_block_intro": "brutalist",
    "no_image_local_conversion": "local_conversion",
}


def render_typographic_hero(ctx: RenderContext, component, mode_reason: str) -> str:
    parts = _hero_copy_parts(ctx)
    treatment = _TYPOGRAPHIC_TREATMENTS.get(component.id)
    if treatment is None:
        # Recomposition landed on a family other than typographic (technical/
        # conversion/spatial no-image variants) -- a quiet centered statement
        # is the safe, honest default rather than guessing a treatment for a
        # family this module does not otherwise specialize.
        treatment = "quiet"
    body = {
        "oversized": _typographic_oversized,
        "quiet": _typographic_quiet_centered,
        "manifesto": _typographic_manifesto_columns,
        "void": _typographic_architectural_void,
        "brutalist": _typographic_brutalist_block,
        "local_conversion": _typographic_local_conversion,
    }.get(treatment)
    inner = _typographic_editorial_index(ctx, parts) if treatment == "editorial_index" else body(parts)
    return (
        f'<section id="accueil" class="section hero hero--no-image" '
        f'{component_attributes(component)} data-hero-mode="{html.escape(mode_reason, quote=True)}">{inner}</section>'
    )


# ---------------------------------------------------------------------------
# Hero: material macro (rule W) and technical nodes network (rule R)
# ---------------------------------------------------------------------------

def render_material_hero(ctx: RenderContext, component, media: tuple[RenderMedia, ...]) -> str:
    parts = _hero_copy_parts(ctx)
    location = f' <span class="hero-location">{parts["location"]}</span>' if parts["location"] else ""
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    macro = "".join(image(item, f"Matière et geste — {ctx.trade_label.lower()}", eager=True, class_name="hero-material-macro") for item in media[:1])
    return (
        f'<section id="accueil" class="section hero hero--material" {component_attributes(component)}>'
        f'<div class="g-material-hero"><figure class="g-material-frame">{macro}</figure>'
        f'<div class="g-material-copy"><p class="eyebrow">{parts["eyebrow"]}{location}</p>'
        f'<h1>{parts["name"]}</h1>{tagline}{parts["actions"]}</div></div></section>'
    )


def render_technical_network_hero(ctx: RenderContext, component) -> str:
    parts = _hero_copy_parts(ctx)
    services = ctx.list("services")[:5]
    nodes = "".join(
        f'<li class="network-node"><span class="network-connector" aria-hidden="true"></span>'
        f'<span class="network-label">{html.escape(str(value), quote=True)}</span></li>'
        for value in services
    )
    hub = html.escape(ctx.plain("nom_entreprise") or ctx.trade_label, quote=True)
    tagline = f'<p class="hero-lead">{parts["tagline"]}</p>' if parts["tagline"] else ""
    diagram = (
        f'<div class="hero-network" role="img" aria-label="Schéma des prestations reliées à {hub}">'
        f'<div class="network-hub">{hub}</div><ul class="network-nodes">{nodes}</ul></div>'
        if nodes else ""
    )
    layout_class = "hero-network-layout" if diagram else "hero-network-layout hero-network-layout--no-nodes"
    return (
        f'<section id="accueil" class="section hero hero--technical-network" {component_attributes(component)}>'
        f'<div class="{layout_class}"><div class="g-copy"><p class="eyebrow">{parts["eyebrow"]}</p>'
        f'<h1>{parts["name"]}</h1>{tagline}{parts["actions"]}</div>{diagram}</div></section>'
    )


def render_hero_family(ctx: RenderContext, resolution: HeroResolution) -> str:
    component = resolution.component
    if resolution.mode in {"no_image_intentional", "recomposed"}:
        return render_typographic_hero(ctx, component, resolution.reason)
    if resolution.mode == "media" and component.id == "technical_nodes_network":
        return render_technical_network_hero(ctx, component)
    if resolution.mode == "media" and component.family_id == "hero.material":
        return render_material_hero(ctx, component, resolution.media)
    return None  # signals the caller to use the generic hero renderer


# ---------------------------------------------------------------------------
# Services: family + named-component realizations (rules N, O, P, Q, R)
# ---------------------------------------------------------------------------

def _service_items(services: tuple[str, ...]) -> list[str]:
    return [html.escape(str(value), quote=True) for value in services]


def render_services_bento(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """A real bento: unequal spans and an explicit primary module.

    Not ``01 / 02 / 03`` in a uniform grid -- the first service is the
    dominant module (larger span, larger type), the rest fill progressively
    smaller modules so the grid reads as a hierarchy, not a list.
    """
    items = _service_items(services)
    tiles = []
    for index, label in enumerate(items):
        if index == 0:
            span = "bento-primary"
        elif index == 1:
            span = "bento-tall"
        else:
            span = "bento-standard"
        tiles.append(
            f'<li class="bento-tile {span}"><span class="service-index">{index + 1:02d}</span>'
            f'<h3>{label}</h3></li>'
        )
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--bento" {component_attributes(component)}>'
        f'{copy}<ul class="service-bento-grid">{"".join(tiles)}</ul></section>'
    )


def render_services_folio(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Editorial folio: large offset numbers, rules, alternating measure."""
    items = _service_items(services)
    rows = []
    for index, label in enumerate(items, 1):
        align = "folio-row--offset" if index % 2 == 0 else ""
        rows.append(
            f'<li class="folio-row {align}"><span class="folio-number">{index:02d}</span>'
            f'<h3 class="folio-title">{label}</h3></li>'
        )
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--folio" {component_attributes(component)}>'
        f'{copy}<ol class="service-folio">{"".join(rows)}</ol></section>'
    )


def render_services_selector(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """A selection interface: one dominant service, others as real actions.

    ``conversion_service_selector`` and ``problem_solution_services`` share
    this family concept (turn the service list into the first conversion
    step) but read differently: the selector favours one featured card, the
    problem/solution variant favours a scannable ledger. Both link every
    entry to the real quote path -- never a decorative, unclickable list.
    """
    items = _service_items(services)
    # Mirrors render_site_genome's actual contact-section guarantee exactly
    # (a real slug always gets a #contact section, with or without a
    # DNA-assigned contact/form component -- see render_contact's fallback):
    # gating on contact_component/form_component alone under-detected this
    # and silently dropped every "Demander un devis" link for artisans with
    # no verified phone/email yet, which is most of the lab fixtures.
    has_action = bool(ctx.plain("slug"))
    href = "#contact" if has_action else None
    copy = '<div class="section-heading"><p class="eyebrow">Votre projet</p><h2>Choisissez une prestation</h2></div>'
    if component.id == "problem_solution_services":
        rows = []
        for index, label in enumerate(items, 1):
            action = f'<a class="selector-action" href="{href}">Demander un devis</a>' if href else ""
            rows.append(
                f'<li class="selector-row"><span class="service-index">{index:02d}</span>'
                f'<span class="selector-label">{label}</span>{action}</li>'
            )
        return (
            f'<section id="services" class="section services services--selector services--ledger" {component_attributes(component)}>'
            f'{copy}<ul class="service-selector-ledger">{"".join(rows)}</ul></section>'
        )
    cards = []
    for index, label in enumerate(items):
        featured = index == 0
        role = "selector-card--primary" if featured else "selector-card--secondary"
        action = f'<a class="selector-action" href="{href}">Demander un devis</a>' if href else ""
        cards.append(
            f'<li class="selector-card {role}"><span class="service-index">{index + 1:02d}</span>'
            f'<h3>{label}</h3>{action}</li>'
        )
    return (
        f'<section id="services" class="section services services--selector" {component_attributes(component)}>'
        f'{copy}<ul class="service-selector-grid">{"".join(cards)}</ul></section>'
    )


def render_services_material(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Workshop/material samples: framing and tokens, never invented projects."""
    items = _service_items(services)
    samples = "".join(
        f'<li class="material-sample"><span class="sample-tag">Éch. {index:02d}</span>'
        f'<h3>{label}</h3><span class="sample-swatch" aria-hidden="true"></span></li>'
        for index, label in enumerate(items, 1)
    )
    copy = '<div class="section-heading"><p class="eyebrow">Matière &amp; savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--material" {component_attributes(component)}>'
        f'{copy}<ul class="service-material-samples">{samples}</ul></section>'
    )


def render_services_index(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Typographic index: the service name is the dominant type element."""
    items = _service_items(services)
    rows = "".join(
        f'<li class="index-row"><span class="index-number">{index:02d}</span>'
        f'<span class="index-label">{label}</span></li>'
        for index, label in enumerate(items, 1)
    )
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--index" {component_attributes(component)}>'
        f'{copy}<ol class="service-index-list">{rows}</ol></section>'
    )


def render_services_minimal(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Deliberately quiet: a list of links, no numbering, no cards."""
    items = _service_items(services)
    links = "".join(f'<li><a href="#contact">{label}</a></li>' for label in items) if ctx.plain("slug") else "".join(f'<li>{label}</li>' for label in items)
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--minimal" {component_attributes(component)}>'
        f'{copy}<ul class="service-quiet-list">{links}</ul></section>'
    )


def render_services_grid(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Equal modules -- deliberately uniform, the counterpoint to bento."""
    items = _service_items(services)
    tiles = "".join(
        f'<li class="grid-tile"><span class="service-index">{index:02d}</span><h3>{label}</h3></li>'
        for index, label in enumerate(items, 1)
    )
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--grid" {component_attributes(component)}>'
        f'{copy}<ul class="service-equal-grid">{tiles}</ul></section>'
    )


def render_services_rows(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    """Editorial rows: the safe, still-improved default for unaudited families."""
    items = _service_items(services)
    rows = "".join(
        f'<li class="service-row"><span class="service-index">{index:02d}</span><h3>{label}</h3></li>'
        for index, label in enumerate(items, 1)
    )
    copy = '<div class="section-heading"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div>'
    return (
        f'<section id="services" class="section services services--rows" {component_attributes(component)}>'
        f'{copy}<ol class="service-row-list">{rows}</ol></section>'
    )


def render_services_family(ctx: RenderContext, component, services: tuple[str, ...]) -> str:
    if component.id == "service_bento":
        return render_services_bento(ctx, component, services)
    if component.id == "editorial_service_folio":
        return render_services_folio(ctx, component, services)
    if component.id in {"conversion_service_selector", "problem_solution_services"}:
        return render_services_selector(ctx, component, services)
    if component.id in {"workshop_service_samples", "material_service_catalogue", "project_type_services"}:
        return render_services_material(ctx, component, services)
    if component.family_id == "services.index":
        return render_services_index(ctx, component, services)
    if component.family_id == "services.minimal":
        return render_services_minimal(ctx, component, services)
    if component.family_id in {"services.grid", "services.photo"}:
        return render_services_grid(ctx, component, services)
    return render_services_rows(ctx, component, services)
