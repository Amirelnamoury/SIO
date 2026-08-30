// Scenario 12 (cahier des charges V5, section 8) :
// matrice fonctionnalite x plan - verifie que le backend applique
// exactement les frontieres annoncees sur la page de tarifs (pricing.js) :
// devis/clients/documents toujours libres ; chantiers/factures/conformite/
// statistiques et relances manuelles a partir d'Essentiel ; contrats
// recurrents et automatisations a partir de Pro ; equipe a partir de Business. Trouve en auditant le code
// reel : les factures n'etaient gated nulle part (ni backend ni frontend),
// alors que la page de tarifs les presente comme la fonctionnalite phare du
// plan Essentiel - corrige dans le meme commit que ce scenario.
import { activerAbonnement, api, assert, creerArtisanTest, logEtape } from "./helpers.mjs";

async function attendu402(promesse, message) {
  try {
    await promesse;
    throw new Error(`ASSERTION ECHOUEE : ${message} (aucune erreur levee)`);
  } catch (err) {
    assert(err.message.includes("HTTP 402"), `${message} (recu : ${err.message})`);
  }
}

export default async function run() {
  // ---------- Plan Gratuit : devis/clients/documents libres, le reste bloque ----------
  const { token: tokenGratuit } = await creerArtisanTest("scenario12-gratuit");
  const client = await api.post("/clients", { nom: "Client Gratuit" }, tokenGratuit);
  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Devis gratuit", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenGratuit);
  assert(!!devis.id, "creer un devis doit rester possible sans abonnement (porte d'entree du produit)");
  await api.post("/documents", { nom: "Doc gratuit", type: "autre", url: "https://x.test/d.pdf", client_id: client.id }, tokenGratuit);
  logEtape("plan Gratuit : clients/devis/documents accessibles sans abonnement");

  await attendu402(api.get("/chantiers", tokenGratuit), "les chantiers doivent etre reserves aux abonnes (Essentiel+)");
  await attendu402(api.get("/factures", tokenGratuit), "les factures doivent etre reservees aux abonnes (Essentiel+)");
  await attendu402(api.get("/conformite", tokenGratuit), "la conformite doit etre reservee aux abonnes (Essentiel+)");
  await attendu402(api.get("/analytics", tokenGratuit), "les statistiques doivent etre reservees aux abonnes (Essentiel+)");
  await attendu402(api.get("/contrats", tokenGratuit), "les contrats recurrents doivent etre reserves au plan Pro");
  await attendu402(api.post(`/devis/${devis.id}/relancer`, undefined, tokenGratuit), "la relance manuelle de devis doit etre reservee au plan Essentiel+");
  await attendu402(api.get("/equipe", tokenGratuit), "la lecture de l'equipe doit etre reservee au plan Business");
  await attendu402(api.post("/equipe", { nom: "Test Membre", email: "x@test.fr", password: "TestPass123!" }, tokenGratuit), "la gestion d'equipe doit etre reservee au plan Business");
  logEtape("plan Gratuit : chantiers/factures/conformite/statistiques/contrats/relance-devis/equipe tous bloques (402)");

  // ---------- Plan Essentiel : chantiers/factures/conformite/statistiques debloques, Pro/Business toujours bloques ----------
  const { token: tokenEssentiel, email: emailEssentiel } = await creerArtisanTest("scenario12-essentiel");
  await activerAbonnement(emailEssentiel, "essentiel");

  const clientE = await api.post("/clients", { nom: "Client Essentiel" }, tokenEssentiel);
  const chantierE = await api.post("/chantiers", { client_id: clientE.id, titre: "Chantier essentiel" }, tokenEssentiel);
  assert(!!chantierE.id, "un abonne Essentiel doit pouvoir creer un chantier");
  const factureE = await api.post("/factures", {
    client_id: clientE.id, titre: "Facture essentiel", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenEssentiel);
  assert(!!factureE.id, "un abonne Essentiel doit pouvoir creer une facture");
  await api.patch(`/factures/${factureE.id}`, { statut: "envoyee" }, tokenEssentiel);
  const factureRelancee = await api.post(`/factures/${factureE.id}/relancer`, undefined, tokenEssentiel);
  assert(factureRelancee.nb_relances === 1, "un abonne Essentiel doit pouvoir relancer manuellement une facture");
  const facturePayee = await api.post(`/factures/${factureE.id}/paiements`, {
    montant: 10, date_paiement: new Date().toISOString().slice(0, 10), moyen: "virement",
  }, tokenEssentiel);
  assert(facturePayee.montant_paye === 10, "un abonne Essentiel doit pouvoir enregistrer un paiement");

  const analytics = await api.get("/analytics", tokenEssentiel);
  assert(Array.isArray(analytics.ca_par_mois), "un abonne Essentiel doit acceder aux analytics");
  const expiration = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  const conformite = await api.post("/conformite", {
    type: "assurance_decennale", libelle: "Assurance E2E Essentiel", date_expiration: expiration,
  }, tokenEssentiel);
  assert(!!conformite.id, "un abonne Essentiel doit pouvoir enregistrer sa conformite");
  const alertes = await api.get("/conformite/alertes", tokenEssentiel);
  assert(alertes.some((item) => item.id === conformite.id), "un abonne Essentiel doit voir ses alertes de conformite");
  logEtape("plan Essentiel : factures, relance facture manuelle, chantiers, analytics et conformite debloques");

  await attendu402(api.get("/contrats", tokenEssentiel), "les contrats recurrents doivent rester reserves au plan Pro pour un abonne Essentiel");
  const devisE = await api.post("/devis", {
    client_id: clientE.id, titre: "Devis essentiel", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenEssentiel);
  await api.post(`/devis/${devisE.id}/envoyer`, undefined, tokenEssentiel);
  const relanceEssentiel = await api.post(`/devis/${devisE.id}/relancer`, undefined, tokenEssentiel);
  assert(!!relanceEssentiel.id, "un abonne Essentiel doit pouvoir relancer manuellement un devis");
  assert(["envoye", "non_configure", "echec", "sans_destinataire"].includes(relanceEssentiel.email_statut), "le resultat email doit etre explicite");
  await attendu402(api.get("/equipe", tokenEssentiel), "la lecture de l'equipe doit rester reservee au plan Business pour un abonne Essentiel");
  await attendu402(api.post("/equipe", { nom: "Test Membre", email: "x@test.fr", password: "TestPass123!" }, tokenEssentiel), "l'equipe doit rester reservee au plan Business pour un abonne Essentiel");
  logEtape("plan Essentiel : relance devis manuelle accessible ; contrats/equipe restent bloques");

  // ---------- Plan Pro : tout Essentiel + relances/automatisations/contrats, equipe bloquee ----------
  const { token: tokenPro, email: emailPro } = await creerArtisanTest("scenario12-pro");
  await activerAbonnement(emailPro, "pro");
  await api.get("/factures", tokenPro);
  await api.get("/chantiers", tokenPro);
  await api.get("/conformite", tokenPro);
  await api.get("/analytics", tokenPro);
  await api.get("/contrats", tokenPro);
  const clientP = await api.post("/clients", { nom: "Client Pro" }, tokenPro);
  const devisP = await api.post("/devis", {
    client_id: clientP.id, titre: "Devis pro", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenPro);
  await api.patch(`/devis/${devisP.id}`, { statut: "envoye" }, tokenPro);
  const devisRelance = await api.post(`/devis/${devisP.id}/relancer`, undefined, tokenPro);
  assert(!!devisRelance.id, "un abonne Pro doit pouvoir relancer manuellement un devis");
  await attendu402(api.get("/equipe", tokenPro), "l'equipe doit rester reservee au plan Business pour un abonne Pro");
  logEtape("plan Pro : tout Essentiel, relance devis et contrats accessibles ; equipe bloquee");

  // ---------- Plan Business : tout Pro + equipe/collaborateurs ----------
  const { token: tokenBusiness, email: emailBusiness } = await creerArtisanTest("scenario12-business");
  await activerAbonnement(emailBusiness, "business");
  await api.get("/factures", tokenBusiness);
  await api.get("/chantiers", tokenBusiness);
  await api.get("/analytics", tokenBusiness);
  await api.get("/contrats", tokenBusiness);
  const membre = await api.post("/equipe", {
    nom: "Collaborateur Business", email: `membre-${Date.now()}@e2e-test.fr`, password: "TestPass123!",
  }, tokenBusiness);
  assert(!!membre.id, "un abonne Business doit pouvoir creer un collaborateur");
  const equipe = await api.get("/equipe", tokenBusiness);
  assert(equipe.some((item) => item.id === membre.id), "un abonne Business doit pouvoir lire son equipe");
  logEtape("plan Business : tout Pro et equipe accessibles");
}
