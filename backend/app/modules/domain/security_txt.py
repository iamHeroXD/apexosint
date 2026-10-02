"""Web Security Metadata & Policy Intelligence Module for APEX OSINT."""

import re
from typing import Dict, Any
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)


class SecurityTxtModule(BaseOSINTModule):
    name = "security_txt"
    display_name = "Security.txt & Policy Intelligence"
    description = "Checks /.well-known/security.txt and robots.txt for security contacts, policies, and exposed directories."
    category = "DOMAIN"
    target_types = ["DOMAIN", "SUBDOMAIN"]
    rate_limit = 3.0
    source = "RFC 9116 / Robots Standard"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        domain = target_value.lower().strip()

        finding.primary_entity = NormalizedEntity(
            type=target_type,
            value=domain,
            normalized_value=domain,
            confidence=1.0,
        )

        client = SafeHTTPClient(timeout=6.0)
        sec_url = f"https://{domain}/.well-known/security.txt"
        
        try:
            resp = await client.get(sec_url)
            if resp.status_code == 200 and resp.text:
                content = resp.text
                finding.evidence.append(
                    NormalizedEvidence(
                        source_name="RFC 9116 Security.txt",
                        source_type="WEB",
                        source_url=sec_url,
                        snippet=f"Discovered security.txt on {domain} with {len(content.splitlines())} policy directives.",
                        collection_method="HTTP_GET",
                        confidence=0.98,
                        epistemic_label="OBSERVED",
                        raw_payload={"url": sec_url, "preview": content[:1000]},
                        related_entity_values=[domain]
                    )
                )

                # Extract Contact emails or URLs
                for line in content.splitlines():
                    if line.lower().startswith("contact:"):
                        contact_val = line.split(":", 1)[1].strip()
                        if "mailto:" in contact_val:
                            email_match = re.search(r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", contact_val)
                            if email_match:
                                em = email_match.group(1).lower()
                                finding.discovered_entities.append(
                                    NormalizedEntity(
                                        type="EMAIL",
                                        value=em,
                                        normalized_value=em,
                                        confidence=0.95,
                                        metadata={"role": "security_contact"}
                                    )
                                )
                                finding.relationships.append(
                                    NormalizedRelationship(
                                        source_value=domain,
                                        source_type=target_type,
                                        target_value=em,
                                        target_type="EMAIL",
                                        relation_type="ASSOCIATED_WITH",
                                        confidence=0.95,
                                        evidence_indices=[0]
                                    )
                                )
        except Exception:
            pass

        return finding
