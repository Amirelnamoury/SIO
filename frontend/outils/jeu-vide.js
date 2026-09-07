/* =====================================================================
   Jeu d'essai VIDE — le premier jour d'un artisan
   ---------------------------------------------------------------------
   Le pendant de jeu-essai.js : un compte qui vient d'etre cree, sans un
   client, sans un devis, sans un chantier.

   POURQUOI IL EXISTE
   L'application compte 41 etats vides. Aucun n'avait jamais ete rendu a
   l'ecran : le jeu d'essai a toujours des donnees, donc `.empty-state` ne
   s'affichait jamais. C'est le symetrique exact du piege inverse - « une
   vue vide ne deborde jamais et ne prouve rien » - avec la meme
   consequence : une vue jamais vide ne montre jamais son etat vide.

   Or c'est TOUT ce qu'un nouvel inscrit voit. Treize ecrans sans une
   ligne, avant meme d'avoir saisi son premier contact. C'est la premiere
   impression du produit, et elle n'avait jamais ete regardee.

   Comme son jumeau : lire `backend/app/schemas.py` avant d'inventer une
   charge utile. Ici, la forme compte autant que le vide - un objet dont
   les compteurs valent zero n'est pas la meme chose qu'un objet absent.
   ===================================================================== */
(function () {
const vide = async () => [];

Api.listClients = vide;
Api.listChantiers = vide;
Api.listDevis = vide;
Api.devisARelancer = vide;
Api.listFactures = vide;
Api.facturesARelancer = vide;
Api.listTaches = vide;
Api.listDocuments = vide;
Api.listConformite = vide;
Api.conformiteAlertes = vide;
Api.planning = vide;
Api.listAvis = vide;
Api.listNotifications = vide;
Api.listPrestations = vide;
Api.listFournisseurs = vide;
Api.listEquipe = vide;
Api.listContrats = vide;

// Le tableau de bord renvoie bien un objet : ses sections existent, leurs
// listes sont vides et ses compteurs a zero. Un artisan sans activite n'a
// pas un dashboard absent, il a un dashboard qui n'a rien a dire.
Api.dashboard = async () => ({
  finances: { ca_mois: 0, a_encaisser: 0, paiements_recents: [] },
  commercial: { devis_en_attente: 0, valeur_pipeline: 0 },
  aujourdhui: { factures_en_retard: [], devis_a_relancer: [], taches: [], chantiers_a_venir: [], evenements: [] },
  alertes_conformite: [],
  presence_site: { statut: "non_livre", url: null, nb_demandes_total: 0, nb_demandes_30j: 0, nb_clients_gagnes: 0, ca_genere: 0, taux_conversion: null },
});
Api.dashboardRecommandations = vide;
// Aucun sous-score ne peut etre calcule honnetement : `valeur` est nulle et
// `raison_absence` dit pourquoi. C'est le cas que le schema prevoit.
Api.dashboardSante = async () => ({
  score_global: null,
  raison_absence_globale: "Pas encore assez de données pour calculer un score global",
  commercial: { label: "Commercial", valeur: null, raison_absence: "Pas assez de devis décidés pour juger (minimum 3)" },
  tresorerie: { label: "Trésorerie", valeur: null, raison_absence: "Aucune facture pour le moment" },
  chantiers: { label: "Chantiers", valeur: null, raison_absence: "Aucun chantier avec budget renseigné" },
  conformite: { label: "Conformité", valeur: null, raison_absence: "Aucune information de conformité enregistrée" },
  organisation: { label: "Organisation", valeur: null, raison_absence: "Aucune tâche avec échéance pour le moment" },
});
Api.dashboardActivation = async () => ({
  entierement_active: false, entreprise_configuree: false,
  premier_client: false, premier_devis: false, premiere_facture: false,
});
Api.analytics = async () => ({
  ca_par_mois: [], valeur_pipeline: 0, montant_impayes: 0,
  nb_devis_total: 0, nb_devis_signes: 0, nb_clients_acquis: 0, nb_clients_recurrents: 0,
  taux_acceptation: null, panier_moyen: null, delai_moyen_paiement_jours: null,
  sources_acquisition: [],
});
Api.automationStatus = async () => ({
  email_configure: false, fournisseur: "Resend", intervalle_minutes: 60,
  derniere_execution: null, derniere_execution_resume: null, prochaine_execution_estimee: null,
});
Api.listSiteMedia = async () => ({ photos: [], logo_url: null });

// Un artisan qui vient de s'inscrire n'a renseigne que ce que le
// formulaire d'inscription exige : le nom, le metier, l'email. Tout le
// reste est vide - et c'est exactement l'etat que la page Entreprise doit
// savoir presenter.
currentArtisan = {
  id: 1, nom_entreprise: "Ravel Rénovation", metier: "general",
  email: "contact@ravel-renovation.fr", telephone: null,
  ville: null, code_postal: null, adresse: null,
  siret: null, assurance_decennale_nom: null, assurance_decennale_numero: null,
  assurance_decennale_echeance: null,
  photo_url: null, role: "administrateur", plan: "gratuit", onboarding_termine: true,
  relance_devis_j1: 3, relance_devis_j2: 7, relance_devis_j3: 15, relance_facture_jours: 5,
};
Api.me = async () => currentArtisan;
Api.updateMe = async (p) => Object.assign(currentArtisan, p);
window.hasPlan = () => true;
})();
