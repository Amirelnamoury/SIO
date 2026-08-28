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
    accroche: "Trouver, suivre et signer ses clients",
    fonctionnalites: [
      "CRM clients et prospects",
      "Devis illimites",
      "PDF devis",
      "Taches",
      "Planning",
      "Documents",
      "Dashboard",
    ],
  },
  essentiel: {
    nom: "Essentiel",
    prix: 19,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Gerer ses chantiers et sa facturation",
    fonctionnalites: [
      "Tout le plan Gratuit, plus :",
      "Factures et paiements",
      "Chantiers",
      "Suivi budget, marge et heures",
      "Conformite",
      "Analytics et statistiques",
      "Identification des factures a relancer",
      "Relance manuelle des factures",
    ],
  },
  pro: {
    nom: "Pro",
    prix: 39,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Automatiser son entreprise",
    fonctionnalites: [
      "Tout le plan Essentiel, plus :",
      "Relances manuelles de devis",
      "Relances automatiques de devis",
      "Relances automatiques de factures",
      "Contrats recurrents",
      "Generation et facturation automatique des contrats recurrents",
    ],
  },
  business: {
    nom: "Business",
    prix: 69,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Travailler et piloter en equipe",
    fonctionnalites: [
      "Tout le plan Pro, plus :",
      "Comptes collaborateurs",
      "Gestion de l'equipe",
      "Roles et permissions",
      "Donnees partagees dans l'entreprise",
    ],
  },
};

const PRICING_ORDRE = ["gratuit", "essentiel", "pro", "business"];

const SITE_VITRINE_OFFER = {
  nom: "Site vitrine professionnel",
  creation: 490,
  mensuel: 19,
  mention: "HT",
  planMinimum: "essentiel",
  description: "Suite Artisan realise et gere le site pour l'artisan.",
  recurrentInclut: [
    "Hebergement",
    "SSL",
    "Maintenance technique",
    "Connexion du formulaire au CRM Suite Artisan",
    "Gestion d'un domaine standard selon les conditions commerciales",
  ],
};
