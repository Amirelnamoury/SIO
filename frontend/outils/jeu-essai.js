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

   ECRIRE UNE ENTREE, MODE D'EMPLOI
   Toujours lire le schema du serveur AVANT d'inventer une charge utile.
   `backend/app/schemas.py` fait foi. Quatre fois de suite, une entree
   ecrite de memoire a fait passer une vue pour cassee - ou pour saine :
     - `score` au lieu de `valeur` : les cinq barres de sante ne
       s'affichaient jamais, et l'audit croyait couvrir cette zone ;
     - `nb_demandes_30j` absent : « undefined » ecrit en toutes lettres ;
     - `message`/`lue`/`created_at` au lieu de `sous_titre`/`lu`/`date` :
       les notifications perdaient leur sous-titre et leur date ;
     - une source d'avis inventee : le libelle brut s'affichait.
   Une charge utile fausse ne teste rien ; elle deplace juste le bug dans
   l'outil de test, ou il est bien plus difficile a voir.

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
// Une heure d'AUJOURD'HUI, posee sur l'horloge locale puis convertie en UTC -
// comme le fait le formulaire de rendez-vous (planningLocalToUtcIso).
const hg = (h, m = 0) => { const d = new Date(); d.setHours(h, m, 0, 0); return d.toISOString(); };
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
// Un devis SIGNE en plus : c'est le seul statut qui fait apparaitre « Tout
// preparer » et « Convertir en facture ». Avec un unique devis « consulte »,
// les deux enchainements les plus structurants du produit n'existaient sur
// aucun ecran auditable.
Api.listDevis = (function (base) {
  return async (...a) => [
    ...(await base(...a)),
    { id: 90, client_id: 2, client_nom: "Roussel", numero: "DV-2026-090", titre: "Remplacement de chauffe-eau", description: null, taux_tva: 10, acompte_pourcentage: 40, remise_pourcentage: 0, montant_ht: 2180, montant_ttc: 2398, statut: "signe", date_envoi: tg(14), date_consultation: tg(12), date_derniere_relance: null, date_signature: tg(5), nom_signataire: "M. Roussel", nb_relances: 0, source: "site_vitrine", token: "t90", relance_manuelle_possible: false, created_at: tg(16), lignes: [{ id: 2, description: "Chauffe-eau thermodynamique 200 L, pose comprise", quantite: 1, unite: "u", prix_unitaire_ht: 2180 }] },
  ];
})(Api.listDevis);
Api.devisARelancer = async () => [];
Api.listFactures = async () => [
  { id: 14, client_id: 1, client_nom: "Bertrand", devis_id: null, chantier_id: null, contrat_id: null, numero: "FA-2026-014", type: "standard", taux_tva: 20, statut: "envoyee", montant_ht: 1533, montant_ttc: 1840, montant_paye: 0, montant_restant: 1840, est_en_retard: true, date_emission: jg(-40), date_echeance: jg(-12), date_envoi: tg(40), notes: null, date_derniere_relance: null, nb_relances: 0, token: "f14", created_at: tg(40), paiements: [] },
];
Api.facturesARelancer = async () => [];
// Les deux conversions devis -> facture et devis -> chantier n'etaient pas
// simulees : sans backend elles echouaient sur une erreur reseau, et les deux
// enchainements les plus structurants du produit restaient hors d'atteinte de
// tout audit. Elles renvoient ici les memes formes que le serveur
// (FactureOut, PreparerChantierOut), et donc un `id` reellement ouvrable.
// On capture les listes AVANT que listerOuArchives() ne les enveloppe plus
// bas : sinon ces deux appels suivraient le filtre « archives » de la vue et
// pourraient ne rien renvoyer.
const facturesBrutes = Api.listFactures;
const chantiersBruts = Api.listChantiers;
Api.factureDepuisDevis = async () => (await facturesBrutes())[0];
Api.preparerChantierDepuisDevis = async () => ({
  chantier: (await chantiersBruts())[0],
  facture_acompte: null,
  nb_taches_creees: 3,
});
Api.listTaches = async () => [
  { id: 1, artisan_id: 1, client_id: null, chantier_id: 2, titre: "Commander le carrelage pour la salle de bain", description: null, priorite: "urgente", echeance: jg(-3), statut: "a_faire", created_at: tg(5) },
];
Api.listDocuments = async () => [
  { id: 1, nom: "Photo avant travaux", type: "photo", url: null, nom_original: "photo.jpg", taille_octets: 240000, client_id: null, chantier_id: 2, created_at: tg(3) },
];
// PlanningItem porte desormais `date_fin` (routers/planning.py), qui reste
// null quand l'artisan n'a pas precise de duree. Les trois etats de la grille
// doivent etre representes, sinon on ne verifie qu'un tiers de la vue :
//   - un creneau borne (date_fin renseignee) ;
//   - un debut sans fin connue, dessine en repere ;
//   - deux items sans heure du tout (echeance de tache, debut de chantier),
//     que le serveur ancre a 9h00 et 8h00 pour les trier - ces heures ne
//     doivent JAMAIS se retrouver sur l'axe horaire.
Api.planning = async () => {
  const a = (h, m = 0) => { const d = new Date(); d.setHours(h, m, 0, 0); return d.toISOString(); };
  const demain = (h, m = 0) => { const d = new Date(); d.setDate(d.getDate() + 1); d.setHours(h, m, 0, 0); return d.toISOString(); };
  return [
    { date: a(9), date_fin: a(10, 30), type: "rdv", titre: "Métré chez Mme Roussel", reference_id: 1, client_id: 2, chantier_id: null, lieu: "Lyon 3e" },
    { date: a(14), date_fin: null, type: "visite", titre: "Visite de chantier Ducros", reference_id: 2, client_id: 1, chantier_id: 2, lieu: "Écully" },
    { date: a(15, 30), date_fin: a(15, 45), type: "intervention", titre: "Reprise joint salle de bain", reference_id: 3, client_id: 1, chantier_id: null, lieu: null },
    { date: a(9), date_fin: null, type: "tache", titre: "Commander le carrelage", reference_id: 1, client_id: null, chantier_id: 2, lieu: null },
    { date: demain(8), date_fin: null, type: "chantier_debut", titre: "Début chantier : Villa Ducros", reference_id: 2, client_id: 1, chantier_id: 2, lieu: null },
  ];
};
// Le serveur renvoie DOUZE mois pleins, mois en cours compris et mois sans
// encaissement a zero (routers/analytics.py). Les creux comptent autant que
// les pics : c'est justement ce que l'ancienne serie - construite sur les
// seuls mois encaissants - effacait du graphique. Le dernier mois est
// volontairement bas : il est en cours, et la vue doit le montrer comme tel
// plutot que comme un effondrement.
Api.analytics = async () => ({ ca_par_mois: [3100, 0, 4200, 5100, 0, 0, 6400, 8100, 7300, 9200, 11650, 1480].map((ca, i) => { const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() - (11 - i)); return { mois: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`, ca }; }), valeur_pipeline: 42100, montant_impayes: 13340, nb_devis_total: 48, nb_devis_signes: 21, nb_clients_acquis: 18, nb_clients_recurrents: 7, taux_acceptation: 58, panier_moyen: 6420, delai_moyen_paiement_jours: 34, sources_acquisition: [{ source: "site_vitrine", nb_clients: 15, nb_gagnes: 5, ca: 31200 }] });
// AvisOut : la source est requise et porte un libelle (AVIS_SOURCE_LABELS),
// l'etat de publication s'appelle `publie_site`. Le jeu d'essai disait
// `publie` et omettait `source` : la carte affichait « undefined » a cote de
// la date, et l'onglet « Publies » restait vide quoi qu'il arrive.
Api.listAvis = async () => [
  { id: 1, artisan_id: 1, client_id: 1, client_nom: "Bertrand", note: 5, commentaire: "Travail soigné, délais tenus, je recommande sans hésiter.", nom_auteur: null, source: "lien_public", publie_site: true, created_at: tg(10) },
  { id: 2, artisan_id: 1, client_id: null, client_nom: null, note: 4, commentaire: "Bonne intervention, un peu de retard le premier jour.", nom_auteur: "M. Delaunay", source: "manuel", publie_site: false, created_at: tg(26) },
  { id: 3, artisan_id: 1, client_id: 2, client_nom: "Roussel", note: 5, commentaire: null, nom_auteur: null, source: "lien_public", publie_site: false, created_at: tg(3) },
];
// NotificationOut : `sous_titre`, `urgent`, `date`, `view`, `lu`. Le jeu
// d'essai inventait `message`, `lue` et `created_at` : la ligne perdait son
// sous-titre, affichait « undefined » a la place de la date, et aucune
// notification ne pouvait tomber dans le groupe « A traiter ». Les cinq
// ci-dessous couvrent les quatre groupes et les trois modules.
// `id` n'est PAS un numero de notification : le serveur y met l'identifiant
// de la piece visee (routers/notifications.py) - le devis a relancer, la
// facture impayee, l'item de conformite. C'est `notification_id` qui identifie
// la notification elle-meme, et lui seul sert a la marquer lue. Le jeu d'essai
// numerotait les deux 1..5 : « Voir la facture » cherchait donc la facture
// n°1, qui n'existe pas, et retombait sur la liste - la vue paraissait cassee
// alors que seul le jeu d'essai l'etait.
Api.listNotifications = async () => [
  { id: 14, type: "facture_relance", notification_id: 1, client_id: 1, titre: "Facture FA-2026-014 en retard de 12 jours", sous_titre: "Bertrand · 1 840,00 € restent à encaisser", urgent: true, date: tg(0.2), view: "factures", lu: false },
  { id: 3, type: "conformite", notification_id: 2, client_id: null, titre: "Assurance décennale à renouveler", sous_titre: "AXA · échéance dans 21 jours", urgent: true, date: tg(0.6), view: "entreprise", lu: false },
  { id: 89, type: "devis_relance", notification_id: 3, client_id: 1, titre: "Devis DV-2026-089 lu, sans réponse", sous_titre: "Bertrand · consulté hier, 2 relances envoyées", urgent: false, date: tg(0.4), view: "devis", lu: false },
  { id: 2, type: "nouvelle_demande_devis", notification_id: 4, client_id: 2, titre: "Nouvelle demande depuis le site", sous_titre: "Roussel · remplacement de chauffe-eau", urgent: false, date: tg(1.3), view: "prospects", lu: true },
  { id: 5, type: "message_client", notification_id: 5, client_id: 1, titre: "Message de Bertrand", sous_titre: "« Peut-on décaler la visite de mardi ? »", urgent: false, date: tg(6), view: "prospects", lu: true },
];
Api.dashboard = async () => ({ finances: { ca_mois: 18420, a_encaisser: 1840, paiements_recents: [{ date_paiement: jg(-2), moyen: "Virement", montant: 4200 }] }, commercial: { devis_en_attente: 7, valeur_pipeline: 42100 }, aujourdhui: { factures_en_retard: [{ id: 14, numero: "FA-2026-014", client_nom: "Bertrand", montant_restant: 1840 }], devis_a_relancer: [{ id: 89, numero: "DV-2026-089", client_nom: "Bertrand", relance_manuelle_possible: true }], taches: [{ id: 1, titre: "Commander le carrelage" }], chantiers_a_venir: [{ id: 2, titre: "Villa Ducros — extension côté jardin", date_debut: jg(4) }], evenements: [
  // EvenementOut complet : l'accueil ouvre desormais le rendez-vous lui-meme,
  // il lui faut donc type, client et lieu. Un avec duree, un sans : les deux
  // rendus de l'heure doivent etre visibles sur l'ecran d'accueil.
  { id: 1, artisan_id: 1, client_id: 2, chantier_id: null, titre: "Métré chez Mme Roussel", type: "rdv", date_debut: hg(9), date_fin: hg(10, 30), lieu: "Lyon 3e", notes: null },
  { id: 2, artisan_id: 1, client_id: 1, chantier_id: 2, titre: "Visite de chantier Ducros", type: "visite", date_debut: hg(14), date_fin: null, lieu: "Écully", notes: null },
] }, alertes_conformite: [], presence_site: { statut: "livre", url: "https://exemple.fr", nb_demandes_total: 9, nb_demandes_30j: 3, nb_clients_gagnes: 2, ca_genere: 12400, taux_conversion: 22.2 } });
// RecommandationOut porte toujours une `view`, et parfois un `reference_id`
// quand la phrase designe une piece precise (routers/dashboard.py). Les deux
// cas doivent etre representes : l'un ouvre la liste, l'autre le chantier.
Api.dashboardRecommandations = async () => [
  { message: "Trois devis de plus de 30 jours n'ont jamais été relancés.", urgence: "haute", view: "devis", reference_id: null },
  { message: "Le chantier 'Villa Ducros — extension côté jardin' dépasse actuellement son budget de 12 %.", urgence: "haute", view: "chantiers", reference_id: 2 },
];
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

// ---------------------------------------------------------------------
// L'ENTREPRISE. Cette page lit `currentArtisan` - une liaison lexicale de
// premier niveau d'app.js, donc absente de `window` mais accessible en
// ecriture depuis n'importe quel script. Sans elle, loadEntrepriseForm()
// levait sur `currentArtisan.nom_entreprise` et la vue restait vide :
// c'est la raison pour laquelle Entreprise n'avait jamais ete auditee.
// ---------------------------------------------------------------------
currentArtisan = {
  id: 1, nom_entreprise: "Bertin & Fils", metier: "plombier",
  email: "contact@bertin-plomberie.fr", telephone: "04 78 55 12 40",
  ville: "Villeurbanne", code_postal: "69100", adresse: "14 rue des Charmilles",
  siret: "812 456 789 00021", assurance_decennale_nom: "AXA",
  assurance_decennale_numero: "DEC-2026-4471", assurance_decennale_echeance: jg(120),
  photo_url: null, role: "administrateur", plan: "business", onboarding_termine: true,
  relance_devis_j1: 3, relance_devis_j2: 7, relance_devis_j3: 15, relance_facture_jours: 5,
};
Api.me = async () => currentArtisan;
Api.updateMe = async (p) => Object.assign(currentArtisan, p);
// PrestationOut : le libelle s'appelle `description` - il n'y a pas de champ
// `nom` - et `taux_tva` est requis. Ecrite de memoire, cette entree affichait
// « TVA undefined% » et deux lignes sur trois sans titre.
Api.listPrestations = async () => [
  { id: 1, artisan_id: 1, description: "Remplacement d'un chauffe-eau 200 L", categorie: "Sanitaire", unite: "u", prix_unitaire_ht: 940, taux_tva: 10, created_at: tg(90) },
  { id: 2, artisan_id: 1, description: "Recherche de fuite non destructive", categorie: "Dépannage", unite: "u", prix_unitaire_ht: 180, taux_tva: 20, created_at: tg(60) },
  { id: 3, artisan_id: 1, description: "Pose de carrelage mural", categorie: null, unite: "m2", prix_unitaire_ht: 45.5, taux_tva: 10, created_at: tg(30) },
];
// FournisseurOut : `contact_nom`, pas `contact`, et `categorie` est requise.
Api.listFournisseurs = async () => [
  { id: 1, nom: "Point P Villeurbanne", categorie: "Matériaux", contact_nom: "M. Sanchez", telephone: "04 72 10 88 00", email: "villeurbanne@pointp.fr", adresse: "22 rue Léon Blum", notes: "Remise 12 % sur le sanitaire." },
  { id: 2, nom: "Cedeo Lyon Est", categorie: "Sanitaire", contact_nom: null, telephone: "04 78 03 41 12", email: null, adresse: null, notes: null },
];
Api.listEquipe = async () => [
  { id: 1, artisan_id: 1, nom: "Karim Bertin", email: "karim@bertin-plomberie.fr", role: "administrateur", actif: true, created_at: tg(400) },
  // Les deux seuls roles du modele sont `administrateur` et `salarie`.
  { id: 2, artisan_id: 1, nom: "Léa Fournier", email: "lea@bertin-plomberie.fr", role: "salarie", actif: true, created_at: tg(120) },
];
// ContratOut : `frequence` et `statut`, pas `periodicite`/`actif`.
Api.listContrats = async () => [
  { id: 1, client_id: 1, client_nom: "Bertrand", titre: "Entretien annuel chaudière", montant_ht: 180, taux_tva: 10, frequence: "annuel", statut: "actif", prochaine_echeance: jg(45), derniere_generation: jg(-320), nb_factures_generees: 3, created_at: tg(400) },
];
// ConformiteOut : `libelle`, `date_expiration`, `jours_restants`, `alerte`.
Api.listConformite = async () => [
  { id: 1, artisan_id: 1, type: "assurance_decennale", libelle: "Assurance décennale AXA", date_expiration: jg(21), document_url: null, created_at: tg(300), alerte: true, jours_restants: 21 },
  { id: 2, artisan_id: 1, type: "qualibat", libelle: "Qualification Qualibat 5111", date_expiration: jg(210), document_url: null, created_at: tg(300), alerte: false, jours_restants: 210 },
];
Api.conformiteAlertes = async () => [
  { id: 1, artisan_id: 1, type: "assurance_decennale", libelle: "Assurance décennale AXA", date_expiration: jg(21), document_url: null, created_at: tg(300), alerte: true, jours_restants: 21 },
];
// AutomationStatutOut : etat systeme du moteur, pas des compteurs par artisan.
Api.automationStatus = async () => ({
  email_configure: true, fournisseur: "Resend", intervalle_minutes: 60,
  derniere_execution: tg(0.05),
  derniere_execution_resume: "3 devis relances, 1 facture relancee, 4 emails envoyes, 0 non configures, 0 erreurs",
  prochaine_execution_estimee: new Date(Date.now() + 42 * 60000).toISOString(),
});
Api.listSiteMedia = async () => ({ photos: [], logo_url: null });

// La recherche globale (Ctrl+K). SearchResult : type, id, label, sublabel.
Api.search = async (q) => {
  const tout = [
    { type: "client", id: 1, label: "Bertrand", sublabel: "Bertrand & Fils · Villeurbanne" },
    { type: "devis", id: 89, label: "DV-2026-089", sublabel: "Rénovation salle de bain complète · 1 466,93 €" },
    { type: "facture", id: 14, label: "FA-2026-014", sublabel: "Bertrand · 1 840,00 € · en retard" },
    { type: "chantier", id: 2, label: "Villa Ducros — extension côté jardin", sublabel: "Bertrand · Écully · en cours" },
  ];
  const t = String(q || "").toLowerCase();
  return tout.filter((r) => (r.label + " " + r.sublabel).toLowerCase().includes(t));
};

// Les listes d'archives : les memes appels que les listes vivantes, avec le
// drapeau `archive`. Sans eux, le panneau Archives s'ouvrait sur une erreur.
const archivés = {
  clients: [{ id: 9, nom: "Menuiserie Delcourt", societe: null, statut: "perdu", ville: "Lyon 7e", created_at: tg(300) }],
  devis: [{ id: 41, numero: "DV-2025-041", titre: "Réfection de toiture", client_nom: "Menuiserie Delcourt", statut: "perdu", montant_ttc: 8400, created_at: tg(280) }],
  factures: [{ id: 7, numero: "FA-2025-007", client_nom: "Menuiserie Delcourt", statut: "annulee", montant_ttc: 1200, created_at: tg(260) }],
  chantiers: [{ id: 5, titre: "Cuisine Marchand", client_nom: "Marchand", statut: "termine", created_at: tg(400) }],
  documents: [{ id: 4, nom: "Ancienne attestation décennale", type: "attestation", created_at: tg(500) }],
};
const listerOuArchives = (vivants, cle) => async (_id, archive) => (archive ? archivés[cle] : vivants());
Api.listClients = listerOuArchives(Api.listClients, "clients");
Api.listDevis = listerOuArchives(Api.listDevis, "devis");
Api.listFactures = listerOuArchives(Api.listFactures, "factures");
Api.listChantiers = listerOuArchives(Api.listChantiers, "chantiers");
Api.listDocuments = listerOuArchives(Api.listDocuments, "documents");

// ---------------------------------------------------------------------
// LA FICHE CLIENT (panneau lateral). Sans ces trois entrees, le panneau
// s'ouvrait sur « Impossible de contacter le serveur » : l'un des ecrans
// les plus frequentes du produit n'avait jamais pu etre regarde.
// ---------------------------------------------------------------------
Api.clientResume = async () => ({
  valeur_totale: 31000, nb_chantiers: 2, dernier_contact: tg(2),
  impayes: 1840, date_dernier_devis: tg(12),
});
Api.clientTimeline = async () => [
  { date: tg(1), type: "devis_consulte", label: "Devis DV-2026-089 consulté par le client", reference_id: 89 },
  { date: tg(9), type: "devis_envoye", label: "Devis DV-2026-089 envoyé", reference_id: 89 },
  { date: tg(40), type: "facture_envoyee", label: "Facture FA-2026-014 envoyée", reference_id: 14 },
  { date: tg(70), type: "chantier_demarre", label: "Chantier « Villa Ducros » démarré", reference_id: 2 },
  { date: tg(60), type: "client_cree", label: "Client créé", reference_id: null },
];
Api.listClientMessages = async () => [
  { id: 1, expediteur: "client", texte: "Peut-on décaler la visite de mardi ?", lu: false, created_at: tg(6) },
  { id: 2, expediteur: "artisan", texte: "Bien sûr, je vous propose jeudi 9h.", lu: true, created_at: tg(5) },
];
})();
