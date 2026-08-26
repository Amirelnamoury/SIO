// Scenario 11 (cahier des charges V5, section 5) :
// la numerotation des devis/factures ne doit jamais s'appuyer sur un simple
// count()+1 - deux creations concurrentes liraient le meme compte et
// produiraient le meme numero, un vrai probleme reglementaire pour des
// factures. Cree N devis et N factures en parallele et verifie que tous
// les numeros generes sont uniques (regression du bug corrige dans
// app/numerotation.py).
import { api, assert, creerArtisanTest, logEtape } from "./helpers.mjs";

const N = 15;

export default async function run() {
  const { token } = await creerArtisanTest("scenario11");
  const client = await api.post("/clients", { nom: "Client Numerotation" }, token);

  const devisPromises = Array.from({ length: N }, (_, i) =>
    api.post("/devis", {
      client_id: client.id, titre: `Devis concurrent ${i}`, taux_tva: 20,
      lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
    }, token)
  );
  const devisCrees = await Promise.all(devisPromises);
  const numerosDevis = devisCrees.map((d) => d.numero);
  assert(new Set(numerosDevis).size === N, `les ${N} devis crees en parallele doivent avoir des numeros tous distincts (recu : ${numerosDevis.join(", ")})`);
  logEtape(`${N} devis crees en parallele : tous les numeros sont uniques (${numerosDevis[0]}...${numerosDevis[numerosDevis.length - 1]})`);

  const facturePromises = Array.from({ length: N }, (_, i) =>
    api.post("/factures", {
      client_id: client.id, titre: `Facture concurrente ${i}`, taux_tva: 20,
      lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
    }, token)
  );
  const facturesCreees = await Promise.all(facturePromises);
  const numerosFactures = facturesCreees.map((f) => f.numero);
  assert(new Set(numerosFactures).size === N, `les ${N} factures creees en parallele doivent avoir des numeros tous distincts (recu : ${numerosFactures.join(", ")})`);
  logEtape(`${N} factures creees en parallele : tous les numeros sont uniques (${numerosFactures[0]}...${numerosFactures[numerosFactures.length - 1]})`);

  // La numerotation est isolee par artisan : un deuxieme artisan doit
  // reprendre a 0001, pas continuer la sequence du premier.
  const { token: token2 } = await creerArtisanTest("scenario11b");
  const client2 = await api.post("/clients", { nom: "Client Autre Artisan" }, token2);
  const devis2 = await api.post("/devis", {
    client_id: client2.id, titre: "Premier devis autre artisan", taux_tva: 20,
    lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 10 }],
  }, token2);
  assert(devis2.numero.endsWith("-0001"), `la numerotation doit etre isolee par artisan (recu : ${devis2.numero})`);
  logEtape("numerotation isolee par artisan verifiee (un nouvel artisan repart a 0001)");
}
