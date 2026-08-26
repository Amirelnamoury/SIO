// Scenario 12 (cahier des charges V5, section 8) :
// matrice fonctionnalite x plan - verifie que le backend applique
// exactement les frontieres annoncees sur la page de tarifs (pricing.js) :
// devis/clients/documents toujours libres ; chantiers/factures/conformite/
// statistiques a partir d'Essentiel ; contrats recurrents et relance devis
// a partir de Pro ; equipe a partir de Business. Trouve en auditant le code
// reel : les factures n'etaient gated nulle part (ni backend ni frontend),
// alors que la page de tarifs les presente comme la fonctionnalite phare du
// plan Essentiel - corrige dans le meme commit que ce scenario.
import { api, assert, creerArtisanTest, logEtape } from "./helpers.mjs";

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
  await attendu402(api.post(`/devis/${devis.id}/relancer`, undefined, tokenGratuit), "la relance manuelle de devis doit etre reservee au plan Pro");
  await attendu402(api.post("/equipe", { nom: "Test Membre", email: "x@test.fr", password: "TestPass123!" }, tokenGratuit), "la gestion d'equipe doit etre reservee au plan Business");
  logEtape("plan Gratuit : chantiers/factures/conformite/statistiques/contrats/relance-devis/equipe tous bloques (402)");

  // ---------- Plan Essentiel : chantiers/factures/conformite/statistiques debloques, Pro/Business toujours bloques ----------
  const { token: tokenEssentiel, email: emailEssentiel } = await creerArtisanTest("scenario12-essentiel");
  // manage_subscription.py active "business" par defaut (voir helpers.mjs) ;
  // ce scenario veut specifiquement le plan Essentiel pour verifier que Pro
  // et Business restent bloques, donc on l'appelle directement avec le plan.
  const { execSync } = await import("node:child_process");
  execSync(`cd /home/user/SIO/backend && source .venv/bin/activate && python manage_subscription.py activer "${emailEssentiel}" essentiel`, { shell: "/bin/bash" });

  const clientE = await api.post("/clients", { nom: "Client Essentiel" }, tokenEssentiel);
  const chantierE = await api.post("/chantiers", { client_id: clientE.id, titre: "Chantier essentiel" }, tokenEssentiel);
  assert(!!chantierE.id, "un abonne Essentiel doit pouvoir creer un chantier");
  const factureE = await api.post("/factures", {
    client_id: clientE.id, titre: "Facture essentiel", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenEssentiel);
  assert(!!factureE.id, "un abonne Essentiel doit pouvoir creer une facture");
  logEtape("plan Essentiel : chantiers et factures reellement debloques");

  await attendu402(api.get("/contrats", tokenEssentiel), "les contrats recurrents doivent rester reserves au plan Pro pour un abonne Essentiel");
  const devisE = await api.post("/devis", {
    client_id: clientE.id, titre: "Devis essentiel", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, tokenEssentiel);
  await api.patch(`/devis/${devisE.id}`, { statut: "envoye" }, tokenEssentiel);
  await attendu402(api.post(`/devis/${devisE.id}/relancer`, undefined, tokenEssentiel), "la relance manuelle doit rester reservee au plan Pro pour un abonne Essentiel");
  await attendu402(api.post("/equipe", { nom: "Test Membre", email: "x@test.fr", password: "TestPass123!" }, tokenEssentiel), "l'equipe doit rester reservee au plan Business pour un abonne Essentiel");
  logEtape("plan Essentiel : contrats/relance-devis/equipe restent bloques (le plan ne debloque pas plus que ce qui est annonce)");
}
