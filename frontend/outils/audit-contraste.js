/* =====================================================================
   Audit de contraste — à coller dans la console du navigateur
   ---------------------------------------------------------------------
   Parcourt tout ce qui est réellement visible à l'écran, calcule le
   contraste de chaque texte contre son fond effectif, et liste ce qui
   passe sous le seuil WCAG 2.1 (4.5:1 pour le texte courant, 3:1 pour le
   grand texte).

   Usage :
     auditContraste()              // toute l'application
     auditContraste('#view-devis') // une seule vue

   POURQUOI CET OUTIL EXISTE
   Deux pièges ont chacun coûté une correction pendant la refonte, et
   aucun des deux ne se voit à l'œil :

   1. Le fond effectif n'est pas le premier fond non transparent trouvé en
      remontant l'arbre. Un survol à 7 % d'opacité doit être APLATI sur ce
      qu'il recouvre, sinon la mesure compare un texte à une couleur qui
      n'existe pas. Sans cet aplatissement, l'élément de navigation actif
      ressortait à 1:1 — un faux positif spectaculaire.

   2. Un élément masqué par un ancêtre a bien `display: block` sur
      lui-même. Tester `display` sur l'élément seul laisse donc passer
      toute la navigation mobile, mesurée contre un fond qui n'est pas le
      sien. Le seul test fiable est la boîte réellement occupée.
   ===================================================================== */
(function () {
  const canaux = (couleur) => couleur.match(/[\d.]+/g).slice(0, 3).map(Number);
  const lineaire = (x) => {
    x /= 255;
    return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
  };
  const luminance = (couleur) => {
    const [r, v, b] = canaux(couleur);
    return 0.2126 * lineaire(r) + 0.7152 * lineaire(v) + 0.0722 * lineaire(b);
  };
  const contraste = (a, b) => {
    const l1 = luminance(a), l2 = luminance(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };

  /** Le fond effectif : on empile les couches translucides rencontrées en
   *  remontant, puis on les aplatit de la plus profonde à la plus proche. */
  const fondEffectif = (el) => {
    const pile = [];
    let n = el;
    while (n && n !== document.documentElement) {
      const bg = getComputedStyle(n).backgroundColor;
      const m = bg && bg.match(/[\d.]+/g);
      if (m) {
        const alpha = m.length > 3 ? parseFloat(m[3]) : 1;
        if (alpha > 0) {
          pile.push([canaux(bg), alpha]);
          if (alpha >= 1) break;
        }
      }
      n = n.parentElement;
    }
    let out = canaux(getComputedStyle(document.documentElement).backgroundColor || "rgb(255,255,255)");
    for (let i = pile.length - 1; i >= 0; i--) {
      const [c, a] = pile[i];
      out = [0, 1, 2].map((k) => a * c[k] + (1 - a) * out[k]);
    }
    return `rgb(${out.map(Math.round).join(", ")})`;
  };

  const estVisible = (el) => {
    const b = el.getBoundingClientRect();
    return b.width > 0 && b.height > 0 && el.offsetParent !== null;
  };

  window.auditContraste = function (racine = ".app-shell") {
    const hote = document.querySelector(racine);
    if (!hote) return `Racine introuvable : ${racine}`;
    const echecs = [];
    let audites = 0;

    for (const el of hote.querySelectorAll("*")) {
      // Seul le texte porté DIRECTEMENT par l'élément compte : sinon un
      // conteneur serait mesuré avec la couleur de son premier enfant.
      const texte = [...el.childNodes]
        .filter((n) => n.nodeType === 3 && n.textContent.trim())
        .map((n) => n.textContent.trim())
        .join(" ");
      if (!texte || !estVisible(el)) continue;
      audites++;

      const s = getComputedStyle(el);
      const px = parseFloat(s.fontSize);
      const gras = parseInt(s.fontWeight, 10) >= 600;
      // WCAG : « grand texte » = 24px, ou 18.66px si gras.
      const seuil = px >= 24 || (px >= 18.66 && gras) ? 3 : 4.5;
      const mesure = contraste(s.color, fondEffectif(el));
      if (mesure < seuil) {
        echecs.push({
          element: el.className || el.tagName,
          texte: texte.slice(0, 40),
          mesure: +mesure.toFixed(2),
          seuil,
          couleur: s.color,
          fond: fondEffectif(el),
        });
      }
    }

    if (!echecs.length) {
      console.log(`%cAucun échec de contraste — ${audites} éléments audités.`, "color:#3B6647;font-weight:600");
      return [];
    }
    console.log(`%c${echecs.length} échec(s) sur ${audites} éléments audités`, "color:#9E3A2B;font-weight:600");
    console.table(echecs);
    return echecs;
  };

  console.log("auditContraste() est prêt. auditContraste('#view-devis') pour une seule vue.");
})();
