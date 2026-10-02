"""Certificate Transparency Log Intelligence Module for APEX OSINT."""

from datetime import datetime, timezone
from typing import Dict, Any, Set
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
    NormalizedTimelineEvent,
)


class CertTransparencyModule(BaseOSINTModule):
    name = "cert_transparency"
    display_name = "Certificate Transparency (crt.sh)"
    description = "Queries public Certificate Transparency logs to discover subdomains, TLS certificates, and issuance timelines."
    category = "DOMAIN"
    target_types = ["DOMAIN"]
    rate_limit = 1.0
    source = "crt.sh Certificate Search"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        domain = target_value.lower().strip()

        finding.primary_entity = NormalizedEntity(
            type="DOMAIN",
            value=domain,
            normalized_value=domain,
            confidence=1.0,
        )

        url = f"https://crt.sh/?q=%.{domain}&output=json"

        try:
            client = SafeHTTPClient(timeout=12.0)
            response = await client.get(url)
            if response.status_code != 200:
                return finding
            certs = response.json()
        except Exception:
            return finding

        if not isinstance(certs, list) or not certs:
            return finding

        discovered_subdomains: Set[str] = set()
        discovered_issuers: Set[str] = set()

        evidence_snippet = f"Discovered {len(certs)} certificate log records for {domain} via crt.sh."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="crt.sh Certificate Transparency",
                source_type="CERTIFICATE",
                source_url=url,
                snippet=evidence_snippet,
                collection_method="CT_LOG_SEARCH",
                confidence=0.97,
                epistemic_label="OBSERVED",
                raw_payload={"count": len(certs), "sample_cert_id": certs[0].get("id") if certs else None},
                related_entity_values=[domain]
            )
        )

        # Process each certificate record
        for cert in certs[:100]:  # Cap at top 100 for performance
            name_value = cert.get("name_value", "")
            issuer_name = cert.get("issuer_name", "Unknown Issuer")
            not_before = cert.get("not_before")
            cert_id = str(cert.get("id"))

            # Create Certificate Entity
            cert_entity = NormalizedEntity(
                type="CERTIFICATE",
                value=f"Cert #{cert_id} ({domain})",
                normalized_value=f"crt_{cert_id}",
                confidence=0.96,
                metadata={"issuer": issuer_name, "valid_from": not_before}
            )
            finding.discovered_entities.append(cert_entity)
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=f"Cert #{cert_id} ({domain})",
                    source_type="CERTIFICATE",
                    target_value=domain,
                    target_type="DOMAIN",
                    relation_type="CERTIFICATE_FOR",
                    confidence=0.96,
                    evidence_indices=[0]
                )
            )

            # Timeline event
            if not_before:
                try:
                    dt = datetime.fromisoformat(not_before.replace("Z", "+00:00"))
                    finding.timeline_events.append(
                        NormalizedTimelineEvent(
                            timestamp=dt,
                            event_type="CERTIFICATE_ISSUED",
                            title=f"TLS Certificate Issued for {domain}",
                            description=f"Issued by {issuer_name}. Certificate ID {cert_id}.",
                            entity_value=domain,
                            confidence=0.95
                        )
                    )
                except Exception:
                    pass

            # Extract subdomains
            for line in name_value.split("\n"):
                clean_name = line.strip().lower()
                if clean_name.startswith("*."):
                    clean_name = clean_name[2:]
                if clean_name and clean_name != domain and clean_name.endswith(domain):
                    discovered_subdomains.add(clean_name)

        # Add subdomain entities and SUBDOMAIN_OF relationships
        for sub in list(discovered_subdomains)[:50]:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="SUBDOMAIN",
                    value=sub,
                    normalized_value=sub,
                    confidence=0.95,
                    metadata={"parent_domain": domain}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=sub,
                    source_type="SUBDOMAIN",
                    target_value=domain,
                    target_type="DOMAIN",
                    relation_type="SUBDOMAIN_OF",
                    confidence=0.95,
                    evidence_indices=[0]
                )
            )

        return finding
