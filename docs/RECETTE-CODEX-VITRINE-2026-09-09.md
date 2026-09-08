# Recette visuelle de la vitrine — 9 septembre 2026

Branche : `claude/suite-artisan-site-devis-cbyymn`. Départ vérifié :
`3fff31ec9982bb5f46e0e1fa7abbb9249a7bdbe5`. La passation et les commentaires
des quatre fichiers ont été lus avant modification.

## Méthode et portée

Chrome installé sur Windows, lancé **avec fenêtre visible** par Playwright
déjà disponible dans l'environnement. `document.visibilityState` vaut
`visible`. Page servie par `python -m http.server 8123 --directory frontend`.
Aucune compilation, aucune installation npm, aucun CDN Three.js.

La visite a réellement défilé dans le navigateur : six passages par format,
descente et remontée en 35 s, 12 s puis 3,5 s pour la course complète.
Les déplacements réguliers utilisent le scroll du navigateur piloté par
requestAnimationFrame ; le cas de chargement a aussi été reproduit par
événements de molette, avec arrêt. Les enregistrements WebM du rendu ont été
inspectés par séquences d'images successives. Ce contrôle temporel complète
les captures de sections et les sondes ; il ne prétend pas détecter chaque
défaut d'une seule frame à 60 Hz.

Formats : viewport 1366 × 768, DPR 1 ; viewport mobile 375 × 812, DPR annoncé
3, tactile émulé. Le deuxième utilise le GPU du PC : **ce n'est pas une
mesure sur un téléphone physique**.

Un ancien serveur Python répondait également sur 8123 avec une autre copie
des fichiers. Il a été arrêté. Les fichiers HTTP corrigés ont ensuite été
vérifiés et la recette après correction a été refaite. Les premiers essais
nommés `after-*` sont invalides comme preuve des corrections et ne sont pas
utilisés dans les conclusions.

## Défauts observés et corrections

| Défaut réellement vu | Scène / moment / direction | Cause et correction |
|---|---|---|
| Texte du bureau sur la façade après un grand scroll puis arrêt ; 1 px supplémentaire fait enfin apparaître le bureau | Façade → bureau, molette +3100 px sur desktop, attente de 1,2 s | Les callbacks liaient des textures sans repeindre. Une composition complète est maintenant conservée pendant le chargement puis repeinte à la position actuelle. |
| Réapparition brève de la photographie suivante au raccord en remontant | Notamment galerie → bureau et salon → hall ; visible dans l'enregistrement initial | Même en cache, la liaison passait par une promesse après le rendu. Elle se fait désormais synchroniquement avant les cadrages. |
| La sonde annonce le bureau alors que le framebuffer montre encore la façade | Même arrêt sur le bureau | Les index de diagnostic sont maintenant actualisés après la peinture, pas dans le callback réseau. |
| Cinq photographies restent en mémoire après l'arrêt | Saut vers le bureau : `[0,1,4,5,6]` avant correction | Nettoyage après réception et liaison ; annulation du préchargement différé périmé ; priorité aux images peintes et demandées, limite de quatre. |
| Le panneau beige coupe la terrasse par le bas avant son fondu | Fin de descente et début de remontée, desktop et mobile | Le fond de la conclusion est transparent en WebGL et son opacité suit le même fondu que le shader. La correction finale évite d'ajouter un écran vide. |
| Le contenu d'après-visite apparaît brièvement pendant l'initialisation | Début des enregistrements, avant que le module pose les hauteurs | La conclusion est masquée avant l'affectation de `data-mode`, pour empêcher ce flash. Le mode sans JavaScript garde son contenu. |
| Ancien texte encore visible sur la pièce suivante à grande vitesse | Notamment suite → galerie en remontée rapide | La cascade atteignait 0,78 s. Les éléments entrent ensemble en 0,18 s, avec une translation réduite à 8 px. Les passages normaux et rapides ont été repris après ce réglage. |
| Nom et liens du menu trop sombres sur la façade ; invitation à défiler et repères peu lisibles | Accueil, puis visite | Fond papier translucide du menu présent dès l'ouverture ; encres claires pour l'invitation et les repères. Ces derniers disparaissent à la sortie et ne restent plus sur le footer. |
| Bouton du menu affleurant le bord droit | Largeur 375 px | Espacement et tailles du menu adaptés, en conservant le nom, le logo et le CTA. |
| Mots collés dans les titres : « métier.Enfin », « gratuitement.Montez », « professionnel,relié » | Contenu mobile ; même mécanisme dans les titres de la visite | Espaces conservés autour des sauts de ligne masqués. Aucun texte commercial remplacé. |
| Bénéfices collés au paragraphe, mentions collées aux CTA, derniers items collés aux boutons des tarifs | Contenu après visite, deux formats | Spécificité des marges corrigée face au reset de `p` / `ul`. La grille mobile des bénéfices reste sur une colonne. |

## Descente et remontée après correction

Les huit plans restent présents : façade, hall, salon, cuisine, bureau,
galerie, suite et terrasse. Les passages lents et normaux montrent le
chevauchement des photos, sans retour observé au cadrage initial, sans bord
noir ni zoom excessif. Le léger recul prévu de la suite et de la terrasse
reste conservé. La sortie blanchit vers le papier en plein écran ; en
remontant, elle se recompose dans le sens inverse avant la visite.

Contrôle final de couleur à sortie = 1 : pixel du canevas
`(241, 234, 223, 255)`, fond CSS `rgb(241, 234, 223)`, soit exactement
`#F1EADF`. Les cinq fichiers de page servis par HTTP ont été comparés à
ceux du disque : ils sont identiques.

Après un saut vers une photo non chargée, l'ancienne composition reste
cohérente jusqu'à la disponibilité des textures. Le moteur rejoint ensuite
la position demandée. Un saut qui traverse plusieurs scènes peut toujours
sauter des étapes : aucune seconde animation de rattrapage n'a été ajoutée.

## Contenu à 1366 px et à 375 px

Proposition de valeur, trois bénéfices, quatre tarifs, Site Vitrine, CTA et
footer ont tous été parcourus et inspectés. Fond papier conservé. Après
correction, pas de débordement horizontal ni de bloc vide inexpliqué dans
ce contenu. Les espacements séparent les blocs sans ajouter de section.

À 375 px, les tarifs occupent environ 2214 px, soit 2,7 écrans : les quatre
offres sont empilées et toutes leurs fonctionnalités restent lisibles. Le
Site Vitrine occupe environ 1135 px. Cette longueur vient du contenu
conservé, pas de spacers résiduels. FAQ et grille Métiers n'ont pas été
réintroduites. Tarifs et Site Vitrine n'ont pas été supprimés.

La correction finale de sortie n'ajoute pas de viewport à la hauteur
physique. **La course des photos et du fondu reste identique**, 6260 px
(8,15 écrans) sur desktop et 4368 px (5,38 écrans) dans le viewport mobile.

## Mouvement réduit

`?reduit=1` vérifié aux deux formats avec WebGL explicitement indisponible.
Les huit images sont chargées et lisibles. Canevas, spacers, ombre et repères
sont retirés. Aucun halo sombre incorrect observé ; aucune animation active
au contrôle. L'animation initiale du logo est aussi neutralisée dans ce mode.
La préférence système `prefers-reduced-motion: reduce`, sans paramètre URL,
sélectionne également le mode fixe et ses huit photographies.

## Performances

Relevé sans enregistrement, Chrome 152 / ANGLE Direct3D11, Intel UHD
Graphics 620, 8 cœurs et 8 Go annoncés au navigateur. Trois vitesses dans
les deux sens, 24 s / 12 s / 3,5 s par parcours. Ce sont les intervalles
requestAnimationFrame du navigateur, pas un compteur de présentation GPU.

| Parcours | Desktop FPS | Frame maximale | Mobile émulé FPS | Frame maximale |
|---|---:|---:|---:|---:|
| Lent descendant | 57,6 | 216,6 ms | 59,0 | 116,8 ms |
| Lent remontant | 58,5 | 151,1 ms | 59,6 | 66,6 ms |
| Normal descendant | 57,2 | 133,4 ms | 59,3 | 66,6 ms |
| Normal remontant | 56,8 | 133,1 ms | 59,3 | 66,8 ms |
| Rapide descendant | 52,3 | 116,7 ms | 56,9 | 66,7 ms |
| Rapide remontant | 50,9 | 166,8 ms | 54,6 | 99,8 ms |

Les intervalles au 95e percentile restent entre 16,9 et 18,4 ms, mais les
maxima montrent de vraies pauses ponctuelles. Le poste n'est pas un banc
isolé du système ; une extraction vidéo a aussi chevauché le début du
relevé desktop. Les passages normaux et rapides suivants restent eux aussi
sous 60 FPS. Une fluidité parfaite n'est donc **pas validée**.

Une instrumentation temporaire du rendu, injectée dans la réponse locale
et absente du produit, mesure le temps CPU de `renderer.render` :

| Mesure | Desktop | Mobile émulé |
|---|---:|---:|
| Premier rendu, encore sans photo | 112,4 ms | 39,1 ms |
| Premier rendu photographique | 207,3 ms | 89,1 ms |
| Fin de ce premier rendu depuis navigation | ~1,69 s | ~0,97 s |
| Rendu CPU au 95e percentile | 0,7 ms | 0,8 ms |
| Rendu pendant les fondus, moyenne | 1,01 ms | 0,66 ms |
| Rendu pendant les fondus, maximum | 161,2 ms | 62,1 ms |
| Heap JS observé, instrumentation comprise | ~5,0 Mio | ~4,7 Mio |

Les valeurs de démarrage incluent les conditions locales et le dispositif
d'instrumentation ; elles ne sont pas un LCP de production. Les appels
ordinaires sont courts, alors que les premières peintures de textures
concentrent les coûts élevés. Cela oriente vers leur préparation/transfert
GPU, sans constituer une mesure séparée du temps GPU. Un essai temporaire
avec `HTMLImageElement.decode()` anticipé n'a apporté aucun gain : il n'est
pas intégré au code.

Cache observé : quatre photographies au maximum après correction, trois
après le saut vers le bureau stabilisé. `renderer.info.memory.textures`
atteint quatre objets GPU, texture de secours comprise ; ce compteur ne
mesure pas des octets. Quatre photos décodées en RGBA représenteraient
environ 31,4 Mio en 1920 × 1071 et 10,3 Mio en 1100 × 614, hors autres
allocations. La mémoire GPU totale n'est pas exposée par cette sonde.

Canvas mesuré : 1351 × 768 pixels sur desktop avec sa scrollbar, 600 × 1299
sur mobile émulé. Le DPR mobile effectif reste 1,6 malgré le DPR annoncé 3.
Les plafonds et la fenêtre de textures sont conservés. Réduire arbitrairement
les images desktop à 1100 px aurait réintroduit le flou signalé dans la
passation ; ce changement n'a pas été fait. L'optimisation de ces pauses
reste un point ouvert, à valider aussi sur un téléphone physique.

## Fichiers et vérifications

- `frontend/landing-visite.js` : réception, liaison, peinture et cache des textures.
- `frontend/landing-piste.js` : textes et repères suivent la dernière composition réellement peinte ; notification de chargement.
- `frontend/landing.css` : sortie, menu, repères, animation des textes, espacements et mode fixe.
- `frontend/landing.html` : espaces des titres et versions des ressources modifiées.
- `frontend/landing.js` : espace du titre Site Vitrine et extinction des repères après visite.
- `docs/scripts/recette-textures.mjs` : régressions du chargement sans dépendance externe.
- Ce compte rendu.

`node --check` passe sur les trois scripts JS modifiés. Le script
`node docs/scripts/recette-textures.mjs` passe : ouverture sans geste,
liaison synchrone en cache, arrêt après saut, attente des deux images d'un
fondu, retours rapides, réponses périmées et borne du cache. Il exécute les
modules réels avec DOM, rAF, réseau et renderer contrôlés ; il complète la
recette visuelle, sans la remplacer.

La table `SCENES` et les deux shaders sont identiques au commit de départ,
après normalisation des fins de ligne. `continuite.mjs` n'a donc pas été
relancé, conformément à la demande. Caméra orthographique, cadrages et
focaux par texture, plafond d'échelle, DPR et couleur sRGB en `Vector3`
sont conservés. API, calculs, abonnements, authentification et `pricing.js`
n'ont pas changé. Aucun merge, reset ou réécriture d'historique.
Commit et push sur la branche actuelle demandés explicitement par
l'utilisateur en fin de session.

## Limites de cette recette

Les tests mobiles sont une émulation Chrome, sans iPhone / Android physique
ni variations réelles de barre d'adresse. Pas de simulation de réseau mobile
lent. Le repli CSS animé sans WebGL n'a pas reçu la même recette complète
que WebGL et le mode fixe ; ses règles de mouvement n'ont pas été refondues.
L'inspection temporelle des vidéos ne constitue pas une garantie d'absence
de défaut d'une seule frame. Les limites de performance mesurées ci-dessus
doivent être gardées dans toute conclusion de fluidité.

Les enregistrements de visite sont antérieurs au dernier ajustement de
conclusion transparente, réalisé pour supprimer le vide de la première
correction. Les tests de chargement ont été relancés après cet ajustement.
Sa recette complète dans les deux sens reste à reprendre après le push
prioritaire demandé par l'utilisateur.
