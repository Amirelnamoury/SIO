// Scenario 3 (cahier des charges V3, section 39) :
// facture impayee -> automatisation -> email -> notification -> paiement ->
// arret de l'automatisation. Declenche le VRAI moteur d'automatisation
// (app.scheduler.run_automation_cycle, celui que le planificateur en tache
// de fond appelle toutes les X minutes) plutot que la relance manuelle, pour
// verifier le chemin reellement emprunte en production.
import { execSync } from "node:child_process";
import { api, assert, assertEqual, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

function lancerCycleAutomatisation() {
  execSync(
    `cd /home/user/SIO/backend && source .venv/bin/activate && python -c "from app.scheduler import run_automation_cycle; run_automation_cycle()"`,
    { shell: "/bin/bash" },
  );
}

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario3");
  await activerAbonnement(email);

  const client = await api.post("/clients", { nom: "Client Impaye", email: "client-impaye@e2e-test.fr" }, token);
  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Depannage", taux_tva: 20,
    lignes: [{ description: "Intervention", quantite: 1, prix_unitaire_ht: 500 }],
  }, token);
  await api.patch(`/devis/${devis.id}`, { statut: "signe" }, token);
  const facture = await api.post(`/factures/depuis-devis/${devis.id}?type=standard`, undefined, token);
  // Echeance dans le passe -> facture immediatement en retard.
  await api.patch(`/factures/${facture.id}`, { statut: "envoyee", date_echeance: "2020-01-01" }, token);
  const factureEnRetard = await api.get("/factures", token).then((fs) => fs.find((f) => f.id === facture.id));
  assertEqual(factureEnRetard.statut, "en_retard", "la facture doit etre detectee en retard (echeance passee)");
  assertEqual(factureEnRetard.nb_relances, 0, "aucune relance avant le premier passage de l'automatisation");
  logEtape("facture en retard creee");

  lancerCycleAutomatisation();

  // L'email transactionnel est honnetement journalise (envoye/echec/non_configure/
  // sans_destinataire), jamais simule silencieusement : on verifie qu'une
  // TENTATIVE reelle a ete tracee, quel que soit son resultat.
  const emails = await api.get("/automation/emails", token);
  const emailPourCetteFacture = emails.find((e) => e.facture_id === facture.id && e.type === "relance_facture");
  assert(!!emailPourCetteFacture, "une tentative d'email de relance doit etre journalisee, quel que soit son statut reel");
  logEtape(`email de relance journalise avec le statut reel : ${emailPourCetteFacture.statut}`);

  const apresCycle1 = await api.get("/factures", token).then((fs) => fs.find((f) => f.id === facture.id));
  if (emailPourCetteFacture.statut === "envoye") {
    // Fournisseur email reellement configure (RESEND_API_KEY present) : l'etat
    // avance vraiment, comme concu (voir scheduler.py).
    assert(apresCycle1.nb_relances >= 1, "un envoi reussi doit faire avancer nb_relances");
    logEtape(`email reellement envoye, nb_relances=${apresCycle1.nb_relances}`);
  } else {
    // Environnement de test SANS fournisseur email configure (cas courant en
    // local/CI) : aucun envoi n'a reellement eu lieu, donc nb_relances ne doit
    // PAS bouger - mentir sur un envoi qui n'a pas eu lieu serait le bug que
    // ce projet s'interdit explicitement (voir email_service.py).
    assertEqual(apresCycle1.nb_relances, 0, "sans envoi reel, nb_relances ne doit jamais etre incremente artificiellement");
    logEtape(`fournisseur email non configure dans cet environnement (statut=${emailPourCetteFacture.statut}) : nb_relances reste honnetement a 0`);
  }

  const notifications = await api.get("/notifications", token);
  assert(notifications.some((n) => n.type === "facture_relance" && n.id === facture.id), "la facture impayee doit apparaitre dans le centre de notifications");
  logEtape("facture visible dans le centre de notifications");

  // Paiement integral -> l'automatisation doit s'arreter d'elle-meme (plus jamais relancee).
  await api.post(`/factures/${facture.id}/paiements`, {
    montant: factureEnRetard.montant_ttc, mode: "virement", date_paiement: new Date().toISOString().slice(0, 10),
  }, token);
  const facturePaiee = await api.get("/factures", token).then((fs) => fs.find((f) => f.id === facture.id));
  assertEqual(facturePaiee.statut, "payee", "la facture doit passer a 'payee'");
  const nbTentativesAvantCycle2 = (await api.get("/automation/emails", token)).filter((e) => e.facture_id === facture.id).length;

  lancerCycleAutomatisation();
  const nbTentativesApresCycle2 = (await api.get("/automation/emails", token)).filter((e) => e.facture_id === facture.id).length;
  assertEqual(nbTentativesApresCycle2, nbTentativesAvantCycle2, "une facture payee doit etre exclue de la requete d'automatisation : aucune nouvelle tentative de relance, meme journalisee");
  logEtape("automatisation correctement arretee apres paiement integral (aucune nouvelle tentative journalisee)");
}
