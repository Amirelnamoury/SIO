// Non-regression pour le bug "Planning date/heure decalees" : un rendez-vous
// cree pour une date/heure donnee en Europe/Paris doit s'afficher a cette
// meme date/heure dans le Planning, quel que soit le fuseau horaire de la
// machine qui l'affiche, et quelle que soit la periode de l'annee (ete/hiver,
// avec le changement d'heure). On extrait le vrai code de app.js (pas une
// reimplementation) pour tester le comportement reellement livre.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const start = appSource.indexOf('const PLANNING_TIMEZONE = "Europe/Paris";');
const end = appSource.indexOf("function planningStartOfWeek");
assert.ok(start !== -1 && end !== -1 && end > start, "les helpers de fuseau du Planning sont introuvables dans app.js (le fichier a-t-il change de forme ?)");
const helpersSource = appSource.slice(start, end);

const context = {};
vm.runInNewContext(
  `${helpersSource}\nglobalThis.__planning = { planningToIso, planningHeureLocale, planningDateHeureLocale, PLANNING_TIMEZONE };`,
  context,
  { filename: appPath },
);
const { planningToIso, planningHeureLocale, planningDateHeureLocale } = context.__planning;

// ---- Cas du rapport de bug original : 29/08/2026 09:00 (ete, UTC+2) ----
{
  const iso = new Date("2026-08-29T09:00:00+02:00");
  assert.equal(planningToIso(iso), "2026-08-29", "un RDV a 09:00 heure d'ete doit rester sur le 29/08, pas glisser au 30/08");
  assert.equal(planningHeureLocale(iso), "09:00", "l'heure affichee doit rester 09:00 heure de Paris");
  const { date, heure } = planningDateHeureLocale(iso);
  assert.equal(date, "2026-08-29");
  assert.equal(heure, "09:00");
}

// ---- Cas hiver (UTC+1) : verifie que ce n'est pas juste un hack ete ----
{
  const iso = new Date("2026-01-15T09:00:00+01:00");
  assert.equal(planningToIso(iso), "2026-01-15", "un RDV a 09:00 heure d'hiver doit rester sur le 15/01");
  assert.equal(planningHeureLocale(iso), "09:00");
}

// ---- Heure proche de minuit, ete : 23:30 Paris = 21:30 UTC, ne doit pas ----
// ---- glisser au jour suivant en UTC ni la veille en cle de jour. ----
{
  const iso = new Date("2026-08-29T23:30:00+02:00");
  assert.equal(planningToIso(iso), "2026-08-29", "23:30 heure de Paris ne doit pas etre range sous le 30/08");
  assert.equal(planningHeureLocale(iso), "23:30");
}

// ---- Heure proche de minuit, hiver : 00:30 Paris = 23:30 UTC la veille, ----
// ---- ne doit pas glisser vers la veille dans la cle de jour. ----
{
  const iso = new Date("2026-01-15T00:30:00+01:00");
  assert.equal(planningToIso(iso), "2026-01-15", "00:30 heure de Paris ne doit pas etre range sous le 14/01");
  assert.equal(planningHeureLocale(iso), "00:30");
}

// ---- planningDateHeureLocale pré-remplit bien le formulaire d'edition avec ----
// ---- exactement la date et l'heure saisies a la creation (Bug 2 : reouvrir ----
// ---- un rendez-vous en edition ne doit pas montrer un decalage). ----
{
  const { date, heure } = planningDateHeureLocale("2026-08-29T09:00:00+02:00");
  assert.equal(date, "2026-08-29");
  assert.equal(heure, "09:00");
}

console.log("OK - planning-date.test.mjs");
