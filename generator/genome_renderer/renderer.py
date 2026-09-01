"""Static HTML renderer for Design Genome SiteDNA."""

from __future__ import annotations

import html
import json
from dataclasses import replace
from urllib.parse import urlsplit

from .context import RenderContext
from .sections import SECTION_RENDERERS, render_contact, render_footer, render_header
from .styles import render_css


RENDERER_SCHEMA_VERSION = "design-genome-renderer-0.1"


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _seo(ctx: RenderContext) -> str:
    title = f"{ctx.plain('nom_entreprise')} — {ctx.trade_label}"
    if ctx.plain("ville"):
        title += f" à {ctx.plain('ville')}"
    description = ctx.plain("tagline") or f"{ctx.plain('nom_entreprise')}, {ctx.trade_label.lower()}"
    description = description[:155].rstrip(" ,.;") + "."
    tags = [
        f'<title>{html.escape(title, quote=True)}</title>',
        f'<meta name="description" content="{html.escape(description, quote=True)}">',
        '<meta name="robots" content="noindex,nofollow">' if ctx.lab_mode else '<meta name="robots" content="index,follow">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(description, quote=True)}">',
    ]
    canonical = ctx.plain("url_publique")
    if urlsplit(canonical).scheme in {"http", "https"}:
        tags.append(f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">')
    business = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": ctx.plain("nom_entreprise")}
    for source, target in (("telephone", "telephone"), ("email", "email")):
        if ctx.plain(source):
            business[target] = ctx.plain(source)
    tags.append(f'<script type="application/ld+json">{_json(business)}</script>')
    return "\n".join(tags)


def _form_script(ctx: RenderContext) -> str:
    if not ctx.has_lead_flow:
        return ""
    fallback = "Une erreur est survenue. Merci de réessayer."
    if ctx.plain("telephone"):
        fallback = f"Une erreur est survenue. Vous pouvez appeler le {ctx.plain('telephone')}."
    script = '''<script>(function(){"use strict";
var form=document.getElementById("devis-form");if(!form)return;
var button=document.getElementById("devis-submit"),box=document.getElementById("form-message");
form.addEventListener("submit",function(event){
event.preventDefault();button.disabled=true;button.textContent="Envoi en cours...";box.textContent="";
fetch(__API_BASE__+"/pub/"+encodeURIComponent(__SLUG__)+"/demande-devis",{
method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
nom:document.getElementById("client_nom").value,
telephone:document.getElementById("client_telephone").value||null,
email:document.getElementById("client_email").value||null,
message:document.getElementById("description").value||null
})
}).then(function(response){if(!response.ok)throw new Error();return response.json()})
.then(function(){box.textContent="Merci, votre demande a bien été envoyée.";form.reset()})
.catch(function(){box.textContent=__FALLBACK__})
.finally(function(){button.disabled=false;button.textContent="Envoyer la demande"})
})})();</script>'''
    return (
        script.replace("__API_BASE__", _json(ctx.api_base_url))
        .replace("__SLUG__", _json(ctx.plain("slug")))
        .replace("__FALLBACK__", _json(fallback))
    )


def render_site_genome(ctx: RenderContext) -> str:
    rendered = []
    names = []
    for section in ctx.dna.section_order:
        if section in {"header", "footer"} or section in names:
            continue
        renderer = SECTION_RENDERERS.get(section)
        value = renderer(ctx) if renderer else ""
        if value:
            names.append(section)
            rendered.append(value)
    if ctx.dna.form_component and "contact" not in names:
        value = render_contact(ctx)
        if value:
            names.append("contact")
            rendered.append(value)
    rendered_order = tuple(("header", *names, "footer"))
    chrome_context = replace(ctx, dna=replace(ctx.dna, section_order=rendered_order))
    classes = " ".join((
        f"direction-{ctx.dna.art_direction}",
        f"grid-{ctx.dna.grid_system}",
        f"spacing-{ctx.dna.spacing_system}",
        f"geometry-{ctx.dna.geometry_system}",
        f"motion-{ctx.dna.motion_system}",
        f"mobile-{ctx.dna.mobile_personality}",
        f"spatial-{ctx.dna.spatial_system}",
    ))
    lab_banner = '<div class="lab-banner">Fixture synthétique — revue visuelle uniquement</div>' if ctx.synthetic_fixture else ""
    spatial_rendering = "none" if ctx.dna.spatial_system == "none" else "static-fallback"
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{_seo(ctx)}<style>{render_css(ctx)}</style></head><body class="{classes}" data-renderer="{RENDERER_SCHEMA_VERSION}" data-spatial-rendering="{spatial_rendering}" data-design-signature="{html.escape(ctx.dna.design_signature, quote=True)}" data-composition-signature="{html.escape(ctx.dna.composition_signature, quote=True)}" data-rendered-sections="{','.join(names)}">{lab_banner}<a class="skip-link" href="#contenu">Aller au contenu</a>{render_header(chrome_context)}<main id="contenu">{"".join(rendered)}</main>{render_footer(chrome_context)}{_form_script(ctx)}</body></html>'''
