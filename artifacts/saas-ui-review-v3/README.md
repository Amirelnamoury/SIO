# Suite Artisan — Revue visuelle V3 (captures d'écran)

Ce dossier contient les captures d'écran de vérification de la refonte visuelle V3,
prises avec Playwright/Chromium contre l'application réelle (backend + frontend
lancés localement), avec de vraies données créées via l'API (deux comptes de
test : un compte neuf et un compte avec activité — clients, devis, factures,
chantiers, planning, tâches, avis).

## Portée de ce dossier (volontairement hors du commit Git)

Le brief demande ce paquet de captures "en repo". Il demande aussi, de façon
répétée et explicite, un commit unique contenant **exactement**
`frontend/index.html`, `frontend/style.css`, `frontend/app.js` — rien d'autre.
Ces deux exigences sont en tension : ajouter `artifacts/` au commit violerait
la contrainte de contenu exact du commit.

Choix fait ici : ce dossier est bien généré sur disque, dans le repo, à
l'emplacement demandé (`artifacts/saas-ui-review-v3/`), mais il n'est **pas**
ajouté à l'index Git (`git add`) et ne fait donc partie d'aucun commit. Les
captures sont aussi envoyées directement à l'utilisateur (fichiers joints)
pour une revue immédiate sans avoir à checkout la branche. Si l'utilisateur
préfère que ce dossier soit malgré tout committé (dans un commit séparé, après
le commit produit), c'est un aller-retour d'une minute.

## desktop/ (1440×900)

01. Dashboard — compte neuf (état d'accueil, sans données)
02. Dashboard — compte avec activité (KPI, agenda du jour, à faire)
03. Formulaire Devis
04. Liste des Factures (avec en-tête trésorerie)
05. Formulaire Facture
06. Liste des Clients
07. Fiche client (détail + timeline)
08. Prospects (kanban)
09. Chantiers (liste avec statuts, avancement, actions)
10. Formulaire Chantier
11. Planning (grille horaire semaine)
12. Tâches
13. Documents (état vide)
14. Statistiques
15. Avis clients
16. Entreprise (page + sous-formulaires)
17. Notifications
18. Connexion (auth)
19. Inscription (auth)

## mobile/ (390×844)

01. Dashboard — compte neuf
02. Dashboard — compte avec activité
03. Liste des Devis
04. Formulaire Devis (correction du bug de grille signalé plus bas)
05. Liste des Factures
06. Fiche client
07. Chantiers
08. Connexion
09. Inscription

## tablet/ (1024×768)

01. Dashboard

## Bug réel trouvé et corrigé pendant la revue

`mobile/04-devis-form.png` est la capture **après correction** : la grille CSS
de l'éditeur de lignes de prestations écrasait le champ "Unité" sur mobile
(colonnes `1fr 30px` appliquées à la ligne qté/unité/prix). Corrigée en
`repeat(3, 1fr) 30px` avec zones dédiées. Capture "avant" non conservée
(remplacée en place pendant l'itération), corrigée avant la fin de la session.
