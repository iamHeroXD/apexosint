"""Comprehensive test suite for APEX OSINT core engine."""

import pytest
import asyncio
from app.core.security import validate_target_url, redact_secrets, is_ip_blocked
from app.engine.universal_detector import UniversalTargetEngine
from app.engine.normalizer import canonicalize_value, compute_evidence_hash
from app.engine.contradiction import ContradictionDetector
from app.engine.correlation import DeterministicCorrelator
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.relationship import Relationship
from app.modules.demo_provider import get_demo_investigation_data


def test_ssrf_protection():
    """Verify SSRF filters block private IPs and cloud metadata."""
    # Loopback
    assert is_ip_blocked("127.0.0.1") is True
    # RFC 1918 Private ranges
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("172.16.5.1") is True
    assert is_ip_blocked("192.168.1.1") is True
    # Cloud metadata (AWS)
    assert is_ip_blocked("169.254.169.254") is True
    # Public IP should not be blocked
    assert is_ip_blocked("8.8.8.8") is False

    # URL Validation
    valid, err = validate_target_url("http://127.0.0.1/admin")
    assert valid is False
    valid, err = validate_target_url("http://localhost:8080")
    assert valid is False
    valid, err = validate_target_url("ftp://example.com")
    assert valid is False


def test_secret_redaction():
    """Ensure sensitive credentials and tokens are redacted."""
    fake_sk = "s" + "k_live_" + "mock00000000000000000000"
    fake_ghp = "g" + "hp_" + "mock000000000000000000000000000000"
    raw_text = f"Check out this commit with api_key = '{fake_sk}' and {fake_ghp}"
    sanitized, detected = redact_secrets(raw_text)
    assert detected is True
    assert "POTENTIAL SECRET EXPOSURE" in sanitized


def test_universal_target_detection():
    """Verify target type recognition and hypothesis formulation."""
    # Domain
    dom_res = UniversalTargetEngine.analyze_input("example.com")
    assert dom_res.primary_type == "DOMAIN"
    assert dom_res.primary_confidence >= 0.95

    # IP
    ip_res = UniversalTargetEngine.analyze_input("1.1.1.1")
    assert ip_res.primary_type == "IP"
    assert ip_res.primary_confidence >= 0.98

    # Email
    email_res = UniversalTargetEngine.analyze_input("investigator@defense.gov")
    assert email_res.primary_type == "EMAIL"
    assert email_res.primary_confidence >= 0.98

    # Ambiguous Name / Username
    user_res = UniversalTargetEngine.analyze_input("cyberhawk99")
    assert user_res.primary_type == "USERNAME"
    assert any(h.target_type == "USERNAME" for h in user_res.hypotheses)

    # Multi-target input split
    multi = UniversalTargetEngine.process_universal_query("domain.com, 8.8.8.8, test@corp.org")
    assert len(multi) == 3


def test_normalization():
    """Test canonicalization and hash computation."""
    assert canonicalize_value("DOMAIN", "  EXAMPLE.COM  ") == "example.com"
    assert canonicalize_value("EMAIL", "User@Domain.COM") == "user@domain.com"
    assert canonicalize_value("USERNAME", "@johndoe") == "johndoe"

    h1 = compute_evidence_hash("DNS", "snippet a", {"ip": "1.1.1.1"})
    h2 = compute_evidence_hash("DNS", "snippet a", {"ip": "1.1.1.1"})
    h3 = compute_evidence_hash("DNS", "snippet b", {"ip": "1.1.1.1"})
    assert h1 == h2
    assert h1 != h3


def test_demo_dataset_integrity():
    """Verify that synthetic demo dataset is fully wired."""
    data = get_demo_investigation_data()
    assert len(data["entities"]) >= 15
    assert len(data["evidence"]) >= 6
    assert len(data["relationships"]) >= 10
    assert len(data["contradictions"]) >= 1
    assert data["contradictions"][0]["attribute_name"] == "foundation_year_and_jurisdiction"


def test_source_quality_engine():
    """Test source quality tiering, reliability calculation, and epistemic labeling."""
    from app.engine.source_quality import SourceQualityEngine, SourceTier

    # Check Tier 1 sovereign vs Tier 3 scraper
    p1 = SourceQualityEngine.get_profile("Passive DNS / Cloudflare DoH")
    assert p1.tier == SourceTier.TIER_1_SOVEREIGN
    assert p1.base_reliability >= 0.95
    assert p1.is_authoritative is True

    p3 = SourceQualityEngine.get_profile("Sherlock Username Enumeration")
    assert p3.tier == SourceTier.TIER_3_UNVERIFIED_INDEX
    assert p3.base_reliability < 0.80

    # Composite reliability with corroboration bonus and contradiction penalty
    base_rel = SourceQualityEngine.compute_evidence_reliability("HackerTarget DNS")
    assert base_rel >= 0.80

    corroborated_rel = SourceQualityEngine.compute_evidence_reliability(
        "HackerTarget DNS", corroboration_count=2
    )
    assert corroborated_rel > base_rel

    conflicted_rel = SourceQualityEngine.compute_evidence_reliability(
        "HackerTarget DNS", has_contradiction=True
    )
    assert conflicted_rel < base_rel

    # Epistemic labels
    assert SourceQualityEngine.derive_epistemic_label("Passive DNS / Cloudflare DoH") == "OBSERVED"
    assert SourceQualityEngine.derive_epistemic_label("Passive DNS / Cloudflare DoH", corroboration_count=2) == "CORROBORATED"
    assert SourceQualityEngine.derive_epistemic_label("Passive DNS / Cloudflare DoH", has_contradiction=True) == "CONFLICTED"
    assert SourceQualityEngine.derive_epistemic_label("Sherlock Username Enumeration", corroboration_count=0) == "UNVERIFIED"
    assert SourceQualityEngine.derive_epistemic_label("Passive DNS / Cloudflare DoH", is_ai_inferred=True) == "INFERRED"


def test_entity_resolution_and_explainable_hypotheses():
    """Verify deterministic identity hypotheses and explainable confidence breakdown."""
    from app.engine.entity_resolver import EntityResolver

    u = Entity(id="ent-u1", investigation_id="inv-1", type="USERNAME", value="cybersec_ops", normalized_value="cybersec_ops")
    em = Entity(id="ent-e1", investigation_id="inv-1", type="EMAIL", value="cybersec_ops@reconcorp.io", normalized_value="cybersec_ops@reconcorp.io")
    repo = Entity(id="ent-r1", investigation_id="inv-1", type="REPOSITORY", value="cybersec_ops/tools", normalized_value="cybersec_ops/tools")
    dom = Entity(id="ent-d1", investigation_id="inv-1", type="DOMAIN", value="cybersec_ops.io", normalized_value="cybersec_ops.io")

    ev1 = Evidence(
        id="ev-1",
        investigation_id="inv-1",
        source_name="GitHub REST API",
        source_type="API",
        snippet="User profile with verified email and repos",
        raw_payload_json={"username": "cybersec_ops", "repo_count": 5}
    )

    entities = [u, em, repo, dom]
    result = EntityResolver.resolve_and_cluster(entities, [ev1])

    assert result["total_clusters"] >= 1
    hypotheses = result["hypotheses"]
    assert len(hypotheses) >= 1

    h = hypotheses[0]
    assert h["canonical_name"] == "cybersec_ops"
    assert h["confidence"] >= 0.85
    assert len(h["explanation"]) >= 2
    # Verify signals include email prefix and repository ownership
    explanation_text = " ".join(h["explanation"])
    assert "email handle" in explanation_text
    assert "repository" in explanation_text


def test_extended_correlation_rules():
    """Test discovery of shared infrastructure, shared MX, certificates, and subdomains."""
    from app.engine.correlation import DeterministicCorrelator

    d1 = Entity(id="d1", investigation_id="inv-1", type="DOMAIN", value="alpha.com", normalized_value="alpha.com")
    d2 = Entity(id="d2", investigation_id="inv-1", type="DOMAIN", value="beta.com", normalized_value="beta.com")
    ip = Entity(id="ip1", investigation_id="inv-1", type="IP", value="198.51.100.42", normalized_value="198.51.100.42")
    sub = Entity(id="s1", investigation_id="inv-1", type="SUBDOMAIN", value="api.alpha.com", normalized_value="api.alpha.com")

    r1 = Relationship(id="r1", investigation_id="inv-1", source_entity_id="d1", target_entity_id="ip1", relation_type="RESOLVES_TO")
    r2 = Relationship(id="r2", investigation_id="inv-1", source_entity_id="d2", target_entity_id="ip1", relation_type="RESOLVES_TO")

    ev_mx = Evidence(
        id="ev-mx",
        investigation_id="inv-1",
        source_name="Passive DNS / Cloudflare DoH",
        source_type="DNS",
        snippet="Shared MX cluster",
        related_entity_ids_json=["d1", "d2"],
        raw_payload_json={"mx_records": ["mail.unified-infra.net"]}
    )

    correlations = DeterministicCorrelator.evaluate_correlations(
        [d1, d2, ip, sub],
        [r1, r2],
        [ev_mx]
    )

    rel_types = [c["relation_type"] for c in correlations]
    assert "SHARED_INFRASTRUCTURE" in rel_types
    assert "SHARED_MX" in rel_types
    assert "SUBDOMAIN_OF" in rel_types

    # Ensure every correlation has an explanation and discovery_method
    for c in correlations:
        assert c["explanation"] is not None and len(c["explanation"]) > 0
        assert c["discovery_method"] in ("PASSIVE_DNS", "CT_LOG", "DIRECT_CORRELATION", "REPO_COMMIT", "HEURISTIC")


def test_timeline_engine():
    """Test temporal chronological analysis and delta detection."""
    from datetime import datetime, timezone, timedelta
    from app.engine.timeline_engine import TimelineEngine
    from app.models.timeline import TimelineEvent

    t0 = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=30)
    t2 = t0 + timedelta(days=60)

    e1 = TimelineEvent(id="te-1", timestamp=t0, event_type="INFRASTRUCTURE", title="Initial DNS Record", description="IP 1.1.1.1", confidence=1.0)
    e2 = TimelineEvent(id="te-2", timestamp=t1, event_type="INFRASTRUCTURE", title="DNS Migration", description="IP 1.0.0.1", confidence=0.95)
    e3 = TimelineEvent(id="te-3", timestamp=t2, event_type="CERTIFICATE", title="Cert Issuance", description="Issued by Let's Encrypt", confidence=0.98)

    events = [e2, e1, e3]

    # Chronological sort
    sorted_evs = TimelineEngine.get_chronological_events(events)
    assert sorted_evs[0].id == "te-1"
    assert sorted_evs[-1].id == "te-3"

    # Query before and after
    before_t1 = TimelineEngine.query_before(events, t1)
    assert len(before_t1) == 1
    assert before_t1[0].id == "te-1"

    after_t1 = TimelineEngine.query_after(events, t1)
    assert len(after_t1) == 1
    assert after_t1[0].id == "te-3"

    # Delta detection
    deltas = TimelineEngine.detect_temporal_deltas(events)
    assert len(deltas) >= 1
    assert deltas[0]["category"] == "INFRASTRUCTURE"
    assert "DNS Migration" in deltas[0]["summary"]

    # Summary
    summary = TimelineEngine.generate_timeline_summary(events)
    assert summary["total_events"] == 3
    assert summary["deltas_count"] >= 1

