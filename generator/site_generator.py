"""Genere un mini-site vitrine HTML autonome (CSS + JS inline, aucune
dependance externe a part une police Google Fonts) pour un artisan donne.

Chaque site combine :
- l'identite du METIER (couleurs de base, police, textes, icone de marque) ;
- une VARIANTE choisie automatiquement et de facon stable pour cet artisan
  (palette parmi 3, motif visuel du hero parmi 2) - voir themes.py.
Deux artisans du meme metier ont donc un style cohesif avec leur metier,
mais un rendu different l'un de l'autre.

Le formulaire de devis du site appelle directement l'API publique du SaaS
(POST /pub/{slug}/demande-devis) : pas de mailto, la demande arrive
directement dans le tableau de bord de l'artisan.

Usage :
    from site_generator import generate_site
    artisan = {
        "nom_entreprise": "Plomberie Dupont",
        "metier": "plombier",
        "slug": "plomberie-dupont",
        "ville": "Boulogne-Billancourt",
        "code_postal": "92100",
        "telephone": "06 01 02 03 04",
        "email": "contact@plomberie-dupont.fr",
        "siret": "123 456 789 00012",
        "assurance_decennale_nom": "AXA",
        # optionnel : forcer la variante au lieu de la laisser auto-choisie
        # "variante_couleur": 1, "variante_motif": "gradient-mesh",
        # optionnel : chiffres cles reels (rien n'est invente si absent)
        # "stats": [{"valeur": "12 ans", "label": "d'experience"}],
    }
    generate_site(artisan, api_base_url="https://api.suite-artisan.fr", output_path="site.html")
"""

from pathlib import Path

import requests

try:
    from .themes import (
        GOOGLE_FONTS,
        get_hero_motif,
        get_palette,
        get_theme,
        trade_icon_svg,
        ui_icon_svg,
    )
except ImportError:  # execution directe historique : python site_generator.py
    from themes import (
        GOOGLE_FONTS,
        get_hero_motif,
        get_palette,
        get_theme,
        trade_icon_svg,
        ui_icon_svg,
    )

try:
    from .v2 import is_compatible_design_profile, render_site_v2
    from .v3 import is_compatible_design_profile as is_compatible_v3_profile, render_site_v3
except ImportError:  # execution directe historique : python generator/site_generator.py
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from generator.v2 import is_compatible_design_profile, render_site_v2
    from generator.v3 import is_compatible_design_profile as is_compatible_v3_profile, render_site_v3

POURQUOI_NOUS_CHOISIR = [
    ("shield", "Assurance décennale", "Tous nos chantiers sont couverts, en toute tranquillité."),
    ("document", "Devis gratuit", "Un devis clair et détaillé, sans engagement, sous 48h."),
    ("clock", "Réactivité", "Intervention rapide, y compris en urgence."),
]

# Blocs CSS du hero : chaque motif definit .hero (fond) et ses pseudo-elements
# decoratifs, en s'appuyant uniquement sur les variables de couleur -- aucune
# valeur hexadecimale en dur ici, donc ca marche avec n'importe quelle palette.
HERO_MOTIF_CSS = {
    "wave-gradient": """
.hero { background: linear-gradient(160deg, var(--primary) 0%, var(--primary-dark) 100%); }
.hero::after {
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(ellipse at 80% 15%, rgba(255,255,255,0.16), transparent 55%);
  pointer-events: none;
}
""",
    "gradient-mesh": """
.hero { background: var(--primary-dark); }
.hero::before {
  content: ""; position: absolute; width: 440px; height: 440px; border-radius: 50%;
  background: var(--accent); filter: blur(100px); opacity: 0.5; top: -140px; left: -100px; pointer-events: none;
}
.hero::after {
  content: ""; position: absolute; width: 380px; height: 380px; border-radius: 50%;
  background: var(--secondary); filter: blur(110px); opacity: 0.4; bottom: -160px; right: -80px; pointer-events: none;
}
""",
    "diagonal-stripes": """
.hero {
  background-color: var(--primary);
  background-image: repeating-linear-gradient(115deg, transparent 0px 40px, rgba(255,255,255,0.06) 40px 80px);
}
.hero::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgba(0,0,0,0.35) 100%); pointer-events: none;
}
""",
    "dot-grid": """
.hero {
  background-color: var(--primary);
  background-image: radial-gradient(rgba(255,255,255,0.18) 1.6px, transparent 1.6px);
  background-size: 22px 22px;
}
.hero::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 30%, var(--primary-dark) 130%); opacity: 0.6; pointer-events: none;
}
""",
    "brick-rows": """
.hero { background: repeating-linear-gradient(0deg, var(--primary) 0px 38px, var(--primary-dark) 38px 42px); }
.hero::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.22), transparent 45%); pointer-events: none;
}
""",
}

CSS_TEMPLATE = """
:root {
  --primary: __PRIMARY__;
  --primary-dark: __PRIMARY_DARK__;
  --secondary: __SECONDARY__;
  --accent: __ACCENT__;
  --background: __BACKGROUND__;
  --text: __TEXT__;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: __FONT__;
  color: var(--text);
  background: var(--background);
  line-height: 1.6;
}
a { color: inherit; }
.icon { display: inline-block; vertical-align: middle; flex-shrink: 0; }
.container { max-width: 1120px; margin: 0 auto; padding: 0 24px; }

/* ---------- Header ---------- */
header.site-header {
  position: sticky; top: 0; z-index: 20;
  background: var(--primary-dark);
  color: #fff;
  transition: box-shadow 0.2s ease;
}
header.site-header.scrolled { box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
header.site-header .container {
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  padding-top: 14px; padding-bottom: 14px;
}
.logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.2rem; white-space: nowrap; }
.logo .icon { color: var(--secondary); }
nav.main-nav { display: flex; gap: 26px; }
nav.main-nav a { font-size: 0.92rem; font-weight: 600; opacity: 0.88; text-decoration: none; }
nav.main-nav a:hover { opacity: 1; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.header-phone {
  display: flex; align-items: center; gap: 6px;
  color: #fff; text-decoration: none; font-weight: 600; font-size: 0.92rem;
  white-space: nowrap;
}
.btn-header-cta {
  background: var(--accent); color: #fff; padding: 9px 18px; border-radius: 999px;
  font-weight: 700; font-size: 0.9rem; text-decoration: none; white-space: nowrap;
}

/* ---------- Hero ---------- */
.hero { position: relative; overflow: hidden; padding: 90px 0 76px; text-align: center; color: #fff; }
.hero .container { position: relative; z-index: 1; }
.hero-icon-badge {
  width: 74px; height: 74px; border-radius: 50%; margin: 0 auto 22px;
  background: rgba(255,255,255,0.14); display: flex; align-items: center; justify-content: center;
}
.hero-icon-badge .icon { color: #fff; }
.hero h1 { font-size: 2.5rem; margin-bottom: 14px; letter-spacing: -0.02em; }
.hero p.tagline { font-size: 1.2rem; opacity: 0.94; max-width: 640px; margin: 0 auto 10px; }
.hero p.zone { font-size: 1rem; opacity: 0.82; margin-bottom: 30px; }
.hero-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
.btn-cta {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--accent); color: #fff; padding: 14px 30px; border-radius: 999px;
  font-weight: 700; text-decoration: none; font-size: 1.02rem;
  box-shadow: 0 10px 26px rgba(0,0,0,0.22); transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.btn-cta:hover { transform: translateY(-2px); box-shadow: 0 14px 30px rgba(0,0,0,0.28); }
.btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.08); color: #fff; padding: 14px 26px; border-radius: 999px;
  font-weight: 700; text-decoration: none; font-size: 1.02rem; border: 1.5px solid rgba(255,255,255,0.5);
  transition: background 0.15s ease;
}
.btn-ghost:hover { background: rgba(255,255,255,0.18); }
.palette-swatches { display: flex; gap: 8px; justify-content: center; margin: 0 0 26px; }
.palette-swatches span { width: 18px; height: 18px; border-radius: 50%; display: inline-block; border: 2px solid rgba(255,255,255,0.6); }

/* ---------- Stats (optionnel, uniquement si donnees reelles fournies) ---------- */
.stats-bar { background: var(--background); border-bottom: 1px solid rgba(0,0,0,0.06); }
.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px;
  padding: 34px 0; text-align: center;
}
.stats-grid .stat-value { font-size: 1.9rem; font-weight: 800; color: var(--primary-dark); }
.stats-grid .stat-label { font-size: 0.88rem; opacity: 0.75; }

/* ---------- Sections generiques ---------- */
section { padding: 68px 0; }
section h2 { text-align: center; font-size: 1.9rem; margin-bottom: 44px; color: var(--primary-dark); letter-spacing: -0.01em; }

.services-grid, .pourquoi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 22px;
}
.card {
  background: #fff; border-radius: 16px; padding: 26px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  opacity: 0; transform: translateY(14px);
  transition: opacity 0.5s ease, transform 0.5s ease, box-shadow 0.2s ease, translate 0.2s ease;
}
.card.in-view { opacity: 1; transform: translateY(0); }
.card:hover { box-shadow: 0 10px 26px rgba(0,0,0,0.09); transform: translateY(-3px); }
.card.in-view:hover { transform: translateY(-3px); }
.icon-badge {
  width: 46px; height: 46px; border-radius: 50%; margin-bottom: 14px;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--accent) 16%, white);
  color: var(--accent);
}
.card h3 { font-size: 1.05rem; margin-bottom: 6px; color: var(--primary-dark); }
.card p { font-size: 0.92rem; opacity: 0.8; }

section.pourquoi { background: color-mix(in srgb, var(--background) 55%, white); }
.pourquoi-card { text-align: center; }
.pourquoi-card .icon-badge { margin-left: auto; margin-right: auto; }

/* ---------- Avis clients (uniquement des avis reels, choisis par l'artisan) ---------- */
.avis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 22px; }
.avis-card { text-align: left; }
.avis-stars { color: var(--accent); font-size: 0.95rem; margin-bottom: 10px; letter-spacing: 2px; }
.avis-card p { font-style: italic; margin-bottom: 12px; }
.avis-auteur { font-size: 0.85rem; font-weight: 700; opacity: 0.75; }

/* ---------- Devis ---------- */
section.devis { background: #fff; }
.devis-box {
  max-width: 580px; margin: 0 auto; background: var(--background);
  border-radius: 18px; padding: 36px; border: 1px solid rgba(0,0,0,0.06);
}
.devis-box label { display: block; font-weight: 600; margin: 14px 0 6px; font-size: 0.92rem; }
.devis-box input, .devis-box textarea {
  width: 100%; padding: 12px 14px; border-radius: 10px; border: 1.5px solid rgba(0,0,0,0.14);
  font-family: inherit; font-size: 0.98rem; background: #fff; transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.devis-box input:focus, .devis-box textarea:focus {
  outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent);
}
.devis-box textarea { min-height: 100px; resize: vertical; }
.devis-box button {
  margin-top: 24px; width: 100%; padding: 15px; border: none; border-radius: 999px;
  background: var(--primary); color: #fff; font-weight: 700; font-size: 1.03rem; cursor: pointer;
  transition: opacity 0.15s ease;
}
.devis-box button:disabled { opacity: 0.6; cursor: not-allowed; }
.form-message { margin-top: 16px; padding: 12px 14px; border-radius: 10px; font-size: 0.95rem; display: none; }
.form-message.success { display: block; background: #e7f7ee; color: #1e7e42; }
.form-message.error { display: block; background: #fdeaea; color: #b02a2a; }

/* ---------- Footer ---------- */
footer.site-footer { background: var(--primary-dark); color: rgba(255,255,255,0.82); padding: 44px 0 24px; font-size: 0.88rem; }
.footer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px; margin-bottom: 24px; }
.footer-grid h4 { color: #fff; font-size: 0.92rem; margin-bottom: 10px; }
.footer-grid p { margin: 3px 0; }
.footer-bottom { text-align: center; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.12); opacity: 0.7; }

@media (max-width: 760px) {
  nav.main-nav { display: none; }
  .hero h1 { font-size: 1.9rem; }
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__NOM_ENTREPRISE__ - __METIER_LABEL__ à __VILLE__</title>
<meta name="description" content="__NOM_ENTREPRISE__, __METIER_LABEL__ à __VILLE__ et environs. Devis gratuit sous 48h.">
__GOOGLE_FONT_LINK__
<style>
__CSS__
</style>
</head>
<body>

<header class="site-header" id="site-header">
  <div class="container">
    <div class="logo">__ICON_SMALL__ __NOM_ENTREPRISE__</div>
    <nav class="main-nav">
      <a href="#services">Prestations</a>
      <a href="#pourquoi">Pourquoi nous</a>
      <a href="#devis">Devis gratuit</a>
    </nav>
    <div class="header-actions">
      <a class="header-phone" href="tel:__TELEPHONE_HREF__">__ICON_PHONE__ __TELEPHONE__</a>
      <a class="btn-header-cta" href="#devis">Devis gratuit</a>
    </div>
  </div>
</header>

<section class="hero">
  <div class="container">
    <div class="hero-icon-badge">__ICON_HERO__</div>
    <h1>__NOM_ENTREPRISE__</h1>
    <p class="tagline">__TAGLINE__</p>
    <p class="zone">Intervention à __VILLE__ (__CODE_POSTAL__) et dans les environs</p>
    __PALETTE_SWATCHES__
    <div class="hero-actions">
      <a class="btn-cta" href="#devis">Demander un devis gratuit</a>
      <a class="btn-ghost" href="tel:__TELEPHONE_HREF__">__ICON_PHONE__ Appeler maintenant</a>
    </div>
  </div>
</section>

__STATS_SECTION__

<section id="services">
  <div class="container">
    <h2>Nos prestations</h2>
    <div class="services-grid">
      __SERVICES_CARDS__
    </div>
  </div>
</section>

<section class="pourquoi" id="pourquoi">
  <div class="container">
    <h2>Pourquoi nous choisir</h2>
    <div class="pourquoi-grid">
      __POURQUOI_CARDS__
    </div>
  </div>
</section>

__AVIS_SECTION__

<section class="devis" id="devis">
  <div class="container">
    <h2>Demander un devis gratuit</h2>
    <div class="devis-box">
      <form id="devis-form">
        <label for="client_nom">Nom et prénom *</label>
        <input type="text" id="client_nom" name="client_nom" required>

        <label for="client_telephone">Téléphone</label>
        <input type="tel" id="client_telephone" name="client_telephone">

        <label for="client_email">Email</label>
        <input type="email" id="client_email" name="client_email">

        <label for="description">Décrivez votre projet</label>
        <textarea id="description" name="description" placeholder="Ex: fuite d'eau sous l'évier de la cuisine..."></textarea>

        <button type="submit" id="devis-submit">Envoyer ma demande</button>
      </form>
      <div class="form-message" id="form-message"></div>
    </div>
  </div>
</section>

<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>__NOM_ENTREPRISE__</h4>
        <p>__ADRESSE_LIGNE__</p>
        <p>Tel : __TELEPHONE__</p>
      </div>
      <div>
        <h4>Informations légales</h4>
        <p>SIRET __SIRET__</p>
        <p>Assurance décennale : __ASSURANCE_DECENNALE__</p>
      </div>
    </div>
    <div class="footer-bottom">&copy; __ANNEE__ __NOM_ENTREPRISE__. Tous droits réservés.</div>
  </div>
</footer>

<script>
(function () {
  var API_BASE = "__API_BASE__";
  var SLUG = "__SLUG__";
  var form = document.getElementById("devis-form");
  var messageBox = document.getElementById("form-message");
  var submitBtn = document.getElementById("devis-submit");

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Envoi en cours...";
    messageBox.className = "form-message";

    var payload = {
      nom: document.getElementById("client_nom").value,
      telephone: document.getElementById("client_telephone").value || null,
      email: document.getElementById("client_email").value || null,
      message: document.getElementById("description").value || null
    };

    fetch(API_BASE + "/pub/" + SLUG + "/demande-devis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        if (!response.ok) { throw new Error("Erreur serveur"); }
        return response.json();
      })
      .then(function () {
        messageBox.textContent = "Merci ! Votre demande a bien été envoyée, nous vous recontactons rapidement.";
        messageBox.className = "form-message success";
        form.reset();
      })
      .catch(function () {
        messageBox.textContent = "Une erreur est survenue. Merci de nous appeler directement au __TELEPHONE__.";
        messageBox.className = "form-message error";
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = "Envoyer ma demande";
      });
  });

  var header = document.getElementById("site-header");
  window.addEventListener("scroll", function () {
    header.classList.toggle("scrolled", window.scrollY > 10);
  });

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add("in-view"); }
      });
    }, { threshold: 0.15 });
    document.querySelectorAll(".card").forEach(function (el) { observer.observe(el); });
  } else {
    document.querySelectorAll(".card").forEach(function (el) { el.classList.add("in-view"); });
  }
})();
</script>

</body>
</html>
"""


def _service_card(service: str) -> str:
    return (
        f'<div class="card"><div class="icon-badge">{ui_icon_svg("check", size=20)}</div>'
        f"<h3>{service}</h3></div>"
    )


def _pourquoi_card(icon_name: str, title: str, text: str) -> str:
    return (
        f'<div class="card pourquoi-card"><div class="icon-badge">{ui_icon_svg(icon_name, size=22)}</div>'
        f"<h3>{title}</h3><p>{text}</p></div>"
    )


def _avis_card(avis: dict) -> str:
    note = avis.get("note", 5)
    etoiles = "&#9733;" * note + "&#9734;" * (5 - note)
    commentaire = avis.get("commentaire") or ""
    auteur = avis.get("nom_auteur") or "Client"
    return (
        f'<div class="card avis-card"><div class="avis-stars">{etoiles}</div>'
        f'<p>&laquo;&nbsp;{commentaire}&nbsp;&raquo;</p><div class="avis-auteur">{auteur}</div></div>'
    )


def _avis_section(avis_list: list) -> str:
    """Section avis clients : n'apparait que si l'artisan a reellement des
    avis a montrer (jamais de temoignages fictifs pour "faire joli")."""
    if not avis_list:
        return ""
    cards = "\n      ".join(_avis_card(a) for a in avis_list)
    return f'''<section id="avis">
  <div class="container">
    <h2>Ce que disent nos clients</h2>
    <div class="avis-grid">
      {cards}
    </div>
  </div>
</section>'''


def _stats_section(stats: list) -> str:
    if not stats:
        return ""
    items = "\n      ".join(
        f'<div><div class="stat-value">{s["valeur"]}</div><div class="stat-label">{s["label"]}</div></div>'
        for s in stats
    )
    return f'<section class="stats-bar"><div class="container stats-grid">\n      {items}\n    </div></section>'


def _palette_swatches(palette: dict) -> str:
    colors = palette.get("palette_colors")
    if not colors:
        return ""
    spans = "".join(f'<span style="background:{c}"></span>' for c in colors)
    return f'<div class="palette-swatches">{spans}</div>'


def fetch_avis_publies(slug: str, api_base_url: str) -> list:
    """Recupere les avis que l'artisan a reellement choisi de publier (voir
    PATCH /avis/{id} cote SaaS). Renvoie [] silencieusement si l'API est
    injoignable : un site sans section avis reste un site valide, jamais
    d'avis invente pour compenser."""
    try:
        response = requests.get(f"{api_base_url.rstrip('/')}/pub/{slug}/avis", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


def generate_site(artisan: dict, api_base_url: str, output_path: str | None = None) -> str:
    """Genere le HTML du mini-site pour un artisan. Ecrit le fichier si
    output_path est fourni, et renvoie toujours le HTML en string.

    artisan["avis"] : liste optionnelle d'avis a afficher (chacun avec note/
    commentaire/nom_auteur). Si absente, recupere automatiquement les avis
    reellement publies par l'artisan via GET /pub/{slug}/avis - jamais de
    temoignage fictif genere pour "faire joli"."""

    from datetime import date

    if "avis" not in artisan:
        artisan = {**artisan, "avis": fetch_avis_publies(artisan["slug"], api_base_url)}

    if is_compatible_v3_profile(artisan.get("design_profile")):
        html_v3 = render_site_v3(artisan, api_base_url)
        if output_path:
            Path(output_path).write_text(html_v3, encoding="utf-8")
        return html_v3
    if is_compatible_design_profile(artisan.get("design_profile")):
        html_v2 = render_site_v2(artisan, api_base_url)
        if output_path:
            Path(output_path).write_text(html_v2, encoding="utf-8")
        return html_v2

    metier = artisan.get("metier", "general")
    theme = get_theme(metier)
    palette = get_palette(metier, artisan)
    motif = get_hero_motif(metier, artisan)

    services = artisan.get("services") or theme["services"]

    google_font = GOOGLE_FONTS.get(theme["font"])
    font_link = ""
    if google_font:
        font_link = (
            f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            f'<link href="https://fonts.googleapis.com/css2?family={google_font}&display=swap" rel="stylesheet">'
        )

    css = CSS_TEMPLATE
    css = css.replace("__PRIMARY__", palette["primary"])
    css = css.replace("__PRIMARY_DARK__", palette["primary_dark"])
    css = css.replace("__SECONDARY__", palette["secondary"])
    css = css.replace("__ACCENT__", palette["accent"])
    css = css.replace("__BACKGROUND__", palette["background"])
    css = css.replace("__TEXT__", palette["text"])
    css = css.replace("__FONT__", theme["font"])
    # Le bloc .hero{...} generique ci-dessus fixe position/overflow/padding ;
    # le motif ajoute son propre fond + pseudo-elements par-dessus.
    css += "\n.hero { position: relative; overflow: hidden; }\n"
    css += HERO_MOTIF_CSS.get(motif, HERO_MOTIF_CSS["wave-gradient"])

    services_cards = "\n      ".join(_service_card(s) for s in services)
    pourquoi_cards = "\n      ".join(_pourquoi_card(i, t, d) for i, t, d in POURQUOI_NOUS_CHOISIR)

    telephone = artisan.get("telephone") or "Nous contacter"
    telephone_href = "".join(ch for ch in telephone if ch.isdigit() or ch == "+")

    adresse_ligne = artisan.get("adresse") or f"{artisan.get('ville', '')} ({artisan.get('code_postal', '')})"

    html = HTML_TEMPLATE
    html = html.replace("__CSS__", css)
    html = html.replace("__GOOGLE_FONT_LINK__", font_link)
    html = html.replace("__NOM_ENTREPRISE__", artisan["nom_entreprise"])
    html = html.replace("__METIER_LABEL__", theme["label"])
    html = html.replace("__ICON_SMALL__", trade_icon_svg(metier, size=26))
    html = html.replace("__ICON_HERO__", trade_icon_svg(metier, size=34))
    html = html.replace("__ICON_PHONE__", ui_icon_svg("phone", size=16))
    html = html.replace("__TAGLINE__", artisan.get("tagline") or theme["tagline"])
    html = html.replace("__VILLE__", artisan.get("ville") or "")
    html = html.replace("__CODE_POSTAL__", artisan.get("code_postal") or "")
    html = html.replace("__TELEPHONE_HREF__", telephone_href)
    html = html.replace("__TELEPHONE__", telephone)
    html = html.replace("__PALETTE_SWATCHES__", _palette_swatches(palette))
    html = html.replace("__STATS_SECTION__", _stats_section(artisan.get("stats")))
    html = html.replace("__SERVICES_CARDS__", services_cards)
    html = html.replace("__POURQUOI_CARDS__", pourquoi_cards)
    html = html.replace("__AVIS_SECTION__", _avis_section(artisan.get("avis")))
    html = html.replace("__ADRESSE_LIGNE__", adresse_ligne)
    html = html.replace("__SIRET__", artisan.get("siret") or "en cours d'immatriculation")
    html = html.replace("__ASSURANCE_DECENNALE__", artisan.get("assurance_decennale_nom") or "nous consulter")
    html = html.replace("__ANNEE__", str(date.today().year))
    html = html.replace("__API_BASE__", api_base_url.rstrip("/"))
    html = html.replace("__SLUG__", artisan["slug"])

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Genere le mini-site vitrine d'un artisan")
    parser.add_argument("artisan_json", help="Chemin vers un fichier JSON decrivant l'artisan")
    parser.add_argument("--api-base", default="http://localhost:8000", help="URL de base de l'API Suite Artisan")
    parser.add_argument("--output", default="site.html", help="Fichier HTML de sortie")
    args = parser.parse_args()

    with open(args.artisan_json, encoding="utf-8") as f:
        artisan_data = json.load(f)

    generate_site(artisan_data, api_base_url=args.api_base, output_path=args.output)
    print(f"Site genere : {args.output}")
