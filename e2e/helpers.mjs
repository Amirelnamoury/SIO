// Petites briques partagees par les scenarios E2E (backend/e2e/*.mjs).
// Appelle directement l'API HTTP (pas de navigateur) : plus rapide et plus
// stable qu'une automatisation UI pour verifier la logique metier reelle.
// Necessite un backend demarre sur API_BASE (voir README.md de ce dossier).

export const API_BASE = process.env.API_BASE || "http://localhost:8000";

export function assert(condition, message) {
  if (!condition) throw new Error("ASSERTION ECHOUEE : " + message);
}

export function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`ASSERTION ECHOUEE : ${message} (attendu ${JSON.stringify(expected)}, recu ${JSON.stringify(actual)})`);
  }
}

export function assertClose(actual, expected, message, epsilon = 0.01) {
  if (Math.abs(actual - expected) > epsilon) {
    throw new Error(`ASSERTION ECHOUEE : ${message} (attendu ~${expected}, recu ${actual})`);
  }
}

let compteurEmail = 0;

/** Genere un email unique par execution pour eviter les collisions entre runs. */
export function emailUnique(prefixe) {
  compteurEmail += 1;
  return `${prefixe}-${Date.now()}-${compteurEmail}@e2e-test.fr`;
}

async function req(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(API_BASE + path, {
    method, headers, body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* pas de corps JSON (204, etc.) */ }
  if (!res.ok) {
    throw new Error(`${method} ${path} -> HTTP ${res.status} : ${data ? JSON.stringify(data) : "(pas de corps)"}`);
  }
  return data;
}

export const api = {
  get: (path, token) => req(path, { token }),
  post: (path, body, token) => req(path, { method: "POST", body, token }),
  patch: (path, body, token) => req(path, { method: "PATCH", body, token }),
  del: (path, token) => req(path, { method: "DELETE", token }),
};

/** Cree un artisan de test frais et renvoie {token, artisanId, email}. */
export async function creerArtisanTest(prefixe = "e2e") {
  const email = emailUnique(prefixe);
  const data = await api.post("/auth/register", {
    email, password: "TestPass123!", nom_entreprise: `E2E ${prefixe} ${Date.now()}`,
    nom_artisan: "Test E2E", metier: "general",
  });
  return { token: data.access_token, email };
}

/** Active l'abonnement d'un artisan de test (contourne Stripe, comme le script manage_subscription.py). */
export async function activerAbonnement(email) {
  const { execSync } = await import("node:child_process");
  execSync(`cd /home/user/SIO/backend && source .venv/bin/activate && python manage_subscription.py activer "${email}"`, { shell: "/bin/bash" });
}

export function logEtape(texte) {
  console.log("  -> " + texte);
}
