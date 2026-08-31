import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Verifie le configurateur de design V2 (Lot 4) de l'Admin : affichage du
// design actuel/alternative, actions candidate, etats de chargement/erreur,
// libelles francais, donnees manquantes, reglages avances, responsive.
// Verifications statiques (source), pas de rendu DOM ni de snapshot HTML
// geant - coherent avec les autres tests de frontend/tests/*.test.mjs.

const testDir = path.dirname(fileURLToPath(import.meta.url));
const adminDir = path.resolve(testDir, "..", "admin");
const index = fs.readFileSync(path.join(adminDir, "index.html"), "utf8");
const script = fs.readFileSync(path.join(adminDir, "admin.js"), "utf8");
const css = fs.readFileSync(path.join(adminDir, "admin.css"), "utf8");

// --- Design actuel : affichage lisible, jamais de code technique brut en avant ---
for (const id of ["design-current", "design-sections-availability", "design-family-cards", "pref-family"]) {
  assert.match(index, new RegExp(`id="${id}"`), `le controle ${id} doit exister`);
}
for (const id of ["pref-direction", "pref-ambience", "pref-density"]) {
  assert.match(index, new RegExp(`id="${id}"`), `le controle V3 ${id} doit exister au niveau simple`);
}
assert.match(script, /const DIRECTION_LABELS = \{/, "les directions V3 doivent avoir des libelles lisibles");
assert.match(script, /engine_version: isV3 \? "v3" : "v2"/, "le payload candidate doit annoncer explicitement le moteur choisi");
assert.match(script, /preferred_direction:/, "la direction V3 choisie doit etre envoyee au backend");
assert.match(script, /ambience:/, "l'ambiance V3 choisie doit etre envoyee au backend");
assert.match(script, /function renderDesignCurrent/, "le design actuel doit avoir un rendu dedie");
assert.match(script, /design-family-badge/, "la famille doit etre mise en avant visuellement");
assert.match(script, /<details class="design-technical">/, "le detail technique (signature) doit rester discret, pas la donnee principale");
assert.doesNotMatch(index, /id="site-design-profile"/, "l'ancien inspecteur technique brut ne doit plus exister");

// --- Sections disponibles : message honnete quand une section est absente ---
assert.match(script, /Cette section n'apparaît pas car aucune donnée n'est disponible\./, "le message d'indisponibilite doit reprendre le libelle du brief");
assert.match(script, /function renderSectionsAvailability/, "la disponibilite des sections doit avoir un rendu dedie");

// --- Candidate : generation, comparaison, actions avec libelles previsibles ---
for (const id of [
  "candidate-generate-button", "candidate-regenerate-button", "candidate-preview-button",
  "candidate-adopt-button", "candidate-abandon-button", "design-comparison",
]) {
  assert.match(index, new RegExp(`id="${id}"`), `le bouton/zone candidate ${id} doit exister`);
}
assert.match(index, />Générer une alternative</, "le bouton de generation doit avoir un libelle explicite");
assert.match(index, />Adopter cette version</, "le bouton d'adoption doit etre sans ambiguite");
assert.match(index, />Abandonner</, "le bouton d'abandon doit etre sans ambiguite");
assert.doesNotMatch(index.toLowerCase(), /magie|ia génère|intelligence artificielle/, "pas de vocabulaire vague type 'magie IA'");

// --- Confirmations avant mutation reelle (adopter/abandonner) ---
assert.match(script, /window\.confirm\(.*Adopter cette alternative/, "adopter doit demander une confirmation explicite");
assert.match(script, /window\.confirm\(.*Abandonner cette alternative/, "abandonner doit demander une confirmation");
assert.match(script, /Le site publié n'est jamais modifié automatiquement/, "le message d'adoption doit rappeler qu'il n'y a jamais de publication automatique");

// --- Jamais de publication automatique : rappel visible dans l'UI ---
assert.match(index, /ne publie pas le site/, "la note sous les actions candidate doit rappeler l'absence de publication automatique");

// --- Etats de chargement / anti double-clic ---
assert.match(script, /genBtn\.disabled = true/, "le bouton generer doit se desactiver pendant la requete");
assert.match(script, /regenBtn\.disabled = true/, "le bouton regenerer doit se desactiver pendant la requete");
assert.match(script, /function updateCandidateButtons/, "les boutons candidate doivent etre recalcules a chaque rafraichissement");
assert.match(script, /document\.getElementById\("candidate-generate-button"\)\.disabled = !site\.design_profile/, "generer doit rester disponible tant qu'un design existe, y compris apres abandon");

// --- Erreurs : passent par le meme toast/handleError que le reste de l'Admin, pas de succes fictif ---
assert.match(script, /generateCandidate\(false\)\.catch\(handleError\)/, "une erreur de generation doit remonter via handleError, jamais un faux succes");
assert.match(script, /adoptCandidate\(\)\.catch\(handleError\)/, "une erreur d'adoption doit remonter via handleError");

// --- Libelles francais pour les axes techniques (jamais de code brut en priorite) ---
assert.match(script, /const FAMILY_LABELS = \{/, "les familles doivent avoir un libelle francais");
assert.match(script, /const V3_DESIGN_AXES = \[/, "le resume V3 doit montrer ses axes de composition importants");
assert.match(script, /const IMAGE_TREATMENT_LABELS = \{ flat: "Naturelle", duotone: "Bicolore", framed: "Encadrée", overlay: "Dégradé" \}/, "les traitements d'image doivent avoir les libelles du brief");
assert.match(script, /const FONT_PAIR_LABELS = \{/, "les paires de polices doivent avoir une description, pas un identifiant brut");
assert.match(script, /const PALETTE_LABELS = \{/, "les palettes doivent avoir un libelle, pas seulement un id");

// --- Donnees manquantes : etat honnete quand il n'y a pas encore de design ---
assert.match(script, /Aucun design généré/, "l'absence de design doit etre annoncee honnetement, jamais une candidate vide masquee");

// --- Reglages avances (Niveau 2), replies derriere un toggle natif <details>, jamais force ---
assert.match(index, /<details class="design-personalize"[\s\S]*?<summary/, "les reglages avances doivent etre derriere un disclosure dedie");
assert.doesNotMatch(index, /<details class="design-personalize"[^>]*\bopen\b/, "le panneau avance doit rester masque par defaut (non force)");
assert.match(index, /id="advanced-panel" class="advanced-panel"/, "le panneau avance doit exister");
assert.match(script, /function buildAdvancedPanel/, "le panneau avance doit etre construit depuis le registre de variantes");
assert.match(script, /section-order-editor/, "le reordonnancement des sections doit rester une liste simple (haut\\/bas), pas de librairie drag-and-drop");
assert.doesNotMatch(script + index, /sortablejs|react-beautiful-dnd|interactjs/i, "aucune librairie de drag-and-drop lourde ne doit etre ajoutee");

// --- Palette en swatches visuels, pas un id brut affiche seul ---
assert.match(css, /\.palette-swatch \{/, "les palettes doivent avoir un rendu visuel (swatch), pas seulement du texte");

// --- Media (Lot 2) : toujours reutilise tel quel, pas duplique ---
for (const id of ["admin-media-section", "admin-media-photos", "admin-media-selections"]) {
  assert.match(index, new RegExp(`id="${id}"`), `la zone media existante ${id} doit rester presente et reutilisee`);
}
assert.doesNotMatch(script, /\/site\/media2\b|\/site\/design\/media\b/, "aucune route media dupliquee ne doit etre introduite pour le configurateur");
assert.match(script, /Photographe :/, "la provenance photographe des medias provider doit etre affichee");
assert.match(script, /Voir la source/, "un lien vers la source provider doit etre disponible");

// --- Reactivite raisonnable (pas de redesign mobile-first, mais pas d'overflow) ---
assert.match(css, /@media \(max-width: 900px\) \{ \.design-current-grid/, "le design actuel doit rester lisible sur tablette");
assert.match(css, /@media \(max-width: 900px\) \{ \.design-comparison-grid/, "la comparaison doit repasser en une colonne sur petit ecran");

// --- Endpoints attendus (contrat avec le backend Lot 4, cf backend/app/routers/admin.py) ---
for (const route of [
  "/site/design/preferences", "/site/design/candidate", "/regenerate",
  "/site/design/candidate/adopt", "/site/preview-session/candidate",
]) {
  assert.match(script, new RegExp(route.replace(/\//g, "\\/")), `le front doit appeler ${route}`);
}

console.log("OK - admin-design-configurator.test.mjs");
