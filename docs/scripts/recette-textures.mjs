// Régression du chargement asynchrone, sans navigateur ni dépendance.
// Les deux modules de production sont exécutés tels quels dans un contexte
// isolé ; seuls WebGL, le DOM utilisé par la piste, rAF et le réseau sont
// remplacés. Le renderer conserve les uniformes réellement peints, ce qui
// permet de distinguer une image affichée d'une texture seulement chargée.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const moteurSource = readFileSync(new URL("../../frontend/landing-visite.js", import.meta.url), "utf8")
  .replace(/^import \* as THREE from .*;\r?\n/m, "")
  .replace(/export (const SCENES|function creerVisite)/g, "$1");
const pisteSource = readFileSync(new URL("../../frontend/landing-piste.js", import.meta.url), "utf8")
  .replace(/^import \{ SCENES, creerVisite \} from .*;\r?\n/m,
    "const { SCENES, creerVisite } = moteurTest;\n");

function banc() {
  const images = new Map(), demandes = [], peintures = [], raf = new Map(), delais = new Map();
  let numero = 0;
  class Vecteur {
    constructor(...valeurs) { this.set(...valeurs); }
    set(...valeurs) { this.valeurs = valeurs; return this; }
    toArray() { return [...this.valeurs]; }
  }
  class Texture {
    constructor(index = -1) {
      this.index = index;
      this.image = { width: 1920 + Math.max(0, index) * 13, height: 1071 + Math.max(0, index) * 7 };
      this.liberee = false;
    }
    dispose() { this.liberee = true; }
  }
  class ListeClasses {
    constructor(...noms) { this.noms = new Set(noms); }
    add(nom) { this.noms.add(nom); }
    remove(nom) { this.noms.delete(nom); }
    contains(nom) { return this.noms.has(nom); }
    toggle(nom, actif) { actif ? this.add(nom) : this.remove(nom); }
  }
  const element = (dataset = {}) => ({
    dataset, style: {}, classList: new ListeClasses(), hidden: false,
    removeAttribute(nom) { delete this.dataset[nom.replace(/^data-/, "")]; },
  });
  const vues = Array.from({ length: 8 }, (_, i) => element({ vue: String(i), cote: i % 2 ? "droite" : "gauche" }));
  vues[0].classList.add("is-on");
  const spacers = Array.from({ length: 9 }, () => element());
  const reperes = Array.from({ length: 4 }, (_, i) => ({ dataset: { chap: String(i + 1) }, parentNode: element() }));
  const evenements = new Map();
  const fenetre = {
    innerWidth: 1366, innerHeight: 768, devicePixelRatio: 1, scrollY: 0,
    matchMedia: () => ({ matches: false }),
    addEventListener: (nom, cb) => evenements.set(nom, cb),
    scrollTo(_x, y) { this.scrollY = y; },
  };
  const canvas = { getBoundingClientRect: () => ({ width: 1366, height: 768 }) };
  const visite = { ...element(), getBoundingClientRect: () => ({ top: -fenetre.scrollY }) };
  const elements = {
    "lc-visite": visite, "lc-canvas": canvas,
    "lc-tirages": { ...element(), querySelectorAll: () => [] },
    "lc-vues": { querySelectorAll: () => vues }, "lc-ombre": element(),
    "lc-chapters": { querySelectorAll: () => spacers }, "lc-sortie": spacers[8],
  };
  const contexte = vm.createContext({
    console, window: fenetre, location: { search: "?debug" },
    navigator: { hardwareConcurrency: 8, deviceMemory: 8 },
    document: {
      getElementById: (id) => elements[id],
      querySelectorAll: () => reperes,
      createElement: () => ({ getContext: () => ({}) }),
      addEventListener() {},
    },
    requestAnimationFrame: (cb) => { const id = ++numero; raf.set(id, cb); return id; },
    setTimeout: (cb) => { const id = ++numero; delais.set(id, cb); return id; },
    clearTimeout: (id) => delais.delete(id),
    THREE: {
      Vector2: Vecteur, Vector3: Vecteur, Vector4: Vecteur, DataTexture: Texture,
      OrthographicCamera: class {},
      Scene: class { add(quad) { this.quad = quad; } },
      PlaneGeometry: class { dispose() {} },
      ShaderMaterial: class { constructor(options) { Object.assign(this, options); } dispose() {} },
      Mesh: class { constructor(geometry, material) { Object.assign(this, { geometry, material }); } },
      WebGLRenderer: class {
        setClearColor() {} setPixelRatio() {} setSize() {} dispose() {}
        render(scene) {
          const u = scene.quad.material.uniforms;
          assert.equal(u.uA.value.liberee, false, "aucune texture libérée ne doit être peinte");
          assert.equal(u.uB.value.liberee, false, "aucune texture B libérée ne doit être peinte");
          peintures.push({
            a: u.uA.value.index, b: u.uHasB.value ? u.uB.value.index : -1,
            trA: Array.from(u.uTrA.value.toArray()), trB: Array.from(u.uTrB.value.toArray()),
            focalA: Array.from(u.uFocA.value.toArray()), ratioA: u.uRatioA.value,
            mix: u.uMix.value, sortie: u.uSortie.value,
          });
        }
      },
      TextureLoader: class {
        load(url, termine) {
          const i = contexte.moteurTest.SCENES.findIndex((s) => url.includes(s.f + ".webp"));
          assert.notEqual(i, -1, `image reconnue : ${url}`);
          assert.equal(images.has(i), false, "pas de requête doublée en cours");
          demandes.push(i);
          images.set(i, termine);
        }
      },
    },
  });
  vm.runInContext(`(() => { ${moteurSource}\nglobalThis.moteurTest = { SCENES, creerVisite }; })();`, contexte);
  vm.runInContext(pisteSource, contexte);
  return {
    demandes,
    aller: (i, p = 0.3) => fenetre.__visite.aller(i, p),
    etat: () => fenetre.__visite.etat(),
    peinture: () => peintures.at(-1),
    texte: () => Number(vues.find((v) => v.classList.contains("is-on"))?.dataset.vue),
    finir(i) {
      const termine = images.get(i);
      assert.ok(termine, `requête ${i} attendue`);
      images.delete(i);
      const texture = new Texture(i);
      termine(texture);
      return texture;
    },
    raf() {
      const callbacks = [...raf.values()];
      raf.clear();
      callbacks.forEach((cb) => cb());
    },
    delais() {
      const callbacks = [...delais.values()];
      delais.clear();
      callbacks.forEach((cb) => cb());
    },
  };
}

// Arrivée froide, puis passage vers une image déjà préchargée : aucun
// geste supplémentaire ni microtask ne doit être nécessaire pour la voir.
const visite = banc();
assert.deepEqual(visite.demandes, [0, 1], "ouverture limitée à façade + hall");
visite.finir(0);
assert.equal(visite.etat().moteur.indexA, -1, "le chargement seul ne prétend pas avoir peint");
visite.raf();
assert.equal(visite.peinture().a, 0, "la façade apparaît sans scroll");
visite.finir(1);
visite.raf();
visite.aller(1);
assert.equal(visite.peinture().a, 1, "liaison synchrone de l'image en cache");
assert.equal(visite.texte(), 1);

// Reproduction du défaut observé : grand saut, puis arrêt. L'ancien
// cadrage et son texte restent ensemble jusqu'au prochain vrai rendu.
const hall = visite.peinture();
visite.aller(4);
assert.deepEqual(visite.peinture(), hall, "le cadrage du bureau n'est pas appliqué au hall");
assert.equal(visite.texte(), 1);
visite.finir(4);
assert.equal(visite.etat().moteur.indexA, 1, "l'état décrit encore la peinture précédente");
visite.raf();
assert.equal(visite.peinture().a, 4, "arrivée du bureau après arrêt du scroll");
assert.equal(visite.texte(), 4);
assert.equal(visite.peinture().ratioA, (1920 + 4 * 13) / (1071 + 4 * 7));
visite.finir(5);
visite.raf();
visite.delais();

// Un fondu attend ses deux photographies : ni le texte suivant ni les
// transformations ne prennent de l'avance si seule A est disponible.
const bureau = visite.peinture();
visite.aller(6, 0.85);
visite.finir(6);
visite.raf();
assert.deepEqual(visite.peinture(), bureau);
assert.equal(visite.texte(), 4);
visite.finir(7);
visite.raf();
assert.equal(visite.peinture().a, 6);
assert.equal(visite.peinture().b, 7);
assert.equal(visite.texte(), 7, "texte et image suivent ensemble le fondu demandé");

// Retour puis changement d'avis avant décodage. Une réponse périmée ne
// remplace pas l'image ; seul le dernier emplacement demandé est peint.
visite.aller(1);
visite.aller(4);
assert.equal(visite.finir(1).liberee, true);
assert.equal(visite.finir(2).liberee, true);
visite.raf();
assert.equal(visite.peinture().a, 6);
visite.finir(4);
visite.raf();
assert.equal(visite.peinture().a, 4);
assert.equal(visite.texte(), 4);
assert.ok(visite.etat().moteur.texturesEnMemoire.length <= 4, "cache borné après l'arrêt");

// La façade initiale peut elle aussi arriver en retard. Elle ne doit
// jamais écraser une autre scène ; le préchargement différé est annulé
// lorsqu'on repart avant son échéance.
const froide = banc();
froide.aller(4);
froide.finir(4);
froide.raf();
assert.equal(froide.finir(0).liberee, true);
froide.raf();
assert.equal(froide.peinture().a, 4);
froide.aller(1);
froide.delais();
assert.equal(froide.demandes.includes(6), false, "pas de préchargement obsolète du bureau");
froide.finir(1);
froide.raf();
assert.equal(froide.peinture().a, 1);
assert.equal(froide.texte(), 1);
assert.ok(froide.etat().moteur.texturesEnMemoire.length <= 4);

console.log("Recette textures : chargement sans geste, cache synchrone, fondu, retours et réponses tardives vérifiés.");
