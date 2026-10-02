"""Universal Target Detection & Normalization Engine for APEX OSINT.

Analyzes raw user input, handles multi-target inputs, normalizes values,
computes multi-type hypotheses with probabilistic confidence scores,
and suggests an investigation plan without forcing the user to pick a category.
"""

import ipaddress
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# Regular expressions for detection
RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
RE_DOMAIN = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
RE_PHONE = re.compile(r"^\+?[0-9\s\-().]{7,25}$")
RE_GITHUB_REPO = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/?$")
RE_GITHUB_USER = re.compile(r"^(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/?$")
RE_SOCIAL_URL = re.compile(r"^(?:https?://)?(?:www\.)?(?:twitter|x|linkedin|facebook|instagram|reddit|youtube)\.com/([a-zA-Z0-9_.-]+)/?$")
RE_BITCOIN = re.compile(r"^(?:1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})$")
RE_ETHEREUM = re.compile(r"^0x[a-fA-F0-9]{40}$")
RE_ASN = re.compile(r"^(?:AS|asn)?([0-9]{1,8})$", re.IGNORECASE)
RE_USERNAME_HANDLE = re.compile(r"^@?([a-zA-Z0-9_.-]{3,32})$")


class TargetHypothesis:
    def __init__(self, target_type: str, confidence: float, explanation: str, recommended_modules: List[str]):
        self.target_type = target_type
        self.confidence = confidence
        self.explanation = explanation
        self.recommended_modules = recommended_modules

    @property
    def percentage(self) -> int:
        return int(round(self.confidence * 100))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.target_type,
            "confidence": round(self.confidence, 2),
            "percentage": self.percentage,
            "explanation": self.explanation,
            "recommended_modules": self.recommended_modules,
        }


class AnalyzedTarget:
    def __init__(
        self,
        raw_input: str,
        normalized_value: str,
        primary_type: str,
        primary_confidence: float,
        hypotheses: List[TargetHypothesis],
        extraction_metadata: Optional[Dict[str, Any]] = None
    ):
        self.raw_input = raw_input
        self.normalized_value = normalized_value
        self.primary_type = primary_type
        self.primary_confidence = primary_confidence
        self.hypotheses = hypotheses
        self.extraction_metadata = extraction_metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_input": self.raw_input,
            "normalized_value": self.normalized_value,
            "primary_type": self.primary_type,
            "primary_confidence": round(self.primary_confidence, 2),
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "planned_investigation": self._build_investigation_plan(),
            "extraction_metadata": self.extraction_metadata,
        }

    def _build_investigation_plan(self) -> List[str]:
        """Aggregate recommended steps across high-confidence hypotheses."""
        all_modules = []
        for h in self.hypotheses:
            if h.confidence >= 0.4:
                all_modules.extend(h.recommended_modules)
        # Unique preserving order
        seen = set()
        plan = []
        for mod in all_modules:
            if mod not in seen:
                seen.add(mod)
                plan.append(mod)
        return plan


class UniversalTargetEngine:
    """Universal parser, classifier, and disambiguator for target inputs."""

    @classmethod
    def split_multiple_inputs(cls, text: str) -> List[str]:
        """Split combined inputs by commas, semicolons, or newlines while preserving phrases."""
        if not text:
            return []
        
        # Split on newlines, semicolons, or commas (unless enclosed in quotes)
        tokens = re.split(r"[\r\n,;]+", text)
        cleaned = [t.strip().strip("'\"") for t in tokens if t.strip()]
        return cleaned if cleaned else [text.strip()]

    @classmethod
    def analyze_input(cls, raw: str) -> AnalyzedTarget:
        """Analyze a single raw input string and produce ranked hypotheses."""
        cleaned = raw.strip()
        
        # 1. URL Check
        if cleaned.startswith(("http://", "https://")):
            return cls._analyze_url(cleaned)

        # 2. GitHub Repo Shorthand (e.g. user/repo)
        github_match = RE_GITHUB_REPO.match(cleaned)
        if github_match:
            u, r = github_match.groups()
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=f"{u}/{r}",
                primary_type="REPOSITORY",
                primary_confidence=0.98,
                hypotheses=[
                    TargetHypothesis("REPOSITORY", 0.98, "GitHub public code repository", ["github_repo_analyzer", "github_secrets_scan"]),
                    TargetHypothesis("URL", 0.85, "Web accessible repository URL", ["web_scraper"]),
                ],
                extraction_metadata={"platform": "github", "owner": u, "repo": r}
            )

        # 3. IP Address Check
        try:
            ip_obj = ipaddress.ip_address(cleaned)
            is_v6 = isinstance(ip_obj, ipaddress.IPv6Address)
            norm_ip = str(ip_obj)
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=norm_ip,
                primary_type="IP",
                primary_confidence=0.99,
                hypotheses=[
                    TargetHypothesis("IP", 0.99, f"Valid IPv{'6' if is_v6 else '4'} public address", ["ip_geo_asn", "reverse_dns"]),
                ],
                extraction_metadata={"is_ipv6": is_v6}
            )
        except ValueError:
            pass

        # 4. Email Address Check
        if RE_EMAIL.match(cleaned):
            norm_email = cleaned.lower()
            domain_part = norm_email.split("@")[1]
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=norm_email,
                primary_type="EMAIL",
                primary_confidence=0.99,
                hypotheses=[
                    TargetHypothesis("EMAIL", 0.99, "RFC-compliant email address", ["email_analyzer", "email_breach_metadata"]),
                    TargetHypothesis("DOMAIN", 0.70, f"Parent domain {domain_part}", ["dns_records", "rdap_whois"]),
                ],
                extraction_metadata={"domain": domain_part}
            )

        # 5. Cryptocurrency Address Check
        if RE_BITCOIN.match(cleaned):
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=cleaned,
                primary_type="BITCOIN_ADDRESS",
                primary_confidence=0.98,
                hypotheses=[
                    TargetHypothesis("BITCOIN_ADDRESS", 0.98, "Bitcoin public ledger address", ["crypto_public_ledger"]),
                ]
            )
        if RE_ETHEREUM.match(cleaned):
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=cleaned.lower(),
                primary_type="CRYPTO_ADDRESS",
                primary_confidence=0.98,
                hypotheses=[
                    TargetHypothesis("CRYPTO_ADDRESS", 0.98, "Ethereum / EVM public address", ["crypto_public_ledger"]),
                ]
            )

        # 6. ASN Check
        asn_match = RE_ASN.match(cleaned)
        if asn_match and cleaned.upper().startswith("AS"):
            asn_num = f"AS{asn_match.group(1)}"
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=asn_num,
                primary_type="ASN",
                primary_confidence=0.95,
                hypotheses=[
                    TargetHypothesis("ASN", 0.95, "Autonomous System Number", ["ip_geo_asn"]),
                ]
            )

        # 7. Phone Number Check
        cleaned_digits = re.sub(r"[^\d+]", "", cleaned)
        if (cleaned.startswith("+") or len(cleaned_digits) >= 10) and RE_PHONE.match(cleaned):
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=cleaned_digits,
                primary_type="PHONE",
                primary_confidence=0.92,
                hypotheses=[
                    TargetHypothesis("PHONE", 0.92, "Standardized telephone number", ["phone_analyzer"]),
                ],
                extraction_metadata={"digits_only": cleaned_digits}
            )

        # 8. Domain Check
        if RE_DOMAIN.match(cleaned):
            norm_dom = cleaned.lower()
            is_sub = len(norm_dom.split(".")) > 2
            p_type = "SUBDOMAIN" if is_sub else "DOMAIN"
            return AnalyzedTarget(
                raw_input=cleaned,
                normalized_value=norm_dom,
                primary_type=p_type,
                primary_confidence=0.97,
                hypotheses=[
                    TargetHypothesis(p_type, 0.97, "Internet domain name", ["dns_records", "rdap_whois", "cert_transparency", "security_txt", "tech_stack"]),
                    TargetHypothesis("URL", 0.65, f"Root web endpoint https://{norm_dom}", ["web_scraper"]),
                ]
            )

        # 9. Multi-type Hypotheses: Names, Usernames, Organizations
        hypotheses = []
        norm_val = cleaned.strip("@")

        # Username hypothesis
        has_digits = any(c.isdigit() for c in norm_val)
        has_spaces = " " in cleaned
        word_count = len(cleaned.split())

        if not has_spaces and len(norm_val) >= 3:
            user_conf = 0.91 if has_digits or cleaned.startswith("@") else 0.78
            hypotheses.append(
                TargetHypothesis(
                    "USERNAME",
                    user_conf,
                    "Public account handle across platforms",
                    ["username_profile_finder", "github_repo_analyzer"]
                )
            )

        # Person Name hypothesis
        if word_count in (2, 3) and not has_digits:
            hypotheses.append(
                TargetHypothesis(
                    "PERSON",
                    0.88,
                    "Full person name (possible ambiguity, clustering enabled)",
                    ["person_public_web", "document_extractor"]
                )
            )
        elif not has_spaces and len(norm_val) >= 4 and not has_digits:
            hypotheses.append(
                TargetHypothesis(
                    "PERSON",
                    0.65,
                    "Mononym or given name",
                    ["person_public_web"]
                )
            )

        # Organization hypothesis
        org_indicators = ["corp", "inc", "ltd", "technologies", "tech", "group", "labs", "security", "defense", "systems", "foundation", "holdings"]
        cleaned_lower = cleaned.lower()
        if any(ind in cleaned_lower for ind in org_indicators):
            hypotheses.append(
                TargetHypothesis(
                    "ORGANIZATION",
                    0.92,
                    "Corporate or organizational entity",
                    ["org_public_sources", "web_scraper", "cert_transparency"]
                )
            )
        else:
            hypotheses.append(
                TargetHypothesis(
                    "ORGANIZATION",
                    0.25 if not has_spaces else 0.55,
                    "Potential organizational title",
                    ["org_public_sources"]
                )
            )

        # Sort hypotheses by confidence descending
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        primary = hypotheses[0]

        return AnalyzedTarget(
            raw_input=cleaned,
            normalized_value=norm_val,
            primary_type=primary.target_type,
            primary_confidence=primary.confidence,
            hypotheses=hypotheses
        )

    @classmethod
    def _analyze_url(cls, url: str) -> AnalyzedTarget:
        """Analyze a web URL and extract subcomponents."""
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        path = parsed.path or ""

        # Check for GitHub repo URL
        gh_match = RE_GITHUB_REPO.match(url)
        if gh_match:
            u, r = gh_match.groups()
            return AnalyzedTarget(
                raw_input=url,
                normalized_value=f"{u}/{r}",
                primary_type="REPOSITORY",
                primary_confidence=0.99,
                hypotheses=[
                    TargetHypothesis("REPOSITORY", 0.99, "Public GitHub repository", ["github_repo_analyzer", "github_secrets_scan"]),
                    TargetHypothesis("URL", 0.85, "Web accessible page", ["web_scraper"]),
                ],
                extraction_metadata={"platform": "github", "owner": u, "repo": r}
            )

        # Check for document URL (.pdf, .docx, .txt, .json, .csv)
        if any(path.lower().endswith(ext) for ext in [".pdf", ".docx", ".txt", ".json", ".csv"]):
            doc_ext = path.split(".")[-1].lower()
            return AnalyzedTarget(
                raw_input=url,
                normalized_value=url,
                primary_type="DOCUMENT",
                primary_confidence=0.96,
                hypotheses=[
                    TargetHypothesis("DOCUMENT", 0.96, f"Publicly accessible {doc_ext.upper()} document", ["document_extractor"]),
                    TargetHypothesis("DOMAIN", 0.70, f"Hosting domain {domain}", ["dns_records"]),
                ],
                extraction_metadata={"extension": doc_ext, "domain": domain}
            )

        return AnalyzedTarget(
            raw_input=url,
            normalized_value=url,
            primary_type="URL",
            primary_confidence=0.95,
            hypotheses=[
                TargetHypothesis("URL", 0.95, "Public web URL endpoint", ["web_scraper"]),
                TargetHypothesis("DOMAIN", 0.85, f"Host domain {domain}", ["dns_records", "rdap_whois"]),
            ],
            extraction_metadata={"domain": domain, "path": path}
        )

    @classmethod
    def process_universal_query(cls, query: str) -> List[AnalyzedTarget]:
        """Entry point for universal query. Splits multiple inputs and analyzes each."""
        items = cls.split_multiple_inputs(query)
        results = [cls.analyze_input(item) for item in items if item]
        return results
