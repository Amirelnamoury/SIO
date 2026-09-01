"""Component blueprint registries."""

from .about import ABOUT_COMPONENTS
from .contacts import CONTACT_COMPONENTS, FORM_COMPONENTS
from .ctas import CTA_COMPONENTS
from .footers import FOOTER_COMPONENTS
from .galleries import GALLERY_COMPONENTS
from .headers import HEADER_COMPONENTS
from .heroes import HERO_COMPONENTS
from .services import SERVICES_COMPONENTS
from .trust import TRUST_COMPONENTS

COMPONENT_REGISTRIES = {
    "header": HEADER_COMPONENTS,
    "hero": HERO_COMPONENTS,
    "services": SERVICES_COMPONENTS,
    "gallery": GALLERY_COMPONENTS,
    "about": ABOUT_COMPONENTS,
    "trust": TRUST_COMPONENTS,
    "cta": CTA_COMPONENTS,
    "contact": CONTACT_COMPONENTS,
    "footer": FOOTER_COMPONENTS,
    "form": FORM_COMPONENTS,
}

ALL_COMPONENTS = {
    component_id: component
    for registry in COMPONENT_REGISTRIES.values()
    for component_id, component in registry.items()
}
