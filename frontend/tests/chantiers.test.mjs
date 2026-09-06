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

// =====================================================================
// 1. LE MOTEUR DE LECTURE
// ---------------------------------------------------------------------
// Toute la page Chantiers repose sur des fonctions pures qui DEDUISENT
// l'etat d'un chantier de ses champs (budget, depenses, progression,
// dates, taches). Le backend ne pouvant pas tourner ici, ce sont ces
// fonctions qui tiennent lieu de garde-fou : une regression sur un seuil
// se verrait immediatement en production, sur toutes les fiches a la fois.
// =====================================================================
const moteurStart = appSource.indexOf("const CH_TERMINES");
const moteurEnd = appSource.indexOf("// 8. LE TIROIR", moteurStart);
assert.ok(moteurStart !== -1 && moteurEnd > moteurStart, "le moteur de lecture des chantiers est introuvable");

const moteur = {
  escapeHtml: (v) => String(v),
  fmtEuro: (n) => (n === null || n === undefined ? null : `${Math.round(n)} EUR`),
  CHANTIER_STATUT_META: { en_cours: { label: "En cours" }, termine: { label: "Terminé" } },
  chantiersCache: [],
};
vm.runInNewContext(
  `${appSource.slice(moteurStart, moteurEnd)}
   globalThis.__ch = { chLecture, chSignaux, chNiveau, chScore, chProchaineAction, chSituationHtml, chAttentionHtml, chantierEstASurveiller, chCorrespondRecherche };`,
  moteur,
  { filename: appPath },
);
const CH = moteur.__ch;

const dans = (jours) => {
  const d = new Date();
  d.setDate(d.getDate() + jours);
  return d.toISOString().slice(0, 10);
};
const chantier = (extra = {}) => ({
  id: 1, titre: "Rénovation cuisine", client_nom: "Martin", client_id: 4,
  statut: "en_cours", progression: 50, budget: 10000, total_depenses: 5000,
  date_debut: dans(-30), date_fin_prevue: dans(10),
  marge_estimee: 2000, marge_reelle: null, date_reception: null, reserves: null,
  taches: [], notes: [], depenses: [], heures: [],
  ...extra,
});

// ---- La derive : le calcul central de la page ----
{
  const sain = CH.chLecture(chantier());
  assert.equal(sain.budgetPct, 50);
  assert.equal(sain.derive, 0, "50 % de budget pour 50 % d'avancement = aucune dérive");

  const derape = CH.chLecture(chantier({ progression: 40, total_depenses: 7500 }));
  assert.equal(derape.budgetPct, 75);
  assert.equal(derape.derive, 35, "75 % de budget pour 40 % d'avancement = 35 points de dérive");

  // Un chantier a peine demarre engage forcement des materiaux : compter
  // cela comme une derive declencherait une alerte sur chaque nouveau
  // chantier, et l'utilisateur apprendrait a ignorer le signal.
  const demarrage = CH.chLecture(chantier({ progression: 5, total_depenses: 3000 }));
  assert.equal(demarrage.derive, null, "sous 10 % d'avancement, la dérive n'a pas de sens");

  const sansBudget = CH.chLecture(chantier({ budget: null }));
  assert.equal(sansBudget.budgetPct, null);
  assert.equal(sansBudget.derive, null);
}

// ---- Les signaux ----
{
  const codes = (c) => CH.chSignaux(c).map((s) => s.code);

  assert.ok(codes(chantier({ date_fin_prevue: dans(-3) })).includes("retard"));
  assert.equal(CH.chLecture(chantier({ date_fin_prevue: dans(-3) })).joursRetard, 3);
  assert.ok(!codes(chantier()).includes("retard"), "une fin prévue dans le futur n'est pas un retard");
  assert.ok(
    !codes(chantier({ statut: "termine", date_fin_prevue: dans(-30) })).includes("retard"),
    "un chantier terminé ne peut plus être en retard",
  );

  assert.ok(codes(chantier({ total_depenses: 12000 })).includes("budget_depasse"));
  assert.ok(codes(chantier({ total_depenses: 9000, progression: 90 })).includes("budget_tendu"));
  assert.ok(codes(chantier({ statut: "termine" })).includes("a_facturer"));
  assert.ok(codes(chantier({ statut: "facture" })).includes("reception"));
  assert.ok(!codes(chantier({ statut: "facture", date_reception: dans(-2) })).includes("reception"));
  assert.ok(codes(chantier({ budget: null })).includes("sans_budget"));
  assert.ok(
    codes(chantier({ taches: [{ id: 1, titre: "Carrelage", statut: "a_faire", echeance: dans(-2) }] })).includes("taches"),
  );

  // La gravite ordonne la lecture : le plus grave en premier, toujours.
  const grave = CH.chSignaux(chantier({ date_fin_prevue: dans(-5), budget: null }));
  assert.equal(grave[0].niveau, "critique");
  assert.equal(CH.chNiveau(chantier({ date_fin_prevue: dans(-5) })), "critique");
  assert.equal(CH.chNiveau(chantier()), "calme");
  assert.equal(CH.chNiveau(chantier({ statut: "paye", date_reception: dans(-1) })), "fini");

  // Un chantier en retard doit remonter avant un chantier sain.
  assert.ok(CH.chScore(chantier({ date_fin_prevue: dans(-10) })) > CH.chScore(chantier()));
}

// ---- La prochaine action ----
// L'ancienne fiche lisait `c.prochaine_action`, un champ que ChantierOut ne
// renvoie pas : la ligne affichait donc "Aucune action planifiée" pour tous
// les chantiers, en permanence. Elle est desormais deduite.
{
  // `prochaine_action` existe bien sur un CLIENT (voir renderKanbanCard et le
  // champ cli-prochaine-action), mais PAS sur un chantier. La verification est
  // donc bornee a la section Chantiers : ailleurs, le champ est legitime.
  const sectionChantiers = appSource.slice(
    appSource.indexOf("// ===================== Chantiers"),
    appSource.indexOf("// ===================== Taches"),
  );
  const litLeChamp = sectionChantiers
    .split("\n")
    .filter((l) => l.includes("c.prochaine_action") && !l.trimStart().startsWith("//"));
  assert.deepEqual(litLeChamp, [], "prochaine_action n'existe pas dans ChantierOut : rien ne doit le lire ici");

  assert.match(CH.chProchaineAction(chantier({ statut: "termine" })).texte, /Clôturer/);
  assert.equal(CH.chProchaineAction(chantier({ statut: "termine" })).action, "toggle-cloturer-form");
  assert.match(CH.chProchaineAction(chantier({ statut: "facture" })).texte, /réception/i);

  const avecTaches = CH.chProchaineAction(chantier({
    taches: [
      { id: 1, titre: "Peinture", statut: "a_faire", echeance: dans(9) },
      { id: 2, titre: "Poser le carrelage", statut: "a_faire", echeance: dans(2) },
      { id: 3, titre: "Démolition", statut: "faite", echeance: dans(-9) },
    ],
  }));
  assert.equal(avecTaches.texte, "Poser le carrelage", "la tâche datée la plus proche gagne, les tâches faites sont ignorées");

  const enRetard = CH.chProchaineAction(chantier({
    taches: [{ id: 1, titre: "Carrelage", statut: "a_faire", echeance: dans(-4) }],
  }));
  assert.equal(enRetard.enRetard, true);
  assert.match(enRetard.quand, /retard 4 j/);

  assert.match(CH.chProchaineAction(chantier({ statut: "a_preparer" })).texte, /Démarrage/);
  assert.equal(CH.chProchaineAction(chantier({ date_fin_prevue: null })).vide, true);
}

// ---- La recherche porte sur ce qui est affiche, pas sur le balisage ----
{
  const c = chantier({ titre: "Villa Ducros", client_nom: "Ducros", adresse: "Villeurbanne" });
  assert.equal(CH.chCorrespondRecherche(c, "villeurbanne"), true);
  assert.equal(CH.chCorrespondRecherche(c, "ducros"), true);
  assert.equal(CH.chCorrespondRecherche(c, "budget"), false, "la recherche ne doit pas voir les libellés de l'interface");
  assert.equal(CH.chCorrespondRecherche(c, ""), true);
}

// ---- Les tuiles de situation sont aussi les filtres ----
{
  const html = CH.chSituationHtml([
    chantier({ id: 1 }),
    chantier({ id: 2, date_fin_prevue: dans(-6) }),
    chantier({ id: 3, statut: "a_preparer" }),
  ]);
  assert.match(html, /data-signal="retard"/);
  assert.match(html, /data-signal="budget"/);
  assert.match(html, /aria-pressed/, "une tuile-filtre doit annoncer son état");
}

// ---- Le fil d'attention ne porte que ce qui appelle un geste ----
{
  assert.equal(CH.chAttentionHtml([chantier()]), "", "sans rien à traiter, le bloc disparaît entièrement");
  const html = CH.chAttentionHtml([chantier({ statut: "termine" })]);
  assert.match(html, /data-action="ouvrir-chantier"/);
  assert.match(html, /data-suite="toggle-cloturer-form"/, "l'alerte doit ouvrir directement le geste qui la résout");
}

// =====================================================================
// 2. NAVIGATION DEPUIS LE PLANNING
// =====================================================================
const focusStart = appSource.indexOf("function focusChantierCard");
const focusEnd = appSource.indexOf("async function loadChantiers", focusStart);
assert.ok(focusStart !== -1 && focusEnd > focusStart, "les helpers de navigation vers un chantier sont introuvables");

let switchedTo = null;
let selectedWith = null;
let scrolled = false;
let tiroirOuvertPour = null;
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
  chantiersCache: [{ id: 73 }],
  chOuvrirTiroir: (id) => { tiroirOuvertPour = id; },
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
assert.equal(tiroirOuvertPour, 73, "arriver depuis le planning doit ouvrir le dossier, pas juste le surligner");

// =====================================================================
// 3. LE PLANNING RENVOIE TOUJOURS VERS LES CHANTIERS
// =====================================================================
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

// =====================================================================
// 4. AUCUNE FONCTIONNALITE PERDUE DANS LA REFONTE
// ---------------------------------------------------------------------
// La page a ete entierement redessinee ; ces assertions verifient que
// chaque action de l'ancienne carte depliable existe toujours, sous le
// meme nom, quelque part dans la nouvelle interface.
// =====================================================================
for (const action of [
  "edit-chantier", "edit-depense", "edit-heure", "delete-heure",
  "toggle-note-form", "submit-note", "toggle-depense-form", "submit-depense",
  "toggle-heures-form", "submit-heures", "toggle-reception-form", "submit-reception",
  "toggle-cloturer-form", "confirmer-cloturer", "terminer-chantier",
  "chantier-document", "planifier-intervention", "rapport-chantier", "delete-chantier",
  "toggle-tache-chantier", "submit-chantier-edit",
]) {
  assert.match(appSource, new RegExp(`data-action="${action}"`), `action perdue dans la refonte : ${action}`);
  assert.match(appSource, new RegExp(`"${action}"`), `action non traitée dans la refonte : ${action}`);
}
assert.match(appSource, /finances_verrouillees/);
assert.match(appSource, /if \(hasPlan\("business"\)\) await ensureEquipeCache\(\)/);
assert.doesNotMatch(appSource, /else if \(data\.type === "chantier_debut"\)/);
assert.match(apiSource, /updateChantierDepense/);
assert.match(apiSource, /updateChantierHeures/);

// Le meme gestionnaire branche sur la liste ET sur le tiroir : c'est ce qui
// garantit qu'une action se comporte pareil des deux cotes.
assert.match(appSource, /vue\.addEventListener\("click", chGererAction\)/);
assert.match(appSource, /tiroir\.addEventListener\("click", chGererAction\)/);

// =====================================================================
// 5. PREREMPLISSAGE DES FORMULAIRES
// =====================================================================
const chantierFormStart = appSource.indexOf("async function showChantierEditForm");
const chantierFormEnd = appSource.indexOf("function showDepenseForm", chantierFormStart);
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
  adresse: "Adresse préremplie", date_debut: "2026-08-31", date_fin_prevue: "2026-09-30",
  budget: 1500, finances_verrouillees: false,
});
assert.match(chantierContainer.innerHTML, /value="Titre prérempli"/);
assert.match(chantierContainer.innerHTML, /value="Adresse préremplie"/);
assert.match(chantierContainer.innerHTML, /value="2026-08-31"/);
assert.match(chantierContainer.innerHTML, /value="1500"/);
assert.match(chantierContainer.innerHTML, /data-action="submit-chantier-edit"/);
// La fin prevue existait dans l'API mais n'etait exposee nulle part : sans
// elle, aucun chantier ne peut jamais etre signale comme en retard.
assert.match(chantierContainer.innerHTML, /id="chantier-fin-73"/);
assert.match(chantierContainer.innerHTML, /value="2026-09-30"/);

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
const heuresFormEnd = appSource.indexOf("// ===================== Taches", heuresFormStart);
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
