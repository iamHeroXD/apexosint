"""High-fidelity synthetic dataset generator for APEX OSINT Demo Mode."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from app.modules.base import (
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
    NormalizedTimelineEvent,
)


def get_demo_investigation_data() -> Dict[str, Any]:
    """Generate a rich, fully-connected synthetic OSINT investigation for 'Apex Demo Corporation'."""
    now = datetime.now(timezone.utc)
    one_year_ago = now - timedelta(days=365)
    six_months_ago = now - timedelta(days=180)
    three_months_ago = now - timedelta(days=90)
    one_month_ago = now - timedelta(days=30)

    # 1. Targets
    targets = [
        {
            "raw_input": "apex-defense.org",
            "detected_type": "DOMAIN",
            "normalized_value": "apex-defense.org",
            "confidence": 0.99,
            "hypotheses_json": [
                {"type": "DOMAIN", "confidence": 0.99, "percentage": 99, "explanation": "Registered Internet Domain"},
                {"type": "ORGANIZATION", "confidence": 0.65, "percentage": 65, "explanation": "Corporate entity associated with domain"}
            ]
        }
    ]

    # 2. Entities
    entities = [
        # Domain & Subdomains
        {
            "id": "ent-demo-01",
            "type": "DOMAIN",
            "value": "apex-defense.org",
            "normalized_value": "apex-defense.org",
            "confidence": 1.0,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "apex_domain", "synthetic": True}
        },
        {
            "id": "ent-demo-02",
            "type": "SUBDOMAIN",
            "value": "mail.apex-defense.org",
            "normalized_value": "mail.apex-defense.org",
            "confidence": 0.98,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "mx_endpoint", "synthetic": True}
        },
        {
            "id": "ent-demo-03",
            "type": "SUBDOMAIN",
            "value": "api.apex-defense.org",
            "normalized_value": "api.apex-defense.org",
            "confidence": 0.95,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "api_gateway", "synthetic": True}
        },
        {
            "id": "ent-demo-04",
            "type": "SUBDOMAIN",
            "value": "vpn.apex-defense.org",
            "normalized_value": "vpn.apex-defense.org",
            "confidence": 0.92,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "remote_access", "synthetic": True}
        },
        # IPs & Network
        {
            "id": "ent-demo-05",
            "type": "IP",
            "value": "198.51.100.42",
            "normalized_value": "198.51.100.42",
            "confidence": 0.99,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "web_server", "synthetic": True}
        },
        {
            "id": "ent-demo-06",
            "type": "IP",
            "value": "198.51.100.88",
            "normalized_value": "198.51.100.88",
            "confidence": 0.95,
            "provenance_label": "OBSERVED",
            "metadata_json": {"role": "mail_server", "synthetic": True}
        },
        {
            "id": "ent-demo-07",
            "type": "ASN",
            "value": "AS64496",
            "normalized_value": "AS64496",
            "confidence": 0.98,
            "provenance_label": "OBSERVED",
            "metadata_json": {"asn_org": "Apex Cloud Infrastructure AS", "synthetic": True}
        },
        {
            "id": "ent-demo-08",
            "type": "LOCATION",
            "value": "Reykjavik, Iceland",
            "normalized_value": "reykjavik, iceland",
            "confidence": 0.88,
            "provenance_label": "OBSERVED",
            "metadata_json": {"country": "Iceland", "city": "Reykjavik", "synthetic": True}
        },
        # Organization
        {
            "id": "ent-demo-09",
            "type": "ORGANIZATION",
            "value": "Apex Defense Dynamics Ltd.",
            "normalized_value": "apex defense dynamics ltd.",
            "confidence": 0.95,
            "provenance_label": "CORROBORATED",
            "metadata_json": {"industry": "Aerospace & Defense Telemetry", "synthetic": True}
        },
        # People & Usernames
        {
            "id": "ent-demo-10",
            "type": "PERSON",
            "value": "Dr. Elena Vance",
            "normalized_value": "elena vance",
            "confidence": 0.90,
            "provenance_label": "CORROBORATED",
            "cluster_id": "cluster-elena-vance-lead",
            "metadata_json": {"title": "Chief Scientific Officer", "synthetic": True}
        },
        {
            "id": "ent-demo-11",
            "type": "USERNAME",
            "value": "elena-vance-apex",
            "normalized_value": "elena-vance-apex",
            "confidence": 0.92,
            "provenance_label": "OBSERVED",
            "metadata_json": {"platform": "GitHub", "synthetic": True}
        },
        # Emails
        {
            "id": "ent-demo-12",
            "type": "EMAIL",
            "value": "e.vance@apex-defense.org",
            "normalized_value": "e.vance@apex-defense.org",
            "confidence": 0.98,
            "provenance_label": "CORROBORATED",
            "metadata_json": {"synthetic": True}
        },
        {
            "id": "ent-demo-13",
            "type": "EMAIL",
            "value": "security@apex-defense.org",
            "normalized_value": "security@apex-defense.org",
            "confidence": 0.99,
            "provenance_label": "OBSERVED",
            "metadata_json": {"synthetic": True}
        },
        # Repositories & Documents & Certificates
        {
            "id": "ent-demo-14",
            "type": "REPOSITORY",
            "value": "apex-defense/core-telemetry",
            "normalized_value": "apex-defense/core-telemetry",
            "confidence": 0.96,
            "provenance_label": "OBSERVED",
            "metadata_json": {"language": "Rust", "stars": 340, "synthetic": True}
        },
        {
            "id": "ent-demo-15",
            "type": "CERTIFICATE",
            "value": "TLS Cert #9182301 (apex-defense.org)",
            "normalized_value": "crt_9182301",
            "confidence": 0.99,
            "provenance_label": "OBSERVED",
            "metadata_json": {"issuer": "Let's Encrypt Authority X3", "synthetic": True}
        },
        {
            "id": "ent-demo-16",
            "type": "DOCUMENT",
            "value": "https://apex-defense.org/whitepaper-2025.pdf",
            "normalized_value": "https://apex-defense.org/whitepaper-2025.pdf",
            "confidence": 0.94,
            "provenance_label": "OBSERVED",
            "metadata_json": {"title": "Autonomous Edge Telemetry Architecture", "synthetic": True}
        },
    ]

    # 3. Evidence
    evidence = [
        {
            "id": "ev-demo-01",
            "source_name": "Public Recursive DNS (1.1.1.1)",
            "source_type": "DNS",
            "source_url": "dns://apex-defense.org",
            "collection_method": "DNS_RECURSIVE_QUERY",
            "confidence": 0.99,
            "epistemic_label": "OBSERVED",
            "snippet": "Authoritative A record points apex-defense.org to 198.51.100.42. MX record points to mail.apex-defense.org (198.51.100.88).",
            "raw_payload_json": {"A": ["198.51.100.42"], "MX": ["10 mail.apex-defense.org"], "TXT": ["v=spf1 include:_spf.apex-defense.org ~all"]},
            "related_entity_ids_json": ["ent-demo-01", "ent-demo-05", "ent-demo-02", "ent-demo-06"]
        },
        {
            "id": "ev-demo-02",
            "source_name": "crt.sh Certificate Transparency",
            "source_type": "CERTIFICATE",
            "source_url": "https://crt.sh/?q=%.apex-defense.org",
            "collection_method": "CT_LOG_SEARCH",
            "confidence": 0.98,
            "epistemic_label": "OBSERVED",
            "snippet": "CT log record #9182301 reveals SAN entries for apex-defense.org, api.apex-defense.org, and vpn.apex-defense.org.",
            "raw_payload_json": {"cert_id": 9182301, "issuer": "Let's Encrypt", "san": ["apex-defense.org", "api.apex-defense.org", "vpn.apex-defense.org"]},
            "related_entity_ids_json": ["ent-demo-15", "ent-demo-01", "ent-demo-03", "ent-demo-04"]
        },
        {
            "id": "ev-demo-03",
            "source_name": "BGP Routing & PeeringDB",
            "source_type": "NETWORK",
            "source_url": "https://peeringdb.com/asn/64496",
            "collection_method": "BGP_ROUTING_FEED",
            "confidence": 0.96,
            "epistemic_label": "OBSERVED",
            "snippet": "Subnet 198.51.100.0/24 advertised by AS64496 (Apex Cloud Infrastructure AS) colocated in Reykjavik, Iceland.",
            "raw_payload_json": {"prefix": "198.51.100.0/24", "asn": 64496, "city": "Reykjavik", "country": "IS"},
            "related_entity_ids_json": ["ent-demo-05", "ent-demo-07", "ent-demo-08"]
        },
        {
            "id": "ev-demo-04",
            "source_name": "GitHub Public Code Search",
            "source_type": "CODE_REPOSITORY",
            "source_url": "https://github.com/apex-defense/core-telemetry",
            "collection_method": "GITHUB_REST_API",
            "confidence": 0.98,
            "epistemic_label": "OBSERVED",
            "snippet": "Repository contains commits by 'elena-vance-apex' referencing official contact e.vance@apex-defense.org.",
            "raw_payload_json": {"repo": "apex-defense/core-telemetry", "author": "elena-vance-apex", "email": "e.vance@apex-defense.org"},
            "related_entity_ids_json": ["ent-demo-14", "ent-demo-11", "ent-demo-12", "ent-demo-10"]
        },
        {
            "id": "ev-demo-05",
            "source_name": "RFC 9116 security.txt",
            "source_type": "WEB",
            "source_url": "https://apex-defense.org/.well-known/security.txt",
            "collection_method": "HTTP_GET",
            "confidence": 0.99,
            "epistemic_label": "OBSERVED",
            "snippet": "Discovered security.txt listing Contact: mailto:security@apex-defense.org and policy acknowledgment.",
            "raw_payload_json": {"contact": "security@apex-defense.org", "canonical": "https://apex-defense.org/.well-known/security.txt"},
            "related_entity_ids_json": ["ent-demo-01", "ent-demo-13"]
        },
        {
            "id": "ev-demo-06",
            "source_name": "Public Corporate Registry (Filing #2021-99)",
            "source_type": "REGISTRY",
            "source_url": "https://iceland-registry.example/filing/2021-99",
            "collection_method": "PUBLIC_RECORD_EXTRACTION",
            "confidence": 0.92,
            "epistemic_label": "OBSERVED",
            "snippet": "Registry entry indicates Apex Defense Dynamics founded in Wilmington, Delaware on 2021-04-12.",
            "raw_payload_json": {"registered_year": 2021, "jurisdiction": "Delaware, USA"},
            "related_entity_ids_json": ["ent-demo-09"]
        },
        {
            "id": "ev-demo-07",
            "source_name": "Company Public Press Release Archive",
            "source_type": "PRESS_RELEASE",
            "source_url": "https://apex-defense.org/press/launch-2023",
            "collection_method": "WEB_SCRAPER",
            "confidence": 0.85,
            "epistemic_label": "OBSERVED",
            "snippet": "Press release states: 'Founded in Zurich, Switzerland in 2023, Apex Defense Dynamics is pioneering quantum telemetry.'",
            "raw_payload_json": {"founded_claim": 2023, "location_claim": "Zurich, Switzerland"},
            "related_entity_ids_json": ["ent-demo-09"]
        },
    ]

    # 4. Relationships (Edges)
    relationships = [
        {"source_entity_id": "ent-demo-01", "target_entity_id": "ent-demo-05", "relation_type": "RESOLVES_TO", "confidence": 0.99, "evidence_ids_json": ["ev-demo-01"]},
        {"source_entity_id": "ent-demo-02", "target_entity_id": "ent-demo-01", "relation_type": "SUBDOMAIN_OF", "confidence": 0.99, "evidence_ids_json": ["ev-demo-01"]},
        {"source_entity_id": "ent-demo-02", "target_entity_id": "ent-demo-06", "relation_type": "RESOLVES_TO", "confidence": 0.98, "evidence_ids_json": ["ev-demo-01"]},
        {"source_entity_id": "ent-demo-03", "target_entity_id": "ent-demo-01", "relation_type": "SUBDOMAIN_OF", "confidence": 0.98, "evidence_ids_json": ["ev-demo-02"]},
        {"source_entity_id": "ent-demo-04", "target_entity_id": "ent-demo-01", "relation_type": "SUBDOMAIN_OF", "confidence": 0.98, "evidence_ids_json": ["ev-demo-02"]},
        {"source_entity_id": "ent-demo-15", "target_entity_id": "ent-demo-01", "relation_type": "CERTIFICATE_FOR", "confidence": 0.99, "evidence_ids_json": ["ev-demo-02"]},
        {"source_entity_id": "ent-demo-05", "target_entity_id": "ent-demo-07", "relation_type": "HOSTED_ON", "confidence": 0.96, "evidence_ids_json": ["ev-demo-03"]},
        {"source_entity_id": "ent-demo-05", "target_entity_id": "ent-demo-08", "relation_type": "HOSTED_ON", "confidence": 0.88, "evidence_ids_json": ["ev-demo-03"]},
        {"source_entity_id": "ent-demo-09", "target_entity_id": "ent-demo-01", "relation_type": "OWNS", "confidence": 0.95, "evidence_ids_json": ["ev-demo-05", "ev-demo-06"]},
        {"source_entity_id": "ent-demo-10", "target_entity_id": "ent-demo-09", "relation_type": "ASSOCIATED_WITH", "confidence": 0.92, "evidence_ids_json": ["ev-demo-04"]},
        {"source_entity_id": "ent-demo-10", "target_entity_id": "ent-demo-11", "relation_type": "ASSOCIATED_WITH", "confidence": 0.94, "evidence_ids_json": ["ev-demo-04"]},
        {"source_entity_id": "ent-demo-11", "target_entity_id": "ent-demo-14", "relation_type": "CONTRIBUTES_TO", "confidence": 0.98, "evidence_ids_json": ["ev-demo-04"]},
        {"source_entity_id": "ent-demo-12", "target_entity_id": "ent-demo-01", "relation_type": "ASSOCIATED_WITH", "confidence": 0.98, "evidence_ids_json": ["ev-demo-04"]},
        {"source_entity_id": "ent-demo-13", "target_entity_id": "ent-demo-01", "relation_type": "ASSOCIATED_WITH", "confidence": 0.99, "evidence_ids_json": ["ev-demo-05"]},
        {"source_entity_id": "ent-demo-01", "target_entity_id": "ent-demo-16", "relation_type": "LINKS_TO", "confidence": 0.94, "evidence_ids_json": ["ev-demo-05"]},
    ]

    # 5. Timeline Events
    timeline_events = [
        {
            "timestamp": one_year_ago,
            "event_type": "REGISTRATION",
            "title": "Domain apex-defense.org Registered",
            "description": "Initial domain registration recorded via authoritative registry.",
            "entity_id": "ent-demo-01",
            "evidence_id": "ev-demo-01",
            "confidence": 0.99
        },
        {
            "timestamp": six_months_ago,
            "event_type": "CERTIFICATE_ISSUED",
            "title": "TLS Certificate #9182301 Issued",
            "description": "Issued by Let's Encrypt Authority X3 for apex-defense.org and api subdomains.",
            "entity_id": "ent-demo-15",
            "evidence_id": "ev-demo-02",
            "confidence": 0.98
        },
        {
            "timestamp": three_months_ago,
            "event_type": "REPOSITORY_COMMIT",
            "title": "Public Rust Telemetry Repository Published",
            "description": "Initial commit pushed to apex-defense/core-telemetry by elena-vance-apex.",
            "entity_id": "ent-demo-14",
            "evidence_id": "ev-demo-04",
            "confidence": 0.98
        },
        {
            "timestamp": one_month_ago,
            "event_type": "EXPOSURE_DETECTED",
            "title": "Public Security.txt Contact Published",
            "description": "Official vulnerability disclosure policy published at /.well-known/security.txt.",
            "entity_id": "ent-demo-01",
            "evidence_id": "ev-demo-05",
            "confidence": 0.99
        },
    ]

    # 6. Contradictions (CONFLICT DETECTED)
    contradictions = [
        {
            "entity_id": "ent-demo-09",
            "attribute_name": "foundation_year_and_jurisdiction",
            "source_a_id": "ev-demo-06",
            "source_a_name": "Delaware Corporate Registry Filing",
            "source_a_claim": "Founded in 2021 in Delaware, USA",
            "source_b_id": "ev-demo-07",
            "source_b_name": "Official Press Release Archive",
            "source_b_claim": "Founded in 2023 in Zurich, Switzerland",
            "explanation": "Corporate registry documentation indicates legal incorporation occurred in 2021 in Delaware, whereas public promotional press releases report establishment in Zurich in 2023. Possible re-incorporation, subsidiary formation, or marketing discrepancy requiring manual verification.",
            "resolved": False
        }
    ]

    # 7. Summary
    summary = {
        "entities_count": len(entities),
        "evidence_count": len(evidence),
        "relationships_count": len(relationships),
        "sources_count": 7,
        "high_confidence_count": 12,
        "contradictions_count": 1,
        "executive_summary": "Comprehensive defensive reconnaissance completed for synthetic target 'apex-defense.org'. Infrastructure consists of primary web ingress (198.51.100.42), separate mail exchanger (198.51.100.88), and AS64496 routing in Iceland. Associated open-source repositories reveal active Rust telemetry development led by Dr. Elena Vance. 1 contradiction detected between formal corporate registration and marketing press releases regarding founding year and location.",
    }

    return {
        "targets": targets,
        "entities": entities,
        "evidence": evidence,
        "relationships": relationships,
        "timeline_events": timeline_events,
        "contradictions": contradictions,
        "summary": summary
    }
