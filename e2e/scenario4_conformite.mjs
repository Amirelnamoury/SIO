// Scenario 4 (cahier des charges V3, section 39) :
// document (conformite) -> expiration -> notification -> mise a jour
import { api, assert, assertEqual, creerArtisanTest, activerAbonnement, logEtape } from "./helpers.mjs";

function dansNJours(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default async function run() {
  const { token, email } = await creerArtisanTest("scenario4");
  await activerAbonnement(email);

  // Element deja expire hier.
  const item = await api.post("/conformite", {
    type: "assurance_decennale", libelle: "Assurance decennale E2E", date_expiration: dansNJours(-1),
  }, token);
  logEtape("element de conformite cree, deja expire");

  const alertes = await api.get("/conformite/alertes", token);
  assert(alertes.some((a) => a.id === item.id), "un element expire doit apparaitre dans les alertes");
  logEtape("alerte de conformite detectee");

  const notifications = await api.get("/notifications", token);
  assert(notifications.some((n) => n.type === "conformite" && n.id === item.id), "l'element expire doit apparaitre dans le centre de notifications");
  logEtape("notification de conformite presente dans le centre de notifications");

  // Mise a jour reelle (renouvellement) : la nouvelle date repousse l'element hors du seuil d'alerte.
  await api.patch(`/conformite/${item.id}`, { date_expiration: dansNJours(365) }, token);
  const alertesApresRenouvellement = await api.get("/conformite/alertes", token);
  assert(!alertesApresRenouvellement.some((a) => a.id === item.id), "apres renouvellement, l'element ne doit plus etre en alerte");
  const notificationsApresRenouvellement = await api.get("/notifications", token);
  assert(!notificationsApresRenouvellement.some((n) => n.type === "conformite" && n.id === item.id), "la notification doit disparaitre apres mise a jour de la date");
  logEtape("mise a jour (renouvellement) verifiee : alerte et notification disparaissent");
}
