"""Source Reliability and Quality Framework for APEX OSINT.

Evaluates evidence credibility, source tiers, freshness half-life, and epistemic weight.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum


class SourceTier(str, Enum):
    TIER_1_SOVEREIGN = "TIER_1_SOVEREIGN"          # 0.95 - 0.99 (RIR, DNSSEC, CT logs, IANA)
    TIER_2_PLATFORM_API = "TIER_2_PLATFORM_API"    # 0.85 - 0.92 (GitHub API, Censys, Shodan, VirusTotal)
    TIER_3_UNVERIFIED_INDEX = "TIER_3_UNVERIFIED_INDEX"  # 0.65 - 0.75 (Web scrapers, search indices, aggregators)
    TIER_4_HEURISTIC = "TIER_4_HEURISTIC"          # 0.40 - 0.60 (Regex pattern matching, heuristics)


@dataclass
class SourceProfile:
    source_name: str
    tier: SourceTier
    base_reliability: float
    freshness_halflife_days: float
    is_authoritative: bool
    description: str
    known_failure_modes: List[str] = field(default_factory=list)


# Authoritative Source Registry
DEFAULT_SOURCE_PROFILES: Dict[str, SourceProfile] = {
    # TIER 1
    "Passive DNS / Cloudflare DoH": SourceProfile(
        source_name="Passive DNS / Cloudflare DoH",
        tier=SourceTier.TIER_1_SOVEREIGN,
        base_reliability=0.98,
        freshness_halflife_days=7.0,
        is_authoritative=True,
        description="Cryptographically signed DNS over HTTPS root response",
        known_failure_modes=["Geo-DNS splitting", "Dynamic DNS rotation"]
    ),
    "Certificate Transparency (crt.sh)": SourceProfile(
        source_name="Certificate Transparency (crt.sh)",
        tier=SourceTier.TIER_1_SOVEREIGN,
        base_reliability=0.99,
        freshness_halflife_days=90.0,
        is_authoritative=True,
        description="Append-only cryptographically verifiable Certificate Transparency Log",
        known_failure_modes=["Expired certificates still in log", "Wildcard SAN masking"]
    ),
    "RDAP / Sovereign RIR": SourceProfile(
        source_name="RDAP / Sovereign RIR",
        tier=SourceTier.TIER_1_SOVEREIGN,
        base_reliability=0.97,
        freshness_halflife_days=30.0,
        is_authoritative=True,
        description="Official Regional Internet Registry allocation record (ARIN, RIPE, APNIC)",
        known_failure_modes=["Privacy guard redactions", "Outdated POC contact"]
    ),

    # TIER 2
    "GitHub REST API": SourceProfile(
        source_name="GitHub REST API",
        tier=SourceTier.TIER_2_PLATFORM_API,
        base_reliability=0.92,
        freshness_halflife_days=14.0,
        is_authoritative=False,
        description="Official GitHub API telemetry for profile, repos, and public commit events",
        known_failure_modes=["Rate limits (60 req/hr unauth)", "Deleted repos", "Fake commit author emails"]
    ),
    "AlienVault OTX": SourceProfile(
        source_name="AlienVault OTX",
        tier=SourceTier.TIER_2_PLATFORM_API,
        base_reliability=0.88,
        freshness_halflife_days=14.0,
        is_authoritative=False,
        description="Crowdsourced threat intelligence pulses and passive DNS",
        known_failure_modes=["Community false positives", "Stale pulses"]
    ),
    "HackerTarget DNS": SourceProfile(
        source_name="HackerTarget DNS",
        tier=SourceTier.TIER_2_PLATFORM_API,
        base_reliability=0.86,
        freshness_halflife_days=14.0,
        is_authoritative=False,
        description="HackerTarget curated passive DNS and IP reverse lookup",
        known_failure_modes=["Daily query limits", "Cached historic records"]
    ),

    # TIER 3
    "Sherlock Username Enumeration": SourceProfile(
        source_name="Sherlock Username Enumeration",
        tier=SourceTier.TIER_3_UNVERIFIED_INDEX,
        base_reliability=0.72,
        freshness_halflife_days=30.0,
        is_authoritative=False,
        description="Multi-platform HTTP status probe across 300+ public social web services",
        known_failure_modes=["HTTP 200 false positives", "WAF blocks", "Account name squatting"]
    ),
    "Public Search Index Scraper": SourceProfile(
        source_name="Public Search Index Scraper",
        tier=SourceTier.TIER_3_UNVERIFIED_INDEX,
        base_reliability=0.68,
        freshness_halflife_days=7.0,
        is_authoritative=False,
        description="Search engine snippet extraction without direct API verification",
        known_failure_modes=["SEO spam", "Stale cache snippets", "Scraper blocking"]
    ),

    # TIER 4
    "Heuristic Correlation Engine": SourceProfile(
        source_name="Heuristic Correlation Engine",
        tier=SourceTier.TIER_4_HEURISTIC,
        base_reliability=0.55,
        freshness_halflife_days=365.0,
        is_authoritative=False,
        description="Rule-based hypothesis linking based on shared attributes",
        known_failure_modes=["Coincidental naming collisions", "Shared hosting provider false linkage"]
    ),
}


class SourceQualityEngine:
    """Manages source reputation, evidentiary decay, and epistemic labeling."""

    @classmethod
    def get_profile(cls, source_name: str) -> SourceProfile:
        """Retrieve profile or infer safe fallback tier."""
        if source_name in DEFAULT_SOURCE_PROFILES:
            return DEFAULT_SOURCE_PROFILES[source_name]
        
        # Heuristic matching by prefix/keyword
        lower = source_name.lower()
        if "doh" in lower or "dns" in lower or "cert" in lower or "rdap" in lower or "whois" in lower:
            return SourceProfile(
                source_name=source_name,
                tier=SourceTier.TIER_1_SOVEREIGN,
                base_reliability=0.95,
                freshness_halflife_days=14.0,
                is_authoritative=True,
                description=f"Authoritative infrastructure probe: {source_name}"
            )
        elif "api" in lower or "github" in lower or "otx" in lower:
            return SourceProfile(
                source_name=source_name,
                tier=SourceTier.TIER_2_PLATFORM_API,
                base_reliability=0.88,
                freshness_halflife_days=21.0,
                is_authoritative=False,
                description=f"Structured platform API: {source_name}"
            )
        elif "sherlock" in lower or "scrape" in lower or "search" in lower:
            return SourceProfile(
                source_name=source_name,
                tier=SourceTier.TIER_3_UNVERIFIED_INDEX,
                base_reliability=0.70,
                freshness_halflife_days=30.0,
                is_authoritative=False,
                description=f"Public catalog / web scraper: {source_name}"
            )
        
        # Generic fallback
        return SourceProfile(
            source_name=source_name,
            tier=SourceTier.TIER_3_UNVERIFIED_INDEX,
            base_reliability=0.75,
            freshness_halflife_days=30.0,
            is_authoritative=False,
            description=f"Unclassified evidence source: {source_name}"
        )

    @classmethod
    def compute_evidence_reliability(
        cls,
        source_name: str,
        collected_at: Optional[datetime] = None,
        corroboration_count: int = 0,
        has_contradiction: bool = False
    ) -> float:
        """
        Calculate deterministic reliability score [0.0 - 1.0].
        Incorporates base source tier, corroboration bonuses, contradiction penalties, and time decay.
        """
        profile = cls.get_profile(source_name)
        score = profile.base_reliability

        # Time decay calculation
        if collected_at:
            now = datetime.now(timezone.utc)
            if collected_at.tzinfo is None:
                collected_at = collected_at.replace(tzinfo=timezone.utc)
            age_days = max(0.0, (now - collected_at).total_seconds() / 86400.0)
            half_life = max(1.0, profile.freshness_halflife_days)
            # Exponential decay factor: 0.5^(age / half_life)
            decay_factor = 0.5 ** (age_days / (half_life * 4.0))  # Smooth decay
            score *= (0.85 + 0.15 * decay_factor)

        # Corroboration bonus: +0.03 per independent corroboration (capped at +0.09)
        bonus = min(0.09, corroboration_count * 0.03)
        score += bonus

        # Contradiction penalty: -0.20 if direct discrepancy detected
        if has_contradiction:
            score -= 0.20

        return round(max(0.05, min(0.99, score)), 3)

    @classmethod
    def derive_epistemic_label(
        cls,
        source_name: str,
        corroboration_count: int = 0,
        has_contradiction: bool = False,
        is_ai_inferred: bool = False,
        age_days: float = 0.0
    ) -> str:
        """
        Deterministically assigns epistemic status:
        OBSERVED, CORROBORATED, CONFLICTED, INFERRED, UNVERIFIED, STALE
        """
        if is_ai_inferred:
            return "INFERRED"
        if has_contradiction:
            return "CONFLICTED"

        profile = cls.get_profile(source_name)
        if age_days > (profile.freshness_halflife_days * 3.0):
            return "STALE"

        if corroboration_count >= 1:
            return "CORROBORATED"

        if profile.tier in (SourceTier.TIER_3_UNVERIFIED_INDEX, SourceTier.TIER_4_HEURISTIC):
            return "UNVERIFIED"

        return "OBSERVED"
