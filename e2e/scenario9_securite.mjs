// Scenario 9 (cahier des charges V4, section 37 "Securite") :
// changement de mot de passe (proprietaire + membre d'equipe), isolation
// stricte entre entreprises sur un large echantillon d'endpoints, acces
// aux endpoints publics avec un jeton invalide.
import { api, assert, assertEqual, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  // --- Changement de mot de passe : proprietaire ---
  const { token, email } = await creerArtisanTest("scenario9");
  let refuse400 = false;
  try {
    await api.post("/auth/change-password", { current_password: "mauvais-mdp", new_password: "NouveauMotDePasse123" }, token);
  } catch (err) {
    refuse400 = err.message.includes("HTTP 400");
  }
  assert(refuse400, "un mauvais mot de passe actuel doit etre refuse (400, pas 401 - le token reste valide)");
  // Le token doit rester utilisable malgre l'echec (pas de deconnexion forcee).
  const meApresEchec = await api.get("/auth/me", token);
  assert(!!meApresEchec.id, "le token doit rester valide apres un echec de changement de mot de passe");
  logEtape("mauvais mot de passe actuel refuse sans invalider la session");

  await api.post("/auth/change-password", { current_password: "TestPass123!", new_password: "MotDePasseModifie123" }, token);
  let connexionAncienMdp = false;
  try {
    await api.post("/auth/login", { email, password: "TestPass123!" });
    connexionAncienMdp = true;
  } catch (err) { /* attendu */ }
  assert(!connexionAncienMdp, "l'ancien mot de passe ne doit plus fonctionner apres changement");
  const nouvelleConnexion = await api.post("/auth/login", { email, password: "MotDePasseModifie123" });
  assert(!!nouvelleConnexion.access_token, "le nouveau mot de passe doit fonctionner");
  logEtape("changement de mot de passe (proprietaire) verifie de bout en bout");

  // --- Changement de mot de passe : membre d'equipe ---
  await activerAbonnement(email);
  const emailMembre = `membre-scenario9-${Date.now()}@e2e-test.fr`;
  await api.post("/equipe", { nom: "Membre Securite", email: emailMembre, password: "MembrePass123", role: "salarie" }, nouvelleConnexion.access_token);
  const loginMembre = await api.post("/auth/login", { email: emailMembre, password: "MembrePass123" });
  await api.post("/auth/change-password", { current_password: "MembrePass123", new_password: "MembreNouveauMdp123" }, loginMembre.access_token);
  const nouvelleConnexionMembre = await api.post("/auth/login", { email: emailMembre, password: "MembreNouveauMdp123" });
  assert(!!nouvelleConnexionMembre.access_token, "le changement de mot de passe doit fonctionner aussi pour un membre d'equipe");
  logEtape("changement de mot de passe (membre d'equipe) verifie");

  // --- Isolation multi-tenant sur un large echantillon d'endpoints ---
  const proprietaireToken = nouvelleConnexion.access_token;
  const client = await api.post("/clients", { nom: "Client Isolation" }, proprietaireToken);
  const devis = await api.post("/devis", { client_id: client.id, titre: "Devis isolation", taux_tva: 20, lignes: [{ description: "X", quantite: 1, prix_unitaire_ht: 100 }] }, proprietaireToken);
  const facture = await api.post("/factures", { client_id: client.id, type: "standard", taux_tva: 20, lignes: [{ description: "Y", quantite: 1, prix_unitaire_ht: 100 }] }, proprietaireToken);
  const chantier = await api.post("/chantiers", { client_id: client.id, titre: "Chantier isolation" }, proprietaireToken);
  const fournisseur = await api.post("/fournisseurs", { nom: "Fournisseur isolation" }, proprietaireToken);
  const tache = await api.post("/taches", { titre: "Tache isolation" }, proprietaireToken);

  const { token: autreToken, email: autreEmail } = await creerArtisanTest("scenario9-autre");
  await activerAbonnement(autreEmail);

  const cibles = [
    ["GET", `/clients/${client.id}`],
    ["GET", `/devis/${devis.id}`],
    ["GET", `/factures/${facture.id}`],
    ["GET", `/chantiers/${chantier.id}`],
    ["PATCH", `/fournisseurs/${fournisseur.id}`, { nom: "Vole" }],
    ["PATCH", `/taches/${tache.id}`, { titre: "Vole" }],
    ["DELETE", `/clients/${client.id}`],
    ["DELETE", `/devis/${devis.id}`],
    ["DELETE", `/chantiers/${chantier.id}`],
  ];
  for (const [methode, chemin, corps] of cibles) {
    let refuse = false;
    try {
      if (methode === "GET") await api.get(chemin, autreToken);
      else if (methode === "PATCH") await api.patch(chemin, corps, autreToken);
      else if (methode === "DELETE") await api.del(chemin, autreToken);
    } catch (err) {
      refuse = err.message.includes("HTTP 404");
    }
    assert(refuse, `${methode} ${chemin} doit etre invisible/inaccessible pour un autre artisan (404 attendu)`);
  }
  logEtape(`isolation multi-tenant verifiee sur ${cibles.length} endpoints (clients/devis/factures/chantiers/fournisseurs/taches)`);

  // --- Endpoints publics : jeton invalide ---
  let publicRefuse = false;
  try {
    await api.get("/pub/devis/jeton-completement-invalide-qui-nexiste-pas");
  } catch (err) {
    publicRefuse = err.message.includes("HTTP 404");
  }
  assert(publicRefuse, "un jeton public invalide doit etre refuse (404), jamais exposer de donnees");
  logEtape("endpoint public avec jeton invalide correctement refuse");
}
