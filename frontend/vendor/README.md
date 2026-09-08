# Dépendances tierces servies depuis le dépôt

## `three.module.min.js`

| | |
|---|---|
| Bibliothèque | [Three.js](https://threejs.org) |
| Version | **r160** (`REVISION = "160"`) |
| Licence | MIT — *Copyright 2010-2023 Three.js Authors* |
| Origine | `https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js` |
| Taille | 670 681 octets |
| SHA-256 | `3e690ac7d180b0aadf0891bea39eec643e29e2d3e75c99b18689518665f69ba6` |

### Pourquoi le fichier est ici et non sur un CDN

Le projet n'a ni `package.json` ni étape de construction : la seule
manière d'utiliser une bibliothèque est de la servir. Deux raisons de la
servir depuis le dépôt plutôt que depuis un CDN tiers :

- **la page ne dépend de personne d'autre.** Un CDN indisponible, bloqué
  par un réseau d'entreprise ou par un bloqueur, et la visite ne démarre
  pas. Ici elle démarre ou elle bascule sur son repli, mais elle ne
  dépend pas d'un tiers ;
- **rien ne change sous les pieds.** Un fichier figé, avec son empreinte
  notée ci-dessus, ne peut pas être remplacé sans qu'on le sache.

### Qui l'utilise

`frontend/landing-visite.js` seulement, et ce module n'est chargé que par
la page publique. **L'application n'en dépend pas** : `index.html` ne le
référence nulle part.

### Pour le mettre à jour

Télécharger la nouvelle version, remplacer le fichier, mettre à jour la
version, la taille et l'empreinte de ce tableau, puis vérifier la visite
sur `landing.html?debug=1` — le point d'observation `window.__visite`
donne la position de la caméra et les textures en mémoire.
