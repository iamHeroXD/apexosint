# APEX OSINT

> **Intelligence, connected.**  
> *A local-first, modular, AI-native Open-Source Intelligence & Investigation Platform.*

---

## 1. Overview

**APEX OSINT** is an investigation and defensive reconnaissance platform designed for legitimate security research, threat intelligence, journalists, academic researchers, and defensive security analysts investigating publicly accessible telemetry.

Unlike scripts that generate disconnected outputs, APEX constructs a unified, provenance-backed **Evidence Graph**. Every discovered domain, IP, certificate, mail exchanger, repository, and public username is anchored to verifiable telemetry records with explicit epistemic tiers (`OBSERVED EVIDENCE`, `CORROBORATED`, `AI INFERENCE`, `UNVERIFIED`).

---

## 2. Core Architectural Pillars

- **The Universal Target Engine**: Enter anything into a single universal search box (`domain`, `IP`, `email`, `username`, `phone`, `repository`, `crypto address`, `person`, or multiple targets at once). APEX automatically computes multi-type hypotheses with probabilistic percentages (e.g., `username: 78%`, `person name: 65%`) and constructs a tailored investigation plan.
- **Strict Provenance & Epistemic Labeling**: Every claim stores source, URL, collection method, confidence, raw payload, and timestamp. The AI Copilot is forbidden from inventing evidence—all inferences cite Evidence IDs.
- **Contradiction Detection Engine**: If independent sources disagree (e.g., conflicting incorporation dates or differing registration registries), APEX never silently merges them. It flags `[CONFLICT DETECTED]` with side-by-side citations.
- **Interactive Topological Graph**: Powered by Cytoscape.js with dark terminal styling, physics layouts, neighborhood inspection, confidence sliders, and node filtering.
- **Google Gemini Intelligence Copilot**: Powered by function calling against permission-controlled tools (`resolve_dns`, `lookup_rdap`, `inspect_certificate`, `search_username`, `search_public_email`, `query_investigation_evidence`, `find_contradictions`). Operates in multiple specialized modes (`INVESTIGATOR`, `ANALYST`, `CORRELATOR`, `VERIFIER`, `REPORTER`, `SUMMARIZER`).
- **Local-First & Offline Demo Sandbox**: Operates 100% locally on `127.0.0.1`. Includes a 1-click synthetic demo dataset for "Apex Demo Corporation" (`apex-defense.org`) enabling instant exploration without external network calls.
- **Defensive SSRF Protection**: Safe HTTP client with strict blocking of RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`), link-local / AWS metadata (`169.254.169.254`), DNS rebinding mitigation, payload truncation (5MB cap), and secret redaction.

---

## 3. System Architecture

```
User / Analyst
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  React 18 + TypeScript + Tailwind UI (or CLI tool)     │
└────────────────────────────────────────────────────────┘
      │
      ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI Async REST & Server-Sent Events (SSE) Stream  │
└────────────────────────────────────────────────────────┘
      │
      ├───────────────────────┬──────────────────────────┐
      ▼                       ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Universal Target │    │ OSINT Module     │    │ Gemini Copilot   │
│ Engine           │    │ Plugin Registry  │    │ Function Calling │
└──────────────────┘    └──────────────────┘    └──────────────────┘
      │                       │                          │
      │  ┌────────────────────┴────────────────────┐     │
      ▼  ▼                                         ▼     ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Data Normalizer  │───>│ Deterministic    │───>│ Contradiction &  │
│ & Provenance     │    │ Rule Correlation │    │ Conflict Guard   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │ SQLite / PostgreSQL  │
                        │ SQLAlchemy Models    │
                        └──────────────────────┘
```

---

## 4. Quickstart

### Option A: One-Command Scripts (No Docker Required)

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Windows (Command Prompt):**
```cmd
start.bat
```

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

The application will be accessible at:
- **Web UI:** [http://127.0.0.1:5173](http://127.0.0.1:5173) (or [http://127.0.0.1:8000](http://127.0.0.1:8000))
- **OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Option B: Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

---

## 5. APEX Command-Line Interface (`apex`)

The CLI uses the exact same core engine as the GUI:

```bash
# Run system diagnostics
python apex.py doctor

# Test the Universal Target Engine on any input
python apex.py target "johnsmith"

# Test compound multi-target queries
python apex.py target "johnsmith, sec-ops@defense.gov, 8.8.8.8, apex-defense.org"

# List registered OSINT modules & health
python apex.py modules

# Launch an investigation directly from terminal
python apex.py scan "apex-defense.org" --mode standard --depth 1
```

---

## 6. Supported Target Types

| Target Type | Detection Heuristics | Primary Intelligence Collected |
|:---|:---|:---|
| `DOMAIN` | FQDN regex | DNS (A, AAAA, MX, NS, TXT, SPF, DMARC), RDAP registrar, TLS Certificate Transparency (crt.sh), security.txt, robots.txt |
| `SUBDOMAIN` | Deep hierarchy FQDN | Host routing, parent domain association, certificates |
| `IP ADDRESS` | IPv4 & IPv6 validation | BGP ASN, hosting provider/ISP, coarse geolocation (country, city), reverse DNS (PTR) |
| `ASN` | AS number prefix | Routing prefixes, autonomous system organization |
| `EMAIL` | RFC 5322 validation | Domain deliverability, MX servers, SPF/DMARC flags, Gravatar public avatar presence |
| `USERNAME` | Alphanumeric handle / `@handle` | Multi-platform discovery (GitHub, GitLab, Reddit, HackerNews, Keybase, Medium, Dev.to, DockerHub, Kaggle) |
| `PERSON` | Multi-word human name | Disambiguation clusters (`cluster_id`), public author metadata |
| `ORGANIZATION` | Corporate keywords (`Inc`, `Corp`, `Technologies`) | Associated domains, infrastructure mapping, legal filings |
| `REPOSITORY` | GitHub URL or `owner/repo` | Commit authors, languages, stars, dependencies, credential exposure scanner |
| `PHONE NUMBER` | E.164 digits pattern | Standardized representation, lawful public country/carrier metadata |
| `CRYPTO ADDRESS`| Bitcoin & Ethereum patterns | Public ledger address format identification |

---

## 7. OSINT Module Plugin Development

To build a custom collector, create a subclass of `BaseOSINTModule`:

```python
from app.modules.base import BaseOSINTModule, NormalizedFinding, NormalizedEntity, NormalizedEvidence

class CustomLookupModule(BaseOSINTModule):
    name = "custom_lookup"
    display_name = "Custom Public Lookup"
    description = "Queries a custom public registry"
    category = "DOMAIN"
    target_types = ["DOMAIN"]
    rate_limit = 2.0
    source = "Custom Public Source"

    async def collect(self, target_value: str, target_type: str, context: dict) -> NormalizedFinding:
        finding = NormalizedFinding()
        finding.primary_entity = NormalizedEntity(
            type="DOMAIN",
            value=target_value,
            normalized_value=target_value.lower()
        )
        finding.evidence.append(NormalizedEvidence(
            source_name="Custom Source",
            source_type="PUBLIC_REGISTRY",
            snippet=f"Telemetry collected for {target_value}",
            epistemic_label="OBSERVED"
        ))
        return finding
```

Register it in `app.modules.registry`:
```python
from app.modules.registry import module_registry
module_registry.register(CustomLookupModule())
```

---

## 8. Safety, Security & Ethical Boundaries

APEX OSINT strictly adheres to defensive and lawful intelligence boundaries:
- **No Credential Harvesting or Theft**: Never collects passwords, session cookies, or private credentials.
- **Secret Redaction**: Commit messages and documents containing tokens (API keys, AWS keys, GitHub tokens) are automatically flagged with `[POTENTIAL SECRET EXPOSURE: <TYPE> REDACTED]` and masked.
- **SSRF Defense**: Enforces loopback and RFC 1918 private network blocking, DNS rebinding guards, and 5MB payload caps.
- **Coarse Geolocation Only**: Geolocation metadata is limited to country and city granularity. Personal tracking is prohibited.

---

## 9. Running Tests

```bash
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest backend\tests
```

All tests verify SSRF blocking, target parsing, data normalization, and demo dataset integrity.
