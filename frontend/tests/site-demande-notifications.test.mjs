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
assert.match(appSource, /await Api\.markNotificationRead\(notificationId\)/, "ouvrir la demande doit acquitter la notification");
assert.match(appSource, /await showTimeline\(clientId\)/, "ouvrir la notification doit afficher le bon prospect");

console.log("OK - site-demande-notifications.test.mjs");
