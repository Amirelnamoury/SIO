# Suite Artisan — Direction visuelle V4 ("Atelier")

Reset d'identité visuelle décisif, scope strictement limité à l'app shell
(sidebar, topbar, workspace) et au dashboard (vide + peuplé). Aucune autre
vue (Devis, Factures, Clients, etc.) n'a été retouchée — elles continuent
de lire l'ancien système `--sa-*` (indigo/gris/Manrope) en attendant
validation de cette direction avant propagation.

## Ce qui change

- **Palette** : indigo `#4f46e5` + gris froid `#f7f8fa` → papier chaud
  `#f1eee4` + encre `#1c2420` + un seul accent, un vert atelier profond
  `#2f4a3c`. Zéro cliché BTP (pas d'orange/jaune/béton/cuivre), zéro cliché
  "IA" (pas de fond crème + serif + terracotta).
- **Typographie** : Manrope → Archivo (display : titres, "Bonjour", gros
  chiffres KPI) + Public Sans (UI/corps). Deux familles nettement
  distinctes, contraste voulu entre le poids éditorial des titres et la
  neutralité fonctionnelle du texte courant.
- **Sidebar** : gris clair générique avec pastille active arrondie → plan
  sombre permanent ("la colonne vertébrale du produit"), marqueur d'état
  actif en bord (trait vert), marque "SA" + wordmark en tête.
- **Topbar** : barre blanche à bordure → se fond dans le plan papier du
  workspace ; recherche intégrée avec sa propre surface ; bouton "+Créer"
  en vert atelier (plus de rectangle violet générique).
- **KPI dashboard** : bande de 4 chiffres à plat → un chiffre héros (CA du
  mois, grand format Archivo) + deux rangées de stats secondaires plus
  discrètes, séparées par des hairlines chaudes.
- **"À faire aujourd'hui"** : ligne point+texte+boutons → composition en
  champs distincts (type/titre/contexte/montant), mêmes données, mieux
  scannable.
- **Rayons/ombres** : 8-10px partout, ombres douces génériques → langage
  plus architectural (3-6px), profondeur par plans de fond (sombre/papier/
  blanc) plutôt que par ombres.
- **Accessibilité** : contrastes vérifiés WCAG (tous les textes ≥ 6.6:1,
  voir le rapport de session) ; anneau de focus recoloré en vert dans le
  shell/dashboard ; l'urgence des tâches ne repose pas uniquement sur la
  couleur (point + gras + position).

## Captures

- `desktop/01-dashboard-empty.png`, `02-dashboard-populated.png` (1440×900)
- `desktop/03-shell-1280.png`, `04-shell-1600.png` — bonus, autres largeurs
  testées (1280×800, 1600×900)
- `mobile/01-dashboard-empty.png`, `02-dashboard-populated.png` (390×844)
- `tablet/01-dashboard-populated.png` (768×1024)

Toutes capturées contre l'application réelle (Playwright/Chromium), avec
un compte neuf et un compte avec activité réelle créés via l'API — jamais
de données inventées dans le frontend.

## Note technique : artefact de capture (pas un bug produit)

Les premières captures `full_page` sur mobile/tablette montraient une
grille à 2 colonnes et une bande vide à droite en bas de page. Diagnostic
via `getComputedStyle` en conditions réelles : la page elle-même est
correcte (`grid-template-columns` bien en 1 colonne, `scrollWidth` = largeur
du viewport, aucun débordement). L'artefact vient de l'interaction entre
le mode `full_page` de Playwright et la barre de navigation mobile en
`position:fixed`. Les captures finales ci-dessus utilisent un viewport
haut fixe plutôt que `full_page` pour l'éviter.
