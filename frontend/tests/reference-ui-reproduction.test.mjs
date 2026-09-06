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
// La barre de modules de Devis reproduisait une capture de reference :
// « Devis & devis », « Commerciaux », « Contact » etaient trois libelles
// inertes, et ses deux boutons refaisaient la navigation de gauche. La
// direction artistique actuelle proscrit les deux.
assert.doesNotMatch(indexSource, /devis-modulebar/, "la barre de modules inerte ne doit pas revenir");
assert.doesNotMatch(styleSource, /devis-modulebar/);
assert.doesNotMatch(appSource, /devis-modulebar/);
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

// LA COQUILLE NE BOUGE PAS.
// Ces trois assertions epinglaient l'inverse : un retrait de contenu propre
// a Planning, un autre propre a Documents, et une largeur de colonne propre
// a Statistiques et Avis. Elles reproduisaient fidelement une reference
// faite de captures d'ecran independantes - mais dans un produit on navigue,
// et la colonne changeait de largeur a chaque clic pendant que la recherche
// globale disparaissait sur neuf vues sur treize.
//
// Ce qui est garde ici est la regle qui a remplace ces mesures : une seule
// largeur de colonne, une seule hauteur de barre, aucune vue qui masque la
// barre du haut.
assert.doesNotMatch(styleSource, /body\[data-view="[a-z]+"\][^{]*\{[^}]*--sa-sidebar-w/,
  "aucune vue ne redefinit la largeur de la colonne de navigation");
assert.doesNotMatch(styleSource, /body\[data-view="[a-z]+"\][^{]*\{[^}]*--sa-header-h/,
  "aucune vue ne redefinit la hauteur de la barre du haut");
assert.doesNotMatch(styleSource, /body:not\(\[data-view[\s\S]{0,200}?\.topbar\s*\{\s*display: none/,
  "la barre du haut - recherche globale et bouton Creer - reste sur toutes les vues");
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

// ---------------------------------------------------------------------
// LE PLANNING PLACE SES RENDEZ-VOUS A LEUR HEURE
// ---------------------------------------------------------------------
// `.planning-item-positioned` recoit un `top` en pixels calcule par app.js
// depuis l'heure du rendez-vous. Sans `position: absolute`, ce `top` ne fait
// que decaler un element reste dans le flux : tous les rendez-vous du jour
// s'empilaient SOUS la grille horaire, et la vue Semaine ne montrait plus
// rien a l'heure juste. Le defaut a survecu longtemps parce qu'un planning
// vide n'a rien a mal placer.
assert.match(styleSource, /\.planning-item-positioned \{[^}]*position: absolute/,
  "un rendez-vous positionne doit l'etre vraiment, sinon il retombe sous la grille");

// ---------------------------------------------------------------------
// NOTIFICATIONS ET AVIS PARLENT LA LANGUE DU RESTE DU PRODUIT
// ---------------------------------------------------------------------
// Ces deux vues etaient les dernieres a etre restees des tableaux CRUD
// generiques. Elles passent maintenant par la gouttiere `.sa-section`,
// comme l'accueil, la fiche client et les statistiques.
assert.match(appSource, /renderNotificationsFiltered[\s\S]{0,3600}?saSection\(/,
  "les groupes de notifications doivent passer par la gouttiere de marge");
assert.match(appSource, /avisResumeHtml[\s\S]{0,3000}?saSection\(/,
  "le resume des avis doit passer par la gouttiere de marge");

// Le meme glyphe de document ouvrait les cinq types de notification : une
// icone qui ne distingue rien est une decoration, et la direction artistique
// les proscrit.
assert.doesNotMatch(appSource, /notif-icon/, "l'icone generique des notifications ne doit pas revenir");
assert.doesNotMatch(styleSource, /\.notif-icon/);

// La moyenne des avis s'annonce en toutes lettres, pas dans une carte-chiffre
// de 260 px avec 800 px de vide a sa droite.
assert.doesNotMatch(styleSource, /\.avis-score-card/, "la carte-chiffre de la moyenne ne doit pas revenir");
assert.match(styleSource, /\.avis-repartition-piste/, "la repartition des notes doit rester : une moyenne seule ment");

// Aucune barre d'outils calee en absolu a une distance fixe du haut : ces
// nombres n'etaient vrais que pour la hauteur d'en-tete du jour ou ils ont
// ete releves.
assert.doesNotMatch(styleSource, /\.notifications-tools \{[^}]*position: absolute/);
assert.doesNotMatch(styleSource, /#view-avis > \.list-search \{[^}]*position: absolute/);

// ---------------------------------------------------------------------
// ENTREPRISE : PAS DE MONOGRAMME LA OU IL N'Y A PAS DE PERSONNE
// ---------------------------------------------------------------------
// Equipe, prestations, fournisseurs, contrats et conformite partagent le
// composant `.enterprise-record`. Il ouvrait chaque entree sur deux lettres
// dans un carre : « RD » devant « Remplacement d'un chauffe-eau », « AD »
// devant « Assurance decennale ». Des initiales de phrase, qui se lisent
// comme des initiales de personne.
assert.doesNotMatch(appSource, /enterprise-record-avatar/, "le monogramme des listes Entreprise ne doit pas revenir");
assert.doesNotMatch(styleSource, /\.enterprise-record-avatar/);

// La vue Entreprise n'est plus enfermee dans de grands cadres arrondis :
// `.form-box` encadre un formulaire qui SURGIT dans une liste, pas un ecran
// de reglages, qui EST la page.
for (const boite of ["#entreprise-form-box", "#visual-identity-box, #automatisation-form-box"]) {
  assert.match(styleSource, new RegExp(`${boite.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} \\{[^}]*border: 0`),
    `${boite} ne doit plus porter de cadre`);
}

// Un texte destine a un artisan, pas a un developpeur : ni pluriel entre
// parentheses, ni verbe qui ne s'accorde pas avec son sujet.
//
// L'assertion porte sur le CODE seul, commentaires retires : sans cela elle
// se declenchait sur le commentaire qui, dans app.js, cite justement la
// tournure qu'il explique avoir corrigee.
const appSansCommentaires = appSource
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").map((l) => l.replace(/(^|\s)\/\/.*$/, "$1")).join("\n");
// La negative exclut les signatures dont le parametre s'appelle `s` -
// `sousScoreHtml(s) {`, `(s) =>` : du JavaScript, pas du francais.
assert.doesNotMatch(appSansCommentaires, /\w+\(s\)(?!\s*[{=])/,
  "pas de pluriel entre parentheses dans un texte visible");

console.log("OK - reference-ui-reproduction.test.mjs");
