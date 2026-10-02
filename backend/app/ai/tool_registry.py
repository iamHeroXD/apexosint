"""Explicit, permission-controlled tool registry for Gemini function calling."""

import json
from typing import Dict, Any, List, Callable, Awaitable
from sqlalchemy import select
from app.database import async_session_factory
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.relationship import Relationship
from app.models.contradiction import Contradiction
from app.modules.registry import module_registry


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert to Google Gemini tool declaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class AIToolRegistry:
    """Manages strictly controlled OSINT tools accessible to Gemini."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_all()

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition:
        return self._tools.get(name)

    def get_declarations(self) -> List[Dict[str, Any]]:
        return [tool.to_gemini_schema() for tool in self._tools.values()]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute registered tool with arguments."""
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' is not registered."}
        try:
            return await tool.handler(args)
        except Exception as e:
            return {"error": f"Execution error in {name}: {str(e)}"}

    def _register_all(self):
        # 1. resolve_dns
        async def handle_resolve_dns(args: Dict[str, Any]) -> Dict[str, Any]:
            domain = args.get("domain", "")
            f = await module_registry.execute_module("dns_records", domain, "DOMAIN")
            return {
                "domain": domain,
                "discovered_entities": [e.value for e in f.discovered_entities],
                "evidence_snippet": f.evidence[0].snippet if f.evidence else "No records found"
            }

        self.register(ToolDefinition(
            name="resolve_dns",
            description="Queries authoritative DNS records for a domain (A, MX, NS, TXT).",
            parameters={
                "type": "object",
                "properties": {"domain": {"type": "string", "description": "Domain name to resolve"}},
                "required": ["domain"]
            },
            handler=handle_resolve_dns
        ))

        # 2. lookup_rdap
        async def handle_lookup_rdap(args: Dict[str, Any]) -> Dict[str, Any]:
            target = args.get("domain_or_ip", "")
            t_type = "IP" if target.replace(".", "").isdigit() else "DOMAIN"
            f = await module_registry.execute_module("rdap_whois", target, t_type)
            return {
                "target": target,
                "entities": [e.value for e in f.discovered_entities],
                "evidence": f.evidence[0].snippet if f.evidence else "No RDAP record"
            }

        self.register(ToolDefinition(
            name="lookup_rdap",
            description="Queries authoritative RDAP registry for domain or IP registration.",
            parameters={
                "type": "object",
                "properties": {"domain_or_ip": {"type": "string", "description": "Domain or IP address"}},
                "required": ["domain_or_ip"]
            },
            handler=handle_lookup_rdap
        ))

        # 3. inspect_certificate
        async def handle_inspect_cert(args: Dict[str, Any]) -> Dict[str, Any]:
            domain = args.get("domain", "")
            f = await module_registry.execute_module("cert_transparency", domain, "DOMAIN")
            subdomains = [e.value for e in f.discovered_entities if e.type == "SUBDOMAIN"]
            return {
                "domain": domain,
                "subdomains_count": len(subdomains),
                "subdomains_sample": subdomains[:10],
                "evidence": f.evidence[0].snippet if f.evidence else "No certificates found"
            }

        self.register(ToolDefinition(
            name="inspect_certificate",
            description="Queries public Certificate Transparency logs for domain subdomains and TLS metadata.",
            parameters={
                "type": "object",
                "properties": {"domain": {"type": "string", "description": "Root domain name"}},
                "required": ["domain"]
            },
            handler=handle_inspect_cert
        ))

        # 4. search_username
        async def handle_search_username(args: Dict[str, Any]) -> Dict[str, Any]:
            username = args.get("username", "")
            f = await module_registry.execute_module("username_profile_finder", username, "USERNAME")
            profiles = [e.value for e in f.discovered_entities if e.type == "SOCIAL_PROFILE"]
            return {
                "username": username,
                "profiles_found": profiles,
                "evidence": f.evidence[0].snippet if f.evidence else "No public profiles found"
            }

        self.register(ToolDefinition(
            name="search_username",
            description="Checks existence of public profile handles across code and developer platforms.",
            parameters={
                "type": "object",
                "properties": {"username": {"type": "string", "description": "Target handle or username"}},
                "required": ["username"]
            },
            handler=handle_search_username
        ))

        # 5. search_public_email
        async def handle_search_email(args: Dict[str, Any]) -> Dict[str, Any]:
            email = args.get("email", "")
            f = await module_registry.execute_module("email_analyzer", email, "EMAIL")
            return {
                "email": email,
                "associated_domain": [e.value for e in f.discovered_entities if e.type == "DOMAIN"],
                "evidence": f.evidence[0].snippet if f.evidence else "Analysis complete"
            }

        self.register(ToolDefinition(
            name="search_public_email",
            description="Inspects public deliverability, MX configuration, and Gravatar hash for an email.",
            parameters={
                "type": "object",
                "properties": {"email": {"type": "string", "description": "Target email address"}},
                "required": ["email"]
            },
            handler=handle_search_email
        ))

        # 6. query_investigation_evidence
        async def handle_query_evidence(args: Dict[str, Any]) -> Dict[str, Any]:
            inv_id = args.get("investigation_id", "")
            async with async_session_factory() as session:
                query = await session.execute(
                    select(Evidence).where(Evidence.investigation_id == inv_id).limit(20)
                )
                evs = query.scalars().all()
                return {
                    "total_evidence_returned": len(evs),
                    "evidence": [
                        {
                            "id": e.id,
                            "source": e.source_name,
                            "type": e.source_type,
                            "snippet": e.snippet,
                            "confidence": e.confidence
                        }
                        for e in evs
                    ]
                }

        self.register(ToolDefinition(
            name="query_investigation_evidence",
            description="Retrieves collected evidence records and snippets from the database for an ongoing investigation.",
            parameters={
                "type": "object",
                "properties": {"investigation_id": {"type": "string", "description": "ID of the current investigation"}},
                "required": ["investigation_id"]
            },
            handler=handle_query_evidence
        ))

        # 7. find_contradictions
        async def handle_find_contradictions(args: Dict[str, Any]) -> Dict[str, Any]:
            inv_id = args.get("investigation_id", "")
            async with async_session_factory() as session:
                query = await session.execute(
                    select(Contradiction).where(Contradiction.investigation_id == inv_id)
                )
                confs = query.scalars().all()
                return {
                    "contradictions_count": len(confs),
                    "contradictions": [
                        {
                            "attribute": c.attribute_name,
                            "source_a": c.source_a_name,
                            "claim_a": c.source_a_claim,
                            "source_b": c.source_b_name,
                            "claim_b": c.source_b_claim,
                            "explanation": c.explanation
                        }
                        for c in confs
                    ]
                }

        self.register(ToolDefinition(
            name="find_contradictions",
            description="Checks for conflicting claims and divergent facts detected in the investigation.",
            parameters={
                "type": "object",
                "properties": {"investigation_id": {"type": "string", "description": "Investigation ID"}},
                "required": ["investigation_id"]
            },
            handler=handle_find_contradictions
        ))


ai_tool_registry = AIToolRegistry()
