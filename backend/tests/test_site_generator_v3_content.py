from app.admin_service import LEGACY_GENERATED_CONTENT, default_site_config, merged_site_config, site_content_warnings
from app.models import Artisan, SiteVitrine


def artisan(metier):
    return Artisan(id=91, nom_entreprise="Test", metier=metier, email="test@example.test", slug=f"test-{metier}", plan="essentiel", subscription_status="active")


def test_ancien_bundle_plomberie_est_omis_sans_etre_efface():
    current = artisan("peintre")
    tagline, services = LEGACY_GENERATED_CONTENT[0]
    plumbing = {"tagline": tagline, "services": services}
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


def test_nouveaux_sites_ne_recoivent_aucun_contenu_metier_invente():
    wood = default_site_config(artisan("menuisier"))
    renovation = default_site_config(artisan("renovateur"))
    assert wood["tagline"] == renovation["tagline"] == ""
    assert wood["services"] == renovation["services"] == []
