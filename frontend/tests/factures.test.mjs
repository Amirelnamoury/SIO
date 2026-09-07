import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const appPath = path.resolve(testDir, "..", "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const helpersStart = appSource.indexOf("function buildPublicFrontendUrl");
const helpersEnd = appSource.indexOf("function renderFactureCard", helpersStart);
assert.ok(helpersStart !== -1 && helpersEnd > helpersStart, "les helpers Factures sont introuvables");

const containers = { "paiement-form-42": { innerHTML: "" } };
const context = {
  URL,
  document: {
    baseURI: "http://localhost:8080/frontend/index.html",
    getElementById: (id) => containers[id],
  },
  fmtEuro: (value) => `${Number(value).toFixed(2)} EUR`,
};

vm.runInNewContext(
  `${appSource.slice(helpersStart, helpersEnd)}\nglobalThis.__factureHelpers = { buildPublicFrontendUrl, erreurMontantPaiement };`,
  context,
  { filename: appPath },
);

const { buildPublicFrontendUrl, erreurMontantPaiement } = context.__factureHelpers;
assert.equal(
  buildPublicFrontendUrl("facture-public.html", "token local"),
  "http://localhost:8080/frontend/facture-public.html?t=token+local",
  "le lien local doit conserver le repertoire depuis lequel le frontend est servi",
);

context.document.baseURI = "https://app.example.com/suite/index.html";
assert.equal(
  buildPublicFrontendUrl("facture-public.html", "abc/123"),
  "https://app.example.com/suite/facture-public.html?t=abc%2F123",
  "le lien de production doit conserver le chemin de deploiement et encoder le token",
);

assert.equal(erreurMontantPaiement(80, 80), null, "le paiement exact du solde doit etre accepte");
assert.equal(erreurMontantPaiement(79.99, 80), null, "un paiement partiel doit etre accepte");
assert.match(erreurMontantPaiement(80.01, 80), /dépasse le solde restant/);
assert.match(erreurMontantPaiement(0, 80), /supérieur à zéro/);
assert.match(erreurMontantPaiement(-1, 80), /supérieur à zéro/);
assert.match(erreurMontantPaiement(1, 0), /déjà totalement payée/);

const formStart = appSource.indexOf("function showPaiementForm");
const formEnd = appSource.indexOf("function showFactureForm", formStart);
assert.ok(formStart !== -1 && formEnd > formStart, "showPaiementForm est introuvable");
vm.runInNewContext(
  `${appSource.slice(formStart, formEnd)}\nglobalThis.__showPaiementForm = showPaiementForm;`,
  context,
  { filename: appPath },
);
context.__showPaiementForm(42, 80);
const formulairePaiement = containers["paiement-form-42"].innerHTML;
assert.match(formulairePaiement, /max="80\.00"/);
// Le solde reste annonce - il l'etait dans l'intitule du champ, entasse avec
// le nom et l'asterisque de champ requis (« Montant (euros) * · Solde
// 80,00 € »), il est maintenant sous le champ, dans sa propre phrase.
assert.match(formulairePaiement, /Solde restant : 80\.00 EUR/);
// Et surtout : le champ est PRE-REMPLI au solde. Un artisan qui enregistre
// un paiement encaisse la totalite de ce qui reste du dans la plupart des
// cas ; lui faire ressaisir un montant affiche juste a cote, c'est du
// travail rendu a la main et une occasion de faute de frappe comptable.
assert.match(formulairePaiement, /value="80\.00"/,
  "le montant doit etre pre-rempli au solde restant, tout en restant modifiable");

console.log("OK - factures.test.mjs");
