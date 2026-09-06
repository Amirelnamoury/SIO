# Suite Artisan — direction artistique « Atelier »

Ce document fixe la direction visuelle du produit. Il n'est pas décoratif :
chaque règle ci-dessous se retrouve dans `atelier.css`, et toute nouvelle
page doit s'y conformer ou justifier son écart.

---

## 1. Le sujet, avant l'esthétique

L'utilisateur de Suite Artisan n'est pas un cadre devant un tableau de bord.
C'est un artisan ou un conducteur de travaux : il travaille dans une
camionnette, sur un chantier, et fait son administratif le soir. Le logiciel
n'a pas à l'impressionner — il doit lui donner sur ses papiers le même
sentiment de maîtrise qu'il a sur son métier.

L'objet le plus caractéristique de ce métier n'est ni un graphique ni un
KPI : c'est **le devis**. Un document français formel — en-tête, bloc
d'adresse, tableau numéroté, lignes de TVA, total encadré, mentions légales
en pied. À côté : le carnet de chantier, le métré, le papier quadrillé, les
lignes de cote.

**La thèse de la direction artistique en découle : l'interface doit se lire
comme un document technique bien composé, pas comme un dashboard.**

## 2. Pourquoi pas le « premium sombre »

L'interface précédente était un fond quasi noir avec un accent champagne.
C'est précisément le réflexe que ce produit devait éviter : le « SaaS
premium » sombre-et-doré est devenu un défaut d'usine, et il ne dit rien de
l'artisanat. Il travaille aussi contre le contenu — un devis, une facture,
un tableau de montants se lisent mieux sur du clair, et c'est sur du clair
qu'ils seront imprimés.

La direction « Atelier » pose donc l'application **sur du papier**, avec de
l'encre, des filets et des marges. Le doré ne disparaît pas : il redevient
ce qu'il est, un détail de laiton — un filet sous un chiffre clé, l'état
actif d'un onglet — et non la couleur de tous les boutons.

## 3. Palette

Chaque valeur a été mesurée avant d'être retenue (WCAG 2.1 : 4.5:1 pour le
texte, 3:1 pour les composants d'interface). Les ratios notés sont ceux
mesurés sur le fond papier.

### Surfaces — trois plans seulement

| Rôle | Valeur | Usage |
|---|---|---|
| `--sa-bg` papier | `#F4F1EA` | le plan de travail. Pierre calcaire, jamais du blanc pur : un blanc absolu sur écran rétroéclairé fatigue et ne ressemble à aucun papier réel. |
| `--sa-surface` feuille | `#FCFAF5` | le document posé sur l'établi : carte, panneau, ligne de tableau. |
| `--sa-surface-2` creux | `#EBE7DE` | ce qui recule : en-tête de tableau, zone inerte, champ désactivé. |

Trois plans suffisent. Un quatrième niveau de gris ne se perçoit plus, il
ne fait qu'ajouter des règles à écrire.

**Le creux fixe le plancher de contraste.** C'est la plus sombre des trois
surfaces, donc celle sur laquelle un texte passe le moins bien. La
validation initiale de la palette ne l'avait pas testée : les en-têtes de
colonnes des listes, qui vivent dessus, tombaient à 4.28:1 — sous le seuil.
Toute couleur de texte doit être vérifiée **sur les trois surfaces**, jamais
seulement sur le papier.

### Encre — trois niveaux

| Rôle | Valeur | Contraste | Usage |
|---|---|---|---|
| principal | `#1C1E1A` | 14.89:1 | titres, montants, contenu. Noir chaud, jamais `#000`. |
| secondaire | `#55584F` | 6.43:1 | descriptions, métadonnées lisibles. |
| tertiaire | `#66695E` | 4.97:1 | libellés de colonne, mentions. Reste **au-dessus** du seuil : un libellé illisible n'est pas « discret », il est raté. |

### Accents

**Vert-de-gris `#2E4739`** — l'accent primaire. Couleur du zinc patiné et du
vêtement de travail. Elle tient lieu d'encre soutenue plutôt que de couleur
vive : elle porte l'action primaire et l'état actif sans crier. Blanc sur ce
fond : 9.69:1.

**Laiton `#8A6024`** — le détail. Filet sous un chiffre clé, soulignement
d'un onglet actif, pastille d'un état remarquable. **Jamais un aplat, jamais
un bouton plein.** 4.93:1 en texte.

### Sémantique

| État | Valeur | Contraste |
|---|---|---|
| succès | `#3B6647` | 5.86:1 |
| attention | `#8A5E19` | 5.04:1 |
| danger / retard | `#9E3A2B` — terre cuite | 6.02:1 |
| information | `#42596B` — ardoise | 6.48:1 |

Aucune n'est saturée : un statut mal lu coûte plus cher qu'une nuance
imparfaite, mais une interface qui clignote coûte l'attention de toute la
journée.

### Filets

| Rôle | Valeur | Contraste |
|---|---|---|
| `--sa-border` filet | `#DFDACE` | 1.24:1 — **volontairement sous le seuil**. Il texture, il ne structure pas. |
| `--sa-border-strong` contour | `#86806E` | 3.19:1 — contour fonctionnel d'un champ ou d'un bouton. WCAG 1.4.11 impose 3:1 pour identifier un composant. Mesuré sur le creux, la surface la plus sombre. |

## 4. Typographie

Le site public utilise **Fraunces** et **Inter**. L'application utilisait
Archivo et Public Sans. Deux typographies pour une seule marque, sans
raison. L'application adopte celles du site : une marque, une voix.

- **Fraunces** — titres et chiffres. Serif à contraste optique, un peu
  irrégulière : elle lit « imprimé », pas « interface ». C'est elle qui fait
  qu'un montant ressemble à un montant de devis et non à une donnée.
- **Inter** — texte d'interface, libellés, formulaires. Neutre, dense,
  excellente en petit corps.

Les chiffres sont **toujours en chasse fixe** (`font-variant-numeric:
tabular-nums`). Sans cela, deux montants voisins ne se comparent pas à
l'œil, et c'est le premier signe qu'une interface n'a pas été composée.

## 5. Les quatre gestes de composition

Ce sont eux qui distinguent le produit, bien plus que la palette.

### La marge

Les pages composées (accueil, fiche client, détail d'un devis, entreprise)
portent une gouttière à gauche, où vivent les intitulés de section en petites
capitales, séparée du contenu par un filet vertical. C'est la structure d'un
document technique. Aucun SaaS ne fait ça, et cela coûte zéro complexité.

Les pages denses (listes, planning) n'en ont pas : elles ont besoin de toute
la largeur. **Même identité ≠ même page.**

### Le filet plutôt que la boîte

Une section n'est pas une carte. Elle est séparée par un filet et de
l'espace. La carte est réservée à ce qui est un **objet manipulable** : un
chantier, un devis, un client. Cela supprime d'un coup l'empilement de
rectangles qui fait « généré ».

### Le rythme asymétrique

Un titre de section est collé à son contenu (12 px en dessous) et détaché de
ce qui précède (40 px au-dessus). Cette asymétrie est ce qui fait lire une
page comme typographiée plutôt qu'assemblée.

### L'angle vif

Rayons : `2px` sur les champs et les boutons, `4px` sur les cartes, `0` sur
les filets et les sections. Les grands arrondis partout sont la signature
visuelle du composant générique.

Ombres : quasiment aucune. La profondeur vient du ton du papier et des
filets. Une seule ombre douce, pour ce qui flotte réellement au-dessus de la
page (menu, modale, tiroir).

## 6. Ce qui est proscrit

- La bande de quatre KPI en ouverture de page. Elle était sur presque toutes
  les pages ; elle ne répond à aucune question précise.
- La même composition d'une page à l'autre.
- Les cartes empilées sur une seule colonne quand une grille ferait le même
  travail en trois fois moins de hauteur.
- Les badges partout, les icônes décoratives, les dégradés, les séparateurs
  qui ne séparent rien.
- La couleur seule comme porteuse d'information : un état porte toujours un
  mot en plus de sa teinte.
