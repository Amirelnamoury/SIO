/* =====================================================================
   Empreinte des styles calcules — filet de securite d'un refactor CSS
   ---------------------------------------------------------------------
   Parcourt toutes les vues, chargees avec le jeu d'essai, et releve les
   styles REELLEMENT CALCULES de chaque element visible. Le resultat est
   une empreinte comparable avant / apres une modification de feuille de
   style.

   POURQUOI
   Fusionner deux feuilles « sans rien changer » est une promesse
   invérifiable a l'oeil : 3 500 lignes, des centaines de selecteurs, et
   des regressions qui ne se voient que sur une vue precise, dans un etat
   precis. La seule preuve possible est de comparer ce que le navigateur
   calcule, propriete par propriete, element par element.

   Usage :
     const avant = await empreinteStyles();   // avant le refactor
     // ... modification de la feuille ...
     const apres = await empreinteStyles();
     comparerEmpreintes(avant, apres);        // liste les differences

   Les elements sont identifies par leur CHEMIN dans l'arbre (indices des
   enfants) et non par un id : le balisage est regenere a chaque rendu, et
   deux passages doivent produire le meme chemin pour le meme element.
   ===================================================================== */
(function () {
  // Les proprietes qui portent le rendu. On evite celles qui dependent de
  // la position (top, left) : elles varient avec le defilement et
  // produiraient un bruit qui masquerait les vraies differences.
  const PROPRIETES = [
    "color", "backgroundColor", "borderTopColor", "borderRightColor",
    "borderBottomColor", "borderLeftColor", "borderTopWidth", "borderRightWidth",
    "borderBottomWidth", "borderLeftWidth", "borderRadius", "boxShadow",
    "fontFamily", "fontSize", "fontWeight", "fontStyle", "lineHeight",
    "letterSpacing", "textTransform", "textDecorationLine", "opacity",
    "display", "flexDirection", "justifyContent", "alignItems", "gap",
    "gridTemplateColumns", "padding", "margin", "width", "height",
    "textAlign", "whiteSpace", "overflow", "position", "zIndex",
  ];

  const chemin = (el, racine) => {
    const parts = [];
    let n = el;
    while (n && n !== racine) {
      parts.unshift([...n.parentElement.children].indexOf(n));
      n = n.parentElement;
    }
    return (racine.id || "?") + ":" + parts.join(".");
  };

  window.empreinteStyles = async function (chargeurs) {
    const empreinte = {};
    for (const [nom, fn] of Object.entries(chargeurs)) {
      document.querySelectorAll(".view").forEach((v) => v.setAttribute("hidden", ""));
      const vue = document.getElementById("view-" + nom);
      if (!vue) continue;
      vue.removeAttribute("hidden");
      document.body.dataset.view = nom;
      try { await fn(); } catch (e) { empreinte["ERREUR:" + nom] = String(e).slice(0, 80); continue; }
      await new Promise((r) => setTimeout(r, 140));

      for (const el of vue.querySelectorAll("*")) {
        const b = el.getBoundingClientRect();
        if (b.width === 0 && b.height === 0) continue;
        const s = getComputedStyle(el);
        const vals = {};
        for (const p of PROPRIETES) vals[p] = s[p];
        empreinte[chemin(el, vue)] = vals;
      }
    }
    // La coquille (navigation, barre du haut) compte autant que les vues.
    for (const racine of [document.querySelector(".sidebar"), document.querySelector(".topbar")]) {
      if (!racine) continue;
      for (const el of racine.querySelectorAll("*")) {
        const b = el.getBoundingClientRect();
        if (b.width === 0 && b.height === 0) continue;
        const s = getComputedStyle(el);
        const vals = {};
        for (const p of PROPRIETES) vals[p] = s[p];
        empreinte[(racine.className.split(" ")[0]) + ":" + chemin(el, racine)] = vals;
      }
    }
    return empreinte;
  };

  window.comparerEmpreintes = function (avant, apres) {
    const differences = [];
    const cles = new Set([...Object.keys(avant), ...Object.keys(apres)]);
    for (const cle of cles) {
      const a = avant[cle], b = apres[cle];
      if (!a || !b) { differences.push({ cle, quoi: !a ? "apparu" : "disparu" }); continue; }
      if (typeof a === "string" || typeof b === "string") {
        if (a !== b) differences.push({ cle, quoi: "erreur de chargement", avant: a, apres: b });
        continue;
      }
      for (const p of Object.keys(a)) {
        if (a[p] !== b[p]) differences.push({ cle, propriete: p, avant: a[p], apres: b[p] });
      }
    }
    return {
      elementsCompares: cles.size,
      differences: differences.length,
      detail: differences.slice(0, 40),
    };
  };
})();
