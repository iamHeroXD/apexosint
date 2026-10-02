"""DNS Intelligence Module for APEX OSINT."""

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import dns.asyncresolver
import dns.resolver
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
    NormalizedTimelineEvent,
)


class DNSRecordsModule(BaseOSINTModule):
    name = "dns_records"
    display_name = "DNS Intelligence"
    description = "Queries authoritative DNS records: A, AAAA, MX, TXT, SPF, DMARC, NS, CNAME, SOA."
    category = "DOMAIN"
    target_types = ["DOMAIN", "SUBDOMAIN"]
    rate_limit = 5.0
    source = "Public Recursive DNS Resolvers"

    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        domain = target_value.lower().strip()

        finding.primary_entity = NormalizedEntity(
            type=target_type,
            value=domain,
            normalized_value=domain,
            confidence=1.0,
            metadata={"domain": domain}
        )

        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 4.0
        resolver.lifetime = 5.0
        # Public DNS providers fallback (Cloudflare, Google, Quad9)
        resolver.nameservers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]

        raw_records: Dict[str, List[str]] = {}

        async def query_rtype(rtype: str):
            try:
                answers = await resolver.resolve(domain, rtype)
                raw_records[rtype] = [str(rdata) for rdata in answers]
            except Exception:
                raw_records[rtype] = []

        await asyncio.gather(*(query_rtype(rt) for rt in self.RECORD_TYPES))

        total_count = sum(len(v) for v in raw_records.values())
        if total_count == 0:
            return finding

        # Evidence entry
        dns_snippet = f"Resolved {total_count} DNS records for {domain} across {len(self.RECORD_TYPES)} query types."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="Public DNS Resolver",
                source_type="DNS",
                source_url=f"dns://{domain}",
                snippet=dns_snippet,
                collection_method="DNS_RECURSIVE_QUERY",
                confidence=0.98,
                epistemic_label="OBSERVED",
                raw_payload={"domain": domain, "records": raw_records},
                related_entity_values=[domain]
            )
        )

        # Process A / AAAA -> IP entities and HOSTED_ON / RESOLVES_TO edges
        for ip in raw_records.get("A", []) + raw_records.get("AAAA", []):
            clean_ip = ip.strip()
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="IP",
                    value=clean_ip,
                    normalized_value=clean_ip,
                    confidence=0.98,
                    metadata={"record_type": "A/AAAA"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=domain,
                    source_type=target_type,
                    target_value=clean_ip,
                    target_type="IP",
                    relation_type="RESOLVES_TO",
                    confidence=0.98,
                    evidence_indices=[0]
                )
            )

        # Process MX records -> Mail servers
        for mx in raw_records.get("MX", []):
            parts = mx.strip().split()
            mx_host = parts[-1].rstrip(".").lower()
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="DOMAIN",
                    value=mx_host,
                    normalized_value=mx_host,
                    confidence=0.95,
                    metadata={"role": "mail_exchanger", "priority": parts[0] if len(parts) > 1 else "10"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=domain,
                    source_type=target_type,
                    target_value=mx_host,
                    target_type="DOMAIN",
                    relation_type="ASSOCIATED_WITH",
                    confidence=0.95,
                    evidence_indices=[0]
                )
            )

        # Process NS records -> Name servers
        for ns in raw_records.get("NS", []):
            ns_host = ns.strip().rstrip(".").lower()
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="DOMAIN",
                    value=ns_host,
                    normalized_value=ns_host,
                    confidence=0.95,
                    metadata={"role": "nameserver"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=domain,
                    source_type=target_type,
                    target_value=ns_host,
                    target_type="DOMAIN",
                    relation_type="HOSTED_ON",
                    confidence=0.95,
                    evidence_indices=[0]
                )
            )

        # Process TXT records (SPF, DMARC, verification tokens)
        for txt in raw_records.get("TXT", []):
            clean_txt = txt.strip(' "')
            if "v=spf1" in clean_txt.lower():
                finding.primary_entity.metadata["spf_record"] = clean_txt
            elif "google-site-verification" in clean_txt.lower():
                finding.primary_entity.metadata["google_verified"] = True

        return finding
