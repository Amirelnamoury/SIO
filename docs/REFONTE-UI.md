# Refonte UI — ce qui a changé, et pourquoi

Sept commits, 20 fichiers, +2 413 / −972 lignes. La direction artistique est
décrite dans [`frontend/DIRECTION-ARTISTIQUE.md`](../frontend/DIRECTION-ARTISTIQUE.md) ;
ce document raconte le chantier.

---

## Le fil rouge

L'interface n'était pas laide. Elle était **assemblée** — écran par écran,
devant l'écran, une valeur mesurée à la main à la fois. Cela ne se voit sur
aucune capture, et cela se compte :

| Ce qui disait la même chose N fois | N |
|---|---|
| retouches de mise en page écrites au nom d'une vue | **55** |
| traitements différents du petit libellé qui nomme une valeur | **34** |
| règles posant la romane, dont **tous les montants du produit** | **57** |
| tailles de texte sous le plancher de lisibilité | **8** |

Six marges d'en-tête — 18, 21, 38, 34, 29, 22 px — pour le même élément.
Quatorze largeurs de liste déroulante. Neuf valeurs d'espacement de
capitales, de 0,03 à 0,12 em. Rien de tout cela n'est un choix ; c'est la
trace d'une interface composée à la main, écran après écran.

**La conséquence pour l'utilisateur** : le contenu se décalait de vingt
pixels à chaque changement de page, et les cinq dialectes divergeaient —
Documents refusait le retour à la ligne sur bureau, et sa dernière commande
sortait de 18 px hors du champ sans que rien ne le signale.

---

## 1. La direction artistique

« Atelier » — papier calcaire, encre chaude, laiton, photographies
d'établi — est abandonnée, comme l'avait été le sombre-et-doré avant elle.
Le brief nomme précisément ce qu'elle était devenue : beige généralisé,
cuivre décoratif, vieux papier.

**Ce qui la remplace : documentaire et opérationnelle.** La personnalité
vient de la précision — références, numéros, montants, états, chronologies —
pas d'un décor qui évoque le métier.

Palette : gris neutres et vert profond. Quatre plans, un rôle chacun : le
sommaire recule, le plan de travail porte, la feuille reçoit, le creux
n'intervient qu'au survol.

**Le contraste de chaque couple a été mesuré avant application**, et deux
valeurs proposées échouaient : l'encre des libellés de colonne (4,44:1 sur
la feuille, 3,60:1 sur le creux) et le contour fonctionnel des champs
(2,53:1 pour un seuil à 3). Corrigées avant d'entrer dans la palette.

Les dix-huit usages du laiton ont été repris **un par un**, selon ce qu'ils
disaient réellement : le vert pour la position courante, l'ambre pour ce qui
appelle une action. Les jetons sont **retirés, pas neutralisés** — un jeton
mort qui répond encore est ce qui permet à une identité abandonnée de
revenir par une règle écrite distraitement.

## 2. Le système de familles

**Même identité, pas même page.** Chaque vue déclare sa mission
(`data-famille`) et la feuille en déduit sa composition : registre, poste,
parc, agenda, file, rapport, gestion, réputation — plus document et dossier
pour ce qui vit hors des vues. Huit familles pour treize vues.

La largeur suit la mission : un agenda a besoin d'étaler du temps, un
rapport se lit, une file se descend.

C'est ce système qui remplace les 55 retouches. Une famille ne se déclare
qu'une fois.

## 3. Les trois écrans pilotes

**La pièce** (devis, facture). C'étaient des panneaux de 380 px où quatre
commandes de même poids s'alignaient *en tête* : on lisait l'outillage avant
de lire le devis. La feuille prend le centre, le suivi et les commandes se
rangent dans un rail. Une seule action domine ; « Télécharger le PDF »,
« Copier le lien client », « Dupliquer » redeviennent du texte cliquable.

**Le dossier d'exécution** (chantier). Les chiffres de rentabilité
occupaient le milieu de la fiche, « Dépenses 56 000,00 € » en grand, *avant*
la liste des interventions : on ouvrait un chantier et on lisait sa
comptabilité. L'ordre suit désormais les questions du terrain, et « ce qui
vient » montre la prochaine intervention — l'information était déjà chargée,
elle était rangée sous les chiffres.

**La fiche de qualification** (prospect). Prospect et client sont le même
enregistrement, distingué par son statut, et le dossier les traitait à
l'identique : un prospect reçu la semaine dernière ouvrait sur « Facturé
0,00 € · Impayé — · Chantiers 0 ». Quatre réponses à des questions que
personne ne pose à ce stade, quand les vraies — qu'est-ce qu'il veut, d'où
vient-il, quand le rappeler — n'apparaissaient nulle part. **Aucun champ
nouveau** : tout existait dans `ClientOut` sans être montré.

## 4. Ce qu'on n'affiche pas

Trois formes du même défaut, toutes corrigées : une échelle de valeur
dessinée quand il n'y a rien à mesurer (« — / 0 prospect » répété en travers
de la largeur) ; une colonne qui aligne des tirets sous son intitulé ; un
dossier qui répond à des questions qu'on ne pose pas encore.

L'absence est déjà une information. Elle n'a pas besoin d'être étiquetée.

## 5. La typographie

C'est la correction la plus importante, et elle est venue de
l'**auto-critique** : en *mesurant* où tombait la romane plutôt qu'en la
regardant, j'ai trouvé 57 règles — dont la totalité des montants du produit.

Fraunces est une romane à fort contraste de graisse, dessinée pour des
titres. Ses chiffres, même forcés en chasse fixe, gardent des empattements
qui s'accrochent quand on descend une colonne de montants — le geste exact
sur lequel repose toute la grammaire du registre. **On avait bâti une
colonne de comptable et composé ses chiffres comme un magazine.**

La cause était une seule règle : `h1, h2, h3 { font-family: display }`. Elle
est désormais demandée nommément, là où elle **nomme** : 17 usages.

Et le plancher de lisibilité, tenu partout : huit tailles vivaient sous
11 px, dont l'**heure d'un rendez-vous** à 9,9 px. L'agenda a le droit
d'être plus dense que le reste du produit ; il n'a pas le droit d'être
illisible à bout de bras dans un fourgon.

## 6. Un seul produit

L'écran de connexion portait **sa propre feuille de 307 lignes**, avec son
propre jeu de variables « pour ne dépendre de rien » : fond quasi noir,
photographies d'atelier, laiton sur les onglets. Le premier écran du produit
enseignait une identité qu'il fallait désapprendre en entrant.

La vitrine a suivi le même mouvement — sa feuille disait déjà pourquoi :
« un prospect cliquait *Essayer gratuitement* et changeait de marque en
route ». Seule la palette bouge ; la composition de la page, refaite
récemment, n'est pas touchée.

Douze sur-titres de page ont disparu : « COMMERCIAL », « GESTION »,
« ORGANISATION » répétaient le libellé du groupe qui figure dans la colonne
de gauche, à trois centimètres de là.

---

## Les signatures — ce qui rend le produit reconnaissable sans logo

- **La bande de référence.** Dans le bâtiment, chaque pièce porte un numéro,
  et ce numéro est ce qu'on dit au téléphone. La plupart des logiciels le
  rangent en gris dans un coin ; ici il ouvre la pièce, en chiffres
  tabulaires, tenu par un filet vert, et il ne défile pas.
- **La colonne des sommes**, séparée du libellé par un filet vertical comme
  dans un livre de comptes — ce qui permet de descendre la colonne des yeux
  sans relire les intitulés.
- **L'état s'écrit, le compte s'encadre.** Un état est un mot précédé d'une
  marque carrée ; la couleur double le mot, elle ne le remplace jamais.
- **La feuille qui ressort** du plan inerte : le même geste partout pour
  dire « vous êtes ici ».
- **La marge**, colonne d'intitulés contre un filet — la structure d'un
  document technique.

---

## Ce que la vérification a trouvé

Chaque lot a été vérifié en pilotant un navigateur, pas en relisant du code.
Trois fois, cela a changé la conclusion :

**Une position absolue calée sur un pixel.** Les outils de recherche des
Tâches étaient posés en `top: 159px`, mesuré à la main sur la hauteur
d'en-tête de l'époque. Cet en-tête a changé : la recherche se retrouvait
par-dessus la première tâche, recouvrant l'intitulé du groupe « En retard ».

**Un état que le jeu d'essai ne pouvait pas montrer.** Le dossier de
chantier ouvre sur « ce qui vient » — mais les deux interventions du jeu
d'essai sont posées à heure fixe, donc passées dès que l'audit tourne
l'après-midi. Le bloc n'apparaissait jamais, et rien ne disait s'il était
absent ou cassé. Un état non couvert est un état invisible, pas un état
correct.

**Un faux défaut, vérifié avant d'être « corrigé ».** Les scènes de la
vitrine mesuraient une opacité de 0,1 et les captures rendaient une page
vide. Avant de conclure, j'ai remis la version *commitée* de la feuille :
même résultat. Le défaut n'était donc pas le mien — et il n'en était pas un :
le fondu dure 0,7 s, et mes mesures comme mes captures tombaient pendant ce
fondu.

Et une correction de ma part sur un dégât que j'avais causé : une
réécriture par expression régulière avait déplacé le suffixe `select` d'un
sélecteur groupé, appliquant une hauteur de contrôle au conteneur de la
barre. Le balayage visuel était passé au vert — c'est en relisant le CSS que
je l'ai vu. Un balayage qui ne trouve rien ne prouve pas qu'il n'y a rien.

---

## Vérification

- **647 éléments audités à 1366 px**, **554 à 375 px** — sur les treize
  vues, l'écran de connexion, les deux pièces et les deux dossiers. Aucun
  échec de contraste, aucun débordement horizontal, aucun texte rogné,
  aucune erreur console, plancher typographique tenu à 11 px.
- **209 éléments** sur la vitrine déroulée, aucun échec.
- **27 tests frontend**, dont deux nouveaux fichiers qui protègent ce que la
  capture d'écran ne montre pas : le plancher typographique, l'absence de
  retouche par vue, le retour impossible des identités abandonnées, la
  taille des champs, la casse des intitulés.
- **144 tests backend** — le backend n'a pas été touché, et le vérifier
  était le moyen de le prouver.

## Ce qui reste ouvert

- **La colonne de gauche** reste le point le moins distinctif du produit.
  Les comptes en chiffres tabulaires alignés à droite lui donnent l'allure
  d'un index de registre, mais seules trois entrées en portent un. Les
  étendre coûterait quatre requêtes au démarrage — un prix réel pour un gain
  d'apparence, que je n'ai pas voulu payer sans arbitrage.
- **Les deux photographies de l'écran de connexion** ne sont plus
  référencées. Elles sont conservées, avec une note : elles peuvent servir à
  la vitrine.
- **`graphify update .`** reste bloqué par la politique de contrôle
  d'applications de cette machine ; le graphe du dépôt n'est pas à jour.
