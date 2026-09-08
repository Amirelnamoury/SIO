/* Verifie, sur la timeline COMPLETE et sans navigateur, les contraintes
   que le brief pose sur le mouvement. La question n'est pas « est-ce que
   ca a l'air continu » mais « la valeur affichee revient-elle en
   arriere, oui ou non ». Ca se calcule. */
import { SCENES } from "../../frontend/landing-visite.js";

const lerp = (a, b, t) => a + (b - a) * t;
const doux = (t) => t * t * (3 - 2 * t) * 0.35 + t * 0.65;
const rad = (d) => (d * Math.PI) / 180;
const PREROLL = 0.22;
const T_DEBUT = 0.70, T_FIN = 0.96;

function transformer(s, p) {
  const q = p < 0 || p > 1 ? p : doux(p);
  return [
    Math.max(1, lerp(s.sc[0], s.sc[1], q)),   // le shader borne a 1.0
    lerp(s.px[0], s.px[1], q),
    lerp(s.py[0], s.py[1], q),
    rad(lerp(s.rot[0], s.rot[1], q)),
  ];
}

let echecs = 0;
const dire = (ok, txt) => { if (!ok) echecs++; console.log((ok ? "  ok   " : "  ECHEC") + " " + txt); };

console.log("\n=== 1. AMPLITUDE DE L'ECHELLE (brief : max ~1.05, vise 1.025-1.035) ===");
SCENES.forEach((s, i) => {
  const max = Math.max(s.sc[0], s.sc[1]);
  const amp = Math.abs(s.sc[1] - s.sc[0]);
  dire(max <= 1.035 && amp <= 0.030,
    `plan ${i} ${s.f.padEnd(26)} echelle ${s.sc[0].toFixed(3)} -> ${s.sc[1].toFixed(3)}  (max ${max.toFixed(3)}, amplitude ${(amp * 100).toFixed(1)} %)`);
});

console.log("\n=== 2. CONTINUITE : la valeur affichee revient-elle en arriere ? ===");
// On echantillonne la timeline entiere, y compris le pre-roll de B, et on
// suit CHAQUE texture separement - c'est la que l'ancien moteur cassait :
// la camera partagee sautait de la fin de A au debut de B.
const PAS = 400;
for (let i = 0; i < SCENES.length; i++) {
  const s = SCENES[i];
  // La course reellement parcourue par cette scene : de son pre-roll
  // (quand elle est encore B) jusqu'a la fin de sa propre scene.
  const debut = -PREROLL;
  const suivi = [];
  for (let k = 0; k <= PAS; k++) {
    const p = debut + (1 - debut) * (k / PAS);
    suivi.push(transformer(s, p));
  }
  const noms = ["echelle", "trans-x", "trans-y", "rotation"];
  for (let c = 0; c < 4; c++) {
    const v = suivi.map((x) => x[c]);
    const monteTout = v.every((x, k) => k === 0 || x >= v[k - 1] - 1e-12);
    const descendTout = v.every((x, k) => k === 0 || x <= v[k - 1] + 1e-12);
    const plat = Math.abs(v[v.length - 1] - v[0]) < 1e-9;
    dire(monteTout || descendTout,
      `plan ${i} ${noms[c].padEnd(8)} ${plat ? "constant" : (monteTout ? "croissant" : (descendTout ? "decroissant" : "NON MONOTONE"))}`);
  }
}

console.log("\n=== 3. AUCUN RETOUR A L'ETAT INITIAL AVANT DE DISPARAITRE ===");
// Le symptome decrit par l'utilisateur : « l'image avance puis revient a
// sa position initiale ». Concretement : la valeur en fin de scene est-
// elle plus proche du depart que ne l'etait le milieu ?
SCENES.forEach((s, i) => {
  const mid = transformer(s, 0.5);
  const fin = transformer(s, 1);
  const deb = transformer(s, 0);
  const noms = ["echelle", "trans-x", "trans-y", "rotation"];
  for (let c = 0; c < 4; c++) {
    if (Math.abs(fin[c] - deb[c]) < 1e-9) continue;   // axe non anime
    const retour = Math.abs(fin[c] - deb[c]) < Math.abs(mid[c] - deb[c]);
    dire(!retour, `plan ${i} ${noms[c].padEnd(8)} fin=${fin[c].toFixed(4)} vs debut=${deb[c].toFixed(4)} (milieu ${mid[c].toFixed(4)})`);
  }
});

console.log("\n=== 4. RACCORD ENTRE DEUX PLANS ===");
// Il ne peut plus y avoir de saut PARTAGE, puisqu'il n'y a plus de valeur
// partagee. Ce qu'on verifie ici, c'est que B est deja en mouvement quand
// elle apparait : sa transformation au debut du fondu doit differer de
// celle qu'elle aura a la fin du fondu.
for (let i = 0; i < SCENES.length - 1; i++) {
  const b = SCENES[i + 1];
  const auDebutDuFondu = transformer(b, -PREROLL);      // t = 0
  const aLaFinDuFondu = transformer(b, 0);              // t = 1
  const bouge = auDebutDuFondu.some((v, c) => Math.abs(v - aLaFinDuFondu[c]) > 1e-6);
  dire(bouge, `plan ${i} -> ${i + 1} : la scene entrante bouge pendant le fondu (dx=${(aLaFinDuFondu[1] - auDebutDuFondu[1]).toFixed(4)}, dz=${(aLaFinDuFondu[0] - auDebutDuFondu[0]).toFixed(4)})`);
  // Et le pre-roll ne doit jamais faire passer l'echelle sous 1.0, sinon
  // des bords noirs apparaissent.
  dire(auDebutDuFondu[0] >= 1, `plan ${i + 1} : echelle au pre-roll = ${auDebutDuFondu[0].toFixed(4)} (>= 1.0, pas de bord noir)`);
}

console.log("\n=== 5. LONGUEUR TOTALE (brief : 700 a 900 vh) ===");
const somme = SCENES.reduce((a, s) => a + s.poids, 0);
const SORTIE = 0.65;
dire(somme + SORTIE >= 7 && somme + SORTIE <= 9,
  `${SCENES.length} plans, somme des poids ${somme.toFixed(2)} + sortie ${SORTIE} = ${((somme + SORTIE) * 100).toFixed(0)} vh`);
SCENES.forEach((s, i) => {
  dire(s.poids >= 0.70 && s.poids <= 1.10,
    `plan ${i} : ${(s.poids * 100).toFixed(0)} svh (brief : 70 a 110)`);
});
console.log(`         mobile (x0.66) : ${((somme + SORTIE) * 66).toFixed(0)} vh`);

console.log("\n=== 6. ALTERNANCE DES COTES ===");
SCENES.forEach((s, i) => {
  if (i === 0) return;
  dire(s.cote !== SCENES[i - 1].cote, `plan ${i} : ${SCENES[i - 1].cote} -> ${s.cote}`);
});

console.log("\n=== 7. MOMENTS CHIFFRES ===");
const cartes = SCENES.map((s, i) => (s.carte ? i : -1)).filter((i) => i >= 0);
dire(cartes.length === 2, `exactement deux moments chiffres, aux plans ${cartes.join(" et ")}`);
dire(cartes[1] - cartes[0] >= 3, `ils sont espaces de ${cartes[1] - cartes[0]} plans`);

console.log("\n" + (echecs === 0 ? "TOUT PASSE." : echecs + " ECHEC(S)."));
process.exit(echecs ? 1 : 0);
