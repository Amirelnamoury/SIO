import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const appPath = path.resolve(testDir, "..", "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

const feedbackStart = appSource.indexOf("function feedbackRelanceDevis");
const feedbackEnd = appSource.indexOf("async function withErrorToast", feedbackStart);
const renderStart = appSource.indexOf("function renderDevisCard");
const renderEnd = appSource.indexOf("async function showDevisForm", renderStart);
assert.ok(feedbackStart !== -1 && feedbackEnd > feedbackStart, "feedbackRelanceDevis est introuvable");
assert.ok(renderStart !== -1 && renderEnd > renderStart, "renderDevisCard est introuvable");

// La colonne « Suivi » est desormais calculee par devisSuivi(), qui
// exploite `date_consultation` - un champ que l'API renvoyait depuis
// toujours et que l'interface n'affichait nulle part.
const suiviStart = appSource.indexOf("function joursDepuis(");
const suiviEnd = appSource.indexOf("function devisKpiBandHtml(", suiviStart);
assert.ok(suiviStart !== -1 && suiviEnd > suiviStart, "les helpers de suivi sont introuvables");

let plan = "essentiel";
const plans = ["gratuit", "essentiel", "pro", "business"];
const context = {
  DEVIS_STATUT_META: {
    nouveau: { label: "Nouveau", badge: "badge-gray" },
    envoye: { label: "Envoyé", badge: "badge-blue" },
    consulte: { label: "Consulté", badge: "badge-blue" },
    signe: { label: "Signé", badge: "badge-green" },
    perdu: { label: "Perdu", badge: "badge-red" },
  },
  devisDueIds: new Set(),
  escapeHtml: (value) => String(value ?? ""),
  monogram: (value) => String(value || "?").slice(0, 2).toUpperCase(),
  fmtEuro: (value) => value == null ? null : `${value} €`,
  fmtDate: () => "29/08/2026",
  fmtDateCourte: () => "29 août",
  hasPlan: (minimum) => plans.indexOf(plan) >= plans.indexOf(minimum),
};
vm.runInNewContext(
  `${appSource.slice(suiviStart, suiviEnd)}\n${appSource.slice(feedbackStart, feedbackEnd)}\n${appSource.slice(renderStart, renderEnd)}\n`
    + "globalThis.__devisRelances = { feedbackRelanceDevis, renderDevisCard, devisSuivi };",
  context,
  { filename: appPath },
);

const { feedbackRelanceDevis, renderDevisCard, devisSuivi } = context.__devisRelances;

// ---------------------------------------------------------------------
// L'ETAT DE LECTURE D'UN DEVIS
// ---------------------------------------------------------------------
// Trois situations que l'ancienne colonne « Suivi » confondait toutes en
// « En attente de réponse » : jamais envoye, envoye mais jamais ouvert,
// ouvert et reste sans reponse. Ce sont pourtant trois gestes differents.
{
  const ilYA = (jours) => new Date(Date.now() - jours * 86400000).toISOString();
  const suivi = (extra) => devisSuivi({ statut: "envoye", nb_relances: 0, montant_ht: 100, ...extra }, false);

  assert.match(suivi({ date_envoi: ilYA(3), date_consultation: ilYA(1) }).texte, /^Lu hier/,
    "un devis ouvert doit dire quand il a ete lu");
  assert.equal(suivi({ date_envoi: ilYA(3), date_consultation: ilYA(1) }).cls, "is-success");

  const jamaisOuvert = suivi({ date_envoi: ilYA(12), date_consultation: null });
  assert.match(jamaisOuvert.texte, /Jamais ouvert · envoyé il y a 12 j/);
  assert.equal(jamaisOuvert.cls, "is-alerte",
    "au-dela d'une semaine sans ouverture, ce n'est plus de l'attente");

  assert.equal(suivi({ date_envoi: ilYA(2), date_consultation: null }).cls, "is-muted",
    "deux jours sans ouverture reste normal");

  assert.match(suivi({ date_envoi: ilYA(9), date_consultation: ilYA(2), nb_relances: 2 }).texte,
    /2 relances/, "le nombre de relances doit rester visible");

  assert.match(devisSuivi({ statut: "nouveau", montant_ht: null }, false).texte, /À chiffrer/);
  assert.match(devisSuivi({ statut: "nouveau", montant_ht: 100 }, false).texte, /Prêt à envoyer/);
  assert.match(devisSuivi({ statut: "envoye" }, true).texte, /Relance due aujourd'hui/,
    "une relance due passe avant tout le reste");
}
const base = {
  id: 42,
  client_nom: "Client test",
  titre: "Salle de bain",
  description: null,
  montant_ttc: 120,
  montant_ht: 100,
  remise_montant: null,
  numero: "DEV-0042",
  source: "manuel",
  token: "token-public-stable",
  lignes: [{ id: 1 }],
  nb_relances: 0,
  date_derniere_relance: null,
  relance_manuelle_possible: true,
};

for (const statut of ["envoye", "consulte"]) {
  plan = "essentiel";
  const html = renderDevisCard({ ...base, statut });
  assert.match(html, /data-action="relancer-devis"/, `Essentiel doit voir Relancer pour ${statut}`);
  assert.match(html, />Relancer<\/button>/, "le libellé doit rester clair");
  assert.match(html, /data-action="marquer-devis"/, "les actions signé/perdu doivent rester présentes");
  assert.match(html, /data-action="pdf-devis"/, "le téléchargement PDF doit rester présent");
  assert.match(html, /data-action="copier-lien-devis"/, "le lien client doit rester présent");
  assert.match(html, /data-action="dupliquer-devis"/, "la duplication doit rester présente");
  assert.match(html, /data-action="delete-devis"/, "l'archivage doit rester présent");
}

plan = "gratuit";
assert.doesNotMatch(renderDevisCard({ ...base, statut: "envoye" }), /data-action="relancer-devis"/);

plan = "essentiel";
for (const statut of ["nouveau", "signe", "perdu"]) {
  assert.doesNotMatch(
    renderDevisCard({ ...base, statut }),
    /data-action="relancer-devis"/,
    `le statut ${statut} ne doit pas proposer de relance`,
  );
}
assert.doesNotMatch(
  renderDevisCard({ ...base, statut: "consulte", relance_manuelle_possible: false }),
  /data-action="relancer-devis"/,
  "le bouton doit disparaître pendant le cooldown",
);

const succes = feedbackRelanceDevis({ email_statut: "envoye", message: "Relance envoyée par email." });
assert.equal(succes.message, "Relance envoyée par email.");
assert.equal(succes.isError, false);
const sansFournisseur = feedbackRelanceDevis({ email_statut: "non_configure", message: "Relance non envoyée." });
assert.equal(sansFournisseur.message, "Relance non envoyée.");
assert.equal(
  sansFournisseur.isError,
  true,
  "le frontend ne doit jamais présenter un fournisseur absent comme un succès",
);

console.log("OK - devis-relances.test.mjs");
