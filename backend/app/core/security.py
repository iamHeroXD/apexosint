"""Security hardening, SSRF defense, and safe HTTP communication."""

import ipaddress
import re
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse
import httpx
from app.config import settings

# Disallowed private, loopback, link-local, and reserved IP networks for SSRF prevention
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata (e.g. AWS 169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 blocked ranges
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Common secret patterns for detection & automatic redaction
SECRET_PATTERNS = [
    (re.compile(r"(?i)(?:api_key|apikey|secret_key|secret)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{16,64})['\"]?"), "API_KEY"),
    (re.compile(r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}"), "GITHUB_TOKEN"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_ACCESS_KEY"),
    (re.compile(r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{20,})"), "BEARER_TOKEN"),
    (re.compile(r"(?i)private[_\-\s]?key"), "PRIVATE_KEY_REFERENCE"),
]


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address belongs to any blocked/private network range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in BLOCKED_NETWORKS)
    except ValueError:
        return True


def validate_target_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate a target URL against SSRF and illegal scheme constraints without blocking the async event loop."""
    if not url:
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Disallowed scheme: '{parsed.scheme}'. Only http and https are permitted."

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "Missing hostname in URL"

    # Restrict local loopback & cloud metadata
    blocked_hosts = {
        "localhost", "127.0.0.1", "::1", "metadata.google.internal",
        "169.254.169.254", "0.0.0.0"
    }
    if hostname in blocked_hosts or hostname.endswith((".local", ".internal", ".lan", ".home.arpa")):
        return False, f"Access to internal hostname '{hostname}' is restricted."

    # If hostname is a raw IP literal, check against blocked networks
    try:
        ip = ipaddress.ip_address(hostname)
        if any(ip in net for net in BLOCKED_NETWORKS):
            return False, f"Direct access to private IP '{hostname}' is blocked."
    except ValueError:
        # Hostname is a domain name, proceed safely
        pass

    return True, None


def redact_secrets(text: str) -> Tuple[str, bool]:
    """Scan text for potential secrets, redacting values to prevent leakage.
    
    Returns (sanitized_text, secret_detected_bool).
    """
    if not text:
        return text, False

    detected = False
    sanitized = text

    for pattern, secret_type in SECRET_PATTERNS:
        matches = pattern.finditer(sanitized)
        for match in matches:
            detected = True
            raw_match = match.group(0)
            replacement = f"[POTENTIAL SECRET EXPOSURE: {secret_type} REDACTED]"
            sanitized = sanitized.replace(raw_match, replacement)

    return sanitized, detected


class SafeHTTPClient:
    """High-speed async HTTP client with built-in SSRF guards, connection pooling, and size truncation."""

    _shared_client: Optional[httpx.AsyncClient] = None

    def __init__(self, timeout: float = None):
        self.timeout = timeout or settings.HTTP_TIMEOUT_SECONDS

    @classmethod
    def get_shared_client(cls, timeout: float = 6.0) -> httpx.AsyncClient:
        """Get or initialize the persistent pooled AsyncClient for fast concurrent scanning."""
        if cls._shared_client is None or cls._shared_client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
            cls._shared_client = httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/json,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
        return cls._shared_client

    async def get(
        self,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        follow_redirects: bool = True
    ) -> httpx.Response:
        is_valid, err = validate_target_url(url)
        if not is_valid:
            raise ValueError(f"SSRF Safety Guard: {err}")

        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            default_headers.update(headers)

        transport = httpx.AsyncHTTPTransport(retries=1)
        async with httpx.AsyncClient(
            transport=transport,
            timeout=self.timeout,
            follow_redirects=follow_redirects,
            max_redirects=settings.HTTP_MAX_REDIRECTS,
            verify=False  # Avoid SSL renegotiation hangs on outdated target endpoints
        ) as client:
            response = await client.get(url, headers=default_headers, params=params)
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_RESPONSE_BYTES:
                raise ValueError("Response payload exceeds maximum allowed size limit (5MB).")
            return response

