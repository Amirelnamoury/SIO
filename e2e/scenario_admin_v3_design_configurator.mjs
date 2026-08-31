// Parcours E2E reel du configurateur Admin pour le moteur Site Vitrine V3.
// Requiert ADMIN_TEST_EMAIL / ADMIN_TEST_PASSWORD et un backend dedie.
import { api, API_BASE, assert, assertEqual, logEtape } from "./helpers.mjs";
import { pathToFileURL } from "node:url";

const ADMIN_EMAIL = process.env.ADMIN_TEST_EMAIL;
const ADMIN_PASSWORD = process.env.ADMIN_TEST_PASSWORD;

async function raw(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(API_BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await response.json(); } catch (error) { /* HTML ou reponse vide */ }
  return { response, data };
}

async function run() {
  assert(ADMIN_EMAIL && ADMIN_PASSWORD, "ADMIN_TEST_EMAIL et ADMIN_TEST_PASSWORD sont requis");
  const login = await api.post("/admin/auth/login", { email: ADMIN_EMAIL, password: ADMIN_PASSWORD });
  const adminToken = login.access_token;
  assert(!!adminToken, "la connexion Admin doit fournir un jeton");

  const inscription = await api.post("/auth/register", {
    email: `site-v3-${Date.now()}@e2e-test.fr`,
    password: "TestPass123!",
    nom_entreprise: "Atelier Trait Franc",
    nom_artisan: "Camille Test",
    metier: "menuisier",
    telephone: "06 10 20 30 40",
    ville: "Lyon",
    code_postal: "69002",
  });
  const artisanId = inscription.artisan.id;
  const slug = inscription.artisan.slug;
  logEtape("artisan ouvert dans le flux Admin");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    tagline: "Agencements en bois concus pour durer",
    services: ["Agencement interieur", "Mobilier sur mesure", "Pose de menuiseries"],
  }, adminToken);
  const current = await api.post(`/admin/api/artisans/${artisanId}/site/generate`, undefined, adminToken);
  assertEqual(current.design_profile.design_engine_version, "v3.0", "un nouveau site doit utiliser V3");
  assertEqual(current.statut, "genere", "la preview actuelle doit etre generee");

  const direction = current.design_profile.art_direction === "warm_craft" ? "technical_spatial" : "warm_craft";
  const saved = await api.patch(`/admin/api/artisans/${artisanId}/site/design/preferences`, {
    engine_version: "v3",
    preferred_direction: direction,
    ambience: "warm",
    density: "balanced",
  }, adminToken);
  assertEqual(saved.design_preferences.preferred_direction, direction, "la direction choisie doit etre enregistree");
  logEtape(`direction ${direction} choisie et enregistree`);

  const candidateOne = await api.post(`/admin/api/artisans/${artisanId}/site/design/candidate`, {
    engine_version: "v3",
    preferred_direction: direction,
    ambience: "warm",
    density: "balanced",
  }, adminToken);
  assertEqual(candidateOne.profile.art_direction, direction, "la candidate doit respecter la direction choisie");
  assert(candidateOne.profile.design_signature !== current.design_profile.design_signature, "la candidate doit differer du design actuel");

  const candidatePreview = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview/candidate`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  assertEqual(candidatePreview.status, 200, "la preview candidate doit etre accessible");
  const candidateHtml = await candidatePreview.text();
  assert(candidateHtml.includes(`direction-${direction}`), "la preview doit refleter la direction candidate");
  assert(candidateHtml.includes('var API_BASE = "/admin/preview-api"'), "le formulaire candidate doit rester isole");
  const sink = await raw(`/admin/preview-api/pub/${slug}/demande-devis`, {
    method: "POST", token: adminToken, body: { nom: "Visiteur preview", email: "preview@example.test" },
  });
  assertEqual(sink.response.status, 200, "le formulaire de preview doit utiliser le sink Admin");
  logEtape("candidate et formulaire de preview isole verifies");

  const abandoned = await api.del(`/admin/api/artisans/${artisanId}/site/design/candidate`, adminToken);
  assertEqual(abandoned.candidate_design_profile, null, "abandonner doit supprimer la candidate");
  assertEqual(abandoned.design_profile.design_signature, current.design_profile.design_signature, "abandonner ne doit pas changer le design actuel");

  const secondDirection = direction === "technical_spatial" ? "editorial_luxury" : "technical_spatial";
  const candidateTwo = await api.post(`/admin/api/artisans/${artisanId}/site/design/candidate`, {
    engine_version: "v3",
    preferred_direction: secondDirection,
    ambience: "material",
    density: "airy",
  }, adminToken);
  assertEqual(candidateTwo.profile.art_direction, secondDirection, "la nouvelle candidate doit respecter la nouvelle direction");
  assert(candidateTwo.profile.design_signature !== candidateOne.profile.design_signature, "la nouvelle candidate ne doit pas repeter la precedente");

  const adopted = await api.post(`/admin/api/artisans/${artisanId}/site/design/candidate/adopt`, undefined, adminToken);
  assertEqual(adopted.design_profile.design_signature, candidateTwo.profile.design_signature, "adopter doit promouvoir la candidate");
  assertEqual(adopted.candidate_design_profile, null, "la candidate doit etre videe apres adoption");
  assertEqual(adopted.statut, "genere", "adopter ne doit jamais publier automatiquement");
  assertEqual(adopted.date_publication, null, "adopter ne doit pas creer de date de publication");

  const currentPreview = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  assertEqual(currentPreview.status, 200, "la preview actuelle doit rester accessible apres adoption");
  const currentHtml = await currentPreview.text();
  assert(currentHtml.includes(`direction-${secondDirection}`), "la preview actuelle doit utiliser le design adopte");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    domaine: "atelier-trait-franc.test",
    url_publique: "https://atelier-trait-franc.test",
  }, adminToken);
  const ready = await api.post(`/admin/api/artisans/${artisanId}/site/ready`, undefined, adminToken);
  assertEqual(ready.statut, "pret", "le site doit pouvoir etre marque pret");
  assertEqual(ready.date_publication, null, "ready ne doit jamais publier automatiquement");
  logEtape("abandon, nouvelle candidate, adoption, preview actuelle et ready valides sans publication");
}

export default run;

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().then(() => console.log("OK : Admin V3 - parcours configurateur complet")).catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
