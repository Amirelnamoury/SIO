# Assets 3D — landing page

Aucun modèle 3D externe (`.glb`/`.gltf`), texture ou asset graphique tiers
n'est utilisé par l'expérience 3D de la landing page.

La maison, le chantier et tous les éléments techniques (tuyaux, câbles,
tableau électrique, mobilier, outils...) sont **entièrement procéduraux** :
générés au runtime par `frontend/landing-scene.js` avec les géométries
primitives de Three.js (`BoxGeometry`, `CylinderGeometry`, `PlaneGeometry`,
`TubeGeometry`, `ShapeGeometry`) et des matériaux `MeshStandardMaterial` /
`MeshPhysicalMaterial` colorés directement en code.

Conséquences :

- Aucune question de licence ou de provenance ne se pose (rien n'est
  téléchargé ni copié depuis une source tierce).
- Aucun fichier binaire lourd dans ce dossier — le poids de l'expérience
  se limite au code JS et à la dépendance Three.js (chargée depuis un CDN,
  voir `landing-scene.js`).
- Ce dossier est conservé comme emplacement dédié si des assets réels
  (GLB/GLTF, textures) sont ajoutés plus tard : documenter alors ici leur
  source et leur licence, comme demandé dans le brief de la mission.
