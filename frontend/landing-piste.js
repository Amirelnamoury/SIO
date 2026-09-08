/* =====================================================================
   LA PISTE — ce qui relie le défilement à la visite
   ---------------------------------------------------------------------
   Le moteur (landing-visite.js) sait dessiner une pièce à une
   progression donnée. Ce fichier décide QUAND, et il s'occupe de tout ce
   qui n'est pas du WebGL : les textes posés par-dessus, l'ombre locale
   qui les rend lisibles, les repères de progression, et le repli.

   TROIS MODES, DÉCIDÉS UNE FOIS
     visite   WebGL disponible, mouvement accepté  →  la caméra vole
     repli    pas de WebGL, ou appareil trop juste →  fondus CSS
     fixe     prefers-reduced-motion               →  une image par pièce,
                                                      aucun mouvement

   Dans les trois cas la MÊME timeline pilote les textes : ce qui change
   est la façon de peindre l'image, jamais la lecture.
   ===================================================================== */

import { SCENES, creerVisite } from "./landing-visite.js?v=9";

const BASE = "assets/landing/villa/";
const doc = document;
const reduit = (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
  // Aide de recette : ?reduit=1 force le mode sans mouvement. Il ne se
  // simule pas autrement sur une page deja chargee, et c'est precisement
  // le chemin de lecture qu-on verifie le moins souvent.
  || /(?:^|[?&])reduit(?:=|&|$)/.test(location.search);

const visite = doc.getElementById("lc-visite");
const canvas = doc.getElementById("lc-canvas");
const hotePlans = doc.getElementById("lc-tirages");
const hoteVues = doc.getElementById("lc-vues");
const ombre = doc.getElementById("lc-ombre");
const chapitres = doc.getElementById("lc-chapters");
if (visite && canvas && hotePlans && hoteVues) demarrer();

function demarrer() {
  const vues = Array.prototype.slice.call(hoteVues.querySelectorAll(".lc-vue"));
  const spacers = Array.prototype.slice.call(chapitres.querySelectorAll(".lc-spacer"));

  // -------------------------------------------------------------------
  // Le repli, construit dans tous les cas
  // -------------------------------------------------------------------
  // Il porte les textes alternatifs des quatorze photographies. Il est
  // construit même quand le WebGL démarre : les <img> restent alors
  // vides de `src` et ne coûtent rien, mais leur `alt` reste lisible par
  // un lecteur d'écran qui parcourt la page.
  // Quelle definition charger ? Ce qui compte n'est ni la largeur CSS ni
  // la densite prise isolement, mais le nombre de pixels REELS a couvrir.
  // Un portable de 1351 px a densite 1 en demande 1351 : lui servir la
  // version 1100 px la ferait remonter, visiblement floue. Un telephone de
  // 390 px a densite 3 en demande 1170 : la version 1920 y serait deux
  // fois trop lourde pour rien.
  const petit = window.innerWidth * (window.devicePixelRatio || 1) <= 1250;

  hotePlans.innerHTML = SCENES.map((s, i) => (
    '<figure class="lc-tirage" data-tirage="' + i + '"'
    + ' style="--focal-x:' + (s.focal[0] * 100).toFixed(1) + '%;--focal-y:' + (s.focal[1] * 100).toFixed(1) + '%">'
    + '<img alt="' + s.alt.replace(/"/g, "&quot;") + '" decoding="async"'
    + (i === 0 ? ' fetchpriority="high"' : ' loading="lazy"')
    + ' width="1920" height="1071">'
    + "</figure>"
  )).join("");
  const plans = Array.prototype.slice.call(hotePlans.querySelectorAll(".lc-tirage"));

  function poserImage(i) {
    const img = plans[i] && plans[i].querySelector("img");
    if (!img || img.getAttribute("src")) return;
    img.src = BASE + SCENES[i].f + (petit ? "-sm" : "") + ".webp";
    img.srcset = BASE + SCENES[i].f + "-sm.webp 1100w, " + BASE + SCENES[i].f + ".webp 1920w";
    img.sizes = "100vw";
  }

  // -------------------------------------------------------------------
  // Quel mode ?
  // -------------------------------------------------------------------
  function webglPossible() {
    if (reduit) return false;
    // Un appareil qui annonce peu de coeurs ou peu de memoire fera une
    // visite saccadee : mieux vaut un repli net qu'un WebGL qui rame.
    const coeurs = navigator.hardwareConcurrency || 4;
    const memoire = navigator.deviceMemory || 4;
    if (coeurs <= 2 || memoire <= 2) return false;
    try {
      const c = doc.createElement("canvas");
      return !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch (e) { return false; }
  }

  let moteur = null;
  const mode = webglPossible() ? "visite" : (reduit ? "fixe" : "repli");
  visite.dataset.mode = mode;

  // -------------------------------------------------------------------
  // MOUVEMENT RÉDUIT : la page redevient une page
  // -------------------------------------------------------------------
  // Garder le plateau collant en supprimant seulement les animations
  // obligerait à faire défiler quatorze hauteurs d'écran pour lire
  // quatorze phrases courtes : c'est plus pénible, pas plus calme. La
  // visite redevient donc un enchaînement de sections normales - une
  // photographie posée, son texte en dessous, tout lisible d'un trait.
  if (mode === "fixe") {
    doc.body.classList.add("lc-static");
    canvas.remove();
    spacers.forEach((s) => s.remove());
    vues.forEach((el, i) => {
      el.hidden = false;
      el.classList.add("is-on");
      const planche = doc.createElement("div");
      planche.className = "lc-planche-statique";
      const img = doc.createElement("img");
      img.src = BASE + SCENES[i].f + (petit ? "-sm" : "") + ".webp";
      img.alt = SCENES[i].alt;
      img.loading = i < 2 ? "eager" : "lazy";
      img.decoding = "async";
      img.width = 1920; img.height = 1071;
      img.style.objectPosition = (SCENES[i].focal[0] * 100).toFixed(1) + "% " + (SCENES[i].focal[1] * 100).toFixed(1) + "%";
      planche.appendChild(img);
      const dedans = el.querySelector(".lc-vue-in");
      if (dedans) dedans.appendChild(planche);
    });
    hotePlans.remove();
    if (ombre) ombre.remove();
    return;
  }

  if (mode === "visite") {
    try {
      moteur = creerVisite({ canvas, scenes: SCENES, petit });
      moteur.amorcer();
    } catch (e) {
      // Une carte graphique qui refuse le contexte, un shader qui ne
      // compile pas : on ne laisse pas la page vide pour autant.
      moteur = null;
      visite.dataset.mode = "repli";
    }
  }
  if (!moteur) {
    canvas.remove();
    poserImage(0);
    poserImage(1);
  }

  // -------------------------------------------------------------------
  // La timeline
  // -------------------------------------------------------------------
  // Chaque pièce reçoit une course proportionnelle à son `poids`. Sur
  // mobile, tout est raccourci : le même mouvement demande moins de
  // pouce, sinon la visite paraît interminable.
  let vh = 0, haut = 0, course = 1;
  const bornes = [];

  function echelle() { return window.innerWidth < 760 ? 0.66 : 1; }

  function mesurer() {
    vh = window.innerHeight;
    const k = echelle();
    // Une seule boucle : la hauteur posée sur le spacer et la borne de la
    // timeline sont la MÊME valeur. Les calculer deux fois, c'est se
    // donner la possibilité qu'elles divergent - et une timeline qui ne
    // correspond plus aux hauteurs réelles fait afficher la mauvaise
    // pièce sans que rien ne le signale.
    let curseur = 0;
    bornes.length = 0;
    SCENES.forEach((s, i) => {
      const h = Math.round(s.poids * k * vh);
      spacers[i].style.height = h + "px";
      bornes.push({ debut: curseur, fin: curseur + h });
      curseur += h;
    });
    haut = visite.getBoundingClientRect().top + window.scrollY;
    course = Math.max(1, curseur);
  }

  // La transition occupe le dernier quart de chaque pièce : assez long
  // pour ne pas se lire comme une coupe, assez court pour que chaque
  // pièce ait un moment où elle est seule à l'écran.
  const PART_TRANSITION = 0.26;

  let dernierIndex = -1, dernierChapitre = -1;
  const progressLiens = doc.querySelectorAll("#lc-progress [data-chap]");

  function peindre() {
    const y = Math.min(Math.max(window.scrollY - haut, 0), course);
    let i = 0;
    while (i < bornes.length - 1 && y >= bornes[i].fin) i++;
    const b = bornes[i];
    const span = Math.max(1, b.fin - b.debut);
    const brut = (y - b.debut) / span;
    const p = Math.min(1, Math.max(0, brut));
    // t : progression de la transition vers la pièce suivante.
    const t = i >= SCENES.length - 1 ? 0
      : Math.min(1, Math.max(0, (p - (1 - PART_TRANSITION)) / PART_TRANSITION));

    if (moteur) {
      moteur.rendre(i, p, t);
    } else {
      // Repli : un simple fondu, et un très lent agrandissement pour que
      // l'image ne soit pas parfaitement inerte. En mode `fixe`, même
      // pas d'agrandissement.
      plans.forEach((el, j) => {
        let o = 0;
        if (j === i) o = 1 - t;
        else if (j === i + 1) o = t;
        el.style.opacity = o;
        if (o > 0.01) {
          poserImage(j);
          if (mode !== "fixe") {
            const img = el.querySelector("img");
            if (img) img.style.transform = "scale(" + (1.04 + p * 0.035).toFixed(4) + ")";
          }
        }
      });
      if (i + 2 < SCENES.length && p > 0.5) poserImage(i + 2);
    }

    // Les textes. Chaque pièce garde le sien pendant sa durée propre ;
    // il s'efface pendant la transition, celui d'après entre après lui -
    // jamais les deux à pleine opacité en même temps.
    vues.forEach((el, j) => {
      const actif = j === i && t < 0.55;
      el.classList.toggle("is-on", actif);
      el.hidden = !actif && j !== i + 1;
      if (j === i + 1) el.classList.toggle("is-on", t >= 0.55);
    });

    if (i !== dernierIndex) {
      dernierIndex = i;
      if (ombre) ombre.dataset.cote = SCENES[i].cote;
      // Cinq reperes pour onze etapes : deux etapes par repere, et les
      // trois dernieres pieces partagent le cinquieme. Sans le plafond,
      // la sequence produisait un sixieme numero qui nexiste pas dans la
      // liste, et le dernier repere ne sallumait jamais.
      const chap = Math.min(5, Math.floor(i / 2) + 1);
      if (chap !== dernierChapitre) {
        dernierChapitre = chap;
        Array.prototype.forEach.call(progressLiens, (a) => {
          a.parentNode.classList.toggle("is-on", Number(a.dataset.chap) === chap);
        });
      }
    }
  }

  // -------------------------------------------------------------------
  // Branchement
  // -------------------------------------------------------------------
  let attente = false;
  function surDefilement() {
    if (attente) return;
    attente = true;
    requestAnimationFrame(() => { attente = false; peindre(); });
  }
  window.addEventListener("scroll", surDefilement, { passive: true });
  // Le verrou est rendu au retour sur l'onglet, et la visite recalee sur
  // la position reelle - qui a pu changer pendant l'absence.
  doc.addEventListener("visibilitychange", () => {
    if (doc.hidden) return;
    attente = false;
    peindre();
  });

  let redim;
  function surRedimensionnement() {
    clearTimeout(redim);
    redim = setTimeout(() => {
      mesurer();
      if (moteur) moteur.dimensionner();
      dernierIndex = -1;
      peindre();
    }, 120);
  }
  window.addEventListener("resize", surRedimensionnement, { passive: true });
  window.addEventListener("orientationchange", surRedimensionnement, { passive: true });

  mesurer();
  peindre();

  // Point d'observation, ouvert par ?debug seulement. Une visite en WebGL
  // ne se verifie pas a la capture d'ecran : le canevas n'expose rien au
  // DOM. Ceci permet de poser la visite a une piece et a une progression
  // donnees, et de lire ce que la camera fait vraiment.
  if (/(?:^|[?&])debug(?:=|&|$)/.test(location.search)) {
    window.__visite = {
      // Peint SANS attendre requestAnimationFrame : dans un volet qui
      // garde la page cachee, rAF ne tourne jamais et rien ne serait
      // verifiable.
      aller(i, p) {
        const b = bornes[Math.max(0, Math.min(bornes.length - 1, i))];
        window.scrollTo(0, Math.round(haut + b.debut + (b.fin - b.debut) * (p || 0)));
        peindre();
        return Promise.resolve();
      },
      peindre,
      mesurer,
      etat: () => ({
        index: dernierIndex,
        mode,
        cote: ombre ? ombre.dataset.cote : null,
        vueVisible: (vues.find((v) => v.classList.contains("is-on")) || {}).dataset,
        moteur: moteur ? moteur.etat() : null,
      }),
      scenes: SCENES,
    };
  }

  // Les polices arrivent parfois après le premier calcul : les hauteurs
  // de chapitre mesurées trop tôt décaleraient toute la visite.
  if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(() => { mesurer(); peindre(); });
}
