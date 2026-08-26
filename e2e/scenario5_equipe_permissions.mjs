// Scenario 5 (cahier des charges V3, section 39) :
// equipe -> invitation -> attribution -> permission -> acces limite
import { api, assert, assertEqual, creerArtisanTest, activerAbonnement, emailUnique, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token: tokenProprietaire, email } = await creerArtisanTest("scenario5");
  await activerAbonnement(email);

  // Un client existe deja avant l'arrivee du salarie : les donnees restent
  // scopees sur l'ENTREPRISE (artisan_id), pas sur le membre qui les cree.
  const clientExistant = await api.post("/clients", { nom: "Client Existant" }, tokenProprietaire);

  // Invitation d'un salarie.
  const emailSalarie = emailUnique("salarie-scenario5");
  const membre = await api.post("/equipe", { nom: "Salarie Test", email: emailSalarie, password: "SalariePass123!", role: "salarie" }, tokenProprietaire);
  assertEqual(membre.role, "salarie", "le membre cree doit avoir le role demande");
  logEtape("salarie invite dans l'equipe");

  // Connexion en tant que salarie.
  const loginSalarie = await api.post("/auth/login", { email: emailSalarie, password: "SalariePass123!" });
  const tokenSalarie = loginSalarie.access_token;
  assert(!!tokenSalarie, "le salarie doit pouvoir se connecter avec ses propres identifiants");
  logEtape("salarie connecte avec son propre compte");

  // Attribution : les donnees de l'entreprise (creees par le proprietaire)
  // restent visibles par le salarie - c'est une seule entreprise partagee.
  const clientsVusParSalarie = await api.get("/clients", tokenSalarie);
  assert(clientsVusParSalarie.some((c) => c.id === clientExistant.id), "le salarie doit voir les clients de l'entreprise, pas seulement les siens");
  logEtape("acces partage aux donnees de l'entreprise verifie");

  // Le salarie peut travailler normalement (creer un client).
  const clientCreeParSalarie = await api.post("/clients", { nom: "Client cree par le salarie" }, tokenSalarie);
  assert(!!clientCreeParSalarie.id, "le salarie doit pouvoir creer des donnees pour l'entreprise");
  const vuParProprietaire = await api.get("/clients", tokenProprietaire);
  assert(vuParProprietaire.some((c) => c.id === clientCreeParSalarie.id), "les donnees creees par le salarie doivent etre visibles par le proprietaire (meme entreprise)");
  logEtape("donnees creees par le salarie visibles par le proprietaire");

  // Permission / acces limite : un salarie NE PEUT PAS gerer l'equipe.
  let accesRefuse = false;
  try {
    await api.post("/equipe", { nom: "Autre", email: emailUnique("intrus"), password: "Pass123456!", role: "salarie" }, tokenSalarie);
  } catch (err) {
    accesRefuse = err.message.includes("HTTP 403");
  }
  assert(accesRefuse, "un salarie ne doit jamais pouvoir gerer l'equipe (403 attendu)");
  logEtape("acces limite verifie : le salarie ne peut pas gerer l'equipe (403)");

  // Un administrateur (role eleve), lui, le peut.
  const emailAdmin = emailUnique("admin-scenario5");
  const membreAdmin = await api.post("/equipe", { nom: "Admin Test", email: emailAdmin, password: "AdminPass123!", role: "administrateur" }, tokenProprietaire);
  const loginAdmin = await api.post("/auth/login", { email: emailAdmin, password: "AdminPass123!" });
  const membreCreeParAdmin = await api.post("/equipe", { nom: "Cree par admin", email: emailUnique("par-admin"), password: "Pass123456!", role: "salarie" }, loginAdmin.access_token);
  assert(!!membreCreeParAdmin.id, "un administrateur doit pouvoir gerer l'equipe");
  logEtape("permission verifiee : un administrateur peut gerer l'equipe");
}
