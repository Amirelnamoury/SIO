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
  apiSource,
  /genererContrat:\s*\(id\)\s*=>\s*apiFetch\(`\/contrats\/\$\{id\}\/generer`,\s*\{ method: "POST" \}\)/,
  "Api.genererContrat doit retourner directement le JSON de l'endpoint",
);
assert.match(indexSource, /app\.js\?v=[\w-]+/, "app.js doit être versionné pour invalider l'ancien handler en cache");
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

const feedbacks = {
  envoye: context.__contrats.feedbackGenerationContrat({ email_statut: "envoye", message: "Message backend ignoré pour le test." }),
  non_configure: context.__contrats.feedbackGenerationContrat({
    email_statut: "non_configure",
    message: "Facture générée et envoyée.",
  }),
  sans_destinataire: context.__contrats.feedbackGenerationContrat({ email_statut: "sans_destinataire" }),
  echec: context.__contrats.feedbackGenerationContrat({ email_statut: "echec" }),
};
assert.equal(feedbacks.envoye.message, "Facture générée et envoyée par email.");
assert.equal(
  feedbacks.non_configure.message,
  "Facture générée. L'email n'a pas été envoyé car le service email n'est pas configuré.",
);
assert.doesNotMatch(feedbacks.non_configure.message, /^Facture générée et envoyée\.?$/);
assert.equal(
  feedbacks.sans_destinataire.message,
  "Facture générée. L'email n'a pas été envoyé car ce client n'a pas d'adresse email.",
);
assert.equal(
  feedbacks.echec.message,
  "Facture générée. L'email n'a pas pu être envoyé par le fournisseur.",
);
assert.equal(feedbacks.non_configure.isError, false, "une facture créée sans fournisseur email ne doit pas être présentée comme un échec global");
assert.equal(feedbacks.sans_destinataire.isError, false, "l'absence d'adresse email ne doit pas masquer la facture créée");
assert.equal(feedbacks.echec.isError, true, "l'échec fournisseur doit rester visuellement signalé sans nier la facture créée");

const formStart = appSource.indexOf("async function showContratForm");
const setupEnd = appSource.indexOf("// ===================== Chantiers", formStart);
const contractUiSource = appSource.slice(formStart, setupEnd);
assert.match(contractUiSource, /Api\.createContrat\(payload\)/, "le formulaire doit créer");
assert.match(contractUiSource, /Api\.updateContrat\(contrat\.id, payload\)/, "le formulaire doit modifier");
assert.match(contractUiSource, /Api\.deleteContrat\(id\)/, "l'action Supprimer doit appeler DELETE");
assert.match(contractUiSource, /confirmDialog\("Supprimer ce contrat/, "la suppression doit être confirmée");
assert.match(contractUiSource, /btn\.disabled = true/, "Générer maintenant doit bloquer les doubles clics");
assert.match(contractUiSource, /const result = await Api\.genererContrat\(id\)/, "le handler doit conserver la réponse JSON de génération");
assert.match(contractUiSource, /feedbackGenerationContrat\(result\)/, "le toast doit être construit depuis le statut email réel");
assert.doesNotMatch(contractUiSource, /showToast\("Facture générée et envoyée\."\)/, "aucun toast générique d'envoi ne doit subsister");

console.log("OK - contrats.test.mjs");
