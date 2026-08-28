// Scenario 13 : bug persistant "decalage d'heure dans le Planning", teste
// reellement de bout en bout (backend FastAPI reel, SQLite reelle, frontend
// reel servi, navigateur Chromium reel via Playwright) plutot que via un
// helper JS isole.
//
// Cause racine reelle (confirmee par inspection directe du payload HTTP, de
// la reponse API et de la ligne SQLite) : SQLite ne conserve pas le fuseau
// horaire des colonnes DateTime(timezone=True) - une valeur relue revient
// "naive" (sans tzinfo), et FastAPI/Pydantic la serialisait donc sans "Z" ni
// offset. Le frontend, qui convertit deja correctement l'heure locale saisie
// vers UTC avant l'envoi (planningLocalToUtcIso), recevait ensuite cette
// chaine ambigue et la reinterpretait avec `new Date(...)` dans le fuseau
// AMBIANT du navigateur plutot qu'UTC - d'ou le decalage silencieux
// (exactement -2h en ete, -1h en hiver) qui persistait malgre la conversion
// cote frontend deja correcte. Voir backend/app/schemas.py (_naive_vers_utc,
// utilise par EvenementOut et PlanningItem) pour le correctif.
//
// Ce scenario echouait avant ce correctif et doit passer apres. Il utilise
// deliberement un contexte navigateur regle sur Europe/Paris (pas le fuseau
// de la machine hote, qui peut etre UTC et masquer le bug par coincidence -
// c'est exactement ce qui s'est produit lors d'une verification precedente).
//
// Necessite Playwright ET un backend deja demarre sur http://localhost:8000
// (voir README.md). Saute proprement si l'un des deux est indisponible.
import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { api, API_BASE, emailUnique } from "./helpers.mjs";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..", "frontend");

async function resolvePlaywright() {
  try {
    return await import("playwright");
  } catch {
    // ignore - tente le prefixe global npm ci-dessous
  }
  try {
    const globalRoot = execSync("npm root -g", { encoding: "utf8" }).trim();
    const candidate = path.join(globalRoot, "playwright", "index.js");
    if (fs.existsSync(candidate)) return await import(pathToFileURL(candidate).href);
  } catch {
    // ignore
  }
  return null;
}

/** Petit serveur statique (sans dependance externe) pour servir frontend/. */
function serveFrontend(port) {
  const server = http.createServer((req, res) => {
    const reqPath = req.url.split("?")[0];
    const filePath = path.join(frontendDir, reqPath === "/" ? "/index.html" : reqPath);
    if (!filePath.startsWith(frontendDir)) { res.writeHead(403); res.end(); return; }
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end("Not found"); return; }
      const ext = path.extname(filePath);
      const type = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" }[ext] || "application/octet-stream";
      res.writeHead(200, { "Content-Type": type });
      res.end(data);
    });
  });
  return new Promise((resolve) => server.listen(port, () => resolve(server)));
}

export default async function scenario13() {
  const playwrightModule = await resolvePlaywright();
  if (!playwrightModule) {
    console.log("  -> SAUTE : Playwright indisponible dans cet environnement.");
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/docs`);
    if (!res.ok) throw new Error("backend indisponible");
  } catch {
    console.log(`  -> SAUTE : backend injoignable sur ${API_BASE} (voir README.md).`);
    return;
  }

  const chromium = playwrightModule.chromium || playwrightModule.default.chromium;
  const FRONTEND_PORT = 8099;
  const server = await serveFrontend(FRONTEND_PORT);
  const executablePath = "/opt/pw-browsers/chromium";
  const browser = await chromium.launch(fs.existsSync(executablePath) ? { executablePath } : {});

  try {
    // Contexte EXPLICITEMENT regle sur Europe/Paris, comme la machine d'un
    // artisan francais reel - jamais le fuseau (potentiellement UTC) de la
    // machine qui execute le test, qui masquerait le bug par coincidence.
    const context = await browser.newContext({ timezoneId: "Europe/Paris", locale: "fr-FR" });
    const page = await context.newPage();

    const email = emailUnique("planning-tz");
    const { access_token } = await api.post("/auth/register", {
      email, password: "TestPass123!", nom_entreprise: `Planning TZ ${Date.now()}`, metier: "plombier",
    });

    async function connecter() {
      await page.goto(`http://localhost:${FRONTEND_PORT}/index.html`);
      await page.evaluate((token) => localStorage.setItem("suite_artisan_token", token), access_token);
      await page.reload();
      await page.waitForSelector("#dashboard-screen:not([hidden])", { timeout: 10000 });
      const onboardingVisible = await page.locator("#onboarding-modal").evaluate((el) => !el.hidden);
      if (onboardingVisible) {
        await page.click('[data-action="onboarding-skip"]');
        await page.waitForTimeout(200);
      }
    }

    async function ouvrirPlanning() {
      await page.click('[data-view="planning"]');
      await page.waitForSelector("#view-planning:not([hidden])");
    }

    async function creerRdv(dateStr, heureStr, titre) {
      await page.click('[data-action="show-evenement-form"]');
      await page.waitForSelector("#evenement-form");
      await page.fill("#ev-titre", titre);
      await page.fill("#ev-date", dateStr);
      await page.fill("#ev-heure", heureStr);
      await page.click("#evenement-form button[type=submit]");
      await page.waitForTimeout(500);
    }

    async function chipTexte() {
      await page.waitForSelector(".planning-item", { timeout: 5000 });
      return page.locator(".planning-item").first().innerText();
    }

    async function modifierHeure(nouvelleHeure) {
      await page.locator(".planning-item").first().click();
      await page.waitForSelector("#evenement-detail-modal:not([hidden])", { timeout: 5000 });
      await page.click('[data-action="modifier-evenement"]');
      await page.waitForSelector("#evenement-form", { timeout: 5000 });
      const heureAvant = await page.inputValue("#ev-heure");
      await page.fill("#ev-heure", nouvelleHeure);
      await page.click("#evenement-form button[type=submit]");
      await page.waitForTimeout(500);
      return heureAvant;
    }

    async function heurePreremplie() {
      return page.inputValue("#ev-heure");
    }

    // ---------- ETE : creation 29/08/2026 09:00 -> doit afficher 09:00 ----------
    await connecter();
    await ouvrirPlanning();
    await creerRdv("2026-08-29", "09:00", "TEST_ETE");
    const chip1 = await chipTexte();
    assert.ok(chip1.includes("09:00"), `creation ete : 09:00 saisi doit afficher 09:00, chip="${chip1}"`);
    assert.ok(!chip1.includes("07:00"), `REGRESSION EXACTE DU BUG SIGNALE : chip affiche 07:00 au lieu de 09:00, chip="${chip1}"`);

    // Verification directe de la reponse API (pas seulement le DOM).
    const planningApres1 = await api.get(`/planning?debut=2026-08-29&fin=2026-08-29`, access_token);
    assert.match(planningApres1[0].date, /^2026-08-29T07:00:00(\.000)?Z$/, `l'API doit renvoyer un instant UTC explicite (Z), recu="${planningApres1[0].date}"`);

    // ---------- EDITION 09:00 -> 10:00 ----------
    const heureAvantEdition = await modifierHeure("10:00");
    assert.equal(heureAvantEdition, "09:00", `le formulaire d'edition doit pre-remplir 09:00 avant modification, affiche="${heureAvantEdition}"`);
    const chip2 = await chipTexte();
    assert.ok(chip2.includes("10:00"), `edition 09:00->10:00 : doit afficher 10:00, chip="${chip2}"`);
    assert.ok(!chip2.includes("08:00"), `REGRESSION EXACTE DU BUG SIGNALE : chip affiche 08:00 au lieu de 10:00, chip="${chip2}"`);

    // ---------- RECHARGEMENT COMPLET DE LA PAGE : aucune derive ----------
    await connecter();
    await ouvrirPlanning();
    const chip3 = await chipTexte();
    assert.ok(chip3.includes("10:00"), `apres rechargement complet de la page, doit toujours afficher 10:00, chip="${chip3}"`);

    // ---------- EDITION REPETEE : ouvrir/enregistrer sans rien changer, ----------
    // ---------- plusieurs fois, ne doit jamais deriver. ----------
    await page.locator(".planning-item").first().click();
    await page.waitForSelector("#evenement-detail-modal:not([hidden])", { timeout: 5000 });
    await page.click('[data-action="modifier-evenement"]');
    await page.waitForSelector("#evenement-form", { timeout: 5000 });
    const heurePrefillEdition1 = await heurePreremplie();
    assert.equal(heurePrefillEdition1, "10:00", `le formulaire d'edition doit pre-remplir 10:00, affiche="${heurePrefillEdition1}"`);
    await page.click("#evenement-form button[type=submit]"); // enregistre sans rien changer
    await page.waitForTimeout(500);

    await page.locator(".planning-item").first().click();
    await page.waitForSelector("#evenement-detail-modal:not([hidden])", { timeout: 5000 });
    await page.click('[data-action="modifier-evenement"]');
    await page.waitForSelector("#evenement-form", { timeout: 5000 });
    const heurePrefillEdition2 = await heurePreremplie();
    assert.equal(heurePrefillEdition2, "10:00", `apres un enregistrement sans changement, doit toujours pre-remplir 10:00 (aucune derive), affiche="${heurePrefillEdition2}"`);
    await page.click('[data-action="cancel-evenement-form"]');
    await page.waitForTimeout(200);

    console.log("  -> ete (creation 09:00, edition 09:00->10:00, rechargement, editions repetees) : OK");

    // ---------- HIVER : 15/01/2026 09:00 -> doit afficher 09:00 ----------
    await creerRdv("2026-01-15", "09:00", "TEST_HIVER");
    // Navigue jusqu'au bon jour n'est pas necessaire : on relit directement
    // via l'API pour cette assertion (le rendu jour/semaine/mois du DOM pour
    // une autre date est deja couvert par planning-date.test.mjs).
    const planningHiver = await api.get(`/planning?debut=2026-01-15&fin=2026-01-15`, access_token);
    const itemHiver = planningHiver.find((i) => i.titre === "TEST_HIVER");
    assert.ok(itemHiver, "le RDV hiver doit exister");
    assert.match(itemHiver.date, /^2026-01-15T08:00:00(\.000)?Z$/, `09:00 Paris en hiver (CET, UTC+1) doit stocker 08:00 UTC, recu="${itemHiver.date}"`);

    console.log("  -> hiver (15/01/2026 09:00 -> 08:00 UTC stocke correctement) : OK");

    // ---------- PROCHE MINUIT : 23:30 reste le meme jour ----------
    await creerRdv("2026-08-29", "23:30", "TEST_MINUIT_ETE");
    const planningMinuitEte = await api.get(`/planning?debut=2026-08-29&fin=2026-08-30`, access_token);
    const itemMinuitEte = planningMinuitEte.find((i) => i.titre === "TEST_MINUIT_ETE");
    assert.ok(itemMinuitEte, "le RDV 23:30 doit exister");
    assert.match(itemMinuitEte.date, /^2026-08-29T21:30:00(\.000)?Z$/, `23:30 Paris ete doit stocker 21:30 UTC le meme jour, recu="${itemMinuitEte.date}"`);

    // ---------- PROCHE MINUIT hiver : 00:30 reste sur le jour attendu ----------
    await creerRdv("2026-01-15", "00:30", "TEST_MINUIT_HIVER");
    const planningMinuitHiver = await api.get(`/planning?debut=2026-01-14&fin=2026-01-15`, access_token);
    const itemMinuitHiver = planningMinuitHiver.find((i) => i.titre === "TEST_MINUIT_HIVER");
    assert.ok(itemMinuitHiver, "le RDV 00:30 doit exister");
    assert.match(itemMinuitHiver.date, /^2026-01-14T23:30:00(\.000)?Z$/, `00:30 Paris hiver doit stocker 23:30 UTC la veille, recu="${itemMinuitHiver.date}"`);

    console.log("  -> proche minuit (ete 23:30, hiver 00:30) : OK");

    await context.close();
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}
