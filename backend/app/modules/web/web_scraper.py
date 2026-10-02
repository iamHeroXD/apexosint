"""Public Web Intelligence & Metadata Scraper for APEX OSINT."""

import re
from typing import Dict, Any, Set
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)

RE_EMAIL_FIND = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_SOCIAL_LINKS = re.compile(r"https?://(?:www\.)?(?:github\.com|twitter\.com|x\.com|linkedin\.com/company|linkedin\.com/in|youtube\.com)/[A-Za-z0-9_.-]+")


class WebScraperModule(BaseOSINTModule):
    name = "web_scraper"
    display_name = "Public Web & Metadata Harvester"
    description = "Safely fetches public web documents to extract titles, metadata, OpenGraph attributes, outbound links, and contact identifiers."
    category = "WEB"
    target_types = ["URL", "DOMAIN"]
    rate_limit = 2.0
    source = "Public Web Documents"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        url = target_value if target_value.startswith(("http://", "https://")) else f"https://{target_value}"
        parsed = urlparse(url)
        domain = parsed.hostname or target_value

        finding.primary_entity = NormalizedEntity(
            type="URL" if target_type == "URL" else "DOMAIN",
            value=url if target_type == "URL" else domain,
            normalized_value=url.lower() if target_type == "URL" else domain.lower(),
            confidence=1.0,
        )

        client = SafeHTTPClient(timeout=8.0)
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return finding
            html_text = resp.text
        except Exception:
            return finding

        soup = BeautifulSoup(html_text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()

        # Evidence record
        evidence_snippet = f"Fetched public web page at {url}. Title: '{title[:80]}'. Description: '{meta_desc[:120]}'."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="Public Web Crawler",
                source_type="WEB",
                source_url=url,
                snippet=evidence_snippet,
                collection_method="HTTP_GET",
                confidence=0.95,
                epistemic_label="OBSERVED",
                raw_payload={"title": title, "description": meta_desc, "status_code": resp.status_code},
                related_entity_values=[domain]
            )
        )

        # Extract Emails
        found_emails: Set[str] = set()
        for em in RE_EMAIL_FIND.findall(html_text):
            lower_em = em.lower().strip()
            # Filter common image extensions falsely matched
            if not any(lower_em.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"]):
                found_emails.add(lower_em)

        for em in list(found_emails)[:10]:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="EMAIL",
                    value=em,
                    normalized_value=em,
                    confidence=0.92,
                    metadata={"source_page": url}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=domain,
                    source_type="DOMAIN",
                    target_value=em,
                    target_type="EMAIL",
                    relation_type="MENTIONS",
                    confidence=0.92,
                    evidence_indices=[0]
                )
            )

        # Extract Social profile links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if RE_SOCIAL_LINKS.match(href):
                finding.discovered_entities.append(
                    NormalizedEntity(
                        type="SOCIAL_PROFILE",
                        value=href,
                        normalized_value=href.lower(),
                        confidence=0.90,
                        metadata={"origin": url}
                    )
                )
                finding.relationships.append(
                    NormalizedRelationship(
                        source_value=domain,
                        source_type="DOMAIN",
                        target_value=href,
                        target_type="SOCIAL_PROFILE",
                        relation_type="LINKS_TO",
                        confidence=0.90,
                        evidence_indices=[0]
                    )
                )

        return finding
