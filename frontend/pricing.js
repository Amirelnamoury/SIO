// Source unique des tarifs Suite Artisan, partagee entre la page d'accueil
// (landing.html) et l'application (index.html / app.js) pour eviter que les
// prix affiches divergent d'un endroit a l'autre.
//
// Les 4 plans correspondent exactement aux frontieres appliquees cote
// backend (voir app/deps.py, PLAN_ORDRE) : chaque plan inclut tout ce que
// le precedent debloque, plus une seule couche de valeur en plus - pas de
// matrice de permissions elaboree.
const PRICING = {
  gratuit: {
    nom: "Gratuit",
    prix: 0,
    periode: null,
    accroche: "Pour demarrer, sans carte bancaire",
    fonctionnalites: [
      "Clients & prospects (CRM) illimites",
      "Devis illimites avec PDF pro",
      "Taches et planning",
      "Documents (attestations, photos, contrats)",
      "Tableau de bord \"a faire aujourd'hui\"",
    ],
  },
  essentiel: {
    nom: "Essentiel",
    prix: 19,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Pour facturer et suivre vos chantiers",
    fonctionnalites: [
      "Tout le plan Gratuit, plus :",
      "Factures et paiements (acomptes, echeances)",
      "Suivi de chantiers (budget, marge, heures, documents)",
      "Conformite : alertes assurance decennale, Qualibat, RGE",
      "Statistiques d'activite (CA, taux de transformation...)",
    ],
  },
  pro: {
    nom: "Pro",
    prix: 39,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Ne relancez plus rien a la main",
    fonctionnalites: [
      "Tout le plan Essentiel, plus :",
      "Relances automatiques de devis (email, plusieurs paliers)",
      "Contrats recurrents facture automatiquement",
      "Le temps gagne rembourse largement l'abonnement",
    ],
  },
  business: {
    nom: "Business",
    prix: 79,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Pour piloter avec votre equipe",
    fonctionnalites: [
      "Tout le plan Pro, plus :",
      "Comptes illimites pour vos collaborateurs",
      "Roles et permissions (administrateur / salarie)",
      "Donnees partagees sur toute l'entreprise",
    ],
  },
};

const PRICING_ORDRE = ["gratuit", "essentiel", "pro", "business"];
