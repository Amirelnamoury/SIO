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
  moi: () => apiFetch("/auth/moi"),
  updateMe: (payload) => apiFetch("/auth/me", { method: "PATCH", body: payload }),

  // ---------- Equipe ----------
  listEquipe: () => apiFetch("/equipe"),
  createMembre: (payload) => apiFetch("/equipe", { method: "POST", body: payload }),
  updateMembre: (id, payload) => apiFetch(`/equipe/${id}`, { method: "PATCH", body: payload }),
  deleteMembre: (id) => apiFetch(`/equipe/${id}`, { method: "DELETE" }),

  // ---------- Clients (CRM : prospects + clients, meme pipeline) ----------
  listClients: (statut) => apiFetch("/clients" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  createClient: (payload) => apiFetch("/clients", { method: "POST", body: payload }),
  updateClient: (id, payload) => apiFetch(`/clients/${id}`, { method: "PATCH", body: payload }),
  deleteClient: (id) => apiFetch(`/clients/${id}`, { method: "DELETE" }),
  clientTimeline: (id) => apiFetch(`/clients/${id}/timeline`),
  clientResume: (id) => apiFetch(`/clients/${id}/resume`),

  // ---------- Catalogue de prestations ----------
  listPrestations: (q) => apiFetch("/prestations" + (q ? `?q=${encodeURIComponent(q)}` : "")),
  createPrestation: (payload) => apiFetch("/prestations", { method: "POST", body: payload }),
  updatePrestation: (id, payload) => apiFetch(`/prestations/${id}`, { method: "PATCH", body: payload }),
  deletePrestation: (id) => apiFetch(`/prestations/${id}`, { method: "DELETE" }),

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
  addChantierDepense: (id, payload) => apiFetch(`/chantiers/${id}/depenses`, { method: "POST", body: payload }),
  preparerChantierDepuisDevis: (devisId, payload) => apiFetch(`/chantiers/depuis-devis/${devisId}`, { method: "POST", body: payload }),
  cloturerChantier: (id, payload) => apiFetch(`/chantiers/${id}/cloturer`, { method: "POST", body: payload }),

  // ---------- Fournisseurs ----------
  listFournisseurs: () => apiFetch("/fournisseurs"),
  createFournisseur: (payload) => apiFetch("/fournisseurs", { method: "POST", body: payload }),
  updateFournisseur: (id, payload) => apiFetch(`/fournisseurs/${id}`, { method: "PATCH", body: payload }),
  deleteFournisseur: (id) => apiFetch(`/fournisseurs/${id}`, { method: "DELETE" }),

  // ---------- Contrats recurrents ----------
  listContrats: () => apiFetch("/contrats"),
  createContrat: (payload) => apiFetch("/contrats", { method: "POST", body: payload }),
  updateContrat: (id, payload) => apiFetch(`/contrats/${id}`, { method: "PATCH", body: payload }),
  deleteContrat: (id) => apiFetch(`/contrats/${id}`, { method: "DELETE" }),
  genererContrat: (id) => apiFetch(`/contrats/${id}/generer`, { method: "POST" }),

  // ---------- Conformite ----------
  listConformite: () => apiFetch("/conformite"),
  conformiteAlertes: () => apiFetch("/conformite/alertes"),
  createConformite: (payload) => apiFetch("/conformite", { method: "POST", body: payload }),
  deleteConformite: (id) => apiFetch(`/conformite/${id}`, { method: "DELETE" }),

  // ---------- Factures ----------
  listFactures: (statut) => apiFetch("/factures" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  facturesARelancer: () => apiFetch("/factures/a-relancer"),
  createFacture: (payload) => apiFetch("/factures", { method: "POST", body: payload }),
  factureDepuisDevis: (devisId, type) => apiFetch(`/factures/depuis-devis/${devisId}?type=${encodeURIComponent(type || "standard")}`, { method: "POST" }),
  updateFacture: (id, payload) => apiFetch(`/factures/${id}`, { method: "PATCH", body: payload }),
  deleteFacture: (id) => apiFetch(`/factures/${id}`, { method: "DELETE" }),
  relancerFacture: (id) => apiFetch(`/factures/${id}/relancer`, { method: "POST" }),
  ajouterPaiement: (id, payload) => apiFetch(`/factures/${id}/paiements`, { method: "POST", body: payload }),

  // ---------- Avis clients ----------
  listAvis: () => apiFetch("/avis"),
  createAvis: (payload) => apiFetch("/avis", { method: "POST", body: payload }),
  updateAvis: (id, payload) => apiFetch(`/avis/${id}`, { method: "PATCH", body: payload }),
  deleteAvis: (id) => apiFetch(`/avis/${id}`, { method: "DELETE" }),
  demanderAvis: (clientId) => apiFetch(`/clients/${clientId}/demande-avis`, { method: "POST" }),

  // ---------- Portail client ----------
  genererLienPortail: (clientId) => apiFetch(`/clients/${clientId}/portail/generer`, { method: "POST" }),
  listClientMessages: (clientId) => apiFetch(`/clients/${clientId}/messages`),
  envoyerClientMessage: (clientId, payload) => apiFetch(`/clients/${clientId}/messages`, { method: "POST", body: payload }),

  // ---------- Automatisation ----------
  automationStatus: () => apiFetch("/automation/status"),
  automationEmails: () => apiFetch("/automation/emails"),

  // ---------- Notifications ----------
  listNotifications: () => apiFetch("/notifications"),

  // ---------- Tableau de bord & analytics ----------
  dashboard: () => apiFetch("/dashboard"),
  dashboardRecommandations: () => apiFetch("/dashboard/recommandations"),
  dashboardSante: () => apiFetch("/dashboard/sante"),
  analytics: () => apiFetch("/analytics"),

  // ---------- Recherche globale ----------
  search: (q) => apiFetch(`/search?q=${encodeURIComponent(q)}`),

  // ---------- Taches ----------
  listTaches: (statut) => apiFetch("/taches" + (statut ? `?statut=${encodeURIComponent(statut)}` : "")),
  createTache: (payload) => apiFetch("/taches", { method: "POST", body: payload }),
  updateTache: (id, payload) => apiFetch(`/taches/${id}`, { method: "PATCH", body: payload }),
  deleteTache: (id) => apiFetch(`/taches/${id}`, { method: "DELETE" }),

  // ---------- Planning ----------
  planning: (debut, fin) => apiFetch(`/planning?debut=${debut}&fin=${fin}`),
  listEvenements: () => apiFetch("/evenements"),
  createEvenement: (payload) => apiFetch("/evenements", { method: "POST", body: payload }),
  updateEvenement: (id, payload) => apiFetch(`/evenements/${id}`, { method: "PATCH", body: payload }),
  deleteEvenement: (id) => apiFetch(`/evenements/${id}`, { method: "DELETE" }),

  // ---------- Documents ----------
  listDocuments: (params) => apiFetch("/documents" + (params ? "?" + new URLSearchParams(params).toString() : "")),
  createDocument: (payload) => apiFetch("/documents", { method: "POST", body: payload }),
  uploadDocument: (formData) => uploadFetch("/documents/upload", formData),
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

/** Envoie un FormData (upload de fichier) avec le token JWT, sans Content-Type manuel
 * (le navigateur ajoute le boundary multipart tout seul). */
async function uploadFetch(path, formData) {
  const token = getToken();
  let response;
  try {
    response = await fetch(API_BASE + path, {
      method: "POST",
      headers: token ? { Authorization: "Bearer " + token } : {},
      body: formData,
    });
  } catch (networkError) {
    throw new Error("Impossible de contacter le serveur. Verifiez votre connexion.");
  }
  if (response.status === 401) {
    clearToken();
    if (typeof onUnauthorized === "function") onUnauthorized();
    throw new Error("Votre session a expire, merci de vous reconnecter.");
  }
  if (!response.ok) {
    let data = null;
    try { data = await response.json(); } catch (e) { /* pas de corps JSON */ }
    throw new Error(formatApiError(data));
  }
  return response.json();
}

/**
 * Telecharge reellement un document uploade (pas d'ouverture d'onglet : on force
 * le telechargement avec le nom de fichier original via un lien <a download>).
 */
async function telechargerDocument(id, nomFichier) {
  const token = getToken();
  const response = await fetch(API_BASE + `/documents/${id}/fichier`, {
    headers: token ? { Authorization: "Bearer " + token } : {},
  });
  if (!response.ok) {
    let data = null;
    try { data = await response.json(); } catch (e) { /* pas de corps JSON */ }
    throw new Error(formatApiError(data) || "Impossible de telecharger le document.");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nomFichier || "document";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
