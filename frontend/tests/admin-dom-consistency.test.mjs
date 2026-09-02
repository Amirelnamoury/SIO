import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Garde-fou anti-regression (refonte Admin) : verifie que chaque id lu par
// admin.js (getElementById / querySelector('#id') / [id="..."] statiques)
// existe reellement dans le HTML qu'il cible, et inversement que chaque id
// declare dans le HTML est reconnu par au moins une reference JS (sauf ids
// remplis dynamiquement par innerHTML, exclus explicitement ci-dessous).
//
// Objectif : detecter mecaniquement la classe de bug "Cannot set properties
// of null (setting 'hidden')" - un id present dans admin.js mais absent du
// HTML apres une reorganisation de la page - sans dependre d'un navigateur.

const testDir = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(testDir, "..", "admin");
const indexHtml = fs.readFileSync(path.join(adminDir, "index.html"), "utf8");
const loginHtml = fs.readFileSync(path.join(adminDir, "login.html"), "utf8");
const script = fs.readFileSync(path.join(adminDir, "admin.js"), "utf8");

function idsDeclaredIn(html) {
  const ids = new Set();
  const re = /\bid="([^"]+)"/g;
  let match;
  while ((match = re.exec(html)) !== null) ids.add(match[1]);
  return ids;
}

function idsReferencedInScript(source) {
  const ids = new Set();
  const getById = /getElementById\("([^"]+)"\)/g;
  let match;
  while ((match = getById.exec(source)) !== null) ids.add(match[1]);
  // querySelector/querySelectorAll('#literal-id') - selecteurs composes
  // (ex: '#advanced-panel select[data-override]') sont ignores ici : seul
  // le premier segment '#id' pur (sans espace ni combinateur) est fiable a
  // extraire automatiquement.
  const bySelector = /querySelector(?:All)?\("#([a-zA-Z0-9_-]+)"\)/g;
  while ((match = bySelector.exec(source)) !== null) ids.add(match[1]);
  return ids;
}

const indexIds = idsDeclaredIn(indexHtml);
const loginIds = idsDeclaredIn(loginHtml);
const scriptIds = idsReferencedInScript(script);
// admin.js construit lui-meme certains blocs via innerHTML (panneau avance
// du configurateur de design, editeur d'ordre des sections) : les id qu'il
// y declare comptent comme "presents" au meme titre que le HTML statique,
// tant qu'ils sont bien construits AVANT d'etre lus (verifie manuellement :
// buildAdvancedPanel() s'execute avant tout getElementById les ciblant).
const idsInjectedByScript = idsDeclaredIn(script);

// L'admin.js sert deux pages distinctes (login.html tres court, index.html
// l'app complete) : un id n'a besoin d'exister que dans AU MOINS une des
// deux, puisque le bloc de code correspondant est gardé par le `return`
// anticipe quand #admin-login-form est present (page de login uniquement).
const allDeclaredIds = new Set([...indexIds, ...loginIds, ...idsInjectedByScript]);

const idsManquants = [...scriptIds].filter((id) => !allDeclaredIds.has(id));
assert.deepEqual(
  idsManquants,
  [],
  `admin.js reference des id absents de tout le HTML Admin (regression du type "Cannot set properties of null") : ${idsManquants.join(", ")}`
);

// Chaque bouton/formulaire d'action declare dans index.html avec un id doit
// etre reference au moins une fois par admin.js (sinon il est mort : aucun
// gestionnaire ne peut jamais s'y attacher). On exclut les ids qui ne sont
// que des CIBLES de rendu (remplies via innerHTML, jamais lues par id) -
// lister ceux-la explicitement pour que la liste reste honnete et courte.
const idsRempliesUniquementParInnerHtmlOuCss = new Set([
  "page-title", "metric-grid", "attention-groups", "recent-sites",
  "artisan-count", "artisan-table", "site-count", "site-table",
  "detail-title", "detail-meta", "detail-stats",
  "progress-rows", "progress-hint",
  "site-slug", "site-published-at",
  "step-contenu-badge", "step-medias-badge", "step-publication-badge",
  "media-summary-logo", "media-summary-photos",
  "pub-statut", "pub-domaine", "pub-url", "pub-date",
  "toast", "login-error", "drawer-scrim", "admin-name",
  "view-dashboard", "view-artisans", "view-sites", "view-detail",
  "tab-panel-overview", "tab-panel-entreprise", "tab-panel-site",
  "artisan-filters", "site-filters",
]);
const actionableIdsInHtml = [...indexIds].filter((id) => /button|form|select$/i.test(id) === false && !idsRempliesUniquementParInnerHtmlOuCss.has(id))
  .filter((id) => /-button$|-form$|-toggle$|-delete$|^logout-button$|^detail-back$/.test(id));
const idsSansAucuneReference = actionableIdsInHtml.filter((id) => !script.includes(id));
assert.deepEqual(
  idsSansAucuneReference,
  [],
  `Ces controles ont un id dans index.html mais ne sont jamais references par admin.js (bouton mort) : ${idsSansAucuneReference.join(", ")}`
);

console.log("OK - admin-dom-consistency.test.mjs");
