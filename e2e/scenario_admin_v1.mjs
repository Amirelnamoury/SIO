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
  try { data = await response.json(); } catch (err) { /* HTML ou reponse vide */ }
  return { response, data };
}

export default async function run() {
  assert(ADMIN_EMAIL && ADMIN_PASSWORD, "ADMIN_TEST_EMAIL et ADMIN_TEST_PASSWORD sont requis pour le scenario Admin V1");

  const inscription = await api.post("/auth/register", {
    email: `dupont-admin-${Date.now()}@e2e-test.fr`,
    password: "TestPass123!",
    nom_entreprise: "Dupont Plomberie",
    metier: "plombier",
    telephone: "06 10 20 30 40",
    ville: "Lyon",
    code_postal: "69003",
    siret: "123 456 789 00012",
    assurance_decennale_nom: "AXA BTP",
  });
  const artisanToken = inscription.access_token;
  const artisanId = inscription.artisan.id;

  const artisanPage = await raw("/admin", { token: artisanToken });
  assertEqual(artisanPage.response.status, 403, "un artisan normal doit etre refuse sur /admin");
  const artisanDashboard = await raw("/admin/api/dashboard", { token: artisanToken });
  assertEqual(artisanDashboard.response.status, 403, "un artisan normal doit etre refuse sur les endpoints admin");
  const artisanGenerate = await raw(`/admin/api/artisans/${artisanId}/site/generate`, { method: "POST", token: artisanToken });
  assertEqual(artisanGenerate.response.status, 403, "un artisan ne doit pas pouvoir generer son site");
  const artisanUpdateSite = await raw(`/admin/api/artisans/${artisanId}/site`, { method: "PATCH", token: artisanToken, body: { tagline: "Interdit" } });
  assertEqual(artisanUpdateSite.response.status, 403, "un artisan ne doit pas pouvoir modifier SiteVitrine");
  const artisanPreview = await raw(`/admin/api/artisans/${artisanId}/site/preview`, { token: artisanToken });
  assertEqual(artisanPreview.response.status, 403, "un artisan ne doit pas pouvoir voir une preview admin");
  logEtape("artisan normal refuse sur page, API, generation, modification et preview admin");

  const login = await api.post("/admin/auth/login", { email: ADMIN_EMAIL, password: ADMIN_PASSWORD });
  const adminToken = login.access_token;
  assert(!!adminToken, "la connexion admin doit fournir un jeton dedie");
  const adminPage = await fetch(API_BASE + "/admin", { headers: { Authorization: `Bearer ${adminToken}` } });
  assertEqual(adminPage.status, 200, "un admin doit acceder a /admin");
  assert((await adminPage.text()).includes("ADMIN SUITE ARTISAN"), "la page admin doit avoir une identite distincte");
  logEtape("connexion admin et acces a l'espace separe verifies");

  const invalidId = await raw("/admin/api/artisans/999999999", { token: adminToken });
  assertEqual(invalidId.response.status, 404, "un identifiant artisan invalide doit etre refuse");
  const traversalRoute = await raw("/admin/api/artisans/%2e%2e%2fetc%2fpasswd/site/preview", { token: adminToken });
  assert([404, 422].includes(traversalRoute.response.status), "un chemin de traversal doit etre refuse par le routage");

  const detailInitial = await api.get(`/admin/api/artisans/${artisanId}`, adminToken);
  assertEqual(detailInitial.plan, "gratuit", "un nouvel artisan doit rester au plan Gratuit avant la generation de son site");
  assertEqual(detailInitial.site.statut, "non_cree", "un nouvel artisan ne doit pas avoir de faux site");
  assert(detailInitial.site.config.services.length > 0, "les prestations du metier doivent etre pre-remplies");

  await api.patch(`/admin/api/artisans/${artisanId}`, {
    nom_entreprise: "Dupont Plomberie & Fils",
    metier: "plombier",
    email: inscription.artisan.email,
    telephone: "06 10 20 30 40",
    ville: "Villeurbanne",
    code_postal: "69100",
    adresse: "12 rue des Artisans",
    siret: "123 456 789 00012",
    assurance_decennale_nom: "AXA BTP",
  }, adminToken);

  const tentativeStorage = await raw(`/admin/api/artisans/${artisanId}/site`, {
    method: "PATCH",
    token: adminToken,
    body: { storage_key: "../../etc/passwd" },
  });
  assertEqual(tentativeStorage.response.status, 422, "storage_key doit etre controle par le serveur et jamais modifiable via l'API");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    tagline: "Votre plombier de confiance a Villeurbanne",
    services: ["Depannage fuite express", "Renovation de salle de bain"],
    stats: [{ valeur: "12 ans", label: "d'experience" }],
  }, adminToken);
  const genere = await api.post(`/admin/api/artisans/${artisanId}/site/generate`, undefined, adminToken);
  assertEqual(genere.statut, "genere", "la generation doit faire passer le site a genere");
  assertEqual(genere.storage_key, `admin-site-previews/${artisanId}/index.html`, "la cle preview doit etre serveur et deterministe");
  logEtape("Site Vitrine genere pour un artisan au plan Gratuit");

  const preview = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview`, { headers: { Authorization: `Bearer ${adminToken}` } });
  assertEqual(preview.status, 200, "la preview admin doit etre accessible a l'admin");
  const html = await preview.text();
  for (const attendu of [
    "Dupont Plomberie &amp; Fils",
    "Plombier",
    "Villeurbanne",
    "06 10 20 30 40",
    inscription.artisan.slug,
    "/admin/preview-api",
    "Depannage fuite express",
    "Renovation de salle de bain",
  ]) {
    assert(html.includes(attendu), `le HTML genere doit contenir ${attendu}`);
  }

  const detailAvantFormulaire = await api.get(`/admin/api/artisans/${artisanId}`, adminToken);
  const previewLead = await raw(`/admin/preview-api/pub/${inscription.artisan.slug}/demande-devis`, {
    method: "POST",
    token: adminToken,
    body: { nom: "Prospect preview", email: "preview@example.test" },
  });
  assertEqual(previewLead.response.status, 200, "le formulaire de preview doit repondre sans polluer la production");
  const detailApresFormulaire = await api.get(`/admin/api/artisans/${artisanId}`, adminToken);
  assertEqual(detailApresFormulaire.clients_total, detailAvantFormulaire.clients_total, "la preview ne doit creer aucun prospect reel");
  logEtape("generation reelle, contenu HTML et neutralisation des prospects preview verifies");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    tagline: "Nouvelle version controlee",
    services: ["Depannage fuite express", "Renovation complete"],
    stats: [],
  }, adminToken);
  const regenere = await api.post(`/admin/api/artisans/${artisanId}/site/generate`, undefined, adminToken);
  assertEqual(regenere.storage_key, genere.storage_key, "la regeneration doit ecraser la meme preview");
  const previewRegeneree = await fetch(API_BASE + `/admin/api/artisans/${artisanId}/site/preview`, { headers: { Authorization: `Bearer ${adminToken}` } });
  const htmlRegenere = await previewRegeneree.text();
  assert(htmlRegenere.includes("Nouvelle version controlee"), "la nouvelle preview doit contenir les modifications");
  assert(!htmlRegenere.includes("Votre plombier de confiance a Villeurbanne"), "l'ancienne preview doit etre remplacee");

  await api.patch(`/admin/api/artisans/${artisanId}/site`, {
    domaine: "dupont-plomberie.test",
    url_publique: "https://dupont-plomberie.test",
  }, adminToken);
  const pret = await api.post(`/admin/api/artisans/${artisanId}/site/ready`, undefined, adminToken);
  assertEqual(pret.statut, "pret", "le site genere doit pouvoir etre marque pret");
  const publie = await api.post(`/admin/api/artisans/${artisanId}/site/publish`, undefined, adminToken);
  assertEqual(publie.statut, "publie", "le site pret avec domaine et URL doit pouvoir etre marque publie");
  assert(!!publie.date_publication, "la date de publication doit etre tracee");

  const sites = await api.get("/admin/api/sites?q=Dupont", adminToken);
  assert(sites.items.some((item) => item.id === artisanId && item.site_statut === "publie"), "le site publie doit apparaitre dans la liste admin");
  const sitesParDomaine = await api.get("/admin/api/sites?q=dupont-plomberie.test", adminToken);
  assert(sitesParDomaine.items.some((item) => item.id === artisanId), "la recherche Sites doit trouver un site par son domaine");
  const dashboard = await api.get("/admin/api/dashboard", adminToken);
  assert(dashboard.sites_publies >= 1, "le dashboard doit compter le site publie");
  logEtape("workflow complet Artisans -> config -> generation -> regeneration -> pret -> publie verifie");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().then(() => console.log("OK : Admin V1")).catch((err) => { console.error(err.message); process.exit(1); });
}
