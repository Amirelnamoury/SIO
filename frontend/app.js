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
  relance_j3: { label: "Relance J+3", badge: "badge-orange" },
  relance_j7: { label: "Relance J+7", badge: "badge-orange" },
  relance_j15: { label: "Relance J+15", badge: "badge-red" },
  signe: { label: "Signe", badge: "badge-green" },
  perdu: { label: "Perdu", badge: "badge-gray" },
};

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

// ===================== Coquille du tableau de bord =====================
function enterDashboard() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("dashboard-screen").hidden = false;
  switchView("devis");
  refreshBadges();
}

function switchView(view) {
  document.querySelectorAll(".tab-link").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `view-${view}`;
  });
  if (view === "devis") loadDevis();
  if (view === "chantiers") loadChantiers();
  if (view === "conformite") loadConformite();
}

async function refreshBadges() {
  try {
    const [aRelancer, alertes] = await Promise.all([Api.devisARelancer(), Api.conformiteAlertes()]);
    devisDueIds = new Set(aRelancer.map((d) => d.id));

    const badgeRelances = document.getElementById("badge-relances");
    badgeRelances.textContent = aRelancer.length;
    badgeRelances.hidden = aRelancer.length === 0;

    const badgeAlertes = document.getElementById("badge-alertes");
    badgeAlertes.textContent = alertes.length;
    badgeAlertes.hidden = alertes.length === 0;
  } catch (err) {
    // les badges sont un bonus d'affichage, on ne bloque pas le reste si ca echoue
    console.warn("Impossible de charger les compteurs :", err.message);
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
      <div class="profil-row"><div class="label">Abonnement</div><div class="value">${escapeHtml(currentArtisan.subscription_status)}</div></div>
      <div class="profil-row"><div class="label">Lien public du formulaire de devis</div><div class="value" style="font-weight:400;font-size:0.82rem;">${escapeHtml(publicUrl)}</div></div>
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
  document.querySelectorAll(".tab-link").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
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
  actions += `<button type="button" class="btn-sm btn-sm-danger" data-action="delete-devis" data-id="${d.id}">Supprimer</button>`;

  const contact = [d.client_telephone, d.client_email].filter(Boolean).map(escapeHtml).join(" · ");

  return `
  <div class="item-card ${isDue ? "is-due" : ""}">
    <div class="item-card-top">
      <div>
        <div class="item-title">${escapeHtml(d.client_nom)}</div>
        <div class="item-sub">${escapeHtml(d.description || "Pas de description")}</div>
      </div>
      <span class="badge ${meta.badge}">${meta.label}</span>
    </div>
    <div class="item-meta">
      ${montantTxt}${contact ? " · " + contact : ""}
      ${isDue ? " · <strong>Relance due aujourd'hui</strong>" : ""}
      · Source : ${d.source === "site_vitrine" ? "Site vitrine" : "Manuel"}
    </div>
    <div class="item-actions">${actions}</div>
  </div>`;
}

function showDevisForm(devis) {
  const container = document.getElementById("devis-form-container");
  const isEdit = !!devis;
  container.dataset.editingId = isEdit ? devis.id : "";
  container.innerHTML = `
    <div class="form-box">
      <h3>${isEdit ? "Modifier le devis" : "Nouveau devis"}</h3>
      <form id="devis-form">
        <div class="form-grid">
          <div>
            <label for="df-client-nom">Nom du client *</label>
            <input type="text" id="df-client-nom" required value="${isEdit ? escapeHtml(devis.client_nom) : ""}">
          </div>
          <div>
            <label for="df-client-telephone">Telephone</label>
            <input type="tel" id="df-client-telephone" value="${isEdit ? escapeHtml(devis.client_telephone || "") : ""}">
          </div>
          <div>
            <label for="df-client-email">Email</label>
            <input type="email" id="df-client-email" value="${isEdit ? escapeHtml(devis.client_email || "") : ""}">
          </div>
          <div>
            <label for="df-montant-ht">Montant HT (euros)</label>
            <input type="number" step="0.01" min="0" id="df-montant-ht" value="${isEdit && devis.montant_ht !== null ? devis.montant_ht : ""}">
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
    const payload = {
      client_nom: document.getElementById("df-client-nom").value,
      client_telephone: emptyToNull(document.getElementById("df-client-telephone").value),
      client_email: emptyToNull(document.getElementById("df-client-email").value),
      montant_ht: montantRaw === "" ? null : parseFloat(montantRaw),
      taux_tva: parseFloat(document.getElementById("df-taux-tva").value),
      description: emptyToNull(document.getElementById("df-description").value),
    };
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

// ===================== Chantiers =====================
async function loadChantiers() {
  const list = document.getElementById("chantiers-list");
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
    <div class="item-meta">Debut : ${fmtDate(c.date_debut)}</div>
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
  document.querySelector('[data-action="show-chantier-form"]').addEventListener("click", () => {
    const container = document.getElementById("chantier-form-container");
    container.innerHTML = `
      <div class="form-box">
        <h3>Nouveau chantier</h3>
        <form id="chantier-form">
          <div class="form-grid">
            <div><label for="cf-titre">Titre *</label><input type="text" id="cf-titre" required></div>
            <div><label for="cf-client">Client</label><input type="text" id="cf-client"></div>
            <div><label for="cf-adresse">Adresse</label><input type="text" id="cf-adresse"></div>
            <div><label for="cf-date">Date de debut</label><input type="date" id="cf-date"></div>
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
      try {
        await Api.createChantier({
          titre: document.getElementById("cf-titre").value,
          client_nom: emptyToNull(document.getElementById("cf-client").value),
          adresse: emptyToNull(document.getElementById("cf-adresse").value),
          date_debut: emptyToNull(document.getElementById("cf-date").value),
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

// ===================== Conformite =====================
async function loadConformite() {
  const list = document.getElementById("conformite-list");
  const banner = document.getElementById("conformite-alert-banner");
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
  setupDevisView();
  setupChantiersView();
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
