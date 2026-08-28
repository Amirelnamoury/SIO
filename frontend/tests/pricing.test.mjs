import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const pricingPath = path.join(frontendDir, "pricing.js");
const pricingSource = fs.readFileSync(pricingPath, "utf8");
const context = {};

vm.runInNewContext(
  `${pricingSource}\nglobalThis.__pricing = { PRICING, PRICING_ORDRE, SITE_VITRINE_OFFER };`,
  context,
  { filename: pricingPath },
);

const { PRICING, PRICING_ORDRE, SITE_VITRINE_OFFER } = context.__pricing;
const surfaces = ["landing.html", "app.js", "pricing.js"]
  .map((file) => fs.readFileSync(path.join(frontendDir, file), "utf8"))
  .join("\n");

assert.deepEqual(
  Object.fromEntries(PRICING_ORDRE.map((plan) => [plan, PRICING[plan].prix])),
  { gratuit: 0, essentiel: 19, pro: 39, business: 69 },
  "les tarifs SaaS doivent rester a 0 / 19 / 39 / 69",
);
assert.equal(PRICING.pro.recommande, true, "Pro doit rester recommande");
assert.equal(SITE_VITRINE_OFFER.creation, 490, "la creation du Site Vitrine doit rester a 490 EUR HT");
assert.equal(SITE_VITRINE_OFFER.mensuel, 19, "la gestion et maintenance doit rester a 19 EUR HT/mois");
assert.deepEqual(
  [...SITE_VITRINE_OFFER.disponibleAvec],
  ["gratuit", "essentiel", "pro", "business"],
  "le Site Vitrine doit etre disponible avec tous les plans",
);
assert.equal("planMinimum" in SITE_VITRINE_OFFER, false, "aucun plan minimum ne doit etre impose au Site Vitrine");
assert.match(SITE_VITRINE_OFFER.description, /gestion technique/i, "le Site Vitrine doit etre presente comme un service gere");
assert.match(SITE_VITRINE_OFFER.resumeInclus, /maintenance/i, "la maintenance doit etre explicite");
assert.match(SITE_VITRINE_OFFER.domaineStandard, /15 EUR HT\/an/, "la limite du domaine standard doit etre precisee");
assert.match(SITE_VITRINE_OFFER.domaineStandard, /transférable au client/i, "le domaine doit rester transferable au client");
assert.match(SITE_VITRINE_OFFER.horsForfaitResume, /sur devis/i, "les evolutions importantes doivent etre annoncees sur devis");
assert.doesNotMatch(surfaces, /disponible (?:a|des) partir du plan Essentiel|disponible des Essentiel|Essentiel, Pro et Business/i);
assert.doesNotMatch(surfaces, /planMinimum/);
assert.match(surfaces, /prestation optionnelle|option distincte/i, "le Site Vitrine doit rester optionnel");
assert.doesNotMatch(surfaces, /site vitrine[^.]{0,80}obligatoire/i, "le Site Vitrine ne doit jamais etre obligatoire");
assert.doesNotMatch(surfaces, /\d+[,.]99\s*(?:EUR|&nbsp;|€)/i, "aucun prix psychologique ne doit etre introduit");

assert(PRICING.essentiel.fonctionnalites.includes("Relance manuelle des factures"));
assert(PRICING.pro.fonctionnalites.includes("Relances automatiques de factures"));
assert(PRICING.pro.fonctionnalites.includes("Contrats récurrents"));
assert(PRICING.business.fonctionnalites.includes("Rôles et permissions"));

console.log("Pricing frontend: OK");
