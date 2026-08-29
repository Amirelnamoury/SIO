import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const appPath = path.join(frontendDir, "app.js");
const apiPath = path.join(frontendDir, "api.js");
const appSource = fs.readFileSync(appPath, "utf8");
const apiSource = fs.readFileSync(apiPath, "utf8");

const focusStart = appSource.indexOf("function focusChantierCard");
const focusEnd = appSource.indexOf("function rentabiliteHtml", focusStart);
assert.ok(focusStart !== -1 && focusEnd > focusStart, "les helpers de navigation vers un chantier sont introuvables");

let switchedTo = null;
let selectedWith = null;
let scrolled = false;
const focusContext = {
  document: {
    querySelector(selector) {
      selectedWith = selector;
      return {
        classList: { add: () => {}, remove: () => {} },
        scrollIntoView: () => { scrolled = true; },
      };
    },
  },
  switchView: (view) => { switchedTo = view; },
  setTimeout: (callback) => callback(),
};
vm.runInNewContext(
  `let chantierFocusId = null;\n${appSource.slice(focusStart, focusEnd)}\nglobalThis.__chantiers = { ouvrirChantierDepuisPlanning, focusChantierCard };`,
  focusContext,
  { filename: appPath },
);
focusContext.__chantiers.ouvrirChantierDepuisPlanning(73);
assert.equal(switchedTo, "chantiers");
focusContext.__chantiers.focusChantierCard();
assert.equal(selectedWith, '[data-chantier-id="73"]', "le chantier doit être retrouvé par son ID");
assert.equal(scrolled, true);

const chipStart = appSource.indexOf("function planningItemChip");
const chipEnd = appSource.indexOf("function planningDayCellHtml", chipStart);
assert.ok(chipStart !== -1 && chipEnd > chipStart, "planningItemChip est introuvable");
const chipContext = {
  PLANNING_TYPES_EVENEMENT: new Set(["rdv", "visite", "intervention", "autre"]),
  PLANNING_TYPE_CLASS: { chantier_debut: "planning-item-green", rdv: "planning-item-blue" },
  planningHeureLocale: () => "10:00",
  escapeHtml: (value) => String(value),
};
vm.runInNewContext(
  `${appSource.slice(chipStart, chipEnd)}\nglobalThis.__planningItemChip = planningItemChip;`,
  chipContext,
  { filename: appPath },
);
const chantierChip = chipContext.__planningItemChip({
  type: "chantier_debut", reference_id: 73, date: "2026-08-31T08:00:00Z", titre: "Début chantier : Test",
}, false);
assert.match(chantierChip, /draggable="false"/);
assert.match(chantierChip, /role="button"/);
assert.match(chantierChip, /data-ref-id="73"/);

const rendezVousChip = chipContext.__planningItemChip({
  type: "rdv", reference_id: 91, date: "2026-08-31T10:00:00Z", titre: "Rendez-vous",
}, false);
assert.match(rendezVousChip, /draggable="true"/);
assert.match(rendezVousChip, /role="button"/);

assert.match(appSource, /data-action="edit-chantier"/);
assert.match(appSource, /data-action="edit-depense"/);
assert.match(appSource, /data-action="edit-heure"/);
assert.match(appSource, /finances_verrouillees/);
assert.match(appSource, /if \(hasPlan\("business"\)\) await ensureEquipeCache\(\)/);
assert.doesNotMatch(appSource, /else if \(data\.type === "chantier_debut"\)/);
assert.match(apiSource, /updateChantierDepense/);
assert.match(apiSource, /updateChantierHeures/);

const chantierFormStart = appSource.indexOf("async function showChantierEditForm");
const chantierFormEnd = appSource.indexOf("function renderChantierCard", chantierFormStart);
const chantierContainer = { innerHTML: "" };
const chantierFormContext = {
  document: { getElementById: () => chantierContainer },
  ensureClientsCache: async () => [],
  clientOptionsHtml: (id) => `<option value="${id}" selected>Client</option>`,
  escapeHtml: (value) => String(value),
};
vm.runInNewContext(
  `${appSource.slice(chantierFormStart, chantierFormEnd)}\nglobalThis.__showChantierEditForm = showChantierEditForm;`,
  chantierFormContext,
  { filename: appPath },
);
await chantierFormContext.__showChantierEditForm({
  id: 73, titre: "Titre prérempli", client_id: 4, devis_id: null,
  adresse: "Adresse préremplie", date_debut: "2026-08-31", budget: 1500,
  finances_verrouillees: false,
});
assert.match(chantierContainer.innerHTML, /value="Titre prérempli"/);
assert.match(chantierContainer.innerHTML, /value="Adresse préremplie"/);
assert.match(chantierContainer.innerHTML, /value="2026-08-31"/);
assert.match(chantierContainer.innerHTML, /value="1500"/);
assert.match(chantierContainer.innerHTML, /data-action="submit-chantier-edit"/);

const depenseFormStart = appSource.indexOf("function showDepenseForm");
const depenseFormEnd = appSource.indexOf("function showNoteForm", depenseFormStart);
const depenseContainer = { innerHTML: "" };
const depenseFormContext = {
  document: { getElementById: () => depenseContainer },
  fournisseursCache: [{ id: 8, nom: "Fournisseur test" }],
  escapeHtml: (value) => String(value),
};
vm.runInNewContext(
  `${appSource.slice(depenseFormStart, depenseFormEnd)}\nglobalThis.__showDepenseForm = showDepenseForm;`,
  depenseFormContext,
  { filename: appPath },
);
depenseFormContext.__showDepenseForm(73, {
  id: 21, libelle: "Dépense préremplie", montant: 350,
  date_depense: "2026-08-31", fournisseur_id: 8,
});
assert.match(depenseContainer.innerHTML, /value="Dépense préremplie"/);
assert.match(depenseContainer.innerHTML, /value="350"/);
assert.match(depenseContainer.innerHTML, /data-depense-id="21"/);
assert.match(depenseContainer.innerHTML, /value="8" selected/);

const heuresFormStart = appSource.indexOf("function showHeuresForm");
const heuresFormEnd = appSource.indexOf("function progressionHtml", heuresFormStart);
const heuresContainer = { innerHTML: "" };
const heuresFormContext = {
  document: { getElementById: () => heuresContainer },
  equipeCache: [],
  escapeHtml: (value) => String(value),
};
vm.runInNewContext(
  `${appSource.slice(heuresFormStart, heuresFormEnd)}\nglobalThis.__showHeuresForm = showHeuresForm;`,
  heuresFormContext,
  { filename: appPath },
);
heuresFormContext.__showHeuresForm(73, {
  id: 31, membre_id: null, nom_intervenant: "Artisan prérempli",
  duree_heures: 2, date_travail: "2026-08-31", taux_horaire: 35, note: "Pose",
});
assert.match(heuresContainer.innerHTML, /value="Artisan prérempli"/);
assert.match(heuresContainer.innerHTML, /value="2"/);
assert.match(heuresContainer.innerHTML, /value="35"/);
assert.match(heuresContainer.innerHTML, /data-heure-id="31"/);

console.log("OK - chantiers.test.mjs");
