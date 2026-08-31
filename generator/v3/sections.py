"""Structural section systems for V3 sites."""

from __future__ import annotations

import html
from datetime import date

from .context import SiteContext


def image(ctx: SiteContext, item: dict, alt: str, *, eager: bool = False, class_name: str = "") -> str:
    loading = "eager" if eager else "lazy"
    priority = ' fetchpriority="high"' if eager else ""
    return (
        f'<img class="{class_name}" src="{item["content_url"]}" alt="{ctx.image_alt(item, alt)}"'
        f'{ctx.media_dimensions(item)} loading="{loading}" decoding="async"{priority}>'
    )


def brand(ctx: SiteContext) -> str:
    if ctx.logo:
        return f'<a class="brand brand-logo" href="#accueil">{image(ctx, ctx.logo, f"Logo {ctx.plain["nom_entreprise"]}", eager=True)}</a>'
    return f'<a class="brand brand-type" href="#accueil">{ctx.business_name}</a>'


def nav(ctx: SiteContext, sections: list[str]) -> str:
    labels = {"services": "Prestations", "gallery": "Réalisations", "about": "Atelier", "reviews": "Avis", "contact": "Contact"}
    return "".join(f'<a href="#{key}">{label}</a>' for key, label in labels.items() if key in sections)


def render_header(ctx: SiteContext, sections: list[str]) -> str:
    system = ctx.profile["header_system"]
    links = nav(ctx, sections)
    phone = f'<a class="header-phone" href="tel:{ctx.phone_href}">{ctx.text("telephone")}</a>' if ctx.phone_href else ""
    cta = '<a class="header-cta" href="#devis">Demander un devis</a>'
    menu = f'<details class="mobile-menu"><summary aria-label="Ouvrir le menu">Menu</summary><nav>{links}{phone}{cta}</nav></details>'
    if system == "editorial_index":
        body = f'<span class="edition">Édition locale</span>{brand(ctx)}<nav>{links}</nav>{menu}'
    elif system == "utility_conversion":
        body = f'{brand(ctx)}<nav>{links}</nav><div class="header-actions">{phone}{cta}</div>{menu}'
    elif system == "architectural_rail":
        body = f'<span class="header-index">SA / 03</span>{brand(ctx)}<nav>{links}</nav>{phone}{menu}'
    elif system == "atelier_mark":
        body = f'{brand(ctx)}<span class="atelier-label">Atelier & savoir-faire</span><nav>{links}</nav>{menu}'
    elif system == "cinematic_overlay":
        body = f'{brand(ctx)}<nav>{links}</nav>{phone}{menu}'
    else:
        body = f'{brand(ctx)}<nav>{links}</nav>{phone}{menu}'
    return f'<header class="site-header header-{system}" id="site-header"><div class="header-inner">{body}</div></header>'


def _hero_copy(ctx: SiteContext, *, compact: bool = False) -> str:
    location = f'<span>{ctx.location}</span>' if ctx.location else ""
    tagline = f'<p class="hero-lead">{ctx.text("tagline")}</p>' if ctx.plain.get("tagline") else ""
    phone = f'<a class="button button-ghost" href="tel:{ctx.phone_href}">Appeler</a>' if ctx.phone_href else ""
    actions = f'<div class="hero-actions"><a class="button button-primary" href="#devis">Parler du projet</a>{phone}</div>'
    return f'<div class="hero-copy"><p class="eyebrow">{ctx.trade_label}{location}</p><h1>{ctx.business_name}</h1>{tagline}{actions}</div>'


def _fallback(ctx: SiteContext) -> str:
    direction = ctx.profile["art_direction"]
    if direction == "technical_spatial":
        return '''<div class="visual-fallback technical" aria-hidden="true"><svg viewBox="0 0 760 620"><path d="M90 300 380 90l290 210v250H90Z"/><path d="M380 90v460M90 300h580M210 550V360h150v190M440 300v250M520 390h90M520 440h90"/><circle cx="380" cy="300" r="16"/><circle cx="520" cy="390" r="10"/></svg><span>Plan / réseau</span></div>'''
    if direction == "architectural_brutalist":
        return '<div class="visual-fallback brutalist" aria-hidden="true"><i></i><i></i><i></i><b>01</b></div>'
    if direction == "warm_craft":
        return '<div class="visual-fallback craft" aria-hidden="true"><i></i><i></i><i></i><span>Matière / geste</span></div>'
    if direction == "bold_conversion":
        return '<div class="visual-fallback signal" aria-hidden="true"><b>→</b><i></i><span>Un besoin.<br>Une réponse claire.</span></div>'
    if direction == "cinematic_luxury":
        return '<div class="visual-fallback cinematic" aria-hidden="true"><i></i><span>Transformation</span><b>01 — 03</b></div>'
    return '<div class="visual-fallback editorial" aria-hidden="true"><i></i><i></i><span>Forme<br>& matière</span></div>'


def render_hero(ctx: SiteContext) -> str:
    system = ctx.profile["hero_system"]
    system_class = system.replace("_", "-")
    media = list(ctx.selected("hero"))
    gallery = list(ctx.selected("gallery"))
    primary = image(ctx, media[0], f"{ctx.trade_label} - {ctx.plain['nom_entreprise']}", eager=True, class_name="hero-image") if media else _fallback(ctx)
    copy = _hero_copy(ctx)
    if system == "full_bleed_photo":
        body = f'<div class="hero-full-media">{primary}</div><div class="hero-full-copy">{copy}<span class="scroll-mark">Découvrir ↓</span></div>'
    elif system == "editorial_offset":
        body = f'<div class="hero-folio">No. 01</div>{copy}<div class="hero-offset-media">{primary}</div><p class="hero-side-note">Conception / réalisation</p>'
    elif system == "oversized_type":
        body = f'<div class="hero-word">{ctx.trade_label}</div>{copy}<div class="hero-type-media">{primary}</div>'
    elif system == "split_architecture":
        body = f'<div class="hero-split-copy">{copy}<span class="drawing-index">A — 01</span></div><div class="hero-split-media">{primary}</div>'
    elif system == "project_canvas":
        body = f'<div class="hero-canvas-media">{primary}</div><div class="hero-canvas-label"><span>Projet sélectionné</span>{copy}</div>'
    elif system == "conversion_panel":
        body = f'<div class="hero-conversion-copy">{copy}<ul class="real-contact"><li>{ctx.location or "Intervention sur devis"}</li>{f"<li>{ctx.text('telephone')}</li>" if ctx.phone_href else ""}</ul></div><div class="hero-conversion-media">{primary}</div>'
    elif system in {"isometric_spatial", "blueprint_scene"}:
        body = f'<div class="hero-spatial-copy">{copy}</div><div class="hero-spatial-stage">{primary}<span class="node node-a">A</span><span class="node node-b">B</span><span class="node node-c">C</span></div>'
    elif system == "material_macro":
        body = f'<div class="hero-material-copy">{copy}<span class="material-caption">Détail / matière / finition</span></div><div class="hero-material-media">{primary}</div>'
    elif system == "gallery_collage":
        extras = gallery[:2]
        tiles = "".join(image(ctx, item, "Détail de réalisation", eager=True, class_name=f"hero-collage-{index+2}") for index, item in enumerate(extras))
        body = f'{copy}<div class="hero-collage"><div class="hero-collage-1">{primary}</div>{tiles}</div>'
    elif system == "cinematic_layered":
        body = f'<div class="hero-cinematic-media">{primary}</div><div class="hero-cinematic-shade"></div>{copy}<div class="hero-scene">SCÈNE 01</div>'
    else:
        body = f'{copy}<div class="hero-minimal-mark">{_fallback(ctx)}</div><span class="hero-minimal-line"></span>'
    return f'<section id="accueil" class="hero hero-{system} hero-{system_class}" data-section="hero" data-system="{system}">{body}</section>'


def render_manifesto(ctx: SiteContext) -> str:
    tagline = ctx.text("tagline") or f"{ctx.trade_label}."
    return f'<section class="manifesto" data-section="manifesto"><p class="eyebrow">Approche</p><h2>{tagline}</h2><span class="manifesto-index">02</span></section>'


def render_services(ctx: SiteContext) -> str:
    system = ctx.profile["services_composition"]
    items = []
    for index, service in enumerate(ctx.items("services"), 1):
        value = html.escape(str(service), quote=True)
        items.append(f'<li><span>{index:02d}</span><h3>{value}</h3><i aria-hidden="true"></i></li>')
    return f'<section id="services" class="services services-{system}" data-section="services"><div class="section-kicker"><p class="eyebrow">Savoir-faire</p><h2>Prestations</h2></div><ol>{"".join(items)}</ol></section>'


def _gallery_media(ctx: SiteContext) -> list[dict]:
    values = list(ctx.selected("gallery"))
    featured = list(ctx.selected("featured_project"))
    for item in featured:
        if item.get("media_id") not in {value.get("media_id") for value in values}:
            values.append(item)
    return values


def render_gallery(ctx: SiteContext) -> str:
    values = _gallery_media(ctx)
    count_class = "single" if len(values) == 1 else "diptych" if len(values) == 2 else "trio" if len(values) == 3 else "sequence"
    figures = "".join(
        f'<figure><span>{index:02d}</span>{image(ctx, item, f"Réalisation {index} de {ctx.plain["nom_entreprise"]}", class_name="gallery-image")}</figure>'
        for index, item in enumerate(values, 1)
    )
    return f'<section id="gallery" class="gallery gallery-{ctx.profile["project_showcase"]} gallery-{count_class}" data-section="gallery"><div class="gallery-heading"><p class="eyebrow">Réalisations</p><h2>Le travail, en situation.</h2></div><div class="gallery-layout">{figures}</div></section>'


def render_featured(ctx: SiteContext) -> str:
    values = list(ctx.selected("featured_project")) or _gallery_media(ctx)[:1]
    if not values:
        return ""
    visual = image(ctx, values[0], "Projet sélectionné", class_name="featured-image")
    return f'<section class="featured" data-section="featured_project"><div class="featured-copy"><p class="eyebrow">Projet sélectionné</p><h2>Un détail juste change l’ensemble.</h2></div><div class="featured-media">{visual}</div></section>'


def render_about(ctx: SiteContext) -> str:
    facts = []
    if ctx.plain.get("ville"):
        facts.append(f'<li><span>Implantation</span><strong>{ctx.text("ville")}</strong></li>')
    if ctx.plain.get("adresse"):
        facts.append(f'<li><span>Adresse</span><strong>{ctx.text("adresse")}</strong></li>')
    if ctx.plain.get("assurance_decennale_nom"):
        facts.append(f'<li><span>Assurance décennale</span><strong>{ctx.text("assurance_decennale_nom")}</strong></li>')
    media = list(ctx.selected("about"))
    visual = image(ctx, media[0], f"{ctx.business_name}", class_name="about-image") if media else _fallback(ctx)
    return f'<section id="about" class="about" data-section="about"><div class="about-visual">{visual}</div><div class="about-copy"><p class="eyebrow">L’entreprise</p><h2>{ctx.business_name}</h2><ul>{"".join(facts)}</ul></div></section>'


def render_process(ctx: SiteContext) -> str:
    steps = ctx.items("process_steps")
    if not steps:
        return ""
    items = "".join(f'<li><span>{index:02d}</span><p>{html.escape(str(step), quote=True)}</p></li>' for index, step in enumerate(steps, 1))
    return f'<section class="process" data-section="process"><p class="eyebrow">Déroulé</p><h2>Le projet, étape par étape.</h2><ol>{items}</ol></section>'


def render_before_after(ctx: SiteContext) -> str:
    values = list(ctx.selected("before_after"))[:2]
    if len(values) < 2:
        return ""
    figures = "".join(f'<figure>{image(ctx, item, "Avant travaux" if index == 0 else "Après travaux", class_name="before-after-image")}<figcaption>{"Avant" if index == 0 else "Après"}</figcaption></figure>' for index, item in enumerate(values))
    return f'<section class="before-after" data-section="before_after"><div><p class="eyebrow">Transformation</p><h2>Avant / après</h2></div><div class="before-after-grid">{figures}</div></section>'


def render_trust(ctx: SiteContext) -> str:
    if not ctx.plain.get("assurance_decennale_nom"):
        return ""
    return f'<section class="trust" data-section="trust"><span>Protection vérifiée</span><h2>Assurance décennale</h2><p>{ctx.text("assurance_decennale_nom")}</p></section>'


def render_stats(ctx: SiteContext) -> str:
    values = ctx.items("stats")
    if not values:
        return ""
    items = "".join(f'<li><strong>{html.escape(item["valeur"], quote=True)}</strong><span>{html.escape(item["label"], quote=True)}</span></li>' for item in values)
    return f'<section class="stats" data-section="stats"><ul>{items}</ul></section>'


def render_reviews(ctx: SiteContext) -> str:
    values = ctx.items("avis")
    if not values:
        return ""
    items = "".join(f'<figure><blockquote>{html.escape(item["commentaire"], quote=True)}</blockquote><figcaption>{html.escape(item["nom_auteur"] or "Client", quote=True)} · {item["note"]}/5</figcaption></figure>' for item in values)
    return f'<section id="reviews" class="reviews" data-section="reviews"><p class="eyebrow">Avis publiés</p><h2>Ce qu’ils en disent.</h2><div>{items}</div></section>'


def render_service_area(ctx: SiteContext) -> str:
    if not ctx.location:
        return ""
    return f'<section class="service-area" data-section="service_area"><p class="eyebrow">Implantation</p><h2>{ctx.location}</h2></section>'


def render_contact(ctx: SiteContext) -> str:
    contacts = []
    if ctx.phone_href:
        contacts.append(f'<a href="tel:{ctx.phone_href}"><span>Téléphone</span><strong>{ctx.text("telephone")}</strong></a>')
    if ctx.plain.get("email"):
        contacts.append(f'<a href="mailto:{ctx.text("email")}"><span>Email</span><strong>{ctx.text("email")}</strong></a>')
    return f'''<section class="contact" id="devis" data-section="contact">
<div class="contact-intro"><p class="eyebrow">Votre projet</p><h2>Commençons par en parler.</h2><div class="contact-details">{"".join(contacts)}</div></div>
<form id="devis-form" class="quote-form"><label for="client_nom">Nom et prénom *</label><input id="client_nom" name="client_nom" autocomplete="name" required><div class="form-pair"><div><label for="client_telephone">Téléphone</label><input type="tel" id="client_telephone" autocomplete="tel"></div><div><label for="client_email">Email</label><input type="email" id="client_email" autocomplete="email"></div></div><label for="description">Votre projet</label><textarea id="description" rows="5"></textarea><button class="button button-primary" type="submit" id="devis-submit">Envoyer ma demande</button><div class="form-message" id="form-message" role="status" aria-live="polite"></div></form>
</section>'''


def render_footer(ctx: SiteContext) -> str:
    legal = []
    if ctx.plain.get("siret"):
        legal.append(f'<span>SIRET {ctx.text("siret")}</span>')
    if ctx.plain.get("assurance_decennale_nom"):
        legal.append(f'<span>Décennale : {ctx.text("assurance_decennale_nom")}</span>')
    credits = []
    seen = set()
    for values in ctx.media.values():
        for item in values:
            credit = str(item.get("credit") or "").strip()
            source_url = str(item.get("source_url") or "").strip()
            key = (credit, source_url)
            if credit and key not in seen:
                seen.add(key)
                credits.append(f'<a href="{html.escape(source_url, quote=True)}" rel="noopener noreferrer">{html.escape(credit, quote=True)}</a>' if source_url else f'<span>{html.escape(credit, quote=True)}</span>')
    return f'<footer class="site-footer footer-{ctx.profile["footer_system"]}"><div class="footer-brand">{brand(ctx)}</div><div class="footer-meta">{"".join(legal)}</div><div class="media-credits">{"".join(credits)}</div><p>© {date.today().year}</p></footer>'


RENDERERS = {
    "hero": render_hero, "manifesto": render_manifesto, "services": render_services,
    "gallery": render_gallery, "featured_project": render_featured, "about": render_about,
    "process": render_process, "before_after": render_before_after, "trust": render_trust,
    "stats": render_stats, "reviews": render_reviews, "service_area": render_service_area,
    "contact": render_contact,
}


def available(ctx: SiteContext, name: str) -> bool:
    checks = {
        "hero": True, "manifesto": bool(ctx.plain.get("tagline")), "services": bool(ctx.items("services")),
        "gallery": bool(_gallery_media(ctx)), "featured_project": bool(ctx.selected("featured_project") or _gallery_media(ctx)),
        "about": bool(ctx.selected("about") or ctx.plain.get("ville") or ctx.plain.get("adresse") or ctx.plain.get("assurance_decennale_nom")),
        "process": bool(ctx.items("process_steps")), "before_after": len(ctx.selected("before_after")) >= 2,
        "trust": bool(ctx.plain.get("assurance_decennale_nom")), "stats": bool(ctx.items("stats")),
        "reviews": bool(ctx.items("avis")), "service_area": bool(ctx.location), "contact": True,
    }
    return bool(name in RENDERERS and checks.get(name))
