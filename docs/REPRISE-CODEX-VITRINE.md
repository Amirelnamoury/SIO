# Reprise du travail — page vitrine Suite Artisan

Ce fichier est la passation. Il est écrit pour être collé tel quel à un
autre agent.

---

## Contexte

Dépôt `https://github.com/Amirelnamoury/SIO`, branche
`claude/suite-artisan-site-devis-cbyymn`, dernier commit poussé `3d65540`.

Le fichier concerné est la **page publique** : `frontend/landing.html` et
ses trois fichiers compagnons. Elle présente Suite Artisan, un logiciel de
gestion pour les artisans du bâtiment, à travers la **visite d'une villa**
— huit photographies traversées au défilement, en WebGL.

Le travail vient de passer sa sixième révision, faite à partir d'un
enregistrement vidéo commenté par l'utilisateur. La phase est **terminée
et vérifiée**, sauf trois points listés plus bas.

---

## Contraintes permanentes, à ne jamais enfreindre

- **Ne merge aucune autre branche. Ne force-push jamais. Ne réécris pas
  l'historique. Ne reset pas brutalement le travail existant.**
- Ne modifie ni les contrats d'API, ni les calculs, ni les abonnements,
  ni l'authentification sous couvert de présentation.
- Les prix et les prestations ne sont **jamais écrits en dur** dans la
  page : ils sont lus depuis `frontend/pricing.js`.
- **N'invente aucune statistique ni aucune promesse commerciale.** Seuls
  des faits vérifiables dans le produit peuvent être affichés. Les trois
  qui sont utilisés aujourd'hui : la conversion devis → facture en un
  clic, les relances automatiques à J+3 / J+7 / J+15, et le plan gratuit
  à 0 €.
- Aucune étape de compilation : pas de `package.json`, pas de `npm`, pas
  de bundler. Des scripts classiques et deux modules ES, servis tels
  quels. Three.js r160 est **vendorisé** dans
  `frontend/vendor/three.module.min.js` — jamais un CDN tiers.

---

## Les quatre fichiers

| Fichier | Rôle |
|---|---|
| `frontend/landing-visite.js` | Le moteur. La table des huit scènes, les shaders, le rendu. |
| `frontend/landing-piste.js` | Le branchement au défilement : la timeline, les textes, les trois modes, la sortie. |
| `frontend/landing.html` | La structure : huit `.lc-vue`, huit `.lc-spacer` + `#lc-sortie`, le contenu d'après-visite. |
| `frontend/landing.css` | Toute la présentation. |
| `frontend/outils/contraste-visite.js` | La sonde de contraste. Chargée à la main, jamais par la page. |

Chaque fichier porte en tête un commentaire qui explique **pourquoi** il
est fait ainsi. Lis-les avant de modifier quoi que ce soit : plusieurs
décisions qui paraissent arbitraires sont la trace d'un défaut mesuré.

---

## Ce qui vient d'être fait, et le principe à ne pas casser

Le défaut principal signalé était : *« l'image avance puis revient à sa
position initiale avant de disparaître »*.

Ce n'était pas un réglage d'amplitude. Une seule `PerspectiveCamera`
servait les **deux** images du fondu, et chaque scène déclarait ses
propres valeurs de départ et d'arrivée : à chaque frontière, la caméra
sautait de la valeur finale de A à la valeur initiale de B — et comme les
deux textures sont visibles pendant le fondu, ce saut se lisait sur les
deux à la fois.

**La caméra a été supprimée.** Il y a maintenant un quad plein écran, une
projection orthographique, et tout le cadrage se fait **dans le fragment
shader, texture par texture** : chacune porte son cadrage `cover`, son
point focal et son mouvement propre. Il n'existe plus une seule valeur
partagée entre deux scènes, donc plus rien à réinitialiser.

> **La règle à préserver : aucun état de cadrage ne doit être partagé
> entre deux scènes.** Si tu réintroduis une caméra, une variable globale
> de zoom ou un `transform` posé sur un conteneur commun, le défaut
> revient immédiatement et il ne se verra qu'à la vidéo.

Deux conséquences documentées dans le code, à ne pas « corriger » :

1. **La translation est exprimée en fraction de la marge disponible**
   (`px`, `py` entre −1 et 1), pas en pixels. À cadrage `cover`, un écran
   16:9 ne laisse presque aucune marge horizontale sur une photo 16:9 :
   la même valeur produit donc un travelling large sur téléphone et une
   poussée douce sur écran large, sans configuration séparée, et aucun
   bord noir ne peut apparaître.
2. **L'échelle ne dépasse jamais 1,035.** Le zoom n'est plus l'animation.

---

## Ce qui reste à faire

### 1. Le test visuel au défilement réel — LE POINT PRINCIPAL

Le brief le demande explicitement : faire défiler **lentement,
normalement, vite, vers le bas puis vers le haut**, et vérifier à l'œil
qu'aucune image ne recule, ne saute ni ne clignote.

**Je n'ai pas pu le faire.** L'outil de navigation dont je disposais garde
la page dans l'état `hidden` : `requestAnimationFrame` ne tourne jamais,
les événements de défilement ne se déclenchent pas, `innerHeight` vaut 0
et les captures d'écran reviennent vides. Toute ma vérification est donc
**par la mesure**, pas par l'observation.

Ce que la mesure établit déjà (ne le refais pas, sauf si tu changes la
table des scènes) :

```bash
node docs/scripts/continuite.mjs
```

Ce script rejoue la timeline complète hors navigateur et vérifie que les
32 courbes (échelle, translation x et y, rotation × 8 plans) sont
monotones et qu'aucune ne revient vers sa valeur de départ, pré-roll
compris. *(Si ce fichier n'existe pas dans le dépôt, il est à recréer :
il vivait dans un répertoire temporaire. Son contenu est décrit au
paragraphe « Le script de continuité » ci-dessous.)*

**Ce qu'il te reste à faire, dans un vrai navigateur visible :**
ouvrir `frontend/landing.html`, défiler aux quatre vitesses dans les deux
sens, et confirmer. Si tu as un outil qui enregistre, produis une courte
vidéo et compare-la à l'enregistrement d'origine.

Aides de recette disponibles :

- `landing.html?debug` expose `window.__visite` :
  - `__visite.aller(i, p)` pose la visite au plan `i`, progression `p`
  - `__visite.allerSortie(f)` pose le fondu de sortie à `f` (0 → 1)
  - `__visite.etat()` renvoie l'index réellement rendu (`indexA`), les
    transformations en cours, les textures en mémoire, la course totale
  - `preserveDrawingBuffer` n'est activé que sous `?debug` : sans lui, on
    ne peut pas relire les pixels du canevas
- `landing.html?reduit=1` force le mode sans mouvement

⚠️ **`etat().indexA` n'est pas décoratif.** Les textures se chargent de
façon asynchrone : si tu mesures juste après un `aller()`, tu mesures
souvent la photographie **précédente**. Vérifie toujours que `indexA`
vaut bien le plan que tu crois observer. Cette sonde m'a menti trois fois
là-dessus.

### 2. La performance

Non mesurée. À faire : images par seconde pendant le défilement, mémoire
GPU, coût du premier rendu. Le moteur plafonne déjà le `devicePixelRatio`
(2 sur ordinateur, 1,6 sur petit écran, 1,3 si la machine annonce quatre
cœurs ou moins) et ne garde que quatre textures en mémoire.

### 3. Le contenu d'après-visite, à l'œil

Les mesures de contraste et de débordement passent, mais je n'ai pas
**regardé** la fin de page : proposition de valeur + 3 bénéfices, tarifs,
Site Vitrine, appel à l'action, pied de page. À vérifier aux deux
largeurs (1366 et 375).

---

## Points de décision à signaler à l'utilisateur

J'ai **retiré la FAQ et la section Métiers** pour respecter la demande de
raccourcir le contenu d'après-visite. Les métiers sont désormais nommés
dans une phrase du paragraphe d'ouverture, et l'ancre `#metiers` est
conservée pour ne casser aucun lien.

**J'ai en revanche gardé les Tarifs et le Site Vitrine**, alors que le
brief ne listait que « proposition de valeur, 3 bénéfices, CTA, footer » :
ce sont les seules informations commerciales réelles que la page publie,
elles sont injectées depuis `pricing.js`, et les supprimer aurait dépassé
une passe de présentation. **C'est un écart assumé au brief, à confirmer
avec l'utilisateur.** S'il veut la FAQ de retour, elle est dans
l'historique git (`git show da8c118:frontend/landing.html`).

---

## Résultats de vérification déjà acquis

| Contrôle | Résultat |
|---|---|
| Continuité du mouvement | 32 courbes monotones, aucun retour |
| Échelle maximale | 1,035 (1,0353 transitoire pendant un fondu) |
| Longueur totale | 815 vh sur ordinateur, 538 sur téléphone |
| Longueur par plan | 85 à 110 svh |
| Cadrage `cover` | Aucun liseré : pire suite contiguë de 9 px sur un bord de 768 |
| Contraste, 1366×768 | 24 relevés, minimum 4,64 — zéro échec |
| Contraste, 375×812 | 24 relevés, minimum 9,65 — zéro échec |
| Débordement horizontal | Aucun, aux deux largeurs |
| Sortie vers le papier | Arrive exactement sur `#F1EADF`, écart (0, 0, 0) |
| Mode sans mouvement | 8 photographies posées, halo neutralisé, repères retirés |

---

## Le script de continuité

À recréer si absent. Il importe `SCENES` depuis
`frontend/landing-visite.js`, réimplémente `transformer()` à l'identique
(easing `t*t*(3-2t)*0.35 + t*0.65`, pré-roll de 0,22, échelle bornée à
1,0 par le bas) et vérifie, pour chaque plan et chaque axe :

- que la courbe échantillonnée de `p = −0,22` à `p = 1` est **monotone** ;
- que la valeur finale est **plus éloignée** du départ que ne l'est le
  milieu — c'est le test du « retour à la position initiale » ;
- que la scène entrante **bouge déjà** pendant le fondu ;
- que l'échelle au pré-roll reste ≥ 1,0 (sinon : bords noirs).

Plus les contraintes du brief : échelle ≤ 1,035, poids entre 0,70 et
1,10, total entre 7 et 9 hauteurs d'écran, alternance stricte des côtés,
exactement deux moments chiffrés espacés d'au moins trois plans.

---

## Trois pièges où je suis tombé — ne refais pas le chemin

1. **Un accent grave dans un commentaire GLSL.** Les shaders vivent dans
   des littéraux de gabarit JavaScript. Une paire d'accents graves autour
   d'un nom de variable dans un commentaire referme la chaîne puis la
   rouvre : le navigateur signale alors une erreur de syntaxe sur ce nom,
   sans rapport visible avec sa cause. **Aucun accent grave dans les
   commentaires des shaders.**

2. **La sonde de contraste jetait l'alpha de la couleur du texte.** Elle
   jugeait une encre `rgba(…, .70)` comme si elle était pleine. Le
   symptôme qui l'a trahie : on change l'opacité du texte, et la mesure ne
   bouge pas d'un centième. *Une valeur qui refuse de changer quand sa
   cause change est un signe plus fiable qu'une valeur qui paraît fausse.*
   C'est corrigé, mais garde le réflexe.

3. **`THREE.Color` linéarise.** Le shader travaille en sRGB brut :
   il échantillonne des textures et les écrit telles quelles, sans aucun
   éclairage. Un `new THREE.Color("#F1EADF")` passé en uniforme était
   converti dans l'espace linéaire, et le fondu de sortie s'arrêtait à
   (224, 210, 188) au lieu de (241, 234, 223) — la jointure avec la page
   redevenait visible. La couleur est maintenant passée en `Vector3` de
   composantes sRGB. **Ne remets pas de `THREE.Color` dans ce shader.**

Plus généralement : sur cette page, **une sonde fausse ne mesure rien —
elle déplace le défaut dans l'outil, où il est bien plus difficile à
voir.** Quand un chiffre te surprend, soupçonne d'abord l'instrument.

---

## Servir la page

Aucun serveur n'est nécessaire pour la logique, mais les modules ES
exigent une origine HTTP :

```bash
python -m http.server 8123 --directory frontend
```

Puis `http://localhost:8123/landing.html`. Une configuration existe déjà
dans `.claude/launch.json` sous le nom `vitrine`.
