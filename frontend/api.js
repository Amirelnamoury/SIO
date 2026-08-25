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

  // ---------- Devis ----------
  listDevis: (statut) => apiFetch("/devis" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  devisARelancer: () => apiFetch("/devis/a-relancer"),
  createDevis: (payload) => apiFetch("/devis", { method: "POST", body: payload }),
  updateDevis: (id, payload) => apiFetch(`/devis/${id}`, { method: "PATCH", body: payload }),
  envoyerDevis: (id) => apiFetch(`/devis/${id}/envoyer`, { method: "POST" }),
  relancerDevis: (id) => apiFetch(`/devis/${id}/relancer`, { method: "POST" }),
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

  // ---------- Abonnement ----------
  checkoutSession: () => apiFetch("/stripe/checkout-session", { method: "POST" }),
};

// Definie dans app.js : appelee quand le serveur renvoie 401 (token expire/invalide).
let onUnauthorized = null;
