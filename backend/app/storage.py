"""Abstraction de stockage de fichiers (section 26 du cahier des charges V4).

Un seul point d'entree (get_storage()) utilise par les routers : en
developpement (et pour l'instant en production, faute d'objet storage
configure), les fichiers vont sur le disque local sous UPLOADS_DIR. Pour
migrer vers un stockage objet (S3, R2, Spaces...), il suffit d'ecrire une
nouvelle classe qui implemente Storage (save/read/delete/exists) et de la
brancher ici - aucun router n'a besoin de changer.

Volontairement PAS d'implementation S3 pour l'instant : sans credentials
reels a tester, du code S3 non exerce serait justement le genre de
fonctionnalite "qui a l'air de marcher" que ce projet s'interdit. Le jour
ou un bucket est disponible, l'implementer et le brancher ici est un
changement d'un seul fichier.
"""
from __future__ import annotations

import abc
from pathlib import Path

from app.config import settings


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


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        root = Path(settings.uploads_dir)
        root.mkdir(parents=True, exist_ok=True)
        _storage = LocalFilesystemStorage(str(root))
    return _storage
