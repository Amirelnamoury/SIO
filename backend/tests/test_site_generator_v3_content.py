from app.admin_service import default_site_config, merged_site_config, site_content_warnings
from app.models import Artisan, SiteVitrine


def artisan(metier):
    return Artisan(id=91, nom_entreprise="Test", metier=metier, email="test@example.test", slug=f"test-{metier}", plan="essentiel", subscription_status="active")


def test_peintre_ne_recoit_jamais_defaults_plomberie():
    current = artisan("peintre")
    plumbing = default_site_config(artisan("plombier"))
    site = SiteVitrine(artisan_id=current.id, statut="brouillon", config=plumbing)
    merged = merged_site_config(current, site)
    assert "plombier" not in merged["tagline"].lower()
    assert not any("canalisation" in service.lower() for service in merged["services"])
    assert site.config == plumbing
    assert site_content_warnings(current, site)


def test_contenu_personnalise_n_est_jamais_ecrase():
    current = artisan("peintre")
    custom = {"tagline": "Une phrase écrite par l’artisan", "services": ["Fresque personnalisée"]}
    site = SiteVitrine(artisan_id=current.id, statut="brouillon", config=custom)
    assert merged_site_config(current, site)["services"] == custom["services"]
    assert site_content_warnings(current, site) == []


def test_defaults_menuisier_et_renovateur_sont_specifiques():
    wood = default_site_config(artisan("menuisier"))
    renovation = default_site_config(artisan("renovateur"))
    assert any("bois" in service.lower() or "menuiser" in service.lower() for service in wood["services"])
    assert any("rénovation" in service.lower() for service in renovation["services"])
    assert wood != renovation
