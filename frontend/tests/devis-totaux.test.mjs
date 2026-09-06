import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

// =====================================================================
// LE TOTALISATEUR DU DEVIS
// ---------------------------------------------------------------------
// L'ecran de creation n'affichait aucun total : on construisait un devis
// en aveugle. Le bloc de totaux ajoute doit reproduire le calcul du
// serveur AU CENTIME PRES, arrondi intermediaire compris — un total
// affiche qui differerait de celui enregistre serait pire que pas de
// total du tout. Ce test est le garde-fou de cette promesse.
//
// Reference (backend/app/models.py, proprietes du modele Devis) :
//   montant_ht_brut = round(somme(quantite x prix_unitaire_ht), 2)
//   remise_montant  = round(brut x remise% / 100, 2)
//   montant_ht      = round(brut - remise, 2)
//   montant_ttc     = round(montant_ht x (1 + tva/100), 2)
// et l'acompte, cote serveur (routers/chantiers.py), se calcule sur le
// HT : round(montant_ht x acompte% / 100, 2).
// =====================================================================
const testDir = path.dirname(fileURLToPath(import.meta.url));
const appPath = path.resolve(testDir, "..", "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const debut = appSource.indexOf("const arrondi2 =");
const fin = appSource.indexOf("function devisTotalisateurHtml(", debut);
assert.ok(debut !== -1 && fin > debut, "devisTotaux est introuvable");

const ctx = {};
vm.runInNewContext(
  `${appSource.slice(debut, fin)}\nglobalThis.__t = devisTotaux;`,
  ctx,
  { filename: appPath },
);
const devisTotaux = ctx.__t;

/** La formule du serveur, reecrite ici independamment : si les deux
 *  implementations derivent un jour, le test le dira. */
const arrondi = (n) => Math.round((n + Number.EPSILON) * 100) / 100;
function serveur(lignes, tva, remisePct, acomptePct) {
  if (!lignes.length) return null;
  const brut = arrondi(lignes.reduce((s, l) => s + l.quantite * l.prix_unitaire_ht, 0));
  const remise = remisePct ? arrondi((brut * remisePct) / 100) : 0;
  const ht = arrondi(brut - remise);
  return {
    brut, remise, ht,
    ttc: arrondi(ht * (1 + tva / 100)),
    acompte: acomptePct ? arrondi((ht * acomptePct) / 100) : 0,
  };
}

const cas = [
  { nom: "cas simple", lignes: [{ quantite: 1, prix_unitaire_ht: 1000 }], tva: 20, remise: 0, acompte: 30 },
  { nom: "TVA rénovation 10 %", lignes: [{ quantite: 12, prix_unitaire_ht: 45.5 }], tva: 10, remise: 0, acompte: 30 },
  { nom: "avec remise", lignes: [{ quantite: 3, prix_unitaire_ht: 1250 }], tva: 20, remise: 5, acompte: 40 },
  {
    nom: "plusieurs lignes et centimes",
    lignes: [
      { quantite: 2.5, prix_unitaire_ht: 33.33 },
      { quantite: 7, prix_unitaire_ht: 12.99 },
      { quantite: 1, prix_unitaire_ht: 899.95 },
    ],
    tva: 10, remise: 7, acompte: 35,
  },
  // Le cas qui exige l'arrondi intermediaire : sans arrondir la remise
  // AVANT de la soustraire, le HT derive d'un centime, et le TTC avec.
  { nom: "arrondi intermédiaire", lignes: [{ quantite: 3, prix_unitaire_ht: 333.33 }], tva: 20, remise: 3, acompte: 33 },
  { nom: "sans remise ni acompte", lignes: [{ quantite: 1, prix_unitaire_ht: 7500 }], tva: 20, remise: 0, acompte: 0 },
];

for (const c of cas) {
  const obtenu = devisTotaux(c.lignes, c.tva, c.remise, c.acompte);
  const attendu = serveur(c.lignes, c.tva, c.remise, c.acompte);
  assert.equal(obtenu.brut, attendu.brut, `${c.nom} : total HT brut`);
  assert.equal(obtenu.remise, attendu.remise, `${c.nom} : remise`);
  assert.equal(obtenu.ht, attendu.ht, `${c.nom} : net HT`);
  assert.equal(obtenu.ttc, attendu.ttc, `${c.nom} : total TTC`);
  assert.equal(obtenu.acompte, attendu.acompte, `${c.nom} : acompte`);
  // La TVA affichee doit etre la difference exacte entre TTC et HT, sinon
  // le bloc ne s'additionne pas a l'ecran.
  assert.equal(arrondi(obtenu.ht + obtenu.tva), obtenu.ttc, `${c.nom} : HT + TVA doit faire TTC`);
}

// Aucune ligne : pas de total, et surtout pas un zero qui laisserait
// croire a un devis a 0 €.
assert.equal(devisTotaux([], 20, 0, 30), null, "sans ligne, aucun total ne doit être affiché");

// L'acompte se calcule sur le HT, jamais sur le TTC : c'est ce que fait
// le serveur au moment de creer la facture d'acompte.
{
  const t = devisTotaux([{ quantite: 1, prix_unitaire_ht: 1000 }], 20, 0, 50);
  assert.equal(t.ht, 1000);
  assert.equal(t.ttc, 1200);
  assert.equal(t.acompte, 500, "50 % d'acompte sur 1 000 € HT = 500 €, pas 600 €");
}

// ---------------------------------------------------------------------
// LA FACTURE MONTRE SES TOTAUX, ELLE AUSSI
// ---------------------------------------------------------------------
// L'ecran de creation d'une facture listait les memes prestations avec le
// meme taux de TVA que le devis, et n'affichait aucun total : on emettait
// une facture de 1 840 € sans jamais voir le montant avant de cliquer
// « Creer ». La cause etait un detail d'implementation - le totalisateur
// avait ses selecteurs de champs ecrits en dur sur les identifiants du
// devis (`#df-taux-tva`...), donc inutilisable ailleurs.
{
  const source = appSource;
  assert.match(source, /function brancherTotalisateur\(formEl, containerId, champs/,
    "les champs du totalisateur doivent etre parametrables, sinon il ne sert qu'au devis");
  assert.match(source, /brancherTotalisateur\(formEl, "fa-lignes"/,
    "le formulaire de facture doit brancher le totalisateur");
  assert.match(source, /aria-label="Totaux de la facture"/,
    "le formulaire de facture doit reserver la place des totaux");
  // Une facture n'a ni remise ni acompte : les deux lignes ne doivent pas
  // apparaitre, et le total TTC se calcule directement sur le brut.
  const t = devisTotaux([{ quantite: 1, prix_unitaire_ht: 940 }], 10, 0, 0);
  assert.equal(t.remise, 0);
  assert.equal(t.acompte, 0);
  assert.equal(t.ttc, 1034);
}

console.log("OK - devis-totaux.test.mjs");
