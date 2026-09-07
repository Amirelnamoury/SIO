/* =====================================================================
   STATISTIQUES — le rapport et son graphique
   ---------------------------------------------------------------------
   Quatrieme decoupage de app.js par domaine (Astra §16). Meme regle que
   les precedents : aucune ligne reecrite, seulement deplacee. Voir
   docs/DECOUPAGE-FRONTEND.md.

   Un rapport, pas un tableau de bord : chaque section annonce SA periode,
   chaque chiffre dit sur quelle population il porte, et ceux dont la
   population a un filtre equivalent dans une liste ouvrent leurs pieces.
   La courbe distingue le mois en cours - incomplet - des mois revolus.

   Charge APRES planning.js et AVANT app.js (voir index.html).
   ===================================================================== */

// ===================== Statistiques =====================
function fmtMoisCourt(moisIso) {
  const [annee, mois] = String(moisIso).split("-").map(Number);
  if (!annee || !mois) return escapeHtml(moisIso);
  return new Date(annee, mois - 1, 1).toLocaleDateString("fr-FR", { month: "short" });
}

// Graphique en aire (SVG inline) du CA par mois : memes points que
// l'ancienne liste .dash-row (a.ca_par_mois), juste trace au lieu
// d'enumere. Echelle lineaire simple, pas de librairie.
// OUVRIR LES ELEMENTS SOURCES D'UN CHIFFRE.
//
// Un indicateur qu'on ne peut pas ouvrir est un indicateur qu'on ne peut pas
// verifier : « 21 devis signés » ne se recoupe qu'en allant voir lesquels.
// Chaque entree ci-dessous nomme une population EXACTE, atteignable avec un
// filtre qui existe deja dans la liste visee. Les chiffres dont la population
// n'a pas de filtre equivalent - le taux de signature porte sur les devis
// « decides », les clients acquis sur un statut absent de l'annuaire - ne
// recoivent volontairement aucun lien : ouvrir un sur-ensemble en pretendant
// montrer la source serait pire que de ne rien ouvrir.
const SOURCES_STATISTIQUES = {
  "devis-crees": { vue: "devis", ouvrir: () => activerDevisFiltreStatut("") },
  "devis-signes": { vue: "devis", ouvrir: () => activerDevisFiltreStatut("signe") },
  "factures-dues": { vue: "factures", ouvrir: () => activerFactureFiltreStatut("a_encaisser") },
  "factures-payees": { vue: "factures", ouvrir: () => activerFactureFiltreStatut("payee") },
};

/** Bouton discret « voir les N pièces » accroché à un chiffre. */
function lienSource(cle, libelle) {
  return SOURCES_STATISTIQUES[cle]
    ? ` <button type="button" class="stats-source" data-action="ouvrir-source" data-source="${cle}">${escapeHtml(libelle)}</button>`
    : "";
}

async function ouvrirSourceStatistique(cle) {
  const source = SOURCES_STATISTIQUES[cle];
  if (!source) return;
  await switchView(source.vue);
  await source.ouvrir();
}

function caAreaChartSvg(caParMois, { dernierEnCours = false } = {}) {
  // PAD_R tient compte de l'etiquette du dernier mois, centree sous son
  // point : a 8 px, « sept. » sortait du cadre et se retrouvait rognee.
  // PAD_L : la gouttiere de gauche doit contenir la GRADUATION la plus
  // large. Mesuree a 44 px, elle en demandait 60 tant que l'axe affichait
  // des montants complets ; l'axe est passe aux ordres de grandeur
  // (fmtEuroAxe) et 52 px lui laissent de la marge.
  const W = 760, H = 220, PAD_L = 52, PAD_R = 22, PAD_T = 12, PAD_B = 24;
  const values = caParMois.map((m) => m.ca);
  const max = Math.max(1, ...values);
  const innerW = W - PAD_L - PAD_R, innerH = H - PAD_T - PAD_B;
  const stepX = caParMois.length > 1 ? innerW / (caParMois.length - 1) : 0;
  const points = values.map((v, i) => ({
    x: PAD_L + stepX * i,
    y: PAD_T + innerH - (v / max) * innerH,
  }));
  // Le dernier mois de la fenetre est le mois EN COURS : il n'est pas
  // comparable aux autres, et trace plein il ressemble a un effondrement le
  // 3 du mois. Son segment est pointille et l'aplat s'arrete avant lui.
  const dernier = points.length - 1;
  const finPleine = dernierEnCours && points.length > 1 ? dernier - 1 : dernier;
  const chemin = (deb, fin) => points.slice(deb, fin + 1)
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const linePath = chemin(0, finPleine);
  const segmentEnCours = finPleine < dernier ? chemin(finPleine, dernier) : "";
  const areaPath = `${linePath} L${points[finPleine].x.toFixed(1)},${PAD_T + innerH} L${points[0].x.toFixed(1)},${PAD_T + innerH} Z`;
  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const y = PAD_T + innerH * (1 - f);
    return `<line x1="${PAD_L}" y1="${y.toFixed(1)}" x2="${W - PAD_R}" y2="${y.toFixed(1)}" class="chart-gridline"/>
      <text x="${PAD_L - 8}" y="${(y + 3).toFixed(1)}" class="chart-axis-label" text-anchor="end">${fmtEuroAxe(Math.round(max * f))}</text>`;
  }).join("");
  const moisLabels = caParMois.map((m, i) => {
    if (caParMois.length > 8 && i % 2 !== 0 && i !== caParMois.length - 1) return "";
    return `<text x="${points[i].x.toFixed(1)}" y="${H - 6}" class="chart-axis-label" text-anchor="middle">${fmtMoisCourt(m.mois)}</text>`;
  }).join("");
  return `
  <svg viewBox="0 0 ${W} ${H}" class="chart-svg" role="img" aria-label="Chiffre d'affaires par mois">
    <defs>
      <linearGradient id="chartFade" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--sa-accent)" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="var(--sa-accent)" stop-opacity="0"/>
      </linearGradient>
    </defs>
    ${gridLines}
    <path d="${areaPath}" fill="url(#chartFade)"/>
    <path d="${linePath}" fill="none" stroke="var(--sa-accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    ${segmentEnCours ? `<path d="${segmentEnCours}" fill="none" stroke="var(--sa-accent)" stroke-width="2" stroke-dasharray="4 3" stroke-linecap="round" opacity="0.6"/>` : ""}
    ${moisLabels}
  </svg>`;
}

// Interpolation pure entre deux couleurs hex (#rrggbb) - aucune donnee
// metier, sert uniquement a degrader la couleur de fond de chaque etape
// du ruban "Performance commerciale" (pale -> accent champagne).
function mixHexColors(hexA, hexB, t) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

async function loadStatistiques() {
  const container = document.getElementById("statistiques-content");
  debutChargement(container);
  if (!hasPlan("essentiel")) {
    container.innerHTML = renderUpgradeCard(
      "Statistiques réservées aux abonnés",
      "Le suivi de la performance commerciale et financière (CA, taux d'acceptation, impayés, panier moyen) fait partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  try {
    const a = await Api.analytics();
    const caTotal = a.ca_par_mois.reduce((s, m) => s + m.ca, 0);
    // Le dernier point de la serie est le mois EN COURS. Comparer un mois
    // commence il y a trois jours au mois complet qui le precede produisait
    // une chute mecanique, annoncee comme un recul reel. La comparaison porte
    // donc sur les deux derniers mois COMPLETS, et le libelle le dit.
    const nbMois = a.ca_par_mois.length;
    const moisEnCours = nbMois ? a.ca_par_mois[nbMois - 1] : null;
    const dernierComplet = nbMois > 1 ? a.ca_par_mois[nbMois - 2] : null;
    const avantDernierComplet = nbMois > 2 ? a.ca_par_mois[nbMois - 3] : null;
    const deltaPct = dernierComplet && avantDernierComplet && avantDernierComplet.ca
      ? Math.round(((dernierComplet.ca - avantDernierComplet.ca) / avantDernierComplet.ca) * 100)
      : null;

    const chartHtml = a.ca_par_mois.some((m) => m.ca > 0)
      ? caAreaChartSvg(a.ca_par_mois, { dernierEnCours: true })
      : '<div class="dash-empty">Aucun paiement encaissé sur les douze derniers mois.</div>';

    const sourcesHtml = a.sources_acquisition.length
      ? a.sources_acquisition.map((s) => {
          const maxContacts = Math.max(1, ...a.sources_acquisition.map((x) => x.nb_clients));
          return `
          <div class="acq-source-row">
            <span class="acq-source-label">${escapeHtml(CLIENT_SOURCE_LABELS[s.source] || s.source)}</span>
            <div class="acq-source-bar"><div class="remplissage" style="width:${Math.round((s.nb_clients / maxContacts) * 100)}%;"></div></div>
            <span class="acq-source-value">${s.nb_clients} contact${s.nb_clients > 1 ? "s" : ""}, ${s.nb_gagnes} client${s.nb_gagnes > 1 ? "s" : ""} (${fmtEuro(s.ca)})</span>
          </div>`;
        }).join("")
      : '<div class="dash-empty">Pas encore de contact enregistré.</div>';

    // « Devis envoyés » comptait en realite TOUS les devis, brouillons
    // compris (nb_devis_total). Un devis jamais sorti du bureau etait
    // presente comme envoye au client, et le taux de conversion affiche en
    // dessous s'en trouvait fausse. Le libelle dit maintenant ce que le
    // nombre contient.
    const commercialSteps = [
      { label: "Devis créés", nb: a.nb_devis_total, population: "devis", source: "devis-crees" },
      { label: "Devis signés", nb: a.nb_devis_signes, population: "devis", source: "devis-signes" },
      // « Clients acquis » compte les clients au statut « gagné » : l'annuaire
      // ne filtre pas sur ce statut, aucun lien ne peut donc etre honnete.
      { label: "Clients acquis", nb: a.nb_clients_acquis, population: "clients" },
    ];
    // Le pourcentage n'est calcule qu'entre deux etapes qui comptent LA MEME
    // CHOSE. « Devis signés / Devis créés » compare des devis a des devis :
    // c'est un taux. « Clients acquis / Devis signés » comparait 18 clients a
    // 21 devis et affichait « 86 % » : deux populations differentes, un
    // pourcentage qui ne veut rien dire. Astra l'interdit nommement pour cet
    // ecran, et le nombre seul reste parfaitement utile.
    const commercialFunnelHtml = commercialSteps.map((etape, i) => {
      const precedent = i > 0 ? commercialSteps[i - 1] : null;
      const conversion = precedent && precedent.population === etape.population && precedent.nb && etape.nb <= precedent.nb
        ? Math.round((etape.nb / precedent.nb) * 100)
        : null;
      // Le degrade etait calcule en inline sur des valeurs de l'ancienne
      // identite sombre : sur du papier, le texte y tombait jusqu'a
      // 3.01:1. L'etape porte desormais son rang en classe, et c'est la
      // feuille de style qui decide - la densite se lit sur le FILET du
      // bas, pas sur un aplat derriere le texte.
      return `${i ? '<span class="stats-commercial-arrow" aria-hidden="true">&rarr;</span>' : ""}
        <div class="stats-commercial-step est-etape-${i + 1}">
          <span>${escapeHtml(etape.label)}</span>
          <strong>${etape.nb}${conversion !== null ? ` (${conversion} %)` : ""}</strong>
          ${etape.source ? lienSource(etape.source, "Voir ces devis") : ""}
        </div>`;
    }).join("");

    const topSource = a.sources_acquisition.slice().sort((x, y) => y.nb_gagnes - x.nb_gagnes || y.ca - x.ca)[0] || null;
    const pointsCles = [
      deltaPct === null
        ? "Le suivi mensuel sera comparable après deux mois complets de paiements."
        : `Sur les deux derniers mois complets, le chiffre d'affaires ${deltaPct >= 0 ? "progresse" : "recule"} de ${Math.abs(deltaPct)} % (${fmtMoisCourt(dernierComplet.mois)} contre ${fmtMoisCourt(avantDernierComplet.mois)}).`,
      topSource
        ? `${CLIENT_SOURCE_LABELS[topSource.source] || topSource.source} est la première source d'acquisition avec ${topSource.nb_gagnes} client${topSource.nb_gagnes > 1 ? "s" : ""} gagné${topSource.nb_gagnes > 1 ? "s" : ""}.`
        : "Aucune source d'acquisition n'est encore mesurable.",
      a.montant_impayes > 0
        ? `${fmtEuro(a.montant_impayes)} restent à encaisser sur les factures ouvertes.`
        : "Aucun montant impayé sur les factures ouvertes.",
    ];

    // Un rapport mene avec ses conclusions, pas avec ses preuves. Les
    // « points cles » etaient en bas de page, apres quatre panneaux de
    // chiffres : personne ne lisait la lecture. Ils ouvrent desormais.
    //
    // La page adopte la gouttiere des pages COMPOSEES (voir
    // DIRECTION-ARTISTIQUE.md) : les intitules vivent dans la marge, le
    // contenu a droite. C'est la forme d'un rapport, et Statistiques en
    // est un - contrairement aux listes, qui ont besoin de leur largeur.
    container.innerHTML = `
      ${saSection("Ce qu'il faut retenir",
        `<div class="stats-lecture">${pointsCles.map((p) => `<p>${escapeHtml(p)}</p>`).join("")}</div>`)}

      ${saSection("Chiffre d'affaires", `
        <div class="stats-ca">
          <div class="stats-ca-tete">
            <span class="stats-ca-valeur">${fmtEuro(caTotal)}</span>
            <span class="stats-ca-note">encaissé${deltaPct !== null ? ` · <span class="${deltaPct >= 0 ? "est-hausse" : "est-baisse"}">${deltaPct >= 0 ? "+" : ""}${deltaPct} % entre les deux derniers mois complets</span>` : ""}</span>
          </div>
          <div class="stats-chart-wrap">${chartHtml}</div>
          ${moisEnCours ? `<p class="stats-note">Le dernier point (${escapeHtml(fmtMoisCourt(moisEnCours.mois))}) est le mois en cours : il n'est pas encore comparable aux autres, et son trait reste en pointillé.</p>` : ""}
          <div class="stats-ca-legende">
            <span>Pipeline <strong>${fmtEuro(a.valeur_pipeline)}</strong></span>
            <span>Encore à encaisser <strong>${fmtEuro(a.montant_impayes)}</strong>${lienSource("factures-dues", "Voir ces factures")}</span>
            <span class="stats-ca-legende-note">à aujourd'hui, pas sur douze mois</span>
          </div>
        </div>`, "douze derniers mois")}

      ${/* Chacune des trois sections suivantes porte enfin sa periode. Elles
            comptent depuis l'ouverture du compte, quand celle du dessus couvre
            douze mois : rien ne le disait, et les quatre blocs se lisaient
            comme un seul tableau de bord du moment. */""}
      ${saSection("Performance commerciale", `
        <div class="stats-commercial-funnel">${commercialFunnelHtml}</div>
        <div class="stats-metric-list">
          <div><span>Taux de signature</span><strong>${a.taux_acceptation === null || a.taux_acceptation === undefined ? "—" : a.taux_acceptation + " %"}</strong></div>
          <div><span>Panier moyen</span><strong>${fmtEuro(a.panier_moyen)}</strong>${lienSource("devis-signes", "Voir ces devis")}</div>
          <div><span>Valeur du pipeline</span><strong>${fmtEuro(a.valeur_pipeline)}</strong></div>
        </div>`, "depuis l'ouverture du compte")}

      ${saSection("Acquisition", `<div class="acq-source-list">${sourcesHtml}</div>`,
        "tous vos contacts, depuis l'ouverture")}

      ${saSection("Clients et paiements", `
        <div class="stats-metric-list">
          <div><span>Clients avec plusieurs devis signés</span><strong>${a.nb_clients_recurrents}</strong></div>
          <div><span>Délai moyen de paiement</span><strong>${a.delai_moyen_paiement_jours !== null ? a.delai_moyen_paiement_jours + " j" : "—"}</strong>${a.delai_moyen_paiement_jours !== null ? lienSource("factures-payees", "Voir ces factures") : ""}</div>
          <div><span>Montant impayé</span><strong>${fmtEuro(a.montant_impayes)}</strong>${lienSource("factures-dues", "Voir ces factures")}</div>
        </div>`, "depuis l'ouverture du compte")}
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}
