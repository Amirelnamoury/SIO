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
const indexSource = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");

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

// =====================================================================
// LES QUATRE CORRECTIFS
// ---------------------------------------------------------------------
// Quatre defauts silencieux : ils ne levaient aucune erreur, la page
// s'affichait normalement, et l'information etait simplement fausse ou
// absente. C'est exactement le genre de chose qu'un test doit retenir.
// =====================================================================
const correctifsStart = appSource.indexOf("function chantierJoursRetard");
const correctifsEnd = appSource.indexOf("function chantierMatchesFilter", correctifsStart);
assert.ok(correctifsStart !== -1 && correctifsEnd > correctifsStart, "les helpers de lecture d'un chantier sont introuvables");
const correctifs = {};
vm.runInNewContext(
  `${appSource.slice(correctifsStart, correctifsEnd)}
   globalThis.__c = { chantierJoursRetard, chantierProchaineAction, chantierEstASurveiller };`,
  correctifs,
  { filename: appPath },
);
const C = correctifs.__c;
// Le jour est lu sur l'horloge LOCALE, pas via toISOString(). L'ancienne
// version passait par UTC : entre minuit local et minuit UTC, elle rendait
// la veille, et le test echouait d'un jour - une nuit sur douze en France,
// jamais aux heures ou on le lance d'habitude. `chantierJoursRetard` compare
// deux minuits locaux ; le jeu d'essai doit parler la meme langue.
const dans = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const chantier = (extra = {}) => ({
  id: 1, titre: "Rénovation cuisine", client_nom: "Martin", adresse: "Villeurbanne",
  statut: "en_cours", progression: 50, budget: 10000, total_depenses: 5000,
  date_debut: dans(-30), date_fin_prevue: dans(10), date_reception: null, taches: [], ...extra,
});

// 1. `date_fin_prevue` est renvoyee par ChantierOut mais n'etait exposee
//    nulle part : aucun chantier ne pouvait etre signale en retard.
assert.equal(C.chantierJoursRetard(chantier({ date_fin_prevue: dans(-3) })), 3);
assert.equal(C.chantierJoursRetard(chantier()), 0, "une fin prévue dans le futur n'est pas un retard");
assert.equal(
  C.chantierJoursRetard(chantier({ statut: "termine", date_fin_prevue: dans(-30) })), 0,
  "un chantier terminé ne peut plus être en retard",
);
assert.equal(C.chantierJoursRetard(chantier({ date_fin_prevue: null })), 0);
// Le champ doit etre saisissable des deux cotes, sinon il reste toujours vide.
assert.match(appSource, /id="cf-fin"/, "la création doit permettre de saisir la fin prévue");
assert.match(appSource, /date_fin_prevue: emptyToNull\(document\.getElementById\("cf-fin"\)\.value\)/);
assert.match(appSource, /id="chantier-fin-\$\{c\.id\}"/, "la modification doit permettre de saisir la fin prévue");
assert.match(appSource, /date_fin_prevue: emptyToNull\(document\.getElementById\(`chantier-fin-\$\{id\}`\)\.value\)/);

// 2. La fiche lisait `c.prochaine_action`, un champ qui existe sur un
//    CLIENT mais pas sur un chantier : la ligne affichait "Aucune action
//    planifiée" pour tous les chantiers, en permanence.
const sectionChantiers = appSource.slice(
  appSource.indexOf("// ===================== Chantiers"),
  appSource.indexOf("// ===================== Taches"),
);
assert.deepEqual(
  sectionChantiers.split("\n").filter((l) => l.includes("c.prochaine_action") && !l.trimStart().startsWith("//")),
  [],
  "prochaine_action n'existe pas dans ChantierOut : rien ne doit le lire ici",
);
assert.match(C.chantierProchaineAction(chantier({ statut: "termine" })).texte, /Clôturer/);
assert.match(C.chantierProchaineAction(chantier({ statut: "facture" })).texte, /réception/i);
const avecTaches = C.chantierProchaineAction(chantier({
  taches: [
    { id: 1, titre: "Peinture", statut: "a_faire", echeance: dans(9) },
    { id: 2, titre: "Poser le carrelage", statut: "a_faire", echeance: dans(2) },
    { id: 3, titre: "Démolition", statut: "faite", echeance: dans(-9) },
  ],
}));
assert.equal(avecTaches.texte, "Poser le carrelage", "la tâche datée la plus proche gagne, les tâches faites sont ignorées");
const tacheEnRetard = C.chantierProchaineAction(chantier({
  taches: [{ id: 1, titre: "Carrelage", statut: "a_faire", echeance: dans(-4) }],
}));
assert.equal(tacheEnRetard.enRetard, true);
assert.match(tacheEnRetard.quand, /retard 4 j/);
assert.match(C.chantierProchaineAction(chantier({ statut: "a_preparer" })).texte, /Démarrage/);
assert.equal(C.chantierProchaineAction(chantier({ date_fin_prevue: null })).vide, true);

// 3. Les deux listes de tri concurrentes sont fusionnees : la seconde
//    ecrasait silencieusement la premiere, qui restait affichee.
assert.doesNotMatch(appSource, /currentChantierPriorite/, "le second tri concurrent doit avoir disparu");
assert.doesNotMatch(indexSource, /chantiers-priorite-tri/);
for (const valeur of ["risque", "progression", "date_debut_desc", "date_debut_asc", "budget_desc", "titre_asc"]) {
  assert.match(indexSource, new RegExp(`value="${valeur}"`), `option de tri perdue : ${valeur}`);
}

// 4. La recherche portait sur le textContent de la carte entiere, donc
//    aussi sur les libelles de l'interface.
const rechercheStart = appSource.indexOf("function chantierMatchesRecherche");
const rechercheEnd = appSource.indexOf("function renderChantiersListFiltered", rechercheStart);
const recherche = {};
vm.runInNewContext(
  `${appSource.slice(rechercheStart, rechercheEnd)}\nglobalThis.__r = chantierMatchesRecherche;`,
  recherche,
  { filename: appPath },
);
const cible = chantier({ titre: "Villa Ducros", client_nom: "Ducros", adresse: "Villeurbanne" });
assert.equal(recherche.__r(cible, "villeurbanne"), true);
assert.equal(recherche.__r(cible, "ducros"), true);
assert.equal(recherche.__r(cible, "note"), false, "la recherche ne doit pas voir les libellés de l'interface");
assert.equal(recherche.__r(cible, ""), true);
assert.doesNotMatch(appSource, /setupListeSearch\("chantiers-search"/, "la recherche générique ne doit plus être branchée");

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
