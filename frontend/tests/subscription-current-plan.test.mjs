import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const appPath = path.join(frontendDir, "app.js");
const pricingPath = path.join(frontendDir, "pricing.js");
const appSource = fs.readFileSync(appPath, "utf8");
const pricingSource = fs.readFileSync(pricingPath, "utf8");

const start = appSource.indexOf("function normalizeCurrentPlan");
const end = appSource.indexOf('document.addEventListener("click", (e) => {', start);
assert.ok(start !== -1 && end !== -1 && end > start, "le rendu Abonnement est introuvable dans app.js");

const elements = {
  "pricing-plans": { innerHTML: "" },
  "pricing-site-offer": { innerHTML: "" },
  "pricing-modal": { hidden: true },
};
const context = {
  currentArtisan: null,
  document: { getElementById: (id) => elements[id] },
  escapeHtml: (value) => String(value),
};

vm.runInNewContext(
  `${pricingSource}\n${appSource.slice(start, end)}\nglobalThis.__subscription = { normalizeCurrentPlan, renderPlanCards, openPricingModal };`,
  context,
  { filename: appPath },
);

const { renderPlanCards, openPricingModal } = context.__subscription;
const planKeys = ["gratuit", "essentiel", "pro", "business"];

function cardHtml(html, key) {
  const startIndex = html.indexOf(`data-plan-key="${key}"`);
  assert.notEqual(startIndex, -1, `la carte ${key} doit etre rendue`);
  const nextIndexes = planKeys
    .map((candidate) => html.indexOf(`data-plan-key="${candidate}"`, startIndex + 1))
    .filter((index) => index !== -1);
  return html.slice(startIndex, nextIndexes.length ? Math.min(...nextIndexes) : html.length);
}

for (const currentPlan of planKeys) {
  const html = renderPlanCards(currentPlan);
  assert.equal((html.match(/data-current-plan="true"/g) || []).length, 1, `${currentPlan} doit produire une seule carte actuelle`);

  for (const key of planKeys) {
    const card = cardHtml(html, key);
    if (key === currentPlan) {
      assert.match(card, /data-current-plan="true"/, `la carte ${key} doit etre actuelle`);
      assert.match(card, />Plan actuel<\/button>/, `la carte ${key} doit afficher Plan actuel`);
      assert.match(card, /<button[^>]*disabled[^>]*>Plan actuel<\/button>/, `le bouton du plan actuel ${key} doit etre desactive`);
      assert.doesNotMatch(card, /S'abonner a/, `la carte ${key} ne doit pas proposer de s'abonner a son plan actuel`);
    } else {
      assert.doesNotMatch(card, /data-current-plan="true"/, `la carte ${key} ne doit pas etre actuelle`);
      assert.doesNotMatch(card, />Plan actuel<\/button>/, `la carte ${key} ne doit pas afficher Plan actuel`);
      if (key !== "gratuit") {
        assert.match(card, new RegExp(`data-action="confirm-upgrade" data-plan="${key}"`), `la carte ${key} doit conserver son action d'abonnement`);
      } else {
        assert.match(card, /data-action="close-pricing">Conserver mon plan actuel<\/button>/, "Gratuit non courant doit conserver l'action de fermeture sans se dire actuel");
      }
    }
  }

  if (currentPlan !== "gratuit") {
    assert.doesNotMatch(cardHtml(html, "gratuit"), /Rester sur le plan Gratuit/, "Gratuit ne doit pas se presenter comme le plan actuel");
  }
}

// Non-regression du flux asynchrone : un premier rendu sans profil utilise
// Gratuit, puis l'ouverture suivante doit relire currentArtisan.plan recu de /me.
openPricingModal();
assert.match(cardHtml(elements["pricing-plans"].innerHTML, "gratuit"), /data-current-plan="true"/);

context.currentArtisan = await Promise.resolve({ plan: "essentiel" });
openPricingModal();
assert.equal((elements["pricing-plans"].innerHTML.match(/data-current-plan="true"/g) || []).length, 1);
assert.match(cardHtml(elements["pricing-plans"].innerHTML, "essentiel"), /data-current-plan="true"/);
assert.doesNotMatch(cardHtml(elements["pricing-plans"].innerHTML, "gratuit"), /data-current-plan="true"/);
assert.equal(elements["pricing-modal"].hidden, false);

console.log("OK - subscription-current-plan.test.mjs");
