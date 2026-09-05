# Assets — landing page publique

## `frames/` — les 20 photographies de la visite

La landing (`frontend/landing.html`) est une visite photographique pilotée
par le scroll. Les 20 frames, nommées `frame-a` … `frame-t`, suivent
l'ordre narratif de la visite :

| Frame | Plan | Chapitre |
|---|---|---|
| a, b | vue extérieure, approche de la façade | 01 — Arrivée |
| c, d, e | porte fermée, porte ouverte, seuil | 02 — L'entrée |
| f, g, h, i | hall, salle de bain | 03 — Le terrain |
| j, k, l | retour hall, local technique | 04 — La technique |
| m, n, o | pièce en travaux, **puis la même terminée** | 05 — Le chantier |
| p, q, r | hall, bureau, poste informatique | 06 — Le bureau |
| s, t | ouverture, salon final | 07 — Le salon |

`n` et `o` sont cadrées à l'identique : c'est ce qui permet le volet
avant/après (`clip-path`) sans aucun décalage visible.

### Format et poids

Chaque frame existe en deux largeurs, servies via `srcset` :

- `frame-x.webp` — 1920 px (desktop)
- `frame-x-sm.webp` — 1100 px (mobile / tablette)

Total : **~2,6 Mo** pour le jeu desktop, contre 46 Mo pour les JPEG
d'origine. Et rien n'est chargé d'avance : seule `frame-a` est préchargée,
`landing.js` va ensuite chercher les frames au fur et à mesure de la
descente (3 d'avance).

**Pourquoi WebP et pas AVIF** : ces images sont des fonds plein écran
qu'on enchaîne au scroll, donc le temps de *décodage* compte autant que le
poids. L'AVIF gagnerait ~30 % de taille mais décode nettement plus
lentement, ce qui se verrait sur un fondu.

### Régénérer les WebP

Les JPEG d'origine (2752 × 1536) ne sont pas versionnés — ils sont trop
lourds pour Git. Ils sont conservés hors dépôt, à l'endroit où ils ont été
fournis. Pour reconstruire les WebP à partir d'eux, avec `sharp` :

```js
sharp(source)
  .resize({ width: 1920, withoutEnlargement: true, kernel: "lanczos3" })
  .webp({ quality: 82, effort: 6 })   // 1100 px / qualité 74 pour la variante -sm
```

## Écran produit du bureau (frame R)

Le moniteur de la frame `r` est volontairement laissé **neutre**. Aucune
capture du SaaS n'y est incrustée : l'application est en cours de refonte,
et y coller une image périmée serait trompeur.

L'emplacement est prêt dans `landing.js` (constante `PRODUCT_SCREEN`) : il
suffit de déposer une capture validée et de renseigner son chemin.

```js
var PRODUCT_SCREEN = {
  src: "assets/landing/product-screen.webp",
  left: 48.9, top: 45.5, width: 13.8, height: 16.3   // en % de la photo
};
```

Le positionnement tient compte du recadrage `object-fit: cover`, donc
l'écran reste calé sur le moniteur quelle que soit la taille du viewport.

## Autres ressources

Aucune autre ressource externe n'est chargée, hormis :

- les deux polices Google Fonts (**Fraunces** et **Inter**), toutes deux
  sous licence SIL Open Font License 1.1, libres d'usage commercial ;
- **GSAP 3.12.5 + ScrollTrigger**, servis par cdnjs (licence standard
  GreenSock, gratuite pour cet usage). Si le CDN ne répond pas,
  `landing.js` bascule automatiquement sur un écouteur de scroll natif :
  la page reste identique.
