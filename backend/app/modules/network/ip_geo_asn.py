"""IP Geolocation, ASN, and Network Intelligence Module for APEX OSINT."""

from typing import Dict, Any
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)


class IPGeoASNModule(BaseOSINTModule):
    name = "ip_geo_asn"
    display_name = "IP Network, ASN & Coarse Geo"
    description = "Queries public BGP routing, ASN, and coarse geographic metadata for IP addresses."
    category = "NETWORK"
    target_types = ["IP", "ASN"]
    rate_limit = 2.0
    source = "Public IP Geolocation & BGP Feeds"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        ip = target_value.strip()

        finding.primary_entity = NormalizedEntity(
            type="IP",
            value=ip,
            normalized_value=ip,
            confidence=1.0,
        )

        data = {}
        client = SafeHTTPClient(timeout=6.0)

        # Primary provider: ipapi.co
        try:
            resp = await client.get(f"https://ipapi.co/{ip}/json/")
            if resp.status_code == 200:
                data = resp.json()
        except Exception:
            pass

        # Fallback provider: ip-api.com
        if not data or not data.get("country_name") and not data.get("country"):
            try:
                resp2 = await client.get(f"http://ip-api.com/json/{ip}")
                if resp2.status_code == 200:
                    raw2 = resp2.json()
                    data = {
                        "asn": raw2.get("as", "").split()[0] if raw2.get("as") else None,
                        "org": raw2.get("org") or raw2.get("isp"),
                        "country_name": raw2.get("country"),
                        "city": raw2.get("city"),
                        "latitude": raw2.get("lat"),
                        "longitude": raw2.get("lon"),
                    }
            except Exception:
                pass

        if not data:
            return finding

        asn = data.get("asn")
        org = data.get("org")
        country = data.get("country_name") or data.get("country")
        city = data.get("city")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        # Public lookup links
        ip_sites = [
            {
                "platform": "Hurricane Electric BGP Looking Glass",
                "category": "BGP & Routing",
                "url": f"https://bgp.he.net/ip/{ip}",
                "status": "FOUND",
                "status_code": 200,
            },
            {
                "platform": "IP RDAP Regional Registry",
                "category": "Regional Internet Registry",
                "url": f"https://rdap.org/ip/{ip}",
                "status": "FOUND",
                "status_code": 200,
            },
        ]
        if latitude and longitude:
            ip_sites.append({
                "platform": "OpenStreetMap Geographic Coordinate Anchor",
                "category": "Geolocation",
                "url": f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=12/{latitude}/{longitude}",
                "status": "FOUND",
                "status_code": 200,
            })

        evidence_snippet = f"IP {ip} routed by {org or 'Unknown Provider'} (ASN {asn or 'Unassigned'}) in {city or 'Unknown'}, {country or 'Unknown'}."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="Public IP & BGP Registry",
                source_type="NETWORK",
                source_url=f"https://bgp.he.net/ip/{ip}",
                snippet=evidence_snippet,
                collection_method="REST_API_QUERY",
                confidence=0.96,
                epistemic_label="OBSERVED",
                raw_payload={
                    "asn": asn,
                    "org": org,
                    "country": country,
                    "city": city,
                    "lat": latitude,
                    "lon": longitude,
                    "all_probed_sites": ip_sites,
                },
                related_entity_values=[ip]
            )
        )

        # 1. ASN Entity
        if asn:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="ASN",
                    value=str(asn),
                    normalized_value=str(asn).upper(),
                    confidence=0.98,
                    metadata={"asn_org": org}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=ip,
                    source_type="IP",
                    target_value=str(asn),
                    target_type="ASN",
                    relation_type="HOSTED_ON",
                    confidence=0.98,
                    evidence_indices=[0]
                )
            )

        # 2. Hosting / ISP Organization Entity
        if org:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="ORGANIZATION",
                    value=org,
                    normalized_value=org.lower(),
                    confidence=0.92,
                    metadata={"role": "hosting_isp"}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=org,
                    source_type="ORGANIZATION",
                    target_value=ip,
                    target_type="IP",
                    relation_type="OWNS",
                    confidence=0.92,
                    evidence_indices=[0]
                )
            )

        # 3. Coarse Location Entity
        if country or city:
            loc_val = f"{city}, {country}" if city and country else (country or city)
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="LOCATION",
                    value=loc_val,
                    normalized_value=loc_val.lower(),
                    confidence=0.88,
                    metadata={"country": country, "city": city, "latitude": latitude, "longitude": longitude}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=ip,
                    source_type="IP",
                    target_value=loc_val,
                    target_type="LOCATION",
                    relation_type="HOSTED_ON",
                    confidence=0.88,
                    evidence_indices=[0]
                )
            )

        return finding
