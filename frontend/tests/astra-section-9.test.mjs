/* Les écarts §9 corrigés, figés.
 *
 * Chacun de ces défauts avait la même forme : un chiffre exact, présenté de
 * telle manière qu'il dit autre chose que ce qu'il compte. Ils ne lèvent
 * aucune erreur et ne se voient pas à la relecture du code.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appPath = path.join(frontendDir, "app.js");
const appSource = fs.readFileSync(appPath, "utf8");
const dashboardPy = fs.readFileSync(path.resolve(frontendDir, "..", "backend", "app", "routers", "dashboard.py"), "utf8");

// ---------------------------------------------------------------------
// §9-1 — « Aucun score opaque »
// ---------------------------------------------------------------------
// Le serveur calcule toujours score_global : on ne touche pas au contrat
// d'API. Mais c'était la moyenne arithmétique de cinq échelles sans unité
// commune (un taux de signature, une part de montant, une pénalité de 25
// points par document expiré...). « 72/100 » ne désignait aucun fait.
assert.match(dashboardPy, /score_global = round\(sum\(valeurs\) \/ len\(valeurs\)\)/,
  "le serveur calcule bien une moyenne — c'est précisément pourquoi elle ne s'affiche plus");

const santeDebut = appSource.indexOf("const SANTE_MESURES");
const santeFin = appSource.indexOf("function activationChecklistHtml");
assert.ok(santeDebut !== -1 && santeFin > santeDebut, "le bloc santé est introuvable");
const santeSource = appSource.slice(santeDebut, santeFin);
// On juge sur le RENDU, pas sur le texte du fichier : le commentaire qui
// explique le retrait cite forcément le nom de ce qui a été retiré.

const contexteSante = { escapeHtml: (v) => String(v ?? "") };
vm.runInNewContext(`${santeSource}\nglobalThis.__s = { santeWidgetHtml, santeMesure };`, contexteSante, { filename: appPath });
const { santeWidgetHtml, santeMesure } = contexteSante.__s;

// Les libellés arrivent du serveur SANS accents : « Tresorerie », « Conformite ».
for (const [label, attendu] of [
  ["Commercial", "devis signés parmi les devis décidés"],
  ["Tresorerie", "part du montant à encaisser qui n'est pas en retard"],
  ["Trésorerie", "part du montant à encaisser qui n'est pas en retard"],
  ["Chantiers", "chantiers qui tiennent leur budget"],
  ["Conformite", "25 points retirés par document expiré ou proche de l'échéance"],
  ["Organisation", "tâches à échéance qui ne sont pas en retard"],
]) {
  assert.equal(santeMesure(label), attendu, `« ${label} » doit dire ce qu'il mesure`);
}
assert.equal(santeMesure("Inconnu"), "", "un libellé inattendu n'invente pas d'explication");

const sante = {
  score_global: 72,
  commercial: { label: "Commercial", valeur: 68 },
  tresorerie: { label: "Tresorerie", valeur: 31 },
  chantiers: { label: "Chantiers", valeur: 80 },
  conformite: { label: "Conformite", valeur: null, raison_absence: "Aucune information de conformité enregistrée" },
  organisation: { label: "Organisation", valeur: 42 },
};
const html = santeWidgetHtml(sante);
assert.doesNotMatch(html, /72/, "le score global ne doit apparaître nulle part");
assert.doesNotMatch(html, /Score global/, "ni son intitulé");
assert.doesNotMatch(html, /sante-score-global/, "ni son conteneur");
assert.match(html, /68\/100/, "les mesures réelles restent");
assert.match(html, /devis signés parmi les devis décidés/, "et disent ce qu'elles comptent");
assert.match(html, /Aucune information de conformité enregistrée/,
  "une mesure impossible garde sa raison, elle ne vaut pas zéro");

// ---------------------------------------------------------------------
// §9-14 — pas de pourcentage entre deux populations différentes
// ---------------------------------------------------------------------
const vue = appSource.slice(appSource.indexOf("async function loadStatistiques"), appSource.indexOf("// ===================== Avis clients"));
assert.match(vue, /label: "Devis créés", nb: a\.nb_devis_total, population: "devis"/);
assert.match(vue, /label: "Devis signés", nb: a\.nb_devis_signes, population: "devis"/);
assert.match(vue, /label: "Clients acquis", nb: a\.nb_clients_acquis, population: "clients"/);
assert.match(vue, /precedent\.population === etape\.population/,
  "le taux ne se calcule qu'entre deux étapes qui comptent la même chose");
// 18 clients rapportés à 21 devis signés donnaient « 86 % ». Deux ensembles
// différents : le nombre seul reste utile, le pourcentage ne veut rien dire.
assert.doesNotMatch(vue, /const conversion = i > 0 && precedent && etape\.nb <= precedent$/m);

// ---------------------------------------------------------------------
// §9-12 — une tâche sans échéance n'est pas « plus tard »
// ---------------------------------------------------------------------
const tachesDebut = appSource.indexOf("const TACHE_GROUPE_LABELS");
const tachesFin = appSource.indexOf("function tacheEcheanceMeta");
const contexteTaches = {};
vm.runInNewContext(
  `${appSource.slice(tachesDebut, tachesFin)}\nglobalThis.__t = { tacheGroupe, TACHE_GROUPE_ORDRE, TACHE_GROUPE_LABELS };`,
  contexteTaches, { filename: appPath },
);
const { tacheGroupe, TACHE_GROUPE_ORDRE, TACHE_GROUPE_LABELS } = contexteTaches.__t;

const jour = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
assert.equal(tacheGroupe({ echeance: null, statut: "a_faire" }), "sans_date",
  "sans échéance, une tâche ne peut pas être rangée dans un futur qu'elle n'a pas");
assert.equal(tacheGroupe({ echeance: undefined, statut: "a_faire" }), "sans_date");
assert.equal(tacheGroupe({ echeance: jour(-2), statut: "a_faire" }), "en_retard");
assert.equal(tacheGroupe({ echeance: jour(0), statut: "a_faire" }), "aujourdhui");
assert.equal(tacheGroupe({ echeance: jour(3), statut: "a_faire" }), "cette_semaine");
assert.equal(tacheGroupe({ echeance: jour(30), statut: "a_faire" }), "plus_tard");
// Une tâche faite ne réclame plus rien : elle quitte la file des échéances.
assert.equal(tacheGroupe({ echeance: jour(-2), statut: "faite" }), "plus_tard");
assert.ok(TACHE_GROUPE_ORDRE.includes("sans_date"), "le groupe doit être affichable");
assert.equal(TACHE_GROUPE_LABELS.sans_date, "Sans date");
assert.equal(TACHE_GROUPE_ORDRE.indexOf("sans_date"), TACHE_GROUPE_ORDRE.length - 1,
  "sans date vient en dernier : ces tâches n'ont pas d'urgence à revendiquer");

// ---------------------------------------------------------------------
// §9-6 — avertissement avant abandon d'un devis
// ---------------------------------------------------------------------
const empDebut = appSource.indexOf("function empreinteFormulaire");
const empFin = appSource.indexOf("\n}", appSource.indexOf("function devisFormModifie")) + 2;
const contexteForm = {};
vm.runInNewContext(
  `${appSource.slice(empDebut, empFin)}\nglobalThis.__f = { empreinteFormulaire, devisFormModifie };`,
  contexteForm, { filename: appPath },
);
const { empreinteFormulaire, devisFormModifie } = contexteForm.__f;

const champ = (id, value, type = "text") => ({ id, value, type, checked: false });
const faireConteneur = (champs) => ({ champs, dataset: {}, querySelectorAll: () => champs });

// Un formulaire NEUF porte déjà des valeurs par défaut (TVA, acompte) : elles
// ne sont pas une saisie. C'est le piège de la première version, qui aurait
// réclamé une confirmation sur un formulaire auquel personne n'avait touché.
const conteneur = faireConteneur([champ("df-titre", ""), champ("df-tva", "10", "number"), champ("df-acompte", "30", "number")]);
conteneur.dataset.empreinte = empreinteFormulaire(conteneur);
assert.equal(devisFormModifie(conteneur), false, "un formulaire non touché ne doit rien demander");

conteneur.champs[0].value = "Rénovation salle de bain";
assert.equal(devisFormModifie(conteneur), true, "une saisie réelle doit être protégée");

// Revenir à l'état initial n'est plus une modification.
conteneur.champs[0].value = "";
assert.equal(devisFormModifie(conteneur), false);

// Ajouter une ligne change l'empreinte : c'est exactement ce qu'on protège.
conteneur.champs.push(champ("ligne-2-desc", ""));
assert.equal(devisFormModifie(conteneur), true, "une ligne ajoutée compte comme une saisie");

// Sans empreinte de départ, on ne bloque jamais : mieux vaut ne rien demander
// que d'inventer une modification.
assert.equal(devisFormModifie(faireConteneur([])), false);

// ---------------------------------------------------------------------
// §9-9 — une marge incomplète est annoncée comme telle
// ---------------------------------------------------------------------
const bandeDebut = appSource.indexOf("function chantiersKpiBandHtml");
const bande = appSource.slice(bandeDebut, bandeDebut + 2600);
assert.match(bande, /acc\.mesures \+= 1/, "les marges réelles doivent être comptées à part");
assert.match(bande, /acc\.estimes \+= 1/, "les marges estimées aussi");
assert.match(bande, /encore estimé/, "un total mixte doit dire ce qu'il contient");
assert.match(bande, /marge réelle/, "un total entièrement mesuré doit pouvoir se nommer");

// ---------------------------------------------------------------------
// §9-11 — une entrée dérivée ouvre sa source
// ---------------------------------------------------------------------
assert.match(appSource, /item\.type === "tache" \|\| PLANNING_TYPES_EVENEMENT\.has\(item\.type\)/,
  "un chip de tâche doit être cliquable dans le planning");
assert.match(appSource, /else if \(item && item\.type === "tache"\) ouvrirTacheDepuisPlanning/);
assert.match(appSource, /data-tache-id="\$\{t\.id\}"/, "la ligne de tâche doit être adressable dans le DOM");
assert.match(appSource, /Cette tâche n'apparaît pas dans la liste affichée/,
  "une tâche masquée par un filtre doit être signalée, pas ignorée");

// ---------------------------------------------------------------------
// §9-1 — chaque ligne « À faire » expose son échéance
// ---------------------------------------------------------------------
const groupes = appSource.slice(appSource.indexOf("const taskGroupes = ["), appSource.indexOf("const prioriteItems"));
assert.match(groupes, /échéance \$\{f\.date_echeance \? fmtDate\(f\.date_echeance\) : "non fixée"\}/,
  "une facture en retard doit montrer la date dépassée");
assert.match(groupes, /envoyé le \$\{fmtDate\(dv\.date_envoi\)\}/, "un devis à relancer doit dire depuis quand il attend");
assert.match(groupes, /t\.echeance \? `échéance \$\{fmtDate\(t\.echeance\)\}` : "sans échéance"/);

// ---------------------------------------------------------------------
// §9-2 — la liste de travail est la vue principale de Prospects
// ---------------------------------------------------------------------
// Le pipeline repond a « comment se repartit mon commerce », question de
// bilan. La question du matin est « qui dois-je rappeler » : elle se lit sur
// une liste ordonnee par l'anciennete du dernier mouvement.
assert.match(appSource, /let prospectsMode = "travail"/, "la liste de travail doit etre le mode par defaut");
assert.match(appSource, /function prospectsTravailHtml/);
assert.match(appSource, /const enTravail = prospectsMode === "travail"/);
const indexSource = fs.readFileSync(path.join(frontendDir, "index.html"), "utf8");
assert.match(indexSource, /id="prospects-travail"/, "la liste doit avoir son conteneur");
assert.match(indexSource, /<div class="kanban" id="clients-kanban" hidden>/,
  "le pipeline demarre masque : c'est la liste qui s'ouvre en premier");
// `display: flex` bat l'attribut hidden : sans cette regle les deux vues
// s'affichaient l'une sous l'autre, defaut vu a l'ecran avant correction.
const styleSource = fs.readFileSync(path.join(frontendDir, "style.css"), "utf8");
assert.match(styleSource, /\.kanban\[hidden\], \.list\[hidden\] \{ display: none; \}/,
  "masquer un conteneur en flex demande une regle explicite");

// ---------------------------------------------------------------------
// §9-21 — la photo est celle de l'entreprise, pas de la personne
// ---------------------------------------------------------------------
// Artisan.photo_url appartient a l'entreprise : la montrer sous « Mon profil »
// ferait croire a un salarie qu'il regarde la sienne.
assert.match(appSource, /Photo de \$\{entreprise\}/, "le texte de remplacement doit nommer l'entreprise");
assert.match(indexSource, /alt="Photo de l'entreprise"/);
assert.match(indexSource, /Cette photo représente l'entreprise/,
  "le formulaire doit dire qu'elle est commune a toute l'entreprise");
assert.doesNotMatch(indexSource, /aria-label="Mon profil"/, "l'intitule ne doit plus promettre un profil personnel");

// ---------------------------------------------------------------------
// §9-22 — une notification dit pourquoi elle apparait
// ---------------------------------------------------------------------
const raisons = appSource.slice(appSource.indexOf("const NOTIFICATION_RAISONS"), appSource.indexOf("const NOTIFICATION_TYPE_LABELS"));
for (const type of ["devis_relance", "facture_relance", "conformite", "message_client", "nouvelle_demande_devis"]) {
  assert.match(raisons, new RegExp(`${type}:`), `le type ${type} doit expliquer sa presence`);
}
assert.match(appSource, /NOTIFICATION_RAISONS\[n\.type\]/, "la raison doit etre rendue sur la ligne");
// La phrase decrit la regle REELLE du serveur, pas une paraphrase inventee.
const conformitePy = fs.readFileSync(path.resolve(frontendDir, "..", "backend", "app", "routers", "conformite.py"), "utf8");
assert.match(conformitePy, /SEUIL_ALERTE_JOURS = 30/,
  "la phrase annonce 30 jours : ce seuil doit rester celui du serveur");

console.log("OK - astra-section-9.test.mjs");
