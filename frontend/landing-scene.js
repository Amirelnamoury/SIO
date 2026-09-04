// =====================================================================
// Suite Artisan — landing-scene.js
// -----------------------------------------------------------------------
// Scene 3D procedurale (Three.js) pour la landing publique : une maison /
// un chantier construit entierement avec des geometries primitives
// (BoxGeometry, CylinderGeometry, TubeGeometry, ExtrudeGeometry...), sans
// aucun modele externe (.glb/.gltf) — voir README dans
// frontend/assets/landing/ pour la note de provenance.
//
// Ce module expose une API minimale utilisee par landing.js :
//   initScene(canvas)         -> cree le renderer/scene/camera, demarre
//                                 la boucle de rendu, renvoie un handle.
//   updateScene(handle, p)    -> p = progression 0..1 sur toute la
//                                 timeline narrative ; positionne camera,
//                                 materiaux, visibilite, lumieres.
//   resizeScene(handle)       -> a rappeler sur resize/orientationchange.
//   setQuality(handle, low)   -> reduit DPR/ombres/segments (mobile).
//   disposeScene(handle)      -> stoppe la boucle et libere le GPU.
//
// Aucune dependance a GSAP/ScrollTrigger ici : la progression 0..1 est
// calculee par landing.js (scroll natif) et simplement consommee.
// =====================================================================

import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";

// ---------- Palette (coherente avec landing.css : --landing-* tokens) ----------
const COLOR = {
  bg: 0x0b0a08,
  concrete: 0x8d867c,
  concreteDark: 0x5c564e,
  plasterRaw: 0x9a9187,
  plasterDone: 0xefe7d8, // beige chaud, mur "fini"
  wood: 0x6b4a34,
  woodLight: 0x8a6547,
  glassTint: 0x9fb3bd,
  metal: 0x707478,
  brass: 0xc7a15a, // laiton / champagne
  brassBright: 0xe4c988,
  copper: 0xb5714a,
  roof: 0x2b2a28,
  sofaFabric: 0x3c332a,
  paperCream: 0xf1ead9,
  emberWarm: 0xffb066,
  emberCool: 0x9fd0ff,
};

// ---------- Petit utilitaire de courbe d'acceleration (cinematique) ----------
function smoothstep(edge0, edge1, x) {
  const t = Math.min(1, Math.max(0, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}
function lerp(a, b, t) { return a + (b - a) * t; }
function lerpColorHex(hexA, hexB, t, out) {
  const a = new THREE.Color(hexA);
  const b = new THREE.Color(hexB);
  return (out || new THREE.Color()).copy(a).lerp(b, t);
}

// ---------- Materiaux partages (crees une fois, reutilises) ----------
function buildMaterials() {
  return {
    concrete: new THREE.MeshStandardMaterial({ color: COLOR.concrete, roughness: 0.95, metalness: 0.02 }),
    concreteDark: new THREE.MeshStandardMaterial({ color: COLOR.concreteDark, roughness: 0.9, metalness: 0.02 }),
    // Murs interieurs : couleur/roughness animes (brut -> fini) sur la piece
    // renovation ; les autres murs interieurs restent proches du "brut".
    plaster: new THREE.MeshStandardMaterial({ color: COLOR.plasterRaw, roughness: 0.85, metalness: 0.0 }),
    renoWall: new THREE.MeshStandardMaterial({ color: COLOR.plasterRaw, roughness: 0.9, metalness: 0.0 }),
    exterior: new THREE.MeshStandardMaterial({ color: COLOR.concreteDark, roughness: 0.8, metalness: 0.05, transparent: true, opacity: 1 }),
    roof: new THREE.MeshStandardMaterial({ color: COLOR.roof, roughness: 0.6, metalness: 0.3, transparent: true, opacity: 1 }),
    glass: new THREE.MeshPhysicalMaterial({ color: COLOR.glassTint, roughness: 0.05, metalness: 0, transmission: 0.85, transparent: true, opacity: 0.55, thickness: 0.2 }),
    wood: new THREE.MeshStandardMaterial({ color: COLOR.wood, roughness: 0.7, metalness: 0.05 }),
    woodLight: new THREE.MeshStandardMaterial({ color: COLOR.woodLight, roughness: 0.65, metalness: 0.05 }),
    metal: new THREE.MeshStandardMaterial({ color: COLOR.metal, roughness: 0.35, metalness: 0.85 }),
    chrome: new THREE.MeshStandardMaterial({ color: 0xd8dadc, roughness: 0.15, metalness: 0.95 }),
    brass: new THREE.MeshStandardMaterial({ color: COLOR.brass, roughness: 0.3, metalness: 0.85 }),
    ceramic: new THREE.MeshStandardMaterial({ color: 0xf4f1ea, roughness: 0.25, metalness: 0.0 }),
    rubber: new THREE.MeshStandardMaterial({ color: 0x1c1a18, roughness: 0.75, metalness: 0.1 }),
    copper: new THREE.MeshStandardMaterial({ color: COLOR.copper, roughness: 0.35, metalness: 0.8 }),
    panelBody: new THREE.MeshStandardMaterial({ color: 0x2a2c2e, roughness: 0.5, metalness: 0.4 }),
    emissiveWarm: new THREE.MeshStandardMaterial({ color: COLOR.emberWarm, emissive: COLOR.emberWarm, emissiveIntensity: 0, roughness: 0.4, metalness: 0.2 }),
    sofa: new THREE.MeshStandardMaterial({ color: COLOR.sofaFabric, roughness: 0.95, metalness: 0.0 }),
    paper: new THREE.MeshStandardMaterial({ color: COLOR.paperCream, roughness: 0.9, metalness: 0.0, side: THREE.DoubleSide }),
    ground: new THREE.MeshStandardMaterial({ color: 0x141210, roughness: 1, metalness: 0.0 }),
  };
}

// ---------- Construction procedurale de la maison ----------
function buildHouse(mats) {
  const house = new THREE.Group();
  house.name = "House";

  // Empreinte : X in [-4,4] (8 large), Z in [-3,3] (6 profond), murs h=3.
  const W = 8, D = 6, H = 3;

  // ---------- Sol / dalle ----------
  const floor = new THREE.Mesh(new THREE.BoxGeometry(W, 0.2, D), mats.concrete);
  floor.position.y = -0.1;
  floor.receiveShadow = true;
  floor.name = "Floor";
  house.add(floor);

  // ---------- Groupe murs exterieurs ----------
  const exteriorWalls = new THREE.Group();
  exteriorWalls.name = "ExteriorWalls";
  const wallThickness = 0.2;
  const backWall = new THREE.Mesh(new THREE.BoxGeometry(W, H, wallThickness), mats.exterior);
  backWall.position.set(0, H / 2, -D / 2);
  const leftWall = new THREE.Mesh(new THREE.BoxGeometry(wallThickness, H, D), mats.exterior);
  leftWall.position.set(-W / 2, H / 2, 0);
  const rightWall = new THREE.Mesh(new THREE.BoxGeometry(wallThickness, H, D), mats.exterior);
  rightWall.position.set(W / 2, H / 2, 0);
  // Facade avant avec ouverture porte (2 segments + linteau)
  const frontLeft = new THREE.Mesh(new THREE.BoxGeometry(W * 0.32, H, wallThickness), mats.exterior);
  frontLeft.position.set(-W * 0.34, H / 2, D / 2);
  const frontRight = new THREE.Mesh(new THREE.BoxGeometry(W * 0.32, H, wallThickness), mats.exterior);
  frontRight.position.set(W * 0.34, H / 2, D / 2);
  const frontLintel = new THREE.Mesh(new THREE.BoxGeometry(W * 0.36, H * 0.28, wallThickness), mats.exterior);
  frontLintel.position.set(0, H - (H * 0.14), D / 2);
  [backWall, leftWall, rightWall, frontLeft, frontRight, frontLintel].forEach((m) => { m.castShadow = true; m.receiveShadow = true; exteriorWalls.add(m); });
  house.add(exteriorWalls);

  // ---------- Fenetres (verre) ----------
  const windows = new THREE.Group();
  windows.name = "Windows";
  const winGeo = new THREE.PlaneGeometry(1.4, 1.1);
  const winPositions = [
    [-2.6, 1.7, -D / 2 + 0.01, 0],
    [2.6, 1.7, -D / 2 + 0.01, 0],
    [-W / 2 + 0.01, 1.7, -1.4, Math.PI / 2],
    [W / 2 - 0.01, 1.7, 1.2, -Math.PI / 2],
  ];
  winPositions.forEach(([x, y, z, ry]) => {
    const w = new THREE.Mesh(winGeo, mats.glass);
    w.position.set(x, y, z);
    w.rotation.y = ry;
    windows.add(w);
  });
  house.add(windows);

  // ---------- Toit (2 pans + pignons), groupe independant ----------
  const roof = new THREE.Group();
  roof.name = "Roof";
  const slopeLen = Math.sqrt((D / 2) * (D / 2) + 1.6 * 1.6);
  const slopeAngle = Math.atan2(1.6, D / 2);
  const slopeGeo = new THREE.BoxGeometry(W + 0.6, 0.12, slopeLen);
  const slopeA = new THREE.Mesh(slopeGeo, mats.roof);
  slopeA.position.set(0, H + 0.85, -D / 4);
  slopeA.rotation.x = slopeAngle;
  const slopeB = new THREE.Mesh(slopeGeo, mats.roof);
  slopeB.position.set(0, H + 0.85, D / 4);
  slopeB.rotation.x = -slopeAngle;
  roof.add(slopeA, slopeB);
  // Pignons (triangles) via ShapeGeometry
  const gableShape = new THREE.Shape();
  gableShape.moveTo(-W / 2, 0);
  gableShape.lineTo(W / 2, 0);
  gableShape.lineTo(0, 1.6);
  gableShape.lineTo(-W / 2, 0);
  const gableGeo = new THREE.ShapeGeometry(gableShape);
  const gableFront = new THREE.Mesh(gableGeo, mats.exterior);
  gableFront.position.set(0, H, D / 2);
  const gableBack = new THREE.Mesh(gableGeo, mats.exterior);
  gableBack.position.set(0, H, -D / 2);
  gableBack.rotation.y = Math.PI;
  roof.add(gableFront, gableBack);
  roof.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  house.add(roof);

  // ---------- Murs interieurs (2 cloisons) ----------
  const interiorWalls = new THREE.Group();
  interiorWalls.name = "InteriorWalls";
  const div1 = new THREE.Mesh(new THREE.BoxGeometry(0.12, H, D * 0.62), mats.plaster);
  div1.position.set(-1.3, H / 2, -D * 0.12);
  const div2 = new THREE.Mesh(new THREE.BoxGeometry(0.12, H, D * 0.5), mats.plaster);
  div2.position.set(1.0, H / 2, D * 0.05);
  [div1, div2].forEach((m) => { m.castShadow = true; m.receiveShadow = true; interiorWalls.add(m); });
  house.add(interiorWalls);

  // Mur du fond de la piece "renovation", materiau anime separement
  const renoWallMesh = new THREE.Mesh(new THREE.BoxGeometry(W * 0.32 - 0.1, H - 0.1, 0.1), mats.renoWall);
  renoWallMesh.position.set(2.55, (H - 0.1) / 2, -D / 2 + 0.11);
  renoWallMesh.castShadow = true;
  renoWallMesh.receiveShadow = true;
  renoWallMesh.name = "RenoWall";
  house.add(renoWallMesh);

  // ===================== Salle de bain (plomberie) =====================
  const bathroom = new THREE.Group();
  bathroom.name = "Bathroom";
  bathroom.position.set(-2.6, 0, -0.6);

  const sink = new THREE.Group();
  sink.name = "Sink";
  const basin = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.24, 0.18, 24), mats.ceramic);
  basin.position.set(0, 0.85, 0);
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.75, 12), mats.ceramic);
  stand.position.set(0, 0.42, 0);
  const tap = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.22, 8), mats.chrome);
  tap.position.set(0, 1.02, -0.12);
  sink.add(basin, stand, tap);
  sink.position.set(-1.1, 0, 0.9);
  bathroom.add(sink);

  const shower = new THREE.Group();
  shower.name = "Shower";
  const showerTray = new THREE.Mesh(new THREE.BoxGeometry(1, 0.08, 1), mats.ceramic);
  showerTray.position.set(0, 0.04, 0);
  const showerGlass = new THREE.Mesh(new THREE.PlaneGeometry(1, 2), mats.glass);
  showerGlass.position.set(0, 1.05, 0.5);
  const showerHead = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.05, 12), mats.chrome);
  showerHead.position.set(0.35, 2.05, 0);
  shower.add(showerTray, showerGlass, showerHead);
  shower.position.set(0.9, 0, -1.1);
  bathroom.add(shower);

  // Reseau de tuyaux : une TubeGeometry (courbe) = le collecteur principal,
  // + 2 embranchements courts vers sink/shower.
  const pipes = new THREE.Group();
  pipes.name = "Pipes";
  const pipeCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-1.1, 0.05, 1.3),
    new THREE.Vector3(-1.1, 0.05, 0.2),
    new THREE.Vector3(-0.2, 0.05, -0.3),
    new THREE.Vector3(0.9, 0.05, -1.1),
  ]);
  const pipeTube = new THREE.Mesh(new THREE.TubeGeometry(pipeCurve, 48, 0.045, 8, false), mats.copper);
  pipes.add(pipeTube);
  const branch1 = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.75, 8), mats.copper);
  branch1.position.set(-1.1, 0.42, 1.1);
  const branch2 = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.45, 8), mats.copper);
  branch2.position.set(0.9, 0.25, -1.05);
  pipes.add(branch1, branch2);
  // Petite bille emissive qui "coule" le long du collecteur (flux visuel).
  const flowBead = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 12), mats.emissiveWarm);
  pipes.add(flowBead);
  pipes.userData.curve = pipeCurve;
  pipes.userData.bead = flowBead;
  bathroom.add(pipes);

  bathroom.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  house.add(bathroom);

  // ===================== Electricite =====================
  const electrical = new THREE.Group();
  electrical.name = "Electrical";
  electrical.position.set(-0.15, 0, -2.2);

  const panel = new THREE.Group();
  panel.name = "Panel";
  const panelBody = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.8, 0.12), mats.panelBody);
  panelBody.position.set(0, 1.5, 0.05);
  panel.add(panelBody);
  const breakerGeo = new THREE.BoxGeometry(0.08, 0.16, 0.03);
  const breakerMesh = new THREE.InstancedMesh(breakerGeo, mats.brass, 6);
  const m4 = new THREE.Matrix4();
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    m4.makeTranslation(-0.16 + col * 0.16, 1.68 - row * 0.22, 0.12);
    breakerMesh.setMatrixAt(i, m4);
  }
  panel.add(breakerMesh);
  electrical.add(panel);

  // Cables : 3 TubeGeometry du panneau vers des points muraux (reveles
  // progressivement via morphTarget-like : on anime plutot le "drawRange"
  // via geometry.setDrawRange n'est pas trivial sur TubeGeometry indexee ;
  // on anime donc l'opacite + une legere echelle en Y pour simuler le tirage).
  const cables = new THREE.Group();
  cables.name = "Cables";
  const cableMat = mats.rubber;
  const cableTargets = [
    [[0, 1.3, 0.1], [0.9, 1.3, 0.9], [1.6, 0.9, 1.6]],
    [[0, 1.1, 0.1], [-0.7, 0.9, 0.6], [-1.1, 0.6, 1.3]],
    [[0, 1.0, 0.1], [0.1, 0.5, 1.0], [0.1, 0.15, 1.8]],
  ];
  cableTargets.forEach((pts) => {
    const curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)));
    const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 24, 0.025, 6, false), cableMat.clone());
    tube.material.transparent = true;
    cables.add(tube);
  });
  electrical.add(cables);

  // Prises (sockets) : petites plaques + point emissif "sous tension".
  const sockets = new THREE.Group();
  sockets.name = "Sockets";
  const socketPlateGeo = new THREE.BoxGeometry(0.14, 0.14, 0.02);
  const socketDotGeo = new THREE.SphereGeometry(0.02, 8, 8);
  const socketPositions = [[1.6, 0.5, 1.6], [-1.1, 0.35, 1.3], [0.1, 0.12, 1.85]];
  socketPositions.forEach((p) => {
    const plate = new THREE.Mesh(socketPlateGeo, mats.ceramic);
    plate.position.set(...p);
    const dot = new THREE.Mesh(socketDotGeo, mats.emissiveWarm.clone());
    dot.position.set(p[0], p[1], p[2] + 0.02);
    sockets.add(plate, dot);
  });
  electrical.add(sockets);

  electrical.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  house.add(electrical);

  // ===================== Renovation / chantier =====================
  const construction = new THREE.Group();
  construction.name = "Construction";
  construction.position.set(2.5, 0, -0.3);

  const ladder = new THREE.Group();
  ladder.name = "Ladder";
  const railGeo = new THREE.BoxGeometry(0.06, 1.8, 0.06);
  const railL = new THREE.Mesh(railGeo, mats.wood);
  railL.position.set(-0.22, 0.9, 0);
  const railR = new THREE.Mesh(railGeo, mats.wood);
  railR.position.set(0.22, 0.9, 0);
  ladder.add(railL, railR);
  for (let i = 0; i < 5; i++) {
    const rung = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.04, 0.04), mats.wood);
    rung.position.set(0, 0.25 + i * 0.35, 0);
    ladder.add(rung);
  }
  ladder.position.set(0.9, 0, 0.9);
  ladder.rotation.y = 0.25;
  construction.add(ladder);

  const paintCan = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.22, 16), mats.metal);
  paintCan.position.set(1.2, 0.11, 0.4);
  construction.add(paintCan);

  const boards = new THREE.Group();
  for (let i = 0; i < 3; i++) {
    const board = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.03, 0.22), mats.woodLight);
    board.position.set(-0.6, 0.03 + i * 0.035, 0.7);
    boards.add(board);
  }
  construction.add(boards);

  // Meubles "piece terminee" — caches au depart, reveles a la fin de la scene.
  const furniture = new THREE.Group();
  furniture.name = "Furniture";
  const sofaBase = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.4, 0.6), mats.sofa);
  sofaBase.position.set(0.6, 0.2, -1.5);
  const sofaBack = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.5, 0.15), mats.sofa);
  sofaBack.position.set(0.6, 0.5, -1.75);
  const artFrame = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.8, 0.03), mats.brass);
  artFrame.position.set(2.5, 1.5, -D / 2 + 0.15);
  furniture.add(sofaBase, sofaBack, artFrame);
  furniture.visible = false;
  construction.add(furniture);

  construction.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  house.add(construction);

  // ===================== Documents / suivi terrain =====================
  const documents = new THREE.Group();
  documents.name = "Documents";
  const plan = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.6), mats.paper);
  plan.rotation.x = -Math.PI / 2.3;
  plan.position.set(1.7, 0.75, 0.6);
  const photo = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.3), mats.paper);
  photo.rotation.set(-Math.PI / 2.6, 0, 0.12);
  photo.position.set(2.3, 0.76, 0.9);
  documents.add(plan, photo);
  documents.visible = false;
  house.add(documents);

  // ===================== Details chantier exterieur (hero) =====================
  const yardDetails = new THREE.Group();
  yardDetails.name = "YardDetails";
  const crate = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.5, 0.6), mats.wood);
  crate.position.set(-4.8, 0.25, 2.4);
  crate.rotation.y = 0.3;
  const brickStackGeo = new THREE.BoxGeometry(0.5, 0.28, 0.3);
  const brickStack = new THREE.InstancedMesh(brickStackGeo, mats.concreteDark, 4);
  for (let i = 0; i < 4; i++) {
    m4.makeTranslation(5.1, 0.14 + i * 0.29, 2.0 - i * 0.02);
    brickStack.setMatrixAt(i, m4);
  }
  yardDetails.add(crate, brickStack);
  yardDetails.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  house.add(yardDetails);

  return {
    house, exteriorWalls, windows, roof, interiorWalls, renoWallMesh,
    bathroom, pipes, electrical, cables, sockets,
    construction, furniture, documents, yardDetails,
  };
}

// ---------- Timeline camera (positions cles, interpolees + easing) ----------
const CAMERA_KEYS = [
  { t: 0.00, pos: [9.5, 5.6, 11.5], look: [0, 1.8, 0] },     // Hero exterieur
  { t: 0.10, pos: [6.2, 3.4, 7.4], look: [0, 1.5, 1.1] },     // Approche / prospect
  { t: 0.20, pos: [1.4, 2.6, 3.2], look: [-2.2, 1.3, 0] },    // Entree
  { t: 0.35, pos: [-2.8, 1.9, 1.1], look: [-3.3, 1.1, -1.0] },// Plomberie
  { t: 0.48, pos: [-0.4, 2.1, 1.7], look: [-0.15, 1.5, -1.6] },// Electricite
  { t: 0.62, pos: [1.6, 1.9, 2.2], look: [2.6, 1.3, -0.6] },  // Renovation
  { t: 0.72, pos: [2.2, 2.2, 3.0], look: [2.4, 1.2, -0.1] },  // Documents
  { t: 0.82, pos: [4.6, 3.4, 6.2], look: [0.4, 1.6, 0] },     // Finances (recul)
  { t: 0.90, pos: [7.4, 4.3, 9.2], look: [0, 1.8, 0] },       // Maison terminee
  { t: 1.00, pos: [13, 6.6, 16], look: [0, 1.5, 0] },         // Transition -> SaaS
];

function sampleCamera(progress, out) {
  const keys = CAMERA_KEYS;
  let i = 0;
  while (i < keys.length - 2 && progress > keys[i + 1].t) i++;
  const a = keys[i], b = keys[i + 1];
  const span = b.t - a.t || 1;
  const localT = smoothstep(0, 1, (progress - a.t) / span);
  out.pos.set(lerp(a.pos[0], b.pos[0], localT), lerp(a.pos[1], b.pos[1], localT), lerp(a.pos[2], b.pos[2], localT));
  out.look.set(lerp(a.look[0], b.look[0], localT), lerp(a.look[1], b.look[1], localT), lerp(a.look[2], b.look[2], localT));
}

// ---------- Init ----------
export function initScene(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(COLOR.bg, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(COLOR.bg, 14, 34);

  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);

  const hemi = new THREE.HemisphereLight(0xcbd5df, 0x141210, 0.55);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xdfe6ee, 1.15);
  key.position.set(6, 9, 5);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.left = -10; key.shadow.camera.right = 10;
  key.shadow.camera.top = 10; key.shadow.camera.bottom = -10;
  key.shadow.camera.far = 30;
  key.shadow.bias = -0.0025;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8fa2c0, 0.25);
  fill.position.set(-6, 4, -4);
  scene.add(fill);
  const accent = new THREE.PointLight(COLOR.brassBright, 0, 8, 2);
  accent.position.set(-1.5, 2.2, 0.5);
  scene.add(accent);

  const mats = buildMaterials();
  const parts = buildHouse(mats);
  scene.add(parts.house);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), mats.ground);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.2;
  ground.receiveShadow = true;
  scene.add(ground);

  const handle = {
    renderer, scene, camera, mats, parts,
    cameraSample: { pos: new THREE.Vector3(), look: new THREE.Vector3() },
    lowQuality: false,
    running: true,
    rafId: 0,
    lastProgress: 0,
    clock: new THREE.Clock(),
  };

  resizeScene(handle);
  handle.rafId = requestAnimationFrame(() => renderLoop(handle));
  return handle;
}

function renderLoop(handle) {
  if (!handle.running) return;
  const t = handle.clock.getElapsedTime();
  // Bille de flux dans le tuyau : boucle independante du scroll, tres subtile.
  const pipes = handle.parts.pipes;
  if (pipes && pipes.userData.curve && pipes.visible) {
    const pt = pipes.userData.curve.getPointAt((t * 0.12) % 1);
    pipes.userData.bead.position.copy(pt);
  }
  handle.renderer.render(handle.scene, handle.camera);
  handle.rafId = requestAnimationFrame(() => renderLoop(handle));
}

// ---------- Update piloté par le scroll (0..1) ----------
export function updateScene(handle, progress) {
  progress = Math.min(1, Math.max(0, progress));
  handle.lastProgress = progress;
  const { camera, mats, parts, cameraSample } = handle;

  sampleCamera(progress, cameraSample);
  camera.position.copy(cameraSample.pos);
  camera.lookAt(cameraSample.look);

  // --- Toit : visible sur le hero, disparait tot (vue cutaway) ---
  const roofOpacity = 1 - smoothstep(0.04, 0.15, progress);
  mats.roof.opacity = roofOpacity;
  parts.roof.visible = roofOpacity > 0.01;

  // --- Murs exterieurs : s'effacent pour laisser voir l'interieur, puis
  //     reviennent pour la maison terminee, puis re-effacent en transition ---
  let extOpacity;
  if (progress < 0.20) extOpacity = lerp(0.95, 0.22, smoothstep(0.05, 0.2, progress));
  else if (progress < 0.78) extOpacity = 0.22;
  else if (progress < 0.90) extOpacity = lerp(0.22, 0.92, smoothstep(0.78, 0.9, progress));
  else extOpacity = lerp(0.92, 0.08, smoothstep(0.9, 1, progress));
  mats.exterior.opacity = extOpacity;
  parts.windows.children.forEach((w) => { w.material.opacity = Math.max(0.15, extOpacity * 0.6); });

  // --- Details exterieurs (hero uniquement) ---
  parts.yardDetails.visible = progress < 0.22;

  // --- Salle de bain / tuyaux (scene plomberie) ---
  const bathAppear = smoothstep(0.17, 0.24, progress);
  const bathFade = 1 - smoothstep(0.44, 0.52, progress);
  const bathVisible = Math.min(bathAppear, progress < 0.44 ? 1 : bathFade);
  parts.pipes.visible = bathVisible > 0.02;
  parts.pipes.scale.setScalar(lerp(0.3, 1, smoothstep(0.18, 0.3, progress)));
  parts.pipes.children.forEach((c) => { if (c.material) c.material.opacity = bathVisible; });
  if (parts.mats) { /* noop */ }

  // --- Electricite ---
  const elecAppear = smoothstep(0.32, 0.4, progress);
  const elecFade = 1 - smoothstep(0.58, 0.65, progress);
  const elecVisible = Math.min(elecAppear, progress < 0.58 ? 1 : elecFade);
  parts.cables.children.forEach((cable, i) => {
    const stagger = i * 0.03;
    const local = smoothstep(0.34 + stagger, 0.44 + stagger, progress) * (progress < 0.58 ? 1 : elecFade);
    cable.material.opacity = local;
    cable.visible = local > 0.02;
  });
  parts.sockets.children.forEach((s) => {
    if (s.material && s.material.emissiveIntensity !== undefined) {
      s.material.emissiveIntensity = elecVisible * 1.4;
    }
  });
  accentLightFor(handle, elecVisible * 0.6);

  // --- Renovation : mur brut -> fini, mobilier revele ---
  const renoT = smoothstep(0.5, 0.62, progress);
  lerpColorHex(COLOR.plasterRaw, COLOR.plasterDone, renoT, mats.renoWall.color);
  mats.renoWall.roughness = lerp(0.9, 0.45, renoT);
  parts.furniture.visible = progress > 0.6;
  if (parts.furniture.visible) {
    const furnitureT = smoothstep(0.6, 0.68, progress);
    parts.furniture.scale.setScalar(lerp(0.6, 1, furnitureT));
    parts.furniture.children.forEach((c) => {
      c.material.transparent = true;
      c.material.opacity = furnitureT;
    });
  }

  // --- Documents ---
  const docT = smoothstep(0.63, 0.68, progress) * (1 - smoothstep(0.72, 0.76, progress));
  parts.documents.visible = docT > 0.02;
  parts.documents.children.forEach((c) => { c.material.transparent = true; c.material.opacity = docT; });

  // --- Lumiere : plus neutre pendant le chantier, plus chaude a la fin ---
  const warmT = smoothstep(0.8, 0.9, progress) * (1 - smoothstep(0.95, 1, progress));
  const key = handle.scene.children.find((o) => o.isDirectionalLight && o.intensity > 0.5);
  if (key) {
    lerpColorHex(0xdfe6ee, 0xffe3bf, warmT, key.color);
    key.intensity = lerp(1.15, 1.5, warmT);
  }

  // --- Transition finale : effet "epure" (fondu general + recul) ---
  const finalFade = smoothstep(0.92, 1, progress);
  handle.scene.fog.near = lerp(14, 8, finalFade);
  handle.scene.fog.far = lerp(34, 20, finalFade);
}

function accentLightFor(handle, amount) {
  const accent = handle.scene.children.find((o) => o.isPointLight);
  if (accent) accent.intensity = amount * 1.2;
}

// ---------- Resize ----------
export function resizeScene(handle) {
  const canvas = handle.renderer.domElement;
  const parent = canvas.parentElement || canvas;
  const w = parent.clientWidth || window.innerWidth;
  const h = parent.clientHeight || window.innerHeight;
  const dpr = handle.lowQuality ? Math.min(1.25, window.devicePixelRatio || 1) : Math.min(2, window.devicePixelRatio || 1);
  handle.renderer.setPixelRatio(dpr);
  handle.renderer.setSize(w, h, false);
  handle.camera.aspect = w / Math.max(1, h);
  handle.camera.updateProjectionMatrix();
}

// ---------- Qualite (mobile / basse puissance) ----------
export function setQuality(handle, low) {
  handle.lowQuality = low;
  handle.renderer.shadowMap.enabled = !low;
  const key = handle.scene.children.find((o) => o.isDirectionalLight && o.castShadow);
  if (key) key.castShadow = !low;
  resizeScene(handle);
}

// ---------- Pause / reprise (economie GPU hors-ecran ou onglet masque) ----------
export function pauseScene(handle) {
  handle.running = false;
  if (handle.rafId) cancelAnimationFrame(handle.rafId);
  handle.rafId = 0;
}
export function resumeScene(handle) {
  if (handle.running) return;
  handle.running = true;
  handle.rafId = requestAnimationFrame(() => renderLoop(handle));
}

// ---------- Dispose ----------
export function disposeScene(handle) {
  handle.running = false;
  if (handle.rafId) cancelAnimationFrame(handle.rafId);
  handle.scene.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) {
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      mats.forEach((m) => m.dispose());
    }
  });
  handle.renderer.dispose();
}
