import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const appPath = path.join(frontendDir, "app.js");
const apiPath = path.join(frontendDir, "api.js");
const indexPath = path.join(frontendDir, "index.html");
const appSource = fs.readFileSync(appPath, "utf8");
const apiSource = fs.readFileSync(apiPath, "utf8");
const indexSource = fs.readFileSync(indexPath, "utf8");

const facturesStart = indexSource.indexOf('id="view-factures"');
const chantiersStart = indexSource.indexOf('id="view-chantiers"');
const entrepriseStart = indexSource.indexOf('id="view-entreprise"');
const entrepriseEnd = indexSource.indexOf('id="view-notifications"', entrepriseStart);
assert.ok(facturesStart !== -1 && chantiersStart > facturesStart, "la vue Factures est introuvable");
assert.ok(entrepriseStart !== -1 && entrepriseEnd > entrepriseStart, "la vue Entreprise est introuvable");
assert.doesNotMatch(
  indexSource.slice(facturesStart, chantiersStart),
  /Contrats récurrents/,
  "les contrats ne doivent plus être enfouis dans Factures",
);
assert.match(
  indexSource.slice(entrepriseStart, entrepriseEnd),
  /Contrats récurrents/,
  "la section doit être visible dans Entreprise",
);

for (const apiMethod of ["listContrats", "createContrat", "updateContrat", "deleteContrat", "genererContrat"]) {
  assert.match(apiSource, new RegExp(`${apiMethod}:`), `Api.${apiMethod} doit exister`);
}
assert.match(
  appSource,
  /if \(view === "entreprise"\)[\s\S]*?loadContrats\(\);[\s\S]*?\n  }/,
  "ouvrir Entreprise doit charger les contrats",
);

const start = appSource.indexOf("const CONTRAT_FREQUENCE_LABELS");
const end = appSource.indexOf("async function showContratForm", start);
assert.ok(start !== -1 && end > start, "les fonctions de rendu Contrat sont introuvables");
const context = {
  escapeHtml: (value) => String(value ?? ""),
  fmtEuro: (value) => `${value} €`,
  fmtDate: (value) => String(value),
};
vm.runInNewContext(
  `${appSource.slice(start, end)}\nglobalThis.__contrats = { renderContratCard, feedbackGenerationContrat };`,
  context,
  { filename: appPath },
);

const contratActif = {
  id: 17,
  client_nom: "Client entretien",
  titre: "Entretien chaudière",
  montant_ht: 240,
  taux_tva: 20,
  frequence: "trimestriel",
  statut: "actif",
  prochaine_echeance: "2026-09-30",
  derniere_generation: "2026-06-30",
  nb_factures_generees: 2,
};
const htmlActif = context.__contrats.renderContratCard(contratActif);
for (const texte of [
  "Client entretien",
  "240 € HT",
  "TVA 20%",
  "Trimestrielle",
  "Actif",
  "2026-09-30",
  "2026-06-30",
  "2 factures générées",
  "Modifier",
  "Générer maintenant",
  "Suspendre",
  "Résilier",
  "Supprimer",
]) {
  assert.ok(htmlActif.includes(texte), `la carte doit afficher « ${texte} »`);
}

const htmlSuspendu = context.__contrats.renderContratCard({ ...contratActif, statut: "suspendu" });
assert.ok(htmlSuspendu.includes("Réactiver"));
assert.ok(!htmlSuspendu.includes("Générer maintenant"));

const sansEmail = context.__contrats.feedbackGenerationContrat({
  email_statut: "non_configure",
  message: "Facture générée. L'email n'a pas été envoyé.",
});
assert.equal(sansEmail.message, "Facture générée. L'email n'a pas été envoyé.");
assert.equal(sansEmail.isError, false, "une facture créée ne doit pas être présentée comme un échec global");
const echecEmail = context.__contrats.feedbackGenerationContrat({ email_statut: "echec", message: "Facture générée." });
assert.equal(echecEmail.isError, true);

const formStart = appSource.indexOf("async function showContratForm");
const setupEnd = appSource.indexOf("// ===================== Chantiers", formStart);
const contractUiSource = appSource.slice(formStart, setupEnd);
assert.match(contractUiSource, /Api\.createContrat\(payload\)/, "le formulaire doit créer");
assert.match(contractUiSource, /Api\.updateContrat\(contrat\.id, payload\)/, "le formulaire doit modifier");
assert.match(contractUiSource, /Api\.deleteContrat\(id\)/, "l'action Supprimer doit appeler DELETE");
assert.match(contractUiSource, /confirmDialog\("Supprimer ce contrat/, "la suppression doit être confirmée");
assert.match(contractUiSource, /btn\.disabled = true/, "Générer maintenant doit bloquer les doubles clics");

console.log("OK - contrats.test.mjs");
