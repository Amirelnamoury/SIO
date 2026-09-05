import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontend = path.resolve(here, "..");
const index = fs.readFileSync(path.join(frontend, "index.html"), "utf8");
const style = fs.readFileSync(path.join(frontend, "style.css"), "utf8");
const app = fs.readFileSync(path.join(frontend, "app.js"), "utf8");
const api = fs.readFileSync(path.join(frontend, "api.js"), "utf8");

const tabs = ["profil", "identite-visuelle", "equipe", "prestations", "fournisseurs", "automatisations", "contrats", "conformite"];
for (const tab of tabs) {
  assert.match(index, new RegExp(`data-tab="${tab}"`), `onglet Entreprise manquant: ${tab}`);
  assert.match(index, new RegExp(`data-tab-panel="${tab}"`), `panneau Entreprise manquant: ${tab}`);
}

assert.match(index, /id="profile-photo-file"[\s\S]*accept="image\/png,image\/jpeg,image\/webp"/);
assert.match(index, /id="enterprise-profile-photo"/);
assert.match(index, /id="topbar-profile-photo"/);
assert.match(api, /uploadProfilePhoto:[\s\S]*uploadFetch\("\/auth\/me\/photo-profil"/);
assert.match(api, /deleteProfilePhoto:[\s\S]*apiFetch\("\/auth\/me\/photo-profil"/);
assert.match(app, /protectedImageUrl\(path\)/);
assert.match(app, /URL\.revokeObjectURL\(profilePhotoObjectUrl\)/);
assert.match(app, /setupProfilePhoto\(\)/);

assert.match(style, /#view-entreprise \.entreprise-tabs \{[\s\S]*background: var\(--sa-surface\)/);
assert.match(style, /\.enterprise-record \{ display: grid/);
assert.match(style, /#view-entreprise \.entreprise-section > \.list \{/);
assert.match(style, /#view-factures #facture-filters \{ margin-bottom: var\(--sa-space-4\); \}/);

console.log("OK - entreprise-ui.test.mjs");
