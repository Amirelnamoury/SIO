/* Le systeme de composition : une identite, des pages differentes.
 *
 * La refonte UI a remplace une coquille unique - meme sur-titre, meme grand
 * titre, meme phrase de presentation, meme barre de filtres sur les treize
 * ecrans - par des FAMILLES declarees dans le balisage. Une vue dit sa
 * mission, la feuille en deduit sa composition.
 *
 * Ce que ces tests protegent, dans l'ordre d'importance :
 *
 *   1. la famille est declaree la ou elle se lit (le balisage), et remontee
 *      sur <body> pour que la coquille puisse suivre ;
 *   2. aucune retouche ne revient sous le nom d'une vue - c'est ce qui avait
 *      produit sept largeurs de colonne differentes pour une meme coquille,
 *      puis quatorze reglages de filtres mesures a la main ;
 *   3. la direction artistique abandonnee ne peut pas revenir par un jeton
 *      mort laisse en place ;
 *   4. les regles de lisibilite que l'oeil ne verifie pas : la taille des
 *      champs, la hauteur des commandes, la casse des intitules.
 */
import assert from "node:assert/strict";
import * as sources from "./_sources.mjs";

const { style, index, navigation } = sources;

// ---------------------------------------------------------------------
// 1. Chaque vue declare sa famille, et la coquille peut la lire
// ---------------------------------------------------------------------
const vues = [...index.matchAll(/<section id="view-([a-z]+)" class="view"([^>]*)>/g)];
assert.equal(vues.length, 13, "les treize vues du produit");
for (const [, nom, attributs] of vues) {
  assert.match(attributs, /data-famille="[a-z]+"/,
    `la vue ${nom} doit declarer sa famille de composition`);
}
// Une famille par mission, pas une par vue : si chaque ecran avait la
// sienne, le systeme ne dirait plus rien.
const familles = new Set(vues.map(([, , a]) => /data-famille="([a-z]+)"/.exec(a)[1]));
assert.ok(familles.size <= 9, `${familles.size} familles pour 13 vues : le systeme doit regrouper`);
assert.ok(familles.has("registre") && familles.has("poste") && familles.has("agenda"));

assert.match(navigation, /document\.body\.dataset\.famille = \(section && section\.dataset\.famille\)/,
  "switchView remonte la famille sur <body> pour que la coquille suive");

// La feuille doit reellement s'en servir, sinon l'attribut est decoratif.
assert.ok((style.match(/data-famille="/g) || []).length >= 12,
  "la feuille compose a partir de la famille, pas a partir du nom des vues");

// ---------------------------------------------------------------------
// 2. Rien ne revient sous le nom d'une vue
// ---------------------------------------------------------------------
// On tolere les regles qui portent sur un CONTENU propre a une vue (une
// grille de colonnes, un onglet d'entreprise) ; on refuse celles qui
// refont la mise en page generale d'un ecran pour lui seul.
assert.doesNotMatch(style, /#view-[a-z]+ \.view-header \{[^}]*margin-bottom: \d+px/,
  "une marge d'en-tete en pixels, ecrite pour une vue, est une retouche - pas une composition");
assert.doesNotMatch(style, /#view-[a-z]+ \.view-header-actions \{[^}]*margin-top: \d+px/,
  "aucun decalage d'actions mesure a la main");
assert.doesNotMatch(style, /#view-[a-z]+ #[a-z-]+ \{ width: \d+px; \}/,
  "la largeur d'un filtre suit son contenu, pas une valeur relevee ecran par ecran");

// ---------------------------------------------------------------------
// 3. La direction « Atelier » ne peut pas revenir
// ---------------------------------------------------------------------
// Le brief est explicite : ni cuivre, ni bronze, ni vieux papier, ni beige
// generalise. Un jeton mort qui repond encore est precisement ce qui
// permet a une identite abandonnee de rentrer par une regle distraite.
assert.doesNotMatch(style, /--sa-laiton|--sa-bronze/,
  "les jetons de la direction abandonnee sont retires, pas neutralises");
// Les fonds papier de l'ancienne palette. On les cherche dans TOUTE la
// feuille : une seule reapparition suffit a rompre l'unite des plans.
for (const beige of ["#F4F1EA", "#FCFAF5", "#EBE7DE", "#E3DED2", "#8A6024", "#1C1E1A", "#23261F"]) {
  assert.ok(!style.toUpperCase().includes(beige), `${beige} appartient a la direction abandonnee`);
}

// ---------------------------------------------------------------------
// 4. Les regles que l'oeil ne verifie pas
// ---------------------------------------------------------------------
// 16 px dans les champs : en dessous, iOS zoome a la mise au point et
// deplace l'utilisateur dans la page sans prevenir.
assert.match(style, /--sa-text-md: 1rem;/, "les champs sont a 16 px");
assert.match(style, /input, select, textarea \{ font-size: var\(--sa-text-md\); \}/);
// Une hauteur de commande par famille, et un plancher tactile.
assert.match(style, /--sa-control-h: 40px;/);
assert.match(style, /--sa-touch: 44px;/);
assert.match(style, /@media \(pointer: coarse\)[\s\S]{0,400}min-height: var\(--sa-touch\)/,
  "sur un ecran tactile le plancher monte a 44 px");

// L'intitule de marge etait en capitales espacees et sortait de sa colonne :
// « Performance » demandait 91 px pour 72 disponibles.
assert.doesNotMatch(style, /\.sa-section-titre \{[^}]*text-transform: uppercase/,
  "les intitules de marge ne sont pas en capitales espacees");

// ---------------------------------------------------------------------
// LE PLANCHER DE LISIBILITE
// ---------------------------------------------------------------------
// Huit tailles vivaient sous 11 px : 0.58, 0.62, 0.64, 0.65, 0.66, 0.68 rem
// et un 10 px en SVG. La plus grave etait l'HEURE d'un rendez-vous, a
// 9,9 px - la donnee la plus importante d'un agenda, ecrite sous le seuil
// de ce qu'on lit sans effort a bout de bras dans un fourgon. Aucune de ces
// derives ne se voit sur une capture d'ecran ; elles se mesurent.
//
// L'agenda a le droit d'etre plus dense que le reste du produit. Il n'a pas
// le droit d'etre illisible.
const tropPetit = [...style.matchAll(/font-size:\s*(0\.\d+)rem/g)]
  .map((m) => Number(m[1]))
  .filter((v) => v < 0.6875);
assert.deepEqual(tropPetit, [], `tailles sous le plancher de 11 px : ${tropPetit.join(", ")}`);
assert.match(style, /--sa-text-2xs: 0\.6875rem;/, "le plancher du systeme est 11 px");

// Un etat s'ecrit, un compte s'encadre : aucun badge d'etat ne doit
// reprendre un aplat de couleur, sinon un registre redevient une guirlande
// et la couleur cesse d'etre un signal.
assert.match(style, /\.badge \{[\s\S]{0,160}background: none;/,
  "un etat est un mot marque, pas une pastille pleine");
assert.match(style, /\.badge::before \{[\s\S]{0,120}border-radius: 1px;/,
  "la marque d'etat est carree : un rond se lit comme un voyant");

// Le compte du sommaire est un chiffre dans sa colonne. Un seul badge
// garde un fond dans toute l'application : celui pose sur l'icone de
// notifications, qui n'a pas de colonne ou vivre.
assert.match(style, /\.badge-count \{[\s\S]{0,220}font-variant-numeric: tabular-nums;/);
assert.match(style, /\.topbar-badge\.badge-count \{[\s\S]{0,220}background: var\(--sa-danger\)/);

console.log("OK - systeme-de-composition.test.mjs");
