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
  const icon = isError ? "&#9888;" : "&#10003;";
  toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${escapeHtml(message)}</span>`;
  toast.classList.toggle("toast-error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3500);
}

async function withErrorToast(promiseFn) {
  try {
    return await promiseFn();
  } catch (err) {
    showToast(err.message || "Une erreur est survenue.", true);
    throw err;
  }
}

// ===================== Constantes d'affichage =====================
const METIER_LABELS = {
  plombier: "Plombier",
  electricien: "Electricien",
  macon: "Macon",
  peintre: "Peintre",
  general: "Artisan du BTP",
};

const DEVIS_STATUT_META = {
  nouveau: { label: "Nouvelle demande", badge: "badge-gray" },
  envoye: { label: "Envoye", badge: "badge-blue" },
  consulte: { label: "Consulte", badge: "badge-blue" },
  relance_j3: { label: "Relance J+3", badge: "badge-orange" },
  relance_j7: { label: "Relance J+7", badge: "badge-orange" },
  relance_j15: { label: "Relance J+15", badge: "badge-red" },
  signe: { label: "Signe", badge: "badge-green" },
  perdu: { label: "Perdu", badge: "badge-gray" },
  expire: { label: "Expire", badge: "badge-gray" },
};

const CLIENT_STATUT_META = {
  nouveau: { label: "Nouveau", badge: "badge-gray" },
  contacte: { label: "Contacte", badge: "badge-blue" },
  qualification: { label: "Qualification", badge: "badge-blue" },
  visite_prevue: { label: "Visite prevue", badge: "badge-blue" },
  devis_a_faire: { label: "Devis a faire", badge: "badge-orange" },
  devis_envoye: { label: "Devis envoye", badge: "badge-orange" },
  negociation: { label: "Negociation", badge: "badge-orange" },
  gagne: { label: "Gagne", badge: "badge-green" },
  perdu: { label: "Perdu", badge: "badge-gray" },
};

const CLIENT_SOURCE_LABELS = {
  manuel: "Ajoute manuellement",
  site_vitrine: "Site vitrine",
  google: "Google",
  recommandation: "Recommandation",
  telephone: "Telephone",
  facebook: "Facebook",
  instagram: "Instagram",
  ancien_client: "Ancien client",
  autre: "Autre",
};

const FACTURE_STATUT_META = {
  brouillon: { label: "Brouillon", badge: "badge-gray" },
  envoyee: { label: "Envoyee", badge: "badge-blue" },
  partiellement_payee: { label: "Partiellement payee", badge: "badge-orange" },
  payee: { label: "Payee", badge: "badge-green" },
  en_retard: { label: "En retard", badge: "badge-red" },
  annulee: { label: "Annulee", badge: "badge-gray" },
};

// Cache simple des clients pour remplir les listes deroulantes des formulaires
// devis/chantier/facture sans reinterroger l'API a chaque frappe.
let clientsCache = [];
async function ensureClientsCache() {
  clientsCache = await Api.listClients();
  return clientsCache;
}

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

const PHASE_LABELS = { avant: "Avant", pendant: "Pendant", apres: "Apres" };
const CONFORMITE_TYPE_LABELS = {
  assurance_decennale: "Assurance decennale",
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
function isSubscriptionActive() {
  return currentArtisan && currentArtisan.subscription_status === "active";
}

function renderUpgradeCard(title, description) {
  const pro = PRICING.pro;
  return `
  <div class="upgrade-card">
    <div class="upgrade-icon">&#128274;</div>
    <h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(description)} A partir de ${pro.prix}&nbsp;&euro; ${pro.mention}.</p>
    <button type="button" class="btn-primary" data-action="upgrade-subscription">Voir les tarifs</button>
  </div>`;
}

async function attemptUpgrade() {
  const btn = document.querySelector('[data-action="confirm-upgrade"]');
  if (btn) btn.disabled = true;
  try {
    const data = await Api.checkoutSession();
    window.location.href = data.checkout_url;
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
function planCardHtml(key, plan) {
  const isPro = key === "pro";
  const priceHtml = plan.prix === 0
    ? '<div class="plan-price">Gratuit</div>'
    : `<div class="plan-price">${plan.prix}&nbsp;&euro; <span class="period">/ ${plan.periode}</span></div>`;
  return `
  <div class="plan-card ${isPro ? "plan-highlight" : ""}">
    ${isPro ? '<span class="plan-badge">Recommande</span>' : ""}
    <div class="plan-name">${escapeHtml(plan.nom)}</div>
    <div class="plan-accroche">${escapeHtml(plan.accroche)}</div>
    ${priceHtml}
    ${plan.mention ? `<div class="plan-mention">${escapeHtml(plan.mention)}</div>` : '<div class="plan-mention">&nbsp;</div>'}
    <ul class="plan-features">
      ${plan.fonctionnalites.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}
    </ul>
    ${isPro
      ? '<button type="button" class="btn-primary" data-action="confirm-upgrade">S\'abonner a Suite Artisan Pro</button>'
      : '<button type="button" class="btn-secondary" data-action="close-pricing">Rester sur le plan Gratuit</button>'}
  </div>`;
}

function openPricingModal() {
  const container = document.getElementById("pricing-plans");
  container.innerHTML = Object.entries(PRICING).map(([key, plan]) => planCardHtml(key, plan)).join("");
  document.getElementById("pricing-modal").hidden = false;
}
function closePricingModal() {
  document.getElementById("pricing-modal").hidden = true;
}

document.addEventListener("click", (e) => {
  if (e.target.closest('[data-action="upgrade-subscription"]')) {
    openPricingModal();
  } else if (e.target.closest('[data-action="confirm-upgrade"]')) {
    attemptUpgrade();
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
    icon: "&#128075;",
    title: "Bienvenue sur Suite Artisan",
    body: "Un seul outil pour ne plus perdre de prospects, relancer vos devis automatiquement et garder une vue claire sur votre activite. Tout ce dont vous avez besoin pour demarrer est deja gratuit.",
  },
  {
    icon: "&#128203;",
    title: "Comment ca marche",
    list: [
      "Ajoutez un client ou un prospect",
      "Creez un devis avec vos lignes de prestation, envoyez le PDF",
      "Suite Artisan vous rappelle quand relancer",
    ],
  },
  {
    icon: "&#127970;",
    title: "Votre site vitrine",
    body: "Si vous avez commande un site vitrine, il apparaitra dans votre tableau de bord des qu'il sera livre, avec les demandes recues automatiquement dans vos prospects.",
  },
  {
    icon: "&#128274;",
    title: "Pour aller plus loin",
    body: `Suite ${PRICING.pro.nom.replace("Suite ", "")} (${PRICING.pro.prix}€ ${PRICING.pro.mention}) ajoute le suivi de chantiers, la conformite et les statistiques. Vous pourrez l'activer a tout moment depuis votre profil.`,
  },
];
let onboardingStepIndex = 0;

function renderOnboardingStep() {
  const step = ONBOARDING_STEPS[onboardingStepIndex];
  document.getElementById("onboarding-steps").innerHTML = `
    <div class="onboarding-step">
      <div class="onboarding-step-icon">${step.icon}</div>
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

function switchView(view) {
  document.querySelectorAll(".nav-link").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
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
    loadConformite();
    loadEquipe();
    loadAutomationStatus();
  }
}

async function refreshBadges() {
  // Les deux compteurs sont independants : la conformite est une fonction payante
  // (402 si l'abonnement n'est pas actif), on ne veut pas que ca empeche le badge
  // des relances (gratuit) de s'afficher. D'ou Promise.allSettled plutot que Promise.all.
  const [relancerResult, alertesResult, notificationsResult] = await Promise.allSettled([
    Api.devisARelancer(), Api.conformiteAlertes(), Api.listNotifications(),
  ]);

  const badgeRelances = document.getElementById("badge-relances");
  if (relancerResult.status === "fulfilled") {
    devisDueIds = new Set(relancerResult.value.map((d) => d.id));
    badgeRelances.textContent = relancerResult.value.length;
    badgeRelances.hidden = relancerResult.value.length === 0;
  } else {
    badgeRelances.hidden = true;
    console.warn("Impossible de charger les relances a faire :", relancerResult.reason?.message);
  }

  const badgeAlertes = document.getElementById("badge-alertes");
  if (alertesResult.status === "fulfilled") {
    badgeAlertes.textContent = alertesResult.value.length;
    badgeAlertes.hidden = alertesResult.value.length === 0;
  } else {
    // 402 si pas abonne : pas d'alerte affichee, c'est attendu.
    badgeAlertes.hidden = true;
  }

  const badgeNotifications = document.getElementById("badge-notifications");
  if (notificationsResult.status === "fulfilled") {
    badgeNotifications.textContent = notificationsResult.value.length;
    badgeNotifications.hidden = notificationsResult.value.length === 0;
  } else {
    badgeNotifications.hidden = true;
    console.warn("Impossible de charger les notifications :", notificationsResult.reason?.message);
  }
}

function setupProfilPanel() {
  document.getElementById("btn-profil").addEventListener("click", () => {
    const content = document.getElementById("profil-content");
    const publicUrl = `${API_BASE}/pub/${currentArtisan.slug}/demande-devis`;
    content.innerHTML = `
      <div class="profil-row"><div class="label">Entreprise</div><div class="value">${escapeHtml(currentArtisan.nom_entreprise)}</div></div>
      <div class="profil-row"><div class="label">Metier</div><div class="value">${escapeHtml(METIER_LABELS[currentArtisan.metier] || currentArtisan.metier)}</div></div>
      <div class="profil-row"><div class="label">Email</div><div class="value">${escapeHtml(currentArtisan.email)}</div></div>
      <div class="profil-row"><div class="label">Ville</div><div class="value">${escapeHtml(currentArtisan.ville || "-")}</div></div>
      <div class="profil-row"><div class="label">SIRET</div><div class="value">${escapeHtml(currentArtisan.siret || "-")}</div></div>
      <div class="profil-row"><div class="label">Lien public du formulaire de devis</div><div class="value" style="font-weight:400;font-size:0.82rem;">${escapeHtml(publicUrl)}</div></div>
      <div class="profil-row">
        <div class="label">Abonnement Suite Artisan</div>
        <div class="value">
          <span class="badge ${isSubscriptionActive() ? "badge-green" : "badge-gray"}">${isSubscriptionActive() ? "Actif" : "Inactif"}</span>
        </div>
        ${!isSubscriptionActive() ? '<button type="button" class="btn-primary" data-action="upgrade-subscription" style="margin-top:10px;width:100%;">Voir les tarifs</button>' : ""}
      </div>
    `;
    document.getElementById("panel-profil").hidden = false;
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
  document.getElementById("ent-telephone").value = currentArtisan.telephone || "";
  document.getElementById("ent-ville").value = currentArtisan.ville || "";
  document.getElementById("ent-code-postal").value = currentArtisan.code_postal || "";
  document.getElementById("ent-adresse").value = currentArtisan.adresse || "";
  document.getElementById("ent-siret").value = currentArtisan.siret || "";
  document.getElementById("ent-assurance").value = currentArtisan.assurance_decennale_nom || "";

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
const MEMBRE_ROLE_LABELS = { administrateur: "Administrateur", salarie: "Salarie" };

async function loadEquipe() {
  const list = document.getElementById("equipe-list");
  const addBtn = document.getElementById("btn-show-membre-form");
  addBtn.hidden = !estAdministrateur();
  list.innerHTML = skeletonCards();
  try {
    const equipe = await Api.listEquipe();
    if (equipe.length === 0) {
      list.innerHTML = '<div class="empty-state">Personne dans votre equipe pour le moment. Vous etes seul(e) sur ce compte.</div>';
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
    actions += `<button type="button" class="btn-sm" data-action="toggle-membre-actif" data-id="${m.id}" data-actif="${m.actif}">${m.actif ? "Desactiver" : "Reactiver"}</button>`;
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
    ${!m.actif ? '<div class="item-meta"><span class="badge badge-gray">Desactive</span></div>' : ""}
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
          <div><label for="mb-password">Mot de passe * (8 caracteres minimum)</label><input type="password" id="mb-password" minlength="8" required></div>
          <div>
            <label for="mb-role">Role</label>
            <select id="mb-role">
              <option value="salarie">Salarie (acces normal)</option>
              <option value="administrateur">Administrateur (peut gerer l'equipe)</option>
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
      showToast("Membre ajoute. Communiquez-lui son email et son mot de passe pour qu'il se connecte.");
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
        showToast(actif ? "Membre desactive." : "Membre reactive.");
        loadEquipe();
      });
    } else if (btn.dataset.action === "delete-membre") {
      if (!confirm("Supprimer ce membre de l'equipe ?")) return;
      await withErrorToast(async () => {
        await Api.deleteMembre(id);
        showToast("Membre supprime.");
        loadEquipe();
      });
    }
  });
}

// ===================== Catalogue de prestations =====================
const PRESTATION_CATEGORIE_DEFAUT = "Sans categorie";

async function loadPrestations() {
  const list = document.getElementById("prestations-list");
  list.innerHTML = skeletonCards();
  try {
    const prestations = await Api.listPrestations();
    prestationsCache = prestations;
    if (prestations.length === 0) {
      list.innerHTML = `<div class="empty-state">
        Aucune prestation dans votre catalogue.<br><br>
        Ajoutez vos prestations types pour les retrouver en tapant leur nom lors de la creation d'un devis.
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
            <div><label for="pr-categorie">Categorie</label><input type="text" id="pr-categorie" placeholder="Ex: Peinture"></div>
            <div><label for="pr-unite">Unite</label><input type="text" id="pr-unite" value="u" placeholder="u, m2, h, forfait..."></div>
            <div><label for="pr-prix">Prix unitaire HT *</label><input type="number" step="0.01" min="0" id="pr-prix" required></div>
            <div>
              <label for="pr-tva">TVA</label>
              <select id="pr-tva">
                <option value="10">10% (renovation)</option>
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
        showToast("Prestation ajoutee au catalogue.");
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
    if (!confirm("Supprimer cette prestation du catalogue ?")) return;
    await withErrorToast(async () => {
      await Api.deletePrestation(parseInt(btn.dataset.id, 10));
      showToast("Prestation supprimee.");
      loadPrestations();
    });
  });
}

// ===================== Statistiques =====================
async function loadStatistiques() {
  const container = document.getElementById("statistiques-content");
  container.innerHTML = skeletonCards();
  if (!isSubscriptionActive()) {
    container.innerHTML = renderUpgradeCard(
      "Statistiques reservees aux abonnes",
      "Le suivi de la performance commerciale et financiere (CA, taux d'acceptation, impayes, panier moyen) fait partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  try {
    const a = await Api.analytics();
    const stats = [
      { label: "CA (12 derniers mois)", value: fmtEuro(a.ca_par_mois.reduce((s, m) => s + m.ca, 0)) },
      { label: "Valeur du pipeline", value: fmtEuro(a.valeur_pipeline) },
      { label: "Impayes", value: fmtEuro(a.montant_impayes) },
      { label: "Devis envoyes", value: a.nb_devis_total },
      { label: "Devis signes", value: a.nb_devis_signes },
      { label: "Taux d'acceptation", value: `${a.taux_acceptation}%` },
      { label: "Panier moyen", value: fmtEuro(a.panier_moyen) },
      { label: "Delai moyen de paiement", value: a.delai_moyen_paiement_jours !== null ? `${a.delai_moyen_paiement_jours} j` : "-" },
      { label: "Clients acquis", value: a.nb_clients_acquis },
      { label: "Clients recurrents", value: a.nb_clients_recurrents },
    ];
    const statsHtml = stats.map((s) => `<div class="dash-stat"><div class="value">${s.value}</div><div class="label">${escapeHtml(s.label)}</div></div>`).join("");

    const moisHtml = a.ca_par_mois.length
      ? a.ca_par_mois.map((m) => `<div class="dash-row"><span>${escapeHtml(m.mois)}</span><strong>${fmtEuro(m.ca)}</strong></div>`).join("")
      : '<div class="dash-empty">Pas encore de paiement enregistre.</div>';

    const sourcesHtml = a.sources_acquisition.length
      ? a.sources_acquisition.map((s) => `<div class="dash-row"><span>${escapeHtml(CLIENT_SOURCE_LABELS[s.source] || s.source)}</span><strong>${s.nb_clients} contact${s.nb_clients > 1 ? "s" : ""} · ${s.nb_gagnes} gagne${s.nb_gagnes > 1 ? "s" : ""} · ${fmtEuro(s.ca)}</strong></div>`).join("")
      : '<div class="dash-empty">Pas encore de contact enregistre.</div>';

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
    `;
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// ===================== Avis clients =====================
const AVIS_SOURCE_LABELS = { manuel: "Saisi a la main", lien_public: "Envoye par le client" };

function starsText(note) {
  return "★".repeat(note) + "☆".repeat(5 - note);
}

function avisResumeHtml(avis) {
  if (avis.length === 0) return "";
  const moyenne = avis.reduce((s, a) => s + a.note, 0) / avis.length;
  return `
    <div class="dash-grid" style="margin-bottom:20px;">
      <div class="dash-stat"><div class="value">${moyenne.toFixed(1)}/5</div><div class="label">Note moyenne</div></div>
      <div class="dash-stat"><div class="value">${avis.length}</div><div class="label">Avis recus</div></div>
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
              <option value="4">4 - Tres bien</option>
              <option value="3">3 - Correct</option>
              <option value="2">2 - Deçu</option>
              <option value="1">1 - Tres deçu</option>
            </select>
          </div>
          <div><label for="av-client">Client (optionnel)</label><select id="av-client"><option value="">Aucun</option>${clientOptionsHtml()}</select></div>
          <div><label for="av-nom-auteur">Nom (si pas de client lie)</label><input type="text" id="av-nom-auteur"></div>
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
      showToast("Avis ajoute.");
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
    const btn = e.target.closest('[data-action="delete-avis"]');
    if (!btn) return;
    if (!confirm("Supprimer cet avis ?")) return;
    await withErrorToast(async () => {
      await Api.deleteAvis(parseInt(btn.dataset.id, 10));
      showToast("Avis supprime.");
      loadAvis();
    });
  });
}

// ===================== Notifications =====================
const NOTIFICATION_TYPE_LABELS = {
  devis_relance: "Devis", facture_relance: "Facture", conformite: "Conformite",
};

async function loadNotifications() {
  const list = document.getElementById("notifications-list");
  list.innerHTML = skeletonCards();
  try {
    const notifications = await Api.listNotifications();
    if (notifications.length === 0) {
      list.innerHTML = '<div class="empty-state">Rien a signaler. Tout est a jour.</div>';
      return;
    }
    list.innerHTML = notifications.map(renderNotificationCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderNotificationCard(n) {
  return `
  <div class="item-card ${n.urgent ? "is-due" : ""}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(n.titre)}</div>
        ${n.sous_titre ? `<div class="item-sub">${escapeHtml(n.sous_titre)}</div>` : ""}
      </div>
      <span class="badge ${n.urgent ? "badge-red" : "badge-gray"}">${NOTIFICATION_TYPE_LABELS[n.type] || n.type}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn-sm btn-sm-primary" data-action="voir-notification" data-view="${n.view}">Voir</button>
    </div>
  </div>`;
}

function setupNotificationsView() {
  document.getElementById("notifications-list").addEventListener("click", (e) => {
    const btn = e.target.closest('[data-action="voir-notification"]');
    if (!btn) return;
    switchView(btn.dataset.view);
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

function openSearch() {
  const modal = document.getElementById("search-modal");
  modal.hidden = false;
  const input = document.getElementById("search-input");
  input.value = "";
  document.getElementById("search-results").innerHTML = "";
  input.focus();
}

function closeSearch() {
  document.getElementById("search-modal").hidden = true;
}

async function runSearch(q) {
  const resultsBox = document.getElementById("search-results");
  if (!q || q.trim().length < 2) {
    resultsBox.innerHTML = '<div class="search-empty">Tapez au moins 2 caracteres...</div>';
    return;
  }
  try {
    const results = await Api.search(q);
    if (results.length === 0) {
      resultsBox.innerHTML = '<div class="search-empty">Aucun resultat.</div>';
      return;
    }
    const parGroupe = {};
    results.forEach((r) => { (parGroupe[r.type] = parGroupe[r.type] || []).push(r); });
    resultsBox.innerHTML = Object.keys(parGroupe).map((type) => {
      const meta = SEARCH_TYPE_META[type] || { label: type, view: type };
      const items = parGroupe[type].map((r) => `
        <button type="button" class="search-result-item" data-type="${type}" data-id="${r.id}">
          <div class="title">${escapeHtml(r.label)}</div>
          ${r.sublabel ? `<div class="sub">${escapeHtml(r.sublabel)}</div>` : ""}
        </button>`).join("");
      return `<div class="search-result-group">${meta.label}</div>${items}`;
    }).join("");
  } catch (err) {
    resultsBox.innerHTML = `<div class="search-empty">Erreur : ${escapeHtml(err.message)}</div>`;
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

// ===================== Tableau de bord =====================
const SITE_STATUT_META = {
  non_livre: { label: "Pas encore livre", badge: "badge-gray" },
  en_cours: { label: "En cours de fabrication", badge: "badge-orange" },
  livre: { label: "En ligne", badge: "badge-green" },
};

function renderPresenceSite(p) {
  const meta = SITE_STATUT_META[p.statut] || { label: p.statut, badge: "badge-gray" };
  let rows = `<div class="dash-row"><span>Statut du site</span><span class="badge ${meta.badge}">${meta.label}</span></div>`;
  if (p.url) {
    rows += `<div class="dash-row"><span>Adresse</span><a href="${escapeHtml(p.url)}" target="_blank" rel="noopener">${escapeHtml(p.url)}</a></div>`;
  }
  rows += `<div class="dash-row"><span>Demandes recues (30 derniers jours)</span><strong>${p.nb_demandes_30j}</strong></div>`;
  rows += `<div class="dash-row"><span>Demandes recues (total)</span><strong>${p.nb_demandes_total}</strong></div>`;
  if (p.statut === "non_livre") {
    rows += `<div class="dash-empty">Votre site vitrine professionnel n'est pas encore livre. C'est nous qui le fabriquons et vous le connectons a votre compte : contactez-nous pour en discuter.</div>`;
  }
  return rows;
}

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  container.innerHTML = skeletonCards();
  try {
    const d = await Api.dashboard();
    const stats = [
      { label: "CA ce mois-ci", value: fmtEuro(d.finances.ca_mois) },
      { label: "A encaisser", value: fmtEuro(d.finances.a_encaisser) },
      { label: "Valeur du pipeline", value: fmtEuro(d.commercial.valeur_pipeline) },
      { label: "Devis en attente", value: d.commercial.devis_en_attente },
      { label: "Taux de transformation", value: d.commercial.taux_transformation + "%" },
      { label: "Nouveaux prospects (7j)", value: d.commercial.nouveaux_prospects_7j },
    ];

    const aujourdhuiItems = [
      ...d.aujourdhui.evenements.map((e) => ({
        label: `${new Date(e.date_debut).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })} · ${escapeHtml(e.titre)}`,
        badge: `<span class="badge badge-blue">${e.type}</span>`,
      })),
      ...d.aujourdhui.taches.map((t) => ({
        label: escapeHtml(t.titre),
        badge: `<span class="badge badge-gray">Tache</span>`,
      })),
    ];

    const aTraiterItems = [
      ...d.aujourdhui.devis_a_relancer.map((dv) => ({
        label: `Relancer ${escapeHtml(dv.client_nom)} (${escapeHtml(dv.numero || "devis #" + dv.id)})`,
        badge: `<span class="badge badge-orange">Devis</span>`,
      })),
      ...d.aujourdhui.factures_en_retard.map((f) => ({
        label: `${escapeHtml(f.numero)} · ${escapeHtml(f.client_nom)} · ${fmtEuro(f.montant_restant)} en retard`,
        badge: `<span class="badge badge-red">Facture</span>`,
      })),
      ...d.alertes_conformite.map((c) => ({
        label: `${escapeHtml(c.libelle)} (${c.jours_restants} j)`,
        badge: `<span class="badge badge-red">Conformite</span>`,
      })),
    ];

    container.innerHTML = `
      <div class="dash-grid">
        ${stats.map((s) => `<div class="dash-stat"><div class="value">${s.value}</div><div class="label">${s.label}</div></div>`).join("")}
      </div>
      <div class="dash-two-col">
        <div class="dash-section">
          <h3>Aujourd'hui</h3>
          ${aujourdhuiItems.length
            ? aujourdhuiItems.map((i) => `<div class="dash-row"><span>${i.label}</span>${i.badge}</div>`).join("")
            : '<div class="dash-empty">Rien de prevu aujourd\'hui.</div>'}
        </div>
        <div class="dash-section">
          <h3>A traiter</h3>
          ${aTraiterItems.length
            ? aTraiterItems.map((i) => `<div class="dash-row"><span>${i.label}</span>${i.badge}</div>`).join("")
            : '<div class="dash-empty">Rien qui necessite votre attention.</div>'}
        </div>
      </div>
      ${d.finances.paiements_recents.length ? `
      <div class="dash-section">
        <h3>Paiements recents</h3>
        ${d.finances.paiements_recents.map((p) => `<div class="dash-row"><span>${fmtDate(p.date_paiement)} · ${p.moyen}</span><strong>${fmtEuro(p.montant)}</strong></div>`).join("")}
      </div>` : ""}
      <div class="dash-section">
        <h3>Presence en ligne</h3>
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
      <select data-action="changer-statut-client" data-id="${c.id}">${statutOptions}</select>
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-client" data-id="${c.id}" title="Supprimer">&times;</button>
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
          <div><label for="cli-telephone">Telephone</label><input type="tel" id="cli-telephone"></div>
          <div><label for="cli-email">Email</label><input type="email" id="cli-email"></div>
          <div><label for="cli-societe">Societe</label><input type="text" id="cli-societe"></div>
          <div><label for="cli-adresse">Adresse</label><input type="text" id="cli-adresse"></div>
          <div><label for="cli-ville">Ville</label><input type="text" id="cli-ville"></div>
          <div>
            <label for="cli-source">Source</label>
            <select id="cli-source">${Object.entries(CLIENT_SOURCE_LABELS).map(([v, l]) => `<option value="${v}" ${v === "manuel" ? "selected" : ""}>${l}</option>`).join("")}</select>
          </div>
          <div><label for="cli-montant-estime">Montant estime (EUR)</label><input type="number" step="0.01" min="0" id="cli-montant-estime"></div>
          <div><label for="cli-probabilite">Probabilite (%)</label><input type="number" step="1" min="0" max="100" id="cli-probabilite"></div>
        </div>
        <label for="cli-prochaine-action" style="margin-top:14px;">Prochaine action</label>
        <input type="text" id="cli-prochaine-action" placeholder="Ex: Rappeler jeudi pour confirmer le RDV">
        <label for="cli-notes" style="margin-top:14px;">Notes</label>
        <textarea id="cli-notes" placeholder="Contexte, besoin exprime..."></textarea>
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
      showToast("Contact ajoute.");
      container.hidden = true;
      container.innerHTML = "";
      loadClients();
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    }
  });
}

const TIMELINE_ICONS = {
  prospect_cree: "✨", devis_cree: "\u{1F4C4}", devis_envoye: "\u{1F4E4}",
  devis_consulte: "\u{1F441}️", devis_relance: "\u{1F514}", devis_signe: "✅",
  facture_creee: "\u{1F9FE}", facture_envoyee: "\u{1F4E4}", paiement_recu: "\u{1F4B0}",
  chantier_cree: "\u{1F477}",
};

function clientQuickActionsHtml(client) {
  const actions = [];
  if (client.telephone) actions.push(`<a class="btn-sm" href="tel:${escapeHtml(client.telephone)}">Appeler</a>`);
  if (client.email) actions.push(`<a class="btn-sm" href="mailto:${escapeHtml(client.email)}">Email</a>`);
  actions.push(`<button type="button" class="btn-sm btn-sm-primary" data-action="quick-devis" data-client-id="${client.id}">+ Nouveau devis</button>`);
  actions.push(`<button type="button" class="btn-sm" data-action="demander-avis" data-client-id="${client.id}">Demander un avis</button>`);
  return `<div class="item-actions" style="margin-bottom:18px;">${actions.join("")}</div>`;
}

function clientResumeHtml(r) {
  const rows = [
    { label: "Valeur totale facturee", value: fmtEuro(r.valeur_totale) },
    { label: "Impayes", value: fmtEuro(r.impayes) },
    { label: "Chantiers", value: r.nb_chantiers },
    { label: "Dernier contact", value: r.dernier_contact ? fmtDate(r.dernier_contact) : "-" },
    { label: "Dernier devis", value: r.date_dernier_devis ? fmtDate(r.date_dernier_devis) : "-" },
  ];
  return `<div class="profil-row-group" style="margin-bottom:18px;">
    ${rows.map((row) => `<div class="profil-row"><div class="label">${row.label}</div><div class="value">${row.value}</div></div>`).join("")}
  </div>`;
}

async function showTimeline(clientId) {
  const client = clientsCache.find((c) => c.id === clientId) || (await Api.listClients()).find((c) => c.id === clientId);
  document.getElementById("timeline-titre").textContent = client ? `Historique - ${client.nom}` : "Historique";
  const content = document.getElementById("timeline-content");
  content.innerHTML = skeletonCards();
  document.getElementById("panel-timeline").hidden = false;
  document.getElementById("panel-timeline").dataset.clientId = clientId;

  try {
    const [entries, resume] = await Promise.all([Api.clientTimeline(clientId), Api.clientResume(clientId)]);
    const entriesHtml = entries.length === 0
      ? '<div class="empty-state">Aucun evenement pour le moment.</div>'
      : entries.map((e) => `<div class="timeline-entry">
          <span class="timeline-icon">${TIMELINE_ICONS[e.type] || "•"}</span>
          <div><div class="timeline-label">${escapeHtml(e.label)}</div><div class="timeline-date">${fmtDateTime(e.date)}</div></div>
        </div>`).join("");

    content.innerHTML = (client ? clientQuickActionsHtml(client) : "") + clientResumeHtml(resume) + entriesHtml;
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
      showToast("Statut mis a jour.");
      loadClients();
    });
  });

  document.getElementById("clients-kanban").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "delete-client") {
      if (!confirm("Supprimer ce contact ? Ses devis, factures et chantiers seront supprimes aussi.")) return;
      await withErrorToast(async () => {
        await Api.deleteClient(id);
        showToast("Contact supprime.");
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
          showToast("Lien copie. Envoyez-le a votre client par email ou SMS.");
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

// ===================== Clients (annuaire des affaires gagnees) =====================
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
    container.innerHTML = clients
      .map((c) => {
        const contact = [c.telephone, c.email].filter(Boolean).map(escapeHtml).join(" · ");
        return `
        <div class="item-card">
          <div class="item-card-top">
            <div>
              <div class="item-title">${escapeHtml(c.nom)}${c.societe ? " · " + escapeHtml(c.societe) : ""}</div>
              <div class="item-sub">${contact || "Pas de coordonnees"}${c.ville ? " · " + escapeHtml(c.ville) : ""}</div>
            </div>
          </div>
          <div class="item-actions">
            <button type="button" class="btn-sm" data-action="voir-timeline" data-id="${c.id}">Voir l'historique</button>
          </div>
        </div>`;
      })
      .join("");
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
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
    <input type="text" class="ligne-description" list="prestations-datalist" placeholder="Description de la prestation (recherchez votre catalogue)" value="${escapeHtml(l.description || "")}">
    <input type="number" step="0.01" min="0" class="ligne-quantite" placeholder="Qte" value="${l.quantite ?? 1}">
    <input type="text" class="ligne-unite" placeholder="Unite" value="${escapeHtml(l.unite || "forfait")}">
    <input type="number" step="0.01" min="0" class="ligne-prix" placeholder="PU HT" value="${l.prix_unitaire_ht !== undefined && l.prix_unitaire_ht !== null ? l.prix_unitaire_ht : ""}">
    <button type="button" class="btn-sm btn-sm-danger" data-action="remove-ligne" title="Retirer">&times;</button>
  </div>`;
}

function lignesEditorHtml(containerId, lignes) {
  const rows = (lignes && lignes.length ? lignes : [null]).map(ligneRowHtml).join("");
  return `
  <div class="lignes-editor">
    <label>Prestations</label>
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

function renderDevisCard(d) {
  const meta = DEVIS_STATUT_META[d.statut] || { label: d.statut, badge: "badge-gray" };
  const isDue = devisDueIds.has(d.id);
  const montantTxt = fmtEuro(d.montant_ttc) ? fmtEuro(d.montant_ttc) + " TTC" : "Montant non defini";

  let actions = "";
  if (d.statut === "nouveau") {
    actions += `<button type="button" class="btn-sm" data-action="edit-devis" data-id="${d.id}">Editer / chiffrer</button>`;
    if (d.montant_ht !== null) {
      actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="envoyer-devis" data-id="${d.id}">Envoyer le devis</button>`;
    }
  } else if (["envoye", "relance_j3", "relance_j7"].includes(d.statut)) {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="relancer-devis" data-id="${d.id}">Relancer maintenant</button>`;
  }
  if (["envoye", "relance_j3", "relance_j7", "relance_j15"].includes(d.statut)) {
    actions += `<button type="button" class="btn-sm" data-action="marquer-devis" data-id="${d.id}" data-statut="signe">Marquer signe</button>`;
    actions += `<button type="button" class="btn-sm" data-action="marquer-devis" data-id="${d.id}" data-statut="perdu">Marquer perdu</button>`;
  }
  if (d.statut === "signe") {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="facturer-devis" data-id="${d.id}">Convertir en facture</button>`;
  }
  if (d.lignes && d.lignes.length > 0) {
    actions += `<button type="button" class="btn-sm" data-action="pdf-devis" data-id="${d.id}">Telecharger le PDF</button>`;
  }
  if (d.token && d.statut !== "nouveau") {
    actions += `<button type="button" class="btn-sm" data-action="copier-lien-devis" data-token="${escapeHtml(d.token)}">Copier le lien client</button>`;
  }
  actions += `<button type="button" class="btn-sm" data-action="dupliquer-devis" data-id="${d.id}">Dupliquer</button>`;
  actions += `<button type="button" class="btn-sm btn-sm-danger" data-action="delete-devis" data-id="${d.id}">Supprimer</button>`;

  return `
  <div class="item-card ${isDue ? "is-due" : ""}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(d.client_nom)}</div>
        <div class="item-sub">${escapeHtml(d.titre || d.description || "Pas de description")}</div>
      </div>
      <span class="badge ${meta.badge}">${meta.label}</span>
    </div>
    <div class="item-meta">
      ${montantTxt}${d.numero ? " · " + escapeHtml(d.numero) : ""}
      ${d.remise_montant ? ` · Remise ${d.remise_pourcentage}%` : ""}
      ${isDue ? " · <strong>Relance due aujourd'hui</strong>" : ""}
      · Source : ${d.source === "site_vitrine" ? "Site vitrine" : "Manuel"}
      ${d.statut === "signe" && d.nom_signataire ? ` · Accepte par ${escapeHtml(d.nom_signataire)}` : ""}
    </div>
    <div class="item-actions">${actions}</div>
  </div>`;
}

async function showDevisForm(devis, preselectClientId) {
  const container = document.getElementById("devis-form-container");
  const isEdit = !!devis;
  await Promise.all([ensureClientsCache(), ensurePrestationsCache()]);

  if (!isEdit && clientsCache.length === 0) {
    container.innerHTML = `<div class="form-box"><p>Vous n'avez pas encore de client. Ajoutez d'abord un contact dans l'onglet <strong>Clients &amp; prospects</strong>, puis revenez creer un devis.</p>
      <div class="form-actions"><button type="button" class="btn-sm" data-action="cancel-devis-form">Fermer</button></div></div>`;
    container.hidden = false;
    return;
  }

  container.dataset.editingId = isEdit ? devis.id : "";
  container.innerHTML = `
    <div class="form-box">
      <h3>${isEdit ? "Modifier le devis" : "Nouveau devis"}</h3>
      <form id="devis-form">
        <div class="form-grid">
          <div>
            <label for="df-client">Client *</label>
            ${isEdit
              ? `<input type="text" value="${escapeHtml(devis.client_nom)}" disabled>`
              : `<select id="df-client" required><option value="">Choisir...</option>${clientOptionsHtml(preselectClientId)}</select>`
            }
          </div>
          <div>
            <label for="df-titre">Titre</label>
            <input type="text" id="df-titre" placeholder="Ex: Renovation salle de bain" value="${isEdit ? escapeHtml(devis.titre || "") : ""}">
          </div>
          <div>
            <label for="df-taux-tva">TVA</label>
            <select id="df-taux-tva">
              <option value="10" ${!isEdit || devis.taux_tva === 10 ? "selected" : ""}>10% (renovation)</option>
              <option value="20" ${isEdit && devis.taux_tva === 20 ? "selected" : ""}>20% (neuf)</option>
            </select>
          </div>
          <div>
            <label for="df-acompte">Acompte a la signature (%)</label>
            <input type="number" step="1" min="0" max="100" id="df-acompte" value="${isEdit ? devis.acompte_pourcentage : 30}">
          </div>
          <div>
            <label for="df-remise">Remise (%, optionnel)</label>
            <input type="number" step="1" min="0" max="100" id="df-remise" placeholder="0" value="${isEdit && devis.remise_pourcentage ? devis.remise_pourcentage : ""}">
          </div>
        </div>
        ${lignesEditorHtml("df-lignes", isEdit ? devis.lignes : null)}
        <label for="df-description" style="margin-top:14px;">Description / notes</label>
        <textarea id="df-description">${isEdit ? escapeHtml(devis.description || "") : ""}</textarea>
        <p class="field-error" id="devis-form-error" hidden></p>
        <div class="form-actions">
          <button type="submit" class="btn-sm btn-sm-primary">${isEdit ? "Enregistrer" : "Creer le devis"}</button>
          <button type="button" class="btn-sm" data-action="cancel-devis-form">Annuler</button>
        </div>
      </form>
    </div>`;
  container.hidden = false;
  container.scrollIntoView({ behavior: "smooth", block: "start" });

  const formEl = document.getElementById("devis-form");
  attacherEditeurLignes(formEl);

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
      payload.client_id = parseInt(document.getElementById("df-client").value, 10);
    }

    try {
      if (isEdit) {
        await Api.updateDevis(devis.id, payload);
        showToast("Devis mis a jour.");
      } else {
        await Api.createDevis(payload);
        showToast("Devis cree.");
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
        showToast("Devis envoye. Copiez le lien client pour le transmettre (email, SMS...).");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "relancer-devis") {
      await withErrorToast(async () => {
        await Api.relancerDevis(id);
        showToast("Relance enregistree.");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "marquer-devis") {
      await withErrorToast(async () => {
        await Api.updateDevis(id, { statut: btn.dataset.statut });
        showToast("Statut mis a jour.");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "delete-devis") {
      if (!confirm("Supprimer ce devis ?")) return;
      await withErrorToast(async () => {
        await Api.deleteDevis(id);
        showToast("Devis supprime.");
        loadDevis();
        refreshBadges();
      });
    } else if (btn.dataset.action === "facturer-devis") {
      await withErrorToast(async () => {
        await Api.factureDepuisDevis(id, "standard");
        showToast("Facture creee a partir du devis.");
        switchView("factures");
      });
    } else if (btn.dataset.action === "pdf-devis") {
      await withErrorToast(() => ouvrirPdf(`/devis/${id}/pdf`));
    } else if (btn.dataset.action === "copier-lien-devis") {
      const url = `${window.location.origin}/devis-public.html?t=${btn.dataset.token}`;
      try {
        await navigator.clipboard.writeText(url);
        showToast("Lien copie. Envoyez-le a votre client par email ou SMS.");
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
  const enRetard = enCours.filter((f) => f.est_en_retard).reduce((s, f) => s + f.montant_restant, 0);
  return `
  <div class="dash-grid" style="margin-bottom:20px;">
    <div class="dash-stat"><div class="value">${fmtEuro(aEncaisser)}</div><div class="label">A encaisser</div></div>
    <div class="dash-stat"><div class="value" style="${enRetard > 0 ? "color:var(--danger);" : ""}">${fmtEuro(enRetard)}</div><div class="label">Dont en retard</div></div>
  </div>`;
}

async function loadFactures() {
  const list = document.getElementById("factures-list");
  const tresorerie = document.getElementById("factures-tresorerie");
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
      list.innerHTML = '<div class="empty-state">Aucune facture pour le moment. Convertissez un devis signe, ou creez-en une directement.</div>';
      return;
    }
    list.innerHTML = affichees.map(renderFactureCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

const FACTURE_TYPE_LABELS = { standard: "Standard", acompte: "Acompte", situation: "Situation", finale: "Finale", avoir: "Avoir" };

function renderFactureCard(f) {
  const meta = FACTURE_STATUT_META[f.statut] || { label: f.statut, badge: "badge-gray" };
  const isDue = facturesDueIds.has(f.id);
  const retard = joursRetard(f.date_echeance);
  let actions = "";
  if (f.statut === "brouillon") {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="envoyer-facture" data-id="${f.id}">Marquer envoyee</button>`;
  }
  if (f.montant_restant > 0 && f.statut !== "brouillon" && f.statut !== "annulee") {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="ajouter-paiement" data-id="${f.id}">+ Enregistrer un paiement</button>`;
  }
  if (isDue) {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="relancer-facture" data-id="${f.id}">Relancer</button>`;
  }
  if (f.token && f.statut !== "brouillon") {
    actions += `<button type="button" class="btn-sm" data-action="copier-lien-facture" data-token="${escapeHtml(f.token)}">Copier le lien client</button>`;
  }
  actions += `<button type="button" class="btn-sm" data-action="pdf-facture" data-id="${f.id}">Telecharger le PDF</button>`;
  actions += `<button type="button" class="btn-sm btn-sm-danger" data-action="delete-facture" data-id="${f.id}">Supprimer</button>`;

  const paiementsHtml = (f.paiements || [])
    .map((p) => `<div class="item-sub">${fmtDate(p.date_paiement)} · ${fmtEuro(p.montant)} · ${p.moyen}${p.reference ? " · Ref : " + escapeHtml(p.reference) : ""}</div>`)
    .join("");

  const relanceTxt = f.nb_relances > 0
    ? `<div class="item-sub">${f.nb_relances} relance${f.nb_relances > 1 ? "s" : ""}${f.date_derniere_relance ? " · derniere le " + fmtDate(f.date_derniere_relance) : ""}</div>`
    : "";

  return `
  <div class="item-card ${f.est_en_retard ? "is-due" : ""}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(f.client_nom)} &mdash; ${escapeHtml(f.numero)}</div>
        <div class="item-sub">${FACTURE_TYPE_LABELS[f.type] || f.type}</div>
      </div>
      <span class="badge ${meta.badge}">${meta.label}</span>
    </div>
    <div class="item-meta">
      ${fmtEuro(f.montant_ttc)} TTC · Paye : ${fmtEuro(f.montant_paye)} · Restant : ${fmtEuro(f.montant_restant)}
      ${f.date_echeance ? " · Echeance : " + fmtDate(f.date_echeance) : ""}
      ${retard !== null ? ` · <span style="color:var(--danger);">${retard} j de retard</span>` : ""}
    </div>
    ${paiementsHtml ? `<div class="item-meta">${paiementsHtml}</div>` : ""}
    ${relanceTxt}
    <div class="item-actions" id="facture-actions-${f.id}">${actions}</div>
    <div id="paiement-form-${f.id}"></div>
  </div>`;
}

function showPaiementForm(factureId) {
  const container = document.getElementById(`paiement-form-${factureId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div><label for="pay-montant-${factureId}">Montant (euros) *</label><input type="number" step="0.01" min="0.01" id="pay-montant-${factureId}" required></div>
        <div><label for="pay-date-${factureId}">Date</label><input type="date" id="pay-date-${factureId}" value="${today}"></div>
        <div>
          <label for="pay-moyen-${factureId}">Moyen</label>
          <select id="pay-moyen-${factureId}">
            <option value="virement">Virement</option>
            <option value="cheque">Cheque</option>
            <option value="especes">Especes</option>
            <option value="cb">Carte bancaire</option>
            <option value="autre">Autre</option>
          </select>
        </div>
        <div><label for="pay-reference-${factureId}">Reference (optionnel)</label><input type="text" id="pay-reference-${factureId}" placeholder="N° cheque, ref virement..."></div>
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
          <div class="form-grid">
            <div><label for="fa-client">Client *</label><select id="fa-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select></div>
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
              <select id="fa-tva"><option value="10">10% (renovation)</option><option value="20">20% (neuf)</option></select>
            </div>
            <div><label for="fa-echeance">Date d'echeance</label><input type="date" id="fa-echeance"></div>
          </div>
          ${lignesEditorHtml("fa-lignes", null)}
          <p class="field-error" id="facture-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Creer</button>
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
        showToast("Facture creee.");
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
        showToast("Facture marquee envoyee.");
        loadFactures();
      });
    } else if (btn.dataset.action === "ajouter-paiement") {
      showPaiementForm(id);
    } else if (btn.dataset.action === "cancel-paiement-form") {
      document.getElementById(`paiement-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-paiement") {
      const montant = document.getElementById(`pay-montant-${id}`).value;
      const datePaiement = document.getElementById(`pay-date-${id}`).value;
      const moyen = document.getElementById(`pay-moyen-${id}`).value;
      const reference = document.getElementById(`pay-reference-${id}`).value;
      try {
        await Api.ajouterPaiement(id, { montant: parseFloat(montant), date_paiement: datePaiement, moyen, reference: emptyToNull(reference) });
        showToast("Paiement enregistre.");
        loadFactures();
      } catch (err) {
        const errorBox = document.getElementById(`paiement-error-${id}`);
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "delete-facture") {
      if (!confirm("Supprimer cette facture ?")) return;
      await withErrorToast(async () => {
        await Api.deleteFacture(id);
        showToast("Facture supprimee.");
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
      const url = `${window.location.origin}/facture-public.html?t=${btn.dataset.token}`;
      try {
        await navigator.clipboard.writeText(url);
        showToast("Lien copie. Envoyez-le a votre client par email ou SMS.");
      } catch (err) {
        showToast(url, false);
      }
    }
  });
}

// ===================== Chantiers =====================
async function loadChantiers() {
  const list = document.getElementById("chantiers-list");
  const newBtn = document.querySelector('[data-action="show-chantier-form"]');
  const formContainer = document.getElementById("chantier-form-container");

  if (!isSubscriptionActive()) {
    newBtn.hidden = true;
    formContainer.hidden = true;
    formContainer.innerHTML = "";
    list.innerHTML = renderUpgradeCard(
      "Chantiers reserve aux abonnes",
      "Le suivi de chantier (photos et notes avant/pendant/apres) fait partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  newBtn.hidden = false;

  list.innerHTML = skeletonCards();
  try {
    const chantiers = await Api.listChantiers();
    if (chantiers.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun chantier pour le moment.</div>';
      return;
    }
    list.innerHTML = chantiers.map(renderChantierCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function rentabiliteHtml(c) {
  if (c.total_depenses === 0 && c.montant_facture === null) return "";
  const margeTxt = c.marge_reelle !== null
    ? `<span style="${c.marge_reelle < 0 ? "color:var(--danger);" : ""}">${fmtEuro(c.marge_reelle)}</span>`
    : "-";
  return `
    <div class="dash-grid" style="margin:12px 0;">
      <div class="dash-stat"><div class="value">${fmtEuro(c.total_depenses)}</div><div class="label">Depenses</div></div>
      <div class="dash-stat"><div class="value">${c.montant_facture !== null ? fmtEuro(c.montant_facture) : "-"}</div><div class="label">Facture</div></div>
      <div class="dash-stat"><div class="value">${c.montant_encaisse !== null ? fmtEuro(c.montant_encaisse) : "-"}</div><div class="label">Encaisse</div></div>
      <div class="dash-stat"><div class="value">${margeTxt}</div><div class="label">Marge reelle</div></div>
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
    .map((d) => `<div class="item-sub">${fmtDate(d.date_depense)} · ${escapeHtml(d.libelle)} · ${fmtEuro(d.montant)}</div>`)
    .join("");

  return `
  <div class="item-card">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(c.titre)}</div>
        <div class="item-sub">${escapeHtml(c.client_nom || "")}${c.adresse ? " · " + escapeHtml(c.adresse) : ""}</div>
      </div>
      <span class="badge ${c.statut === "termine" ? "badge-green" : "badge-blue"}">${c.statut === "termine" ? "Termine" : "En cours"}</span>
    </div>
    <div class="item-meta">
      Debut : ${fmtDate(c.date_debut)}
      ${c.budget !== null ? ` · Budget : ${fmtEuro(c.budget)}` : ""}
      ${c.marge_estimee !== null ? ` · Marge estimee : ${fmtEuro(c.marge_estimee)}` : ""}
    </div>
    ${rentabiliteHtml(c)}
    ${depensesHtml ? `<div class="item-meta">${depensesHtml}</div>` : ""}
    <div class="notes-list">${notesHtml || '<div class="item-sub">Aucune note pour le moment.</div>'}</div>
    <div class="item-actions">
      <button type="button" class="btn-sm btn-sm-primary" data-action="toggle-note-form" data-id="${c.id}">+ Ajouter une note</button>
      <button type="button" class="btn-sm" data-action="toggle-depense-form" data-id="${c.id}">+ Ajouter une depense</button>
      ${c.statut !== "termine" ? `<button type="button" class="btn-sm" data-action="terminer-chantier" data-id="${c.id}">Marquer termine</button>` : ""}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-chantier" data-id="${c.id}">Supprimer</button>
    </div>
    <div id="note-form-${c.id}"></div>
    <div id="depense-form-${c.id}"></div>
  </div>`;
}

function showDepenseForm(chantierId) {
  const container = document.getElementById(`depense-form-${chantierId}`);
  if (!container) return;
  const today = new Date().toISOString().slice(0, 10);
  container.innerHTML = `
    <div class="form-box" style="margin-top:12px;">
      <div class="form-grid">
        <div><label for="dep-libelle-${chantierId}">Libelle *</label><input type="text" id="dep-libelle-${chantierId}" placeholder="Ex: Materiaux carrelage"></div>
        <div><label for="dep-montant-${chantierId}">Montant (euros) *</label><input type="number" step="0.01" min="0.01" id="dep-montant-${chantierId}"></div>
        <div><label for="dep-date-${chantierId}">Date</label><input type="date" id="dep-date-${chantierId}" value="${today}"></div>
      </div>
      <p class="field-error" id="depense-error-${chantierId}" hidden></p>
      <div class="form-actions">
        <button type="button" class="btn-sm btn-sm-primary" data-action="submit-depense" data-id="${chantierId}">Ajouter</button>
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
            <option value="apres">Apres</option>
          </select>
        </div>
        <div>
          <label for="note-photo-${chantierId}">URL de la photo (optionnel)</label>
          <input type="url" id="note-photo-${chantierId}" placeholder="https://...">
        </div>
      </div>
      <label for="note-texte-${chantierId}" style="margin-top:14px;">Note</label>
      <textarea id="note-texte-${chantierId}" placeholder="Ex: demolition terminee, prêt pour le carrelage"></textarea>
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
          <div class="form-grid">
            <div><label for="cf-titre">Titre *</label><input type="text" id="cf-titre" required></div>
            <div><label for="cf-client">Client *</label><select id="cf-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select></div>
            <div><label for="cf-adresse">Adresse</label><input type="text" id="cf-adresse"></div>
            <div><label for="cf-date">Date de debut</label><input type="date" id="cf-date"></div>
            <div><label for="cf-budget">Budget prevu (euros)</label><input type="number" step="0.01" min="0" id="cf-budget"></div>
          </div>
          <p class="field-error" id="chantier-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Creer</button>
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
        showToast("Chantier cree.");
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
    const id = parseInt(btn.dataset.id, 10);

    if (btn.dataset.action === "toggle-note-form") {
      showNoteForm(id);
    } else if (btn.dataset.action === "cancel-note-form") {
      document.getElementById(`note-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-note") {
      const texte = document.getElementById(`note-texte-${id}`).value;
      const phase = document.getElementById(`note-phase-${id}`).value;
      const photoUrl = document.getElementById(`note-photo-${id}`).value;
      try {
        await Api.addChantierNote(id, { phase, texte: emptyToNull(texte), photo_url: emptyToNull(photoUrl) });
        showToast("Note ajoutee.");
        loadChantiers();
      } catch (err) {
        const errorBox = document.getElementById(`note-error-${id}`);
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "toggle-depense-form") {
      showDepenseForm(id);
    } else if (btn.dataset.action === "cancel-depense-form") {
      document.getElementById(`depense-form-${id}`).innerHTML = "";
    } else if (btn.dataset.action === "submit-depense") {
      const libelle = document.getElementById(`dep-libelle-${id}`).value.trim();
      const montant = document.getElementById(`dep-montant-${id}`).value;
      const dateDepense = document.getElementById(`dep-date-${id}`).value;
      const errorBox = document.getElementById(`depense-error-${id}`);
      if (!libelle || !montant) {
        errorBox.hidden = false;
        errorBox.textContent = "Libelle et montant sont obligatoires.";
        return;
      }
      try {
        await Api.addChantierDepense(id, { libelle, montant: parseFloat(montant), date_depense: dateDepense });
        showToast("Depense ajoutee.");
        loadChantiers();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    } else if (btn.dataset.action === "terminer-chantier") {
      await withErrorToast(async () => {
        await Api.updateChantier(id, { statut: "termine" });
        showToast("Chantier marque termine.");
        loadChantiers();
      });
    } else if (btn.dataset.action === "delete-chantier") {
      if (!confirm("Supprimer ce chantier et toutes ses notes ?")) return;
      await withErrorToast(async () => {
        await Api.deleteChantier(id);
        showToast("Chantier supprime.");
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
      list.innerHTML = '<div class="empty-state">Aucune tache ici.</div>';
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
    <div class="item-meta">${t.echeance ? "Echeance : " + fmtDate(t.echeance) : "Pas d'echeance"}</div>
    <div class="item-actions">
      ${!estFaite
        ? `<button type="button" class="btn-sm btn-sm-primary" data-action="terminer-tache" data-id="${t.id}">Marquer faite</button>`
        : `<button type="button" class="btn-sm" data-action="reouvrir-tache" data-id="${t.id}">Reouvrir</button>`}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-tache" data-id="${t.id}">Supprimer</button>
    </div>
  </div>`;
}

function showTacheForm() {
  const container = document.getElementById("tache-form-container");
  container.innerHTML = `
    <div class="form-box">
      <h3>Nouvelle tache</h3>
      <form id="tache-form">
        <div class="form-grid">
          <div><label for="ta-titre">Titre *</label><input type="text" id="ta-titre" required></div>
          <div><label for="ta-echeance">Echeance</label><input type="date" id="ta-echeance"></div>
          <div>
            <label for="ta-priorite">Priorite</label>
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
          <button type="submit" class="btn-sm btn-sm-primary">Creer</button>
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
      showToast("Tache creee.");
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
        showToast("Tache marquee faite.");
        loadTaches();
      });
    } else if (btn.dataset.action === "reouvrir-tache") {
      await withErrorToast(async () => {
        await Api.updateTache(id, { statut: "a_faire" });
        loadTaches();
      });
    } else if (btn.dataset.action === "delete-tache") {
      if (!confirm("Supprimer cette tache ?")) return;
      await withErrorToast(async () => {
        await Api.deleteTache(id);
        showToast("Tache supprimee.");
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
    <div class="item-meta">Ajoute le ${fmtDate(d.created_at)}</div>
    <div class="item-actions">
      ${estFichier
        ? `<button type="button" class="btn-sm btn-sm-primary" data-action="telecharger-document" data-id="${d.id}" data-nom="${escapeHtml(d.nom_original)}">Telecharger</button>`
        : `<a class="btn-sm" href="${escapeHtml(d.url)}" target="_blank" rel="noopener">Ouvrir le lien</a>`}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-document" data-id="${d.id}">Supprimer</button>
    </div>
  </div>`;
}

function showDocumentForm() {
  const container = document.getElementById("document-form-container");
  container.innerHTML = "";
  Promise.all([ensureClientsCache(), Api.listChantiers().catch(() => [])]).then(([clients, chantiers]) => {
    const chantierOptions = chantiers
      .map((c) => `<option value="${c.id}">${escapeHtml(c.titre)}</option>`)
      .join("");
    container.innerHTML = `
      <div class="form-box">
        <h3>Ajouter un document</h3>
        <form id="document-form">
          <div class="form-grid">
            <div><label for="doc-fichier">Fichier *</label><input type="file" id="doc-fichier" required accept=".pdf,.jpg,.jpeg,.png,.heic,.heif,.doc,.docx,.xls,.xlsx,.odt,.txt"></div>
            <div><label for="doc-nom">Nom (optionnel)</label><input type="text" id="doc-nom" placeholder="Par defaut : nom du fichier"></div>
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
        showToast("Document ajoute.");
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
      if (!confirm("Supprimer ce document ?")) return;
      await withErrorToast(async () => {
        await Api.deleteDocument(id);
        showToast("Document supprime.");
        loadDocuments();
      });
    }
  });
}

// ===================== Planning =====================
const PLANNING_TYPE_LABELS = { rdv: "RDV", visite: "Visite", intervention: "Intervention", autre: "Autre", tache: "Tache", chantier_debut: "Debut chantier" };

async function loadPlanning() {
  const container = document.getElementById("planning-content");
  container.innerHTML = skeletonCards();
  try {
    const debut = new Date();
    const fin = new Date();
    fin.setDate(fin.getDate() + 13);
    const toIso = (d) => d.toISOString().slice(0, 10);
    const items = await Api.planning(toIso(debut), toIso(fin));

    if (items.length === 0) {
      container.innerHTML = '<div class="empty-state">Rien de prevu dans les 14 prochains jours. Ajoutez un rendez-vous, ou planifiez une tache / un chantier avec une date.</div>';
      return;
    }

    const parJour = {};
    items.forEach((i) => {
      const jour = i.date.slice(0, 10);
      (parJour[jour] = parJour[jour] || []).push(i);
    });

    container.innerHTML = Object.keys(parJour).sort().map((jour) => {
      const dateLisible = new Date(jour + "T00:00:00").toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });
      const rows = parJour[jour].map((i) => {
        const heure = i.type === "chantier_debut" ? "" : new Date(i.date).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) + " · ";
        return `<div class="dash-row"><span>${heure}${escapeHtml(i.titre)}</span><span class="badge badge-blue">${PLANNING_TYPE_LABELS[i.type] || i.type}</span></div>`;
      }).join("");
      return `<div class="dash-section"><h3 style="text-transform:capitalize;">${dateLisible}</h3>${rows}</div>`;
    }).join("");
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function setupPlanningView() {
  document.querySelector('[data-action="show-evenement-form"]').addEventListener("click", async () => {
    const container = document.getElementById("evenement-form-container");
    await ensureClientsCache();
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouveau rendez-vous</h3>
        <form id="evenement-form">
          <div class="form-grid">
            <div><label for="ev-titre">Titre *</label><input type="text" id="ev-titre" required></div>
            <div>
              <label for="ev-type">Type</label>
              <select id="ev-type">
                <option value="rdv">Rendez-vous</option>
                <option value="visite">Visite</option>
                <option value="intervention">Intervention</option>
                <option value="autre">Autre</option>
              </select>
            </div>
            <div><label for="ev-date">Date *</label><input type="date" id="ev-date" required></div>
            <div><label for="ev-heure">Heure</label><input type="time" id="ev-heure" value="09:00"></div>
            <div><label for="ev-client">Client (optionnel)</label><select id="ev-client"><option value="">Aucun</option>${clientOptionsHtml()}</select></div>
            <div><label for="ev-lieu">Lieu</label><input type="text" id="ev-lieu"></div>
          </div>
          <p class="field-error" id="evenement-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Creer</button>
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
      try {
        await Api.createEvenement({
          titre: document.getElementById("ev-titre").value,
          type: document.getElementById("ev-type").value,
          date_debut: new Date(`${dateVal}T${heureVal}:00`).toISOString(),
          lieu: emptyToNull(document.getElementById("ev-lieu").value),
          client_id: clientVal ? parseInt(clientVal, 10) : null,
        });
        showToast("Rendez-vous cree.");
        container.hidden = true;
        container.innerHTML = "";
        loadPlanning();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  });

  document.getElementById("evenement-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-evenement-form"]')) {
      const container = document.getElementById("evenement-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });
}

// ===================== Conformite =====================
async function loadConformite() {
  const list = document.getElementById("conformite-list");
  const banner = document.getElementById("conformite-alert-banner");
  const newBtn = document.querySelector('[data-action="show-conformite-form"]');
  const formContainer = document.getElementById("conformite-form-container");

  if (!isSubscriptionActive()) {
    newBtn.hidden = true;
    formContainer.hidden = true;
    formContainer.innerHTML = "";
    banner.hidden = true;
    list.innerHTML = renderUpgradeCard(
      "Conformite reservee aux abonnes",
      "Le suivi des echeances (assurance decennale, Qualibat, RGE) et les alertes automatiques font partie de l'abonnement mensuel Suite Artisan."
    );
    return;
  }
  newBtn.hidden = false;

  list.innerHTML = skeletonCards();
  try {
    const [items, alertes] = await Promise.all([Api.listConformite(), Api.conformiteAlertes()]);

    if (alertes.length > 0) {
      banner.hidden = false;
      banner.textContent = `${alertes.length} element(s) de conformite arrivent a echeance dans moins de 30 jours (ou sont deja expires).`;
    } else {
      banner.hidden = true;
    }

    if (items.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucun element de conformite enregistre.</div>';
      return;
    }
    list.innerHTML = items.map(renderConformiteCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

function renderConformiteCard(item) {
  const badgeClass = item.alerte ? "badge-red" : "badge-green";
  const badgeLabel = item.jours_restants < 0 ? "Expire" : item.alerte ? `Expire dans ${item.jours_restants} j` : "A jour";
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
    if (!confirm("Supprimer cet element de conformite ?")) return;
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
    showToast("Votre session a expire, merci de vous reconnecter.", true);
  };

  setupAuthScreen();
  setupTabs();
  setupProfilPanel();
  setupGlobalSearch();
  setupClientsView();
  setupEntrepriseForm();
  setupAutomatisationForm();
  setupEquipeView();
  setupPrestationsView();
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
        showToast("Paiement recu ! Votre abonnement Pro s'active dans quelques instants.");
      } else if (abonnement === "annule") {
        showToast("Abonnement annule, vous pouvez reessayer a tout moment depuis votre profil.", true);
      }
      return;
    } catch (err) {
      clearToken();
    }
  }
  showAuthScreen();
});
