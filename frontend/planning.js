/* =====================================================================
   PLANNING — la grille horaire, les durees, le glisser-deposer
   ---------------------------------------------------------------------
   Troisieme decoupage de app.js par domaine (Astra §16). Meme regle que
   les precedents : aucune ligne reecrite, seulement deplacee. Voir
   docs/DECOUPAGE-FRONTEND.md.

   Le domaine le plus autonome du produit : il ne parle que du planning et
   de ses trois vues (jour, semaine, mois). Il porte notamment la regle des
   TROIS NIVEAUX DE CERTITUDE - duree connue, debut seul, aucune heure -
   qui empeche la grille d'affirmer une occupation que personne n'a saisie.

   Charge APRES navigation.js et AVANT app.js (voir index.html).
   ===================================================================== */

// ===================== Planning (calendrier jour/semaine/mois, drag & drop reel) =====================
const PLANNING_TYPE_LABELS = { rdv: "RDV", visite: "Visite", intervention: "Intervention", autre: "Autre", tache: "Tâche", chantier_debut: "Début chantier" };
const PLANNING_TYPE_CLASS = { rdv: "planning-item-blue", visite: "planning-item-blue", intervention: "planning-item-orange", autre: "planning-item-gray", tache: "planning-item-gray", chantier_debut: "planning-item-green" };

let planningViewMode = "semaine"; // jour | semaine | mois
let planningAnchorDate = new Date();

// Filtres (recherche + type/client/chantier) : purement client, appliques
// sur les items deja recus par Api.planning() pour la periode affichee -
// aucun nouvel appel reseau au changement de filtre, seulement un nouveau
// rendu depuis planningItemsCache. La periode courante est memorisee pour
// pouvoir re-rendre sans refaire un aller-retour serveur.
let planningFilters = { q: "", type: "", clientId: "", chantierId: "" };
let planningRangeDebut = null;
let planningRangeFin = null;
let planningChantiersCache = [];

function planningFilterItems(items) {
  const q = planningFilters.q.trim().toLowerCase();
  return items.filter((i) => {
    if (planningFilters.type && i.type !== planningFilters.type) return false;
    if (planningFilters.clientId && String(i.client_id || "") !== planningFilters.clientId) return false;
    if (planningFilters.chantierId && String(i.chantier_id || "") !== planningFilters.chantierId) return false;
    if (q && !`${i.titre} ${i.lieu || ""}`.toLowerCase().includes(q)) return false;
    return true;
  });
}

function planningFiltersHtml() {
  const typeOptions = Object.entries(PLANNING_TYPE_LABELS)
    .map(([v, l]) => `<option value="${v}" ${planningFilters.type === v ? "selected" : ""}>${escapeHtml(l)}</option>`)
    .join("");
  const clientOptions = clientsCache
    .map((c) => `<option value="${c.id}" ${planningFilters.clientId === String(c.id) ? "selected" : ""}>${escapeHtml(c.nom)}</option>`)
    .join("");
  const chantierOptions = planningChantiersCache
    .map((c) => `<option value="${c.id}" ${planningFilters.chantierId === String(c.id) ? "selected" : ""}>${escapeHtml(c.titre)}</option>`)
    .join("");
  return `
    <div class="planning-filters">
      <input type="text" id="planning-filtre-q" placeholder="Rechercher un client, chantier..." value="${escapeHtml(planningFilters.q)}">
      <select id="planning-filtre-type"><option value="">Type</option>${typeOptions}</select>
      <select id="planning-filtre-client"><option value="">Client</option>${clientOptions}</select>
      <select id="planning-filtre-chantier"><option value="">Chantier</option>${chantierOptions}</select>
    </div>`;
}

function renderPlanningFiltered() {
  renderPlanning(planningRangeDebut, planningRangeFin, planningFilterItems(planningItemsCache));
}

// Fuseau fixe (pas le fuseau ambiant du navigateur) : la cle "jour" d'une
// date doit rester la meme quel que soit le fuseau systeme de la machine qui
// affiche l'ecran, et gerer automatiquement le passage heure d'ete/hiver
// (Intl/IANA, jamais un decalage +1/+2 code en dur). Avant ce correctif,
// planningToIso() faisait d.toISOString().slice(0, 10) : ca convertit en UTC
// avant de lire la date, donc un evenement cree a 09:00 a Paris (UTC+2 l'ete)
// finissait range sur la case du jour suivant dans la grille - exactement le
// bug "29/08 09:00 affiche 30/08 07:00" remonte par le test manuel.
const PLANNING_TIMEZONE = "Europe/Paris";
const _planningIsoFormatter = new Intl.DateTimeFormat("en-CA", {
  timeZone: PLANNING_TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
});
function planningToIso(d) {
  return _planningIsoFormatter.format(d);
}
function planningHeureLocale(d) {
  return new Date(d).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", timeZone: PLANNING_TIMEZONE });
}
// Decompose une date/heure en {date:"YYYY-MM-DD", heure:"HH:MM"} tels
// qu'ils doivent apparaitre dans les <input type="date">/<input type="time">
// du formulaire, evalues en Europe/Paris (jamais le fuseau ambiant) - sert a
// pre-remplir le formulaire d'edition avec exactement ce que l'artisan a
// saisi a la creation.
function planningDateHeureLocale(dateInput) {
  const d = new Date(dateInput);
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: PLANNING_TIMEZONE, hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d);
  const get = (t) => parts.find((p) => p.type === t)?.value || "00";
  return { date: planningToIso(d), heure: `${get("hour")}:${get("minute")}` };
}
// Inverse de planningDateHeureLocale() : convertit une date/heure saisie
// dans le formulaire (valeurs des <input type="date"/"time">, donc une heure
// murale en Europe/Paris) en instant UTC. `new Date(\`${date}T${heure}:00\`)`
// est ambigu : sans suffixe de fuseau, le moteur JS l'interprete dans le
// fuseau AMBIANT de la machine qui l'execute (navigateur ou environnement de
// test), pas forcement Europe/Paris - d'ou le decalage observe uniquement a
// la modification (la machine de test n'est pas forcement a l'heure de
// Paris). On calcule l'instant UTC explicitement : une premiere estimation
// naive, puis on lit comment cet instant s'affiche reellement en
// Europe/Paris via Intl et on corrige l'ecart. Fonctionne quel que soit le
// fuseau de la machine et gere nativement ete/hiver (jamais de +1h/+2h code
// en dur).
function planningLocalToUtcIso(dateStr, heureStr) {
  const [annee, mois, jour] = dateStr.split("-").map(Number);
  const [heure, minute] = heureStr.split(":").map(Number);
  const estimation = Date.UTC(annee, mois - 1, jour, heure, minute, 0);
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: PLANNING_TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  }).formatToParts(new Date(estimation));
  const get = (t) => parseInt(parts.find((p) => p.type === t)?.value || "0", 10);
  const afficheCommeUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour") % 24, get("minute"), get("second"));
  return new Date(estimation - (afficheCommeUtc - estimation)).toISOString();
}

function planningStartOfWeek(d) {
  const date = new Date(d);
  const jour = date.getDay(); // 0 = dimanche
  const decalage = jour === 0 ? -6 : 1 - jour; // lundi = premier jour
  date.setDate(date.getDate() + decalage);
  date.setHours(0, 0, 0, 0);
  return date;
}

function planningRange() {
  const anchor = new Date(planningAnchorDate);
  anchor.setHours(0, 0, 0, 0);
  if (planningViewMode === "jour") return [new Date(anchor), new Date(anchor)];
  if (planningViewMode === "semaine") {
    const debut = planningStartOfWeek(anchor);
    const fin = new Date(debut);
    fin.setDate(fin.getDate() + 6);
    return [debut, fin];
  }
  const premier = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const dernier = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0);
  const debut = planningStartOfWeek(premier);
  const fin = planningStartOfWeek(dernier);
  fin.setDate(fin.getDate() + 6);
  return [debut, fin];
}

function planningShift(direction) {
  const d = new Date(planningAnchorDate);
  if (planningViewMode === "jour") d.setDate(d.getDate() + direction);
  else if (planningViewMode === "semaine") d.setDate(d.getDate() + direction * 7);
  else d.setMonth(d.getMonth() + direction);
  return d;
}

function planningToolbarHtml(debut, fin) {
  const label = planningViewMode === "jour"
    ? debut.toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
    : planningViewMode === "semaine"
      ? `${debut.toLocaleDateString("fr-FR", { day: "numeric", month: "short" })} – ${fin.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" })}`
      : planningAnchorDate.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
  return `
    <div class="planning-toolbar">
      <div class="planning-nav">
        <button type="button" class="btn-sm" data-action="planning-prev">&larr;</button>
        <button type="button" class="btn-sm" data-action="planning-today">Aujourd'hui</button>
        <button type="button" class="btn-sm" data-action="planning-next">&rarr;</button>
        <strong class="planning-label">${escapeHtml(label)}</strong>
      </div>
      <div class="planning-modes">
        ${["jour", "semaine", "mois"].map((m) => `<button type="button" class="btn-sm ${planningViewMode === m ? "btn-sm-primary" : ""}" data-action="planning-mode" data-mode="${m}">${m[0].toUpperCase()}${m.slice(1)}</button>`).join("")}
      </div>
    </div>`;
}

function planningItemChip(item, compact) {
  // Une echeance de tache affichait « 09:00 » en vue mois : c'est l'ancre de
  // tri du serveur, pas une heure saisie. Les items sans heure n'en montrent
  // donc aucune, ici comme sur la grille horaire.
  const duree = planningDureeMinutes(item);
  const heure = planningSansHeure(item)
    ? ""
    : `<span class="planning-item-heure">${planningHeureLocale(item.date)}${duree !== null ? `–${planningHeureLocale(item.date_fin)}` : ""}</span> `;
  // La tache aussi ouvre sa source : c'est une echeance affichee ici, elle
  // existe ailleurs. Une entree derivee qui ne mene pas a son origine oblige a
  // retrouver la tache a la main dans une autre vue.
  const ouvreFiche = item.type === "chantier_debut" || item.type === "tache" || PLANNING_TYPES_EVENEMENT.has(item.type);
  return `<div class="planning-item ${PLANNING_TYPE_CLASS[item.type] || ""} ${ouvreFiche ? "planning-item-clickable" : ""}" draggable="${item.type === "chantier_debut" ? "false" : "true"}" data-type="${item.type}" data-ref-id="${item.reference_id}" data-current-date="${item.date}" ${ouvreFiche ? 'role="button" tabindex="0"' : ""} title="${escapeHtml(item.titre)}">
    ${compact ? "" : heure}<span class="planning-item-titre">${escapeHtml(item.titre)}</span>
  </div>`;
}

// Grille horaire (vues jour/semaine) : la vue "brief" precedente empilait les
// evenements du haut vers le bas sans notion d'heure, ce qui laissait la
// quasi-totalite de la colonne vide des qu'un jour avait 0-2 rendez-vous.
// Ici chaque evenement est positionne a sa vraie heure sur un axe 7h-20h.
//
// TROIS ETATS, PARCE QU'IL Y A TROIS NIVEAUX DE CERTITUDE
// La version precedente dessinait un bloc d'UNE HEURE pour tout : un
// rendez-vous, une echeance de tache, un debut de chantier. La grille
// affirmait donc une occupation que personne n'avait saisie - un artisan
// pouvait y lire « mon mardi matin est pris » sur la foi d'une constante.
//   1. Duree connue (PlanningItem.date_fin) : bloc a la hauteur reelle.
//   2. Debut connu, fin inconnue : un marqueur fin, pose a l'heure exacte.
//      Il dit « ca commence a 9h », pas « ca dure une heure ».
//   3. Aucune heure (echeance de tache, debut de chantier) : hors de l'axe,
//      dans une bande « Sans heure » en tete de journee. Le 9h00/8h00 que
//      renvoie l'API pour ces items est une ancre de tri, pas un horaire.
const PLANNING_HOUR_START = 7;
const PLANNING_HOUR_END = 20; // 13h affichees ; les items hors plage restent visibles, ancres au bord.
const PLANNING_ROW_H = 41; // px par heure - garder synchronise avec les hauteurs CSS.
const PLANNING_MARQUEUR_H = 19; // hauteur du marqueur "debut sans fin connue"
const PLANNING_BLOC_MIN_H = 20; // un bloc de 15 min doit rester lisible
const PLANNING_BANDE_LIGNE_H = 22; // hauteur d'un chip dans la bande "Sans heure"
const PLANNING_BANDE_MAX_LIGNES = 3;

// Durees proposees au formulaire. « Non precisee » est la premiere valeur et
// la valeur par defaut : le produit n'invente pas un creneau que l'artisan
// n'a pas saisi. Une duree deja enregistree qui ne figure pas dans la liste
// (rendez-vous cree ailleurs, ou liste modifiee depuis) est ajoutee telle
// quelle, sinon la rouvrir en edition l'effacerait silencieusement.
const PLANNING_DUREES = [
  { minutes: "", label: "Non précisée" },
  { minutes: "15", label: "15 min" },
  { minutes: "30", label: "30 min" },
  { minutes: "60", label: "1 h" },
  { minutes: "90", label: "1 h 30" },
  { minutes: "120", label: "2 h" },
  { minutes: "180", label: "3 h" },
  { minutes: "240", label: "Demi-journée (4 h)" },
  { minutes: "480", label: "Journée (8 h)" },
];

function planningDureeLabel(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (!h) return `${m} min`;
  return m ? `${h} h ${String(m).padStart(2, "0")}` : `${h} h`;
}

function planningDureeOptionsHtml(dureeVal) {
  const liste = PLANNING_DUREES.some((d) => d.minutes === dureeVal) || dureeVal === ""
    ? PLANNING_DUREES
    : [...PLANNING_DUREES, { minutes: dureeVal, label: planningDureeLabel(Number(dureeVal)) }];
  return liste
    .map((d) => `<option value="${d.minutes}"${d.minutes === dureeVal ? " selected" : ""}>${escapeHtml(d.label)}</option>`)
    .join("");
}

// Ces deux types n'ont pas d'heure : une tache a une echeance (un jour), un
// chantier a une date de debut (un jour). Voir routers/planning.py, qui leur
// donne 9h00 et 8h00 uniquement pour pouvoir trier la liste.
function planningSansHeure(item) {
  return item.type === "tache" || item.type === "chantier_debut";
}

// Duree reelle en minutes, ou null si la fin n'est pas renseignee. Une fin
// anterieure ou egale au debut est traitee comme inconnue plutot que comme
// une duree nulle : c'est une donnee aberrante, pas une information.
function planningDureeMinutes(item) {
  if (!item.date_fin) return null;
  const minutes = Math.round((new Date(item.date_fin) - new Date(item.date)) / 60000);
  return minutes > 0 ? minutes : null;
}

function planningTimeMinutes(dateVal) {
  const { heure } = planningDateHeureLocale(dateVal);
  const [h, m] = heure.split(":").map(Number);
  return h * 60 + m;
}

function planningHourRowsHtml() {
  let html = "";
  for (let h = PLANNING_HOUR_START; h < PLANNING_HOUR_END; h++) html += '<div class="planning-hour-row"></div>';
  return html;
}

function planningHourGutterHtml(bande = false) {
  let html = '<div class="planning-hour-gutter"><div class="planning-hour-gutter-spacer"></div>';
  // La gouttiere doit reserver exactement la meme bande que les colonnes,
  // sinon les reglures ne tombent plus en face des heures.
  if (bande) html += '<div class="planning-jour-bande planning-jour-bande-libelle">Sans heure</div>';
  for (let h = PLANNING_HOUR_START; h < PLANNING_HOUR_END; h++) html += `<div class="planning-hour-label">${h}h</div>`;
  return html + "</div>";
}

function planningNowLineHtml() {
  const minutes = planningTimeMinutes(new Date());
  if (minutes < PLANNING_HOUR_START * 60 || minutes > PLANNING_HOUR_END * 60) return "";
  const top = ((minutes - PLANNING_HOUR_START * 60) / 60) * PLANNING_ROW_H;
  return `<div class="planning-now-line" style="top:${top}px;"><span class="planning-now-dot"></span></div>`;
}

// Attribue une colonne a chaque item par ordre chronologique (chevauchements
// rares pour un artisan seul sur son planning) : algorithme glouton simple,
// pas de vrai decoupage par cluster - un item tardif isole peut partager une
// largeur reduite avec un chevauchement plus tot dans la meme journee, cas
// limite juge acceptable au vu de la frequence.
function planningLayoutDay(dayItems) {
  // Emprise du marqueur convertie en minutes : elle sert UNIQUEMENT a ne pas
  // superposer deux marqueurs voisins. Ce n'est pas une duree supposee.
  const empriseMarqueur = Math.ceil((PLANNING_MARQUEUR_H / PLANNING_ROW_H) * 60);
  const columns = [];
  const placed = dayItems.map((item) => {
    const start = planningTimeMinutes(item.date);
    const duree = planningDureeMinutes(item);
    const emprise = duree !== null ? duree : empriseMarqueur;
    let col = columns.findIndex((endTime) => endTime <= start);
    if (col === -1) { col = columns.length; columns.push(start + emprise); }
    else columns[col] = start + emprise;
    return { item, start, duree, col };
  });
  const totalCols = Math.max(1, columns.length);
  return placed.map((p) => ({ ...p, totalCols }));
}

function planningPositionedItemHtml({ item, start, duree, col, totalCols }) {
  const hauteurAxe = (PLANNING_HOUR_END - PLANNING_HOUR_START) * PLANNING_ROW_H;
  const hauteur = duree !== null
    ? Math.max(PLANNING_BLOC_MIN_H, (duree / 60) * PLANNING_ROW_H - 2)
    : PLANNING_MARQUEUR_H;
  const top = Math.min(Math.max(0, ((start - PLANNING_HOUR_START * 60) / 60) * PLANNING_ROW_H), hauteurAxe - hauteur);
  const widthPct = 100 / totalCols;
  const ouvreFiche = PLANNING_TYPES_EVENEMENT.has(item.type);
  // Un creneau borne s'annonce en toutes lettres ; un debut seul ne montre
  // que son heure de debut, sans tiret qui laisserait croire a une fin.
  const heure = duree !== null
    ? `${planningHeureLocale(item.date)} – ${planningHeureLocale(item.date_fin)}`
    : planningHeureLocale(item.date);
  const infobulle = duree !== null
    ? `${item.titre} · ${heure}`
    : `${item.titre} · commence à ${heure}, fin non renseignée`;
  // Sous ~30 px, deux lignes ne tiennent pas : l'heure et le titre passent
  // cote a cote plutot que le titre soit rogne a l'invisible.
  const forme = duree === null ? "est-marqueur" : hauteur < 30 ? "est-borne est-court" : "est-borne";
  return `<div class="planning-item planning-item-positioned ${forme} ${PLANNING_TYPE_CLASS[item.type] || ""} ${ouvreFiche ? "planning-item-clickable" : ""}"
    style="top:${top}px; height:${hauteur}px; left:calc(${col * widthPct}% + 2px); width:calc(${widthPct}% - 4px);"
    draggable="true" data-type="${item.type}" data-ref-id="${item.reference_id}" data-current-date="${item.date}"
    ${ouvreFiche ? 'role="button" tabindex="0"' : ""} title="${escapeHtml(infobulle)}"><span class="planning-item-heure">${escapeHtml(heure)}</span> <span class="planning-item-titre">${escapeHtml(item.titre)}</span></div>`;
}

// Hauteur reservee a la bande « Sans heure », identique pour toute la grille :
// la gouttiere des heures et les colonnes de jour la lisent depuis la meme
// variable CSS, sinon les reglures se decaleraient d'une colonne a l'autre.
function planningBandeHauteur(jours, items) {
  const maxParJour = jours.reduce((max, jour) => {
    const iso = planningToIso(jour);
    const n = items.filter((i) => planningSansHeure(i) && planningToIso(new Date(i.date)) === iso).length;
    return Math.max(max, n);
  }, 0);
  if (maxParJour === 0) return 0;
  return Math.min(maxParJour, PLANNING_BANDE_MAX_LIGNES) * PLANNING_BANDE_LIGNE_H + 6;
}

function planningDayCellHtml(dateObj, items, { compact = false, showWeekday = true, extraClass = "", hourGrid = false, bande = false } = {}) {
  const iso = planningToIso(dateObj);
  // Comparaison sur la cle "jour" calculee en Europe/Paris des deux cotes
  // (jamais un slice(0,10) direct de la chaine UTC renvoyee par l'API) :
  // voir le commentaire de planningToIso() pour le bug que ca evite.
  const dayItems = items.filter((i) => planningToIso(new Date(i.date)) === iso).sort((a, b) => a.date.localeCompare(b.date));
  const isToday = iso === planningToIso(new Date());
  // Samedi/dimanche : marques ici plutot que par un nth-child cote CSS,
  // car les trois vues n'ont pas la meme structure de grille (le gutter
  // des heures occupe la premiere colonne en vue jour/semaine, sept
  // en-tetes precedent les cases en vue mois) - un calcul de position y
  // serait faux a la premiere evolution.
  const jourSemaine = dateObj.getDay();
  const isWeekend = jourSemaine === 0 || jourSemaine === 6;
  const headerLabel = showWeekday
    ? dateObj.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric" })
    : String(dateObj.getDate());
  // Sur l'axe horaire, seuls les items qui ont VRAIMENT une heure. Les autres
  // passent dans la bande du haut : les poser a 9h ferait dire a la grille
  // quelque chose que personne n'a saisi.
  const surAxe = hourGrid ? dayItems.filter((i) => !planningSansHeure(i)) : dayItems;
  const horsAxe = hourGrid ? dayItems.filter(planningSansHeure) : [];
  const bandeHtml = bande
    ? `<div class="planning-jour-bande">${horsAxe.map((i) => planningItemChip(i, true)).join("")}</div>`
    : "";
  const body = hourGrid
    ? `${bandeHtml}<div class="planning-day-track">${planningHourRowsHtml()}${planningLayoutDay(surAxe).map(planningPositionedItemHtml).join("")}${isToday ? planningNowLineHtml() : ""}</div>`
    : `<div class="planning-day-items">${dayItems.map((i) => planningItemChip(i, compact)).join("") || (compact ? "" : '<div class="planning-day-empty">Rien de prévu</div>')}</div>`;
  return `
    <div class="planning-day-cell ${isToday ? "is-today" : ""} ${isWeekend ? "is-weekend" : ""} ${hourGrid ? "has-hour-grid" : ""} ${extraClass}" data-date="${iso}">
      <div class="planning-day-header">${headerLabel}</div>
      ${body}
    </div>`;
}

function renderPlanning(debut, fin, items) {
  const container = document.getElementById("planning-content");
  const jours = [];
  for (let d = new Date(debut); d <= fin; d.setDate(d.getDate() + 1)) jours.push(new Date(d));

  let gridHtml;
  if (planningViewMode === "jour" || planningViewMode === "semaine") {
    const joursAxe = planningViewMode === "jour" ? [debut] : jours;
    const hauteurBande = planningBandeHauteur(joursAxe, items);
    const bande = hauteurBande > 0;
    const style = ` style="--planning-bande-h:${hauteurBande}px;"`;
    const classe = planningViewMode === "jour" ? "planning-day-view" : "planning-week-grid";
    gridHtml = `<div class="${classe}"${style}>${planningHourGutterHtml(bande)}${joursAxe
      .map((j) => planningDayCellHtml(j, items, { compact: false, showWeekday: true, hourGrid: true, bande }))
      .join("")}</div>`;
  } else {
    const moisAnchor = planningAnchorDate.getMonth();
    gridHtml = `<div class="planning-month-grid">
      ${["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((j) => `<div class="planning-month-weekday">${j}</div>`).join("")}
      ${jours.map((j) => planningDayCellHtml(j, items, { compact: true, showWeekday: false, extraClass: j.getMonth() !== moisAnchor ? "is-outside-month" : "" })).join("")}
    </div>`;
  }
  container.innerHTML = planningToolbarHtml(debut, fin) + planningFiltersHtml() + gridHtml;
}

// Derniers items charges, pour retrouver le detail complet (lieu, client_id...)
// d'un rendez-vous au clic sans re-appeler l'API.
let planningItemsCache = [];

async function loadPlanning() {
  const container = document.getElementById("planning-content");
  debutChargement(container);
  try {
    const [debut, fin] = planningRange();
    planningRangeDebut = debut;
    planningRangeFin = fin;
    const [items] = await Promise.all([
      Api.planning(planningToIso(debut), planningToIso(fin)),
      ensureClientsCache(),
    ]);
    planningItemsCache = items;
    // Chantiers pour le filtre uniquement (repli silencieux comme ailleurs
    // si le plan ne les autorise pas) - meme endpoint que la page Chantiers.
    // Filtre uniquement : un echec y retire une possibilite de tri, il ne
    // fausse aucun rendez-vous affiche.
    planningChantiersCache = await Api.listChantiers().catch(() => []);
    renderPlanningFiltered();
  } catch (err) {
    container.innerHTML = `<div class="empty-state">Erreur : ${escapeHtml(err.message)}</div>`;
  }
}

// Types de planning correspondant a une ligne Evenement reelle (donc
// consultable/modifiable/supprimable) - "tache" et "chantier_debut" sont
// calcules a la volee depuis d'autres tables (voir routers/planning.py) et
// n'ont pas d'Evenement associe.
const PLANNING_TYPES_EVENEMENT = new Set(["rdv", "visite", "intervention", "autre"]);

function evenementDetailHtml(item) {
  const client = item.client_id ? clientsCache.find((c) => c.id === item.client_id) : null;
  const dateLabel = new Date(item.date).toLocaleDateString("fr-FR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: PLANNING_TIMEZONE,
  });
  const duree = planningDureeMinutes(item);
  return `
    <div class="profil-row"><div class="label">Type</div><div class="value">${escapeHtml(PLANNING_TYPE_LABELS[item.type] || item.type)}</div></div>
    <div class="profil-row"><div class="label">Date</div><div class="value">${escapeHtml(dateLabel)}</div></div>
    <div class="profil-row"><div class="label">Heure</div><div class="value">${planningHeureLocale(item.date)}${
      duree !== null ? ` – ${planningHeureLocale(item.date_fin)}` : ""
    }</div></div>
    <div class="profil-row"><div class="label">Durée</div><div class="value">${
      duree !== null ? escapeHtml(planningDureeLabel(duree)) : "Non précisée"
    }</div></div>
    ${client ? `<div class="profil-row"><div class="label">Client</div><div class="value">${escapeHtml(client.nom)}</div></div>` : ""}
    ${item.lieu ? `<div class="profil-row"><div class="label">Lieu</div><div class="value">${escapeHtml(item.lieu)}</div></div>` : ""}
  `;
}

let planningEvenementDetailItem = null;

async function ouvrirDetailEvenement(item) {
  await ensureClientsCache();
  planningEvenementDetailItem = item;
  document.getElementById("evenement-detail-titre").textContent = item.titre;
  document.getElementById("evenement-detail-body").innerHTML = evenementDetailHtml(item);
  document.getElementById("evenement-detail-modal").hidden = false;
}
function fermerDetailEvenement() {
  document.getElementById("evenement-detail-modal").hidden = true;
  planningEvenementDetailItem = null;
}

document.addEventListener("click", async (e) => {
  if (e.target.closest('[data-action="close-evenement-detail"]') || e.target.id === "evenement-detail-modal") {
    fermerDetailEvenement();
  } else if (e.target.closest('[data-action="modifier-evenement"]')) {
    const item = planningEvenementDetailItem;
    if (!item) return;
    fermerDetailEvenement();
    switchView("planning").then(() => window.showEvenementForm({
      evenementId: item.reference_id, titre: item.titre, type: item.type,
      date: item.date, dateFin: item.date_fin, lieu: item.lieu, clientId: item.client_id, chantierId: item.chantier_id,
    }));
  } else if (e.target.closest('[data-action="supprimer-evenement"]')) {
    const item = planningEvenementDetailItem;
    if (!item) return;
    const confirme = await confirmDialog(`Supprimer le rendez-vous "${item.titre}" ?`, { title: "Supprimer", confirmLabel: "Supprimer", danger: true });
    if (!confirme) return;
    await withErrorToast(async () => {
      await Api.deleteEvenement(item.reference_id);
      showToast("Rendez-vous supprimé.");
      fermerDetailEvenement();
      loadPlanning();
    });
  }
});
document.addEventListener("keydown", (e) => {
  // Si la confirmation de suppression est ouverte par-dessus, elle gere son
  // propre Echap (voir confirmDialog()) : sans ce garde-fou, les deux
  // ecouteurs Echap se declenchaient sur la meme frappe et refermaient les
  // deux modales d'un coup, alors qu'Annuler doit ramener au detail du
  // rendez-vous, pas tout fermer.
  if (e.key === "Escape" && !document.getElementById("evenement-detail-modal").hidden && document.getElementById("confirm-dialog").hidden) {
    fermerDetailEvenement();
  }
});

function setupPlanningView() {
  async function showEvenementForm(prefill = {}) {
    const container = document.getElementById("evenement-form-container");
    await ensureClientsCache();
    const isEdit = !!prefill.evenementId;
    // Date/heure pre-remplies en Europe/Paris (jamais le fuseau ambiant) :
    // reouvrir un rendez-vous en edition doit remontrer exactement la date
    // et l'heure que l'artisan avait saisies, pas un decalage.
    const { date: dateVal, heure: heureVal } = prefill.date ? planningDateHeureLocale(prefill.date) : { date: "", heure: "09:00" };
    // La duree n'a PAS de valeur par defaut : « non precisee » est un etat
    // legitime, et c'est le seul honnete tant que l'artisan n'a rien dit. Une
    // heure choisie d'office se retrouverait dessinee sur la grille comme un
    // creneau reellement occupe.
    const dureeVal = prefill.date && prefill.dateFin
      ? String(Math.max(0, Math.round((new Date(prefill.dateFin) - new Date(prefill.date)) / 60000)))
      : "";
    container.innerHTML = `
      <div class="form-box">
        <h3>${isEdit ? "Modifier le rendez-vous" : prefill.titre ? "Planifier une intervention" : "Nouveau rendez-vous"}</h3>
        <form id="evenement-form">
          <div class="form-grid">
            <div><label for="ev-titre">Titre *</label><input type="text" id="ev-titre" value="${escapeHtml(prefill.titre || "")}" required></div>
            <div>
              <label for="ev-type">Type</label>
              <select id="ev-type">
                <option value="rdv" ${prefill.type === "rdv" ? "selected" : ""}>Rendez-vous</option>
                <option value="visite" ${prefill.type === "visite" ? "selected" : ""}>Visite</option>
                <option value="intervention" ${prefill.type === "intervention" ? "selected" : ""}>Intervention</option>
                <option value="autre" ${prefill.type === "autre" ? "selected" : ""}>Autre</option>
              </select>
            </div>
            <div><label for="ev-date">Date *</label><input type="date" id="ev-date" value="${escapeHtml(dateVal)}" required></div>
            <div><label for="ev-heure">Heure</label><input type="time" id="ev-heure" value="${escapeHtml(heureVal)}"></div>
            <div>
              <label for="ev-duree">Durée</label>
              <select id="ev-duree">${planningDureeOptionsHtml(dureeVal)}</select>
            </div>
            <div><label for="ev-client">Client (optionnel)</label><select id="ev-client"><option value="">Aucun</option>${clientOptionsHtml(prefill.clientId)}</select></div>
            <div><label for="ev-lieu">Lieu</label><input type="text" id="ev-lieu" value="${escapeHtml(prefill.lieu || "")}"></div>
          </div>
          <p class="field-hint">Sans durée, le rendez-vous s'affiche comme un simple repère à son heure de début : le planning ne montre pas d'occupation qui n'a pas été saisie.</p>
          <p class="field-error" id="evenement-form-error" hidden></p>
          <div class="form-actions">
            <button type="submit" class="btn-sm btn-sm-primary">${isEdit ? "Enregistrer" : "Créer"}</button>
            <button type="button" class="btn-sm" data-action="cancel-evenement-form">Annuler</button>
          </div>
        </form>
      </div>`;
    container.hidden = false;
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("evenement-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById("evenement-form-error");
      errorBox.hidden = true;
      const dateVal = document.getElementById("ev-date").value;
      const heureVal = document.getElementById("ev-heure").value || "09:00";
      const clientVal = document.getElementById("ev-client").value;
      const dureeMin = parseInt(document.getElementById("ev-duree").value, 10);
      const debutIso = planningLocalToUtcIso(dateVal, heureVal);
      const payload = {
        titre: document.getElementById("ev-titre").value,
        type: document.getElementById("ev-type").value,
        date_debut: debutIso,
        // null quand la duree n'est pas precisee : c'est ce null qui fait
        // afficher un repere plutot qu'un creneau plein sur la grille.
        date_fin: Number.isFinite(dureeMin) && dureeMin > 0
          ? new Date(new Date(debutIso).getTime() + dureeMin * 60000).toISOString()
          : null,
        lieu: emptyToNull(document.getElementById("ev-lieu").value),
        client_id: clientVal ? parseInt(clientVal, 10) : null,
        chantier_id: prefill.chantierId || null,
      };
      try {
        if (isEdit) {
          await Api.updateEvenement(prefill.evenementId, payload);
          showToast("Rendez-vous mis à jour.");
        } else {
          await Api.createEvenement(payload);
          showToast("Rendez-vous créé.");
        }
        container.hidden = true;
        container.innerHTML = "";
        loadPlanning();
      } catch (err) {
        errorBox.hidden = false;
        errorBox.textContent = err.message;
      }
    });
  }
  window.showEvenementForm = showEvenementForm;

  document.querySelector('[data-action="show-evenement-form"]').addEventListener("click", () => showEvenementForm());

  document.getElementById("evenement-form-container").addEventListener("click", (e) => {
    if (e.target.closest('[data-action="cancel-evenement-form"]')) {
      const container = document.getElementById("evenement-form-container");
      container.hidden = true;
      container.innerHTML = "";
    }
  });

  const planningContent = document.getElementById("planning-content");

  planningContent.addEventListener("click", (e) => {
    const chip = e.target.closest(".planning-item");
    if (chip) {
      const item = planningItemsCache.find(
        (i) => String(i.reference_id) === chip.dataset.refId && i.type === chip.dataset.type,
      );
      if (item && item.type === "chantier_debut") ouvrirChantierDepuisPlanning(item.chantier_id || item.reference_id);
      else if (item && item.type === "tache") ouvrirTacheDepuisPlanning(item.reference_id);
      else if (item && PLANNING_TYPES_EVENEMENT.has(item.type)) ouvrirDetailEvenement(item);
      return;
    }
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    if (btn.dataset.action === "planning-prev") {
      planningAnchorDate = planningShift(-1);
      loadPlanning();
    } else if (btn.dataset.action === "planning-next") {
      planningAnchorDate = planningShift(1);
      loadPlanning();
    } else if (btn.dataset.action === "planning-today") {
      planningAnchorDate = new Date();
      loadPlanning();
    } else if (btn.dataset.action === "planning-mode") {
      planningViewMode = btn.dataset.mode;
      loadPlanning();
    }
  });

  // Filtres : jamais un rechargement serveur, seulement un nouveau rendu
  // depuis planningItemsCache (deja recu pour la periode affichee).
  planningContent.addEventListener("input", (e) => {
    if (e.target.id === "planning-filtre-q") {
      const pos = e.target.selectionStart;
      planningFilters.q = e.target.value;
      renderPlanningFiltered();
      // renderPlanningFiltered() remplace tout innerHTML(donc aussi ce
      // champ) a chaque frappe : sans ca, le focus et le curseur sauteraient
      // au debut du champ apres chaque caractere tape.
      const nouveauChamp = document.getElementById("planning-filtre-q");
      nouveauChamp?.focus();
      nouveauChamp?.setSelectionRange(pos, pos);
    }
  });
  planningContent.addEventListener("change", (e) => {
    if (e.target.id === "planning-filtre-type") planningFilters.type = e.target.value;
    else if (e.target.id === "planning-filtre-client") planningFilters.clientId = e.target.value;
    else if (e.target.id === "planning-filtre-chantier") planningFilters.chantierId = e.target.value;
    else return;
    renderPlanningFiltered();
  });

  // (Entree/Espace sur un item du planning : plus de gestionnaire local, le
  // relais delegue en tete de fichier couvre tous les role="button" du
  // produit. En garder un ici declencherait deux clics sur la meme frappe.)

  planningContent.addEventListener("dragstart", (e) => {
    const chip = e.target.closest(".planning-item");
    if (!chip || chip.dataset.type === "chantier_debut") {
      e.preventDefault();
      return;
    }
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", JSON.stringify({
      type: chip.dataset.type, refId: chip.dataset.refId, currentDate: chip.dataset.currentDate,
    }));
  });

  planningContent.addEventListener("dragover", (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (!cell) return;
    e.preventDefault();
    cell.classList.add("drag-over");
  });

  planningContent.addEventListener("dragleave", (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (cell) cell.classList.remove("drag-over");
  });

  planningContent.addEventListener("drop", async (e) => {
    const cell = e.target.closest(".planning-day-cell");
    if (!cell) return;
    e.preventDefault();
    cell.classList.remove("drag-over");
    let data;
    try {
      data = JSON.parse(e.dataTransfer.getData("text/plain"));
    } catch (err) {
      return;
    }
    const newDate = cell.dataset.date;
    // planningToIso(...) des deux cotes (jamais un slice(0,10) direct de la
    // chaine UTC) : voir le commentaire de planningToIso() plus haut.
    if (planningToIso(new Date(data.currentDate)) === newDate) return;

    await withErrorToast(async () => {
      if (data.type === "tache") {
        await Api.updateTache(parseInt(data.refId, 10), { echeance: newDate });
      } else if (PLANNING_TYPES_EVENEMENT.has(data.type)) {
        const refId = parseInt(data.refId, 10);
        const oldDate = new Date(data.currentDate);
        const [y, m, d] = newDate.split("-").map(Number);
        const combined = new Date(oldDate);
        combined.setFullYear(y, m - 1, d);
        // La fin suit le debut du meme decalage. Sans ca, deplacer un
        // rendez-vous d'une journee laissait sa fin sur l'ancien jour : la
        // duree enregistree devenait celle de l'ecart entre les deux dates.
        const source = planningItemsCache.find((i) => i.reference_id === refId && i.type === data.type);
        const decalage = combined - oldDate;
        const payload = { date_debut: combined.toISOString() };
        if (source && source.date_fin) {
          payload.date_fin = new Date(new Date(source.date_fin).getTime() + decalage).toISOString();
        }
        await Api.updateEvenement(refId, payload);
      } else {
        return;
      }
      showToast("Deplace au " + new Date(newDate + "T00:00:00").toLocaleDateString("fr-FR"));
      loadPlanning();
    });
  });
}
