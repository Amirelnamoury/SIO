"""Reusable section renderers and their real-data availability rules."""

from __future__ import annotations

import html
from datetime import date
from typing import Callable

from .context import SiteContext


def _image(ctx: SiteContext, item: dict, alt: str, *, eager: bool = False, class_name: str = "") -> str:
    loading = "eager" if eager else "lazy"
    priority = ' fetchpriority="high"' if eager else ""
    return (
        f'<img class="{class_name}" src="{item["content_url"]}" '
        f'alt="{ctx.image_alt(item, alt)}"{ctx.media_dimensions(item)} '
        f'loading="{loading}" decoding="async"{priority}>'
    )


def _brand(ctx: SiteContext, modifier: str = "") -> str:
    class_name = f"site-brand {modifier}".strip()
    if ctx.logo:
        logo = _image(ctx, ctx.logo, f"Logo {ctx.plain['nom_entreprise']}", eager=True, class_name="brand-logo")
        return f'<a class="{class_name}" href="#accueil" aria-label="Accueil - {ctx.business_name}">{logo}</a>'
    return f'<a class="{class_name} brand-wordmark" href="#accueil">{ctx.business_name}</a>'


def _nav(ctx: SiteContext, visible_sections: list[str]) -> str:
    labels = {
        "services": "Prestations", "about": "Entreprise", "gallery": "Réalisations",
        "reviews": "Avis", "service_area": "Zone", "contact": "Contact",
    }
    links = [f'<a href="#{name}">{label}</a>' for name, label in labels.items() if name in visible_sections]
    return "".join(links)


def _phone_link(ctx: SiteContext, class_name: str = "header-phone") -> str:
    if not ctx.phone_href:
        return ""
    return f'<a class="{class_name}" href="tel:{ctx.phone_href}">{ctx.text("telephone")}</a>'


def render_header(ctx: SiteContext, visible_sections: list[str]) -> str:
    variant = ctx.profile["header_variant"]
    brand = _brand(ctx)
    nav = _nav(ctx, visible_sections)
    phone = _phone_link(ctx)
    cta = '<a class="button header-cta" href="#devis">Demander un devis</a>'
    mobile = f'<details class="mobile-menu"><summary aria-label="Ouvrir le menu">Menu</summary><nav>{nav}{phone}{cta}</nav></details>'
    if variant == "centered":
        body = f'<div class="header-meta">{phone}{cta}</div><div class="header-brand-center">{brand}</div><nav class="main-nav centered-nav" aria-label="Navigation principale">{nav}</nav>{mobile}'
    elif variant == "minimal":
        body = f'<div class="header-minimal-row">{brand}<nav class="main-nav" aria-label="Navigation principale">{nav}</nav><div class="header-actions">{phone}{cta}</div>{mobile}</div>'
    elif variant == "compact":
        body = f'<div class="header-compact-row">{brand}<nav class="main-nav compact-nav" aria-label="Navigation principale">{nav}</nav>{phone}{cta}{mobile}</div>'
    else:
        body = f'<div class="header-classic-row">{brand}<nav class="main-nav" aria-label="Navigation principale">{nav}</nav><div class="header-actions">{phone}{cta}</div>{mobile}</div>'
    return f'<header class="site-header header-{variant}" id="site-header" data-variant="{variant}"><div class="container">{body}</div></header>'


def _hero_copy(ctx: SiteContext) -> str:
    tagline = ctx.text("tagline")
    location = ctx.location
    eyebrow = ctx.trade_label + (f" · {location}" if location else "")
    lead = f'<p class="hero-lead">{tagline}</p>' if tagline else ""
    phone = f'<a class="button button-secondary" href="tel:{ctx.phone_href}">Appeler</a>' if ctx.phone_href else ""
    return (
        f'<p class="eyebrow">{eyebrow}</p><h1>{ctx.business_name}</h1>{lead}'
        f'<div class="hero-actions"><a class="button button-primary" href="#devis">Demander un devis</a>{phone}</div>'
    )


def render_hero(ctx: SiteContext) -> str:
    variant = ctx.profile["hero_variant"]
    media = ctx.selected("hero")
    image = _image(ctx, media[0], f"{ctx.theme.get('label') or ctx.plain['metier']} - {ctx.plain['nom_entreprise']}", eager=True, class_name="hero-image") if media else ""
    fallback = '<div class="hero-fallback" aria-hidden="true"><span></span><span></span><span></span></div>'
    copy = _hero_copy(ctx)
    if variant == "fullscreen":
        body = f'<div class="hero-media-full">{image or fallback}</div><div class="container hero-overlay"><div class="hero-copy">{copy}</div></div>'
    elif variant == "split":
        body = f'<div class="container hero-columns"><div class="hero-copy">{copy}</div><div class="hero-visual">{image or fallback}</div></div>'
    elif variant == "asymmetric":
        body = f'<div class="container hero-asymmetric-grid"><div class="hero-copy">{copy}</div><div class="hero-aside">{image or fallback}<span class="hero-index">01</span></div></div>'
    elif variant == "compact":
        body = f'<div class="container hero-compact-row"><div class="hero-copy">{copy}</div><div class="hero-compact-mark">{image or fallback}</div></div>'
    elif variant == "editorial":
        body = f'<div class="container hero-editorial-layout"><div class="hero-edition">{ctx.trade_label}</div><div class="hero-copy">{copy}</div><div class="hero-editorial-media">{image or fallback}</div></div>'
    else:
        body = f'<div class="container hero-card-stage"><div class="hero-card-panel">{copy}</div><div class="hero-card-media">{image or fallback}</div></div>'
    return f'<section class="hero hero-{variant} image-{ctx.profile["image_treatment"]}" id="accueil" data-section="hero" data-variant="{variant}">{body}</section>'


def render_services(ctx: SiteContext) -> str:
    variant = ctx.profile["services_variant"]
    services = ctx.items("services")
    items = []
    for index, service in enumerate(services, 1):
        safe = html.escape(str(service), quote=True)
        if variant == "editorial":
            items.append(f'<article class="service-editorial"><span>{index:02d}</span><h3>{safe}</h3></article>')
        elif variant == "list":
            items.append(f'<li><span aria-hidden="true">{index:02d}</span><strong>{safe}</strong></li>')
        elif variant == "alternating":
            items.append(f'<article class="service-alternating"><span>{index}</span><h3>{safe}</h3><i aria-hidden="true"></i></article>')
        else:
            items.append(f'<article class="service-item"><span class="service-number">{index:02d}</span><h3>{safe}</h3></article>')
    tag = "ol" if variant == "list" else "div"
    return (
        f'<section id="services" class="services services-{variant}" data-section="services" data-variant="{variant}">'
        f'<div class="container"><div class="section-heading"><p class="eyebrow">Expertise</p><h2>Nos prestations</h2></div>'
        f'<{tag} class="services-layout">{"".join(items)}</{tag}></div></section>'
    )


def render_trust(ctx: SiteContext) -> str:
    insurance = ctx.text("assurance_decennale_nom")
    return (
        '<section class="trust-strip" data-section="trust"><div class="container trust-inner">'
        f'<span class="trust-symbol" aria-hidden="true">✓</span><div><p class="eyebrow">Protection</p><h2>Assurance décennale</h2><p>{insurance}</p></div>'
        '</div></section>'
    )


def render_about(ctx: SiteContext) -> str:
    variant = ctx.profile["about_variant"]
    city = ctx.text("ville")
    address = ctx.text("adresse")
    insurance = ctx.text("assurance_decennale_nom")
    facts = []
    if city:
        facts.append(f'<li>Entreprise de {ctx.trade_label} à {city}</li>')
    if address:
        facts.append(f'<li>{address}</li>')
    if insurance:
        facts.append(f'<li>Assurance décennale : {insurance}</li>')
    media = ctx.selected("about")
    visual = _image(ctx, media[0], f"À propos de {ctx.plain['nom_entreprise']}", class_name="about-image") if media else '<div class="about-monogram" aria-hidden="true"><span></span><span></span><span></span></div>'
    content = f'<div class="about-copy"><p class="eyebrow">L’entreprise</p><h2>{ctx.business_name}</h2><ul>{"".join(facts)}</ul></div>'
    if variant == "editorial":
        body = f'<div class="about-editorial-title">À propos</div>{content}{visual}'
    elif variant == "split":
        body = f'<div class="about-visual">{visual}</div>{content}'
    elif variant == "compact":
        body = f'{content}<aside class="about-compact-aside">{ctx.trade_label}</aside>'
    else:
        body = f'{content}<div class="about-visual">{visual}</div>'
    return f'<section id="about" class="about about-{variant}" data-section="about" data-variant="{variant}"><div class="container about-layout">{body}</div></section>'


def render_gallery(ctx: SiteContext) -> str:
    variant = ctx.profile["gallery_variant"]
    figures = []
    for index, item in enumerate(ctx.selected("gallery")):
        image = _image(ctx, item, f"Réalisation {index + 1} de {ctx.plain['nom_entreprise']}", class_name="gallery-image")
        figures.append(f'<figure class="gallery-item gallery-item-{index + 1}">{image}</figure>')
    return (
        f'<section id="gallery" class="gallery gallery-{variant} image-{ctx.profile["image_treatment"]}" data-section="gallery" data-variant="{variant}">'
        f'<div class="container"><div class="section-heading"><p class="eyebrow">Réalisations</p><h2>Notre travail en images</h2></div>'
        f'<div class="gallery-layout">{"".join(figures)}</div></div></section>'
    )


def render_reviews(ctx: SiteContext) -> str:
    variant = ctx.profile["reviews_variant"]
    cards = []
    for review in ctx.items("avis"):
        stars = '<span class="review-stars" aria-label="{} étoiles sur 5">{}</span>'.format(review["note"], "★" * review["note"])
        author = html.escape(review["nom_auteur"], quote=True) if review["nom_auteur"] else "Client"
        comment = html.escape(review["commentaire"], quote=True)
        cards.append(f'<figure class="review-item">{stars}<blockquote>{comment}</blockquote><figcaption>{author}</figcaption></figure>')
    return (
        f'<section id="reviews" class="reviews reviews-{variant}" data-section="reviews" data-variant="{variant}">'
        f'<div class="container"><div class="section-heading"><p class="eyebrow">Avis publiés</p><h2>Retours de nos clients</h2></div>'
        f'<div class="reviews-layout">{"".join(cards)}</div></div></section>'
    )


def render_stats(ctx: SiteContext) -> str:
    items = "".join(
        f'<div class="stat"><strong>{html.escape(item["valeur"], quote=True)}</strong><span>{html.escape(item["label"], quote=True)}</span></div>'
        for item in ctx.items("stats")
    )
    return f'<section class="stats" data-section="stats"><div class="container stats-layout">{items}</div></section>'


def render_featured_project(ctx: SiteContext) -> str:
    item = ctx.selected("featured_project")[0]
    image = _image(ctx, item, f"Réalisation de {ctx.plain['nom_entreprise']}", class_name="featured-image")
    return f'<section class="featured-project image-{ctx.profile["image_treatment"]}" data-section="featured_project"><div class="container featured-layout"><div><p class="eyebrow">Projet sélectionné</p><h2>Une réalisation en images</h2></div>{image}</div></section>'


def render_before_after(ctx: SiteContext) -> str:
    items = ctx.selected("before_after")[:2]
    figures = "".join(
        f'<figure>{_image(ctx, item, ("Avant" if index == 0 else "Après") + " travaux", class_name="before-after-image")}<figcaption>{"Avant" if index == 0 else "Après"}</figcaption></figure>'
        for index, item in enumerate(items)
    )
    return f'<section class="before-after" data-section="before_after"><div class="container"><div class="section-heading"><p class="eyebrow">Transformation</p><h2>Avant et après</h2></div><div class="before-after-layout">{figures}</div></div></section>'


def render_process(ctx: SiteContext) -> str:
    items = "".join(f'<li><span>{index:02d}</span>{html.escape(step, quote=True)}</li>' for index, step in enumerate(ctx.items("process_steps"), 1))
    return f'<section class="process" data-section="process"><div class="container"><div class="section-heading"><p class="eyebrow">Étapes</p><h2>Déroulement</h2></div><ol>{items}</ol></div></section>'


def render_reasons(ctx: SiteContext) -> str:
    items = "".join(f'<li>{html.escape(reason, quote=True)}</li>' for reason in ctx.items("reasons"))
    return f'<section class="reasons" data-section="reasons"><div class="container"><div class="section-heading"><p class="eyebrow">Repères</p><h2>Nos engagements</h2></div><ul>{items}</ul></div></section>'


def render_service_area(ctx: SiteContext) -> str:
    location = ctx.location
    return f'<section id="service_area" class="service-area" data-section="service_area"><div class="container service-area-layout"><p class="eyebrow">Zone d’intervention</p><h2>{location}</h2></div></section>'


def render_cta(ctx: SiteContext) -> str:
    variant = ctx.profile["cta_variant"]
    phone = _phone_link(ctx, "button button-secondary")
    if variant == "split":
        body = f'<div><p class="eyebrow">Votre projet</p><h2>Échangeons sur votre besoin</h2></div><div class="cta-actions"><a class="button button-primary" href="#devis">Demander un devis</a>{phone}</div>'
    elif variant == "floating":
        body = f'<div class="cta-floating-panel"><p class="eyebrow">Un projet ?</p><h2>Contactez {ctx.business_name}</h2><a class="button button-primary" href="#devis">Demander un devis</a>{phone}</div>'
    elif variant == "minimal":
        body = f'<h2>Parlons de votre projet.</h2><a class="text-link" href="#devis">Demander un devis →</a>{phone}'
    else:
        body = f'<p class="eyebrow">Prendre contact</p><h2>Décrivez votre projet.</h2><div class="cta-actions"><a class="button button-primary" href="#devis">Demander un devis</a>{phone}</div>'
    return f'<section class="cta cta-{variant}" data-section="cta" data-variant="{variant}"><div class="container cta-layout">{body}</div></section>'


def render_contact(ctx: SiteContext) -> str:
    details = []
    if ctx.plain.get("telephone"):
        details.append(f'<a href="tel:{ctx.phone_href}"><span>Téléphone</span><strong>{ctx.text("telephone")}</strong></a>')
    if ctx.plain.get("email"):
        email_value = ctx.text("email")
        details.append(f'<a href="mailto:{email_value}"><span>Email</span><strong>{email_value}</strong></a>')
    if ctx.location:
        details.append(f'<div><span>Zone</span><strong>{ctx.location}</strong></div>')
    return f'''<section class="contact" id="devis" data-section="contact">
  <div class="container contact-layout">
    <div class="contact-intro"><p class="eyebrow">Contact</p><h2>Demander un devis</h2><div class="contact-details">{"".join(details)}</div></div>
    <form id="devis-form" class="quote-form">
      <div class="field"><label for="client_nom">Nom et prénom *</label><input type="text" id="client_nom" name="client_nom" autocomplete="name" required></div>
      <div class="form-columns"><div class="field"><label for="client_telephone">Téléphone</label><input type="tel" id="client_telephone" name="client_telephone" autocomplete="tel"></div><div class="field"><label for="client_email">Email</label><input type="email" id="client_email" name="client_email" autocomplete="email"></div></div>
      <div class="field"><label for="description">Votre projet</label><textarea id="description" name="description" rows="5"></textarea></div>
      <button class="button button-primary" type="submit" id="devis-submit">Envoyer ma demande</button>
      <div class="form-message" id="form-message" role="status" aria-live="polite"></div>
    </form>
  </div>
</section>'''


def render_footer(ctx: SiteContext) -> str:
    variant = ctx.profile["footer_variant"]
    address = ctx.text("adresse") or ctx.location
    legal = []
    if ctx.plain.get("siret"):
        legal.append(f'<span>SIRET {ctx.text("siret")}</span>')
    if ctx.plain.get("assurance_decennale_nom"):
        legal.append(f'<span>Décennale : {ctx.text("assurance_decennale_nom")}</span>')
    contacts = []
    if ctx.plain.get("telephone"):
        contacts.append(f'<a href="tel:{ctx.phone_href}">{ctx.text("telephone")}</a>')
    if ctx.plain.get("email"):
        contacts.append(f'<a href="mailto:{ctx.text("email")}">{ctx.text("email")}</a>')
    if variant == "centered":
        body = f'<div class="footer-centered">{_brand(ctx, "footer-brand")}<p>{address}</p><div>{"".join(contacts)}</div><div>{"".join(legal)}</div></div>'
    elif variant in {"columns", "map"}:
        body = f'<div class="footer-columns"><div>{_brand(ctx, "footer-brand")}<p>{ctx.trade_label}</p></div><div><h2>Contact</h2>{"".join(contacts)}<p>{address}</p></div><div><h2>Informations</h2>{"".join(legal)}</div></div>'
    else:
        body = f'<div class="footer-simple">{_brand(ctx, "footer-brand")}<div>{"".join(contacts)}</div><div>{"".join(legal)}</div></div>'
    return f'<footer class="site-footer footer-{variant}" data-variant="{variant}"><div class="container">{body}<p class="copyright">© {date.today().year} {ctx.business_name}</p></div></footer>'


SECTION_RENDERERS: dict[str, Callable[[SiteContext], str]] = {
    "hero": render_hero,
    "trust": render_trust,
    "services": render_services,
    "featured_project": render_featured_project,
    "about": render_about,
    "gallery": render_gallery,
    "reviews": render_reviews,
    "service_area": render_service_area,
    "cta": render_cta,
    "stats": render_stats,
    "process": render_process,
    "before_after": render_before_after,
    "reasons": render_reasons,
    "contact": render_contact,
}


def section_is_available(ctx: SiteContext, section: str) -> bool:
    checks = {
        "hero": True,
        "trust": bool(ctx.plain.get("assurance_decennale_nom")),
        "services": bool(ctx.items("services")),
        "featured_project": bool(ctx.selected("featured_project")),
        "about": bool(ctx.plain.get("ville") or ctx.plain.get("adresse") or ctx.plain.get("assurance_decennale_nom") or ctx.selected("about")),
        "gallery": bool(ctx.selected("gallery")),
        "reviews": bool(ctx.items("avis")),
        "service_area": bool(ctx.plain.get("ville")),
        "cta": True,
        "stats": bool(ctx.items("stats")),
        "process": bool(ctx.items("process_steps")),
        "before_after": len(ctx.selected("before_after")) >= 2,
        "reasons": bool(ctx.items("reasons")),
        "contact": True,
    }
    return bool(checks.get(section, False) and section in SECTION_RENDERERS)
