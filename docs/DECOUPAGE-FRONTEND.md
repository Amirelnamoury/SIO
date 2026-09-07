# Découpage du frontend par domaine

Astra §16 : « Évolution **progressive** du JavaScript existant vers des modules
par domaine : navigation, accès API, état de vue et rendu séparés. » Et :
« Aucune réécriture React ou migration de stack n'est justifiée par cet audit. »

Ce document dit où on en est, et ce qui reste.

## La règle qu'on se donne

**Une extraction ne réécrit rien.** Les lignes sont déplacées telles quelles,
dans l'ordre où elles étaient. Un découpage qui range *et* réécrit en même temps
n'est pas vérifiable : à la première régression, on ne sait plus si elle vient
du rangement ou de la réécriture.

La preuve se fait par comparaison : code avant et code après, commentaires et
espaces ignorés, doivent faire **exactement la même longueur**, et les seules
différences doivent être aux coutures — les fragments qui chevauchent un point
de découpe. C'est ce qui a été vérifié pour `socle.js` : 341 005 caractères des
deux côtés, six fragments de couture.

## Pourquoi des scripts classiques, pas des modules ES

Les fichiers sont chargés à la suite dans `index.html`. Les déclarations de
premier niveau (`let`, `const`, `function`) restent partagées entre eux,
exactement comme lorsque tout tenait dans `app.js` — le comportement ne peut
donc pas changer du fait du découpage lui-même.

Passer aux modules ES (`type="module"`) demanderait de revoir toutes les
fonctions posées sur `window` et la façon dont les `data-action` sont résolus.
C'est un autre lot, et il faudra d'abord démontrer qu'il apporte quelque chose :
l'audit ne le réclame pas.

## Fait

### `socle.js` — les primitives partagées (418 lignes)

Ce dont **tous** les écrans se servent :

- les formats — montants, dates, dates courtes, échappement HTML ;
- les états d'un écran — vide, filtré par une recherche, incomplet
  (`bandeauCharge`), en cours d'actualisation (`debutChargement`) ;
- les messages de résultat et les confirmations ;
- la section composée (`saSection`) ;
- le clavier dans les fenêtres modales — piège, restitution du focus.

### `navigation.js` — où l'on est, et comment y aller (375 lignes)

Trois questions, et elles seules :

- **quelle vue** est à l'écran, et qui la charge — `switchView`, qui rend la
  promesse de son chargeur pour qu'on puisse ouvrir un objet *après* ;
- **quelle adresse** décrit cet état, dans les deux sens : l'écrire en
  naviguant, retrouver l'état en recevant un lien ;
- **comment ouvrir** une pièce précise : la trouver en cache ou la demander au
  serveur, l'afficher, et dire quand elle est introuvable.

Ce fichier ne sait rien du contenu des écrans. Les fonctions d'ouverture
(`showTimeline`, `showDevisDetail`…) vivent dans `app.js` et sont appelées par
leur nom.

## Reste à extraire

Dans l'ordre où Astra le suggère, et par lots séparés :

1. **`planning.js`** — la grille horaire, les durées, le glisser-déposer.
   Fortement autonome : peu de couplage avec le reste.
3. **`statistiques.js`** — le rapport et son graphique.
4. **`devis.js`** et **`chantier.js`** — les deux compositions les plus lourdes.
   Astra demande justement de leur « garder des compositions spécifiques ».

Après ces extractions, `app.js` ne devrait plus contenir que la coquille, les
constantes d'affichage et les écrans qui n'ont pas de logique propre.

## Ce que les tests en disent

`tests/_sources.mjs` lit les scripts du produit dans leur ordre de chargement.
Un test qui vérifie **un comportement** lit `tout` : il survit aux extractions
suivantes sans être touché. Un test qui vérifie **l'organisation** — quel
fichier contient quoi — vise un fichier précis, et c'est voulu.

Un test qui affirme « ce code n'existe plus nulle part » doit lire `tout`
également : sur un seul fichier, il passerait pour la mauvaise raison.
