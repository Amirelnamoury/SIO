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
  const document = await api.post("/documents", { nom: "Document isolation", type: "autre", url: "https://x.test/d.pdf", client_id: client.id }, proprietaireToken);

  const { token: autreToken, email: autreEmail } = await creerArtisanTest("scenario9-autre");
  await activerAbonnement(autreEmail);

  const cibles = [
    ["GET", `/clients/${client.id}`],
    ["GET", `/devis/${devis.id}`],
    ["GET", `/factures/${facture.id}`],
    ["GET", `/chantiers/${chantier.id}`],
    ["GET", `/documents/${document.id}/fichier`],
    ["PATCH", `/fournisseurs/${fournisseur.id}`, { nom: "Vole" }],
    ["PATCH", `/taches/${tache.id}`, { titre: "Vole" }],
    ["DELETE", `/clients/${client.id}`],
    ["DELETE", `/devis/${devis.id}`],
    ["DELETE", `/chantiers/${chantier.id}`],
    ["DELETE", `/documents/${document.id}`],
    ["POST", `/documents/${document.id}/restaurer`],
  ];
  for (const [methode, chemin, corps] of cibles) {
    let refuse = false;
    try {
      if (methode === "GET") await api.get(chemin, autreToken);
      else if (methode === "PATCH") await api.patch(chemin, corps, autreToken);
      else if (methode === "DELETE") await api.del(chemin, autreToken);
      else if (methode === "POST") await api.post(chemin, corps, autreToken);
    } catch (err) {
      refuse = err.message.includes("HTTP 404");
    }
    assert(refuse, `${methode} ${chemin} doit etre invisible/inaccessible pour un autre artisan (404 attendu)`);
  }
  logEtape(`isolation multi-tenant verifiee sur ${cibles.length} endpoints (clients/devis/factures/chantiers/fournisseurs/taches/documents)`);

  // --- Injection cross-tenant a la creation : un artisan ne doit jamais
  // pouvoir rattacher un document qu'il cree a un client/chantier/devis/
  // facture d'un AUTRE artisan (trouve en auditant creer_document/
  // uploader_document, qui ne validaient aucune des references fournies -
  // un document ainsi injecte apparaissait dans le portail client ou la
  // galerie photo du chantier de l'artisan victime). ---
  let injectionRefusee = false;
  try {
    await api.post("/documents", { nom: "Document injecte", type: "autre", url: "https://evil.test/x.pdf", client_id: client.id }, autreToken);
  } catch (err) {
    injectionRefusee = err.message.includes("HTTP 404");
  }
  assert(injectionRefusee, "creer un document rattache au client_id d'un AUTRE artisan doit etre refuse (404)");
  logEtape("injection cross-tenant a la creation de document (client_id d'un autre artisan) correctement refusee");

  // Meme classe de bug trouvee dans taches.py et planning.py : une tache ou
  // un evenement rattache au chantier d'un autre artisan apparaissait dans
  // SON tableau de bord chantier (Chantier.taches n'est jamais filtre par
  // artisan_id, un chantier n'ayant par construction qu'un seul proprietaire).
  let tacheInjecteeRefusee = false;
  try {
    await api.post("/taches", { titre: "Tache injectee", chantier_id: chantier.id }, autreToken);
  } catch (err) {
    tacheInjecteeRefusee = err.message.includes("HTTP 404");
  }
  assert(tacheInjecteeRefusee, "creer une tache rattachee au chantier_id d'un AUTRE artisan doit etre refuse (404)");

  let evenementInjecteRefuse = false;
  try {
    await api.post("/evenements", { titre: "RDV injecte", date_debut: "2026-09-01T10:00:00Z", chantier_id: chantier.id }, autreToken);
  } catch (err) {
    evenementInjecteRefuse = err.message.includes("HTTP 404");
  }
  assert(evenementInjecteRefuse, "creer un evenement rattache au chantier_id d'un AUTRE artisan doit etre refuse (404)");
  logEtape("injection cross-tenant a la creation de tache/evenement (chantier_id d'un autre artisan) correctement refusee");

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
