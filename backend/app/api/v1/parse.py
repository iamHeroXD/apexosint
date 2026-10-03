"""Natural Language Query Parser — APEX OSINT.

Accepts free-form sentences like:
  "his name is John Smith, lives in Kochi, phone +91 9846 123456, email john@gmail.com"
Uses Gemini AI to extract all structured identifiers and return them as a list
of typed target tokens ready for investigation.
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel
import httpx

from app.config import settings

logger = logging.getLogger("apex.parse")
router = APIRouter(prefix="/parse-query", tags=["NL Parser"])


class ParseRequest(BaseModel):
    text: str  # Free-form natural language input


class ParsedTarget(BaseModel):
    value: str           # The extracted value (e.g. "+12025550143")
    type: str            # PHONE | EMAIL | USERNAME | DOMAIN | IP | PERSON | LOCATION | ORGANIZATION | URL
    label: str           # Human label (e.g. "Phone Number")
    confidence: float    # 0.0 – 1.0
    context: str         # How it was found (e.g. "phone number extracted from sentence")


class ParseResponse(BaseModel):
    original_text: str
    parsed_targets: List[ParsedTarget]
    multi_target_query: str   # Joined string to pass to create_investigation
    is_natural_language: bool


# ── Regex fallback extractors ──────────────────────────────────────────────────
RE_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
RE_PHONE = re.compile(r"\+?[\d][\d\s\-().]{6,18}[\d]")
RE_DOMAIN = re.compile(r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+(?:com|in|org|net|io|co|gov|edu|info|biz|app|dev|ai)\b")
RE_IP = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
RE_GITHUB = re.compile(r"github\.com/[a-zA-Z0-9_.\-]+(?:/[a-zA-Z0-9_.\-]+)?")
RE_URL = re.compile(r"https?://[^\s]+")
RE_CRYPTO_BTC = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
RE_CRYPTO_ETH = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


def _regex_fallback_extract(text: str) -> List[ParsedTarget]:
    """Extract identifiers using pure regex when AI is unavailable."""
    targets = []
    seen = set()

    def add(value: str, typ: str, label: str, confidence: float, ctx: str):
        v = value.strip()
        if v and v not in seen:
            seen.add(v)
            targets.append(ParsedTarget(value=v, type=typ, label=label, confidence=confidence, context=ctx))

    for m in RE_URL.finditer(text):
        add(m.group(), "URL", "Web URL", 0.97, "URL pattern detected")

    for m in RE_EMAIL.finditer(text):
        add(m.group(), "EMAIL", "Email Address", 0.97, "Email pattern detected")

    for m in RE_GITHUB.finditer(text):
        url = m.group()
        if "/" in url[10:]:
            add(url, "GITHUB_REPO", "GitHub Repository", 0.97, "GitHub repo URL")
        else:
            add(url, "USERNAME", "GitHub Username", 0.95, "GitHub user URL")

    for m in RE_IP.finditer(text):
        add(m.group(), "IP", "IP Address", 0.96, "IPv4 pattern detected")

    for m in RE_DOMAIN.finditer(text):
        add(m.group(), "DOMAIN", "Domain Name", 0.90, "Domain pattern detected")

    # Phone: normalize by removing spaces/dashes and check length 8–15
    for m in RE_PHONE.finditer(text):
        raw = m.group()
        digits = re.sub(r"[^\d+]", "", raw)
        if len(digits) >= 8:
            add(digits if digits.startswith("+") else raw.strip(), "PHONE", "Phone Number", 0.88, "Phone number pattern detected")

    for m in RE_CRYPTO_ETH.finditer(text):
        add(m.group(), "CRYPTO_ADDRESS", "Ethereum Address", 0.96, "ETH address detected")

    for m in RE_CRYPTO_BTC.finditer(text):
        add(m.group(), "CRYPTO_ADDRESS", "Bitcoin Address", 0.93, "BTC address detected")

    return targets


_GEMINI_PARSE_PROMPT = """You are an expert OSINT Entity Extractor. The user will give you a free-form sentence containing mixed intelligence about a target person or entity.

Your task:
1. Read the sentence carefully.
2. Extract ALL distinct identifiable pieces of information.
3. Classify each as one of: PERSON, PHONE, EMAIL, USERNAME, DOMAIN, URL, IP, LOCATION, ORGANIZATION, GITHUB_REPO, CRYPTO_ADDRESS.
4. Return ONLY valid JSON — an array of objects with keys: value, type, label, confidence (0.0-1.0), context.

Rules:
- Normalize phone numbers to E.164 format if the country is clear (e.g. "020 7946 0958" from UK → "+442079460958")
- For person names, include the full name as given.
- For locations (city, state, country), extract them separately.
- confidence: 0.97 for exact matches (email/phone/URL), 0.85 for inferred/partial.
- DO NOT include generic words — only concrete identifiers.

Example input: "target user John Doe, lives in Dublin Ireland, phone +353 1 496 0123, uses handle jdoe99 on twitter, email jdoe@example.org"
Example output:
[
  {"value": "John Doe", "type": "PERSON", "label": "Full Name", "confidence": 0.95, "context": "name extracted from sentence"},
  {"value": "Dublin, Ireland", "type": "LOCATION", "label": "City / Country", "confidence": 0.90, "context": "location context from 'lives in'"},
  {"value": "+35314960123", "type": "PHONE", "label": "Phone Number", "confidence": 0.95, "context": "phone number normalized to E.164"},
  {"value": "jdoe99", "type": "USERNAME", "label": "Twitter Handle", "confidence": 0.92, "context": "handle from 'twitter'"},
  {"value": "jdoe@example.org", "type": "EMAIL", "label": "Email Address", "confidence": 0.97, "context": "email pattern detected"}
]

Now extract from this input:
"""


async def _gemini_parse(text: str) -> Optional[List[Dict[str, Any]]]:
    """Call Gemini to parse NL text into structured targets."""
    if not settings.GEMINI_API_KEY:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": _GEMINI_PARSE_PROMPT + text}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning("Gemini parse API %s: %s", resp.status_code, resp.text[:300])
                return None

            result = resp.json()
            candidate = result.get("candidates", [{}])[0]
            raw_text = "".join(
                p.get("text", "")
                for p in candidate.get("content", {}).get("parts", [])
                if "text" in p
            )

            # Strip markdown code fences if present
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)
            if isinstance(parsed, list):
                return parsed

    except Exception as e:
        logger.error("Gemini parse error: %s", e)

    return None


def _is_natural_language(text: str) -> bool:
    """Heuristic: is the input a natural language sentence vs a bare identifier?"""
    t = text.strip()
    # Has multiple words with spaces (more than 2 words)
    words = t.split()
    if len(words) < 3:
        return False
    # Contains connecting words typical of NL
    nl_keywords = {
        "name", "is", "lives", "in", "at", "email", "phone", "number",
        "his", "her", "their", "and", "also", "username", "handle",
        "works", "located", "from", "called", "known", "guy", "girl",
        "person", "contact", "mobile", "cell", "address", "the", "a", "an",
        "think", "maybe", "possibly", "found", "uses", "on", "with",
    }
    word_set = {w.lower().strip(".,;:\"'") for w in words}
    overlap = word_set & nl_keywords
    return len(overlap) >= 2


@router.post("", response_model=ParseResponse)
async def parse_natural_language_query(req: ParseRequest) -> ParseResponse:
    """Parse free-form natural language into structured OSINT targets."""
    text = req.text.strip()
    nl = _is_natural_language(text)

    parsed_targets: List[ParsedTarget] = []

    if nl:
        # 1. Try Gemini AI parse first
        gemini_result = await _gemini_parse(text)
        if gemini_result:
            for item in gemini_result:
                try:
                    parsed_targets.append(ParsedTarget(
                        value=str(item.get("value", "")).strip(),
                        type=str(item.get("type", "UNKNOWN")).upper(),
                        label=str(item.get("label", item.get("type", "Target"))),
                        confidence=float(item.get("confidence", 0.85)),
                        context=str(item.get("context", "AI extracted"))
                    ))
                except Exception:
                    pass

        # 2. Always also run regex to catch anything Gemini missed
        regex_targets = _regex_fallback_extract(text)
        existing_values = {t.value.lower() for t in parsed_targets}
        for rt in regex_targets:
            if rt.value.lower() not in existing_values:
                parsed_targets.append(rt)
                existing_values.add(rt.value.lower())

    else:
        # Simple identifier — use regex extraction
        parsed_targets = _regex_fallback_extract(text)
        if not parsed_targets:
            # Treat the whole thing as a single target
            parsed_targets = [ParsedTarget(
                value=text,
                type="UNKNOWN",
                label="Target Identifier",
                confidence=0.80,
                context="Single identifier"
            )]

    # Build multi-target query string (space-separated unique identifiers)
    # Investigation-worthy types only (skip raw LOCATION/PERSON for now as they need special handling)
    investigation_types = {"PHONE", "EMAIL", "USERNAME", "DOMAIN", "IP", "URL", "GITHUB_REPO", "GITHUB_USER", "CRYPTO_ADDRESS", "PERSON", "ORGANIZATION"}
    query_parts = [t.value for t in parsed_targets if t.type in investigation_types]
    multi_query = "\n".join(query_parts) if query_parts else text

    return ParseResponse(
        original_text=text,
        parsed_targets=parsed_targets,
        multi_target_query=multi_query,
        is_natural_language=nl
    )
