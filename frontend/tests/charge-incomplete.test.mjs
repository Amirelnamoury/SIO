/* Une vue qui n'a pas pu tout charger doit le DIRE.
 *
 * Douze chargements etaient enveloppes dans un `catch` qui renvoyait un
 * tableau vide : une panne reseau, un plan insuffisant ou une erreur serveur
 * s'affichaient exactement comme « vous n'avez rien ». Sur un dossier client,
 * cela revient a annoncer « aucune facture » a quelqu'un qui en a.
 *
 * La phrase elle-meme est un piege a elle seule : elle a deja ete fausse deux
 * fois. « Les chantiers n'A pas pu etre chargE » d'abord - le verbe suivait le
 * NOMBRE DE SOURCES en panne au lieu du sujet, qui reste pluriel. Puis « les
 * factures n'ont pas pu etre chargeS », le participe ne s'accordant jamais en
 * genre. Ce test fige les deux accords.
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

const debut = appSource.indexOf("function journalDeCharge");
const fin = appSource.indexOf("\n}", appSource.indexOf("function bandeauCharge")) + 2;
assert.ok(debut !== -1 && fin > debut, "le journal de charge est introuvable");
// La table des etiquettes feminines vit entre les deux : la tranche la prend.
assert.ok(appSource.slice(debut, fin).includes("ETIQUETTES_FEMININES"),
  "la table des genres doit rester dans le meme bloc que le bandeau qui l'utilise");

const contexte = { escapeHtml: (v) => String(v ?? "") };
vm.runInNewContext(
  `${appSource.slice(debut, fin)}\nglobalThis.__c = { journalDeCharge, tolerant, bandeauCharge };`,
  contexte,
  { filename: appPath },
);
const { journalDeCharge, tolerant, bandeauCharge } = contexte.__c;

// Rien en panne : pas de bandeau. Une vue saine ne s'excuse pas.
assert.equal(bandeauCharge(journalDeCharge()), "");

// Une source en panne : le sujet reste pluriel.
{
  const journal = journalDeCharge();
  const repli = await tolerant(journal, "les chantiers", Promise.reject(new Error("500")));
  // Le tableau vient du contexte VM : on compare son contenu, pas son prototype.
  assert.equal(Array.isArray(repli) || repli.length === 0, true);
  assert.equal(repli.length, 0, "l'appelant recoit un repli utilisable, il ne casse pas");
  assert.deepEqual([...journal.manquants], ["les chantiers"]);
  const html = bandeauCharge(journal);
  assert.match(html, /Les chantiers n'ont pas pu être chargés\./);
  assert.doesNotMatch(html, /n'a pas pu/, "le verbe suit le sujet, pas le nombre de sources");
  assert.match(html, /data-action="recharger-vue"/, "il doit rester un moyen de reessayer");
  assert.match(html, /role="status"/, "l'information doit atteindre un lecteur d'ecran");
}

// Une source feminine : le participe s'accorde.
{
  const journal = journalDeCharge();
  await tolerant(journal, "les factures", Promise.reject(new Error("500")));
  assert.match(bandeauCharge(journal), /Les factures n'ont pas pu être chargées\./);
}

// Genres melanges : le masculin l'emporte. C'est la regle, pas un repli.
{
  const journal = journalDeCharge();
  await tolerant(journal, "les factures", Promise.reject(new Error("500")));
  await tolerant(journal, "les devis", Promise.reject(new Error("500")));
  const html = bandeauCharge(journal);
  assert.match(html, /Les factures et les devis n'ont pas pu être chargés\./);
}

// Trois sources : virgules puis « et », et la majuscule initiale.
{
  const journal = journalDeCharge();
  for (const source of ["les messages", "les chantiers", "les devis"]) {
    await tolerant(journal, source, Promise.reject(new Error("500")));
  }
  assert.match(bandeauCharge(journal), /Les messages, les chantiers et les devis n'ont pas pu être chargés\./);
}

// Un chargement qui reussit ne laisse aucune trace, et sa valeur passe intacte.
{
  const journal = journalDeCharge();
  const valeur = await tolerant(journal, "les devis", Promise.resolve([{ id: 1 }]));
  assert.deepEqual([...valeur], [{ id: 1 }], "la valeur passe intacte");
  assert.equal(journal.manquants.length, 0);
  assert.equal(bandeauCharge(journal), "");
}

// Le repli peut etre autre chose qu'un tableau : certains appels rendent un objet.
{
  const journal = journalDeCharge();
  const valeur = await tolerant(journal, "les devis", Promise.reject(new Error("500")), { total: 0 });
  assert.deepEqual({ ...valeur }, { total: 0 });
}

// Les vues qui peuvent afficher une donnee partielle doivent poser le bandeau.
for (const vue of ["showTimeline", "loadClientsDirectory", "loadDashboard", "loadDocuments"]) {
  const debutVue = appSource.indexOf(`function ${vue}`);
  assert.ok(debutVue !== -1, `${vue} est introuvable`);
  // Jusqu'a la prochaine fonction de premier niveau : ces chargeurs vont de
  // quelques lignes a plusieurs centaines, une fenetre fixe en manquerait.
  const suite = appSource.slice(debutVue + 10);
  const finVue = debutVue + 10 + Math.min(
    ...["\nfunction ", "\nasync function ", "\n// ====="].map((m) => {
      const i = suite.indexOf(m);
      return i === -1 ? suite.length : i;
    }),
  );
  assert.match(appSource.slice(debutVue, finVue), /bandeauCharge\(journal\)/,
    `${vue} doit annoncer un chargement incomplet`);
}

console.log("OK - charge-incomplete.test.mjs");
