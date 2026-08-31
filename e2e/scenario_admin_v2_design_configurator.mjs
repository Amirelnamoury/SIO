// Scenario E2E du configurateur admin des sites vitrines V2 (Lot 4).
// Comme scenario_admin_v1.mjs, requiert un compte Admin deja provisionne
// (ADMIN_TEST_EMAIL / ADMIN_TEST_PASSWORD) : non branche dans run_all.mjs
// pour ne pas exiger ces identifiants dans la suite generale (meme
// convention que scenario_admin_v1.mjs, jamais rattache a run_all).
import { api, API_BASE, assert, assertEqual, logEtape } from "./helpers.mjs";
import { pathToFileURL } from "node:url";

const ADMIN_EMAIL = process.env.ADMIN_TEST_EMAIL;
const ADMIN_PASSWORD = process.env.ADMIN_TEST_PASSWORD;

async function raw(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(API_BASE + path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  let data = null;
  try { data = await response.json(); } catch (err) { /* HTML ou reponse vide */ }
  return { response, data };
}

/** Scenario principal (16 etapes) : login -> ouvrir artisan -> ouvrir site ->
 * observer le design actuel -> generer une alternative -> verifier la
 * candidate -> ouvrir sa preview isolee -> verifier le formulaire isole ->
 * revenir a l'Admin -> comparer -> adopter -> verifier le current mis a jour
 * -> verifier la candidate videe -> verifier le site publie inchange ->
 * regenerer la preview courante -> marquer pret sans publication automatique. */
async function scenarioPrincipal() {
  assert(ADMIN_EMAIL && ADMIN_PASSWORD, "ADMIN_TEST_EMAIL et ADMIN_TEST_PASSWORD sont requis pour ce scenario");

  const login = await api.post("/admin/auth/login", { email: ADMIN_EMAIL, password: ADMIN_PASSWORD });
  const adminToken = login.access_token;
  assert(!!adminToken, "1. la connexion admin doit fournir un jeton");

  const inscription = await api.post("/auth/register", {
    email: `lot4-${Date.now()}@e2e-test.fr`,
    password: "TestPass123!",
    nom_entreprise: "Toiture Sud Est",
    metier: "macon",
    telephone: "06 11 22 33 44",
    ville: "Grenoble",
    code_postal: "38000",
  });
  const artisanId = inscription.artisan.id;
  logEtape("2. artisan cree et ouvert cote Admin");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    services: ["Toiture", "Zinguerie", "Isolation"],
    tagline: "Votre toiture, notre expertise",
  }, adminToken);
  const genere = await api.post(`/admin/api/artisans/${artisanId}/site/generate`, undefined, adminToken);
  assertEqual(genere.statut, "genere", "3. le site doit etre genere avant toute configuration de design");
  const currentFamily = genere.design_profile.design_family;
  assert(!!currentFamily, "4. observer le design actuel : une famille doit etre choisie par le moteur");
  logEtape(`4. design actuel observe (famille=${currentFamily})`);

  const candidateResp = await raw(`/admin/api/artisans/${artisanId}/site/design/candidate`, { method: "POST", token: adminToken, body: {} });
  assertEqual(candidateResp.response.status, 200, "5. generer une alternative doit reussir");
  const candidate = candidateResp.data;
  assert(!!candidate.profile.design_family, "6. la candidate doit avoir un design_profile complet");
  logEtape(`6. candidate verifiee (distinct=${candidate.distinct}, famille=${candidate.profile.design_family})`);

  const siteApresGenerate = await api.get(`/admin/api/artisans/${artisanId}/site`, adminToken);
  assertEqual(siteApresGenerate.design_profile.design_family, currentFamily, "le design actuel ne doit JAMAIS bouger avant adoption");
  assert(!!siteApresGenerate.candidate_design_profile, "la candidate doit etre persistee");

  const previewCandidate = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview/candidate`, { headers: { Authorization: `Bearer ${adminToken}` } });
  assertEqual(previewCandidate.status, 200, "7. la preview de l'alternative doit etre accessible a l'admin");
  const htmlCandidate = await previewCandidate.text();
  assert(htmlCandidate.includes(`class="family-${candidate.profile.design_family}`), "la preview candidate doit refleter le design de l'alternative, pas le design actuel");
  assert(htmlCandidate.includes("<form"), "8. la preview isolee doit conserver un vrai formulaire de contact");
  logEtape("7-8. preview candidate isolee et formulaire verifies");

  const avantLead = await api.get(`/admin/api/artisans/${artisanId}`, adminToken);
  const leadCandidate = await raw(`/admin/preview-api/pub/${inscription.artisan.slug}/demande-devis`, {
    method: "POST", token: adminToken, body: { nom: "Prospect candidate", email: "candidate-preview@example.test" },
  });
  assertEqual(leadCandidate.response.status, 200, "le formulaire de la preview candidate doit repondre");
  const apresLead = await api.get(`/admin/api/artisans/${artisanId}`, adminToken);
  assertEqual(apresLead.clients_total, avantLead.clients_total, "la preview candidate ne doit jamais creer de vrai prospect");
  logEtape("9. retour Admin : aucune pollution de prospects via la preview candidate");

  const siteAvantAdopt = await api.get(`/admin/api/artisans/${artisanId}/site`, adminToken);
  const axesDifferents = ["design_family", "header_variant", "hero_variant", "services_variant", "gallery_variant", "about_variant", "reviews_variant", "cta_variant", "footer_variant", "palette", "font_pair", "radius_style", "spacing_style", "image_treatment"]
    .filter((axe) => siteAvantAdopt.design_profile[axe] !== siteAvantAdopt.candidate_design_profile[axe]);
  logEtape(`10. comparaison : ${axesDifferents.length} axe(s) different(s) entre version actuelle et alternative`);

  const adoptResp = await raw(`/admin/api/artisans/${artisanId}/site/design/candidate/adopt`, { method: "POST", token: adminToken });
  assertEqual(adoptResp.response.status, 200, "11. l'adoption doit reussir");
  assertEqual(adoptResp.data.design_profile.design_family, candidate.profile.design_family, "12. le design actuel doit devenir celui de l'alternative apres adoption");
  assertEqual(adoptResp.data.candidate_design_profile, null, "13. la candidate doit etre videe apres adoption");
  logEtape("12-13. design actuel mis a jour et candidate videe apres adoption");

  assertEqual(adoptResp.data.statut, "genere", "14. adopter ne doit jamais publier automatiquement le site (statut reste genere, jamais publie)");
  assert(!adoptResp.data.date_publication, "aucune date de publication ne doit apparaitre suite a une adoption");
  logEtape("14. site public inchange : aucune publication automatique declenchee par l'adoption");

  const previewApresAdopt = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview`, { headers: { Authorization: `Bearer ${adminToken}` } });
  assertEqual(previewApresAdopt.status, 200, "15. la preview courante doit etre regenerable/accessible apres adoption");
  const htmlApresAdopt = await previewApresAdopt.text();
  assert(htmlApresAdopt.includes(`class="family-${candidate.profile.design_family}`), "la preview courante doit refleter le design nouvellement adopte");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, { domaine: "toiture-sud-est.test", url_publique: "https://toiture-sud-est.test" }, adminToken);
  const pret = await api.post(`/admin/api/artisans/${artisanId}/site/ready`, undefined, adminToken);
  assertEqual(pret.statut, "pret", "16. le site doit pouvoir etre marque pret");
  assert(!pret.date_publication, "marquer pret ne doit jamais publier automatiquement le site");
  logEtape("16. site marque pret sans aucune publication automatique");
}

/** Second scenario, plus court : generer -> abandonner -> le design actuel
 * ne doit strictement pas avoir bouge. */
async function scenarioGenererAbandonnerInchange() {
  assert(ADMIN_EMAIL && ADMIN_PASSWORD, "ADMIN_TEST_EMAIL et ADMIN_TEST_PASSWORD sont requis pour ce scenario");
  const login = await api.post("/admin/auth/login", { email: ADMIN_EMAIL, password: ADMIN_PASSWORD });
  const adminToken = login.access_token;

  const inscription = await api.post("/auth/register", {
    email: `lot4-abandon-${Date.now()}@e2e-test.fr`,
    password: "TestPass123!",
    nom_entreprise: "Peinture Precision",
    metier: "peintre",
    telephone: "06 22 33 44 55",
    ville: "Nantes",
    code_postal: "44000",
  });
  const artisanId = inscription.artisan.id;
  await api.patch(`/admin/api/artisans/${artisanId}/site`, { services: ["Peinture interieure", "Ravalement"] }, adminToken);
  const genere = await api.post(`/admin/api/artisans/${artisanId}/site/generate`, undefined, adminToken);
  const profilAvant = genere.design_profile;

  const candidateResp = await raw(`/admin/api/artisans/${artisanId}/site/design/candidate`, { method: "POST", token: adminToken, body: {} });
  assertEqual(candidateResp.response.status, 200, "generer une alternative doit reussir");

  const abandonResp = await raw(`/admin/api/artisans/${artisanId}/site/design/candidate`, { method: "DELETE", token: adminToken });
  assertEqual(abandonResp.response.status, 200, "abandonner doit reussir");
  assertEqual(abandonResp.data.candidate_design_profile, null, "la candidate doit disparaitre apres abandon");
  assertEqual(JSON.stringify(abandonResp.data.design_profile), JSON.stringify(profilAvant), "le design actuel doit rester rigoureusement identique apres un abandon");

  const previewCandidateApresAbandon = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview/candidate`, { headers: { Authorization: `Bearer ${adminToken}` } });
  assertEqual(previewCandidateApresAbandon.status, 404, "la preview de l'alternative abandonnee ne doit plus etre servie");
  logEtape("generer -> abandonner -> design actuel strictement inchange, preview candidate invalidee");
}

export default async function run() {
  await scenarioPrincipal();
  await scenarioGenererAbandonnerInchange();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().then(() => console.log("OK : Admin V2 - configurateur de design")).catch((err) => { console.error(err.message); process.exit(1); });
}
