/* Astra §11 — les états d'un écran.
 *
 * Deux exigences qui n'étaient pas tenues :
 *
 * « Lors d'une actualisation, conserver les informations déjà chargées en
 * indiquant leur état. » Chaque chargeur commençait par remplacer sa liste par
 * trois lignes de squelette. Cocher une tâche, enregistrer un paiement,
 * changer un statut : chacun de ces gestes faisait disparaître la liste qu'on
 * regardait, pour la voir revenir presque identique.
 *
 * « Une réponse incertaine après enregistrement demande une vérification, pas
 * un second envoi aveugle. » Une écriture dont la réponse se perd et un refus
 * du serveur donnaient exactement le même message. Le serveur a pourtant pu
 * enregistrer : recommencer crée un doublon — deux factures, deux paiements.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");
const apiSource = fs.readFileSync(path.join(frontendDir, "api.js"), "utf8");

// ---------------------------------------------------------------------
// 1. Actualisation : le contenu reste, l'état est dit
// ---------------------------------------------------------------------
// Plus aucun chargeur ne vide sa liste pour la remplir de squelettes.
assert.doesNotMatch(appSource, /\.innerHTML = skeletonCards\(\);/,
  "un chargeur ne doit plus effacer ce qui est affiché avant de le recharger");
assert.ok((appSource.match(/debutChargement\(/g) || []).length >= 15,
  "les quatorze chargeurs plus la définition doivent passer par debutChargement");

const debut = appSource.indexOf("function debutChargement");
const fin = appSource.indexOf("\n}", appSource.indexOf("const secours = setTimeout")) + 2;
const contexte = { skeletonCards: () => "SQUELETTE", MutationObserver: class {
  constructor(fn) { this.fn = fn; }
  observe() { contexte.__observe = this; }
  disconnect() { contexte.__deconnecte = true; }
}, setTimeout: () => 1, clearTimeout: () => {} };
vm.runInNewContext(`${appSource.slice(debut, fin)}\nglobalThis.__c = { debutChargement };`, contexte, { filename: appPath });
const { debutChargement } = contexte.__c;

const faireConteneur = (nbEnfants) => {
  const attributs = {};
  return {
    innerHTML: "",
    children: { length: nbEnfants },
    dataset: {},
    classes: new Set(),
    classList: { add: (c) => attributs.c1 = c, remove: () => {}, contains: () => false },
    setAttribute: (n, v) => { attributs[n] = v; },
    removeAttribute: (n) => { delete attributs[n]; },
    attributs,
  };
};

// Écran VIDE : rien à conserver, on montre un squelette.
const vide = faireConteneur(0);
debutChargement(vide);
assert.equal(vide.innerHTML, "SQUELETTE");
assert.equal(vide.attributs["aria-busy"], undefined, "un premier chargement n'a rien à signaler comme occupé");

// Écran DÉJÀ REMPLI : on le garde, et on dit qu'il se rafraîchit.
const rempli = faireConteneur(7);
debutChargement(rempli);
assert.equal(rempli.innerHTML, "", "le contenu affiché ne doit pas être remplacé");
assert.equal(rempli.attributs["aria-busy"], "true", "l'état doit être annoncé aux lecteurs d'écran");
assert.equal(rempli.attributs.c1, "est-en-actualisation");
assert.equal(rempli.dataset.actualisation, "1");

// Deux appels rapprochés ne posent qu'un seul voile.
contexte.__deconnecte = false;
debutChargement(rempli);
assert.equal(contexte.__deconnecte, false, "un second appel ne doit pas réinstaller l'observateur");

// Un conteneur absent ne fait rien exploser.
debutChargement(null);

// Le voile se lève de lui-même quand le contenu est remplacé : c'est ce qui
// évite d'avoir à ajouter un appel de fin dans chaque chargeur — et donc
// d'en oublier un le jour où un quinzième apparaît.
const bloc = appSource.slice(debut, fin);
assert.match(bloc, /new MutationObserver\(finir\)/);
assert.match(bloc, /observateur\.observe\(conteneur, \{ childList: true \}\)/);
// Et un filet, pour qu'un chargement qui n'aboutit jamais ne laisse pas la
// liste en retrait pour toujours.
assert.match(bloc, /const secours = setTimeout\(finir, 15000\)/);

// La règle de style existe, et ne déplace aucune commande — seule l'opacité
// change, et la transition est neutralisée en mouvement réduit.
const styleSource = fs.readFileSync(path.join(frontendDir, "style.css"), "utf8");
assert.match(styleSource, /\.est-en-actualisation \{ opacity: 0\.55;/);
assert.match(styleSource, /prefers-reduced-motion: reduce\)\s*\{\s*\n\s*\.est-en-actualisation \{ transition: none; \}/);

// ---------------------------------------------------------------------
// 2. Une réponse perdue n'est pas un refus
// ---------------------------------------------------------------------
assert.match(apiSource, /function erreurReseau\(ecriture\)/);
assert.match(apiSource, /erreur\.issueIncertaine = Boolean\(ecriture\)/);
assert.match(apiSource, /L'enregistrement a peut-etre abouti : verifiez avant de recommencer/,
  "le message doit demander une vérification, pas suggérer un nouvel envoi");
// La lecture garde son message d'origine : la retenter est sans conséquence.
assert.match(apiSource, /Impossible de contacter le serveur\. Verifiez votre connexion\./);
assert.match(apiSource, /throw erreurReseau\(method !== "GET"\)/,
  "seules les écritures ont une issue incertaine");
assert.match(apiSource, /\/\/ Un envoi de fichier est toujours une ecriture\.\s*\n\s*throw erreurReseau\(true\)/);

// Le message reste affiché plus longtemps : il demande d'aller vérifier.
assert.match(appSource, /function showToast\(message, isError = false, duree = 3500\)/);
assert.match(appSource, /err\.issueIncertaine \? 12000 : undefined/);

console.log("OK - etats-chargement.test.mjs");
