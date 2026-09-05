// =====================================================================
// Suite Artisan — landing.js
// ---------------------------------------------------------------------
// Landing PUBLIQUE uniquement. Aucun code du SaaS authentifie ici : ce
// fichier n'est charge que par landing.html.
//
// PRINCIPE
// Un seul "plateau" (.lc-stage) reste colle en haut de l'ecran pendant
// toute la visite. Les 20 photographies y sont empilees ; le scroll ne
// fait que deplacer un curseur sur une timeline, qui decide quelles
// frames sont visibles, avec quelle opacite et quel micro-zoom.
//
// Il n'y a donc ni video, ni 3D, ni images intermediaires inventees :
// la sensation de camera vient uniquement de l'enchainement controle
// des frames fournies (crossfade, Ken Burns tres leger, et un volet
// clip-path pour l'avant/apres du chantier).
//
// TOUT SE REGLE DANS `FRAMES` ci-dessous : ordre, duree de scroll,
// echelle de depart/arrivee, cadrage, type de transition.
// =====================================================================

(function () {
  "use strict";

  var BASE = "assets/landing/frames/";
  var reduceMotion = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // -------------------------------------------------------------------
  // 1. CONFIGURATION DES SCENES
  //
  //   id       lettre de la frame (frame-a.webp / frame-a-sm.webp)
  //   chapter  chapitre narratif auquel elle appartient (1..7)
  //   w        duree de scroll en vh (poids sur la timeline)
  //   t        part de `w` consacree a la transition vers la frame
  //            suivante (0.4 = 40 % de transition, 60 % de pause)
  //   from/to  micro-zoom Ken Burns (jamais au-dela de ~1.07 : au-dela
  //            on voit la photo "respirer" et ca fait gadget)
  //   pos      object-position, pour ne pas couper un element important
  //   reveal   transition speciale : la frame suivante est devoilee par
  //            un volet horizontal au lieu d'un fondu (avant/apres)
  //
  // La hauteur de chaque chapitre 1..6 est deduite automatiquement de la
  // somme des `w` de ses frames : les changements d'image tombent donc
  // toujours pile sur les changements de texte.
  // -------------------------------------------------------------------
  var FRAMES = [
    // -- 01 arrivee ---------------------------------------------------
    // Approche resserree : l'exterieur est joli mais ce n'est pas lui qui
    // vend le produit, il ne doit pas couter 4 ecrans de scroll.
    { id: "a", chapter: 1, w: 85, t: 0.45, from: 1.00, to: 1.05, pos: "50% 58%" },
    { id: "b", chapter: 1, w: 58, t: 0.62, from: 1.00, to: 1.05, pos: "50% 55%" },
    // -- 02 l'entree --------------------------------------------------
    // La frame E (seuil) est volontairement absente : elle montrait le
    // meme hall que D et F et n'ajoutait qu'un temps mort. D -> F se lit
    // comme une avancee franche vers l'interieur.
    { id: "c", chapter: 2, w: 66, t: 0.42, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "d", chapter: 2, w: 64, t: 0.55, from: 1.02, to: 1.06, pos: "50% 50%" },
    // -- 03 le terrain ------------------------------------------------
    { id: "f", chapter: 3, w: 60,  t: 0.50, from: 1.00, to: 1.05, pos: "50% 50%" },
    { id: "g", chapter: 3, w: 42,  t: 0.70, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "h", chapter: 3, w: 46,  t: 0.65, from: 1.00, to: 1.05, pos: "50% 50%" },
    { id: "i", chapter: 3, w: 82,  t: 0.40, from: 1.00, to: 1.05, pos: "50% 50%" },
    // -- 04 la technique ----------------------------------------------
    { id: "j", chapter: 4, w: 48,  t: 0.65, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "k", chapter: 4, w: 48,  t: 0.60, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "l", chapter: 4, w: 79,  t: 0.40, from: 1.00, to: 1.05, pos: "50% 50%" },
    // -- 05 le chantier -----------------------------------------------
    { id: "m", chapter: 5, w: 54,  t: 0.65, from: 1.00, to: 1.04, pos: "50% 50%" },
    // n -> o : volet, pas fondu. Les deux photos sont cadrees a
    // l'identique, donc le front de transformation est parfaitement net.
    { id: "n", chapter: 5, w: 105, t: 0.60, from: 1.00, to: 1.03, pos: "50% 50%", reveal: true },
    { id: "o", chapter: 5, w: 91,  t: 0.40, from: 1.03, to: 1.06, pos: "50% 50%" },
    // -- 06 le bureau -------------------------------------------------
    { id: "p", chapter: 6, w: 48,  t: 0.65, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "q", chapter: 6, w: 48,  t: 0.60, from: 1.00, to: 1.04, pos: "50% 50%" },
    { id: "r", chapter: 6, w: 144, t: 0.30, from: 1.00, to: 1.04, pos: "50% 50%" },
    // -- 07 le salon --------------------------------------------------
    { id: "s", chapter: 7, w: 70,  t: 0.60, from: 1.00, to: 1.04, pos: "50% 50%" },
    // `t` absorbe toute la hauteur restante du chapitre 7 (contenu long).
    { id: "t", chapter: 7, w: 0,   t: 0,    from: 1.00, to: 1.06, pos: "50% 50%", fill: true }
  ];

  // Emplacement de l'ecran du bureau dans la frame R, en % de l'image
  // (mesure sur la photo d'origine). On y affiche la marque, pas une
  // capture du SaaS : l'application est en refonte, et y incruster une
  // vieille capture donnerait une fausse idee du produit.
  // Emplacement de la dalle, mesure sur la photo.
  //
  // Le moniteur n'est PAS d'aplomb : ses coins sont en
  // (951,500) (1198,504) (1204,635) (953,638), soit un bord haut incline
  // de 1,15deg et un bord gauche de 0,81deg. Prendre la boite englobante
  // de ce quadrilatere — ce qui avait ete fait — donne forcement un
  // rectangle plus grand que la dalle, qui deborde aux coins : c'est ce
  // qu'on voyait en bas a gauche.
  //
  // On utilise donc le rectangle INSCRIT, plus la rotation du moniteur.
  // Le leger retrait qui subsiste se lit comme la bordure noire de la
  // dalle, ce qui est realiste.
  // Coins releves sur la photo :
  //   TL (943.7, 495.3)  TR (1200.0, 494.3)
  //   BL (947.1, 641.7)  BR (1209.4, 636.4)
  // Ce n'est ni un rectangle ni un simple rectangle tourne : le bord haut
  // mesure 256 px et le bord bas 262 px. Le moniteur est vu en legere
  // perspective, et les verticales penchent a droite en descendant.
  //
  // D'ou la matrice : un `rotate` seul laissait un liseré gris d'un cote
  // et debordait de l'autre. Les coefficients sont l'ajustement affine au
  // sens des moindres carres sur les quatre coins ; le rectangle est
  // retreci de 3 px (echelle native) pour absorber la perspective
  // residuelle et ne jamais mordre sur le cadre.
  // Les QUATRE COINS de la dalle, en % de l'image (elargis de 1 px vers
  // l'exterieur : mieux vaut mordre d'un pixel sur le cadre noir que
  // laisser paraitre un pixel de gris sur du noir).
  //
  // Une transformation affine ne suffit pas ici : le bord gauche ne se
  // decale que de 3 px sur la hauteur quand le droit se decale de 8 px.
  // Une affine ne peut rendre qu'une seule pente et prend donc la
  // moyenne — elle sur-incline a gauche et sous-incline a droite, d'ou le
  // gris qui restait en bas a gauche. Il faut une homographie.
  var PRODUCT_SCREEN = {
    enabled: true,
    tl: [49.11, 46.16], tr: [62.55, 46.06],
    br: [63.04, 59.41], bl: [49.28, 59.91]
  };
  var FRAME_AR = 1920 / 1072;

  var film = document.getElementById("lc-film");
  var layers = document.getElementById("lc-layers");
  var chapters = document.getElementById("lc-chapters");
  if (!film || !layers || !chapters) return;

  // -------------------------------------------------------------------
  // 2. CONSTRUCTION DES CALQUES
  //    La frame A est deja dans le HTML (affichage immediat). Les autres
  //    sont creees ici SANS src : elles ne seront chargees qu'a
  //    l'approche (voir 4.), pour ne pas tirer 2,6 Mo au premier rendu.
  // -------------------------------------------------------------------
  var nodes = {};
  FRAMES.forEach(function (f, i) {
    var img = layers.querySelector('[data-frame="' + f.id + '"]');
    if (!img) {
      img = document.createElement("img");
      img.className = "lc-frame";
      img.alt = "";
      img.width = 1920;
      img.height = 1072;
      img.decoding = "async";
      img.dataset.frame = f.id;
      layers.appendChild(img);
    }
    img.style.objectPosition = f.pos;
    img.style.zIndex = String(i + 1);
    f.node = img;
    f.loaded = !!img.getAttribute("src");
    nodes[f.id] = img;
  });

  function loadFrame(f) {
    if (f.loaded) return;
    f.loaded = true;
    f.node.srcset = BASE + "frame-" + f.id + "-sm.webp 1100w, " + BASE + "frame-" + f.id + ".webp 1920w";
    f.node.sizes = "100vw";
    f.node.src = BASE + "frame-" + f.id + ".webp";
  }
  // Les deux frames suivantes tout de suite : le visiteur scrolle vite.
  loadFrame(FRAMES[1]);
  loadFrame(FRAMES[2]);

  // -------------------------------------------------------------------
  // 3. HAUTEURS DES CHAPITRES
  //    Chapitres 1..6 : hauteur = somme des poids de leurs frames, pour
  //    que image et texte changent au meme moment.
  //    Chapitre 7 : hauteur libre, dictee par son contenu (benefices,
  //    metiers, tarifs, FAQ, CTA) — on ne force pas un nombre arbitraire.
  // -------------------------------------------------------------------
  var chapterEls = {};
  Array.prototype.forEach.call(chapters.querySelectorAll("[data-spacer]"), function (el) {
    chapterEls[el.dataset.spacer] = el;
  });
  // Sur petit ecran on raccourcit la visite : les memes 18 frames en
  // ~880vh au lieu de ~1295vh. Les mouvements restent lisibles mais le
  // pouce a beaucoup moins de chemin a parcourir.
  function scrollScale() { return window.innerWidth < 760 ? 0.68 : 1; }

  function layoutSpacers() {
    var k = scrollScale();
    for (var c = 1; c <= 6; c++) {
      var sum = 0;
      FRAMES.forEach(function (f) { if (f.chapter === c) sum += f.w; });
      if (chapterEls[c]) chapterEls[c].style.height = (sum * k) + "vh";
    }
  }
  layoutSpacers();

  // Les scenes du calque, indexees par numero de chapitre.
  var sceneEls = {};
  Array.prototype.forEach.call(document.querySelectorAll("[data-scene]"), function (el) {
    sceneEls[el.dataset.scene] = el;
  });

  // -------------------------------------------------------------------
  // 4. TIMELINE + RENDU
  // -------------------------------------------------------------------
  var timeline = [];   // { f, start, end, transStart } en pixels
  var filmTop = 0, filmRange = 1, vh = 0;

  function measure() {
    vh = window.innerHeight;
    layoutSpacers();
    var rect = film.getBoundingClientRect();
    filmTop = rect.top + window.scrollY;
    // Le plateau est colle : la course utile s'arrete une hauteur
    // d'ecran avant la fin du film.
    filmRange = Math.max(1, film.offsetHeight - vh);

    var k = scrollScale();
    var fixedPx = 0;
    FRAMES.forEach(function (f) { if (!f.fill) fixedPx += f.w * k * vh / 100; });
    // Ce qui reste apres les frames a poids fixe revient a la frame T.
    var fillPx = Math.max(vh, filmRange - fixedPx);

    timeline = [];
    var cursor = 0;
    FRAMES.forEach(function (f) {
      var span = f.fill ? fillPx : f.w * k * vh / 100;
      timeline.push({
        f: f,
        start: cursor,
        end: cursor + span,
        transStart: cursor + span * (1 - f.t)
      });
      cursor += span;
    });
  }

  var lastIndex = -1;

  function render(scrolled) {
    var y = Math.min(Math.max(scrolled, 0), filmRange);

    // Frame courante = celle dont la fenetre contient le curseur.
    var idx = 0;
    for (var i = 0; i < timeline.length; i++) {
      if (y >= timeline[i].start) idx = i; else break;
    }
    var cur = timeline[idx];
    var nxt = timeline[idx + 1];
    var f = cur.f;

    // Progression a l'interieur de la frame courante (0..1)
    var span = cur.end - cur.start || 1;
    var p = (y - cur.start) / span;

    // Part de transition (0 tant qu'on est en pause, 1 a la bascule)
    var tp = 0;
    if (nxt && y > cur.transStart) {
      tp = (y - cur.transStart) / Math.max(1, cur.end - cur.transStart);
      tp = Math.min(1, Math.max(0, tp));
    }

    // --- Fenetre de compositing : seules les frames voisines restent
    //     "vivantes". Sans cela, 20 images plein ecran resteraient
    //     composees en permanence sur le GPU.
    if (idx !== lastIndex) {
      lastIndex = idx;
      FRAMES.forEach(function (fr, i) {
        var live = i >= idx - 1 && i <= idx + 2;
        fr.node.classList.toggle("is-live", live);
        if (i >= idx && i <= idx + 3) loadFrame(fr);
      });
    }

    FRAMES.forEach(function (fr, i) {
      var node = fr.node;
      if (i < idx || i > idx + 1) {
        // Avant : deja passee. Apres : pas encore entree.
        node.style.opacity = i < idx ? "1" : "0";
        if (i < idx - 1 || i > idx + 2) node.style.opacity = i < idx ? "1" : "0";
        return;
      }
      if (i === idx) {
        var scale = fr.from + (fr.to - fr.from) * p;
        if (i === rIndex) rScale = scale;
        node.style.opacity = "1";
        node.style.transform = "scale(" + scale.toFixed(4) + ")";
        node.style.clipPath = "none";
      } else {
        if (i === rIndex) rScale = fr.from;
        // Frame suivante : elle entre en fondu, SAUF si la frame
        // courante demande un volet (avant/apres du chantier).
        if (f.reveal) {
          node.style.opacity = tp > 0 ? "1" : "0";
          node.style.clipPath = "inset(0 0 0 " + ((1 - tp) * 100).toFixed(2) + "%)";
          node.style.transform = "scale(" + fr.from.toFixed(4) + ")";
        } else {
          node.style.opacity = tp.toFixed(3);
          node.style.clipPath = "none";
          node.style.transform = "scale(" + fr.from.toFixed(4) + ")";
        }
      }
    });

    // Le trait lumineux qui marque le front de transformation
    if (revealEdge) {
      if (f.reveal && tp > 0 && tp < 1) {
        revealEdge.style.opacity = "1";
        // La frame revelee est clippee par `inset(0 0 0 X%)` avec
        // X = (1 - tp) * 100 : le front se trouve donc en X, pas en tp.
        revealEdge.style.left = ((1 - tp) * 100).toFixed(2) + "%";
      } else {
        revealEdge.style.opacity = "0";
      }
    }

    // Le bloc "marge" n'a de sens qu'une fois la piece terminee revelee :
    // on ne le laisse entrer que lorsque la frame O prend la main.
    if (lateBlock) {
      var ready = f.id === "o";
      lateBlock.classList.toggle("is-ready", ready);
      if (ready && !countersDone) { countersDone = true; runCounters(lateBlock); }
    }

    // L'ecran du bureau n'existe que sur la frame R : il suit exactement
    // son opacite, sinon il flotterait au-dessus des autres plans.
    if (screenSlot) {
      var so = idx === rIndex ? 1 - tp : (idx === rIndex - 1 ? tp : 0);
      screenSlot.style.opacity = so.toFixed(3);
      // ... et surtout son ECHELLE. La frame R est agrandie de 1.00 a
      // 1.04 par le Ken Burns : sans reporter ce zoom, le moniteur grandit
      // et s'ecarte pendant que le calque reste fige, et le noir finit par
      // mordre sur le cadre. Le decalage n'apparait donc qu'a mesure qu'on
      // avance dans le plan — ce qui le rendait invisible sur une capture
      // prise en debut de plan.
      screenWrap.style.transform = "scale(" + rScale.toFixed(4) + ")";
    }

    // Le calque des scenes 1-6 s'eteint AVANT que le contenu du chapitre 7
    // n'entre dans l'ecran. Sans cela le texte du bureau restait affiche
    // par-dessus les benefices qui remontaient : les deux se superposaient.
    if (overlayEl && finalEl) {
      var ft = finalEl.getBoundingClientRect().top;
      var o = Math.min(1, Math.max(0, (ft - vh * 0.55) / (vh * 0.45)));
      overlayEl.style.opacity = o.toFixed(3);
      overlayEl.style.pointerEvents = o < 0.05 ? "none" : "";
    }

    // Libelle Avant / Pendant / Apres, cale sur le volet
    if (phaseEl) {
      var phase = !f.reveal ? (f.id === "o" ? 3 : 0) : (tp < 0.08 ? 1 : tp < 0.92 ? 2 : 3);
      if (phase !== phaseEl._p) {
        phaseEl._p = phase;
        Array.prototype.forEach.call(phaseEl.children, function (s) {
          s.classList.toggle("is-on", Number(s.dataset.phase) === phase);
        });
      }
    }

    // Voile : discret dehors, plus present quand du texte doit se lire.
    // La scene correspondante s'allume en meme temps, donc texte et image
    // ne peuvent pas se desynchroniser.
    if (f.chapter !== lastChapter) {
      lastChapter = f.chapter;
      if (scrim) scrim.dataset.chapter = String(f.chapter);
      for (var s = 1; s <= 6; s++) {
        if (sceneEls[s]) sceneEls[s].classList.toggle("is-on", s === f.chapter);
      }
      if (progressLinks) {
        Array.prototype.forEach.call(progressLinks, function (a) {
          a.parentNode.classList.toggle("is-on", Number(a.dataset.chap) === f.chapter);
        });
      }
    }
  }
  // Declares ici (et non plus bas) : render() s'en sert des le premier
  // appel, qui a lieu avant la section 8.
  var lastChapter = -1;
  var nav = document.getElementById("lc-nav");
  var progress = document.getElementById("lc-progress");
  var progressLinks = progress ? progress.querySelectorAll("[data-chap]") : null;
  var overlayEl = document.getElementById("lc-overlay");
  var finalEl = document.querySelector(".lc-chapter-final");
  var rIndex = 0;
  FRAMES.forEach(function (f, i) { if (f.id === "r") rIndex = i; });
  var rScale = 1;
  var screenWrap = null;

  // Compteurs des chiffres de marge : ils montent une seule fois, quand
  // la piece terminee vient d'etre revelee.
  var countersDone = false;
  function spaced(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }
  function runCounters(root) {
    Array.prototype.forEach.call(root.querySelectorAll("[data-count]"), function (el) {
      var target = Number(el.dataset.count || 0);
      var pre = el.dataset.prefix || "", suf = el.dataset.suffix || "";
      if (reduceMotion) { el.textContent = pre + spaced(target) + suf; return; }
      var start = null, dur = 1250;
      (function step(now) {
        if (start === null) start = now;
        var t = Math.min(1, (now - start) / dur);
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = pre + spaced(Math.round(target * eased)) + suf;
        if (t < 1) requestAnimationFrame(step);
      })(performance.now());
    });
  }

  var revealEdge = null;
  var phaseEl = document.getElementById("lc-phase");
  var scrim = document.getElementById("lc-scrim");
  var lateBlock = document.querySelector(".lc-block-late");

  (function buildRevealEdge() {
    var stage = document.querySelector(".lc-stage");
    if (!stage) return;
    revealEdge = document.createElement("span");
    revealEdge.className = "lc-reveal-edge";
    revealEdge.setAttribute("aria-hidden", "true");
    stage.appendChild(revealEdge);
  })();

  // -------------------------------------------------------------------
  // 5. EMPLACEMENT ECRAN PRODUIT (frame R)
  //    L'image de fond est en object-fit: cover : on recalcule donc le
  //    rectangle reellement occupe par la photo pour poser l'ecran
  //    exactement sur le moniteur, quelle que soit la taille du viewport.
  // -------------------------------------------------------------------
  // Rendu en HTML et non en image : on reutilise ainsi les polices de la
  // page, le texte reste net a toutes les resolutions, et il n'y a aucun
  // fichier supplementaire a charger.
  var screenSlot = null;
  if (PRODUCT_SCREEN.enabled) {
    screenSlot = document.createElement("div");
    screenSlot.className = "lc-screen";
    screenSlot.setAttribute("aria-hidden", "true");
    screenSlot.innerHTML = '<img class="lc-screen-logo" src="' + BASE.replace("frames/", "") + 'logo.webp" alt="" decoding="async">'
      + '<span class="lc-screen-rule"></span>'
      + '<span class="lc-screen-word">Suite Artisan</span>';
    // Un conteneur qui rejoue exactement le zoom Ken Burns de la frame R
    // (meme origine 50% 50%, meme boite que les photos). Le calque garde
    // ainsi sa propre matrice de perspective, sans avoir a la combiner
    // avec l'echelle a la main.
    screenWrap = document.createElement("div");
    screenWrap.className = "lc-screen-wrap";
    screenWrap.setAttribute("aria-hidden", "true");
    screenWrap.appendChild(screenSlot);
    // Dans .lc-layers et non dans .lc-stage : l'ecran doit subir la meme
    // parallaxe au curseur que la photo, sinon il glisse a cote du
    // moniteur des que la souris bouge.
    layers.appendChild(screenWrap);
  }

  // Homographie envoyant le rectangle (0,0)-(W0,H0) sur un quadrilatere
  // quelconque. C'est la seule transformation capable de rendre deux
  // bords verticaux de pentes differentes, donc la perspective du
  // moniteur. Formule classique pour le carre unite, puis remise a
  // l'echelle du rectangle source.
  function homography(W0, H0, q) {
    var x0 = q[0][0], y0 = q[0][1], x1 = q[1][0], y1 = q[1][1];
    var x2 = q[2][0], y2 = q[2][1], x3 = q[3][0], y3 = q[3][1];
    var dx1 = x1 - x2, dy1 = y1 - y2;
    var dx2 = x3 - x2, dy2 = y3 - y2;
    var sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
    var den = dx1 * dy2 - dx2 * dy1;
    var g = (sx * dy2 - dx2 * sy) / den;
    var hh = (dx1 * sy - sx * dy1) / den;
    var a = x1 - x0 + g * x1, b = x3 - x0 + hh * x3, c = x0;
    var d = y1 - y0 + g * y1, e = y3 - y0 + hh * y3, f = y0;
    // matrix3d est en colonnes ; on divise par W0/H0 pour partir du
    // rectangle source plutot que du carre unite.
    return "matrix3d("
      + (a / W0) + "," + (d / W0) + ",0," + (g / W0) + ","
      + (b / H0) + "," + (e / H0) + ",0," + (hh / H0) + ","
      + "0,0,1,0," + c + "," + f + ",0,1)";
  }

  function placeScreen() {
    if (!screenSlot) return;
    var W = window.innerWidth, H = window.innerHeight, ar = FRAME_AR;
    var w = W, h = W / ar;
    if (h < H) { h = H; w = H * ar; }
    var offX = (W - w) / 2, offY = (H - h) / 2;
    // Les quatre coins ramenes en pixels du viewport
    var pt = function (p) { return [offX + w * p[0] / 100, offY + h * p[1] / 100]; };
    var TL = pt(PRODUCT_SCREEN.tl), TR = pt(PRODUCT_SCREEN.tr);
    var BR = pt(PRODUCT_SCREEN.br), BL = pt(PRODUCT_SCREEN.bl);
    var hyp = function (a, b) { return Math.hypot(b[0] - a[0], b[1] - a[1]); };
    // Boite source : les longueurs moyennes du quadrilatere, pour que le
    // contenu soit mis en page a la bonne echelle avant deformation.
    var W0 = (hyp(TL, TR) + hyp(BL, BR)) / 2;
    var H0 = (hyp(TL, BL) + hyp(TR, BR)) / 2;
    var sw = W0;
    screenSlot.style.left = TL[0] + "px";
    screenSlot.style.top = TL[1] + "px";
    screenSlot.style.width = W0 + "px";
    screenSlot.style.height = H0 + "px";
    // Coins exprimes relativement au coin haut-gauche de l'element
    screenSlot.style.transform = homography(W0, H0, [
      [0, 0],
      [TR[0] - TL[0], TR[1] - TL[1]],
      [BR[0] - TL[0], BR[1] - TL[1]],
      [BL[0] - TL[0], BL[1] - TL[1]]
    ]);
    // Tout l'interieur est dimensionne en em : une seule valeur a poser
    // pour que la marque suive la taille reelle du moniteur a l'ecran.
    screenSlot.style.fontSize = (sw * 0.098).toFixed(2) + "px";
  }

  // -------------------------------------------------------------------
  // 6. BRANCHEMENT AU SCROLL
  //    GSAP + ScrollTrigger pilotent la progression (ils gerent proprement
  //    resize, refresh et restauration de position). Si le CDN ne repond
  //    pas, on retombe sur un listener natif : la page reste identique.
  // -------------------------------------------------------------------
  var hasGsap = typeof window.gsap !== "undefined" && typeof window.ScrollTrigger !== "undefined";

  // --- LISSAGE ------------------------------------------------------
  // La camera glisse vers la position de scroll au lieu de la suivre au
  // pixel pres. C'est ce qui separe "une image qui bouge quand je
  // scrolle" d'un vrai mouvement de camera : la molette donne une
  // impulsion, le plan la rattrape.
  var SMOOTH = 0.11;
  var targetY = 0, currentY = 0, looping = false;

  // Parallaxe au curseur : quelques pixels seulement, mais la scene
  // cesse d'etre une image plate. Souris uniquement — au doigt, le
  // pointeur EST le scroll, ca n'aurait aucun sens.
  var pointerFine = !!(window.matchMedia && window.matchMedia("(pointer: fine)").matches);
  var tmx = 0, tmy = 0, mx = 0, my = 0;

  function loop() {
    var dy = targetY - currentY;
    var dmx = tmx - mx, dmy = tmy - my;
    currentY += dy * SMOOTH;
    mx += dmx * 0.07;
    my += dmy * 0.07;
    if (Math.abs(dy) < 0.4) currentY = targetY;
    if (Math.abs(dmx) < 0.002) mx = tmx;
    if (Math.abs(dmy) < 0.002) my = tmy;

    render(currentY);
    placeScreen();
    if (pointerFine) {
      // scale(1.03) : la marge qui evite de decouvrir un bord en
      // deplacant le calque de quelques pixels.
      layers.style.transform = "scale(1.03) translate3d("
        + (-mx * 9).toFixed(2) + "px," + (-my * 6).toFixed(2) + "px,0)";
    }

    if (currentY === targetY && mx === tmx && my === tmy) { looping = false; return; }
    requestAnimationFrame(loop);
  }
  function kick() { if (!looping) { looping = true; requestAnimationFrame(loop); } }

  function frame() {
    targetY = window.scrollY - filmTop;
    currentY = targetY;
    render(currentY);
    placeScreen();
    // Pose l'echelle du calque des le depart : sans cela le scale(1.03)
    // apparaitrait d'un coup au premier mouvement de souris.
    if (pointerFine && !reduceMotion) layers.style.transform = "scale(1.03) translate3d(0,0,0)";
  }

  if (pointerFine && !reduceMotion) {
    window.addEventListener("pointermove", function (e) {
      tmx = (e.clientX / window.innerWidth - 0.5) * 2;
      tmy = (e.clientY / window.innerHeight - 0.5) * 2;
      kick();
    }, { passive: true });
  }

  if (reduceMotion) {
    // Pas de camera, pas de scroll pilote : la page redevient une page
    // normale. Chaque scene devient une section classique avec, en fond,
    // la photo de pause de son chapitre. Tout le contenu est lisible et
    // rien ne bouge.
    document.body.classList.add("lc-static");
    var PAUSE = { 1: "a", 2: "d", 3: "i", 4: "l", 5: "o", 6: "r" };
    Object.keys(PAUSE).forEach(function (s) {
      if (!sceneEls[s]) return;
      sceneEls[s].classList.add("is-on");
      sceneEls[s].style.backgroundImage = "url(" + BASE + "frame-" + PAUSE[s] + ".webp)";
    });
    var fin = document.querySelector(".lc-chapter-final");
    if (fin) fin.style.backgroundImage = "url(" + BASE + "frame-t.webp)";
    if (lateBlock) lateBlock.classList.add("is-ready");
    if (phaseEl) Array.prototype.forEach.call(phaseEl.children, function (s) { s.classList.add("is-on"); });
  } else if (hasGsap) {
    window.gsap.registerPlugin(window.ScrollTrigger);
    measure();
    window.ScrollTrigger.create({
      trigger: film,
      start: "top top",
      end: "bottom bottom",
      onUpdate: function (self) { targetY = self.progress * filmRange; kick(); },
      onRefresh: function () { measure(); lastIndex = -1; frame(); }
    });
    frame();
  } else {
    measure();
    var onScroll = function () { targetY = window.scrollY - filmTop; kick(); };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () { measure(); lastIndex = -1; frame(); }, { passive: true });
    frame();
  }

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
  if ("IntersectionObserver" in window && chapterEls[7] && progressLinks) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        Array.prototype.forEach.call(progressLinks, function (a) {
          a.parentNode.classList.toggle("is-on", a.dataset.chap === "7");
        });
      });
    }, { threshold: 0.01, rootMargin: "-45% 0px -45% 0px" }).observe(chapterEls[7]);
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
  })();

  // Recalage si les polices arrivent apres coup (evite un decalage des
  // hauteurs de chapitre mesurees trop tot).
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () {
      if (hasGsap && !reduceMotion) window.ScrollTrigger.refresh();
      else { measure(); lastIndex = -1; frame(); }
    });
  }
})();
