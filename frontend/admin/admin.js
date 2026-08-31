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

  const state = { currentView: "dashboard", previousView: "artisans", artisan: null, mediaObjectUrls: [] };
  const motifs = {
    plombier: ["wave-gradient", "gradient-mesh"],
    electricien: ["diagonal-stripes", "dot-grid"],
    macon: ["brick-rows", "dot-grid"],
    peintre: ["gradient-mesh", "wave-gradient"],
    general: ["wave-gradient", "gradient-mesh"],
  };
  const statusLabels = { non_cree: "Non créé", brouillon: "Brouillon", genere: "Généré", pret: "Prêt", publie: "Publié" };

  // ---------- Configurateur de design V2 (Lot 4) ----------
  // Ce vocabulaire reflete generator/design_registry.py (source de verite).
  // Le backend revalide integralement chaque valeur ; ces listes ne servent
  // qu'a construire des controles lisibles, jamais a la validation.
  const FAMILY_LABELS = { atelier: "Atelier", architecture: "Architecture", impact: "Impact", technique: "Technique", local: "Local", signature: "Signature" };
  const FAMILY_DESCRIPTIONS = {
    atelier: "Chaleureux et artisanal : met en valeur le savoir-faire.",
    architecture: "Premium, minimal et éditorial : très épuré.",
    impact: "Fort et dynamique : met en avant l'action (devis, contact).",
    technique: "Structuré et précis : clarté et expertise.",
    local: "Proximité et confiance : ancrage dans le territoire.",
    signature: "Haut de gamme et photographique : très visuel.",
  };
  const HEADER_VARIANTS = ["classic", "minimal", "centered", "compact"];
  const HERO_VARIANTS = ["fullscreen", "split", "asymmetric", "compact", "editorial", "card"];
  const SERVICES_VARIANTS = ["cards", "editorial", "list", "grid", "alternating"];
  const GALLERY_VARIANTS = ["grid", "masonry", "featured", "horizontal"];
  const ABOUT_VARIANTS = ["classic", "editorial", "split", "compact"];
  const REVIEWS_VARIANTS = ["cards", "featured", "minimal"];
  const CTA_VARIANTS = ["banner", "floating", "split", "minimal"];
  const FOOTER_VARIANTS = ["simple", "columns", "centered", "map"];
  const RADIUS_STYLES = ["sharp", "soft", "rounded", "pill"];
  const SPACING_STYLES = ["compact", "comfortable", "spacious"];
  const IMAGE_TREATMENTS = ["flat", "duotone", "framed", "overlay"];
  const PALETTE_SLOTS = ["palette-1", "palette-2", "palette-3"];
  const FONT_PAIR_IDS = ["poppins-inter", "archivo-inter", "fredoka-inter", "rajdhani-inter"];
  const VARIANT_LABELS = {
    header_variant: { classic: "Classique", minimal: "Minimaliste", centered: "Centré", compact: "Compact" },
    hero_variant: { fullscreen: "Plein écran", split: "Divisé", asymmetric: "Asymétrique", compact: "Compact", editorial: "Éditorial", card: "Carte" },
    services_variant: { cards: "Cartes", editorial: "Éditorial", list: "Liste", grid: "Grille", alternating: "Alterné" },
    gallery_variant: { grid: "Grille", masonry: "Mosaïque", featured: "Mise en avant", horizontal: "Horizontal" },
    about_variant: { classic: "Classique", editorial: "Éditorial", split: "Divisé", compact: "Compact" },
    reviews_variant: { cards: "Cartes", featured: "Mise en avant", minimal: "Minimaliste" },
    cta_variant: { banner: "Bandeau", floating: "Flottant", split: "Divisé", minimal: "Minimaliste" },
    footer_variant: { simple: "Simple", columns: "Colonnes", centered: "Centré", map: "Carte" },
  };
  const RADIUS_LABELS = { sharp: "Angles nets", soft: "Légèrement arrondi", rounded: "Arrondi", pill: "Très arrondi" };
  const SPACING_LABELS = { compact: "Compact", comfortable: "Confortable", spacious: "Aéré" };
  const IMAGE_TREATMENT_LABELS = { flat: "Naturelle", duotone: "Bicolore", framed: "Encadrée", overlay: "Dégradé" };
  const FONT_PAIR_LABELS = {
    "poppins-inter": "Moderne et arrondie",
    "archivo-inter": "Neutre et structurée",
    "fredoka-inter": "Ludique et chaleureuse",
    "rajdhani-inter": "Technique et anguleuse",
  };
  const PALETTE_LABELS = { "palette-1": "Palette 1", "palette-2": "Palette 2", "palette-3": "Palette 3" };
  const SECTION_LABELS = {
    hero: "Introduction", trust: "Confiance", services: "Prestations", featured_project: "Réalisation phare",
    about: "À propos", gallery: "Galerie photo", reviews: "Avis clients", service_area: "Zone d'intervention",
    cta: "Appel à l'action", stats: "Chiffres clés", process: "Déroulé", before_after: "Avant / après",
    reasons: "Pourquoi nous choisir", contact: "Formulaire de contact",
  };
  const DESIGN_AXES = [
    ["design_family", "Famille"], ["header_variant", "En-tête"], ["hero_variant", "Bloc d'accueil"],
    ["services_variant", "Prestations"], ["gallery_variant", "Galerie"], ["about_variant", "À propos"],
    ["reviews_variant", "Avis"], ["cta_variant", "Appel à l'action"], ["footer_variant", "Pied de page"],
    ["palette", "Palette"], ["font_pair", "Typographie"], ["radius_style", "Arrondis"],
    ["spacing_style", "Espacement"], ["image_treatment", "Traitement des images"],
  ];
  const ADVANCED_AXES = [
    ["header_variant", "En-tête", HEADER_VARIANTS], ["hero_variant", "Bloc d'accueil", HERO_VARIANTS],
    ["services_variant", "Prestations", SERVICES_VARIANTS], ["gallery_variant", "Galerie", GALLERY_VARIANTS],
    ["about_variant", "À propos", ABOUT_VARIANTS], ["reviews_variant", "Avis", REVIEWS_VARIANTS],
    ["cta_variant", "Appel à l'action", CTA_VARIANTS], ["footer_variant", "Pied de page", FOOTER_VARIANTS],
    ["radius_style", "Arrondis", RADIUS_STYLES], ["spacing_style", "Espacement", SPACING_STYLES],
  ];

  function axisValueLabel(axis, value) {
    if (!value) return "-";
    if (axis === "design_family") return FAMILY_LABELS[value] || value;
    if (axis === "palette") return PALETTE_LABELS[value] || value;
    if (axis === "font_pair") return FONT_PAIR_LABELS[value] || value;
    if (axis === "radius_style") return RADIUS_LABELS[value] || value;
    if (axis === "spacing_style") return SPACING_LABELS[value] || value;
    if (axis === "image_treatment") return IMAGE_TREATMENT_LABELS[value] || value;
    if (VARIANT_LABELS[axis] && VARIANT_LABELS[axis][value]) return VARIANT_LABELS[axis][value];
    return value;
  }

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

  async function apiUpload(path, formData) {
    const token = window.sessionStorage.getItem(ADMIN_TOKEN_KEY);
    const response = await fetch(apiUrl(path), {
      method: "POST",
      headers: token ? { Authorization: "Bearer " + token } : {},
      body: formData,
    });
    let data = null;
    try { data = await response.json(); } catch (err) { data = null; }
    if (!response.ok) throw new Error(data && data.detail ? data.detail : "Import impossible");
    return data;
  }

  async function protectedImageUrl(path) {
    const token = window.sessionStorage.getItem(ADMIN_TOKEN_KEY);
    const response = await fetch(apiUrl(path), { headers: token ? { Authorization: "Bearer " + token } : {} });
    if (!response.ok) throw new Error("Image protégée indisponible");
    return URL.createObjectURL(await response.blob());
  }

  function clearMediaObjectUrls() {
    state.mediaObjectUrls.splice(0).forEach(function (url) { URL.revokeObjectURL(url); });
  }

  async function hydrateAdminMediaImages() {
    const images = Array.from(document.querySelectorAll("#admin-media-section img[data-media-url]"));
    await Promise.all(images.map(async function (image) {
      const url = await protectedImageUrl(image.dataset.mediaUrl);
      state.mediaObjectUrls.push(url);
      image.src = url;
    }));
  }

  async function renderAdminMedia(media) {
    clearMediaObjectUrls();
    document.getElementById("admin-media-count").textContent = media.photos.length + " / " + media.max_photos + " photos";
    document.getElementById("admin-logo-preview").innerHTML = media.logo
      ? `<img data-media-url="${escapeHtml(media.logo.thumbnail_url)}" alt="Logo artisan">`
      : '<span class="muted">Aucun logo</span>';
    document.getElementById("admin-logo-delete").hidden = !media.logo;
    document.getElementById("admin-media-photos").innerHTML = media.photos.length ? media.photos.map(function (photo) {
      return `<article class="admin-media-item"><img data-media-url="${escapeHtml(photo.thumbnail_url)}" alt="${escapeHtml(photo.alt_text || photo.nom_original)}"><div><strong>${escapeHtml(photo.nom_original)}</strong><span>${escapeHtml(photo.categorie || "autre")} · ${photo.actif ? "active" : "inactive"} · source artisan</span></div></article>`;
    }).join("") : '<p class="muted">Aucune photo artisan.</p>';
    const selections = media.profile.selections || [];
    document.getElementById("admin-media-selections").innerHTML = selections.length ? selections.map(function (selection) {
      const preview = selection.thumbnail_url ? `<img data-media-url="${escapeHtml(selection.thumbnail_url)}" alt="">` : '<span class="selection-fallback">Sans photo</span>';
      return `<article class="admin-selection-item" data-selection-id="${selection.id}">${preview}<div><strong>${escapeHtml(selection.usage)}${selection.position ? " " + (selection.position + 1) : ""}</strong><span>${escapeHtml(selection.source)}${selection.credit ? " · " + escapeHtml(selection.credit) : ""}</span></div><button class="button button-secondary" data-action="remove-selection" type="button">Retirer</button></article>`;
    }).join("") : '<p class="muted">La sélection sera créée à la première génération.</p>';
    await hydrateAdminMediaImages();
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

  function renderDesignCurrent(site) {
    const el = document.getElementById("design-current");
    const profile = site.design_profile;
    if (!profile) {
      el.innerHTML = '<p class="design-empty">Aucun design généré pour l’instant. Cliquez sur « Générer la preview » ci-dessus.</p>';
      return;
    }
    const rows = DESIGN_AXES.filter(function (entry) { return entry[0] !== "design_family"; }).map(function (entry) {
      return '<div><dt>' + escapeHtml(entry[1]) + '</dt><dd>' + escapeHtml(axisValueLabel(entry[0], profile[entry[0]])) + '</dd></div>';
    }).join("");
    el.innerHTML = '<div class="design-current-card"><div class="design-current-family">' +
      '<span class="design-family-badge">' + escapeHtml(FAMILY_LABELS[profile.design_family] || profile.design_family) + '</span>' +
      '<p>' + escapeHtml(FAMILY_DESCRIPTIONS[profile.design_family] || "") + '</p></div>' +
      '<dl class="design-current-grid">' + rows + '</dl>' +
      '<details class="design-technical"><summary>Détails techniques</summary><code>' + escapeHtml(profile.design_signature || "") + '</code></details></div>';
  }

  function renderSectionsAvailability(list) {
    const el = document.getElementById("design-sections-availability");
    if (!list || !list.length) { el.innerHTML = ""; return; }
    el.innerHTML = '<h4>Sections qui pourront apparaître</h4><ul class="design-sections-list">' + list.map(function (item) {
      const label = SECTION_LABELS[item.section] || item.section;
      const reason = !item.disponible ? (item.raison || "Cette section n'apparaît pas car aucune donnée n'est disponible.") : "";
      return '<li class="' + (item.disponible ? "available" : "unavailable") + '"><span>' + (item.disponible ? "✓ " : "– ") + escapeHtml(label) + '</span>' +
        (reason ? '<small>' + escapeHtml(reason) + '</small>' : "") + '</li>';
    }).join("") + '</ul>';
  }

  function renderFamilyCards(selected) {
    document.getElementById("design-family-cards").innerHTML = Object.keys(FAMILY_LABELS).map(function (fam) {
      return '<button type="button" class="design-family-card' + (fam === selected ? " selected" : "") + '" data-family="' + fam + '">' +
        '<strong>' + escapeHtml(FAMILY_LABELS[fam]) + '</strong><span>' + escapeHtml(FAMILY_DESCRIPTIONS[fam]) + '</span></button>';
    }).join("");
  }

  function buildAdvancedPanel() {
    const grid = ADVANCED_AXES.map(function (entry) {
      const axis = entry[0], label = entry[1], options = entry[2];
      const opts = options.map(function (opt) { return '<option value="' + opt + '">' + escapeHtml(axisValueLabel(axis, opt)) + '</option>'; }).join("");
      return '<label>' + escapeHtml(label) + '<select data-override="' + axis + '"><option value="">Automatique</option>' + opts + '</select></label>';
    }).join("");
    const palettes = '<div class="override-group" data-override="palette"><span>Palette</span><div class="palette-swatches">' +
      '<button type="button" class="palette-swatch auto selected" data-value="">Auto</button>' +
      PALETTE_SLOTS.map(function (p, i) { return '<button type="button" class="palette-swatch swatch-' + (i + 1) + '" data-value="' + p + '" aria-label="' + escapeHtml(PALETTE_LABELS[p]) + '" title="' + escapeHtml(PALETTE_LABELS[p]) + '"></button>'; }).join("") +
      '</div></div>';
    const fonts = '<div class="override-group" data-override="font_pair"><span>Typographie</span><div class="font-options">' +
      '<button type="button" class="font-option selected" data-value="">Automatique</button>' +
      FONT_PAIR_IDS.map(function (id) { return '<button type="button" class="font-option" data-value="' + id + '">' + escapeHtml(FONT_PAIR_LABELS[id]) + '</button>'; }).join("") +
      '</div></div>';
    const images = '<div class="override-group" data-override="image_treatment"><span>Traitement des images</span><div class="image-treatment-options">' +
      '<button type="button" class="image-treatment-option selected" data-value="">Automatique</button>' +
      IMAGE_TREATMENTS.map(function (t) { return '<button type="button" class="image-treatment-option treatment-' + t + '" data-value="' + t + '">' + escapeHtml(IMAGE_TREATMENT_LABELS[t]) + '</button>'; }).join("") +
      '</div></div>';
    document.getElementById("advanced-panel").innerHTML = '<div class="form-grid">' + grid + '</div>' + palettes + fonts + images +
      '<div class="section-order-editor" id="section-order-editor"><span>Ordre des sections</span></div>';
  }

  function paintSectionOrderEditor() {
    const el = document.getElementById("section-order-editor");
    if (!el) return;
    const order = state.sectionOrderDraft || [];
    el.innerHTML = '<span>Ordre des sections</span><ol class="section-order-list">' + order.map(function (section, index) {
      const label = escapeHtml(SECTION_LABELS[section] || section);
      return '<li><span>' + label + '</span><span>' +
        '<button type="button" class="button button-secondary" data-move="up" data-index="' + index + '" aria-label="Monter ' + label + '"' + (index === 0 ? " disabled" : "") + '>↑</button> ' +
        '<button type="button" class="button button-secondary" data-move="down" data-index="' + index + '" aria-label="Descendre ' + label + '"' + (index === order.length - 1 ? " disabled" : "") + '>↓</button></span></li>';
    }).join("") + '</ol>';
  }

  function resetAdvancedPanelSelections() {
    document.querySelectorAll('#advanced-panel select[data-override]').forEach(function (select) { select.value = ""; });
    document.querySelectorAll('#advanced-panel .override-group [data-value]').forEach(function (btn) { btn.classList.toggle("selected", btn.dataset.value === ""); });
    state.overrideChoices = {};
  }

  function gatherOverrides() {
    const overrides = {};
    document.querySelectorAll('#advanced-panel select[data-override]').forEach(function (select) {
      if (select.value) overrides[select.dataset.override] = select.value;
    });
    Object.entries(state.overrideChoices || {}).forEach(function (entry) {
      if (entry[1]) overrides[entry[0]] = entry[1];
    });
    if (state.sectionOrderDraft && state.originalSectionOrder && JSON.stringify(state.sectionOrderDraft) !== JSON.stringify(state.originalSectionOrder)) {
      overrides.section_order = state.sectionOrderDraft;
    }
    return Object.keys(overrides).length ? overrides : null;
  }

  function updateCandidateButtons(site) {
    const hasCandidate = !!site.candidate_design_profile;
    document.getElementById("candidate-generate-button").disabled = !site.design_profile;
    document.getElementById("candidate-regenerate-button").disabled = !hasCandidate;
    document.getElementById("candidate-adopt-button").disabled = !hasCandidate;
    document.getElementById("candidate-abandon-button").disabled = !hasCandidate;
    document.getElementById("candidate-preview-button").disabled = !site.candidate_preview_disponible;
  }

  function renderDesignComparison(site) {
    const el = document.getElementById("design-comparison");
    const current = site.design_profile;
    const candidate = site.candidate_design_profile;
    if (!candidate) { el.hidden = true; el.innerHTML = ""; return; }
    el.hidden = false;
    const diffAxes = DESIGN_AXES.filter(function (entry) { return !current || current[entry[0]] !== candidate[entry[0]]; });
    const currentRows = diffAxes.map(function (entry) { return '<div><dt>' + escapeHtml(entry[1]) + '</dt><dd>' + escapeHtml(axisValueLabel(entry[0], current ? current[entry[0]] : null)) + '</dd></div>'; }).join("");
    const candidateRows = diffAxes.map(function (entry) { return '<div><dt>' + escapeHtml(entry[1]) + '</dt><dd>' + escapeHtml(axisValueLabel(entry[0], candidate[entry[0]])) + '</dd></div>'; }).join("");
    el.innerHTML = '<h4>Version actuelle vs alternative</h4><div class="design-comparison-grid">' +
      '<div class="design-comparison-card current"><span class="design-comparison-tag">Version actuelle</span>' + currentRows + '</div>' +
      '<div class="design-comparison-card candidate"><span class="design-comparison-tag">Alternative</span>' + candidateRows + '</div></div>' +
      (diffAxes.length ? "" : '<p class="muted">Cette alternative est très proche du design actuel sur les axes affichés.</p>');
  }

  function candidatePayload() {
    const keepFamily = document.getElementById("candidate-keep-family").checked;
    const familySelect = document.getElementById("pref-family").value;
    const density = document.getElementById("pref-density").value;
    return {
      keep_current_family: keepFamily,
      preferred_family: keepFamily ? null : (familySelect || null),
      density: density || null,
      overrides: gatherOverrides(),
    };
  }

  async function generateCandidate(regenerate) {
    const genBtn = document.getElementById("candidate-generate-button");
    const regenBtn = document.getElementById("candidate-regenerate-button");
    genBtn.disabled = true;
    regenBtn.disabled = true;
    try {
      const path = "/admin/api/artisans/" + state.artisan.id + "/site/design/candidate" + (regenerate ? "/regenerate" : "");
      const result = await api(path, { method: "POST", body: JSON.stringify(candidatePayload()) });
      toast(result.distinct ? "Alternative générée : structure bien distincte du design actuel" : "Alternative générée (proche du design actuel malgré les réglages)");
      await openArtisan(state.artisan.id);
    } catch (error) {
      genBtn.disabled = false;
      regenBtn.disabled = state.artisan && state.artisan.site && !state.artisan.site.candidate_design_profile;
      throw error;
    }
  }

  async function savePreferences() {
    const payload = {
      preferred_family: document.getElementById("pref-family").value || null,
      density: document.getElementById("pref-density").value || null,
    };
    await api("/admin/api/artisans/" + state.artisan.id + "/site/design/preferences", { method: "PATCH", body: JSON.stringify(payload) });
    toast("Orientation enregistrée pour la prochaine alternative");
    await openArtisan(state.artisan.id);
  }

  async function abandonCandidate() {
    if (!window.confirm("Abandonner cette alternative ? Elle sera définitivement supprimée. Le design actuel du site n'est pas concerné.")) return;
    await api("/admin/api/artisans/" + state.artisan.id + "/site/design/candidate", { method: "DELETE" });
    toast("Alternative abandonnée");
    await openArtisan(state.artisan.id);
  }

  async function adoptCandidate() {
    if (!window.confirm("Adopter cette alternative comme nouveau design du site ? Le site publié n'est jamais modifié automatiquement : vous devrez le republier explicitement si besoin.")) return;
    await api("/admin/api/artisans/" + state.artisan.id + "/site/design/candidate/adopt", { method: "POST" });
    toast("Nouveau design adopté — pensez à vérifier le statut du site avant de le republier");
    await openArtisan(state.artisan.id);
  }

  async function previewCandidate() {
    const previewWindow = window.open("about:blank", "_blank");
    if (!previewWindow) throw new Error("Autorisez l'ouverture de fenêtres pour afficher la preview");
    previewWindow.opener = null;
    try {
      const session = await api("/admin/api/artisans/" + state.artisan.id + "/site/preview-session/candidate", { method: "POST" });
      previewWindow.location.replace(apiUrl(session.url));
    } catch (error) {
      previewWindow.close();
      throw error;
    }
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
    document.getElementById("site-slug").textContent = artisan.slug;
    document.getElementById("site-generated-at").textContent = formatDate(artisan.site.date_generation);
    document.getElementById("site-published-at").textContent = formatDate(artisan.site.date_publication);
    updateWorkflow(artisan.site);

    const preferredFamily = (artisan.site.design_preferences && artisan.site.design_preferences.preferred_family) || "";
    renderDesignCurrent(artisan.site);
    renderSectionsAvailability(artisan.site.sections_disponibles);
    renderFamilyCards(preferredFamily);
    document.getElementById("pref-family").value = preferredFamily;
    document.getElementById("pref-density").value = (artisan.site.design_preferences && artisan.site.design_preferences.density) || "";
    document.getElementById("candidate-keep-family").checked = false;
    state.originalSectionOrder = (artisan.site.design_profile && artisan.site.design_profile.section_order) || [];
    state.sectionOrderDraft = state.originalSectionOrder.slice();
    paintSectionOrderEditor();
    resetAdvancedPanelSelections();
    updateCandidateButtons(artisan.site);
    renderDesignComparison(artisan.site);

    await renderAdminMedia(artisan.media);
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
  document.getElementById("admin-logo-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
      await apiUpload("/admin/api/artisans/" + state.artisan.id + "/site/media/logo", new FormData(event.target));
      event.target.reset();
      toast("Logo artisan enregistré");
      await openArtisan(state.artisan.id);
    } catch (error) { handleError(error); }
  });
  document.getElementById("admin-logo-delete").addEventListener("click", async function () {
    try {
      await api("/admin/api/artisans/" + state.artisan.id + "/site/media/logo", { method: "DELETE" });
      toast("Logo artisan supprimé");
      await openArtisan(state.artisan.id);
    } catch (error) { handleError(error); }
  });
  document.getElementById("admin-media-selections").addEventListener("click", async function (event) {
    const button = event.target.closest('[data-action="remove-selection"]');
    const item = event.target.closest("[data-selection-id]");
    if (!button || !item) return;
    try {
      await api("/admin/api/artisans/" + state.artisan.id + "/site/media/selections/" + item.dataset.selectionId, { method: "DELETE" });
      toast("Image retirée de la sélection");
      await openArtisan(state.artisan.id);
    } catch (error) { handleError(error); }
  });
  document.getElementById("artisan-form").elements.metier.addEventListener("change", function (event) { updateMotifs(event.target.value, ""); });
  document.getElementById("logout-button").addEventListener("click", async function () {
    await api("/admin/auth/logout", { method: "POST" });
    window.sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    window.location.assign("/admin/login.html");
  });

  buildAdvancedPanel();
  document.getElementById("advanced-toggle").addEventListener("click", function () {
    const panel = document.getElementById("advanced-panel");
    const expanded = !panel.hidden;
    panel.hidden = expanded;
    this.setAttribute("aria-expanded", String(!expanded));
  });
  document.getElementById("design-family-cards").addEventListener("click", function (event) {
    const card = event.target.closest(".design-family-card");
    if (!card) return;
    document.getElementById("pref-family").value = card.dataset.family;
    renderFamilyCards(card.dataset.family);
  });
  document.getElementById("advanced-panel").addEventListener("click", function (event) {
    const moveButton = event.target.closest("[data-move]");
    if (moveButton) {
      const index = Number(moveButton.dataset.index);
      const swapIndex = index + (moveButton.dataset.move === "up" ? -1 : 1);
      const order = state.sectionOrderDraft;
      if (!order || swapIndex < 0 || swapIndex >= order.length) return;
      const tmp = order[index];
      order[index] = order[swapIndex];
      order[swapIndex] = tmp;
      paintSectionOrderEditor();
      return;
    }
    const choiceButton = event.target.closest(".override-group [data-value]");
    if (!choiceButton) return;
    const group = choiceButton.closest(".override-group");
    state.overrideChoices = state.overrideChoices || {};
    state.overrideChoices[group.dataset.override] = choiceButton.dataset.value || null;
    group.querySelectorAll("[data-value]").forEach(function (el) { el.classList.toggle("selected", el === choiceButton); });
  });
  document.getElementById("save-preferences-button").addEventListener("click", function () { savePreferences().catch(handleError); });
  document.getElementById("candidate-generate-button").addEventListener("click", function () { generateCandidate(false).catch(handleError); });
  document.getElementById("candidate-regenerate-button").addEventListener("click", function () { generateCandidate(true).catch(handleError); });
  document.getElementById("candidate-abandon-button").addEventListener("click", function () { abandonCandidate().catch(handleError); });
  document.getElementById("candidate-adopt-button").addEventListener("click", function () { adoptCandidate().catch(handleError); });
  document.getElementById("candidate-preview-button").addEventListener("click", function () { previewCandidate().catch(handleError); });

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
