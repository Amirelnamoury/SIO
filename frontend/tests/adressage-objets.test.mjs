/* Un bouton qui NOMME une piece doit l'ouvrir, pas ouvrir son rayon.
 *
 * Le defaut corrige ici etait partout le meme : « Voir la facture » sur une
 * relance, « Voir » sur l'accueil, un resultat de recherche « FA-2026-014 »,
 * une affaire du dossier client - tous basculaient sur la LISTE et laissaient
 * l'artisan retrouver la ligne a la main. Deux causes :
 *   1. l'identifiant de la piece n'etait pas transmis au bouton ;
 *   2. la navigation etait temporisee (`setTimeout(..., 200)`) au lieu
 *      d'attendre le chargement reel de la vue - un reseau lent ratait la
 *      fenetre, et rien ne s'ouvrait.
 * Ce test verrouille les deux.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

// ---------------------------------------------------------------------
// 1. switchView rend la promesse du chargeur de vue.
// ---------------------------------------------------------------------
const switchStart = appSource.indexOf("function switchView(view)");
const switchEnd = appSource.indexOf("\n}", appSource.indexOf("const chargeurs = {", switchStart));
assert.ok(switchStart !== -1 && switchEnd > switchStart, "switchView est introuvable");
assert.match(
  appSource.slice(switchStart, switchEnd),
  /return Promise\.resolve\(chargeurs\[view\]/,
  "switchView doit rendre la promesse du chargeur, sinon aucun appelant ne peut ouvrir un objet apres coup",
);

// Plus aucune navigation temporisee : c'etait le pari sur la lenteur du reseau.
const temporisees = appSource.match(/setTimeout\([^)]*(?:switchView|showDevisForm|showDocumentForm|action\.run)[^)]*\)/g) || [];
assert.deepEqual(temporisees, [], `navigation temporisee residuelle : ${temporisees.join(" | ")}`);

// ---------------------------------------------------------------------
// 2. ouvrirObjet ouvre la bonne piece, et refuse un identifiant vide.
// ---------------------------------------------------------------------
const ouvreStart = appSource.indexOf("async function ouvrirObjet");
// ouvrirObjet delegue l'ouverture proprement dite a ouvrirFiche, juste en
// dessous : les deux sont indissociables et s'executent donc ensemble.
const ouvreEnd = appSource.indexOf("\n}", appSource.indexOf("async function ouvrirFiche")) + 2;
const cibleStart = appSource.indexOf("async function ouvrirCible");
const cibleEnd = appSource.indexOf("\n}", cibleStart) + 2;
assert.ok(ouvreStart !== -1 && cibleStart !== -1, "les ouvertures d'objet sont introuvables");

const journal = [];
const contexte = {
  SEARCH_TYPE_META: {
    client: { view: "prospects" }, devis: { view: "devis" },
    facture: { view: "factures" }, chantier: { view: "chantiers" },
  },
  switchView: async (view) => { journal.push(`vue:${view}`); contexte.document.body.dataset.view = view; },
  // Les vrais ouvreurs rendent VRAI quand la fiche s'affiche, FAUX quand la
  // piece n'est plus dans la liste (archivee, supprimee) : `absent` permet
  // d'eprouver ce second cas, celui d'une adresse recue par message.
  absent: false,
  showTimeline: (id) => { journal.push(`client:${id}`); return !contexte.absent; },
  showDevisDetail: (id) => { journal.push(`devis:${id}`); return !contexte.absent; },
  showFactureDetail: (id) => { journal.push(`facture:${id}`); return !contexte.absent; },
  focusChantierCard: () => journal.push("chantier:focus"),
  document: {
    querySelector: () => (contexte.absent
      ? null
      : { click: () => journal.push("chantier:deplie"), getAttribute: () => "false" }),
    body: { dataset: {} },
  },
  // L'adresse est ecrite par les ouvreurs eux-memes, hors de ce decoupage,
  // sauf pour le chantier - qui n'a pas de fonction d'ouverture a lui.
  ecrireAdresse: () => {},
  adresseFiche: (type, id) => `#/${type}/${id}`,
  // Les caches de liste que consulte le registre des fiches. Ici toutes les
  // pieces demandees y sont deja : l'aller-retour serveur a son propre test
  // plus bas.
  // `window.__devisTousCache` : le cache des devis archives, consulte par le
  // registre avant de solliciter le serveur.
  window: {},
  devisListCache: [{ id: 7 }], facturesCache: [{ id: 7 }, { id: 14 }], clientsCache: [{ id: 7 }],
  chantiersCache: [{ id: 7 }],
  renderChantiersListFiltered: () => {},
  showToast: (m) => journal.push(`message:${m.slice(0, 20)}`),
  // Le serveur connait le devis 900, pas le 901 : les deux cas du registre.
  Api: {
    getDevis: async (id) => { journal.push(`serveur:devis:${id}`); if (id !== 900) throw new Error("404"); return { id }; },
    getFacture: async (id) => { if (id !== 900) throw new Error("404"); return { id }; },
    getClient: async (id) => { if (id !== 900) throw new Error("404"); return { id }; },
  },
};
vm.runInNewContext(
  `let chantierFocusId = null;\nlet currentChantierFilter = "", currentChantierAvancement = "", currentChantierClient = "", currentChantierRecherche = "";\n${appSource.slice(ouvreStart, ouvreEnd)}\n${appSource.slice(cibleStart, cibleEnd)}\nglobalThis.__ouvre = { ouvrirObjet, ouvrirCible, assurerFiche };`,
  contexte,
  { filename: appPath },
);
const { ouvrirObjet, ouvrirCible } = contexte.__ouvre;

for (const [type, vue, trace] of [
  ["client", "prospects", "client:7"],
  ["devis", "devis", "devis:7"],
  ["facture", "factures", "facture:7"],
]) {
  journal.length = 0;
  assert.equal(await ouvrirObjet(type, 7), true, `${type} doit s'ouvrir`);
  assert.deepEqual(journal, [`vue:${vue}`, trace], `${type} : la vue doit etre chargee AVANT l'ouverture`);
}

journal.length = 0;
assert.equal(await ouvrirObjet("chantier", 7), true);
assert.deepEqual(journal, ["vue:chantiers", "chantier:focus", "chantier:deplie"]);

// Un type inconnu ou un identifiant absent ne doit rien declencher : mieux
// vaut ne pas bouger que de basculer de vue pour rien.
for (const [type, id] of [["inconnu", 7], ["facture", ""], ["facture", null], ["devis", undefined]]) {
  journal.length = 0;
  assert.equal(await ouvrirObjet(type, id), false, `${type}/${JSON.stringify(id)} ne doit pas s'ouvrir`);
  assert.deepEqual(journal, [], "aucune navigation sans cible exploitable");
}

// ---------------------------------------------------------------------
// 3. ouvrirCible : l'objet quand il est nomme, la liste sinon.
// ---------------------------------------------------------------------
journal.length = 0;
await ouvrirCible({ objetType: "facture", objetId: "14", view: "factures" });
assert.deepEqual(journal, ["vue:factures", "facture:14"], "un bouton qui nomme une facture doit l'ouvrir");

journal.length = 0;
await ouvrirCible({ view: "devis" });
assert.deepEqual(journal, ["vue:devis"], "une alerte qui parle d'un ensemble ouvre la liste, et c'est correct");

journal.length = 0;
await ouvrirCible({ objetType: "facture", objetId: "", view: "factures" });
assert.deepEqual(journal, ["vue:factures"], "un identifiant vide doit retomber sur la liste, jamais rester bloque");

// ---------------------------------------------------------------------
// 4. Les boutons transportent bien l'identifiant.
// ---------------------------------------------------------------------
assert.match(appSource, /data-objet-type="\$\{item\.objet \|\| ""\}" data-objet-id="\$\{item\.objetId \|\| ""\}"/,
  "les lignes « A faire » de l'accueil doivent porter la piece visee");
for (const groupe of [
  /factures_en_retard\.map\(\(f\) => \(\{[\s\S]*?objet: "facture", objetId: f\.id/,
  /devis_a_relancer\.map\(\(dv\) => \(\{[\s\S]*?objet: "devis", objetId: dv\.id/,
  /chantiers_a_venir\.map\(\(c\) => \(\{[\s\S]*?objet: "chantier", objetId: c\.id/,
]) {
  assert.match(appSource, groupe, "chaque groupe de l'accueil doit nommer sa piece");
}

// Le dossier client annonce « la piece en un clic » : les trois affaires
// doivent donc ouvrir un objet, pas trois listes.
for (const [action, objet] of [["chantier", "chantier"], ["devis", "devis"], ["facture", "facture"]]) {
  assert.match(
    appSource,
    new RegExp(`ouvrir-${action}-depuis-client"\\) ouvrirObjet\\("${objet}"|else ouvrirObjet\\("${objet}", id\\)`),
    `l'affaire ${action} du dossier client doit ouvrir la piece`,
  );
}

// Les deux conversions rendent un objet : il doit etre ouvert, pas cherche.
assert.match(appSource, /const facture = await Api\.factureDepuisDevis\([\s\S]*?ouvrirObjet\("facture", facture\.id\)/,
  "convertir un devis en facture doit ouvrir la facture creee");
assert.match(appSource, /await ouvrirObjet\("chantier", res\.chantier\.id\)/,
  "preparer un chantier doit ouvrir le chantier cree");

// ---------------------------------------------------------------------
// 5. Une fiche absente de la liste chargee est demandee au serveur.
// ---------------------------------------------------------------------
// Les panneaux de detail lisaient directement le cache de la liste affichee
// et sortaient en silence quand la piece n'y etait pas : un devis archive,
// une facture filtree par statut, un client sur une autre page. Les quatre
// routes GET /<type>/{id} existaient pourtant deja cote serveur.
const { assurerFiche } = contexte.__ouvre;
journal.length = 0;
assert.equal(await assurerFiche("devis", 7), true, "une piece deja en cache ne redemande rien");
assert.deepEqual(journal, [], "aucun appel serveur quand la piece est la");

journal.length = 0;
assert.equal(await assurerFiche("devis", 900), true, "une piece absente du cache est demandee au serveur");
assert.deepEqual(journal, ["serveur:devis:900"]);
assert.equal(await assurerFiche("devis", 900), true, "et elle est memorisee : un seul aller-retour");
assert.deepEqual(journal, ["serveur:devis:900"], "la seconde ouverture ne rappelle pas le serveur");

journal.length = 0;
assert.equal(await assurerFiche("devis", 901), false, "le serveur ne la connait pas non plus : c'est un vrai echec");
// Un type sans registre (le chantier vit dans sa carte) n'est jamais bloque ici.
assert.equal(await assurerFiche("chantier", 12345), true);

// L'ouverture doit prevenir quand la fiche ne figure pas dans la liste
// affichee : sans un mot, la refermer donne l'impression qu'elle a disparu.
assert.match(appSource, /Cette fiche n'apparaît pas dans la liste affichée/,
  "ouvrir une fiche hors de la liste visible doit etre signale");
assert.match(appSource, /const horsListe = selecteur && !document\.querySelector\(selecteur\)/);
// Le chantier, lui, EST sa ligne de liste : on leve les filtres au lieu de
// pretendre qu'il n'existe pas.
assert.match(appSource, /currentChantierFilter = "";[\s\S]*?renderChantiersListFiltered\(\)/,
  "un chantier masque par un filtre doit faire lever le filtre, pas disparaitre");

// ---------------------------------------------------------------------
// 6. Atteindre un objet au clavier autant qu'a la souris.
// ---------------------------------------------------------------------
// Onze elements portent role="button" tabindex="0" sans etre des <button> :
// ils prennent le focus et s'annoncent comme des boutons. Seul le planning
// gerait Entree/Espace ; ailleurs, la touche ne faisait rien. Un relais
// delegue unique - deux relais produiraient deux clics sur une seule frappe.
assert.match(
  appSource,
  /if \(e\.key !== "Enter" && e\.key !== " "\) return;[\s\S]*?\[role="button"\]\[tabindex="0"\][\s\S]*?cible\.click\(\)/,
  "Entree et Espace doivent activer les elements qui se presentent comme des boutons",
);
const relais = appSource.match(/e\.key === "Enter" \|\| e\.key === " "/g) || [];
assert.equal(relais.length, 0, "aucun relais clavier local ne doit doubler le relais delegue");

console.log("OK - adressage-objets.test.mjs");
