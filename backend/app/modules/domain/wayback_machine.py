"""Wayback Machine / Internet Archive CDX Passive Intelligence Module.
Performs passive discovery of historical subdomains, endpoints, and archived documents.
Leaves zero trace on target infrastructure because all queries go to the Internet Archive.
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse
import httpx
from app.modules.base import BaseOSINTModule, NormalizedFinding

logger = logging.getLogger("apex.modules.wayback")


class WaybackMachineModule(BaseOSINTModule):
    """Passive Internet Archive CDX Intelligence Collector."""

    name = "wayback_archive"
    display_name = "Wayback Machine Passive Archive Scout"
    description = "Queries the public Internet Archive CDX server to passively discover historical subdomains, documents, and endpoints without contacting the target."
    category = "Infrastructure"
    target_types = ["DOMAIN", "SUBDOMAIN"]
    rate_limit = 20
    source = "web.archive.org (CDX Server API)"
    license = "Public Domain"

    def can_handle(self, target_type: str, target_value: str) -> bool:
        return target_type in ("DOMAIN", "SUBDOMAIN")

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        domain = target_value.lower().strip()

        cdx_url = (
            f"https://web.archive.org/cdx/search/cdx?"
            f"url=*.{domain}/*&output=json&fl=original,mimetype,statuscode&limit=40&collapse=urlkey"
        )

        discovered_subdomains = set()
        interesting_endpoints = []

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(cdx_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code == 200:
                    data = resp.json()
                    # Skip header row [original, mimetype, statuscode]
                    if len(data) > 1:
                        for row in data[1:]:
                            orig_url = row[0]
                            parsed = urlparse(orig_url)
                            hostname = parsed.hostname
                            if hostname and hostname.endswith(domain) and hostname != domain:
                                discovered_subdomains.add(hostname)

                            mimetype = row[1] if len(row) > 1 else ""
                            if any(ext in orig_url.lower() for ext in (".pdf", ".doc", ".xls", ".env", ".git", ".json", "api", "admin")):
                                interesting_endpoints.append(orig_url)

        except Exception as e:
            logger.debug("Wayback CDX lookup error for %s: %s", domain, e)

        # Add discovered subdomains
        for sub in list(discovered_subdomains)[:12]:
            finding.add_entity("SUBDOMAIN", sub, confidence=0.90, provenance="OBSERVED")
            finding.add_relationship(
                source_type="DOMAIN",
                source_value=domain,
                target_type="SUBDOMAIN",
                target_value=sub,
                relation_type="HAS_HISTORICAL_HOST",
                confidence=0.88
            )

        if discovered_subdomains or interesting_endpoints:
            finding.add_evidence(
                source_name="Internet Archive (Wayback Machine CDX)",
                source_type="PUBLIC_ARCHIVE",
                source_url=f"https://web.archive.org/web/*/{domain}",
                snippet=(
                    f"Passive historical footprint: {len(discovered_subdomains)} subdomains observed: "
                    f"{', '.join(list(discovered_subdomains)[:6])}. {len(interesting_endpoints)} documents/endpoints indexed."
                ),
                raw_payload={
                    "subdomains": list(discovered_subdomains),
                    "interesting_endpoints": interesting_endpoints[:15],
                },
                confidence=0.92,
                epistemic_label="OBSERVED"
            )

        return finding
