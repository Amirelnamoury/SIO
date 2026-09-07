# Suite Artisan — direction artistique

Ce document fixe la direction visuelle du produit. Il n'est pas décoratif :
chaque règle ci-dessous se retrouve dans `style.css` — la feuille unique du
produit — et toute nouvelle page doit s'y conformer ou justifier son écart.

> **Ce document remplace la direction « Atelier »** (papier calcaire, encre
> chaude, laiton, photographies d'atelier), abandonnée à son tour après
> l'identité sombre-et-dorée qui l'avait précédée. La raison est donnée au
> §1. Les deux voies sont fermées : ne pas les reproposer.

---

## 1. Le sujet, avant l'esthétique

L'utilisateur de Suite Artisan n'est pas un cadre devant un tableau de bord.
C'est un artisan ou un conducteur de travaux : il travaille dans une
camionnette, sur un chantier, et fait son administratif le soir. Le logiciel
n'a pas à l'impressionner — il doit lui donner sur ses papiers le même
sentiment de maîtrise qu'il a sur son métier.

**Le piège**, et il a été retenu deux fois : chercher cette identité dans le
*décor* du métier. Bois, cuir, cuivre, vieux papier, texture kraft, atelier
vintage, photographies d'établi. C'est de la couleur locale posée sur un
logiciel de gestion — reconnaissable sur une capture d'écran, fatigante au
bout de huit heures, et sans rapport avec ce que l'outil fait.

**La direction retenue : documentaire et opérationnelle.** La personnalité
vient de la **précision** — les références, les numéros, les montants, les
états, les chronologies, l'organisation de l'information. La référence au
métier est structurelle, pas illustrative.

---

## 2. Les quatre plans

Un plan = un rôle, et le rôle se lit à la clarté. Du plus inerte au plus
vivant : le sommaire recule, le plan de travail porte, la feuille reçoit.

| Jeton | Valeur | Rôle |
|---|---|---|
| `--sa-rail` | `#EEF1F2` | le sommaire — il n'est pas le travail |
| `--sa-bg` | `#F6F7F8` | le plan de travail |
| `--sa-surface` | `#FFFFFF` | la feuille |
| `--sa-surface-2` | `#EEF1F2` | zone inerte : en-tête de colonne, encart |
| `--sa-surface-3` | `#E3E8EA` | le creux : survol d'une zone déjà inerte |
| `--sa-brand-ground` | `#1B3A31` | le fond de marque — connexion et page publique **uniquement** |

Trois valeurs suffisent à dire la hiérarchie ; une quatrième nuance de gris
ne se percevrait plus.

## 3. Les filets

Deux rôles à ne pas confondre.

- `--sa-border` `#DFE4E6` **texture sans structurer**. Il est volontairement
  sous le seuil de contraste (1,28:1) : c'est une réglure de registre, pas
  un contour.
- `--sa-border-strong` `#7B888F` est **fonctionnel**. WCAG 1.4.11 impose 3:1
  pour qu'un champ ou un bouton soit identifiable. Mesuré sur la surface la
  plus sombre où il apparaît : 3,21:1.

## 4. L'encre

`--sa-text` `#20282C` · `--sa-text-muted` `#536168` · `--sa-text-faint`
`#5B6A71` — soit 15,0:1 / 6,4:1 / 5,6:1 sur la feuille.

Le troisième niveau porte les libellés de colonne. **C'est le creux qui fixe
son plancher, pas la feuille** : il y vaut 4,54:1, et c'est le fond qu'une
validation faite sur le blanc oublie systématiquement. Deux valeurs
proposées pendant la refonte échouaient à ce contrôle et ont dû être
corrigées avant d'entrer dans la palette.

## 5. L'ancrage : vert profond

`--sa-accent` `#245548`. Il tient **trois rôles et pas un de plus** :

1. l'action dominante ;
2. la position courante ;
3. le filet de référence en tête des dossiers.

Partout ailleurs, l'interface est en gris et en noir. Une marque qui remplit
l'écran de sa couleur cesse d'être reconnaissable.

## 6. La sémantique : quatre états, jamais décoratifs

`--sa-info` `#365C82` · `--sa-success` `#326343` · `--sa-warning` `#805B16`
· `--sa-danger` `#A03332`.

Le rouge ne sort que pour un **problème réel**, l'ambre pour ce qui demande
une décision, le vert pour ce qui est confirmé, le bleu pour ce qui informe
sans rien demander.

**La couleur n'est jamais la seule information.** Elle double toujours un
mot.

---

## 7. Typographie

**Inter** fait le travail : lecture, formulaires, colonnes, **nombres**,
métadonnées, commandes.

**Fraunces ne sert qu'à NOMMER** : titre de page, nom de dossier, titre de
chantier, objet d'une pièce, la phrase du jour sur l'accueil, la lecture
d'un rapport, une citation d'avis, la marque. Dix-sept usages, listables.

> Elle en avait cinquante-sept, dont **la totalité des montants du produit**.
> Ce n'était pas qu'une question de doctrine : Fraunces est une romane à fort
> contraste de graisse, dessinée pour des titres. Ses chiffres, même forcés
> en chasse fixe, gardent des empattements qui s'accrochent quand on descend
> une colonne de montants — le geste exact sur lequel repose toute la
> grammaire du registre. On avait bâti une colonne de comptable et composé
> ses chiffres comme un magazine.

**Le plancher est 11 px** (`--sa-text-2xs`) et il est mesuré par un test.
Huit tailles vivaient en dessous, dont l'**heure d'un rendez-vous** à 9,9 px
— la donnée la plus importante d'un agenda, sous le seuil de ce qui se lit à
bout de bras dans un fourgon.

Les champs sont à **16 px** : en dessous, iOS zoome à la mise au point et
déplace l'utilisateur dans la page sans prévenir.

Inter et Fraunces sont chargées en 400/500/600/700. Toute autre graisse est
arrondie en silence par le navigateur — n'en écrire aucune.

---

## 8. Les familles de composition

**Même identité, pas même page.** Chaque vue déclare sa mission
(`data-famille` sur la section, recopiée sur `<body>` par `switchView`), et
c'est la mission qui décide de la composition.

| Famille | Mission | Écrans |
|---|---|---|
| `registre` | on parcourt et on compare | Prospects, Clients, Devis, Factures, Documents |
| `poste` | on décide quoi faire maintenant | Accueil |
| `parc` | on reconnaît des objets | Chantiers |
| `agenda` | on lit du temps | Planning |
| `file` | on exécute à la suite | Tâches, Notifications |
| `rapport` | on tire des conclusions | Statistiques |
| `gestion` | on règle quelque chose | Entreprise |
| `reputation` | on soigne une image | Avis |

Et deux familles qui vivent hors des vues : `document` (devis, facture) et
`dossier` (fiche client, fiche chantier).

Ce qui reste identique d'une famille à l'autre : l'encre, les filets, les
hauteurs de contrôle, le traitement des nombres, la manière de dire un état.
Ce qui change : ce qui domine, et donc où va la largeur.

**La règle d'écriture : une famille ne se déclare qu'une fois, dans le bloc
des familles.** Aucune vue ne doit recevoir de retouche à son seul nom.

> La refonte a retiré **cinquante-cinq** retouches de ce type : six marges
> d'en-tête mesurées à la main (18, 21, 38, 34, 29, 22 px pour le même
> élément), quatorze largeurs de liste déroulante, et vingt-huit règles
> disant en cinq dialectes que la barre de commandes passe à la ligne sur
> mobile. Elles divergeaient : Documents refusait le retour à la ligne sur
> bureau et sa dernière commande sortait de 18 px hors du champ.

---

## 9. Les signatures

Ce qui rend le produit reconnaissable **sans son logo**. Toutes viennent du
métier, aucune n'est un ornement.

### La bande de référence

En tête de chaque pièce et de chaque dossier, toujours identique : la
référence, de qui il s'agit, où en est la pièce. Elle ne défile pas.

Dans le bâtiment, chaque pièce porte un numéro, et ce numéro est ce qu'on
dit au téléphone — « je vous rappelle au sujet du devis DV-2026-089 ». La
plupart des logiciels le rangent en gris dans un coin. Ici il ouvre la
pièce, en chiffres tabulaires, tenu par un filet vert.

### La colonne des sommes

Dans un livre de comptes, la colonne des montants est séparée du libellé par
un **filet vertical**. Ce n'est pas un ornement : c'est ce qui permet de
descendre la colonne des yeux sans relire les intitulés. Tous les registres
la portent, y compris sur mobile.

### L'état s'écrit, le compte s'encadre

Un **état** — « Consulté », « Signé », « En retard » — se lit dans une
colonne, ligne après ligne. Une pastille pleine par ligne transforme un
registre en guirlande, et quand tout est coloré plus rien ne ressort. L'état
s'écrit donc en toutes lettres, précédé d'une **marque carrée** de la couleur
de son sens. Un carré, pas un rond : un rond se lit « voyant lumineux », un
carré « marque portée sur un formulaire ».

Un **compte** — « Documents 3 » — garde son fond : un nombre isolé a besoin
d'être enclos pour qu'on voie à quoi il se rapporte.

### La feuille qui ressort

Partout où il faut dire « vous êtes ici », c'est le même geste : la surface
blanche qui ressort du plan inerte, avec la seule ombre légère du système.
La section ouverte du sommaire, l'onglet actif d'un sélecteur d'affichage,
l'onglet de connexion. Jamais un aplat de couleur — la couleur de marque
désigne, elle ne remplit pas.

### La marge

Colonne d'intitulés à gauche du contenu, séparée par un filet vertical
(`--sa-marge`, 96 px). C'est la structure d'un document technique. Elle ne
vaut que si elle **porte** quelque chose — l'intitulé de section et son
compte — sinon c'est une gouttière vide qui prend la largeur du travail.
Réservée au dossier, au poste de travail et au rapport ; les registres et
l'agenda ont besoin de toute leur largeur.

---

## 10. Profondeur, rayons, mouvement

**La séparation vient des filets et des plans, pas des ombres.** Une ombre
ne se justifie que si la surface est réellement superposée : un menu, une
modale, une feuille de document posée sur le plan de travail.
`--sa-shadow-sm` vaut `none` : rien ne flotte par défaut.

Rayons : 4 px sur ce qu'on manipule, 6 px sur ce qui se répète, 8 px au
maximum sur ce qui flotte. Au-delà, on quitte l'outil professionnel.

Mouvement : 110/160/200 ms. Court, et au service du repérage. Rien ne doit
se donner en spectacle sur un écran qu'on regarde huit heures par jour.

## 11. Contrôles

Une hauteur par famille, tenue partout : **40 px** sur bureau, **32 px**
pour les commandes secondaires (chercher et filtrer n'est pas agir), et un
plancher de **44 px** sur écran tactile — c'est la largeur d'un pouce, pas
une convention.

**Une seule action dominante par contexte.** Les autres restent disponibles
sans être proposées : du texte cliquable, pas des boutons. Un rang de cinq
boutons de même poids ne désigne rien.

Un « Voir » qui double une ligne déjà cliquable n'est pas une action : c'est
la ligne elle-même. Toute zone portant `role="button"` répond à Entrée et
Espace — un seul écouteur, en capture sur le document, les couvre toutes.

---

## 12. Ce qu'on n'affiche pas

Une interface intelligente sait aussi quelles informations **ne pas**
afficher. Trois formes du même défaut, toutes corrigées :

- une **échelle de valeur** dessinée quand il n'y a rien à mesurer —
  « — / 0 prospect » répété en travers de la largeur ;
- une **colonne** qui aligne des tirets sous son intitulé — « Encaissé — »
  sur un répertoire de clients récents ;
- un **dossier de prospect** qui ouvre sur « Facturé 0,00 € · Impayé — ·
  Chantiers 0 », quatre réponses à des questions que personne ne pose à ce
  stade.

L'absence est déjà une information. Elle n'a pas besoin d'être étiquetée
pour se faire comprendre.

---

## 13. Comment on vérifie

Rien de ce document ne se vérifie à l'œil. Les outils sont dans
`frontend/outils/` :

- `jeu-essai.js` peuple les treize vues sans backend. **Une vue vide ne
  déborde jamais et ne prouve rien** : l'audit mobile qui a révélé six vues
  en débordement n'a été possible qu'avec des données dans chaque écran. Un
  état que le jeu d'essai ne couvre pas est un état invisible, pas un état
  correct.
- `audit-contraste.js` mesure le contraste réel contre le fond **effectif**,
  aplati. Il prend un **sélecteur**, pas un élément.
- `jeu-vide.js` pour les états de premier usage.

Les tests `frontend/tests/systeme-de-composition.test.mjs` et
`pieces-et-dossiers.test.mjs` vérifient ce que la capture d'écran ne montre
pas : le plancher typographique, l'absence de retouche par vue, le retour
impossible des identités abandonnées, la taille des champs, la casse des
intitulés.

Chiffres de la dernière vérification : **647 éléments audités à 1366 px**,
**554 à 375 px**, sur les treize vues plus l'écran de connexion, les deux
pièces et les deux dossiers — aucun échec de contraste, aucun débordement
horizontal, aucun texte rogné, plancher tenu à 11 px.
