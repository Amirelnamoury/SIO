// Adresse du backend Suite Artisan. A changer une fois l'API deployee en prod.
const API_BASE = "http://localhost:8000";

const TOKEN_KEY = "suite_artisan_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Met en forme les erreurs renvoyees par FastAPI (422 = erreurs de
 * validation Pydantic, sous forme de liste) en un message lisible.
 */
function formatApiError(data) {
  if (!data) return "Une erreur est survenue.";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.msg || JSON.stringify(e)).join(" ");
  }
  return "Une erreur est survenue.";
}

/**
 * Appelle le backend. Ajoute automatiquement le token JWT si present.
 * Ne stocke JAMAIS les donnees metier (devis, chantiers...) en local :
 * chaque appel va chercher les donnees fraiches sur le serveur.
 */
async function apiFetch(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
  }

  let response;
  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkError) {
    throw new Error("Impossible de contacter le serveur. Verifiez votre connexion.");
  }

  if (response.status === 401 && auth) {
    clearToken();
    if (typeof onUnauthorized === "function") onUnauthorized();
    throw new Error("Votre session a expire, merci de vous reconnecter.");
  }

  if (!response.ok) {
    let data = null;
    try {
      data = await response.json();
    } catch (e) {
      /* pas de corps JSON */
    }
    throw new Error(formatApiError(data));
  }

  if (response.status === 204) return null;
  return response.json();
}

// ---------- Auth ----------
const Api = {
  register: (payload) => apiFetch("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiFetch("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiFetch("/auth/me"),
  updateMe: (payload) => apiFetch("/auth/me", { method: "PATCH", body: payload }),

  // ---------- Clients (CRM : prospects + clients, meme pipeline) ----------
  listClients: (statut) => apiFetch("/clients" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  createClient: (payload) => apiFetch("/clients", { method: "POST", body: payload }),
  updateClient: (id, payload) => apiFetch(`/clients/${id}`, { method: "PATCH", body: payload }),
  deleteClient: (id) => apiFetch(`/clients/${id}`, { method: "DELETE" }),
  clientTimeline: (id) => apiFetch(`/clients/${id}/timeline`),

  // ---------- Devis ----------
  listDevis: (statut) => apiFetch("/devis" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  devisARelancer: () => apiFetch("/devis/a-relancer"),
  createDevis: (payload) => apiFetch("/devis", { method: "POST", body: payload }),
  updateDevis: (id, payload) => apiFetch(`/devis/${id}`, { method: "PATCH", body: payload }),
  envoyerDevis: (id) => apiFetch(`/devis/${id}/envoyer`, { method: "POST" }),
  relancerDevis: (id) => apiFetch(`/devis/${id}/relancer`, { method: "POST" }),
  dupliquerDevis: (id) => apiFetch(`/devis/${id}/dupliquer`, { method: "POST" }),
  deleteDevis: (id) => apiFetch(`/devis/${id}`, { method: "DELETE" }),

  // ---------- Chantiers ----------
  listChantiers: () => apiFetch("/chantiers"),
  createChantier: (payload) => apiFetch("/chantiers", { method: "POST", body: payload }),
  updateChantier: (id, payload) => apiFetch(`/chantiers/${id}`, { method: "PATCH", body: payload }),
  deleteChantier: (id) => apiFetch(`/chantiers/${id}`, { method: "DELETE" }),
  addChantierNote: (id, payload) => apiFetch(`/chantiers/${id}/notes`, { method: "POST", body: payload }),

  // ---------- Conformite ----------
  listConformite: () => apiFetch("/conformite"),
  conformiteAlertes: () => apiFetch("/conformite/alertes"),
  createConformite: (payload) => apiFetch("/conformite", { method: "POST", body: payload }),
  deleteConformite: (id) => apiFetch(`/conformite/${id}`, { method: "DELETE" }),

  // ---------- Factures ----------
  listFactures: (statut) => apiFetch("/factures" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  createFacture: (payload) => apiFetch("/factures", { method: "POST", body: payload }),
  factureDepuisDevis: (devisId, type) => apiFetch(`/factures/depuis-devis/${devisId}?type=${encodeURIComponent(type || "standard")}`, { method: "POST" }),
  updateFacture: (id, payload) => apiFetch(`/factures/${id}`, { method: "PATCH", body: payload }),
  deleteFacture: (id) => apiFetch(`/factures/${id}`, { method: "DELETE" }),
  ajouterPaiement: (id, payload) => apiFetch(`/factures/${id}/paiements`, { method: "POST", body: payload }),

  // ---------- Tableau de bord & analytics ----------
  dashboard: () => apiFetch("/dashboard"),
  analytics: () => apiFetch("/analytics"),

  // ---------- Taches ----------
  listTaches: (statut) => apiFetch("/taches" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  createTache: (payload) => apiFetch("/taches", { method: "POST", body: payload }),
  updateTache: (id, payload) => apiFetch(`/taches/${id}`, { method: "PATCH", body: payload }),
  deleteTache: (id) => apiFetch(`/taches/${id}`, { method: "DELETE" }),

  // ---------- Planning ----------
  planning: (debut, fin) => apiFetch(`/planning?debut=${debut}&fin=${fin}`),
  listEvenements: () => apiFetch("/evenements"),
  createEvenement: (payload) => apiFetch("/evenements", { method: "POST", body: payload }),
  deleteEvenement: (id) => apiFetch(`/evenements/${id}`, { method: "DELETE" }),

  // ---------- Documents ----------
  listDocuments: (params) => apiFetch("/documents" + (params ? "?" + new URLSearchParams(params).toString() : "")),
  createDocument: (payload) => apiFetch("/documents", { method: "POST", body: payload }),
  deleteDocument: (id) => apiFetch(`/documents/${id}`, { method: "DELETE" }),

  // ---------- Abonnement ----------
  checkoutSession: () => apiFetch("/stripe/checkout-session", { method: "POST" }),
};

// Definie dans app.js : appelee quand le serveur renvoie 401 (token expire/invalide).
let onUnauthorized = null;

/**
 * Recupere un PDF (devis ou facture) et l'ouvre dans un nouvel onglet.
 * Pas de simple lien <a href> possible : l'endpoint exige le token JWT en
 * en-tete, donc on le recupere en JS puis on ouvre un blob local.
 */
async function ouvrirPdf(path) {
  const token = getToken();
  const response = await fetch(API_BASE + path, {
    headers: token ? { Authorization: "Bearer " + token } : {},
  });
  if (!response.ok) {
    let data = null;
    try { data = await response.json(); } catch (e) { /* pas de corps JSON */ }
    throw new Error(formatApiError(data) || "Impossible de generer le PDF.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}
