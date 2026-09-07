# Audit §9 — architecture de chaque écran

Confrontation des vingt-trois écrans décrits par Astra §9 au code réel du dépôt.
Chaque verdict est établi en lisant le code ou en pilotant le navigateur, jamais
de mémoire. Trois valeurs possibles :

- **Conforme** — l'exigence est satisfaite, et je peux dire où.
- **Écart** — l'exigence n'est pas satisfaite ; la cause est nommée.
- **Non applicable** — l'exigence suppose une capacité que le produit n'a pas
  (entité, endpoint, champ), et Astra la range lui-même en évolution backend.

Une exigence non vérifiable sans utilisateur réel (« objectif : décider quoi
faire ») est notée **non éprouvée** : elle ne peut pas être cochée depuis le
code.

---

## 1. Aujourd'hui

**Écart.**

Conforme : composition asymétrique (file d'actions « À faire », agenda du jour,
puis chiffres du mois) ; première action réelle proposée sur un compte vide
(« Ajouter un client », « Créer un devis ») ; une source en panne n'efface plus
les autres (`bandeauCharge`).

Écarts :

1. **Score global opaque.** `santeWidgetHtml` affiche « 72/100 · Score global ».
   Le serveur le calcule comme la moyenne arithmétique de cinq sous-scores
   (`routers/dashboard.py`) qui ne partagent aucune unité : un taux de
   signature, une part de montant non en retard, une part de chantiers dans
   leur budget, une pénalité de 25 points par document expiré, une part de
   tâches à l'heure. La moyenne de ces cinq échelles n'est pas un fait
   d'entreprise. Astra : « Aucun score opaque ».
2. **Les cinq sous-scores ne disent pas ce qu'ils mesurent.** « Commercial
   65/100 » est exact mais illisible sans la formule.
3. **Les lignes « À faire » n'exposent pas l'échéance.** Astra demande objet,
   raison, échéance et action. Une facture en retard affiche « FA-2026-014 · en
   retard » sans la date dépassée, alors que `date_echeance` est disponible.

## 2. Prospects

**Écart.**

Conforme : filtres conservés au retour d'une fiche (routage) ; colonnes vides
repliées ; pas de débordement horizontal à 390 px.

Écart : **le pipeline est la vue principale.** Astra demande une liste de
travail ordonnée par prochaine action, le pipeline restant facultatif pour
comparer les étapes. `loadClients()` rend la réglette puis les neuf colonnes ;
aucune liste par prochaine action n'existe, alors que `prochaine_action` et
`updated_at` sont déjà renvoyés par l'API.

## 3. Clients

**Conforme.**

Répertoire de relations et non second pipeline ; recherche en tête puis filtres ;
un clic ouvre le dossier exact ; les trois absences sont distinguées (aucun
client / aucun résultat de recherche / données indisponibles) par `etatVide`,
`etatFiltre` et `bandeauCharge`.

## 4. Fiche client

**Écart.**

Conforme : identité compacte, affaires liées, chronologie ; les affaires
ouvrent la pièce exacte ; adresse propre (`#/clients/<id>`).

Écart : **c'est un panneau latéral, pas une page.** Astra demande explicitement
de lui « donner une adresse et davantage de place ». L'adresse est faite, la
place non : le dossier reste contraint à la largeur d'un panneau superposé au
répertoire.

## 5. Devis

**Conforme.**

Registre orienté décision ; en-tête et lignes partagent la même
`grid-template-columns` (`.list-row-devis, .list-header-row-devis`) ; les états
distinguent non chiffré, en attente et décidé ; recherche de largeur modérée et
filtres non compressés.

## 6. Création de devis

**Écart.**

Conforme : espace documentaire complet ; totalisateur réutilisé ; sauvegarde et
envoi distincts ; **aucune TVA par ligne** — `LigneDevisIn` n'en porte pas, le
formulaire n'en propose pas.

Écart : **aucun avertissement avant abandon.** Fermer le formulaire ou changer
de vue perd les lignes saisies sans un mot.

## 7. Factures

**Conforme.**

Registre financier avec numéro, total, payé, restant, échéance et action ;
émission, règlement et retard distingués ; montants alignés à droite en chiffres
tabulaires ; en-tête et lignes sur la même grille.

## 8. Facture et paiement

**Écart.**

Conforme : document d'abord, règlements ensuite ; conversion depuis un devis
avec origine visible et sans ressaisie ; validation serveur contre le
surpaiement conservée ; champ pré-rempli au solde restant.

Écart : **le solde attendu après confirmation n'est pas montré.** Astra demande
les trois : solde avant, montant, solde après. Seuls les deux premiers existent.

## 9. Chantiers

**Écart.**

Conforme : liste par démarrage et activité ; client, lieu et avancement sourcés ;
sur une carte, une marge réelle absente s'affiche « — » et non zéro.

Écart : **le total de marge du bandeau mélange réel et estimé sans le dire.**
`margeTotale` retient `marge_reelle` quand elle existe, sinon `marge_estimee`,
et présente la somme comme un seul chiffre. Astra : « Une marge incomplète reste
annoncée comme telle. »

## 10. Fiche chantier

**Non éprouvée.**

La séparation « avancement d'exécution » / « situation financière » et les
conséquences explicites de réception, arrêt et clôture demandent un parcours
complet à mener écran en main. Je ne l'ai pas fait : je ne peux ni cocher ni
invalider.

## 11. Planning

**Écart.**

Conforme : semaine horaire sur bureau ; durées réelles depuis que
`PlanningItem.date_fin` existe ; échéances et débuts de chantier dans une bande
sans heure ; aucun conflit d'équipe déduit d'un chevauchement.

Écart : **les entrées dérivées n'ouvrent pas leur source.** Un chip de tâche
n'est pas cliquable : `planningItemChip` ne marque `planning-item-clickable` que
pour les événements et les débuts de chantier.

## 12. Tâches

**Écart.**

Conforme : file d'exécution ; titre, contexte, échéance et priorité ; cocher
signifie tâche faite et rien d'autre ; grandes cibles au tactile.

Écart : **une tâche sans échéance est rangée dans « Plus tard ».** `tacheGroupe`
renvoie `plus_tard` quand `t.echeance` est absente : une date future est donc
sous-entendue là où il n'y en a aucune. Astra demande un groupe « sans date ».

## 13. Documents

**Conforme.**

Explorateur contextualisé ; aucune date d'expiration ni statut de conformité
inventé pour un simple fichier — ces notions vivent dans l'onglet Conformité,
sur des éléments déclarés pour cela.

## 14. Statistiques

**Écart.**

Conforme : périodes annoncées par section ; mois sans paiement présents ; mois
en cours distingué ; base et population nommées.

Écarts :

1. **Un pourcentage entre deux populations différentes.** L'entonnoir affiche
   « Clients acquis 18 (86 %) » : 18 clients rapportés à 21 devis signés. Astra
   l'interdit explicitement pour cet écran.
2. **Aucun résultat n'ouvre ses éléments sources.**

## 15. Avis

**Conforme.**

Collecte à effectuer, avis reçus et sélection pour le site séparés ; auteur,
date, source et texte prioritaires ; moyenne toujours accompagnée du nombre
(« 4,7 sur 5, sur 12 avis ») ; aucune synchronisation Google annoncée ; aucun
témoignage de démonstration.

## 16. Entreprise — Profil et Identité visuelle

**Conforme.**

Sections ouvertes, deux colonnes sur bureau et une sur mobile, sauvegarde par
ensemble cohérent, aucune jauge de complétude arbitraire.

## 17. Entreprise — Équipe

**Conforme.**

Annuaire compact ; état verrouillé distinct d'une équipe vide ; **ni photo
individuelle ni affectation aux chantiers** ne sont présentées — ce sont
précisément les capacités absentes qu'Astra demande de ne pas simuler.

## 18. Entreprise — Prestations et Fournisseurs

**Conforme.**

Deux compositions distinctes ; aucune métrique d'achat fictive ; aucune action
sans endpoint correspondant.

## 19. Entreprise — Automatisations et Contrats

**Conforme.**

Contrats présentés en échéancier ; suspension et résiliation restent
différentes ; un résultat partiel distingue facture créée et email non envoyé
(`feedbackGenerationContrat` couvre les quatre statuts email réels).

## 20. Entreprise — Conformité

**Conforme.**

La couleur accompagne toujours un libellé : « Expiré », « Expire dans N j »,
« À jour ». Absence de justificatif et pièce expirée sont distinctes.

## 21. Compte, authentification et onboarding

**Écart.**

Conforme : onboarding court et interrompable ; **aucune création de données
d'exemple** ; reprise après expiration de session.

Écart : **la photo est présentée comme celle de la personne connectée.** Elle
est portée par `Artisan` (`models.py:52`), donc par l'entreprise. Un salarié
connecté voit la photo de l'entreprise à la place de la sienne.

## 22. Notifications

**Écart.**

Conforme : chaque entrée ouvre l'objet précis (corrigé cette session) ; lire
n'efface pas une facture en retard, recalculée à chaque chargement ; liste
chronologique sans badges redondants.

Écart : **l'entrée n'indique pas pourquoi elle apparaît.** Le sous-titre porte
un contexte (« Bertrand · 1 840 € restent à encaisser ») mais jamais la règle
qui a déclenché l'alerte.

Non applicable : reporter, traiter et consulter l'historique demandent le
contrat explicite qu'Astra range en évolution backend — le routeur mélange
aujourd'hui notifications persistantes et alertes calculées.

## 23. Pages client et Admin interne

**Conforme.**

Aucune navigation du SaaS ni donnée interne dans le portail client, le devis
public ou la page d'avis ; lien invalide et lien expiré ont chacun leur état ;
aucun retour du générateur de sites supprimé.

---

## Récapitulatif

| Verdict | Écrans |
|---|---|
| Conforme | 3, 5, 7, 13, 15, 16, 17, 18, 19, 20, 23 — **11** |
| Écart | 1, 2, 4, 6, 8, 9, 11, 12, 14, 21, 22 — **11** |
| Non éprouvée | 10 — **1** |

Treize écarts nommés, tous frontend sauf deux : la photo individuelle (§21) et
le cycle des notifications (§22), qu'Astra range lui-même en évolutions backend
à arbitrer séparément.
