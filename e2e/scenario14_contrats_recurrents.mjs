import { activerAbonnement, api, assert, assertEqual, creerArtisanTest, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario14-contrats");
  await activerAbonnement(email, "pro");

  const client = await api.post("/clients", {
    nom: "Client contrat récurrent",
    email: `client-contrat-${Date.now()}@e2e-test.fr`,
  }, token);
  const contrat = await api.post("/contrats", {
    client_id: client.id,
    titre: "Entretien annuel chaudière",
    montant_ht: 900,
    taux_tva: 20,
    frequence: "annuel",
    prochaine_echeance: "2026-09-30",
  }, token);
  assertEqual(contrat.nb_factures_generees, 0, "un nouveau contrat ne doit avoir aucune facture");
  logEtape("contrat Pro créé et visible via l'API utilisée par Entreprise");

  const generation = await api.post(`/contrats/${contrat.id}/generer`, undefined, token);
  assertEqual(generation.nb_factures_generees, 1, "Générer maintenant doit créer exactement une facture");
  assertEqual(generation.prochaine_echeance, "2027-09-30", "l'échéance annuelle doit avancer d'un an");
  assert(["envoye", "non_configure", "echec", "sans_destinataire"].includes(generation.email_statut), "le statut email doit être explicite");

  const factures = await api.get("/factures", token);
  const facture = factures.find((item) => item.id === generation.facture_id);
  assert(!!facture, "la facture générée doit apparaître dans Factures");
  assertEqual(facture.contrat_id, contrat.id, "la facture doit rester liée au contrat");
  assertEqual(facture.montant_ht, 900, "le montant HT doit provenir du contrat");
  assertEqual(facture.montant_ttc, 1080, "la TVA du contrat doit être appliquée");
  if (generation.email_statut === "envoye") {
    assertEqual(facture.statut, "envoyee", "un email réellement envoyé doit marquer la facture envoyée");
  } else {
    assertEqual(facture.statut, "brouillon", "sans envoi réel, la facture ne doit pas prétendre être envoyée");
  }
  logEtape(`facture ${facture.numero} générée, liée et affichable (email=${generation.email_statut})`);

  const suspendu = await api.patch(`/contrats/${contrat.id}`, { statut: "suspendu" }, token);
  assertEqual(suspendu.statut, "suspendu", "le contrat doit pouvoir être suspendu");
  const reactive = await api.patch(`/contrats/${contrat.id}`, { statut: "actif" }, token);
  assertEqual(reactive.statut, "actif", "le contrat doit pouvoir être réactivé");
}
