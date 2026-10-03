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
