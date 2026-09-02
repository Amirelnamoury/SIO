// Scenario 1 (cahier des charges V3, section 39) :
// site -> prospect -> devis -> email -> consultation -> relance -> signature
// -> chantier -> facture -> paiement -> avis
import { api, assert, assertEqual, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario1");
  await activerAbonnement(email);
  logEtape("artisan cree et abonnement actif");

  // Prospect reellement cree via le formulaire PUBLIC du site vitrine
  // (le meme endpoint que celui appele par le site livre a l'artisan),
  // pas une insertion directe.
  const moi = await api.get("/auth/me", token);
  const demandeSite = await api.post(`/pub/${moi.slug}/demande-devis`, {
    nom: "Prospect Scenario 1", email: "prospect1@e2e-test.fr", message: "Interesse par une renovation",
  });
  const clientsApresDemande = await api.get("/clients", token);
  const client = clientsApresDemande.find((c) => c.id === demandeSite.client_id);
  assert(!!client, "le prospect issu du site vitrine doit exister cote artisan");
  assertEqual(client.source, "site_vitrine", "le prospect doit venir du site vitrine");
  logEtape("prospect cree via le formulaire public du site vitrine");

  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Renovation salle de bain", taux_tva: 10, acompte_pourcentage: 30,
    lignes: [{ description: "Travaux", quantite: 1, prix_unitaire_ht: 4000 }],
  }, token);
  await api.post(`/devis/${devis.id}/envoyer`, {}, token);
  logEtape("devis cree et envoye");

  // Consultation reelle par le client (endpoint public, marque "consulte").
  const devisPublic = await api.get(`/pub/devis/${devis.token}`);
  assertEqual(devisPublic.statut, "consulte", "le devis doit passer a 'consulte' apres consultation publique");
  logEtape("devis consulte via le lien public");

  // Relance manuelle (meme logique que l'automatisation, declenchee a la main ici pour ne pas attendre le planificateur).
  const relance = await api.post(`/devis/${devis.id}/relancer`, {}, token);
  if (relance.email_statut === "envoye") {
    assert(relance.nb_relances >= 1, "un email reellement envoye doit incrementer nb_relances");
  } else {
    assert(relance.nb_relances === 0, "une tentative non envoyee ne doit pas incrementer nb_relances");
  }
  logEtape(`tentative de relance devis tracee (email=${relance.email_statut})`);

  // Signature reelle par le client (endpoint public).
  const devisSigne = await api.post(`/pub/devis/${devis.token}/accepter`, { nom_signataire: "Jean Prospect" });
  assertEqual(devisSigne.statut, "signe", "le devis doit passer a 'signe' apres acceptation");
  const clientApresSignature = await api.get("/clients", token).then((cs) => cs.find((c) => c.id === client.id));
  assertEqual(clientApresSignature.statut, "gagne", "le client doit passer a 'gagne' des la signature");
  logEtape("devis signe par le client, client passe a 'gagne'");

  // Chantier a partir du devis signe.
  const prep = await api.post(`/chantiers/depuis-devis/${devis.id}`, { creer_acompte: false, creer_checklist: false }, token);
  assertEqual(prep.chantier.client_id, client.id, "le chantier doit etre rattache au bon client");
  logEtape("chantier prepare depuis le devis signe");

  // Facturation et paiement.
  const facture = await api.post(`/factures/depuis-devis/${devis.id}?type=standard`, undefined, token);
  await api.patch(`/factures/${facture.id}`, { statut: "envoyee" }, token);
  const facturePaiee = await api.post(`/factures/${facture.id}/paiements`, {
    montant: facture.montant_ttc, mode: "virement", date_paiement: new Date().toISOString().slice(0, 10),
  }, token);
  assertEqual(facturePaiee.statut, "payee", "la facture doit passer a 'payee' apres reglement integral");
  logEtape(`facture payee (${facturePaiee.montant_ttc} EUR)`);

  // Avis client.
  const demande = await api.post(`/clients/${client.id}/demande-avis`, {}, token);
  assert(!!demande.token_avis, "un jeton de demande d'avis doit etre genere");
  await api.post(`/pub/avis/${demande.token_avis}`, { note: 5, commentaire: "Tres satisfait, e2e test." });
  const avisListe = await api.get("/avis", token);
  assert(avisListe.some((a) => a.client_id === client.id && a.note === 5), "l'avis soumis doit apparaitre cote artisan");
  logEtape("avis soumis par le client et visible cote artisan");
}
