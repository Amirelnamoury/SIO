/* =====================================================================
   Jeu d'essai — peupler toutes les vues sans backend
   ---------------------------------------------------------------------
   A charger dans la console AVANT d'ouvrir une vue :

     const s = document.createElement('script');
     s.src = 'outils/jeu-essai.js';
     document.head.appendChild(s);

   Il remplace les points d'entree de l'API par des donnees couvrant les
   cas qui comptent : une facture en retard, un devis lu mais sans
   reponse, un chantier au-dela de son budget, une tache rattachee a un
   chantier, un prospect qui dort.

   POURQUOI IL EST VERSE AU DEPOT
   Une vue VIDE ne deborde jamais et ne prouve rien. L'audit mobile qui a
   revele six vues en debordement horizontal n'a ete possible qu'avec des
   donnees reelles dans chaque ecran - a vide, les douze vues passaient.

   A n'utiliser qu'en developpement, evidemment : il ecrase l'objet Api.
   ===================================================================== */
// Jeu d'essai global : de quoi peupler chaque vue pour un audit mobile
// reel. Sans donnees, une vue vide ne deborde jamais - et ne prouve rien.
//
// La fonction enveloppante n'est pas de la coquetterie : au premier jet, ce
// fichier declarait ses aides avec `const` au niveau global. Le recharger
// dans une page deja ouverte - le reflexe meme d'un audit - levait alors une
// SyntaxError de redeclaration qui tuait TOUT le script, sans rien afficher,
// et l'audit continuait sur les anciennes donnees en croyant les avoir
// remplacees. Ici, un second chargement se contente d'ecraser Api a nouveau.
(function () {
// Jour LOCAL, pas UTC : entre minuit local et minuit UTC, `toISOString()`
// rend la veille et le jeu d'essai decale toutes ses echeances d'un jour.
const jg = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const tg = (n) => new Date(Date.now() - n * 86400e3).toISOString();
Api.listClients = async () => [
  { id: 1, nom: "Bertrand", societe: "Bertrand & Fils", statut: "gagne", source: "manuel", email: "contact@bertrand-fils.fr", telephone: "06 12 34 56 78", ville: "Villeurbanne", montant_estime: 31000, probabilite: 80, prochaine_action: "Relancer après la visite de mardi", updated_at: tg(2), created_at: tg(60) },
  { id: 2, nom: "Roussel", societe: null, statut: "nouveau", source: "site_vitrine", email: null, telephone: "07 88 12 45 66", ville: "Lyon 3e", montant_estime: null, probabilite: null, prochaine_action: null, updated_at: tg(22), created_at: tg(30) },
];
Api.listChantiers = async () => [
  { id: 2, client_id: 1, client_nom: "Bertrand", titre: "Villa Ducros — extension côté jardin", adresse: "Écully", statut: "en_cours", progression: 72, budget: 64000, total_depenses: 56000, marge_estimee: 10240, marge_reelle: null, date_debut: jg(-70), date_fin_prevue: jg(-3), date_reception: null, reserves: null, finances_verrouillees: false, total_heures: null, cout_main_oeuvre: null, montant_facture: null, montant_encaisse: null, created_at: tg(70), notes: [], depenses: [], heures: [], taches: [] },
];
Api.listDevis = async () => [
  { id: 89, client_id: 1, client_nom: "Bertrand", numero: "DV-2026-089", titre: "Rénovation salle de bain complète", description: null, taux_tva: 10, acompte_pourcentage: 30, remise_pourcentage: 5, montant_ht: 1333.57, montant_ttc: 1466.93, statut: "consulte", date_envoi: tg(9), date_consultation: tg(1), date_derniere_relance: tg(3), date_signature: null, nom_signataire: null, nb_relances: 2, source: "manuel", token: "t89", relance_manuelle_possible: true, created_at: tg(12), lignes: [{ id: 1, description: "Pose de carrelage", quantite: 24, unite: "m2", prix_unitaire_ht: 45.5 }] },
];
Api.devisARelancer = async () => [];
Api.listFactures = async () => [
  { id: 14, client_id: 1, client_nom: "Bertrand", devis_id: null, chantier_id: null, contrat_id: null, numero: "FA-2026-014", type: "standard", taux_tva: 20, statut: "envoyee", montant_ht: 1533, montant_ttc: 1840, montant_paye: 0, montant_restant: 1840, est_en_retard: true, date_emission: jg(-40), date_echeance: jg(-12), date_envoi: tg(40), notes: null, date_derniere_relance: null, nb_relances: 0, token: "f14", created_at: tg(40), paiements: [] },
];
Api.facturesARelancer = async () => [];
Api.listTaches = async () => [
  { id: 1, artisan_id: 1, client_id: null, chantier_id: 2, titre: "Commander le carrelage pour la salle de bain", description: null, priorite: "urgente", echeance: jg(-3), statut: "a_faire", created_at: tg(5) },
];
Api.listDocuments = async () => [
  { id: 1, nom: "Photo avant travaux", type: "photo", url: null, nom_original: "photo.jpg", taille_octets: 240000, client_id: null, chantier_id: 2, created_at: tg(3) },
];
Api.listConformite = async () => [];
Api.planning = async () => [{ id: 1, date: new Date().toISOString(), type: "rdv", titre: "Métré chez Mme Roussel", reference_id: 1, client_id: null, chantier_id: null }];
Api.analytics = async () => ({ ca_par_mois: [4200, 5100, 6400, 8100, 9200, 11650].map((ca, i) => { const d = new Date(); d.setMonth(d.getMonth() - (5 - i)); return { mois: d.toISOString().slice(0, 7), ca }; }), valeur_pipeline: 42100, montant_impayes: 13340, nb_devis_total: 48, nb_devis_signes: 21, nb_clients_acquis: 18, nb_clients_recurrents: 7, taux_acceptation: 58, panier_moyen: 6420, delai_moyen_paiement_jours: 34, sources_acquisition: [{ source: "site_vitrine", nb_clients: 15, nb_gagnes: 5, ca: 31200 }] });
Api.listAvis = async () => [{ id: 1, client_nom: "Bertrand", note: 5, commentaire: "Travail soigné, délais tenus, je recommande sans hésiter.", publie: true, created_at: tg(10) }];
Api.listNotifications = async () => [{ id: 1, type: "facture_retard", titre: "Facture FA-2026-014 en retard", message: "1 840 € restent à encaisser.", lue: false, created_at: tg(1) }];
Api.dashboard = async () => ({ finances: { ca_mois: 18420, a_encaisser: 1840, paiements_recents: [{ date_paiement: jg(-2), moyen: "Virement", montant: 4200 }] }, commercial: { devis_en_attente: 7, valeur_pipeline: 42100 }, aujourdhui: { factures_en_retard: [{ id: 14, numero: "FA-2026-014", client_nom: "Bertrand", montant_restant: 1840 }], devis_a_relancer: [], taches: [{ id: 1, titre: "Commander le carrelage" }], chantiers_a_venir: [], evenements: [{ id: 1, titre: "Métré chez Mme Roussel", date_debut: new Date().toISOString() }] }, alertes_conformite: [], presence_site: { statut: "livre", url: "https://exemple.fr", nb_demandes_total: 9, nb_demandes_30j: 3, nb_clients_gagnes: 2, ca_genere: 12400, taux_conversion: 22.2 } });
Api.dashboardRecommandations = async () => [{ message: "Trois devis de plus de 30 jours n'ont jamais été relancés.", urgence: "haute" }];
// Le contrat serveur est SanteEntrepriseOut / SousScoreOut : la valeur du
// sous-score s'appelle `valeur`, pas `score`, et peut etre nulle quand il n'y
// a pas de quoi juger. Le jeu d'essai disait `score` : chaque sous-score
// tombait donc dans la branche « pas assez de donnees » et les barres
// n'etaient jamais rendues - une zone de l'ecran que l'audit croyait couvrir
// et qu'il ne voyait pas. Les cinq valeurs ci-dessous traversent les trois
// seuils de couleur (>=70, >=40, <40) et le cas nul.
Api.dashboardSante = async () => ({ score_global: 72, raison_absence_globale: null, commercial: { label: "Commercial", valeur: 68 }, tresorerie: { label: "Trésorerie", valeur: 31 }, chantiers: { label: "Chantiers", valeur: 80 }, conformite: { label: "Conformité", valeur: null, raison_absence: "Aucune information de conformité enregistrée" }, organisation: { label: "Organisation", valeur: 42 } });
Api.dashboardActivation = async () => ({ entierement_active: true, entreprise_configuree: true, premier_client: true, premier_devis: true, premiere_facture: true });
window.hasPlan = () => true;
})();
