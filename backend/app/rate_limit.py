"""Limiteur de debit en memoire pour les endpoints PUBLICS (non authentifies) :
demande de devis, soumission d'avis, messages du portail client... Sans
limite, n'importe qui peut les spammer en boucle (faux prospects, faux avis,
flood de messages) sans meme avoir de compte.

Deliberement en memoire (pas de Redis) : ce backend tourne en un seul
process (voir scheduler.py pour le meme choix sur l'automatisation), un
limiteur partage entre plusieurs workers n'aurait de sens qu'avec un
deploiement multi-process, non utilise ici. A revisiter si l'app passe un
jour en plusieurs workers/instances (voir rapport final)."""
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

_hits: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def rate_limiter(max_requests: int, window_seconds: int):
    """Fabrique une dependance FastAPI limitant a max_requests par
    window_seconds, par adresse IP et par endpoint (cle = ip + chemin)."""

    def _dependency(request: Request) -> None:
        ip = request.client.host if request.client else "inconnu"
        cle = f"{ip}:{request.url.path}"
        maintenant = time.monotonic()
        seuil = maintenant - window_seconds
        with _lock:
            horodatages = [h for h in _hits[cle] if h > seuil]
            if len(horodatages) >= max_requests:
                _hits[cle] = horodatages
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Trop de requetes. Merci de reessayer dans quelques instants.",
                )
            horodatages.append(maintenant)
            _hits[cle] = horodatages

    return _dependency
