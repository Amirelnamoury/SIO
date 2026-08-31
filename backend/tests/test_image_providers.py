from unittest.mock import Mock

import pytest
import requests

from generator.v3.media.providers import (
    PixabayProvider,
    PexelsProvider,
    ProviderRateLimited,
    ProviderUnavailable,
    search_with_fallback,
)
from generator.v3.media.query_profiles import build_query_profile


def response(status=200, payload=None):
    result = Mock(status_code=status, content=b"image")
    result.json.return_value = payload
    return result


def test_pexels_success_normalise_licence_credit_et_source():
    session = Mock()
    session.get.return_value = response(payload={"photos": [{"id": 42, "width": 2000, "height": 1300, "url": "https://pexels.test/photo/42", "photographer": "Ada", "src": {"large2x": "https://img.test/42.jpg"}}]})
    assets = PexelsProvider("secret", session=session).search("concrete architecture")
    assert len(assets) == 1
    assert assets[0].asset_id == "42"
    assert assets[0].photographer == "Ada"
    assert assets[0].licence == "Pexels License"
    assert "secret" not in repr(assets[0])


def test_pexels_rate_limit_est_explicit():
    session = Mock()
    session.get.return_value = response(status=429, payload={})
    with pytest.raises(ProviderRateLimited):
        PexelsProvider("secret", session=session).search("query")


def test_pexels_timeout_est_normalise():
    session = Mock()
    session.get.side_effect = requests.Timeout()
    with pytest.raises(ProviderUnavailable, match="timeout"):
        PexelsProvider("secret", session=session).search("query")


def test_pexels_reponse_invalide_est_refusee():
    session = Mock()
    session.get.return_value = response(payload={"unexpected": []})
    with pytest.raises(ProviderUnavailable, match="photos"):
        PexelsProvider("secret", session=session).search("query")


def test_pixabay_prend_le_relais_apres_pexels_down():
    pexels_session = Mock()
    pexels_session.get.return_value = response(status=503, payload={})
    pixabay_session = Mock()
    pixabay_session.get.return_value = response(payload={"hits": [{"id": 9, "imageWidth": 1800, "imageHeight": 1200, "largeImageURL": "https://img.test/9.jpg", "pageURL": "https://pixabay.test/9", "user": "Lin"}]})
    assets, failures = search_with_fallback([PexelsProvider("p", session=pexels_session), PixabayProvider("x", session=pixabay_session)], "wood interior")
    assert assets[0].provider == "pixabay"
    assert failures and failures[0].startswith("pexels:")


def test_aucune_cle_et_zero_resultat_ne_bloquent_pas():
    assets, failures = search_with_fallback([PexelsProvider(None), PixabayProvider("")], "query")
    assert assets == []
    assert failures == []


def test_provider_down_total_retourne_zero_asset():
    sessions = [Mock(), Mock()]
    for session in sessions:
        session.get.return_value = response(status=500, payload={})
    assets, failures = search_with_fallback([PexelsProvider("p", session=sessions[0]), PixabayProvider("x", session=sessions[1])], "query")
    assert assets == []
    assert len(failures) == 2


def test_query_profile_change_avec_direction_et_usage():
    editorial = build_query_profile("peintre", {"art_direction": "editorial_luxury"}, "hero")
    technical = build_query_profile("peintre", {"art_direction": "technical_spatial"}, "gallery")
    assert editorial.queries != technical.queries
    assert all("peintre" not in query.lower() for query in editorial.queries)
