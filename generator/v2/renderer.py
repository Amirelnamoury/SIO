"""Composition engine producing one autonomous, static V2 HTML document."""

from __future__ import annotations

import html
import json
from urllib.parse import urlsplit

from .context import SiteContext, safe_url
from .sections import SECTION_RENDERERS, render_contact, render_footer, render_header, section_is_available
from .styles import render_css


def _json(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _seo(ctx: SiteContext) -> tuple[str, str]:
    title = f'{ctx.plain["nom_entreprise"]} - {ctx.theme.get("label") or ctx.plain["metier"]}'
    if ctx.plain.get("ville"):
        title += f' à {ctx.plain["ville"]}'

    description_parts = [ctx.plain["nom_entreprise"], ctx.theme.get("label")]
    if ctx.plain.get("ville"):
        description_parts.append(f'à {ctx.plain["ville"]}')
    services = ctx.items("services")[:3]
    description = " ".join(str(part) for part in description_parts if part)
    if services:
        description += ". Prestations : " + ", ".join(services)
    description = description[:155].rstrip(" ,.;") + "."

    canonical = safe_url(ctx.plain.get("url_publique"))
    canonical = canonical if canonical and urlsplit(html.unescape(canonical)).scheme in {"http", "https"} else ""
    tags = [
        f"<title>{html.escape(title, quote=True)}</title>",
        f'<meta name="description" content="{html.escape(description, quote=True)}">',
        '<meta name="robots" content="index,follow">',
        f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
        f'<meta property="og:description" content="{html.escape(description, quote=True)}">',
        '<meta property="og:type" content="website">',
    ]
    if canonical:
        tags.extend((f'<link rel="canonical" href="{canonical}">', f'<meta property="og:url" content="{canonical}">'))
    hero = ctx.selected("hero")
    if hero and urlsplit(html.unescape(hero[0]["content_url"])).scheme in {"http", "https"}:
        tags.append(f'<meta property="og:image" content="{hero[0]["content_url"]}">')

    business: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": ctx.plain["nom_entreprise"],
    }
    if canonical:
        business["url"] = html.unescape(canonical)
    if ctx.plain.get("telephone"):
        business["telephone"] = ctx.plain["telephone"]
    if ctx.plain.get("email"):
        business["email"] = ctx.plain["email"]
    address = {key: value for key, value in {
        "streetAddress": ctx.plain.get("adresse"),
        "postalCode": ctx.plain.get("code_postal"),
        "addressLocality": ctx.plain.get("ville"),
        "addressCountry": "FR" if any(ctx.plain.get(key) for key in ("adresse", "code_postal", "ville")) else None,
    }.items() if value}
    if address:
        business["address"] = {"@type": "PostalAddress", **address}
    tags.append(f'<script type="application/ld+json">{_json(business)}</script>')
    return "\n".join(tags), title


def _script(ctx: SiteContext, api_base_url: str) -> str:
    phone = ctx.plain.get("telephone") or ""
    return f"""<script>
(function () {{
  "use strict";
  var API_BASE = {_json(api_base_url.rstrip('/'))};
  var SLUG = {_json(ctx.plain['slug'])};
  var form = document.getElementById("devis-form");
  var messageBox = document.getElementById("form-message");
  var submitBtn = document.getElementById("devis-submit");
  form.addEventListener("submit", function (event) {{
    event.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Envoi en cours...";
    messageBox.textContent = "";
    messageBox.className = "form-message";
    var payload = {{
      nom: document.getElementById("client_nom").value,
      telephone: document.getElementById("client_telephone").value || null,
      email: document.getElementById("client_email").value || null,
      message: document.getElementById("description").value || null
    }};
    fetch(API_BASE + "/pub/" + encodeURIComponent(SLUG) + "/demande-devis", {{
      method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(payload)
    }})
      .then(function (response) {{ if (!response.ok) throw new Error("Erreur serveur"); return response.json(); }})
      .then(function () {{ messageBox.textContent = "Merci, votre demande a bien été envoyée."; messageBox.className = "form-message success"; form.reset(); }})
      .catch(function () {{ messageBox.textContent = {_json('Une erreur est survenue.' + (f' Vous pouvez nous appeler au {phone}.' if phone else ' Merci de réessayer.'))}; messageBox.className = "form-message error"; }})
      .finally(function () {{ submitBtn.disabled = false; submitBtn.textContent = "Envoyer ma demande"; }});
  }});
  var header = document.getElementById("site-header");
  window.addEventListener("scroll", function () {{ header.classList.toggle("scrolled", window.scrollY > 12); }}, {{ passive: true }});
  document.querySelectorAll(".mobile-menu a").forEach(function (link) {{ link.addEventListener("click", function () {{ link.closest("details").removeAttribute("open"); }}); }});
}})();
</script>"""


def _mobile_actions(ctx: SiteContext) -> str:
    actions = []
    if ctx.phone_href:
        actions.append(f'<a href="tel:{ctx.phone_href}">Appeler</a>')
    actions.append('<a href="#devis">Demander un devis</a>')
    return f'<nav class="mobile-action-bar" aria-label="Actions rapides" style="--mobile-actions:{len(actions)}">{"".join(actions)}</nav>'


def render_site_v2(payload: dict, api_base_url: str) -> str:
    ctx = SiteContext.from_payload(payload)
    requested = []
    for name in ctx.profile["section_order"]:
        if name not in requested and section_is_available(ctx, name):
            requested.append(name)
    if "hero" not in requested:
        requested.insert(0, "hero")
    sections = [SECTION_RENDERERS[name](ctx) for name in requested]
    if "contact" not in requested:
        sections.append(render_contact(ctx))
        requested.append("contact")
    seo, _ = _seo(ctx)
    body_classes = " ".join((
        f'family-{ctx.profile["design_family"]}',
        f'radius-{ctx.profile["radius_style"]}',
        f'spacing-{ctx.profile["spacing_style"]}',
    ))
    section_names = ",".join(requested)
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{seo}
<style>{render_css(ctx)}</style>
</head>
<body class="{body_classes}" data-design-engine="{ctx.profile['design_engine_version']}" data-design-signature="{html.escape(str(ctx.profile.get('design_signature') or ''), quote=True)}" data-rendered-sections="{section_names}">
<a href="#contenu" class="skip-link">Aller au contenu</a>
{render_header(ctx, requested)}
<main id="contenu">{"".join(sections)}</main>
{render_footer(ctx)}
{_mobile_actions(ctx)}
{_script(ctx, api_base_url)}
</body>
</html>'''
