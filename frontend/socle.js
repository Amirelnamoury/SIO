/* =====================================================================
   SOCLE — les primitives partagees par tous les ecrans
   ---------------------------------------------------------------------
   Premier decoupage de app.js par domaine (Astra §16 : « evolution
   PROGRESSIVE du JavaScript existant vers des modules par domaine »).

   Ce fichier ne contient que ce dont TOUS les ecrans se servent : les
   formats (montants, dates), les etats d'un ecran (vide, filtre par une
   recherche, incomplet, en cours d'actualisation), les messages de
   resultat, les confirmations, la section composee, et le clavier dans
   les fenetres modales.

   AUCUNE LIGNE N'A ETE REECRITE : elles ont ete deplacees telles quelles.
   Un decoupage qui change le comportement en meme temps qu'il range n'est
   pas verifiable - on ne saurait plus si une regression vient du rangement
   ou de la reecriture.

   Charge AVANT app.js (voir index.html). Ce sont des scripts classiques,
   pas des modules ES : les declarations de premier niveau sont partagees
   entre les fichiers, exactement comme lorsque tout tenait dans app.js.
   Passer aux modules ES demanderait de revoir tous les `data-action` et
   les fonctions posees sur window - un autre lot, s'il se justifie.

   Ce qui reste a extraire, dans l'ordre ou Astra le suggere : la
   navigation et l'adressage, puis les compositions propres au devis, au
   planning, au chantier et aux statistiques.
   ===================================================================== */

// ===================== Utilitaires =====================
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function emptyToNull(value) {
  return value === "" || value === undefined ? null : value;
}

function fmtDate(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("fr-FR");
}
// `toLocaleString("fr-FR")` sans options rend « 06/09/2026 01:21:23 » : les
// SECONDES d'un evenement commercial. Personne ne se demande a quelle
// seconde un devis a ete ouvert, et ces deux chiffres de trop donnaient a la
// chronologie du client comme a la vie d'un devis l'allure d'un journal
// technique. La minute suffit partout ou cette fonction est appelee, y
// compris pour le dernier passage du moteur d'automatisation.
function fmtDateTime(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
function fmtDateCourte(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}
// Rend un TIRET quand le montant est absent, jamais `null`. La version
// precedente renvoyait la valeur nulle telle quelle : interpolee dans un
// gabarit, elle s'ecrivait « null » en toutes lettres. Le defaut ne se
// voyait que sur les montants reellement absents - c'est-a-dire, pour
// l'essentiel, sur un compte qui vient d'etre cree. Un artisan inscrit du
// jour lisait « Panier moyen : null » sur sa page Statistiques.
// Les rares appels qui voulaient une chaine VIDE plutot qu'un tiret le
// demandent maintenant explicitement (fmtEuroOuRien).
function fmtEuro(n) {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(n);
}
/** Comme fmtEuro, mais rend une chaine vide pour un montant absent : sert la
 *  ou une cellule sans montant doit rester blanche plutot que barree. */
function fmtEuroOuRien(n) {
  return n === null || n === undefined ? "" : fmtEuro(n);
}

/** Un montant pour une GRADUATION, pas pour une piece comptable.
 *
 *  L'axe d'un graphique n'annonce pas une somme, il donne l'echelle :
 *  « 11,7 k€ » se lit d'un coup d'oeil la ou « 11 650,00 € » demande a
 *  etre dechiffre. Ce n'est pas qu'une question de gout - l'axe des
 *  ordonnees dispose de 44 px, et le montant complet en demandait 60. Il
 *  sortait donc du cadre du SVG, ou il etait purement et simplement
 *  rogne : les quatre graduations du chiffre d'affaires etaient illisibles
 *  et personne ne pouvait dire a quelle hauteur passait la courbe.
 *
 *  Les centimes n'ont aucun sens sur une graduation, et la valeur exacte
 *  reste disponible la ou elle compte : sur le point, et dans le tableau.
 */
function fmtEuroAxe(n) {
  if (n === null || n === undefined) return "";
  const abs = Math.abs(n);
  if (abs >= 1e6) return `${(n / 1e6).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} M€`;
  if (abs >= 1000) return `${(n / 1000).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} k€`;
  return `${Math.round(n).toLocaleString("fr-FR")} €`;
}

function skeletonCards(n = 3) {
  return Array.from({ length: n }).map(() => '<div class="skeleton skeleton-card"></div>').join("");
}

/** Debut d'un chargement, selon qu'il y a deja quelque chose a l'ecran.
 *
 *  Un ECRAN VIDE recoit un squelette : il n'y a rien a conserver.
 *  Un ECRAN DEJA REMPLI le garde. Cocher une tache, enregistrer un paiement,
 *  changer un statut : chacun de ces gestes rechargeait sa liste, et la liste
 *  disparaissait le temps de l'aller-retour pour revenir presque identique.
 *  Trois lignes de squelette a la place de la liste qu'on regardait, c'est
 *  perdre sa place et sa lecture pour une donnee qu'on avait deja. Le contenu
 *  reste donc affiche, en retrait, avec aria-busy pour que ce soit dit aussi
 *  aux lecteurs d'ecran (Astra §11 : « conserver les informations deja
 *  chargees en indiquant leur etat »).
 *
 *  Le voile se leve DE LUI-MEME des que le conteneur recoit son nouveau
 *  contenu : aucun appel de fin a ajouter dans les quatorze chargeurs - donc
 *  aucun oubli possible le jour ou un quinzieme apparait. */
function debutChargement(conteneur, squelette = skeletonCards) {
  if (!conteneur) return;
  if (!conteneur.children.length) {
    conteneur.innerHTML = typeof squelette === "function" ? squelette() : squelette;
    return;
  }
  if (conteneur.dataset.actualisation === "1") return;
  conteneur.dataset.actualisation = "1";
  conteneur.classList.add("est-en-actualisation");
  conteneur.setAttribute("aria-busy", "true");
  const finir = () => {
    observateur.disconnect();
    clearTimeout(secours);
    delete conteneur.dataset.actualisation;
    conteneur.classList.remove("est-en-actualisation");
    conteneur.removeAttribute("aria-busy");
  };
  const observateur = new MutationObserver(finir);
  observateur.observe(conteneur, { childList: true });
  // Filet : si le chargement n'aboutit jamais et ne remplace rien, on rend
  // sa lisibilite au contenu plutot que de le laisser en retrait pour
  // toujours. Il reste juste : ce sont les dernieres donnees recues.
  const secours = setTimeout(finir, 15000);
}

let toastTimer = null;
// `duree` : trois secondes et demie suffisent pour une confirmation, pas pour
// un message qui demande de VERIFIER quelque chose avant de recommencer.
function showToast(message, isError = false, duree = 3500) {
  const toast = document.getElementById("toast");
  toast.innerHTML = `<span class="toast-icon"></span><span>${escapeHtml(message)}</span>`;
  toast.classList.toggle("toast-error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), duree);
}

function feedbackRelanceDevis(result) {
  const statut = result && result.email_statut;
  return {
    message: result && result.message ? result.message : "Tentative de relance enregistrée.",
    isError: statut !== "envoye",
  };
}

async function withErrorToast(promiseFn) {
  try {
    return await promiseFn();
  } catch (err) {
    // Trois registres, pas un seul :
    //   - un REFUS DE DROITS (403) : le serveur a compris et refuse.
    //     Recommencer ne changera rien ; on dit a qui s'adresser plutot que
    //     de laisser croire a une panne du produit.
    //   - une ISSUE INCERTAINE : le message demande d'aller verifier, il ne
    //     peut pas disparaitre au bout de trois secondes.
    //   - une erreur ordinaire.
    if (err.accesInterdit) {
      // Le serveur nomme deja qui a le droit (« Reserve aux administrateurs de
      // l'equipe ») : reciter « demandez a un administrateur » derriere ferait
      // dire deux fois la meme chose. On ne complete que si le refus reste
      // muet sur la personne a qui s'adresser.
      const texte = err.message.replace(/\s*$/, "").replace(/([^.!?])$/, "$1.");
      const nommeQui = /administrateur|propriétaire|proprietaire/i.test(texte);
      showToast(nommeQui ? texte : `${texte} Demandez à un administrateur de votre équipe.`, true, 9000);
    } else {
      showToast(err.message || "Une erreur est survenue.", true, err.issueIncertaine ? 12000 : undefined);
    }
    // Un 402 "plan requis" (voir app/deps.py, require_plan) est un moment
    // d'upgrade, pas juste une erreur : on ouvre directement la modale des
    // tarifs a la place de laisser l'utilisateur deviner ou aller (section
    // "moments d'upgrade" du cahier des charges V4).
    if (err.message && err.message.includes("fait partie du plan")) {
      setTimeout(() => openPricingModal(), 400);
    }
    throw err;
  }
}

// Remplace window.confirm() (bloquant, non stylé) par une modale coherente
// avec le design system. Resout true/false selon le choix de l'utilisateur.
function confirmDialog(message, { title = "Confirmer", confirmLabel = "Confirmer", danger = false } = {}) {
  return new Promise((resolve) => {
    const modal = document.getElementById("confirm-dialog");
    const box = modal.querySelector(".confirm-dialog-box");
    document.getElementById("confirm-dialog-title").textContent = title;
    document.getElementById("confirm-dialog-message").textContent = message;
    const okBtn = document.getElementById("confirm-dialog-ok");
    const cancelBtn = document.getElementById("confirm-dialog-cancel");
    okBtn.textContent = confirmLabel;
    box.classList.toggle("is-danger", danger);
    modal.hidden = false;

    function cleanup(result) {
      modal.hidden = true;
      okBtn.removeEventListener("click", onOk);
      cancelBtn.removeEventListener("click", onCancel);
      modal.removeEventListener("click", onBackdrop);
      document.removeEventListener("keydown", onKeydown);
      resolve(result);
    }
    function onOk() { cleanup(true); }
    function onCancel() { cleanup(false); }
    function onBackdrop(e) { if (e.target === modal) cleanup(false); }
    function onKeydown(e) { if (e.key === "Escape") cleanup(false); }

    okBtn.addEventListener("click", onOk);
    cancelBtn.addEventListener("click", onCancel);
    modal.addEventListener("click", onBackdrop);
    document.addEventListener("keydown", onKeydown);
    okBtn.focus();
  });
}

// ===================== Le clavier dans les fenetres modales =====================
//
// Onze elements portent role="dialog" aria-modal="true". Ils annoncent donc a
// un lecteur d'ecran que le reste de la page est hors d'atteinte - mais rien
// ne le rendait vrai : la tabulation sortait de la fenetre et continuait dans
// la page derriere, et refermer une fiche laissait le focus au neant, si bien
// qu'une frappe suivante repartait du haut du document. Astra §13, et le
// motif « dialog (modal) » des pratiques ARIA.
//
// Un observateur sur l'attribut `hidden` plutot qu'un appel dans chaque
// ouverture : les onze fenetres s'ouvrent et se ferment a une quinzaine
// d'endroits differents, et la prochaine n'aurait pas ete branchee.
const SELECTEUR_FOCUSABLE = [
  "a[href]", "button:not([disabled])", "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])", "textarea:not([disabled])", '[tabindex]:not([tabindex="-1"])',
].join(", ");

// Empilement : une confirmation peut s'ouvrir PAR-DESSUS un detail de
// rendez-vous. Seule la fenetre du dessus retient le clavier.
const pileModales = [];
const declencheurs = new WeakMap();

// QUI a ouvert la fenetre. Certaines fenetres deplacent le focus
// SYNCHRONEMENT a leur ouverture (le bouton Fermer d'un panneau) : quand
// l'observateur passe, l'element actif est deja dedans et le declencheur
// serait perdu. On retient donc le dernier GESTE fait hors d'une fenetre.
//
// Le geste, et non l'evenement `focusin` : celui-ci ne se declenche pas quand
// le document n'a pas le focus systeme - ce qui arrive dans un navigateur
// pilote, mais aussi chez un utilisateur dont la fenetre vient de perdre la
// main. Un clic et une touche, eux, arrivent toujours. Capture, pour passer
// avant le gestionnaire qui ouvre la fenetre.
let dernierGeste = null;
const noterGeste = (e) => {
  const cible = e.target instanceof Element ? e.target.closest("button, a, [role=\"button\"], input, select, textarea, [tabindex]") : null;
  if (cible && !cible.closest('[role="dialog"]')) dernierGeste = cible;
};
document.addEventListener("pointerdown", noterGeste, true);
document.addEventListener("keydown", noterGeste, true);
document.addEventListener("focusin", noterGeste, true);

function focusablesDe(dialogue) {
  return [...dialogue.querySelectorAll(SELECTEUR_FOCUSABLE)]
    .filter((el) => !el.hidden && el.offsetParent !== null);
}

function modaleOuverte(dialogue) {
  if (pileModales.includes(dialogue)) return;
  const candidats = [document.activeElement, dernierGeste];
  const declencheur = candidats.find((el) => el && el !== document.body && el.isConnected && !dialogue.contains(el));
  if (declencheur) declencheurs.set(dialogue, declencheur);
  pileModales.push(dialogue);
  // Certaines fenetres placent deja leur focus (le bouton Fermer d'un
  // panneau) : on ne le deplace pas si elles l'ont fait.
  if (!dialogue.contains(document.activeElement)) focusablesDe(dialogue)[0]?.focus();
}

function modaleFermee(dialogue) {
  const rang = pileModales.indexOf(dialogue);
  if (rang === -1) return;
  pileModales.splice(rang, 1);
  const declencheur = declencheurs.get(dialogue);
  declencheurs.delete(dialogue);
  // On ne rend le focus que s'il etait reste dans la fenetre qu'on ferme :
  // sinon on l'arracherait a l'endroit ou l'artisan vient de le poser.
  if (!declencheur || !declencheur.isConnected) return;
  if (document.activeElement && document.activeElement !== document.body
      && !dialogue.contains(document.activeElement)) return;
  declencheur.focus();
}

function surveillerModales() {
  document.querySelectorAll('[role="dialog"]').forEach((dialogue) => {
    new MutationObserver(() => (dialogue.hidden ? modaleFermee(dialogue) : modaleOuverte(dialogue)))
      .observe(dialogue, { attributes: true, attributeFilter: ["hidden"] });
    if (!dialogue.hidden) modaleOuverte(dialogue);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Tab" || !pileModales.length) return;
    const dialogue = pileModales[pileModales.length - 1];
    const focusables = focusablesDe(dialogue);
    if (!focusables.length) { e.preventDefault(); return; }
    const premier = focusables[0], dernier = focusables[focusables.length - 1];
    // Le focus a pu sortir (clic dans la page derriere) : on le ramene.
    if (!dialogue.contains(document.activeElement)) {
      e.preventDefault();
      (e.shiftKey ? dernier : premier).focus();
      return;
    }
    if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus(); }
    else if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus(); }
  });
}

/** Un ecran vide qui INVITE au lieu de constater une absence.
 *
 *  « Aucun devis pour le moment. » est une phrase de base de donnees : elle
 *  decrit l'etat d'une table. Un artisan qui vient de s'inscrire n'a pas
 *  besoin qu'on lui apprenne qu'il n'a pas encore de devis - il a besoin de
 *  savoir ce que cette page fera pour lui et par ou commencer.
 *
 *  `action` est facultatif : certaines pages se remplissent toutes seules
 *  (les notifications, les avis recus) et n'ont aucun geste a proposer. */
function etatVide(titre, phrase = "", action = null) {
  return `<div class="empty-state">${escapeHtml(titre)}
    ${phrase ? `<p>${phrase}</p>` : ""}
    ${action ? `<button type="button" class="btn-primary" data-action="${action.action}">${escapeHtml(action.libelle)}</button>` : ""}
  </div>`;
}

/** Vide parce qu'un filtre exclut tout : il y a bien des donnees ailleurs. */
function etatFiltre(phrase) {
  return `<div class="empty-state est-filtre">${escapeHtml(phrase)}</div>`;
}

/* Les boutons des etats vides portent le meme `data-action` que ceux de
   l'en-tete de page - mais les gestionnaires d'origine sont branches par
   `querySelector`, qui ne retient QUE LE PREMIER element. Un bouton cree
   plus tard dans un etat vide serait donc reste muet.
   Plutot que de rebrancher chaque formulaire, on delegue : un clic dans un
   etat vide releve le bouton d'en-tete correspondant et le declenche. Une
   seule source de verite pour l'ouverture des formulaires. */
/* « Réessayer » d'un chargement incomplet : on relance la vue courante par
   son propre chargeur, plutot que de recharger la page - la saisie en cours
   ailleurs dans l'ecran survit. */
document.addEventListener("click", (e) => {
  if (!e.target.closest('[data-action="recharger-vue"]')) return;
  const vue = document.body.dataset.view;
  if (vue) switchView(vue);
});

document.addEventListener("click", (e) => {
  const bouton = e.target.closest(".empty-state [data-action]");
  if (!bouton) return;
  const cible = document.querySelector(`.view-header [data-action="${bouton.dataset.action}"], .subsection-header [data-action="${bouton.dataset.action}"]`);
  if (cible && cible !== bouton) { e.preventDefault(); cible.click(); }
});

/* =====================================================================
   UN ECHEC DE CHARGEMENT N'EST PAS UNE ABSENCE DE DONNEES
   ---------------------------------------------------------------------
   Douze appels du produit etaient ecrits `Api.listFactures().catch(() =>
   [])`. Le repli silencieux evitait qu'une source en panne casse toute la
   page - l'intention etait bonne - mais il produisait un mensonge : le
   dossier d'un client affichait « aucune facture » alors que l'appel avait
   echoue. Un artisan pouvait en conclure que ce client ne lui doit rien.

   `tolerant()` garde le repli et ENREGISTRE la panne. La vue peut alors
   dire ce qu'elle ne sait pas, au lieu d'affirmer qu'il n'y a rien.
   ===================================================================== */
function journalDeCharge() { return { manquants: [] }; }

async function tolerant(journal, etiquette, promesse, repli = []) {
  try {
    return await promesse;
  } catch (err) {
    journal.manquants.push(etiquette);
    return repli;
  }
}

/** Le bandeau qui annonce ce qui manque. Il ne remplace pas le contenu
 *  charge : le reste de la page reste utilisable, on signale seulement
 *  qu'elle est incomplete. */
// Les etiquettes passees a tolerant() sont des groupes nominaux : celles-ci
// sont feminines. Toute nouvelle etiquette feminine doit y etre ajoutee.
const ETIQUETTES_FEMININES = new Set(["les factures"]);

function bandeauCharge(journal) {
  if (!journal.manquants.length) return "";
  const liste = journal.manquants.length === 1
    ? journal.manquants[0]
    : `${journal.manquants.slice(0, -1).join(", ")} et ${journal.manquants[journal.manquants.length - 1]}`;
  // Le verbe s'accorde avec le SUJET, pas avec le nombre de sources en
  // panne. Une seule source manquante donnait « Les chantiers n'a pas pu
  // etre charge » : le compteur valait un, mais le sujet reste pluriel.
  // Toutes les etiquettes du produit sont des groupes nominaux pluriels
  // (« les devis », « les factures », « les elements de conformite ») ;
  // l'accord est donc au pluriel, et la seule chose que le nombre de
  // sources change est l'enumeration.
  //
  // Le GENRE, lui, suit les etiquettes : « les factures n'ont pas pu etre
  // chargeS » se lisait sur la fiche client. Quand plusieurs sources sont en
  // panne et qu'elles ne sont pas toutes feminines, le masculin l'emporte -
  // c'est la regle, pas un repli.
  const toutesFeminines = journal.manquants.every((e) => ETIQUETTES_FEMININES.has(e));
  return `<p class="charge-incomplete" role="status">
    ${escapeHtml(liste.charAt(0).toUpperCase() + liste.slice(1))} n'ont pas pu être chargé${toutesFeminines ? "es" : "s"}.
    Ce qui s'affiche ci-dessous est donc incomplet.
    <button type="button" class="btn-sm" data-action="recharger-vue">Réessayer</button>
  </p>`;
}

function saSection(titre, corps, note = "", classe = "") {
  if (!corps) return "";
  return `
  <section class="sa-section ${classe}">
    <div class="sa-section-marge">
      <h3 class="sa-section-titre">${titre}</h3>
      ${note ? `<p class="sa-section-note">${note}</p>` : ""}
    </div>
    <div class="sa-section-corps">${corps}</div>
  </section>`;
}
