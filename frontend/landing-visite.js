/* =====================================================================
   LA VISITE — huit plans, un mouvement qui ne revient jamais en arrière
   ---------------------------------------------------------------------
   POURQUOI CE FICHIER A ÉTÉ RÉÉCRIT

   La version précédente faisait voler une caméra 3D au-dessus d'un grand
   tirage. Elle avait un défaut structurel, visible à l'œil sur
   l'enregistrement : au salon comme à la cour, l'image avançait, puis
   REVENAIT en arrière avant de céder la place à la suivante.

   La cause n'était pas un réglage d'amplitude. Une seule caméra servait
   les DEUX images, et chaque scène déclarait ses propres valeurs de
   départ et d'arrivée. À la frontière, la caméra passait donc de la
   valeur finale de A à la valeur initiale de B en une image — et comme
   les deux textures sont visibles pendant le fondu, ce saut se lisait
   sur les deux à la fois. Aucun réglage ne pouvait le corriger : il
   fallait supprimer la caméra partagée.

   LE MODÈLE ACTUEL
   Il n'y a plus de caméra du tout. Un quad qui remplit l'écran, une
   projection orthographique, et TOUT le cadrage se fait dans le shader,
   texture par texture :

     - chaque image a son propre cadrage « cover », calculé à partir de
       son rapport et de celui de la fenêtre. À l'échelle 1.00 on voit
       donc le MAXIMUM de la photographie : le cadrage d'origine est
       respecté, et le recadrage se limite à ce que la forme de l'écran
       impose ;
     - chaque image a son point focal, qui décide de ce qu'on garde
       quand il faut rogner ;
     - chaque image a son propre mouvement, continu et monotone.

   Comme chaque texture porte son mouvement, il n'existe plus une seule
   valeur partagée entre deux scènes — donc plus rien à réinitialiser. A
   termine son geste pendant le fondu ; B a déjà commencé le sien AVANT
   d'apparaître, en prolongeant sa course en amont de zéro. La continuité
   est une propriété du modèle, pas un réglage à maintenir.

   LE ZOOM N'EST PLUS L'ANIMATION
   Les amplitudes précédentes atteignaient 30 % de distance focale : on
   voyait un zoom, et on perdait l'architecture des pièces. Ici l'échelle
   ne dépasse jamais 1.035, et le déplacement se lit surtout comme une
   TRANSLATION.

   UNE CONSÉQUENCE GÉOMÉTRIQUE QU'IL FAUT ASSUMER
   Sur un écran large, une photographie en 16:9 remplit le cadre presque
   exactement : à l'échelle 1.00 il ne reste aucune marge pour se
   déplacer. La translation est donc exprimée en FRACTION DE LA MARGE
   DISPONIBLE, et non en pixels : là où l'écran est plus étroit que
   l'image — une tablette, un téléphone — la marge est large et le
   travelling devient le mouvement dominant ; sur un 16:9, elle est
   étroite et c'est la poussée qui mène. Le même réglage produit le
   mouvement juste dans les deux cas, sans configuration séparée, et
   aucun bord noir ne peut apparaître.
   ===================================================================== */

import * as THREE from "./vendor/three.module.min.js?v=160";

const BASE = "assets/landing/villa/";

/* ---------------------------------------------------------------------
   LES HUIT PLANS
   ---------------------------------------------------------------------
   Une sélection, pas un inventaire. La visite en comptait onze, dont
   deux paliers qui réaffichaient une photographie déjà vue. Six pièces
   ont été écartées parce qu'elles redisaient visuellement une autre :
   salle à manger et salon TV redisaient le salon, salle de bain et
   chambre d'amis redisaient la suite, balcon et cour enchaînaient trois
   extérieurs avant la terrasse — le regard n'y voyait plus qu'une seule
   longue scène dehors.

     focal   le point de l'image gardé au centre quand il faut rogner
     sc      l'échelle, début → fin. Jamais au-delà de 1.035
     px, py  la translation, en fraction de la marge disponible (-1 à 1)
     rot     la rotation, en degrés. Au-delà d'un demi-degré, une
             photographie d'architecture penche visiblement : les
             verticales d'un mur ne pardonnent pas
     poids   la course accordée, en hauteurs d'écran
     cote    le côté du texte, décidé par l'espace vide de l'image
     carte   le numéro du moment chiffré, s'il y en a un
   --------------------------------------------------------------------- */
export const SCENES = [
  {
    f: "00_villa-master-facade", poids: 1.0, cote: "gauche",
    alt: "Façade d'une villa en pierre au crépuscule, entrée voûtée éclairée et jardin taillé.",
    // Façade : une poussée très lente vers l'entrée, et une descente.
    focal: [0.50, 0.47], sc: [1.004, 1.032], px: [0.00, 0.10], py: [0.55, -0.60], rot: [0, 0],
  },
  {
    f: "01_hall-entree", poids: 0.85, cote: "droite",
    alt: "Hall d'entrée, escalier tournant et lustre en fer forgé, tapis sur un sol de pierre claire.",
    // Hall : un glissement vers la droite, vers l'escalier.
    focal: [0.56, 0.48], sc: [1.006, 1.028], px: [-0.70, 0.75], py: [0.15, -0.20], rot: [0.10, -0.10],
  },
  {
    f: "02_salon-principal", poids: 0.95, cote: "gauche",
    alt: "Salon avec cheminée en pierre, larges baies vitrées et vue sur la piscine.",
    // Salon : travelling horizontal, de la cheminée vers les baies.
    focal: [0.48, 0.51], sc: [1.008, 1.030], px: [-0.80, 0.80], py: [0, 0], rot: [0, 0],
  },
  {
    f: "04_cuisine", poids: 0.9, cote: "droite", carte: 1,
    alt: "Cuisine avec îlot central en pierre, hotte en cuivre et rangements en bois clair.",
    // Cuisine : une diagonale douce qui descend vers l'îlot.
    focal: [0.51, 0.52], sc: [1.004, 1.026], px: [0.60, -0.55], py: [-0.35, 0.40], rot: [-0.12, 0.10],
  },
  {
    f: "06_bureau-bibliotheque", poids: 0.9, cote: "gauche", dense: true,
    alt: "Bureau avec plans dépliés sur une table en bois, fauteuil de cuir et bibliothèque murale.",
    // Bureau : de la table vers la bibliothèque, sur la droite.
    //
    // `dense` : la seule piece dont la fenetre lumineuse tombe du cote ou
    // le texte se pose. Mesure : le paragraphe y tenait 4,18 pour un
    // seuil de 4,5, alors que les sept autres plans etaient entre 4,6 et
    // 10,2. Deplacer le texte a droite casserait l'alternance demandee,
    // et changer le point focal ne sert a rien sur un ecran large - a
    // cadrage cover, il n'y a presque aucune marge horizontale. C'est
    // donc l'ombre de CETTE piece qui est plus dense, declaree ici plutot
    // qu'en exception CSS sur un numero de scene : une regle accrochee a
    // `[data-vue="4"]` survivrait a un changement d'ordre sans suivre la
    // photographie qu'elle corrige.
    focal: [0.52, 0.49], sc: [1.006, 1.028], px: [-0.65, 0.70], py: [0.25, -0.25], rot: [0, 0],
  },
  {
    f: "09_galerie-couloir", poids: 0.95, cote: "droite",
    alt: "Galerie voûtée bordée de tableaux, perspective vers le fond de la maison.",
    // Galerie : le point de fuite est au centre, donc la sensation
    // d'avancer vient ici de l'échelle. C'est le seul plan où elle mène,
    // et il reste le plus sage des huit : 1.8 % du début à la fin.
    focal: [0.50, 0.50], sc: [1.002, 1.020], px: [0, 0], py: [0.30, -0.30], rot: [0, 0],
  },
  {
    f: "07_suite-parentale", poids: 0.85, cote: "gauche", carte: 2,
    alt: "Suite parentale, lit bas, cheminée et coin salon devant de larges fenêtres.",
    // Suite : un léger RECUL, qui rouvre l'espace. C'est le seul plan
    // dont l'échelle diminue, et cela se lit comme une respiration après
    // la fuite de la galerie.
    focal: [0.52, 0.51], sc: [1.030, 1.006], px: [0.45, -0.50], py: [0, 0.20], rot: [0.10, -0.08],
  },
  {
    f: "13_terrasse-piscine", poids: 1.1, cote: "droite",
    alt: "Terrasse au crépuscule, salon d'extérieur, piscine éclairée et jardin méditerranéen.",
    // Terrasse : un dernier recul, qui ouvre sur le jardin — puis la
    // sortie vers la page, portée par uSortie.
    focal: [0.50, 0.49], sc: [1.028, 1.004], px: [-0.40, 0.45], py: [-0.20, 0.20], rot: [0, 0],
  },
];

/* =====================================================================
   LES SHADERS
   ===================================================================== */

const VERT = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

/* Aucun accent grave dans les commentaires ci-dessous : ils vivent DANS
   un litteral de gabarit, et un accent grave y terminerait la chaine. Au
   premier jet, le navigateur signalait une erreur de syntaxe a la ligne
   suivante, loin de sa cause. */
const FRAG = `
precision highp float;
varying vec2 vUv;

uniform sampler2D uA;
uniform sampler2D uB;
uniform float uRatioA;     // largeur / hauteur de l'image A
uniform float uRatioB;
uniform float uVue;        // largeur / hauteur de la fenetre
uniform vec2  uFocA;       // point focal, en fraction de l'image
uniform vec2  uFocB;
uniform vec4  uTrA;        // (echelle, translation x, translation y, rotation)
uniform vec4  uTrB;
uniform float uMix;        // 0 = A seule, 1 = B seule
uniform float uHasB;
uniform vec2  uDir;        // le cote par lequel B arrive
uniform float uSortie;     // 0 = image, 1 = papier
uniform vec3  uPapier;
uniform float uVignette;
uniform float uGrain;
uniform float uTemps;

/* LE CADRAGE, PAR IMAGE.

   La variable "part" est la fraction de la texture reellement visible :
   pleine largeur si l'ecran est plus etroit que l'image, pleine hauteur
   sinon.

   (Aucun accent grave dans ce commentaire. Il vit DANS un litteral de
   gabarit, et une paire d'accents graves autour d'un nom de variable y
   referme la chaine puis la rouvre : tout ce qui est entre les deux est
   alors lu comme du JavaScript. Le navigateur signale une erreur de
   syntaxe sur ce nom de variable, sans rapport visible avec sa cause.
   C'est arrive deux fois sur ce fichier.)
   A l'echelle 1.0 on voit donc le maximum de la photographie.

   L'echelle est bornee a 1.0 par le bas. La scene suivante commence son
   mouvement AVANT d'apparaitre, avec une progression negative : sans
   cette borne, elle passerait sous le cadrage cover et laisserait voir
   des bords noirs pendant le fondu.

   La translation est une FRACTION de la marge disponible, jamais une
   distance : elle ne peut donc pas sortir de l'image, quelle que soit la
   forme de l'ecran, et il n'y a rien a clamper apres coup - un clamp
   ecraserait le mouvement sur les ecrans larges et le rendrait
   irregulier d'un appareil a l'autre. */
vec2 cadrer(vec2 uv, float ratioImg, vec2 focal, vec4 tr) {
  vec2 part = uVue > ratioImg
    ? vec2(1.0, ratioImg / uVue)
    : vec2(uVue / ratioImg, 1.0);
  part /= max(tr.x, 1.0);

  // La rotation s'applique dans un espace ou l'ecran est carre, sinon
  // une rotation d'un demi-degre cisaille l'image au lieu de la tourner.
  float c = cos(tr.w), s = sin(tr.w);
  vec2 d = uv - 0.5;
  vec2 e = vec2(d.x * uVue, d.y);
  e = vec2(e.x * c - e.y * s, e.x * s + e.y * c);
  d = vec2(e.x / uVue, e.y);

  // La demi-etendue de la fenetre TOURNEE : c'est elle qui borne le
  // centre, sinon un coin sortirait de l'image des que la rotation n'est
  // plus nulle.
  vec2 demi = 0.5 * vec2(
    part.x * abs(c) + part.y * abs(s),
    part.x * abs(s) + part.y * abs(c));
  vec2 marge = max(vec2(0.0), vec2(0.5) - demi);
  // Deux bornes, et la seconde n'est pas redondante. La translation est
  // exprimee en fraction de la marge, donc dans [-1, 1] - mais le
  // pre-roll de la scene entrante EXTRAPOLE cette course en amont de
  // zero, et depasse alors legerement l'intervalle (mesure : -1.019 sur
  // le hall). Sans cette borne, un liset noir apparaissait sur un bord
  // pendant le fondu. Elle rend la garantie independante des valeurs
  // ecrites dans la table des scenes.
  vec2 centre = clamp(
    clamp(focal, demi, 1.0 - demi) + tr.yz * marge,
    demi, 1.0 - demi);

  return centre + d * part;
}

float bruit(vec2 p) {
  return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
  vec3 a = texture2D(uA, cadrer(vUv, uRatioA, uFocA, uTrA)).rgb;
  vec3 b = texture2D(uB, cadrer(vUv, uRatioB, uFocB, uTrB)).rgb;

  /* LE FRONT. L'image suivante entre par le cote vers lequel on se
     deplace, sur un front tres large : on ne doit pas lire un balayage,
     seulement sentir que quelque chose vient de ce cote-la. La part de
     fondu uniforme a ete augmentee (0.45 -> 0.55) parce qu'avec huit
     plans au lieu de quatorze, chaque transition compte davantage et un
     front trop marque se remarquait. */
  float d = dot(vUv - 0.5, normalize(uDir + vec2(1e-5))) + 0.5;
  float front = smoothstep(d - 0.62, d + 0.62, uMix * 2.0 - 0.5 + d);
  float m = clamp(mix(uMix, front, 0.55), 0.0, 1.0) * uHasB;

  vec3 c = mix(a, b, m);

  float r = distance(vUv, vec2(0.5));
  c *= 1.0 - uVignette * smoothstep(0.36, 0.95, r);
  c += (bruit(vUv * 900.0 + uTemps) - 0.5) * uGrain;

  /* LA SORTIE. Plutot qu'une coupure entre la derniere photographie et
     la page, l'image se decolore VERS le papier : le contraste tombe
     d'abord, la teinte ensuite. Le lecteur ne franchit pas une
     frontiere, il en sort. */
  vec3 gris = vec3(dot(c, vec3(0.2126, 0.7152, 0.0722)));
  c = mix(c, mix(c, gris, 0.62), clamp(uSortie * 1.5, 0.0, 1.0));
  c = mix(c, uPapier, smoothstep(0.18, 1.0, uSortie));

  gl_FragColor = vec4(c, 1.0);
}`;

/* =====================================================================
   LE MOTEUR
   ===================================================================== */

const lerp = (a, b, t) => a + (b - a) * t;

/* Un easing DÉLIBÉRÉMENT FAIBLE. L'ancien était un cubique complet :
   le mouvement s'arrêtait presque à chaque fin de scène, puis repartait
   sec au début de la suivante. Deux ruptures de vitesse par frontière —
   et c'est précisément ce qu'on cherche à supprimer. Ici la courbe reste
   à 65 % linéaire : assez pour que le départ ne soit pas mécanique, trop
   peu pour qu'on sente le mouvement se poser. */
const doux = (t) => t * t * (3 - 2 * t) * 0.35 + t * 0.65;
const rad = (d) => (d * Math.PI) / 180;

const DEBUG = typeof location !== "undefined" && /(?:^|[?&])debug(?:=|&|$)/.test(location.search);

/* Le pré-roll : la part de sa propre course que la scène suivante a déjà
   parcourue quand elle apparaît. Sans lui, B arrive figée puis démarre —
   ce qui se lit comme un à-coup au moment exact où le regard se pose sur
   elle. Avec, les deux images bougent pendant tout le fondu. */
const PREROLL = 0.22;

export function creerVisite({ canvas, scenes, petit, papier }) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: false,       // une photographie n'a pas d'arêtes à lisser
    alpha: false,
    powerPreference: "high-performance",
    preserveDrawingBuffer: DEBUG,
  });
  renderer.setClearColor(0x1b1f1d, 1);

  const scene = new THREE.Scene();
  // Une projection orthographique et un quad qui remplit exactement le
  // champ. Il n'y a plus de caméra à déplacer, donc plus rien qui puisse
  // sauter d'une scène à l'autre.
  const camera = new THREE.OrthographicCamera(-0.5, 0.5, 0.5, -0.5, 0, 1);

  const vide = new THREE.DataTexture(new Uint8Array([27, 31, 29, 255]), 1, 1, THREE.RGBAFormat);
  vide.needsUpdate = true;

  const u = {
    uA: { value: vide }, uB: { value: vide },
    uRatioA: { value: 1.79 }, uRatioB: { value: 1.79 }, uVue: { value: 1.6 },
    uFocA: { value: new THREE.Vector2(0.5, 0.5) },
    uFocB: { value: new THREE.Vector2(0.5, 0.5) },
    uTrA: { value: new THREE.Vector4(1, 0, 0, 0) },
    uTrB: { value: new THREE.Vector4(1, 0, 0, 0) },
    uMix: { value: 0 }, uHasB: { value: 0 },
    uDir: { value: new THREE.Vector2(1, 0) },
    uSortie: { value: 0 },
    /* LE PAPIER, EN sRGB BRUT ET NON EN THREE.Color.
       `new THREE.Color("#F1EADF")` convertit la valeur dans l'espace de
       travail LINEAIRE - c'est le comportement voulu par Three.js quand
       on eclaire une scene. Ici le shader ne fait aucun eclairage : il
       echantillonne des textures et les ecrit telles quelles. Un seul
       uniforme linearise au milieu de valeurs sRGB donnait un fondu qui
       s'arretait a (224, 210, 188) au lieu de (241, 234, 223) : la
       visite finissait sur un beige plus sombre que la page qui suit, et
       la jointure redevenait visible - exactement ce que la sortie doit
       supprimer. On passe donc les composantes directement. */
    uPapier: { value: (() => {
      const h = (papier || "#F1EADF").replace("#", "");
      const n = parseInt(h, 16);
      return new THREE.Vector3(((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255);
    })() },
    uVignette: { value: 0.15 }, uGrain: { value: 0.02 }, uTemps: { value: 0 },
  };

  const quad = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms: u, depthTest: false })
  );
  scene.add(quad);

  let dpr = 1;
  function dimensionner() {
    const r = canvas.getBoundingClientRect();
    const W = Math.max(1, Math.round(r.width));
    const H = Math.max(1, Math.round(r.height));
    // Au-delà de 2, on paie des pixels que personne ne distingue sur une
    // photographie. Une machine qui annonce peu de cœurs descend encore :
    // le coût d'un plein écran en WebGL est proportionnel aux pixels, et
    // c'est le seul levier qui ne coûte rien à l'image.
    const faible = (navigator.hardwareConcurrency || 8) <= 4;
    dpr = Math.min(window.devicePixelRatio || 1, petit ? 1.6 : (faible ? 1.3 : 2));
    renderer.setPixelRatio(dpr);
    renderer.setSize(W, H, false);
    u.uVue.value = W / H;
  }

  // -------------------------------------------------------------------
  // Les textures : une fenêtre glissante, jamais les huit à la fois.
  // -------------------------------------------------------------------
  const chargeur = new THREE.TextureLoader();
  const textures = new Map();
  const enCours = new Map();
  const ratios = new Map();
  let indexA = -1, indexB = -1;

  const url = (i) => BASE + scenes[i].f + (petit ? "-sm" : "") + ".webp";

  function charger(i) {
    if (i < 0 || i >= scenes.length) return Promise.resolve(null);
    if (textures.has(i)) return Promise.resolve(textures.get(i));
    if (enCours.has(i)) return enCours.get(i);
    const p = new Promise((ok) => {
      chargeur.load(url(i), (t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.minFilter = t.magFilter = THREE.LinearFilter;   // on ne réduit jamais
        t.generateMipmaps = false;
        t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
        textures.set(i, t);
        // Le rapport RÉEL de l'image, pas celui qu'on suppose. C'est lui
        // qui fait le cadrage cover : une photographie livrée dans un
        // format différent des autres serait sinon étirée.
        ratios.set(i, t.image.width / t.image.height);
        enCours.delete(i);
        ok(t);
      }, undefined, () => { enCours.delete(i); ok(null); });
    });
    enCours.set(i, p);
    return p;
  }

  // ON NE LIBÈRE JAMAIS CE QUI EST À L'ÉCRAN.
  //
  // Une première version détachait la texture avant de la libérer, ce
  // qui revient à effacer l'image affichée : en descendant vite, l'écran
  // passait au gris uni avant que la suivante ne soit décodée. Une
  // texture encore liée reste, et redevient libérable au passage suivant.
  function liberer(courant) {
    for (const [i, t] of textures) {
      if (i >= courant - 1 && i <= courant + 2) continue;
      if (u.uA.value === t || u.uB.value === t) continue;
      t.dispose();
      textures.delete(i);
      ratios.delete(i);
    }
  }

  /* La transformation d'une image à une progression donnée.

     `p` peut être NÉGATIF : c'est ainsi que la scène suivante entre déjà
     en mouvement. Hors de [0, 1] la course est prolongée LINÉAIREMENT,
     sans easing — la vitesse au raccord reste donc celle du bord, et il
     n'y a pas de rupture au moment où la scène devient la scène
     courante. C'est le seul endroit du fichier où la continuité se
     joue. */
  function transformer(s, p, cible) {
    const q = p < 0 || p > 1 ? p : doux(p);
    cible.set(
      lerp(s.sc[0], s.sc[1], q),
      lerp(s.px[0], s.px[1], q),
      lerp(s.py[0], s.py[1], q),
      rad(lerp(s.rot[0], s.rot[1], q))
    );
  }

  let dernier = -1;

  /**
   * @param i      l'index de la scène courante
   * @param p      sa progression, 0 → 1
   * @param t      la transition vers la suivante, 0 → 1
   * @param sortie le fondu final vers le papier, 0 → 1
   */
  function rendre(i, p, t, sortie) {
    const s = scenes[i];
    const suivante = scenes[i + 1];

    transformer(s, p, u.uTrA.value);
    u.uFocA.value.set(s.focal[0], s.focal[1]);
    u.uRatioA.value = ratios.get(i) || 1.79;

    if (suivante) {
      transformer(suivante, -(1 - t) * PREROLL, u.uTrB.value);
      u.uFocB.value.set(suivante.focal[0], suivante.focal[1]);
      u.uRatioB.value = ratios.get(i + 1) || 1.79;
      const dx = suivante.px[1] - suivante.px[0];
      const dy = suivante.py[1] - suivante.py[0];
      u.uDir.value.set(Math.abs(dx) + Math.abs(dy) < 1e-4 ? 1 : dx, dy);
    }

    u.uMix.value = t;
    u.uSortie.value = sortie || 0;
    u.uTemps.value = i * 7.13;       // le grain est figé par scène

    if (i !== dernier) {
      dernier = i;
      charger(i).then((tex) => { if (tex && dernier === i) { u.uA.value = tex; indexA = i; } });
      charger(i + 1).then((tex) => {
        if (tex && dernier === i) { u.uB.value = tex; u.uHasB.value = 1; indexB = i + 1; }
      });
      // La suivante encore n'est demandée qu'une fois la visite
      // commencée : à l'ouverture, on ne télécharge que la façade et le
      // hall, conformément au « hero + prochaine scène » du brief.
      if (i > 0) setTimeout(() => charger(i + 2), 400);
      liberer(i);
    }
    if (!textures.has(i + 1)) u.uHasB.value = 0;

    renderer.render(scene, camera);
  }

  dimensionner();
  return {
    dimensionner,
    rendre,
    amorcer: () => charger(0).then((t) => { if (t) { u.uA.value = t; indexA = 0; } }),
    // Ouvert au diagnostic seulement. Une visite en WebGL ne se vérifie
    // pas à la capture d'écran : le canevas n'expose rien au DOM. C'est
    // ce qui permet de constater qu'un mouvement est bien MONOTONE, au
    // lieu de le croire d'après une impression.
    etat: () => ({
      indexA, indexB,
      trA: u.uTrA.value.toArray().map((v) => +v.toFixed(5)),
      trB: u.uTrB.value.toArray().map((v) => +v.toFixed(5)),
      mix: +u.uMix.value.toFixed(3),
      sortie: +u.uSortie.value.toFixed(3),
      vue: +u.uVue.value.toFixed(4),
      aPret: u.uA.value !== vide,
      bPret: u.uHasB.value === 1,
      texturesEnMemoire: [...textures.keys()].sort((a, b) => a - b),
      dpr,
    }),
    detruire() {
      for (const [, t] of textures) t.dispose();
      textures.clear();
      quad.geometry.dispose();
      quad.material.dispose();
      renderer.dispose();
    },
  };
}
