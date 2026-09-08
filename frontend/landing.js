// =====================================================================
// Suite Artisan — landing.js
// ---------------------------------------------------------------------
// Landing PUBLIQUE uniquement. Aucun code du SaaS authentifie ici : ce
// fichier n'est charge que par landing.html.
//
// CE QUI VIT ICI, ET CE QUI N'Y VIT PLUS
// La visite - les quatorze pieces, la camera, les textes qui se posent
// dessus - a demenage dans deux modules ES : landing-visite.js pour le
// moteur, landing-piste.js pour le branchement au defilement. Elle
// demandait un canvas et des shaders, ce qui n'a rien a faire dans un
// script classique charge en tete de page.
//
// Reste ici tout ce qui n'a rien a voir avec la visite : l'apparition
// des panneaux de la conclusion, la barre de navigation, et l'affichage
// des tarifs - lus depuis pricing.js, jamais ecrits en dur.
// =====================================================================

(function () {
  "use strict";

  var reduceMotion = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var nav = document.getElementById("lc-nav");
  var progress = document.getElementById("lc-progress");
  var progressLinks = progress ? progress.querySelectorAll("[data-chap]") : null;
  var chapitreFinal = document.querySelector(".lc-chapter-final");

  // -------------------------------------------------------------------
  // 7. PANNEAUX DE LA CONCLUSION
  //    Les scenes 1 a 6 sont pilotees par la timeline (voir render).
  //    Seul le chapitre 7, qui defile normalement, utilise un observer.
  // -------------------------------------------------------------------
  var panels = document.querySelectorAll(".lc-panel");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    Array.prototype.forEach.call(panels, function (b) { b.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.2, rootMargin: "0px 0px -10% 0px" });
    Array.prototype.forEach.call(panels, function (b) { io.observe(b); });
  }

  // Le chapitre 7 ne fait pas partie de la timeline des scenes : c'est
  // lui qui allume la 7e pastille de l'indicateur.
  if ("IntersectionObserver" in window && chapitreFinal && progressLinks) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        Array.prototype.forEach.call(progressLinks, function (a) {
          a.parentNode.classList.toggle("is-on", a.dataset.chap === "7");
        });
      });
    }, { threshold: 0.01, rootMargin: "-45% 0px -45% 0px" }).observe(chapitreFinal);
  }

  // -------------------------------------------------------------------
  // 8. NAV
  // -------------------------------------------------------------------
  var barFill = document.getElementById("lc-bar-fill");
  var navTick = false;
  function navFrame() {
    navTick = false;
    var y = window.scrollY;
    if (nav) nav.classList.toggle("is-stuck", y > 24);
    if (progress) progress.classList.toggle("is-on", y > window.innerHeight * 0.6);
    if (barFill) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      barFill.style.transform = "scaleX(" + (max > 0 ? Math.min(1, y / max) : 0).toFixed(4) + ")";
    }
  }
  window.addEventListener("scroll", function () {
    if (navTick) return;
    navTick = true;
    requestAnimationFrame(navFrame);
  }, { passive: true });
  navFrame();

  // -------------------------------------------------------------------
  // 9. TARIFS — donnees partagees avec le SaaS (pricing.js), en lecture
  //    seule. La landing ne fait que les afficher : jamais de prix ecrit
  //    en dur ici.
  // -------------------------------------------------------------------
  function euro(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }

  (function renderPlans() {
    var host = document.getElementById("lc-plans");
    if (!host || typeof PRICING === "undefined") return;
    var order = (typeof PRICING_ORDRE !== "undefined") ? PRICING_ORDRE : Object.keys(PRICING);
    host.innerHTML = order.map(function (key) {
      var plan = PRICING[key];
      if (!plan) return "";
      var reco = plan.recommande === true;
      return ''
        + '<div class="lc-plan' + (reco ? " is-reco" : "") + '">'
        + (reco ? '<span class="lc-plan-badge">Recommandé</span>' : "")
        + '<div class="lc-plan-name">' + plan.nom + "</div>"
        + '<p class="lc-plan-hook">' + plan.accroche + "</p>"
        + '<div class="lc-plan-price">' + euro(plan.prix) + " €<span> / " + plan.periode + "</span></div>"
        + '<ul class="lc-plan-feats">'
        + plan.fonctionnalites.map(function (x) { return "<li>" + x + "</li>"; }).join("")
        + "</ul>"
        + '<a href="index.html?tab=register" class="lc-btn ' + (reco ? "lc-btn-primary" : "lc-btn-ghost") + '">Commencer</a>'
        + "</div>";
    }).join("");
  })();

  (function renderSiteOffer() {
    if (typeof SITE_VITRINE_OFFER === "undefined") return;
    var o = SITE_VITRINE_OFFER;
    var price = document.getElementById("lc-faq-site-price");
    if (price) {
      price.innerHTML = "Comptez " + euro(o.creation) + " " + o.mention + " à la création, puis "
        + euro(o.mensuel) + " " + o.mention + "/mois de gestion &amp; maintenance.";
    }

    // Le bloc entier est construit depuis pricing.js : aucun prix ni
    // aucune prestation n'est ecrit en dur dans la landing.
    var host = document.getElementById("lc-site-offer");
    if (!host) return;
    var nbPlans = (typeof PRICING_ORDRE !== "undefined") ? PRICING_ORDRE.length : 0;
    var avecTous = nbPlans > 0 && (o.disponibleAvec || []).length === nbPlans;

    host.innerHTML = ''
      + '<p class="lc-eyebrow">Option · hors abonnement</p>'
      + '<h2 class="lc-h2">' + o.nom + ',<br>relié à votre Suite Artisan.</h2>'
      + '<div class="lc-offer">'
      +   '<div class="lc-offer-main">'
      +     '<p class="lc-lead">' + o.description + '</p>'
      +     '<div class="lc-offer-prices">'
      +       '<div class="lc-offer-price">'
      +         '<span class="lc-offer-amount">' + euro(o.creation) + ' €</span>'
      +         '<span class="lc-offer-unit">' + o.mention + ' — création, une seule fois</span>'
      +       '</div>'
      +       '<div class="lc-offer-price is-option">'
      +         '<span class="lc-offer-flag">Facultatif</span>'
      +         '<span class="lc-offer-amount">' + euro(o.mensuel) + ' €</span>'
      +         '<span class="lc-offer-unit">' + o.mention + ' / mois — gestion &amp; maintenance</span>'
      +       '</div>'
      +     '</div>'
      +     '<p class="lc-offer-note"><strong>La gestion et la maintenance sont facultatives.</strong> Si vous la prenez, elle couvre : ' + o.resumeInclus.charAt(0).toLowerCase() + o.resumeInclus.slice(1).replace(/\s*inclus\s*\.?\s*$/i, '') + '.' + '</p>'
      +     '<div class="lc-actions">'
      +       '<a href="index.html?tab=register" class="lc-btn lc-btn-primary lc-btn-lg">Créer mon compte</a>'
      +       '<a href="#faq" class="lc-btn lc-btn-ghost lc-btn-lg">Ce qui est compris</a>'
      +     '</div>'
      +     '<p class="lc-note">Prestation facultative, facturée séparément de l’abonnement'
      +       (avecTous ? ' et disponible avec tous les plans, y compris le plan gratuit.' : '.') + '</p>'
      +   '</div>'
      +   '<ul class="lc-offer-list">'
      +     o.carteInclus.map(function (x) { return "<li>" + x + "</li>"; }).join("")
      +   '</ul>'
      + '</div>';
  })();

  // Le recalage des hauteurs de chapitre a l'arrivee des polices est
  // desormais l'affaire de landing-piste.js : c'est lui qui les mesure.
  // Ce qui restait ici appelait GSAP et les fonctions du film supprime.
})();
