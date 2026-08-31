import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(testDir, "..", "admin");
const login = fs.readFileSync(path.join(adminDir, "login.html"), "utf8");
const index = fs.readFileSync(path.join(adminDir, "index.html"), "utf8");
const script = fs.readFileSync(path.join(adminDir, "admin.js"), "utf8");
const css = fs.readFileSync(path.join(adminDir, "admin.css"), "utf8");

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
assert.match(script, /preview-session/, "Voir la preview doit demander une session protégée au backend");
assert.match(script, /previewWindow\.location\.replace\(apiUrl\(session\.url\)\)/, "la preview doit utiliser API_BASE après le handoff authentifié");
assert.doesNotMatch(script, /window\.open\("\/admin\/api\/artisans\//, "la preview ne doit plus viser directement le serveur statique");
assert.match(index, /id="design-configurator-section"/, "le configurateur de design V2 (Lot 4) doit exister dans la fiche site");
assert.match(index, /id="design-current"/, "le design actuel doit avoir une zone d'affichage lisible");
assert.match(index, /id="design-comparison"/, "la comparaison version actuelle / alternative doit exister");
for (const field of ["header_variant", "hero_variant", "services_variant", "gallery_variant", "about_variant", "reviews_variant", "cta_variant", "footer_variant", "font_pair", "radius_style", "spacing_style", "image_treatment", "section_order"]) {
  assert.match(script, new RegExp(field), `l'Admin doit exposer la décision ${field}`);
}
assert.match(script, /escapeHtml\(SECTION_LABELS\[section\] \|\| section\)/, "l'ordre des sections doit rester échappé avant affichage");
assert.match(css, /\.design-current-grid/, "le profil V2 doit avoir une présentation lisible");

console.log("OK - admin-assets.test.mjs");
