"""Abstraction de stockage de fichiers (section 26 du cahier des charges V4).

Un seul point d'entree (get_storage()) utilise par les routers : le backend
reel (disque local ou objet S3-compatible) est choisi par STORAGE_BACKEND,
sans qu'aucun router n'ait besoin de changer (interface save/read/delete/exists
commune, voir la classe Storage ci-dessous).

S3CompatibleStorage n'a jamais ete exerce contre un vrai bucket (aucun
credential reel disponible dans cet environnement) - seulement teste via des
mocks (voir backend/tests/test_storage.py). C'est honnete a savoir avant un
premier deploiement reel avec STORAGE_BACKEND=s3 : verifier manuellement
save/read/delete/exists contre le bucket cible avant de s'y fier en
production.
"""
from __future__ import annotations

import abc
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger("suite_artisan.storage")


class Storage(abc.ABC):
    """Interface minimale : juste ce dont les documents uploades ont besoin."""

    @abc.abstractmethod
    def save(self, relative_path: str, contenu: bytes) -> None:
        ...

    @abc.abstractmethod
    def read(self, relative_path: str) -> bytes | None:
        """None si le fichier n'existe pas (jamais d'exception pour ce cas)."""
        ...

    @abc.abstractmethod
    def delete(self, relative_path: str) -> None:
        """Ne leve jamais si le fichier n'existe deja plus (idempotent)."""
        ...

    @abc.abstractmethod
    def exists(self, relative_path: str) -> bool:
        ...


class LocalFilesystemStorage(Storage):
    """Stockage sur disque local, sous settings.uploads_dir. C'est le seul
    backend disponible aujourd'hui : suffisant pour un deploiement mono-
    instance (voir la meme limite documentee pour le scheduler et le
    rate limiter), mais les fichiers ne survivent pas a un conteneur
    ephemere ou a plusieurs instances - a migrer vers un stockage objet
    avant un deploiement multi-instance."""

    def __init__(self, root: str):
        self._root = Path(root)

    def _resolve(self, relative_path: str) -> Path:
        # Empeche toute tentative de sortir de la racine (../..) : le nom de
        # fichier sur disque est de toute facon toujours un uuid genere par
        # nous (voir routers/documents.py), jamais le nom fourni par
        # l'utilisateur, mais on se protege quand meme au niveau du stockage.
        chemin = (self._root / relative_path).resolve()
        if self._root.resolve() not in chemin.parents and chemin != self._root.resolve():
            raise ValueError(f"Chemin de stockage invalide : {relative_path}")
        return chemin

    def save(self, relative_path: str, contenu: bytes) -> None:
        chemin = self._resolve(relative_path)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(contenu)

    def read(self, relative_path: str) -> bytes | None:
        chemin = self._resolve(relative_path)
        if not chemin.is_file():
            return None
        return chemin.read_bytes()

    def delete(self, relative_path: str) -> None:
        chemin = self._resolve(relative_path)
        if chemin.is_file():
            chemin.unlink()

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).is_file()


class S3CompatibleStorage(Storage):
    """Stockage objet via l'API S3, compatible AWS S3 et tout service exposant
    un endpoint S3 custom (Cloudflare R2 est la cible prevue, endpoint de la
    forme https://<account_id>.r2.cloudflarestorage.com). Passe entierement
    par boto3 - aucune reimplementation du protocole S3 ici."""

    def __init__(self, *, endpoint_url: str, access_key_id: str, secret_access_key: str, bucket_name: str, region: str):
        import boto3

        self._bucket = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    def save(self, relative_path: str, contenu: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=relative_path, Body=contenu)

    def read(self, relative_path: str) -> bytes | None:
        from botocore.exceptions import ClientError

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=relative_path)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            raise
        return response["Body"].read()

    def delete(self, relative_path: str) -> None:
        # delete_object est deja idempotent cote S3 (204 meme si la cle
        # n'existe pas) : rien a faire de special pour respecter le contrat
        # "ne leve jamais si le fichier n'existe deja plus".
        self._client.delete_object(Bucket=self._bucket, Key=relative_path)

    def exists(self, relative_path: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=relative_path)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise
        return True


_storage: Storage | None = None

_S3_CHAMPS_REQUIS = ("s3_endpoint_url", "s3_access_key_id", "s3_secret_access_key", "s3_bucket_name")


def get_storage() -> Storage:
    global _storage
    if _storage is not None:
        return _storage

    if settings.storage_backend == "local":
        root = Path(settings.uploads_dir)
        root.mkdir(parents=True, exist_ok=True)
        _storage = LocalFilesystemStorage(str(root))
    elif settings.storage_backend == "s3":
        # Fail fast, jamais de fallback silencieux vers le disque local : un
        # artisan qui croit ses documents sur R2 alors qu'ils sont sur le
        # disque ephemere du conteneur perdrait ses fichiers au redemarrage
        # sans le savoir.
        manquants = [c.upper() for c in _S3_CHAMPS_REQUIS if not getattr(settings, c)]
        if manquants:
            raise RuntimeError(
                "STORAGE_BACKEND=s3 mais des parametres obligatoires manquent : "
                + ", ".join(manquants)
            )
        logger.info("Storage : backend s3 (bucket=%s, endpoint configure)", settings.s3_bucket_name)
        _storage = S3CompatibleStorage(
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            bucket_name=settings.s3_bucket_name,
            region=settings.s3_region,
        )
    else:
        raise RuntimeError(f"STORAGE_BACKEND doit etre 'local' ou 's3', pas {settings.storage_backend!r}")

    return _storage
