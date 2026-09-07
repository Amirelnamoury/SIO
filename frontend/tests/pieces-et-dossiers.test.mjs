/* Les trois ecrans pilotes de la refonte : piece, dossier, qualification.
 *
 * Ce qu'ils demontrent, et donc ce qu'il faut proteger : le langage visuel
 * est commun (bande de reference, une action dominante, un etat qui
 * s'ecrit) mais les COMPOSITIONS different, parce que les missions
 * different. Un systeme qui produirait trois fois la meme page n'aurait
 * rien prouve.
 */
import assert from "node:assert/strict";
import * as sources from "./_sources.mjs";

const { socle, app, style } = sources;
const tout = sources.tout;

// ---------------------------------------------------------------------
// 1. La bande de reference : le meme objet partout
// ---------------------------------------------------------------------
// C'est la signature du produit, et elle vient du metier : dans le
// batiment, chaque piece porte un numero, et ce numero est ce qu'on dit
// au telephone. Il merite d'etre compose, pas range en gris dans un coin.
assert.match(socle, /function bandeReference\(/, "la bande est un helper partage, pas un gabarit recopie");
assert.match(style, /\.ref-bande-numero \{[\s\S]{0,320}font-variant-numeric: tabular-nums;/,
  "la reference est en chiffres tabulaires : on la lit en colonne et on la recopie");
assert.match(style, /\.ref-bande \{[\s\S]{0,200}position: sticky;/,
  "la reference ne defile pas : au milieu d'un devis de trente lignes, on doit savoir lequel");
// Les deux pieces l'emploient.
for (const piece of ["devis-detail-corps", "facture-detail-corps"]) {
  const debut = app.indexOf(`document.getElementById("${piece}").innerHTML`);
  assert.ok(debut !== -1, `${piece} est introuvable`);
  assert.match(app.slice(debut, debut + 1400), /bandeReference\(\{/, `${piece} doit ouvrir sur la bande de reference`);
}

// ---------------------------------------------------------------------
// 2. UNE action dominante, pas un rang de boutons
// ---------------------------------------------------------------------
// Le panneau alignait jusqu'a cinq boutons de meme poids - « Relancer »,
// « Telecharger le PDF », « Copier le lien client », « Dupliquer » - ce
// qui revient a n'en designer aucun.
assert.match(socle, /function actionsPiece\(/);
assert.match(socle, /const dominante = actions\.find\(\(x\) => x\.p\);/,
  "la dominante est celle que le metier marque, pas la premiere venue");
assert.doesNotMatch(app, /class="btn-sm\$\{x\.p \? " btn-sm-primary" : ""\}"/,
  "aucune piece ne doit revenir a un rang de boutons de meme poids");
assert.match(style, /\.piece-action-secondaire \{[\s\S]{0,300}background: none;/,
  "les actions secondaires sont du texte cliquable, pas des boutons");

// ---------------------------------------------------------------------
// 3. LE DOCUMENT domine sa piece
// ---------------------------------------------------------------------
assert.match(style, /\.piece \{[\s\S]{0,200}grid-template-columns: minmax\(0, 1fr\) 264px;/,
  "la feuille prend la place, le rail se range a cote");
// La seule ombre justifiee du produit : une piece est REELLEMENT posee
// sur le plan de travail. Partout ailleurs, ce sont les filets qui
// separent.
assert.match(style, /\.piece-feuille \{[\s\S]{0,300}box-shadow: var\(--sa-shadow-feuille\);/);
assert.match(style, /--sa-shadow-sm: none;/, "rien ne flotte par defaut");

// ---------------------------------------------------------------------
// 4. UN PROSPECT N'EST PAS UN CLIENT SANS CHIFFRES
// ---------------------------------------------------------------------
// Prospect et client sont le meme enregistrement, distingue par son
// statut - et le dossier les traitait a l'identique. Un prospect recu la
// semaine derniere ouvrait sur « Facture 0,00 € · Impaye — · Chantiers 0 ».
assert.match(app, /const estProspect = \(client\) => STADES_PROSPECT\.has\(client\.statut\);/);
assert.match(app, /function prospectQualificationHtml\(/);
assert.match(app, /function prospectBesoinHtml\(/);
assert.match(app, /function prospectProchaineActionHtml\(/);

// Les stades doivent couvrir TOUT ce qui n'est ni gagne ni perdu :
// un stade oublie ferait retomber ce prospect sur le dossier client.
const metaDebut = app.indexOf("const CLIENT_STATUT_META");
const metaFin = app.indexOf("};", metaDebut);
const stadesConnus = [...app.slice(metaDebut, metaFin).matchAll(/^\s{2}([a-z_]+):/gm)].map((m) => m[1]);
const stadesDebut = app.indexOf("const STADES_PROSPECT");
const stadesProspect = [...app.slice(stadesDebut, app.indexOf("]);", stadesDebut)).matchAll(/"([a-z_]+)"/g)].map((m) => m[1]);
for (const stade of stadesConnus) {
  if (stade === "gagne" || stade === "perdu") {
    assert.ok(!stadesProspect.includes(stade), `${stade} n'est plus un prospect`);
  } else {
    assert.ok(stadesProspect.includes(stade), `le stade ${stade} doit ouvrir la fiche de qualification`);
  }
}

// Le dossier annonce ce qu'il est.
assert.match(app, /estProspect\(client\) \? "Dossier prospect" : "Dossier client"/);
// Le potentiel ne s'affiche que s'il a ete estime : « Potentiel : 0 € »
// est un champ vide deguise en chiffre.
assert.match(app, /const potentiel = client\.montant_estime\s*\n?\s*\? fait\("Potentiel estimé"/);
// Une section « Affaires » vide n'apparait pas sur un prospect : il n'y a
// pas encore d'affaire, c'est la definition d'un prospect.
assert.match(app, /clientAAffaires\(clientId, chantiers, devis, factures\)\s*\n?\s*\? ficheSection\("Affaires"/);

// Aucun champ nouveau n'a ete invente : tout vient de ClientOut.
const clientOut = sources.backend("schemas.py");
for (const champ of ["notes", "source", "prochaine_action", "montant_estime", "probabilite"]) {
  assert.match(clientOut, new RegExp(`\\n    ${champ}:`), `${champ} doit deja exister dans ClientOut`);
}

// ---------------------------------------------------------------------
// 5. LE DOSSIER D'EXECUTION mene par ce qui vient, pas par ce que ca coute
// ---------------------------------------------------------------------
// Les chiffres de rentabilite occupaient le milieu du dossier, « Depenses
// 56 000,00 € » en grand, AVANT la liste des interventions : on ouvrait un
// chantier et on lisait sa comptabilite.
assert.match(app, /function prochaineInterventionHtml\(/);
const dossierDebut = app.indexOf('<div class="chantier-details dossier"');
const dossier = app.slice(dossierDebut, app.indexOf("</div>\n  </article>", dossierDebut));
assert.ok(dossierDebut !== -1, "le dossier de chantier est introuvable");
const rang = (titre) => dossier.indexOf(`saSection("${titre}"`);
for (const titre of ["Ce qui vient", "Interventions", "Documents et photos", "Dépenses et heures", "Historique"]) {
  assert.ok(rang(titre) !== -1, `section manquante : ${titre}`);
}
assert.ok(rang("Ce qui vient") < rang("Interventions"), "ce qui vient ouvre le dossier");
assert.ok(rang("Interventions") < rang("Dépenses et heures"),
  "les interventions passent avant la comptabilite : un chantier est un dossier d'execution");
assert.ok(rang("Dépenses et heures") < rang("Historique"));

// Les sous-rendus ne decident plus de leur mise en place : un composant
// qui produit sa propre boite ET son propre titre empeche toute
// recomposition - la fiche affichait deux fois chaque intitule.
for (const fonction of ["interventionsChantierHtml", "documentsChantierHtml"]) {
  const debut = app.indexOf(`function ${fonction}(`);
  const corps = app.slice(debut, app.indexOf("\n}", debut));
  assert.doesNotMatch(corps, /class="dash-section"/, `${fonction} ne doit plus poser sa propre boite`);
  assert.doesNotMatch(corps, /<h3/, `${fonction} ne doit plus poser son propre titre`);
}

// Rien ne s'affiche s'il n'y a aucune intervention a venir : une fiche
// qui ecrit « Prochaine intervention : aucune » fait du bruit avec du vide.
const prochaine = app.slice(app.indexOf("function prochaineInterventionHtml("));
assert.match(prochaine.slice(0, 1200), /if \(!suivante\) return "";/);

// Et le jeu d'essai doit pouvoir MONTRER cet etat : les deux
// interventions d'origine sont posees a une heure fixe de la journee,
// donc passees des que l'audit tourne l'apres-midi.
assert.match(sources.jeuEssai, /date_debut: `\$\{jg\(2\)\}T07:30:00\.000Z`/,
  "le jeu d'essai doit porter une intervention A VENIR, sinon l'etat est invisible");

// ---------------------------------------------------------------------
// 6. Les libelles de travail parlent la meme langue
// ---------------------------------------------------------------------
// Trente-quatre traitements pour le meme objet, avec neuf valeurs
// d'espacement differentes. Ce qui garde ses capitales : l'en-tete de
// colonne (convention du livre de comptes) et le sur-titre de page.
assert.doesNotMatch(style, /\.fiche-section-titre \{[^}]*text-transform: uppercase/);
assert.doesNotMatch(style, /\.kpi-card-label \{[^}]*text-transform: uppercase/);
assert.doesNotMatch(style, /\.fiche-chiffre-label \{[^}]*text-transform: uppercase/);
assert.doesNotMatch(style, /\.form-section-title \{[^}]*text-transform: uppercase/);
assert.ok((style.match(/text-transform: uppercase/g) || []).length <= 14,
  "les capitales espacees doivent rester l'exception, pas le traitement par defaut");

// Un bouton « Appeler » ne doit pas peser autant que le contexte qui
// l'entoure, ni que la seule action qui fait avancer l'affaire.
const actionsClient = app.slice(app.indexOf("function clientQuickActionsHtml("));
assert.match(actionsClient.slice(0, 1600), /piece-action-secondaire" href="tel:/);
assert.doesNotMatch(actionsClient.slice(0, 1600), /class="btn-sm" href="tel:/,
  "Appeler et Email redeviennent du texte cliquable");
assert.match(actionsClient.slice(0, 1600), /if \(!estProspect\(client\)\) \{/,
  "demander un avis a quelqu'un qui n'a rien achete n'a pas de sens");

console.log("OK - pieces-et-dossiers.test.mjs");
