// Source unique de verite pour l'URL de l'API, partagee par les 5 points
// d'entree frontend (index.html/api.js + les 4 pages publiques
// devis-public/facture-public/avis-public/portail-client). Avant ce fichier,
// chacun definissait sa propre constante API_BASE codee en dur sur
// localhost:8000 : plus jamais a editer un par un a chaque environnement.
//
// Resolution, dans l'ordre :
//   1. window.SUITE_ARTISAN_API_BASE deja definie (par env.js, charge juste
//      avant ce fichier) - c'est le point d'override pour staging/production,
//      sans toucher au code source ni le committer (voir env.example.js).
//   2. Developpement local (hostname localhost/127.0.0.1) : le port par
//      defaut du backend en dev, http://localhost:8000.
//   3. Sinon (env.js absent) : meme origine que la page. Suppose un reverse
//      proxy qui expose l'API sous le meme domaine que le frontend - le cas
//      le plus courant. Si l'API vit sur un domaine different, definir
//      SUITE_ARTISAN_API_BASE dans env.js pour cet environnement.
(function () {
  if (typeof window.SUITE_ARTISAN_API_BASE === "string" && window.SUITE_ARTISAN_API_BASE) return;
  var isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  window.SUITE_ARTISAN_API_BASE = isLocal ? "http://localhost:8000" : window.location.origin;
})();
