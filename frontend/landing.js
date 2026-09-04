// =====================================================================
// Suite Artisan — landing.js
// -----------------------------------------------------------------------
// Orchestration de la landing publique : detection WebGL / reduced-motion,
// calcul de la progression de scroll (0..1) sur la timeline narrative,
// pilotage de la scene 3D (landing-scene.js) et des panneaux de texte,
// puis peuplement des tarifs/FAQ (donnees partagees : pricing.js).
//
// Aucune dependance a GSAP/ScrollTrigger : le pin de la scene est un
// simple `position: sticky` (CSS), et la progression de scroll est geree
// ici avec un seul listener rAF-throttle - plus simple a maintenir et a
// nettoyer qu'une librairie de scroll tierce pour ce besoin precis.
// =====================================================================

(function () {
  "use strict";

  const track = document.getElementById("scene-track");
  const canvas = document.getElementById("scene-canvas");
  const panels = Array.from(document.querySelectorAll(".scene-panel"));
  const progressBar = document.getElementById("scene-progress-bar");
  const databloom = document.getElementById("scene-databloom");
  const root = document.documentElement;

  const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function supportsWebGL() {
    try {
      const test = document.createElement("canvas");
      return !!(window.WebGLRenderingContext && (test.getContext("webgl") || test.getContext("experimental-webgl")));
    } catch (e) {
      return false;
    }
  }

  const use3D = !!(track && canvas && supportsWebGL() && !prefersReducedMotion);

  if (!use3D) {
    // Repli statique premium : chaque scene reste un vrai bloc de contenu
    // empile dans le flux normal (voir landing.css .no-3d), rien ne depend
    // du JS pour etre lisible - le texte et les CTA existent deja dans le
    // DOM, ils redeviennent simplement visibles sans mise en scene.
    root.classList.add("no-3d");
    if (canvas) canvas.remove();
  } else {
    root.classList.add("has-3d");
    startExperience();
  }

  async function startExperience() {
    let scene;
    try {
      const mod = await import("./landing-scene.js?v=3");
      scene = mod.initScene(canvas);
    } catch (err) {
      // Echec de chargement/initialisation (ex: contexte WebGL perdu,
      // module bloque) : on retombe proprement sur le mode statique plutot
      // que de laisser une page a moitie fonctionnelle.
      console.warn("Suite Artisan — scene 3D indisponible, repli statique.", err);
      root.classList.remove("has-3d");
      root.classList.add("no-3d");
      canvas.remove();
      return;
    }

    const isNarrow = window.innerWidth < 860;
    const isLowPower = (navigator.hardwareConcurrency || 8) <= 4;
    if (isNarrow || isLowPower) {
      const mod = await import("./landing-scene.js?v=3");
      mod.setQuality(scene, true);
    }

    let ticking = false;
    let trackTop = 0;
    let scrollRange = 1;

    // Recalcule a chaque appel (pas seulement au chargement) : au premier
    // rendu, la mise en page de #scene-track (haut de 900vh) peut ne pas
    // encore etre stabilisee au moment ou startExperience() s'execute, ce
    // qui figeait trackTop/scrollRange sur des valeurs perimees et bloquait
    // la progression a 0 pour tout le reste du scroll. getBoundingClientRect
    // est une lecture peu couteuse (aucune ecriture de style avant), donc la
    // rappeler a chaque scroll ne pese pas sur la performance.
    function measure() {
      const rect = track.getBoundingClientRect();
      trackTop = rect.top + window.scrollY;
      scrollRange = Math.max(1, track.offsetHeight - window.innerHeight);
    }

    function progressFor(el) {
      const [start, end] = (el.dataset.range || "0,1").split(",").map(Number);
      return { start, end };
    }

    // Fondu doux en entree/sortie de chaque panneau, plein a l'interieur
    // de sa plage - evite un "cut" brutal entre deux scenes.
    function panelOpacity(p, start, end) {
      const span = end - start;
      // Fenetre volontairement etroite : un fondu trop large fait se
      // chevaucher deux paragraphes de texte pendant la transition (illisible
      // si le scroll s'arrete pile a ce moment, ex. molette a crans). Rester
      // court garde un fondu perceptible sans jamais superposer deux blocs
      // de texte pleinement lisibles en meme temps.
      const fade = Math.min(0.018, span * 0.12);
      if (p < start - fade || p > end + fade) return 0;
      if (p < start) return (p - (start - fade)) / fade;
      if (p > end) return 1 - (p - end) / fade;
      return 1;
    }

    function updateDatabloom(p) {
      if (!databloom) return;
      const t = Math.max(0, Math.min(1, (p - 0.9) / 0.1));
      databloom.style.opacity = String(t);
      databloom.querySelectorAll(".scene-chip").forEach((chip, i) => {
        const scatterX = Number(chip.dataset.sx || 0);
        const scatterY = Number(chip.dataset.sy || 0);
        const gridX = Number(chip.dataset.gx || 0);
        const gridY = Number(chip.dataset.gy || 0);
        const local = Math.max(0, Math.min(1, t * 1.4 - i * 0.05));
        const x = scatterX + (gridX - scatterX) * local;
        const y = scatterY + (gridY - scatterY) * local;
        chip.style.transform = "translate(" + x + "px, " + y + "px) scale(" + (0.85 + local * 0.15) + ")";
        chip.style.opacity = String(Math.min(1, local * 1.6));
      });
    }

    function update() {
      ticking = false;
      measure();
      const p = Math.max(0, Math.min(1, (window.scrollY - trackTop) / scrollRange));
      scene && updateSceneSafe(p);
      panels.forEach((el) => {
        const { start, end } = progressFor(el);
        const op = panelOpacity(p, start, end);
        el.style.opacity = String(op);
        el.style.visibility = op > 0.02 ? "visible" : "hidden";
        el.setAttribute("aria-hidden", op > 0.02 ? "false" : "true");
      });
      if (progressBar) progressBar.style.transform = "scaleX(" + p + ")";
      updateDatabloom(p);
    }

    let sceneModulePromise = null;
    function updateSceneSafe(p) {
      // updateScene est importe une seule fois (module deja charge par
      // initScene) ; on le recupere via la meme promesse pour ne jamais
      // re-declencher un import.
      if (!sceneModulePromise) sceneModulePromise = import("./landing-scene.js?v=3");
      sceneModulePromise.then((mod) => mod.updateScene(scene, p));
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }

    function onResize() {
      measure();
      import("./landing-scene.js?v=3").then((mod) => mod.resizeScene(scene));
      update();
    }

    measure();
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);

    // Coupe le rendu quand la scene n'est plus a l'ecran (au-dela, sections
    // classiques) ou quand l'onglet est masque - economie GPU/batterie.
    // Une seule source de verite (trackIntersecting + tabVisible) evite les
    // etats incoherents entre deux observers concurrents.
    let trackIntersecting = true;
    function syncRunning() {
      const shouldRun = trackIntersecting && !document.hidden;
      sceneModulePromise = sceneModulePromise || import("./landing-scene.js?v=3");
      sceneModulePromise.then((mod) => { shouldRun ? mod.resumeScene(scene) : mod.pauseScene(scene); });
    }
    const io = new IntersectionObserver((entries) => {
      trackIntersecting = entries[0].isIntersecting;
      syncRunning();
    }, { threshold: 0 });
    io.observe(track);
    document.addEventListener("visibilitychange", syncRunning);

    window.addEventListener("beforeunload", () => {
      import("./landing-scene.js?v=3").then((mod) => mod.disposeScene(scene));
    });
  }

  // =====================================================================
  // Tarifs & FAQ — donnees partagees (pricing.js), rendu premium landing.
  // =====================================================================
  function renderPricingAndFaq() {
    if (typeof PRICING === "undefined") return;
    const plansEl = document.getElementById("landing-pricing-plans");
    if (plansEl) {
      plansEl.innerHTML = Object.entries(PRICING).map(([key, plan]) => {
        const isPro = plan.recommande === true;
        return `
        <div class="scene-plan-card${isPro ? " is-highlight" : ""}">
          ${isPro ? '<span class="scene-plan-badge">Recommandé</span>' : ""}
          <div class="scene-plan-name">${plan.nom}</div>
          <p class="scene-plan-accroche">${plan.accroche}</p>
          <div class="scene-plan-price">${plan.prix}&nbsp;&euro;<span>/ ${plan.periode}</span></div>
          <div class="scene-plan-mention">${plan.mention || "Sans engagement"}</div>
          <ul class="scene-plan-features">${plan.fonctionnalites.map((f) => `<li>${f}</li>`).join("")}</ul>
          <a href="index.html?tab=register" class="scene-btn ${isPro ? "scene-btn-primary" : "scene-btn-ghost"}">Commencer</a>
        </div>`;
      }).join("");
    }
    const offerEl = document.getElementById("landing-site-offer");
    if (offerEl && typeof SITE_VITRINE_OFFER !== "undefined") {
      offerEl.innerHTML = `
      <div class="scene-offer">
        <div>
          <div class="scene-offer-label">Option distincte du SaaS · Disponible avec tous les plans, y compris Gratuit</div>
          <h3>${SITE_VITRINE_OFFER.nom}</h3>
          <p class="scene-offer-benefit">${SITE_VITRINE_OFFER.accroche}</p>
          <p>${SITE_VITRINE_OFFER.description}</p>
        </div>
        <div class="scene-offer-price">
          <strong>${SITE_VITRINE_OFFER.creation}&nbsp;&euro; HT</strong> à la création
          <span>+ ${SITE_VITRINE_OFFER.mensuel}&nbsp;&euro; HT / mois de gestion &amp; maintenance</span>
        </div>
        <ul>${SITE_VITRINE_OFFER.carteInclus.map((item) => `<li>${item}</li>`).join("")}</ul>
        <p class="scene-offer-summary">${SITE_VITRINE_OFFER.resumeInclus}</p>
      </div>`;
    }
    const faqPrice = document.getElementById("faq-site-price");
    if (faqPrice && typeof SITE_VITRINE_OFFER !== "undefined") {
      faqPrice.innerHTML = `${SITE_VITRINE_OFFER.creation}&nbsp;&euro; ${SITE_VITRINE_OFFER.mention} à la création puis ${SITE_VITRINE_OFFER.mensuel}&nbsp;&euro; ${SITE_VITRINE_OFFER.mention}/mois de gestion &amp; maintenance`;
    }
    const faqCreation = document.getElementById("faq-site-creation");
    if (faqCreation && typeof SITE_VITRINE_OFFER !== "undefined") {
      faqCreation.innerHTML = SITE_VITRINE_OFFER.creationInclut.map((item) => `<li>${item}</li>`).join("");
    }
    const faqMaintenance = document.getElementById("faq-site-maintenance");
    if (faqMaintenance && typeof SITE_VITRINE_OFFER !== "undefined") {
      faqMaintenance.innerHTML = `<ul>${SITE_VITRINE_OFFER.maintenanceInclut.map((item) => `<li>${item}</li>`).join("")}</ul><p>${SITE_VITRINE_OFFER.domaineStandard}</p>`;
    }
    const faqHorsForfait = document.getElementById("faq-site-hors-forfait");
    if (faqHorsForfait && typeof SITE_VITRINE_OFFER !== "undefined") {
      faqHorsForfait.innerHTML = `<p>${SITE_VITRINE_OFFER.horsForfaitResume}</p><ul>${SITE_VITRINE_OFFER.horsForfait.map((item) => `<li>${item}</li>`).join("")}</ul>`;
    }
  }
  renderPricingAndFaq();

  // =====================================================================
  // Reveal au scroll pour les sections classiques (Produit/Metiers/CTA) —
  // simple toggle de classe via IntersectionObserver, anime en CSS pur.
  // Fonctionne aussi en mode .no-3d (juste une apparition douce).
  // =====================================================================
  const revealEls = document.querySelectorAll("[data-reveal]");
  if (revealEls.length) {
    if (prefersReducedMotion) {
      revealEls.forEach((el) => el.classList.add("is-revealed"));
    } else {
      const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      revealEls.forEach((el) => revealObserver.observe(el));
    }
  }
})();
