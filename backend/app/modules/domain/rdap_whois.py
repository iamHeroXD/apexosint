"""RDAP / WHOIS Intelligence Module for APEX OSINT."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
    NormalizedTimelineEvent,
)


class RDAPWhoisModule(BaseOSINTModule):
    name = "rdap_whois"
    display_name = "RDAP / Registry Intelligence"
    description = "Queries authoritative Registration Data Access Protocol (RDAP) endpoints for domain registration and registrar data."
    category = "DOMAIN"
    target_types = ["DOMAIN", "IP"]
    rate_limit = 2.0
    source = "ICANN RDAP Services (rdap.org)"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        value = target_value.lower().strip()

        finding.primary_entity = NormalizedEntity(
            type=target_type,
            value=value,
            normalized_value=value,
            confidence=1.0,
        )

        endpoint_type = "ip" if target_type == "IP" else "domain"
        url = f"https://rdap.org/{endpoint_type}/{value}"

        try:
            client = SafeHTTPClient(timeout=8.0)
            response = await client.get(url, headers={"Accept": "application/rdap+json, application/json"})
            if response.status_code != 200:
                return finding
            data = response.json()
        except Exception:
            return finding

        # Evidence record
        evidence_snippet = f"RDAP record obtained from {data.get('port43', 'RDAP service')} for {value}."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="ICANN RDAP Service",
                source_type="RDAP",
                source_url=url,
                snippet=evidence_snippet,
                collection_method="RDAP_REST_LOOKUP",
                confidence=0.99,
                epistemic_label="OBSERVED",
                raw_payload={"rdap_object": data.get("handle"), "status": data.get("status")},
                related_entity_values=[value]
            )
        )

        # Parse Entities (Registrar, abuse contacts)
        entities_list = data.get("entities", [])
        for ent in entities_list:
            roles = ent.get("roles", [])
            vcard_array = ent.get("vcardArray", [])
            ent_name = None
            ent_email = None

            if len(vcard_array) > 1 and isinstance(vcard_array[1], list):
                for field in vcard_array[1]:
                    if isinstance(field, list) and len(field) > 3:
                        prop_name = field[0]
                        prop_val = field[3]
                        if prop_name == "fn":
                            ent_name = str(prop_val).strip()
                        elif prop_name == "email":
                            ent_email = str(prop_val).strip().lower()

            if "registrar" in roles and ent_name:
                reg_entity = NormalizedEntity(
                    type="ORGANIZATION",
                    value=ent_name,
                    normalized_value=ent_name.lower(),
                    confidence=0.95,
                    metadata={"role": "registrar"}
                )
                finding.discovered_entities.append(reg_entity)
                finding.relationships.append(
                    NormalizedRelationship(
                        source_value=ent_name,
                        source_type="ORGANIZATION",
                        target_value=value,
                        target_type=target_type,
                        relation_type="OWNS" if target_type == "IP" else "ASSOCIATED_WITH",
                        confidence=0.95,
                        evidence_indices=[0]
                    )
                )

            if ent_email:
                finding.discovered_entities.append(
                    NormalizedEntity(
                        type="EMAIL",
                        value=ent_email,
                        normalized_value=ent_email,
                        confidence=0.90,
                        metadata={"role": "rdap_contact", "contact_roles": roles}
                    )
                )

        # Parse Events (Registration, Expiration, Last Changed)
        for ev in data.get("events", []):
            action = ev.get("eventAction")
            date_str = ev.get("eventDate")
            if not date_str:
                continue

            try:
                # Handle ISO 8601 formatting e.g. 2020-05-15T00:00:00Z
                clean_date = date_str.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_date)
            except Exception:
                continue

            event_title = f"{action.capitalize()} of {value}" if action else f"Registry event for {value}"
            finding.timeline_events.append(
                NormalizedTimelineEvent(
                    timestamp=dt,
                    event_type=f"RDAP_{action.upper()}" if action else "RDAP_EVENT",
                    title=event_title,
                    description=f"Recorded by RDAP authority on {date_str}.",
                    entity_value=value,
                    confidence=0.98
                )
            )

        return finding
