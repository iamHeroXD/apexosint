"""OSINT Module Registry and execution lifecycle manager."""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Type
from datetime import datetime, timezone
from app.modules.base import BaseOSINTModule, ModuleHealth, NormalizedFinding

# Import built-in modules
from app.modules.domain.dns_records import DNSRecordsModule
from app.modules.domain.rdap_whois import RDAPWhoisModule
from app.modules.domain.cert_transparency import CertTransparencyModule
from app.modules.domain.security_txt import SecurityTxtModule
from app.modules.network.ip_geo_asn import IPGeoASNModule
from app.modules.network.reverse_dns import ReverseDNSModule
from app.modules.username.profile_finder import UsernameProfileFinderModule
from app.modules.email.email_analyzer import EmailAnalyzerModule
from app.modules.github.repo_analyzer import GitHubRepoAnalyzerModule
from app.modules.web.web_scraper import WebScraperModule
from app.modules.documents.doc_extractor import DocumentExtractorModule
from app.modules.phone.phone_analyzer import PhoneAnalyzerModule
from app.modules.domain.wayback_machine import WaybackMachineModule

logger = logging.getLogger("apex.modules")


class ModuleRegistry:
    """Central registry and execution manager for all OSINT modules."""

    def __init__(self):
        self._modules: Dict[str, BaseOSINTModule] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._register_defaults()

    def _register_defaults(self):
        default_classes = [
            DNSRecordsModule,
            RDAPWhoisModule,
            CertTransparencyModule,
            SecurityTxtModule,
            IPGeoASNModule,
            ReverseDNSModule,
            UsernameProfileFinderModule,
            EmailAnalyzerModule,
            GitHubRepoAnalyzerModule,
            WebScraperModule,
            DocumentExtractorModule,
            PhoneAnalyzerModule,
            WaybackMachineModule,
        ]
        for cls in default_classes:
            self.register(cls())

    def register(self, module: BaseOSINTModule) -> None:
        """Register an initialized OSINT module instance."""
        self._modules[module.name] = module
        self._metrics[module.name] = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_latency_ms": 0.0,
            "last_run": None,
            "last_error": None,
        }
        logger.info("Registered OSINT module: %s (%s)", module.name, module.category)

    def get_module(self, name: str) -> Optional[BaseOSINTModule]:
        return self._modules.get(name)

    def list_modules(self) -> List[Dict[str, Any]]:
        """Return metadata and telemetry for all registered modules."""
        output = []
        for name, mod in self._modules.items():
            metrics = self._metrics[name]
            total = metrics["total_runs"]
            avg_latency = (metrics["total_latency_ms"] / total) if total > 0 else 0.0
            err_rate = (metrics["failed_runs"] / total) if total > 0 else 0.0

            output.append({
                "name": mod.name,
                "display_name": mod.display_name,
                "description": mod.description,
                "category": mod.category,
                "target_types": mod.target_types,
                "rate_limit": mod.rate_limit,
                "source": mod.source,
                "license": mod.license,
                "enabled": mod.enabled,
                "safety_level": mod.safety_level,
                "average_latency_ms": round(avg_latency, 1),
                "error_rate": round(err_rate, 2),
                "last_run": metrics["last_run"],
                "status": "HEALTHY" if mod.enabled and err_rate < 0.2 else ("DEGRADED" if mod.enabled else "DISABLED")
            })
        return output

    def set_module_enabled(self, name: str, enabled: bool) -> bool:
        if name in self._modules:
            self._modules[name].enabled = enabled
            return True
        return False

    def get_applicable_modules(self, target_type: str, mode: str = "standard") -> List[BaseOSINTModule]:
        """Select applicable modules matching the target type and investigation mode."""
        matching = [
            mod for mod in self._modules.values()
            if mod.can_handle(target_type, "")
        ]

        # Filter by mode intensity
        if mode == "quick":
            # Quick mode: only fast core modules, skipping deep web or heavy probes
            quick_skip = {"web_scraper", "document_extractor"}
            matching = [m for m in matching if m.name not in quick_skip]
        elif mode == "deep":
            # Deep mode runs all enabled modules
            pass

        return matching

    async def execute_module(
        self,
        module_name: str,
        target_value: str,
        target_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NormalizedFinding:
        """Execute a module safely, collecting latency metrics and normalizing errors."""
        mod = self.get_module(module_name)
        if not mod:
            raise ValueError(f"Module '{module_name}' is not registered.")
        if not mod.enabled:
            return NormalizedFinding()

        metrics = self._metrics[module_name]
        metrics["total_runs"] += 1
        metrics["last_run"] = datetime.now(timezone.utc).isoformat()

        start_time = time.monotonic()
        try:
            finding = await mod.collect(target_value, target_type, context or {})
            duration_ms = (time.monotonic() - start_time) * 1000.0
            metrics["successful_runs"] += 1
            metrics["total_latency_ms"] += duration_ms
            return finding
        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            metrics["failed_runs"] += 1
            metrics["total_latency_ms"] += duration_ms
            metrics["last_error"] = str(e)
            logger.error("Error executing module %s on %s: %s", module_name, target_value, e)
            return NormalizedFinding()


# Global singleton instance
module_registry = ModuleRegistry()
