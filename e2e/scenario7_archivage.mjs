// Scenario 7 (cahier des charges V4, section 44) :
// "Supprimer" un client/devis/facture/chantier n'efface plus rien - ca
// l'archive (disparait des listes actives, reste consultable, jamais de
// cascade destructrice sur les donnees financieres/historiques liees).
import { api, assert, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario7");
  await activerAbonnement(email);

  // --- Client : archivage + restauration, aucune cascade sur devis/factures ---
  const client = await api.post("/clients", { nom: "Client Archivage" }, token);
  const devis = await api.post("/devis", {
    client_id: client.id, titre: "Devis lie", taux_tva: 20,
    lignes: [{ description: "Prestation", quantite: 1, prix_unitaire_ht: 500 }],
  }, token);

  await api.del(`/clients/${client.id}`, token);
  let clients = await api.get("/clients", token);
  assert(!clients.some((c) => c.id === client.id), "le client archive ne doit plus apparaitre dans la liste active");
  let clientsArchives = await api.get("/clients?archive=true", token);
  assert(clientsArchives.some((c) => c.id === client.id), "le client archive doit apparaitre dans la liste des archives");
  logEtape("client archive : invisible en actif, visible en archive");

  // Le devis du client archive doit rester intact (pas de cascade destructrice).
  let devisListe = await api.get("/devis", token);
  assert(devisListe.some((d) => d.id === devis.id), "archiver le client NE DOIT PAS supprimer ses devis existants");
  logEtape("aucune cascade destructrice : le devis du client archive existe toujours");

  await api.post(`/clients/${client.id}/restaurer`, {}, token);
  clients = await api.get("/clients", token);
  assert(clients.some((c) => c.id === client.id), "le client doit reapparaitre apres restauration");
  logEtape("restauration du client verifiee");

  // --- Devis : archivage puis restauration (V5 : la restauration devis
  // n'existait pas du tout avant cette passe - seul le client en avait une) ---
  await api.del(`/devis/${devis.id}`, token);
  devisListe = await api.get("/devis", token);
  assert(!devisListe.some((d) => d.id === devis.id), "le devis archive ne doit plus apparaitre dans la liste active");
  let devisArchives = await api.get("/devis?archive=true", token);
  assert(devisArchives.some((d) => d.id === devis.id), "le devis archive doit apparaitre dans la liste des archives");
  logEtape("devis archive : invisible en actif, visible en archive");

  await api.post(`/devis/${devis.id}/restaurer`, {}, token);
  devisListe = await api.get("/devis", token);
  assert(devisListe.some((d) => d.id === devis.id), "le devis doit reapparaitre apres restauration");
  logEtape("restauration du devis verifiee");
  await api.del(`/devis/${devis.id}`, token); // rearchive pour la suite du scenario

  // --- Facture : archivage puis restauration ---
  const facture = await api.post("/factures", {
    client_id: client.id, type: "standard", taux_tva: 20,
    lignes: [{ description: "Solde", quantite: 1, prix_unitaire_ht: 300 }],
  }, token);
  await api.del(`/factures/${facture.id}`, token);
  let factures = await api.get("/factures", token);
  assert(!factures.some((f) => f.id === facture.id), "la facture archivee ne doit plus apparaitre dans la liste active");
  logEtape("facture archivee : document financier jamais perdu");

  await api.post(`/factures/${facture.id}/restaurer`, {}, token);
  factures = await api.get("/factures", token);
  assert(factures.some((f) => f.id === facture.id), "la facture doit reapparaitre apres restauration");
  logEtape("restauration de la facture verifiee");
  await api.del(`/factures/${facture.id}`, token); // rearchive pour la suite du scenario

  // --- Chantier : archivage, notes/depenses/heures conservees, puis restauration ---
  const chantier = await api.post("/chantiers", { client_id: client.id, titre: "Chantier a archiver", budget: 2000 }, token);
  await api.post(`/chantiers/${chantier.id}/notes`, { phase: "avant", texte: "Etat des lieux" }, token);
  await api.post(`/chantiers/${chantier.id}/depenses`, { libelle: "Materiaux", montant: 150, date_depense: "2026-08-20" }, token);
  await api.del(`/chantiers/${chantier.id}`, token);
  let chantiers = await api.get("/chantiers", token);
  assert(!chantiers.some((c) => c.id === chantier.id), "le chantier archive ne doit plus apparaitre dans la liste active");
  const chantiersArchives = await api.get("/chantiers?archive=true", token);
  const chantierArchive = chantiersArchives.find((c) => c.id === chantier.id);
  assert(!!chantierArchive, "le chantier archive doit apparaitre dans la liste des archives");
  assert(chantierArchive.notes.length === 1, "les notes du chantier archive doivent etre conservees");
  assert(chantierArchive.depenses.length === 1, "les depenses du chantier archive doivent etre conservees");
  logEtape("chantier archive : notes et depenses conservees, aucune perte de donnees");

  await api.post(`/chantiers/${chantier.id}/restaurer`, {}, token);
  chantiers = await api.get("/chantiers", token);
  assert(chantiers.some((c) => c.id === chantier.id), "le chantier doit reapparaitre apres restauration");
  logEtape("restauration du chantier verifiee");

  // --- Document : avant cette passe, supprimer un document faisait un vrai
  // db.delete() (fichier + ligne detruits, aucune restauration possible).
  // Verifie que ce n'est plus le cas. ---
  const document = await api.post("/documents", {
    nom: "Attestation assurance", type: "assurance", url: "https://exemple.test/attestation.pdf", client_id: client.id,
  }, token);
  await api.del(`/documents/${document.id}`, token);
  let documents = await api.get("/documents", token);
  assert(!documents.some((d) => d.id === document.id), "le document archive ne doit plus apparaitre dans la liste active");
  const documentsArchives = await api.get("/documents?archive=true", token);
  assert(documentsArchives.some((d) => d.id === document.id), "le document archive doit apparaitre dans la liste des archives (pas de suppression definitive)");
  logEtape("document archive : plus de db.delete() direct, restaurable comme les autres entites");

  await api.post(`/documents/${document.id}/restaurer`, {}, token);
  documents = await api.get("/documents", token);
  assert(documents.some((d) => d.id === document.id), "le document doit reapparaitre apres restauration");
  logEtape("restauration du document verifiee");
}
