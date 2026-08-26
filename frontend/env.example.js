// Gabarit : copier ce fichier en env.js (non versionne, voir .gitignore)
// sur chaque environnement staging/production ou l'API n'est PAS accessible
// sur la meme origine que le frontend (donc ou le defaut same-origin de
// config.js ne convient pas). Charge avant config.js : si la variable est
// deja definie ici, elle prend le pas sur la detection automatique.
//
// Ne pas committer de vraie URL de production dans ce depot - env.js reste
// local a chaque environnement de deploiement.
window.SUITE_ARTISAN_API_BASE = "https://api.exemple.invalid";
