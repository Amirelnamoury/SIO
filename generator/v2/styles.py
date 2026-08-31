"""Shared, variant and family CSS for the V2 static renderer."""

from .context import SiteContext
from .tokens import design_tokens


BASE_CSS = r"""
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 90px; }
body { margin: 0; color: var(--color-text); background: var(--color-background); font-family: var(--font-body); line-height: 1.6; overflow-x: hidden; }
body, button, input, textarea { font-size: 16px; }
img { display: block; max-width: 100%; }
a { color: inherit; }
button, input, textarea, summary { font: inherit; }
:focus-visible { outline: 3px solid var(--color-secondary); outline-offset: 3px; }
.skip-link { position: fixed; z-index: 100; left: 12px; top: 12px; padding: 10px 14px; color: #151515; background: #ffffff; transform: translateY(-160%); }
.skip-link:focus { transform: translateY(0); }
.container { width: min(calc(100% - 40px), var(--container)); margin-inline: auto; }
section { padding-block: var(--space-section); }
h1, h2, h3 { margin: 0; font-family: var(--font-heading); line-height: 1.08; letter-spacing: 0; }
h1 { max-width: 14ch; font-size: clamp(2.45rem, 5.4vw, 5.9rem); }
h2 { max-width: 18ch; font-size: clamp(2rem, 3.5vw, 3.6rem); }
h3 { font-size: 1.2rem; }
p { margin: 0; }
.eyebrow { margin-bottom: 14px; color: var(--color-accent); font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .09em; }
.section-heading { display: grid; gap: 8px; margin-bottom: clamp(30px, 5vw, 60px); }
.button { min-height: 46px; display: inline-flex; align-items: center; justify-content: center; padding: 10px 18px; border: 1px solid transparent; border-radius: var(--radius-md); font-weight: 750; text-decoration: none; cursor: pointer; }
.button-primary { color: var(--color-on-accent); background: var(--color-accent); }
.button-secondary { color: var(--color-text); background: transparent; border-color: currentColor; }
.text-link { font-weight: 800; text-decoration-thickness: 2px; text-underline-offset: 4px; }

/* Header compositions */
.site-header { position: sticky; top: 0; z-index: 30; background: color-mix(in srgb, var(--color-background) 94%, transparent); border-bottom: 1px solid color-mix(in srgb, var(--color-text) 14%, transparent); backdrop-filter: blur(12px); }
.site-header.scrolled { box-shadow: 0 8px 30px rgba(0,0,0,.08); }
.site-brand { display: inline-flex; align-items: center; min-width: 0; color: var(--color-primary-dark); text-decoration: none; }
.brand-logo { width: auto; max-width: 190px; height: 48px; object-fit: contain; }
.brand-wordmark { font-family: var(--font-heading); font-size: 1.08rem; font-weight: 850; }
.main-nav { display: flex; align-items: center; gap: 22px; }
.main-nav a { font-size: .88rem; font-weight: 700; text-decoration: none; }
.header-actions { display: flex; align-items: center; gap: 14px; }
.header-phone { white-space: nowrap; font-size: .88rem; font-weight: 750; text-decoration: none; }
.header-classic-row, .header-minimal-row, .header-compact-row { min-height: 76px; display: flex; align-items: center; justify-content: space-between; gap: 22px; }
.header-minimal .container { width: min(calc(100% - 64px), 1320px); }
.header-minimal-row { min-height: 88px; }
.header-minimal .main-nav { margin-left: auto; }
.header-compact-row { min-height: 58px; }
.header-compact .brand-logo { height: 36px; }
.header-compact .header-cta { min-height: 38px; padding-block: 6px; }
.header-centered .container { padding-block: 10px 0; }
.header-meta { min-height: 32px; display: flex; justify-content: flex-end; align-items: center; gap: 18px; }
.header-brand-center { display: grid; place-items: center; padding: 5px 0 10px; }
.centered-nav { justify-content: center; min-height: 38px; border-top: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
.mobile-menu { display: none; }

/* Hero compositions */
.hero { position: relative; min-height: 560px; display: grid; align-items: center; overflow: hidden; background: var(--color-primary-dark); color: var(--color-on-primary); }
.hero .eyebrow { color: var(--color-secondary); }
.hero-lead { max-width: 580px; margin-top: 22px; font-size: clamp(1.05rem, 1.8vw, 1.3rem); }
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; }
.hero .button-secondary { color: inherit; }
.hero-copy { position: relative; z-index: 2; }
.hero-fallback { position: relative; width: 100%; min-height: 360px; overflow: hidden; background: var(--color-primary); }
.hero-fallback span { position: absolute; display: block; background: var(--color-secondary); opacity: .62; }
.hero-fallback span:nth-child(1) { width: 70%; height: 24%; right: -8%; top: 12%; transform: rotate(-8deg); }
.hero-fallback span:nth-child(2) { width: 46%; height: 42%; left: 10%; bottom: 8%; border: 1px solid color-mix(in srgb, white 48%, transparent); background: transparent; }
.hero-fallback span:nth-child(3) { width: 22%; height: 66%; right: 13%; bottom: -20%; background: var(--color-accent); }
.hero-image { width: 100%; height: 100%; object-fit: cover; }
.hero-fullscreen { min-height: min(820px, 88vh); }
.hero-media-full { position: absolute; inset: 0; }
.hero-media-full::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,.74), rgba(0,0,0,.08)); }
.hero-media-full .hero-fallback { height: 100%; }
.hero-overlay { padding-block: 100px; }
.hero-overlay .hero-copy { max-width: 760px; }
.hero-columns { display: grid; grid-template-columns: minmax(0, .9fr) minmax(360px, 1.1fr); align-items: stretch; gap: clamp(34px, 7vw, 100px); padding-block: 70px; }
.hero-visual { min-height: 500px; }
.hero-asymmetric-grid { display: grid; grid-template-columns: 1.15fr .85fr; align-items: center; gap: 36px; padding-block: 72px; }
.hero-aside { position: relative; align-self: stretch; min-height: 490px; margin-right: -7vw; }
.hero-index { position: absolute; right: 20px; bottom: 10px; font-family: var(--font-heading); font-size: 6rem; font-weight: 900; opacity: .18; }
.hero-compact { min-height: 410px; }
.hero-compact-row { display: grid; grid-template-columns: 1fr 280px; align-items: center; gap: 54px; padding-block: 58px; }
.hero-compact h1 { font-size: clamp(2.4rem, 4.5vw, 4.5rem); }
.hero-compact-mark { height: 260px; }
.hero-editorial-layout { display: grid; grid-template-columns: 90px minmax(0, .9fr) minmax(300px, .65fr); gap: 34px; align-items: end; padding-block: 78px; }
.hero-edition { align-self: stretch; writing-mode: vertical-rl; transform: rotate(180deg); font-weight: 800; text-transform: uppercase; letter-spacing: .12em; opacity: .65; }
.hero-editorial-media { height: 480px; }
.hero-card { background: var(--color-background); color: var(--color-text); }
.hero-card-stage { display: grid; grid-template-columns: .82fr 1.18fr; align-items: center; padding-block: 72px; }
.hero-card-panel { position: relative; z-index: 2; margin-right: -76px; padding: clamp(34px, 5vw, 72px); color: var(--color-on-primary); background: var(--color-primary-dark); border-radius: var(--radius-lg); }
.hero-card-media { min-height: 540px; }

/* Grid items with an image child default to min-width:auto, so a broken or
   slow-loading <img> (its HTML width/height attributes) can force its whole
   grid track wider than the container ("grid blowout") - this breaks the
   1fr mobile collapse used throughout (Lot 3.1b : bug reel trouve en
   inspection visuelle, corrige ici plutot que sur chaque grille au cas par
   cas). */
.hero-columns > *, .hero-asymmetric-grid > *, .hero-card-stage > *, .hero-compact-row > *,
.hero-editorial-layout > *, .about-layout > *, .featured-layout > *, .contact-layout > *,
.service-area-layout > * { min-width: 0; }

/* Content variants */
.services { background: var(--color-background); }
.services-layout { margin: 0; padding: 0; list-style: none; }
.services-cards .services-layout, .services-grid .services-layout { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-gap); }
.service-item { min-height: 190px; display: flex; flex-direction: column; justify-content: space-between; padding: 26px; background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); border-radius: var(--radius-lg); }
.services-grid .service-item { min-height: 145px; border-left: 5px solid var(--color-secondary); }
.service-number { color: var(--color-accent); font-family: var(--font-heading); font-size: .8rem; font-weight: 900; }
.services-editorial .services-layout { border-top: 1px solid var(--color-text); }
.service-editorial { display: grid; grid-template-columns: 90px 1fr; gap: 28px; align-items: center; padding: 24px 0; border-bottom: 1px solid color-mix(in srgb, var(--color-text) 24%, transparent); }
.service-editorial span { color: var(--color-accent); font-weight: 800; }
.service-editorial h3 { font-size: clamp(1.5rem, 3vw, 2.7rem); }
.services-list .services-layout { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0 40px; }
.services-list li { min-height: 62px; display: flex; align-items: center; gap: 18px; border-bottom: 1px solid color-mix(in srgb, var(--color-text) 18%, transparent); }
.services-list li span { color: var(--color-accent); font-size: .75rem; font-weight: 800; }
.services-alternating .services-layout { display: grid; }
.service-alternating { min-height: 108px; display: grid; grid-template-columns: 70px 1fr 22%; align-items: center; border-top: 1px solid color-mix(in srgb, var(--color-text) 22%, transparent); }
.service-alternating:nth-child(even) { padding-left: 12%; }
.service-alternating span { color: var(--color-accent); font-weight: 850; }
.service-alternating i { height: 2px; background: var(--color-secondary); }

.trust-strip { padding-block: 34px; color: var(--color-on-primary); background: var(--color-primary); }
.trust-inner { display: flex; align-items: center; gap: 22px; }
.trust-strip h2 { font-size: 1.35rem; }
.trust-strip .eyebrow { margin: 0; color: inherit; opacity: .75; }
.trust-symbol { width: 54px; height: 54px; display: grid; place-items: center; flex: 0 0 auto; border: 1px solid currentColor; border-radius: 50%; font-size: 1.4rem; }

.about { background: var(--color-surface); }
.about-layout { display: grid; grid-template-columns: 1fr .9fr; gap: clamp(42px, 9vw, 130px); align-items: center; }
.about-copy ul { display: grid; gap: 12px; margin: 28px 0 0; padding: 0; list-style: none; }
.about-copy li { padding: 12px 0; border-bottom: 1px solid color-mix(in srgb, var(--color-text) 15%, transparent); }
.about-visual, .about-image { min-height: 390px; width: 100%; object-fit: cover; }
.about-monogram { position: relative; min-height: 390px; overflow: hidden; background: var(--color-primary); }
.about-monogram span { position: absolute; display: block; background: var(--color-secondary); }
.about-monogram span:nth-child(1) { inset: 14% 18% auto; height: 24%; }
.about-monogram span:nth-child(2) { inset: auto 12% 12% 42%; height: 48%; opacity: .7; }
.about-monogram span:nth-child(3) { width: 34%; height: 34%; left: 10%; bottom: 14%; border: 1px solid color-mix(in srgb, white 55%, transparent); background: transparent; }
.about-editorial .about-layout { grid-template-columns: .35fr 1fr .8fr; }
.about-editorial-title { align-self: stretch; color: var(--color-primary); font-family: var(--font-heading); font-size: clamp(3rem, 7vw, 7rem); font-weight: 900; writing-mode: vertical-rl; opacity: .12; }
.about-compact { padding-block: 50px; }
.about-compact .about-layout { grid-template-columns: 1fr auto; }
.about-compact-aside { padding: 22px; color: var(--color-on-primary); background: var(--color-primary); font-family: var(--font-heading); font-weight: 800; }

.gallery { background: color-mix(in srgb, var(--color-background) 70%, white); }
.gallery-layout { display: grid; gap: 14px; }
.gallery-item { margin: 0; overflow: hidden; background: var(--color-primary); }
.gallery-image { width: 100%; height: 100%; min-height: 280px; object-fit: cover; }
.gallery-grid .gallery-layout { grid-template-columns: repeat(3, 1fr); }
.gallery-masonry .gallery-layout { grid-template-columns: repeat(3, 1fr); grid-auto-rows: 180px; }
.gallery-masonry .gallery-item:nth-child(3n+1) { grid-row: span 2; }
.gallery-masonry .gallery-image { min-height: 100%; }
.gallery-featured .gallery-layout { grid-template-columns: 1.7fr 1fr; grid-auto-rows: 230px; }
.gallery-featured .gallery-item:first-child { grid-row: span 2; }
.gallery-featured .gallery-image { min-height: 100%; }
.gallery-horizontal .gallery-layout { grid-auto-flow: column; grid-auto-columns: minmax(320px, 48%); overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 12px; }
.gallery-horizontal .gallery-item { scroll-snap-align: start; }
.image-duotone img { filter: grayscale(1) sepia(.2) contrast(1.08); mix-blend-mode: multiply; }
.image-framed img { border: 10px solid var(--color-surface); outline: 1px solid color-mix(in srgb, var(--color-text) 18%, transparent); }
.image-overlay .gallery-item, .image-overlay .hero-card-media, .image-overlay .hero-visual { position: relative; }
.image-overlay img { opacity: .82; }

.reviews { background: var(--color-primary-dark); color: var(--color-on-primary); }
.reviews .eyebrow { color: var(--color-secondary); }
.reviews-layout { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-gap); }
.review-item { margin: 0; padding: 28px; border: 1px solid color-mix(in srgb, currentColor 22%, transparent); border-radius: var(--radius-lg); }
.review-stars { color: var(--color-secondary); letter-spacing: .12em; }
.review-item blockquote { margin: 24px 0; font-family: var(--font-heading); font-size: 1.22rem; line-height: 1.45; }
.review-item figcaption { font-size: .88rem; font-weight: 800; opacity: .78; }
.reviews-featured .reviews-layout { grid-template-columns: 1.5fr repeat(2, .75fr); }
.reviews-featured .review-item:first-child blockquote { font-size: clamp(1.5rem, 2.8vw, 2.5rem); }
.reviews-minimal .reviews-layout { grid-template-columns: 1fr; }
.reviews-minimal .review-item { padding: 22px 0; border-width: 0 0 1px; }

.stats { padding-block: 44px; background: var(--color-secondary); }
.stats-layout { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 28px; }
.stat { display: grid; gap: 3px; }
.stat strong { font-family: var(--font-heading); font-size: 2rem; }
.stat span { font-size: .88rem; }
.featured-project { background: var(--color-surface); }
.featured-layout { display: grid; grid-template-columns: .55fr 1.45fr; gap: 50px; align-items: start; }
.featured-image { width: 100%; min-height: 520px; object-fit: cover; }
.before-after-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.before-after figure { position: relative; margin: 0; }
.before-after-image { width: 100%; height: 460px; object-fit: cover; }
.before-after figcaption { position: absolute; left: 16px; bottom: 16px; padding: 6px 12px; color: white; background: #151515; font-weight: 800; }
.process ol, .reasons ul { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 0; padding: 0; list-style: none; }
.process li, .reasons li { min-height: 140px; padding: 24px; border: 1px solid color-mix(in srgb, var(--color-text) 18%, transparent); }
.process li span { display: block; margin-bottom: 20px; color: var(--color-accent); font-weight: 900; }
.service-area { color: var(--color-on-primary); background: var(--color-primary); }
.service-area .eyebrow { color: var(--color-secondary); }
.service-area-layout { display: grid; grid-template-columns: .4fr 1fr; align-items: end; gap: 40px; }

.cta { padding-block: 58px; }
.cta-layout { display: flex; justify-content: space-between; align-items: center; gap: 34px; }
.cta-actions { display: flex; flex-wrap: wrap; gap: 12px; }
.cta-banner { color: var(--color-on-primary); background: var(--color-primary-dark); }
.cta-banner .eyebrow { color: var(--color-secondary); }
.cta-floating { padding-block: 0; background: linear-gradient(var(--color-background) 50%, var(--color-primary-dark) 50%); }
.cta-floating-panel { width: 100%; display: flex; align-items: center; gap: 24px; padding: 42px; color: var(--color-on-primary); background: var(--color-primary); box-shadow: 0 20px 60px rgba(0,0,0,.16); }
.cta-floating-panel h2 { margin-right: auto; }
.cta-minimal .cta-layout { border-block: 1px solid currentColor; padding-block: 34px; }

.contact { background: var(--color-surface); }
.contact-layout { display: grid; grid-template-columns: .72fr 1.28fr; gap: clamp(44px, 9vw, 120px); align-items: start; }
.contact-details { display: grid; gap: 12px; margin-top: 36px; }
.contact-details a, .contact-details div { display: grid; gap: 2px; padding-block: 13px; border-bottom: 1px solid color-mix(in srgb, var(--color-text) 14%, transparent); text-decoration: none; }
.contact-details span { color: var(--color-muted); font-size: .78rem; text-transform: uppercase; }
.quote-form { display: grid; gap: 18px; padding: clamp(24px, 4vw, 48px); background: var(--color-background); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); border-radius: var(--radius-lg); }
.field { display: grid; gap: 7px; }
.field label { font-size: .84rem; font-weight: 750; }
.field input, .field textarea { width: 100%; min-height: 48px; padding: 11px 13px; color: var(--color-text); background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 32%, transparent); border-radius: var(--radius-sm); }
.field textarea { min-height: 130px; resize: vertical; }
.form-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-message { min-height: 24px; font-weight: 700; }
.form-message.success { color: #176b3a; }
.form-message.error { color: #a12121; }

.site-footer { padding-block: 54px 24px; color: white; background: #181a1d; }
.site-footer .site-brand { color: white; }
.footer-brand .brand-logo { filter: drop-shadow(0 0 1px white); }
.footer-columns { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 54px; }
.footer-columns h2 { margin-bottom: 16px; font-size: .9rem; text-transform: uppercase; }
.footer-columns div > a, .footer-columns div > span { display: block; margin-bottom: 8px; }
.footer-centered { display: grid; justify-items: center; gap: 14px; text-align: center; }
.footer-centered div { display: flex; flex-wrap: wrap; justify-content: center; gap: 16px; }
.footer-simple { display: flex; justify-content: space-between; align-items: center; gap: 28px; }
.footer-simple div { display: grid; gap: 4px; }
.copyright { margin-top: 42px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,.16); font-size: .78rem; opacity: .65; }
.mobile-action-bar { display: none; }

/* ============================================================
   Six directions artistiques - systemes distincts (Lot 3.1).
   Chaque famille reecrit typographie, rythme vertical, boutons,
   decoration ET fallbacks sans photo - pas seulement une couleur
   ou un motif de fond en filigrane (cause de l'effet "template"
   du Lot 3 : voir le rapport). Les identifiants de variantes
   (header-classic-row, hero-columns...) restent inchanges : seule
   l'habillage visuel par famille est renforce ici.
   ============================================================ */

/* --- ATELIER : chaleureux, artisanal, tactile --- */
body.family-atelier { --container: 1100px; }
.family-atelier h1, .family-atelier h2 { font-weight: 750; letter-spacing: -.005em; }
.family-atelier .eyebrow { text-transform: none; font-weight: 800; }
.family-atelier .eyebrow::before { content: "●"; margin-right: 8px; font-size: .55em; color: var(--color-secondary); }
.family-atelier section:nth-of-type(even) { padding-block: calc(var(--space-section) * 1.12); }
.family-atelier .button, .family-atelier .header-cta { border-radius: 999px; }
.family-atelier .button-primary { box-shadow: 0 14px 30px -14px color-mix(in srgb, var(--color-accent) 75%, transparent); }
.family-atelier .service-item { border-top: 5px solid var(--color-secondary); border-radius: var(--radius-lg) var(--radius-lg) 6px 6px; }
.family-atelier .review-item, .family-atelier .quote-form { border-radius: var(--radius-lg); }
.family-atelier .hero { background: color-mix(in srgb, var(--color-primary-dark) 88%, #3f2f24); }
.family-atelier .hero-fallback, .family-atelier .about-monogram { background: radial-gradient(120% 140% at 18% 16%, color-mix(in srgb, var(--color-secondary) 55%, transparent), transparent 60%), var(--color-primary); }
.family-atelier .hero-fallback span, .family-atelier .about-monogram span { border-radius: 46% 54% 58% 42% / 50% 44% 56% 50%; opacity: .55; background: color-mix(in srgb, var(--color-secondary) 80%, transparent); border-color: transparent; }
.family-atelier .hero-fallback span:nth-child(1) { transform: rotate(-6deg); }
.family-atelier .hero-fallback span:nth-child(3), .family-atelier .about-monogram span:nth-child(3) { background: var(--color-accent); border-radius: 60% 40% 45% 55% / 55% 60% 40% 45%; }
.family-atelier .footer-simple, .family-atelier .footer-centered { border-top: 3px solid var(--color-secondary); }

/* --- ARCHITECTURE : premium, minimal, editorial --- */
body.family-architecture { --container: 1260px; --font-heading: Georgia, 'Iowan Old Style', 'Times New Roman', serif; --space-section: calc(var(--space-section) * 1.32); }
.family-architecture section { border-bottom: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
.family-architecture h1 { font-weight: 400; letter-spacing: -.015em; line-height: 1.02; }
.family-architecture h2 { font-weight: 400; }
.family-architecture .eyebrow { color: var(--color-text); font-weight: 600; letter-spacing: .18em; }
.family-architecture .button-primary { border-radius: 2px; box-shadow: none; padding-inline: 26px; font-size: .82rem; letter-spacing: .06em; text-transform: uppercase; }
.family-architecture .button-secondary { border-radius: 2px; }
.family-architecture .service-item, .family-architecture .review-item, .family-architecture .quote-form { border-radius: 2px; }
.family-architecture .hero-fallback, .family-architecture .about-monogram { background: linear-gradient(115deg, color-mix(in srgb, var(--color-primary) 92%, black) 0 62%, color-mix(in srgb, var(--color-secondary) 40%, var(--color-primary)) 62% 100%); }
.family-architecture .hero-fallback span, .family-architecture .about-monogram span { border-radius: 0; background: transparent; border: 1px solid color-mix(in srgb, white 32%, transparent); opacity: .55; }
.family-architecture .hero-fallback span:nth-child(3), .family-architecture .about-monogram span:nth-child(3) { background: color-mix(in srgb, white 12%, transparent); border: none; }
.family-architecture .footer-columns { border-top: 1px solid color-mix(in srgb, white 16%, transparent); padding-top: 40px; }

/* --- IMPACT : energique, commercial, direct --- */
.family-impact h1 { text-transform: uppercase; font-weight: 950; letter-spacing: -.02em; line-height: .96; }
.family-impact .hero h1 { font-size: clamp(2.7rem, 6.4vw, 6.6rem); }
.family-impact .eyebrow { display: inline-block; padding: 5px 12px; color: var(--color-on-accent); background: var(--color-accent); letter-spacing: .06em; }
.family-impact .button-primary { min-height: 56px; padding-inline: 26px; border-radius: 0; box-shadow: 7px 7px 0 var(--color-secondary); font-size: 1.02rem; }
.family-impact .button-secondary { border-radius: 0; border-width: 2px; }
.family-impact .section-heading { grid-template-columns: .35fr 1fr; align-items: end; }
.family-impact .cta { padding-block: calc(var(--space-section) * 1.15); }
.family-impact .hero-fallback, .family-impact .about-monogram { background: linear-gradient(125deg, var(--color-primary) 0 46%, var(--color-accent) 46% 54%, var(--color-primary-dark) 54% 100%); }
.family-impact .hero-fallback span, .family-impact .about-monogram span { border-radius: 0; opacity: .85; background: color-mix(in srgb, white 20%, var(--color-secondary)); border-color: transparent; }
.family-impact .service-item { border-radius: 0; border-top: 6px solid var(--color-accent); }
.family-impact .site-footer { background: #0d0e10; }

/* --- TECHNIQUE : structure, precis, fiable --- */
.family-technique { --space-section: calc(var(--space-section) * .84); }
.family-technique h1, .family-technique h2 { font-weight: 640; letter-spacing: -.01em; }
.family-technique .eyebrow { font-family: 'Courier New', monospace; letter-spacing: .04em; }
.family-technique .section-heading { border-left: 2px solid var(--color-accent); padding-left: 16px; }
.family-technique .service-item, .family-technique .quote-form, .family-technique .review-item { border-left: 5px solid var(--color-accent); border-radius: 0; }
.family-technique .button { border-radius: 0; }
.family-technique .button-primary { border: 1px solid var(--color-accent); }
.family-technique .hero-fallback, .family-technique .about-monogram { background-image: linear-gradient(rgba(255,255,255,.14) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.14) 1px, transparent 1px); background-size: 22px 22px; background-color: var(--color-primary-dark); }
.family-technique .hero-fallback span, .family-technique .about-monogram span { border-radius: 0; background: transparent; border: 1px solid color-mix(in srgb, white 45%, transparent); opacity: .8; }
.family-technique .hero-fallback span:nth-child(3), .family-technique .about-monogram span:nth-child(3) { background: var(--color-accent); border: none; }
.family-technique .site-footer { border-top: 4px solid var(--color-accent); }

/* --- LOCAL : proximite, confiance, accessible --- */
.family-local { --space-section: calc(var(--space-section) * .93); }
.family-local h1, .family-local h2 { font-weight: 720; }
.family-local .hero { background: var(--color-primary); }
.family-local .button, .family-local .header-cta { border-radius: 999px; }
.family-local .service-item { border-radius: var(--radius-lg); border-bottom: 4px solid var(--color-secondary); }
.family-local .header-phone { padding: 6px 12px; border-radius: 999px; background: color-mix(in srgb, var(--color-accent) 14%, transparent); }
.family-local .hero-fallback, .family-local .about-monogram { background: radial-gradient(38% 55% at 74% 30%, color-mix(in srgb, var(--color-secondary) 60%, transparent), transparent), radial-gradient(30% 45% at 24% 78%, color-mix(in srgb, var(--color-accent) 55%, transparent), transparent), var(--color-primary); }
.family-local .hero-fallback span, .family-local .about-monogram span { border-radius: 50%; opacity: .5; background: color-mix(in srgb, white 15%, var(--color-secondary)); border-color: transparent; }
.family-local .footer-simple a, .family-local .footer-centered a { font-weight: 800; }

/* --- SIGNATURE : haut de gamme, magazine, photographique --- */
body.family-signature { --container: 1300px; --font-heading: 'Bodoni MT', Didot, Georgia, serif; --space-section: calc(var(--space-section) * 1.42); }
.family-signature h1 { font-weight: 300; letter-spacing: -.025em; line-height: .96; }
.family-signature .hero h1 { font-size: clamp(2.9rem, 6.6vw, 7.4rem); }
.family-signature .eyebrow { font-size: .68rem; letter-spacing: .22em; opacity: .8; }
.family-signature .section-heading { justify-items: center; text-align: center; gap: 16px; }
.family-signature .button-primary { border-radius: 999px; box-shadow: none; }
.family-signature .button-secondary { border: none; text-decoration: underline; text-underline-offset: 5px; }
.family-signature .hero { min-height: 700px; }
.family-signature .gallery-image, .family-signature .featured-image { min-height: 420px; }
.family-signature .hero-fallback, .family-signature .about-monogram { background: linear-gradient(150deg, var(--color-primary-dark) 0 55%, color-mix(in srgb, var(--color-secondary) 45%, var(--color-primary)) 55% 100%); }
.family-signature .hero-fallback span, .family-signature .about-monogram span { border-radius: 0; background: transparent; border: 1px solid color-mix(in srgb, white 36%, transparent); opacity: .45; }
.family-signature .site-footer { padding-block: 90px 30px; }
.family-signature .footer-simple { flex-direction: column; align-items: center; gap: 14px; text-align: center; }
.family-signature .footer-columns { justify-items: center; text-align: center; }

/* --- Traitements d'image (Lot 3.1 : plus perceptibles, sans wrapper DOM) --- */
.image-framed img { border: 12px solid var(--color-surface); outline: 1px solid color-mix(in srgb, var(--color-text) 20%, transparent); box-shadow: 0 18px 40px -18px rgba(0,0,0,.35); }
.image-duotone img { filter: grayscale(1) sepia(.35) hue-rotate(-8deg) saturate(1.5) contrast(1.05); }
.image-overlay img { filter: brightness(.92) contrast(1.06); box-shadow: inset 0 -140px 120px -70px color-mix(in srgb, var(--color-primary-dark) 70%, black); }

@media (max-width: 1024px) {
  .main-nav, .site-header .header-phone, .site-header .header-cta, .header-meta { display: none; }
  .mobile-menu { display: block; margin-left: auto; }
  .mobile-menu summary { min-width: 48px; min-height: 44px; display: grid; place-items: center; cursor: pointer; font-weight: 800; list-style: none; }
  .mobile-menu[open] nav { position: absolute; left: 20px; right: 20px; top: calc(100% + 8px); display: grid; gap: 4px; padding: 16px; color: var(--color-text); background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 18%, transparent); box-shadow: 0 14px 34px rgba(0,0,0,.16); }
  .mobile-menu nav a { min-height: 44px; display: flex; align-items: center; padding-inline: 10px; text-decoration: none; }
  .mobile-menu .header-phone, .mobile-menu .header-cta { display: flex; }
  .header-centered .container { min-height: 70px; display: flex; align-items: center; }
  .header-brand-center { justify-items: start; }
  .hero-columns, .hero-asymmetric-grid, .hero-card-stage { grid-template-columns: 1fr 1fr; gap: 30px; }
  .hero-editorial-layout { grid-template-columns: 50px 1fr; }
  .hero-editorial-media { display: none; }
  .services-cards .services-layout, .services-grid .services-layout, .reviews-layout { grid-template-columns: repeat(2, 1fr); }
  .reviews-featured .reviews-layout { grid-template-columns: 1fr 1fr; }
  .about-editorial .about-layout { grid-template-columns: 80px 1fr; }
  .about-editorial .about-image, .about-editorial .about-monogram { display: none; }
}

@media (max-width: 768px) {
  :root { --space-section: 58px; }
  .container { width: min(calc(100% - 32px), var(--container)); }
  .hero { min-height: auto; }
  .hero-fullscreen { min-height: 650px; }
  .hero-overlay { padding-block: 80px; }
  .hero-columns, .hero-asymmetric-grid, .hero-card-stage, .hero-compact-row, .about-layout, .about-editorial .about-layout, .contact-layout, .featured-layout, .service-area-layout { grid-template-columns: 1fr; }
  .hero-columns, .hero-asymmetric-grid { padding-block: 56px; }
  .hero-columns .hero-visual, .hero-aside, .hero-card-media { min-height: 300px; height: 300px; margin: 0; }
  .hero-card-panel { margin: 0 0 -42px; }
  .hero-compact-mark { display: none; }
  .hero-editorial-layout { grid-template-columns: 1fr; }
  .hero-edition { writing-mode: initial; transform: none; }
  .services-cards .services-layout, .services-grid .services-layout, .reviews-layout, .reviews-featured .reviews-layout, .services-list .services-layout, .process ol, .reasons ul { grid-template-columns: 1fr; }
  .service-alternating, .service-alternating:nth-child(even) { grid-template-columns: 50px 1fr; padding-left: 0; }
  .service-alternating i { display: none; }
  .gallery-grid .gallery-layout, .gallery-masonry .gallery-layout, .gallery-featured .gallery-layout { grid-template-columns: 1fr 1fr; grid-auto-rows: 210px; }
  .gallery-featured .gallery-item:first-child { grid-column: span 2; }
  .gallery-horizontal .gallery-layout { grid-auto-columns: 86%; }
  .about-visual, .about-image, .about-monogram { min-height: 300px; }
  .about-editorial-title { display: none; }
  .about-compact .about-layout { grid-template-columns: 1fr; }
  .before-after-image { height: 320px; }
  .cta-layout, .cta-floating-panel, .footer-simple { align-items: flex-start; flex-direction: column; }
  .cta-floating-panel { padding: 30px 24px; }
  .footer-columns { grid-template-columns: 1fr 1fr; }
  .mobile-action-bar { position: fixed; z-index: 40; left: 0; right: 0; bottom: 0; display: grid; grid-template-columns: repeat(var(--mobile-actions), 1fr); padding: 8px max(8px, env(safe-area-inset-left)) calc(8px + env(safe-area-inset-bottom)); background: #ffffff; border-top: 1px solid #d6d6d6; }
  .mobile-action-bar a { min-height: 46px; display: grid; place-items: center; color: #151515; font-size: .86rem; font-weight: 800; text-decoration: none; }
  .mobile-action-bar a:last-child { color: var(--color-on-accent); background: var(--color-accent); }
  body { padding-bottom: 62px; }

  /* Barre CTA mobile configurable par famille (Lot 3.1, section 8) */
  .mobile-action-bar--architecture { background: var(--color-surface); border-top: 1px solid color-mix(in srgb, var(--color-text) 16%, transparent); }
  .mobile-action-bar--architecture a { color: var(--color-text); font-weight: 700; letter-spacing: .04em; text-transform: uppercase; font-size: .78rem; }
  .mobile-action-bar--technique { padding-block: 5px; }
  .mobile-action-bar--technique a { font-size: .8rem; }
  .mobile-action-bar--signature { left: auto; right: 14px; bottom: 14px; width: auto; display: block; padding: 0; background: transparent; border: none; }
  .mobile-action-bar--signature a { min-width: 168px; padding-inline: 24px; border-radius: 999px; color: var(--color-on-accent); background: var(--color-accent); box-shadow: 0 12px 30px -8px rgba(0,0,0,.4); }

  /* Familles : le mobile ne doit pas s'effondrer vers la meme pile
     header -> hero -> CTA -> image -> sticky bar pour tout le monde
     (Lot 3.1, section 7 - point critique). */
  .family-impact .hero { min-height: 560px; }
  .family-impact .hero h1 { font-size: clamp(2.6rem, 11vw, 4.2rem); }
  .family-architecture h1, .family-signature h1 { font-size: clamp(2.5rem, 10vw, 4.2rem); }
  .family-architecture section, .family-signature section { padding-block: calc(var(--space-section) * .8); }
  .family-atelier .hero-copy, .family-atelier .about-copy { margin-left: 14px; }
  .family-technique .reasons ul, .family-technique .process ol, .family-technique .services-list .services-layout { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .family-technique .service-item, .family-technique .reasons li, .family-technique .process li { padding: 14px; min-height: auto; }
  .family-local .service-area, .family-local .trust-strip { border-radius: var(--radius-lg); margin-inline: 4px; }
  .family-signature .hero-index { display: none; }
}

@media (max-width: 430px) {
  .container { width: min(calc(100% - 24px), var(--container)); }
  h1 { font-size: 2.55rem; }
  h2 { font-size: 2rem; }
  .hero-fullscreen { min-height: 590px; }
  .hero-actions, .cta-actions { align-items: stretch; flex-direction: column; }
  .hero-actions .button, .cta-actions .button { width: 100%; }
  .gallery-grid .gallery-layout, .gallery-masonry .gallery-layout, .gallery-featured .gallery-layout { grid-template-columns: 1fr; grid-auto-rows: auto; }
  .gallery-featured .gallery-item:first-child { grid-column: auto; }
  .gallery-image { min-height: 260px; }
  .before-after-layout, .form-columns, .footer-columns { grid-template-columns: 1fr; }
  .before-after-image { height: 280px; }
  .service-editorial { grid-template-columns: 45px 1fr; }
  .family-impact .section-heading { grid-template-columns: 1fr; align-items: start; }
  .quote-form { padding: 20px 16px; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }
}
"""


def render_css(ctx: SiteContext) -> str:
    return design_tokens(ctx) + "\n" + BASE_CSS
