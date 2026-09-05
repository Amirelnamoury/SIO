# Assets — landing page

Ce dossier est vide intentionnellement.

La landing page (`frontend/landing.html`) n'utilise **aucun asset externe** :
ni image, ni photo, ni modèle 3D, ni icône téléchargée.

Tout le visuel est produit en CSS pur :

- les cartes produit du hero (devis, planning, encaissements, relances) sont
  des éléments HTML stylés ;
- les halos colorés sont des `radial-gradient` ;
- la grille de fond est un `linear-gradient` répété ;
- les puces, coches et barres de progression sont des formes CSS.

Les seules ressources externes chargées sont les deux polices Google Fonts
déclarées dans `landing.html` (Bricolage Grotesque et Inter), toutes deux
sous licence SIL Open Font License 1.1, libres d'usage commercial.

Conséquence : aucune question de licence ou de provenance à documenter, et
aucun fichier lourd à charger au premier affichage.
