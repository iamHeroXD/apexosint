"""Reverse DNS Intelligence Module for APEX OSINT."""

from typing import Dict, Any
import dns.asyncresolver
import dns.reversename
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)


class ReverseDNSModule(BaseOSINTModule):
    name = "reverse_dns"
    display_name = "Reverse DNS (PTR)"
    description = "Resolves PTR records for IP addresses to uncover associated hostnames and reverse domains."
    category = "NETWORK"
    target_types = ["IP"]
    rate_limit = 5.0
    source = "Public DNS In-Addr/IP6 Arpa Resolvers"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        ip = target_value.strip()

        finding.primary_entity = NormalizedEntity(
            type="IP",
            value=ip,
            normalized_value=ip,
            confidence=1.0,
        )

        try:
            rev_name = dns.reversename.from_address(ip)
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = 3.0
            resolver.lifetime = 4.0
            answers = await resolver.resolve(rev_name, "PTR")
            hostnames = [str(r).rstrip(".").lower() for r in answers]
        except Exception:
            return finding

        if not hostnames:
            return finding

        evidence_snippet = f"Reverse DNS lookup for {ip} resolved {len(hostnames)} PTR hostname(s): {', '.join(hostnames[:3])}."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="DNS PTR Resolver",
                source_type="DNS",
                source_url=f"dns://{rev_name}",
                snippet=evidence_snippet,
                collection_method="DNS_PTR_QUERY",
                confidence=0.98,
                epistemic_label="OBSERVED",
                raw_payload={"ip": ip, "ptr_hostnames": hostnames},
                related_entity_values=[ip]
            )
        )

        for host in hostnames:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="DOMAIN",
                    value=host,
                    normalized_value=host,
                    confidence=0.97,
                    metadata={"source": "PTR"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=host,
                    source_type="DOMAIN",
                    target_value=ip,
                    target_type="IP",
                    relation_type="RESOLVES_TO",
                    confidence=0.97,
                    evidence_indices=[0]
                )
            )

        return finding
