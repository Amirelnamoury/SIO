## Graphify

Ce projet utilise un graphe de connaissances local dans `graphify-out/` pour réduire les lectures répétées du dépôt. Les fichiers générés restent ignorés par Git.

### Avant une question sur le code

- Si `graphify-out/graph.json` existe, commencer par `graphify query "<question>" --budget 1500`.
- Utiliser `graphify path "<A>" "<B>"` pour tracer une relation et `graphify explain "<concept>"` pour un élément précis.
- Lire directement les fichiers sources nécessaires pour confirmer les conclusions avant toute modification.
- Utiliser `GRAPH_REPORT.md` seulement pour une revue d'architecture large.

### Maintien du graphe

- Si le graphe est absent, exécuter `bash scripts/setup_codex_graphify.sh`.
- Après une modification de code, exécuter `graphify update .`.
- Ne jamais considérer le graphe comme une preuve suffisante lorsqu'il est ancien, incomplet ou en conflit avec le code.
- Ne jamais ajouter `graphify-out/` à un commit : le graphe doit rester reproductible et sans secret.

### Garde-fous

- L'installation et la génération du graphe ne doivent modifier aucun fichier métier.
- Une erreur Graphify ne doit jamais bloquer un correctif urgent : revenir à `rg` et à la lecture ciblée des sources.
- Aucun secret ou fichier d'environnement ne doit entrer dans le corpus.
