"""APP_ENV verrouille a un Literal strict (section 1 du durcissement
Production Readiness) : seules "development" et "production" sont
acceptees, toute autre valeur fait echouer la construction de Settings()
elle-meme (donc le chargement de app.config au demarrage reel), avec un
message explicite - pas une verification separee a cote."""
import pytest
from pydantic import ValidationError

from app.config import Settings


def test_development_accepte():
    assert Settings(app_env="development").app_env == "development"


def test_production_accepte():
    assert Settings(app_env="production").app_env == "production"


def test_defaut_est_development():
    assert Settings().app_env == "development"


@pytest.mark.parametrize(
    "valeur",
    ["prod", "prodution", "staging", "", "Production", "DEVELOPMENT", "dev", "none", " production"],
)
def test_valeur_invalide_refusee(valeur):
    with pytest.raises(ValidationError) as exc_info:
        Settings(app_env=valeur)
    message = str(exc_info.value)
    assert "app_env" in message
    assert "development" in message and "production" in message


def test_message_erreur_liste_les_valeurs_acceptees():
    with pytest.raises(ValidationError) as exc_info:
        Settings(app_env="staging")
    message = str(exc_info.value)
    assert "'development'" in message
    assert "'production'" in message
