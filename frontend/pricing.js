// Source unique des tarifs Suite Artisan, partagee entre la page d'accueil
// (landing.html) et l'application (index.html / app.js) pour eviter que les
// prix affiches divergent d'un endroit a l'autre.
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
  pro: {
    nom: "Suite Artisan Pro",
    prix: 27,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Pour piloter vraiment votre activite",
    fonctionnalites: [
      "Tout le plan Gratuit, plus :",
      "Relances automatiques de devis",
      "Suivi de chantiers (budget, marge, documents)",
      "Conformite : alertes assurance decennale, Qualibat, RGE",
      "Statistiques d'activite (CA, taux de transformation...)",
    ],
  },
};
