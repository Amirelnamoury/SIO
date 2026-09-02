import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(testDir, "..", "admin");
const login = fs.readFileSync(path.join(adminDir, "login.html"), "utf8");
const index = fs.readFileSync(path.join(adminDir, "index.html"), "utf8");
const script = fs.readFileSync(path.join(adminDir, "admin.js"), "utf8");

for (const [name, html] of [["login.html", login], ["index.html", index]]) {
  assert.match(html, /href="admin\.css"/, `${name} doit charger le CSS présent dans son propre dossier`);
  assert.match(html, /src="admin\.js"/, `${name} doit charger le JavaScript présent dans son propre dossier`);
  assert.doesNotMatch(html, /\/admin\/assets\//, `${name} ne doit plus utiliser les routes d'assets réservées au backend`);
}

assert.match(script, /isLocalFrontend[\s\S]*?"http:\/\/localhost:8000"/, "l'Admin statique local doit appeler le backend sur le port 8000");
assert.match(script, /fetch\(apiUrl\("\/admin\/auth\/login"\)/, "la connexion doit utiliser l'URL API résolue");
assert.match(script, /sessionStorage\.setItem\(ADMIN_TOKEN_KEY, data\.access_token\)/, "le jeton Admin doit survivre à la redirection locale");
assert.match(script, /opts\.headers\.Authorization = "Bearer " \+ token/, "les appels Admin doivent transmettre le jeton au backend");
assert.match(script, /location\.assign\("\/admin\/"\)/, "la connexion doit rediriger vers l'index Admin statique");
assert.match(script, /location\.assign\("\/admin\/login\.html"\)/, "une session absente ou fermée doit rediriger vers le login statique");
assert.doesNotMatch(script, /location\.assign\("\/admin\/login"\)/, "l'ancienne redirection backend-only ne doit plus subsister");
assert.doesNotMatch(script, /preview-session|design\/candidate|site\/generate/, "le moteur de generation retire ne doit laisser aucun appel mort dans l'Admin");

// Micro-lot "nettoyer le workflow admin des sites vitrines" : aucun texte ni
// bouton ne doit plus laisser croire qu'une generation automatique de site
// existe ou peut encore se produire (voir aussi admin-dom-consistency, qui
// verifie mecaniquement l'absence de bouton mort/orphelin).
assert.doesNotMatch(index + script, /Générés?\b/, "le mot \"Généré(s)\" (moteur retire) ne doit plus apparaître dans l'UI Admin");
assert.doesNotMatch(index + script, /Generez une preview|Dernière génération/i, "les formulations de generation retirees ne doivent plus apparaître");
assert.doesNotMatch(index, /id="generate-button"|id="preview-button"/, "aucun bouton generer\/preview ne doit exister dans la fiche site");
assert.doesNotMatch(script, /Générés à vérifier/, "le dashboard ne doit plus présenter les sites \"genere\" comme une génération à vérifier");
assert.match(script, /statusLabels[\s\S]*?genere:\s*"À finaliser"/, "le statut historique \"genere\" doit être présenté comme à finaliser, pas comme généré");

console.log("OK - admin-assets.test.mjs");
