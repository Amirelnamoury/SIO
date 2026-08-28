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
    periode: "mois",
    accroche: "Demarrez et gerez vos premiers clients gratuitement.",
    positionnement: "Decouvrez Suite Artisan et commencez a organiser votre activite sans engagement.",
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
    accroche: "Gerez vos chantiers et votre facturation au meme endroit.",
    positionnement: "Pour l'artisan qui veut structurer son activite et suivre son entreprise au quotidien.",
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
    recommande: true,
    accroche: "Automatisez votre gestion et gagnez du temps chaque semaine.",
    positionnement: "Pour l'artisan qui ne veut plus perdre de temps sur les relances et les taches repetitives.",
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
    accroche: "Pilotez votre entreprise et travaillez efficacement en equipe.",
    positionnement: "Pour les entreprises artisanales avec plusieurs collaborateurs.",
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
  disponibleAvec: [...PRICING_ORDRE],
  accroche: "Votre site professionnel, cree et gere par Suite Artisan.",
  description: "On cree votre site, on le met en ligne et on s'occupe de sa gestion technique. Vos demandes de devis arrivent directement dans Suite Artisan.",
  resumeInclus: "Hebergement securise, SSL, maintenance technique, gestion du domaine standard et connexion a Suite Artisan inclus.",
  carteInclus: [
    "Creation et mise en ligne initiale",
    "Gestion et maintenance du site",
    "Petites modifications ponctuelles du contenu existant",
    "Formulaire connecte au CRM Suite Artisan",
  ],
  creationInclut: [
    "Creation et personnalisation du site professionnel",
    "Adaptation au metier de l'artisan",
    "Personnalisation de l'entreprise, des coordonnees, de la zone geographique et des services",
    "Adaptation des contenus necessaires au site",
    "Configuration responsive desktop et mobile",
    "Integration du formulaire de demande de devis",
    "Connexion du formulaire au CRM Suite Artisan",
    "Configuration initiale du domaine",
    "Configuration HTTPS et SSL",
    "Preparation technique et verifications avant publication",
    "Mise en ligne initiale",
  ],
  maintenanceInclut: [
    "Hebergement et maintien du site accessible en ligne",
    "Certificat SSL et HTTPS",
    "Maintenance et corrections techniques necessaires au bon fonctionnement",
    "Gestion technique du domaine standard",
    "Renouvellement d'un domaine standard selon les conditions commerciales",
    "Connexion continue du formulaire au CRM Suite Artisan",
    "Maintenance de compatibilite",
    "Support en cas de dysfonctionnement technique du site",
    "Petites modifications ponctuelles du contenu existant dans une limite raisonnable",
  ],
  domaineStandard: "Nom de domaine standard inclus dans la limite de 15 EUR HT/an. Une extension ou un domaine plus couteux peut faire l'objet d'un supplement. Le domaine reste transferable au client en cas de depart, selon les conditions contractuelles applicables.",
  horsForfaitResume: "Les evolutions importantes, nouvelles pages, refontes, contenus ou fonctionnalites specifiques sont realisees sur devis.",
  horsForfait: [
    "Nouvelle page importante ou section complexe",
    "Refonte graphique, changement complet de design ou de structure",
    "Reecriture complete ou creation reguliere de contenus et d'articles",
    "Shooting photo ou video, logo ou nouvelle identite visuelle",
    "SEO avance, campagnes publicitaires ou gestion des reseaux sociaux",
    "Fonctionnalites sur mesure, espace client, e-commerce ou reservation complexe",
    "Integrations externes specifiques ou ajout massif de contenus",
    "Migration ou refonte importante apres livraison",
    "Intervention liee a un service tiers choisi par le client",
    "Domaine premium ou extension depassant le plafond prevu",
  ],
};
