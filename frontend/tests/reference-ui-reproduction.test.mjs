import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const indexSource = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");
const appSource = fs.readFileSync(path.join(frontendDir, "app.js"), "utf8");
const styleSource = fs.readFileSync(path.join(frontendDir, "style.css"), "utf8");

const views = [
  "dashboard", "prospects", "clients", "devis", "factures", "chantiers", "planning",
  "taches", "documents", "statistiques", "avis", "entreprise", "notifications",
];
for (const view of views) {
  assert.match(indexSource, new RegExp(`id="view-${view}"`), `la vue ${view} doit rester présente`);
}

assert.match(appSource, /document\.body\.dataset\.view = view/);
assert.match(appSource, /matchMedia\("\(max-width: 900px\)"\)/);
assert.match(indexSource, /class="devis-modulebar"/);
assert.match(indexSource, /id="clients-pagination"/);

for (const id of [
  "documents-type-filter", "documents-client-filter", "documents-chantier-filter",
  "documents-date-filter", "documents-sort",
]) {
  assert.match(indexSource, new RegExp(`id="${id}"`), `${id} doit être rendu`);
  assert.ok(appSource.includes(`getElementById("${id}")`), `${id} doit être fonctionnel`);
}

assert.match(appSource, /documentsChantiersCache/);
assert.match(appSource, /String\(d\.chantier_id \|\| ""\)/);
assert.match(appSource, /String\(d\.client_id \|\| ""\)/);

const factureStart = appSource.indexOf("function renderFactureCard");
const factureEnd = appSource.indexOf("function showPaiementForm", factureStart);
const factureRenderer = appSource.slice(factureStart, factureEnd);
assert.doesNotMatch(factureRenderer, /toggle-chantier-details/);
assert.doesNotMatch(factureRenderer, /\$\{c\.id\}/);
assert.match(factureRenderer, /monogram\(f\.client_nom\)/);

const chantierActionsStart = appSource.indexOf("function chantierActionsHtml");
const chantierActionsEnd = appSource.indexOf("function renderChantierCard", chantierActionsStart);
assert.match(appSource.slice(chantierActionsStart, chantierActionsEnd), /toggle-chantier-details/);

assert.match(appSource, /const a = await Api\.analytics\(\)/);
// Statistiques est passe des panneaux empiles a la gouttiere des pages
// composees, et les « points cles » ont remonte en tete : un rapport mene
// avec ses conclusions, pas avec ses preuves. Ce qui est garde ici est
// l'INTENTION - la page raconte quelque chose avant d'aligner des
// chiffres - et non les anciens noms de panneaux.
{
  const statsStart = appSource.indexOf("async function loadStatistiques");
  const statsEnd = appSource.indexOf("async function loadAvis", statsStart);
  const stats = appSource.slice(statsStart, statsEnd);
  assert.ok(statsStart !== -1 && statsEnd > statsStart, "loadStatistiques est introuvable");
  assert.match(stats, /saSection\("Ce qu'il faut retenir"/, "la lecture doit ouvrir la page");
  assert.ok(
    stats.indexOf("Ce qu'il faut retenir") < stats.indexOf("Chiffre d'affaires"),
    "les points clés doivent précéder les chiffres",
  );
  for (const bloc of ["Chiffre d'affaires", "Performance commerciale", "Acquisition", "Clients et paiements"]) {
    assert.ok(stats.includes(bloc), `section perdue dans la refonte : ${bloc}`);
  }
  // Les mesures elles-memes doivent rester : la refonte recompose, elle
  // ne retire pas d'information.
  for (const mesure of ["taux_acceptation", "panier_moyen", "valeur_pipeline",
    "delai_moyen_paiement_jours", "montant_impayes", "sources_acquisition"]) {
    assert.ok(stats.includes(mesure), `mesure perdue dans la refonte : ${mesure}`);
  }
}
assert.doesNotMatch(appSource, /84\s?720\s?€/);
assert.doesNotMatch(appSource, /45\s?300\s?€/);

assert.match(indexSource, /data-action="show-avis-request-form"/);
assert.match(appSource, /async function showAvisRequestForm/);
assert.match(appSource, /await demanderAvisEtCopierLien\(clientId\)/);
assert.match(indexSource, /data-action="show-avis-form">Saisir un avis/);

assert.match(indexSource, /id="ent-email" readonly/);
assert.match(indexSource, /id="enterprise-profile-progress"/);
assert.match(appSource, /function refreshEntrepriseProfileSummary/);
assert.match(appSource, /entreprise-form-cancel/);

assert.match(indexSource, /id="notifications-module-filter"/);
assert.match(appSource, /currentNotificationModule/);
assert.match(appSource, /function fmtNotificationDate/);
assert.match(appSource, /label: "À traiter"/);

assert.match(styleSource, /body\[data-view="planning"\] \.content \{ padding: 28px 45px 72px; \}/);
assert.match(styleSource, /body\[data-view="documents"\] \.content \{ padding: 36px 80px 72px; \}/);
assert.match(styleSource, /body\[data-view="statistiques"\], body\[data-view="avis"\] \{ --sa-sidebar-w: 230px; \}/);
assert.doesNotMatch(styleSource, /body\[data-view="statistiques"\]::before/);
assert.doesNotMatch(styleSource, /width: 1024px; height: 702px; min-height: 702px/);
assert.match(styleSource, /minmax\(210px, 1\.45fr\) 142px 94px minmax\(150px, 1fr\) 108px 128px 28px/);
assert.match(styleSource, /minmax\(170px, 1\.35fr\) 122px 128px 96px minmax\(130px, 1fr\) 122px 138px 28px/);
assert.match(styleSource, /#view-devis \.list-toolbar \.list-search \{ flex: 0 1 460px/);
assert.match(styleSource, /#view-devis \.list-toolbar \{[^}]*margin-bottom: var\(--sa-space-4\)/);
assert.match(styleSource, /#view-factures \.list-toolbar \{[^}]*margin-bottom: var\(--sa-space-4\)/);
assert.match(styleSource, /#view-factures #facture-filters \{ margin-bottom: var\(--sa-space-4\); \}/);
assert.match(styleSource, /#view-factures #factures-statut-filtre \{ width: 108px; \}/);
assert.doesNotMatch(styleSource, /\.list-row\.is-due \{[^}]*padding-left/);
// Les chantiers sont presentes en CARTES, a la demande explicite de
// l'utilisateur ("je veux pas que les chantiers soit ligne par ligne je
// veux que ca soit des cards"), et ces cartes sont disposees en GRILLE :
// empilees, elles reproduiraient le defilement interminable qu'il
// reprochait a la version precedente.
//
// L'assertion porte sur `auto-fill` et non sur l'expression exacte de la
// piste. Elle epinglait `minmax(330px, 1fr)` - c'est-a-dire la valeur que
// la couche de correction ecrasait deja : le test etait vert en lisant une
// declaration morte, et la fusion des deux feuilles, en la retirant, l'a
// fait echouer. Ce qui doit etre garanti ici est l'INTENTION (des cartes
// qui se rangent en colonnes, pas une pile), pas la syntaxe du jour.
assert.match(styleSource, /\.chantier-grille \{[\s\S]*?grid-template-columns: repeat\(auto-fill,/);
// Le `min(330px, 100%)` n'est pas cosmetique : `minmax(330px, 1fr)` seul
// impose une piste de 330px meme dans un conteneur de 343px moins ses
// marges, et la vue debordait horizontalement sur mobile.
assert.match(styleSource, /\.chantier-grille \{[\s\S]*?minmax\(min\(330px, 100%\), 1fr\)/,
  "la piste doit ceder sous 330px, sinon la grille deborde sur mobile");
assert.match(styleSource, /\.chantier-card \{/);
assert.match(styleSource, /\.chantier-card\.is-open \{ grid-column: 1 \/ -1; \}/, "une carte dépliée doit prendre toute la rangée");
assert.doesNotMatch(styleSource, /\.chantier-entete/, "l'en-tete de colonnes du tableau n'a plus lieu d'etre");
assert.match(styleSource, /\.tache-row \{[\s\S]*?min-height: 63px/);
assert.match(styleSource, /\.doc-row \{[\s\S]*?min-height: 63px/);
// L'approche negative etait interdite tout court a l'epoque ou cette suite
// reproduisait une reference. Cette interdiction absolue n'a jamais ete
// verifiee sur le produit entier : le test ne lisait que style.css, et le
// -0.005em des titres vivait dans la feuille de correction posee par-dessus.
// La fusion des deux feuilles a rendu la lecture complete - et l'assertion
// fausse.
//
// Ce qui reste vrai, et que la direction artistique enonce, c'est que le
// resserrement MARQUE est proscrit : c'est le tic du SaaS generique, et il
// abime un serif a contraste. On garde donc un seuil plutot qu'un interdit.
for (const [, valeur] of styleSource.matchAll(/letter-spacing:\s*(-[\d.]+)em/g)) {
  assert.ok(Number(valeur) >= -0.01,
    `approche trop serree (${valeur}em) : au-dela de -0.01em on retombe dans le SaaS generique`);
}

console.log("OK - reference-ui-reproduction.test.mjs");
