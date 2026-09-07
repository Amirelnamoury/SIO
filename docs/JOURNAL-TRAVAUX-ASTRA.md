# Ce qui a été fait, à partir de l'audit Astra

Vingt-neuf commits sur `claude/suite-artisan-site-devis-cbyymn`, de `95ed418`
à `a02fb7e`. 43 fichiers, +6 145 / −1 342 lignes.

Ce document dit ce qui a changé, pourquoi, et ce qui reste. Il est écrit pour
être lu sans la conversation qui l'a produit.

---

## Le fil rouge

Presque tous les défauts corrigés ont la même forme : **un chiffre exact,
présenté de telle manière qu'il dit autre chose que ce qu'il compte.** Ils ne
lèvent aucune erreur, ne se voient pas à la relecture du code, et un compte de
démonstration les traverse sans rien signaler.

D'où la méthode : ne rien conclure du code seul. Chaque correction est vérifiée
en pilotant un navigateur sur les deux comptes (peuplé et vide), aux deux
formats (bureau et mobile). Trois fois, cette vérification a montré que le
défaut était dans mon outil de test et non dans le produit — le détail est plus
bas, parce que c'est utile à savoir.

---

## 1. Ce qui mentait, et ne ment plus

### La navigation ouvrait le rayon, pas la pièce

« Voir la facture » sur une relance impayée, « Voir » sur l'accueil, un résultat
de recherche « FA-2026-014 », les affaires du dossier client, les deux
conversions depuis un devis : tous basculaient sur la **liste**, à charge pour
l'artisan de retrouver la ligne.

Deux causes. L'identifiant de la pièce n'était pas transmis — alors que les
notifications le recevaient du serveur depuis toujours (`NotificationOut.id`
porte l'objet visé, pas la notification). Et la navigation était temporisée :
`switchView(...)` puis `setTimeout(..., 200)`, un pari sur la vitesse du réseau.
Trop lent, rien ne s'ouvrait ; trop rapide, on attendait pour rien.

`switchView` rend maintenant la promesse de son chargeur, et un seul chemin
d'ouverture — `ouvrirObjet(type, id)` — sert la recherche, les notifications,
l'accueil, le dossier client, le planning et les conversions. Treize parcours
vérifiés avec 500 ms de latence simulée.

### Le planning affirmait une occupation que personne n'avait saisie

`const DUREE = 60` dessinait **tout** sur une heure : un rendez-vous sans fin
renseignée, une échéance de tâche, un début de chantier. Un artisan pouvait y
lire « mon mardi matin est pris » sur la foi d'une constante de dessin. Pire :
les tâches et les débuts de chantier n'ont aucune heure — le serveur les ancre à
9h00 et 8h00 pour pouvoir les trier — et ces ancres arrivaient telles quelles
sur l'axe horaire.

Trois états, parce qu'il y a trois niveaux de certitude : durée connue (bloc à
la hauteur réelle), début connu et fin inconnue (un repère fin, qui ne prétend
rien), aucune heure (une bande « Sans heure » hors de l'axe).

Pour que la durée existe, le formulaire la demande enfin — `EvenementCreate.
date_fin` était accepté par l'API, rien ne le remplissait. « Non précisée » est
la valeur par défaut : le produit n'invente pas un créneau à la place de
l'artisan.

### Les statistiques mélangeaient les périodes

Une pastille « 12 derniers mois » valait pour toute la page, alors que quatre
blocs sur cinq comptent depuis l'ouverture du compte. Et les mois sans
encaissement étaient **absents de la série** : un CA en janvier, février et
septembre donnait trois points côte à côte, que le graphique présentait comme
trois mois consécutifs en progression.

Le dernier point de la courbe est le mois **en cours**. Comparé au mois complet
qui le précède, il produisait un recul mécanique annoncé comme un recul réel :
« −87 % » le 3 du mois. La comparaison porte désormais sur les deux derniers
mois complets, nommés, et le mois en cours est tracé en pointillé avec la raison
écrite en clair.

Deux libellés ne décrivaient pas leur nombre : « Devis envoyés » affichait tous
les devis, brouillons compris ; « Clients récurrents, N % » divisait deux
populations différentes et pouvait dépasser 100 %.

### Un échec de chargement passait pour une absence de données

Douze appels enveloppés dans un `catch` qui rendait un tableau vide. Sur un
dossier client, cela revient à annoncer « aucune facture » à quelqu'un qui en a.
Les vues disent maintenant ce qu'elles n'ont pas pu lire, et proposent de
réessayer.

La phrase elle-même a été fausse deux fois : le verbe suivait le *nombre de
sources* en panne au lieu du sujet (« Les chantiers n'**a** pas pu être
chargé »), puis le participe ne s'accordait jamais en genre (« Les factures
n'ont pas pu être chargé**s** »). Elle a maintenant son test.

---

## 2. L'audit §9, écran par écran

Les vingt-trois compositions décrites par Astra §9, confrontées au code réel.
Rapport complet : [`AUDIT-ASTRA-SECTION-9.md`](AUDIT-ASTRA-SECTION-9.md).

**Onze écrans étaient conformes** — Clients, Devis, Factures, Documents, Avis,
les cinq onglets Entreprise, les pages publiques.

**Douze écarts trouvés, tous traités côté frontend :**

| Écran | Ce qui n'allait pas |
|---|---|
| Aujourd'hui | « Score global 72/100 » : moyenne de cinq échelles sans unité commune. Retiré ; chaque mesure dit ce qu'elle compte |
| Aujourd'hui | Les lignes « À faire » cachaient l'échéance |
| Prospects | Le pipeline occupait la place de la liste de travail |
| Fiche client | Un panneau latéral de 460 px pour l'écran qui rassemble toute la relation |
| Création de devis | Aucun avertissement avant d'abandonner une saisie |
| Paiement | Le solde attendu **après** le règlement n'était pas montré |
| Chantiers | Le total de marge substituait l'estimé au réel sans le dire |
| Fiche chantier | Ni documents ni interventions listés ; dépenses sans intitulé |
| Planning | Une échéance de tâche n'ouvrait pas sa source |
| Tâches | Une tâche sans date était rangée dans « Plus tard » |
| Statistiques | « Clients acquis 18 (86 %) » — 18 clients rapportés à 21 devis |
| Compte | La photo de l'entreprise s'affichait sous « Mon profil » |

Le point le plus délicat fut la **fiche client en page**. Le dossier occupe
maintenant 1 040 px sur 1 366 — mais il n'est **pas une vue** :
`document.body.dataset.view` reste `clients`, la liste demeure montée dessous,
et la refermer ne recharge rien. Recherche et position conservées, focus rendu à
la ligne d'où l'on venait.

Trois écarts ne pouvaient pas se régler côté écran : les interventions d'un
chantier, l'identité individuelle, le cycle des notifications. Le rapport les a
laissés ouverts en nommant ce qui manquait au serveur — et ce sont exactement
les trois sujets des lots backend du §6 ci-dessous. Deux sont clos ; le
troisième ne devait pas l'être, pour la raison dite plus bas.

---

## 3. Ce qui ne se voyait pas du tout

Quatre défauts qu'aucun écran ne signalait.

**Les caches survivaient à la déconnexion.** Seul le jeton était effacé : les
dix-sept caches de données restaient en mémoire. Sur un poste partagé, la
personne suivante se connectait sur un onglet contenant encore les clients, les
devis et les factures de la précédente. Session expirée : même trou. Le test
lit la liste des caches *dans* le fichier — il restera vrai quand un cache sera
ajouté.

**Une réponse lente écrasait une réponse fraîche.** En tapant « ber » puis
« bertrand », la réponse de « ber » pouvait revenir après et gagner.

**Onze fenêtres annonçaient `aria-modal="true"` sans que rien ne le rende
vrai.** La tabulation sortait dans la page derrière ; refermer une fiche
laissait le focus au néant.

**Une réponse perdue était présentée comme un refus.** Le serveur a pu
enregistrer, et c'est la réponse qui s'est perdue : recommencer crée un doublon —
deux factures, deux paiements. L'écriture dit maintenant « L'enregistrement a
peut-être abouti : vérifiez avant de recommencer ».

---

## 4. Performance et états

**Entreprise déclenchait sept appels à l'ouverture** pour un seul panneau
visible. Mesuré après correction : **un** à l'ouverture, un de plus en changeant
d'onglet, zéro en revenant sur un onglet déjà vu.

**Le dossier client téléchargeait tout le compte** — trois listes complètes pour
afficher deux ou trois pièces. Le serveur acceptait `client_id` sur `/devis` et
`/factures` depuis toujours ; le frontend ne le passait jamais.

**L'écran se vidait quand on agissait dessus.** Les quatorze chargeurs
commençaient par remplacer leur liste par des squelettes. Désormais : écran vide
→ squelette ; écran déjà rempli → il reste, en retrait, avec `aria-busy`. Le
voile se lève **de lui-même** quand le contenu est remplacé — un observateur
posé à l'ouverture, donc aucun appel de fin à oublier dans un futur chargeur.

**Un 403 n'est pas une panne.** Le serveur a compris et refuse ; recommencer ne
changera rien. Et la moitié la plus utile : la vue Équipe masquait ses commandes
pour un salarié **sans un mot**, ce qui laisse croire que la fonction n'existe
pas.

---

## 5. Le découpage du frontend (§16)

`app.js` faisait 8 220 lignes en début de session et 9 518 avant le découpage —
les corrections précédentes l'avaient épaissi de 1 300 lignes. Le découpage l'a
ramené à **7 935**, soit sous son point de départ. Quatre domaines extraits :

| Fichier | Lignes | Rôle |
|---|---|---|
| `socle.js` | 418 | formats, états d'écran, messages, confirmations, clavier des fenêtres |
| `navigation.js` | 375 | quelle vue, quelle adresse, comment ouvrir une pièce |
| `planning.js` | 742 | la grille horaire, les durées, le glisser-déposer |
| `statistiques.js` | 256 | le rapport et son graphique |

**La règle : une extraction ne réécrit rien.** Les lignes sont déplacées telles
quelles. Un découpage qui range *et* réécrit n'est pas vérifiable — à la
première régression, on ne sait plus d'où elle vient. La preuve est mesurée à
chaque fois : longueur de code identique au caractère près, différences
uniquement aux coutures.

Détail dans [`DECOUPAGE-FRONTEND.md`](DECOUPAGE-FRONTEND.md), y compris le piège
qui a failli corrompre une extraction (voir plus bas).

Restent `devis.js` et `chantier.js` — les plus lourdes et les plus couplées.

---

## 6. Les évolutions backend

Chacune répond à un besoin démontré par le frontend, et forme son propre lot,
comme Astra le demande. Aucun calcul, aucune permission, aucun abonnement
touché.

1. **`client_id` sur les notifications de message** — le champ existait
   (`Optional`), il n'était pas rempli : « Voir le message » ne pouvait pas
   ouvrir la conversation.
2. **`date_fin` dans le planning agrégé** — `Evenement.date_fin` existait en
   base et dans `EvenementOut` ; l'agrégation l'aplatissait, d'où la durée
   inventée.
3. **La série mensuelle complète** — douze mois pleins, mois vides à zéro. Le
   début de fenêtre reculait de 365 jours depuis le premier du mois, ce qui
   tombe au milieu du mois et tronquait le premier mois.
4. **`client_id` sur `/chantiers`** — il existait sur `/devis` et `/factures`.
5. **`GET /chantiers/{id}/interventions`** — `Evenement.chantier_id` existait,
   mais `/planning` répond par période, pas par chantier.
6. **Le cycle des notifications** — nouvelle table `alertes_reportees`
   (migration `b2c3d4e5f6a7`), `?historique=true`, `POST /notifications/reporter`
   et son annulation.

**Reporter n'efface rien** : la facture reste en retard, l'alerte reparaît le
jour dit, et la ligne l'écrit — « la situation, elle, n'a pas changé ». Une date
passée est refusée en 422, sinon « reporter » deviendrait « masquer ».

### Une évolution que je n'ai pas faite, et pourquoi

J'avais annoncé « l'identité individuelle » comme une évolution backend à venir.
En relisant Astra §21, ce n'est pas ce qu'il demande : il demande de **ne pas
simuler** une identité qui n'existe pas dans le modèle — c'est fait — et de
séparer préférences personnelles et entreprise, ce qui manquait vraiment.
Ajouter `Membre.photo_url` aurait été mon extrapolation, contre le §20 qui met
en garde contre l'ajout d'objets avant validation du besoin.

---

## 7. Trois fois où le défaut était dans l'outil, pas dans le produit

Ces épisodes valent d'être consignés : sans eux, on corrige du vide, ou on croit
avoir vérifié ce qu'on n'a pas vérifié.

**L'auditeur de contraste rendait un tableau, pas un objet.** Chaque sonde lisait
`res.echecs` sur un tableau — donc `undefined`, donc `[]`, donc « zéro échec »
quoi qu'il arrive. Tous les « zéro échec » rapportés avant ce correctif étaient
la longueur d'un tableau vide.

**`focusin` ne se déclenche pas quand le document n'a pas le focus système.** La
restitution du focus semblait cassée ; elle ne l'était pas, le mécanisme de
détection l'était. D'où le choix de retenir le déclencheur au **geste** (clic,
touche) plutôt qu'à l'événement de focus — ce qui vaut aussi pour un utilisateur
dont la fenêtre vient de perdre la main.

**Git Bash mange une barre oblique.** Le script d'extraction prend ses marqueurs
en argument ; un argument commençant par `//` — tous les marqueurs de section en
commencent — subit la conversion de chemin MSYS. Le bloc extrait emportait le
`/` de la ligne suivante. C'est la mesure de longueur qui l'a signalé.

Et une fois, j'ai failli « corriger » un `total_heures.toFixed()` non gardé :
vérification faite côté serveur, la propriété ne vaut `None` que quand la liste
est vide, cas où le bloc n'est pas rendu. Pas de bug.

Le jeu d'essai, lui, a été corrigé une dizaine de fois — un `id` de notification
qui numérotait la notification au lieu de la pièce, un filtre de statut ignoré,
un drapeau d'archive tombé dans le mauvais paramètre, quatre lectures par
identifiant non simulées. Chacun de ces défauts faisait passer une vue saine
pour cassée.

---

## 8. Ce qui reste

- **La contradiction §7–8** : Astra propose d'abandonner la palette Atelier pour
  une palette neutre (`#F6F7F8` / `#245548`). Votre consigne diffère la direction
  artistique à une seconde passe, et le §20 d'Astra dit lui-même de ne pas
  commencer par l'architecture visuelle. Aucune couleur n'a été touchée — **cet
  arbitrage vous revient**.
- **Les 30 marqueurs `[À COMPLÉTER]` légaux**, que vous aviez remis à plus tard.
- **`devis.js` et `chantier.js`** à extraire, quand le besoin s'en fera sentir.
- **L'entité *Affaire*** (§5), qu'Astra range lui-même en « à arbitrer
  séparément » et que son §20 déconseille d'introduire avant validation.
- La modale tarifs rogne sa rangée de boutons — signalé, non corrigé.

### Deux points d'environnement

- `backend/tests/test_startup_checks.py` échoue sur deux tests, **avant comme
  après** ces travaux : un `ADMIN_PASSWORD` de démonstration présent dans
  l'environnement local. Sans rapport avec ces changements.
- `graphify update .` est bloqué par la politique de contrôle d'applications de
  cette machine : le graphe du dépôt n'est donc pas à jour.

---

## Vérification

À chaque lot, sans exception :

- **25 tests frontend** (`node --test frontend/tests/*.test.mjs`) ;
- **142 tests backend** (`pytest backend/tests`), moins les deux ci-dessus ;
- **un balayage des 13 vues** × compte peuplé et compte vide × bureau (1366) et
  mobile (390) : aucune erreur console, aucun débordement horizontal, aucun
  échec de contraste — environ 1 380 éléments audités par passage ;
- **les sondes de comportement rejouées** : treize parcours d'ouverture d'objet
  sous latence, les trois états de la grille horaire, les quatre liens des
  statistiques avec leurs ouvertures filtrées, le dossier client et ses filtres
  conservés, l'isolation des caches, le clavier des fenêtres.

Dix-neuf tests sont nouveaux — dont plusieurs remplacent des assertions qui
citaient une forme de code disparue et **ne vérifiaient donc plus rien**.
