# Captures de comparaison UI

Captures d'ecran du frontend reel (donnees API reelles, aucune valeur
d'exemple codee en dur) pour les 13 vues principales, a comparer aux
images de reference visuelle fournies pour ce lot de travail.

- `desktop-1376x768/*.png` - viewport CSS exact de 1376x768, les 13 vues
  finales comparees aux references de ce lot.
- `desktop/*.png` - anciennes captures de travail en 1440x900, les 13 vues (dashboard, prospects, clients,
  devis, factures, chantiers, planning, taches, documents, statistiques,
  avis, entreprise, notifications).
- `mobile/*.png` - captures de controle en 390x844 (dashboard,
  prospects, clients, devis, factures, chantiers, planning, entreprise).

Chaque image est un cadrage fixe d'une seule fenetre de navigateur (pas
un defilement plein page), pour rester comparable au cadrage des
images de reference elles-memes (egalement des captures d'une seule
fenetre, ~1376x768).

## Methode de capture

Les captures finales ont ete produites avec le navigateur integre Codex,
connecte au frontend local et au backend FastAPI local sur une base de
test temporaire. Le viewport a ete fixe a 1376x768 avant chaque capture.
Chaque vue a ensuite ete ouverte depuis la navigation reelle, laissee se
charger, puis capturee sans modifier le DOM ni injecter de donnees.

Les valeurs visibles proviennent donc de l'API et peuvent differer des
valeurs d'exemple des references. La comparaison porte sur la structure,
les dimensions, les espacements, la typographie, les couleurs et les
etats visuels. Aucun chiffre de reference n'a ete ajoute au frontend.
