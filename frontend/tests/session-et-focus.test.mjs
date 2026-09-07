/* Trois défauts que rien ne signale à l'écran.
 *
 * 1. La déconnexion n'effaçait que le jeton. Dix-sept caches de données
 *    survivaient en mémoire : sur un poste partagé, la personne suivante se
 *    connectait sur un onglet contenant encore les clients, devis et factures
 *    de la précédente. Une session expirée posait le même problème.
 * 2. Les réponses de recherche n'arrivent pas dans l'ordre où elles partent :
 *    la réponse d'une frappe abandonnée pouvait écraser la bonne.
 * 3. Onze éléments portent role="dialog" aria-modal="true" — ils annoncent que
 *    le reste de la page est hors d'atteinte, sans que rien ne le rende vrai.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import * as sources from "./_sources.mjs";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
// Depuis le decoupage §16, une partie de ce code vit dans socle.js.
// On lit les scripts du produit dans leur ordre de chargement : le test
// verifie un COMPORTEMENT, pas dans quel fichier il est range.
const appSource = sources.tout;

// ---------------------------------------------------------------------
// 1. Rien ne survit à une fin de session
// ---------------------------------------------------------------------
const videDebut = appSource.indexOf("function viderCaches()");
const videFin = appSource.indexOf("\n}", videDebut) + 2;
assert.ok(videDebut !== -1, "viderCaches est introuvable");
const viderSource = appSource.slice(videDebut, videFin);

// Ce test reste vrai quand un cache est AJOUTÉ au produit : il lit la liste
// des déclarations dans le fichier plutôt que d'en figer une copie.
const declares = [...appSource.matchAll(/^let (\w*[Cc]ache\w*) =/gm)].map((m) => m[1]);
assert.ok(declares.length >= 15, `trop peu de caches détectés (${declares.length}) : le motif de détection a dû changer`);
for (const nom of declares) {
  assert.ok(viderSource.includes(`${nom} =`), `le cache ${nom} n'est pas effacé à la déconnexion`);
}
// L'identité aussi, et le cache posé sur window par la vue Archives.
for (const attendu of ["currentArtisan = null", "currentUtilisateur = null", "delete window.__devisTousCache"]) {
  assert.ok(viderSource.includes(attendu), `viderCaches doit contenir « ${attendu} »`);
}

// Les trois fins de session appellent le ménage : déconnexion volontaire,
// session expirée, et jeton refusé au démarrage.
assert.match(appSource, /clearToken\(\);\s*\n\s*viderCaches\(\);\s*\n\s*showAuthScreen\(\);/,
  "la déconnexion doit vider les caches");
assert.match(appSource, /onUnauthorized = \(\) => \{[\s\S]*?viderCaches\(\);/,
  "une session expirée doit vider les caches");
assert.equal((appSource.match(/viderCaches\(\)/g) || []).length, 4,
  "trois appels plus la déclaration : toute nouvelle fin de session doit être branchée ici");

// ---------------------------------------------------------------------
// 2. Une réponse tardive ne peut plus écraser une réponse fraîche
// ---------------------------------------------------------------------
const rechercheDebut = appSource.indexOf("async function runSearch");
const rechercheFin = appSource.indexOf("function setupGlobalSearch");
const recherche = appSource.slice(rechercheDebut, rechercheFin);
assert.match(recherche, /const numero = \+\+rechercheEnCours;/, "chaque appel doit porter un numéro");
assert.match(recherche, /if \(numero !== rechercheEnCours\) return;/,
  "on n'écrit que si le dernier appel parti est celui qui revient");
// Le cas d'erreur aussi : une erreur tardive ne doit pas effacer un résultat valide.
assert.equal((recherche.match(/if \(numero !== rechercheEnCours\) return;/g) || []).length, 2,
  "la branche d'erreur doit être gardée elle aussi");
// Vider le champ périme ce qui est en vol.
assert.match(recherche, /rechercheEnCours \+= 1;[\s\S]*?quickActionsHtml\(QUICK_ACTIONS\)/,
  "effacer la recherche doit périmer les appels encore en vol");

// ---------------------------------------------------------------------
// 3. Le clavier reste dans la fenêtre modale, et en ressort là où il était
// ---------------------------------------------------------------------
// Le clavier des fenetres modales fait partie du SOCLE depuis le decoupage
// §16 : on le decoupe dans son fichier, pas dans la concatenation - sinon la
// tranche court jusqu'a un marqueur reste dans app.js et avale tout ce qui
// separe les deux.
const modalesDebut = sources.socle.indexOf("const SELECTEUR_FOCUSABLE");
const modalesFin = sources.socle.indexOf("/** Un ecran vide qui INVITE");
assert.ok(modalesDebut !== -1 && modalesFin > modalesDebut,
  "le bloc des fenetres modales doit vivre dans socle.js");
assert.ok(modalesDebut !== -1 && modalesFin > modalesDebut, "le bloc des fenêtres modales est introuvable");

// Le déclencheur est retenu au GESTE, pas à l'événement `focusin` : celui-ci
// ne se déclenche pas quand le document n'a pas le focus système. Défaut
// constaté en pilotant le navigateur, pas déduit du code.
const modales = sources.socle.slice(modalesDebut, modalesFin);
for (const evenement of ["pointerdown", "keydown", "focusin"]) {
  assert.ok(modales.includes(`document.addEventListener("${evenement}", noterGeste, true)`),
    `le geste ${evenement} doit être écouté en capture`);
}
assert.match(modales, /cible\.closest\('\[role="dialog"\]'\)/,
  "un geste fait DANS une fenêtre ne peut pas être son propre déclencheur");

const ecouteurs = {};
const faireElement = (nom, dansDialogue = false) => ({
  nom, hidden: false, offsetParent: {}, isConnected: true,
  // `noterGeste` remonte jusqu'au conteneur cliquable, puis vérifie qu'il
  // n'est pas dans une fenêtre : nos nœuds répondent aux deux.
  closest(sel) { return sel.includes("dialog") ? (dansDialogue ? dialogue : null) : this; },
  focus() { contexte.document.activeElement = this; },
});
const dialogue = {
  nom: "dialogue", hidden: true, enfants: [],
  contains(el) { return this.enfants.includes(el); },
  querySelectorAll() { return this.enfants; },
};
const contexte = {
  document: {
    activeElement: null,
    addEventListener: (type, fn) => { ecouteurs[type] = fn; },
    querySelectorAll: () => [dialogue],
  },
  MutationObserver: class { observe() {} },
  // `noterGeste` teste `e.target instanceof Element` : le contexte VM n'a pas
  // le DOM, on fournit un Element dont nos faux nœuds sont des instances.
  Element: class {},
};
vm.runInNewContext(
  `${modales}\nglobalThis.__m = { modaleOuverte, modaleFermee, surveillerModales, pileModales };`,
  contexte, { filename: appPath },
);
const M = contexte.__m;

const declencheur = faireElement("ligne de liste");
const premier = faireElement("premier", true);
const dernier = faireElement("dernier", true);
dialogue.enfants = [premier, dernier];

M.surveillerModales();
assert.ok(ecouteurs.keydown, "le piège clavier doit être posé");

// Le geste qui ouvre : un clic sur la ligne, hors de la fenêtre. La cible
// doit être une instance de l'Element du contexte pour passer le garde-fou.
const cibleCliquee = Object.assign(new contexte.Element(), {
  closest: (sel) => (sel.includes("dialog") ? null : declencheur),
});
ecouteurs.pointerdown({ target: cibleCliquee });

contexte.document.activeElement = declencheur;

// La fenêtre s'ouvre ET prend le focus elle-même, comme le font les panneaux.
dialogue.hidden = false;
contexte.document.activeElement = premier;
M.modaleOuverte(dialogue);
assert.equal(M.pileModales.length, 1);

// Tab depuis le dernier revient au premier ; Maj+Tab depuis le premier va au dernier.
const frappe = (shiftKey) => {
  let empeche = false;
  ecouteurs.keydown({ key: "Tab", shiftKey, preventDefault: () => { empeche = true; } });
  return empeche;
};
contexte.document.activeElement = dernier;
assert.equal(frappe(false), true, "la tabulation ne doit pas sortir de la fenêtre");
assert.equal(contexte.document.activeElement, premier, "elle revient au premier élément");

contexte.document.activeElement = premier;
assert.equal(frappe(true), true);
assert.equal(contexte.document.activeElement, dernier, "Maj+Tab va au dernier");

// Le focus a fui dans la page derrière : la tabulation le ramène.
contexte.document.activeElement = declencheur;
assert.equal(frappe(false), true);
assert.equal(contexte.document.activeElement, premier, "un focus échappé est rattrapé");

// À la fermeture, le focus revient au déclencheur.
contexte.document.activeElement = premier;
dialogue.hidden = true;
M.modaleFermee(dialogue);
assert.equal(M.pileModales.length, 0);
assert.equal(contexte.document.activeElement, declencheur,
  "refermer une fiche doit rendre le focus là où il était, pas au néant");

// Une touche autre que Tab ne doit rien intercepter.
contexte.document.activeElement = declencheur;
let interceptee = false;
ecouteurs.keydown({ key: "a", preventDefault: () => { interceptee = true; } });
assert.equal(interceptee, false);

console.log("OK - session-et-focus.test.mjs");
