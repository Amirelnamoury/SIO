"""Truth model for separating facts, derivations, safe copy and invention."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from .models import ClaimRequirement, TruthClass


@dataclass(frozen=True)
class ClaimAssessment:
    claim: str
    classification: TruthClass
    supporting_field: str | None = None
    reason: str = ""


CLAIM_RULES = {
    "years_experience": re.compile(r"\b\d+\s*(?:ans|années?)\s+d['’ ]expérience", re.I),
    "project_count": re.compile(r"\b\d+\s+(?:projets?|chantiers?|réalisations?)", re.I),
    "client_count": re.compile(r"\b\d+\s+clients?", re.I),
    "response_delay": re.compile(r"\b(?:sous|en moins de)\s+\d+\s*(?:h|heures?|jours?)", re.I),
    "average_rating": re.compile(r"\b\d(?:[.,]\d)?\s*/\s*5\b", re.I),
    "rge": re.compile(r"\bRGE\b", re.I),
    "insurance": re.compile(r"\b(?:décennale|assur(?:é|ance))\b", re.I),
    "guarantee": re.compile(r"\bgaranti(?:e|s)?\b", re.I),
    "emergency_service": re.compile(r"\b(?:urgence|24\s*h\s*/\s*24|7\s*j\s*/\s*7)\b", re.I),
    "certifications": re.compile(r"\b(?:certifi(?:é|cation)|Qualibat|Qualipac)\b", re.I),
}

CLAIM_REQUIREMENTS = {
    "years_experience": ClaimRequirement("years_experience", "years_experience", description="Exact supplied duration required."),
    "project_count": ClaimRequirement("project_count", "project_count", description="Count must come from artisan data."),
    "client_count": ClaimRequirement("client_count", "client_count", description="Count must come from artisan data."),
    "response_delay": ClaimRequirement("response_delay", "response_delay", description="No default response promise."),
    "average_rating": ClaimRequirement("average_rating", "average_rating", description="Rating and source must be supplied."),
    "rge": ClaimRequirement("rge", "rge", True, "RGE may render only when explicitly true."),
    "insurance": ClaimRequirement("insurance", "insurance", description="Verified insurance data required."),
    "guarantee": ClaimRequirement("guarantee", "guarantee", description="Terms must be supplied."),
    "emergency_service": ClaimRequirement("emergency_service", "emergency_service", True, "Emergency availability may render only when explicitly true."),
    "certifications": ClaimRequirement("certifications", "certifications", description="Named supplied certifications required."),
    "availability": ClaimRequirement("availability", "availability", description="Availability must be current supplied data."),
}

SAFE_PATTERNS = (
    re.compile(r"^Découvrez (?:nos|les) ", re.I),
    re.compile(r"^Parlons de votre projet", re.I),
    re.compile(r"^Contactez-nous", re.I),
    re.compile(r"^Nos prestations", re.I),
)


def can_render_claim(claim_type: str, facts: Mapping[str, Any]) -> bool:
    """Authorize a structured claim before any copy is composed."""
    requirement = CLAIM_REQUIREMENTS.get(claim_type)
    if requirement is None:
        return False
    value = facts.get(requirement.required_field)
    if requirement.expected_value is not None:
        return value is requirement.expected_value or value == requirement.expected_value
    return value not in (None, "", [], (), False)


def can_use_media_wording(media_source: str, media_role: str, wording_role: str) -> bool:
    """Block stock imagery from project, team and transformation semantics."""
    artisan_only_roles = {"project", "realisation", "chantier", "before_after", "team", "selected_project"}
    if wording_role in artisan_only_roles:
        return media_source == "artisan" and media_role in {"artisan_project", "before_after", "portrait"}
    return media_source in {"artisan", "stock", "none"}


def classify_claim(claim: str, facts: Mapping[str, Any]) -> ClaimAssessment:
    normalized = claim.strip()
    for field, pattern in CLAIM_RULES.items():
        if pattern.search(normalized):
            if can_render_claim(field, facts):
                return ClaimAssessment(normalized, TruthClass.FACT, field, "verified_field_present")
            return ClaimAssessment(normalized, TruthClass.FORBIDDEN_INVENTION, field, "required_field_missing")
    if normalized in {str(value) for value in facts.values() if isinstance(value, (str, int, float))}:
        return ClaimAssessment(normalized, TruthClass.FACT, reason="exact_verified_value")
    if any(pattern.search(normalized) for pattern in SAFE_PATTERNS):
        return ClaimAssessment(normalized, TruthClass.SAFE_GENERIC_COPY, reason="non_factual_prompt")
    return ClaimAssessment(normalized, TruthClass.SAFE_GENERIC_COPY, reason="no factual assertion detected")


def validate_claims(claims: tuple[str, ...], facts: Mapping[str, Any]) -> tuple[ClaimAssessment, ...]:
    return tuple(classify_claim(claim, facts) for claim in claims)
