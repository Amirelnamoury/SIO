# Assets — landing page publique

## `logo.webp` / `logo-64.png` — la marque

Le logo fourni était un PNG doré **sur fond noir opaque**, inutilisable
tel quel sur une photo. Il a été détouré sans masque manuel : le logo
étant clair sur un fond quasi noir, la **luminance de l'image est déjà
une bonne approximation du masque**. On l'extrait, on écrase le résidu de
fond avec une rampe linéaire (`linear(1.55, -26)`), puis on la rebranche
comme canal alpha sur les couleurs d'origine — la texture brossée de l'or
est donc conservée intacte.

- `logo.webp` — 320 px, transparent, **48 Ko**. En PNG le même rendu
  pesait 481 Ko : l'or est une texture photographique, le PNG y est très
  mauvais. Le logo ne dépasse jamais ~60 px à l'écran.
- `logo-64.png` — 64 px, favicon (3,4 Ko).

Il sert à trois endroits : la navigation, le pied de page, et **l'écran
du moniteur dans la frame R**, où il est accompagné de « SUITE ARTISAN »
en capitales espacées.

Pour régénérer après un changement de logo, voir la méthode ci-dessus ;
le recadrage (`CROP`) doit être ajusté au nouveau fichier.


## `villa/` — les quatorze pièces de la visite

La page publique est une visite d'une villa livrée, pilotée par le
défilement : quatorze photographies traversées pièce par pièce, avec des
mouvements de caméra en WebGL (voir `frontend/landing-visite.js`).

Les fichiers sont nommés dans l'ordre narratif, de la façade à la
terrasse :

| | |
|---|---|
| `00_villa-master-facade` | façade, l'ouverture |
| `01_hall-entree` | le hall |
| `02_salon-principal` | le salon |
| `03_salle-a-manger` | la salle à manger |
| `04_cuisine` | la cuisine |
| `05_salon-tv-detente` | le salon TV |
| `06_bureau-bibliotheque` | le bureau |
| `07_suite-parentale` | la suite |
| `08_salle-bain-parentale` | la salle de bain |
| `09_galerie-couloir` | la galerie |
| `10_chambre-invites` | la chambre d'amis |
| `11_balcon-suite` | le balcon |
| `12_cour-interieure-bassin` | la cour |
| `13_terrasse-piscine` | la terrasse, la clôture |

Deux définitions par pièce : **1920 px** pour le bureau, **1100 px**
(`-sm`) pour le téléphone. Le choix ne se fait pas sur la largeur CSS
mais sur le nombre de pixels réels à couvrir — `innerWidth ×
devicePixelRatio` — parce qu'un portable de 1351 px à densité 1 en
demande davantage qu'un téléphone de 390 px à densité 3.

Les originaux pesaient **12,9 Mo** (dont 5,3 Mo pour la seule façade, en
PNG avec un canal alpha inutile). Après conversion : **3,2 Mo**, soit
25 %. La conversion est reproductible avec Pillow — redimensionnement
Lanczos, WebP qualité 76 (72 pour les `-sm`), `method=6`.

### Ce qui a remplacé `frames/`

Le dossier `frames/` portait les vingt photographies abstraites de la
visite précédente. Plus rien ne les référence depuis que la visite est
celle de la villa : elles ont été retirées (3,6 Mo). Elles restent dans
l'historique Git si le besoin s'en présentait.
