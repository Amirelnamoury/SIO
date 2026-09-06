# Assets — écran connexion / inscription

Deux visuels d'atelier propres à cet écran, **distincts des frames de la
visite** de la landing : l'authentification a sa propre respiration, tout
en gardant la même lumière dorée.

| Fichier | Écran | Sujet |
|---|---|---|
| `connexion.webp` | Connexion | artisan en tablier consultant une tablette dans son atelier, camionnette et paysage au fond |
| `inscription.webp` | Inscription | établi de créateur : plans, échantillons de matériaux, ordinateur portable, fenêtre au couchant |

`auth.css` bascule de l'un à l'autre selon l'onglet actif, via
`:has(#register-form:not([hidden]))` — sans JavaScript ni duplication du
panneau dans `index.html`.

## Origine

Les deux images sont **générées par intelligence artificielle**, comme le
logo (`assets/landing/logo.webp`) et les 20 frames de la visite. Elles ont
été fournies par l'éditeur du site.

Conséquences pratiques, utiles à garder en tête :

- **Aucune licence de banque d'images à respecter**, aucune attribution à
  afficher, aucune redevance.
- **La personne visible sur `connexion.webp` n'existe pas.** Il n'y a donc
  aucun droit à l'image à obtenir — contrairement à une photographie de
  stock montrant un modèle réel.
- Ce ne sont **pas des chantiers réalisés par des clients** de Suite
  Artisan. Les mentions légales le précisent déjà pour les photographies
  de la page d'accueil ; la formulation couvre également celles-ci.

## Format

Sources en 1122 × 1402 (portrait), redimensionnées à 900 px de large et
converties en WebP (qualité 78) : **61 Ko** et **82 Ko**.

Le format portrait correspond à celui du panneau : le recadrage
`object-fit: cover` ne rogne donc presque rien, contrairement à une image
en paysage qu'il aurait fallu tailler sévèrement.

Pour régénérer après remplacement d'une image :

```js
sharp(source)
  .resize({ width: 900, withoutEnlargement: true, kernel: "lanczos3" })
  .webp({ quality: 78, effort: 6 })
```
