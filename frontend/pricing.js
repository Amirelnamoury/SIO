// Source unique des tarifs Suite Artisan, partagée entre la page d'accueil
// (landing.html) et l'application (index.html / app.js) pour éviter que les
// prix affichés divergent d'un endroit à l'autre.
//
// Les 4 plans correspondent exactement aux frontières appliquées côté
// backend (voir app/deps.py, PLAN_ORDRE) : chaque plan inclut tout ce que
// le précédent débloque, plus une seule couche de valeur en plus - pas de
// matrice de permissions élaborée.
const PRICING = {
  gratuit: {
    nom: "Gratuit",
    prix: 0,
    periode: "mois",
    accroche: "Démarrez et gérez vos premiers clients gratuitement.",
    positionnement: "Découvrez Suite Artisan et commencez à organiser votre activité sans engagement.",
    fonctionnalites: [
      "CRM clients et prospects",
      "Devis illimités",
      "PDF devis",
      "Tâches",
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
    accroche: "Gérez vos chantiers et votre facturation au même endroit.",
    positionnement: "Pour l'artisan qui veut structurer son activité et suivre son entreprise au quotidien.",
    fonctionnalites: [
      "Tout le plan Gratuit, plus :",
      "Factures et paiements",
      "Chantiers",
      "Suivi budget, marge et heures",
      "Conformité",
      "Analytics et statistiques",
      "Identification des factures à relancer",
      "Relance manuelle des factures",
    ],
  },
  pro: {
    nom: "Pro",
    prix: 39,
    periode: "mois",
    mention: "HT, sans engagement",
    recommande: true,
    accroche: "Automatisez votre gestion et gagnez du temps chaque semaine.",
    positionnement: "Pour l'artisan qui ne veut plus perdre de temps sur les relances et les tâches répétitives.",
    fonctionnalites: [
      "Tout le plan Essentiel, plus :",
      "Relances manuelles de devis",
      "Relances automatiques de devis",
      "Relances automatiques de factures",
      "Contrats récurrents",
      "Génération et facturation automatique des contrats récurrents",
    ],
  },
  business: {
    nom: "Business",
    prix: 69,
    periode: "mois",
    mention: "HT, sans engagement",
    accroche: "Pilotez votre entreprise et travaillez efficacement en équipe.",
    positionnement: "Pour les entreprises artisanales avec plusieurs collaborateurs.",
    fonctionnalites: [
      "Tout le plan Pro, plus :",
      "Comptes collaborateurs",
      "Gestion de l'équipe",
      "Rôles et permissions",
      "Données partagées dans l'entreprise",
    ],
  },
};

const PRICING_ORDRE = ["gratuit", "essentiel", "pro", "business"];

const SITE_VITRINE_OFFER = {
  nom: "Site vitrine professionnel",
  creation: 490,
  mensuel: 19,
  mention: "HT",
  disponibleAvec: [...PRICING_ORDRE],
  accroche: "Votre site professionnel, créé et géré par Suite Artisan.",
  description: "On crée votre site, on le met en ligne et on s'occupe de sa gestion technique. Vos demandes de devis arrivent directement dans Suite Artisan.",
  resumeInclus: "Hébergement sécurisé, SSL, maintenance technique, gestion du domaine standard et connexion à Suite Artisan inclus.",
  carteInclus: [
    "Création et mise en ligne initiale",
    "Gestion et maintenance du site",
    "Petites modifications ponctuelles du contenu existant",
    "Formulaire connecté au CRM Suite Artisan",
  ],
  creationInclut: [
    "Création et personnalisation du site professionnel",
    "Adaptation au métier de l'artisan",
    "Personnalisation de l'entreprise, des coordonnées, de la zone géographique et des services",
    "Adaptation des contenus nécessaires au site",
    "Configuration responsive desktop et mobile",
    "Intégration du formulaire de demande de devis",
    "Connexion du formulaire au CRM Suite Artisan",
    "Configuration initiale du domaine",
    "Configuration HTTPS et SSL",
    "Préparation technique et vérifications avant publication",
    "Mise en ligne initiale",
  ],
  maintenanceInclut: [
    "Hébergement et maintien du site accessible en ligne",
    "Certificat SSL et HTTPS",
    "Maintenance et corrections techniques nécessaires au bon fonctionnement",
    "Gestion technique du domaine standard",
    "Renouvellement d'un domaine standard selon les conditions commerciales",
    "Connexion continue du formulaire au CRM Suite Artisan",
    "Maintenance de compatibilité",
    "Support en cas de dysfonctionnement technique du site",
    "Petites modifications ponctuelles du contenu existant dans une limite raisonnable",
  ],
  domaineStandard: "Nom de domaine standard inclus dans la limite de 15 EUR HT/an. Une extension ou un domaine plus coûteux peut faire l'objet d'un supplément. Le domaine reste transférable au client en cas de départ, selon les conditions contractuelles applicables.",
  horsForfaitResume: "Les évolutions importantes, nouvelles pages, refontes, contenus ou fonctionnalités spécifiques sont réalisées sur devis.",
  horsForfait: [
    "Nouvelle page importante ou section complexe",
    "Refonte graphique, changement complet de design ou de structure",
    "Réécriture complète ou création régulière de contenus et d'articles",
    "Shooting photo ou vidéo, logo ou nouvelle identité visuelle",
    "SEO avancé, campagnes publicitaires ou gestion des réseaux sociaux",
    "Fonctionnalités sur mesure, espace client, e-commerce ou réservation complexe",
    "Intégrations externes spécifiques ou ajout massif de contenus",
    "Migration ou refonte importante après livraison",
    "Intervention liée à un service tiers choisi par le client",
    "Domaine premium ou extension dépassant le plafond prévu",
  ],
};
