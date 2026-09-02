(function () {
  "use strict";

  const isLocalFrontend = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const API_BASE = (window.SUITE_ARTISAN_API_BASE || (isLocalFrontend ? "http://localhost:8000" : window.location.origin)).replace(/\/$/, "");
  const ADMIN_TOKEN_KEY = "suite_artisan_admin_token";

  function apiUrl(path) {
    return API_BASE + path;
  }

  const loginForm = document.getElementById("admin-login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const error = document.getElementById("login-error");
      error.textContent = "";
      try {
        const response = await fetch(apiUrl("/admin/auth/login"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: document.getElementById("login-email").value, password: document.getElementById("login-password").value }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Connexion impossible");
        window.sessionStorage.setItem(ADMIN_TOKEN_KEY, data.access_token);
        window.location.assign("/admin/");
      } catch (err) {
        error.textContent = err.message;
      }
    });
    return;
  }

  const state = {
    currentView: "dashboard", previousView: "artisans", artisan: null,
    artisanItems: [], siteItems: [], artisanFilter: "all", siteFilter: "all", currentTab: "overview",
  };
  // "genere" est un statut technique historique (sites crees avant le
  // retrait du moteur de generation) : il reste lisible tel quel en base,
  // mais son libelle affiche ne doit plus jamais laisser croire qu'une
  // generation automatique vient de se produire ou peut encore se produire.
  // Il est presente comme un site encore a finaliser.
  const statusLabels = { non_cree: "Non créé", brouillon: "Brouillon", genere: "À finaliser", pret: "Prêt", publie: "Publié" };
  const PLAN_LABELS = { gratuit: "Gratuit", essentiel: "Essentiel", pro: "Pro", business: "Business" };
  const ARTISAN_FILTERS = [
    ["all", "Tous", null],
    ["non_cree", "Sans site", "non_cree"],
    ["brouillon", "À préparer", "brouillon"],
    ["genere", "À finaliser", "genere"],
    ["pret", "Prêts", "pret"],
    ["publie", "Publiés", "publie"],
  ];
  const SITE_FILTERS = [
    ["all", "Tous", null],
    ["brouillon", "À préparer", "brouillon"],
    ["genere", "À finaliser", "genere"],
    ["pret", "Prêts", "pret"],
    ["publie", "Publiés", "publie"],
  ];

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>'"]/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char];
    });
  }

  function formatDate(value) {
    return value ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(new Date(value)) : "Jamais";
  }

  function pill(value, label) {
    return `<span class="status-pill ${escapeHtml(value)}">${escapeHtml(label || statusLabels[value] || value)}</span>`;
  }

  function toast(message, isError) {
    const node = document.getElementById("toast");
    node.textContent = message;
    node.className = "toast show" + (isError ? " error" : "");
    window.clearTimeout(toast.timer);
    toast.timer = window.setTimeout(function () { node.className = "toast"; }, 3200);
  }

  async function api(path, options) {
    const opts = Object.assign({ credentials: "same-origin" }, options || {});
    opts.headers = Object.assign({}, opts.body ? { "Content-Type": "application/json" } : {}, opts.headers || {});
    const token = window.sessionStorage.getItem(ADMIN_TOKEN_KEY);
    if (token) opts.headers.Authorization = "Bearer " + token;
    const response = await fetch(apiUrl(path), opts);
    if (response.status === 401) {
      window.sessionStorage.removeItem(ADMIN_TOKEN_KEY);
      window.location.assign("/admin/login.html");
      throw new Error("Session expirée");
    }
    let data = null;
    if (response.status !== 204) {
      try { data = await response.json(); } catch (err) { data = null; }
    }
    if (!response.ok) throw new Error(data && data.detail ? data.detail : "Action impossible");
    return data;
  }

  function showView(name, title) {
    document.querySelectorAll(".view").forEach(function (view) { view.classList.remove("active"); });
    document.getElementById("view-" + name).classList.add("active");
    document.querySelectorAll(".nav-item").forEach(function (item) { item.classList.toggle("active", item.dataset.view === name); });
    document.getElementById("page-title").textContent = title;
    state.currentView = name;
    closeDrawer();
  }

  function showTab(name) {
    document.querySelectorAll(".tab-item").forEach(function (t) { t.classList.toggle("active", t.dataset.tab === name); });
    document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.toggle("active", p.id === "tab-panel-" + name); });
    state.currentTab = name;
  }

  // ---------- Menu mobile ----------
  const sidebarEl = document.getElementById("sidebar");
  const drawerScrim = document.getElementById("drawer-scrim");
  const drawerToggle = document.getElementById("drawer-toggle");
  function closeDrawer() {
    if (!sidebarEl) return;
    sidebarEl.classList.remove("open");
    if (drawerScrim) drawerScrim.hidden = true;
    if (drawerToggle) drawerToggle.setAttribute("aria-expanded", "false");
  }
  function openDrawer() {
    if (!sidebarEl) return;
    sidebarEl.classList.add("open");
    if (drawerScrim) drawerScrim.hidden = false;
    if (drawerToggle) drawerToggle.setAttribute("aria-expanded", "true");
  }
  if (drawerToggle) {
    drawerToggle.addEventListener("click", function () {
      if (sidebarEl.classList.contains("open")) closeDrawer(); else openDrawer();
    });
  }
  if (drawerScrim) drawerScrim.addEventListener("click", closeDrawer);

  async function loadDashboard() {
    showView("dashboard", "Vue d'ensemble");
    const [metrics, artisansData] = await Promise.all([
      api("/admin/api/dashboard"),
      api("/admin/api/artisans?limit=100"),
    ]);
    renderDashboardMetrics(metrics);
    renderAttentionGroups(artisansData.items);
    renderRecentSites(artisansData.items);
  }

  function renderDashboardMetrics(data) {
    // "sites_generes" est un decompte technique (statut historique "genere"
    // en base) : cote UI il compte comme un site encore a preparer, jamais
    // comme une production active du moteur retire.
    const metrics = [
      ["Artisans", data.artisans_total, false],
      ["Sites à préparer", data.sites_brouillon + data.sites_generes, false],
      ["Sites prêts", data.sites_prets, data.sites_prets > 0],
      ["Sites publiés", data.sites_publies, false],
    ];
    document.getElementById("metric-grid").innerHTML = metrics.map(function (item) {
      return `<article class="metric${item[2] ? " metric-accent" : ""}"><span>${item[0]}</span><strong>${item[1]}</strong></article>`;
    }).join("");
  }

  function attentionRow(item) {
    return '<div class="attention-row" data-open-id="' + item.id + '"><span class="attention-row-title">' + escapeHtml(item.nom_entreprise) +
      '</span><span class="attention-row-sub">' + escapeHtml(item.ville || item.metier) + '</span></div>';
  }

  function bindOpenRows(container) {
    container.querySelectorAll("[data-open-id]").forEach(function (row) {
      row.addEventListener("click", function () { openArtisan(Number(row.dataset.openId)).catch(handleError); });
    });
  }

  function renderAttentionGroups(items) {
    const groups = [
      ["Sites à démarrer", "Aucun site à démarrer pour l'instant.", items.filter(function (i) { return i.site_statut === "non_cree" || i.site_statut === "brouillon"; })],
      ["Sites à finaliser", "Rien à finaliser pour le moment.", items.filter(function (i) { return i.site_statut === "genere"; })],
      ["Prêts à publier", "Aucun site en attente de publication.", items.filter(function (i) { return i.site_statut === "pret"; })],
      ["Médias manquants", "Tous les sites suivis ont au moins un média actif.", items.filter(function (i) { return i.media_manquant; })],
    ];
    const el = document.getElementById("attention-groups");
    el.innerHTML = groups.map(function (group) {
      const label = group[0], emptyText = group[1], list = group[2];
      const shown = list.slice(0, 5);
      const rows = shown.length ? shown.map(attentionRow).join("") : '<p class="attention-empty">' + escapeHtml(emptyText) + '</p>';
      const more = list.length > shown.length ? '<span class="attention-more">+ ' + (list.length - shown.length) + ' autre(s)</span>' : "";
      return '<div class="attention-group' + (list.length ? " has-items" : "") + '"><div class="attention-group-heading"><h3>' + escapeHtml(label) +
        '</h3><span class="count-badge">' + list.length + '</span></div><div class="attention-list">' + rows + '</div>' + more + '</div>';
    }).join("");
    bindOpenRows(el);
  }

  function renderRecentSites(items) {
    const sites = items.filter(function (i) { return i.site_statut !== "non_cree"; }).slice(0, 8);
    const el = document.getElementById("recent-sites");
    if (!sites.length) {
      el.innerHTML = '<div class="empty-state"><strong>Aucun site en cours</strong><p>Les sites récemment suivis apparaîtront ici.</p></div>';
      return;
    }
    el.innerHTML = sites.map(function (item) {
      return '<div class="recent-site-row" data-open-id="' + item.id + '"><div><div class="cell-title">' + escapeHtml(item.nom_entreprise) +
        '</div><div class="cell-sub">' + escapeHtml(item.metier) + (item.ville ? " · " + escapeHtml(item.ville) : "") + '</div></div>' +
        pill(item.site_statut) + '<span class="recent-site-when">' + formatDate(item.created_at) + '</span></div>';
    }).join("");
    bindOpenRows(el);
  }

  function artisanRows(items, sitesMode) {
    if (!items.length) return `<tr><td colspan="${sitesMode ? 6 : 7}" class="muted">Aucun résultat</td></tr>`;
    return items.map(function (item) {
      const openCell = '<td class="cell-actions"><span class="row-open-hint">Ouvrir →</span></td>';
      if (sitesMode) {
        return `<tr data-id="${item.id}"><td><div class="cell-title">${escapeHtml(item.nom_entreprise)}</div><div class="cell-sub">${escapeHtml(item.slug)}</div></td><td>${escapeHtml(item.metier)}</td><td>${pill(item.site_statut)}</td><td>${escapeHtml(item.domaine || "-")}</td><td>${escapeHtml(item.url_publique || "-")}</td>${openCell}</tr>`;
      }
      return `<tr data-id="${item.id}"><td><div class="cell-title">${escapeHtml(item.nom_entreprise)}</div><div class="cell-sub">${escapeHtml(item.email)}</div></td><td>${escapeHtml(item.metier)}</td><td>${escapeHtml(item.ville || "-")}</td><td>${escapeHtml(item.plan)}</td><td>${pill(item.subscription_status)}</td><td>${pill(item.site_statut)}</td>${openCell}</tr>`;
    }).join("");
  }

  function bindRows(table) {
    table.querySelectorAll("tr[data-id]").forEach(function (row) {
      row.addEventListener("click", function () { openArtisan(Number(row.dataset.id)); });
    });
  }

  function filterByStatut(items, filters, activeKey) {
    const def = filters.find(function (f) { return f[0] === activeKey; });
    if (!def || def[2] === null) return items;
    return items.filter(function (i) { return i.site_statut === def[2]; });
  }

  function renderFilterChips(containerId, items, filters, activeKey, onSelect) {
    document.getElementById(containerId).innerHTML = filters.map(function (f) {
      const count = f[2] === null ? items.length : items.filter(function (i) { return i.site_statut === f[2]; }).length;
      return '<button type="button" class="filter-chip' + (activeKey === f[0] ? " active" : "") + '" data-filter="' + f[0] + '">' + escapeHtml(f[1]) + '<span class="count">' + count + '</span></button>';
    }).join("");
    document.getElementById(containerId).querySelectorAll("[data-filter]").forEach(function (chip) {
      chip.addEventListener("click", function () { onSelect(chip.dataset.filter); });
    });
  }

  function renderArtisanView() {
    renderFilterChips("artisan-filters", state.artisanItems, ARTISAN_FILTERS, state.artisanFilter, function (key) {
      state.artisanFilter = key;
      renderArtisanView();
    });
    const table = document.getElementById("artisan-table");
    table.innerHTML = artisanRows(filterByStatut(state.artisanItems, ARTISAN_FILTERS, state.artisanFilter), false);
    bindRows(table);
  }

  function renderSiteView() {
    renderFilterChips("site-filters", state.siteItems, SITE_FILTERS, state.siteFilter, function (key) {
      state.siteFilter = key;
      renderSiteView();
    });
    const table = document.getElementById("site-table");
    table.innerHTML = artisanRows(filterByStatut(state.siteItems, SITE_FILTERS, state.siteFilter), true);
    bindRows(table);
  }

  async function loadArtisans(q) {
    showView("artisans", "Artisans");
    const data = await api("/admin/api/artisans?limit=100" + (q ? "&q=" + encodeURIComponent(q) : ""));
    state.artisanItems = data.items;
    document.getElementById("artisan-count").textContent = data.total + " compte" + (data.total > 1 ? "s" : "");
    renderArtisanView();
  }

  async function loadSites(q) {
    showView("sites", "Sites vitrines");
    const data = await api("/admin/api/sites?limit=100" + (q ? "&q=" + encodeURIComponent(q) : ""));
    state.siteItems = data.items;
    document.getElementById("site-count").textContent = data.total + " site" + (data.total > 1 ? "s" : "");
    renderSiteView();
  }

  function setForm(form, values) {
    Object.entries(values).forEach(function (entry) {
      if (form.elements[entry[0]]) form.elements[entry[0]].value = entry[1] == null ? "" : entry[1];
    });
  }

  function updateWorkflow(site) {
    // "pret" est atteignable depuis "brouillon" (site realise hors Suite
    // Artisan) ou depuis "genere" (etat historique, avant le retrait du
    // moteur) - jamais depuis "pret" ou "publie" eux-memes.
    document.getElementById("ready-button").disabled = site.statut !== "brouillon" && site.statut !== "genere";
    document.getElementById("publish-button").disabled = site.statut !== "pret";
    const badge = document.getElementById("detail-site-status");
    badge.className = "status-pill " + site.statut;
    badge.textContent = statusLabels[site.statut] || site.statut;
  }

  function hasMedia(site) {
    const profile = site.media_profile || {};
    return !!(profile.has_logo || profile.artisan_photo_count > 0);
  }

  // Le moteur de generation automatique a ete retire : aucune action ne doit
  // jamais appeler generate/preview/candidate. Le site peut desormais avoir
  // ete realise en dehors de Suite Artisan - l'Admin se contente d'enregistrer
  // son existence. Un site "brouillon" (nouveau) ou "genere" (etat historique)
  // peut donc etre marque pret des que son contenu est configure, sans etape
  // de generation intermediaire.
  function computeNextAction(artisan) {
    const site = artisan.site;
    if (site.statut === "pret") return { label: "Publier le site", run: function () { transition("publish", "Publication enregistrée").catch(handleError); } };
    if (!(site.config.services || []).length) return { label: "Configurer le site", run: function () { showTab("site"); } };
    if (site.statut === "brouillon" || site.statut === "genere") return { label: "Marquer prêt", run: function () { transition("ready", "Site marqué prêt à publier").catch(handleError); } };
    return null;
  }

  function renderPrimaryAction(artisan) {
    const nextAction = computeNextAction(artisan);
    const button = document.getElementById("detail-primary-action");
    if (!nextAction) { button.hidden = true; return; }
    button.hidden = false;
    button.textContent = nextAction.label;
    button.onclick = nextAction.run;
  }

  function renderProgressCard(artisan) {
    const site = artisan.site;
    const rows = [
      ["Identité", true, "Renseignée"],
      ["Médias", hasMedia(site), hasMedia(site) ? "Complétés" : "À compléter"],
      ["Publication", site.statut === "publie", site.statut === "publie" ? "Publié" : "Non publiée"],
    ];
    document.getElementById("progress-rows").innerHTML = rows.map(function (row) {
      return '<div class="progress-row ' + (row[1] ? "done" : "attention") + '"><span class="progress-row-label"><span class="progress-dot"></span>' +
        escapeHtml(row[0]) + '</span><span class="progress-row-status">' + escapeHtml(row[2]) + '</span></div>';
    }).join("");
    const nextAction = computeNextAction(artisan);
    document.getElementById("progress-hint").textContent = nextAction
      ? "Prochaine étape recommandée : " + nextAction.label + "."
      : "Le site est publié. Aucune action requise pour l'instant.";
  }

  function setStepBadge(id, ok, label) {
    const el = document.getElementById(id);
    el.className = "step-status-badge status-pill " + (ok ? "publie" : "brouillon");
    el.textContent = label;
    el.closest(".workflow-step").classList.toggle("done", ok);
  }

  function renderStepBadges(artisan) {
    const site = artisan.site;
    const media = artisan.media || { photos: [], max_photos: 0, logo: null };
    const contentOk = (site.config.services || []).length > 0;
    setStepBadge("step-contenu-badge", contentOk, contentOk ? "Configuré" : "À compléter");
    setStepBadge("step-medias-badge", hasMedia(site), hasMedia(site) ? "Complétés" : "À compléter");
    setStepBadge("step-publication-badge", site.statut === "publie", site.statut === "publie" ? "Publié" : "Non publiée");
    document.getElementById("media-summary-logo").textContent = media.logo ? "Défini" : "Non défini";
    document.getElementById("media-summary-photos").textContent = media.photos.length + " / " + media.max_photos;
  }

  function renderPublicationSummary(site) {
    document.getElementById("pub-statut").textContent = statusLabels[site.statut] || site.statut;
    document.getElementById("pub-domaine").textContent = site.domaine || "Non renseigné";
    document.getElementById("pub-url").textContent = site.url_publique || "Non renseignée";
    document.getElementById("pub-date").textContent = formatDate(site.date_publication);
  }

  async function openArtisan(id) {
    // Un rafraichissement apres une action (enregistrer, marquer pret...)
    // rouvre le meme artisan : ne jamais reinitialiser l'onglet actif dans ce
    // cas, sinon chaque action ramene l'utilisateur a "Vue d'ensemble" et lui
    // fait perdre le contexte de l'onglet ou il travaillait.
    const reopeningSameArtisan = state.currentView === "detail" && state.artisan && state.artisan.id === id;
    if (!reopeningSameArtisan) {
      state.previousView = state.currentView === "sites" ? "sites" : "artisans";
    }
    const artisan = await api("/admin/api/artisans/" + id);
    state.artisan = artisan;
    showView("detail", artisan.nom_entreprise);
    if (!reopeningSameArtisan) showTab("overview");

    document.getElementById("detail-title").textContent = artisan.nom_entreprise;
    document.getElementById("detail-meta").textContent = artisan.slug + " · " + artisan.email + " · inscrit le " + formatDate(artisan.created_at);
    document.getElementById("detail-plan-badge").textContent = PLAN_LABELS[artisan.plan] || artisan.plan;
    document.getElementById("detail-stats").innerHTML = [
      ["Plan", artisan.plan], ["Abonnement", artisan.subscription_status], ["Clients", artisan.clients_total], ["Documents commerciaux", artisan.devis_total + artisan.factures_total],
    ].map(function (item) { return `<div class="detail-stat"><span>${item[0]}</span><strong>${escapeHtml(item[1])}</strong></div>`; }).join("");
    setForm(document.getElementById("artisan-form"), artisan);

    const config = artisan.site.config || {};
    setForm(document.getElementById("site-form"), {
      tagline: config.tagline,
      services: (config.services || []).join("\n"),
      stats: (config.stats || []).map(function (item) { return item.valeur + " | " + item.label; }).join("\n"),
      domaine: artisan.site.domaine,
      url_publique: artisan.site.url_publique,
    });
    document.getElementById("site-slug").textContent = artisan.slug;
    document.getElementById("site-published-at").textContent = formatDate(artisan.site.date_publication);
    updateWorkflow(artisan.site);
    renderPublicationSummary(artisan.site);

    renderPrimaryAction(artisan);
    renderProgressCard(artisan);
    renderStepBadges(artisan);

    const warningBox = document.getElementById("site-content-warnings");
    warningBox.hidden = !(artisan.site.content_warnings || []).length;
    warningBox.textContent = (artisan.site.content_warnings || []).join(" ");
  }

  function artisanPayload() {
    const data = new FormData(document.getElementById("artisan-form"));
    return Object.fromEntries(Array.from(data.entries()).map(function (entry) { return [entry[0], entry[1].trim() || null]; }));
  }

  function sitePayload() {
    const form = document.getElementById("site-form");
    const data = new FormData(form);
    const services = String(data.get("services") || "").split("\n").map(function (item) { return item.trim(); }).filter(Boolean);
    const stats = String(data.get("stats") || "").split("\n").map(function (line) {
      const parts = line.split("|");
      return parts.length >= 2 ? { valeur: parts.shift().trim(), label: parts.join("|").trim() } : null;
    }).filter(Boolean);
    return {
      tagline: String(data.get("tagline") || "").trim() || null,
      services: services,
      stats: stats,
      domaine: String(data.get("domaine") || "").trim() || null,
      url_publique: String(data.get("url_publique") || "").trim() || null,
    };
  }

  async function saveArtisan() {
    await api("/admin/api/artisans/" + state.artisan.id, { method: "PATCH", body: JSON.stringify(artisanPayload()) });
    toast("Informations artisan enregistrées");
    await openArtisan(state.artisan.id);
  }

  async function saveSite() {
    await api("/admin/api/artisans/" + state.artisan.id + "/site", { method: "PATCH", body: JSON.stringify(sitePayload()) });
    toast("Contenu du site enregistré");
    await openArtisan(state.artisan.id);
  }

  async function transition(action, message) {
    if (action === "publish") await saveSite();
    await api("/admin/api/artisans/" + state.artisan.id + "/site/" + action, { method: "POST" });
    toast(message);
    await openArtisan(state.artisan.id);
  }

  document.querySelectorAll(".nav-item").forEach(function (item) {
    item.addEventListener("click", function () {
      if (item.dataset.view === "dashboard") loadDashboard().catch(handleError);
      if (item.dataset.view === "artisans") loadArtisans().catch(handleError);
      if (item.dataset.view === "sites") loadSites().catch(handleError);
    });
  });
  document.querySelectorAll(".tab-item").forEach(function (tab) {
    tab.addEventListener("click", function () { showTab(tab.dataset.tab); });
  });
  document.getElementById("detail-back").addEventListener("click", function () { (state.previousView === "sites" ? loadSites() : loadArtisans()).catch(handleError); });
  document.getElementById("artisan-form").addEventListener("submit", function (event) { event.preventDefault(); saveArtisan().catch(handleError); });
  document.getElementById("site-form").addEventListener("submit", function (event) { event.preventDefault(); saveSite().catch(handleError); });
  document.getElementById("ready-button").addEventListener("click", function () { transition("ready", "Site marqué prêt à publier").catch(handleError); });
  document.getElementById("publish-button").addEventListener("click", function () { transition("publish", "Publication enregistrée").catch(handleError); });
  document.getElementById("logout-button").addEventListener("click", async function () {
    await api("/admin/auth/logout", { method: "POST" });
    window.sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    window.location.assign("/admin/login.html");
  });

  function debounceSearch(input, loader) {
    let timer;
    input.addEventListener("input", function () { window.clearTimeout(timer); timer = window.setTimeout(function () { loader(input.value.trim()).catch(handleError); }, 220); });
  }
  debounceSearch(document.getElementById("artisan-search"), loadArtisans);
  debounceSearch(document.getElementById("site-search"), loadSites);

  function handleError(error) { toast(error.message || "Action impossible", true); }

  Promise.all([api("/admin/api/me"), loadDashboard()]).then(function (results) {
    document.getElementById("admin-name").textContent = results[0].nom;
  }).catch(handleError);
})();
