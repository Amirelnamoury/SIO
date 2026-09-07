/* Le planning ne doit affirmer que ce qui a ete saisi.
 *
 * Avant : chaque item de la grille horaire etait dessine sur UNE HEURE, quelle
 * que soit sa nature - un rendez-vous sans fin renseignee, une echeance de
 * tache, un debut de chantier. La constante `const DUREE = 60` produisait donc
 * une occupation que personne n'avait declaree, et l'artisan pouvait y lire
 * « ma matinee est prise » sur la foi d'un defaut de dessin. Pire : les taches
 * et les debuts de chantier n'ont AUCUNE heure - le serveur les ancre a 9h00
 * et 8h00 pour pouvoir les trier (routers/planning.py) - et ces ancres se
 * retrouvaient telles quelles sur l'axe horaire.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");
const schemasSource = fs.readFileSync(path.resolve(frontendDir, "..", "backend", "app", "schemas.py"), "utf8");
const planningRouter = fs.readFileSync(path.resolve(frontendDir, "..", "backend", "app", "routers", "planning.py"), "utf8");

// La duree ne peut plus etre une constante de dessin.
assert.doesNotMatch(appSource, /const DUREE = 60/, "aucune duree inventee ne doit subsister");

// Le contrat serveur doit reellement porter la fin, sinon le front n'a rien a
// afficher et retombe sur des reperes pour tout.
assert.match(schemasSource, /class PlanningItem\(BaseModel\):[\s\S]*?date_fin: Optional\[datetime\] = None/,
  "PlanningItem doit transporter la fin de l'evenement");
assert.match(planningRouter, /PlanningItem\(\s*date=e\.date_debut, date_fin=e\.date_fin/,
  "l'agregation du planning ne doit plus aplatir date_fin");
// Taches et debuts de chantier n'ont pas de fin : rien ne doit leur en donner.
assert.doesNotMatch(planningRouter, /type="tache"[\s\S]{0,200}date_fin=/, "une echeance de tache n'a pas de fin");
assert.doesNotMatch(planningRouter, /type="chantier_debut"[\s\S]{0,200}date_fin=/, "un debut de chantier n'a pas de fin");

// ---------------------------------------------------------------------
// Le calcul de mise en page, execute pour de vrai.
// ---------------------------------------------------------------------
const debut = appSource.indexOf("const PLANNING_HOUR_START");
const fin = appSource.indexOf("function planningDayCellHtml");
assert.ok(debut !== -1 && fin > debut, "le bloc de la grille horaire est introuvable");

const contexte = {
  escapeHtml: (v) => String(v ?? ""),
  PLANNING_TYPE_CLASS: {},
  PLANNING_TYPES_EVENEMENT: new Set(["rdv", "visite", "intervention", "autre"]),
  // Heures lues en UTC pour que le test ne depende pas du fuseau de la machine.
  planningDateHeureLocale: (v) => {
    const d = new Date(v);
    return { date: d.toISOString().slice(0, 10), heure: d.toISOString().slice(11, 16) };
  },
  planningHeureLocale: (v) => new Date(v).toISOString().slice(11, 16),
  planningToIso: (v) => new Date(v).toISOString().slice(0, 10),
};
vm.runInNewContext(
  `${appSource.slice(debut, fin)}\nglobalThis.__p = { planningSansHeure, planningDureeMinutes, planningLayoutDay, planningPositionedItemHtml, planningBandeHauteur, planningDureeOptionsHtml, PLANNING_ROW_H, PLANNING_MARQUEUR_H };`,
  contexte,
  { filename: appPath },
);
const P = contexte.__p;

const jour = "2026-09-07";
const a = (h, m = 0) => `${jour}T${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00.000Z`;

// 1. Les types sans heure sont reconnus comme tels.
assert.equal(P.planningSansHeure({ type: "tache" }), true);
assert.equal(P.planningSansHeure({ type: "chantier_debut" }), true);
assert.equal(P.planningSansHeure({ type: "rdv" }), false);

// 2. La duree vient des donnees, jamais d'une constante.
assert.equal(P.planningDureeMinutes({ date: a(9), date_fin: a(10, 30) }), 90);
assert.equal(P.planningDureeMinutes({ date: a(9), date_fin: null }), null);
assert.equal(P.planningDureeMinutes({ date: a(9) }), null);
// Une fin anterieure au debut est une donnee aberrante, pas une duree negative.
assert.equal(P.planningDureeMinutes({ date: a(9), date_fin: a(8) }), null);
assert.equal(P.planningDureeMinutes({ date: a(9), date_fin: a(9) }), null);

// 3. La hauteur dessinee suit la duree reelle ; sans duree, c'est un repere.
const rendu = (item) => {
  const [place] = P.planningLayoutDay([item]);
  const html = P.planningPositionedItemHtml(place);
  return {
    html,
    hauteur: Number(/height:(\d+(?:\.\d+)?)px/.exec(html)[1]),
    top: Number(/top:(\d+(?:\.\d+)?)px/.exec(html)[1]),
  };
};
const uneHeureTrente = rendu({ date: a(9), date_fin: a(10, 30), type: "rdv", titre: "Metre", reference_id: 1 });
assert.ok(Math.abs(uneHeureTrente.hauteur - (1.5 * P.PLANNING_ROW_H - 2)) < 0.5,
  `1 h 30 doit occuper une heure et demie de grille (obtenu ${uneHeureTrente.hauteur}px)`);
assert.match(uneHeureTrente.html, /est-borne/);
assert.match(uneHeureTrente.html, /09:00 – 10:30/, "un creneau borne annonce ses deux bornes");

const sansFin = rendu({ date: a(9), date_fin: null, type: "rdv", titre: "Visite", reference_id: 2 });
assert.equal(sansFin.hauteur, P.PLANNING_MARQUEUR_H, "sans fin connue, pas de bloc d'une heure");
assert.match(sansFin.html, /est-marqueur/);
assert.doesNotMatch(sansFin.html, /–/, "aucun tiret : il laisserait croire a une fin");
assert.match(sansFin.html, /fin non renseignée/, "l'infobulle doit le dire franchement");
assert.ok(sansFin.hauteur < P.PLANNING_ROW_H / 2, "le repere ne doit pas ressembler a une plage occupee");

// Meme heure de debut : les deux items commencent au meme endroit.
assert.equal(uneHeureTrente.top, sansFin.top);

// 4. Deux rendez-vous qui se chevauchent vraiment se partagent la largeur ;
//    deux reperes espaces de 40 min ne se genent pas.
const chevauchent = P.planningLayoutDay([
  { date: a(9), date_fin: a(10, 30), type: "rdv", titre: "A", reference_id: 1 },
  { date: a(10), date_fin: a(11), type: "rdv", titre: "B", reference_id: 2 },
]);
assert.equal(chevauchent[0].totalCols, 2, "deux creneaux qui se recouvrent occupent deux colonnes");
const espaces = P.planningLayoutDay([
  { date: a(9), date_fin: null, type: "rdv", titre: "A", reference_id: 1 },
  { date: a(9, 40), date_fin: null, type: "rdv", titre: "B", reference_id: 2 },
]);
assert.equal(espaces[0].totalCols, 1, "deux reperes espaces gardent la pleine largeur");

// 5. La bande « Sans heure » est reservee a la meme hauteur pour toute la
//    grille - c'est ce qui garde les reglures en face des heures.
const jours = [new Date(`${jour}T12:00:00Z`), new Date("2026-09-08T12:00:00Z")];
assert.equal(P.planningBandeHauteur(jours, []), 0, "sans item hors axe, aucune bande");
const avecTaches = P.planningBandeHauteur(jours, [
  { date: a(9), type: "tache" },
  { date: a(9), type: "tache" },
  { date: "2026-09-08T08:00:00.000Z", type: "chantier_debut" },
]);
assert.ok(avecTaches > 0, "deux taches le meme jour reservent une bande");
assert.equal(
  P.planningBandeHauteur(jours, [{ date: a(9), type: "tache" }, { date: "2026-09-08T08:00:00.000Z", type: "chantier_debut" }]) < avecTaches,
  true,
  "la hauteur suit le jour le plus charge",
);

// 6. Le formulaire ne propose aucune duree par defaut.
const options = P.planningDureeOptionsHtml("");
assert.match(options, /^<option value=""( selected)?>Non précisée<\/option>/, "« Non précisée » ouvre la liste");
assert.match(options, /value=""\s+selected/, "et c'est la valeur retenue quand rien n'a ete saisi");
// Une duree enregistree hors liste ne doit pas etre effacee a la reouverture.
assert.match(P.planningDureeOptionsHtml("75"), /<option value="75" selected>1 h 15<\/option>/);

// 7. La grille ne recoit que des items reellement horaires.
assert.match(appSource, /const surAxe = hourGrid \? dayItems\.filter\(\(i\) => !planningSansHeure\(i\)\)/,
  "les items sans heure ne doivent pas atteindre l'axe horaire");

// 8. Deplacer un rendez-vous deplace aussi sa fin.
assert.match(appSource, /payload\.date_fin = new Date\(new Date\(source\.date_fin\)\.getTime\(\) \+ decalage\)/,
  "un glisser-deposer doit decaler la fin comme le debut");

console.log("OK - planning-duree.test.mjs");
