// Scenario 2 (cahier des charges V3, section 39) :
// devis accepte -> "Tout preparer" -> chantier -> progression -> depenses ->
// marge -> facture finale (verifie explicitement l'absence de double
// facturation entre l'acompte et le solde, bug reel trouve et corrige en
// Phase B de ce projet).
import { api, assert, assertEqual, assertClose, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario2");
  await activerAbonnement(email);

  const client = await api.post("/clients", { nom: "Client Scenario 2" }, token);
  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Renovation cuisine", taux_tva: 10, acompte_pourcentage: 30,
    lignes: [{ description: "Travaux", quantite: 1, prix_unitaire_ht: 5000 }],
  }, token);
  await api.patch(`/devis/${devis.id}`, { statut: "signe" }, token);
  logEtape(`devis signe : ${devis.id}, montant TTC attendu 5500`);

  const prep = await api.post(`/chantiers/depuis-devis/${devis.id}`, {
    date_debut: new Date().toISOString().slice(0, 10), creer_acompte: true, creer_checklist: true,
  }, token);
  assertEqual(prep.nb_taches_creees, 6, "la checklist de preparation doit creer 6 taches");
  assert(!!prep.facture_acompte, "un acompte doit etre genere (acompte_pourcentage renseigne)");
  assertClose(prep.facture_acompte.montant_ttc, 1650, "l'acompte doit valoir 30% de 5500 = 1650");
  const chantierId = prep.chantier.id;
  logEtape(`chantier prepare (id=${chantierId}), acompte=${prep.facture_acompte.montant_ttc} EUR`);

  // Progression : cocher une partie des taches de la checklist.
  const chantierAvecTaches = await api.get("/chantiers", token).then((cs) => cs.find((c) => c.id === chantierId));
  assertEqual(chantierAvecTaches.progression, 0, "aucune tache faite -> progression 0%");
  const taches = chantierAvecTaches.taches;
  for (const t of taches.slice(0, 3)) {
    await api.patch(`/taches/${t.id}`, { statut: "faite" }, token);
  }
  const chantierMoitie = await api.get("/chantiers", token).then((cs) => cs.find((c) => c.id === chantierId));
  assertEqual(chantierMoitie.progression, 50, "3 taches sur 6 faites -> progression 50%");
  logEtape("progression verifiee (0% -> 50%)");

  // Depenses et marge.
  await api.post(`/chantiers/${chantierId}/depenses`, { libelle: "Materiaux", montant: 1200, date_depense: new Date().toISOString().slice(0, 10) }, token);
  const chantierAvecDepenses = await api.get("/chantiers", token).then((cs) => cs.find((c) => c.id === chantierId));
  assertClose(chantierAvecDepenses.total_depenses, 1200, "les depenses doivent etre comptabilisees");
  assertClose(chantierAvecDepenses.marge_estimee, 5000 - 1200, "marge estimee = budget - depenses");
  logEtape(`depense ajoutee, marge estimee=${chantierAvecDepenses.marge_estimee} EUR`);

  // Cloture : la facture finale ne doit PAS re-facturer l'acompte deja engage.
  await api.patch(`/chantiers/${chantierId}`, { statut: "termine" }, token);
  const cloture = await api.post(`/chantiers/${chantierId}/cloturer`, { generer_facture_finale: true, demander_avis: false }, token);
  assert(!!cloture.facture_finale, "une facture finale doit etre generee");
  assertClose(cloture.facture_finale.montant_ttc, 5500 - 1650, "le solde final doit exclure l'acompte deja engage (pas de double facturation)");
  logEtape(`chantier cloture : solde final=${cloture.facture_finale.montant_ttc} EUR (acompte 1650 + solde 3850 = 5500 total, coherent)`);
}
