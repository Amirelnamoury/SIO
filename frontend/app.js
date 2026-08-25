// ===================== Etat global =====================
let currentArtisan = null;
let currentDevisFilter = "";
let devisDueIds = new Set();

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

let toastTimer = null;
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
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
  return `
  <div class="upgrade-card">
    <div class="upgrade-icon">&#128274;</div>
    <h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(description)}</p>
    <button type="button" class="btn-primary" data-action="upgrade-subscription">S'abonner a Suite Artisan</button>
  </div>`;
}

async function attemptUpgrade() {
  try {
    const data = await Api.checkoutSession();
    window.location.href = data.checkout_url;
  } catch (err) {
    if (err.message.toLowerCase().includes("stripe")) {
      showToast("Le paiement en ligne n'est pas encore active sur ce compte. Contactez l'administrateur pour activer votre abonnement.", true);
    } else {
      showToast(err.message, true);
    }
  }
}

document.addEventListener("click", (e) => {
  if (e.target.closest('[data-action="upgrade-subscription"]')) {
    attemptUpgrade();
  }
});

// ===================== Coquille du tableau de bord =====================
function enterDashboard() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("dashboard-screen").hidden = false;
  switchView("dashboard");
  refreshBadges();
}

function switchView(view) {
  document.querySelectorAll(".nav-link").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `view-${view}`;
  });
  if (view === "dashboard") loadDashboard();
  if (view === "clients") loadClients();
  if (view === "devis") loadDevis();
  if (view === "factures") loadFactures();
  if (view === "chantiers") loadChantiers();
  if (view === "planning") loadPlanning();
  if (view === "taches") loadTaches();
  if (view === "conformite") loadConformite();
}

async function refreshBadges() {
  // Les deux compteurs sont independants : la conformite est une fonction payante
  // (402 si l'abonnement n'est pas actif), on ne veut pas que ca empeche le badge
  // des relances (gratuit) de s'afficher. D'ou Promise.allSettled plutot que Promise.all.
  const [relancerResult, alertesResult] = await Promise.allSettled([Api.devisARelancer(), Api.conformiteAlertes()]);

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
        ${!isSubscriptionActive() ? '<button type="button" class="btn-primary" data-action="upgrade-subscription" style="margin-top:10px;width:100%;">S\'abonner</button>' : ""}
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

function setupTabs() {
  document.querySelectorAll(".nav-link").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });
}

// ===================== Tableau de bord =====================
async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  container.innerHTML = '<div class="empty-state">Chargement...</div>';
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
  board.innerHTML = '<div class="empty-state">Chargement...</div>';
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

  return `
  <div class="kanban-card" data-action="voir-timeline" data-id="${c.id}">
    <div class="kanban-card-title">${escapeHtml(c.nom)}</div>
    <div class="kanban-card-sub">${contact || "Pas de coordonnees"}${c.societe ? " · " + escapeHtml(c.societe) : ""}</div>
    ${c.source === "site_vitrine" ? '<div class="kanban-card-sub">Source : site vitrine</div>' : ""}
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
        </div>
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

async function showTimeline(clientId) {
  const client = clientsCache.find((c) => c.id === clientId) || (await Api.listClients()).find((c) => c.id === clientId);
  document.getElementById("timeline-titre").textContent = client ? `Historique - ${client.nom}` : "Historique";
  const content = document.getElementById("timeline-content");
  content.innerHTML = '<div class="empty-state">Chargement...</div>';
  document.getElementById("panel-timeline").hidden = false;

  try {
    const entries = await Api.clientTimeline(clientId);
    if (entries.length === 0) {
      content.innerHTML = '<div class="empty-state">Aucun evenement pour le moment.</div>';
      return;
    }
    content.innerHTML = entries
      .map(
        (e) => `<div class="timeline-entry">
          <span class="timeline-icon">${TIMELINE_ICONS[e.type] || "•"}</span>
          <div><div class="timeline-label">${escapeHtml(e.label)}</div><div class="timeline-date">${fmtDateTime(e.date)}</div></div>
        </div>`
      )
      .join("");
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

  document.getElementById("panel-timeline").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="close-timeline"]') || e.target.id === "panel-timeline") {
      document.getElementById("panel-timeline").hidden = true;
    }
  });
}

// ===================== Devis & relances =====================
async function loadDevis() {
  const list = document.getElementById("devis-list");
  list.innerHTML = '<div class="empty-state">Chargement...</div>';
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
      ${isDue ? " · <strong>Relance due aujourd'hui</strong>" : ""}
      · Source : ${d.source === "site_vitrine" ? "Site vitrine" : "Manuel"}
    </div>
    <div class="item-actions">${actions}</div>
  </div>`;
}

async function showDevisForm(devis) {
  const container = document.getElementById("devis-form-container");
  const isEdit = !!devis;
  await ensureClientsCache();

  if (!isEdit && clientsCache.length === 0) {
    container.innerHTML = `<div class="form-box"><p>Vous n'avez pas encore de client. Ajoutez d'abord un contact dans l'onglet <strong>Clients &amp; prospects</strong>, puis revenez creer un devis.</p>
      <div class="form-actions"><button type="button" class="btn-sm" data-action="cancel-devis-form">Fermer</button></div></div>`;
    container.hidden = false;
    return;
  }

  container.dataset.editingId = isEdit ? devis.id : "";
  const montantActuel = isEdit && devis.montant_ht !== null ? devis.montant_ht : "";
  container.innerHTML = `
    <div class="form-box">
      <h3>${isEdit ? "Modifier le devis" : "Nouveau devis"}</h3>
      <form id="devis-form">
        <div class="form-grid">
          <div>
            <label for="df-client">Client *</label>
            ${isEdit
              ? `<input type="text" value="${escapeHtml(devis.client_nom)}" disabled>`
              : `<select id="df-client" required><option value="">Choisir...</option>${clientOptionsHtml()}</select>`
            }
          </div>
          <div>
            <label for="df-titre">Titre</label>
            <input type="text" id="df-titre" placeholder="Ex: Renovation salle de bain" value="${isEdit ? escapeHtml(devis.titre || "") : ""}">
          </div>
          <div>
            <label for="df-montant-ht">Montant HT (euros)</label>
            <input type="number" step="0.01" min="0" id="df-montant-ht" value="${montantActuel}">
          </div>
          <div>
            <label for="df-taux-tva">TVA</label>
            <select id="df-taux-tva">
              <option value="10" ${!isEdit || devis.taux_tva === 10 ? "selected" : ""}>10% (renovation)</option>
              <option value="20" ${isEdit && devis.taux_tva === 20 ? "selected" : ""}>20% (neuf)</option>
            </select>
          </div>
        </div>
        <label for="df-description" style="margin-top:14px;">Description</label>
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

  document.getElementById("devis-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById("devis-form-error");
    errorBox.hidden = true;
    const montantRaw = document.getElementById("df-montant-ht").value;
    const titre = document.getElementById("df-titre").value;
    const description = document.getElementById("df-description").value;
    const lignes = montantRaw === "" ? undefined : [{
      description: description || titre || "Prestation", quantite: 1, unite: "forfait", prix_unitaire_ht: parseFloat(montantRaw),
    }];

    const payload = {
      titre: emptyToNull(titre),
      description: emptyToNull(description),
      taux_tva: parseFloat(document.getElementById("df-taux-tva").value),
      lignes,
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
        showToast("Devis marque comme envoye. Le cycle de relance a demarre.");
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

async function loadFactures() {
  const list = document.getElementById("factures-list");
  list.innerHTML = '<div class="empty-state">Chargement...</div>';
  try {
    const factures = await Api.listFactures(currentFactureFilter);
    if (factures.length === 0) {
      list.innerHTML = '<div class="empty-state">Aucune facture pour le moment. Convertissez un devis signe, ou creez-en une directement.</div>';
      return;
    }
    list.innerHTML = factures.map(renderFactureCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

const FACTURE_TYPE_LABELS = { standard: "Standard", acompte: "Acompte", situation: "Situation", finale: "Finale", avoir: "Avoir" };

function renderFactureCard(f) {
  const meta = FACTURE_STATUT_META[f.statut] || { label: f.statut, badge: "badge-gray" };
  let actions = "";
  if (f.statut === "brouillon") {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="envoyer-facture" data-id="${f.id}">Marquer envoyee</button>`;
  }
  if (f.montant_restant > 0 && f.statut !== "brouillon" && f.statut !== "annulee") {
    actions += `<button type="button" class="btn-sm btn-sm-primary" data-action="ajouter-paiement" data-id="${f.id}">+ Enregistrer un paiement</button>`;
  }
  actions += `<button type="button" class="btn-sm btn-sm-danger" data-action="delete-facture" data-id="${f.id}">Supprimer</button>`;

  const paiementsHtml = (f.paiements || [])
    .map((p) => `<div class="item-sub">${fmtDate(p.date_paiement)} · ${fmtEuro(p.montant)} · ${p.moyen}</div>`)
    .join("");

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
    </div>
    ${paiementsHtml ? `<div class="item-meta">${paiementsHtml}</div>` : ""}
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
  ensureClientsCache().then(() => {
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
            <div><label for="fa-description">Description de la prestation *</label><input type="text" id="fa-description" required></div>
            <div><label for="fa-montant">Montant HT (euros) *</label><input type="number" step="0.01" min="0.01" id="fa-montant" required></div>
            <div>
              <label for="fa-tva">TVA</label>
              <select id="fa-tva"><option value="10">10% (renovation)</option><option value="20">20% (neuf)</option></select>
            </div>
            <div><label for="fa-echeance">Date d'echeance</label><input type="date" id="fa-echeance"></div>
          </div>
          <p class="field-error" id="facture-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">Creer</button>
            <button type="button" class="btn-sm" data-action="cancel-facture-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("facture-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("facture-form-error");
      errorBox.hidden = true;
      try {
        await Api.createFacture({
          client_id: parseInt(document.getElementById("fa-client").value, 10),
          taux_tva: parseFloat(document.getElementById("fa-tva").value),
          date_echeance: emptyToNull(document.getElementById("fa-echeance").value),
          lignes: [{
            description: document.getElementById("fa-description").value,
            quantite: 1, unite: "forfait",
            prix_unitaire_ht: parseFloat(document.getElementById("fa-montant").value),
          }],
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
      try {
        await Api.ajouterPaiement(id, { montant: parseFloat(montant), date_paiement: datePaiement, moyen });
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

  list.innerHTML = '<div class="empty-state">Chargement...</div>';
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
    <div class="notes-list">${notesHtml || '<div class="item-sub">Aucune note pour le moment.</div>'}</div>
    <div class="item-actions">
      <button type="button" class="btn-sm btn-sm-primary" data-action="toggle-note-form" data-id="${c.id}">+ Ajouter une note</button>
      ${c.statut !== "termine" ? `<button type="button" class="btn-sm" data-action="terminer-chantier" data-id="${c.id}">Marquer termine</button>` : ""}
      <button type="button" class="btn-sm btn-sm-danger" data-action="delete-chantier" data-id="${c.id}">Supprimer</button>
    </div>
    <div id="note-form-${c.id}"></div>
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
  list.innerHTML = '<div class="empty-state">Chargement...</div>';
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

// ===================== Planning =====================
const PLANNING_TYPE_LABELS = { rdv: "RDV", visite: "Visite", intervention: "Intervention", autre: "Autre", tache: "Tache", chantier_debut: "Debut chantier" };

async function loadPlanning() {
  const container = document.getElementById("planning-content");
  container.innerHTML = '<div class="empty-state">Chargement...</div>';
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

  list.innerHTML = '<div class="empty-state">Chargement...</div>';
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
  setupClientsView();
  setupDevisView();
  setupFacturesView();
  setupChantiersView();
  setupPlanningView();
  setupTachesView();
  setupConformiteView();

  const toast = document.createElement("div");
  toast.id = "toast";
  document.body.appendChild(toast);

  const token = getToken();
  if (token) {
    try {
      currentArtisan = await Api.me();
      enterDashboard();
      return;
    } catch (err) {
      clearToken();
    }
  }
  showAuthScreen();
});
