// Scenario 6 (cahier des charges V4, section 16 + section 39 "Production") :
// chantier -> heures de main d'oeuvre -> cout reel -> rentabilite.
import { api, assert, assertClose, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario6");
  await activerAbonnement(email);

  const client = await api.post("/clients", { nom: "Client Heures" }, token);
  const chantier = await api.post("/chantiers", { client_id: client.id, titre: "Renovation salle de bain", budget: 5000 }, token);
  assertClose(chantier.marge_estimee, 5000, "sans heures ni depense, marge estimee = budget");
  logEtape("chantier cree, budget 5000 EUR");

  // Un intervenant avec taux horaire connu, un autre sans (sous-traitant dont
  // on ne connait pas encore le cout) : le cout doit rester honnete, jamais invente.
  const h1 = await api.post(`/chantiers/${chantier.id}/heures`, {
    nom_intervenant: "Paul", date_travail: "2026-08-20", duree_heures: 6.5, taux_horaire: 35, note: "Carrelage",
  }, token);
  assertClose(h1.cout, 227.5, "cout = duree x taux quand le taux est connu");

  const h2 = await api.post(`/chantiers/${chantier.id}/heures`, {
    nom_intervenant: "Karim", date_travail: "2026-08-21", duree_heures: 8,
  }, token);
  assert(h2.cout === null, "sans taux horaire, le cout ne doit jamais etre invente (null, pas 0)");
  logEtape("heures saisies pour 2 intervenants (un avec taux, un sans)");

  let c = await api.get(`/chantiers/${chantier.id}`, token);
  assertClose(c.total_heures, 14.5, "total_heures = somme de toutes les entrees, meme sans taux");
  assertClose(c.cout_main_oeuvre, 227.5, "cout_main_oeuvre = somme des seules entrees avec taux connu");
  assertClose(c.marge_estimee, 5000 - 227.5, "la main d'oeuvre reelle doit reduire la marge estimee");
  logEtape(`rentabilite alimentee : ${c.total_heures}h, cout main d'oeuvre=${c.cout_main_oeuvre} EUR, marge estimee=${c.marge_estimee} EUR`);

  // Une depense materiaux s'ajoute au meme calcul de cout total.
  await api.post(`/chantiers/${chantier.id}/depenses`, { libelle: "Carrelage", montant: 500, date_depense: "2026-08-20" }, token);
  c = await api.get(`/chantiers/${chantier.id}`, token);
  assertClose(c.marge_estimee, 5000 - 500 - 227.5, "marge estimee = budget - depenses - main d'oeuvre reelle");
  logEtape(`depense materiaux ajoutee : marge estimee=${c.marge_estimee} EUR (coherente avec depenses + main d'oeuvre)`);

  // Isolation multi-tenant : un autre artisan ne doit ni voir ni modifier ces heures.
  const { token: tokenAutre, email: emailAutre } = await creerArtisanTest("scenario6-autre");
  await activerAbonnement(emailAutre);
  let refuse404 = false;
  try {
    await api.del(`/chantiers/${chantier.id}/heures/${h1.id}`, tokenAutre);
  } catch (err) {
    refuse404 = err.message.includes("HTTP 404");
  }
  assert(refuse404, "un artisan ne doit jamais pouvoir supprimer les heures d'un chantier qui n'est pas le sien (404)");
  logEtape("isolation multi-tenant verifiee sur les heures de main d'oeuvre");

  // Suppression reelle : le total doit refleter la suppression, pas juste marquer un flag.
  await api.del(`/chantiers/${chantier.id}/heures/${h1.id}`, token);
  c = await api.get(`/chantiers/${chantier.id}`, token);
  assertClose(c.total_heures, 8, "apres suppression de l'entree avec taux, il ne reste que les 8h sans taux");
  assert(c.cout_main_oeuvre === null, "plus aucune entree n'a de taux : le cout de main d'oeuvre redevient honnetement null");
  logEtape("suppression d'une entree d'heures verifiee (total et cout recalcules)");
}
