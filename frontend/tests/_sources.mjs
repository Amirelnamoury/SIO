/* Les sources du frontend, lues une fois.
 *
 * app.js est en cours de decoupage par domaine (Astra §16). Chaque extraction
 * deplace du code d'un fichier a l'autre sans rien changer a son
 * comportement - mais un test qui decoupe `app.js` par `indexOf` echoue alors
 * pour une raison qui n'a rien a voir avec ce qu'il verifie.
 *
 * D'ou `tout` : la concatenation des scripts du produit, dans leur ordre de
 * chargement. Un test qui verifie « ce code existe et fait ceci » s'en sert et
 * survit aux extractions. Un test qui verifie « ce code n'existe PLUS nulle
 * part » doit s'en servir AUSSI - sur un seul fichier, il passerait pour la
 * mauvaise raison. Seuls les tests qui portent sur l'organisation elle-meme
 * (quel fichier contient quoi) visent un fichier precis.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const backendDir = path.resolve(frontendDir, "..", "backend", "app");

const lire = (nom) => fs.readFileSync(path.join(frontendDir, nom), "utf8");

export const api = lire("api.js");
export const socle = lire("socle.js");
export const navigation = lire("navigation.js");
export const planning = lire("planning.js");
export const statistiques = lire("statistiques.js");
export const app = lire("app.js");
export const index = lire("index.html");
export const style = lire("style.css");
export const jeuEssai = lire(path.join("outils", "jeu-essai.js"));

/** Tous les scripts du produit, dans leur ordre de chargement. */
export const tout = [api, socle, navigation, planning, statistiques, app].join("\n");

/** Un fichier du backend, par son chemin relatif a backend/app. */
export const backend = (relatif) => fs.readFileSync(path.join(backendDir, ...relatif.split("/")), "utf8");
