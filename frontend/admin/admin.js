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

  const state = { currentView: "dashboard", previousView: "artisans", artisan: null };
  const motifs = {
    plombier: ["wave-gradient", "gradient-mesh"],
    electricien: ["diagonal-stripes", "dot-grid"],
    macon: ["brick-rows", "dot-grid"],
    peintre: ["gradient-mesh", "wave-gradient"],
    general: ["wave-gradient", "gradient-mesh"],
  };
  const statusLabels = { non_cree: "Non créé", brouillon: "Brouillon", genere: "Généré", pret: "Prêt", publie: "Publié" };

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
  }

  async function loadDashboard() {
    showView("dashboard", "Dashboard");
    const data = await api("/admin/api/dashboard");
    const metrics = [
      ["Artisans", data.artisans_total], ["Artisans actifs", data.artisans_actifs],
      ["Sites vitrines", data.sites_total], ["Sites publiés", data.sites_publies],
    ];
    document.getElementById("metric-grid").innerHTML = metrics.map(function (item) {
      return `<article class="metric"><span>${item[0]}</span><strong>${item[1]}</strong></article>`;
    }).join("");
    const maxPlan = Math.max(1, ...Object.values(data.plans));
    const labels = { gratuit: "Gratuit", essentiel: "Essentiel", pro: "Pro", business: "Business" };
    document.getElementById("plan-breakdown").innerHTML = Object.entries(data.plans).map(function (entry) {
      return `<div class="breakdown-row"><span>${labels[entry[0]] || entry[0]}</span><div class="bar"><i style="width:${entry[1] / maxPlan * 100}%"></i></div><strong>${entry[1]}</strong></div>`;
    }).join("");
    const pipeline = [["Brouillons", data.sites_brouillon], ["Générés", data.sites_generes], ["Prêts", data.sites_prets], ["Publiés", data.sites_publies]];
    document.getElementById("site-pipeline").innerHTML = pipeline.map(function (entry) {
      return `<div class="breakdown-row"><span>${entry[0]}</span><div class="bar"><i style="width:${data.sites_total ? entry[1] / data.sites_total * 100 : 0}%"></i></div><strong>${entry[1]}</strong></div>`;
    }).join("");
  }

  function artisanRows(items, sitesMode) {
    if (!items.length) return `<tr><td colspan="7" class="muted">Aucun résultat</td></tr>`;
    return items.map(function (item) {
      if (sitesMode) {
        return `<tr data-id="${item.id}"><td><div class="cell-title">${escapeHtml(item.nom_entreprise)}</div><div class="cell-sub">${escapeHtml(item.slug)}</div></td><td>${escapeHtml(item.metier)}</td><td>${pill(item.site_statut)}</td><td>${escapeHtml(item.domaine || "-")}</td><td>${escapeHtml(item.url_publique || "-")}</td><td>${formatDate(item.created_at)}</td></tr>`;
      }
      return `<tr data-id="${item.id}"><td><div class="cell-title">${escapeHtml(item.nom_entreprise)}</div><div class="cell-sub">${escapeHtml(item.email)}</div></td><td>${escapeHtml(item.metier)}</td><td>${escapeHtml(item.ville || "-")}</td><td>${escapeHtml(item.plan)}</td><td>${pill(item.subscription_status)}</td><td>${pill(item.site_statut)}</td><td>${formatDate(item.created_at)}</td></tr>`;
    }).join("");
  }

  function bindRows(table) {
    table.querySelectorAll("tr[data-id]").forEach(function (row) {
      row.addEventListener("click", function () { openArtisan(Number(row.dataset.id)); });
    });
  }

  async function loadArtisans(q) {
    showView("artisans", "Artisans");
    const data = await api("/admin/api/artisans" + (q ? "?q=" + encodeURIComponent(q) : ""));
    document.getElementById("artisan-count").textContent = data.total + " compte" + (data.total > 1 ? "s" : "");
    const table = document.getElementById("artisan-table");
    table.innerHTML = artisanRows(data.items, false);
    bindRows(table);
  }

  async function loadSites(q) {
    showView("sites", "Sites vitrines");
    const data = await api("/admin/api/sites" + (q ? "?q=" + encodeURIComponent(q) : ""));
    document.getElementById("site-count").textContent = data.total + " site" + (data.total > 1 ? "s" : "");
    const table = document.getElementById("site-table");
    table.innerHTML = artisanRows(data.items, true);
    bindRows(table);
  }

  function setForm(form, values) {
    Object.entries(values).forEach(function (entry) {
      if (form.elements[entry[0]]) form.elements[entry[0]].value = entry[1] == null ? "" : entry[1];
    });
  }

  function updateMotifs(metier, selected) {
    const select = document.getElementById("motif-select");
    select.innerHTML = `<option value="">Automatique</option>` + (motifs[metier] || motifs.general).map(function (motif) {
      return `<option value="${motif}">${motif}</option>`;
    }).join("");
    select.value = selected || "";
  }

  function updateWorkflow(site) {
    document.getElementById("preview-button").disabled = !site.preview_disponible;
    document.getElementById("ready-button").disabled = site.statut !== "genere";
    document.getElementById("publish-button").disabled = site.statut !== "pret";
    const badge = document.getElementById("detail-site-status");
    badge.className = "status-pill " + site.statut;
    badge.textContent = statusLabels[site.statut] || site.statut;
  }

  async function openArtisan(id) {
    state.previousView = state.currentView === "sites" ? "sites" : "artisans";
    const artisan = await api("/admin/api/artisans/" + id);
    state.artisan = artisan;
    showView("detail", artisan.nom_entreprise);
    document.getElementById("detail-title").textContent = artisan.nom_entreprise;
    document.getElementById("detail-meta").textContent = artisan.slug + " · " + artisan.email + " · inscrit le " + formatDate(artisan.created_at);
    document.getElementById("detail-stats").innerHTML = [
      ["Plan", artisan.plan], ["Abonnement", artisan.subscription_status], ["Clients", artisan.clients_total], ["Documents commerciaux", artisan.devis_total + artisan.factures_total],
    ].map(function (item) { return `<div class="detail-stat"><span>${item[0]}</span><strong>${escapeHtml(item[1])}</strong></div>`; }).join("");
    setForm(document.getElementById("artisan-form"), artisan);
    const config = artisan.site.config || {};
    setForm(document.getElementById("site-form"), {
      tagline: config.tagline,
      services: (config.services || []).join("\n"),
      stats: (config.stats || []).map(function (item) { return item.valeur + " | " + item.label; }).join("\n"),
      variante_couleur: config.variante_couleur,
      domaine: artisan.site.domaine,
      url_publique: artisan.site.url_publique,
    });
    updateMotifs(artisan.metier, config.variante_motif);
    const designProfile = artisan.site.design_profile;
    const designProfileEl = document.getElementById("site-design-profile");
    if (designProfile) {
      designProfileEl.hidden = false;
      designProfileEl.textContent = "Profil de design (V2) : " + [
        designProfile.design_family, designProfile.hero_variant, designProfile.services_variant,
        designProfile.gallery_variant, designProfile.palette,
      ].join(" · ");
    } else {
      designProfileEl.hidden = true;
    }
    document.getElementById("site-slug").textContent = artisan.slug;
    document.getElementById("site-generated-at").textContent = formatDate(artisan.site.date_generation);
    document.getElementById("site-published-at").textContent = formatDate(artisan.site.date_publication);
    updateWorkflow(artisan.site);
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
      variante_couleur: data.get("variante_couleur") === "" ? null : Number(data.get("variante_couleur")),
      variante_motif: data.get("variante_motif") || null,
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
    toast("Configuration du site enregistrée");
    await openArtisan(state.artisan.id);
  }

  async function generate() {
    const nextSite = sitePayload();
    await api("/admin/api/artisans/" + state.artisan.id, { method: "PATCH", body: JSON.stringify(artisanPayload()) });
    await api("/admin/api/artisans/" + state.artisan.id + "/site", { method: "PATCH", body: JSON.stringify(nextSite) });
    await api("/admin/api/artisans/" + state.artisan.id + "/site/generate", { method: "POST" });
    toast("Preview générée");
    await openArtisan(state.artisan.id);
  }

  async function transition(action, message) {
    if (action === "publish") await saveSite();
    await api("/admin/api/artisans/" + state.artisan.id + "/site/" + action, { method: "POST" });
    toast(message);
    await openArtisan(state.artisan.id);
  }

  async function openPreview() {
    const previewWindow = window.open("about:blank", "_blank");
    if (!previewWindow) throw new Error("Autorisez l'ouverture de fenêtres pour afficher la preview");
    previewWindow.opener = null;
    try {
      const session = await api("/admin/api/artisans/" + state.artisan.id + "/site/preview-session", { method: "POST" });
      previewWindow.location.replace(apiUrl(session.url));
    } catch (error) {
      previewWindow.close();
      throw error;
    }
  }

  document.querySelectorAll(".nav-item").forEach(function (item) {
    item.addEventListener("click", function () {
      if (item.dataset.view === "dashboard") loadDashboard().catch(handleError);
      if (item.dataset.view === "artisans") loadArtisans().catch(handleError);
      if (item.dataset.view === "sites") loadSites().catch(handleError);
    });
  });
  document.getElementById("detail-back").addEventListener("click", function () { (state.previousView === "sites" ? loadSites() : loadArtisans()).catch(handleError); });
  document.getElementById("artisan-form").addEventListener("submit", function (event) { event.preventDefault(); saveArtisan().catch(handleError); });
  document.getElementById("site-form").addEventListener("submit", function (event) { event.preventDefault(); saveSite().catch(handleError); });
  document.getElementById("generate-button").addEventListener("click", function () { generate().catch(handleError); });
  document.getElementById("preview-button").addEventListener("click", function () { openPreview().catch(handleError); });
  document.getElementById("ready-button").addEventListener("click", function () { transition("ready", "Site marqué prêt à publier").catch(handleError); });
  document.getElementById("publish-button").addEventListener("click", function () { transition("publish", "Publication enregistrée").catch(handleError); });
  document.getElementById("artisan-form").elements.metier.addEventListener("change", function (event) { updateMotifs(event.target.value, ""); });
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
