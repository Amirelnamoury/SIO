/* =====================================================================
   Contraste du texte posé sur la visite
   ---------------------------------------------------------------------
   Un audit de contraste ordinaire lit la couleur de fond déclarée en CSS.
   Sur la page publique il n'y en a pas : le fond est une photographie
   peinte en WebGL, recouverte d'un dégradé. Rien de tout cela n'est
   lisible depuis le DOM.

   On mesure donc le résultat RÉEL, en trois temps :
     1. les pixels du canevas sous la boîte de texte ;
     2. l'alpha du dégradé à cet endroit, obtenu en lisant le
        `background-image` calculé et en projetant le point sur l'axe du
        dégradé — la valeur appliquée, pas une valeur supposée ;
     3. la composition des deux, puis le rapport avec la couleur du texte.

   On retient le pixel le PLUS CLAIR de la zone : c'est lui qui décide de
   la lisibilité, pas la moyenne.

   USAGE
     landing.html?debug=1   (le canevas doit conserver son tampon)
     const c = await mesurerContrasteVisite(3);

   TROIS FOIS CET OUTIL M'A MENTI AVANT D'ÊTRE JUSTE, ET C'EST NOTÉ ICI
   POUR QU'ON NE REFASSE PAS LE CHEMIN :
     - il mesurait pendant le chargement d'une texture, donc l'image
       précédente : d'où `indexA`, qui dit quelle scène est réellement
       liée, et non « une scène est prête » ;
     - il itérait positionnellement sur un sous-tableau de scènes et
       comparait la boîte de texte de la scène 0 au canevas d'une autre ;
     - il lisait la moyenne de la zone au lieu de son point le plus clair.
   Une sonde fausse ne mesure rien : elle déplace le défaut dans l'outil,
   où il est bien plus difficile à voir.
   ===================================================================== */
(function () {
  const lin = (c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const lum = ([r, g, b]) => 0.2126 * lin(r / 255) + 0.7152 * lin(g / 255) + 0.0722 * lin(b / 255);
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const rgb = (s) => (s.match(/[\d.]+/g) || []).slice(0, 3).map(Number);

  function lireDegrade(el) {
    const bg = getComputedStyle(el).backgroundImage;
    const angle = parseFloat((bg.match(/([\d.]+)deg/) || [])[1]);
    const arrets = [...bg.matchAll(/rgba?\(([^)]+)\)\s+([\d.]+)%/g)].map((m) => {
      const parts = m[1].split(",").map((x) => Number(x));
      return { c: parts.slice(0, 3), a: parts.length > 3 ? parts[3] : 1, p: Number(m[2]) / 100 };
    });
    return { angle: isNaN(angle) ? 180 : angle, arrets };
  }

  function voileEn(deg, x, y, w, h) {
    if (!deg.arrets.length) return { a: 0, c: [0, 0, 0] };
    const a = (deg.angle - 90) * Math.PI / 180;
    const ux = Math.cos(a), uy = Math.sin(a);
    const L = Math.abs(w * Math.cos(a)) + Math.abs(h * Math.sin(a));
    const p = Math.max(0, Math.min(1, (((x - w / 2) * ux + (y - h / 2) * uy) / L) + 0.5));
    let av = deg.arrets[0];
    for (let i = 1; i < deg.arrets.length; i++) {
      const ap = deg.arrets[i];
      if (p <= ap.p) {
        const k = ap.p === av.p ? 0 : (p - av.p) / (ap.p - av.p);
        return { a: av.a + (ap.a - av.a) * k, c: av.c };
      }
      av = ap;
    }
    return { a: av.a, c: av.c };
  }

  /** Mesure la scène `i` telle qu'elle est peinte MAINTENANT. */
  window.mesurerContrasteVisite = function (i) {
    const canvas = document.getElementById("lc-canvas");
    const ombre = document.getElementById("lc-ombre");
    const vue = document.querySelector('.lc-vue[data-vue="' + i + '"]');
    if (!canvas || !ombre || !vue) return { erreur: "element introuvable pour la scene " + i };
    const bloc = vue.querySelector(".lc-bloc");
    const r = bloc.getBoundingClientRect();
    const cr = canvas.getBoundingClientRect();

    const c2 = document.createElement("canvas");
    c2.width = Math.max(1, Math.round(cr.width));
    c2.height = Math.max(1, Math.round(cr.height));
    const ctx = c2.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(canvas, 0, 0, c2.width, c2.height);

    const x0 = Math.max(0, Math.round(r.left - cr.left));
    const y0 = Math.max(0, Math.round(r.top - cr.top));
    const w = Math.max(1, Math.min(c2.width - x0, Math.round(r.width)));
    const h = Math.max(1, Math.min(c2.height - y0, Math.round(r.height)));
    const data = ctx.getImageData(x0, y0, w, h).data;

    const deg = lireDegrade(ombre);

    /* DEUXIEME VOILE : l'ombre posee derriere le bloc de texte.
       Sur mobile, assombrir tout l'ecran assez pour tenir le contraste
       sur une piece pleine de baies vitrees reviendrait a noircir la
       photographie. Une ombre locale est donc posee derriere le bloc, en
       ::before. Elle est invisible au DOM : si la sonde l'ignore, elle
       sous-estime le contraste reel et fait corriger un faux probleme. */
    const st = getComputedStyle(bloc, "::before");
    let voileBloc = null;
    if (st && st.content && st.content !== "none" && /gradient/.test(st.backgroundImage)) {
      const px = (v) => (parseFloat(v) || 0);
      const b = bloc.getBoundingClientRect();
      // Les retraits sont NEGATIFS : `top: -26px` place le bord 26 px
      // AU-DESSUS du bloc, et agrandit la boite d'autant. Les additionner
      // revenait a la retrecir - la sonde cherchait alors le voile la ou
      // il n'est pas, et rapportait exactement les memes echecs qu'avant
      // la correction. Un signe inverse dans une sonde ressemble a s'y
      // meprendre a une correction sans effet.
      voileBloc = {
        deg: null,
        boite: {
          x: 0,
          y: b.top - cr.top + px(st.top),
          w: c2.width,
          h: b.height - px(st.top) - px(st.bottom),
        },
      };
      // On lit le degrade du pseudo-element directement.
      const bg = st.backgroundImage;
      const angle = parseFloat((bg.match(/([\d.]+)deg/) || [])[1]);
      const arrets = [...bg.matchAll(/rgba?\(([^)]+)\)\s+([\d.]+)%/g)].map((m) => {
        const p = m[1].split(",").map(Number);
        return { c: p.slice(0, 3), a: p.length > 3 ? p[3] : 1, p: Number(m[2]) / 100 };
      });
      voileBloc.deg = { angle: isNaN(angle) ? 180 : angle, arrets };
      // Le voile s'etend d'un bord a l'autre : sa boite couvre la largeur
      // du canevas, seule sa hauteur compte.
      voileBloc.boite.x = 0;
      voileBloc.boite.w = c2.width;
    }
    function voileLocalEn(gx, gy) {
      if (!voileBloc) return { a: 0, c: [0, 0, 0] };
      const bo = voileBloc.boite;
      if (gy < bo.y || gy > bo.y + bo.h) return { a: 0, c: [0, 0, 0] };
      return voileEn(voileBloc.deg, gx - bo.x, gy - bo.y, bo.w, bo.h);
    }

    /* Le fond le plus clair SOUS UN ELEMENT DONNE.
       Mesurer une seule fois pour toute la boite surestime le probleme :
       un titre pose sur une zone sombre etait juge d'apres un pixel clair
       situe sous le paragraphe, trois lignes plus bas. */
    function fondSous(el) {
      const b = el.getBoundingClientRect();
      const ex = Math.max(0, Math.round(b.left - cr.left));
      const ey = Math.max(0, Math.round(b.top - cr.top));
      const ew = Math.max(1, Math.min(c2.width - ex, Math.round(b.width)));
      const eh = Math.max(1, Math.min(c2.height - ey, Math.round(b.height)));
      let pire = null, pireLum = -1;
      const pas = Math.max(1, Math.floor(Math.min(ew, eh) / 14));
      for (let y = 0; y < eh; y += pas) {
        for (let x = 0; x < ew; x += pas) {
          const px = ex - x0 + x, py = ey - y0 + y;
          if (px < 0 || py < 0 || px >= w || py >= h) continue;
          const k = (py * w + px) * 4;
          // Les deux voiles sont composes dans l'ordre de la page : la
          // photographie, puis l'ombre du bloc, puis l'ombre d'ecran.
          const local = voileLocalEn(ex + x, ey + y);
          const ecran = voileEn(deg, ex + x, ey + y, c2.width, c2.height);
          let compose = [data[k], data[k + 1], data[k + 2]];
          compose = compose.map((c, j) => c * (1 - local.a) + local.c[j] * local.a);
          compose = compose.map((c, j) => c * (1 - ecran.a) + ecran.c[j] * ecran.a);
          const L = lum(compose);
          if (L > pireLum) { pireLum = L; pire = compose; }
        }
      }
      return pire;
    }

    /* Le seuil depend de la TAILLE du texte, pas de son role.
       WCAG : 3:1 a partir de 24 px, ou 18,7 px en gras. En dessous,
       4,5:1. Juger un titre de 3,5 rem au seuil du texte courant
       conduirait a noircir la photographie pour rien. */
    function juger(el, nom) {
      if (!el) return null;
      const cs = getComputedStyle(el);
      const px = parseFloat(cs.fontSize);
      const gras = (parseInt(cs.fontWeight, 10) || 400) >= 700;
      const grand = px >= 24 || (gras && px >= 18.66);
      const fond = fondSous(el);
      if (!fond) return null;
      const r = +ratio(rgb(cs.color), fond).toFixed(2);
      const seuil = grand ? 3 : 4.5;
      return { nom, px: +px.toFixed(1), grand, ratio: r, seuil, ok: r >= seuil };
    }

    const elements = [
      juger(vue.querySelector(".lc-h1, .lc-h2"), "titre"),
      juger(vue.querySelector(".lc-lead"), "lead"),
      juger(vue.querySelector(".lc-eyebrow"), "eyebrow"),
      juger(vue.querySelector(".lc-note"), "note"),
    ].filter(Boolean);

    return {
      i,
      cote: vue.dataset.cote,
      ok: elements.every((e) => e.ok),
      elements,
    };
  };
})();
