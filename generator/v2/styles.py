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

/* Six recognisable directions */
body.family-atelier { --container: 1100px; }
.family-atelier .hero { background: color-mix(in srgb, var(--color-primary-dark) 88%, #3f2f24); }
.family-atelier .hero-fallback { background-image: repeating-linear-gradient(105deg, transparent 0 28px, rgba(255,255,255,.06) 28px 30px); }
.family-atelier .section-heading h2 { font-weight: 700; }
.family-atelier .service-item { border-top: 5px solid var(--color-secondary); }
body.family-architecture { --container: 1260px; }
.family-architecture section { border-bottom: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
.family-architecture .hero-fallback { background-image: linear-gradient(90deg, transparent 49.7%, rgba(255,255,255,.28) 50%, transparent 50.3%), linear-gradient(transparent 49.7%, rgba(255,255,255,.18) 50%, transparent 50.3%); background-size: 90px 90px; }
.family-architecture .eyebrow { color: var(--color-text); }
.family-impact .hero h1 { text-transform: uppercase; font-weight: 950; }
.family-impact .hero-fallback { background-image: repeating-linear-gradient(125deg, transparent 0 40px, rgba(255,255,255,.1) 40px 80px); }
.family-impact .button-primary { box-shadow: 7px 7px 0 var(--color-secondary); }
.family-impact .section-heading { grid-template-columns: .35fr 1fr; align-items: end; }
.family-technique .hero-fallback { background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px); background-size: 24px 24px; }
.family-technique .service-item, .family-technique .quote-form { border-left: 5px solid var(--color-accent); }
.family-technique .eyebrow { font-family: monospace; }
.family-local .hero { background: var(--color-primary); }
.family-local .hero-fallback { background-image: repeating-linear-gradient(0deg, rgba(255,255,255,.07) 0 2px, transparent 2px 18px); }
.family-local .button { border-radius: 999px; }
.family-local .service-item { border-bottom: 4px solid var(--color-secondary); }
body.family-signature { --container: 1280px; }
.family-signature .hero { min-height: 700px; }
.family-signature .hero-fallback { background-image: linear-gradient(135deg, transparent 0 48%, rgba(255,255,255,.15) 48% 50%, transparent 50%); }
.family-signature .section-heading { justify-items: center; text-align: center; }
.family-signature .gallery-image, .family-signature .featured-image { min-height: 420px; }

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
