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

**Corrigé.**

Le « Score global » a disparu de l'écran : il valait la moyenne arithmétique de
cinq échelles sans unité commune. Le serveur le calcule toujours — le contrat
d'API ne change pas — mais chacune des cinq mesures dit maintenant ce qu'elle
compte. Les lignes « À faire » exposent leur échéance : la date dépassée d'une
facture, la date d'envoi d'un devis qui attend, l'échéance d'une tâche.

## 2. Prospects

**Corrigé.**

La liste de travail est devenue la vue principale : les prospects actifs y sont
ordonnés par ancienneté du dernier mouvement, chacun avec sa prochaine action —
ou « à définir », qui est une information en soi — son contact composable, sa
source et le temps écoulé. Le pipeline reste à un clic, pour ce à quoi il sert :
comparer les étapes.

## 3. Clients

**Conforme.**

Répertoire de relations et non second pipeline ; recherche en tête puis filtres ;
un clic ouvre le dossier exact ; les trois absences sont distinguées (aucun
client / aucun résultat de recherche / données indisponibles) par `etatVide`,
`etatFiltre` et `bandeauCharge`.

## 4. Fiche client

**Corrigé.**

Le dossier tenait dans un panneau latéral de 460 px superposé au répertoire :
une fenêtre modale, pour l'écran qui rassemble toute la relation avec un
client — son identité, ses affaires, ses documents, ses échanges, sa
chronologie. Il occupe désormais la pleine largeur (1040 px sur 1366), à la
place de la liste.

Le point délicat était de ne pas perdre ce que la liste avait en mémoire. Le
dossier n'est donc **pas une vue** : `document.body.dataset.view` reste
`clients` ou `prospects`, la liste demeure montée dessous, et la refermer ne
recharge rien. Vérifié : recherche « Bertrand » et position conservées à
l'ouverture comme au retour, sur bureau et sur mobile, et le focus revient à
la ligne d'où l'on venait.

Ce n'est plus une fenêtre — ni `role="dialog"`, ni `aria-modal`, ni croix de
fermeture : rien n'est superposé, il n'y a rien à confiner, et on la quitte
par un retour.
## 5. Devis

**Conforme.**

Registre orienté décision ; en-tête et lignes partagent la même
`grid-template-columns` (`.list-row-devis, .list-header-row-devis`) ; les états
distinguent non chiffré, en attente et décidé ; recherche de largeur modérée et
filtres non compressés.

## 6. Création de devis

**Corrigé.**

Conforme : espace documentaire complet ; totalisateur réutilisé ; sauvegarde et
envoi distincts ; aucune TVA par ligne — `LigneDevisIn` n'en porte pas.

Un devis en cours de saisie est désormais protégé : la comparaison porte sur une
empreinte prise à l'ouverture, et non sur « des champs sont non vides » — les
valeurs par défaut auraient réclamé une confirmation sur un formulaire auquel
personne n'avait touché.

## 7. Factures

**Conforme.**

Registre financier avec numéro, total, payé, restant, échéance et action ;
émission, règlement et retard distingués ; montants alignés à droite en chiffres
tabulaires ; en-tête et lignes sur la même grille.

## 8. Facture et paiement

**Corrigé.**

Le formulaire de paiement montre les trois chiffres qu'Astra demande : solde
avant, montant, et solde attendu après. Un montant supérieur au solde se voit
avant l'envoi, là où le serveur le refusait après coup.

## 9. Chantiers

**Corrigé.**

Le total de marge substituait l'estimé au réel dès qu'il manquait, et présentait
la somme comme un seul chiffre. Il annonce maintenant de quoi il est fait :
« marge réelle », « marge prévisionnelle », ou le total avec le nombre de
chantiers encore estimés.

## 10. Fiche chantier

**Éprouvée, puis corrigée en partie.**

Éprouvée en pilotant le navigateur sur un chantier peuplé — notes, dépenses,
heures et tâches aux formes exactes du serveur.

Conforme : bandeau opérationnel (titre, client, lieu, statut, début, livraison
prévue) ; **avancement d'exécution et situation financière séparés** — deux
jauges nommées, puis une ligne financière distincte ; les pièces gardent leur
rattachement.

Corrigé : les dépenses n'avaient pas d'intitulé de section alors que les heures
en avaient un ; l'historique non plus. Et surtout, **les documents rattachés au
chantier n'étaient pas listés** — `Document.chantier_id` existe depuis toujours,
mais il fallait ouvrir la vue Documents et y retrouver le bon rattachement à la
main. La fiche compte désormais six sections : préparation et tâches, dépenses,
heures, documents et photos, historique, réception.

Reste : **aucune section « interventions ».** Les événements portent un
`chantier_id`, mais aucun endpoint ne permet de demander les interventions d'un
chantier — `/planning` répond par période, pas par chantier. C'est une évolution
backend (filtre `chantier_id` sur `/planning`, ou route dédiée), à traiter comme
telle et non à contourner en chargeant le planning entier.

## 11. Planning

**Corrigé.**

Conforme : semaine horaire sur bureau ; durées réelles depuis que
`PlanningItem.date_fin` existe ; échéances et débuts de chantier dans une bande
sans heure ; aucun conflit d'équipe déduit d'un chevauchement.

Une échéance de tâche ouvre maintenant sa source : le chip est cliquable, la vue
Tâches s'ouvre et la ligne est mise en avant. Masquée par un filtre, elle est
signalée plutôt qu'ignorée.

## 12. Tâches

**Corrigé.**

Une tâche sans échéance tombait dans « Plus tard », ce qui sous-entend une date
future qu'elle n'a pas, et la noyait parmi des tâches datées où elle ne remontait
jamais. Elle a désormais son propre groupe, placé en dernier : ces tâches n'ont
pas d'urgence à revendiquer.

## 13. Documents

**Conforme.**

Explorateur contextualisé ; aucune date d'expiration ni statut de conformité
inventé pour un simple fichier — ces notions vivent dans l'onglet Conformité,
sur des éléments déclarés pour cela.

## 14. Statistiques

**Corrigé.**

Conforme : périodes annoncées par section ; mois sans paiement présents ; mois
en cours distingué ; base et population nommées.

Les deux écarts sont traités :

1. Le pourcentage entre populations différentes a disparu. « Clients acquis
   18 (86 %) » rapportait 18 clients à 21 devis signés ; le taux ne se calcule
   plus qu'entre deux étapes qui comptent la même chose.
2. Quatre chiffres ouvrent leurs éléments sources, avec le filtre exact :
   devis créés, devis signés, montants à encaisser, factures payées. Les
   chiffres dont la population n'a pas de filtre équivalent — le taux de
   signature porte sur les devis « décidés », les clients acquis sur un statut
   absent de l'annuaire — n'ont volontairement aucun lien : ouvrir un
   sur-ensemble en prétendant montrer la source serait pire que de ne rien
   ouvrir.

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

**Corrigé.**

Conforme : onboarding court et interrompable ; aucune création de données
d'exemple ; reprise après expiration de session.

La photo appartient à `Artisan`, donc à l'entreprise. Elle s'affichait dans la
pastille « Mon profil », où un salarié connecté croyait voir la sienne.
L'intitulé nomme maintenant les deux, le texte de remplacement de l'image nomme
l'entreprise, et le formulaire dit qu'elle est commune à toutes les personnes
qui s'y connectent. Aucune identité individuelle n'est simulée — c'est une
évolution backend qu'Astra range à part.

## 22. Notifications

**Corrigé.**

Chaque entrée ouvre l'objet précis, et dit maintenant **pourquoi elle
apparaît** : les cinq phrases décrivent la condition réellement évaluée par le
serveur. Sans cela, une alerte qui revient ou qui manque est incompréhensible —
on ignore quel réglage la gouverne.

Non applicable : reporter, traiter et consulter l'historique demandent le contrat
explicite qu'Astra range en évolution backend — le routeur mélange aujourd'hui
notifications persistantes et alertes calculées.

## 23. Pages client et Admin interne

**Conforme.**

Aucune navigation du SaaS ni donnée interne dans le portail client, le devis
public ou la page d'avis ; lien invalide et lien expiré ont chacun leur état ;
aucun retour du générateur de sites supprimé.

---

## Récapitulatif

| Verdict | Écrans |
|---|---|
| Conforme à l'audit | 3, 5, 7, 13, 15, 16, 17, 18, 19, 20, 23 — **11** |
| Écart corrigé | 1, 2, 4, 6, 8, 9, 11, 12, 14, 21, 22 — **11** |
| Corrigé en partie | 10 — **1** |

Douze écarts nommés, tous traités côté frontend. Ce qui reste demande le
serveur, et Astra le range lui-même à part :

- **§9-10, les interventions d'un chantier.** `/planning` répond par période,
  pas par chantier. Charger le planning entier pour filtrer côté client serait
  exactement ce que §14 reproche.
- **§9-21, l'identité individuelle.** La photo appartient à `Artisan` ; aucune
  identité par personne n'existe dans le modèle, et rien ne la simule.
- **§9-22, le cycle des notifications.** Reporter, traiter et consulter
  l'historique demandent un contrat explicite : le routeur mélange aujourd'hui
  notifications persistantes et alertes calculées.

Chaque correction est vérifiée en pilotant le navigateur, pas seulement en
relisant le code — et trois d'entre elles ont d'abord révélé un défaut dans le
jeu d'essai ou dans la sonde, pas dans le produit.
