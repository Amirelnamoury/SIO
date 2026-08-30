import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const index = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");
const api = fs.readFileSync(path.join(frontendDir, "api.js"), "utf8");
const app = fs.readFileSync(path.join(frontendDir, "app.js"), "utf8");
const adminIndex = fs.readFileSync(path.join(frontendDir, "admin", "index.html"), "utf8");
const adminScript = fs.readFileSync(path.join(frontendDir, "admin", "admin.js"), "utf8");

for (const id of [
  "visual-identity-box", "site-logo-form", "site-logo-preview", "site-logo-delete",
  "site-photo-form", "site-photo-category", "site-photos-list", "site-media-error",
]) {
  assert.match(index, new RegExp(`id="${id}"`), `le contrôle artisan ${id} doit exister`);
}
assert.match(index, /accept="image\/png,image\/jpeg,image\/webp"/, "l'UI ne doit proposer que les formats supportés");
assert.match(api, /siteMedia:\s*\(\) => apiFetch\("\/site-media"\)/, "la liste médias doit passer par l'API protégée");
assert.match(api, /uploadSiteLogo:[\s\S]*?uploadFetch\("\/site-media\/logo"/, "le logo doit utiliser multipart avec Bearer");
assert.match(api, /orderSitePhotos:[\s\S]*?method: "PUT"/, "l'ordre doit être persisté au backend");
assert.match(api, /async function protectedImageUrl[\s\S]*?Authorization: "Bearer " \+ token/, "les images artisan doivent être chargées avec le JWT");
assert.match(app, /loadSiteMedia\(\)\.catch\(showSiteMediaError\)/, "ouvrir Entreprise doit charger les médias");
assert.match(app, /button\.textContent = "Traitement\.\.\."/, "l'upload doit donner un retour pendant le traitement");
assert.match(app, /Api\.updateSiteMedia[\s\S]*?categorie/, "la catégorie doit être modifiable");
assert.match(app, /Api\.updateSiteMedia[\s\S]*?actif/, "une photo doit pouvoir être désactivée");
assert.match(app, /Api\.deleteSiteMedia/, "une photo doit pouvoir être supprimée");

for (const id of ["admin-media-section", "admin-logo-form", "admin-media-photos", "admin-media-selections"]) {
  assert.match(adminIndex, new RegExp(`id="${id}"`), `le contrôle Admin ${id} doit exister`);
}
assert.match(adminScript, /async function protectedImageUrl[\s\S]*?Authorization: "Bearer " \+ token/, "les miniatures Admin doivent conserver le Bearer token");
assert.match(adminScript, /site\/media\/selections\//, "l'Admin doit pouvoir retirer une sélection");
assert.match(adminScript, /source artisan/, "la source réelle des photos doit être visible");

console.log("OK - site-media.test.mjs");
