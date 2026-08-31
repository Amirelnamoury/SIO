"""Static HTML composer for the Site Vitrine V3 grammar."""

from __future__ import annotations

import html
import json
from urllib.parse import urlsplit

from .context import SiteContext
from .grammar import PAGE_SILHOUETTES
from .sections import RENDERERS, available, render_contact, render_footer, render_header
from .styles import render_css


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _seo(ctx: SiteContext) -> str:
    label = str(ctx.theme.get("label") or ctx.plain["metier"])
    title = f'{ctx.plain["nom_entreprise"]} - {label}' + (f' à {ctx.plain["ville"]}' if ctx.plain.get("ville") else "")
    description = f'{ctx.plain["nom_entreprise"]}, {label.lower()}' + (f' à {ctx.plain["ville"]}' if ctx.plain.get("ville") else "")
    services = ctx.items("services")[:3]
    if services:
        description += ". " + ", ".join(services)
    description = description[:155].rstrip(" ,.;") + "."
    tags = [f'<title>{html.escape(title, quote=True)}</title>', f'<meta name="description" content="{html.escape(description, quote=True)}">', '<meta name="robots" content="index,follow">', f'<meta property="og:title" content="{html.escape(title, quote=True)}">', f'<meta property="og:description" content="{html.escape(description, quote=True)}">', '<meta property="og:type" content="website">']
    canonical = str(ctx.plain.get("url_publique") or "").strip()
    if urlsplit(canonical).scheme in {"http", "https"}:
        safe = html.escape(canonical, quote=True)
        tags.extend((f'<link rel="canonical" href="{safe}">', f'<meta property="og:url" content="{safe}">'))
    business = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": ctx.plain["nom_entreprise"]}
    for source, target in (("telephone", "telephone"), ("email", "email")):
        if ctx.plain.get(source):
            business[target] = ctx.plain[source]
    address = {key: value for key, value in {"streetAddress": ctx.plain.get("adresse"), "postalCode": ctx.plain.get("code_postal"), "addressLocality": ctx.plain.get("ville")}.items() if value}
    if address:
        business["address"] = {"@type": "PostalAddress", "addressCountry": "FR", **address}
    tags.append(f'<script type="application/ld+json">{_json(business)}</script>')
    return "\n".join(tags)


def _script(ctx: SiteContext, api_base_url: str) -> str:
    phone = ctx.plain.get("telephone") or ""
    return f'''<script>(function(){{"use strict";var API_BASE = {_json(api_base_url.rstrip('/'))};var form=document.getElementById("devis-form"),box=document.getElementById("form-message"),button=document.getElementById("devis-submit"),slug={_json(ctx.plain['slug'])};form.addEventListener("submit",function(event){{event.preventDefault();button.disabled=true;button.textContent="Envoi en cours...";box.textContent="";fetch(API_BASE+"/pub/"+encodeURIComponent(slug)+"/demande-devis",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{nom:document.getElementById("client_nom").value,telephone:document.getElementById("client_telephone").value||null,email:document.getElementById("client_email").value||null,message:document.getElementById("description").value||null}})}}).then(function(response){{if(!response.ok)throw new Error();return response.json()}}).then(function(){{box.textContent="Merci, votre demande a bien été envoyée.";box.className="form-message success";form.reset()}}).catch(function(){{box.textContent={_json('Une erreur est survenue.' + (f' Vous pouvez nous appeler au {phone}.' if phone else ' Merci de réessayer.'))};box.className="form-message error"}}).finally(function(){{button.disabled=false;button.textContent="Envoyer ma demande"}})}});document.querySelectorAll(".mobile-menu a").forEach(function(link){{link.addEventListener("click",function(){{link.closest("details").removeAttribute("open")}})}})}})();</script>'''


def render_site_v3(payload: dict, api_base_url: str) -> str:
    ctx = SiteContext.from_payload(payload)
    order = list(PAGE_SILHOUETTES[ctx.profile["page_silhouette"]])
    names = []
    rendered = []
    for name in order:
        if name not in names and available(ctx, name):
            names.append(name)
            value = RENDERERS[name](ctx)
            if value:
                rendered.append(value)
    if "contact" not in names:
        names.append("contact")
        rendered.append(render_contact(ctx))
    classes = " ".join((f'direction-{ctx.profile["art_direction"]}', f'silhouette-{ctx.profile["page_silhouette"]}', f'mobile-{ctx.profile["mobile_personality"]}', f'image-{ctx.profile["image_treatment"]}', f'motion-{ctx.profile["motion_level"]}'))
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{_seo(ctx)}<style>{render_css(ctx)}</style></head><body class="{classes}" data-design-engine="{ctx.profile['design_engine_version']}" data-design-signature="{html.escape(ctx.profile['design_signature'], quote=True)}" data-rendered-sections="{','.join(names)}"><a class="skip-link" href="#contenu">Aller au contenu</a>{render_header(ctx, names)}<main id="contenu">{"".join(rendered)}</main>{render_footer(ctx)}{_script(ctx, api_base_url)}</body></html>'''
