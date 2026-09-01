import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(testDir, "..", "admin");
const index = fs.readFileSync(path.join(adminDir, "index.html"), "utf8");
const script = fs.readFileSync(path.join(adminDir, "admin.js"), "utf8");
const css = fs.readFileSync(path.join(adminDir, "admin.css"), "utf8");
const activeUi = index + "\n" + script;

for (const id of ["design-current", "design-sections-availability", "design-family-cards", "pref-direction", "pref-ambience", "pref-density"]) {
  assert.match(index, new RegExp(`id="${id}"`), `le controle V3 ${id} doit exister`);
}

for (const label of [
  "Éditorial luxe", "Conversion premium", "Technique spatial", "Architecture brutaliste",
  "Atelier chaleureux", "Cinématique luxe", "Architecture minimale", "Matière éditoriale",
]) {
  assert.match(script, new RegExp(label), `la direction V3 ${label} doit etre exposee`);
}

for (const axis of [
  "Direction", "Silhouette", "Hero", "Typographie", "Images", "Prestations", "Projets",
  "Densité", "Mouvement", "Spatial / 3D", "Mobile", "Ambiance",
]) {
  assert.match(script, new RegExp(axis.replace("/", "\\/")), `l'axe V3 ${axis} doit etre affiche`);
}

assert.doesNotMatch(activeUi, /preferred_family|keep_current_family|pref-family|engine_version\s*:/, "aucun controle ou payload V2 ne doit rester actif");
assert.doesNotMatch(activeUi, /const FAMILY_LABELS|const DESIGN_AXES|header_variant|hero_variant|services_variant|gallery_variant|about_variant|reviews_variant|cta_variant|footer_variant|font_pair|radius_style|spacing_style/, "les axes V2 ne doivent plus etre exposes");
assert.doesNotMatch(activeUi, /variante_couleur|variante_motif|motif-select|gradient-mesh|wave-gradient/, "les controles du moteur legacy ne doivent plus etre exposes");
assert.doesNotMatch(index, /Personnaliser davantage|advanced-panel/, "l'ancien panneau avance V2 doit avoir disparu");

assert.match(script, /Ancien design/, "un profil historique doit etre signale discretement");
assert.match(script, /Une nouvelle génération utilisera le moteur V3/, "la prochaine etape V3 doit etre explicite");
assert.match(script, /currentVersion\.startsWith\("v2"\)/, "le bouton de generation doit reconnaitre l'etat historique");
assert.match(script, /site\/design\/candidate/, "un ancien site doit passer par une candidate V3");
assert.match(script, /Alternative V3 générée/, "le feedback de migration doit rester honnete");

for (const id of [
  "candidate-generate-button", "candidate-regenerate-button", "candidate-preview-button",
  "candidate-adopt-button", "candidate-abandon-button", "design-comparison",
]) {
  assert.match(index, new RegExp(`id="${id}"`), `la commande ${id} doit rester disponible`);
}
assert.match(script, /window\.confirm\(.*Adopter cette alternative/, "l'adoption doit demander confirmation");
assert.match(script, /window\.confirm\(.*Abandonner cette alternative/, "l'abandon doit demander confirmation");
assert.match(index, /ne publie pas le site/, "l'absence de publication automatique doit etre visible");
assert.match(script, /keep_current_direction:/, "la direction V3 actuelle peut etre conservee");
assert.match(script, /preferred_direction:/, "la direction choisie doit etre envoyee");
assert.match(script, /ambience:/, "l'ambiance choisie doit etre envoyee");

assert.match(script, /generateCandidate\(false\)\.catch\(handleError\)/, "les erreurs de generation doivent remonter");
assert.match(script, /adoptCandidate\(\)\.catch\(handleError\)/, "les erreurs d'adoption doivent remonter");
assert.match(script, /Cette section n'apparaît pas car aucune donnée n'est disponible\./, "les sections sans donnees doivent etre honnetes");

for (const id of ["admin-media-section", "admin-media-photos", "admin-media-selections"]) {
  assert.match(index, new RegExp(`id="${id}"`), `la zone media ${id} doit rester presente`);
}
assert.doesNotMatch(script, /\/site\/media2\b|\/site\/design\/media\b/, "aucune route media parallele ne doit apparaitre");
assert.match(script, /Photographe :/, "la provenance photographe doit rester affichee");
assert.match(script, /Voir la source/, "le lien provider doit rester disponible");
assert.match(css, /@media \(max-width: 900px\) \{ \.design-current-grid/, "le resume doit rester responsive");
assert.match(css, /@media \(max-width: 900px\) \{ \.design-comparison-grid/, "la comparaison doit rester responsive");

console.log("OK - admin-design-configurator.test.mjs");
