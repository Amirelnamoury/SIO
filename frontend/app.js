// ===================== Etat global =====================
let currentArtisan = null;
let currentUtilisateur = null; // { role, nom, email, membre_id } - qui est precisement connecte
let currentDevisFilter = "";
let currentAvisFilter = ""; // "" | "1" (publies) | "0" (non publies)
let devisDueIds = new Set();
let profilePhotoObjectUrl = null;
let profilePhotoApiPath = null;

function estAdministrateur() {
  return currentUtilisateur && (currentUtilisateur.role === "proprietaire" || currentUtilisateur.role === "administrateur");
}

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

function skeletonCards(n = 3) {
  return Array.from({ length: n }).map(() => '<div class="skeleton skeleton-card"></div>').join("");
}

let toastTimer = null;
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.innerHTML = `<span class="toast-icon"></span><span>${escapeHtml(message)}</span>`;
  toast.classList.toggle("toast-error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3500);
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
    showToast(err.message || "Une erreur est survenue.", true);
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

// ===================== Constantes d'affichage =====================
const METIER_LABELS = {
  plombier: "Plombier",
  electricien: "Électricien",
  macon: "Maçon",
  peintre: "Peintre",
  general: "Artisan du BTP",
};

const DEVIS_STATUT_META = {
  nouveau: { label: "Nouvelle demande", badge: "badge-gray" },
  envoye: { label: "Envoyé", badge: "badge-blue" },
  consulte: { label: "Consulté", badge: "badge-blue" },
  relance_j3: { label: "Relance J+3", badge: "badge-orange" },
  relance_j7: { label: "Relance J+7", badge: "badge-orange" },
  relance_j15: { label: "Relance J+15", badge: "badge-red" },
  signe: { label: "Signé", badge: "badge-green" },
  perdu: { label: "Perdu", badge: "badge-gray" },
  expire: { label: "Expiré", badge: "badge-gray" },
};

const CLIENT_STATUT_META = {
  nouveau: { label: "Nouveau", badge: "badge-gray" },
  contacte: { label: "Contacté", badge: "badge-blue" },
  qualification: { label: "Qualification", badge: "badge-blue" },
  visite_prevue: { label: "Visite prévue", badge: "badge-blue" },
  devis_a_faire: { label: "Devis à faire", badge: "badge-orange" },
  devis_envoye: { label: "Devis envoyé", badge: "badge-orange" },
  negociation: { label: "Négociation", badge: "badge-orange" },
  gagne: { label: "Gagné", badge: "badge-green" },
  perdu: { label: "Perdu", badge: "badge-gray" },
};

const CLIENT_SOURCE_LABELS = {
  manuel: "Ajouté manuellement",
  site_vitrine: "Site vitrine",
  google: "Google",
  recommandation: "Recommandation",
  telephone: "Téléphone",
  facebook: "Facebook",
  instagram: "Instagram",
  ancien_client: "Ancien client",
  autre: "Autre",
};

const FACTURE_STATUT_META = {
  brouillon: { label: "Brouillon", badge: "badge-gray" },
  envoyee: { label: "Envoyée", badge: "badge-blue" },
  partiellement_payee: { label: "Partiellement payée", badge: "badge-orange" },
  payee: { label: "Payée", badge: "badge-green" },
  en_retard: { label: "En retard", badge: "badge-red" },
  annulee: { label: "Annulée", badge: "badge-gray" },
};

const CHANTIER_STATUT_META = {
  a_preparer: { label: "À préparer", badge: "badge-gray" },
  planifie: { label: "Planifié", badge: "badge-blue" },
  en_cours: { label: "En cours", badge: "badge-blue" },
  en_pause: { label: "En pause", badge: "badge-orange" },
  termine: { label: "Terminé", badge: "badge-green" },
  facture: { label: "Facturé", badge: "badge-green" },
  paye: { label: "Payé", badge: "badge-green" },
};

// Cache simple des clients pour remplir les listes deroulantes des formulaires
// devis/chantier/facture sans reinterroger l'API a chaque frappe.
let clientsCache = [];
async function ensureClientsCache() {
  clientsCache = await Api.listClients();
  return clientsCache;
}

// Cache simple des chantiers charges, pour retrouver les donnees d'un
// chantier (ex: pre-remplir le formulaire de reception) sans reinterroger.
let chantiersCache = [];
let chantierFocusId = null;

function clientOptionsHtml(selectedId) {
  return clientsCache
    .map((c) => `<option value="${c.id}" ${selectedId === c.id ? "selected" : ""}>${escapeHtml(c.nom)}</option>`)
    .join("");
}

// Catalogue de prestations : meme principe, mis en cache pour la recherche
// rapide (datalist) dans l'editeur de lignes de devis/facture.
let prestationsCache = [];
async function ensurePrestationsCache() {
  prestationsCache = await Api.listPrestations();
  return prestationsCache;
}

function prestationsDatalistHtml() {
  return `<datalist id="prestations-datalist">${prestationsCache
    .map((p) => `<option value="${escapeHtml(p.description)}"></option>`)
    .join("")}</datalist>`;
}

const PHASE_LABELS = { avant: "Avant", pendant: "Pendant", apres: "Après" };
const CONFORMITE_TYPE_LABELS = {
  assurance_decennale: "Assurance décennale",
  qualibat: "Qualibat",
  rge: "RGE",
  autre: "Autre",
};

// ===================== Ecran d'authentification =====================
function showAuthScreen() {
  clearProfilePhoto();
  document.getElementById("auth-screen").hidden = false;
  document.getElementById("dashboard-screen").hidden = true;
}

function showAuthError(message) {
  const box = document.getElementById("auth-error");
  if (!message) {
    box.hidden = true;
    box.textContent = "";
    return;
  }
  box.hidden = false;
  box.textContent = message;
}

function setupAuthScreen() {
  const wantedTab = new URLSearchParams(window.location.search).get("tab");
  if (wantedTab === "register") {
    document.querySelectorAll(".auth-tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === "register"));
    document.getElementById("login-form").hidden = true;
    document.getElementById("register-form").hidden = false;
  }

  document.querySelectorAll(".auth-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".auth-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      showAuthError(null);
      document.getElementById("login-form").hidden = tab.dataset.tab !== "login";
      document.getElementById("register-form").hidden = tab.dataset.tab !== "register";
    });
  });

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthError(null);
    const submitBtn = e.target.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const data = await Api.login({
        email: document.getElementById("login-email").value,
        password: document.getElementById("login-password").value,
      });
      setToken(data.access_token);
      currentArtisan = data.artisan;
      currentUtilisateur = await Api.moi();
      enterDashboard();
    } catch (err) {
      showAuthError(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });

  document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthError(null);
    const submitBtn = e.target.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      const data = await Api.register({
        nom_entreprise: document.getElementById("reg-nom-entreprise").value,
        metier: document.getElementById("reg-metier").value,
        email: document.getElementById("reg-email").value,
        password: document.getElementById("reg-password").value,
        telephone: emptyToNull(document.getElementById("reg-telephone").value),
        ville: emptyToNull(document.getElementById("reg-ville").value),
        code_postal: emptyToNull(document.getElementById("reg-code-postal").value),
        siret: emptyToNull(document.getElementById("reg-siret").value),
        assurance_decennale_nom: emptyToNull(document.getElementById("reg-assurance").value),
      });
      setToken(data.access_token);
      currentArtisan = data.artisan;
      currentUtilisateur = await Api.moi();
      enterDashboard();
    } catch (err) {
      showAuthError(err.message);
    } finally {
      submitBtn.disabled = false;
    }
  });
}

// ===================== Fonctions payantes (abonnement) =====================
function isBillingSubscriptionActive() {
  return currentArtisan && currentArtisan.subscription_status === "active";
}

// Doit rester le miroir exact de PLAN_ORDRE / require_plan cote backend
// (app/deps.py) : c'est juste pour eviter d'afficher un ecran qui va
// echouer au clic, jamais la source de verite (toujours revalidee par
// l'API a chaque action).
function hasPlan(minimum) {
  const planActuel = currentArtisan && PRICING_ORDRE.includes(currentArtisan.plan) ? currentArtisan.plan : "gratuit";
  if (!PRICING_ORDRE.includes(minimum)) return false;
  return PRICING_ORDRE.indexOf(planActuel) >= PRICING_ORDRE.indexOf(minimum);
}

function renderUpgradeCard(title, description, minPlan = "essentiel") {
  const plan = PRICING[minPlan];
  return `
  <div class="upgrade-card">
    <h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(description)} A partir du plan ${escapeHtml(plan.nom)}, ${plan.prix}&nbsp;&euro; ${plan.mention}.</p>
    <button type="button" class="btn-primary" data-action="upgrade-subscription">Voir les tarifs</button>
  </div>`;
}

async function attemptUpgrade(plan) {
  const btn = document.querySelector(`[data-action="confirm-upgrade"][data-plan="${plan}"]`);
  if (btn) btn.disabled = true;
  try {
    const data = await Api.checkoutSession(plan);
    if (data.plan_change_immediat) {
      // Abonnement deja actif : le changement de plan a ete applique
      // directement (proration Stripe), pas besoin de repasser par une
      // page de paiement externe.
      showToast("Votre plan a été mis à jour.");
      closePricingModal();
      currentArtisan = await Api.me();
      switchView(document.querySelector(".nav-link.active")?.dataset.view || "dashboard");
    } else {
      window.location.href = data.checkout_url;
    }
  } catch (err) {
    if (err.message.toLowerCase().includes("stripe")) {
      showToast("Le paiement en ligne n'est pas encore active sur ce compte. Contactez l'administrateur pour activer votre abonnement.", true);
    } else {
      showToast(err.message, true);
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ===================== Modale des tarifs =====================
function normalizeCurrentPlan(plan) {
  const normalized = typeof plan === "string" ? plan.trim().toLowerCase() : "";
  return PRICING_ORDRE.includes(normalized) ? normalized : "gratuit";
}

function planCardHtml(key, plan, currentPlan) {
  const isPro = plan.recommande === true;
  const isGratuit = key === "gratuit";
  const isCurrent = key === currentPlan;
  const priceHtml = `<div class="plan-price">${plan.prix}&nbsp;&euro; <span class="period">/ ${plan.periode}</span></div>`;
  return `
  <div class="plan-card ${isPro ? "plan-highlight" : ""} ${isCurrent ? "plan-current" : ""}" data-plan-key="${key}"${isCurrent ? ' data-current-plan="true" aria-current="true"' : ""}>
    ${isPro ? '<span class="plan-badge">Recommandé</span>' : ""}
    <div class="plan-name">${escapeHtml(plan.nom)}</div>
    <div class="plan-accroche">${escapeHtml(plan.accroche)}</div>
    ${priceHtml}
    <div class="plan-mention">${escapeHtml(plan.mention || "Sans engagement")}</div>
    <p class="plan-positionnement">${escapeHtml(plan.positionnement)}</p>
    <ul class="plan-features">
      ${plan.fonctionnalites.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}
    </ul>
    ${isCurrent
      ? '<button type="button" class="btn-secondary" disabled aria-disabled="true">Plan actuel</button>'
      : isGratuit
      ? '<button type="button" class="btn-secondary" data-action="close-pricing">Conserver mon plan actuel</button>'
      : `<button type="button" class="btn-primary" data-action="confirm-upgrade" data-plan="${key}">S'abonner a ${escapeHtml(plan.nom)}</button>`}
  </div>`;
}

function renderPlanCards(currentPlan) {
  const normalizedPlan = normalizeCurrentPlan(currentPlan);
  return Object.entries(PRICING).map(([key, plan]) => planCardHtml(key, plan, normalizedPlan)).join("");
}

function siteOfferHtml() {
  return `
  <div class="site-offer">
    <div>
      <div class="site-offer-label">Option distincte du SaaS · Disponible avec tous les plans, y compris Gratuit</div>
      <h3>${escapeHtml(SITE_VITRINE_OFFER.nom)}</h3>
      <p class="site-offer-benefit">${escapeHtml(SITE_VITRINE_OFFER.accroche)}</p>
      <p>${escapeHtml(SITE_VITRINE_OFFER.description)}</p>
    </div>
    <div class="site-offer-price">
      <strong>${SITE_VITRINE_OFFER.creation}&nbsp;&euro; ${SITE_VITRINE_OFFER.mention}</strong> a la creation
      <span>+ ${SITE_VITRINE_OFFER.mensuel}&nbsp;&euro; ${SITE_VITRINE_OFFER.mention} / mois de gestion &amp; maintenance</span>
    </div>
    <ul>${SITE_VITRINE_OFFER.carteInclus.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <p class="site-offer-summary">${escapeHtml(SITE_VITRINE_OFFER.resumeInclus)}</p>
  </div>`;
}

function openPricingModal() {
  const container = document.getElementById("pricing-plans");
  container.innerHTML = renderPlanCards(currentArtisan && currentArtisan.plan);
  document.getElementById("pricing-site-offer").innerHTML = siteOfferHtml();
  document.getElementById("pricing-modal").hidden = false;
}
function closePricingModal() {
  document.getElementById("pricing-modal").hidden = true;
}

document.addEventListener("click", (e) => {
  if (e.target.closest('[data-action="upgrade-subscription"]')) {
    openPricingModal();
  } else if (e.target.closest('[data-action="confirm-upgrade"]')) {
    attemptUpgrade(e.target.closest('[data-action="confirm-upgrade"]').dataset.plan);
  } else if (e.target.closest('[data-action="close-pricing"]') || e.target.id === "pricing-modal") {
    closePricingModal();
  }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !document.getElementById("pricing-modal").hidden) closePricingModal();
});

// ===================== Coquille du tableau de bord =====================
function enterDashboard() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("dashboard-screen").hidden = false;
  refreshProfilePhoto().catch(() => {});
  switchView("dashboard");
  refreshBadges();
  maybeShowOnboarding();
}

// ===================== Onboarding (premiere connexion) =====================
const ONBOARDING_STEPS = [
  {
    title: "Bienvenue sur Suite Artisan",
    body: "Un seul outil pour ne plus perdre de prospects, suivre vos devis et garder une vue claire sur votre activité. Tout ce dont vous avez besoin pour démarrer est déjà gratuit.",
  },
  {
    title: "Comment ça marche",
    list: [
      "Ajoutez un client ou un prospect",
      "Créez un devis avec vos lignes de prestation, envoyez le PDF",
      `Suite Artisan repère les devis à relancer et vous le signale — l'envoi automatique de la relance fait partie du plan ${PRICING.pro.nom}`,
    ],
  },
  {
    title: "Votre site vitrine",
    body: "Si vous avez commandé un site vitrine, il apparaîtra dans votre tableau de bord dès qu'il sera livré, avec les demandes reçues automatiquement dans vos prospects.",
  },
  {
    title: "Pour aller plus loin",
    body: `Le plan ${PRICING.essentiel.nom} (${PRICING.essentiel.prix}€ ${PRICING.essentiel.mention}) ajoute le suivi de chantiers, la conformité et les statistiques. Vous pourrez vous abonner à tout moment depuis votre profil.`,
  },
];
let onboardingStepIndex = 0;

function renderOnboardingStep() {
  const step = ONBOARDING_STEPS[onboardingStepIndex];
  document.getElementById("onboarding-steps").innerHTML = `
    <div class="onboarding-step">
      <h3 id="onboarding-step-title">${escapeHtml(step.title)}</h3>
      ${step.body ? `<p>${escapeHtml(step.body)}</p>` : ""}
      ${step.list ? `<ul>${step.list.map((l, i) => `<li data-num="${i + 1}">${escapeHtml(l)}</li>`).join("")}</ul>` : ""}
    </div>`;
  document.getElementById("onboarding-dots").innerHTML = ONBOARDING_STEPS
    .map((_, i) => `<span class="${i === onboardingStepIndex ? "active" : ""}"></span>`)
    .join("");
  const nextBtn = document.querySelector('[data-action="onboarding-next"]');
  const isLast = onboardingStepIndex === ONBOARDING_STEPS.length - 1;
  nextBtn.textContent = isLast ? "Commencer" : "Suivant";
  document.querySelector('[data-action="onboarding-skip"]').hidden = isLast;
}

async function finishOnboarding() {
  document.getElementById("onboarding-modal").hidden = true;
  try {
    currentArtisan = await Api.updateMe({ onboarding_termine: true });
  } catch (err) {
    /* pas grave si ca echoue, on ne bloque pas l'utilisateur */
  }
}

function maybeShowOnboarding() {
  if (!currentArtisan || currentArtisan.onboarding_termine) return;
  onboardingStepIndex = 0;
  renderOnboardingStep();
  document.getElementById("onboarding-modal").hidden = false;
}

document.addEventListener("click", (e) => {
  if (e.target.closest('[data-action="onboarding-next"]')) {
    if (onboardingStepIndex === ONBOARDING_STEPS.length - 1) {
      finishOnboarding();
    } else {
      onboardingStepIndex++;
      renderOnboardingStep();
    }
  } else if (e.target.closest('[data-action="onboarding-skip"]')) {
    finishOnboarding();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !document.getElementById("onboarding-modal").hidden) finishOnboarding();
  if (e.key === "Escape") {
    ["panel-profil", "panel-timeline", "panel-archives"].forEach((id) => {
      const el = document.getElementById(id);
      if (el && !el.hidden) el.hidden = true;
    });
  }
});

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
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `view-${view}`;
  });
  if (view === "dashboard") loadDashboard();
  if (view === "prospects") loadClients();
  if (view === "clients") loadClientsDirectory();
  if (view === "devis") loadDevis();
  if (view === "factures") loadFactures();
  if (view === "chantiers") loadChantiers();
  if (view === "planning") loadPlanning();
  if (view === "taches") loadTaches();
  if (view === "documents") loadDocuments();
  if (view === "notifications") loadNotifications();
  if (view === "statistiques") loadStatistiques();
  if (view === "avis") loadAvis();
  if (view === "entreprise") {
    loadEntrepriseForm();
    loadPrestations();
    loadFournisseurs();
    loadConformite();
    loadEquipe();
    loadAutomationStatus();
    loadContrats();
  }
}

// Reflete un compteur sur toutes les pastilles qui representent la meme
// donnee (sidebar desktop + copie dans la barre basse/le tiroir mobile,
// quand elle existe). Purement presentation : une seule valeur deja
// calculee, juste affichee a plusieurs endroits du DOM.
function setBadgeCount(id, count) {
  document.querySelectorAll(`#${id}, #${id}-mobile, #${id}-topbar`).forEach((el) => {
    if (!el) return;
    el.textContent = count;
    el.hidden = count === 0;
  });
}

async function refreshBadges() {
  // Les deux compteurs sont independants : la conformite est une fonction payante
  // (402 si l'abonnement n'est pas actif), on ne veut pas que ca empeche le badge
  // des relances (gratuit) de s'afficher. D'ou Promise.allSettled plutot que Promise.all.
  const [relancerResult, alertesResult, notificationsResult] = await Promise.allSettled([
    Api.devisARelancer(), Api.conformiteAlertes(), Api.listNotifications(),
  ]);

  if (relancerResult.status === "fulfilled") {
    devisDueIds = new Set(relancerResult.value.map((d) => d.id));
    setBadgeCount("badge-relances", relancerResult.value.length);
  } else {
    setBadgeCount("badge-relances", 0);
    console.warn("Impossible de charger les relances a faire :", relancerResult.reason?.message);
  }

  if (alertesResult.status === "fulfilled") {
    setBadgeCount("badge-alertes", alertesResult.value.length);
  } else {
    // 402 si pas abonne : pas d'alerte affichee, c'est attendu.
    setBadgeCount("badge-alertes", 0);
  }

  if (notificationsResult.status === "fulfilled") {
    setBadgeCount("badge-notifications", notificationsResult.value.length);
  } else {
    setBadgeCount("badge-notifications", 0);
    console.warn("Impossible de charger les notifications :", notificationsResult.reason?.message);
  }
}

function setupProfilPanel() {
  document.getElementById("btn-profil").addEventListener("click", () => {
    const content = document.getElementById("profil-content");
    // Le slug (currentArtisan.slug) sert toujours a construire l'URL technique
    // POST /pub/{slug}/demande-devis appelee par le futur site vitrine - il
    // reste disponible cote donnees, simplement plus affiche ici comme un
    // lien a copier : cette URL attend un POST, un artisan qui la colle dans
    // son navigateur (GET) recoit une 405 Method Not Allowed. Ce n'est pas
    // une page publique partageable.
    content.innerHTML = `
      <div class="profil-identity">
        ${profilePhotoObjectUrl
          ? `<img class="crm-avatar profil-identity-avatar profil-identity-avatar-photo" src="${escapeHtml(profilePhotoObjectUrl)}" alt="Photo du compte">`
          : `<div class="crm-avatar profil-identity-avatar">${escapeHtml(monogram(currentArtisan.nom_entreprise))}</div>`}
        <div>
          <div class="profil-identity-name">${escapeHtml(currentArtisan.nom_entreprise)}</div>
          <div class="profil-identity-sub">${escapeHtml(METIER_LABELS[currentArtisan.metier] || currentArtisan.metier)}</div>
        </div>
      </div>
      <div class="profil-row-group">
        <div class="profil-row"><div class="label">Email</div><div class="value">${escapeHtml(currentArtisan.email)}</div></div>
        <div class="profil-row"><div class="label">Ville</div><div class="value">${escapeHtml(currentArtisan.ville || "-")}</div></div>
        <div class="profil-row"><div class="label">SIRET</div><div class="value">${escapeHtml(currentArtisan.siret || "-")}</div></div>
        <div class="profil-row">
          <div class="label">Abonnement Suite Artisan</div>
          <div class="value">
            <span class="badge ${isBillingSubscriptionActive() ? "badge-green" : "badge-gray"}">${isBillingSubscriptionActive() ? "Actif" : "Inactif"}</span>
          </div>
        </div>
      </div>
      ${!isBillingSubscriptionActive() ? '<button type="button" class="btn-primary profil-upgrade-btn" data-action="upgrade-subscription">Voir les tarifs</button>' : ""}
      <div class="form-section">
        <p class="form-section-title">Changer le mot de passe</p>
        <form id="password-change-form" class="form-box">
          <label for="pwd-actuel">Mot de passe actuel</label>
          <input type="password" id="pwd-actuel" required autocomplete="current-password">
          <label for="pwd-nouveau">Nouveau mot de passe</label>
          <input type="password" id="pwd-nouveau" required autocomplete="new-password" minlength="8">
          <p class="field-error" id="password-change-error" hidden></p>
          <div class="form-actions"><button type="submit" class="btn-sm btn-sm-primary">Mettre à jour</button></div>
        </form>
      </div>
    `;
    document.getElementById("panel-profil").hidden = false;
    document.getElementById("password-change-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("password-change-error");
      errorBox.hidden = true;
      const current_password = document.getElementById("pwd-actuel").value;
      const new_password = document.getElementById("pwd-nouveau").value;
      try {
        await Api.changerMotDePasse({ current_password, new_password });
        showToast("Mot de passe mis à jour.");
        document.getElementById("password-change-form").reset();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });
  document.getElementById("panel-profil").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="close-profil"]') || e.target.id === "panel-profil") {
      document.getElementById("panel-profil").hidden = true;
    }
  });
  document.getElementById("btn-logout").addEventListener("click", () => {
    clearToken();
    currentArtisan = null;
    showAuthScreen();
  });
}

// ===================== Entreprise (infos + conformite) =====================
// Vrais onglets (un seul panneau visible a la fois), pas une simple
// navigation d'ancrage : toutes les sections restent chargees en arriere-
// plan des l'ouverture de la vue (switchView() appelle deja tous les
// load*() existants), seule leur visibilite change ici - zero nouvel appel
// reseau au changement d'onglet.
function afficherOngletEntreprise(cible) {
  document.querySelectorAll("#view-entreprise [data-tab-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.tabPanel !== cible;
  });
}

function setupEntrepriseTabs() {
  const tabs = document.getElementById("entreprise-tabs");
  if (!tabs) return;
  tabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-chip");
    if (!btn) return;
    tabs.querySelectorAll(".filter-chip").forEach((c) => {
      c.classList.remove("active");
      c.setAttribute("aria-selected", "false");
    });
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    afficherOngletEntreprise(btn.dataset.tab);
  });
  // Sans cet appel, les 8 panneaux restent tous visibles (leur etat naturel
  // dans le HTML) tant qu'aucun clic n'a jamais eu lieu sur un onglet - le
  // gestionnaire de clic ci-dessus ne s'execute qu'au premier clic. Le nom
  // de l'onglet actif par defaut vient du bouton deja marque .active dans
  // le HTML (voir index.html), jamais code en dur ici.
  const ongletParDefaut = tabs.querySelector(".filter-chip.active")?.dataset.tab || "profil";
  afficherOngletEntreprise(ongletParDefaut);
}

function applyProfilePhoto(url) {
  const enterprisePhoto = document.getElementById("enterprise-profile-photo");
  const enterpriseFallback = document.getElementById("enterprise-profile-monogram");
  const topbarPhoto = document.getElementById("topbar-profile-photo");
  const topbarFallback = document.getElementById("topbar-profile-fallback");
  const hasPhoto = Boolean(url);
  if (enterprisePhoto) {
    enterprisePhoto.hidden = !hasPhoto;
    enterprisePhoto.src = url || "";
  }
  if (enterpriseFallback) enterpriseFallback.hidden = hasPhoto;
  if (topbarPhoto) {
    topbarPhoto.hidden = !hasPhoto;
    topbarPhoto.src = url || "";
  }
  if (topbarFallback) topbarFallback.hidden = hasPhoto;
}

function updateProfilePhotoControls() {
  const hasPhoto = Boolean(currentArtisan && currentArtisan.photo_profil_url);
  const choose = document.getElementById("profile-photo-choose");
  const remove = document.getElementById("profile-photo-delete");
  if (choose) choose.textContent = hasPhoto ? "Remplacer la photo" : "Ajouter une photo";
  if (remove) remove.hidden = !hasPhoto;
}

function clearProfilePhoto() {
  if (profilePhotoObjectUrl) URL.revokeObjectURL(profilePhotoObjectUrl);
  profilePhotoObjectUrl = null;
  profilePhotoApiPath = null;
  applyProfilePhoto(null);
}

async function refreshProfilePhoto({ force = false } = {}) {
  const path = currentArtisan && currentArtisan.photo_profil_url;
  updateProfilePhotoControls();
  if (!path) {
    clearProfilePhoto();
    return;
  }
  if (!force && profilePhotoObjectUrl && profilePhotoApiPath === path) {
    applyProfilePhoto(profilePhotoObjectUrl);
    return;
  }
  const nextUrl = await protectedImageUrl(path);
  if (profilePhotoObjectUrl) URL.revokeObjectURL(profilePhotoObjectUrl);
  profilePhotoObjectUrl = nextUrl;
  profilePhotoApiPath = path;
  applyProfilePhoto(nextUrl);
}

function refreshEntrepriseProfileSummary() {
  // On nomme les champs manquants au lieu de les compter. « 3 informations
  // manquantes » oblige a relire tout le formulaire pour trouver lesquelles ;
  // « SIRET, adresse et assurance » dit ou aller. Et quand tout est
  // renseigne, le bloc DISPARAIT : une barre de progression a 100 % est une
  // decoration, et elle occupait le coin le plus visible de la page.
  const champs = [
    { valeur: currentArtisan.nom_entreprise, nom: "le nom de l'entreprise" },
    { valeur: currentArtisan.metier, nom: "le métier" },
    { valeur: currentArtisan.email, nom: "l'email" },
    { valeur: currentArtisan.telephone, nom: "le téléphone" },
    { valeur: currentArtisan.ville, nom: "la ville" },
    { valeur: currentArtisan.code_postal, nom: "le code postal" },
    { valeur: currentArtisan.adresse, nom: "l'adresse" },
    { valeur: currentArtisan.siret, nom: "le SIRET" },
    { valeur: currentArtisan.assurance_decennale_nom, nom: "l'assureur décennale" },
  ];
  const manquants = champs.filter((c) => !String(c.valeur || "").trim());
  const progression = Math.round(((champs.length - manquants.length) / champs.length) * 100);
  document.getElementById("enterprise-profile-monogram").textContent = monogram(currentArtisan.nom_entreprise || "SA");
  document.getElementById("enterprise-profile-name").textContent = currentArtisan.nom_entreprise || "Entreprise";
  document.getElementById("enterprise-profile-trade").textContent = METIER_LABELS[currentArtisan.metier] || currentArtisan.metier || "";

  const bloc = document.querySelector(".enterprise-profile-completion");
  bloc.hidden = manquants.length === 0;
  if (manquants.length) {
    const noms = manquants.map((c) => c.nom);
    const liste = noms.length === 1 ? noms[0] : `${noms.slice(0, -1).join(", ")} et ${noms[noms.length - 1]}`;
    document.getElementById("enterprise-profile-completion-label").textContent = `Profil complété à ${progression}%`;
    document.getElementById("enterprise-profile-progress").style.width = `${progression}%`;
    document.getElementById("enterprise-profile-missing").textContent = `Il manque ${liste}.`;
  }
  updateProfilePhotoControls();
}

function loadEntrepriseForm() {
  document.getElementById("ent-nom-entreprise").value = currentArtisan.nom_entreprise || "";
  document.getElementById("ent-metier").value = currentArtisan.metier || "general";
  document.getElementById("ent-telephone").value = currentArtisan.telephone || "";
  document.getElementById("ent-email").value = currentArtisan.email || "";
  document.getElementById("ent-ville").value = currentArtisan.ville || "";
  document.getElementById("ent-code-postal").value = currentArtisan.code_postal || "";
  document.getElementById("ent-adresse").value = currentArtisan.adresse || "";
  document.getElementById("ent-siret").value = currentArtisan.siret || "";
  document.getElementById("ent-assurance").value = currentArtisan.assurance_decennale_nom || "";
  refreshEntrepriseProfileSummary();
  loadSiteMedia().catch(showSiteMediaError);

  const automationBox = document.getElementById("automatisation-form-box");
  const automationPaywall = document.getElementById("automatisation-paywall");
  const automationDisponible = hasPlan("pro");
  automationBox.hidden = !automationDisponible;
  automationPaywall.hidden = automationDisponible;
  if (!automationDisponible) {
    automationPaywall.innerHTML = renderUpgradeCard(
      "Automatisations réservées au plan Pro",
      "Suite Artisan identifie les factures à relancer dès le plan Essentiel. Le plan Pro envoie automatiquement les relances de devis et de factures.",
      "pro"
    );
    return;
  }

  document.getElementById("auto-devis-j1").value = currentArtisan.relance_devis_j1;
  document.getElementById("auto-devis-j2").value = currentArtisan.relance_devis_j2;
  document.getElementById("auto-devis-j3").value = currentArtisan.relance_devis_j3;
  document.getElementById("auto-facture-jours").value = currentArtisan.relance_facture_jours;
}

function setupEntrepriseForm() {
  document.getElementById("entreprise-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("entreprise-form-error");
    errorBox.hidden = true;
    const submitBtn = e.target.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      currentArtisan = await Api.updateMe({
        nom_entreprise: document.getElementById("ent-nom-entreprise").value,
        metier: document.getElementById("ent-metier").value,
        telephone: emptyToNull(document.getElementById("ent-telephone").value),
        ville: emptyToNull(document.getElementById("ent-ville").value),
        code_postal: emptyToNull(document.getElementById("ent-code-postal").value),
        adresse: emptyToNull(document.getElementById("ent-adresse").value),
        siret: emptyToNull(document.getElementById("ent-siret").value),
        assurance_decennale_nom: emptyToNull(document.getElementById("ent-assurance").value),
      });
      refreshEntrepriseProfileSummary();
      showToast("Informations enregistrees.");
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
    }
  });
  document.getElementById("entreprise-form-cancel").addEventListener("click", () => {
    loadEntrepriseForm();
    document.getElementById("entreprise-form-error").hidden = true;
  });
}

function setupProfilePhoto() {
  const input = document.getElementById("profile-photo-file");
  const choose = document.getElementById("profile-photo-choose");
  const remove = document.getElementById("profile-photo-delete");
  const errorBox = document.getElementById("profile-photo-error");
  choose.addEventListener("click", () => input.click());
  input.addEventListener("change", async () => {
    if (!input.files || !input.files[0]) return;
    errorBox.hidden = true;
    choose.disabled = true;
    const previous = choose.textContent;
    choose.textContent = "Traitement...";
    try {
      currentArtisan = await Api.uploadProfilePhoto(new FormData(document.getElementById("profile-photo-form")));
      await refreshProfilePhoto({ force: true });
      refreshEntrepriseProfileSummary();
      showToast("Photo de profil enregistrée.");
    } catch (error) {
      errorBox.hidden = false;
      errorBox.textContent = error.message;
    } finally {
      input.value = "";
      choose.disabled = false;
      choose.textContent = previous;
      updateProfilePhotoControls();
    }
  });
  remove.addEventListener("click", async () => {
    if (!(await confirmDialog("Supprimer la photo de profil ?", { danger: true }))) return;
    errorBox.hidden = true;
    remove.disabled = true;
    try {
      await Api.deleteProfilePhoto();
      currentArtisan = await Api.me();
      clearProfilePhoto();
      refreshEntrepriseProfileSummary();
      showToast("Photo de profil supprimée.");
    } catch (error) {
      errorBox.hidden = false;
      errorBox.textContent = error.message;
    } finally {
      remove.disabled = false;
    }
  });
}

function setupAutomatisationForm() {
  document.getElementById("automatisation-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("automatisation-form-error");
    errorBox.hidden = true;
    const submitBtn = e.target.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    try {
      currentArtisan = await Api.updateMe({
        relance_devis_j1: parseInt(document.getElementById("auto-devis-j1").value, 10),
        relance_devis_j2: parseInt(document.getElementById("auto-devis-j2").value, 10),
        relance_devis_j3: parseInt(document.getElementById("auto-devis-j3").value, 10),
        relance_facture_jours: parseInt(document.getElementById("auto-facture-jours").value, 10),
      });
      showToast("Delais de relance enregistres.");
      refreshBadges();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
    }
  });
}

async function loadAutomationStatus() {
  const box = document.getElementById("automation-status");
  if (!hasPlan("pro")) {
    box.innerHTML = "";
    return;
  }
  try {
    const s = await Api.automationStatus();
    const badge = s.email_configure
      ? '<span class="badge badge-green">Actif</span>'
      : '<span class="badge badge-orange">Non configure</span>';
    const detail = s.email_configure
      ? `Envoi reel des relances et notifications via ${escapeHtml(s.fournisseur)}.`
      : `Les relances automatiques sont detectees mais pas envoyees : aucun fournisseur email n'est configure cote serveur (variable RESEND_API_KEY). En attendant, utilisez "Copier le lien client" pour les envoyer vous-meme.`;
    box.innerHTML = `
      <div class="dash-row"><span>Emails automatiques</span>${badge}</div>
      <p class="section-hint" style="margin-top:4px;">${detail}</p>
      ${s.derniere_execution ? `<p class="section-hint">Dernier passage : ${fmtDateTime(s.derniere_execution)} (${escapeHtml(s.derniere_execution_resume || "")}). Prochain vers ${fmtDateTime(s.prochaine_execution_estimee)}.</p>` : ""}
    `;
  } catch (err) {
    box.innerHTML = "";
  }
}

// ===================== Equipe =====================
const MEMBRE_ROLE_LABELS = { administrateur: "Administrateur", salarie: "Salarié" };

async function loadEquipe() {
  const list = document.getElementById("equipe-list");
  const addBtn = document.getElementById("btn-show-membre-form");
  if (!hasPlan("business")) {
    addBtn.hidden = true;
    list.innerHTML = renderUpgradeCard(
      "Gérez votre équipe",
      "Affectez vos chantiers et vos tâches à vos collaborateurs, avec des rôles et permissions.",
      "business"
    );
    return;
  }
  addBtn.hidden = !estAdministrateur();
  list.innerHTML = skeletonCards();
  try {
    const equipe = await Api.listEquipe();
    if (equipe.length === 0) {
      list.innerHTML = '<div class="empty-state">Personne dans votre équipe pour le moment. Vous êtes la seule personne sur ce compte.</div>';
      return;
    }
    list.innerHTML = equipe.map(renderMembreCard).join("");
  } catch (err) {
    // 402 si pas abonne : la liste (lecture) reste gratuite normalement, mais
    // on affiche quand meme un message clair en cas d'erreur inattendue.
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderMembreCard(m) {
  const estMoi = currentUtilisateur && currentUtilisateur.membre_id === m.id;
  let actions = "";
  if (estAdministrateur()) {
    actions += `<button type="button" class="btn-sm" data-action="toggle-membre-actif" data-id="${m.id}" data-actif="${m.actif}">${m.actif ? "Désactiver" : "Réactiver"}</button>`;
    if (!estMoi) {
      actions += `<button type="button" class="btn-sm btn-sm-danger" data-action="delete-membre" data-id="${m.id}">Supprimer</button>`;
    }
  }
  return `
  <div class="item-card enterprise-record">
    <div class="enterprise-record-main">
      <div class="item-title">${escapeHtml(m.nom)}${estMoi ? " (vous)" : ""}</div>
      <div class="item-sub">${escapeHtml(m.email)}</div>
      ${!m.actif ? '<div class="item-meta"><span class="badge badge-gray">Compte désactivé</span></div>' : ""}
    </div>
    <span class="badge enterprise-record-status ${m.role === "administrateur" ? "badge-blue" : "badge-gray"}">${MEMBRE_ROLE_LABELS[m.role] || m.role}</span>
    ${actions ? `<div class="item-actions enterprise-record-actions">${actions}</div>` : ""}
  </div>`;
}

function showMembreForm() {
  const container = document.getElementById("membre-form-container");
  container.innerHTML = `
    <div class="form-box">
      <h3>Ajouter un membre</h3>
      <form id="membre-form">
        <div class="form-grid">
          <div><label for="mb-nom">Nom *</label><input type="text" id="mb-nom" required></div>
          <div><label for="mb-email">Email *</label><input type="email" id="mb-email" required></div>
          <div><label for="mb-password">Mot de passe * (8 caractères minimum)</label><input type="password" id="mb-password" minlength="8" required></div>
          <div>
            <label for="mb-role">Rôle</label>
            <select id="mb-role">
              <option value="salarie">Salarié (accès normal)</option>
              <option value="administrateur">Administrateur (peut gérer l'équipe)</option>
            </select>
          </div>
        </div>
        <p class="field-error" id="membre-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
          <button type="button" class="btn-sm" data-action="cancel-membre-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("membre-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("membre-form-error");
    errorBox.hidden = true;
    try {
      await Api.createMembre({
        nom: document.getElementById("mb-nom").value,
        email: document.getElementById("mb-email").value,
        password: document.getElementById("mb-password").value,
        role: document.getElementById("mb-role").value,
      });
      showToast("Membre ajouté. Communiquez-lui son email et son mot de passe pour qu'il se connecte.");
      container.hidden = true;
      container.innerHTML = "";
      loadEquipe();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

function setupEquipeView() {
  document.getElementById("btn-show-membre-form").addEventListener("click", showMembreForm);
  document.getElementById("membre-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-membre-form"]')) {
      const container = document.getElementById("membre-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });
  document.getElementById("equipe-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "toggle-membre-actif") {
      const actif = btn.dataset.actif === "true";
      await withErrorToast(async () => {
        await Api.updateMembre(id, { actif: !actif });
        showToast(actif ? "Membre désactivé." : "Membre réactivé.");
        loadEquipe();
      });
    } else if (btn.dataset.action === "delete-membre") {
      if (!(await confirmDialog("Supprimer ce membre de l'équipe ?", { danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteMembre(id);
        showToast("Membre supprimé.");
        loadEquipe();
      });
    }
  });
}

// ===================== Catalogue de prestations =====================
const PRESTATION_CATEGORIE_DEFAUT = "Sans catégorie";

async function loadPrestations() {
  const list = document.getElementById("prestations-list");
  list.innerHTML = skeletonCards();
  try {
    const prestations = await Api.listPrestations();
    prestationsCache = prestations;
    if (prestations.length === 0) {
      list.innerHTML = `<div class="empty-state">
        Aucune prestation dans votre catalogue.<br><br>
        Ajoutez vos prestations types pour les retrouver en tapant leur nom lors de la création d'un devis.
      </div>`;
      return;
    }
    list.innerHTML = prestations.map(renderPrestationCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderPrestationCard(p) {
  return `
  <div class="item-card enterprise-record">
    <div class="enterprise-record-main">
      <div class="item-title">${escapeHtml(p.description)}</div>
      <div class="item-sub">${escapeHtml(p.categorie || PRESTATION_CATEGORIE_DEFAUT)} · ${escapeHtml(p.unite)} · TVA ${p.taux_tva}%</div>
    </div>
    <strong class="enterprise-record-amount">${fmtEuro(p.prix_unitaire_ht)}</strong>
    <div class="item-actions enterprise-record-actions">
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-prestation" data-id="${p.id}">Supprimer</button>
    </div>
  </div>`;
}

function setupPrestationsView() {
  document.querySelector('[data-action="show-prestation-form"]').addEventListener("click", () => {
    const container = document.getElementById("prestation-form-container");
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouvelle prestation</h3>
        <form id="prestation-form">
          <div class="form-grid">
            <div><label for="pr-description">Description *</label><input type="text" id="pr-description" required placeholder="Ex: Peinture murale"></div>
            <div><label for="pr-categorie">Catégorie</label><input type="text" id="pr-categorie" placeholder="Ex: Peinture"></div>
            <div><label for="pr-unite">Unité</label><input type="text" id="pr-unite" value="u" placeholder="u, m2, h, forfait..."></div>
            <div><label for="pr-prix">Prix unitaire HT *</label><input type="number" step="0.01" min="0" id="pr-prix" required></div>
            <div>
              <label for="pr-tva">TVA</label>
              <select id="pr-tva">
                <option value="10">10% (rénovation)</option>
                <option value="20">20% (neuf)</option>
              </select>
            </div>
          </div>
          <p class="field-error" id="prestation-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
            <button type="button" class="btn-sm" data-action="cancel-prestation-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("prestation-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("prestation-form-error");
      errorBox.hidden = true;
      try {
        await Api.createPrestation({
          description: document.getElementById("pr-description").value,
          categorie: emptyToNull(document.getElementById("pr-categorie").value),
          unite: document.getElementById("pr-unite").value.trim() || "u",
          prix_unitaire_ht: parseFloat(document.getElementById("pr-prix").value),
          taux_tva: parseFloat(document.getElementById("pr-tva").value),
        });
        showToast("Prestation ajoutée au catalogue.");
        container.hidden = true;
        container.innerHTML = "";
        loadPrestations();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });

  document.getElementById("prestation-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-prestation-form"]')) {
      const container = document.getElementById("prestation-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("prestations-list").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="delete-prestation"]');
    if (!btn) return;
    if (!(await confirmDialog("Supprimer cette prestation du catalogue ?", { danger: true }))) return;
    await withErrorToast(async () => {
      await Api.deletePrestation(parseInt(btn.dataset.id, 10));
      showToast("Prestation supprimee.");
      loadPrestations();
    });
  });
}

// ===================== Fournisseurs =====================
const FOURNISSEUR_CATEGORIE_LABELS = { materiaux: "Matériaux", sous_traitance: "Sous-traitance", outillage: "Outillage", autre: "Autre" };
let fournisseursCache = [];
async function ensureFournisseursCache() {
  try {
    fournisseursCache = await Api.listFournisseurs();
  } catch (err) {
    fournisseursCache = [];
  }
  return fournisseursCache;
}

let equipeCache = [];
async function ensureEquipeCache() {
  try {
    equipeCache = await Api.listEquipe();
  } catch (err) {
    equipeCache = [];
  }
  return equipeCache;
}

async function loadFournisseurs() {
  const list = document.getElementById("fournisseurs-list");
  list.innerHTML = skeletonCards();
  try {
    const fournisseurs = await Api.listFournisseurs();
    fournisseursCache = fournisseurs;
    if (fournisseurs.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun fournisseur pour le moment. Ajoutez vos fournisseurs de matériaux, sous-traitants ou loueurs pour les retrouver lors de la saisie de vos dépenses de chantier.</div>';
      return;
    }
    list.innerHTML = fournisseurs.map(renderFournisseurCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderFournisseurCard(f) {
  const contact = [f.contact_nom, f.telephone, f.email].filter(Boolean).map(escapeHtml).join(" · ");
  return `
  <div class="item-card enterprise-record">
    <div class="enterprise-record-main">
      <div class="item-title">${escapeHtml(f.nom)}</div>
      <div class="item-sub">${contact || "Pas de contact renseigné"}</div>
      ${f.total_achats > 0 ? `<div class="item-meta">Total achats : ${fmtEuro(f.total_achats)}</div>` : ""}
    </div>
    <span class="badge badge-gray enterprise-record-status">${FOURNISSEUR_CATEGORIE_LABELS[f.categorie] || f.categorie}</span>
    <div class="item-actions enterprise-record-actions">
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-fournisseur" data-id="${f.id}">Supprimer</button>
    </div>
  </div>`;
}

function setupFournisseursView() {
  document.querySelector('[data-action="show-fournisseur-form"]').addEventListener("click", () => {
    const container = document.getElementById("fournisseur-form-container");
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouveau fournisseur</h3>
        <form id="fournisseur-form">
          <div class="form-grid">
            <div><label for="fo-nom">Nom *</label><input type="text" id="fo-nom" required placeholder="Ex: Point P"></div>
            <div>
              <label for="fo-categorie">Catégorie</label>
              <select id="fo-categorie">${Object.entries(FOURNISSEUR_CATEGORIE_LABELS).map(([v, l]) => `<option value="${v}" ${v === "autre" ? "selected" : ""}>${l}</option>`).join("")}</select>
            </div>
            <div><label for="fo-contact">Contact</label><input type="text" id="fo-contact"></div>
            <div><label for="fo-telephone">Téléphone</label><input type="tel" id="fo-telephone"></div>
            <div><label for="fo-email">Email</label><input type="email" id="fo-email"></div>
            <div><label for="fo-adresse">Adresse</label><input type="text" id="fo-adresse"></div>
          </div>
          <label for="fo-notes" style="margin-top:14px;">Notes</label>
          <textarea id="fo-notes"></textarea>
          <p class="field-error" id="fournisseur-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
            <button type="button" class="btn-sm" data-action="cancel-fournisseur-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("fournisseur-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("fournisseur-form-error");
      errorBox.hidden = true;
      try {
        await Api.createFournisseur({
          nom: document.getElementById("fo-nom").value,
          categorie: document.getElementById("fo-categorie").value,
          contact_nom: emptyToNull(document.getElementById("fo-contact").value),
          telephone: emptyToNull(document.getElementById("fo-telephone").value),
          email: emptyToNull(document.getElementById("fo-email").value),
          adresse: emptyToNull(document.getElementById("fo-adresse").value),
          notes: emptyToNull(document.getElementById("fo-notes").value),
        });
        showToast("Fournisseur ajouté.");
        container.hidden = true;
        container.innerHTML = "";
        loadFournisseurs();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });

  document.getElementById("fournisseur-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-fournisseur-form"]')) {
      const container = document.getElementById("fournisseur-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("fournisseurs-list").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="delete-fournisseur"]');
    if (!btn) return;
    if (!(await confirmDialog("Supprimer ce fournisseur ?", { danger: true }))) return;
    await withErrorToast(async () => {
      await Api.deleteFournisseur(parseInt(btn.dataset.id, 10));
      showToast("Fournisseur supprime.");
      loadFournisseurs();
    });
  });
}

// ===================== Statistiques =====================
function fmtMoisCourt(moisIso) {
  const [annee, mois] = String(moisIso).split("-").map(Number);
  if (!annee || !mois) return escapeHtml(moisIso);
  return new Date(annee, mois - 1, 1).toLocaleDateString("fr-FR", { month: "short" });
}

// Graphique en aire (SVG inline) du CA par mois : memes points que
// l'ancienne liste .dash-row (a.ca_par_mois), juste trace au lieu
// d'enumere. Echelle lineaire simple, pas de librairie.
function caAreaChartSvg(caParMois) {
  const W = 760, H = 220, PAD_L = 44, PAD_R = 8, PAD_T = 12, PAD_B = 24;
  const values = caParMois.map((m) => m.ca);
  const max = Math.max(1, ...values);
  const innerW = W - PAD_L - PAD_R, innerH = H - PAD_T - PAD_B;
  const stepX = caParMois.length > 1 ? innerW / (caParMois.length - 1) : 0;
  const points = values.map((v, i) => ({
    x: PAD_L + stepX * i,
    y: PAD_T + innerH - (v / max) * innerH,
  }));
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${PAD_T + innerH} L${points[0].x.toFixed(1)},${PAD_T + innerH} Z`;
  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const y = PAD_T + innerH * (1 - f);
    return `<line x1="${PAD_L}" y1="${y.toFixed(1)}" x2="${W - PAD_R}" y2="${y.toFixed(1)}" class="chart-gridline"/>
      <text x="${PAD_L - 8}" y="${(y + 3).toFixed(1)}" class="chart-axis-label" text-anchor="end">${fmtEuro(Math.round(max * f))}</text>`;
  }).join("");
  const moisLabels = caParMois.map((m, i) => {
    if (caParMois.length > 8 && i % 2 !== 0 && i !== caParMois.length - 1) return "";
    return `<text x="${points[i].x.toFixed(1)}" y="${H - 6}" class="chart-axis-label" text-anchor="middle">${fmtMoisCourt(m.mois)}</text>`;
  }).join("");
  return `
  <svg viewBox="0 0 ${W} ${H}" class="chart-svg" role="img" aria-label="Chiffre d'affaires par mois">
    <defs>
      <linearGradient id="chartFade" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="var(--sa-accent)" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="var(--sa-accent)" stop-opacity="0"/>
      </linearGradient>
    </defs>
    ${gridLines}
    <path d="${areaPath}" fill="url(#chartFade)"/>
    <path d="${linePath}" fill="none" stroke="var(--sa-accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    ${moisLabels}
  </svg>`;
}

// Interpolation pure entre deux couleurs hex (#rrggbb) - aucune donnee
// metier, sert uniquement a degrader la couleur de fond de chaque etape
// du ruban "Performance commerciale" (pale -> accent champagne).
function mixHexColors(hexA, hexB, t) {
  const a = [1, 3, 5].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [1, 3, 5].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

async function loadStatistiques() {
  const container = document.getElementById("statistiques-content");
  container.innerHTML = skeletonCards();
  if (!hasPlan("essentiel")) {
    container.innerHTML = renderUpgradeCard(
      "Statistiques réservées aux abonnés",
      "Le suivi de la performance commerciale et financière (CA, taux d'acceptation, impayés, panier moyen) fait partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  try {
    const a = await Api.analytics();
    const caTotal = a.ca_par_mois.reduce((s, m) => s + m.ca, 0);
    // Delta honnete : dernier mois vs precedent (mêmes points deja recus),
    // pas une periode fabriquee.
    const nbMois = a.ca_par_mois.length;
    const dernierMois = nbMois ? a.ca_par_mois[nbMois - 1].ca : 0;
    const moisPrecedent = nbMois > 1 ? a.ca_par_mois[nbMois - 2].ca : null;
    const deltaPct = moisPrecedent ? Math.round(((dernierMois - moisPrecedent) / moisPrecedent) * 100) : null;

    const chartHtml = a.ca_par_mois.length
      ? caAreaChartSvg(a.ca_par_mois)
      : '<div class="dash-empty">Pas encore de paiement enregistré.</div>';

    const sourcesHtml = a.sources_acquisition.length
      ? a.sources_acquisition.map((s) => {
          const maxContacts = Math.max(1, ...a.sources_acquisition.map((x) => x.nb_clients));
          return `
          <div class="acq-source-row">
            <span class="acq-source-label">${escapeHtml(CLIENT_SOURCE_LABELS[s.source] || s.source)}</span>
            <div class="acq-source-bar"><div class="remplissage" style="width:${Math.round((s.nb_clients / maxContacts) * 100)}%;"></div></div>
            <span class="acq-source-value">${s.nb_clients} contact${s.nb_clients > 1 ? "s" : ""}, ${s.nb_gagnes} client${s.nb_gagnes > 1 ? "s" : ""} (${fmtEuro(s.ca)})</span>
          </div>`;
        }).join("")
      : '<div class="dash-empty">Pas encore de contact enregistré.</div>';

    const commercialSteps = [
      { label: "Devis envoyés", nb: a.nb_devis_total },
      { label: "Devis signés", nb: a.nb_devis_signes },
      { label: "Clients acquis", nb: a.nb_clients_acquis },
    ];
    const commercialFunnelHtml = commercialSteps.map((etape, i) => {
      const precedent = i > 0 ? commercialSteps[i - 1].nb : 0;
      const conversion = i > 0 && precedent && etape.nb <= precedent
        ? Math.round((etape.nb / precedent) * 100)
        : null;
      // Le degrade etait calcule en inline sur des valeurs de l'ancienne
      // identite sombre : sur du papier, le texte y tombait jusqu'a
      // 3.01:1. L'etape porte desormais son rang en classe, et c'est la
      // feuille de style qui decide - la densite se lit sur le FILET du
      // bas, pas sur un aplat derriere le texte.
      return `${i ? '<span class="stats-commercial-arrow" aria-hidden="true">&rarr;</span>' : ""}
        <div class="stats-commercial-step est-etape-${i + 1}">
          <span>${escapeHtml(etape.label)}</span>
          <strong>${etape.nb}${conversion !== null ? ` (${conversion} %)` : ""}</strong>
        </div>`;
    }).join("");

    const recurrentPct = a.nb_clients_acquis
      ? Math.round((a.nb_clients_recurrents / a.nb_clients_acquis) * 100)
      : 0;
    const topSource = a.sources_acquisition.slice().sort((x, y) => y.nb_gagnes - x.nb_gagnes || y.ca - x.ca)[0] || null;
    const pointsCles = [
      deltaPct === null
        ? "Le suivi mensuel sera comparable après deux mois de paiements."
        : `Le chiffre d'affaires du dernier mois ${deltaPct >= 0 ? "progresse" : "recule"} de ${Math.abs(deltaPct)}% par rapport au mois précédent.`,
      topSource
        ? `${CLIENT_SOURCE_LABELS[topSource.source] || topSource.source} est la première source d'acquisition avec ${topSource.nb_gagnes} client${topSource.nb_gagnes > 1 ? "s" : ""} gagné${topSource.nb_gagnes > 1 ? "s" : ""}.`
        : "Aucune source d'acquisition n'est encore mesurable.",
      a.montant_impayes > 0
        ? `${fmtEuro(a.montant_impayes)} restent à encaisser sur les factures ouvertes.`
        : "Aucun montant impayé sur les factures ouvertes.",
    ];

    // Un rapport mene avec ses conclusions, pas avec ses preuves. Les
    // « points cles » etaient en bas de page, apres quatre panneaux de
    // chiffres : personne ne lisait la lecture. Ils ouvrent desormais.
    //
    // La page adopte la gouttiere des pages COMPOSEES (voir
    // DIRECTION-ARTISTIQUE.md) : les intitules vivent dans la marge, le
    // contenu a droite. C'est la forme d'un rapport, et Statistiques en
    // est un - contrairement aux listes, qui ont besoin de leur largeur.
    container.innerHTML = `
      ${saSection("Ce qu'il faut retenir",
        `<div class="stats-lecture">${pointsCles.map((p) => `<p>${escapeHtml(p)}</p>`).join("")}</div>`)}

      ${saSection("Chiffre d'affaires", `
        <div class="stats-ca">
          <div class="stats-ca-tete">
            <span class="stats-ca-valeur">${fmtEuro(caTotal)}</span>
            <span class="stats-ca-note">encaissé${deltaPct !== null ? ` · <span class="${deltaPct >= 0 ? "est-hausse" : "est-baisse"}">${deltaPct >= 0 ? "+" : ""}${deltaPct} % sur le dernier mois</span>` : ""}</span>
          </div>
          <div class="stats-chart-wrap">${chartHtml}</div>
          <div class="stats-ca-legende">
            <span>Pipeline <strong>${fmtEuro(a.valeur_pipeline)}</strong></span>
            <span>Encore à encaisser <strong>${fmtEuro(a.montant_impayes)}</strong></span>
          </div>
        </div>`, "douze derniers mois")}

      ${saSection("Performance commerciale", `
        <div class="stats-commercial-funnel">${commercialFunnelHtml}</div>
        <div class="stats-metric-list">
          <div><span>Taux de signature</span><strong>${a.taux_acceptation === null || a.taux_acceptation === undefined ? "—" : a.taux_acceptation + " %"}</strong></div>
          <div><span>Panier moyen</span><strong>${fmtEuro(a.panier_moyen)}</strong></div>
          <div><span>Valeur du pipeline</span><strong>${fmtEuro(a.valeur_pipeline)}</strong></div>
        </div>`)}

      ${saSection("Acquisition", `<div class="acq-source-list">${sourcesHtml}</div>`,
        "d'où viennent vos clients")}

      ${saSection("Clients et paiements", `
        <div class="stats-metric-list">
          <div><span>Clients récurrents</span><strong>${recurrentPct} %</strong></div>
          <div><span>Délai moyen de paiement</span><strong>${a.delai_moyen_paiement_jours !== null ? a.delai_moyen_paiement_jours + " j" : "—"}</strong></div>
          <div><span>Montant impayé</span><strong>${fmtEuro(a.montant_impayes)}</strong></div>
        </div>`)}
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// ===================== Avis clients =====================
const AVIS_SOURCE_LABELS = { manuel: "Saisi à la main", lien_public: "Envoyé par le client" };

// Les etoiles pleines et les vides ne se lisent pas au meme niveau : toutes
// dans la meme encre laiton, « ★★★★☆ » se compte au lieu de se voir. Les
// vides reculent d'un ton, et la note reste lisible pour qui ne distingue
// pas les deux glyphes - l'element porte un aria-label « n sur 5 ».
function starsText(note) {
  return `${"★".repeat(note)}<span class="avis-stars-vides">${"☆".repeat(5 - note)}</span>`;
}

// Partagee entre le panneau timeline client et le panneau "Avis a demander"
// de la vue Avis clients : meme action, deux points d'entree.
async function demanderAvisEtCopierLien(clientId) {
  await withErrorToast(async () => {
    const { token_avis } = await Api.demanderAvis(clientId);
    const url = `${window.location.origin}/avis-public.html?t=${token_avis}`;
    try {
      await navigator.clipboard.writeText(url);
      showToast("Lien copié. Envoyez-le à votre client par email ou SMS.");
    } catch (err) {
      showToast(url, false);
    }
  });
}

function avisResumeHtml(avis, clients) {
  // Panneau "Avis a demander" : clients gagnes qui n'ont pas encore d'avis
  // enregistre - simple difference d'ensembles sur des donnees deja
  // chargees (clientsCache + avis), aucun nouvel appel, aucune invention.
  const idsAvecAvis = new Set(avis.map((a) => a.client_id).filter(Boolean));
  const aDemander = (clients || []).filter((c) => c.statut === "gagne" && !idsAvecAvis.has(c.id)).slice(0, 2);

  if (!avis.length) {
    return `<p class="avis-lede">Aucun avis pour le moment.</p>
      <p class="avis-lede-sub">Saisissez-en un, ou envoyez une demande depuis la fiche d'un client.</p>`;
  }

  // La moyenne SEULE ment : 4,7 peut cacher quatre 5 et un 1, ou cinq
  // 4,7 - ce ne sont pas les memes entreprises et ce n'est pas la meme
  // chose a faire. La repartition est donc affichee a cote, en reglettes.
  const moyenne = avis.reduce((s, a) => s + a.note, 0) / avis.length;
  const nonPublies = avis.filter((a) => !a.publie_site).length;
  const enFrancais = (n) => ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix"][n] || String(n);
  const attente = nonPublies === 0
    ? "Tous sont publiés sur votre site."
    : nonPublies === 1
      ? "Un n'est pas encore publié sur votre site."
      : `${enFrancais(nonPublies).replace(/^./, (c) => c.toUpperCase())} ne sont pas encore publiés sur votre site.`;

  const lede = `
    <p class="avis-lede">${moyenne.toFixed(1).replace(".", ",")} sur 5, sur ${avis.length} avis.</p>
    <p class="avis-lede-sub">${attente}</p>`;

  const maxi = Math.max(...[5, 4, 3, 2, 1].map((n) => avis.filter((a) => a.note === n).length));
  const repartition = `
    <div class="avis-repartition">
      ${[5, 4, 3, 2, 1].map((n) => {
        const compte = avis.filter((a) => a.note === n).length;
        const part = maxi ? (compte / maxi) * 100 : 0;
        return `<div class="avis-repartition-ligne">
          <span class="avis-repartition-note">${n}<span aria-hidden="true"> ★</span></span>
          <span class="avis-repartition-piste"><span class="avis-repartition-trait" style="width:${part}%"></span></span>
          <span class="avis-repartition-compte">${compte}</span>
        </div>`;
      }).join("")}
    </div>`;

  const demander = aDemander.length ? `
    <div class="avis-demander">
      ${aDemander.map((c) => `
        <div class="avis-demander-ligne">
          <span class="avis-demander-nom">${escapeHtml(c.nom)}</span>
          <span class="avis-demander-sub">${escapeHtml(c.societe || c.ville || "Client gagné")}</span>
          <button type="button" class="btn-sm" data-action="demander-avis" data-client-id="${c.id}">Demander</button>
        </div>`).join("")}
    </div>` : "";

  return lede
    + saSection("Répartition", repartition, `${avis.length} avis reçus`)
    + saSection("À demander", demander, "clients gagnés sans avis");
}

// Dernier avis charge, pour filtrer par onglet (Tous/Publies/Non publies)
// sans reinterroger l'API a chaque clic.
let avisCache = [];

async function loadAvis() {
  const list = document.getElementById("avis-list");
  const resume = document.getElementById("avis-resume");
  list.innerHTML = skeletonCards();
  try {
    const [avis, clients] = await Promise.all([Api.listAvis(), ensureClientsCache()]);
    avisCache = avis;
    resume.innerHTML = avisResumeHtml(avis, clients);
    const setCount = (sel, n) => {
      const el = document.querySelector(`#avis-filters [data-publie="${sel}"] .filter-chip-count`);
      if (el) el.textContent = `(${n})`;
    };
    setCount("", avis.length);
    setCount("1", avis.filter((a) => a.publie_site).length);
    setCount("0", avis.filter((a) => !a.publie_site).length);
    renderAvisListFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderAvisListFiltered() {
  const list = document.getElementById("avis-list");
  if (avisCache.length === 0) {
    list.innerHTML = etatVide(
      "Vos avis clients vivront ici.",
      "Envoyez une demande depuis la fiche d'un client, ou saisissez un avis reçu par téléphone. Vous choisissez ensuite lesquels paraissent sur votre site.",
      { action: "show-avis-request-form", libelle: "Demander un avis" },
    );
    return;
  }
  const filtres = currentAvisFilter === "" ? avisCache : avisCache.filter((a) => (currentAvisFilter === "1" ? a.publie_site : !a.publie_site));
  list.innerHTML = filtres.length
    ? `<div class="avis-grid">${filtres.map(renderAvisCard).join("")}</div>`
    : etatFiltre("Aucun avis dans cet onglet.");
}

// Un avis EST une citation : c'est le temoignage qui doit dominer, pas le
// cadre autour. La carte s'ouvre donc sur la note, puis donne la parole au
// client en corps de texte, et ne range l'attribution qu'apres - l'ordre
// d'une citation sur une page imprimee. L'avatar monogramme a disparu :
// deux lettres dans un carre gris n'apprenaient rien que le nom, ecrit
// juste a cote, ne disait deja.
function renderAvisCard(a) {
  const auteur = a.client_nom || a.nom_auteur || "Anonyme";
  const source = AVIS_SOURCE_LABELS[a.source] || "Origine inconnue";
  return `
  <div class="avis-card ${a.publie_site ? "est-publie" : ""}">
    <div class="avis-card-top">
      <span class="avis-stars" aria-label="${a.note} sur 5">${starsText(a.note)}</span>
      <div class="action-menu">
        <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur cet avis">
          <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
        </button>
        <div class="action-menu-panel" role="menu">
          <button type="button" class="is-danger" data-action="delete-avis" data-id="${a.id}">Supprimer</button>
        </div>
      </div>
    </div>
    ${a.commentaire
      ? `<blockquote class="avis-card-quote">« ${escapeHtml(a.commentaire)} »</blockquote>`
      : `<p class="avis-card-sans-mot">Une note, sans commentaire.</p>`}
    <p class="avis-card-attribution">${escapeHtml(auteur)}<span class="avis-card-origine">${fmtDate(a.created_at)} · ${source}</span></p>
    <div class="avis-card-bottom">
      <span class="avis-card-etat">${a.publie_site ? "Publié sur le site" : "Non publié"}</span>
      <button type="button" class="btn-sm ${a.publie_site ? "" : "btn-sm-primary"}" data-action="toggle-publie-site" data-id="${a.id}" data-publie="${a.publie_site ? "1" : "0"}">
        ${a.publie_site ? "Retirer du site" : "Publier sur le site"}
      </button>
    </div>
  </div>`;
}

async function showAvisRequestForm() {
  const container = document.getElementById("avis-form-container");
  const clients = (await ensureClientsCache()).filter((client) => client.statut === "gagne");
  container.innerHTML = `
    <div class="form-box avis-request-form-box">
      <h3>Demander un avis</h3>
      ${clients.length ? `
        <form id="avis-request-form">
          <label for="avis-request-client">Client</label>
          <select id="avis-request-client" required>
            <option value="">Choisir un client</option>
            ${clients.map((client) => `<option value="${client.id}">${escapeHtml(client.nom)}</option>`).join("")}
          </select>
          <p class="section-hint">Le lien d'avis sera copié pour pouvoir être envoyé au client.</p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Copier le lien</button>
            <button type="button" class="btn-sm" data-action="cancel-avis-form">Annuler</button>
          </div>
        </form>`
        : '<p class="section-hint">Aucun client gagné n’est disponible pour une demande d’avis.</p>'}
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("avis-request-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const clientId = parseInt(document.getElementById("avis-request-client").value, 10);
    if (!clientId) return;
    await demanderAvisEtCopierLien(clientId);
    container.hidden = true;
    container.innerHTML = "";
  });
}

function showAvisForm() {
  const container = document.getElementById("avis-form-container");
  container.innerHTML = `
    <div class="form-box">
      <h3>Saisir un avis</h3>
      <form id="avis-form">
        <div class="form-grid">
          <div>
            <label for="av-note">Note</label>
            <select id="av-note">
              <option value="5">5 - Excellent</option>
              <option value="4">4 - Très bien</option>
              <option value="3">3 - Correct</option>
              <option value="2">2 - Déçu</option>
              <option value="1">1 - Très déçu</option>
            </select>
          </div>
          <div><label for="av-client">Client (optionnel)</label><select id="av-client"><option value="">Aucun</option>${clientOptionsHtml()}</select></div>
          <div><label for="av-nom-auteur">Nom (si pas de client lié)</label><input type="text" id="av-nom-auteur"></div>
        </div>
        <label for="av-commentaire" style="margin-top:10px;">Commentaire (optionnel)</label>
        <textarea id="av-commentaire" placeholder="Ce que le client a dit..."></textarea>
        <p class="field-error" id="avis-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
          <button type="button" class="btn-sm" data-action="cancel-avis-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("avis-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("avis-form-error");
    errorBox.hidden = true;
    const clientId = document.getElementById("av-client").value;
    try {
      await Api.createAvis({
        note: parseInt(document.getElementById("av-note").value, 10),
        client_id: clientId ? parseInt(clientId, 10) : null,
        nom_auteur: emptyToNull(document.getElementById("av-nom-auteur").value),
        commentaire: emptyToNull(document.getElementById("av-commentaire").value),
      });
      showToast("Avis ajouté.");
      container.hidden = true;
      container.innerHTML = "";
      loadAvis();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

function setupAvisView() {
  document.querySelector('[data-action="show-avis-form"]').addEventListener("click", showAvisForm);
  document.querySelector('[data-action="show-avis-request-form"]').addEventListener("click", showAvisRequestForm);
  document.getElementById("avis-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#avis-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentAvisFilter = chip.dataset.publie;
    renderAvisListFiltered();
  });
  document.getElementById("avis-resume").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="demander-avis"]');
    if (btn) await demanderAvisEtCopierLien(parseInt(btn.dataset.clientId, 10));
  });
  document.getElementById("avis-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-avis-form"]')) {
      const container = document.getElementById("avis-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });
  document.getElementById("avis-list").addEventListener("click", async (e) => {
    const deleteBtn = e.target.closest('[data-action="delete-avis"]');
    if (deleteBtn) {
      if (!(await confirmDialog("Supprimer cet avis ?", { danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteAvis(parseInt(deleteBtn.dataset.id, 10));
        showToast("Avis supprimé.");
        loadAvis();
      });
      return;
    }
    const publieBtn = e.target.closest('[data-action="toggle-publie-site"]');
    if (publieBtn) {
      const dejaPublie = publieBtn.dataset.publie === "1";
      await withErrorToast(async () => {
        await Api.updateAvis(parseInt(publieBtn.dataset.id, 10), { publie_site: !dejaPublie });
        showToast(dejaPublie ? "Avis retiré du site." : "Avis publié sur le site.");
        loadAvis();
      });
    }
  });
}

// ===================== Notifications =====================
const NOTIFICATION_TYPE_LABELS = {
  devis_relance: "Devis", facture_relance: "Facture", conformite: "Conformité", message_client: "Message",
  nouvelle_demande_devis: "Prospect",
};

// Vraie inbox : les notifications urgentes (n.urgent, deja calcule cote
// serveur) forment un groupe "Important" separe du reste - meme donnee que
// l'ancienne pastille rouge, seul le regroupement change. Ligne dense
// plutot qu'un item-card par notification.
let notificationsCache = [];
let currentNotificationModule = "";

async function loadNotifications() {
  const list = document.getElementById("notifications-list");
  list.innerHTML = skeletonCards();
  try {
    const notifications = await Api.listNotifications();
    notificationsCache = notifications;
    const setCount = (mode, n) => {
      const el = document.querySelector(`#notifications-filters [data-mode="${mode}"] .filter-chip-count`);
      if (el) el.textContent = `(${n})`;
    };
    setCount("toutes", notifications.length);
    setCount("non-lues", notifications.filter((n) => !n.lu).length);
    setCount("importantes", notifications.filter((n) => n.urgent).length);
    renderNotificationsFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderNotificationsFiltered() {
  const list = document.getElementById("notifications-list");
  if (notificationsCache.length === 0) {
    // Pas de bouton : cette page se remplit toute seule. Proposer une action
    // reviendrait a inventer un geste que l'artisan n'a pas a faire.
    list.innerHTML = etatVide(
      "Rien à signaler.",
      "Un devis lu sans réponse, une facture qui dépasse son échéance, une assurance qui arrive à terme : c'est ici que le produit vous préviendra.",
    );
    return;
  }
  const base = currentNotificationsFilter === "non-lues" ? notificationsCache.filter((n) => !n.lu)
    : currentNotificationsFilter === "importantes" ? notificationsCache.filter((n) => n.urgent)
    : notificationsCache;
  const moduleTypes = {
    commercial: new Set(["devis_relance", "nouvelle_demande_devis", "message_client"]),
    gestion: new Set(["facture_relance"]),
    entreprise: new Set(["conformite"]),
  };
  const filtrees = currentNotificationModule
    ? base.filter((n) => moduleTypes[currentNotificationModule]?.has(n.type))
    : base;
  if (filtrees.length === 0) {
    list.innerHTML = etatFiltre("Aucune notification dans cet onglet.");
    return;
  }
  const aujourdHui = new Date();
  const hier = new Date(aujourdHui);
  hier.setDate(hier.getDate() - 1);
  const memeJour = (iso, date) => {
    const valeur = new Date(iso);
    return valeur.getFullYear() === date.getFullYear() && valeur.getMonth() === date.getMonth() && valeur.getDate() === date.getDate();
  };
  // Les groupes passent par la gouttiere de `.sa-section` : l'intitule et le
  // decompte vivent dans la marge, a droite du filet, comme sur l'accueil, la
  // fiche client et les statistiques. C'est ce qui manquait le plus a cet
  // ecran - il etait le seul a parler une autre langue que le reste du
  // produit, avec ses lignes en boites posees sur le papier.
  const nombre = (n, singulier, pluriel) => `${n} ${n > 1 ? pluriel : singulier}`;
  const groupes = [
    { label: "À traiter", classe: "est-urgente",
      note: (n) => nombre(n, "demande une action", "demandent une action"),
      items: filtrees.filter((n) => n.urgent) },
    { label: "Aujourd'hui", classe: "",
      note: (n) => nombre(n, "événement", "événements"),
      items: filtrees.filter((n) => !n.urgent && memeJour(n.date, aujourdHui)) },
    { label: "Hier", classe: "",
      note: (n) => nombre(n, "événement", "événements"),
      items: filtrees.filter((n) => !n.urgent && memeJour(n.date, hier)) },
    { label: "Plus tôt", classe: "",
      note: (n) => nombre(n, "événement", "événements"),
      items: filtrees.filter((n) => !n.urgent && !memeJour(n.date, aujourdHui) && !memeJour(n.date, hier)) },
  ];
  list.innerHTML = groupes
    .filter((groupe) => groupe.items.length)
    .map((groupe) => saSection(
      groupe.label,
      `<div class="notif-lignes">${groupe.items.map(notificationRowHtml).join("")}</div>`,
      groupe.note(groupe.items.length),
      groupe.classe,
    ))
    .join("");
}

function fmtNotificationDate(iso) {
  const valeur = new Date(iso);
  const maintenant = new Date();
  const hier = new Date(maintenant);
  hier.setDate(hier.getDate() - 1);
  const memeJour = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  const heure = valeur.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  if (memeJour(valeur, maintenant)) return `Aujourd'hui · ${heure}`;
  if (memeJour(valeur, hier)) return `Hier · ${heure}`;
  return fmtDate(iso);
}

function notificationRowHtml(n) {
  const actionLabels = {
    devis: "Voir le devis", factures: "Voir la facture", chantiers: "Voir le chantier",
    entreprise: "Mettre à jour", prospects: n.type === "message_client" ? "Voir le message" : "Voir le prospect",
  };
  // Plus d'icone : c'etait le meme glyphe de document pour les cinq types de
  // notification, repete a chaque ligne. Il ne distinguait rien - le bouton
  // d'action, lui, nomme la destination (« Voir la facture », « Voir le
  // devis »). L'etat lu/non lu n'est plus une pastille grise indistinguable
  // d'une puce : il se lit sur l'encre du titre et sur un cran de laiton dans
  // la marge, c'est-a-dire sur la ligne elle-meme.
  return `
  <div class="notif-row ${n.urgent ? "is-urgent" : ""} ${n.lu ? "est-lue" : "est-non-lue"}">
    <span class="notif-cran" aria-hidden="true"></span>
    <div class="notif-main">
      <span class="notif-title">${escapeHtml(n.titre)}</span>
      ${n.sous_titre ? `<span class="notif-sub">${escapeHtml(n.sous_titre)}</span>` : ""}
    </div>
    <time class="notif-date" datetime="${escapeHtml(n.date)}">${fmtNotificationDate(n.date)}</time>
    <button type="button" class="btn-sm" data-action="voir-notification" data-view="${n.view}"
      data-notification-type="${escapeHtml(n.type)}" data-notification-id="${n.notification_id || ""}" data-client-id="${n.client_id || ""}">${actionLabels[n.view] || "Ouvrir"}</button>
    <div class="action-menu">
      <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur cette notification">
        <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
      </button>
      <div class="action-menu-panel" role="menu"><button type="button" data-action="voir-notification" data-view="${n.view}" data-notification-type="${escapeHtml(n.type)}" data-notification-id="${n.notification_id || ""}" data-client-id="${n.client_id || ""}">Ouvrir</button></div>
    </div>
  </div>`;
}

const siteMediaObjectUrls = [];
const siteMediaCategories = {
  realisation: "Réalisation", chantier: "Chantier", equipe: "Équipe", atelier: "Atelier",
  vehicule: "Véhicule", avant: "Avant", apres: "Après", autre: "Autre",
};

function showSiteMediaError(error) {
  const box = document.getElementById("site-media-error");
  box.hidden = false;
  box.textContent = error && error.message ? error.message : "Impossible de charger les médias.";
}

function clearSiteMediaObjectUrls() {
  siteMediaObjectUrls.splice(0).forEach((url) => URL.revokeObjectURL(url));
}

async function hydrateSiteMediaImages() {
  const images = Array.from(document.querySelectorAll("#visual-identity-box img[data-media-url]"));
  await Promise.all(images.map(async (image) => {
    const url = await protectedImageUrl(image.dataset.mediaUrl);
    siteMediaObjectUrls.push(url);
    image.src = url;
  }));
}

function categoryOptions(selected) {
  return Object.entries(siteMediaCategories).map(([value, label]) =>
    `<option value="${value}"${value === selected ? " selected" : ""}>${label}</option>`
  ).join("");
}

async function loadSiteMedia() {
  const errorBox = document.getElementById("site-media-error");
  errorBox.hidden = true;
  const data = await Api.siteMedia();
  clearSiteMediaObjectUrls();
  const logoBox = document.getElementById("site-logo-preview");
  const logoDelete = document.getElementById("site-logo-delete");
  if (data.logo) {
    logoBox.innerHTML = `<img data-media-url="${escapeHtml(data.logo.thumbnail_url)}" alt="Aperçu du logo">`;
    logoDelete.hidden = false;
  } else {
    logoBox.innerHTML = '<span class="media-empty">Aucun logo</span>';
    logoDelete.hidden = true;
  }
  document.getElementById("site-photo-count").textContent = `${data.photos.length} / ${data.max_photos}`;
  document.getElementById("site-photos-list").innerHTML = data.photos.length ? data.photos.map((photo, index) => `
    <article class="site-photo-item" data-media-id="${photo.id}">
      <img data-media-url="${escapeHtml(photo.thumbnail_url)}" alt="${escapeHtml(photo.alt_text || photo.nom_original)}">
      <div class="site-photo-fields">
        <strong>${escapeHtml(photo.nom_original)}</strong>
        <select data-action="media-category" aria-label="Catégorie de ${escapeHtml(photo.nom_original)}">${categoryOptions(photo.categorie)}</select>
        <label class="checkbox-option"><input type="checkbox" data-action="media-active"${photo.actif ? " checked" : ""}> Active sur le site</label>
      </div>
      <div class="site-photo-actions">
        <button type="button" class="btn-sm" data-action="media-up" title="Monter"${index === 0 ? " disabled" : ""}>↑</button>
        <button type="button" class="btn-sm" data-action="media-down" title="Descendre"${index === data.photos.length - 1 ? " disabled" : ""}>↓</button>
        <button type="button" class="btn-sm btn-sm-danger" data-action="media-delete">Supprimer</button>
      </div>
    </article>
  `).join("") : '<p class="media-empty">Aucune photo ajoutée.</p>';
  await hydrateSiteMediaImages();
}

function setupSiteMedia() {
  document.getElementById("site-logo-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.target.querySelector("button[type=submit]");
    button.disabled = true;
    const previous = button.textContent;
    button.textContent = "Traitement...";
    try {
      await Api.uploadSiteLogo(new FormData(event.target));
      event.target.reset();
      await loadSiteMedia();
      showToast("Logo enregistré.");
    } catch (error) {
      showSiteMediaError(error);
    } finally {
      button.disabled = false;
      button.textContent = previous;
    }
  });

  document.getElementById("site-photo-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = event.target.querySelector("button[type=submit]");
    button.disabled = true;
    const previous = button.textContent;
    button.textContent = "Traitement...";
    try {
      await Api.uploadSitePhoto(new FormData(event.target));
      event.target.reset();
      document.getElementById("site-photo-category").value = "realisation";
      await loadSiteMedia();
      showToast("Photo ajoutée.");
    } catch (error) {
      showSiteMediaError(error);
    } finally {
      button.disabled = false;
      button.textContent = previous;
    }
  });

  document.getElementById("site-logo-delete").addEventListener("click", async () => {
    if (!(await confirmDialog("Supprimer le logo ?", { danger: true }))) return;
    try {
      await Api.deleteSiteLogo();
      await loadSiteMedia();
      showToast("Logo supprimé.");
    } catch (error) { showSiteMediaError(error); }
  });

  document.getElementById("site-photos-list").addEventListener("change", async (event) => {
    const item = event.target.closest("[data-media-id]");
    if (!item) return;
    try {
      if (event.target.dataset.action === "media-category") {
        await Api.updateSiteMedia(Number(item.dataset.mediaId), { categorie: event.target.value });
      }
      if (event.target.dataset.action === "media-active") {
        await Api.updateSiteMedia(Number(item.dataset.mediaId), { actif: event.target.checked });
      }
      showToast("Photo mise à jour.");
    } catch (error) {
      showSiteMediaError(error);
      await loadSiteMedia();
    }
  });

  document.getElementById("site-photos-list").addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    const item = event.target.closest("[data-media-id]");
    if (!button || !item) return;
    try {
      if (button.dataset.action === "media-delete") {
        if (!(await confirmDialog("Supprimer cette photo ?", { danger: true }))) return;
        await Api.deleteSiteMedia(Number(item.dataset.mediaId));
      } else {
        const ids = Array.from(document.querySelectorAll("#site-photos-list [data-media-id]"), (node) => Number(node.dataset.mediaId));
        const index = ids.indexOf(Number(item.dataset.mediaId));
        const target = button.dataset.action === "media-up" ? index - 1 : index + 1;
        if (target < 0 || target >= ids.length) return;
        [ids[index], ids[target]] = [ids[target], ids[index]];
        await Api.orderSitePhotos(ids);
      }
      await loadSiteMedia();
    } catch (error) { showSiteMediaError(error); }
  });
}

let currentNotificationsFilter = "toutes"; // toutes | non-lues | importantes

function setupNotificationsView() {
  document.getElementById("notifications-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#notifications-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentNotificationsFilter = chip.dataset.mode;
    renderNotificationsFiltered();
  });
  document.getElementById("notifications-module-filter").addEventListener("change", (e) => {
    currentNotificationModule = e.target.value;
    renderNotificationsFiltered();
  });
  document.getElementById("notifications-list").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="voir-notification"]');
    if (!btn) return;
    await withErrorToast(async () => {
      const notificationId = parseInt(btn.dataset.notificationId, 10);
      const clientId = parseInt(btn.dataset.clientId, 10);
      switchView(btn.dataset.view);
      if (btn.dataset.notificationType === "conformite") {
        const tab = document.querySelector('#entreprise-tabs [data-tab="conformite"]');
        if (tab) tab.click();
      }
      if (btn.dataset.view === "prospects" && Number.isInteger(clientId)) {
        await loadClients();
        await showTimeline(clientId);
      }
      if (Number.isInteger(notificationId)) await Api.markNotificationRead(notificationId);
      refreshBadges();
    });
  });
}

function setupDashboardView() {
  document.getElementById("dashboard-content").addEventListener("click", async (e) => {
    const voirBtn = e.target.closest('[data-action="voir-notification"]');
    if (voirBtn) {
      switchView(voirBtn.dataset.view);
      return;
    }
    const relanceDevisBtn = e.target.closest('[data-action="relancer-devis"]');
    if (relanceDevisBtn) {
      const id = parseInt(relanceDevisBtn.dataset.id, 10);
      await withErrorToast(async () => {
        const result = await Api.relancerDevis(id);
        const feedback = feedbackRelanceDevis(result);
        showToast(feedback.message, feedback.isError);
        loadDashboard();
      });
      return;
    }
    const relanceFactureBtn = e.target.closest('[data-action="relancer-facture"]');
    if (relanceFactureBtn) {
      const id = parseInt(relanceFactureBtn.dataset.id, 10);
      await withErrorToast(async () => {
        await Api.relancerFacture(id);
        showToast("Relance envoyée.");
        loadDashboard();
      });
      return;
    }
    // Etat vide du dashboard (compte neuf) : relaie vers les memes
    // formulaires que QUICK_ACTIONS, aucune nouvelle action.
    const emptyClientBtn = e.target.closest('[data-action="dash-empty-client"]');
    if (emptyClientBtn) {
      const action = QUICK_ACTIONS.find((a) => a.id === "qa-client");
      switchView(action.view);
      setTimeout(action.run, 200);
      return;
    }
    const emptyDevisBtn = e.target.closest('[data-action="dash-empty-devis"]');
    if (emptyDevisBtn) {
      const action = QUICK_ACTIONS.find((a) => a.id === "qa-devis");
      switchView(action.view);
      setTimeout(action.run, 200);
      return;
    }
  });
}

// ===================== Recherche globale (Ctrl+K) =====================
const SEARCH_TYPE_META = {
  client: { label: "Clients & prospects", view: "prospects" },
  devis: { label: "Devis", view: "devis" },
  facture: { label: "Factures", view: "factures" },
  chantier: { label: "Chantiers", view: "chantiers" },
};

let searchDebounceTimer = null;

// Palette de commandes (section "actions rapides") : creer quelque chose en
// un seul geste depuis n'importe quel ecran, au lieu de naviguer puis
// chercher le bouton "+ Nouveau...". Reutilise les formulaires existants -
// aucune nouvelle logique de creation, juste un raccourci d'acces.
const QUICK_ACTIONS = [
  { id: "qa-devis", label: "Nouveau devis", view: "devis", run: () => showDevisForm(null) },
  { id: "qa-client", label: "Nouveau contact", view: "prospects", run: () => showClientForm() },
  { id: "qa-facture", label: "Nouvelle facture", view: "factures", run: () => showFactureForm() },
  { id: "qa-chantier", label: "Nouveau chantier", view: "chantiers", run: () => document.querySelector('[data-action="show-chantier-form"]').click() },
  { id: "qa-tache", label: "Nouvelle tache", view: "taches", run: () => showTacheForm() },
  { id: "qa-rdv", label: "Nouveau rendez-vous", view: "planning", run: () => document.querySelector('[data-action="show-evenement-form"]').click() },
];

function quickActionsHtml(actions) {
  if (actions.length === 0) return "";
  const items = actions.map((a) => `
    <button type="button" class="search-result-item search-action-item" data-action-id="${a.id}">
      <div class="title">+ ${escapeHtml(a.label)}</div>
    </button>`).join("");
  return `<div class="search-result-group">Actions rapides</div>${items}`;
}

function openSearch() {
  const modal = document.getElementById("search-modal");
  modal.hidden = false;
  const input = document.getElementById("search-input");
  input.value = "";
  document.getElementById("search-results").innerHTML = quickActionsHtml(QUICK_ACTIONS);
  input.focus();
}

function closeSearch() {
  document.getElementById("search-modal").hidden = true;
}

async function runSearch(q) {
  const resultsBox = document.getElementById("search-results");
  const query = (q || "").trim();
  if (!query) {
    resultsBox.innerHTML = quickActionsHtml(QUICK_ACTIONS);
    return;
  }
  const actionsMatch = QUICK_ACTIONS.filter((a) => a.label.toLowerCase().includes(query.toLowerCase()));
  if (query.length < 2) {
    resultsBox.innerHTML = quickActionsHtml(actionsMatch) || '<div class="search-empty">Tapez au moins 2 caracteres pour chercher...</div>';
    return;
  }
  try {
    const results = await Api.search(query);
    const parGroupe = {};
    results.forEach((r) => { (parGroupe[r.type] = parGroupe[r.type] || []).push(r); });
    const resultsHtml = Object.keys(parGroupe).map((type) => {
      const meta = SEARCH_TYPE_META[type] || { label: type, view: type };
      const items = parGroupe[type].map((r) => `
        <button type="button" class="search-result-item" data-type="${type}" data-id="${r.id}">
          <div class="title">${escapeHtml(r.label)}</div>
          ${r.sublabel ? `<div class="sub">${escapeHtml(r.sublabel)}</div>` : ""}
        </button>`).join("");
      return `<div class="search-result-group">${meta.label}</div>${items}`;
    }).join("");
    const combined = quickActionsHtml(actionsMatch) + resultsHtml;
    resultsBox.innerHTML = combined || '<div class="search-empty">Aucun résultat.</div>';
  } catch (err) {
    resultsBox.innerHTML = quickActionsHtml(actionsMatch) + `<div class="search-empty">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function setupGlobalSearch() {
  document.getElementById("btn-open-search").addEventListener("click", openSearch);

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      const modal = document.getElementById("search-modal");
      if (modal.hidden) openSearch(); else closeSearch();
    } else if (e.key === "Escape") {
      closeSearch();
    }
  });

  document.getElementById("search-modal").addEventListener("click", (e) => {
    if (e.target.id === "search-modal") closeSearch();
  });

  document.getElementById("search-input").addEventListener("input", (e) => {
    clearTimeout(searchDebounceTimer);
    const q = e.target.value;
    searchDebounceTimer = setTimeout(() => runSearch(q), 250);
  });

  /* La palette s'ouvre au clavier (Ctrl+K) et se remplit au clavier - puis
     il fallait prendre la souris pour choisir. Ni fleches, ni Entree : ce
     n'etait pas une palette de commandes, c'etait un champ de recherche
     avec un raccourci. Les fleches parcourent les resultats, Entree ouvre
     le resultat marque (ou le premier), Echap referme. */
  const resultats = () => [...document.querySelectorAll("#search-results .search-result-item")];
  const marque = () => document.querySelector("#search-results .search-result-item.est-marque");
  const marquer = (el) => {
    resultats().forEach((r) => r.classList.remove("est-marque"));
    if (!el) return;
    el.classList.add("est-marque");
    el.scrollIntoView({ block: "nearest" });
  };
  document.getElementById("search-input").addEventListener("keydown", (e) => {
    const liste = resultats();
    if (!liste.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const i = liste.indexOf(marque());
      const suivant = e.key === "ArrowDown"
        ? liste[i < 0 || i === liste.length - 1 ? 0 : i + 1]
        : liste[i <= 0 ? liste.length - 1 : i - 1];
      marquer(suivant);
    } else if (e.key === "Enter") {
      e.preventDefault();
      (marque() || liste[0]).click();
    }
  });
  // Une frappe qui change la liste invalide la marque : on repart du haut.
  document.getElementById("search-results").addEventListener("mousemove", (e) => {
    const item = e.target.closest(".search-result-item");
    if (item && !item.classList.contains("est-marque")) marquer(item);
  });

  document.getElementById("search-results").addEventListener("click", (e) => {
    const actionItem = e.target.closest(".search-action-item");
    if (actionItem) {
      const action = QUICK_ACTIONS.find((a) => a.id === actionItem.dataset.actionId);
      closeSearch();
      if (action) {
        switchView(action.view);
        setTimeout(action.run, 200);
      }
      return;
    }
    const item = e.target.closest(".search-result-item");
    if (!item) return;
    const meta = SEARCH_TYPE_META[item.dataset.type];
    closeSearch();
    if (meta) {
      switchView(meta.view);
      if (item.dataset.type === "client") {
        setTimeout(() => showTimeline(parseInt(item.dataset.id, 10)), 300);
      }
    }
  });
}

function setupTabs() {
  document.querySelectorAll(".nav-link").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });
}

// ===================== Navigation mobile (barre basse + tiroir "Plus") =====================
// Purement presentation : les boutons de la barre basse et du tiroir portent
// deja la classe .nav-link et un data-view, donc setupTabs()/switchView()
// ci-dessus les cablent et les activent sans aucun code specifique. Ici on
// ne gere que l'ouverture/fermeture du tiroir et le relais de deux boutons
// (recherche, profil) vers leurs equivalents desktop deja fonctionnels.
function setupMobileNav() {
  const drawer = document.getElementById("more-drawer");
  const openBtn = document.getElementById("btn-open-more");
  if (!drawer || !openBtn) return;

  function openDrawer() {
    drawer.hidden = false;
    openBtn.setAttribute("aria-expanded", "true");
  }
  function closeDrawer() {
    drawer.hidden = true;
    openBtn.setAttribute("aria-expanded", "false");
  }

  openBtn.addEventListener("click", openDrawer);
  drawer.addEventListener("click", (e) => {
    if (e.target.id === "more-drawer" || e.target.closest(".nav-link")) closeDrawer();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !drawer.hidden) closeDrawer();
  });

  const searchMobileBtn = document.getElementById("btn-open-search-mobile");
  if (searchMobileBtn) searchMobileBtn.addEventListener("click", () => openSearch());

  const profilMobileBtn = document.getElementById("btn-profil-mobile");
  const profilBtn = document.getElementById("btn-profil");
  if (profilMobileBtn && profilBtn) profilMobileBtn.addEventListener("click", () => profilBtn.click());
}

// ===================== Topbar desktop (recherche, creation rapide, notifications, profil) =====================
// Purement presentation : relaie vers des controles/handlers deja existants
// (openSearch, QUICK_ACTIONS + switchView, panneau #btn-profil, vue notifications).
// Aucune nouvelle logique metier - seulement de nouveaux points d'entree vers
// des actions qui existaient deja (menu Ctrl+K, formulaires de creation).
function setupTopbar() {
  const createBtn = document.getElementById("btn-topbar-create");
  const createMenu = document.getElementById("topbar-create-menu");
  if (createBtn && createMenu) {
    createMenu.innerHTML = QUICK_ACTIONS.map(
      (a) => `<button type="button" role="menuitem" data-action-id="${a.id}">+ ${escapeHtml(a.label)}</button>`
    ).join("");
    const closeCreateMenu = () => {
      createMenu.hidden = true;
      createBtn.setAttribute("aria-expanded", "false");
    };
    createBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = createMenu.hidden;
      closeCreateMenu();
      if (willOpen) {
        createMenu.hidden = false;
        createBtn.setAttribute("aria-expanded", "true");
      }
    });
    createMenu.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-action-id]");
      if (!btn) return;
      const action = QUICK_ACTIONS.find((a) => a.id === btn.dataset.actionId);
      closeCreateMenu();
      if (action) {
        switchView(action.view);
        setTimeout(action.run, 200);
      }
    });
    document.addEventListener("click", (e) => {
      if (!createMenu.hidden && !e.target.closest(".topbar-create")) closeCreateMenu();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !createMenu.hidden) closeCreateMenu();
    });
  }

  const notifTopbarBtn = document.getElementById("btn-topbar-notifications");
  if (notifTopbarBtn) notifTopbarBtn.addEventListener("click", () => switchView("notifications"));

  const profilTopbarBtn = document.getElementById("btn-profil-topbar");
  const profilBtn = document.getElementById("btn-profil");
  if (profilTopbarBtn && profilBtn) profilTopbarBtn.addEventListener("click", () => profilBtn.click());
}

// ===================== Menu d'actions generique ("•••") =====================
// Reutilise par toutes les listes premium (Devis, Factures...) : le bouton
// declencheur et les actions a l'interieur du panneau portent deja leurs
// propres data-action/data-id/data-token, geres par la delegation existante
// de chaque liste (#devis-list, #factures-list...) - ce controleur ne fait
// qu'ouvrir/fermer le panneau, jamais de logique metier.
function closeAllActionMenus(except) {
  document.querySelectorAll(".action-menu.is-open").forEach((menu) => {
    if (menu === except) return;
    menu.classList.remove("is-open");
    const trigger = menu.querySelector(".action-menu-trigger");
    if (trigger) trigger.setAttribute("aria-expanded", "false");
  });
}

function setupActionMenus() {
  document.addEventListener("click", (e) => {
    const trigger = e.target.closest('[data-action="toggle-action-menu"]');
    if (trigger) {
      const menu = trigger.closest(".action-menu");
      const wasOpen = menu.classList.contains("is-open");
      closeAllActionMenus();
      if (!wasOpen) {
        menu.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
      }
      return;
    }
    if (e.target.closest(".action-menu-panel")) {
      // Une action du menu vient d'etre declenchee (geree par la delegation
      // de la liste parente, ci-dessus/ci-dessous) : on referme le panneau
      // dans tous les cas, que l'action recharge la liste ou non.
      closeAllActionMenus();
      return;
    }
    closeAllActionMenus();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAllActionMenus();
  });
}

// ===================== Tableau de bord =====================
const SITE_STATUT_META = {
  non_livre: { label: "Pas encore livré", badge: "badge-gray" },
  en_cours: { label: "En cours de fabrication", badge: "badge-orange" },
  livre: { label: "En ligne", badge: "badge-green" },
};

function renderPresenceSite(p) {
  const meta = SITE_STATUT_META[p.statut] || { label: p.statut, badge: "badge-gray" };
  let rows = `<div class="dash-row"><span>Statut du site</span><span class="badge ${meta.badge}">${meta.label}</span></div>`;
  if (p.url) {
    rows += `<div class="dash-row"><span>Adresse</span><a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.url)}</a></div>`;
  }
  // Le schema serveur garantit ces deux entiers, mais une charge utile
  // amputee ecrivait « undefined » en toutes lettres sous les yeux de
  // l'artisan. Un tiret dit la meme chose sans avoir l'air casse.
  const compte = (n) => (Number.isFinite(n) ? n : "—");
  rows += `<div class="dash-row"><span>Demandes reçues (30 derniers jours)</span><strong>${compte(p.nb_demandes_30j)}</strong></div>`;
  rows += `<div class="dash-row"><span>Demandes reçues (total)</span><strong>${compte(p.nb_demandes_total)}</strong></div>`;
  if (p.nb_demandes_total > 0) {
    rows += `<div class="dash-row"><span>Devenues clients</span><strong>${p.nb_clients_gagnes}${p.taux_conversion !== null ? ` (${p.taux_conversion}%)` : ""}</strong></div>`;
    rows += `<div class="dash-row"><span>CA réellement généré par le site</span><strong>${fmtEuro(p.ca_genere)}</strong></div>`;
  }
  if (p.statut === "non_livre") {
    rows += `<div class="dash-empty">${escapeHtml(SITE_VITRINE_OFFER.nom)} — ${SITE_VITRINE_OFFER.creation}&nbsp;&euro; HT à la création + ${SITE_VITRINE_OFFER.mensuel}&nbsp;&euro; HT/mois de gestion &amp; maintenance. C'est nous qui le réalisons et le gérons. Cette option est disponible avec tous les plans, y compris Gratuit.</div>`;
  }
  return rows;
}

const URGENCE_CLASSES = { haute: "urgence-haute", moyenne: "urgence-moyenne", basse: "urgence-basse", info: "urgence-info" };

function taskRowHtml(item) {
  const classe = URGENCE_CLASSES[item.urgence] || URGENCE_CLASSES.info;
  // Action en un clic quand elle est sans ambiguite (relancer directement) :
  // pas besoin de traverser un autre ecran pour un geste deja evident
  // (section "UX one click" du cahier des charges). L'urgence se lit
  // desormais a un point de couleur discret (CSS), plus a une icone emoji.
  const actionBtn = item.action
    ? `<button type="button" class="btn-sm btn-sm-primary" data-action="${item.action}" data-id="${item.actionId}">${item.actionLabel}</button>`
    : "";
  const voirBtn = item.view ? `<button type="button" class="btn-sm" data-action="voir-notification" data-view="${item.view}">Voir</button>` : "";
  // Composition en champs distincts (type / titre / contexte / montant)
  // plutot qu'une seule chaine concatenee : memes donnees deja calculees
  // par prioriteItems, juste reparties pour rester scannable d'un coup
  // d'oeil (voir aussi item.label, conserve tel quel pour compat).
  // Le type (Facture/Devis/...) n'est plus affiche en ligne : chaque ligne
  // vit desormais sous un en-tete de categorie (voir dashTaskGroupsHtml) qui
  // joue deja ce role, comme sur la reference.
  return `
  <div class="task-row ${classe}">
    <span class="task-dot"></span>
    <div class="task-row-body">
      <div class="task-row-top">
        <span class="task-row-titre">${item.titre || item.label}</span>
      </div>
      ${item.meta ? `<span class="task-row-meta">${item.meta}</span>` : ""}
    </div>
    ${item.montant ? `<span class="task-row-montant">${item.montant}</span>` : ""}
    <span class="task-row-actions">${actionBtn}${voirBtn}</span>
  </div>`;
}

// Regroupe les items "a faire" par categorie avec un sous-en-tete (comme
// "FACTURES EN RETARD" / "DEVIS A RELANCER" sur la reference), au lieu
// d'une liste plate ou seul un badge en ligne indiquait le type. Memes
// items, seul le regroupement visuel change.
function dashTaskGroupsHtml(groupes) {
  return groupes
    .filter((g) => g.items.length)
    .map((g) => `
      <div class="task-group">
        <p class="task-group-label">${g.label}</p>
        <div class="task-feed">${g.items.slice(0, 2).map(taskRowHtml).join("")}</div>
      </div>`)
    .join("");
}

const RECOMMANDATION_URGENCE_LABELS = { haute: "Important", moyenne: "À surveiller", basse: "Info" };

function recommandationRowHtml(r) {
  const badgeClasse = r.urgence === "haute" ? "badge-red" : r.urgence === "moyenne" ? "badge-orange" : "badge-blue";
  return `
  <div class="recommandation-row">
    <span>${escapeHtml(r.message)}</span>
    <span class="recommandation-row-actions">
      <span class="badge ${badgeClasse}">${RECOMMANDATION_URGENCE_LABELS[r.urgence] || r.urgence}</span>
      <button type="button" class="btn-sm" data-action="voir-notification" data-view="${r.view}">Voir</button>
    </span>
  </div>`;
}

function sousScoreHtml(s) {
  if (s.valeur === null || s.valeur === undefined) {
    return `<div class="sante-sous-score">
      <div class="ligne"><span>${s.label}</span></div>
      <div class="raison">${escapeHtml(s.raison_absence || "Pas encore assez de données.")}</div>
    </div>`;
  }
  // Reference morte trouvee lors de la fusion des feuilles de style : les
  // tokens --v5-* n'existaient dans AUCUNE des deux, et ce depuis
  // longtemps - la barre etait donc peinte avec une couleur invalide,
  // c'est-a-dire pas peinte du tout. Le commentaire d'origine parlait
  // d'une « scene sombre du dashboard » qui n'existe plus.
  // Les tokens semantiques conviennent : ils sont calibres sur le papier,
  // qui est justement le fond de cette barre.
  const couleur = s.valeur >= 70 ? "var(--sa-success)" : s.valeur >= 40 ? "var(--sa-warning)" : "var(--sa-danger)";
  return `<div class="sante-sous-score">
    <div class="ligne"><span>${s.label}</span><span class="valeur">${s.valeur}/100</span></div>
    <div class="sante-barre"><div class="remplissage" style="width:${s.valeur}%;background:${couleur};"></div></div>
  </div>`;
}

function santeWidgetHtml(sante) {
  const sousScores = [sante.commercial, sante.tresorerie, sante.chantiers, sante.conformite, sante.organisation];
  return `
  <div class="sante-widget">
    <div class="sante-score-global">
      ${sante.score_global !== null && sante.score_global !== undefined
        ? `<div class="chiffre">${sante.score_global}<span class="sur-cent">/100</span></div><div class="libelle">Score global</div>`
        : `<div class="dash-empty" style="max-width:160px;">${escapeHtml(sante.raison_absence_globale || "Pas assez de données.")}</div>`}
    </div>
    <div class="sante-sous-scores">
      ${sousScores.map(sousScoreHtml).join("")}
    </div>
  </div>`;
}

function activationChecklistHtml(activation) {
  if (!activation || activation.entierement_active) return "";
  const etapes = [
    { fait: activation.entreprise_configuree, label: "Entreprise (logo, téléphone)", view: "entreprise" },
    { fait: activation.premier_client, label: "Premier client", view: "prospects" },
    { fait: activation.premier_devis, label: "Premier devis", view: "devis" },
    { fait: activation.premier_devis_envoye, label: "Premier devis envoyé", view: "devis" },
    { fait: activation.premier_chantier, label: "Premier chantier", view: "chantiers" },
    { fait: activation.premiere_facture, label: "Première facture", view: "factures" },
  ];
  const nbFaites = etapes.filter((e) => e.fait).length;
  return `
  <div class="activation-card">
    <div class="activation-head"><h3>Mise en route</h3><span>${nbFaites}/${etapes.length}</span></div>
    <div class="activation-bar"><span style="width:${Math.round(nbFaites / etapes.length * 100)}%;"></span></div>
    <div class="activation-list">
      ${etapes.map((e) => `
        <div class="activation-item ${e.fait ? "is-done" : ""}"${e.fait ? "" : ` data-action="voir-notification" data-view="${e.view}" role="button" tabindex="0"`}>${escapeHtml(e.label)}</div>`).join("")}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------
// L'ACCUEIL — « la journee »
// ---------------------------------------------------------------------
// L'ancienne version ouvrait sur une bande de quatre KPI : chiffre
// d'affaires, devis en attente, factures a relancer, chantiers en cours.
// Quatre nombres alignes ne repondent a aucune question. L'artisan qui
// ouvre son logiciel le matin n'en pose qu'une : « qu'est-ce que je dois
// faire aujourd'hui ? »
//
// La page repond donc dans cet ordre : une PHRASE qui resume la situation,
// puis ce qu'il y a a faire, puis la journee, et seulement ensuite les
// chiffres du mois - qui sont un bilan, pas une consigne.

/** La phrase d'ouverture. Elle est calculee, jamais decorative : c'est le
 *  resume que l'utilisateur lirait a voix haute en ouvrant son cahier. */
function dashLede(nbAFaire, retards, montantRetard) {
  if (!nbAFaire) return { titre: "Rien ne vous attend ce matin.", detail: "Tout est à jour. Bonne journée." };
  const titre = nbAFaire === 1 ? "Une chose à traiter aujourd'hui." : `${nbAFaire} choses à traiter aujourd'hui.`;
  if (retards) {
    return {
      titre,
      detail: retards === 1
        ? `Dont une facture en retard, ${fmtEuro(montantRetard)}.`
        : `Dont ${retards} factures en retard, ${fmtEuro(montantRetard)} au total.`,
      alerte: true,
    };
  }
  return { titre, detail: "Aucun retard de paiement." };
}

/** Une section composee : intitule dans la marge, contenu a droite. C'est
 *  la structure d'un document technique, et c'est ce qui distingue les
 *  pages composees des pages denses. Voir DIRECTION-ARTISTIQUE.md. */
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
document.addEventListener("click", (e) => {
  const bouton = e.target.closest(".empty-state [data-action]");
  if (!bouton) return;
  const cible = document.querySelector(`.view-header [data-action="${bouton.dataset.action}"], .subsection-header [data-action="${bouton.dataset.action}"]`);
  if (cible && cible !== bouton) { e.preventDefault(); cible.click(); }
});

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

/** Les chiffres du mois : une ligne typographiee, pas quatre cartes. Le
 *  filet sous chaque montant remplace la boite - c'est le meme geste que
 *  le soulignement d'un total sur un devis. */
function dashChiffresHtml(d, chantiersEnCours) {
  const chiffre = (label, valeur, note, classe = "") => `
    <div class="dash-chiffre ${classe}">
      <span class="dash-chiffre-label">${label}</span>
      <span class="dash-chiffre-valeur">${valeur}</span>
      <span class="dash-chiffre-note">${note}</span>
    </div>`;
  return `
    <div class="dash-chiffres">
      ${chiffre("Facture ce mois-ci", fmtEuro(d.finances.ca_mois), "encaissé et en attente")}
      ${chiffre("Reste à encaisser", fmtEuro(d.finances.a_encaisser),
        d.finances.a_encaisser > 0 ? "sur factures émises" : "tout est encaissé",
        d.finances.a_encaisser > 0 ? "est-du" : "")}
      ${chiffre("Devis en attente", String(d.commercial.devis_en_attente), `${fmtEuro(d.commercial.valeur_pipeline)} de pipeline`)}
      ${chiffre("Chantiers ouverts", String(chantiersEnCours.length), chantiersEnCours.length ? "en cours ou en pause" : "aucun chantier actif")}
    </div>`;
}

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  container.innerHTML = '<div class="dash-squelette"><span></span><span></span><span></span></div>';
  try {
    const [d, recommandations, sante, activation, chantiers] = await Promise.all([
      Api.dashboard(), Api.dashboardRecommandations(), Api.dashboardSante(), Api.dashboardActivation(),
      // "Chantiers en cours" n'existe pas dans DashboardOut (voir backend/app/
      // schemas.py) : meme endpoint que la page Chantiers, avec le meme
      // repli silencieux qu'ailleurs si le plan ne l'autorise pas.
      Api.listChantiers().catch(() => []),
    ]);

    const dateBrut = new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
    const dateLabel = dateBrut.charAt(0).toUpperCase() + dateBrut.slice(1);

    // Compte neuf : aucun client, devis ou facture pose encore. Un ecran de
    // chiffres a zero ne sert a rien - on montre un vrai point de depart.
    const estCompteNeuf = !!activation && !activation.premier_client && !activation.premier_devis && !activation.premiere_facture;
    if (estCompteNeuf) {
      container.innerHTML = `
        <header class="dash-entete">
          <p class="dash-date">${dateLabel}</p>
          <h2 class="dash-lede">Votre atelier est prêt.</h2>
          <p class="dash-lede-detail">Ajoutez votre premier client, puis créez votre premier devis. Cette page se remplira de votre activité au fur et à mesure.</p>
          <div class="dash-entete-actions">
            <button type="button" class="btn-primary" data-action="dash-empty-client">Ajouter un client</button>
            <button type="button" class="btn-secondary" data-action="dash-empty-devis">Créer un devis</button>
          </div>
        </header>
        ${saSection("Mise en route", activationChecklistHtml(activation))}
      `;
      return;
    }

    // "A faire" : regroupe par nature, comme un cahier de releve. Les
    // rendez-vous vivent a part - ce sont des horaires, pas des taches.
    const taskGroupes = [
      {
        label: "Factures en retard",
        items: d.aujourdhui.factures_en_retard.map((f) => ({
          urgence: "haute", view: "factures",
          titre: escapeHtml(f.client_nom), meta: `${escapeHtml(f.numero)} · en retard`,
          montant: fmtEuro(f.montant_restant),
          label: `${escapeHtml(f.numero)} · ${escapeHtml(f.client_nom)} · ${fmtEuro(f.montant_restant)} en retard`,
          ...(hasPlan("essentiel") ? { action: "relancer-facture", actionId: f.id, actionLabel: "Relancer" } : {}),
        })),
      },
      {
        label: "Devis à relancer",
        items: d.aujourdhui.devis_a_relancer.map((dv) => ({
          urgence: "moyenne", view: "devis",
          titre: escapeHtml(dv.client_nom), meta: escapeHtml(dv.numero || "Devis #" + dv.id),
          label: `Relancer ${escapeHtml(dv.client_nom)} (${escapeHtml(dv.numero || "devis #" + dv.id)})`,
          ...(hasPlan("essentiel") && dv.relance_manuelle_possible !== false
            ? { action: "relancer-devis", actionId: dv.id, actionLabel: "Relancer" }
            : {}),
        })),
      },
      {
        label: "Conformité",
        items: d.alertes_conformite.map((c) => ({
          urgence: c.jours_restants < 7 ? "haute" : "moyenne", view: "entreprise",
          titre: escapeHtml(c.libelle), meta: `Expire dans ${c.jours_restants} j`,
          label: `${escapeHtml(c.libelle)} · expire dans ${c.jours_restants} j`,
        })),
      },
      {
        label: "Tâches",
        items: d.aujourdhui.taches.map((t) => ({
          urgence: "moyenne", view: "taches",
          titre: escapeHtml(t.titre),
          label: `Tache du jour : ${escapeHtml(t.titre)}`,
        })),
      },
      {
        label: "Chantiers à venir",
        items: d.aujourdhui.chantiers_a_venir.map((c) => ({
          urgence: "basse", view: "chantiers",
          titre: escapeHtml(c.titre), meta: `Commence le ${fmtDate(c.date_debut)}`,
          label: `Chantier '${escapeHtml(c.titre)}' commence le ${fmtDate(c.date_debut)}`,
        })),
      },
    ];
    const prioriteItems = taskGroupes.flatMap((g) => g.items);
    const retards = d.aujourdhui.factures_en_retard.length;
    const montantRetard = d.aujourdhui.factures_en_retard.reduce((s, f) => s + f.montant_restant, 0);
    const lede = dashLede(prioriteItems.length, retards, montantRetard);

    // La journee : une ligne de temps, pas une liste. L'heure est dans la
    // marge de la ligne et les evenements sont relies par un filet - on lit
    // la forme de la journee avant d'en lire le contenu.
    const agenda = d.aujourdhui.evenements.length
      ? `<ol class="dash-journee">${d.aujourdhui.evenements.map((e) => `
          <li class="dash-journee-item" data-action="voir-notification" data-view="planning" role="button" tabindex="0">
            <time class="dash-journee-heure">${new Date(e.date_debut).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</time>
            <span class="dash-journee-titre">${escapeHtml(e.titre)}</span>
          </li>`).join("")}</ol>`
      : `<p class="dash-vide">Journée dégagée — aucun rendez-vous prévu.
         <button type="button" class="lien-action" data-action="show-evenement-form">Planifier quelque chose</button></p>`;

    const chantiersEnCours = chantiers.filter((c) => !["a_preparer", "termine", "facture", "paye"].includes(c.statut));

    container.innerHTML = `
      <header class="dash-entete">
        <p class="dash-date">${dateLabel}</p>
        <h2 class="dash-lede${lede.alerte ? " est-alerte" : ""}">${lede.titre}</h2>
        <p class="dash-lede-detail">${lede.detail}</p>
      </header>

      ${saSection(
        "À faire",
        prioriteItems.length
          ? dashTaskGroupsHtml(taskGroupes)
          : '<p class="dash-vide">Rien qui nécessite votre attention aujourd\'hui.</p>',
        prioriteItems.length ? `${prioriteItems.length} point${prioriteItems.length > 1 ? "s" : ""}` : "")}

      ${saSection("Aujourd'hui", agenda,
        d.aujourdhui.evenements.length ? `${d.aujourdhui.evenements.length} rendez-vous` : "")}

      ${saSection("Le mois", dashChiffresHtml(d, chantiersEnCours) + (d.finances.paiements_recents.length
        ? `<div class="dash-paiements">
             <span class="dash-paiements-titre">Derniers encaissements</span>
             ${d.finances.paiements_recents.map((p) => `
               <div class="dash-paiement"><span>${fmtDate(p.date_paiement)} · ${escapeHtml(p.moyen)}</span><strong>${fmtEuro(p.montant)}</strong></div>`).join("")}
           </div>`
        : ""),
        new Date().toLocaleDateString("fr-FR", { month: "long", year: "numeric" }))}

      ${saSection("Mise en route", activationChecklistHtml(activation))}

      ${saSection("À surveiller",
        `<div class="dash-conseils">
           <div class="dash-conseils-col">
             ${recommandations.length
               ? recommandations.map(recommandationRowHtml).join("")
               : '<p class="dash-vide">Aucune recommandation pour le moment.</p>'}
           </div>
           <div class="dash-conseils-col">${santeWidgetHtml(sante)}</div>
         </div>`)}

      ${saSection("Présence en ligne", renderPresenceSite(d.presence_site))}
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// ===================== Clients & prospects (CRM, vue Kanban) =====================
const CLIENT_PIPELINE_ORDRE = [
  "nouveau", "contacte", "qualification", "visite_prevue",
  "devis_a_faire", "devis_envoye", "negociation", "gagne", "perdu",
];

// ---------------------------------------------------------------------
// PROSPECTS — « la reglette »
// ---------------------------------------------------------------------
// La page ouvrait sur cinq cartes de KPI (total, a contacter, en
// qualification, visites, valeur) au-dessus d'un kanban de neuf colonnes.
// Cinq nombres alignes ne disent pas ou en est le commerce, et les neuf
// colonnes s'affichaient toutes, vides comprises : quatre colonnes
// « Vide » a faire defiler avant d'atteindre la suivante.
//
// A la place : UN objet, la reglette. Le pipeline est une valeur qui se
// deplace le long d'un axe ; on le montre donc comme un axe, pas comme
// des cartes. Et les colonnes vides se replient.

/** Jours ecoules depuis le dernier mouvement de la fiche. `updated_at` est
 *  deja renvoye par ClientOut : c'est la donnee qui dit qu'un prospect
 *  dort, et elle n'etait exploitee nulle part. */
function clientJoursSansMouvement(c) {
  if (!c.updated_at) return null;
  const d = new Date(c.updated_at);
  if (isNaN(d)) return null;
  return Math.floor((Date.now() - d.getTime()) / 86400000);
}
const CLIENT_SEUIL_DORMANT = 15;

function clientDort(c) {
  if (["gagne", "perdu"].includes(c.statut)) return false;
  const j = clientJoursSansMouvement(c);
  return j !== null && j >= CLIENT_SEUIL_DORMANT;
}

/** La reglette : la valeur du pipeline repartie sur les trois maturites,
 *  sur un seul axe. Un pipeline est un mouvement, pas un tableau de bord -
 *  on montre la forme de ce mouvement. */
function prospectsRegletteHtml(clients) {
  const actifs = clients.filter((c) => !["gagne", "perdu"].includes(c.statut));
  const blocs = [
    { cle: "amont", label: "Premier contact", statuts: ["nouveau", "contacte"] },
    { cle: "qualif", label: "Qualification", statuts: ["qualification", "visite_prevue"] },
    { cle: "aval", label: "Devis et négociation", statuts: ["devis_a_faire", "devis_envoye", "negociation"] },
  ].map((b) => {
    const items = actifs.filter((c) => b.statuts.includes(c.statut));
    return { ...b, nb: items.length, valeur: items.reduce((s, c) => s + (c.montant_estime || 0), 0) };
  });
  const total = blocs.reduce((s, b) => s + b.valeur, 0);
  const aContacter = actifs.filter((c) => c.statut === "nouveau").length;
  const dormants = actifs.filter(clientDort).length;

  // Les signaux : uniquement ceux qui appellent un geste. Un compteur a
  // zero n'a rien a dire, il ne s'affiche pas.
  const signaux = [];
  signaux.push(`${actifs.length} prospect${actifs.length > 1 ? "s" : ""} actif${actifs.length > 1 ? "s" : ""}`);
  if (aContacter) signaux.push(`<strong>${aContacter}</strong> à contacter`);
  if (dormants) signaux.push(`<strong class="est-dormant">${dormants}</strong> sans mouvement depuis plus de ${CLIENT_SEUIL_DORMANT} jours`);

  // Sans montant estime, la reglette affichait « — » en gros caracteres
  // suivi de « de pipeline actif » : une phrase amputee, qui se lit comme un
  // chiffre qui n'a pas su se calculer. Quand il n'y a rien a chiffrer, on
  // le dit - et on en profite pour indiquer ou saisir le montant, puisque
  // c'est precisement le geste qui manque.
  const aucunMontant = !total;
  return `
  <section class="reglette ${aucunMontant ? "est-sans-montant" : ""}">
    <div class="reglette-total">
      ${aucunMontant
        ? `<span class="reglette-total-vide">Aucun montant estimé sur vos prospects actifs.</span>
           <span class="reglette-total-label">Renseignez-le sur une fiche pour suivre la valeur du pipeline.</span>`
        : `<span class="reglette-total-valeur">${fmtEuro(total)}</span>
           <span class="reglette-total-label">de pipeline actif</span>`}
    </div>
    <div class="reglette-axe">
      ${total ? `<div class="reglette-barre">
        ${blocs.filter((b) => b.valeur).map((b) => `
          <span class="reglette-seg est-${b.cle}" style="flex:${b.valeur}"
                title="${b.label} : ${fmtEuro(b.valeur)}"></span>`).join("")}
      </div>` : ""}
      <div class="reglette-legende">
        ${blocs.map((b) => `
          <span class="reglette-item">
            <span class="reglette-puce est-${b.cle}" aria-hidden="true"></span>
            <span class="reglette-item-label">${b.label}</span>
            <span class="reglette-item-valeur">${b.valeur ? fmtEuro(b.valeur) : "—"}</span>
            <span class="reglette-item-nb">${b.nb} prospect${b.nb > 1 ? "s" : ""}</span>
          </span>`).join("")}
      </div>
    </div>
    <p class="reglette-signaux">${signaux.join(" · ")}</p>
  </section>`;
}

// Conserve : la bande de KPI d'origine n'existe plus, mais d'autres vues
// appellent encore ce nom. Il redirige vers la reglette.
function prospectsKpiBandHtml(clients) { return prospectsRegletteHtml(clients); }

function renderClientCard(c) {
  const contact = [c.telephone, c.email].filter(Boolean).map(escapeHtml).join(" · ");
  const statutOptions = Object.entries(CLIENT_STATUT_META)
    .map(([value, m]) => `<option value="${value}" ${value === c.statut ? "selected" : ""}>${m.label}</option>`)
    .join("");

  // L'ancienne carte affichait toujours Source / Valeur / Action, avec
  // « Non renseignée », « Inconnue », « Aucune action prévue » quand la
  // donnee manquait : trois lignes de rien sur la majorite des cartes. On
  // n'affiche desormais que ce qui existe - une carte muette est une
  // information en soi, elle dit « ce prospect n'a pas encore ete qualifie ».
  const lignes = [];
  if (c.montant_estime) {
    const proba = c.probabilite !== null && c.probabilite !== undefined ? ` · ${c.probabilite} %` : "";
    lignes.push(`<div class="kanban-card-valeur">${fmtEuro(c.montant_estime)}<span>${proba}</span></div>`);
  }
  if (c.prochaine_action) {
    lignes.push(`<div class="kanban-card-action"><span aria-hidden="true">→</span> ${escapeHtml(c.prochaine_action)}</div>`);
  }

  const jours = clientJoursSansMouvement(c);
  const dort = clientDort(c);

  // Une seule indication a la fois, la plus specifique en priorite. Le
  // sommeil passe avant le potentiel : c'est celle qui appelle un geste.
  let badge = null;
  if (dort) badge = { label: `${jours} j sans suite`, cls: "pill-dormant" };
  else if (c.probabilite !== null && c.probabilite !== undefined && c.probabilite >= 70) badge = { label: "Fort potentiel", cls: "pill-accent" };
  else if (c.statut === "visite_prevue") badge = { label: "Visite prévue", cls: "pill-green" };
  else if (c.statut === "nouveau") badge = { label: "À contacter", cls: "pill-accent" };

  return `
  <div class="kanban-card${dort ? " est-dormant" : ""}" data-action="voir-timeline" data-id="${c.id}">
    <div class="kanban-card-top">
      <div class="kanban-card-title">${escapeHtml(c.nom)}</div>
      ${badge ? `<span class="pill ${badge.cls}">${badge.label}</span>` : ""}
    </div>
    ${contact || c.societe ? `<div class="kanban-card-sub">${contact}${c.societe ? (contact ? " · " : "") + escapeHtml(c.societe) : ""}</div>` : ""}
    ${lignes.join("")}
    <div class="kanban-card-actions">
      <select data-action="changer-statut-client" data-id="${c.id}" aria-label="Statut de ${escapeHtml(c.nom)}">${statutOptions}</select>
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-client" data-id="${c.id}" title="Archiver" aria-label="Archiver">&times;</button>
    </div>
  </div>`;
}

async function loadClients() {
  const kpiBand = document.getElementById("prospects-kpi-band");
  const board = document.getElementById("clients-kanban");
  board.innerHTML = '<div class="kanban-squelette"><span></span><span></span><span></span></div>';
  try {
    const clients = await Api.listClients();
    clientsCache = clients;
    if (kpiBand) kpiBand.innerHTML = clients.length ? prospectsRegletteHtml(clients) : "";
    if (clients.length === 0) {
      board.innerHTML = `<div class="empty-state">
        <strong>Aucun contact pour le moment.</strong><br><br>
        Les demandes venant de votre site vitrine arrivent automatiquement ici.
        Vous pouvez aussi ajouter un contact à la main.
      </div>`;
      return;
    }
    const parColonne = {};
    CLIENT_PIPELINE_ORDRE.forEach((s) => (parColonne[s] = []));
    clients.forEach((c) => { (parColonne[c.statut] || (parColonne[c.statut] = [])).push(c); });

    board.innerHTML = CLIENT_PIPELINE_ORDRE.map((statut, i) => {
      const meta = CLIENT_STATUT_META[statut] || { label: statut };
      const items = parColonne[statut] || [];
      const valeurColonne = items.reduce((s, c) => s + (c.montant_estime || 0), 0);

      // Une etape vide se replie en rail etroit. Elle reste visible - le
      // pipeline est un enchainement, en retirer un maillon rendrait la
      // suite incomprehensible - mais elle ne coute plus 258 px de
      // defilement horizontal chacune. A neuf etapes, cela faisait
      // regulierement un ecran entier de colonnes « Vide » a traverser.
      if (!items.length) {
        return `
        <div class="kanban-column est-repliee" title="${escapeHtml(meta.label)} — aucun prospect">
          <div class="kanban-column-header">
            <span class="kanban-column-title">${meta.label}</span>
            <span class="kanban-column-zero">0</span>
          </div>
        </div>`;
      }

      return `
      <div class="kanban-column">
        <div class="kanban-column-header">
          <div>
            <span class="kanban-column-title">${meta.label}</span>
            <div class="kanban-column-meta">${items.length} prospect${items.length > 1 ? "s" : ""}${valeurColonne ? ` · ${fmtEuro(valeurColonne)}` : ""}</div>
          </div>
          ${i < CLIENT_PIPELINE_ORDRE.length - 1 ? '<span class="kanban-column-arrow" aria-hidden="true">&rarr;</span>' : ""}
        </div>
        <div class="kanban-cards">${items.map(renderClientCard).join("")}</div>
      </div>`;
    }).join("");
  } catch (err) {
    board.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}




function showClientForm() {
  const container = document.getElementById("client-form-container");
  container.innerHTML = `
    <div class="form-box">
      <h3>Nouveau contact</h3>
      <form id="client-form">
        <div class="form-grid">
          <div><label for="cli-nom">Nom *</label><input type="text" id="cli-nom" required></div>
          <div><label for="cli-telephone">Téléphone</label><input type="tel" id="cli-telephone"></div>
          <div><label for="cli-email">Email</label><input type="email" id="cli-email"></div>
          <div><label for="cli-societe">Société</label><input type="text" id="cli-societe"></div>
          <div><label for="cli-adresse">Adresse</label><input type="text" id="cli-adresse"></div>
          <div><label for="cli-ville">Ville</label><input type="text" id="cli-ville"></div>
          <div>
            <label for="cli-source">Source</label>
            <select id="cli-source">${Object.entries(CLIENT_SOURCE_LABELS).map(([v, l]) => `<option value="${v}" ${v === "manuel" ? "selected" : ""}>${l}</option>`).join("")}</select>
          </div>
          <div><label for="cli-montant-estime">Montant estimé (EUR)</label><input type="number" step="0.01" min="0" id="cli-montant-estime"></div>
          <div><label for="cli-probabilite">Probabilité (%)</label><input type="number" step="1" min="0" max="100" id="cli-probabilite"></div>
        </div>
        <label for="cli-prochaine-action" style="margin-top:14px;">Prochaine action</label>
        <input type="text" id="cli-prochaine-action" placeholder="Ex: Rappeler jeudi pour confirmer le RDV">
        <label for="cli-notes" style="margin-top:14px;">Notes</label>
        <textarea id="cli-notes" placeholder="Contexte, besoin exprimé..."></textarea>
        <p class="field-error" id="client-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
          <button type="button" class="btn-sm" data-action="cancel-client-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("client-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("client-form-error");
    errorBox.hidden = true;
    try {
      await Api.createClient({
        nom: document.getElementById("cli-nom").value,
        telephone: emptyToNull(document.getElementById("cli-telephone").value),
        email: emptyToNull(document.getElementById("cli-email").value),
        societe: emptyToNull(document.getElementById("cli-societe").value),
        adresse: emptyToNull(document.getElementById("cli-adresse").value),
        ville: emptyToNull(document.getElementById("cli-ville").value),
        source: document.getElementById("cli-source").value,
        montant_estime: document.getElementById("cli-montant-estime").value ? parseFloat(document.getElementById("cli-montant-estime").value) : null,
        probabilite: document.getElementById("cli-probabilite").value ? parseInt(document.getElementById("cli-probabilite").value, 10) : null,
        prochaine_action: emptyToNull(document.getElementById("cli-prochaine-action").value),
        notes: emptyToNull(document.getElementById("cli-notes").value),
      });
      showToast("Contact ajouté.");
      container.hidden = true;
      container.innerHTML = "";
      loadClients();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

// ---------------------------------------------------------------------
// FICHE CLIENT — « le dossier »
// ---------------------------------------------------------------------
// L'ancienne fiche tenait dans un panneau de 460 px et se composait de
// cinq lignes libelle/valeur, d'un historique, puis d'une liste de
// messages. Elle ne montrait ni les chantiers, ni les devis, ni les
// factures du client : pour savoir ou en etait la relation, il fallait
// ouvrir trois autres pages et recoller soi-meme.
//
// Trois decisions :
//   - les chiffres passent en tete, typographies comme sur l'accueil ;
//   - un bloc « Affaires » reunit chantiers, devis et factures - les
//     memes listes que la page Clients recupere deja ;
//   - l'historique et les messages fusionnent en UNE chronologie. Ce
//     sont deux facons de raconter la meme chose : ce qui s'est passe
//     avec ce client, dans l'ordre.

/** Les chiffres du client : quatre reperes typographies, filet dessous,
 *  comme le total souligne d'un devis. Remplace cinq lignes
 *  libelle/valeur qui se lisaient comme un formulaire en lecture seule. */
function clientResumeHtml(r) {
  const jours = r.dernier_contact
    ? Math.floor((Date.now() - new Date(r.dernier_contact).getTime()) / 86400000)
    : null;
  const chiffre = (label, valeur, note, classe = "") => `
    <div class="fiche-chiffre ${classe}">
      <span class="fiche-chiffre-label">${label}</span>
      <span class="fiche-chiffre-valeur">${valeur}</span>
      <span class="fiche-chiffre-note">${note}</span>
    </div>`;
  return `
  <div class="fiche-chiffres">
    ${chiffre("Facturé", fmtEuro(r.valeur_totale), "depuis le début")}
    ${chiffre("Impayé", r.impayes ? fmtEuro(r.impayes) : "—",
      r.impayes ? "à recouvrer" : "rien en attente", r.impayes > 0 ? "est-du" : "")}
    ${chiffre("Chantiers", String(r.nb_chantiers ?? 0), r.nb_chantiers ? "au total" : "aucun à ce jour")}
    ${chiffre("Dernier contact", jours === null ? "—" : (jours === 0 ? "aujourd'hui" : `${jours} j`),
      r.date_dernier_devis ? `dernier devis ${fmtDate(r.date_dernier_devis)}` : "aucun devis")}
  </div>`;
}

/** Les affaires du client : chantiers, devis, factures. Rien de tout cela
 *  n'etait visible depuis la fiche. Les listes sont celles que la page
 *  Clients charge deja - on les reutilise quand elles sont en cache, on
 *  les demande sinon, avec le meme repli silencieux qu'ailleurs. */
function clientAffairesHtml(clientId, chantiers, devis, factures) {
  const sesChantiers = chantiers.filter((c) => c.client_id === clientId);
  const sesDevis = devis.filter((d) => d.client_id === clientId);
  const sesFactures = factures.filter((f) => f.client_id === clientId);
  if (!sesChantiers.length && !sesDevis.length && !sesFactures.length) {
    return `<p class="fiche-vide">Aucune affaire pour ce client. Le prochain devis créera son premier dossier.</p>`;
  }

  const ligne = (attrs, titre, meta, montant, alerte = false) => `
    <div class="fiche-affaire" ${attrs}>
      <span class="fiche-affaire-titre">${titre}</span>
      <span class="fiche-affaire-meta">${meta}</span>
      <span class="fiche-affaire-montant${alerte ? " est-alerte" : ""}">${montant}</span>
    </div>`;

  const bloc = (titre, n, contenu) => n
    ? `<div class="fiche-affaire-groupe">
         <h5 class="fiche-affaire-groupe-titre">${titre} <span>${n}</span></h5>
         ${contenu}
       </div>`
    : "";

  return `
    ${bloc("Chantiers", sesChantiers.length, sesChantiers.map((c) => {
      const meta = CHANTIER_STATUT_META[c.statut] || { label: c.statut };
      const progression = Number(c.progression) || 0;
      return ligne(`data-action="ouvrir-chantier-depuis-client" data-id="${c.id}" role="button" tabindex="0"`,
        escapeHtml(c.titre), escapeHtml(meta.label),
        ["termine", "facture", "paye"].includes(c.statut) ? "" : `${progression} %`);
    }).join(""))}

    ${bloc("Devis", sesDevis.length, sesDevis.map((d) => {
      const meta = DEVIS_STATUT_META[d.statut] || { label: d.statut };
      return ligne(`data-action="ouvrir-devis-depuis-client" data-id="${d.id}" role="button" tabindex="0"`,
        escapeHtml(d.numero || `Devis #${d.id}`), escapeHtml(meta.label), fmtEuroOuRien(d.montant_ttc));
    }).join(""))}

    ${bloc("Factures", sesFactures.length, sesFactures.map((f) => {
      const meta = FACTURE_STATUT_META[f.statut] || { label: f.statut };
      const impaye = (f.montant_restant || 0) > 0 && f.statut !== "payee";
      return ligne(`data-action="ouvrir-facture-depuis-client" data-id="${f.id}" role="button" tabindex="0"`,
        escapeHtml(f.numero || `Facture #${f.id}`), escapeHtml(meta.label),
        impaye ? fmtEuro(f.montant_restant) : fmtEuroOuRien(f.montant_ttc), impaye);
    }).join(""))}`;
}

/** L'historique et les messages fusionnes en une seule chronologie.
 *  C'etaient deux listes de meme forme, l'une sous l'autre, qui
 *  racontaient la meme chose - ce qui s'est passe avec ce client - dans
 *  deux ordres separes. On les trie ensemble, du plus recent au plus
 *  ancien, et un message se distingue par son filet et non par sa place. */
function clientChronologieHtml(entries, messages) {
  const items = [
    ...entries.map((e) => ({ date: e.date, type: "evenement", label: e.label })),
    ...messages.map((m) => ({
      date: m.created_at, type: "message",
      expediteur: m.expediteur === "client" ? "Client" : "Vous",
      label: m.texte,
    })),
  ].filter((i) => i.date).sort((a, b) => new Date(b.date) - new Date(a.date));

  if (!items.length) {
    return `<p class="fiche-vide">Rien ne s'est encore passé avec ce client. Les devis, factures et messages viendront se ranger ici.</p>`;
  }
  return `<div class="fiche-chrono">${items.map((i) => `
    <div class="fiche-chrono-item${i.type === "message" ? " est-message" : ""}">
      <time class="fiche-chrono-date">${fmtDateTime(i.date)}</time>
      <div class="fiche-chrono-corps">
        ${i.type === "message" ? `<span class="fiche-chrono-qui">${i.expediteur}</span>` : ""}
        <span class="fiche-chrono-label">${escapeHtml(i.label)}</span>
      </div>
    </div>`).join("")}</div>`;
}

function messagesPanelHtml() {
  return `
  <form id="client-message-form" class="fiche-reponse">
    <label for="client-message-texte">Écrire au client</label>
    <textarea id="client-message-texte" placeholder="Votre message apparaîtra dans son espace client." required></textarea>
    <p class="field-error" id="client-message-error" hidden></p>
    <div class="form-actions"><button type="submit" class="btn-sm btn-sm-primary">Envoyer</button></div>
  </form>`;
}

function clientQuickActionsHtml(client) {
  const actions = [];
  if (client.telephone) actions.push(`<a class="btn-sm" href="tel:${escapeHtml(client.telephone)}">Appeler</a>`);
  if (client.email) actions.push(`<a class="btn-sm" href="mailto:${escapeHtml(client.email)}">Email</a>`);
  actions.push(`<button type="button" class="btn-sm" data-action="demander-avis" data-client-id="${client.id}">Demander un avis</button>`);
  actions.push(`<button type="button" class="btn-sm" data-action="copier-lien-portail" data-client-id="${client.id}">Copier le lien de l'espace client</button>`);
  return `<div class="fiche-actions">
    <button type="button" class="btn-primary" data-action="quick-devis" data-client-id="${client.id}">+ Nouveau devis</button>
    ${actions.join("")}
  </div>`;
}

// L'en-tete d'identite : monogramme, nom, societe, statut, coordonnees
// cliquables. Les actions vivent desormais dans clientQuickActionsHtml,
// juste en dessous, action primaire en tete.
function clientDetailHeaderHtml(client) {
  const initiales = (client.nom || "?").trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const statutMeta = CLIENT_STATUT_META[client.statut] || { label: client.statut };
  const coords = [
    client.telephone ? `<a href="tel:${escapeHtml(client.telephone)}">${escapeHtml(client.telephone)}</a>` : null,
    client.email ? `<a href="mailto:${escapeHtml(client.email)}">${escapeHtml(client.email)}</a>` : null,
    client.ville || null,
  ].filter(Boolean);
  return `
  <header class="fiche-entete">
    <div class="crm-avatar fiche-avatar" aria-hidden="true">${escapeHtml(initiales)}</div>
    <div class="fiche-identite">
      <h4 class="fiche-nom">${escapeHtml(client.nom)}</h4>
      <p class="fiche-sous">
        ${client.societe ? escapeHtml(client.societe) + " · " : ""}<span class="badge badge-gray">${escapeHtml(statutMeta.label)}</span>
      </p>
      ${coords.length ? `<p class="fiche-coords">${coords.join(" · ")}</p>` : ""}
    </div>
  </header>`;
}

/** Une section du dossier : intitule dans la marge, contenu a droite.
 *  Meme grammaire que les pages composees, a l'echelle du panneau. */
function ficheSection(titre, corps) {
  if (!corps) return "";
  return `
  <section class="fiche-section">
    <h5 class="fiche-section-titre">${titre}</h5>
    <div class="fiche-section-corps">${corps}</div>
  </section>`;
}

async function showTimeline(clientId) {
  const client = clientsCache.find((c) => c.id === clientId) || (await Api.listClients()).find((c) => c.id === clientId);
  document.getElementById("timeline-titre").textContent = "Dossier client";
  const content = document.getElementById("timeline-content");
  content.innerHTML = '<div class="fiche-squelette"><span></span><span></span><span></span></div>';
  document.getElementById("panel-timeline").hidden = false;
  document.getElementById("panel-timeline").dataset.clientId = clientId;

  try {
    // Les trois listes d'affaires sont deja en cache quand on arrive depuis
    // la page Clients ; sinon on les demande, avec le meme repli silencieux
    // qu'ailleurs si le plan ne les autorise pas.
    const cache = clientsDirectoryCache;
    const [entries, resume, messages, chantiers, devis, factures] = await Promise.all([
      Api.clientTimeline(clientId),
      Api.clientResume(clientId),
      Api.listClientMessages(clientId).catch(() => []),
      cache.chantiers?.length ? cache.chantiers : Api.listChantiers().catch(() => []),
      cache.devis?.length ? cache.devis : Api.listDevis().catch(() => []),
      cache.factures?.length ? cache.factures : Api.listFactures().catch(() => []),
    ]);

    content.innerHTML = `
      ${client ? clientDetailHeaderHtml(client) : ""}
      ${client ? clientQuickActionsHtml(client) : ""}
      ${clientResumeHtml(resume)}
      ${ficheSection("Affaires", clientAffairesHtml(clientId, chantiers, devis, factures))}
      ${ficheSection("Chronologie", clientChronologieHtml(entries, messages) + messagesPanelHtml())}
    `;
    refreshBadges();

    document.getElementById("client-message-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("client-message-error");
      errorBox.hidden = true;
      const texte = document.getElementById("client-message-texte").value.trim();
      if (!texte) return;
      try {
        await Api.envoyerClientMessage(clientId, { texte });
        showTimeline(clientId);
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  } catch (err) {
    content.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function setupClientsView() {
  document.querySelector('[data-action="show-client-form"]').addEventListener("click", showClientForm);
  document.getElementById("client-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-client-form"]')) {
      const container = document.getElementById("client-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("clients-kanban").addEventListener("change", async (e) => {
    const select = e.target.closest('[data-action="changer-statut-client"]');
    if (!select) return;
    const id = parseInt(select.dataset.id, 10);
    await withErrorToast(async () => {
      await Api.updateClient(id, { statut: select.value });
      showToast("Statut mis à jour.");
      loadClients();
    });
  });

  document.getElementById("clients-kanban").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "delete-client") {
      if (!(await confirmDialog("Archiver ce contact ? Il disparaitra de vos listes actives. Ses devis, factures et chantiers restent intacts et consultables.", { confirmLabel: "Archiver", danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteClient(id);
        showToast("Contact archive.");
        loadClients();
      });
    } else if (btn.dataset.action === "voir-timeline") {
      showTimeline(id);
    }
  });

  document.getElementById("panel-timeline").addEventListener("click", async (e) => {
    if (e.target.closest('[data-action="close-timeline"]') || e.target.id === "panel-timeline") {
      document.getElementById("panel-timeline").hidden = true;
      return;
    }
    const devisBtn = e.target.closest('[data-action="quick-devis"]');
    if (devisBtn) {
      const clientId = parseInt(devisBtn.dataset.clientId, 10);
      document.getElementById("panel-timeline").hidden = true;
      switchView("devis");
      setTimeout(() => showDevisForm(null, clientId), 200);
    }

    // Le bloc « Affaires » du dossier renvoie vers la piece concernee.
    // C'est tout l'interet de l'avoir ajoute : depuis la fiche, on atteint
    // le chantier, le devis ou la facture en un clic, au lieu d'ouvrir la
    // page correspondante et d'y rechercher la ligne a la main.
    const affaire = e.target.closest('[data-action^="ouvrir-"][data-action$="-depuis-client"]');
    if (affaire) {
      const id = parseInt(affaire.dataset.id, 10);
      document.getElementById("panel-timeline").hidden = true;
      if (affaire.dataset.action === "ouvrir-chantier-depuis-client") ouvrirChantierDepuisPlanning(id);
      else if (affaire.dataset.action === "ouvrir-devis-depuis-client") switchView("devis");
      else switchView("factures");
      return;
    }

    const avisBtn = e.target.closest('[data-action="demander-avis"]');
    if (avisBtn) await demanderAvisEtCopierLien(parseInt(avisBtn.dataset.clientId, 10));

    const portailBtn = e.target.closest('[data-action="copier-lien-portail"]');
    if (portailBtn) {
      const clientId = parseInt(portailBtn.dataset.clientId, 10);
      await withErrorToast(async () => {
        const { token_portail } = await Api.genererLienPortail(clientId);
        const url = `${window.location.origin}/portail-client.html?t=${token_portail}`;
        try {
          await navigator.clipboard.writeText(url);
          showToast("Lien copié. Ce lien remplace l'ancien (si un lien avait déjà été envoyé, il ne fonctionne plus).");
        } catch (err) {
          showToast(url, false);
        }
      });
    }
  });

  document.getElementById("clients-directory").addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="voir-timeline"]');
    if (btn) showTimeline(parseInt(btn.dataset.id, 10));
  });

  document.getElementById("btn-new-client")?.addEventListener("click", () => {
    switchView("prospects");
    showClientForm();
  });
  ["clients-statut-filtre", "clients-projet-filtre", "clients-tri"].forEach((id) => {
    document.getElementById(id)?.addEventListener("change", () => {
      currentClientsPage = 1;
      renderClientsDirectoryPage();
    });
  });
  document.getElementById("clients-pagination")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-clients-page]");
    if (!btn) return;
    currentClientsPage = parseInt(btn.dataset.clientsPage, 10) || 1;
    renderClientsDirectoryPage();
  });
}

// ===================== Archives (clients/devis/factures/chantiers/documents) =====================
// Rien n'est jamais supprime definitivement (V5 section 3-4) : ce panneau
// generique liste les elements archives d'un type donne et permet de les
// restaurer, quelle que soit la vue depuis laquelle on l'ouvre.
const ARCHIVE_ENTITES = {
  client: {
    titre: "Clients archivés",
    lister: () => Api.listClients(null, true),
    restaurer: (id) => Api.restaurerClient(id),
    ligne: (c) => `${escapeHtml(c.nom)}${c.societe ? " · " + escapeHtml(c.societe) : ""}`,
    recharger: () => { loadClients(); loadClientsDirectory(); },
  },
  devis: {
    titre: "Devis archivés",
    lister: () => Api.listDevis(null, true),
    restaurer: (id) => Api.restaurerDevis(id),
    ligne: (d) => `${escapeHtml(d.numero || "Devis #" + d.id)} · ${escapeHtml(d.client_nom || "")} · ${fmtEuro(d.montant_ttc)}`,
    recharger: () => loadDevis(),
  },
  facture: {
    titre: "Factures archivées",
    lister: () => Api.listFactures(null, true),
    restaurer: (id) => Api.restaurerFacture(id),
    ligne: (f) => `${escapeHtml(f.numero || "Facture #" + f.id)} · ${escapeHtml(f.client_nom || "")} · ${fmtEuro(f.montant_ttc)}`,
    recharger: () => loadFactures(),
  },
  chantier: {
    titre: "Chantiers archivés",
    lister: () => Api.listChantiers(true),
    restaurer: (id) => Api.restaurerChantier(id),
    ligne: (c) => `${escapeHtml(c.titre)}${c.client_nom ? " · " + escapeHtml(c.client_nom) : ""}`,
    recharger: () => loadChantiers(),
  },
  document: {
    titre: "Documents archivés",
    lister: () => Api.listDocuments({ archive: true }),
    restaurer: (id) => Api.restaurerDocument(id),
    ligne: (d) => `${escapeHtml(d.nom)}${d.type ? " · " + escapeHtml(d.type) : ""}`,
    recharger: () => loadDocuments(),
  },
};

async function openArchivesPanel(entite) {
  const config = ARCHIVE_ENTITES[entite];
  if (!config) return;
  const panel = document.getElementById("panel-archives");
  const content = document.getElementById("archives-content");
  document.getElementById("archives-titre").textContent = config.titre;
  panel.dataset.entite = entite;
  panel.hidden = false;
  content.innerHTML = skeletonCards();
  try {
    const items = await config.lister();
    content.innerHTML = items.length
      ? items.map((item) => `
        <div class="item-card">
          <div class="item-card-top">
            <div class="item-title">${config.ligne(item)}</div>
          </div>
          <div class="item-actions">
            <button type="button" class="btn-sm btn-sm-primary" data-action="restaurer-archive" data-id="${item.id}">Restaurer</button>
          </div>
        </div>`).join("")
      : `<div class="empty-state">Aucun élément archivé.</div>`;
  } catch (err) {
    content.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function setupArchivesPanel() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="voir-archives"]');
    if (btn) openArchivesPanel(btn.dataset.entite);
  });

  document.getElementById("panel-archives").addEventListener("click", async (e) => {
    if (e.target.closest('[data-action="close-archives"]') || e.target.id === "panel-archives") {
      document.getElementById("panel-archives").hidden = true;
      return;
    }
    const restoreBtn = e.target.closest('[data-action="restaurer-archive"]');
    if (restoreBtn) {
      const panel = document.getElementById("panel-archives");
      const entite = panel.dataset.entite;
      const config = ARCHIVE_ENTITES[entite];
      const id = parseInt(restoreBtn.dataset.id, 10);
      await withErrorToast(async () => {
        await config.restaurer(id);
        showToast("Element restaure.");
        config.recharger();
        openArchivesPanel(entite);
      });
    }
  });
}

window.openArchivesPanel = openArchivesPanel;

// ===================== Clients (annuaire des affaires gagnees) =====================
// Monogramme derive du vrai nom du client (premiere lettre des deux premiers
// mots, ou les deux premieres lettres s'il n'y a qu'un seul mot) - jamais de
// donnee inventee, juste une initiale visuelle pour scanner la liste plus
// vite qu'une colonne de texte seule.
function monogram(nom) {
  const mots = String(nom || "").trim().split(/\s+/).filter(Boolean);
  if (mots.length === 0) return "?";
  if (mots.length === 1) return mots[0].slice(0, 2).toUpperCase();
  return (mots[0][0] + mots[1][0]).toUpperCase();
}

// Bande de KPI de l'annuaire Clients : chantiers recupere en parallele
// (avec repli silencieux sur [] si le plan ne l'autorise pas, comme
// ailleurs dans le fichier) uniquement pour le rattacher aux clients
// gagnes par client_id - aucune nouvelle donnee, aucun nouvel endpoint.
// ---------------------------------------------------------------------
// CLIENTS — « le repertoire »
// ---------------------------------------------------------------------
// Ce n'est pas un CRM, c'est un annuaire : on y vient pour retrouver
// quelqu'un. La composition suit donc celle d'un repertoire - trie par
// nom, avec l'initiale dans la marge des que la lettre change. C'est ce
// geste, et pas une table de plus, qui rend la page reconnaissable.
//
// Trois defauts corriges au passage, tous les trois lourds a l'usage :
//   - la page affichait QUATRE clients a la fois. Un annuaire feuillete
//     quatre par quatre n'est pas un annuaire.
//   - la recherche passait par le masquage generique, qui compare le
//     textContent des lignes DEJA AFFICHEES : elle ne cherchait donc que
//     dans la page courante de quatre, et paraissait ne rien trouver.
//   - une bande de quatre KPI ouvrait la page, comme partout ailleurs.

/** La synthese : une ligne, pas quatre cartes. Elle situe l'annuaire
 *  (combien, combien d'actifs, combien encaisse) sans occuper un ecran. */
function clientsSyntheseHtml(clients, chantiers, factures) {
  const ids = new Set(clients.map((c) => c.id));
  const leurs = chantiers.filter((c) => ids.has(c.client_id));
  const actifs = new Set(leurs.filter((c) => !["termine", "facture", "paye"].includes(c.statut)).map((c) => c.client_id));
  const sansChantier = clients.length - new Set(leurs.map((c) => c.client_id)).size;
  const encaisse = factures.filter((f) => ids.has(f.client_id)).reduce((s, f) => s + (f.montant_paye || 0), 0);

  const parts = [`<strong>${clients.length}</strong> client${clients.length > 1 ? "s" : ""}`];
  if (actifs.size) parts.push(`<strong>${actifs.size}</strong> avec un chantier en cours`);
  if (sansChantier) parts.push(`<strong>${sansChantier}</strong> sans aucun chantier`);
  if (encaisse) parts.push(`<strong>${fmtEuro(encaisse)}</strong> encaissés`);

  return `<p class="clients-synthese">${parts.join(" · ")}</p>`;
}

// Conserve : d'autres appels portent encore ce nom.
function clientsKpiBandHtml(clients, chantiers) {
  return clientsSyntheseHtml(clients, chantiers, clientsDirectoryCache.factures || []);
}

// Un annuaire se feuillette entierement. La pagination ne reapparait qu'au
// dela d'un seuil ou le defilement deviendrait vraiment couteux ; en
// dessous, tout tient sur une page qu'on parcourt a la molette.
const CLIENTS_PAGE_SIZE = 60;
let clientsDirectoryCache = { clients: [], chantiers: [], factures: [], devis: [] };
let currentClientsPage = 1;
let clientsRecherche = "";

/** La recherche porte sur ce que l'utilisateur connait de son client :
 *  son nom, sa societe, ses coordonnees, sa ville. Pas sur le textContent
 *  de la ligne, qui contenait aussi « Derniere activite » ou « CA genere ». */
function clientMatchesRecherche(c, q) {
  if (!q) return true;
  return [c.nom, c.societe, c.email, c.telephone, c.ville]
    .filter(Boolean).join(" ").toLowerCase().includes(q);
}

function filteredClientsDirectory() {
  const { clients, chantiers, factures } = clientsDirectoryCache;
  const statut = document.getElementById("clients-statut-filtre")?.value || "";
  const projet = document.getElementById("clients-projet-filtre")?.value || "";
  const tri = document.getElementById("clients-tri")?.value || "nom";
  const q = clientsRecherche.trim().toLowerCase();
  const clientChantiers = (id) => chantiers.filter((ch) => ch.client_id === id);
  const estTermine = (ch) => ["termine", "facture", "paye"].includes(ch.statut);

  const resultat = clients.filter((client) => {
    const projets = clientChantiers(client.id);
    const aProjetActif = projets.some((ch) => !estTermine(ch));
    if (statut === "actif" && !aProjetActif) return false;
    if (statut === "inactif" && aProjetActif) return false;
    if (projet === "en_cours" && !aProjetActif) return false;
    if (projet === "termine" && !projets.some(estTermine)) return false;
    if (projet === "sans" && projets.length) return false;
    return clientMatchesRecherche(client, q);
  });

  if (tri === "recent") resultat.sort((a, b) => (b.id || 0) - (a.id || 0));
  else if (tri === "ca") resultat.sort((a, b) => {
    const ca = (id) => factures.filter((f) => f.client_id === id).reduce((s, f) => s + (f.montant_paye || 0), 0);
    return ca(b.id) - ca(a.id);
  });
  else resultat.sort((a, b) => a.nom.localeCompare(b.nom, "fr")); // nom, par defaut
  return resultat;
}

/** L'initiale d'un nom, pour le decoupage du repertoire. On enleve les
 *  accents : Élie et Elie doivent se ranger sous la meme lettre. */
function clientInitiale(nom) {
  const c = (nom || "?").trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").charAt(0).toUpperCase();
  return /[A-Z]/.test(c) ? c : "#";
}

function renderClientsDirectoryPage() {
  const container = document.getElementById("clients-directory");
  const pagination = document.getElementById("clients-pagination");
  const { chantiers, factures, devis } = clientsDirectoryCache;
  const clients = filteredClientsDirectory();
  const tri = document.getElementById("clients-tri")?.value || "nom";

  if (!clients.length) {
    const q = clientsRecherche.trim();
    container.innerHTML = `<div class="empty-state">${q
      ? `Aucun client ne correspond à « ${escapeHtml(q)} ».`
      : "Aucun client ne correspond à ces filtres."}</div>`;
    pagination.innerHTML = "";
    return;
  }

  const pageCount = Math.max(1, Math.ceil(clients.length / CLIENTS_PAGE_SIZE));
  currentClientsPage = Math.min(Math.max(1, currentClientsPage), pageCount);
  const debut = (currentClientsPage - 1) * CLIENTS_PAGE_SIZE;
  const page = clients.slice(debut, debut + CLIENTS_PAGE_SIZE);

  // Le decoupage par initiale n'a de sens que sur un tri alphabetique.
  // Trie par CA ou par recence, il decouperait au hasard.
  let lettre = null;
  container.innerHTML = page.map((c) => {
    let entete = "";
    if (tri === "nom") {
      const l = clientInitiale(c.nom);
      if (l !== lettre) { lettre = l; entete = `<div class="repertoire-lettre" aria-hidden="true">${l}</div>`; }
    }
    return entete + renderClientDirectoryRow(c, chantiers, factures, devis);
  }).join("");

  pagination.innerHTML = clients.length > CLIENTS_PAGE_SIZE
    ? `<button type="button" class="btn-icon-sm" data-clients-page="1" aria-label="Première page">«</button>
       <button type="button" class="btn-icon-sm" data-clients-page="${Math.max(1, currentClientsPage - 1)}" aria-label="Page précédente">‹</button>
       <span>Page ${currentClientsPage} sur ${pageCount}</span>
       <button type="button" class="btn-icon-sm" data-clients-page="${Math.min(pageCount, currentClientsPage + 1)}" aria-label="Page suivante">›</button>
       <button type="button" class="btn-icon-sm" data-clients-page="${pageCount}" aria-label="Dernière page">»</button>`
    : "";
}

async function loadClientsDirectory() {
  const container = document.getElementById("clients-directory");
  const synthese = document.getElementById("clients-kpi-band");
  container.innerHTML = '<div class="repertoire-squelette"><span></span><span></span><span></span><span></span><span></span></div>';
  try {
    const [clients, chantiers, factures, devis] = await Promise.all([
      Api.listClients("gagne"),
      Api.listChantiers().catch(() => []),
      Api.listFactures().catch(() => []),
      Api.listDevis().catch(() => []),
    ]);
    clientsDirectoryCache = { clients, chantiers, factures, devis };
    if (clients.length === 0) {
      synthese.innerHTML = "";
      container.innerHTML = `<div class="empty-state">
        <strong>Aucun client pour le moment.</strong><br><br>
        Un prospect devient client automatiquement quand il passe au statut « Gagné » dans le pipeline.
      </div>`;
      return;
    }
    synthese.innerHTML = clientsSyntheseHtml(clients, chantiers, factures);
    currentClientsPage = 1;
    renderClientsDirectoryPage();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// La ligne du repertoire. L'ancienne portait un bouton « Voir le client »
// alors que la ligne entiere etait deja cliquable : deux cibles pour le
// meme geste, et 150 px de largeur perdus. Le CA passe en Fraunces a
// droite, aligne d'une ligne a l'autre - c'est le chiffre qu'on parcourt
// verticalement quand on cherche son meilleur client.
function renderClientDirectoryRow(c, chantiers, factures, devis) {
  const contact = [c.email, c.telephone].filter(Boolean).join(" · ");
  const chantiersClient = chantiers.filter((ch) => ch.client_id === c.id);
  const enCours = chantiersClient.filter((ch) => !["termine", "facture", "paye"].includes(ch.statut)).length;
  const termines = chantiersClient.filter((ch) => ["termine", "facture", "paye"].includes(ch.statut)).length;
  const chantiersTxt = chantiersClient.length
    ? [enCours ? `${enCours} en cours` : null, termines ? `${termines} terminé${termines > 1 ? "s" : ""}` : null].filter(Boolean).join(" · ")
    : "—";
  const caGenere = factures.filter((f) => f.client_id === c.id).reduce((s, f) => s + (f.montant_paye || 0), 0);
  const activite = dernierActiviteClient(c.id, devis, factures);

  return `
  <div class="crm-row" data-action="voir-timeline" data-id="${c.id}" role="button" tabindex="0"
       aria-label="Ouvrir la fiche de ${escapeHtml(c.nom)}">
    <div class="crm-avatar" aria-hidden="true">${escapeHtml(monogram(c.nom))}</div>
    <div class="crm-main">
      <div class="crm-name">${escapeHtml(c.nom)}${c.societe ? `<span class="crm-societe">${escapeHtml(c.societe)}</span>` : ""}</div>
      <div class="crm-contact">${escapeHtml(contact || "Pas de coordonnées")}</div>
    </div>
    <div class="crm-stat">
      <div class="crm-stat-label">Dernière activité</div>
      <div class="crm-stat-value">${activite ? `${escapeHtml(activite.label)} · ${escapeHtml(activite.date)}` : "—"}</div>
    </div>
    <div class="crm-stat">
      <div class="crm-stat-label">Chantiers</div>
      <div class="crm-stat-value">${escapeHtml(chantiersTxt)}</div>
    </div>
    <div class="crm-ca">
      <div class="crm-stat-label">Encaissé</div>
      <div class="crm-ca-valeur">${caGenere > 0 ? fmtEuro(caGenere) : "—"}</div>
    </div>
  </div>`;
}

// "Derniere activite" : le plus recent des evenements commerciaux DEJA
// dates que l'on connait pour ce client (devis envoye/signe, facture
// envoyee/payee) - aucune donnee inventee ni nouvel endpoint ; juste le
// max() des dates deja presentes sur les devis/factures de ce client parmi
// les listes recues ci-dessus. Rien si le client n'a encore aucun de ces
// evenements (ex. gagne hier, aucun devis/facture cree depuis).
function dernierActiviteClient(clientId, devisListe, facturesListe) {
  const candidats = [];
  devisListe.filter((d) => d.client_id === clientId).forEach((d) => {
    if (d.date_signature) candidats.push({ date: d.date_signature, label: "Devis accepté" });
    else if (d.date_envoi) candidats.push({ date: d.date_envoi, label: "Devis envoyé" });
  });
  facturesListe.filter((f) => f.client_id === clientId).forEach((f) => {
    if (f.statut === "payee" && f.date_envoi) candidats.push({ date: f.date_envoi, label: "Facture payée" });
    else if (f.date_envoi) candidats.push({ date: f.date_envoi, label: "Facture envoyée" });
  });
  if (!candidats.length) return null;
  candidats.sort((a, b) => new Date(b.date) - new Date(a.date));
  return { label: candidats[0].label, date: fmtDateCourte(candidats[0].date) };
}

// ---------------------------------------------------------------------
// DEVIS & RELANCES — « le suivi »
// ---------------------------------------------------------------------
// La page ouvrait sur CINQ cartes de KPI. Elle ne repond pourtant qu'a une
// question : lequel dois-je relancer, et depuis combien de temps
// attend-il ? Le chiffre qui compte passe donc en tete, en toutes lettres,
// et les quatre autres redeviennent une ligne de contexte.
//
// LE POINT IMPORTANT : `date_consultation` est renvoye par DevisOut depuis
// toujours et n'etait affiche NULLE PART. C'est pourtant le fait le plus
// decisif pour decider d'une relance - un devis lu avant-hier et reste
// sans reponse n'appelle pas le meme geste qu'un devis jamais ouvert
// depuis douze jours. Il devient la colonne « Suivi ».

/** Jours ecoules depuis une date ISO, ou null. */
function joursDepuis(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d)) return null;
  return Math.floor((Date.now() - d.getTime()) / 86400000);
}
function ilYA(j) {
  if (j === null) return "";
  if (j === 0) return "aujourd'hui";
  if (j === 1) return "hier";
  return `il y a ${j} j`;
}

/** L'etat de lecture d'un devis. Trois situations distinctes que
 *  l'interface confondait toutes en « En attente de réponse » :
 *  jamais envoye, envoye mais jamais ouvert, ouvert sans reponse. */
function devisSuivi(d, isDue) {
  if (isDue) return { texte: "Relance due aujourd'hui", cls: "is-accent" };
  if (d.statut === "signe") return { texte: `Accepté${d.date_signature ? " · " + fmtDateCourte(d.date_signature) : ""}`, cls: "is-success" };
  if (d.statut === "perdu") return { texte: "Perdu", cls: "is-muted" };
  if (d.statut === "nouveau") return { texte: d.montant_ht !== null ? "Prêt à envoyer" : "À chiffrer", cls: "is-muted" };

  const relances = d.nb_relances > 0 ? ` · ${d.nb_relances} relance${d.nb_relances > 1 ? "s" : ""}` : "";
  const jLu = joursDepuis(d.date_consultation);
  if (jLu !== null) return { texte: `Lu ${ilYA(jLu)}${relances}`, cls: "is-success" };

  const jEnvoi = joursDepuis(d.date_envoi);
  if (jEnvoi === null) return { texte: `En attente de réponse${relances}`, cls: "is-muted" };
  // Jamais ouvert : au-dela d'une semaine, ce n'est plus de l'attente,
  // c'est un devis qui n'est probablement jamais arrive.
  return {
    texte: `Jamais ouvert · envoyé ${ilYA(jEnvoi)}${relances}`,
    cls: jEnvoi >= 7 ? "is-alerte" : "is-muted",
  };
}

/** Le suivi en tete de page. Le chiffre qui appelle un geste est ecrit en
 *  toutes lettres ; les quatre autres KPI deviennent une ligne de
 *  contexte. Meme grammaire que la phrase d'ouverture de l'accueil,
 *  appliquee a une autre question - c'est ce que veut dire « meme
 *  identite, page differente ». */
function devisKpiBandHtml(tousDevis, nbARelancer) {
  const enCours = tousDevis.filter((d) => !["signe", "perdu", "expire"].includes(d.statut));
  const aChiffrer = tousDevis.filter((d) => d.statut === "nouveau" && d.montant_ht === null).length;
  const pretsAEnvoyer = tousDevis.filter((d) => d.statut === "nouveau" && d.montant_ht !== null).length;
  const valeurEnJeu = enCours.reduce((s, d) => s + (d.montant_ttc || 0), 0);
  const signes = tousDevis.filter((d) => d.statut === "signe").length;
  const perdus = tousDevis.filter((d) => d.statut === "perdu").length;
  const taux = signes + perdus > 0 ? Math.round((signes / (signes + perdus)) * 100) : null;

  // Les devis jamais ouverts depuis plus d'une semaine : un signal que
  // l'interface ne donnait pas, et qui vaut souvent mieux qu'une relance
  // de plus (le devis n'est peut-etre jamais arrive).
  const jamaisOuverts = enCours.filter((d) =>
    d.date_envoi && !d.date_consultation && (joursDepuis(d.date_envoi) ?? 0) >= 7).length;

  const montantDus = tousDevis
    .filter((d) => devisDueIds.has(d.id))
    .reduce((s, d) => s + (d.montant_ttc || 0), 0);

  // Compte sans un seul devis : cette lede n'a rien a dire, et « Rien a
  // relancer aujourd'hui » au-dessus de « Vos devis vivront ici » empile
  // deux titres dont le premier commente une activite qui n'a pas commence.
  // L'etat vide de la liste prend seul la parole.
  if (tousDevis.length === 0) return "";

  let titre, detail, alerte = false;
  if (nbARelancer) {
    titre = nbARelancer === 1 ? "Un devis à relancer aujourd'hui." : `${nbARelancer} devis à relancer aujourd'hui.`;
    detail = montantDus ? `${fmtEuro(montantDus)} en attente de réponse.` : "En attente de réponse.";
    alerte = true;
  } else if (aChiffrer) {
    titre = aChiffrer === 1 ? "Un devis reste à chiffrer." : `${aChiffrer} devis restent à chiffrer.`;
    detail = "Aucune relance due aujourd'hui.";
  } else if (pretsAEnvoyer) {
    titre = pretsAEnvoyer === 1 ? "Un devis est prêt à partir." : `${pretsAEnvoyer} devis sont prêts à partir.`;
    detail = "Aucune relance due aujourd'hui.";
  } else {
    titre = "Rien à relancer aujourd'hui.";
    detail = enCours.length ? `${enCours.length} devis en attente de réponse.` : "Aucun devis en cours.";
  }

  const contexte = [];
  if (valeurEnJeu) contexte.push(`<strong>${fmtEuro(valeurEnJeu)}</strong> en jeu`);
  if (aChiffrer) contexte.push(`<strong>${aChiffrer}</strong> à chiffrer`);
  if (pretsAEnvoyer) contexte.push(`<strong>${pretsAEnvoyer}</strong> prêt${pretsAEnvoyer > 1 ? "s" : ""} à envoyer`);
  if (jamaisOuverts) contexte.push(`<strong class="est-alerte">${jamaisOuverts}</strong> jamais ouvert${jamaisOuverts > 1 ? "s" : ""}`);
  if (taux !== null) contexte.push(`signature <strong>${taux} %</strong> (${signes} sur ${signes + perdus})`);

  return `
  <section class="devis-suivi">
    <div class="devis-suivi-lede${alerte ? " est-alerte" : ""}">
      <h3>${titre}</h3>
      <p>${detail}</p>
    </div>
    ${contexte.length ? `<p class="devis-suivi-contexte">${contexte.join(" · ")}</p>` : ""}
  </section>`;
}

function devisTabCountsHtml(tousDevis) {
  const compte = (statut) => tousDevis.filter((d) => d.statut === statut).length;
  return {
    nouveau: compte("nouveau"),
    envoye: tousDevis.filter((d) => ["envoye", "consulte", "relance_j3", "relance_j7", "relance_j15"].includes(d.statut)).length,
    signe: compte("signe"),
    perdu: compte("perdu"),
  };
}

// Dernier lot recu pour le statut actif (currentDevisFilter), pour pouvoir
// re-trier sans refaire l'appel serveur a chaque changement de tri.
let devisListCache = [];
let currentDevisSort = "date_desc";
// Filtres additionnels (voir 04-devis&relances) au-dela de l'onglet de
// statut grossier deja existant (#devis-filters) : un statut plus fin
// (les sous-etats de relance), une tranche de montant et un filtre sur la
// relance due - tout calcule cote client sur devisListCache/devisDueIds
// deja recus, aucun nouvel appel.
let currentDevisStatutFiltre = "";
let currentDevisMontantFiltre = "";
let currentDevisRelanceFiltre = "";

function devisSort(devis) {
  const d = devis.slice();
  if (currentDevisSort === "montant_desc") return d.sort((a, b) => (b.montant_ttc || 0) - (a.montant_ttc || 0));
  if (currentDevisSort === "client_asc") return d.sort((a, b) => a.client_nom.localeCompare(b.client_nom, "fr"));
  return d.sort((a, b) => b.created_at.localeCompare(a.created_at)); // date_desc, par defaut
}

function devisMatchesFiltres(d) {
  if (currentDevisStatutFiltre && d.statut !== currentDevisStatutFiltre) return false;
  if (currentDevisMontantFiltre) {
    const m = d.montant_ttc || 0;
    if (currentDevisMontantFiltre === "lt2000" && !(m < 2000)) return false;
    if (currentDevisMontantFiltre === "2000_10000" && !(m >= 2000 && m <= 10000)) return false;
    if (currentDevisMontantFiltre === "gt10000" && !(m > 10000)) return false;
  }
  if (currentDevisRelanceFiltre === "a_relancer" && !devisDueIds.has(d.id)) return false;
  if (currentDevisRelanceFiltre === "pas_de_relance" && devisDueIds.has(d.id)) return false;
  return true;
}

function renderDevisListFiltered() {
  const list = document.getElementById("devis-list");
  if (devisListCache.length === 0) {
    list.innerHTML = etatVide(
      "Vos devis vivront ici.",
      "Chaque devis envoyé est suivi jusqu'à la réponse du client : consulté ou non, relancé ou non. Vous verrez d'un coup d'œil lesquels attendent un geste de votre part.",
      { action: "show-devis-form", libelle: "Créer un devis" },
    );
    return;
  }
  const filtres = devisSort(devisListCache.filter(devisMatchesFiltres));
  list.innerHTML = filtres.length ? filtres.map(renderDevisCard).join("") : etatFiltre("Aucun devis ne correspond à ce filtre.");
  reapplyListSearch("devis-search", "#devis-list .list-row");
}

async function loadDevis() {
  const kpiBand = document.getElementById("devis-kpi-band");
  const list = document.getElementById("devis-list");
  list.innerHTML = skeletonCards();
  try {
    const [devis, tousDevis, aRelancer] = await Promise.all([
      Api.listDevis(currentDevisFilter), Api.listDevis(), Api.devisARelancer(),
    ]);
    devisDueIds = new Set(aRelancer.map((d) => d.id));
    if (kpiBand) kpiBand.innerHTML = devisKpiBandHtml(tousDevis, aRelancer.length);
    const counts = devisTabCountsHtml(tousDevis);
    const setCount = (statut, n) => {
      const el = document.querySelector(`#devis-filters .filter-chip[data-statut="${statut}"] .filter-chip-count`);
      if (el) el.textContent = `(${n})`;
    };
    setCount("nouveau", counts.nouveau);
    setCount("envoye", counts.envoye);
    setCount("signe", counts.signe);
    setCount("perdu", counts.perdu);
    devisListCache = devis;
    renderDevisListFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// ---------- Editeur de lignes reutilisable (devis + factures) ----------
function ligneRowHtml(ligne) {
  const l = ligne || { description: "", quantite: 1, unite: "forfait", prix_unitaire_ht: "" };
  return `
  <div class="ligne-row">
    <input type="text" class="ligne-description" list="prestations-datalist" placeholder="Description de la prestation (recherchez votre catalogue)" aria-label="Description de la prestation" value="${escapeHtml(l.description || "")}">
    <input type="number" step="0.01" min="0" class="ligne-quantite" placeholder="Qté" aria-label="Quantité" value="${l.quantite ?? 1}">
    <input type="text" class="ligne-unite" placeholder="Unité" aria-label="Unité" value="${escapeHtml(l.unite || "forfait")}">
    <input type="number" step="0.01" min="0" class="ligne-prix" placeholder="Prix HT" aria-label="Prix unitaire HT" value="${l.prix_unitaire_ht !== undefined && l.prix_unitaire_ht !== null ? l.prix_unitaire_ht : ""}">
    <!-- Le total de la ligne. C'est la qu'une erreur de quantite ou de
         prix se voit, bien avant le total general. -->
    <span class="ligne-total" aria-live="polite"></span>
    <button type="button" class="icon-btn ligne-remove" data-action="remove-ligne" title="Retirer" aria-label="Retirer cette ligne">
      <svg viewBox="0 0 24 24" class="nav-icon"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
    </button>
  </div>`;
}

// ---------------------------------------------------------------------
// LE TOTALISATEUR — le bloc de totaux d'un devis, calcule en direct
// ---------------------------------------------------------------------
// L'ecran de creation ne montrait AUCUN total. On saisissait des lignes,
// des quantites, des prix, un pourcentage de remise et un pourcentage
// d'acompte, et on decouvrait le montant apres avoir enregistre. On
// construisait un devis en aveugle.
//
// LA REGLE ABSOLUE ICI : ce calcul doit reproduire celui du serveur au
// centime pres, ARRONDI INTERMEDIAIRE COMPRIS (voir les proprietes du
// modele Devis dans backend/app/models.py). Un total affiche qui differe
// de celui qui sera enregistre serait pire que pas de total du tout.
//
//   montant_ht_brut = round(somme(quantite x prix_unitaire_ht), 2)
//   remise_montant  = round(brut x remise% / 100, 2)
//   montant_ht      = round(brut - remise, 2)
//   montant_ttc     = round(montant_ht x (1 + tva/100), 2)
//
// L'acompte se calcule sur le HT et non sur le TTC (voir
// routers/chantiers.py, creation de la facture d'acompte) : il est donc
// libelle « HT » pour ne pas laisser croire a un montant a encaisser.
const arrondi2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

function devisTotaux(lignes, tauxTva, remisePct, acomptePct) {
  const brut = lignes.length
    ? arrondi2(lignes.reduce((s, l) => s + (Number(l.quantite) || 0) * (Number(l.prix_unitaire_ht) || 0), 0))
    : null;
  if (brut === null) return null;
  const remise = remisePct ? arrondi2((brut * remisePct) / 100) : 0;
  const ht = arrondi2(brut - remise);
  const tva = arrondi2(ht * (Number(tauxTva) || 0) / 100);
  const ttc = arrondi2(ht * (1 + (Number(tauxTva) || 0) / 100));
  // L'acompte se calcule sur le HT, comme le serveur (routers/chantiers.py :
  // la facture d'acompte porte `montant_ht = ht x pct / 100`). Mais ce que le
  // client PAIE, c'est cette facture TTC - et c'est ce montant-la qui figure
  // sur la page publique qu'il signe. Les deux existaient donc cote a cote
  // sans que rien ne dise lequel etait lequel : l'artisan lisait 311,22 € et
  // son client 342,34 € pour le meme acompte du meme devis. On calcule les
  // deux, et on les libelle.
  const acompte = acomptePct ? arrondi2((ht * acomptePct) / 100) : 0;
  const acompteTtc = acomptePct ? arrondi2(acompte * (1 + (Number(tauxTva) || 0) / 100)) : 0;
  return { brut, remise, remisePct, ht, tva, tauxTva, ttc, acompte, acompteTtc, acomptePct };
}

/** Le bloc de totaux, aligne a droite comme sur un devis imprime : les
 *  libelles a gauche, les montants en colonne, un filet fort avant le
 *  total a payer. C'est la forme que l'artisan connait deja. */
function devisTotalisateurHtml(t) {
  if (!t) {
    return `<div class="totalisateur est-vide">
      <p>Ajoutez une prestation pour voir le total se calculer.</p>
    </div>`;
  }
  const ligne = (label, montant, classe = "") =>
    `<div class="totalisateur-ligne ${classe}"><span>${label}</span><span>${fmtEuro(montant)}</span></div>`;

  return `
  <div class="totalisateur">
    ${ligne("Total HT", t.brut)}
    ${t.remise ? ligne(`Remise ${t.remisePct} %`, -t.remise, "est-remise") : ""}
    ${t.remise ? ligne("Net HT", t.ht) : ""}
    ${ligne(`TVA ${t.tauxTva} %`, t.tva)}
    ${ligne("Total TTC", t.ttc, "est-total")}
    ${t.acompte ? ligne(`Acompte ${t.acomptePct} % à la signature`, t.acompteTtc, "est-acompte") : ""}
    ${t.acompte ? `<div class="totalisateur-note">soit ${fmtEuro(t.acompte)} HT, le montant de la facture d'acompte</div>` : ""}
  </div>`;
}

/** Recalcule le bloc a chaque frappe. Branche sur `input` ET `change` :
 *  le premier couvre la saisie au clavier, le second les listes
 *  deroulantes (TVA) et les fleches d'un champ nombre.
 *
 *  Les selecteurs des champs sont passes en argument plutot qu'ecrits en
 *  dur : le meme totalisateur sert au devis (remise et acompte) et a la
 *  facture (ni l'une ni l'autre). Ils etaient figes sur les identifiants du
 *  devis, ce qui interdisait toute reutilisation - et la facture, qui liste
 *  pourtant les memes prestations avec le meme taux de TVA, ne montrait
 *  aucun total avant l'enregistrement. */
function brancherTotalisateur(formEl, containerId, champs = {}) {
  const { tva = "#df-taux-tva", remise = "#df-remise", acompte = "#df-acompte" } = champs;
  const cible = formEl.querySelector(".totalisateur-hote");
  if (!cible) return;
  const lire = (sel) => (sel ? parseFloat(formEl.querySelector(sel)?.value) || 0 : 0);
  const recalculer = () => {
    const t = devisTotaux(lireLignes(containerId), lire(tva), lire(remise), lire(acompte));
    cible.innerHTML = devisTotalisateurHtml(t);
    // Chaque ligne affiche aussi son propre total : c'est la ou une erreur
    // de quantite ou de prix se voit, bien avant le total general.
    formEl.querySelectorAll(`#${containerId} .ligne-row`).forEach((row) => {
      const q = parseFloat(row.querySelector(".ligne-quantite")?.value) || 0;
      const p = parseFloat(row.querySelector(".ligne-prix")?.value) || 0;
      const cellule = row.querySelector(".ligne-total");
      if (cellule) cellule.textContent = q && p ? fmtEuro(arrondi2(q * p)) : "";
    });
  };
  formEl.addEventListener("input", recalculer);
  formEl.addEventListener("change", recalculer);
  formEl.addEventListener("click", (e) => {
    // Ajout ou suppression d'une ligne : le recalcul doit suivre le DOM,
    // donc apres que le gestionnaire de l'editeur a fait son travail.
    if (e.target.closest('[data-action="add-ligne"], [data-action="remove-ligne"]')) setTimeout(recalculer, 0);
  });
  recalculer();
}

function lignesEditorHtml(containerId, lignes) {
  const rows = (lignes && lignes.length ? lignes : [null]).map(ligneRowHtml).join("");
  return `
  <div class="lignes-editor">
    <div class="ligne-row ligne-row-header" aria-hidden="true">
      <span>Désignation</span><span>Qté</span><span>Unité</span><span>Prix HT</span><span>Total HT</span><span></span>
    </div>
    <div id="${containerId}">${rows}</div>
    <button type="button" class="btn-sm" data-action="add-ligne" data-target="${containerId}">+ Ajouter une ligne</button>
    ${prestationsDatalistHtml()}
  </div>`;
}

function attacherEditeurLignes(formEl) {
  formEl.addEventListener("click", (e) => {
    const addBtn = e.target.closest('[data-action="add-ligne"]');
    if (addBtn) {
      document.getElementById(addBtn.dataset.target).insertAdjacentHTML("beforeend", ligneRowHtml());
      return;
    }
    const removeBtn = e.target.closest('[data-action="remove-ligne"]');
    if (removeBtn) {
      const row = removeBtn.closest(".ligne-row");
      const parent = row.parentElement;
      if (parent.children.length > 1) row.remove();
    }
  });

  // Choisir une prestation du catalogue (via la datalist) remplit
  // automatiquement l'unite et le prix unitaire de la ligne.
  formEl.addEventListener("input", (e) => {
    if (!e.target.classList.contains("ligne-description")) return;
    const prestation = prestationsCache.find((p) => p.description === e.target.value);
    if (!prestation) return;
    const row = e.target.closest(".ligne-row");
    row.querySelector(".ligne-unite").value = prestation.unite;
    row.querySelector(".ligne-prix").value = prestation.prix_unitaire_ht;
  });
}

function lireLignes(containerId) {
  const rows = document.querySelectorAll(`#${containerId} .ligne-row`);
  const lignes = [];
  rows.forEach((row) => {
    const description = row.querySelector(".ligne-description").value.trim();
    const prixRaw = row.querySelector(".ligne-prix").value;
    if (!description || prixRaw === "") return;
    lignes.push({
      description,
      quantite: parseFloat(row.querySelector(".ligne-quantite").value) || 1,
      unite: row.querySelector(".ligne-unite").value.trim() || "u",
      prix_unitaire_ht: parseFloat(prixRaw),
    });
  });
  return lignes;
}

function showPreparerChantierForm(devisId) {
  const container = document.getElementById(`preparer-form-${devisId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <h3 style="font-size:0.95rem;">Tout préparer</h3>
      <p class="section-hint">Crée le chantier, l'acompte à facturer et une checklist de préparation.</p>
      <div class="form-grid form-grid-labels-aligned">
        <div><label for="prep-adresse-${devisId}">Adresse du chantier</label><input type="text" id="prep-adresse-${devisId}"></div>
        <div><label for="prep-date-${devisId}">Date de début</label><input type="date" id="prep-date-${devisId}" min="${today}"></div>
        <div><label for="prep-budget-${devisId}">Budget (optionnel, sinon = montant HT du devis)</label><input type="number" step="0.01" min="0" id="prep-budget-${devisId}"></div>
      </div>
      <label class="checkbox-option">
        <input type="checkbox" id="prep-acompte-${devisId}" checked> Créer la facture d'acompte
      </label>
      <label class="checkbox-option">
        <input type="checkbox" id="prep-checklist-${devisId}" checked> Créer la checklist de préparation
      </label>
      <p class="field-error" id="preparer-error-${devisId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="confirmer-preparer-chantier" data-id="${devisId}">Confirmer</button>
        <button type="button" class="btn-sm" data-action="cancel-preparer-form" data-id="${devisId}">Annuler</button>
      </div>
    </div>`;
}

function renderDevisCard(d) {
  const meta = DEVIS_STATUT_META[d.statut] || { label: d.statut, badge: "badge-gray" };
  const isDue = devisDueIds.has(d.id);
  const montantTxt = d.montant_ttc !== null && d.montant_ttc !== undefined ? fmtEuro(d.montant_ttc) : "Non défini";

  // Actions possibles, evaluees dans les memes conditions qu'avant (memes
  // data-action/data-id/data-token) : seule leur repartition entre le
  // bouton primaire visible sur la ligne et le menu "•••" change - voir
  // setupActionMenus() pour le controleur generique du menu.
  const items = [];
  if (d.statut === "nouveau" && d.montant_ht !== null) {
    items.push({ primaire: true, attrs: `data-action="envoyer-devis" data-id="${d.id}"`, label: "Envoyer le devis" });
  }
  if (d.statut === "nouveau") {
    // Un devis pas encore chiffre n'a rien d'autre a faire en priorite que
    // d'etre chiffre : "Editer" devient alors l'action primaire visible.
    items.push({ primaire: d.montant_ht === null, attrs: `data-action="edit-devis" data-id="${d.id}"`, label: "Éditer / chiffrer" });
  }
  if (["envoye", "consulte", "relance_j3", "relance_j7"].includes(d.statut)
      && hasPlan("essentiel") && d.relance_manuelle_possible !== false) {
    items.push({ primaire: true, attrs: `data-action="relancer-devis" data-id="${d.id}"`, label: "Relancer" });
  }
  if (d.statut === "signe") {
    items.push({ primaire: true, attrs: `data-action="preparer-chantier" data-id="${d.id}"`, label: "Tout préparer" });
    items.push({ attrs: `data-action="facturer-devis" data-id="${d.id}"`, label: "Convertir en facture" });
  }
  if (["envoye", "consulte", "relance_j3", "relance_j7", "relance_j15"].includes(d.statut)) {
    items.push({ attrs: `data-action="marquer-devis" data-id="${d.id}" data-statut="signe"`, label: "Marquer signé" });
    items.push({ attrs: `data-action="marquer-devis" data-id="${d.id}" data-statut="perdu"`, label: "Marquer perdu" });
  }
  if (d.lignes && d.lignes.length > 0) {
    items.push({ attrs: `data-action="pdf-devis" data-id="${d.id}"`, label: "Télécharger le PDF" });
  }
  if (d.token && d.statut !== "nouveau") {
    items.push({ attrs: `data-action="copier-lien-devis" data-token="${escapeHtml(d.token)}"`, label: "Copier le lien client" });
  }
  items.push({ attrs: `data-action="dupliquer-devis" data-id="${d.id}"`, label: "Dupliquer" });
  items.push({ divider: true });
  items.push({ attrs: `data-action="delete-devis" data-id="${d.id}"`, label: "Archiver", danger: true });

  const primaireIdx = items.findIndex((it) => it.primaire);
  const primaireHtml = primaireIdx !== -1
    ? `<button type="button" class="btn-sm btn-sm-primary" ${items[primaireIdx].attrs}>${items[primaireIdx].label}</button>`
    : "";
  const menuHtml = items
    .filter((it, i) => i !== primaireIdx)
    .map((it) => it.divider
      ? '<div class="action-menu-divider"></div>'
      : `<button type="button"${it.danger ? ' class="is-danger"' : ""} ${it.attrs}>${it.label}</button>`)
    .join("");

  // "Suivi" (voir 04-devis&relances) : un texte de statut contextuel colore,
  // separe du numero de devis (colonne dediee "Devis N°" juste a cote) -
  // toujours derive de champs deja recus (statut, date_signature, relance
  // due, nb_relances), jamais une nouvelle donnee.
  const suivi = devisSuivi(d, isDue);

  return `
  <div class="list-row list-row-devis ${isDue ? "is-due" : ""}">
    <!-- Le bloc d'identite ouvre le devis en LECTURE. C'etait le geste
         manquant : on pouvait tout faire d'un devis sauf le consulter. -->
    <div class="list-row-primary est-cliquable" data-action="voir-devis" data-id="${d.id}"
         role="button" tabindex="0" aria-label="Lire le devis ${escapeHtml(d.numero || "")} de ${escapeHtml(d.client_nom)}">
      <span class="crm-avatar">${escapeHtml(monogram(d.client_nom))}</span>
      <div class="list-row-primary-copy">
        <div class="list-row-title">${escapeHtml(d.client_nom)}</div>
        <div class="list-row-sub">${escapeHtml(d.titre || d.description || "Sans titre")}</div>
      </div>
    </div>
    <div class="list-row-status"><span class="badge ${meta.badge}">${meta.label}</span></div>
    <div class="list-row-amount">${montantTxt}${d.montant_ttc !== null && d.montant_ttc !== undefined ? '<span class="list-row-amount-sub">TTC</span>' : ""}</div>
    <div class="list-row-suivi ${suivi.cls}">${escapeHtml(suivi.texte)}</div>
    <div class="list-row-numero">${escapeHtml(d.numero)}</div>
    <div class="list-row-primary-action">${primaireHtml}</div>
    <div class="list-row-menu">
      <div class="action-menu">
        <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur ce devis">
          <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
        </button>
        <div class="action-menu-panel" role="menu">${menuHtml}</div>
      </div>
    </div>
    ${d.statut === "signe" ? `<div class="list-row-banner moment-banner"><span>Devis accepté ! ${fmtEuro(d.montant_ttc)}${d.nom_signataire ? " · signé par " + escapeHtml(d.nom_signataire) : ""} — prêt à démarrer le projet avec « Tout préparer ».</span></div>` : ""}
    <div id="preparer-form-${d.id}" class="list-row-expand"></div>
  </div>`;
}

// ---------------------------------------------------------------------
// DETAIL D'UN DEVIS — « lire le document »
// ---------------------------------------------------------------------
// Il n'existait AUCUN ecran pour lire un devis dans l'application. On
// pouvait l'editer, l'envoyer, le dupliquer, telecharger son PDF - mais
// pour voir ce qu'on avait vendu, il fallait ouvrir le PDF ou le portail
// client. Les lignes, les quantites, les prix et les totaux etaient
// inaccessibles depuis le produit lui-meme.
//
// Aucun appel supplementaire n'est necessaire : `listDevis` renvoie deja
// les lignes de chaque devis, et toutes les dates de son parcours.
//
// L'ecran repose sur deux blocs que le reste du produit connait deja - le
// tableau des prestations et le totalisateur, les memes qu'a la saisie -
// plus un troisieme, propre a la lecture : la vie du devis.

/** La vie du devis, reconstituee a partir des dates deja presentes sur
 *  l'objet. La liste ne pouvait en montrer qu'une ligne de resume ; ici on
 *  voit le parcours entier, et donc pourquoi une relance est due. */
function devisVieHtml(d) {
  const etapes = [];
  if (d.created_at) etapes.push({ date: d.created_at, label: "Devis créé" });
  if (d.date_envoi) etapes.push({ date: d.date_envoi, label: "Envoyé au client" });
  if (d.date_consultation) etapes.push({ date: d.date_consultation, label: "Ouvert par le client", fort: true });
  if (d.date_derniere_relance) {
    etapes.push({
      date: d.date_derniere_relance,
      label: d.nb_relances > 1 ? `Dernière relance (${d.nb_relances} au total)` : "Relance envoyée",
    });
  }
  if (d.date_signature) {
    etapes.push({
      date: d.date_signature,
      label: d.nom_signataire ? `Accepté par ${escapeHtml(d.nom_signataire)}` : "Accepté",
      fort: true,
    });
  }
  if (!etapes.length) return `<p class="fiche-vide">Ce devis n'a pas encore d'histoire : il n'a pas été envoyé.</p>`;

  etapes.sort((a, b) => new Date(a.date) - new Date(b.date));
  // Un devis envoye et jamais ouvert est la seule chose que les dates ne
  // disent pas d'elles-memes : on l'ecrit.
  const attente = d.date_envoi && !d.date_consultation && !d.date_signature
    ? `<p class="devis-vie-attente">Jamais ouvert depuis l'envoi. Le devis n'est peut-être pas arrivé — vérifiez l'adresse du client avant de relancer une fois de plus.</p>`
    : "";

  return `
    <ol class="devis-vie">
      ${etapes.map((e) => `
        <li class="devis-vie-etape${e.fort ? " est-forte" : ""}">
          <time>${fmtDateTime(e.date)}</time>
          <span>${e.label}</span>
        </li>`).join("")}
    </ol>
    ${attente}`;
}

/** Le tableau des prestations, en LECTURE. Meme colonnes qu'a la saisie,
 *  meme alignement des chiffres : on relit le document tel qu'on l'a
 *  construit, et tel que le client le recevra. */
function devisLignesLectureHtml(lignes) {
  if (!lignes || !lignes.length) {
    return `<p class="fiche-vide">Aucune prestation n'a encore été chiffrée sur ce devis.</p>`;
  }
  return `
  <table class="devis-lecture">
    <thead>
      <tr>
        <th scope="col">Désignation</th>
        <th scope="col" class="est-nombre">Qté</th>
        <th scope="col">Unité</th>
        <th scope="col" class="est-nombre">Prix HT</th>
        <th scope="col" class="est-nombre">Total HT</th>
      </tr>
    </thead>
    <tbody>
      ${lignes.map((l) => `
        <tr>
          <td>${escapeHtml(l.description)}</td>
          <td class="est-nombre">${l.quantite}</td>
          <td>${escapeHtml(l.unite || "")}</td>
          <td class="est-nombre">${fmtEuro(l.prix_unitaire_ht)}</td>
          <td class="est-nombre est-total">${fmtEuro(Math.round((l.quantite * l.prix_unitaire_ht + Number.EPSILON) * 100) / 100)}</td>
        </tr>`).join("")}
    </tbody>
  </table>`;
}

function showDevisDetail(devisId) {
  const d = devisListCache.find((x) => x.id === devisId)
    || (window.__devisTousCache || []).find((x) => x.id === devisId);
  const panneau = document.getElementById("panel-devis");
  if (!panneau || !d) return;

  const meta = DEVIS_STATUT_META[d.statut] || { label: d.statut, badge: "badge-gray" };
  const suivi = devisSuivi(d, devisDueIds.has(d.id));
  // Les memes totaux qu'a la saisie, recalcules depuis les lignes : le
  // document se relit exactement comme il a ete construit.
  const totaux = devisTotaux(d.lignes || [], d.taux_tva, d.remise_pourcentage || 0, d.acompte_pourcentage || 0);

  document.getElementById("devis-detail-titre").textContent = d.numero || `Devis #${d.id}`;
  document.getElementById("devis-detail-sous").innerHTML =
    `${escapeHtml(d.client_nom)}${d.titre ? " · " + escapeHtml(d.titre) : ""}`;

  document.getElementById("devis-detail-corps").innerHTML = `
    <div class="devis-detail-etat">
      <span class="badge ${meta.badge}">${escapeHtml(meta.label)}</span>
      <span class="devis-detail-suivi ${suivi.cls}">${escapeHtml(suivi.texte)}</span>
    </div>

    ${chantierActionsDevisHtml(d)}

    ${ficheSection("Prestations", devisLignesLectureHtml(d.lignes))}

    ${totaux ? `<div class="devis-detail-totaux">${devisTotalisateurHtml(totaux)}</div>` : ""}

    ${d.description ? ficheSection("Notes au client", `<p class="devis-detail-notes">${escapeHtml(d.description)}</p>`) : ""}

    ${ficheSection("La vie de ce devis", devisVieHtml(d))}
  `;
  panneau.hidden = false;
  panneau.dataset.devisId = devisId;
  panneau.querySelector(".side-panel-close").focus();
}

/** Les actions du devis, reprises telles quelles de la ligne de liste :
 *  memes `data-action`, memes conditions. Le gestionnaire delegue de la
 *  vue Devis est branche sur le panneau, donc rien n'a change de nom. */
function chantierActionsDevisHtml(d) {
  const actions = [];
  if (d.statut === "nouveau" && d.montant_ht !== null) actions.push({ p: true, a: `data-action="envoyer-devis" data-id="${d.id}"`, l: "Envoyer le devis" });
  if (d.statut === "nouveau") actions.push({ p: d.montant_ht === null, a: `data-action="edit-devis" data-id="${d.id}"`, l: "Éditer / chiffrer" });
  if (["envoye", "consulte", "relance_j3", "relance_j7"].includes(d.statut) && hasPlan("essentiel") && d.relance_manuelle_possible !== false) {
    actions.push({ p: true, a: `data-action="relancer-devis" data-id="${d.id}"`, l: "Relancer" });
  }
  if (d.statut === "signe") actions.push({ p: true, a: `data-action="preparer-chantier" data-id="${d.id}"`, l: "Tout préparer" });
  if (d.lignes && d.lignes.length) actions.push({ a: `data-action="pdf-devis" data-id="${d.id}"`, l: "Télécharger le PDF" });
  if (d.token && d.statut !== "nouveau") actions.push({ a: `data-action="copier-lien-devis" data-token="${escapeHtml(d.token)}"`, l: "Copier le lien client" });
  actions.push({ a: `data-action="dupliquer-devis" data-id="${d.id}"`, l: "Dupliquer" });

  return `<div class="fiche-actions">${actions
    .map((x) => `<button type="button" class="btn-sm${x.p ? " btn-sm-primary" : ""}" ${x.a}>${x.l}</button>`)
    .join("")}</div>`;
}

async function showDevisForm(devis, preselectClientId) {
  const container = document.getElementById("devis-form-container");
  const isEdit = !!devis;
  await Promise.all([ensureClientsCache(), ensurePrestationsCache()]);

  // Un nouvel artisan sans aucun client ne doit pas etre bloque hors de cet
  // ecran pour en creer un : le backend supporte deja la creation a la volee
  // (DevisCreate.nouveau_client), on demarre donc directement en mode
  // "nouveau client" plutot que d'afficher un select vide.
  const demarrerEnNouveauClient = !isEdit && clientsCache.length === 0;

  container.dataset.editingId = isEdit ? devis.id : "";
  container.innerHTML = `
    <div class="form-box">
      <h3>${isEdit ? "Modifier le devis" : "Nouveau devis"}</h3>
      <form id="devis-form">
        <div class="form-section">
          <div class="form-section-title">Client</div>
          <div>
            <label for="df-client">Client *</label>
            ${isEdit
              ? `<input type="text" value="${escapeHtml(devis.client_nom)}" disabled>`
              : `
              <div id="df-client-existant" ${demarrerEnNouveauClient ? "hidden" : ""}>
                <select id="df-client" ${demarrerEnNouveauClient ? "" : "required"}><option value="">Choisir...</option>${clientOptionsHtml(preselectClientId)}</select>
                ${clientsCache.length > 0 ? `<button type="button" class="btn-sm" data-action="toggle-nouveau-client-devis" style="margin-top:6px;">+ Nouveau client</button>` : ""}
              </div>
              <div id="df-client-nouveau" ${demarrerEnNouveauClient ? "" : "hidden"}>
                <input type="text" id="df-nouveau-client-nom" placeholder="Nom du client *" ${demarrerEnNouveauClient ? "required" : ""}>
                <input type="email" id="df-nouveau-client-email" placeholder="Email (optionnel)" style="margin-top:6px;">
                <input type="tel" id="df-nouveau-client-telephone" placeholder="Téléphone (optionnel)" style="margin-top:6px;">
                ${clientsCache.length > 0 ? `<button type="button" class="btn-sm" data-action="toggle-nouveau-client-devis" style="margin-top:6px;">Choisir un client existant</button>` : ""}
              </div>
              `
            }
          </div>
        </div>

        <div class="form-section">
          <div class="form-section-title">Informations du devis</div>
          <div class="form-grid">
            <div>
              <label for="df-titre">Titre</label>
              <input type="text" id="df-titre" placeholder="Ex: Rénovation salle de bain" value="${isEdit ? escapeHtml(devis.titre || "") : ""}">
            </div>
            <div>
              <label for="df-taux-tva">TVA</label>
              <select id="df-taux-tva">
                <option value="10" ${!isEdit || devis.taux_tva === 10 ? "selected" : ""}>10% (rénovation)</option>
                <option value="20" ${isEdit && devis.taux_tva === 20 ? "selected" : ""}>20% (neuf)</option>
              </select>
            </div>
          </div>
        </div>

        <div class="form-section">
          <div class="form-section-title">Prestations</div>
          ${lignesEditorHtml("df-lignes", isEdit ? devis.lignes : null)}
        </div>

        <!-- Le pied du document : conditions a gauche, totaux a droite,
             exactement comme sur le devis imprime. Les pourcentages
             d'acompte et de remise cessent d'etre abstraits - leur montant
             en euros s'affiche en face, et se recalcule a chaque frappe.
             L'ecran ne montrait AUCUN total : on construisait un devis en
             aveugle et on decouvrait le montant apres enregistrement. -->
        <div class="doc-pied">
          <div class="doc-pied-conditions">
            <div class="form-section-title">Conditions</div>
            <div class="form-grid">
              <div>
                <label for="df-acompte">Acompte à la signature (%)</label>
                <input type="number" step="1" min="0" max="100" id="df-acompte" value="${isEdit ? devis.acompte_pourcentage : 30}">
              </div>
              <div>
                <label for="df-remise">Remise (%, optionnel)</label>
                <input type="number" step="1" min="0" max="100" id="df-remise" placeholder="0" value="${isEdit && devis.remise_pourcentage ? devis.remise_pourcentage : ""}">
              </div>
            </div>
            <label for="df-description" style="margin-top:14px;">Notes au client</label>
            <textarea id="df-description" placeholder="Conditions particulières, délais, précisions…">${isEdit ? escapeHtml(devis.description || "") : ""}</textarea>
          </div>
          <div class="totalisateur-hote" aria-live="polite" aria-label="Totaux du devis"></div>
        </div>

        <p class="field-error" id="devis-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">${isEdit ? "Enregistrer" : "Créer le devis"}</button>
          <button type="button" class="btn-sm" data-action="cancel-devis-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  const formEl = document.getElementById("devis-form");
  attacherEditeurLignes(formEl);
  brancherTotalisateur(formEl, "df-lignes");

  if (!isEdit) {
    const btnExistant = document.getElementById("df-client-existant");
    const btnNouveau = document.getElementById("df-client-nouveau");
    formEl.addEventListener("click", (e) => {
      if (!e.target.closest('[data-action="toggle-nouveau-client-devis"]')) return;
      const versNouveau = btnNouveau.hidden;
      btnExistant.hidden = versNouveau;
      btnNouveau.hidden = !versNouveau;
      document.getElementById("df-client").required = !versNouveau;
      document.getElementById("df-nouveau-client-nom").required = versNouveau;
    });
  }

  formEl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("devis-form-error");
    errorBox.hidden = true;
    const titre = document.getElementById("df-titre").value;
    const description = document.getElementById("df-description").value;

    const remiseRaw = document.getElementById("df-remise").value;
    const payload = {
      titre: emptyToNull(titre),
      description: emptyToNull(description),
      taux_tva: parseFloat(document.getElementById("df-taux-tva").value),
      acompte_pourcentage: parseFloat(document.getElementById("df-acompte").value) || 0,
      remise_pourcentage: remiseRaw ? parseFloat(remiseRaw) : null,
      lignes: lireLignes("df-lignes"),
    };
    if (!isEdit) {
      const enModeNouveauClient = document.getElementById("df-client-nouveau").hidden === false;
      if (enModeNouveauClient) {
        const nom = document.getElementById("df-nouveau-client-nom").value.trim();
        if (!nom) {
          errorBox.hidden = false;
          errorBox.textContent = "Indiquez le nom du nouveau client.";
          return;
        }
        payload.nouveau_client = {
          nom,
          email: emptyToNull(document.getElementById("df-nouveau-client-email").value),
          telephone: emptyToNull(document.getElementById("df-nouveau-client-telephone").value),
        };
      } else {
        payload.client_id = parseInt(document.getElementById("df-client").value, 10);
      }
    }

    try {
      if (isEdit) {
        await Api.updateDevis(devis.id, payload);
        showToast("Devis mis à jour.");
      } else {
        await Api.createDevis(payload);
        showToast("Devis créé.");
      }
      container.hidden = true;
      container.innerHTML = "";
      loadDevis();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

function setupDevisView() {
  document.getElementById("devis-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#devis-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentDevisFilter = chip.dataset.statut;
    loadDevis();
  });

  document.getElementById("devis-sort").addEventListener("change", (e) => {
    currentDevisSort = e.target.value;
    renderDevisListFiltered();
  });
  document.getElementById("devis-statut-filtre").addEventListener("change", (e) => {
    currentDevisStatutFiltre = e.target.value;
    renderDevisListFiltered();
  });
  document.getElementById("devis-montant-filtre").addEventListener("change", (e) => {
    currentDevisMontantFiltre = e.target.value;
    renderDevisListFiltered();
  });
  document.getElementById("devis-relance-filtre").addEventListener("change", (e) => {
    currentDevisRelanceFiltre = e.target.value;
    renderDevisListFiltered();
  });

  // Le meme gestionnaire est branche sur la liste ET sur le panneau de
  // lecture : les actions d'un devis se comportent pareil des deux cotes,
  // sans qu'aucune ait change de nom.
  const surActionDevis = async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "voir-devis") {
      showDevisDetail(id);
      return;
    }
    if (btn.dataset.action === "close-devis-detail") {
      document.getElementById("panel-devis").hidden = true;
      return;
    }

    if (btn.dataset.action === "edit-devis") {
      const devis = (await Api.listDevis(currentDevisFilter)).find((d) => d.id === id);
      showDevisForm(devis);
    } else if (btn.dataset.action === "envoyer-devis") {
      await withErrorToast(async () => {
        await Api.envoyerDevis(id);
        showToast("Devis envoyé. Copiez le lien client pour le transmettre (email, SMS...).");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "relancer-devis") {
      await withErrorToast(async () => {
        btn.disabled = true;
        try {
          const result = await Api.relancerDevis(id);
          const feedback = feedbackRelanceDevis(result);
          showToast(feedback.message, feedback.isError);
          btn.remove();
          loadDevis();
          refreshBadges();
        } catch (err) {
          btn.disabled = false;
          throw err;
        }
      });
    } else if (btn.dataset.action === "marquer-devis") {
      await withErrorToast(async () => {
        await Api.updateDevis(id, { statut: btn.dataset.statut });
        showToast("Statut mis à jour.");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "delete-devis") {
      if (!(await confirmDialog("Archiver ce devis ? Il disparaitra de vos listes actives mais reste conserve.", { confirmLabel: "Archiver", danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteDevis(id);
        showToast("Devis archive.");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "facturer-devis") {
      await withErrorToast(async () => {
        await Api.factureDepuisDevis(id, "standard");
        showToast("Facture créée à partir du devis.");
        switchView("factures");
      });
    } else if (btn.dataset.action === "preparer-chantier") {
      showPreparerChantierForm(id);
    } else if (btn.dataset.action === "cancel-preparer-form") {
      document.getElementById(`preparer-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "confirmer-preparer-chantier") {
      const errorBox = document.getElementById(`preparer-error-${id}`);
      errorBox.hidden = true;
      const budgetRaw = document.getElementById(`prep-budget-${id}`).value;
      try {
        const res = await Api.preparerChantierDepuisDevis(id, {
          adresse: emptyToNull(document.getElementById(`prep-adresse-${id}`).value),
          date_debut: emptyToNull(document.getElementById(`prep-date-${id}`).value),
          budget: budgetRaw === "" ? null : parseFloat(budgetRaw),
          creer_acompte: document.getElementById(`prep-acompte-${id}`).checked,
          creer_checklist: document.getElementById(`prep-checklist-${id}`).checked,
        });
        let msg = `Chantier "${res.chantier.titre}" cree.`;
        if (res.facture_acompte) msg += ` Facture d'acompte ${fmtEuro(res.facture_acompte.montant_ttc)} creee.`;
        if (res.nb_taches_creees > 0) msg += ` ${res.nb_taches_creees} taches de preparation ajoutees.`;
        showToast(msg);
        switchView("chantiers");
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "pdf-devis") {
      await withErrorToast(() => ouvrirPdf(`/devis/${id}/pdf`));
    } else if (btn.dataset.action === "copier-lien-devis") {
      const url = `${window.location.origin}/devis-public.html?t=${btn.dataset.token}`;
      try {
        await navigator.clipboard.writeText(url);
        showToast("Lien copié. Envoyez-le à votre client par email ou SMS.");
      } catch (err) {
        showToast(url, false);
      }
    } else if (btn.dataset.action === "dupliquer-devis") {
      await withErrorToast(async () => {
        await Api.dupliquerDevis(id);
        showToast("Devis duplique.");
        loadDevis();
      });
    }
  };
  document.getElementById("devis-list").addEventListener("click", surActionDevis);
  const panneauDevis = document.getElementById("panel-devis");
  panneauDevis.addEventListener("click", (e) => {
    // Clic sur le fond du panneau : on ferme, comme les autres panneaux.
    if (e.target === panneauDevis) { panneauDevis.hidden = true; return; }
    surActionDevis(e);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !panneauDevis.hidden) panneauDevis.hidden = true;
  });
  // La ligne de liste est une zone cliquable : au clavier, Entree et
  // Espace doivent l'ouvrir comme un bouton.
  document.getElementById("devis-list").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const cible = e.target.closest('[data-action="voir-devis"]');
    if (!cible) return;
    e.preventDefault();
    showDevisDetail(parseInt(cible.dataset.id, 10));
  });

  document.querySelector('[data-action="show-devis-form"]').addEventListener("click", () => showDevisForm(null));
  document.getElementById("devis-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-devis-form"]')) {
      const container = document.getElementById("devis-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });
}

// ===================== Factures =====================
let currentFactureFilter = "";
let facturesDueIds = new Set();

function joursRetard(dateEcheance) {
  if (!dateEcheance) return null;
  const diff = Math.floor((new Date() - new Date(dateEcheance)) / 86400000);
  return diff > 0 ? diff : null;
}

// ---------------------------------------------------------------------
// FACTURES — « la balance agee »
// ---------------------------------------------------------------------
// La page ouvrait sur trois cartes : a encaisser, en retard, factures en
// cours. Elles disaient COMBIEN mais jamais DEPUIS QUAND, alors que c'est
// la seule chose qui compte sur une creance. 1 840 € en retard de cinq
// jours est un oubli ; les memes 1 840 € en retard de soixante-dix jours
// sont un probleme de recouvrement. Les deux s'affichaient a l'identique.
//
// La balance agee est la vue que tout gestionnaire connait : le montant
// du, reparti par anciennete. Elle tient en un objet, et l'encre
// s'assombrit avec le retard - la couleur dit la gravite, le libelle la
// nomme (une teinte ne porte jamais seule une information).

const FACTURE_TRANCHES = [
  { cle: "a_venir", label: "Pas encore échu", min: -Infinity, max: 0 },
  { cle: "recent", label: "1 à 30 jours", min: 1, max: 30 },
  { cle: "moyen", label: "31 à 60 jours", min: 31, max: 60 },
  { cle: "ancien", label: "Plus de 60 jours", min: 61, max: Infinity },
];

/** Jours de retard d'une facture, negatif si l'echeance est a venir. */
function factureAnciennete(f) {
  if (!f.date_echeance) return null;
  const d = new Date(String(f.date_echeance).slice(0, 10) + "T00:00:00");
  if (isNaN(d)) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((today - d) / 86400000);
}

function tresorerieHeaderHtml(factures) {
  // Meme perimetre qu'avant : ce qui reste a encaisser, hors brouillons,
  // annulees et payees.
  const enCours = factures.filter((f) => !["brouillon", "annulee", "payee"].includes(f.statut));
  if (enCours.length === 0) return "";

  const total = enCours.reduce((s, f) => s + f.montant_restant, 0);
  const tranches = FACTURE_TRANCHES.map((t) => {
    const items = enCours.filter((f) => {
      const j = factureAnciennete(f);
      // Une facture sans echeance ne peut pas etre en retard : elle est
      // rangee avec ce qui n'est pas encore du.
      if (j === null) return t.cle === "a_venir";
      return j >= t.min && j <= t.max;
    });
    return { ...t, nb: items.length, montant: items.reduce((s, f) => s + f.montant_restant, 0) };
  });

  const enRetard = tranches.filter((t) => t.cle !== "a_venir").reduce((s, t) => s + t.montant, 0);
  const nbEnRetard = tranches.filter((t) => t.cle !== "a_venir").reduce((s, t) => s + t.nb, 0);

  return `
  <section class="balance">
    <div class="balance-total">
      <span class="balance-total-valeur">${fmtEuro(total)}</span>
      <span class="balance-total-label">à encaisser sur ${enCours.length} facture${enCours.length > 1 ? "s" : ""}</span>
    </div>
    <div class="balance-axe">
      ${total ? `<div class="balance-barre">
        ${tranches.filter((t) => t.montant > 0).map((t) => `
          <span class="balance-seg est-${t.cle}" style="flex:${t.montant}"
                title="${t.label} : ${fmtEuro(t.montant)}"></span>`).join("")}
      </div>` : ""}
      <div class="balance-legende">
        ${tranches.map((t) => `
          <span class="balance-tranche${t.nb ? "" : " est-vide"}">
            <span class="balance-puce est-${t.cle}" aria-hidden="true"></span>
            <span class="balance-tranche-label">${t.label}</span>
            <span class="balance-tranche-montant">${t.montant ? fmtEuro(t.montant) : "—"}</span>
            <span class="balance-tranche-nb">${t.nb ? `${t.nb} facture${t.nb > 1 ? "s" : ""}` : "aucune"}</span>
          </span>`).join("")}
      </div>
    </div>
    <p class="balance-verdict">${enRetard > 0
      ? `<strong class="est-retard">${fmtEuro(enRetard)}</strong> en retard sur ${nbEnRetard} facture${nbEnRetard > 1 ? "s" : ""}.`
      : "Aucune facture en retard."}</p>
  </section>`;
}

let facturesCache = [];
let currentFactureSort = ""; // "" = respecte l'ordre deja produit par le filtre actif (ex: echeance pour "a_encaisser")
// Filtres additionnels (voir 05-factures) au-dela de l'onglet/menu Statut
// deja synchronises par activerFactureFiltreStatut() : Paiement et
// Echeance, tous deux calcules sur des champs deja recus
// (montant_paye/montant_restant/date_echeance/est_en_retard).
let currentFacturePaiementFiltre = "";
let currentFactureEcheanceFiltre = "";

function factureSort(factures) {
  if (!currentFactureSort) return factures;
  const f = factures.slice();
  if (currentFactureSort === "montant_desc") return f.sort((a, b) => (b.montant_ttc || 0) - (a.montant_ttc || 0));
  if (currentFactureSort === "echeance_asc") return f.sort((a, b) => (a.date_echeance || "9999-99-99").localeCompare(b.date_echeance || "9999-99-99"));
  if (currentFactureSort === "client_asc") return f.sort((a, b) => a.client_nom.localeCompare(b.client_nom, "fr"));
  return f;
}

function factureMatchesFiltresSupp(f) {
  if (currentFacturePaiementFiltre === "paye" && !(f.montant_restant <= 0 && f.montant_paye > 0)) return false;
  if (currentFacturePaiementFiltre === "partiel" && !(f.montant_paye > 0 && f.montant_restant > 0)) return false;
  if (currentFacturePaiementFiltre === "non_paye" && f.montant_paye > 0) return false;
  if (currentFactureEcheanceFiltre) {
    if (!f.date_echeance) return false;
    const jours = Math.round((new Date(f.date_echeance) - new Date()) / 86400000);
    if (currentFactureEcheanceFiltre === "retard" && !f.est_en_retard) return false;
    if (currentFactureEcheanceFiltre === "semaine" && !(jours >= 0 && jours <= 7)) return false;
    if (currentFactureEcheanceFiltre === "mois" && !(jours >= 0 && jours <= 31)) return false;
  }
  return true;
}

function renderFacturesListFiltered() {
  const list = document.getElementById("factures-list");
  let affichees = facturesCache;
  if (currentFactureFilter === "a_encaisser") {
    affichees = facturesCache
      .filter((f) => f.montant_restant > 0 && !["brouillon", "annulee"].includes(f.statut))
      .sort((a, b) => (a.date_echeance || "9999-99-99").localeCompare(b.date_echeance || "9999-99-99"));
  } else if (currentFactureFilter) {
    affichees = facturesCache.filter((f) => f.statut === currentFactureFilter);
  }
  affichees = factureSort(affichees.filter(factureMatchesFiltresSupp));
  if (affichees.length === 0) {
    // On distinguait mal les deux cas : un artisan sans la moindre facture
    // lisait « Aucune facture dans ce filtre » alors qu'aucun filtre n'etait
    // pose. C'est le genre de phrase qui fait douter de l'outil.
    list.innerHTML = facturesCache.length === 0
      ? etatVide(
          "Vos factures vivront ici.",
          "Émettez-les depuis un devis signé ou directement, suivez les encaissements, et voyez tout de suite ce qui a dépassé son échéance.",
          { action: "show-facture-form", libelle: "Créer une facture" },
        )
      : etatFiltre("Aucune facture ne correspond à ce filtre.");
    reapplyListSearch("factures-search", "#factures-list .list-row");
    return;
  }
  list.innerHTML = affichees.map(renderFactureCard).join("");
  reapplyListSearch("factures-search", "#factures-list .list-row");
}

async function loadFactures() {
  const list = document.getElementById("factures-list");
  const tresorerie = document.getElementById("factures-tresorerie");
  const newBtn = document.querySelector('[data-action="show-facture-form"]');
  const formContainer = document.getElementById("facture-form-container");

  if (!hasPlan("essentiel")) {
    if (newBtn) newBtn.hidden = true;
    if (formContainer) { formContainer.hidden = true; formContainer.innerHTML = ""; }
    tresorerie.innerHTML = "";
    list.innerHTML = renderUpgradeCard(
      "Facturation réservée aux abonnés",
      "Les factures, acomptes et suivi des paiements font partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  if (newBtn) newBtn.hidden = false;

  list.innerHTML = skeletonCards();
  try {
    const [factures, aRelancer] = await Promise.all([Api.listFactures(), Api.facturesARelancer()]);
    facturesDueIds = new Set(aRelancer.map((f) => f.id));
    facturesCache = factures;
    tresorerie.innerHTML = tresorerieHeaderHtml(factures);
    renderFacturesListFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

const FACTURE_TYPE_LABELS = { standard: "Standard", acompte: "Acompte", situation: "Situation", finale: "Finale", avoir: "Avoir" };

function buildPublicFrontendUrl(page, token) {
  const url = new URL(page, document.baseURI);
  url.searchParams.set("t", token);
  return url.href;
}

function erreurMontantPaiement(montant, soldeRestant) {
  const montantCentimes = Math.round(Number(montant) * 100);
  const soldeCentimes = Math.round(Number(soldeRestant) * 100);
  if (!Number.isFinite(montantCentimes) || montantCentimes <= 0) {
    return "Le montant du paiement doit être supérieur à zéro.";
  }
  if (!Number.isFinite(soldeCentimes) || soldeCentimes <= 0) {
    return "Cette facture est déjà totalement payée.";
  }
  if (montantCentimes > soldeCentimes) {
    return `Le montant du paiement dépasse le solde restant de ${fmtEuro(soldeRestant)}.`;
  }
  return null;
}

function renderFactureCard(f) {
  const meta = FACTURE_STATUT_META[f.statut] || { label: f.statut, badge: "badge-gray" };
  const isDue = facturesDueIds.has(f.id);
  const retard = joursRetard(f.date_echeance);

  // Memes actions, memes conditions et memes data-action/data-id/data-token
  // qu'avant : seule leur repartition entre le bouton primaire visible sur
  // la ligne et le menu "•••" change (voir setupActionMenus()).
  const items = [];
  if (f.statut === "brouillon") {
    items.push({ primaire: true, attrs: `data-action="envoyer-facture" data-id="${f.id}"`, label: "Marquer envoyée" });
  }
  if (f.montant_restant > 0 && f.statut !== "brouillon" && f.statut !== "annulee") {
    items.push({ primaire: true, attrs: `data-action="ajouter-paiement" data-id="${f.id}" data-restant="${f.montant_restant}"`, label: "+ Enregistrer un paiement" });
  }
  if (isDue) {
    // "Enregistrer un paiement" (ci-dessus) reste l'action dominante quand
    // les deux sont proposees ensemble (une seule couleur d'appel par
    // ligne) : Relancer ne devient primaire que si aucun paiement n'est
    // attendu.
    items.push({ primaire: f.montant_restant <= 0, attrs: `data-action="relancer-facture" data-id="${f.id}"`, label: "Relancer" });
  }
  if (f.token && f.statut !== "brouillon") {
    items.push({ attrs: `data-action="copier-lien-facture" data-token="${escapeHtml(f.token)}"`, label: "Copier le lien client" });
  }
  items.push({ attrs: `data-action="pdf-facture" data-id="${f.id}"`, label: "Télécharger le PDF" });
  items.push({ divider: true });
  items.push({ attrs: `data-action="delete-facture" data-id="${f.id}"`, label: "Archiver", danger: true });

  const primaireIdx = items.findIndex((it) => it.primaire);
  const primaireHtml = primaireIdx !== -1
    ? `<button type="button" class="btn-sm btn-sm-primary" ${items[primaireIdx].attrs}>${items[primaireIdx].label}</button>`
    : "";
  const menuHtml = items
    .filter((it, i) => i !== primaireIdx)
    .map((it) => it.divider
      ? '<div class="action-menu-divider"></div>'
      : `<button type="button"${it.danger ? ' class="is-danger"' : ""} ${it.attrs}>${it.label}</button>`)
    .join("");

  // Le montant qui compte vraiment d'un coup d'oeil : le reste du a
  // encaisser (ou le total une fois soldee) - meme valeur deja calculee.
  const montantCle = f.montant_restant > 0 ? fmtEuro(f.montant_restant) : fmtEuro(f.montant_ttc);
  const montantCleLabel = f.montant_restant > 0 ? "restant" : "soldée";

  // Colonnes "Paiement" et "Echeance" (voir 05-factures) : deux colonnes
  // reelles distinctes, au lieu d'un seul texte de contexte combine comme
  // avant - memes champs deja recus (f.montant_paye/.montant_restant/
  // .date_echeance), aucune donnee nouvelle.
  const paiementTxt = f.montant_paye > 0
    ? `${fmtEuro(f.montant_paye)} payé${f.montant_restant > 0 ? `, ${fmtEuro(f.montant_restant)} restant` : ""}`
    : "—";
  const echeanceTxt = retard !== null
    ? `${retard} j de retard`
    : (f.date_echeance ? "Éch. " + fmtDate(f.date_echeance) : "—");

  // Historique (paiements, relances) : releve seulement quand il y a
  // effectivement quelque chose a dire, sous la ligne plutot que dans une
  // colonne dense - meme donnee, juste repliee par defaut.
  const historique = [];
  if ((f.paiements || []).length > 0) {
    historique.push((f.paiements)
      .map((p) => `${fmtDate(p.date_paiement)} · ${fmtEuro(p.montant)} · ${p.moyen}${p.reference ? " · réf. " + escapeHtml(p.reference) : ""}`)
      .join(" — "));
  }
  if (f.nb_relances > 0) {
    historique.push(`${f.nb_relances} relance${f.nb_relances > 1 ? "s" : ""}${f.date_derniere_relance ? " · dernière le " + fmtDate(f.date_derniere_relance) : ""}`);
  }

  return `
  <div class="list-row list-row-facture ${f.est_en_retard ? "is-due" : ""}">
    <!-- Le bloc d'identite ouvre la facture en LECTURE : ses lignes et son
         historique de paiements n'etaient visibles nulle part. -->
    <div class="list-row-primary est-cliquable" data-action="voir-facture" data-id="${f.id}"
         role="button" tabindex="0" aria-label="Lire la facture ${escapeHtml(f.numero)} de ${escapeHtml(f.client_nom)}">
      <span class="crm-avatar">${escapeHtml(monogram(f.client_nom))}</span>
      <div class="list-row-primary-copy">
        <div class="list-row-title">${escapeHtml(f.client_nom)}</div>
        <div class="list-row-sub">${FACTURE_TYPE_LABELS[f.type] || f.type}</div>
      </div>
    </div>
    <div class="list-row-numero">${escapeHtml(f.numero)}</div>
    <div class="list-row-status"><span class="badge ${meta.badge}">${meta.label}</span></div>
    <div class="list-row-amount">${montantCle}<span class="list-row-amount-sub">${montantCleLabel}</span></div>
    <div class="list-row-paiement">${escapeHtml(paiementTxt)}</div>
    <div class="list-row-echeance${retard !== null ? " is-alert" : ""}">${escapeHtml(echeanceTxt)}</div>
    <div class="list-row-primary-action">${primaireHtml}</div>
    <div class="list-row-menu">
      <div class="action-menu">
        <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur cette facture">
          <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
        </button>
        <div class="action-menu-panel" role="menu">${menuHtml}</div>
      </div>
    </div>
    ${historique.length ? `<div class="list-row-banner item-meta">${historique.join(" · ")}</div>` : ""}
    <div id="paiement-form-${f.id}" class="list-row-expand"></div>
  </div>`;
}

// ---------------------------------------------------------------------
// DETAIL D'UNE FACTURE — « le reglement »
// ---------------------------------------------------------------------
// Meme constat que pour les devis avant qu'on leur donne un ecran de
// lecture : on pouvait envoyer une facture, la relancer, y enregistrer un
// paiement, telecharger son PDF - mais pas la LIRE. Ses lignes n'etaient
// visibles nulle part, et son historique de paiements etait comprime en
// une seule ligne de texte sous la ligne de liste.
//
// FactureOut porte `lignes` ET `paiements` depuis toujours : aucun appel
// supplementaire n'est necessaire.
//
// Ce qui distingue cet ecran de celui d'un devis : un devis raconte une
// negociation, une facture raconte un ENCAISSEMENT. Le bloc de reglement
// passe donc avant le document.

/** Le reglement : ce qui a ete encaisse, ce qui reste. C'est la seule
 *  question qu'on se pose en ouvrant une facture. La barre montre la part
 *  reglee ; le retard, quand il y en a, se compte en jours. */
function factureReglementHtml(f) {
  const paye = f.montant_paye || 0;
  const restant = f.montant_restant || 0;
  const pct = f.montant_ttc ? Math.min(100, Math.round((paye / f.montant_ttc) * 100)) : 0;
  const retard = factureAnciennete(f);
  const enRetard = retard !== null && retard > 0 && restant > 0;

  return `
  <div class="fact-reglement">
    <div class="fact-reglement-tete">
      <span class="fact-reglement-valeur${enRetard ? " est-retard" : ""}">${restant > 0 ? fmtEuro(restant) : fmtEuro(f.montant_ttc)}</span>
      <span class="fact-reglement-label">${restant > 0 ? "restent à encaisser" : "encaissés en totalité"}</span>
    </div>
    <div class="fact-jauge" role="img" aria-label="${pct} % réglé">
      <span class="fact-jauge-part" style="width:${pct}%"></span>
    </div>
    <p class="fact-reglement-note">
      ${paye > 0 ? `${fmtEuro(paye)} réglés sur ${fmtEuro(f.montant_ttc)} · ` : `Aucun paiement enregistré · `}
      ${f.date_echeance
        ? (enRetard
          ? `<strong class="est-retard">échéance dépassée de ${retard} j</strong>`
          : `échéance le ${fmtDate(f.date_echeance)}`)
        : "aucune échéance fixée"}
    </p>
  </div>`;
}

/** La vie de la facture. Comme pour un devis, les dates existantes
 *  suffisent - et les paiements s'y intercalent a leur place, ce que la
 *  ligne de liste ne pouvait pas montrer : on voit enfin qu'un acompte a
 *  ete verse AVANT la relance, ou l'inverse. */
function factureVieHtml(f) {
  const etapes = [];
  if (f.date_emission) etapes.push({ date: f.date_emission, label: "Facture émise" });
  if (f.date_envoi) etapes.push({ date: f.date_envoi, label: "Envoyée au client" });
  (f.paiements || []).forEach((p) => etapes.push({
    date: p.date_paiement,
    label: `Paiement de ${fmtEuro(p.montant)} · ${escapeHtml(p.moyen)}${p.reference ? ` · réf. ${escapeHtml(p.reference)}` : ""}`,
    fort: true,
  }));
  if (f.date_derniere_relance) {
    etapes.push({
      date: f.date_derniere_relance,
      label: f.nb_relances > 1 ? `Dernière relance (${f.nb_relances} au total)` : "Relance envoyée",
    });
  }
  if (!etapes.length) return `<p class="fiche-vide">Cette facture vient d'être créée.</p>`;

  etapes.sort((a, b) => new Date(a.date) - new Date(b.date));
  return `<ol class="devis-vie">${etapes.map((e) => `
    <li class="devis-vie-etape${e.fort ? " est-forte" : ""}">
      <time>${fmtDate(e.date)}</time>
      <span>${e.label}</span>
    </li>`).join("")}</ol>`;
}

function factureActionsHtml(f) {
  const actions = [];
  if (f.statut === "brouillon") actions.push({ p: true, a: `data-action="envoyer-facture" data-id="${f.id}"`, l: "Marquer envoyée" });
  if (f.montant_restant > 0 && f.statut !== "brouillon" && f.statut !== "annulee") {
    actions.push({ p: true, a: `data-action="ajouter-paiement" data-id="${f.id}" data-restant="${f.montant_restant}"`, l: "+ Enregistrer un paiement" });
  }
  if (facturesDueIds.has(f.id)) actions.push({ a: `data-action="relancer-facture" data-id="${f.id}"`, l: "Relancer" });
  if (f.token && f.statut !== "brouillon") actions.push({ a: `data-action="copier-lien-facture" data-token="${escapeHtml(f.token)}"`, l: "Copier le lien client" });
  actions.push({ a: `data-action="pdf-facture" data-id="${f.id}"`, l: "Télécharger le PDF" });
  return `<div class="fiche-actions">${actions
    .map((x) => `<button type="button" class="btn-sm${x.p ? " btn-sm-primary" : ""}" ${x.a}>${x.l}</button>`)
    .join("")}</div>`;
}

function showFactureDetail(factureId) {
  const f = facturesCache.find((x) => x.id === factureId);
  const panneau = document.getElementById("panel-facture");
  if (!panneau || !f) return;

  const meta = FACTURE_STATUT_META[f.statut] || { label: f.statut, badge: "badge-gray" };
  document.getElementById("facture-detail-titre").textContent = f.numero || `Facture #${f.id}`;
  document.getElementById("facture-detail-sous").textContent =
    `${f.client_nom} · ${FACTURE_TYPE_LABELS[f.type] || f.type}`;

  // Les lignes et les totaux sont ceux du document, dans la meme forme
  // qu'un devis : on relit la piece telle que le client la recoit.
  const lignes = f.lignes || [];
  const totaux = lignes.length
    ? devisTotaux(lignes, f.taux_tva, 0, 0)
    : { brut: f.montant_ht, remise: 0, remisePct: 0, ht: f.montant_ht,
        tva: Math.round((f.montant_ttc - f.montant_ht) * 100) / 100,
        tauxTva: f.taux_tva, ttc: f.montant_ttc, acompte: 0, acomptePct: 0 };

  document.getElementById("facture-detail-corps").innerHTML = `
    <div class="devis-detail-etat">
      <span class="badge ${meta.badge}">${escapeHtml(meta.label)}</span>
      ${f.est_en_retard ? '<span class="devis-detail-suivi is-alerte">En retard</span>' : ""}
    </div>

    ${factureReglementHtml(f)}
    ${factureActionsHtml(f)}
    <div id="paiement-form-${f.id}"></div>

    ${lignes.length ? ficheSection("Prestations facturées", devisLignesLectureHtml(lignes)) : ""}
    <div class="devis-detail-totaux">${devisTotalisateurHtml(totaux)}</div>

    ${f.notes ? ficheSection("Notes", `<p class="devis-detail-notes">${escapeHtml(f.notes)}</p>`) : ""}
    ${ficheSection("La vie de cette facture", factureVieHtml(f))}
  `;
  panneau.hidden = false;
  panneau.dataset.factureId = factureId;
  panneau.querySelector(".side-panel-close").focus();
}

function showPaiementForm(factureId, soldeRestant) {
  const container = document.getElementById(`paiement-form-${factureId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  const maximum = Number(soldeRestant).toFixed(2);
  // Le champ est PRE-REMPLI au solde restant. Un artisan qui enregistre un
  // paiement encaisse la totalite de ce qui reste du dans l'immense
  // majorite des cas ; lui faire ressaisir un montant qu'on lui affiche
  // juste a cote, c'est du travail rendu a la main, et une occasion de
  // faute de frappe sur un chiffre comptable. Le champ reste modifiable
  // pour les acomptes et les reglements partiels.
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <h3 class="form-box-titre">Enregistrer un paiement</h3>
      <div class="form-grid">
        <div>
          <label for="pay-montant-${factureId}">Montant (euros) *</label>
          <input type="number" step="0.01" min="0.01" max="${maximum}" id="pay-montant-${factureId}" value="${maximum}" required>
          <p class="champ-aide">Solde restant : ${fmtEuro(soldeRestant)}. Modifiable pour un règlement partiel.</p>
        </div>
        <div><label for="pay-date-${factureId}">Date</label><input type="date" id="pay-date-${factureId}" value="${today}"></div>
        <div>
          <label for="pay-moyen-${factureId}">Moyen</label>
          <select id="pay-moyen-${factureId}">
            <option value="virement">Virement</option>
            <option value="cheque">Chèque</option>
            <option value="especes">Espèces</option>
            <option value="cb">Carte bancaire</option>
            <option value="autre">Autre</option>
          </select>
        </div>
        <div><label for="pay-reference-${factureId}">Référence (optionnel)</label><input type="text" id="pay-reference-${factureId}" placeholder="N° chèque, réf. virement..."></div>
      </div>
      <p class="field-error" id="paiement-error-${factureId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-paiement" data-id="${factureId}">Enregistrer</button>
        <button type="button" class="btn-sm" data-action="cancel-paiement-form" data-id="${factureId}">Annuler</button>
      </div>
    </div>`;
}

function showFactureForm() {
  document.getElementById("facture-form-container").innerHTML = "";
  Promise.all([ensureClientsCache(), ensurePrestationsCache()]).then(() => {
    const container = document.getElementById("facture-form-container");
    if (clientsCache.length === 0) {
      container.innerHTML = `<div class="form-box"><p>Ajoutez d'abord un contact dans l'onglet <strong>Clients &amp; prospects</strong>.</p>
        <div class="form-actions"><button type="button" class="btn-sm" data-action="cancel-facture-form">Fermer</button></div></div>`;
      container.hidden = false;
      return;
    }
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouvelle facture</h3>
        <form id="facture-form">
          <div class="form-section">
            <div class="form-section-title">Client</div>
            <div class="form-grid">
              <div><label for="fa-client">Client *</label><select id="fa-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select></div>
            </div>
          </div>

          <div class="form-section">
            <div class="form-section-title">Détails</div>
            <div class="form-grid">
              <div>
                <label for="fa-type">Type</label>
                <select id="fa-type">
                  <option value="standard">Standard</option>
                  <option value="acompte">Acompte</option>
                  <option value="situation">Situation</option>
                  <option value="finale">Finale</option>
                  <option value="avoir">Avoir</option>
                </select>
              </div>
              <div>
                <label for="fa-tva">TVA</label>
                <select id="fa-tva"><option value="10">10% (rénovation)</option><option value="20">20% (neuf)</option></select>
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="form-section-title">Prestations</div>
            ${lignesEditorHtml("fa-lignes", null)}
          </div>

          <div class="doc-pied">
            <div class="doc-pied-conditions">
              <div class="form-section-title">Échéance</div>
              <div class="form-grid">
                <div><label for="fa-echeance">Date d'échéance</label><input type="date" id="fa-echeance"></div>
              </div>
            </div>
            <!-- Le meme totalisateur que sur le devis. Emettre une facture de
                 1 840 € sans voir le total avant de cliquer « Creer » etait la
                 seule incoherence de fond entre les deux ecrans. -->
            <div class="totalisateur-hote" aria-live="polite" aria-label="Totaux de la facture"></div>
          </div>

          <p class="field-error" id="facture-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Créer</button>
            <button type="button" class="btn-sm" data-action="cancel-facture-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    const formEl = document.getElementById("facture-form");
    attacherEditeurLignes(formEl);
    // Une facture n'a ni remise ni acompte : on ne passe que la TVA.
    brancherTotalisateur(formEl, "fa-lignes", { tva: "#fa-tva", remise: null, acompte: null });

    formEl.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("facture-form-error");
      errorBox.hidden = true;
      try {
        await Api.createFacture({
          client_id: parseInt(document.getElementById("fa-client").value, 10),
          type: document.getElementById("fa-type").value,
          taux_tva: parseFloat(document.getElementById("fa-tva").value),
          date_echeance: emptyToNull(document.getElementById("fa-echeance").value),
          lignes: lireLignes("fa-lignes"),
        });
        showToast("Facture créée.");
        container.hidden = true;
        container.innerHTML = "";
        loadFactures();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });
}

// Partagee entre les onglets (#facture-filters) et le menu deroulant
// "Statut" (voir 05-factures, qui montre les deux a la fois) : une seule
// source de verite (currentFactureFilter), les deux controles restent donc
// toujours synchronises plutot que de filtrer chacun dans son coin.
function activerFactureFiltreStatut(statut) {
  currentFactureFilter = statut;
  document.querySelectorAll("#facture-filters .filter-chip").forEach((c) => c.classList.toggle("active", c.dataset.statut === statut));
  const select = document.getElementById("factures-statut-filtre");
  if (select) select.value = statut;
  renderFacturesListFiltered();
}

function setupFacturesView() {
  document.getElementById("facture-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    activerFactureFiltreStatut(chip.dataset.statut);
  });
  document.getElementById("factures-statut-filtre").addEventListener("change", (e) => {
    activerFactureFiltreStatut(e.target.value);
  });
  document.getElementById("factures-paiement-filtre").addEventListener("change", (e) => {
    currentFacturePaiementFiltre = e.target.value;
    renderFacturesListFiltered();
  });
  document.getElementById("factures-echeance-filtre").addEventListener("change", (e) => {
    currentFactureEcheanceFiltre = e.target.value;
    renderFacturesListFiltered();
  });

  document.getElementById("factures-sort").addEventListener("change", (e) => {
    currentFactureSort = e.target.value;
    renderFacturesListFiltered();
  });

  document.querySelector('[data-action="show-facture-form"]').addEventListener("click", showFactureForm);
  document.getElementById("facture-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-facture-form"]')) {
      const container = document.getElementById("facture-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  // Un seul gestionnaire pour la liste ET le panneau de lecture : les
  // actions se comportent pareil des deux cotes, sans renommage.
  const surActionFacture = async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "voir-facture") { showFactureDetail(id); return; }
    if (btn.dataset.action === "close-facture-detail") {
      document.getElementById("panel-facture").hidden = true;
      return;
    }

    if (btn.dataset.action === "envoyer-facture") {
      await withErrorToast(async () => {
        await Api.updateFacture(id, { statut: "envoyee" });
        showToast("Facture marquée envoyée.");
        loadFactures();
      });
    } else if (btn.dataset.action === "ajouter-paiement") {
      showPaiementForm(id, parseFloat(btn.dataset.restant));
    } else if (btn.dataset.action === "cancel-paiement-form") {
      document.getElementById(`paiement-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-paiement") {
      const montantInput = document.getElementById(`pay-montant-${id}`);
      const montant = montantInput.value;
      const datePaiement = document.getElementById(`pay-date-${id}`).value;
      const moyen = document.getElementById(`pay-moyen-${id}`).value;
      const reference = document.getElementById(`pay-reference-${id}`).value;
      const errorBox = document.getElementById(`paiement-error-${id}`);
      const erreurMontant = erreurMontantPaiement(montant, montantInput.max);
      if (erreurMontant) {
        errorBox.hidden = false;
        errorBox.textContent = erreurMontant;
        return;
      }
      try {
        await Api.ajouterPaiement(id, { montant: parseFloat(montant), date_paiement: datePaiement, moyen, reference: emptyToNull(reference) });
        showToast("Paiement enregistre.");
        loadFactures();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "delete-facture") {
      if (!(await confirmDialog("Archiver cette facture ? Elle disparaitra de vos listes actives mais reste conservee (document financier).", { confirmLabel: "Archiver", danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteFacture(id);
        showToast("Facture archivee.");
        loadFactures();
      });
    } else if (btn.dataset.action === "pdf-facture") {
      await withErrorToast(() => ouvrirPdf(`/factures/${id}/pdf`));
    } else if (btn.dataset.action === "relancer-facture") {
      await withErrorToast(async () => {
        await Api.relancerFacture(id);
        showToast("Relance enregistree.");
        loadFactures();
      });
    } else if (btn.dataset.action === "copier-lien-facture") {
      const url = buildPublicFrontendUrl("facture-public.html", btn.dataset.token);
      try {
        await navigator.clipboard.writeText(url);
        showToast("Lien copié. Envoyez-le à votre client par email ou SMS.");
      } catch (err) {
        showToast(url, false);
      }
    }
  };
  document.getElementById("factures-list").addEventListener("click", surActionFacture);
  const panneauFacture = document.getElementById("panel-facture");
  panneauFacture.addEventListener("click", (e) => {
    if (e.target === panneauFacture) { panneauFacture.hidden = true; return; }
    surActionFacture(e);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !panneauFacture.hidden) panneauFacture.hidden = true;
  });
  document.getElementById("factures-list").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const cible = e.target.closest('[data-action="voir-facture"]');
    if (!cible) return;
    e.preventDefault();
    showFactureDetail(parseInt(cible.dataset.id, 10));
  });
}

// ===================== Contrats recurrents =====================
const CONTRAT_FREQUENCE_LABELS = { mensuel: "Mensuelle", trimestriel: "Trimestrielle", annuel: "Annuelle" };
const CONTRAT_STATUT_META = {
  actif: { label: "Actif", badge: "badge-green" },
  suspendu: { label: "Suspendu", badge: "badge-orange" },
  resilie: { label: "Résilié", badge: "badge-gray" },
};
let contratsCache = [];

function feedbackGenerationContrat(result) {
  const statut = result && result.email_statut;
  const messagesParStatut = {
    envoye: "Facture générée et envoyée par email.",
    non_configure: "Facture générée. L'email n'a pas été envoyé car le service email n'est pas configuré.",
    sans_destinataire: "Facture générée. L'email n'a pas été envoyé car ce client n'a pas d'adresse email.",
    echec: "Facture générée. L'email n'a pas pu être envoyé par le fournisseur.",
  };
  return {
    message: messagesParStatut[statut] || (result && result.message) || "Facture générée. Le statut de l'envoi email est indisponible.",
    isError: statut === "echec",
  };
}

async function loadContrats() {
  const list = document.getElementById("contrats-list");
  const newBtn = document.querySelector('[data-action="show-contrat-form"]');
  const formContainer = document.getElementById("contrat-form-container");
  if (!hasPlan("pro")) {
    contratsCache = [];
    newBtn.hidden = true;
    formContainer.hidden = true;
    formContainer.innerHTML = "";
    list.innerHTML = renderUpgradeCard(
      "Contrats récurrents réservés au plan Pro",
      "La facturation automatique des contrats d'entretien/maintenance fait partie du plan Pro.",
      "pro"
    );
    return;
  }
  newBtn.hidden = false;
  list.innerHTML = skeletonCards();
  try {
    const contrats = await Api.listContrats();
    contratsCache = contrats;
    if (contrats.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun contrat récurrent. Créez votre premier contrat pour planifier sa facturation.</div>';
      return;
    }
    list.innerHTML = contrats.map(renderContratCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderContratCard(c) {
  const meta = CONTRAT_STATUT_META[c.statut] || { label: c.statut, badge: "badge-gray" };
  return `
  <div class="item-card enterprise-record">
    <div class="enterprise-record-main">
      <div class="item-title">${escapeHtml(c.titre)}</div>
      <div class="item-sub">${escapeHtml(c.client_nom)} · ${fmtEuro(c.montant_ht)} HT · TVA ${c.taux_tva}% · ${CONTRAT_FREQUENCE_LABELS[c.frequence] || c.frequence}</div>
      <div class="item-meta">
        Prochaine échéance : ${fmtDate(c.prochaine_echeance)}
        ${c.derniere_generation ? ` · Dernière facture générée le ${fmtDate(c.derniere_generation)}` : ""}
        · ${c.nb_factures_generees} facture${c.nb_factures_generees > 1 ? "s" : ""} générée${c.nb_factures_generees > 1 ? "s" : ""}
      </div>
    </div>
    <span class="badge enterprise-record-status ${meta.badge}">${meta.label}</span>
    <div class="item-actions enterprise-record-actions">
      <button type="button" class="btn-sm" data-action="edit-contrat" data-id="${c.id}">Modifier</button>
      ${c.statut === "actif" ? `<button type="button" class="btn-sm btn-sm-primary" data-action="generer-contrat" data-id="${c.id}">Générer maintenant</button>` : ""}
      ${c.statut === "actif" ? `<button type="button" class="btn-sm" data-action="suspendre-contrat" data-id="${c.id}">Suspendre</button>` : ""}
      ${c.statut === "suspendu" ? `<button type="button" class="btn-sm btn-sm-primary" data-action="reactiver-contrat" data-id="${c.id}">Réactiver</button>` : ""}
      ${c.statut !== "resilie" ? `<button type="button" class="btn-sm btn-sm-danger" data-action="resilier-contrat" data-id="${c.id}">Résilier</button>` : ""}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-contrat" data-id="${c.id}">Supprimer</button>
    </div>
  </div>`;
}

async function showContratForm(contrat = null) {
  const container = document.getElementById("contrat-form-container");
  const isEdit = !!contrat;
  await ensureClientsCache();
  if (!isEdit && clientsCache.length === 0) {
      container.innerHTML = `<div class="form-box"><p>Vous n'avez pas encore de client. Ajoutez d'abord un contact dans l'onglet <strong>Clients &amp; prospects</strong>.</p>
        <div class="form-actions"><button type="button" class="btn-sm" data-action="cancel-contrat-form">Fermer</button></div></div>`;
      container.hidden = false;
      return;
  }
  const today = new Date().toISOString().slice(0, 10);
  const echeance = isEdit ? contrat.prochaine_echeance : today;
  container.innerHTML = `
      <div class="form-box">
        <h3>${isEdit ? "Modifier le contrat récurrent" : "Nouveau contrat récurrent"}</h3>
        <form id="contrat-form">
          <div class="form-grid">
            <div><label for="ct-titre">Titre *</label><input type="text" id="ct-titre" required placeholder="Ex: Contrat d'entretien chaudière" value="${isEdit ? escapeHtml(contrat.titre) : ""}"></div>
            ${isEdit
              ? `<div><label>Client</label><input type="text" value="${escapeHtml(contrat.client_nom)}" disabled></div>`
              : `<div><label for="ct-client">Client *</label><select id="ct-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select></div>`}
            <div><label for="ct-montant">Montant HT par échéance *</label><input type="number" step="0.01" min="0.01" id="ct-montant" required value="${isEdit ? contrat.montant_ht : ""}"></div>
            <div>
              <label for="ct-tva">TVA</label>
              <select id="ct-tva"><option value="10" ${!isEdit || contrat.taux_tva === 10 ? "selected" : ""}>10% (rénovation)</option><option value="20" ${isEdit && contrat.taux_tva === 20 ? "selected" : ""}>20% (neuf)</option></select>
            </div>
            <div>
              <label for="ct-frequence">Fréquence</label>
              <select id="ct-frequence">${Object.entries(CONTRAT_FREQUENCE_LABELS).map(([v, l]) => `<option value="${v}" ${(!isEdit && v === "mensuel") || (isEdit && contrat.frequence === v) ? "selected" : ""}>${l}</option>`).join("")}</select>
            </div>
            <div><label for="ct-echeance">${isEdit ? "Prochaine échéance" : "Première échéance"} *</label><input type="date" id="ct-echeance" required value="${echeance}"></div>
          </div>
          <p class="field-error" id="contrat-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">${isEdit ? "Enregistrer" : "Créer"}</button>
            <button type="button" class="btn-sm" data-action="cancel-contrat-form">Annuler</button>
          </div>
        </form>
      </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("contrat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("contrat-form-error");
    errorBox.hidden = true;
    const payload = {
      titre: document.getElementById("ct-titre").value.trim(),
      montant_ht: parseFloat(document.getElementById("ct-montant").value),
      taux_tva: parseFloat(document.getElementById("ct-tva").value),
      frequence: document.getElementById("ct-frequence").value,
      prochaine_echeance: document.getElementById("ct-echeance").value,
    };
    if (!isEdit) payload.client_id = parseInt(document.getElementById("ct-client").value, 10);
    try {
      if (isEdit) {
        await Api.updateContrat(contrat.id, payload);
        showToast("Contrat mis à jour.");
      } else {
        await Api.createContrat(payload);
        showToast("Contrat créé. Sa première facture sera générée à l'échéance prévue.");
      }
      container.hidden = true;
      container.innerHTML = "";
      loadContrats();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

function setupContratsView() {
  document.querySelector('[data-action="show-contrat-form"]').addEventListener("click", () => showContratForm());

  document.getElementById("contrat-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-contrat-form"]')) {
      const container = document.getElementById("contrat-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("contrats-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "edit-contrat") {
      const contrat = contratsCache.find((item) => item.id === id);
      if (contrat) await showContratForm(contrat);
    } else if (btn.dataset.action === "generer-contrat") {
      await withErrorToast(async () => {
        btn.disabled = true;
        try {
          const result = await Api.genererContrat(id);
          const feedback = feedbackGenerationContrat(result);
          showToast(feedback.message, feedback.isError);
          await loadContrats();
        } catch (err) {
          btn.disabled = false;
          throw err;
        }
      });
    } else if (btn.dataset.action === "suspendre-contrat") {
      await withErrorToast(async () => {
        await Api.updateContrat(id, { statut: "suspendu" });
        showToast("Contrat suspendu : plus aucune facture ne sera générée tant qu'il n'est pas réactivé.");
        loadContrats();
      });
    } else if (btn.dataset.action === "reactiver-contrat") {
      await withErrorToast(async () => {
        await Api.updateContrat(id, { statut: "actif" });
        showToast("Contrat réactivé.");
        loadContrats();
      });
    } else if (btn.dataset.action === "resilier-contrat") {
      if (!(await confirmDialog("Résilier ce contrat ? Plus aucune facture ne sera générée.", { danger: true }))) return;
      await withErrorToast(async () => {
        await Api.updateContrat(id, { statut: "resilie" });
        showToast("Contrat résilié.");
        loadContrats();
      });
    } else if (btn.dataset.action === "delete-contrat") {
      if (!(await confirmDialog("Supprimer ce contrat ? Les factures déjà générées resteront conservées.", { confirmLabel: "Supprimer", danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteContrat(id);
        showToast("Contrat supprimé.");
        loadContrats();
      });
    }
  });
}

// ===================== Chantiers =====================
// "A surveiller" : budget deja consomme au-dela de 85% - signal deja present
// sur l'objet chantier (c.budget/c.total_depenses), pas de calcul metier
// nouveau, juste un seuil d'affichage. Fonction partagee entre la bande de
// KPI et le filtre par onglet pour ne jamais avoir deux definitions.
// Retard : la seule definition du produit. `date_fin_prevue` est renvoyee
// par ChantierOut depuis toujours, mais n'etait exposee nulle part dans
// l'interface - ni en creation, ni en modification, ni en affichage. Aucun
// chantier ne pouvait donc etre signale en retard. Elle est desormais
// saisissable (voir le formulaire de creation et showChantierEditForm).
function chantierJoursRetard(c) {
  if (["termine", "facture", "paye"].includes(c.statut) || !c.date_fin_prevue) return 0;
  const fin = new Date(String(c.date_fin_prevue).slice(0, 10) + "T00:00:00");
  if (isNaN(fin)) return 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((today - fin) / 86400000));
}

// La prochaine action. L'ancienne fiche lisait `c.prochaine_action`, un
// champ qui existe sur un CLIENT mais PAS sur un chantier : ChantierOut ne
// le renvoie pas. La ligne affichait donc "Aucune action planifiee" pour
// tous les chantiers, en permanence. Elle est maintenant deduite de donnees
// qui existent vraiment - les taches ouvertes, les dates et le statut.
// L'ordre des cas est celui de la vie du chantier : ce qui bloque la
// cloture passe avant ce qui reste a faire sur le terrain.
function chantierProchaineAction(c) {
  const fmtCourt = (iso) => new Date(String(iso).slice(0, 10) + "T00:00:00")
    .toLocaleDateString("fr-FR", { day: "numeric", month: "short" });

  if (c.statut === "termine") return { texte: "Clôturer le chantier" };
  if (["facture", "paye"].includes(c.statut) && !c.date_reception) return { texte: "Enregistrer la réception" };

  const ouvertes = (c.taches || []).filter((t) => t.statut !== "faite");
  if (ouvertes.length) {
    const datees = ouvertes.filter((t) => t.echeance).sort((a, b) => a.echeance.localeCompare(b.echeance));
    const t = datees[0] || ouvertes[0];
    if (!t.echeance) return { texte: t.titre };
    const retard = Math.round((new Date().setHours(0, 0, 0, 0) - new Date(t.echeance + "T00:00:00")) / 86400000);
    return { texte: t.titre, quand: retard > 0 ? `retard ${retard} j` : fmtCourt(t.echeance), enRetard: retard > 0 };
  }

  if (c.statut === "a_preparer") {
    return c.date_debut
      ? { texte: "Démarrage du chantier", quand: fmtCourt(c.date_debut) }
      : { texte: "Planifier le démarrage" };
  }
  // Pas de `quand` ici : la date de fin a deja sa propre colonne juste a
  // cote. La repeter donnait "Livraison prevue 27 aout" a gauche et
  // "27/08/2026" a droite - la meme information deux fois sur la meme
  // ligne, ce qui saute aux yeux des que les deux colonnes se retrouvent
  // cote a cote en mobile.
  if (c.date_fin_prevue) {
    return { texte: "Livraison prévue", enRetard: chantierJoursRetard(c) > 0 };
  }
  if (["termine", "facture", "paye"].includes(c.statut)) return { texte: "Dossier clôturé", vide: true };
  return { texte: "Aucune action planifiée", vide: true };
}

function chantierEstASurveiller(c) {
  if (["termine", "facture", "paye", "a_preparer"].includes(c.statut)) return false;
  const consomme = c.budget && c.total_depenses ? (c.total_depenses / c.budget) * 100 : null;
  return consomme !== null && consomme >= 85;
}

// ---------------------------------------------------------------------
// CHANTIERS — la situation, en deux lignes
// ---------------------------------------------------------------------
// La page ouvrait sur quatre cartes de KPI, comme presque toutes les
// autres. Ici la composition ne reprend PAS la grande phrase de l'accueil
// ni celle de Devis : ce n'est pas une page ou l'on decide d'un geste,
// c'est une page ou l'on surveille une charge. Deux lignes typographiees
// suffisent - la composition du portefeuille, puis ce qui derape.
//
// Les cartes elles-memes portent deja la comparaison avancement/budget,
// chantier par chantier. L'en-tete n'a donc qu'a dire combien il y en a
// et lesquels sortent des clous.

function chantiersKpiBandHtml(chantiers) {
  if (!chantiers.length) return "";

  const actifs = chantiers.filter((c) => !["a_preparer", "termine", "facture", "paye"].includes(c.statut));
  const aPreparer = chantiers.filter((c) => c.statut === "a_preparer");
  const enPause = actifs.filter((c) => c.statut === "en_pause");
  const enCours = actifs.filter((c) => c.statut !== "en_pause");
  const ouverts = actifs.length + aPreparer.length;

  const enRetard = chantiers.filter((c) => chantierJoursRetard(c) > 0);
  const retardMax = enRetard.reduce((m, c) => Math.max(m, chantierJoursRetard(c)), 0);
  const depasses = chantiers.filter((c) => c.budget && (c.total_depenses || 0) > c.budget);
  const tendus = chantiers.filter((c) => chantierEstASurveiller(c) && !depasses.includes(c));
  const margeTotale = chantiers.reduce((s, c) => {
    const m = c.marge_reelle !== null && c.marge_reelle !== undefined ? c.marge_reelle : c.marge_estimee;
    return s + (m || 0);
  }, 0);

  // La charge : de quoi est fait le portefeuille ouvert.
  const charge = [`<strong>${ouverts}</strong> chantier${ouverts > 1 ? "s" : ""} ouvert${ouverts > 1 ? "s" : ""}`];
  if (enCours.length) charge.push(`${enCours.length} en cours`);
  if (aPreparer.length) charge.push(`${aPreparer.length} à préparer`);
  if (enPause.length) charge.push(`${enPause.length} en pause`);

  // Les signaux : uniquement ce qui sort des clous. Un compteur a zero n'a
  // rien a dire, il ne s'affiche pas.
  const signaux = [];
  if (enRetard.length) {
    signaux.push(`<strong class="est-retard">${enRetard.length}</strong> en retard${retardMax ? `, jusqu'à ${retardMax} j` : ""}`);
  }
  if (depasses.length) signaux.push(`<strong class="est-retard">${depasses.length}</strong> au-delà du budget`);
  if (tendus.length) signaux.push(`<strong class="est-tendu">${tendus.length}</strong> à surveiller`);
  if (margeTotale) signaux.push(`marge prévisionnelle <strong>${fmtEuro(margeTotale)}</strong>`);
  if (!enRetard.length && !depasses.length && !tendus.length) signaux.unshift("Tous dans les clous");

  return `
  <section class="chantiers-situation">
    <p class="chantiers-charge">${charge.join(" · ")}</p>
    <p class="chantiers-signaux">${signaux.join(" · ")}</p>
  </section>`;
}

let currentChantierFilter = ""; // "" | a_preparer | en_cours | a_surveiller | termine

// Certains onglets regroupent plusieurs vrais statuts (ex. "En cours" =
// planifie+en_cours+en_pause, "Terminés" = termine+facture+paye) ou une
// condition calculee ("À surveiller", voir chantierEstASurveiller) plutot
// qu'un statut unique - comme le fait deja la bande de KPI juste au-dessus.
function chantierMatchesFilter(c, filtre) {
  if (!filtre) return true;
  if (filtre === "a_preparer") return c.statut === "a_preparer";
  if (filtre === "en_cours") return !["a_preparer", "termine", "facture", "paye"].includes(c.statut);
  if (filtre === "a_surveiller") return chantierEstASurveiller(c);
  if (filtre === "termine") return ["termine", "facture", "paye"].includes(c.statut);
  return true;
}

let currentChantierSort = "risque";
let currentChantierAvancement = "";
let currentChantierClient = "";
let currentChantierRecherche = "";

// Tri purement client sur des champs deja recus (c.date_debut, c.budget,
// c.titre) - aucune donnee nouvelle, juste un reordonnancement de
// chantiersCache avant le rendu. .slice() : ne jamais trier le tableau
// source en place (chantiersKpiBandHtml et le compteur par onglet lisent
// le meme chantiersCache juste avant).
//
// Il y avait ici DEUX listes de tri concurrentes : `chantiers-sort` et
// `chantiers-priorite-tri`. La seconde etait testee en premier, donc des
// qu'elle etait renseignee elle ecrasait silencieusement le choix fait
// dans la premiere - qui restait pourtant affiche a l'ecran. Elles sont
// fusionnees en une seule dimension : aucune option n'est perdue, mais le
// resultat correspond enfin a ce qui est selectionne.
function chantierSort(chantiers) {
  const c = chantiers.slice();
  if (currentChantierSort === "progression") return c.sort((a, b) => (b.progression || 0) - (a.progression || 0));
  if (currentChantierSort === "budget_desc") return c.sort((a, b) => (b.budget || 0) - (a.budget || 0));
  if (currentChantierSort === "titre_asc") return c.sort((a, b) => a.titre.localeCompare(b.titre, "fr"));
  if (currentChantierSort === "date_debut_asc") return c.sort((a, b) => (a.date_debut || "").localeCompare(b.date_debut || ""));
  if (currentChantierSort === "date_debut_desc") return c.sort((a, b) => (b.date_debut || "").localeCompare(a.date_debut || ""));
  // "risque", par defaut : le retard d'abord, puis la tension budgetaire.
  const score = (x) => chantierJoursRetard(x) * 10 + (chantierEstASurveiller(x) ? 5 : 0);
  return c.sort((a, b) => score(b) - score(a) || (b.date_debut || "").localeCompare(a.date_debut || ""));
}

// La recherche porte sur ce que l'utilisateur voit et retient : le nom du
// chantier, le client, l'adresse. Elle passait auparavant par le masquage
// generique de reapplyListSearch, qui compare le textContent de la CARTE
// ENTIERE - donc aussi "Budget consomme", "Voir le chantier" ou le libelle
// d'un statut. Taper "note" faisait disparaitre des chantiers au hasard,
// et la liste se vidait sans rien expliquer.
function chantierMatchesRecherche(c, q) {
  if (!q) return true;
  return [c.titre, c.client_nom, c.adresse].filter(Boolean).join(" ").toLowerCase().includes(q);
}

function renderChantiersListFiltered() {
  const list = document.getElementById("chantiers-list");
  ["", "a_preparer", "en_cours", "a_surveiller", "termine"].forEach((f) => {
    const el = document.querySelector(`#chantier-filters [data-statut="${f}"] .filter-chip-count`);
    if (el) el.textContent = `(${chantiersCache.filter((c) => chantierMatchesFilter(c, f)).length})`;
  });
  const q = currentChantierRecherche.trim().toLowerCase();
  const filtres = chantierSort(chantiersCache.filter((c) => {
    if (!chantierMatchesFilter(c, currentChantierFilter)) return false;
    const progression = Number(c.progression) || 0;
    if (currentChantierAvancement === "debut" && progression > 25) return false;
    if (currentChantierAvancement === "milieu" && (progression <= 25 || progression > 75)) return false;
    if (currentChantierAvancement === "fin" && progression <= 75) return false;
    if (currentChantierClient && String(c.client_id) !== currentChantierClient) return false;
    return chantierMatchesRecherche(c, q);
  }));

  if (!filtres.length) {
    list.innerHTML = `<div class="empty-state">${q
      ? `Aucun chantier ne correspond à « ${escapeHtml(currentChantierRecherche.trim())} » dans cette sélection.`
      : "Aucun chantier dans cet onglet."}</div>`;
    return;
  }
  // Grille, pas empilement : c'est ce qui fait tenir trente chantiers en
  // une dizaine de rangees au lieu de trente. Les cartes se rangent
  // d'elles-memes selon la largeur disponible (voir .chantier-grille).
  list.innerHTML = `<div class="chantier-grille">${filtres.map(renderChantierCard).join("")}</div>`;
  focusChantierCard();
}

async function loadChantiers() {
  const kpiBand = document.getElementById("chantiers-kpi-band");
  const list = document.getElementById("chantiers-list");
  const newBtn = document.querySelector('[data-action="show-chantier-form"]');
  const formContainer = document.getElementById("chantier-form-container");

  if (!hasPlan("essentiel")) {
    if (kpiBand) kpiBand.innerHTML = "";
    newBtn.hidden = true;
    formContainer.hidden = true;
    formContainer.innerHTML = "";
    list.innerHTML = renderUpgradeCard(
      "Chantiers réservés aux abonnés",
      "Le suivi de chantier (photos et notes avant/pendant/après) fait partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  newBtn.hidden = false;

  list.innerHTML = skeletonCards();
  try {
    const chantiers = await Api.listChantiers();
    chantiersCache = chantiers;
    const clientSelect = document.getElementById("chantiers-client-filtre");
    if (clientSelect) {
      const clients = [...new Map(chantiers.filter((c) => c.client_id).map((c) => [c.client_id, c.client_nom || `Client ${c.client_id}`])).entries()];
      clientSelect.innerHTML = '<option value="">Client</option>' + clients.map(([id, nom]) => `<option value="${id}">${escapeHtml(nom)}</option>`).join("");
      clientSelect.value = currentChantierClient;
    }
    if (kpiBand) kpiBand.innerHTML = chantiers.length ? chantiersKpiBandHtml(chantiers) : "";
    if (chantiers.length === 0) {
      list.innerHTML = etatVide(
        "Vos chantiers vivront ici.",
        "Avancement, budget consommé, prochaine action : chaque chantier tient sur une carte, et celles qui dérapent se voient sans qu'on les cherche.",
        { action: "show-chantier-form", libelle: "Créer un chantier" },
      );
      return;
    }
    renderChantiersListFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function focusChantierCard() {
  if (!chantierFocusId) return;
  const card = document.querySelector(`[data-chantier-id="${chantierFocusId}"]`);
  if (!card) return;
  chantierFocusId = null;
  card.classList.add("is-focused");
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => card.classList.remove("is-focused"), 3000);
}

function ouvrirChantierDepuisPlanning(chantierId) {
  chantierFocusId = Number(chantierId);
  switchView("chantiers");
}

function rentabiliteHtml(c) {
  if (c.total_depenses === 0 && c.montant_facture === null && !c.total_heures) return "";
  // Le trait d'union servait de « rien » ; c'est le cadratin qui joue ce
  // role partout ailleurs dans le produit, et fmtEuro le rend deja seul.
  const margeTxt = c.marge_reelle !== null
    ? `<span class="${c.marge_reelle < 0 ? "est-negatif" : ""}">${fmtEuro(c.marge_reelle)}</span>`
    : "—";
  const depensesLabel = c.cout_main_oeuvre !== null
    ? `${fmtEuro(c.total_depenses)} + ${fmtEuro(c.cout_main_oeuvre)} main d'oeuvre`
    : fmtEuro(c.total_depenses);
  // Le dernier endroit du produit ou survivait la bande de quatre cartes
  // encadrees en ouverture de bloc - la figure que la direction artistique
  // proscrit en premier. Elle etait d'autant plus voyante ici que trois de
  // ses quatre cases affichent un tiret tant que rien n'est facture : une
  // rangee aux trois quarts vide, en cadres. Les chiffres reviennent au
  // meme geste que partout ailleurs : un libelle, la valeur, un filet.
  return `
    <div class="dash-chiffres chantier-chiffres">
      ${[["Dépenses", depensesLabel, ""],
         ["Facturé", fmtEuro(c.montant_facture), ""],
         ["Encaissé", fmtEuro(c.montant_encaisse), ""],
         ["Marge réelle", margeTxt, ""]]
        .map(([label, valeur, note]) => `
        <div class="dash-chiffre">
          <span class="dash-chiffre-label">${label}</span>
          <span class="dash-chiffre-valeur">${valeur}</span>
          ${note ? `<span class="dash-chiffre-note">${note}</span>` : ""}
        </div>`).join("")}
    </div>`;
}

function heuresHtml(c) {
  if (!c.heures || c.heures.length === 0) return "";
  const parIntervenant = {};
  for (const h of c.heures) {
    parIntervenant[h.nom_intervenant] = (parIntervenant[h.nom_intervenant] || 0) + parseFloat(h.duree_heures);
  }
  const resume = Object.entries(parIntervenant)
    .map(([nom, heures]) => `<div class="item-sub">${escapeHtml(nom)} · ${heures.toFixed(2).replace(/\.00$/, "")}h</div>`)
    .join("");
  const totalTxt = `${c.total_heures.toFixed(2).replace(/\.00$/, "")}h au total${c.cout_main_oeuvre !== null ? " · " + fmtEuro(c.cout_main_oeuvre) + " de main d'oeuvre" : ""}`;
  const detail = c.heures
    .map((h) => `
      <div class="item-sub" style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <span>${fmtDate(h.date_travail)} · ${escapeHtml(h.nom_intervenant)} · ${parseFloat(h.duree_heures).toFixed(2).replace(/\.00$/, "")}h${h.cout !== null ? " · " + fmtEuro(h.cout) : ""}${h.note ? " · " + escapeHtml(h.note) : ""}</span>
        ${c.finances_verrouillees ? "" : `<span style="display:flex;gap:4px;flex-shrink:0;">
          <button type="button" class="btn-sm" style="padding:2px 8px;" data-action="edit-heure" data-id="${c.id}" data-heure-id="${h.id}">Modifier</button>
          <button type="button" class="btn-sm btn-sm-danger" style="padding:2px 8px;" data-action="delete-heure" data-id="${c.id}" data-heure-id="${h.id}" title="Supprimer" aria-label="Supprimer cette entrée d'heures">&times;</button>
        </span>`}
      </div>`)
    .join("");
  return `<div class="dash-section" style="margin:12px 0;">
    <h3 style="font-size:0.88rem;">Heures de main d'oeuvre</h3>
    <div class="item-sub" style="font-weight:700;margin-bottom:4px;">${totalTxt}</div>
    ${detail}
  </div>`;
}

function showHeuresForm(chantierId, heure = null) {
  const container = document.getElementById(`heures-form-${chantierId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  const membreOptions = equipeCache.map((m) => `<option value="${m.id}" data-nom="${escapeHtml(m.nom)}" ${heure && heure.membre_id === m.id ? "selected" : ""}>${escapeHtml(m.nom)}</option>`).join("");
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div>
          <label for="heure-membre-${chantierId}">Intervenant</label>
          <select id="heure-membre-${chantierId}">
            <option value="" ${!heure || !heure.membre_id ? "selected" : ""}>Autre / vous-même...</option>
            ${membreOptions}
          </select>
        </div>
        <div id="heure-nom-libre-wrap-${chantierId}">
          <label for="heure-nom-${chantierId}">Nom (si "Autre")</label>
          <input type="text" id="heure-nom-${chantierId}" value="${escapeHtml(heure && !heure.membre_id ? heure.nom_intervenant : "")}" placeholder="Ex: Vous-même, sous-traitant...">
        </div>
        <div><label for="heure-duree-${chantierId}">Durée (heures) *</label><input type="number" step="0.25" min="0.25" id="heure-duree-${chantierId}" value="${heure ? escapeHtml(heure.duree_heures) : ""}" placeholder="Ex: 6.5"></div>
        <div><label for="heure-date-${chantierId}">Date</label><input type="date" id="heure-date-${chantierId}" value="${heure ? escapeHtml(heure.date_travail) : today}"></div>
        <div><label for="heure-taux-${chantierId}">Coût horaire chargé (optionnel)</label><input type="number" step="0.01" min="0" id="heure-taux-${chantierId}" value="${heure && heure.taux_horaire !== null ? escapeHtml(heure.taux_horaire) : ""}" placeholder="Ex: 35"></div>
        <div><label for="heure-note-${chantierId}">Note (optionnel)</label><input type="text" id="heure-note-${chantierId}" value="${escapeHtml(heure && heure.note ? heure.note : "")}" placeholder="Ex: pose carrelage"></div>
      </div>
      <p class="field-error" id="heures-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-heures" data-id="${chantierId}" ${heure ? `data-heure-id="${heure.id}"` : ""}>${heure ? "Enregistrer" : "Ajouter"}</button>
        <button type="button" class="btn-sm" data-action="cancel-heures-form" data-id="${chantierId}">Annuler</button>
      </div>
    </div>`;
}

// Meme paire de champs et meme seuil (85%) que "A surveiller" dans
// chantiersKpiBandHtml (bande de KPI de la page Chantiers) - ici affiche par
// chantier au lieu d'etre agrege. Le sens des couleurs est invense de
// progressionHtml() : un budget CONSOMME eleve est un signal d'alerte
// (rouge), pas un signal positif.
function budgetConsommeHtml(c) {
  if (!c.budget || c.total_depenses === null || c.total_depenses === undefined) return "";
  const pct = Math.round((c.total_depenses / c.budget) * 100);
  const niveau = pct >= 85 ? "bas" : pct >= 60 ? "moyen" : "haut";
  return `
    <div class="chantier-progress">
      <div class="chantier-progress-row"><span>Budget consommé</span><strong>${pct}%</strong></div>
      <div class="sante-barre"><div class="remplissage niveau-${niveau}" style="width:${Math.min(pct, 100)}%;"></div></div>
    </div>`;
}

function progressionHtml(c) {
  if (c.progression === null || c.progression === undefined) return "";
  const niveau = c.progression >= 70 ? "haut" : c.progression >= 40 ? "moyen" : "bas";
  return `
    <div class="chantier-progress">
      <div class="chantier-progress-row"><span>Avancement</span><strong>${c.progression}%</strong></div>
      <div class="sante-barre"><div class="remplissage niveau-${niveau}" style="width:${c.progression}%;"></div></div>
    </div>`;
}

function aujourdhuiChantierHtml(c) {
  // Qui travaille sur ce chantier aujourd'hui : vue "cockpit" (section 15),
  // deduite des heures reellement saisies pour la date du jour - jamais une
  // affectation fictive.
  const today = new Date().toISOString().slice(0, 10);
  const heuresAujourdhui = (c.heures || []).filter((h) => h.date_travail === today);
  if (!heuresAujourdhui.length) return "";
  const items = heuresAujourdhui
    .map((h) => `<strong>${escapeHtml(h.nom_intervenant)}</strong>${h.note ? " — " + escapeHtml(h.note) : ""}`)
    .join(" · ");
  return `<div class="item-meta">Aujourd'hui : ${items}</div>`;
}

function checklistHtml(c) {
  if (!c.taches || c.taches.length === 0) return "";
  const items = c.taches.map((t) => {
    const checked = t.statut === "faite";
    return `<label class="checklist-item">
      <input type="checkbox" data-action="toggle-tache-chantier" data-chantier-id="${c.id}" data-tache-id="${t.id}" ${checked ? "checked" : ""}>
      <span style="${checked ? "text-decoration:line-through;color:var(--text-muted);" : ""}">${escapeHtml(t.titre)}</span>
    </label>`;
  }).join("");
  return `<div class="dash-section" style="margin:12px 0;"><h3 style="font-size:0.88rem;">Préparation et tâches</h3>${items}</div>`;
}

function receptionHtml(c) {
  if (!c.date_reception) return "";
  return `<div class="item-meta" style="margin:10px 0;">
    <strong>Réception :</strong> ${fmtDate(c.date_reception)}
    <div class="item-sub">${c.reserves ? "Réserves : " + escapeHtml(c.reserves) : "Aucune réserve constatée."}</div>
  </div>`;
}

function showReceptionForm(chantierId, c) {
  const container = document.getElementById(`reception-form-${chantierId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <h3 style="font-size:0.95rem;">Réception du chantier</h3>
      <div class="form-grid">
        <div><label for="recep-date-${chantierId}">Date de réception</label><input type="date" id="recep-date-${chantierId}" value="${c && c.date_reception ? c.date_reception : today}"></div>
      </div>
      <label for="recep-reserves-${chantierId}" style="margin-top:10px;">Réserves constatées (optionnel)</label>
      <textarea id="recep-reserves-${chantierId}" placeholder="Ex: finition plinthes à reprendre dans la cuisine">${c && c.reserves ? escapeHtml(c.reserves) : ""}</textarea>
      <p class="field-error" id="reception-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-reception" data-id="${chantierId}">Enregistrer la réception</button>
        <button type="button" class="btn-sm" data-action="cancel-reception-form" data-id="${chantierId}">Annuler</button>
      </div>
    </div>`;
}

function showCloturerForm(chantierId) {
  const container = document.getElementById(`cloturer-form-${chantierId}`);
  if (!container) return;
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <h3 style="font-size:0.95rem;">Clôturer le chantier</h3>
      <label style="display:flex;align-items:center;gap:8px;margin-top:6px;font-weight:500;">
        <input type="checkbox" id="clot-facture-${chantierId}" checked> Générer et envoyer la facture finale (solde réellement dû)
      </label>
      <label style="display:flex;align-items:center;gap:8px;margin-top:6px;font-weight:500;">
        <input type="checkbox" id="clot-avis-${chantierId}" checked> Demander un avis au client
      </label>
      <p class="field-error" id="cloturer-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="confirmer-cloturer" data-id="${chantierId}">Clôturer et lancer les actions</button>
        <button type="button" class="btn-sm" data-action="cancel-cloturer-form" data-id="${chantierId}">Annuler</button>
      </div>
    </div>`;
}

async function showChantierEditForm(c) {
  const container = document.getElementById(`chantier-edit-form-${c.id}`);
  if (!container) return;
  await ensureClientsCache();
  const verrou = !!c.finances_verrouillees;
  const clientVerrouille = verrou || !!c.devis_id;
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <h3 style="font-size:0.95rem;">Modifier le chantier</h3>
      <div class="form-grid">
        <div><label for="chantier-titre-${c.id}">Titre *</label><input type="text" id="chantier-titre-${c.id}" value="${escapeHtml(c.titre)}"></div>
        <div><label for="chantier-client-${c.id}">Client *</label><select id="chantier-client-${c.id}" ${clientVerrouille ? "disabled" : ""}>${clientOptionsHtml(c.client_id)}</select></div>
        <div><label for="chantier-adresse-${c.id}">Adresse</label><input type="text" id="chantier-adresse-${c.id}" value="${escapeHtml(c.adresse || "")}"></div>
        <div><label for="chantier-date-${c.id}">Date de début</label><input type="date" id="chantier-date-${c.id}" value="${escapeHtml(c.date_debut || "")}"></div>
        <div><label for="chantier-fin-${c.id}">Fin prévue</label><input type="date" id="chantier-fin-${c.id}" value="${escapeHtml(c.date_fin_prevue || "")}"></div>
        <div><label for="chantier-budget-${c.id}">Budget prévu (euros)</label><input type="number" step="0.01" min="0" id="chantier-budget-${c.id}" value="${c.budget !== null ? escapeHtml(c.budget) : ""}" ${verrou ? "disabled" : ""}></div>
      </div>
      <p class="section-hint">Sans fin prévue, le chantier ne peut jamais être signalé en retard.</p>
      ${verrou ? '<div class="item-sub" style="margin-top:8px;">Le client et le budget sont verrouillés car la facture finale a été créée.</div>' : ""}
      ${c.devis_id && !verrou ? '<div class="item-sub" style="margin-top:8px;">Le client reste celui du devis associé.</div>' : ""}
      <p class="field-error" id="chantier-edit-error-${c.id}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-chantier-edit" data-id="${c.id}">Enregistrer</button>
        <button type="button" class="btn-sm" data-action="cancel-chantier-edit" data-id="${c.id}">Annuler</button>
      </div>
    </div>`;
}

// Une action principale visible + le reste dans le menu "•••" (meme systeme
// que renderDevisCard) : memes data-action/data-id qu'avant, seule leur
// repartition entre bouton primaire et menu change.
function chantierActionsHtml(c, { menuSeul = false } = {}) {
  const items = [];
  items.push({ attrs: `data-action="edit-chantier" data-id="${c.id}"`, label: "Modifier le chantier" });
  items.push({ primaire: c.statut !== "termine", attrs: `data-action="toggle-note-form" data-id="${c.id}"`, label: "+ Ajouter une note" });
  if (!c.finances_verrouillees) {
    items.push({ attrs: `data-action="toggle-depense-form" data-id="${c.id}"`, label: "+ Ajouter une dépense" });
    items.push({ attrs: `data-action="toggle-heures-form" data-id="${c.id}"`, label: "+ Ajouter des heures" });
  }
  items.push({ attrs: `data-action="chantier-document" data-id="${c.id}"`, label: "+ Ajouter un document" });
  items.push({ attrs: `data-action="planifier-intervention" data-id="${c.id}"`, label: "Planifier une intervention" });
  if (!["termine", "facture", "paye"].includes(c.statut)) {
    items.push({ attrs: `data-action="terminer-chantier" data-id="${c.id}"`, label: "Marquer terminé" });
  }
  if (["termine", "facture", "paye"].includes(c.statut)) {
    items.push({ attrs: `data-action="toggle-reception-form" data-id="${c.id}"`, label: c.date_reception ? "Modifier la réception" : "Enregistrer la réception" });
  }
  if (c.statut === "termine") {
    items.push({ primaire: true, attrs: `data-action="toggle-cloturer-form" data-id="${c.id}"`, label: "Clôturer le chantier" });
  }
  items.push({ attrs: `data-action="rapport-chantier" data-id="${c.id}"`, label: "Télécharger le rapport" });
  items.push({ divider: true });
  items.push({ attrs: `data-action="delete-chantier" data-id="${c.id}"`, label: "Archiver", danger: true });

  // Sur une carte, le bouton "Voir" ne sert a rien : la carte entiere est
  // la zone cliquable qui deplie le dossier (voir .chantier-card-resume).
  // Le supprimer libere une trentaine de pixels sur chaque carte - a trente
  // chantiers c'est deux ecrans de defilement - et rend au libelle de la
  // prochaine action la largeur qui lui manquait pour tenir en entier.
  const primaireHtml = menuSeul
    ? ""
    : `<button type="button" class="btn-sm btn-sm-primary" data-action="toggle-chantier-details" data-id="${c.id}" aria-expanded="false">Voir</button>`;
  const menuHtml = items
    .map((it) => it.divider
      ? '<div class="action-menu-divider"></div>'
      : `<button type="button"${it.danger ? ' class="is-danger"' : ""} ${it.attrs}>${it.label}</button>`)
    .join("");

  return `
    <div class="item-actions">
      ${primaireHtml}
      <div class="action-menu">
        <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur ce chantier">
          <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
        </button>
        <div class="action-menu-panel" role="menu">${menuHtml}</div>
      </div>
    </div>`;
}

function renderChantierCard(c) {
  const notesHtml = (c.notes || [])
    .slice()
    .reverse()
    .map(
      (n) => `
    <div class="note-item">
      <span class="badge badge-blue">${PHASE_LABELS[n.phase] || n.phase}</span>
      <div style="margin-top:6px;">${escapeHtml(n.texte || "")}</div>
      ${n.photo_url ? `<img class="note-photo" src="${escapeHtml(n.photo_url)}" alt="Photo du chantier" onerror="this.remove()">` : ""}
      <div class="item-sub" style="margin-top:6px;">${fmtDateTime(n.created_at)}</div>
    </div>`
    )
    .join("");

  const depensesHtml = (c.depenses || [])
    .slice()
    .reverse()
    .map((d) => `<div class="item-sub" style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
      <span>${fmtDate(d.date_depense)} · ${escapeHtml(d.libelle)} · ${fmtEuro(d.montant)}${d.fournisseur_nom ? " · " + escapeHtml(d.fournisseur_nom) : ""}</span>
      ${c.finances_verrouillees ? "" : `<button type="button" class="btn-sm" style="padding:2px 8px;flex-shrink:0;" data-action="edit-depense" data-id="${c.id}" data-depense-id="${d.id}">Modifier</button>`}
    </div>`)
    .join("");

  const progression = Math.max(0, Math.min(100, Number(c.progression) || 0));
  const budgetPct = c.budget ? Math.round(((c.total_depenses || 0) / c.budget) * 100) : null;
  const estTermine = ["termine", "facture", "paye"].includes(c.statut);
  const estASurveiller = chantierEstASurveiller(c);
  const joursRetard = chantierJoursRetard(c);
  const action = chantierProchaineAction(c);
  const rowClass = joursRetard > 0 ? " is-late" : estASurveiller ? " is-warning" : estTermine ? " is-complete" : "";
  const statutMeta = CHANTIER_STATUT_META[c.statut] || { badge: "badge-gray", label: c.statut };
  // Les deux barres ne disent pas la meme chose, elles ne peuvent donc pas
  // partager un code couleur. L'AVANCEMENT reste neutre : un chantier a
  // 15 % n'est pas en difficulte, il vient de commencer - le peindre en
  // rouge (ce que faisait l'ancienne fiche) transforme trente lignes de
  // debut de chantier en trente fausses alertes. Seul le BUDGET porte un
  // signal, avec les seuils deja utilises par "A surveiller" (85 %).
  const niveauBudget = (pct) => (pct >= 85 ? "bas" : pct >= 60 ? "moyen" : "haut");

  // Une jauge = un libelle, une barre, une valeur, sur une seule ligne.
  // Empilees, deux jauges tiennent en 40 px et se comparent d'un coup
  // d'oeil : c'est tout l'interet de les mettre l'une sous l'autre.
  const jauge = (libelle, valeur, largeur, classe = "", note = "") => `
    <div class="chantier-jauge">
      <span class="chantier-jauge-label">${libelle}</span>
      <span class="sante-barre"><span class="remplissage ${classe}" style="width:${largeur}%;"></span></span>
      <span class="chantier-jauge-valeur">${valeur}</span>
      ${note ? `<span class="chantier-jauge-note">${note}</span>` : ""}
    </div>`;

  return `
  <article class="chantier-card${rowClass}" data-chantier-id="${c.id}">
    <!-- La zone de resume porte l'action de depliage, pas la carte
         entiere : sinon un clic sur un champ du dossier ouvert -
         qui est aussi un descendant de la carte - refermerait le
         dossier sous les doigts de l'utilisateur. -->
    <div class="chantier-card-resume" data-action="toggle-chantier-details" data-id="${c.id}"
         role="button" tabindex="0" aria-expanded="false"
         aria-controls="chantier-details-${c.id}"
         aria-label="Ouvrir le dossier ${escapeHtml(c.titre)}">
      <div class="chantier-card-tete">
        <div class="chantier-card-identite">
          <h3 class="chantier-card-titre">${escapeHtml(c.titre)}</h3>
          <p class="chantier-card-client">${escapeHtml(c.client_nom || "Client non renseigné")}${c.adresse ? " · " + escapeHtml(c.adresse) : ""}</p>
        </div>
        <span class="badge ${statutMeta.badge}">${escapeHtml(statutMeta.label)}</span>
        <div class="chantier-card-actions">${chantierActionsHtml(c, { menuSeul: true })}</div>
      </div>

      <div class="chantier-card-jauges">
        ${jauge("Avancement", `${progression} %`, progression)}
        ${budgetPct === null
          ? jauge("Budget", "—", 0, "", "non renseigné")
          : jauge("Budget", `${budgetPct} %`, Math.min(budgetPct, 100), `niveau-${niveauBudget(budgetPct)}`)}
      </div>

      <div class="chantier-card-pied">
        <span class="chantier-action-fleche" aria-hidden="true">→</span>
        <span class="chantier-action-texte${action.vide ? " is-vide" : ""}">${escapeHtml(action.texte)}</span>
        ${action.quand ? `<span class="chantier-action-quand${action.enRetard ? " is-late" : ""}">${escapeHtml(action.quand)}</span>` : ""}
        <span class="chantier-card-echeance${joursRetard > 0 ? " is-late" : ""}" title="Fin prévue">
          ${c.date_fin_prevue ? fmtDate(c.date_fin_prevue) : "fin non fixée"}${joursRetard > 0 ? ` <strong>+${joursRetard} j</strong>` : ""}
        </span>
      </div>
    </div>
    <div class="chantier-details" id="chantier-details-${c.id}" hidden>
      ${c.statut === "termine" ? `<div class="moment-banner"><span>Chantier terminé ! Clôturez-le pour générer la facture finale, demander un avis client et archiver le dossier.</span></div>` : ""}
      ${aujourdhuiChantierHtml(c)}
      <div class="item-meta">Début : ${fmtDate(c.date_debut)}${c.adresse ? ` · ${escapeHtml(c.adresse)}` : ""}</div>
      ${checklistHtml(c)}
      ${rentabiliteHtml(c)}
      ${c.finances_verrouillees ? '<div class="moment-banner"><span>Les données financières sont verrouillées depuis la création de la facture finale.</span></div>' : ""}
      ${depensesHtml ? `<div class="item-meta">${depensesHtml}</div>` : ""}
      ${heuresHtml(c)}
      <div class="notes-list">${notesHtml || '<div class="item-sub">Aucune note pour le moment.</div>'}</div>
      ${receptionHtml(c)}
      <div id="chantier-edit-form-${c.id}"></div>
      <div id="note-form-${c.id}"></div>
      <div id="depense-form-${c.id}"></div>
      <div id="heures-form-${c.id}"></div>
      <div id="reception-form-${c.id}"></div>
      <div id="cloturer-form-${c.id}"></div>
    </div>
  </article>`;
}

function showDepenseForm(chantierId, depense = null) {
  const container = document.getElementById(`depense-form-${chantierId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div><label for="dep-libelle-${chantierId}">Libellé *</label><input type="text" id="dep-libelle-${chantierId}" value="${escapeHtml(depense ? depense.libelle : "")}" placeholder="Ex: Matériaux carrelage"></div>
        <div><label for="dep-montant-${chantierId}">Montant (euros) *</label><input type="number" step="0.01" min="0.01" id="dep-montant-${chantierId}" value="${depense ? escapeHtml(depense.montant) : ""}"></div>
        <div><label for="dep-date-${chantierId}">Date</label><input type="date" id="dep-date-${chantierId}" value="${depense ? escapeHtml(depense.date_depense) : today}"></div>
        <div><label for="dep-fournisseur-${chantierId}">Fournisseur (optionnel)</label><select id="dep-fournisseur-${chantierId}"><option value="">Aucun</option>${fournisseursCache.map((f) => `<option value="${f.id}" ${depense && depense.fournisseur_id === f.id ? "selected" : ""}>${escapeHtml(f.nom)}</option>`).join("")}</select></div>
      </div>
      <p class="field-error" id="depense-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-depense" data-id="${chantierId}" ${depense ? `data-depense-id="${depense.id}"` : ""}>${depense ? "Enregistrer" : "Ajouter"}</button>
        <button type="button" class="btn-sm" data-action="cancel-depense-form" data-id="${chantierId}">Annuler</button>
      </div>
    </div>`;
}

function showNoteForm(chantierId) {
  const container = document.getElementById(`note-form-${chantierId}`);
  if (!container) return;
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div>
          <label for="note-phase-${chantierId}">Phase</label>
          <select id="note-phase-${chantierId}">
            <option value="avant">Avant</option>
            <option value="pendant">Pendant</option>
            <option value="apres">Après</option>
          </select>
        </div>
        <div>
          <label for="note-photo-${chantierId}">URL de la photo (optionnel)</label>
          <input type="url" id="note-photo-${chantierId}" placeholder="https://...">
        </div>
      </div>
      <label for="note-texte-${chantierId}" style="margin-top:14px;">Note</label>
      <textarea id="note-texte-${chantierId}" placeholder="Ex: démolition terminée, prêt pour le carrelage"></textarea>
      <p class="field-error" id="note-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-note" data-id="${chantierId}">Ajouter</button>
        <button type="button" class="btn-sm" data-action="cancel-note-form" data-id="${chantierId}">Annuler</button>
      </div>
    </div>`;
}

function setupChantiersView() {
  document.getElementById("chantier-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#chantier-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentChantierFilter = chip.dataset.statut;
    document.getElementById("chantiers-statut-filtre").value = currentChantierFilter;
    renderChantiersListFiltered();
  });

  document.getElementById("chantiers-sort").addEventListener("change", (e) => {
    currentChantierSort = e.target.value;
    renderChantiersListFiltered();
  });
  document.getElementById("chantiers-statut-filtre").addEventListener("change", (e) => {
    currentChantierFilter = e.target.value;
    document.querySelectorAll("#chantier-filters .filter-chip").forEach((chip) => chip.classList.toggle("active", chip.dataset.statut === currentChantierFilter));
    renderChantiersListFiltered();
  });
  document.getElementById("chantiers-avancement-filtre").addEventListener("change", (e) => {
    currentChantierAvancement = e.target.value;
    renderChantiersListFiltered();
  });
  document.getElementById("chantiers-client-filtre").addEventListener("change", (e) => {
    currentChantierClient = e.target.value;
    renderChantiersListFiltered();
  });
  // La carte se deplie au clavier comme au clic : c'est une zone
  // cliquable, elle doit donc repondre a Entree et Espace comme un bouton.
  document.getElementById("chantiers-list").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const resume = e.target.closest(".chantier-card-resume");
    if (!resume || e.target.closest("button")) return;
    e.preventDefault();
    resume.click();
  });

  // La recherche est traitee ici plutot que par setupListesSearch : ce
  // dernier masque les cartes dont le textContent ne contient pas la
  // requete, ce qui revenait a chercher aussi dans les libelles de
  // l'interface. Voir chantierMatchesRecherche.
  document.getElementById("chantiers-search").addEventListener("input", (e) => {
    currentChantierRecherche = e.target.value;
    renderChantiersListFiltered();
  });

  document.querySelector('[data-action="show-chantier-form"]').addEventListener("click", async () => {
    const container = document.getElementById("chantier-form-container");
    await ensureClientsCache();

    if (clientsCache.length === 0) {
      container.innerHTML = `<div class="form-box"><p>Vous n'avez pas encore de client. Ajoutez d'abord un contact dans l'onglet <strong>Clients &amp; prospects</strong>.</p>
        <div class="form-actions"><button type="button" class="btn-sm" data-action="cancel-chantier-form">Fermer</button></div></div>`;
      container.hidden = false;
      return;
    }

    container.innerHTML = `
      <div class="form-box">
        <h3>Nouveau chantier</h3>
        <form id="chantier-form">
          <div class="form-section">
            <div class="form-section-title">Chantier</div>
            <div class="form-grid">
              <div><label for="cf-titre">Titre *</label><input type="text" id="cf-titre" required></div>
              <div><label for="cf-client">Client *</label><select id="cf-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select></div>
              <div><label for="cf-adresse">Adresse</label><input type="text" id="cf-adresse"></div>
            </div>
          </div>
          <div class="form-section">
            <div class="form-section-title">Planification</div>
            <div class="form-grid">
              <div><label for="cf-date">Date de début</label><input type="date" id="cf-date"></div>
              <div><label for="cf-fin">Fin prévue</label><input type="date" id="cf-fin"></div>
              <div><label for="cf-budget">Budget prévu (euros)</label><input type="number" step="0.01" min="0" id="cf-budget"></div>
            </div>
          </div>
          <p class="field-error" id="chantier-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Créer</button>
            <button type="button" class="btn-sm" data-action="cancel-chantier-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("chantier-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("chantier-form-error");
      errorBox.hidden = true;
      const budgetRaw = document.getElementById("cf-budget").value;
      try {
        await Api.createChantier({
          titre: document.getElementById("cf-titre").value,
          client_id: parseInt(document.getElementById("cf-client").value, 10),
          adresse: emptyToNull(document.getElementById("cf-adresse").value),
          date_debut: emptyToNull(document.getElementById("cf-date").value),
          date_fin_prevue: emptyToNull(document.getElementById("cf-fin").value),
          budget: budgetRaw === "" ? null : parseFloat(budgetRaw),
        });
        showToast("Chantier créé.");
        container.hidden = true;
        container.innerHTML = "";
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });

  document.getElementById("chantier-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-chantier-form"]')) {
      const container = document.getElementById("chantier-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("chantiers-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    if (btn.dataset.action === "toggle-tache-chantier") {
      const chantierId = parseInt(btn.dataset.chantierId, 10);
      const tacheId = parseInt(btn.dataset.tacheId, 10);
      const checked = btn.checked;
      try {
        await Api.updateTache(tacheId, { statut: checked ? "faite" : "a_faire" });
        loadChantiers();
      } catch (err) {
        btn.checked = !checked;
        showToast(err.message, true);
      }
      return;
    }

    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "toggle-chantier-details") {
      const details = document.getElementById(`chantier-details-${id}`);
      if (!details) return;
      details.hidden = !details.hidden;
      btn.setAttribute("aria-expanded", String(!details.hidden));
      // Le declencheur est un BOUTON ailleurs dans le produit, mais sur une
      // carte c'est la zone de resume elle-meme : lui reecrire son
      // textContent effacerait tout le contenu de la carte.
      if (btn.tagName === "BUTTON") btn.textContent = details.hidden ? "Voir" : "Masquer";
      // Une carte depliee prend toute la largeur de la grille : sinon le
      // dossier complet s'entasserait dans une colonne de 340 px et
      // etirerait toute sa rangee de voisines.
      const carte = btn.closest(".chantier-card");
      if (carte) carte.classList.toggle("is-open", !details.hidden);
    } else if (btn.dataset.action === "edit-chantier") {
      const chantier = chantiersCache.find((c) => c.id === id);
      if (chantier) await showChantierEditForm(chantier);
    } else if (btn.dataset.action === "cancel-chantier-edit") {
      document.getElementById(`chantier-edit-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-chantier-edit") {
      const chantier = chantiersCache.find((c) => c.id === id);
      const errorBox = document.getElementById(`chantier-edit-error-${id}`);
      const titre = document.getElementById(`chantier-titre-${id}`).value.trim();
      if (!titre) {
        errorBox.hidden = false;
        errorBox.textContent = "Le titre est obligatoire.";
        return;
      }
      const payload = {
        titre,
        adresse: emptyToNull(document.getElementById(`chantier-adresse-${id}`).value),
        date_debut: emptyToNull(document.getElementById(`chantier-date-${id}`).value),
        date_fin_prevue: emptyToNull(document.getElementById(`chantier-fin-${id}`).value),
      };
      if (chantier && !chantier.finances_verrouillees && !chantier.devis_id) {
        payload.client_id = parseInt(document.getElementById(`chantier-client-${id}`).value, 10);
      }
      if (chantier && !chantier.finances_verrouillees) {
        const budget = document.getElementById(`chantier-budget-${id}`).value;
        payload.budget = budget === "" ? null : parseFloat(budget);
      }
      try {
        await Api.updateChantier(id, payload);
        showToast("Chantier mis à jour.");
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "chantier-document") {
      switchView("documents");
      setTimeout(() => showDocumentForm(id), 50);
    } else if (btn.dataset.action === "planifier-intervention") {
      const chantier = chantiersCache.find((c) => c.id === id);
      switchView("planning");
      setTimeout(() => window.showEvenementForm({
        titre: `Intervention - ${chantier ? chantier.titre : ""}`,
        type: "intervention",
        chantierId: id,
        clientId: chantier ? chantier.client_id : null,
      }), 100);
    } else if (btn.dataset.action === "toggle-reception-form") {
      const chantier = chantiersCache.find((c) => c.id === id);
      showReceptionForm(id, chantier);
    } else if (btn.dataset.action === "cancel-reception-form") {
      document.getElementById(`reception-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-reception") {
      const dateReception = document.getElementById(`recep-date-${id}`).value;
      const reserves = document.getElementById(`recep-reserves-${id}`).value;
      try {
        await Api.updateChantier(id, { date_reception: emptyToNull(dateReception), reserves: emptyToNull(reserves) });
        showToast("Réception enregistrée.");
        loadChantiers();
      } catch (err) {
        const errorBox = document.getElementById(`reception-error-${id}`);
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "toggle-note-form") {
      showNoteForm(id);
    } else if (btn.dataset.action === "cancel-note-form") {
      document.getElementById(`note-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-note") {
      const texte = document.getElementById(`note-texte-${id}`).value;
      const phase = document.getElementById(`note-phase-${id}`).value;
      const photoUrl = document.getElementById(`note-photo-${id}`).value;
      try {
        await Api.addChantierNote(id, { phase, texte: emptyToNull(texte), photo_url: emptyToNull(photoUrl) });
        showToast("Note ajoutée.");
        loadChantiers();
      } catch (err) {
        const errorBox = document.getElementById(`note-error-${id}`);
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "toggle-depense-form") {
      await ensureFournisseursCache();
      showDepenseForm(id);
    } else if (btn.dataset.action === "edit-depense") {
      await ensureFournisseursCache();
      const chantier = chantiersCache.find((c) => c.id === id);
      const depense = chantier && chantier.depenses.find((d) => d.id === parseInt(btn.dataset.depenseId, 10));
      if (depense) showDepenseForm(id, depense);
    } else if (btn.dataset.action === "cancel-depense-form") {
      document.getElementById(`depense-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-depense") {
      const libelle = document.getElementById(`dep-libelle-${id}`).value.trim();
      const montant = document.getElementById(`dep-montant-${id}`).value;
      const dateDepense = document.getElementById(`dep-date-${id}`).value;
      const fournisseurId = document.getElementById(`dep-fournisseur-${id}`).value;
      const errorBox = document.getElementById(`depense-error-${id}`);
      if (!libelle || !montant) {
        errorBox.hidden = false;
        errorBox.textContent = "Libellé et montant sont obligatoires.";
        return;
      }
      try {
        const payload = {
          libelle, montant: parseFloat(montant), date_depense: dateDepense,
          fournisseur_id: fournisseurId ? parseInt(fournisseurId, 10) : null,
        };
        if (btn.dataset.depenseId) {
          await Api.updateChantierDepense(id, parseInt(btn.dataset.depenseId, 10), payload);
          showToast("Dépense mise à jour.");
        } else {
          await Api.addChantierDepense(id, payload);
          showToast("Dépense ajoutée.");
        }
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "toggle-heures-form") {
      if (hasPlan("business")) await ensureEquipeCache();
      else equipeCache = [];
      showHeuresForm(id);
    } else if (btn.dataset.action === "edit-heure") {
      if (hasPlan("business")) await ensureEquipeCache();
      else equipeCache = [];
      const chantier = chantiersCache.find((c) => c.id === id);
      const heure = chantier && chantier.heures.find((h) => h.id === parseInt(btn.dataset.heureId, 10));
      if (heure) showHeuresForm(id, heure);
    } else if (btn.dataset.action === "cancel-heures-form") {
      document.getElementById(`heures-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-heures") {
      const membreSelect = document.getElementById(`heure-membre-${id}`);
      const membreId = membreSelect.value;
      const nomLibre = document.getElementById(`heure-nom-${id}`).value.trim();
      const nomIntervenant = membreId
        ? membreSelect.options[membreSelect.selectedIndex].dataset.nom
        : nomLibre;
      const duree = document.getElementById(`heure-duree-${id}`).value;
      const dateTravail = document.getElementById(`heure-date-${id}`).value;
      const taux = document.getElementById(`heure-taux-${id}`).value;
      const note = document.getElementById(`heure-note-${id}`).value.trim();
      const errorBox = document.getElementById(`heures-error-${id}`);
      if (!nomIntervenant || !duree) {
        errorBox.hidden = false;
        errorBox.textContent = "Intervenant (ou nom) et durée sont obligatoires.";
        return;
      }
      try {
        const payload = {
          membre_id: membreId ? parseInt(membreId, 10) : null,
          nom_intervenant: nomIntervenant,
          duree_heures: parseFloat(duree), date_travail: dateTravail,
          taux_horaire: taux ? parseFloat(taux) : null,
          note: emptyToNull(note),
        };
        if (btn.dataset.heureId) {
          await Api.updateChantierHeures(id, parseInt(btn.dataset.heureId, 10), payload);
          showToast("Heures mises à jour.");
        } else {
          await Api.addChantierHeures(id, payload);
          showToast("Heures ajoutées.");
        }
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "delete-heure") {
      const heureId = parseInt(btn.dataset.heureId, 10);
      await withErrorToast(async () => {
        await Api.deleteChantierHeures(id, heureId);
        showToast("Heures supprimées.");
        loadChantiers();
      });
    } else if (btn.dataset.action === "terminer-chantier") {
      await withErrorToast(async () => {
        await Api.updateChantier(id, { statut: "termine" });
        showToast("Chantier marqué terminé.");
        loadChantiers();
      });
    } else if (btn.dataset.action === "toggle-cloturer-form") {
      showCloturerForm(id);
    } else if (btn.dataset.action === "cancel-cloturer-form") {
      document.getElementById(`cloturer-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "confirmer-cloturer") {
      const errorBox = document.getElementById(`cloturer-error-${id}`);
      errorBox.hidden = true;
      try {
        const res = await Api.cloturerChantier(id, {
          generer_facture_finale: document.getElementById(`clot-facture-${id}`).checked,
          demander_avis: document.getElementById(`clot-avis-${id}`).checked,
        });
        let msg = "Chantier clôturé.";
        if (res.facture_finale) {
          const statutTxt = res.facture_finale_email_statut === "envoye" ? "envoyée par email" : "créée (email non envoyé, copiez le lien pour la transmettre)";
          msg += ` Facture finale de ${fmtEuro(res.facture_finale.montant_ttc)} ${statutTxt}.`;
        } else if (res.facture_finale_raison_absence) {
          msg += ` Pas de facture finale : ${res.facture_finale_raison_absence}.`;
        }
        if (res.avis_demande) {
          msg += res.avis_email_statut === "envoye" ? " Demande d'avis envoyée." : " Demande d'avis générée (email non envoyé, lien à transmettre manuellement).";
        }
        showToast(msg);
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "rapport-chantier") {
      await withErrorToast(() => ouvrirPdf(`/chantiers/${id}/rapport-pdf`));
    } else if (btn.dataset.action === "delete-chantier") {
      if (!(await confirmDialog("Archiver ce chantier ? Il disparaîtra de vos listes actives. Ses notes, dépenses, heures et factures liées restent intactes.", { confirmLabel: "Archiver", danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteChantier(id);
        showToast("Chantier archivé.");
        loadChantiers();
      });
    }
  });
}

// ===================== Taches =====================
let currentTacheFilter = "a_faire";
const TACHE_PRIORITE_BADGE = { basse: "badge-gray", normale: "badge-blue", haute: "badge-orange", urgente: "badge-red" };
const TACHE_PRIORITE_LABELS = { basse: "Priorité basse", normale: "Priorité normale", haute: "Priorité haute", urgente: "Priorité urgente" };
const TACHE_PRIORITE_PILL = { basse: "pill-green", normale: "pill-gray", haute: "pill-accent", urgente: "pill-red" };
const TACHE_GROUPE_LABELS = { en_retard: "En retard", aujourdhui: "Aujourd'hui", cette_semaine: "Cette semaine", plus_tard: "Plus tard" };
const TACHE_GROUPE_ORDRE = ["en_retard", "aujourdhui", "cette_semaine", "plus_tard"];

// Regroupement par echeance (En retard / Aujourd'hui / Cette semaine / Plus
// tard) : simple lecture de t.echeance deja recu, aucun nouveau calcul
// metier - juste une facon de presenter la meme liste plate.
function tacheGroupe(t) {
  if (!t.echeance || t.statut !== "a_faire") return "plus_tard";
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(t.echeance + "T00:00:00");
  const diffJours = Math.round((due - today) / 86400000);
  if (diffJours < 0) return "en_retard";
  if (diffJours === 0) return "aujourdhui";
  if (diffJours > 0 && diffJours <= 7) return "cette_semaine";
  return "plus_tard";
}

function tacheEcheanceMeta(t) {
  if (!t.echeance) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const due = new Date(t.echeance + "T00:00:00");
  const diffJours = Math.round((due - today) / 86400000);
  if (t.statut === "a_faire" && diffJours < 0) return { label: `En retard · ${Math.abs(diffJours)} j`, pill: "pill-red" };
  if (diffJours === 0) return { label: "Aujourd'hui", pill: "pill-accent" };
  if (diffJours === 1) return { label: "Demain", pill: "pill-gray" };
  if (diffJours > 1 && diffJours <= 7) return { label: "Cette semaine", pill: "pill-green" };
  return { label: fmtDate(t.echeance), pill: "pill-gray" };
}

let tachesCache = [];
let currentTacheSousFiltre = ""; // "" | en_retard | aujourdhui | cette_semaine (voir tacheGroupe)
let tachesPrioriteFirst = false;

function sortTachesForDisplay(taches) {
  if (!tachesPrioriteFirst) return taches;
  const poids = { urgente: 4, haute: 3, normale: 2, basse: 1 };
  return taches.slice().sort((a, b) => (poids[b.priorite] || 0) - (poids[a.priorite] || 0));
}

// ---------------------------------------------------------------------
// TACHES — rendre le contexte visible
// ---------------------------------------------------------------------
// Le regroupement par echeance (En retard / Aujourd'hui / Cette semaine /
// Plus tard) etait deja la bonne composition pour une liste d'execution,
// et il est conserve. Deux choses lui manquaient.
//
// LE CONTEXTE. TacheOut porte `chantier_id` et `client_id` depuis
// toujours, et ni l'un ni l'autre n'etait affiche. « Commander le
// carrelage » sans savoir pour quel chantier n'est pas une tache, c'est
// une devinette - et l'artisan qui a trois chantiers en cours devait
// ouvrir la fiche pour savoir de quoi il s'agissait.
//
// LE BRUIT. Chaque ligne portait deux pastilles, l'echeance et la
// priorite, y compris quand elles n'avaient rien a dire : « Priorite
// normale » sur une tache sans urgence occupe la place sans jamais rien
// apprendre. Elles ne s'affichent plus que lorsqu'elles signalent
// quelque chose.

/** Le contexte d'une tache : le chantier s'il y en a un, le client
 *  sinon. Les deux listes sont celles que le produit charge deja
 *  ailleurs ; on ne demande rien de plus, et l'absence de cache se
 *  traduit simplement par une ligne sans contexte. */
function tacheContexte(t) {
  if (t.chantier_id) {
    const c = (typeof chantiersCache !== "undefined" ? chantiersCache : []).find((x) => x.id === t.chantier_id);
    if (c) return { label: c.titre, type: "Chantier", action: "ouvrir-chantier-depuis-tache", id: c.id };
  }
  if (t.client_id) {
    const c = (typeof clientsCache !== "undefined" ? clientsCache : []).find((x) => x.id === t.client_id);
    if (c) return { label: c.nom, type: "Client", action: "voir-timeline", id: c.id };
  }
  return null;
}

function renderTacheRow(t) {
  const estFaite = t.statut === "faite";
  const echeance = tacheEcheanceMeta(t);
  const contexte = tacheContexte(t);
  // La priorite ne s'affiche que si elle sort de l'ordinaire : une
  // pastille « Priorite normale » sur chaque ligne ne dit rien.
  const prioriteVisible = !estFaite && ["haute", "urgente"].includes(t.priorite);
  // L'echeance ne s'affiche que si elle presse ou si elle est passee -
  // le regroupement par periode porte deja l'information du « quand ».
  const echeanceVisible = echeance && !estFaite && ["pill-red", "pill-accent"].includes(echeance.pill);

  return `
  <div class="tache-row">
    <input type="checkbox" class="tache-row-check" ${estFaite ? "checked" : ""}
      data-action="${estFaite ? "reouvrir-tache" : "terminer-tache"}" data-id="${t.id}" aria-label="${estFaite ? "Réouvrir la tâche" : "Marquer la tâche faite"}">
    <div class="tache-row-body">
      <div class="tache-row-titre${estFaite ? " is-done" : ""}">${escapeHtml(t.titre)}</div>
      ${contexte
        ? `<button type="button" class="tache-row-contexte" data-action="${contexte.action}" data-id="${contexte.id}">
             <span class="tache-row-contexte-type">${contexte.type}</span>${escapeHtml(contexte.label)}
           </button>`
        : (t.description ? `<div class="tache-row-sub">${escapeHtml(t.description)}</div>` : "")}
    </div>
    ${echeanceVisible ? `<span class="pill ${echeance.pill}">${echeance.label}</span>` : "<span></span>"}
    ${prioriteVisible ? `<span class="pill ${TACHE_PRIORITE_PILL[t.priorite] || "pill-gray"}">${TACHE_PRIORITE_LABELS[t.priorite] || t.priorite}</span>` : "<span></span>"}
    <div class="action-menu">
      <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur cette tâche">
        <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
      </button>
      <div class="action-menu-panel" role="menu">
        <button type="button" class="is-danger" data-action="delete-tache" data-id="${t.id}">Supprimer</button>
      </div>
    </div>
  </div>`;
}

function renderTachesFiltered() {
  const list = document.getElementById("taches-list");
  if (tachesCache.length === 0) {
    list.innerHTML = currentTacheFilter === "faite"
      ? etatFiltre("Aucune tâche terminée pour le moment.")
      : etatVide(
          "Rien à faire aujourd'hui.",
          "Les tâches créées depuis un chantier ou un devis signé viendront se ranger ici toutes seules. Vous pouvez aussi en ajouter une à la main.",
          { action: "show-tache-form", libelle: "Nouvelle tâche" },
        );
    return;
  }
  if (currentTacheFilter !== "a_faire") {
    list.innerHTML = sortTachesForDisplay(tachesCache).map(renderTacheRow).join("");
    return;
  }
  const parGroupe = {};
  tachesCache.forEach((t) => { (parGroupe[tacheGroupe(t)] = parGroupe[tacheGroupe(t)] || []).push(t); });
  const groupesAffiches = currentTacheSousFiltre ? [currentTacheSousFiltre] : TACHE_GROUPE_ORDRE;
  const html = groupesAffiches
    .filter((g) => parGroupe[g] && parGroupe[g].length)
    .map((g) => `
      <div class="tache-groupe-label${g === "en_retard" ? " est-retard" : ""}">
        ${TACHE_GROUPE_LABELS[g]} <span>${parGroupe[g].length}</span>
      </div>
      ${sortTachesForDisplay(parGroupe[g]).map(renderTacheRow).join("")}
    `).join("");
  list.innerHTML = html || etatFiltre("Aucune tâche ne correspond à ce filtre.");
}

async function loadTaches() {
  const list = document.getElementById("taches-list");
  list.innerHTML = '<div class="repertoire-squelette"><span></span><span></span><span></span></div>';
  try {
    // Les chantiers et les clients servent a nommer le contexte de chaque
    // tache. Repli silencieux : sans eux la liste s'affiche, simplement
    // sans le nom du chantier.
    const [taches] = await Promise.all([
      Api.listTaches(currentTacheFilter),
      (typeof chantiersCache !== "undefined" && chantiersCache.length)
        ? Promise.resolve()
        : Api.listChantiers().then((c) => { chantiersCache = c; }).catch(() => {}),
      (typeof clientsCache !== "undefined" && clientsCache.length)
        ? Promise.resolve()
        : ensureClientsCache().catch(() => {}),
    ]);
    tachesCache = taches;
    renderTachesFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}


function showTacheForm() {
  const container = document.getElementById("tache-form-container");
  container.innerHTML = `
    <div class="form-box">
      <h3>Nouvelle tâche</h3>
      <form id="tache-form">
        <div class="form-grid">
          <div><label for="ta-titre">Titre *</label><input type="text" id="ta-titre" required></div>
          <div><label for="ta-echeance">Échéance</label><input type="date" id="ta-echeance"></div>
          <div>
            <label for="ta-priorite">Priorité</label>
            <select id="ta-priorite">
              <option value="basse">Basse</option>
              <option value="normale" selected>Normale</option>
              <option value="haute">Haute</option>
              <option value="urgente">Urgente</option>
            </select>
          </div>
        </div>
        <label for="ta-description" style="margin-top:14px;">Description</label>
        <textarea id="ta-description"></textarea>
        <p class="field-error" id="tache-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">Créer</button>
          <button type="button" class="btn-sm" data-action="cancel-tache-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  document.getElementById("tache-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("tache-form-error");
    errorBox.hidden = true;
    try {
      await Api.createTache({
        titre: document.getElementById("ta-titre").value,
        echeance: emptyToNull(document.getElementById("ta-echeance").value),
        priorite: document.getElementById("ta-priorite").value,
        description: emptyToNull(document.getElementById("ta-description").value),
      });
      showToast("Tâche créée.");
      container.hidden = true;
      container.innerHTML = "";
      loadTaches();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

function setupTachesView() {
  document.getElementById("tache-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#tache-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentTacheFilter = chip.dataset.statut;
    loadTaches();
  });

  document.getElementById("tache-subfilters").addEventListener("click", (e) => {
    const btn = e.target.closest(".subfilter-link");
    if (!btn) return;
    document.querySelectorAll("#tache-subfilters .subfilter-link").forEach((c) => c.classList.remove("active"));
    btn.classList.add("active");
    currentTacheSousFiltre = btn.dataset.groupe;
    renderTachesFiltered();
  });

  document.querySelector('[data-action="show-tache-form"]').addEventListener("click", showTacheForm);
  document.getElementById("taches-focus-filters").addEventListener("click", () => {
    document.querySelector("#tache-subfilters .subfilter-link")?.focus();
  });
  document.getElementById("taches-sort-priority").addEventListener("click", (e) => {
    tachesPrioriteFirst = !tachesPrioriteFirst;
    e.currentTarget.classList.toggle("active", tachesPrioriteFirst);
    e.currentTarget.setAttribute("aria-pressed", String(tachesPrioriteFirst));
    renderTachesFiltered();
  });
  document.getElementById("tache-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-tache-form"]')) {
      const container = document.getElementById("tache-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("taches-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    // Le contexte d'une tache mene a sa piece : « Commander le carrelage »
    // ouvre le chantier concerne, et non plus une devinette.
    if (btn.dataset.action === "ouvrir-chantier-depuis-tache") {
      ouvrirChantierDepuisPlanning(id);
      return;
    }
    if (btn.dataset.action === "voir-timeline") {
      showTimeline(id);
      return;
    }

    if (btn.dataset.action === "terminer-tache") {
      await withErrorToast(async () => {
        await Api.updateTache(id, { statut: "faite" });
        showToast("Tâche marquée faite.");
        loadTaches();
      });
    } else if (btn.dataset.action === "reouvrir-tache") {
      await withErrorToast(async () => {
        await Api.updateTache(id, { statut: "a_faire" });
        loadTaches();
      });
    } else if (btn.dataset.action === "delete-tache") {
      if (!(await confirmDialog("Supprimer cette tâche ?", { danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteTache(id);
        showToast("Tâche supprimée.");
        loadTaches();
      });
    }
  });
}

// ===================== Documents =====================
const DOCUMENT_TYPE_LABELS = {
  contrat: "Contrat", attestation: "Attestation", assurance: "Assurance",
  photo: "Photo", plan: "Plan", administratif: "Administratif", autre: "Autre",
};
const DOCUMENT_TYPE_PILL = {
  contrat: "pill-accent", attestation: "pill-green", assurance: "pill-gray",
  photo: "pill-gray", plan: "pill-gray", administratif: "pill-gray", autre: "pill-gray",
};

let currentDocumentFilter = "";

function fmtTaille(octets) {
  if (octets === null || octets === undefined) return "";
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(0)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

let documentsCache = [];
let documentsChantiersCache = [];
let currentDocumentSort = "date_desc";
let currentDocumentClient = "";
let currentDocumentChantier = "";
let currentDocumentDate = "";

function documentSort(documents) {
  const d = documents.slice();
  if (currentDocumentSort === "nom_asc") return d.sort((a, b) => a.nom.localeCompare(b.nom, "fr"));
  if (currentDocumentSort === "date_asc") return d.sort((a, b) => a.created_at.localeCompare(b.created_at));
  return d.sort((a, b) => b.created_at.localeCompare(a.created_at)); // date_desc, par defaut
}

function renderDocumentsListFiltered() {
  const list = document.getElementById("documents-list");
  const maintenant = new Date();
  const affichees = documentSort(documentsCache.filter((d) => {
    if (currentDocumentFilter && d.type !== currentDocumentFilter) return false;
    if (currentDocumentClient && String(d.client_id || "") !== currentDocumentClient) return false;
    if (currentDocumentChantier && String(d.chantier_id || "") !== currentDocumentChantier) return false;
    if (currentDocumentDate) {
      const dateDocument = new Date(d.created_at);
      if (currentDocumentDate === "year" && dateDocument.getFullYear() !== maintenant.getFullYear()) return false;
      if (/^\d+$/.test(currentDocumentDate)) {
        const limite = new Date(maintenant);
        limite.setDate(limite.getDate() - Number(currentDocumentDate));
        if (dateDocument < limite) return false;
      }
    }
    return true;
  }));
  if (affichees.length === 0) {
    list.innerHTML = `<div class="empty-state">${
      currentDocumentFilter || currentDocumentClient || currentDocumentChantier || currentDocumentDate
        ? "Aucun document ne correspond à ces filtres."
        : "<strong>Aucun document pour le moment.</strong><br><br>Les photos de chantier, attestations et plans déposés ici restent rattachés à leur client ou à leur chantier."
    }</div>`;
    return;
  }

  // On ne cherche pas « un document », on cherche « la photo du chantier
  // Ducros » ou « l'attestation de M. Martin ». Le rattachement est donc
  // l'axe de rangement naturel, et la liste plate le cachait : il fallait
  // lire chaque sous-titre un par un pour retrouver une piece.
  //
  // Le regroupement reprend le geste du repertoire des clients (une
  // en-tete quand la cle change), applique a un autre axe. Meme
  // grammaire, autre composition.
  const groupes = new Map();
  for (const d of affichees) {
    const chantier = d.chantier_id ? documentsChantiersCache.find((c) => c.id === d.chantier_id) : null;
    const client = d.client_id ? clientsCache.find((c) => c.id === d.client_id) : null;
    const cle = chantier ? `ch-${chantier.id}` : client ? `cl-${client.id}` : "aucun";
    if (!groupes.has(cle)) {
      groupes.set(cle, {
        titre: chantier ? chantier.titre : client ? client.nom : "Sans rattachement",
        type: chantier ? "Chantier" : client ? "Client" : null,
        items: [],
      });
    }
    groupes.get(cle).items.push(d);
  }
  // « Sans rattachement » ferme la marche : c'est le fourre-tout, il ne
  // doit pas ouvrir la page.
  const ordonnes = [...groupes.entries()].sort((a, b) => {
    if (a[0] === "aucun") return 1;
    if (b[0] === "aucun") return -1;
    return a[1].titre.localeCompare(b[1].titre, "fr");
  });

  list.innerHTML = ordonnes.map(([, g]) => `
    <div class="doc-groupe">
      <h4 class="doc-groupe-titre">
        ${g.type ? `<span class="doc-groupe-type">${g.type}</span>` : ""}${escapeHtml(g.titre)}
        <span class="doc-groupe-compte">${g.items.length}</span>
      </h4>
      ${g.items.map(renderDocumentCard).join("")}
    </div>`).join("");
  reapplyListSearch("documents-search", "#documents-list .doc-row");
}

async function loadDocuments() {
  const list = document.getElementById("documents-list");
  const compteur = document.getElementById("documents-compteur");
  list.innerHTML = skeletonCards();
  try {
    // Conformite : seule entite reelle qui porte une date d'expiration
    // (ConformiteOut.alerte/.jours_restants, voir backend/app/schemas.py) -
    // Document lui-meme n'en a aucune. Recuperee ici uniquement pour ce
    // deuxieme compteur, pas pour en faire une echeance "par document".
    const [documents, clients, chantiers, conformite] = await Promise.all([
      Api.listDocuments(),
      ensureClientsCache(),
      Api.listChantiers().catch(() => []),
      Api.listConformite().catch(() => []),
    ]);
    documentsCache = documents;
    documentsChantiersCache = chantiers;
    const clientSelect = document.getElementById("documents-client-filter");
    const chantierSelect = document.getElementById("documents-chantier-filter");
    clientSelect.innerHTML = `<option value="">Client</option>${clients.map((c) => `<option value="${c.id}">${escapeHtml(c.nom)}</option>`).join("")}`;
    chantierSelect.innerHTML = `<option value="">Chantier</option>${chantiers.map((c) => `<option value="${c.id}">${escapeHtml(c.titre)}</option>`).join("")}`;
    clientSelect.value = currentDocumentClient;
    chantierSelect.value = currentDocumentChantier;
    const echeances = conformite.filter((c) => c.alerte).length;
    if (compteur) {
      compteur.innerHTML = documents.length
        ? `<span class="doc-compteur-label">Documents</span><span class="pill pill-gray">${documents.length}</span>${
            echeances ? `<span class="doc-compteur-label">Échéances à surveiller</span><span class="pill pill-orange">${echeances}</span>` : ""
          }`
        : "";
    }
    if (documents.length === 0) {
      list.innerHTML = etatVide(
        "Vos documents vivront ici.",
        "Contrats, attestations d'assurance, plans, photos de chantier. Ils se rangent d'eux-mêmes par client et par chantier, pour que vous retrouviez une pièce sans vous souvenir de son nom.",
        { action: "show-document-form", libelle: "Ajouter un document" },
      );
      return;
    }
    renderDocumentsListFiltered();
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderDocumentCard(d) {
  const client = d.client_id ? clientsCache.find((c) => c.id === d.client_id) : null;
  const chantier = d.chantier_id ? documentsChantiersCache.find((c) => c.id === d.chantier_id) : null;
  const lienTxt = [client ? escapeHtml(client.nom) : "", chantier ? escapeHtml(chantier.titre) : ""].filter(Boolean).join(" · ");
  const meta = [d.taille_octets ? fmtTaille(d.taille_octets) : null, `Ajouté le ${fmtDate(d.created_at)}`].filter(Boolean).join(" · ");
  const estFichier = !!d.nom_original;
  return `
  <div class="doc-row">
    <span class="doc-row-icon"><svg viewBox="0 0 24 24" class="nav-icon"><path d="M7 2h7l5 5v15H7z"/><path d="M14 2v5h5"/></svg></span>
    <div class="doc-row-body">
      <div class="doc-row-title">${escapeHtml(d.nom)}</div>
      <div class="doc-row-sub">${lienTxt || "Sans rattachement"}</div>
    </div>
    <span class="pill ${DOCUMENT_TYPE_PILL[d.type] || "pill-gray"}">${DOCUMENT_TYPE_LABELS[d.type] || d.type}</span>
    <div class="doc-row-meta">${meta}</div>
    <div class="doc-row-action">
      ${estFichier
        ? `<button type="button" class="btn-sm" data-action="telecharger-document" data-id="${d.id}" data-nom="${escapeHtml(d.nom_original)}">Télécharger</button>`
        : `<a class="btn-sm" href="${escapeHtml(d.url)}" target="_blank" rel="noopener">Ouvrir le lien</a>`}
    </div>
    <div class="action-menu">
      <button type="button" class="action-menu-trigger" data-action="toggle-action-menu" aria-haspopup="true" aria-expanded="false" aria-label="Plus d'actions sur ce document">
        <svg viewBox="0 0 24 24" class="nav-icon"><circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/></svg>
      </button>
      <div class="action-menu-panel" role="menu">
        <button type="button" class="is-danger" data-action="delete-document" data-id="${d.id}">Supprimer</button>
      </div>
    </div>
  </div>`;
}

function showDocumentForm(preselectChantierId) {
  const container = document.getElementById("document-form-container");
  container.innerHTML = "";
  Promise.all([ensureClientsCache(), Api.listChantiers().catch(() => [])]).then(([clients, chantiers]) => {
    const chantierOptions = chantiers
      .map((c) => `<option value="${c.id}" ${preselectChantierId && c.id === preselectChantierId ? "selected" : ""}>${escapeHtml(c.titre)}</option>`)
      .join("");
    container.innerHTML = `
      <div class="form-box">
        <h3>Ajouter un document</h3>
        <form id="document-form">
          <div class="form-grid">
            <div><label for="doc-fichier">Fichier *</label><input type="file" id="doc-fichier" required accept=".pdf,.jpg,.jpeg,.png,.heic,.heif,.doc,.docx,.xls,.xlsx,.odt,.txt"></div>
            <div><label for="doc-nom">Nom (optionnel)</label><input type="text" id="doc-nom" placeholder="Par défaut : nom du fichier"></div>
            <div>
              <label for="doc-type">Type</label>
              <select id="doc-type">${Object.entries(DOCUMENT_TYPE_LABELS).map(([v, l]) => `<option value="${v}">${l}</option>`).join("")}</select>
            </div>
            <div><label for="doc-client">Client (optionnel)</label><select id="doc-client"><option value="">Aucun</option>${clientOptionsHtml()}</select></div>
            <div><label for="doc-chantier">Chantier (optionnel)</label><select id="doc-chantier"><option value="">Aucun</option>${chantierOptions}</select></div>
          </div>
          <p class="field-error" id="document-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
            <button type="button" class="btn-sm" data-action="cancel-document-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("document-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("document-form-error");
      errorBox.hidden = true;
      const fichier = document.getElementById("doc-fichier").files[0];
      if (!fichier) {
        errorBox.hidden = false;
        errorBox.textContent = "Choisissez un fichier.";
        return;
      }
      const formData = new FormData();
      formData.append("file", fichier);
      const nom = document.getElementById("doc-nom").value.trim();
      if (nom) formData.append("nom", nom);
      formData.append("type", document.getElementById("doc-type").value);
      const clientId = document.getElementById("doc-client").value;
      if (clientId) formData.append("client_id", clientId);
      const chantierId = document.getElementById("doc-chantier").value;
      if (chantierId) formData.append("chantier_id", chantierId);

      try {
        await Api.uploadDocument(formData);
        showToast("Document ajouté.");
        container.hidden = true;
        container.innerHTML = "";
        loadDocuments();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });
}

function setupDocumentsView() {
  document.querySelector('[data-action="show-document-form"]').addEventListener("click", showDocumentForm);
  document.getElementById("document-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-document-form"]')) {
      const container = document.getElementById("document-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("document-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#document-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentDocumentFilter = chip.dataset.type;
    document.getElementById("documents-type-filter").value = currentDocumentFilter;
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-type-filter").addEventListener("change", (e) => {
    currentDocumentFilter = e.target.value;
    document.querySelectorAll("#document-filters .filter-chip").forEach((chip) => chip.classList.toggle("active", chip.dataset.type === currentDocumentFilter));
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-client-filter").addEventListener("change", (e) => {
    currentDocumentClient = e.target.value;
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-chantier-filter").addEventListener("change", (e) => {
    currentDocumentChantier = e.target.value;
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-date-filter").addEventListener("change", (e) => {
    currentDocumentDate = e.target.value;
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-sort").addEventListener("change", (e) => {
    currentDocumentSort = e.target.value;
    renderDocumentsListFiltered();
  });

  document.getElementById("documents-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "telecharger-document") {
      await withErrorToast(() => telechargerDocument(id, btn.dataset.nom));
    } else if (btn.dataset.action === "delete-document") {
      if (!(await confirmDialog("Supprimer ce document ?", { danger: true }))) return;
      await withErrorToast(async () => {
        await Api.deleteDocument(id);
        showToast("Document supprimé.");
        loadDocuments();
      });
    }
  });
}

// ===================== Planning (calendrier jour/semaine/mois, drag & drop reel) =====================
const PLANNING_TYPE_LABELS = { rdv: "RDV", visite: "Visite", intervention: "Intervention", autre: "Autre", tache: "Tâche", chantier_debut: "Début chantier" };
const PLANNING_TYPE_CLASS = { rdv: "planning-item-blue", visite: "planning-item-blue", intervention: "planning-item-orange", autre: "planning-item-gray", tache: "planning-item-gray", chantier_debut: "planning-item-green" };

let planningViewMode = "semaine"; // jour | semaine | mois
let planningAnchorDate = new Date();

// Filtres (recherche + type/client/chantier) : purement client, appliques
// sur les items deja recus par Api.planning() pour la periode affichee -
// aucun nouvel appel reseau au changement de filtre, seulement un nouveau
// rendu depuis planningItemsCache. La periode courante est memorisee pour
// pouvoir re-rendre sans refaire un aller-retour serveur.
let planningFilters = { q: "", type: "", clientId: "", chantierId: "" };
let planningRangeDebut = null;
let planningRangeFin = null;
let planningChantiersCache = [];

function planningFilterItems(items) {
  const q = planningFilters.q.trim().toLowerCase();
  return items.filter((i) => {
    if (planningFilters.type && i.type !== planningFilters.type) return false;
    if (planningFilters.clientId && String(i.client_id || "") !== planningFilters.clientId) return false;
    if (planningFilters.chantierId && String(i.chantier_id || "") !== planningFilters.chantierId) return false;
    if (q && !`${i.titre} ${i.lieu || ""}`.toLowerCase().includes(q)) return false;
    return true;
  });
}

function planningFiltersHtml() {
  const typeOptions = Object.entries(PLANNING_TYPE_LABELS)
    .map(([v, l]) => `<option value="${v}" ${planningFilters.type === v ? "selected" : ""}>${escapeHtml(l)}</option>`)
    .join("");
  const clientOptions = clientsCache
    .map((c) => `<option value="${c.id}" ${planningFilters.clientId === String(c.id) ? "selected" : ""}>${escapeHtml(c.nom)}</option>`)
    .join("");
  const chantierOptions = planningChantiersCache
    .map((c) => `<option value="${c.id}" ${planningFilters.chantierId === String(c.id) ? "selected" : ""}>${escapeHtml(c.titre)}</option>`)
    .join("");
  return `
    <div class="planning-filters">
      <input type="text" id="planning-filtre-q" placeholder="Rechercher un client, chantier..." value="${escapeHtml(planningFilters.q)}">
      <select id="planning-filtre-type"><option value="">Type</option>${typeOptions}</select>
      <select id="planning-filtre-client"><option value="">Client</option>${clientOptions}</select>
      <select id="planning-filtre-chantier"><option value="">Chantier</option>${chantierOptions}</select>
    </div>`;
}

function renderPlanningFiltered() {
  renderPlanning(planningRangeDebut, planningRangeFin, planningFilterItems(planningItemsCache));
}

// Fuseau fixe (pas le fuseau ambiant du navigateur) : la cle "jour" d'une
// date doit rester la meme quel que soit le fuseau systeme de la machine qui
// affiche l'ecran, et gerer automatiquement le passage heure d'ete/hiver
// (Intl/IANA, jamais un decalage +1/+2 code en dur). Avant ce correctif,
// planningToIso() faisait d.toISOString().slice(0, 10) : ca convertit en UTC
// avant de lire la date, donc un evenement cree a 09:00 a Paris (UTC+2 l'ete)
// finissait range sur la case du jour suivant dans la grille - exactement le
// bug "29/08 09:00 affiche 30/08 07:00" remonte par le test manuel.
const PLANNING_TIMEZONE = "Europe/Paris";
const _planningIsoFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: PLANNING_TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
});
function planningToIso(d) {
  return _planningIsoFormatter.format(d);
}
function planningHeureLocale(d) {
  return new Date(d).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", timeZone: PLANNING_TIMEZONE });
}
// Decompose une date/heure en {date:"YYYY-MM-DD", heure:"HH:MM"} tels
// qu'ils doivent apparaitre dans les <input type="date">/<input type="time">
// du formulaire, evalues en Europe/Paris (jamais le fuseau ambiant) - sert a
// pre-remplir le formulaire d'edition avec exactement ce que l'artisan a
// saisi a la creation.
function planningDateHeureLocale(dateInput) {
  const d = new Date(dateInput);
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: PLANNING_TIMEZONE, hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d);
  const get = (t) => parts.find((p) => p.type === t)?.value || "00";
  return { date: planningToIso(d), heure: `${get("hour")}:${get("minute")}` };
}
// Inverse de planningDateHeureLocale() : convertit une date/heure saisie
// dans le formulaire (valeurs des <input type="date"/"time">, donc une heure
// murale en Europe/Paris) en instant UTC. `new Date(\`${date}T${heure}:00\`)`
// est ambigu : sans suffixe de fuseau, le moteur JS l'interprete dans le
// fuseau AMBIANT de la machine qui l'execute (navigateur ou environnement de
// test), pas forcement Europe/Paris - d'ou le decalage observe uniquement a
// la modification (la machine de test n'est pas forcement a l'heure de
// Paris). On calcule l'instant UTC explicitement : une premiere estimation
// naive, puis on lit comment cet instant s'affiche reellement en
// Europe/Paris via Intl et on corrige l'ecart. Fonctionne quel que soit le
// fuseau de la machine et gere nativement ete/hiver (jamais de +1h/+2h code
// en dur).
function planningLocalToUtcIso(dateStr, heureStr) {
  const [annee, mois, jour] = dateStr.split("-").map(Number);
  const [heure, minute] = heureStr.split(":").map(Number);
  const estimation = Date.UTC(annee, mois - 1, jour, heure, minute, 0);
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: PLANNING_TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  }).formatToParts(new Date(estimation));
  const get = (t) => parseInt(parts.find((p) => p.type === t)?.value || "0", 10);
  const afficheCommeUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour") % 24, get("minute"), get("second"));
  return new Date(estimation - (afficheCommeUtc - estimation)).toISOString();
}

function planningStartOfWeek(d) {
  const date = new Date(d);
  const jour = date.getDay(); // 0 = dimanche
  const decalage = jour === 0 ? -6 : 1 - jour; // lundi = premier jour
  date.setDate(date.getDate() + decalage);
  date.setHours(0, 0, 0, 0);
  return date;
}

function planningRange() {
  const anchor = new Date(planningAnchorDate);
  anchor.setHours(0, 0, 0, 0);
  if (planningViewMode === "jour") return [new Date(anchor), new Date(anchor)];
  if (planningViewMode === "semaine") {
    const debut = planningStartOfWeek(anchor);
    const fin = new Date(debut);
    fin.setDate(fin.getDate() + 6);
    return [debut, fin];
  }
  const premier = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const dernier = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0);
  const debut = planningStartOfWeek(premier);
  const fin = planningStartOfWeek(dernier);
  fin.setDate(fin.getDate() + 6);
  return [debut, fin];
}

function planningShift(direction) {
  const d = new Date(planningAnchorDate);
  if (planningViewMode === "jour") d.setDate(d.getDate() + direction);
  else if (planningViewMode === "semaine") d.setDate(d.getDate() + direction * 7);
  else d.setMonth(d.getMonth() + direction);
  return d;
}

function planningToolbarHtml(debut, fin) {
  const label = planningViewMode === "jour"
    ? debut.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
    : planningViewMode === "semaine"
      ? `${debut.toLocaleDateString("fr-FR", { day: "numeric", month: "short" })} – ${fin.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" })}`
      : planningAnchorDate.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
  return `
    <div class="planning-toolbar">
      <div class="planning-nav">
        <button type="button" class="btn-sm" data-action="planning-prev">&larr;</button>
        <button type="button" class="btn-sm" data-action="planning-today">Aujourd'hui</button>
        <button type="button" class="btn-sm" data-action="planning-next">&rarr;</button>
        <strong class="planning-label">${escapeHtml(label)}</strong>
      </div>
      <div class="planning-modes">
        ${["jour", "semaine", "mois"].map((m) => `<button type="button" class="btn-sm ${planningViewMode === m ? "btn-sm-primary" : ""}" data-action="planning-mode" data-mode="${m}">${m[0].toUpperCase()}${m.slice(1)}</button>`).join("")}
      </div>
    </div>`;
}

function planningItemChip(item, compact) {
  const heure = item.type === "chantier_debut" ? "" : `<span class="planning-item-heure">${planningHeureLocale(item.date)}</span> `;
  const ouvreFiche = item.type === "chantier_debut" || PLANNING_TYPES_EVENEMENT.has(item.type);
  return `<div class="planning-item ${PLANNING_TYPE_CLASS[item.type] || ""} ${ouvreFiche ? "planning-item-clickable" : ""}" draggable="${item.type === "chantier_debut" ? "false" : "true"}" data-type="${item.type}" data-ref-id="${item.reference_id}" data-current-date="${item.date}" ${ouvreFiche ? 'role="button" tabindex="0"' : ""} title="${escapeHtml(item.titre)}">
    ${compact ? "" : heure}<span class="planning-item-titre">${escapeHtml(item.titre)}</span>
  </div>`;
}

// Grille horaire (vues jour/semaine) : la vue "brief" precedente empilait les
// evenements du haut vers le bas sans notion d'heure, ce qui laissait la
// quasi-totalite de la colonne vide des qu'un jour avait 0-2 rendez-vous.
// Ici chaque evenement est positionne a sa vraie heure sur un axe 7h-20h -
// mêmes donnees (PlanningItem.date), seule la disposition change. Duree
// d'affichage fixe (1h) : l'API de planning ne renvoie pas de duree de fin
// pour les items agreges (evenements + taches + debut de chantier).
const PLANNING_HOUR_START = 7;
const PLANNING_HOUR_END = 20; // 13h affichees ; les items hors plage restent visibles, ancres au bord.
const PLANNING_ROW_H = 41; // px par heure - garder synchronise avec les hauteurs CSS.

function planningTimeMinutes(dateVal) {
  const { heure } = planningDateHeureLocale(dateVal);
  const [h, m] = heure.split(":").map(Number);
  return h * 60 + m;
}

function planningHourRowsHtml() {
  let html = "";
  for (let h = PLANNING_HOUR_START; h < PLANNING_HOUR_END; h++) html += '<div class="planning-hour-row"></div>';
  return html;
}

function planningHourGutterHtml() {
  let html = '<div class="planning-hour-gutter"><div class="planning-hour-gutter-spacer"></div>';
  for (let h = PLANNING_HOUR_START; h < PLANNING_HOUR_END; h++) html += `<div class="planning-hour-label">${h}h</div>`;
  return html + "</div>";
}

function planningNowLineHtml() {
  const minutes = planningTimeMinutes(new Date());
  if (minutes < PLANNING_HOUR_START * 60 || minutes > PLANNING_HOUR_END * 60) return "";
  const top = ((minutes - PLANNING_HOUR_START * 60) / 60) * PLANNING_ROW_H;
  return `<div class="planning-now-line" style="top:${top}px;"><span class="planning-now-dot"></span></div>`;
}

// Attribue une colonne a chaque item par ordre chronologique (chevauchements
// rares pour un artisan seul sur son planning) : algorithme glouton simple,
// pas de vrai decoupage par cluster - un item tardif isole peut partager une
// largeur reduite avec un chevauchement plus tot dans la meme journee, cas
// limite juge acceptable au vu de la frequence.
function planningLayoutDay(dayItems) {
  const DUREE = 60;
  const columns = [];
  const placed = dayItems.map((item) => {
    const start = planningTimeMinutes(item.date);
    let col = columns.findIndex((endTime) => endTime <= start);
    if (col === -1) { col = columns.length; columns.push(start + DUREE); }
    else columns[col] = start + DUREE;
    return { item, start, col };
  });
  const totalCols = Math.max(1, columns.length);
  return placed.map((p) => ({ ...p, totalCols }));
}

function planningPositionedItemHtml({ item, start, col, totalCols }) {
  const maxTop = (PLANNING_HOUR_END - PLANNING_HOUR_START) * PLANNING_ROW_H - PLANNING_ROW_H + 4;
  const top = Math.min(Math.max(0, ((start - PLANNING_HOUR_START * 60) / 60) * PLANNING_ROW_H), maxTop);
  const widthPct = 100 / totalCols;
  const ouvreFiche = item.type === "chantier_debut" || PLANNING_TYPES_EVENEMENT.has(item.type);
  const heure = item.type === "chantier_debut" ? "" : `<span class="planning-item-heure">${planningHeureLocale(item.date)}</span> `;
  return `<div class="planning-item planning-item-positioned ${PLANNING_TYPE_CLASS[item.type] || ""} ${ouvreFiche ? "planning-item-clickable" : ""}"
    style="top:${top}px; height:${PLANNING_ROW_H - 4}px; left:calc(${col * widthPct}% + 2px); width:calc(${widthPct}% - 4px);"
    draggable="${item.type === "chantier_debut" ? "false" : "true"}" data-type="${item.type}" data-ref-id="${item.reference_id}" data-current-date="${item.date}"
    ${ouvreFiche ? 'role="button" tabindex="0"' : ""} title="${escapeHtml(item.titre)}">${heure}<span class="planning-item-titre">${escapeHtml(item.titre)}</span></div>`;
}

function planningDayCellHtml(dateObj, items, { compact = false, showWeekday = true, extraClass = "", hourGrid = false } = {}) {
  const iso = planningToIso(dateObj);
  // Comparaison sur la cle "jour" calculee en Europe/Paris des deux cotes
  // (jamais un slice(0,10) direct de la chaine UTC renvoyee par l'API) :
  // voir le commentaire de planningToIso() pour le bug que ca evite.
  const dayItems = items.filter((i) => planningToIso(new Date(i.date)) === iso).sort((a, b) => a.date.localeCompare(b.date));
  const isToday = iso === planningToIso(new Date());
  // Samedi/dimanche : marques ici plutot que par un nth-child cote CSS,
  // car les trois vues n'ont pas la meme structure de grille (le gutter
  // des heures occupe la premiere colonne en vue jour/semaine, sept
  // en-tetes precedent les cases en vue mois) - un calcul de position y
  // serait faux a la premiere evolution.
  const jourSemaine = dateObj.getDay();
  const isWeekend = jourSemaine === 0 || jourSemaine === 6;
  const headerLabel = showWeekday
    ? dateObj.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" })
    : String(dateObj.getDate());
  const body = hourGrid
    ? `<div class="planning-day-track">${planningHourRowsHtml()}${planningLayoutDay(dayItems).map(planningPositionedItemHtml).join("")}${isToday ? planningNowLineHtml() : ""}</div>`
    : `<div class="planning-day-items">${dayItems.map((i) => planningItemChip(i, compact)).join("") || (compact ? "" : '<div class="planning-day-empty">Rien de prévu</div>')}</div>`;
  return `
    <div class="planning-day-cell ${isToday ? "is-today" : ""} ${isWeekend ? "is-weekend" : ""} ${hourGrid ? "has-hour-grid" : ""} ${extraClass}" data-date="${iso}">
      <div class="planning-day-header">${headerLabel}</div>
      ${body}
    </div>`;
}

function renderPlanning(debut, fin, items) {
  const container = document.getElementById("planning-content");
  const jours = [];
  for (let d = new Date(debut); d <= fin; d.setDate(d.getDate() + 1)) jours.push(new Date(d));

  let gridHtml;
  if (planningViewMode === "jour") {
    gridHtml = `<div class="planning-day-view">${planningHourGutterHtml()}${planningDayCellHtml(debut, items, { compact: false, showWeekday: true, hourGrid: true })}</div>`;
  } else if (planningViewMode === "semaine") {
    gridHtml = `<div class="planning-week-grid">${planningHourGutterHtml()}${jours.map((j) => planningDayCellHtml(j, items, { compact: false, showWeekday: true, hourGrid: true })).join("")}</div>`;
  } else {
    const moisAnchor = planningAnchorDate.getMonth();
    gridHtml = `<div class="planning-month-grid">
      ${["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((j) => `<div class="planning-month-weekday">${j}</div>`).join("")}
      ${jours.map((j) => planningDayCellHtml(j, items, { compact: true, showWeekday: false, extraClass: j.getMonth() !== moisAnchor ? "is-outside-month" : "" })).join("")}
    </div>`;
  }
  container.innerHTML = planningToolbarHtml(debut, fin) + planningFiltersHtml() + gridHtml;
}

// Derniers items charges, pour retrouver le detail complet (lieu, client_id...)
// d'un rendez-vous au clic sans re-appeler l'API.
let planningItemsCache = [];

async function loadPlanning() {
  const container = document.getElementById("planning-content");
  container.innerHTML = skeletonCards();
  try {
    const [debut, fin] = planningRange();
    planningRangeDebut = debut;
    planningRangeFin = fin;
    const [items] = await Promise.all([
      Api.planning(planningToIso(debut), planningToIso(fin)),
      ensureClientsCache(),
    ]);
    planningItemsCache = items;
    // Chantiers pour le filtre uniquement (repli silencieux comme ailleurs
    // si le plan ne les autorise pas) - meme endpoint que la page Chantiers.
    planningChantiersCache = await Api.listChantiers().catch(() => []);
    renderPlanningFiltered();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// Types de planning correspondant a une ligne Evenement reelle (donc
// consultable/modifiable/supprimable) - "tache" et "chantier_debut" sont
// calcules a la volee depuis d'autres tables (voir routers/planning.py) et
// n'ont pas d'Evenement associe.
const PLANNING_TYPES_EVENEMENT = new Set(["rdv", "visite", "intervention", "autre"]);

function evenementDetailHtml(item) {
  const client = item.client_id ? clientsCache.find((c) => c.id === item.client_id) : null;
  const dateLabel = new Date(item.date).toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: PLANNING_TIMEZONE,
  });
  return `
    <div class="profil-row"><div class="label">Type</div><div class="value">${escapeHtml(PLANNING_TYPE_LABELS[item.type] || item.type)}</div></div>
    <div class="profil-row"><div class="label">Date</div><div class="value">${escapeHtml(dateLabel)}</div></div>
    <div class="profil-row"><div class="label">Heure</div><div class="value">${planningHeureLocale(item.date)}</div></div>
    ${client ? `<div class="profil-row"><div class="label">Client</div><div class="value">${escapeHtml(client.nom)}</div></div>` : ""}
    ${item.lieu ? `<div class="profil-row"><div class="label">Lieu</div><div class="value">${escapeHtml(item.lieu)}</div></div>` : ""}
  `;
}

let planningEvenementDetailItem = null;

async function ouvrirDetailEvenement(item) {
  await ensureClientsCache();
  planningEvenementDetailItem = item;
  document.getElementById("evenement-detail-titre").textContent = item.titre;
  document.getElementById("evenement-detail-body").innerHTML = evenementDetailHtml(item);
  document.getElementById("evenement-detail-modal").hidden = false;
}
function fermerDetailEvenement() {
  document.getElementById("evenement-detail-modal").hidden = true;
  planningEvenementDetailItem = null;
}

document.addEventListener("click", async (e) => {
  if (e.target.closest('[data-action="close-evenement-detail"]') || e.target.id === "evenement-detail-modal") {
    fermerDetailEvenement();
  } else if (e.target.closest('[data-action="modifier-evenement"]')) {
    const item = planningEvenementDetailItem;
    if (!item) return;
    fermerDetailEvenement();
    switchView("planning");
    setTimeout(() => window.showEvenementForm({
      evenementId: item.reference_id, titre: item.titre, type: item.type,
      date: item.date, lieu: item.lieu, clientId: item.client_id, chantierId: item.chantier_id,
    }), 50);
  } else if (e.target.closest('[data-action="supprimer-evenement"]')) {
    const item = planningEvenementDetailItem;
    if (!item) return;
    const confirme = await confirmDialog(`Supprimer le rendez-vous "${item.titre}" ?`, { title: "Supprimer", confirmLabel: "Supprimer", danger: true });
    if (!confirme) return;
    await withErrorToast(async () => {
      await Api.deleteEvenement(item.reference_id);
      showToast("Rendez-vous supprimé.");
      fermerDetailEvenement();
      loadPlanning();
    });
  }
});
document.addEventListener("keydown", (e) => {
  // Si la confirmation de suppression est ouverte par-dessus, elle gere son
  // propre Echap (voir confirmDialog()) : sans ce garde-fou, les deux
  // ecouteurs Echap se declenchaient sur la meme frappe et refermaient les
  // deux modales d'un coup, alors qu'Annuler doit ramener au detail du
  // rendez-vous, pas tout fermer.
  if (e.key === "Escape" && !document.getElementById("evenement-detail-modal").hidden && document.getElementById("confirm-dialog").hidden) {
    fermerDetailEvenement();
  }
});

function setupPlanningView() {
  async function showEvenementForm(prefill = {}) {
    const container = document.getElementById("evenement-form-container");
    await ensureClientsCache();
    const isEdit = !!prefill.evenementId;
    // Date/heure pre-remplies en Europe/Paris (jamais le fuseau ambiant) :
    // reouvrir un rendez-vous en edition doit remontrer exactement la date
    // et l'heure que l'artisan avait saisies, pas un decalage.
    const { date: dateVal, heure: heureVal } = prefill.date ? planningDateHeureLocale(prefill.date) : { date: "", heure: "09:00" };
    container.innerHTML = `
      <div class="form-box">
        <h3>${isEdit ? "Modifier le rendez-vous" : prefill.titre ? "Planifier une intervention" : "Nouveau rendez-vous"}</h3>
        <form id="evenement-form">
          <div class="form-grid">
            <div><label for="ev-titre">Titre *</label><input type="text" id="ev-titre" value="${escapeHtml(prefill.titre || "")}" required></div>
            <div>
              <label for="ev-type">Type</label>
              <select id="ev-type">
                <option value="rdv" ${prefill.type === "rdv" ? "selected" : ""}>Rendez-vous</option>
                <option value="visite" ${prefill.type === "visite" ? "selected" : ""}>Visite</option>
                <option value="intervention" ${prefill.type === "intervention" ? "selected" : ""}>Intervention</option>
                <option value="autre" ${prefill.type === "autre" ? "selected" : ""}>Autre</option>
              </select>
            </div>
            <div><label for="ev-date">Date *</label><input type="date" id="ev-date" value="${escapeHtml(dateVal)}" required></div>
            <div><label for="ev-heure">Heure</label><input type="time" id="ev-heure" value="${escapeHtml(heureVal)}"></div>
            <div><label for="ev-client">Client (optionnel)</label><select id="ev-client"><option value="">Aucun</option>${clientOptionsHtml(prefill.clientId)}</select></div>
            <div><label for="ev-lieu">Lieu</label><input type="text" id="ev-lieu" value="${escapeHtml(prefill.lieu || "")}"></div>
          </div>
          <p class="field-error" id="evenement-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">${isEdit ? "Enregistrer" : "Créer"}</button>
            <button type="button" class="btn-sm" data-action="cancel-evenement-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("evenement-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("evenement-form-error");
      errorBox.hidden = true;
      const dateVal = document.getElementById("ev-date").value;
      const heureVal = document.getElementById("ev-heure").value || "09:00";
      const clientVal = document.getElementById("ev-client").value;
      const payload = {
        titre: document.getElementById("ev-titre").value,
        type: document.getElementById("ev-type").value,
        date_debut: planningLocalToUtcIso(dateVal, heureVal),
        lieu: emptyToNull(document.getElementById("ev-lieu").value),
        client_id: clientVal ? parseInt(clientVal, 10) : null,
        chantier_id: prefill.chantierId || null,
      };
      try {
        if (isEdit) {
          await Api.updateEvenement(prefill.evenementId, payload);
          showToast("Rendez-vous mis à jour.");
        } else {
          await Api.createEvenement(payload);
          showToast("Rendez-vous créé.");
        }
        container.hidden = true;
        container.innerHTML = "";
        loadPlanning();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  }
  window.showEvenementForm = showEvenementForm;

  document.querySelector('[data-action="show-evenement-form"]').addEventListener("click", () => showEvenementForm());

  document.getElementById("evenement-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-evenement-form"]')) {
      const container = document.getElementById("evenement-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  const planningContent = document.getElementById("planning-content");

  planningContent.addEventListener("click", (e) => {
    const chip = e.target.closest(".planning-item");
    if (chip) {
      const item = planningItemsCache.find(
        (i) => String(i.reference_id) === chip.dataset.refId && i.type === chip.dataset.type,
      );
      if (item && item.type === "chantier_debut") ouvrirChantierDepuisPlanning(item.chantier_id || item.reference_id);
      else if (item && PLANNING_TYPES_EVENEMENT.has(item.type)) ouvrirDetailEvenement(item);
      return;
    }
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    if (btn.dataset.action === "planning-prev") {
      planningAnchorDate = planningShift(-1);
      loadPlanning();
    } else if (btn.dataset.action === "planning-next") {
      planningAnchorDate = planningShift(1);
      loadPlanning();
    } else if (btn.dataset.action === "planning-today") {
      planningAnchorDate = new Date();
      loadPlanning();
    } else if (btn.dataset.action === "planning-mode") {
      planningViewMode = btn.dataset.mode;
      loadPlanning();
    }
  });

  // Filtres : jamais un rechargement serveur, seulement un nouveau rendu
  // depuis planningItemsCache (deja recu pour la periode affichee).
  planningContent.addEventListener("input", (e) => {
    if (e.target.id === "planning-filtre-q") {
      const pos = e.target.selectionStart;
      planningFilters.q = e.target.value;
      renderPlanningFiltered();
      // renderPlanningFiltered() remplace tout innerHTML(donc aussi ce
      // champ) a chaque frappe : sans ca, le focus et le curseur sauteraient
      // au debut du champ apres chaque caractere tape.
      const nouveauChamp = document.getElementById("planning-filtre-q");
      nouveauChamp?.focus();
      nouveauChamp?.setSelectionRange(pos, pos);
    }
  });
  planningContent.addEventListener("change", (e) => {
    if (e.target.id === "planning-filtre-type") planningFilters.type = e.target.value;
    else if (e.target.id === "planning-filtre-client") planningFilters.clientId = e.target.value;
    else if (e.target.id === "planning-filtre-chantier") planningFilters.chantierId = e.target.value;
    else return;
    renderPlanningFiltered();
  });

  planningContent.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches(".planning-item-clickable")) {
      e.preventDefault();
      e.target.click();
    }
  });

  planningContent.addEventListener("dragstart", (e) => {
    const chip = e.target.closest(".planning-item");
    if (!chip || chip.dataset.type === "chantier_debut") {
      e.preventDefault();
      return;
    }
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", JSON.stringify({
      type: chip.dataset.type, refId: chip.dataset.refId, currentDate: chip.dataset.currentDate,
    }));
  });

  planningContent.addEventListener("dragover", (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (!cell) return;
    e.preventDefault();
    cell.classList.add("drag-over");
  });

  planningContent.addEventListener("dragleave", (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (cell) cell.classList.remove("drag-over");
  });

  planningContent.addEventListener("drop", async (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (!cell) return;
    e.preventDefault();
    cell.classList.remove("drag-over");
    let data;
    try {
      data = JSON.parse(e.dataTransfer.getData("text/plain"));
    } catch (err) {
      return;
    }
    const newDate = cell.dataset.date;
    // planningToIso(...) des deux cotes (jamais un slice(0,10) direct de la
    // chaine UTC) : voir le commentaire de planningToIso() plus haut.
    if (planningToIso(new Date(data.currentDate)) === newDate) return;

    await withErrorToast(async () => {
      if (data.type === "tache") {
        await Api.updateTache(parseInt(data.refId, 10), { echeance: newDate });
      } else if (PLANNING_TYPES_EVENEMENT.has(data.type)) {
        const oldDate = new Date(data.currentDate);
        const [y, m, d] = newDate.split("-").map(Number);
        const combined = new Date(oldDate);
        combined.setFullYear(y, m - 1, d);
        await Api.updateEvenement(parseInt(data.refId, 10), { date_debut: combined.toISOString() });
      } else {
        return;
      }
      showToast("Deplace au " + new Date(newDate + "T00:00:00").toLocaleDateString("fr-FR"));
      loadPlanning();
    });
  });
}

// ===================== Conformite =====================
async function loadConformite() {
  const list = document.getElementById("conformite-list");
  const banner = document.getElementById("conformite-alert-banner");
  const newBtn = document.querySelector('[data-action="show-conformite-form"]');
  const formContainer = document.getElementById("conformite-form-container");

  if (!hasPlan("essentiel")) {
    newBtn.hidden = true;
    formContainer.hidden = true;
    formContainer.innerHTML = "";
    banner.hidden = true;
    list.innerHTML = renderUpgradeCard(
      "Conformité réservée aux abonnés",
      "Le suivi des échéances (assurance décennale, Qualibat, RGE) et les alertes automatiques font partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  newBtn.hidden = false;

  list.innerHTML = skeletonCards();
  try {
    const [items, alertes] = await Promise.all([Api.listConformite(), Api.conformiteAlertes()]);

    if (alertes.length > 0) {
      banner.hidden = false;
      // « 1 élément(s) ... arrivent » : la parenthese evite d'accorder le nom
      // mais laisse le verbe faux. Deux phrases coutent moins qu'une phrase
      // qui sonne comme un message d'erreur de developpeur.
      banner.textContent = alertes.length === 1
        ? "Un élément de conformité arrive à échéance dans moins de 30 jours, ou est déjà expiré."
        : `${alertes.length} éléments de conformité arrivent à échéance dans moins de 30 jours, ou sont déjà expirés.`;
    } else {
      banner.hidden = true;
    }

    if (items.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun élément de conformité enregistré.</div>';
      return;
    }
    list.innerHTML = items.map(renderConformiteCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderConformiteCard(item) {
  const badgeClass = item.alerte ? "badge-red" : "badge-green";
  const badgeLabel = item.jours_restants < 0 ? "Expiré" : item.alerte ? `Expire dans ${item.jours_restants} j` : "À jour";
  const typeLabel = CONFORMITE_TYPE_LABELS[item.type] || item.type;
  return `
  <div class="item-card enterprise-record ${item.alerte ? "is-due" : ""}">
    <div class="enterprise-record-main">
      <div class="item-title">${escapeHtml(item.libelle)}</div>
      <div class="item-sub">${escapeHtml(typeLabel)}</div>
      <div class="item-meta">
        Échéance : ${fmtDate(item.date_expiration)}
        ${item.document_url ? ` · <a href="${escapeHtml(item.document_url)}" target="_blank" rel="noopener">Document</a>` : ""}
      </div>
    </div>
    <span class="badge enterprise-record-status ${badgeClass}">${badgeLabel}</span>
    <div class="item-actions enterprise-record-actions">
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-conformite" data-id="${item.id}">Supprimer</button>
    </div>
  </div>`;
}

function setupConformiteView() {
  document.querySelector('[data-action="show-conformite-form"]').addEventListener("click", () => {
    const container = document.getElementById("conformite-form-container");
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouvel élément de conformité</h3>
        <form id="conformite-form">
          <div class="form-grid">
            <div>
              <label for="cof-type">Type *</label>
              <select id="cof-type">
                <option value="assurance_decennale">Assurance decennale</option>
                <option value="qualibat">Qualibat</option>
                <option value="rge">RGE</option>
                <option value="autre">Autre</option>
              </select>
            </div>
            <div><label for="cof-libelle">Libelle *</label><input type="text" id="cof-libelle" required placeholder="Ex: AXA - Attestation decennale"></div>
            <div><label for="cof-date">Date d'expiration *</label><input type="date" id="cof-date" required></div>
            <div><label for="cof-doc">URL du document (optionnel)</label><input type="url" id="cof-doc" placeholder="https://..."></div>
          </div>
          <p class="field-error" id="conformite-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Ajouter</button>
            <button type="button" class="btn-sm" data-action="cancel-conformite-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("conformite-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("conformite-form-error");
      errorBox.hidden = true;
      try {
        await Api.createConformite({
          type: document.getElementById("cof-type").value,
          libelle: document.getElementById("cof-libelle").value,
          date_expiration: document.getElementById("cof-date").value,
          document_url: emptyToNull(document.getElementById("cof-doc").value),
        });
        showToast("Element de conformite ajoute.");
        container.hidden = true;
        container.innerHTML = "";
        loadConformite();
        refreshBadges();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });

  document.getElementById("conformite-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-conformite-form"]')) {
      const container = document.getElementById("conformite-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("conformite-list").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="delete-conformite"]');
    if (!btn) return;
    if (!(await confirmDialog("Supprimer cet element de conformite ?", { danger: true }))) return;
    const id = parseInt(btn.dataset.id, 10);
    await withErrorToast(async () => {
      await Api.deleteConformite(id);
      showToast("Element supprime.");
      loadConformite();
      refreshBadges();
    });
  });
}

// ===================== Recherche de liste (generique) =====================
// Champ de recherche present sur toutes les references (Prospects, Clients,
// Devis, Factures, Chantiers, Documents, Avis, Notifications) mais absent
// jusqu'ici de notre reproduction, sauf Planning. Purement visuel : cache
// par correspondance de texte les elements DEJA rendus par les load*()
// existants - aucun nouvel appel, aucun recalcul metier. Le selecteur est
// toujours prefixe par l'id du conteneur de LA page consultee, pour ne
// jamais affecter les elements (memes classes) d'une autre page encore
// presente, cachee, dans le DOM.
// Reapplicable (pas seulement branchee sur "input") : un tri ou un filtre
// par onglet regenere le HTML de la liste et doit donc reappliquer la
// recherche en cours par-dessus, sinon un texte deja tape serait ignore au
// rendu suivant.
function reapplyListSearch(inputId, itemSelector) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const q = input.value.trim().toLowerCase();
  document.querySelectorAll(itemSelector).forEach((el) => {
    el.hidden = !!q && !el.textContent.toLowerCase().includes(q);
  });
}

function setupListeSearch(inputId, itemSelector) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.addEventListener("input", () => reapplyListSearch(inputId, itemSelector));
}

function setupListesSearch() {
  // Pas de recherche sur Prospects : la reference (02-prospects) n'en montre
  // pas sur cette vue, et l'utilisateur a explicitement demande son retrait.
  // Clients : recherche geree par la page (voir clientMatchesRecherche).
  // Le masquage generique compare le textContent des lignes DEJA
  // AFFICHEES : il ne cherchait donc que dans la page courante, et
  // paraissait ne rien trouver des que le client cherche etait ailleurs.
  document.getElementById("clients-search")?.addEventListener("input", (e) => {
    clientsRecherche = e.target.value;
    currentClientsPage = 1;
    renderClientsDirectoryPage();
  });
  setupListeSearch("devis-search", "#devis-list .list-row");
  setupListeSearch("factures-search", "#factures-list .list-row");
  // Chantiers : recherche geree par la page (voir chantierMatchesRecherche).
  // Le masquage generique compare le textContent de la carte entiere, donc
  // aussi les libelles de l'interface - taper "note" faisait disparaitre
  // des chantiers au hasard, et laissait la liste vide sans rien expliquer.
  setupListeSearch("documents-search", "#documents-list .doc-row");
  setupListeSearch("avis-search", "#avis-list .avis-card");
  setupListeSearch("notifications-search", "#notifications-list .notif-row");
  setupListeSearch("taches-search", "#taches-list .tache-row");
}

// ===================== Initialisation =====================
document.addEventListener("DOMContentLoaded", async () => {
  onUnauthorized = () => {
    showAuthScreen();
    showToast("Votre session a expiré, merci de vous reconnecter.", true);
  };

  setupAuthScreen();
  setupTabs();
  setupMobileNav();
  setupTopbar();
  setupActionMenus();
  setupProfilPanel();
  setupGlobalSearch();
  setupDashboardView();
  setupClientsView();
  setupArchivesPanel();
  setupEntrepriseTabs();
  setupEntrepriseForm();
  setupProfilePhoto();
  setupSiteMedia();
  setupAutomatisationForm();
  setupEquipeView();
  setupPrestationsView();
  setupFournisseursView();
  setupContratsView();
  setupDevisView();
  setupFacturesView();
  setupChantiersView();
  setupPlanningView();
  setupTachesView();
  setupDocumentsView();
  setupNotificationsView();
  setupAvisView();
  setupConformiteView();
  setupListesSearch();

  const toast = document.createElement("div");
  toast.id = "toast";
  document.body.appendChild(toast);

  const params = new URLSearchParams(window.location.search);
  const abonnement = params.get("abonnement");
  if (abonnement) {
    window.history.replaceState({}, "", window.location.pathname);
  }

  const token = getToken();
  if (token) {
    try {
      currentArtisan = await Api.me();
      currentUtilisateur = await Api.moi();
      enterDashboard();
      if (abonnement === "succes") {
        showToast("Paiement reçu ! Votre abonnement Pro s'active dans quelques instants.");
      } else if (abonnement === "annule") {
        showToast("Abonnement annulé, vous pouvez réessayer à tout moment depuis votre profil.", true);
      }
      return;
    } catch (err) {
      clearToken();
    }
  }
  showAuthScreen();
});
