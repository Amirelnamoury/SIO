/* =====================================================================
   NAVIGATION — bascule de vue, adresses, ouverture d'un objet
   ---------------------------------------------------------------------
   Deuxieme decoupage de app.js par domaine (Astra §16). Meme regle que
   pour socle.js : aucune ligne n'est reecrite, elles sont deplacees
   telles quelles. Voir docs/DECOUPAGE-FRONTEND.md.

   Ce fichier repond a trois questions, et a elles seules :
     - QUELLE VUE est a l'ecran, et qui la charge (switchView, qui rend la
       promesse de son chargeur pour qu'on puisse ouvrir un objet APRES) ;
     - QUELLE ADRESSE decrit cet etat, dans les deux sens - ecrire l'adresse
       quand on navigue, retrouver l'etat quand on recoit un lien ;
     - COMMENT OUVRIR une piece precise : la trouver en cache ou la demander
       au serveur, l'afficher, et dire quand elle est introuvable.

   Il ne sait rien du contenu des ecrans. Les fonctions d'ouverture
   (showTimeline, showDevisDetail...) vivent dans app.js et sont appelees
   par leur nom - scripts classiques, declarations partagees.

   Charge APRES socle.js et AVANT app.js (voir index.html).
   ===================================================================== */

function switchView(view) {
  // Presentation uniquement : bascule une classe sur <body> pour que la
  // navigation partagee (sidebar/topbar desktop, mobile-topbar/bottom-nav/
  // tiroir "Plus" mobile) adopte le traitement sombre V5 seulement pendant
  // que le dashboard est actif - aucune autre vue n'est affectee (voir
  // style.css, bloc "ATELIER SOMBRE"). body est le seul ancetre commun a
  // #dashboard-screen ET a .bottom-nav/#more-drawer, qui vivent en dehors
  // de #dashboard-screen dans le DOM. Meme mecanisme que .active sur les
  // liens de nav ci-dessous.
  document.body.classList.toggle("is-view-dashboard", view === "dashboard");
  document.body.dataset.view = view;
  document.querySelectorAll(".nav-link").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  // Sur mobile, la nav devient une rangee horizontale scrollable : sans ca,
  // l'onglet actif peut rester hors champ apres un changement de vue
  // programmatique (recherche globale, palette de commandes...).
  const activeLink = document.querySelector(`.nav-link[data-view="${view}"]`);
  if (activeLink && window.matchMedia("(max-width: 900px)").matches) {
    activeLink.scrollIntoView({ inline: "center", block: "nearest" });
  }
  // Le dossier client vit HORS des .view (il occupe leur place sans en etre
  // une, pour que la liste reste montee dessous) : changer de vue doit donc
  // le refermer explicitement, sinon il resterait affiche par-dessus.
  fermerDossier();
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `view-${view}`;
  });
  // L'adresse suit l'ecran. ouvrirObjet() la precisera ensuite avec
  // l'identifiant de la fiche ouverte.
  ecrireAdresse(`#/${view}`);
  // switchView RETOURNE desormais la promesse du chargeur de la vue.
  // Sans elle, tout appelant voulant ouvrir un objet apres la bascule ne
  // pouvait qu'attendre au jugé : `setTimeout(..., 300)`. Un reseau lent
  // ratait la fenetre et l'objet ne s'ouvrait pas ; un reseau rapide
  // attendait pour rien. On attend maintenant le chargement reel.
  const chargeurs = {
    dashboard: loadDashboard, prospects: loadClients, clients: loadClientsDirectory,
    devis: loadDevis, factures: loadFactures, chantiers: loadChantiers,
    planning: loadPlanning, taches: loadTaches, documents: loadDocuments,
    notifications: loadNotifications, statistiques: loadStatistiques, avis: loadAvis,
    // Entreprise ne charge QUE l'onglet consulte. Ouvrir la vue declenchait
    // sept appels d'un coup - equipe, prestations, fournisseurs, conformite,
    // automatisations, contrats - alors qu'un seul panneau est visible et que
    // la plupart des visites ne concernent qu'un onglet. Les autres se
    // chargent a leur premiere ouverture, et une seule fois.
    entreprise: () => chargerOngletEntreprise(ongletEntrepriseActif()),
  };
  return Promise.resolve(chargeurs[view] ? chargeurs[view]() : undefined);
}

/** Ouvre l'OBJET trouve, pas seulement le module qui le contient.
 *
 *  Un resultat de recherche « facture FA-2026-014 » basculait sur la page
 *  Factures et laissait l'artisan la chercher dans la liste - le seul type
 *  qui s'ouvrait vraiment etait le client. La recherche promettait un objet
 *  et livrait un rayon. */
async function ouvrirObjet(type, id) {
  const meta = SEARCH_TYPE_META[type];
  if (!meta) return false;
  // Strict : un attribut vide donne Number("") === 0, un identifiant
  // parfaitement fini qui ferait chercher la piece n°0 - donc un panneau
  // vide ou une erreur, la ou il fallait simplement ouvrir la liste.
  const identifiant = Number(id);
  if (!Number.isInteger(identifiant) || identifiant <= 0) return false;
  await switchView(meta.view);
  // Chaque ouverture rend VRAI ou FAUX. Un devis archive, une fiche
  // supprimee, un identifiant recopie de travers : sans cette reponse,
  // l'artisan restait devant une liste ou rien ne s'ouvrait, sans un mot.
  return ouvrirFiche(type, identifiant);
}

/** Registre des fiches : ou trouver une piece, et comment aller la chercher.
 *
 *  Les panneaux de detail lisaient DIRECTEMENT le cache de la liste affichee
 *  (devisListCache, facturesCache, clientsCache) et sortaient en silence
 *  quand la piece n'y etait pas. Un devis archive, une facture filtree par
 *  statut, un client sur une autre page de la liste : rien ne s'ouvrait, et
 *  rien ne le disait. Le serveur expose pourtant GET /devis/{id},
 *  /factures/{id}, /clients/{id} et /chantiers/{id} depuis le debut - le
 *  frontend ne les appelait simplement jamais.
 *
 *  On garde les caches de liste tels quels : ce sont eux que lisent les
 *  fonctions de rendu, et les reecrire toucherait a tout. On y INSERE la
 *  piece manquante apres etre alle la chercher. */
const REGISTRE_FICHES = {
  devis: {
    dansCache: (id) => devisListCache.some((x) => x.id === id) || (window.__devisTousCache || []).some((x) => x.id === id),
    charger: (id) => Api.getDevis(id),
    memoriser: (piece) => { devisListCache = [...devisListCache, piece]; },
  },
  facture: {
    dansCache: (id) => facturesCache.some((x) => x.id === id),
    charger: (id) => Api.getFacture(id),
    memoriser: (piece) => { facturesCache = [...facturesCache, piece]; },
  },
  client: {
    // Un client peut avoir ete charge par le PIPELINE (clientsCache) ou par
    // l'ANNUAIRE (clientsDirectoryCache.clients) : deux ecrans, deux caches.
    // Ne regarder que le premier faisait redemander au serveur une fiche
    // deja en memoire, a chaque ouverture depuis l'annuaire.
    dansCache: (id) => clientsCache.some((x) => x.id === id)
      || (clientsDirectoryCache.clients || []).some((x) => x.id === id),
    charger: (id) => Api.getClient(id),
    memoriser: (piece) => { clientsCache = [...clientsCache, piece]; },
  },
};

/** Signale, une fois la fiche ouverte, qu'elle ne figure pas dans la liste. */
async function avecAvertissement(horsListe, promesse) {
  const ouvert = await promesse;
  if (ouvert && horsListe) {
    showToast("Cette fiche n'apparaît pas dans la liste affichée : elle est archivée, filtrée, ou sur une autre page.");
  }
  return ouvert;
}

/** S'assure que la piece est connue du cache que lit son panneau.
 *  Rend faux seulement si le SERVEUR ne la connait pas non plus. */
async function assurerFiche(type, identifiant) {
  const entree = REGISTRE_FICHES[type];
  if (!entree) return true;
  if (entree.dansCache(identifiant)) return true;
  try {
    const piece = await entree.charger(identifiant);
    if (!piece || piece.id !== identifiant) return false;
    entree.memoriser(piece);
    return true;
  } catch (err) {
    // 404, 403, reseau : dans tous les cas la fiche ne peut pas s'ouvrir.
    // L'appelant le dira, au lieu de laisser une liste muette.
    return false;
  }
}

// Ou se trouve, dans la page, la ligne qui represente une piece. Sert a
// savoir si la fiche qu'on ouvre est VISIBLE dans la liste derriere elle.
const LIGNE_DE_LISTE = {
  devis: (id) => `#devis-list [data-id="${id}"]`,
  facture: (id) => `#factures-list [data-id="${id}"]`,
  // Un client se regarde depuis deux ecrans : le pipeline en colonnes
  // (Prospects) et l'annuaire (Clients). Ne chercher que dans l'un des deux
  // ferait croire, depuis l'autre, que la fiche est hors liste.
  client: (id) => `#clients-directory [data-id="${id}"], #clients-kanban [data-id="${id}"]`,
};

async function ouvrirFiche(type, identifiant) {
  if (!(await assurerFiche(type, identifiant))) return false;
  // La fiche peut s'ouvrir alors que la liste derriere elle ne la montre pas
  // (filtre en cours, autre page, piece archivee). Sans un mot, la refermer
  // donne l'impression que la piece a disparu.
  const selecteur = LIGNE_DE_LISTE[type]?.(identifiant);
  const horsListe = selecteur && !document.querySelector(selecteur);
  switch (type) {
    case "client": return avecAvertissement(horsListe, showTimeline(identifiant));
    case "devis": return avecAvertissement(horsListe, showDevisDetail(identifiant));
    case "facture": return avecAvertissement(horsListe, showFactureDetail(identifiant));
    case "chantier": {
      // Le chantier n'a pas de panneau : il se deplie dans SA CARTE. Si la
      // carte n'est pas la, c'est un filtre en cours qui la masque - le
      // chantier existe, il est juste hors du tri courant. On leve les
      // filtres une fois, plutot que d'annoncer un chantier introuvable.
      if (!document.querySelector(`[data-chantier-id="${identifiant}"]`)) {
        if (!chantiersCache.some((c) => c.id === identifiant)) return false;
        currentChantierFilter = "";
        currentChantierAvancement = "";
        currentChantierClient = "";
        currentChantierRecherche = "";
        const champ = document.getElementById("chantiers-search");
        if (champ) champ.value = "";
        renderChantiersListFiltered();
        if (!document.querySelector(`[data-chantier-id="${identifiant}"]`)) return false;
        showToast("Les filtres de la liste ont été levés pour afficher ce chantier.");
      }
      chantierFocusId = identifiant;
      focusChantierCard();
      // Le bouton BASCULE : cliquer sur un dossier deja ouvert le refermerait.
      const bascule = document.querySelector(`[data-action="toggle-chantier-details"][data-id="${identifiant}"]`);
      if (bascule && bascule.getAttribute("aria-expanded") !== "true") bascule.click();
      ecrireAdresse(adresseFiche("chantier", identifiant));
      return true;
    }
    default: return false;
  }
}

// ===================== Adresses =====================
// Chaque vue et chaque fiche a une adresse : on peut la mettre en favori,
// l'envoyer par message, la rouvrir apres un rechargement, et le bouton
// Precedent du navigateur fait ce qu'il annonce. Jusqu'ici l'URL ne bougeait
// jamais : quel que soit l'ecran, elle disait « index.html », et « revenir en
// arriere » sortait du produit.
//
// Le HASH plutot que le chemin : le produit est servi en fichiers statiques,
// et une adresse en /devis/89 renverrait un 404 au rechargement sans une
// regle de reecriture cote serveur - une dependance d'hebergement que ce
// changement n'a pas a introduire.
const ROUTE_OBJETS = { prospects: "client", clients: "client", devis: "devis", factures: "facture", chantiers: "chantier" };
const ROUTE_VUES = new Set([
  "dashboard", "prospects", "clients", "devis", "factures", "chantiers", "planning",
  "taches", "documents", "notifications", "statistiques", "avis", "entreprise",
]);
const ROUTE_LIBELLES = { client: "Ce client", devis: "Ce devis", facture: "Cette facture", chantier: "Ce chantier" };

// Vrai pendant qu'on APPLIQUE une adresse. Sans ce garde-fou, switchView()
// reecrirait l'adresse au milieu de sa propre lecture et l'historique
// enregistrerait deux fois la meme etape - Precedent semblerait bloque.
let routageEnCours = false;
let derniereAdresseAppliquee = null;

function ecrireAdresse(hash, { remplacer = false } = {}) {
  if (routageEnCours || window.location.hash === hash) return;
  derniereAdresseAppliquee = hash;
  // history plutot que `location.hash = ...` : l'affectation directe declenche
  // un hashchange, et on rejouerait une navigation qu'on vient de faire.
  // Premiere adresse de la session : on REMPLACE l'entree plutot que d'en
  // ajouter une, sinon le premier Precedent se contenterait de retirer le
  // hash en laissant l'ecran identique - un retour qui ne retourne nulle part.
  const methode = remplacer || !window.location.hash ? "replaceState" : "pushState";
  window.history[methode](null, "", hash);
}

/** Adresse d'une fiche, dans la vue d'ou on la regarde.
 *
 *  Un client se lit depuis Prospects ou depuis Clients : l'adresse garde la
 *  vue courante quand elle convient, pour que fermer la fiche ramene bien a
 *  la liste d'ou l'on venait. */
function adresseFiche(type, id) {
  const vueCourante = document.body.dataset.view;
  const vue = ROUTE_OBJETS[vueCourante] === type
    ? vueCourante
    : Object.keys(ROUTE_OBJETS).find((v) => ROUTE_OBJETS[v] === type);
  return `#/${vue}/${id}`;
}

function lireAdresse() {
  const [vue, segment] = window.location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (!vue || !ROUTE_VUES.has(vue)) return { vue: "dashboard", segment: null };
  return { vue, segment: segment || null };
}

/** Amene l'ecran a l'etat que decrit l'adresse courante. */
async function appliquerAdresse() {
  if (document.getElementById("dashboard-screen").hidden) return;
  if (window.location.hash === derniereAdresseAppliquee) return;
  derniereAdresseAppliquee = window.location.hash;
  const { vue, segment } = lireAdresse();
  routageEnCours = true;
  try {
    fermerFiches();
    // On NE RECHARGE PAS une vue deja affichee. C'est ce qui preserve les
    // filtres en cours et la position dans la liste quand on referme une
    // fiche : le retour a la liste doit rendre la liste telle qu'elle etait,
    // pas une liste neuve remise a zero.
    if (document.body.dataset.view !== vue) await switchView(vue);
    if (!segment) return;
    if (vue === "entreprise") {
      document.querySelector(`#entreprise-tabs [data-tab="${segment.replace(/[^\w-]/g, "")}"]`)?.click();
      return;
    }
    const type = ROUTE_OBJETS[vue];
    const identifiant = Number(segment);
    if (!type || !Number.isInteger(identifiant) || identifiant <= 0) return;
    if (!(await ouvrirFiche(type, identifiant))) {
      // Adresse valide, objet absent : archive, supprime, ou appartenant a un
      // autre compte. On le dit, et on laisse la liste ouverte.
      showToast(`${ROUTE_LIBELLES[type]} n'est plus dans votre liste. Il a peut-être été archivé ou supprimé.`, true);
      // history en direct : ecrireAdresse() se tait pendant qu'on applique une
      // adresse, et c'est justement pendant ce temps qu'il faut effacer celle
      // qui ne mene nulle part - sans quoi Actualiser rejouerait l'echec.
      derniereAdresseAppliquee = `#/${vue}`;
      window.history.replaceState(null, "", `#/${vue}`);
    }
  } finally {
    routageEnCours = false;
  }
}

// Qui a ouvert le dossier client : fige a l'ouverture, pour que refermer
// rende le focus a la ligne d'ou l'on venait et non a un bouton du dossier.
let dossierDeclencheur = null;

/** Referme le dossier client et rend la liste a l'ecran.
 *
 *  On ne touche PAS a la liste : elle est restee montee dessous, avec ses
 *  filtres, sa page et son defilement. C'est tout l'interet d'avoir garde la
 *  meme vue plutot que d'en ouvrir une nouvelle. */
function fermerDossier() {
  const dossier = document.getElementById("client-dossier");
  if (!dossier || dossier.hidden) return;
  dossier.hidden = true;
  document.body.classList.remove("est-dossier-ouvert");
  if (dossierDeclencheur && dossierDeclencheur.isConnected) dossierDeclencheur.focus();
  dossierDeclencheur = null;
}

/** Referme les fiches ouvertes par-dessus une liste, sans toucher a la liste. */
function fermerFiches() {
  fermerDossier();
  ["panel-devis", "panel-facture"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = true;
  });
}

/** Referme la fiche courante ET remet l'adresse sur la liste. */
function fermerFicheEtRevenir() {
  fermerFiches();
  ecrireAdresse(`#/${document.body.dataset.view || "dashboard"}`);
}

window.addEventListener("hashchange", appliquerAdresse);
window.addEventListener("popstate", appliquerAdresse);

/** Ouvre l'objet designe par un bouton, ou a defaut sa vue.
 *
 *  Les boutons « Voir » de l'accueil connaissent la piece exacte (la facture
 *  en retard, le devis a relancer) : ils la nomment dans leur libelle. Ils
 *  doivent donc l'ouvrir, pas se contenter du rayon. */
async function ouvrirCible(donnees) {
  if (donnees.objetType && (await ouvrirObjet(donnees.objetType, parseInt(donnees.objetId, 10)))) return;
  // ouvrirObjet a pu basculer sur la vue avant d'echouer a ouvrir la fiche :
  // sans ce test, on rechargeait la meme vue une seconde fois.
  if (donnees.view && document.body.dataset.view !== donnees.view) await switchView(donnees.view);
}

/** Ouvre ce qu'une notification designe.
 *
 *  « Impaye : Villa Bertrand » posait l'artisan devant la liste complete des
 *  factures. La notification connait pourtant la piece exacte (n.id) : elle
 *  peut donc l'ouvrir. Quand le type ne designe pas un objet adressable
 *  (conformite), on ouvre au moins le bon onglet plutot que la vue nue. */
async function ouvrirNotification(donnees) {
  const objetId = parseInt(donnees.objetId, 10);
  const clientId = parseInt(donnees.clientId, 10);
  switch (donnees.notificationType) {
    case "devis_relance":
      if (await ouvrirObjet("devis", objetId)) return;
      break;
    case "facture_relance":
      if (await ouvrirObjet("facture", objetId)) return;
      break;
    case "message_client":
    case "nouvelle_demande_devis":
      if (await ouvrirObjet("client", clientId)) return;
      break;
    case "conformite":
      await switchView("entreprise");
      document.querySelector('#entreprise-tabs [data-tab="conformite"]')?.click();
      return;
    default:
      break;
  }
  await switchView(donnees.view);
}
