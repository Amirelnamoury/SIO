// =====================================================================
// Suite Artisan — landing.js
// -----------------------------------------------------------------------
// Animations de la landing PUBLIQUE uniquement (aucun code SaaS ici) :
//   - reveal au scroll (IntersectionObserver + classe CSS)
//   - compteurs chiffres qui montent
//   - parallaxe legere sur les elements decoratifs
//   - barre de progression qui se remplit
//   - ombre de la nav quand on quitte le haut de page
//   - tarifs & FAQ remplis depuis pricing.js (donnees reelles partagees)
//
// Aucune dependance externe (pas de Three.js, pas de GSAP) : tout est en
// JS natif + CSS, donc rien de lourd a charger et aucun risque de
// saccade liee a un rendu 3D.
//
// prefers-reduced-motion est respecte partout : dans ce cas, aucun
// mouvement n'est declenche et les valeurs finales sont posees
// directement (le contenu reste integralement lisible).
// =====================================================================

(function () {
  "use strict";

  var reduceMotion = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------
  // 1. Tarifs & FAQ — donnees partagees avec le SaaS (pricing.js), en
  //    lecture seule : la landing ne fait que les afficher.
  // ---------------------------------------------------------------
  function euro(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  }

  function renderPlans() {
    var host = document.getElementById("lp-plans");
    if (!host || typeof PRICING === "undefined") return;
    var order = (typeof PRICING_ORDRE !== "undefined") ? PRICING_ORDRE : Object.keys(PRICING);

    host.innerHTML = order.map(function (key) {
      var plan = PRICING[key];
      if (!plan) return "";
      var reco = plan.recommande === true;
      return ''
        + '<div class="lp-plan' + (reco ? " is-reco" : "") + '">'
        + (reco ? '<span class="lp-plan-badge">Recommandé</span>' : "")
        + '<div class="lp-plan-name">' + plan.nom + "</div>"
        + '<p class="lp-plan-hook">' + plan.accroche + "</p>"
        + '<div class="lp-plan-price">' + euro(plan.prix) + " €<span> / " + plan.periode + "</span></div>"
        + '<div class="lp-plan-mention">' + (plan.mention || "Sans engagement") + "</div>"
        + '<ul class="lp-plan-feats">'
        + plan.fonctionnalites.map(function (f) { return "<li>" + f + "</li>"; }).join("")
        + "</ul>"
        + '<a href="index.html?tab=register" class="lp-btn ' + (reco ? "lp-btn-primary" : "lp-btn-ghost") + '">Commencer</a>'
        + "</div>";
    }).join("");
  }

  function renderSiteOffer() {
    if (typeof SITE_VITRINE_OFFER === "undefined") return;
    var o = SITE_VITRINE_OFFER;

    var host = document.getElementById("lp-site-offer");
    if (host) {
      host.innerHTML = ''
        + '<div class="lp-offer">'
        + '<div class="lp-offer-tag">Option distincte du SaaS · Disponible avec tous les plans, y compris Gratuit</div>'
        + "<h3>" + o.nom + "</h3>"
        + '<p class="lp-offer-hook">' + o.accroche + "</p>"
        + "<p>" + o.description + "</p>"
        + '<div class="lp-offer-price"><strong>' + euro(o.creation) + " € HT à la création</strong>"
        + "<span>puis " + euro(o.mensuel) + " € HT / mois de gestion &amp; maintenance</span></div>"
        + "<ul>" + o.carteInclus.map(function (i) { return "<li>" + i + "</li>"; }).join("") + "</ul>"
        + '<p class="lp-offer-sum">' + o.resumeInclus + "</p>"
        + "</div>";
    }

    var price = document.getElementById("faq-site-price");
    if (price) {
      price.innerHTML = euro(o.creation) + " € " + o.mention + " à la création puis "
        + euro(o.mensuel) + " € " + o.mention + "/mois de gestion &amp; maintenance";
    }
    var creation = document.getElementById("faq-site-creation");
    if (creation) {
      creation.innerHTML = o.creationInclut.map(function (i) { return "<li>" + i + "</li>"; }).join("");
    }
    var maint = document.getElementById("faq-site-maintenance");
    if (maint) {
      maint.innerHTML = "<ul>" + o.maintenanceInclut.map(function (i) { return "<li>" + i + "</li>"; }).join("")
        + "</ul><p>" + o.domaineStandard + "</p>";
    }
    var hors = document.getElementById("faq-site-hors-forfait");
    if (hors) {
      hors.innerHTML = "<p>" + o.horsForfaitResume + "</p><ul>"
        + o.horsForfait.map(function (i) { return "<li>" + i + "</li>"; }).join("") + "</ul>";
    }
  }

  renderPlans();
  renderSiteOffer();

  // ---------------------------------------------------------------
  // 2. Compteurs : le chiffre monte quand il entre dans l'ecran.
  // ---------------------------------------------------------------
  function formatCount(el, value) {
    var prefix = el.dataset.countPrefix || "";
    var suffix = el.dataset.countSuffix || "";
    return prefix + euro(Math.round(value)) + suffix;
  }

  function runCounter(el) {
    var target = Number(el.dataset.count || 0);
    if (reduceMotion) { el.textContent = formatCount(el, target); return; }

    var duration = 1400;
    var start = null;
    function frame(now) {
      if (start === null) start = now;
      var t = Math.min(1, (now - start) / duration);
      // easeOutExpo : demarre vite, finit en douceur - lisible tout du long.
      var eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      el.textContent = formatCount(el, target * eased);
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  // ---------------------------------------------------------------
  // 3. Reveal au scroll + declenchement des compteurs / barres.
  //    Un seul observer pour tout, et chaque element n'est observe
  //    qu'une fois (unobserve des qu'il est apparu) : aucun travail
  //    residuel une fois la page parcourue.
  // ---------------------------------------------------------------
  var revealTargets = document.querySelectorAll("[data-anim], [data-count], [data-fill]");

  function activate(el) {
    if (el.hasAttribute("data-anim")) el.classList.add("is-in");
    if (el.hasAttribute("data-count")) runCounter(el);
    if (el.hasAttribute("data-fill")) {
      var pct = Number(el.dataset.fill || 0);
      if (reduceMotion) el.style.transition = "none";
      el.style.width = pct + "%";
    }
    // Les compteurs a l'interieur d'un bloc revele ne sont pas
    // forcement observes separement s'ils etaient deja visibles :
    // on les declenche avec leur conteneur.
    el.querySelectorAll && el.querySelectorAll("[data-count]").forEach(function (c) {
      if (!c.dataset.countDone) { c.dataset.countDone = "1"; runCounter(c); }
    });
  }

  if (!("IntersectionObserver" in window)) {
    // Repli tres ancien navigateur : tout est affiche immediatement.
    revealTargets.forEach(activate);
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        activate(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.18, rootMargin: "0px 0px -40px 0px" });

    revealTargets.forEach(function (el) {
      // Ce qui est deja visible au chargement (le hero) apparait tout de
      // suite plutot que d'attendre un scroll qui ne viendra peut-etre pas.
      var rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.9) activate(el);
      else observer.observe(el);
    });
  }

  // ---------------------------------------------------------------
  // 4. Parallaxe legere (elements decoratifs uniquement) + ombre nav.
  //    Tout est regroupe dans UNE seule boucle rAF declenchee par le
  //    scroll : pas de listener concurrent, pas de calcul quand rien
  //    ne bouge, et transform uniquement (jamais top/left) pour rester
  //    sur le compositeur.
  // ---------------------------------------------------------------
  var parallaxEls = Array.prototype.slice.call(document.querySelectorAll("[data-parallax]"));
  var nav = document.getElementById("lp-nav");
  var ticking = false;

  function onFrame() {
    ticking = false;
    var y = window.scrollY;

    if (nav) nav.classList.toggle("is-stuck", y > 8);

    if (reduceMotion) return;
    for (var i = 0; i < parallaxEls.length; i++) {
      var el = parallaxEls[i];
      var speed = parseFloat(el.dataset.parallax) || 0;
      // On ne bouge que ce qui est proche de l'ecran : inutile de
      // calculer une transform pour un element a 3 ecrans de distance.
      var rect = el.getBoundingClientRect();
      if (rect.bottom < -200 || rect.top > window.innerHeight + 200) continue;
      el.style.transform = "translate3d(0," + (y * speed).toFixed(1) + "px,0)";
    }
  }

  function onScroll() {
    if (!ticking) { ticking = true; requestAnimationFrame(onFrame); }
  }

  onFrame();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
})();
