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
// Cette ligne verifiait une regle ecrite au nom d'une vue :
// « #view-factures #facture-filters { margin-bottom: 16px } ». La refonte
// a remplace ces quatorze retouches par le systeme de familles, ou
// l'espacement d'un registre est declare une fois. Verifier la regle
// disparue revenait a interdire la correction ; on verifie desormais le
// RESULTAT qu'elle produisait - un registre garde ses filtres et sa
// recherche sur une seule ligne, quel que soit l'ecran.
assert.match(style, /\.view\[data-famille="registre"\] \.list-toolbar,\s*\n\.view\[data-famille="parc"\] \.list-toolbar \{[^}]*flex-wrap: wrap/,
  "les commandes d'un registre passent a la ligne plutot que de deborder");
assert.match(style, /\.view\[data-famille="registre"\] \.list-toolbar,\s*\n\.view\[data-famille="parc"\] \.list-toolbar \{[^}]*margin-bottom: var\(--sa-space-4\)/,
  "l'espacement sous les commandes est declare pour la famille, pas par vue");

console.log("OK - entreprise-ui.test.mjs");
