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
assert.match(appSource, /stats-performance-panel/);
assert.match(appSource, /stats-lower-grid/);
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
assert.match(styleSource, /\.chantier-row \{[\s\S]*?min-height: 82px/);
assert.match(styleSource, /\.tache-row \{[\s\S]*?min-height: 63px/);
assert.match(styleSource, /\.doc-row \{[\s\S]*?min-height: 63px/);
assert.doesNotMatch(styleSource, /letter-spacing:\s*-/);

console.log("OK - reference-ui-reproduction.test.mjs");
