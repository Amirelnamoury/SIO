// Scenario 8 (cahier des charges V4, section 27 + section 39 "Stripe") :
// Free -> upgrade -> paiement -> Pro -> webhook -> echec paiement -> etat
// coherent -> resolution -> annulation. Signe reellement des evenements
// webhook avec HMAC-SHA256 (meme schema que Stripe) pour verifier la
// verification de signature ET la logique metier de bout en bout, sans
// dependre d'un vrai compte Stripe (aucune cle secrete Stripe reelle
// n'est necessaire : le webhook ne fait jamais d'appel sortant vers
// l'API Stripe, seulement une verification de signature + ecriture DB).
//
// Necessite que le backend soit demarre avec STRIPE_WEBHOOK_SECRET fixe a
// la meme valeur que STRIPE_TEST_WEBHOOK_SECRET ci-dessous (voir README.md).
// Si ce n'est pas le cas (config par defaut sans Stripe), le scenario est
// saute proprement plutot que de faire echouer la suite - il ne peut pas
// deviner le secret configure sur un backend qu'il ne controle pas.
import crypto from "node:crypto";
import { api, API_BASE, assert, assertEqual, creerArtisanTest, logEtape } from "./helpers.mjs";

const STRIPE_TEST_WEBHOOK_SECRET = process.env.STRIPE_TEST_WEBHOOK_SECRET;

function signPayload(payload, secret) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const signedPayload = `${timestamp}.${payload}`;
  const signature = crypto.createHmac("sha256", secret).update(signedPayload).digest("hex");
  return `t=${timestamp},v1=${signature}`;
}

async function postWebhookEvent(event) {
  const payload = JSON.stringify(event);
  const sig = signPayload(payload, STRIPE_TEST_WEBHOOK_SECRET);
  const res = await fetch(`${API_BASE}/stripe/webhook`, {
    method: "POST", headers: { "Content-Type": "application/json", "Stripe-Signature": sig }, body: payload,
  });
  return res;
}

export default async function run() {
  if (!STRIPE_TEST_WEBHOOK_SECRET) {
    logEtape("SAUTE : STRIPE_TEST_WEBHOOK_SECRET non defini (backend demarre sans config Stripe de test) - voir README.md");
    return;
  }

  const { token } = await creerArtisanTest("scenario8");
  const me = await api.get("/auth/me", token);
  assertEqual(me.subscription_status, "inactive", "un nouvel artisan est en Free (inactive) par defaut");

  let refuse402 = false;
  try {
    await api.post("/chantiers", { client_id: 1, titre: "test" }, token);
  } catch (err) {
    refuse402 = err.message.includes("HTTP 402");
  }
  assert(refuse402, "les fonctionnalites premium doivent etre bloquees avant paiement (402)");
  logEtape("Free : acces premium bloque avant paiement");

  const customerId = `cus_e2e_${me.id}`;
  const checkoutEvent = {
    id: `evt_checkout_${me.id}`, type: "checkout.session.completed",
    data: { object: { metadata: { artisan_id: String(me.id), plan: "pro" }, subscription: `sub_e2e_${me.id}`, customer: customerId } },
  };
  const resCheckout = await postWebhookEvent(checkoutEvent);
  assertEqual(resCheckout.status, 200, "le webhook checkout.session.completed doit etre accepte (signature valide)");
  const meApresPaiement = await api.get("/auth/me", token);
  assertEqual(meApresPaiement.subscription_status, "active", "le paiement doit activer l'abonnement");
  assertEqual(meApresPaiement.plan, "pro", "le plan achete (metadata.plan du webhook) doit etre applique a l'artisan");
  logEtape("upgrade -> paiement -> Pro : abonnement active et plan correctement mappe via webhook");

  await postWebhookEvent(checkoutEvent);
  const meIdempotence = await api.get("/auth/me", token);
  assertEqual(meIdempotence.subscription_status, "active", "rejouer le meme evenement webhook ne doit rien casser (idempotence)");
  logEtape("idempotence verifiee : evenement rejoue sans effet de bord");

  const client = await api.post("/clients", { nom: "Client E2E Stripe" }, token);
  const chantier = await api.post("/chantiers", { client_id: client.id, titre: "Chantier apres upgrade" }, token);
  assert(!!chantier.id, "l'acces premium doit fonctionner reellement apres paiement");
  logEtape("acces premium reellement debloque (creation de chantier reussie)");

  // Fonctionnalite specifiquement reservee au plan Pro (pas juste "abonne") :
  // verifie que le plan achete via ce webhook debloque bien la bonne frontiere.
  const devis = await api.post("/devis", { client_id: client.id, titre: "Devis E2E Stripe", taux_tva: 20, lignes: [{ description: "x", quantite: 1, prix_unitaire_ht: 100 }] }, token);
  await api.patch(`/devis/${devis.id}`, { statut: "envoye" }, token);
  const devisRelance = await api.post(`/devis/${devis.id}/relancer`, undefined, token);
  assert(!!devisRelance.id, "le plan Pro achete doit reellement debloquer la relance manuelle de devis");
  logEtape("fonctionnalite specifique au plan Pro (relance devis) verifiee reellement debloquee");

  await postWebhookEvent({ id: `evt_fail_${me.id}`, type: "customer.subscription.updated", data: { object: { customer: customerId, status: "past_due" } } });
  const meEchec = await api.get("/auth/me", token);
  assertEqual(meEchec.subscription_status, "past_due", "un echec de paiement Stripe doit se refleter dans l'etat de l'artisan");
  let reBloque = false;
  try {
    await api.post("/chantiers", { client_id: client.id, titre: "test echec" }, token);
  } catch (err) {
    reBloque = err.message.includes("HTTP 402");
  }
  assert(reBloque, "echec de paiement -> etat coherent : l'acces premium doit etre re-bloque automatiquement");
  logEtape("echec de paiement : etat 'past_due' propage, acces re-bloque");

  await postWebhookEvent({ id: `evt_resolve_${me.id}`, type: "customer.subscription.updated", data: { object: { customer: customerId, status: "active" } } });
  const meResolu = await api.get("/auth/me", token);
  assertEqual(meResolu.subscription_status, "active", "la resolution du paiement doit restaurer l'acces");
  logEtape("paiement resolu : acces restaure");

  // V5 section 6 : un changement de plan doit se refleter meme quand il ne
  // vient pas de checkout.session.completed (ex: modifie directement sur
  // l'abonnement Stripe existant - c'est le webhook customer.subscription.updated
  // qui est desormais la source de verite pour le plan, pas seulement pour
  // le statut). Necessite STRIPE_PRICE_ID_BUSINESS pour verifier le mapping
  // price -> plan (peut etre une valeur factice, le webhook ne fait aucun
  // appel sortant vers Stripe).
  if (process.env.STRIPE_PRICE_ID_BUSINESS) {
    await postWebhookEvent({
      id: `evt_changement_plan_${me.id}`, type: "customer.subscription.updated",
      data: { object: { customer: customerId, status: "active", items: { data: [{ price: { id: process.env.STRIPE_PRICE_ID_BUSINESS } }] } } },
    });
    const meApresChangement = await api.get("/auth/me", token);
    assertEqual(meApresChangement.plan, "business", "le plan doit se resynchroniser depuis le price_id de l'evenement webhook, pas seulement a la souscription initiale");
    logEtape("changement de plan via webhook (hors checkout initial) : plan resynchronise depuis le price_id");
  } else {
    logEtape("SAUTE (partiel) : STRIPE_PRICE_ID_BUSINESS non defini, resynchronisation du plan via webhook non verifiee");
  }

  await postWebhookEvent({ id: `evt_cancel_${me.id}`, type: "customer.subscription.deleted", data: { object: { customer: customerId, status: "canceled" } } });
  const meAnnule = await api.get("/auth/me", token);
  assertEqual(meAnnule.subscription_status, "canceled", "l'annulation doit se refleter dans l'etat de l'artisan");
  let bloqueApresAnnulation = false;
  try {
    await api.post("/chantiers", { client_id: client.id, titre: "test annule" }, token);
  } catch (err) {
    bloqueApresAnnulation = err.message.includes("HTTP 402");
  }
  assert(bloqueApresAnnulation, "annulation -> acces bloque");
  logEtape("annulation : acces bloque");

  const resInvalide = await fetch(`${API_BASE}/stripe/webhook`, {
    method: "POST", headers: { "Content-Type": "application/json", "Stripe-Signature": "t=123,v1=signature_invalide" }, body: JSON.stringify({ fake: "event" }),
  });
  assertEqual(resInvalide.status, 400, "une signature webhook invalide doit toujours etre rejetee");
  logEtape("securite : signature webhook invalide rejetee (400)");
}
