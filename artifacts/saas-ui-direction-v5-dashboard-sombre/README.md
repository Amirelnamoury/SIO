# Suite Artisan — Dashboard, direction "Atelier sombre" (V5)

Rupture volontaire avec le papier clair (V4/"Atelier") pour le dashboard
uniquement : charbon profond, vert bouteille, ivoire chaud, accent bronze
très rare. Objectif du brief : "logiciel professionnel haut de gamme conçu
pour des artisans exigeants" — maison/atelier haut de gamme, jamais banque,
jamais gaming, jamais admin template.

**Portée strictement gardée** : `#view-dashboard` (dashboard vide + peuplé)
uniquement. La sidebar/topbar/nav mobile (chrome partagé par toutes les
vues) adoptent ce traitement sombre **seulement pendant que le dashboard
est la vue active**, via une classe `body.is-view-dashboard` posée par
`switchView()` (présentation uniquement, aucune logique) — voir
`controle-autres-pages/` : Devis, Statistiques, Factures, Avis, Chantiers
sont pixel-identiques à avant ce changement.

## Ce qui change (au-delà d'une recoloration de tokens)

- **Palette** : nouveau système `--v5-*`, entièrement distinct de
  `--v4-*`/`--sa-*` (papier, inchangé partout ailleurs). Fond `#0f1412`
  (charbon profond, jamais noir pur), sidebar `#0b0f0d` (encore plus
  sombre), surfaces `#161d1a`/`#1d2521`/`#242d28` (paliers discrets),
  bordures chaudes très fines `#423d2e` (texture) et fonctionnelles
  `#7b6d4c` (boutons/inputs, ≥3:1). Texte ivoire chaud `#f0ede5`, jamais
  blanc pur. Vert bouteille profond `#1b372a` (identité) et un vert plus
  clair `#37815c` (le seul assez lumineux pour porter un bouton primaire
  lisible sur fond sombre). Bronze `#c19d67` réservé aux micro-accents :
  marqueur actif de la sidebar, mark "SA", badge de compte, point actif du
  tiroir mobile — jamais une surface, jamais dominant. Champagne `#ede1c5`
  réservé aux chiffres qui comptent (CA du mois, score santé).
- **Contrastes vérifiés** (script maison, luminance relative WCAG, puis
  re-mesurés sur le rendu réel via `getComputedStyle`) : tout texte ≥4.8:1
  sur sa surface réelle (la plupart ≥7:1), boutons/bordures fonctionnelles
  ≥3:1. Les hairlines décoratives restent volontairement sous 3:1 (texture
  discrète assumée, jamais un découpage en blocs).
- **Scène pleine page** : le dashboard devient sa propre scène sombre
  (bleed exact de la boîte de `.content`, y compris quand le contenu est
  plus court que l'écran — état vide compris, desktop et mobile).
- **Planning** : d'un simple rail à filet gauche → un vrai panneau (surface
  + bordure + rayon), traitement élégant même à vide.
- **Urgence** : les lignes "urgence haute" gagnent un vrai poids visuel
  (filet plein à gauche, même langage que `.item-card.is-due` ailleurs
  dans le produit), pas seulement un point de 6px recoloré.
- **Boutons** : primaire = vert clair (le vert profond de l'identité
  disparaîtrait sur fond sombre), secondaire = surface relevée + bordure
  discrète, actions répétées ("Relancer") = chip neutre qui ne s'allume en
  vert qu'au survol — le vert reste rare et signifiant.
- **Typographie** : petites étiquettes (stats commerciales, labels de
  section) passées en majuscules à tracking discret ; hiérarchie affirmée
  entre le chiffre héros (CA), les chiffres secondaires et les libellés.
- **Sidebar** : harmonisée sur la même profondeur que la scène (plus
  sombre qu'elle), marqueur actif et mark de marque en bronze plutôt
  qu'en vert identité — devient un élément de la nouvelle direction au
  lieu d'un sidebar sombre "générique" à côté d'un dashboard clair.
- **Focus visible** : anneaux de focus dédiés (bronze sur sidebar/topbar,
  vert clair sur le dashboard) — les anneaux V4 (pine) restaient trop
  sombres sur les nouvelles surfaces.

## Bugs réels trouvés et corrigés pendant la vérification

- Un commentaire CSS contenait littéralement `--v4-*/--sa-*` : la
  séquence `*/` fermait le commentaire en plein milieu, invalidant tout le
  texte jusqu'au prochain point de resynchronisation du parseur — qui
  tombait exactement sur le point-virgule de `--v5-bg`, supprimant ce
  token précis. Trouvé via `getComputedStyle` (le fond restait transparent
  malgré la règle), confirmé via un diff du nombre de `/*`/`*/` dans le
  fichier. Deux occurrences corrigées (espace ajouté autour du `/`).
- `.btn-sm` (bouton "Voir") n'avait pas de fond dédié en mode sombre :
  héritait du blanc de `--sa-surface`, un carré blanc flagrant sur fond
  charbon.
- État vide (contenu court) : le fond sombre s'arrêtait à la hauteur du
  contenu, laissant apparaître le papier clair de `.workspace` en dessous
  — visible en desktop et amplifié en mobile (pas de mécanisme d'étirement
  vertical sans sidebar). Corrigé par un conteneur flex colonne à hauteur
  garantie, scopé au dashboard actif uniquement.
- `#btn-open-more` ("Plus", tiroir mobile) n'avait jamais eu la classe
  `.nav-link` de ses 4 voisins (bug préexistant, invisible sur fond clair
  car le bouton natif du navigateur s'y confondait) — flagrant sur fond
  sombre. Reproduit son apparence sans toucher le HTML partagé.

## Vérifications

- Captures Playwright (Chromium réel, comptes de test API) : desktop
  1440px, tablette 820px, mobile 390px, vide et peuplé, plus le menu
  "Créer" et le tiroir "Plus" ouverts.
- `controle-autres-pages/` : Devis (desktop+mobile), Statistiques,
  Factures, Avis, Chantiers — zéro pixel différent d'avant ce changement.
- Tests : frontend 13/13, backend 130/130, e2e 13/14 (échec pré-existant
  documenté — scénario 13 "Planning décalage horaire", sans rapport avec
  ce changement).
- Zéro diff sur `backend/`, `frontend/api.js`, `frontend/admin/`,
  `migrations/`, `generator/`. Zéro `Api.*`/`data-action` ajouté ou
  supprimé.
