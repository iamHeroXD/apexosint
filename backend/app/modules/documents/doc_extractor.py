"""Public Document Intelligence & Metadata Extractor for APEX OSINT."""

import re
from typing import Dict, Any, Set
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)

RE_DOC_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_DOC_URL = re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s\"'<>]*)?")


class DocumentExtractorModule(BaseOSINTModule):
    name = "document_extractor"
    display_name = "Public Document Metadata Extractor"
    description = "Parses publicly hosted documents (PDF, TXT, JSON, CSV, HTML) to extract metadata, authors, emails, and URLs."
    category = "DOCUMENT"
    target_types = ["DOCUMENT", "URL"]
    rate_limit = 2.0
    source = "Public File Endpoints"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        doc_url = target_value.strip()

        finding.primary_entity = NormalizedEntity(
            type="DOCUMENT",
            value=doc_url,
            normalized_value=doc_url.lower(),
            confidence=1.0,
        )

        client = SafeHTTPClient(timeout=10.0)
        try:
            resp = await client.get(doc_url)
            if resp.status_code != 200:
                return finding
            text_content = resp.text
        except Exception:
            return finding

        # Evidence record
        evidence_snippet = f"Analyzed public document at {doc_url} ({len(text_content)} chars)."
        finding.evidence.append(
            NormalizedEvidence(
                source_name="Document Parser",
                source_type="DOCUMENT",
                source_url=doc_url,
                snippet=evidence_snippet,
                collection_method="DOCUMENT_RETRIEVAL",
                confidence=0.95,
                epistemic_label="OBSERVED",
                raw_payload={"url": doc_url, "size_bytes": len(resp.content)},
                related_entity_values=[doc_url]
            )
        )

        # Extract Emails from Document
        emails_found: Set[str] = set()
        for em in RE_DOC_EMAIL.findall(text_content):
            em_clean = em.lower().strip()
            if not any(em_clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
                emails_found.add(em_clean)

        for em in list(emails_found)[:10]:
            finding.discovered_entities.append(
                NormalizedEntity(
                    type="EMAIL",
                    value=em,
                    normalized_value=em,
                    confidence=0.92,
                    metadata={"source_document": doc_url}
                )
            )
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=doc_url,
                    source_type="DOCUMENT",
                    target_value=em,
                    target_type="EMAIL",
                    relation_type="MENTIONS",
                    confidence=0.92,
                    evidence_indices=[0]
                )
            )

        return finding
