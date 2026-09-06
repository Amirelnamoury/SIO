# Assets — écran connexion / inscription

Deux photographies d'atelier, volontairement **différentes de celles de la
visite de la landing** : l'écran d'authentification a sa propre respiration.

| Fichier | Écran | Sujet |
|---|---|---|
| `connexion.webp` | Connexion | outils d'artisan disposés sur un établi en bois sombre |
| `inscription.webp` | Inscription | rabot et copeaux de bois |

`auth.css` bascule de l'une à l'autre selon l'onglet actif, via
`:has(#register-form:not([hidden]))` — sans JavaScript ni duplication du
panneau dans `index.html`.

## Provenance et licence

Les deux images sont en **CC0 1.0** (domaine public) : usage commercial
libre, **aucune attribution requise**, aucune redevance.

| Fichier | Titre d'origine | Licence | Source |
|---|---|---|---|
| `connexion.webp` | *Carpenter toolkit displayed showing tools* | CC0 1.0 | [rawpixel.com/image/3237401](https://www.rawpixel.com/image/3237401/free-photo-image-hammer-wood-creative-commons) |
| `inscription.webp` | *Slivers shaved wood next hand* | CC0 1.0 | [rawpixel.com/image/3303918](https://www.rawpixel.com/image/3303918/free-photo-image-apparel-cc0-clothing) |

Trouvées via l'API [Openverse](https://openverse.org), filtrée sur
`license=cc0` et `category=photograph`.

> **À vérifier avant mise en production.** La licence indiquée ci-dessus est
> celle déclarée par la source au moment du téléchargement. Pour un site
> commercial, il est prudent de la reconfirmer sur la page d'origine et
> d'en conserver une copie datée. Aucune des deux images ne comporte de
> personne reconnaissable ni de marque tierce visible — deux critères qui
> avaient fait écarter d'autres candidates.

## Format

Redimensionnées à 900 px de large et converties en WebP (qualité 80) :
55 Ko et 19 Ko. Le panneau fait au plus ~660 px de large sur un écran de
1440 px, donc 900 px suffit largement, y compris sur écran dense.

Pour régénérer après remplacement d'une image :

```js
sharp(source)
  .resize({ width: 900, withoutEnlargement: true, kernel: "lanczos3" })
  .webp({ quality: 80, effort: 6 })
```
