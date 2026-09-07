/* Chaque vue et chaque fiche a une adresse.
 *
 * Avant, l'URL ne bougeait jamais : quel que soit l'ecran, elle disait
 * « index.html ». On ne pouvait ni mettre un devis en favori, ni l'envoyer a
 * quelqu'un, ni le retrouver apres un rechargement, et le bouton Precedent du
 * navigateur sortait du produit au lieu de refermer la fiche ouverte.
 *
 * Deux exigences que ce test verrouille en plus de l'adressage lui-meme :
 *   - refermer une fiche ne doit PAS recharger la liste, sinon le filtre en
 *     cours et la position dans la page seraient perdus a chaque aller-retour ;
 *   - une adresse valide dont l'objet a disparu (archive, supprime, appartenant
 *     a un autre compte) doit le DIRE, et non laisser une liste muette.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const debut = appSource.indexOf("const ROUTE_OBJETS");
const fin = appSource.indexOf("/** Ouvre l'objet designe par un bouton");
assert.ok(debut !== -1 && fin > debut, "le bloc des adresses est introuvable");

function contexteRoutage({ vueInitiale = "dashboard", hash = "", fiches = new Set([1]) } = {}) {
  const journal = [];
  const historique = [];
  const location = { hash };
  const corps = { dataset: { view: vueInitiale } };
  const panneaux = new Map([
    ["panel-timeline", { hidden: true }], ["panel-devis", { hidden: true }],
    ["panel-facture", { hidden: true }], ["dashboard-screen", { hidden: false }],
  ]);
  const contexte = {
    journal, historique, location,
    window: {
      location,
      history: {
        pushState: (_a, _b, h) => { historique.push(`push ${h}`); location.hash = h; },
        replaceState: (_a, _b, h) => { historique.push(`replace ${h}`); location.hash = h; },
      },
      addEventListener: () => {},
    },
    document: {
      body: corps,
      getElementById: (id) => panneaux.get(id) || null,
      querySelector: (sel) => ({ click: () => journal.push(`clic ${sel}`) }),
    },
    switchView: async (vue) => { journal.push(`charge ${vue}`); corps.dataset.view = vue; },
    ouvrirFiche: async (type, id) => {
      journal.push(`fiche ${type}:${id}`);
      return fiches.has(id);
    },
    showToast: (msg) => journal.push(`message ${msg}`),
  };
  vm.runInNewContext(
    `${appSource.slice(debut, fin)}\nglobalThis.__r = { appliquerAdresse, ecrireAdresse, lireAdresse, adresseFiche, fermerFiches, fermerFicheEtRevenir };`,
    contexte,
    { filename: appPath },
  );
  return { ...contexte.__r, journal, historique, location, corps, panneaux };
}

// ---------------------------------------------------------------------
// 1. Lecture de l'adresse.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage();
  for (const [hash, attendu] of [
    ["", { vue: "dashboard", segment: null }],
    ["#/devis", { vue: "devis", segment: null }],
    ["#/devis/89", { vue: "devis", segment: "89" }],
    ["#devis/89", { vue: "devis", segment: "89" }],
    ["#/entreprise/conformite", { vue: "entreprise", segment: "conformite" }],
    // Une vue inconnue ne doit pas laisser l'ecran vide : on ramene a l'accueil.
    ["#/inexistant/12", { vue: "dashboard", segment: null }],
    ["#/../../etc", { vue: "dashboard", segment: null }],
  ]) {
    r.location.hash = hash;
    // On recopie l'objet : celui que rend le contexte VM a le prototype de
    // SON realm, et deepEqual strict compare aussi les prototypes.
    assert.deepEqual({ ...r.lireAdresse() }, attendu, `lecture de « ${hash} »`);
  }
}

// ---------------------------------------------------------------------
// 2. Ecriture : on REMPLACE la premiere entree, on empile ensuite.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage();
  r.ecrireAdresse("#/devis");
  r.ecrireAdresse("#/devis");           // deja a cette adresse : rien
  r.ecrireAdresse("#/devis/89");
  r.ecrireAdresse("#/devis", { remplacer: true });
  assert.deepEqual(r.historique, ["replace #/devis", "push #/devis/89", "replace #/devis"],
    "la premiere adresse remplace l'entree initiale, sinon Precedent ne ferait que retirer le hash");
}

// ---------------------------------------------------------------------
// 3. Une fiche garde la vue d'ou on la regarde.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage({ vueInitiale: "clients" });
  assert.equal(r.adresseFiche("client", 4), "#/clients/4", "un client ouvert depuis Clients reste dans Clients");
  r.corps.dataset.view = "prospects";
  assert.equal(r.adresseFiche("client", 4), "#/prospects/4");
  // Depuis une vue sans rapport, on retombe sur la vue naturelle du type.
  r.corps.dataset.view = "dashboard";
  assert.equal(r.adresseFiche("facture", 14), "#/factures/14");
}

// ---------------------------------------------------------------------
// 4. Appliquer une adresse : charger la vue, ouvrir la fiche.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage({ vueInitiale: "dashboard", hash: "#/devis/1" });
  await r.appliquerAdresse();
  assert.deepEqual(r.journal, ["charge devis", "fiche devis:1"],
    "la vue doit etre chargee AVANT qu'on cherche la fiche dedans");
}

// LE point : revenir a la liste ne la recharge pas. C'est ce qui preserve le
// filtre en cours et la position dans la page.
{
  const r = contexteRoutage({ vueInitiale: "devis", hash: "#/devis" });
  r.panneaux.get("panel-devis").hidden = false;
  await r.appliquerAdresse();
  assert.deepEqual(r.journal, [], "aucun rechargement quand on est deja sur la vue");
  assert.equal(r.panneaux.get("panel-devis").hidden, true, "la fiche doit tout de meme se refermer");
}

// Deux appels sur la meme adresse ne rejouent rien : hashchange et popstate
// peuvent tomber tous les deux sur un seul Precedent.
{
  const r = contexteRoutage({ vueInitiale: "dashboard", hash: "#/factures/1" });
  await r.appliquerAdresse();
  await r.appliquerAdresse();
  assert.deepEqual(r.journal, ["charge factures", "fiche facture:1"], "une adresse ne s'applique qu'une fois");
}

// ---------------------------------------------------------------------
// 5. Adresse valide, objet disparu : on le dit, et on nettoie l'adresse.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage({ vueInitiale: "dashboard", hash: "#/devis/99999" });
  await r.appliquerAdresse();
  const message = r.journal.find((l) => l.startsWith("message "));
  assert.ok(message, "un objet introuvable doit etre annonce, pas passe sous silence");
  assert.match(message, /Ce devis n'est plus dans votre liste/);
  assert.equal(r.location.hash, "#/devis", "l'adresse morte est remplacee par celle de la liste");
  assert.ok(r.historique.includes("replace #/devis"),
    "remplacee et non empilee : Precedent ne doit pas ramener sur l'echec");
}

// Un identifiant qui n'en est pas un ouvre la liste, sans message d'erreur.
for (const hash of ["#/devis/0", "#/devis/-3", "#/devis/abc", "#/devis/1.5"]) {
  const r = contexteRoutage({ vueInitiale: "dashboard", hash });
  await r.appliquerAdresse();
  assert.deepEqual(r.journal, ["charge devis"], `« ${hash} » doit ouvrir la liste sans chercher de fiche`);
}

// ---------------------------------------------------------------------
// 6. Fermer une fiche remet l'adresse sur la liste.
// ---------------------------------------------------------------------
{
  const r = contexteRoutage({ vueInitiale: "devis", hash: "#/devis/89" });
  r.panneaux.get("panel-devis").hidden = false;
  r.fermerFicheEtRevenir();
  assert.equal(r.panneaux.get("panel-devis").hidden, true);
  assert.equal(r.location.hash, "#/devis");
}

// ---------------------------------------------------------------------
// 7. Les points d'entree sont bien branches dans l'application.
// ---------------------------------------------------------------------
assert.match(appSource, /window\.addEventListener\("hashchange", appliquerAdresse\)/);
assert.match(appSource, /window\.addEventListener\("popstate", appliquerAdresse\)/);
// Les quatre ouvreurs ecrivent l'adresse eux-memes : un seul endroit a
// corriger quel que soit le chemin emprunte pour ouvrir la fiche.
for (const attendu of [
  /ecrireAdresse\(adresseFiche\("devis", devisId\)\)/,
  /ecrireAdresse\(adresseFiche\("facture", factureId\)\)/,
  /ecrireAdresse\(adresseFiche\("client", clientId\)\)/,
  /ecrireAdresse\(adresseFiche\("chantier", identifiant\)\)/,
]) {
  assert.match(appSource, attendu, `ouvreur non branche sur l'adresse : ${attendu}`);
}
// Les trois fermetures passent par l'adresse, jamais par un `hidden = true` nu.
assert.equal((appSource.match(/fermerFicheEtRevenir\(\)/g) || []).length >= 4, true,
  "les trois boutons de fermeture et Echap doivent passer par l'adresse");
// Une adresse dans la barre du navigateur l'emporte sur l'accueil par defaut.
assert.match(appSource, /if \(window\.location\.hash\.startsWith\("#\/"\)\)[\s\S]*?appliquerAdresse\(\)/,
  "au demarrage, un lien recu doit ouvrir ce qu'il designe");

console.log("OK - adresses.test.mjs");
