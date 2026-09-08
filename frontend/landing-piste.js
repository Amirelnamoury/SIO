/* =====================================================================
   LA PISTE — ce qui relie le défilement à la visite
   ---------------------------------------------------------------------
   Le moteur (landing-visite.js) sait dessiner un plan à une progression
   donnée. Ce fichier décide QUAND, et il s'occupe de tout ce qui n'est
   pas du WebGL : les textes posés par-dessus, l'ombre locale qui les
   rend lisibles, les repères, la sortie vers la page, et le repli.

   TROIS MODES, DÉCIDÉS UNE FOIS
     visite   WebGL disponible, mouvement accepté  →  la visite
     repli    pas de WebGL, ou appareil trop juste →  fondus CSS
     fixe     prefers-reduced-motion               →  une image par plan,
                                                      aucun mouvement

   UNE SEULE TIMELINE
   Dans les trois modes, la MÊME progression pilote l'image et les
   textes. Deux horloges séparées finissent toujours par diverger, et une
   divergence se voit : c'est un texte qui parle d'une pièce pendant
   qu'on en regarde une autre.

   LA SORTIE
   La visite ne s'arrêtait pas, elle était coupée : la dernière
   photographie cédait la place au contenu en une image. Une course
   supplémentaire est réservée à la fin, pendant laquelle l'image se
   décolore vers le papier et les textes s'effacent. Le contenu arrive
   ensuite sur le même beige — il n'y a plus de frontière à franchir.
   ===================================================================== */

import { SCENES, creerVisite } from "./landing-visite.js?v=17";

const BASE = "assets/landing/villa/";
const PAPIER = "#F1EADF";
const doc = document;
const reduit = (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
  // Aide de recette : ?reduit=1 force le mode sans mouvement. Il ne se
  // simule pas autrement sur une page déjà chargée, et c'est précisément
  // le chemin de lecture qu'on vérifie le moins souvent.
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
  const sortieSpacer = doc.getElementById("lc-sortie");
  const conclusion = doc.getElementById("chap-final");

  // Quelle définition charger ? Ce qui compte n'est ni la largeur CSS ni
  // la densité prise isolément, mais le nombre de pixels RÉELS à
  // couvrir. Un portable de 1351 px à densité 1 en demande 1351 : lui
  // servir la version 1100 la ferait remonter, visiblement floue.
  const petit = window.innerWidth * (window.devicePixelRatio || 1) <= 1250;

  // -------------------------------------------------------------------
  // Le repli, construit dans tous les cas
  // -------------------------------------------------------------------
  // Il porte les textes alternatifs des huit photographies. Il est
  // construit même quand le WebGL démarre : les <img> restent alors sans
  // `src` et ne coûtent rien, mais leur `alt` reste lisible.
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
    // Un appareil qui annonce peu de cœurs ou peu de mémoire fera une
    // visite saccadée : mieux vaut un repli net qu'un WebGL qui rame.
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
  // obligerait à faire défiler huit hauteurs d'écran pour lire huit
  // phrases courtes : c'est plus pénible, pas plus calme. La visite
  // redevient un enchaînement de sections normales.
  if (mode === "fixe") {
    doc.body.classList.add("lc-static");
    canvas.remove();
    spacers.forEach((s) => s.remove());
    if (sortieSpacer) sortieSpacer.remove();
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
    // Les reperes pointaient sur les ancres des spacers, qu'on vient de
    // retirer : quatre liens morts, et un indicateur qui suivrait une
    // timeline qui n'existe plus. Une page qui defile normalement se
    // repere toute seule.
    const progres = doc.getElementById("lc-progress");
    if (progres) progres.remove();
    return;
  }

  if (mode === "visite") {
    try {
      moteur = creerVisite({ canvas, scenes: SCENES, petit, papier: PAPIER, surChargement: surDefilement });
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

  // ===================================================================
  // LA TIMELINE
  // ===================================================================
  // Huit plans, plus une course de sortie. Le total visé est de 700 à
  // 900 hauteurs d'écran : la version précédente en demandait 1 040 pour
  // onze étapes, et l'enregistrement montrait que le visiteur arrivait
  // au bout fatigué. Ici la somme des poids vaut 7,5, plus 0,65 de
  // sortie — 815 vh sur ordinateur, 545 sur téléphone.
  const SORTIE = 0.65;
  let vh = 0, haut = 0, course = 1, debutSortie = 0, hauteurSortie = 1;
  const bornes = [];

  // Sur mobile, tout est raccourci : le même mouvement demande beaucoup
  // plus de pouce, sinon la visite paraît interminable.
  function echelle() { return window.innerWidth < 760 ? 0.66 : 1; }

  function mesurer() {
    vh = window.innerHeight;
    const k = echelle();
    // Une seule boucle : la hauteur posée sur le spacer et la borne de
    // la timeline sont la MÊME valeur. Les calculer deux fois, c'est se
    // donner la possibilité qu'elles divergent — et une timeline qui ne
    // correspond plus aux hauteurs réelles affiche le mauvais plan sans
    // que rien ne le signale.
    let curseur = 0;
    bornes.length = 0;
    SCENES.forEach((s, i) => {
      const h = Math.round(s.poids * k * vh);
      if (spacers[i]) spacers[i].style.height = h + "px";
      bornes.push({ debut: curseur, fin: curseur + h });
      curseur += h;
    });
    debutSortie = curseur;
    hauteurSortie = Math.round(SORTIE * k * vh);
    if (sortieSpacer) sortieSpacer.style.height = hauteurSortie + "px";
    curseur += hauteurSortie;

    haut = visite.getBoundingClientRect().top + window.scrollY;
    course = Math.max(1, curseur);
  }

  /* LE CALENDRIER D'UNE TRANSITION, en fraction de la scène :

       0 → 70 %    la scène est seule, et elle avance
      70 → 96 %    la suivante arrive, DÉJÀ en mouvement (le moteur lui
                   donne une progression négative), pendant que la
                   courante continue la sienne. Les deux bougent : c'est
                   ce recouvrement qui fait la différence entre un
                   enchaînement et un fondu de diaporama
      96 → 100 %   la suivante est seule, et il lui reste sa course

     Le texte, lui, bascule au milieu de ce recouvrement : il sort avant
     que son image n'ait fini de partir, et le suivant entre après. Deux
     textes à pleine opacité en même temps sont illisibles. */
  const T_DEBUT = 0.70;
  const T_FIN = 0.96;

  let dernierIndex = -1, dernierChapitre = -1, dernierEtatSortie = -1;
  const progressLiens = doc.querySelectorAll("#lc-progress [data-chap]");

  function peindre() {
    const y = Math.min(Math.max(window.scrollY - haut, 0), course);

    let i, p, t, sortie;
    if (y >= debutSortie) {
      // LA SORTIE. Le dernier plan garde sa pose finale — il ne recule
      // pas, il ne se recentre pas — et se décolore vers le papier.
      i = SCENES.length - 1;
      p = 1; t = 0;
      sortie = Math.min(1, (y - debutSortie) / Math.max(1, hauteurSortie));
    } else {
      i = 0;
      while (i < bornes.length - 1 && y >= bornes[i].fin) i++;
      const b = bornes[i];
      const span = Math.max(1, b.fin - b.debut);
      p = Math.min(1, Math.max(0, (y - b.debut) / span));
      t = i >= SCENES.length - 1 ? 0
        : Math.min(1, Math.max(0, (p - T_DEBUT) / (T_FIN - T_DEBUT)));
      sortie = 0;
    }

    if (moteur) {
      const peinte = moteur.rendre(i, p, t, sortie);
      // Une photographie en cours de décodage ne doit pas laisser son
      // texte prendre de l'avance. Le moteur garde la dernière frame
      // complète ; son chargement redemande cette même peinture par rAF,
      // à la position réelle du défilement, même si l'utilisateur s'arrête.
      if (!peinte) return;
      ({ i, p, t, sortie } = peinte);
      // La page entre pendant que la terrasse devient papier. Son fond
      // transparent evite un front opaque ; suivre la sortie evite aussi
      // d'ajouter une hauteur d'ecran vide apres la photographie.
      if (conclusion) conclusion.style.opacity = String(Math.max(0, (sortie - 0.25) / 0.75));
    } else {
      // Repli : un fondu, et un agrandissement très lent pour que
      // l'image ne soit pas parfaitement inerte. Même plafond que le
      // moteur — 3,5 % — pour que les deux modes se ressemblent.
      plans.forEach((el, j) => {
        let o = 0;
        if (j === i) o = 1 - t;
        else if (j === i + 1) o = t;
        el.style.opacity = o;
        if (o > 0.01) {
          poserImage(j);
          const img = el.querySelector("img");
          if (img) img.style.transform = "scale(" + (1 + p * 0.035).toFixed(4) + ")";
        }
      });
      if (i + 2 < SCENES.length && p > 0.5) poserImage(i + 2);
      hotePlans.style.opacity = (1 - sortie).toFixed(3);
    }

    // Les textes. Chaque plan garde le sien pendant sa durée propre ; il
    // s'efface au milieu du recouvrement, et celui d'après entre après
    // lui. Pendant la sortie, aucun n'est actif.
    const bascule = 0.55;
    vues.forEach((el, j) => {
      let actif;
      if (sortie > 0.06) actif = false;
      else if (j === i) actif = t < bascule;
      else if (j === i + 1) actif = t >= bascule;
      else actif = false;
      el.classList.toggle("is-on", actif);
      // `hidden` retire aussi du parcours clavier : un lien de plan
      // masqué mais focusable enverrait le focus sur un texte invisible.
      el.hidden = !actif && j !== i && j !== i + 1;
    });

    /* L'ombre suit la sortie AU DEFILEMENT, pas sur une transition CSS.
       Une transition de 0,7 s pilotee par une classe accuse un retard sur
       le doigt : l'image est deja beige que le degre sombre est encore
       la. Ici l'opacite lit la meme valeur que le shader. */
    if (ombre) ombre.style.opacity = sortie > 0 ? String(1 - sortie) : "";
    const enSortie = sortie > 0.02 ? 1 : 0;
    if (enSortie !== dernierEtatSortie) {
      dernierEtatSortie = enSortie;
      visite.classList.toggle("is-sortie", !!enSortie);
    }

    if (i !== dernierIndex) {
      dernierIndex = i;
      if (ombre) {
        ombre.dataset.cote = SCENES[i].cote;
        // Une piece dont la zone claire tombe du cote du texte demande
        // une ombre plus dense. C'est declare dans la table des scenes,
        // au plus pres de la photographie concernee.
        if (SCENES[i].dense) ombre.dataset.dense = "1";
        else ombre.removeAttribute("data-dense");
      }
      // Quatre repères pour huit plans : deux plans par repère. Le
      // plafond évite qu'un neuvième numéro, qui n'existe pas dans la
      // liste, soit demandé sur la dernière scène.
      const chap = Math.min(4, Math.floor(i / 2) + 1);
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
  // Le verrou est rendu au retour sur l'onglet, et la visite recalée sur
  // la position réelle — qui a pu changer pendant l'absence. Sans cela,
  // un onglet quitté au milieu d'une image gardait le verrou pris et la
  // visite ne repartait jamais.
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

  // Point d'observation, ouvert par ?debug seulement. Une visite en
  // WebGL ne se vérifie pas à la capture d'écran : le canevas n'expose
  // rien au DOM. Ceci permet de la poser à un plan et à une progression
  // donnés, et de lire ce que le shader fait vraiment.
  if (/(?:^|[?&])debug(?:=|&|$)/.test(location.search)) {
    window.__visite = {
      // Peint SANS attendre requestAnimationFrame : dans un volet qui
      // garde la page cachée, rAF ne tourne jamais et rien ne serait
      // vérifiable.
      aller(i, p) {
        const b = bornes[Math.max(0, Math.min(bornes.length - 1, i))];
        window.scrollTo(0, Math.round(haut + b.debut + (b.fin - b.debut) * (p || 0)));
        peindre();
        return Promise.resolve();
      },
      allerSortie(f) {
        window.scrollTo(0, Math.round(haut + debutSortie + hauteurSortie * (f || 0)));
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
        courseTotale: course,
        courseEnVh: +(course / vh).toFixed(2),
        moteur: moteur ? moteur.etat() : null,
      }),
      scenes: SCENES,
    };
  }

  // Les polices arrivent parfois après le premier calcul : des hauteurs
  // mesurées trop tôt décaleraient toute la visite.
  if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(() => { mesurer(); peindre(); });
}
