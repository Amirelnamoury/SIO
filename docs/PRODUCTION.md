# Suite Artisan — Production Readiness

Document court et operationnel. Pour l'audit complet ayant motive ces
changements, voir l'historique de commits de la branche
`claude/suite-artisan-site-devis-cbyymn`.

## Architecture cible

```
Frontend statique (frontend/*.html, api.js, app.js)
        |
        v
FastAPI (backend/app)
        |
        +--> PostgreSQL (production) / SQLite (developpement)
        |
        +--> Storage S3-compatible (production, ex: Cloudflare R2)
             / disque local (developpement)
```

- **Developpement** : SQLite (`sqlite:///./suite_artisan.db`) + filesystem local (`backend/uploads/`). Zero configuration.
- **Production** : PostgreSQL + stockage objet S3-compatible (Cloudflare R2 ou equivalent).

## Variables d'environnement

Voir `backend/.env.example` pour la liste complete avec commentaires. Resume (aucun secret reel ci-dessous) :

| Variable | Role | Defaut |
|---|---|---|
| `APP_ENV` | `development` ou `production` | `development` |
| `DATABASE_URL` | Connexion DB | SQLite local |
| `JWT_SECRET` | Signature des tokens | secret de dev (refuse en production) |
| `APP_BASE_URL` | URL publique du frontend (doit etre https:// en production) | `http://localhost:8080` |
| `CORS_ORIGINS` | Origines autorisees, separees par virgules | `*` |
| `STORAGE_BACKEND` | `local` ou `s3` | `local` |
| `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `S3_REGION` | Requis si `STORAGE_BACKEND=s3` | vides |
| `SCHEDULER_ENABLED` | Demarre le scheduler dans ce process | `true` |
| `UPLOADS_DIR`, `MAX_UPLOAD_MO` | Utilises si `STORAGE_BACKEND=local` | `uploads`, `15` |

En `APP_ENV=production` (ou toute `DATABASE_URL` non-sqlite avec le secret JWT par defaut), le demarrage **refuse** de continuer si :
- `JWT_SECRET` vaut encore la valeur de developpement ;
- `DATABASE_URL` pointe vers SQLite ;
- `APP_BASE_URL` n'est pas en `https://` ;
- `STORAGE_BACKEND=s3` mais un des `S3_*` obligatoires manque.

Voir `backend/app/startup_checks.py`.

## Migrations (Alembic)

```bash
cd backend
alembic upgrade head
```

Le schema de production est gere **exclusivement** par Alembic. `Base.metadata.create_all()` (filet de securite pour un SQLite de developpement neuf) ne s'execute plus quand `APP_ENV=production` (voir `backend/app/main.py`).

## Demarrage

Installation :
```bash
cd backend
pip install -r requirements.txt        # production
pip install -r requirements-dev.txt    # developpement/tests (ajoute pytest)
```

Configuration : copier `backend/.env.example` en `backend/.env` et renseigner les valeurs reelles (jamais commiter `.env`).

Migration puis demarrage :
```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

`$PORT` doit venir de l'environnement d'hebergement (jamais code en dur). En local, `PORT=8000` par convention du projet.

## Scheduler

`SCHEDULER_ENABLED=true` (defaut) demarre l'automatisation (relances, alertes conformite) dans le process courant, comme aujourd'hui. En deploiement multi-instance, ne mettre `SCHEDULER_ENABLED=true` que sur **une seule** instance/process ; toutes les autres doivent avoir `SCHEDULER_ENABLED=false`. Le demarrage journalise clairement `Scheduler enabled` ou `Scheduler disabled`. Aucune coordination distribuee (Redis/Celery) n'a ete introduite : c'est un choix explicite hors du perimetre de cette passe.

## Health / Readiness

- `GET /health` — le process HTTP repond, sans toucher la DB ni le storage.
- `GET /ready` — verifie que la DB repond (`SELECT 1`, jamais d'ecriture). Renvoie `503 {"status":"unavailable"}` sans jamais exposer le detail technique (le detail part dans les logs serveur).
- `GET /` — conserve pour compatibilite, meme reponse que `/health` avec le nom du service.

## Storage

`STORAGE_BACKEND=local` (defaut) : disque local sous `UPLOADS_DIR`, comme aujourd'hui.

`STORAGE_BACKEND=s3` : stockage objet via boto3, compatible AWS S3 et tout endpoint S3-custom (Cloudflare R2 : `S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com`, `S3_REGION=auto`). Aucun fallback silencieux : si `s3` est demande sans tous les parametres requis, le demarrage echoue avec un message explicite.

L'interface (`save`/`read`/`delete`/`exists`) est commune aux deux backends ; aucun router n'a besoin de changer selon le backend choisi.

**Non teste contre un vrai bucket** dans cette passe (aucun credential reel disponible) : uniquement teste via des mocks (`backend/tests/test_storage.py`). Verifier manuellement contre le bucket cible avant de s'y fier en production.

## Limitations connues (honnete, pas de service pretendu operationnel)

- **Aucun deploiement reel n'a ete effectue.** Ce travail prepare le code, ne le deploie pas.
- **Aucun bucket R2 reel n'a ete cree ni teste** : `S3CompatibleStorage` n'a ete exerce que contre des mocks boto3.
- **La publication du Site Vitrine n'est pas implementee** (Workers, domaines custom, DNS, SSL client) : hors perimetre de cette mission, volontairement.
- **Aucun sous-systeme "Admin"** (router, cookie, authentification separee) n'existe dans ce depot a ce jour — a construire separement le jour venu ; l'abstraction Storage est deja prete a servir des cles du type `admin-site-previews/{artisan_id}/index.html` sans changement supplementaire.
- **Stripe reste en mode Test/non configure**, inchange par cette mission.
- **Aucun monitoring externe** (Sentry, Datadog...) n'a ete branche : les logs vont sur stdout/stderr, a collecter par la plateforme d'hebergement.
- **Aucune verification de sauvegardes de production** n'a ete effectuee (pas de base de production existante).
- **Le rate limiting est en memoire, par process** (`backend/app/rate_limit.py`) : suffisant en mono-instance, pas partage entre plusieurs instances/workers. Non modifie dans cette passe (deja documente dans le code).
- **Aucune CI GitHub Actions n'existe dans ce depot** : les tests (`backend/tests/`, `e2e/`) s'executent manuellement.
