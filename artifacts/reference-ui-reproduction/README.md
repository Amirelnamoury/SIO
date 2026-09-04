# Captures de comparaison UI (reproduction fidele des references)

Captures d'ecran du frontend reel (donnees API reelles, aucune valeur
d'exemple codee en dur) pour les 13 vues principales, a comparer aux
images de reference visuelle fournies pour ce lot de travail.

- `desktop/*.png` — 1440x900, les 13 vues (dashboard, prospects, clients,
  devis, factures, chantiers, planning, taches, documents, statistiques,
  avis, entreprise, notifications).
- `mobile/*.png` — 390x844, le sous-ensemble minimal demande (dashboard,
  prospects, clients, devis, factures, chantiers, planning, entreprise).

Chaque image est un cadrage fixe d'une seule fenetre de navigateur (pas
un defilement plein page), pour rester comparable au cadrage des
images de reference elles-memes (egalement des captures d'une seule
fenetre, ~1376x768).

## Methode de capture

Aucun outil d'automatisation navigateur (Playwright, Puppeteer, Selenium)
n'est installe dans cet environnement — la suite E2E du projet documente
deja la meme limite pour son propre scenario 13. Ces captures ont donc
ete produites en pilotant directement, via le protocole CDP brut (sans
dependance externe, juste `node:child_process` + le `WebSocket` natif de
Node 22+), le binaire Microsoft Edge deja present sur la machine :

1. Lancement d'Edge en `--headless=new` avec un profil temporaire et
   `--remote-debugging-port`.
2. Connexion WebSocket a la cible ouverte via l'API HTTP `/json/new` du
   DevTools Protocol.
3. Un jeton d'authentification deja valide (recupere depuis
   `localStorage.suite_artisan_token` d'une session de verification
   interactive de ce meme compte de test) est injecte dans le
   `localStorage` de la page avant rechargement, pour demarrer
   directement sur le tableau de bord authentifie.
4. Pour chaque vue : `Emulation.setDeviceMetricsOverride` (taille de
   fenetre), `switchView("<vue>")` (fonction deja exposee par
   `app.js`), puis `Page.captureScreenshot`.

Le script est jetable et n'a pas ete integre au depot (il ne remplace
pas la suite E2E ni n'ajoute de dependance) ; il a servi uniquement a
produire ces fichiers et a verifier visuellement plusieurs pages a une
largeur bureau reelle, ce que le panneau de navigateur interactif
utilise pendant le reste de ce lot ne permettait pas (largeur plafonnee
a ~530px quel que soit le preset demande). Cette verification a
directement mene a la correction de deux bugs reels : le mode actif
Jour/Semaine/Mois du Planning qui paraissait moins marque que les
inactifs, et les 8 sections Entreprise toutes visibles simultanement
avant le tout premier clic sur un onglet.
