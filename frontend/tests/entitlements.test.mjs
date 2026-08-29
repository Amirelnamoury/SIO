import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const start = appSource.indexOf("function hasPlan");
const end = appSource.indexOf("function renderUpgradeCard", start);
assert.ok(start !== -1 && end > start, "hasPlan est introuvable dans app.js");

const elements = {
  "contrats-list": { innerHTML: "" },
  "contrat-form-container": { hidden: false, innerHTML: "formulaire ouvert" },
};
const contractButton = { hidden: false };
const context = {
  currentArtisan: null,
  PRICING_ORDRE: ["gratuit", "essentiel", "pro", "business"],
  document: {
    getElementById: (id) => elements[id],
    querySelector: (selector) => selector === '[data-action="show-contrat-form"]' ? contractButton : null,
  },
  renderUpgradeCard: () => "LOCKED PRO",
  skeletonCards: () => "LOADING",
  Api: { listContrats: async () => [] },
};
vm.runInNewContext(
  `${appSource.slice(start, end)}\nglobalThis.__entitlements = { hasPlan };`,
  context,
  { filename: appPath },
);

const { hasPlan } = context.__entitlements;
const plans = ["gratuit", "essentiel", "pro", "business"];
const minimums = {
  factures: "essentiel",
  paiements: "essentiel",
  chantiers: "essentiel",
  conformite: "essentiel",
  statistiques: "essentiel",
  relance_factures: "essentiel",
  relance_devis: "pro",
  automatisations: "pro",
  contrats: "pro",
  equipe: "business",
};

for (const plan of plans) {
  // Le statut est volontairement inactive : les droits proviennent du plan
  // authentifie, pas d'un second gate de facturation.
  context.currentArtisan = { plan, subscription_status: "inactive" };
  for (const [feature, minimum] of Object.entries(minimums)) {
    const expected = plans.indexOf(plan) >= plans.indexOf(minimum);
    assert.equal(hasPlan(minimum), expected, `${plan} / ${feature} doit valoir ${expected}`);
  }
}

context.currentArtisan = null;
assert.equal(hasPlan("essentiel"), false, "un profil non charge doit rester Gratuit");
context.currentArtisan = { plan: "inconnu", subscription_status: "active" };
assert.equal(hasPlan("essentiel"), false, "un plan inconnu doit rester Gratuit");
assert.equal(hasPlan("inconnu"), false, "un minimum inconnu doit etre refuse");

const contractsStart = appSource.indexOf("async function loadContrats");
const contractsEnd = appSource.indexOf("function renderContratCard", contractsStart);
assert.ok(contractsStart !== -1 && contractsEnd > contractsStart, "loadContrats est introuvable dans app.js");
vm.runInNewContext(
  `${appSource.slice(contractsStart, contractsEnd)}\nglobalThis.__contractGate = { loadContrats };`,
  context,
  { filename: appPath },
);

context.currentArtisan = { plan: "essentiel", subscription_status: "inactive" };
await context.__contractGate.loadContrats();
assert.equal(contractButton.hidden, true, "Essentiel ne doit pas voir le bouton Nouveau contrat");
assert.equal(elements["contrat-form-container"].hidden, true, "un formulaire Contrat ouvert doit etre ferme hors plan Pro");
assert.equal(elements["contrat-form-container"].innerHTML, "", "le formulaire Contrat interdit doit etre nettoye");
assert.equal(elements["contrats-list"].innerHTML, "LOCKED PRO", "Essentiel doit voir le paywall Pro des contrats");

context.currentArtisan = { plan: "pro", subscription_status: "inactive" };
await context.__contractGate.loadContrats();
assert.equal(contractButton.hidden, false, "Pro doit voir le bouton Nouveau contrat");

console.log("OK - entitlements.test.mjs");
