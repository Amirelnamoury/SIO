/* =====================================================================
   LA VISITE — quatorze pièces, une seule caméra
   ---------------------------------------------------------------------
   Le visiteur traverse une villa livrée. Chaque pièce est une
   photographie ; le passage de l'une à l'autre doit donner l'impression
   qu'une caméra se déplace, pas qu'un diaporama avance.

   LE MODÈLE, ET POURQUOI CELUI-LÀ
   Une photographie est plate. Faire tourner une vraie caméra 3D devant
   un plan texturé ne crée donc pas de profondeur : cela crée une
   déformation en trapèze. Le modèle retenu traite chaque image comme un
   GRAND TIRAGE posé à plat, au-dessus duquel la caméra vole :

     - avancer sur Z  →  on voit moins du tirage : c'est un travelling avant
     - se déplacer en X/Y  →  on parcourt le tirage : c'est un travelling latéral
     - une très légère rotation  →  un ou deux degrés, assez pour que
       l'angle change, trop peu pour que le trapèze se voie

   Le tirage est dimensionné 1,45 fois plus grand que ce que la caméra
   voit à sa distance de référence : les mouvements ne peuvent donc
   jamais atteindre ses bords.

   LA TRANSITION
   Un fondu enchaîné entre deux images se voit comme un fondu. Le shader
   mélange les deux textures avec un FRONT progressif, orienté selon la
   direction du mouvement de caméra de la scène qui arrive : l'image
   suivante entre par le côté vers lequel on se déplace. Le front est
   large et adouci - on ne doit pas lire un balayage, seulement sentir
   que quelque chose vient de ce côté-là.

   CE QUI EST DÉLIBÉRÉMENT ABSENT
   Aucun zoom brutal, aucune rotation spectaculaire, aucun effet de
   transition « gadget ». On vend un logiciel de gestion, pas une
   démonstration de WebGL.
   ===================================================================== */

import * as THREE from "./vendor/three.module.min.js?v=160";

const BASE = "assets/landing/villa/";

/* ---------------------------------------------------------------------
   LES QUATORZE PIÈCES
   ---------------------------------------------------------------------
   `focal` : le point de l'image qui doit rester visible, en fraction de
   largeur et de hauteur. Aucune n'est à 0.5/0.5 : chaque cadrage est
   différent, et un recadrage centré par défaut couperait le sujet sur
   la moitié d'entre elles - une baignoire en bas à gauche, un couloir
   en fuite au centre, une piscine à droite.

   `cam` : le mouvement, en unités normalisées. z = 1 est la distance de
   référence ; x et y sont des fractions de la largeur du tirage ; yaw et
   pitch sont en degrés. Le vocabulaire de caméra vient du brief, pièce
   par pièce.

   `poids` : la course de défilement accordée à la pièce, en multiples de
   la hauteur d'écran. Un couloir en fuite mérite plus de course qu'une
   salle de bain.
   --------------------------------------------------------------------- */
export const SCENES = [
  { f: "00_villa-master-facade", poids: 1.5, focal: [0.50, 0.46], cote: "bas-gauche",
    alt: "Façade d'une villa en pierre au crépuscule, entrée voûtée éclairée et jardin taillé.",
    // Façade : lent push-in vers l'entrée.
    cam: { z: [1.14, 0.94], x: [0, 0], y: [0.02, -0.01], yaw: [0, 0], pitch: [0, 0] } },

  { f: "01_hall-entree", poids: 1.15, focal: [0.62, 0.44], cote: "bas-gauche",
    alt: "Hall d'entrée, escalier tournant et lustre en fer forgé, tapis sur un sol de pierre claire.",
    // Hall : légère rotation vers la droite et montée douce.
    cam: { z: [1.02, 0.97], x: [-0.03, 0.03], y: [-0.03, 0.04], yaw: [-1.1, 1.4], pitch: [0.4, -0.3] } },

  { f: "02_salon-principal", poids: 1.25, focal: [0.48, 0.52], cote: "droite",
    alt: "Salon avec cheminée en pierre, larges baies vitrées et vue sur la piscine.",
    // Salon : travelling latéral, de la gauche vers la droite.
    cam: { z: [1.0, 0.98], x: [-0.055, 0.055], y: [0, 0], yaw: [0.5, -0.5], pitch: [0, 0] } },

  { f: "03_salle-a-manger", poids: 1.1, focal: [0.46, 0.50], cote: "gauche",
    alt: "Salle à manger, longue table en bois sous un lustre, portes-fenêtres ouvertes sur la terrasse.",
    // Salle à manger : rotation douce vers les baies.
    cam: { z: [1.0, 0.95], x: [-0.02, 0.035], y: [0, 0], yaw: [-0.6, 1.6], pitch: [0, 0] } },

  { f: "04_cuisine", poids: 1.15, focal: [0.52, 0.56], cote: "haut-gauche",
    alt: "Cuisine avec îlot central en pierre, hotte en cuivre et rangements en bois clair.",
    // Cuisine : dolly plus proche de l'îlot.
    cam: { z: [1.08, 0.88], x: [0.01, -0.01], y: [-0.02, -0.05], yaw: [0, 0], pitch: [0, 0.4] } },

  { f: "05_salon-tv-detente", poids: 1.0, focal: [0.54, 0.54], cote: "haut-gauche",
    alt: "Salon télévision, grand canapé d'angle et bibliothèque intégrée en bois sombre.",
    // Salon TV : plus intime, plus lent, presque immobile.
    cam: { z: [1.0, 0.94], x: [0.02, -0.02], y: [0, 0.01], yaw: [0.3, -0.3], pitch: [0, 0] } },

  { f: "06_bureau-bibliotheque", poids: 1.2, focal: [0.44, 0.52], cote: "droite",
    alt: "Bureau avec plans dépliés sur une table en bois, fauteuil de cuir et bibliothèque murale.",
    // Bureau : travelling diagonal vers la bibliothèque.
    cam: { z: [1.05, 0.93], x: [-0.045, 0.04], y: [0.03, -0.02], yaw: [-0.8, 1.0], pitch: [0.3, 0] } },

  { f: "07_suite-parentale", poids: 1.1, focal: [0.56, 0.52], cote: "gauche",
    alt: "Suite parentale, lit à baldaquin bas, cheminée et coin salon devant de larges fenêtres.",
    // Suite : légère ouverture, la caméra recule pour révéler l'espace.
    cam: { z: [0.90, 1.06], x: [0.02, -0.01], y: [0, 0], yaw: [0.6, -0.4], pitch: [0, 0] } },

  { f: "08_salle-bain-parentale", poids: 1.05, focal: [0.38, 0.58], cote: "droite",
    alt: "Salle de bain en pierre, baignoire îlot et douche à l'italienne sous une voûte.",
    // Salle de bain : translation latérale vers la baignoire.
    cam: { z: [0.99, 0.96], x: [0.05, -0.05], y: [0, 0.01], yaw: [-0.4, 0.6], pitch: [0, 0] } },

  { f: "09_galerie-couloir", poids: 1.45, focal: [0.50, 0.50], cote: "bas-gauche",
    alt: "Galerie voûtée bordée de tableaux, perspective vers le fond de la maison.",
    // Galerie : mouvement longitudinal, la sensation d'avancer.
    cam: { z: [1.16, 0.82], x: [0, 0], y: [0.01, 0], yaw: [0, 0], pitch: [0, 0] } },

  { f: "10_chambre-invites", poids: 1.0, focal: [0.44, 0.54], cote: "bas-gauche",
    alt: "Chambre d'amis claire, lit habillé de vert d'eau et porte-fenêtre cintrée sur le jardin.",
    // Chambre d'amis : petite rotation vers la fenêtre.
    cam: { z: [1.0, 0.96], x: [-0.02, 0.025], y: [0, 0], yaw: [-1.0, 0.9], pitch: [0, 0] } },

  { f: "11_balcon-suite", poids: 1.15, focal: [0.56, 0.52], cote: "bas-gauche",
    alt: "Balcon de la suite, fauteuils en osier, oliviers en pot et vue plongeante sur la piscine.",
    // Balcon : travelling vers l'extérieur.
    cam: { z: [1.03, 0.92], x: [-0.035, 0.03], y: [-0.01, 0.02], yaw: [-0.5, 0.8], pitch: [0, 0] } },

  { f: "12_cour-interieure-bassin", poids: 1.2, focal: [0.54, 0.52], cote: "gauche",
    alt: "Cour intérieure, arche de pierre, olivier et bassin rectangulaire.",
    // Cour : descente et push-in vers le bassin.
    cam: { z: [1.10, 0.90], x: [0, 0], y: [0.045, -0.02], yaw: [0, 0], pitch: [-0.6, 0.5] } },

  { f: "13_terrasse-piscine", poids: 1.6, focal: [0.50, 0.50], cote: "haut-droite",
    alt: "Terrasse au crépuscule, salon d'extérieur, piscine éclairée et jardin méditerranéen.",
    // Terrasse : ouverture large, finale.
    cam: { z: [0.88, 1.12], x: [0.02, -0.02], y: [-0.02, 0.02], yaw: [0.4, -0.4], pitch: [0, 0] } },
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

const FRAG = `
precision highp float;
varying vec2 vUv;

uniform sampler2D uA;
uniform sampler2D uB;
uniform float uMix;        // 0 = image A, 1 = image B
uniform float uHasB;       // la texture suivante est-elle prete ?
uniform vec2  uDir;        // direction d'ou vient l'image suivante
uniform vec2  uParaA;      // parallaxe UV, image A
uniform vec2  uParaB;
uniform float uVignette;
uniform float uGrain;
uniform float uTime;

// Un bruit suffisant pour casser le banding d'un degrade sombre. Il n'a
// pas besoin d'etre beau, il a besoin d'etre stable et bon marche.
float bruit(vec2 p) {
  return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
  vec3 a = texture2D(uA, clamp(vUv + uParaA, 0.001, 0.999)).rgb;
  vec3 b = texture2D(uB, clamp(vUv + uParaB, 0.001, 0.999)).rgb;

  // LE FRONT. Plutot qu'un fondu uniforme, l'image suivante entre par le
  // cote vers lequel la camera se deplace. La variable d vaut 0 du cote
  // d'ou elle vient et 1 a l'oppose ; le front balaie cet axe, adouci sur
  // 55 % de la largeur pour qu'on ne lise jamais une ligne.
  //
  // (Aucun accent grave dans ce commentaire : il vit DANS un litteral de
  // gabarit, et un accent grave y terminerait la chaine. C'est ce qui
  // s'est produit au premier jet - le navigateur signalait alors une
  // erreur de syntaxe a la ligne suivante, loin de sa cause.)
  float d = dot(vUv - 0.5, normalize(uDir + vec2(1e-5))) + 0.5;
  float front = smoothstep(d - 0.55, d + 0.55, uMix * 2.0 - 0.5 + d);
  float m = mix(uMix, front, 0.65) * uHasB;

  vec3 c = mix(a, b, clamp(m, 0.0, 1.0));

  // Vignette tres legere : elle assoit l'image et aide le texte pose
  // dessus, sans jamais se lire comme un cadre.
  float r = distance(vUv, vec2(0.5));
  c *= 1.0 - uVignette * smoothstep(0.34, 0.92, r);

  // Grain : le meme sur les quatorze images, ce qui les lie entre elles.
  c += (bruit(vUv * 900.0 + uTime) - 0.5) * uGrain;

  gl_FragColor = vec4(c, 1.0);
}`;

/* =====================================================================
   LE MOTEUR
   ===================================================================== */

const rad = (d) => (d * Math.PI) / 180;
const lerp = (a, b, t) => a + (b - a) * t;
// Un easing cinematographique : depart et arrivee amortis, jamais de
// depart sec. C'est ce qui distingue un mouvement de camera d'un
// glissement lineaire.
const doux = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

// Un point d'observation, ouvert uniquement par `?debug` dans l'adresse.
// Sans lui, une visite en WebGL ne se verifie qu'a l'oeil : le canevas ne
// se lit pas depuis le DOM, et sa memoire d'image est effacee apres chaque
// rendu. `preserveDrawingBuffer` a un cout reel - il n'est donc active que
// dans ce mode, jamais pour un visiteur.
const DEBUG = typeof location !== "undefined" && /(?:^|[?&])debug(?:=|&|$)/.test(location.search);

export function creerVisite({ canvas, scenes, petit }) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: false,      // les photographies n'ont pas d'aretes a lisser
    alpha: false,
    powerPreference: "high-performance",
    preserveDrawingBuffer: DEBUG,
  });
  renderer.setClearColor(0x20282c, 1);

  const scene = new THREE.Scene();
  const FOV = 42;
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 100);

  const blanche = new THREE.DataTexture(new Uint8Array([32, 40, 44, 255]), 1, 1, THREE.RGBAFormat);
  blanche.needsUpdate = true;

  const uniforms = {
    uA: { value: blanche }, uB: { value: blanche },
    uMix: { value: 0 }, uHasB: { value: 0 },
    uDir: { value: new THREE.Vector2(1, 0) },
    uParaA: { value: new THREE.Vector2(0, 0) },
    uParaB: { value: new THREE.Vector2(0, 0) },
    uVignette: { value: 0.34 }, uGrain: { value: 0.028 }, uTime: { value: 0 },
  };

  const tirage = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms, depthTest: false })
  );
  scene.add(tirage);

  // Distance de reference : celle a laquelle la camera voit exactement la
  // hauteur du tirage utile. Le tirage est ensuite agrandi de MARGE pour
  // qu'aucun mouvement n'atteigne ses bords.
  const MARGE = 1.45;
  let zRef = 1, largeurTirage = 1, hauteurTirage = 1;
  let W = 0, H = 0, dpr = 1;

  function dimensionner() {
    const r = canvas.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width));
    H = Math.max(1, Math.round(r.height));
    // Le DPR est plafonne : au-dela de 2 on paie des pixels que personne
    // ne distingue sur une photographie, et on fait chauffer le telephone.
    dpr = Math.min(window.devicePixelRatio || 1, petit ? 1.6 : 2);
    renderer.setPixelRatio(dpr);
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    camera.updateProjectionMatrix();

    // La hauteur vue par la camera a la distance 1.
    const hVue = 2 * Math.tan(rad(FOV) / 2);
    zRef = 1 / hVue;                       // pour que la hauteur vue vaille 1
    hauteurTirage = MARGE;
    largeurTirage = MARGE * camera.aspect;
    tirage.scale.set(largeurTirage, hauteurTirage, 1);
  }

  // -------------------------------------------------------------------
  // Les textures : une fenetre glissante, jamais les quatorze a la fois.
  // Quatorze textures 1920 px tiennent environ 110 Mo en memoire video -
  // de quoi faire tomber un telephone. On garde la scene courante, la
  // precedente et les deux suivantes ; le reste est libere.
  // -------------------------------------------------------------------
  const chargeur = new THREE.TextureLoader();
  const textures = new Map();
  const enCours = new Map();

  function url(i) {
    return BASE + scenes[i].f + (petit ? "-sm" : "") + ".webp";
  }

  function charger(i) {
    if (i < 0 || i >= scenes.length) return Promise.resolve(null);
    if (textures.has(i)) return Promise.resolve(textures.get(i));
    if (enCours.has(i)) return enCours.get(i);
    const p = new Promise((resoudre) => {
      chargeur.load(url(i), (t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.minFilter = THREE.LinearFilter;   // pas de mipmaps : on ne reduit jamais
        t.magFilter = THREE.LinearFilter;
        t.generateMipmaps = false;
        t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
        textures.set(i, t);
        enCours.delete(i);
        resoudre(t);
      }, undefined, () => { enCours.delete(i); resoudre(null); });
    });
    enCours.set(i, p);
    return p;
  }

  // ON NE LIBERE JAMAIS CE QUI EST A L'ECRAN.
  //
  // La premiere version detachait la texture avant de la liberer :
  //   if (uniforms.uA.value === t) uniforms.uA.value = blanche;
  // ce qui revient a effacer l'image affichee. En descendant vite - ou
  // simplement quand le reseau est plus lent que le pouce - l'image
  // courante etait donc rendue au gris uni avant que la suivante ne soit
  // decodee, et l'ecran clignotait. Mesure : sur un parcours rapide des
  // quatorze pieces, le nombre de textures en memoire tombait a zero et
  // l'image ne revenait plus.
  //
  // La regle est l'inverse : une texture encore liee reste, et redevient
  // liberable au passage suivant, une fois remplacee.
  function liberer(courant) {
    for (const [i, t] of textures) {
      if (i >= courant - 1 && i <= courant + 2) continue;
      if (uniforms.uA.value === t || uniforms.uB.value === t) continue;
      t.dispose();
      textures.delete(i);
    }
  }

  // -------------------------------------------------------------------
  // Le rendu. `index` est la piece, `p` la progression dans cette piece
  // (0 a 1), `t` la progression de la transition vers la suivante.
  // -------------------------------------------------------------------
  let dernierIndex = -1;
  let indexA = -1, indexB = -1;

  function rendre(index, p, t) {
    const s = scenes[index];
    const suivante = scenes[index + 1];
    const e = doux(p);

    // La camera. `focal` decale son point de visee sur le tirage pour
    // que le sujet de la piece reste dans le champ.
    const fx = (s.focal[0] - 0.5) * (largeurTirage - 1) * 0.9;
    const fy = (0.5 - s.focal[1]) * (hauteurTirage - 1) * 0.9;
    const z = lerp(s.cam.z[0], s.cam.z[1], e);
    camera.position.set(
      fx + lerp(s.cam.x[0], s.cam.x[1], e) * largeurTirage,
      fy + lerp(s.cam.y[0], s.cam.y[1], e) * hauteurTirage,
      zRef * z
    );
    camera.rotation.set(
      rad(lerp(s.cam.pitch[0], s.cam.pitch[1], e)),
      rad(lerp(s.cam.yaw[0], s.cam.yaw[1], e)),
      0
    );

    // La parallaxe : le contenu de l'image glisse tres legerement dans
    // son propre cadre, a contre-sens du deplacement. Ce n'est pas de la
    // profondeur reelle - une photographie n'en a pas - mais c'est ce
    // qui empeche l'image de se lire comme un simple aplat qu'on
    // recadre.
    const px = (lerp(s.cam.x[0], s.cam.x[1], e)) * -0.10;
    const py = (lerp(s.cam.y[0], s.cam.y[1], e)) * 0.10;
    uniforms.uParaA.value.set(px, py);

    if (suivante) {
      const dx = suivante.cam.x[1] - suivante.cam.x[0];
      const dy = suivante.cam.y[1] - suivante.cam.y[0];
      uniforms.uDir.value.set(Math.abs(dx) + Math.abs(dy) < 1e-4 ? 1 : dx, dy);
      uniforms.uParaB.value.set(px * 0.4, py * 0.4);
    }
    uniforms.uMix.value = t;
    uniforms.uTime.value = index * 7.13;   // fige le grain par scene

    if (index !== dernierIndex) {
      dernierIndex = index;
      charger(index).then((tex) => { if (tex && dernierIndex === index) { uniforms.uA.value = tex; indexA = index; } });
      charger(index + 1).then((tex) => {
        if (tex && dernierIndex === index) { uniforms.uB.value = tex; uniforms.uHasB.value = 1; indexB = index + 1; }
      });
      // La suivante encore est demandee sans etre attendue - mais PAS a
      // l'ouverture. Sur la facade, cela faisait trois photographies
      // (610 Ko) avant meme que le visiteur ait touche a sa molette,
      // alors que le brief demande « hero + prochaine scene ». Elle
      // n'est prefetchee qu'une fois la visite reellement commencee.
      if (index > 0) setTimeout(() => charger(index + 2), 400);
      liberer(index);
    }
    if (!textures.has(index + 1)) uniforms.uHasB.value = 0;

    renderer.render(scene, camera);
  }

  dimensionner();
  const moteur = {
    dimensionner,
    rendre,
    // Ouvert au diagnostic seulement : ou est la camera, quelles textures
    // sont en memoire. C'est ce qui permet de verifier qu'un mouvement de
    // camera est bien DIFFERENT d'une piece a l'autre, au lieu de le
    // croire d'apres une capture d'ecran.
    etat: () => ({
      camera: {
        x: +camera.position.x.toFixed(4),
        y: +camera.position.y.toFixed(4),
        z: +camera.position.z.toFixed(4),
        yaw: +(camera.rotation.y * 180 / Math.PI).toFixed(3),
        pitch: +(camera.rotation.x * 180 / Math.PI).toFixed(3),
      },
      texturesEnMemoire: [...textures.keys()].sort((a, b) => a - b),
      mix: +uniforms.uMix.value.toFixed(3),
      aPret: uniforms.uA.value !== blanche,
      bPret: uniforms.uHasB.value === 1,
      // Quelle scene est reellement a l'ecran, pas seulement « une » scene.
      indexA, indexB,
    }),
    // Le tout premier chargement, attendu : il conditionne la premiere
    // image de la page.
    amorcer: () => charger(0).then((t) => { if (t) uniforms.uA.value = t; }),
    detruire() {
      for (const [, t] of textures) t.dispose();
      textures.clear();
      tirage.geometry.dispose();
      tirage.material.dispose();
      renderer.dispose();
    },
  };
  return moteur;
}
