// Scenario 10 (cahier des charges V4, section 39 "E2E 7 - Portail") :
// generation du lien -> acces -> devis/facture visibles -> messagerie
// bidirectionnelle -> revocation par regeneration du jeton.
import { api, API_BASE, assert, assertEqual, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario10");
  await activerAbonnement(email);

  const client = await api.post("/clients", { nom: "Client Portail" }, token);
  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Devis portail", taux_tva: 20,
    lignes: [{ description: "Travaux", quantite: 1, prix_unitaire_ht: 1000 }],
  }, token);
  await api.patch(`/devis/${devis.id}`, { statut: "signe" }, token);
  const facture = await api.post(`/factures/depuis-devis/${devis.id}?type=standard`, undefined, token);
  // Le portail n'affiche jamais une facture encore en brouillon (pas
  // envoyee au client) - on l'envoie pour refleter un usage reel.
  await api.patch(`/factures/${facture.id}`, { statut: "envoyee" }, token);
  const chantier = await api.post(`/chantiers`, { client_id: client.id, titre: "Chantier portail" }, token);

  const contenuPhoto = `photo-portail-${Date.now()}`;
  const formulairePhoto = new FormData();
  formulairePhoto.append("file", new Blob([contenuPhoto], { type: "image/jpeg" }), "chantier-portail.jpg");
  formulairePhoto.append("type", "photo");
  formulairePhoto.append("chantier_id", String(chantier.id));
  const uploadPhoto = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formulairePhoto,
  });
  assertEqual(uploadPhoto.status, 201, "l'upload d'une photo de chantier doit reussir");
  const photo = await uploadPhoto.json();

  // --- Invitation : generer le lien du portail ---
  const portailToken = await api.post(`/clients/${client.id}/portail/generer`, {}, token);
  assert(!!portailToken.token_portail, "un jeton de portail doit etre genere");
  logEtape("lien du portail client genere");

  // --- Acces : le client ouvre son espace avec le jeton (public, sans compte) ---
  const espace = await api.get(`/pub/portail/${portailToken.token_portail}`);
  assertEqual(espace.client_nom, "Client Portail", "l'espace doit afficher les infos du bon client");
  // PortailDevisOut/PortailFactureOut n'exposent jamais l'id interne (voir
  // public.py) : uniquement des champs surs (numero, titre, statut...) -
  // on retrouve donc les entrees par numero, pas par id.
  assert(espace.devis.some((d) => d.numero === devis.numero), "le devis doit etre visible dans le portail");
  assert(espace.factures.some((f) => f.numero === facture.numero), "la facture doit etre visible dans le portail");
  assert(espace.chantiers.length === 1, "le chantier doit etre visible dans le portail");
  assert(espace.chantiers[0].photos.some((p) => p.id === photo.id), "la photo du chantier doit etre visible dans le portail");
  const photoPublique = await fetch(`${API_BASE}/pub/portail/${portailToken.token_portail}/photos/${photo.id}`);
  assertEqual(photoPublique.status, 200, "la photo du chantier doit etre servie depuis le stockage securise");
  assertEqual(await photoPublique.text(), contenuPhoto, "le portail doit renvoyer le contenu exact de la photo uploadee");
  logEtape("acces au portail : devis, facture et chantier tous visibles");

  // --- Fuite de donnees (V5 section 17) : le portail ne doit JAMAIS exposer
  // les infos internes (budget, marge, notes privees) ni les donnees d'un
  // autre client. Verifie sur le JSON brut, pas juste sur le schema. ---
  const chantierId = (await api.get("/chantiers", token)).find((c) => c.titre === "Chantier portail").id;
  await api.patch(`/chantiers/${chantierId}`, { budget: 20000 }, token);
  await api.post(`/chantiers/${chantierId}/depenses`, { libelle: "Materiaux secret ultra confidentiel", montant: 5000, date_depense: "2026-08-20" }, token);
  await api.patch(`/clients/${client.id}`, { notes: "NOTE PRIVEE ARTISAN : ne jamais montrer au client" }, token);
  const autreClient = await api.post("/clients", { nom: "Client Portail Autre Personne" }, token);

  const espaceApresDonneesInternes = await api.get(`/pub/portail/${portailToken.token_portail}`);
  const brut = JSON.stringify(espaceApresDonneesInternes).toLowerCase();
  for (const termeInterdit of ["budget", "materiaux secret", "note privee", "20000", "5000", "client portail autre personne"]) {
    assert(!brut.includes(termeInterdit.toLowerCase()), `le portail ne doit jamais exposer "${termeInterdit}" (budget/depenses/notes internes/autre client)`);
  }
  logEtape("aucune fuite de donnees internes (budget, depenses, notes privees, autre client) verifiee sur la reponse brute");

  // --- Messagerie : le client ecrit, l'artisan voit et repond ---
  await api.post(`/pub/portail/${portailToken.token_portail}/messages`, { texte: "Bonjour, une question sur le chantier." });
  const messagesVusParArtisan = await api.get(`/clients/${client.id}/messages`, token);
  assert(messagesVusParArtisan.some((m) => m.texte === "Bonjour, une question sur le chantier." && m.expediteur === "client"), "le message du client doit etre visible cote artisan");
  logEtape("message du client recu cote artisan");

  await api.post(`/clients/${client.id}/messages`, { texte: "Bonjour, je reviens vers vous rapidement." }, token);
  const espaceApresReponse = await api.get(`/pub/portail/${portailToken.token_portail}`);
  assert(espaceApresReponse.messages.some((m) => m.texte === "Bonjour, je reviens vers vous rapidement." && m.expediteur === "artisan"), "la reponse de l'artisan doit apparaitre dans le portail du client");
  logEtape("reponse de l'artisan visible cote client (messagerie bidirectionnelle verifiee)");

  // --- Isolation : un jeton invalide ne doit jamais rien exposer ---
  let refuseJetonInvalide = false;
  try {
    await api.get("/pub/portail/jeton-invalide-xyz");
  } catch (err) {
    refuseJetonInvalide = err.message.includes("HTTP 404");
  }
  assert(refuseJetonInvalide, "un jeton de portail invalide doit etre refuse (404)");

  // --- Revocation : regenerer le jeton invalide l'ancien immediatement ---
  const nouveauToken = await api.post(`/clients/${client.id}/portail/generer`, {}, token);
  assert(nouveauToken.token_portail !== portailToken.token_portail, "regenerer doit produire un nouveau jeton");
  let ancienJetonRefuse = false;
  try {
    await api.get(`/pub/portail/${portailToken.token_portail}`);
  } catch (err) {
    ancienJetonRefuse = err.message.includes("HTTP 404");
  }
  assert(ancienJetonRefuse, "l'ancien jeton doit etre revoque immediatement apres regeneration");
  const espaceAvecNouveauJeton = await api.get(`/pub/portail/${nouveauToken.token_portail}`);
  assertEqual(espaceAvecNouveauJeton.client_nom, "Client Portail", "le nouveau jeton doit donner acces normalement");
  logEtape("regeneration du jeton = revocation immediate de l'ancien lien, nouveau lien fonctionnel");
}
