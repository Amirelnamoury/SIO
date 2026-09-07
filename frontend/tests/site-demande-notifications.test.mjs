import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(testDir, "..");
const apiSource = fs.readFileSync(path.join(frontendDir, "api.js"), "utf8");
const appSource = fs.readFileSync(path.join(frontendDir, "app.js"), "utf8");

assert.match(apiSource, /markNotificationRead:[\s\S]*?\/notifications\/\$\{id\}\/lire/, "la lecture doit passer par l'API tenant-scopee");
assert.match(appSource, /nouvelle_demande_devis:\s*"Prospect"/, "la nouvelle demande doit avoir un type lisible");
assert.match(appSource, /data-notification-id=/, "la notification persistante doit pouvoir etre marquee lue");
assert.match(appSource, /data-client-id=/, "le bouton doit conserver la cible prospect");
assert.match(appSource, /data-objet-id=/, "le bouton doit porter l'identifiant de la piece visee");
assert.match(appSource, /await Api\.markNotificationRead\(notificationId\)/, "ouvrir la demande doit acquitter la notification");

// Chaque type de notification designe une piece precise ; « Voir » doit
// l'ouvrir, pas deposer l'artisan devant la liste. La correspondance vit
// dans ouvrirNotification().
const routageStart = appSource.indexOf("async function ouvrirNotification");
const routageEnd = appSource.indexOf("\n}", routageStart);
assert.ok(routageStart !== -1 && routageEnd > routageStart, "le routage des notifications est introuvable");
const routage = appSource.slice(routageStart, routageEnd);
for (const [type, objet] of [
  ["devis_relance", "devis"],
  ["facture_relance", "facture"],
  ["message_client", "client"],
  ["nouvelle_demande_devis", "client"],
]) {
  assert.match(
    routage,
    new RegExp(`case "${type}":[\\s\\S]*?ouvrirObjet\\("${objet}"`),
    `une notification « ${type} » doit ouvrir ${objet}`,
  );
}
assert.match(routage, /case "conformite":[\s\S]*?data-tab="conformite"/, "la conformité doit ouvrir son onglet");
assert.match(appSource, /case "client": showTimeline\(identifiant\)/, "ouvrir un client doit afficher son dossier");

console.log("OK - site-demande-notifications.test.mjs");
