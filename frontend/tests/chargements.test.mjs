/* Ne charger que ce qu'on regarde. (Astra §14)
 *
 * Deux excès, tous deux invisibles à l'usage sur un compte de démonstration
 * et coûteux dès que le volume monte :
 *   - ouvrir Entreprise déclenchait sept appels d'un coup — équipe,
 *     prestations, fournisseurs, conformité, automatisations, contrats — alors
 *     qu'un seul panneau est visible ;
 *   - le dossier d'un client téléchargeait TOUS les chantiers, devis et
 *     factures du compte pour en afficher deux ou trois, avec pour les
 *     chantiers leurs notes, dépenses, heures et tâches chargées en même temps.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as sources from "./_sources.mjs";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
// Depuis le decoupage §16, ce code peut vivre dans socle.js ou
// navigation.js. On lit les scripts du produit dans leur ordre de
// chargement : le test verifie un COMPORTEMENT, pas son rangement.
const appSource = sources.tout;
const apiSource = fs.readFileSync(path.join(frontendDir, "api.js"), "utf8");
const backendDir = path.resolve(frontendDir, "..", "backend", "app", "routers");

// ---------------------------------------------------------------------
// 1. Entreprise ne charge que l'onglet consulté
// ---------------------------------------------------------------------
assert.doesNotMatch(appSource, /entreprise: \(\) => Promise\.all\(\[/,
  "les sept chargeurs ne doivent plus partir ensemble");
assert.match(appSource, /entreprise: \(\) => chargerOngletEntreprise\(ongletEntrepriseActif\(\)\)/);

// Les huit onglets du HTML ont chacun leur chargeur : un onglet oublié
// resterait vide sans que rien ne le signale.
const indexSource = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");
const zoneOnglets = indexSource.slice(indexSource.indexOf('id="entreprise-tabs"'), indexSource.indexOf('id="entreprise-form-box"'));
const onglets = [...zoneOnglets.matchAll(/data-tab="([\w-]+)"/g)].map((m) => m[1]);
assert.ok(onglets.length >= 8, `trop peu d'onglets détectés (${onglets.length})`);
const tableChargeurs = appSource.slice(
  appSource.indexOf("const CHARGEURS_ENTREPRISE"),
  appSource.indexOf("let ongletsEntrepriseCharges"),
);
for (const onglet of onglets) {
  assert.ok(tableChargeurs.includes(`${onglet.includes("-") ? `"${onglet}"` : onglet}:`),
    `l'onglet « ${onglet} » n'a pas de chargeur`);
}
// Profil et Identité visuelle partagent un formulaire : une seule charge.
assert.match(tableChargeurs, /profil: \(\) => loadEntrepriseForm\(\)/);
assert.match(tableChargeurs, /"identite-visuelle": \(\) => loadEntrepriseForm\(\)/);
assert.match(appSource, /profil: "entreprise", "identite-visuelle": "entreprise"/,
  "les deux onglets doivent partager la même clé, sinon le formulaire est chargé deux fois");

// Un échec ne condamne pas l'onglet : la marque est retirée pour permettre un
// second passage, au lieu d'un panneau vide définitif.
assert.match(appSource, /\.catch\(\(err\) => \{\s*\n\s*ongletsEntrepriseCharges\.delete\(cle\);\s*\n\s*throw err;/);
// Et une fin de session oublie ce qui a été chargé.
assert.match(appSource, /ongletsEntrepriseCharges = new Set\(\);\s*\n\}/,
  "changer de compte doit oublier les onglets déjà chargés");

// ---------------------------------------------------------------------
// 2. Le dossier client ne demande que les pièces de ce client
// ---------------------------------------------------------------------
for (const [methode, appel] of [
  ["listDevis", /Api\.listDevis\(null, false, clientId\)/],
  ["listFactures", /Api\.listFactures\(null, false, clientId\)/],
  ["listChantiers", /Api\.listChantiers\(false, clientId\)/],
]) {
  assert.match(appSource, appel, `${methode} doit être filtrée sur le client dans le dossier`);
}

// Le client d'API transmet bien le paramètre.
for (const methode of ["listDevis", "listFactures", "listChantiers"]) {
  const bloc = apiSource.slice(apiSource.indexOf(`${methode}:`), apiSource.indexOf(`${methode}:`) + 420);
  assert.match(bloc, /if \(clientId\) params\.set\("client_id", String\(clientId\)\)/,
    `Api.${methode} doit transmettre client_id`);
}

// Et le serveur le comprend. Il l'acceptait deja pour les devis et les
// factures - seul /chantiers en manquait, ajoute dans son propre lot.
for (const [fichier, fonction] of [
  ["devis.py", "def lister_devis"],
  ["factures.py", "def lister_factures"],
  ["chantiers.py", "def lister_chantiers"],
]) {
  const source = fs.readFileSync(path.join(backendDir, fichier), "utf8");
  const debut = source.indexOf(fonction);
  const bloc = source.slice(debut, debut + 1400);
  assert.match(bloc, /client_id: Optional\[int\] = None/, `${fichier} doit accepter client_id`);
  assert.match(bloc, /if client_id:/, `${fichier} doit appliquer le filtre`);
}

console.log("OK - chargements.test.mjs");
