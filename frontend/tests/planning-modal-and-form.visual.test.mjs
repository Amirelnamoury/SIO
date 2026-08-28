// Non-regression visuelle pour 2 bugs remontes apres test manuel :
//
// 1. La confirmation de suppression ("Supprimer ce rendez-vous ?") s'ouvrait
//    derriere la modale de detail du rendez-vous : #confirm-dialog et
//    #evenement-detail-modal partagent la classe .search-modal (meme
//    z-index), donc l'ordre visuel dependait de l'ordre DOM plutot que de
//    l'intention. Verifie que #confirm-dialog passe bien au-dessus.
//
// 2. Dans "Tout preparer", le libelle du champ Budget est plus long
//    ("Budget (optionnel, sinon = montant HT du devis)") et passe sur deux
//    lignes, ce qui decalait son champ par rapport a Adresse/Date sur la
//    meme ligne. Verifie que les trois <input> commencent au meme niveau.
//
// Utilise le vrai style.css et les vrais fragments HTML (copies verbatim de
// index.html/app.js, pas une reimplementation) rendus dans Chromium
// headless. Necessite Playwright ; si indisponible, le test est saute
// proprement (imprime SKIP, sort en 0) plutot que de faire echouer la
// validation - meme esprit que e2e/scenario8_stripe.mjs qui saute si Stripe
// n'est pas configure.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const stylePath = path.join(frontendDir, "style.css");

async function resolvePlaywright() {
  try {
    return await import("playwright");
  } catch {
    // Pas installe localement : tente le prefixe global npm (installation
    // partagee sur cette machine), sans imposer de dependance au projet.
  }
  try {
    const globalRoot = execSync("npm root -g", { encoding: "utf8" }).trim();
    const candidate = path.join(globalRoot, "playwright", "index.js");
    if (fs.existsSync(candidate)) {
      return await import(pathToFileURL(candidate).href);
    }
  } catch {
    // ignore
  }
  return null;
}

const playwrightModule = await resolvePlaywright();
if (!playwrightModule) {
  console.log("SKIP - planning-modal-and-form.visual.test.mjs : Playwright indisponible dans cet environnement.");
  process.exit(0);
}
const chromium = playwrightModule.chromium || playwrightModule.default.chromium;

const executablePath = process.env.PLAYWRIGHT_CHROMIUM_PATH || "/opt/pw-browsers/chromium";
const launchOptions = fs.existsSync(executablePath) ? { executablePath } : {};

const browser = await chromium.launch(launchOptions);
try {
  const page = await browser.newPage();

  // ---------- 1. Confirmation de suppression au-dessus du detail RDV ----------
  await page.setContent(`
    <div id="confirm-dialog" class="search-modal" role="dialog" aria-modal="true">
      <div class="confirm-dialog-box">
        <h3 id="confirm-dialog-title">Supprimer</h3>
        <p id="confirm-dialog-message">Supprimer le rendez-vous "Visite chantier" ?</p>
        <div class="confirm-dialog-actions">
          <button type="button" id="confirm-dialog-cancel">Annuler</button>
          <button type="button" id="confirm-dialog-ok">Supprimer</button>
        </div>
      </div>
    </div>
    <div id="evenement-detail-modal" class="search-modal" role="dialog" aria-modal="true">
      <div class="confirm-dialog-box">
        <h3 id="evenement-detail-titre">Visite chantier</h3>
        <div id="evenement-detail-body"></div>
        <div class="confirm-dialog-actions">
          <button type="button" data-action="close-evenement-detail">Fermer</button>
          <button type="button" data-action="supprimer-evenement">Supprimer</button>
          <button type="button" data-action="modifier-evenement">Modifier</button>
        </div>
      </div>
    </div>
  `);
  await page.addStyleTag({ path: stylePath });

  const zConfirm = await page.locator("#confirm-dialog").evaluate((el) => parseInt(getComputedStyle(el).zIndex, 10));
  const zDetail = await page.locator("#evenement-detail-modal").evaluate((el) => parseInt(getComputedStyle(el).zIndex, 10));
  assert.ok(zConfirm > zDetail, `#confirm-dialog (z-index ${zConfirm}) doit passer au-dessus de #evenement-detail-modal (z-index ${zDetail})`);

  // Verification "reelle" : le point ou se trouve le bouton Supprimer de la
  // confirmation doit bien resoudre vers CE bouton, pas vers un element de
  // la modale de detail qui serait visuellement par-dessus.
  const topElementIsConfirmOk = await page.evaluate(() => {
    const btn = document.getElementById("confirm-dialog-ok");
    const rect = btn.getBoundingClientRect();
    const atPoint = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
    return atPoint === btn || btn.contains(atPoint);
  });
  assert.ok(topElementIsConfirmOk, "le bouton Supprimer de la confirmation doit etre reellement au premier plan (cliquable), pas cache derriere la modale de detail");

  console.log("OK - 1/2 : confirmation de suppression au-dessus du detail du rendez-vous");

  // ---------- 2. Alignement Adresse / Date / Budget dans "Tout preparer" ----------
  await page.setContent(`
    <div class="form-box" style="width:900px;">
      <div class="form-grid form-grid-labels-aligned">
        <div><label for="prep-adresse-1">Adresse du chantier</label><input type="text" id="prep-adresse-1"></div>
        <div><label for="prep-date-1">Date de début</label><input type="date" id="prep-date-1"></div>
        <div><label for="prep-budget-1">Budget (optionnel, sinon = montant HT du devis)</label><input type="number" id="prep-budget-1"></div>
      </div>
    </div>
  `);
  await page.addStyleTag({ path: stylePath });

  const [yAdresse, yDate, yBudget] = await Promise.all([
    page.locator("#prep-adresse-1").evaluate((el) => el.getBoundingClientRect().top),
    page.locator("#prep-date-1").evaluate((el) => el.getBoundingClientRect().top),
    page.locator("#prep-budget-1").evaluate((el) => el.getBoundingClientRect().top),
  ]);
  assert.ok(Math.abs(yAdresse - yBudget) < 1, `le champ Adresse (y=${yAdresse}) et le champ Budget (y=${yBudget}) doivent commencer au meme niveau malgre le libelle du Budget sur deux lignes`);
  assert.ok(Math.abs(yDate - yBudget) < 1, `le champ Date (y=${yDate}) et le champ Budget (y=${yBudget}) doivent commencer au meme niveau`);

  // Le libelle Budget doit effectivement passer sur deux lignes a cette
  // largeur (sinon le test ne verifie rien de pertinent).
  const budgetLabelLines = await page.locator('label[for="prep-budget-1"]').evaluate((el) => {
    const lineHeight = parseFloat(getComputedStyle(el).lineHeight);
    return Math.round(el.getBoundingClientRect().height / lineHeight);
  });
  assert.ok(budgetLabelLines >= 2, "le libelle Budget doit occuper au moins 2 lignes a cette largeur (sinon le cas de regression n'est pas exerce)");

  console.log("OK - 2/2 : Adresse / Date / Budget alignes malgre le libelle Budget sur deux lignes");
} finally {
  await browser.close();
}

console.log("OK - planning-modal-and-form.visual.test.mjs");
