// Lance les 5 scenarios de bout en bout du cahier des charges V3 (section 39)
// contre un backend reellement demarre. Voir README.md pour les instructions.
import scenario1 from "./scenario1_devis_a_avis.mjs";
import scenario2 from "./scenario2_preparation_cloture.mjs";
import scenario3 from "./scenario3_automation_facture.mjs";
import scenario4 from "./scenario4_conformite.mjs";
import scenario5 from "./scenario5_equipe_permissions.mjs";
import scenario6 from "./scenario6_heures_main_oeuvre.mjs";
import scenario7 from "./scenario7_archivage.mjs";
import scenario8 from "./scenario8_stripe.mjs";
import scenario9 from "./scenario9_securite.mjs";

const scenarios = [
  ["1. Devis -> ... -> avis", scenario1],
  ["2. Preparation chantier -> cloture (sans double facturation)", scenario2],
  ["3. Automatisation facture impayee", scenario3],
  ["4. Conformite : expiration -> notification -> renouvellement", scenario4],
  ["5. Equipe : invitation -> attribution -> permissions", scenario5],
  ["6. Heures de main d'oeuvre -> cout reel -> rentabilite", scenario6],
  ["7. Archivage (client/devis/facture/chantier) sans perte de donnees", scenario7],
  ["8. Stripe : Free -> paiement -> Pro -> webhook -> echec -> annulation", scenario8],
  ["9. Securite : mot de passe, isolation multi-tenant, jetons publics", scenario9],
];

let echecs = 0;
for (const [nom, fn] of scenarios) {
  console.log(`\n=== ${nom} ===`);
  try {
    await fn();
    console.log(`OK : ${nom}`);
  } catch (err) {
    echecs += 1;
    console.error(`ECHEC : ${nom}`);
    console.error(err.message);
  }
}

console.log(`\n${scenarios.length - echecs}/${scenarios.length} scenarios reussis.`);
process.exit(echecs > 0 ? 1 : 0);
