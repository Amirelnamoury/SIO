// ===================== Etat global =====================
let currentArtisan = null;
let currentUtilisateur = null; // { role, nom, email, membre_id } - qui est precisement connecte
let currentDevisFilter = "";
let devisDueIds = new Set();

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
function fmtDateTime(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("fr-FR");
}
function fmtEuro(n) {
  if (n === null || n === undefined) return null;
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(n);
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
    ${isPro ? '<span class="plan-badge">Recommande</span>' : ""}
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
      <h3>${escapeHtml(step.title)}</h3>
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
  document.querySelectorAll(".nav-link").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  // Sur mobile, la nav devient une rangee horizontale scrollable : sans ca,
  // l'onglet actif peut rester hors champ apres un changement de vue
  // programmatique (recherche globale, palette de commandes...).
  const activeLink = document.querySelector(`.nav-link[data-view="${view}"]`);
  if (activeLink) activeLink.scrollIntoView({ inline: "center", block: "nearest" });
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
      <div class="profil-row"><div class="label">Entreprise</div><div class="value">${escapeHtml(currentArtisan.nom_entreprise)}</div></div>
      <div class="profil-row"><div class="label">Métier</div><div class="value">${escapeHtml(METIER_LABELS[currentArtisan.metier] || currentArtisan.metier)}</div></div>
      <div class="profil-row"><div class="label">Email</div><div class="value">${escapeHtml(currentArtisan.email)}</div></div>
      <div class="profil-row"><div class="label">Ville</div><div class="value">${escapeHtml(currentArtisan.ville || "-")}</div></div>
      <div class="profil-row"><div class="label">SIRET</div><div class="value">${escapeHtml(currentArtisan.siret || "-")}</div></div>
      <div class="profil-row">
        <div class="label">Abonnement Suite Artisan</div>
        <div class="value">
          <span class="badge ${isBillingSubscriptionActive() ? "badge-green" : "badge-gray"}">${isBillingSubscriptionActive() ? "Actif" : "Inactif"}</span>
        </div>
        ${!isBillingSubscriptionActive() ? '<button type="button" class="btn-primary" data-action="upgrade-subscription" style="margin-top:10px;width:100%;">Voir les tarifs</button>' : ""}
      </div>
      <div class="dash-section" style="margin-top:20px;">
        <h3 style="font-size:0.95rem;">Changer le mot de passe</h3>
        <form id="password-change-form" class="form-box" style="padding:0;border:none;">
          <label for="pwd-actuel">Mot de passe actuel</label>
          <input type="password" id="pwd-actuel" required autocomplete="current-password">
          <label for="pwd-nouveau" style="margin-top:10px;">Nouveau mot de passe</label>
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
function loadEntrepriseForm() {
  document.getElementById("ent-nom-entreprise").value = currentArtisan.nom_entreprise || "";
  document.getElementById("ent-metier").value = currentArtisan.metier || "general";
  document.getElementById("ent-telephone").value = currentArtisan.telephone || "";
  document.getElementById("ent-ville").value = currentArtisan.ville || "";
  document.getElementById("ent-code-postal").value = currentArtisan.code_postal || "";
  document.getElementById("ent-adresse").value = currentArtisan.adresse || "";
  document.getElementById("ent-siret").value = currentArtisan.siret || "";
  document.getElementById("ent-assurance").value = currentArtisan.assurance_decennale_nom || "";
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
      showToast("Informations enregistrees.");
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
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
      list.innerHTML = '<div class="empty-state">Personne dans votre équipe pour le moment. Vous êtes seul(e) sur ce compte.</div>';
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
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(m.nom)}${estMoi ? " (vous)" : ""}</div>
        <div class="item-sub">${escapeHtml(m.email)}</div>
      </div>
      <span class="badge ${m.role === "administrateur" ? "badge-blue" : "badge-gray"}">${MEMBRE_ROLE_LABELS[m.role] || m.role}</span>
    </div>
    ${!m.actif ? '<div class="item-meta"><span class="badge badge-gray">Désactivé</span></div>' : ""}
    ${actions ? `<div class="item-actions">${actions}</div>` : ""}
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
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(p.description)}</div>
        <div class="item-sub">${escapeHtml(p.categorie || PRESTATION_CATEGORIE_DEFAUT)} · ${escapeHtml(p.unite)} · TVA ${p.taux_tva}%</div>
      </div>
      <strong>${fmtEuro(p.prix_unitaire_ht)}</strong>
    </div>
    <div class="item-actions">
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
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(f.nom)}</div>
        <div class="item-sub">${contact || "Pas de contact renseigné"}</div>
      </div>
      <span class="badge badge-gray">${FOURNISSEUR_CATEGORIE_LABELS[f.categorie] || f.categorie}</span>
    </div>
    ${f.total_achats > 0 ? `<div class="item-meta">Total achats : ${fmtEuro(f.total_achats)}</div>` : ""}
    <div class="item-actions">
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
    const stats = [
      { label: "CA (12 derniers mois)", value: fmtEuro(a.ca_par_mois.reduce((s, m) => s + m.ca, 0)) },
      { label: "Valeur du pipeline", value: fmtEuro(a.valeur_pipeline) },
      { label: "Impayés", value: fmtEuro(a.montant_impayes) },
      { label: "Devis envoyés", value: a.nb_devis_total },
      { label: "Devis signés", value: a.nb_devis_signes },
      { label: "Taux d'acceptation", value: `${a.taux_acceptation}%` },
      { label: "Panier moyen", value: fmtEuro(a.panier_moyen) },
      { label: "Délai moyen de paiement", value: a.delai_moyen_paiement_jours !== null ? `${a.delai_moyen_paiement_jours} j` : "-" },
      { label: "Clients acquis", value: a.nb_clients_acquis },
      { label: "Clients récurrents", value: a.nb_clients_recurrents },
    ];
    const statsHtml = stats.map((s) => `<div class="dash-stat"><div class="value">${s.value}</div><div class="label">${escapeHtml(s.label)}</div></div>`).join("");

    const moisHtml = a.ca_par_mois.length
      ? a.ca_par_mois.map((m) => `<div class="dash-row"><span>${escapeHtml(m.mois)}</span><strong>${fmtEuro(m.ca)}</strong></div>`).join("")
      : '<div class="dash-empty">Pas encore de paiement enregistre.</div>';

    const sourcesHtml = a.sources_acquisition.length
      ? a.sources_acquisition.map((s) => `<div class="dash-row"><span>${escapeHtml(CLIENT_SOURCE_LABELS[s.source] || s.source)}</span><strong>${s.nb_clients} contact${s.nb_clients > 1 ? "s" : ""} · ${s.nb_gagnes} gagne${s.nb_gagnes > 1 ? "s" : ""} · ${fmtEuro(s.ca)}</strong></div>`).join("")
      : '<div class="dash-empty">Pas encore de contact enregistre.</div>';

    const nbMax = a.funnel_site.length ? a.funnel_site[0].nb : 0;
    const funnelHtml = a.funnel_site.length
      ? a.funnel_site.map((e) => `
        <div class="sante-sous-score" style="margin-bottom:10px;">
          <div class="ligne"><span>${escapeHtml(e.etape)}</span><span class="valeur">${e.nb}</span></div>
          <div class="sante-barre"><div class="remplissage" style="width:${nbMax ? Math.round(e.nb / nbMax * 100) : 0}%;background:var(--info);"></div></div>
        </div>`).join("")
      : "";

    container.innerHTML = `
      <div class="dash-grid">${statsHtml}</div>
      <div class="dash-section">
        <h3>CA par mois</h3>
        ${moisHtml}
      </div>
      <div class="dash-section">
        <h3>Sources d'acquisition</h3>
        ${sourcesHtml}
      </div>
      ${funnelHtml ? `<div class="dash-section"><h3>Entonnoir d'acquisition du site vitrine</h3>${funnelHtml}</div>` : ""}
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// ===================== Avis clients =====================
const AVIS_SOURCE_LABELS = { manuel: "Saisi à la main", lien_public: "Envoyé par le client" };

function starsText(note) {
  return "★".repeat(note) + "☆".repeat(5 - note);
}

function avisResumeHtml(avis) {
  if (avis.length === 0) return "";
  const moyenne = avis.reduce((s, a) => s + a.note, 0) / avis.length;
  return `
    <div class="dash-grid" style="margin-bottom:20px;">
      <div class="dash-stat"><div class="value">${moyenne.toFixed(1)}/5</div><div class="label">Note moyenne</div></div>
      <div class="dash-stat"><div class="value">${avis.length}</div><div class="label">Avis reçus</div></div>
    </div>`;
}

async function loadAvis() {
  const list = document.getElementById("avis-list");
  const resume = document.getElementById("avis-resume");
  list.innerHTML = skeletonCards();
  try {
    const [avis] = await Promise.all([Api.listAvis(), ensureClientsCache()]);
    resume.innerHTML = avisResumeHtml(avis);
    if (avis.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun avis pour le moment. Saisissez-en un, ou envoyez une demande d\'avis depuis la fiche d\'un client.</div>';
      return;
    }
    list.innerHTML = avis.map(renderAvisCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderAvisCard(a) {
  return `
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title" style="color:#f5a623;letter-spacing:2px;">${starsText(a.note)}</div>
        <div class="item-sub">${escapeHtml(a.client_nom || "Anonyme")} · ${fmtDate(a.created_at)}</div>
      </div>
      <span class="badge badge-gray">${AVIS_SOURCE_LABELS[a.source] || a.source}</span>
    </div>
    ${a.commentaire ? `<div class="item-meta">${escapeHtml(a.commentaire)}</div>` : ""}
    <div class="item-actions">
      <button type="button" class="btn-sm ${a.publie_site ? "btn-sm-primary" : ""}" data-action="toggle-publie-site" data-id="${a.id}" data-publie="${a.publie_site ? "1" : "0"}">
        ${a.publie_site ? "Publié sur le site" : "Publier sur le site"}
      </button>
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-avis" data-id="${a.id}">Supprimer</button>
    </div>
  </div>`;
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
async function loadNotifications() {
  const list = document.getElementById("notifications-list");
  list.innerHTML = skeletonCards();
  try {
    const notifications = await Api.listNotifications();
    if (notifications.length === 0) {
      list.innerHTML = '<div class="empty-state">Rien à signaler. Tout est à jour.</div>';
      return;
    }
    const importantes = notifications.filter((n) => n.urgent);
    const normales = notifications.filter((n) => !n.urgent);
    list.innerHTML = `
      ${importantes.length ? `<div class="notif-group"><p class="notif-group-title">Important</p>${importantes.map(notificationRowHtml).join("")}</div>` : ""}
      ${normales.length ? `<div class="notif-group"><p class="notif-group-title">À faire</p>${normales.map(notificationRowHtml).join("")}</div>` : ""}
    `;
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function notificationRowHtml(n) {
  return `
  <div class="notif-row ${n.urgent ? "is-urgent" : ""}">
    <span class="notif-dot"></span>
    <div class="notif-main">
      <span class="notif-title">${escapeHtml(n.titre)}</span>
      ${n.sous_titre ? `<span class="notif-sub">${escapeHtml(n.sous_titre)}</span>` : ""}
    </div>
    <span class="badge ${n.urgent ? "badge-red" : "badge-gray"}">${NOTIFICATION_TYPE_LABELS[n.type] || n.type}</span>
    <button type="button" class="btn-sm" data-action="voir-notification" data-view="${n.view}"
      data-notification-id="${n.notification_id || ""}" data-client-id="${n.client_id || ""}">Voir</button>
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

function setupNotificationsView() {
  document.getElementById("notifications-list").addEventListener("click", async (e) => {
    const btn = e.target.closest('[data-action="voir-notification"]');
    if (!btn) return;
    await withErrorToast(async () => {
      const notificationId = parseInt(btn.dataset.notificationId, 10);
      const clientId = parseInt(btn.dataset.clientId, 10);
      switchView(btn.dataset.view);
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
  rows += `<div class="dash-row"><span>Demandes reçues (30 derniers jours)</span><strong>${p.nb_demandes_30j}</strong></div>`;
  rows += `<div class="dash-row"><span>Demandes reçues (total)</span><strong>${p.nb_demandes_total}</strong></div>`;
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
  return `
  <div class="task-row ${classe}">
    <span class="task-dot"></span>
    <span class="task-row-text">${item.label}</span>
    <span class="task-row-actions">${actionBtn}${voirBtn}</span>
  </div>`;
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
  const couleur = s.valeur >= 70 ? "var(--success)" : s.valeur >= 40 ? "var(--warning)" : "var(--danger)";
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

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  container.innerHTML = skeletonCards();
  try {
    const [d, recommandations, sante, activation] = await Promise.all([
      Api.dashboard(), Api.dashboardRecommandations(), Api.dashboardSante(), Api.dashboardActivation(),
    ]);

    // Compte neuf : aucun client, devis ou facture pose encore. Un ecran de
    // KPI a 0 ne sert a rien ici - on montre un vrai point de depart a la
    // place, construit uniquement a partir de l'activation deja recue (les
    // memes drapeaux qui alimentent la checklist plus bas). Des qu'une seule
    // de ces trois choses existe, le dashboard standard reprend la main.
    const estCompteNeuf = !!activation && !activation.premier_client && !activation.premier_devis && !activation.premiere_facture;
    if (estCompteNeuf) {
      container.innerHTML = `
        <div class="dash-hero-empty">
          <h3>Votre espace est prêt</h3>
          <p>Ajoutez votre premier client, puis créez votre premier devis : le tableau de bord se remplit avec votre activité au fur et à mesure.</p>
          <div class="dash-hero-actions">
            <button type="button" class="btn-primary" data-action="dash-empty-client">Ajouter un client</button>
            <button type="button" class="btn-secondary" data-action="dash-empty-devis">Créer un devis</button>
          </div>
        </div>
        ${activationChecklistHtml(activation)}
      `;
      return;
    }

    // "A faire" = ce qui demande une action ; les rendez-vous du jour vivent
    // a part, dans le panneau "Aujourd'hui au planning" (meme donnee
    // d.aujourdhui.evenements, seule la place dans la page change).
    const prioriteItems = [
      ...d.aujourdhui.factures_en_retard.map((f) => ({
        urgence: "haute", view: "factures",
        label: `${escapeHtml(f.numero)} · ${escapeHtml(f.client_nom)} · ${fmtEuro(f.montant_restant)} en retard`,
        ...(hasPlan("essentiel") ? { action: "relancer-facture", actionId: f.id, actionLabel: "Relancer" } : {}),
      })),
      ...d.alertes_conformite.map((c) => ({
        urgence: c.jours_restants < 7 ? "haute" : "moyenne", view: "entreprise",
        label: `${escapeHtml(c.libelle)} · expire dans ${c.jours_restants} j`,
      })),
      ...d.aujourdhui.devis_a_relancer.map((dv) => ({
        urgence: "moyenne", view: "devis",
        label: `Relancer ${escapeHtml(dv.client_nom)} (${escapeHtml(dv.numero || "devis #" + dv.id)})`,
        ...(hasPlan("essentiel") && dv.relance_manuelle_possible !== false
          ? { action: "relancer-devis", actionId: dv.id, actionLabel: "Relancer" }
          : {}),
      })),
      ...d.aujourdhui.taches.map((t) => ({
        urgence: "moyenne", view: "taches",
        label: `Tache du jour : ${escapeHtml(t.titre)}`,
      })),
      ...d.aujourdhui.chantiers_a_venir.map((c) => ({
        urgence: "basse", view: "chantiers",
        label: `Chantier '${escapeHtml(c.titre)}' commence le ${fmtDate(c.date_debut)}`,
      })),
    ];

    const planningDuJourHtml = d.aujourdhui.evenements.length
      ? d.aujourdhui.evenements.map((e) => `
        <div class="dash-agenda-row" data-action="voir-notification" data-view="planning" role="button" tabindex="0">
          <span class="dash-agenda-heure">${new Date(e.date_debut).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span>
          <span class="dash-agenda-titre">${escapeHtml(e.titre)}</span>
        </div>`).join("")
      : '<div class="dash-empty">Rien de prévu aujourd\'hui.</div>';

    // Hierarchie de lecture : 1) ce qui demande une action maintenant, en
    // face du planning du jour (meme zone de lecture) ; 2) la bande KPI
    // financiere/commerciale, groupee ; 3) mise en route puis contenu
    // secondaire (recommandations/sante/presence), en retrait visuel.
    // Memes appels API, memes valeurs deja calculees cote serveur - seule
    // la composition change.
    container.innerHTML = `
      <div class="dash-top-grid">
        <div class="dash-section dash-main-col">
          <h3>À faire aujourd'hui</h3>
          ${prioriteItems.length
            ? `<div class="task-feed">${prioriteItems.map(taskRowHtml).join("")}</div>`
            : '<div class="dash-empty">Rien qui nécessite votre attention aujourd\'hui.</div>'}
        </div>
        <div class="dash-section dash-side-col">
          <h3>Aujourd'hui au planning</h3>
          <div class="dash-agenda">${planningDuJourHtml}</div>
        </div>
      </div>

      <div class="dash-section">
        <div class="kpi-row">
          <div class="kpi-inline is-primary"><span class="kpi-label">CA ce mois-ci</span><span class="kpi-value">${fmtEuro(d.finances.ca_mois)}</span></div>
          <div class="kpi-inline${d.finances.a_encaisser > 0 ? " is-alert" : ""}"><span class="kpi-label">À encaisser</span><span class="kpi-value">${fmtEuro(d.finances.a_encaisser)}</span></div>
          <div class="kpi-inline"><span class="kpi-label">Valeur du pipeline</span><span class="kpi-value">${fmtEuro(d.commercial.valeur_pipeline)}</span></div>
          <div class="kpi-inline"><span class="kpi-label">Devis en attente</span><span class="kpi-value">${d.commercial.devis_en_attente}</span></div>
        </div>
        <div class="kpi-row kpi-row-secondary">
          <div class="kpi-inline"><span class="kpi-label">Taux de transformation</span><span class="kpi-value">${d.commercial.taux_transformation}%</span></div>
          <div class="kpi-inline"><span class="kpi-label">Nouveaux prospects (7j)</span><span class="kpi-value">${d.commercial.nouveaux_prospects_7j}</span></div>
        </div>
      </div>

      ${activationChecklistHtml(activation)}

      ${d.finances.paiements_recents.length ? `
      <div class="dash-section">
        <h3>Paiements recents</h3>
        ${d.finances.paiements_recents.map((p) => `<div class="dash-row"><span>${fmtDate(p.date_paiement)} · ${p.moyen}</span><strong>${fmtEuro(p.montant)}</strong></div>`).join("")}
      </div>` : ""}

      <div class="dash-secondary-grid">
        <div class="dash-section">
          <h3>Recommandations</h3>
          ${recommandations.length ? recommandations.map(recommandationRowHtml).join("") : '<div class="dash-empty">Aucune recommandation pour le moment.</div>'}
        </div>
        <div class="dash-section">
          <h3>Santé de votre entreprise</h3>
          ${santeWidgetHtml(sante)}
        </div>
      </div>

      <div class="dash-section">
        <h3>Présence en ligne</h3>
        ${renderPresenceSite(d.presence_site)}
      </div>
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

async function loadClients() {
  const board = document.getElementById("clients-kanban");
  board.innerHTML = skeletonCards();
  try {
    const clients = await Api.listClients();
    clientsCache = clients;
    if (clients.length === 0) {
      board.innerHTML = `<div class="empty-state">
        Aucun contact pour le moment.<br><br>
        Les demandes venant de votre site vitrine arrivent automatiquement ici.
        Vous pouvez aussi ajouter un contact a la main.
      </div>`;
      return;
    }
    const parColonne = {};
    CLIENT_PIPELINE_ORDRE.forEach((s) => (parColonne[s] = []));
    clients.forEach((c) => { (parColonne[c.statut] || (parColonne[c.statut] = [])).push(c); });

    board.innerHTML = CLIENT_PIPELINE_ORDRE.map((statut) => {
      const meta = CLIENT_STATUT_META[statut] || { label: statut };
      const items = parColonne[statut] || [];
      return `
      <div class="kanban-column">
        <div class="kanban-column-header">
          <span class="kanban-column-title">${meta.label}</span>
          <span class="kanban-column-count">${items.length}</span>
        </div>
        <div class="kanban-cards">
          ${items.length ? items.map(renderClientCard).join("") : '<div class="kanban-empty">Vide</div>'}
        </div>
      </div>`;
    }).join("");
  } catch (err) {
    board.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderClientCard(c) {
  const contact = [c.telephone, c.email].filter(Boolean).map(escapeHtml).join(" · ");
  const statutOptions = Object.entries(CLIENT_STATUT_META)
    .map(([value, m]) => `<option value="${value}" ${value === c.statut ? "selected" : ""}>${m.label}</option>`)
    .join("");

  const infosComplementaires = [
    c.montant_estime ? fmtEuro(c.montant_estime) + (c.probabilite !== null && c.probabilite !== undefined ? ` · ${c.probabilite}%` : "") : null,
    c.source && c.source !== "manuel" ? "Source : " + (CLIENT_SOURCE_LABELS[c.source] || c.source) : null,
  ].filter(Boolean);

  return `
  <div class="kanban-card" data-action="voir-timeline" data-id="${c.id}">
    <div class="kanban-card-title">${escapeHtml(c.nom)}</div>
    <div class="kanban-card-sub">${contact || "Pas de coordonnees"}${c.societe ? " · " + escapeHtml(c.societe) : ""}</div>
    ${infosComplementaires.map((t) => `<div class="kanban-card-sub">${escapeHtml(t)}</div>`).join("")}
    ${c.prochaine_action ? `<div class="kanban-card-next">→ ${escapeHtml(c.prochaine_action)}</div>` : ""}
    <div class="kanban-card-actions">
      <select data-action="changer-statut-client" data-id="${c.id}" aria-label="Statut de ${escapeHtml(c.nom)}">${statutOptions}</select>
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-client" data-id="${c.id}" title="Archiver" aria-label="Archiver">&times;</button>
    </div>
  </div>`;
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

function clientQuickActionsHtml(client) {
  const actions = [];
  if (client.telephone) actions.push(`<a class="btn-sm" href="tel:${escapeHtml(client.telephone)}">Appeler</a>`);
  if (client.email) actions.push(`<a class="btn-sm" href="mailto:${escapeHtml(client.email)}">Email</a>`);
  actions.push(`<button type="button" class="btn-sm" data-action="demander-avis" data-client-id="${client.id}">Demander un avis</button>`);
  actions.push(`<button type="button" class="btn-sm" data-action="copier-lien-portail" data-client-id="${client.id}">Copier le lien de l'espace client</button>`);
  return `<div class="item-actions client-detail-actions">${actions.join("")}</div>`;
}

// En-tete d'identite du panneau client : monogramme, nom/societe, statut,
// coordonnees lisibles directement (plus seulement caches derriere les
// boutons Appeler/Email) et l'action principale (+ Nouveau devis) mise en
// avant separement des actions secondaires. Memes donnees que l'ancien
// clientQuickActionsHtml, seule la composition change.
function clientDetailHeaderHtml(client) {
  const initiales = (client.nom || "?").trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const statutMeta = CLIENT_STATUT_META[client.statut] || { label: client.statut };
  const coords = [
    client.telephone ? `<a href="tel:${escapeHtml(client.telephone)}">${escapeHtml(client.telephone)}</a>` : null,
    client.email ? `<a href="mailto:${escapeHtml(client.email)}">${escapeHtml(client.email)}</a>` : null,
    client.ville || null,
  ].filter(Boolean);
  return `
  <div class="client-detail-header">
    <div class="crm-avatar client-detail-avatar">${escapeHtml(initiales)}</div>
    <div class="client-detail-identity">
      <div class="client-detail-name">${escapeHtml(client.nom)}</div>
      ${client.societe ? `<div class="client-detail-societe">${escapeHtml(client.societe)}</div>` : ""}
      <span class="badge badge-gray">${escapeHtml(statutMeta.label)}</span>
    </div>
  </div>
  ${coords.length ? `<div class="client-detail-coords">${coords.join('<span class="client-detail-coords-sep">·</span>')}</div>` : ""}
  <button type="button" class="btn-primary client-detail-cta" data-action="quick-devis" data-client-id="${client.id}">+ Nouveau devis</button>`;
}

function messagesPanelHtml(messages) {
  const listHtml = messages.length
    ? messages.map((m) => `
      <div class="timeline-entry">
        <span class="timeline-icon"></span>
        <div><div class="timeline-label"><strong>${m.expediteur === "client" ? "Client" : "Vous"} :</strong> ${escapeHtml(m.texte)}</div><div class="timeline-date">${fmtDateTime(m.created_at)}</div></div>
      </div>`).join("")
    : '<div class="empty-state">Aucun message pour le moment. Le client peut vous écrire depuis son espace client.</div>';
  return `
  <div class="dash-section" style="margin-top:24px;">
    <h3>Messages</h3>
    <div id="client-messages-list">${listHtml}</div>
    <form id="client-message-form" style="margin-top:12px;">
      <textarea id="client-message-texte" placeholder="Répondre au client..." aria-label="Votre réponse au client" required></textarea>
      <p class="field-error" id="client-message-error" hidden></p>
      <div class="form-actions"><button type="submit" class="btn-sm btn-sm-primary">Envoyer</button></div>
    </form>
  </div>`;
}

function clientResumeHtml(r) {
  const rows = [
    { label: "Valeur totale facturée", value: fmtEuro(r.valeur_totale) },
    { label: "Impayés", value: fmtEuro(r.impayes), alerte: r.impayes > 0 },
    { label: "Chantiers", value: r.nb_chantiers },
    { label: "Dernier contact", value: r.dernier_contact ? fmtDate(r.dernier_contact) : "-" },
    { label: "Dernier devis", value: r.date_dernier_devis ? fmtDate(r.date_dernier_devis) : "-" },
  ];
  return `<div class="client-detail-resume">
    ${rows.map((row) => `<div class="profil-row${row.alerte ? " is-alert" : ""}"><div class="label">${row.label}</div><div class="value">${row.value}</div></div>`).join("")}
  </div>`;
}

async function showTimeline(clientId) {
  const client = clientsCache.find((c) => c.id === clientId) || (await Api.listClients()).find((c) => c.id === clientId);
  document.getElementById("timeline-titre").textContent = "Fiche client";
  const content = document.getElementById("timeline-content");
  content.innerHTML = skeletonCards();
  document.getElementById("panel-timeline").hidden = false;
  document.getElementById("panel-timeline").dataset.clientId = clientId;

  try {
    const [entries, resume, messages] = await Promise.all([
      Api.clientTimeline(clientId), Api.clientResume(clientId), Api.listClientMessages(clientId).catch(() => []),
    ]);
    const entriesHtml = entries.length === 0
      ? '<div class="empty-state">Aucun evenement pour le moment.</div>'
      : entries.map((e) => `<div class="timeline-entry">
          <span class="timeline-icon"></span>
          <div><div class="timeline-label">${escapeHtml(e.label)}</div><div class="timeline-date">${fmtDateTime(e.date)}</div></div>
        </div>`).join("");

    content.innerHTML = `
      ${client ? clientDetailHeaderHtml(client) : ""}
      ${client ? clientQuickActionsHtml(client) : ""}
      ${clientResumeHtml(resume)}
      <div class="dash-section">
        <h3>Historique</h3>
        ${entriesHtml}
      </div>
      ${messagesPanelHtml(messages)}
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

    const avisBtn = e.target.closest('[data-action="demander-avis"]');
    if (avisBtn) {
      const clientId = parseInt(avisBtn.dataset.clientId, 10);
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
}

// ===================== Archives (clients/devis/factures/chantiers/documents) =====================
// Rien n'est jamais supprime definitivement (V5 section 3-4) : ce panneau
// generique liste les elements archives d'un type donne et permet de les
// restaurer, quelle que soit la vue depuis laquelle on l'ouvre.
const ARCHIVE_ENTITES = {
  client: {
    titre: "Clients archives",
    lister: () => Api.listClients(null, true),
    restaurer: (id) => Api.restaurerClient(id),
    ligne: (c) => `${escapeHtml(c.nom)}${c.societe ? " · " + escapeHtml(c.societe) : ""}`,
    recharger: () => { loadClients(); loadClientsDirectory(); },
  },
  devis: {
    titre: "Devis archives",
    lister: () => Api.listDevis(null, true),
    restaurer: (id) => Api.restaurerDevis(id),
    ligne: (d) => `${escapeHtml(d.numero || "Devis #" + d.id)} · ${escapeHtml(d.client_nom || "")} · ${fmtEuro(d.montant_ttc)}`,
    recharger: () => loadDevis(),
  },
  facture: {
    titre: "Factures archivees",
    lister: () => Api.listFactures(null, true),
    restaurer: (id) => Api.restaurerFacture(id),
    ligne: (f) => `${escapeHtml(f.numero || "Facture #" + f.id)} · ${escapeHtml(f.client_nom || "")} · ${fmtEuro(f.montant_ttc)}`,
    recharger: () => loadFactures(),
  },
  chantier: {
    titre: "Chantiers archives",
    lister: () => Api.listChantiers(true),
    restaurer: (id) => Api.restaurerChantier(id),
    ligne: (c) => `${escapeHtml(c.titre)}${c.client_nom ? " · " + escapeHtml(c.client_nom) : ""}`,
    recharger: () => loadChantiers(),
  },
  document: {
    titre: "Documents archives",
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
      : `<div class="empty-state">Aucun element archive.</div>`;
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

async function loadClientsDirectory() {
  const container = document.getElementById("clients-directory");
  container.innerHTML = skeletonCards();
  try {
    const clients = await Api.listClients("gagne");
    if (clients.length === 0) {
      container.innerHTML = `<div class="empty-state">
        Aucun client pour le moment.<br><br>
        Un prospect devient client automatiquement quand il passe au statut "Gagne" dans le pipeline.
      </div>`;
      return;
    }
    container.innerHTML = clients.map(renderClientDirectoryRow).join("");
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderClientDirectoryRow(c) {
  const contact = [c.telephone, c.email].filter(Boolean).join(" · ");
  const secondaire = [c.societe, c.ville].filter(Boolean).join(" · ");
  return `
  <div class="crm-row" data-action="voir-timeline" data-id="${c.id}" role="button" tabindex="0">
    <div class="crm-avatar">${escapeHtml(monogram(c.nom))}</div>
    <div class="crm-main">
      <div class="crm-name">${escapeHtml(c.nom)}</div>
      <div class="crm-contact">${escapeHtml(contact || "Pas de coordonnées")}</div>
    </div>
    <div class="crm-secondary">
      <div class="crm-secondary-line">${secondaire ? escapeHtml(secondaire) : "—"}</div>
      ${c.prochaine_action ? `<div class="crm-secondary-line crm-next-action">→ ${escapeHtml(c.prochaine_action)}</div>` : ""}
    </div>
    <div class="crm-action">
      <button type="button" class="btn-sm" data-action="voir-timeline" data-id="${c.id}">Voir l'historique</button>
    </div>
  </div>`;
}

// ===================== Devis & relances =====================
async function loadDevis() {
  const list = document.getElementById("devis-list");
  list.innerHTML = skeletonCards();
  try {
    const [devis, aRelancer] = await Promise.all([Api.listDevis(currentDevisFilter), Api.devisARelancer()]);
    devisDueIds = new Set(aRelancer.map((d) => d.id));
    if (devis.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun devis pour le moment.</div>';
      return;
    }
    list.innerHTML = devis.map(renderDevisCard).join("");
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
    <button type="button" class="icon-btn ligne-remove" data-action="remove-ligne" title="Retirer" aria-label="Retirer cette ligne">
      <svg viewBox="0 0 24 24" class="nav-icon"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>
    </button>
  </div>`;
}

function lignesEditorHtml(containerId, lignes) {
  const rows = (lignes && lignes.length ? lignes : [null]).map(ligneRowHtml).join("");
  return `
  <div class="lignes-editor">
    <div class="ligne-row ligne-row-header" aria-hidden="true">
      <span>Désignation</span><span>Qté</span><span>Unité</span><span>Prix HT</span><span></span>
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

  const contextTxt = [d.numero, d.nb_relances > 0 ? `${d.nb_relances} relance${d.nb_relances > 1 ? "s" : ""}` : null]
    .filter(Boolean).join(" · ");

  return `
  <div class="list-row ${isDue ? "is-due" : ""}">
    <div class="list-row-primary">
      <div class="list-row-title">${escapeHtml(d.client_nom)}</div>
      <div class="list-row-sub">${escapeHtml(d.titre || d.description || "Sans titre")}</div>
    </div>
    <div class="list-row-status"><span class="badge ${meta.badge}">${meta.label}</span></div>
    <div class="list-row-amount">${montantTxt}${d.montant_ttc !== null && d.montant_ttc !== undefined ? '<span class="list-row-amount-sub">TTC</span>' : ""}</div>
    <div class="list-row-context" title="${isDue ? "Relance due aujourd'hui" : escapeHtml(contextTxt)}">${isDue ? "Relance due aujourd'hui" : escapeHtml(contextTxt)}</div>
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

        <div class="form-section">
          <div class="form-section-title">Conditions financières</div>
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
        </div>

        <div class="form-section">
          <div class="form-section-title">Notes</div>
          <label for="df-description">Description / notes</label>
          <textarea id="df-description">${isEdit ? escapeHtml(devis.description || "") : ""}</textarea>
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

  document.getElementById("devis-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

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

function tresorerieHeaderHtml(factures) {
  const enCours = factures.filter((f) => !["brouillon", "annulee", "payee"].includes(f.statut));
  if (enCours.length === 0) return "";
  const aEncaisser = enCours.reduce((s, f) => s + f.montant_restant, 0);
  const facturesEnRetard = enCours.filter((f) => f.est_en_retard);
  const enRetard = facturesEnRetard.reduce((s, f) => s + f.montant_restant, 0);
  return `
  <div class="kpi-row">
    <div class="kpi-inline is-primary"><span class="kpi-label">À encaisser</span><span class="kpi-value">${fmtEuro(aEncaisser)}</span></div>
    <div class="kpi-inline${enRetard > 0 ? " is-alert" : ""}"><span class="kpi-label">Dont en retard</span><span class="kpi-value">${fmtEuro(enRetard)}</span></div>
    <div class="kpi-inline"><span class="kpi-label">Factures en cours</span><span class="kpi-value">${enCours.length}</span></div>
  </div>`;
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
    tresorerie.innerHTML = tresorerieHeaderHtml(factures);

    let affichees = factures;
    if (currentFactureFilter === "a_encaisser") {
      affichees = factures
        .filter((f) => f.montant_restant > 0 && !["brouillon", "annulee"].includes(f.statut))
        .sort((a, b) => (a.date_echeance || "9999-99-99").localeCompare(b.date_echeance || "9999-99-99"));
    } else if (currentFactureFilter) {
      affichees = factures.filter((f) => f.statut === currentFactureFilter);
    }

    if (affichees.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucune facture pour le moment. Convertissez un devis signé, ou créez-en une directement.</div>';
      return;
    }
    list.innerHTML = affichees.map(renderFactureCard).join("");
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

  // Le retard prime sur l'echeance quand les deux sont vraies : c'est
  // l'info la plus actionnable, et la ligne est deja signalee par l'accent
  // rouge sur le bord gauche - pas besoin des deux dates dans une colonne
  // etroite.
  const contextTxt = retard !== null
    ? `${retard} j de retard`
    : (f.date_echeance ? "Éch. " + fmtDate(f.date_echeance) : "");

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
  <div class="list-row ${f.est_en_retard ? "is-due" : ""}">
    <div class="list-row-primary">
      <div class="list-row-title">${escapeHtml(f.client_nom)} &mdash; ${escapeHtml(f.numero)}</div>
      <div class="list-row-sub">${FACTURE_TYPE_LABELS[f.type] || f.type} · Payé ${fmtEuro(f.montant_paye)}</div>
    </div>
    <div class="list-row-status"><span class="badge ${meta.badge}">${meta.label}</span></div>
    <div class="list-row-amount">${montantCle}<span class="list-row-amount-sub">${montantCleLabel}</span></div>
    <div class="list-row-context" title="${escapeHtml(contextTxt)}">${escapeHtml(contextTxt)}</div>
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

function showPaiementForm(factureId, soldeRestant) {
  const container = document.getElementById(`paiement-form-${factureId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  const maximum = Number(soldeRestant).toFixed(2);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div><label for="pay-montant-${factureId}">Montant (euros) * · Solde ${fmtEuro(soldeRestant)}</label><input type="number" step="0.01" min="0.01" max="${maximum}" id="pay-montant-${factureId}" required></div>
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

          <div class="form-section">
            <div class="form-section-title">Échéance</div>
            <div class="form-grid">
              <div><label for="fa-echeance">Date d'échéance</label><input type="date" id="fa-echeance"></div>
            </div>
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

function setupFacturesView() {
  document.getElementById("facture-filters").addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    document.querySelectorAll("#facture-filters .filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentFactureFilter = chip.dataset.statut;
    loadFactures();
  });

  document.querySelector('[data-action="show-facture-form"]').addEventListener("click", showFactureForm);
  document.getElementById("facture-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-facture-form"]')) {
      const container = document.getElementById("facture-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  document.getElementById("factures-list").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

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
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(c.titre)}</div>
        <div class="item-sub">${escapeHtml(c.client_nom)} · ${fmtEuro(c.montant_ht)} HT · TVA ${c.taux_tva}% · ${CONTRAT_FREQUENCE_LABELS[c.frequence] || c.frequence}</div>
      </div>
      <span class="badge ${meta.badge}">${meta.label}</span>
    </div>
    <div class="item-meta">
      Prochaine échéance : ${fmtDate(c.prochaine_echeance)}
      ${c.derniere_generation ? ` · Dernière facture générée le ${fmtDate(c.derniere_generation)}` : ""}
      · ${c.nb_factures_generees} facture${c.nb_factures_generees > 1 ? "s" : ""} générée${c.nb_factures_generees > 1 ? "s" : ""}
    </div>
    <div class="item-actions">
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
async function loadChantiers() {
  const list = document.getElementById("chantiers-list");
  const newBtn = document.querySelector('[data-action="show-chantier-form"]');
  const formContainer = document.getElementById("chantier-form-container");

  if (!hasPlan("essentiel")) {
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
    if (chantiers.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun chantier pour le moment.</div>';
      return;
    }
    list.innerHTML = chantiers.map(renderChantierCard).join("");
    focusChantierCard();
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
  const margeTxt = c.marge_reelle !== null
    ? `<span style="${c.marge_reelle < 0 ? "color:var(--danger);" : ""}">${fmtEuro(c.marge_reelle)}</span>`
    : "-";
  const depensesLabel = c.cout_main_oeuvre !== null
    ? `${fmtEuro(c.total_depenses)} + ${fmtEuro(c.cout_main_oeuvre)} main d'oeuvre`
    : fmtEuro(c.total_depenses);
  return `
    <div class="dash-grid" style="margin:12px 0;">
      <div class="dash-stat"><div class="value">${depensesLabel}</div><div class="label">Dépenses</div></div>
      <div class="dash-stat"><div class="value">${c.montant_facture !== null ? fmtEuro(c.montant_facture) : "-"}</div><div class="label">Facturé</div></div>
      <div class="dash-stat"><div class="value">${c.montant_encaisse !== null ? fmtEuro(c.montant_encaisse) : "-"}</div><div class="label">Encaissé</div></div>
      <div class="dash-stat"><div class="value">${margeTxt}</div><div class="label">Marge réelle</div></div>
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

function progressionHtml(c) {
  if (c.progression === null || c.progression === undefined) return "";
  const couleur = c.progression >= 70 ? "var(--success)" : c.progression >= 40 ? "var(--warning)" : "var(--danger)";
  return `
    <div style="margin:10px 0;">
      <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:3px;"><span>Avancement</span><strong>${c.progression}%</strong></div>
      <div class="sante-barre"><div class="remplissage" style="width:${c.progression}%;background:${couleur};"></div></div>
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
        <div><label for="chantier-budget-${c.id}">Budget prévu (euros)</label><input type="number" step="0.01" min="0" id="chantier-budget-${c.id}" value="${c.budget !== null ? escapeHtml(c.budget) : ""}" ${verrou ? "disabled" : ""}></div>
      </div>
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
function chantierActionsHtml(c) {
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

  return `
  <div class="item-card chantier-card" data-chantier-id="${c.id}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(c.titre)}</div>
        <div class="item-sub">${escapeHtml(c.client_nom || "")}${c.adresse ? " · " + escapeHtml(c.adresse) : ""}</div>
      </div>
      <span class="badge ${(CHANTIER_STATUT_META[c.statut] || {}).badge || "badge-gray"}">${(CHANTIER_STATUT_META[c.statut] || {}).label || c.statut}</span>
    </div>
    ${c.statut === "termine" ? `<div class="moment-banner"><span>Chantier terminé ! Clôturez-le pour générer la facture finale, demander un avis client et archiver le dossier.</span></div>` : ""}
    ${aujourdhuiChantierHtml(c)}
    <div class="item-meta">
      Début : ${fmtDate(c.date_debut)}
      ${c.budget !== null ? ` · Budget : ${fmtEuro(c.budget)}` : ""}
      ${c.marge_estimee !== null ? ` · Marge estimée : ${fmtEuro(c.marge_estimee)}` : ""}
    </div>
    ${progressionHtml(c)}
    ${checklistHtml(c)}
    ${rentabiliteHtml(c)}
    ${c.finances_verrouillees ? '<div class="moment-banner"><span>Les données financières sont verrouillées depuis la création de la facture finale.</span></div>' : ""}
    ${depensesHtml ? `<div class="item-meta">${depensesHtml}</div>` : ""}
    ${heuresHtml(c)}
    <div class="notes-list">${notesHtml || '<div class="item-sub">Aucune note pour le moment.</div>'}</div>
    ${receptionHtml(c)}
    ${chantierActionsHtml(c)}
    <div id="chantier-edit-form-${c.id}"></div>
    <div id="note-form-${c.id}"></div>
    <div id="depense-form-${c.id}"></div>
    <div id="heures-form-${c.id}"></div>
    <div id="reception-form-${c.id}"></div>
    <div id="cloturer-form-${c.id}"></div>
  </div>`;
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

    if (btn.dataset.action === "edit-chantier") {
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

async function loadTaches() {
  const list = document.getElementById("taches-list");
  list.innerHTML = skeletonCards();
  try {
    const taches = await Api.listTaches(currentTacheFilter);
    if (taches.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucune tâche ici.</div>';
      return;
    }
    list.innerHTML = taches.map(renderTacheCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderTacheCard(t) {
  const estFaite = t.statut === "faite";
  return `
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title" style="${estFaite ? "text-decoration:line-through;opacity:0.6;" : ""}">${escapeHtml(t.titre)}</div>
        ${t.description ? `<div class="item-sub">${escapeHtml(t.description)}</div>` : ""}
      </div>
      <span class="badge ${TACHE_PRIORITE_BADGE[t.priorite] || "badge-gray"}">${t.priorite}</span>
    </div>
    <div class="item-meta">${t.echeance ? "Échéance : " + fmtDate(t.echeance) : "Pas d'échéance"}</div>
    <div class="item-actions">
      ${!estFaite
        ? `<button type="button" class="btn-sm btn-sm-primary" data-action="terminer-tache" data-id="${t.id}">Marquer faite</button>`
        : `<button type="button" class="btn-sm" data-action="reouvrir-tache" data-id="${t.id}">Réouvrir</button>`}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-tache" data-id="${t.id}">Supprimer</button>
    </div>
  </div>`;
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

  document.querySelector('[data-action="show-tache-form"]').addEventListener("click", showTacheForm);
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

let currentDocumentFilter = "";

function fmtTaille(octets) {
  if (octets === null || octets === undefined) return "";
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${(octets / 1024).toFixed(0)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

async function loadDocuments() {
  const list = document.getElementById("documents-list");
  list.innerHTML = skeletonCards();
  try {
    const [documents] = await Promise.all([Api.listDocuments(), ensureClientsCache()]);
    const affichees = currentDocumentFilter ? documents.filter((d) => d.type === currentDocumentFilter) : documents;
    if (affichees.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun document pour le moment. Ajoutez vos contrats, attestations d\'assurance, plans ou photos de chantier.</div>';
      return;
    }
    list.innerHTML = affichees.map(renderDocumentCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderDocumentCard(d) {
  const client = d.client_id ? clientsCache.find((c) => c.id === d.client_id) : null;
  const lienTxt = client ? `Client : ${escapeHtml(client.nom)}` : "";
  const estFichier = !!d.nom_original;
  return `
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(d.nom)}</div>
        <div class="item-sub">${lienTxt}${lienTxt && d.taille_octets ? " · " : ""}${d.taille_octets ? fmtTaille(d.taille_octets) : ""}</div>
      </div>
      <span class="badge badge-gray">${DOCUMENT_TYPE_LABELS[d.type] || d.type}</span>
    </div>
    <div class="item-meta">Ajouté le ${fmtDate(d.created_at)}</div>
    <div class="item-actions">
      ${estFichier
        ? `<button type="button" class="btn-sm btn-sm-primary" data-action="telecharger-document" data-id="${d.id}" data-nom="${escapeHtml(d.nom_original)}">Télécharger</button>`
        : `<a class="btn-sm" href="${escapeHtml(d.url)}" target="_blank" rel="noopener">Ouvrir le lien</a>`}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-document" data-id="${d.id}">Supprimer</button>
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
    loadDocuments();
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
const PLANNING_ROW_H = 44; // px par heure - garder synchronise avec --sa-plan-row-h en CSS.

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
  const headerLabel = showWeekday
    ? dateObj.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" })
    : String(dateObj.getDate());
  const body = hourGrid
    ? `<div class="planning-day-track">${planningHourRowsHtml()}${planningLayoutDay(dayItems).map(planningPositionedItemHtml).join("")}${isToday ? planningNowLineHtml() : ""}</div>`
    : `<div class="planning-day-items">${dayItems.map((i) => planningItemChip(i, compact)).join("") || (compact ? "" : '<div class="planning-day-empty">Rien de prévu</div>')}</div>`;
  return `
    <div class="planning-day-cell ${isToday ? "is-today" : ""} ${hourGrid ? "has-hour-grid" : ""} ${extraClass}" data-date="${iso}">
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
  container.innerHTML = planningToolbarHtml(debut, fin) + gridHtml;
}

// Derniers items charges, pour retrouver le detail complet (lieu, client_id...)
// d'un rendez-vous au clic sans re-appeler l'API.
let planningItemsCache = [];

async function loadPlanning() {
  const container = document.getElementById("planning-content");
  container.innerHTML = skeletonCards();
  try {
    const [debut, fin] = planningRange();
    const items = await Api.planning(planningToIso(debut), planningToIso(fin));
    planningItemsCache = items;
    renderPlanning(debut, fin, items);
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
      banner.textContent = `${alertes.length} élément(s) de conformité arrivent à échéance dans moins de 30 jours (ou sont déjà expirés).`;
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
  return `
  <div class="item-card ${item.alerte ? "is-due" : ""}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(item.libelle)}</div>
        <div class="item-sub">${CONFORMITE_TYPE_LABELS[item.type] || item.type}</div>
      </div>
      <span class="badge ${badgeClass}">${badgeLabel}</span>
    </div>
    <div class="item-meta">
      Echeance : ${fmtDate(item.date_expiration)}
      ${item.document_url ? ` · <a href="${escapeHtml(item.document_url)}" target="_blank" rel="noopener">Document</a>` : ""}
    </div>
    <div class="item-actions">
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-conformite" data-id="${item.id}">Supprimer</button>
    </div>
  </div>`;
}

function setupConformiteView() {
  document.querySelector('[data-action="show-conformite-form"]').addEventListener("click", () => {
    const container = document.getElementById("conformite-form-container");
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouvel element de conformite</h3>
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
  setupEntrepriseForm();
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
