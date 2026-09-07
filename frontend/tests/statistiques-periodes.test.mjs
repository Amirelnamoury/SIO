/* Les statistiques doivent dire de QUOI elles parlent, et sur quelle periode.
 *
 * Trois defauts de presentation, tous invisibles a l'oeil parce que les
 * chiffres eux-memes etaient exacts :
 *   1. la page portait une pastille « 12 derniers mois » valable pour le seul
 *      chiffre d'affaires ; le taux de signature, l'acquisition et les delais
 *      de paiement comptent depuis l'ouverture du compte ;
 *   2. le dernier point de la courbe est le mois EN COURS. Compare au mois
 *      complet qui le precede, il produisait un recul mecanique annonce comme
 *      un recul reel - et trace plein, il ressemblait a un effondrement ;
 *   3. l'etape « Devis envoyés » comptait en realite tous les devis,
 *      brouillons compris.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import * as sources from "./_sources.mjs";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
// Le graphique et la vue vivent dans statistiques.js depuis le decoupage §16.
const appSource = sources.statistiques;
const indexSource = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");
const analyticsSource = fs.readFileSync(path.resolve(frontendDir, "..", "backend", "app", "routers", "analytics.py"), "utf8");

// ---------------------------------------------------------------------
// 1. Le serveur renvoie la fenetre entiere, trous compris.
// ---------------------------------------------------------------------
assert.match(analyticsSource, /for i in range\(NB_MOIS_FENETRE\)/,
  "la serie doit etre construite sur la fenetre, pas sur les mois encaissants");
assert.doesNotMatch(analyticsSource, /sorted\(ca_par_mois_dict\.items\(\)\)/,
  "iterer le dictionnaire des paiements laisserait retomber les mois vides");
assert.doesNotMatch(analyticsSource, /timedelta\(days=365\)/,
  "un recul de 365 jours tronque le premier mois de la fenetre");

// ---------------------------------------------------------------------
// 2. La page ne porte plus une periode unique pour des blocs qui n'en
//    partagent pas.
// ---------------------------------------------------------------------
assert.doesNotMatch(indexSource, /stats-period-control/, "la pastille de periode globale doit avoir disparu");
// Les statistiques sont un fichier a elles depuis le decoupage §16 : le
// marqueur de fin (« Avis clients ») est reste dans app.js, la tranche
// n'a donc plus lieu d'etre - le fichier entier EST la vue.
const vue = sources.statistiques;
for (const [section, periode] of [
  ["Chiffre d'affaires", "douze derniers mois"],
  ["Performance commerciale", "depuis l'ouverture du compte"],
  ["Acquisition", "depuis l'ouverture"],
  ["Clients et paiements", "depuis l'ouverture du compte"],
]) {
  const bloc = vue.slice(vue.indexOf(`saSection("${section}"`));
  assert.ok(bloc.slice(0, 2200).includes(periode), `la section « ${section} » doit annoncer « ${periode} »`);
}
// Pipeline et impayes sont des soldes a l'instant, pas des cumuls sur un an.
assert.match(vue, /stats-ca-legende-note/, "la legende du CA doit corriger la portee de ses deux soldes");

// ---------------------------------------------------------------------
// 3. La comparaison porte sur deux mois COMPLETS.
// ---------------------------------------------------------------------
assert.match(vue, /dernierComplet = nbMois > 1 \? a\.ca_par_mois\[nbMois - 2\]/,
  "le mois de reference est l'avant-dernier point : le dernier est en cours");
assert.match(vue, /avantDernierComplet = nbMois > 2 \? a\.ca_par_mois\[nbMois - 3\]/);
assert.match(vue, /deux derniers mois complets/, "le libelle doit nommer la periode comparee");
assert.match(vue, /caAreaChartSvg\(a\.ca_par_mois, \{ dernierEnCours: true \}\)/);

// ---------------------------------------------------------------------
// 4. Le libelle de l'entonnoir dit ce que le nombre contient.
// ---------------------------------------------------------------------
assert.match(vue, /label: "Devis créés", nb: a\.nb_devis_total/,
  "nb_devis_total compte aussi les brouillons : il ne peut pas s'appeler « envoyés »");
assert.doesNotMatch(vue, /"Devis envoyés", nb: a\.nb_devis_total/);
// Un pourcentage bati sur deux populations differentes a disparu.
assert.doesNotMatch(vue, /recurrentPct/, "le ratio clients recurrents / clients gagnes melait deux ensembles");
assert.match(vue, /Clients avec plusieurs devis signés/, "le libelle doit decrire exactement ce qui est compte");

// ---------------------------------------------------------------------
// 5. Le graphique, execute : le mois en cours n'est pas trace comme les
//    autres, et l'aplat s'arrete avant lui.
// ---------------------------------------------------------------------
const debut = appSource.indexOf("function caAreaChartSvg");
const fin = appSource.indexOf("function mixHexColors");
const contexte = {
  fmtEuro: (v) => `${v} €`,
  // La graduation de l'axe a son propre format : elle vit dans socle.js,
  // hors de la tranche de code executee ici, donc elle est fournie.
  fmtEuroAxe: (v) => (Math.abs(v) >= 1000 ? `${(v / 1000).toFixed(1)} k€` : `${v} €`),
  fmtMoisCourt: (m) => m,
};
vm.runInNewContext(
  `${appSource.slice(debut, fin)}\nglobalThis.__c = { caAreaChartSvg };`,
  contexte,
  { filename: appPath },
);
const serie = Array.from({ length: 12 }, (_, i) => ({ mois: `2026-${String(i + 1).padStart(2, "0")}`, ca: 1000 * (i + 1) }));

const complet = contexte.__c.caAreaChartSvg(serie);
assert.doesNotMatch(complet, /stroke-dasharray/, "sans mois en cours, aucun trait pointille");

const enCours = contexte.__c.caAreaChartSvg(serie, { dernierEnCours: true });
assert.match(enCours, /stroke-dasharray/, "le mois en cours doit se distinguer du trace plein");
const cheminPlein = /<path d="(M[^"]+)" fill="none" stroke="var\(--sa-accent\)" stroke-width="2" stroke-linejoin/.exec(enCours)[1];
assert.equal((cheminPlein.match(/[ML]/g) || []).length, serie.length - 1,
  "le trace plein doit s'arreter au dernier mois complet");
// Les douze etiquettes de mois restent produites, y compris pour les mois a zero.
const creux = serie.map((m, i) => ({ ...m, ca: i % 3 === 0 ? 0 : m.ca }));
const avecCreux = contexte.__c.caAreaChartSvg(creux);
assert.ok((avecCreux.match(/chart-axis-label/g) || []).length > 5, "un mois a zero reste un point du graphique");

// ---------------------------------------------------------------------
// 6. La graduation de l'axe doit TENIR dans sa gouttiere.
// ---------------------------------------------------------------------
// « 11 650,00 € » demandait 60 px la ou l'axe en offrait 36 : les quatre
// graduations sortaient du viewBox et etaient rognees, si bien qu'on ne
// pouvait plus dire a quelle hauteur passait la courbe. Un axe donne une
// ECHELLE ; la somme exacte se lit sur le point et dans le tableau.
const grosseSerie = Array.from({ length: 12 }, (_, i) => ({ mois: `2026-${String(i + 1).padStart(2, "0")}`, ca: 1_000_000 * (i + 1) }));
const svgGros = contexte.__c.caAreaChartSvg(grosseSerie);
assert.doesNotMatch(svgGros, /class="chart-axis-label"[^>]*>[\d\s]{7,}/,
  "aucune graduation ne doit etaler un montant complet sur l'axe");
assert.match(sources.socle, /function fmtEuroAxe/, "le format de graduation est un helper partage, pas une regle locale");
assert.match(sources.statistiques, /PAD_L = 52/,
  "la gouttiere de l'axe doit rester assez large pour sa graduation la plus longue");

console.log("OK - statistiques-periodes.test.mjs");
