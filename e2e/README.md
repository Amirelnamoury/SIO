# Tests de bout en bout (E2E)

Ces scripts implementent les 5 scenarios de bout en bout du cahier des
charges V3 (section 39). Ils appellent l'API HTTP reelle (pas de mocks) :
chaque assertion verifie un effet reellement produit en base (statuts,
montants, emails journalises, permissions...).

## Prerequis

- Le backend doit tourner sur `http://localhost:8000` (ou definissez
  `API_BASE` pour une autre URL).
- Node.js 18+ (utilise `fetch` natif).
- Le script `manage_subscription.py` doit etre executable depuis
  `backend/` avec l'environnement virtuel active (utilise pour activer
  l'abonnement des artisans de test sans passer par Stripe).

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8000 &
cd ../e2e && node run_all.mjs
```

Chaque scenario cree ses propres artisans de test avec des emails uniques
(horodates) : ils peuvent tourner plusieurs fois de suite sans collision,
et n'interferent pas entre eux (isolation multi-tenant garantie par
l'application elle-meme, pas par le test).

## Scenarios

1. **scenario1_devis_a_avis.mjs** - site vitrine -> prospect -> devis -> envoi
   -> consultation -> relance -> signature -> chantier -> facture -> paiement
   -> avis.
2. **scenario2_preparation_cloture.mjs** - devis signe -> "Tout preparer" ->
   chantier -> progression (taches cochees) -> depenses -> marge -> cloture
   -> facture finale (verifie explicitement l'absence de double facturation
   entre l'acompte et le solde).
3. **scenario3_automation_facture.mjs** - facture impayee -> vrai cycle
   d'automatisation (`app.scheduler.run_automation_cycle`, celui utilise en
   production par le planificateur) -> email journalise honnetement ->
   notification -> paiement -> arret verifie de l'automatisation.
4. **scenario4_conformite.mjs** - element de conformite expire ->
   alerte + notification -> renouvellement -> disparition de l'alerte.
5. **scenario5_equipe_permissions.mjs** - invitation d'un salarie ->
   donnees partagees au niveau de l'entreprise -> permissions verifiees
   (un salarie ne peut pas gerer l'equipe, un administrateur le peut).
6. **scenario6_heures_main_oeuvre.mjs** - chantier -> heures saisies pour
   plusieurs intervenants (avec et sans taux horaire) -> cout de main
   d'oeuvre reel -> marge estimee mise a jour -> isolation multi-tenant ->
   suppression (le total et le cout se recalculent, jamais un flag fige).

## Limites connues

- Ne couvrent pas l'UI (formulaires, rendu) : ce sont des tests de logique
  metier au niveau de l'API. Le rendu visuel a ete verifie manuellement au
  fil du developpement (captures d'ecran Playwright, non committees).
- N'incluent pas de test de charge/performance.
- Le scenario 3 s'adapte a l'environnement (avec ou sans fournisseur email
  configure) plutot que de supposer une configuration particuliere.
