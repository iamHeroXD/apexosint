"""Email Intelligence & Security Configuration Module for APEX OSINT."""

import asyncio
import hashlib
import re
from typing import Dict, Any
import dns.asyncresolver
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)


class EmailAnalyzerModule(BaseOSINTModule):
    name = "email_analyzer"
    display_name = "Email Intelligence & Deliverability"
    description = "Analyzes email syntax, domain deliverability (MX, SPF, DMARC), and public gravatar presence."
    category = "EMAIL"
    target_types = ["EMAIL"]
    rate_limit = 3.0
    source = "Public DNS & Gravatar Hashes"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        email = target_value.lower().strip()

        if "@" not in email:
            return finding

        username, domain = email.split("@", 1)

        finding.primary_entity = NormalizedEntity(
            type="EMAIL",
            value=email,
            normalized_value=email,
            confidence=1.0,
            metadata={"user": username, "domain": domain}
        )

        # 1. Connect Email to its Domain
        finding.discovered_entities.append(
            NormalizedEntity(
                type="DOMAIN",
                value=domain,
                normalized_value=domain,
                confidence=0.99,
                metadata={"role": "email_host"}
            )
        )
        finding.relationships.append(
            NormalizedRelationship(
                source_value=email,
                source_type="EMAIL",
                target_value=domain,
                target_type="DOMAIN",
                relation_type="ASSOCIATED_WITH",
                confidence=0.99,
                evidence_indices=[]
            )
        )

        # 2. Check MX Records, SPF, and DMARC concurrently
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 2.0
        resolver.lifetime = 3.0
        resolver.nameservers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        mx_records = []
        spf_valid = False
        dmarc_valid = False

        async def check_mx():
            nonlocal mx_records
            try:
                answers = await resolver.resolve(domain, "MX")
                mx_records = [str(r).split()[-1].rstrip(".") for r in answers]
            except Exception:
                pass

        async def check_spf():
            nonlocal spf_valid
            try:
                txt_answers = await resolver.resolve(domain, "TXT")
                for r in txt_answers:
                    if "v=spf1" in str(r).lower():
                        spf_valid = True
            except Exception:
                pass

        async def check_dmarc():
            nonlocal dmarc_valid
            try:
                dmarc_answers = await resolver.resolve(f"_dmarc.{domain}", "TXT")
                for r in dmarc_answers:
                    if "v=dmarc1" in str(r).lower():
                        dmarc_valid = True
            except Exception:
                pass

        await asyncio.gather(check_mx(), check_spf(), check_dmarc())

        # 3. Holehe-style Passive Account & Identity Probes
        email_hash = hashlib.md5(email.encode("utf-8")).hexdigest()
        gravatar_avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?d=404"
        gravatar_json_url = f"https://en.gravatar.com/{email_hash}.json"
        
        client = SafeHTTPClient(timeout=5.0)
        has_gravatar = False
        gravatar_profile_data = {}
        all_email_sites = []

        # Probe Gravatar Avatar & Profile JSON
        try:
            grav_resp = await client.get(gravatar_avatar_url)
            if grav_resp.status_code == 200:
                has_gravatar = True
                all_email_sites.append({
                    "platform": "Gravatar Global Identity",
                    "category": "Global Avatar & Identity",
                    "url": f"https://gravatar.com/{email_hash}",
                    "status": "FOUND",
                    "status_code": 200,
                })
                # Attempt profile details lookup
                try:
                    prof_resp = await client.get(gravatar_json_url)
                    if prof_resp.status_code == 200:
                        p_entry = prof_resp.json().get("entry", [{}])[0]
                        gravatar_profile_data = p_entry
                        display_name = p_entry.get("displayName") or p_entry.get("preferredUsername")
                        if display_name:
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="PERSON",
                                    value=display_name,
                                    normalized_value=display_name.lower(),
                                    confidence=0.90,
                                    metadata={"source": "Gravatar Profile"}
                                )
                            )
                        loc = p_entry.get("currentLocation")
                        if loc:
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="LOCATION",
                                    value=loc,
                                    normalized_value=loc.lower(),
                                    confidence=0.85,
                                    metadata={"source": "Gravatar Profile"}
                                )
                            )
                except Exception:
                    pass
            else:
                all_email_sites.append({
                    "platform": "Gravatar Global Identity",
                    "category": "Global Avatar & Identity",
                    "url": f"https://gravatar.com/{email_hash}",
                    "status": "NOT_FOUND",
                    "status_code": 404,
                })
        except Exception:
            all_email_sites.append({
                "platform": "Gravatar Global Identity",
                "category": "Global Avatar & Identity",
                "url": f"https://gravatar.com/{email_hash}",
                "status": "NOT_FOUND",
                "status_code": 404,
            })

        # GitHub Public User Search by Email
        try:
            gh_search_url = f"https://api.github.com/search/users?q={email}+in:email"
            gh_resp = await client.get(gh_search_url, headers={"Accept": "application/vnd.github.v3+json"})
            if gh_resp.status_code == 200:
                gh_data = gh_resp.json()
                gh_items = gh_data.get("items", [])
                if gh_items:
                    gh_user = gh_items[0].get("login")
                    all_email_sites.append({
                        "platform": "GitHub (Author / Committer)",
                        "category": "Code & Development",
                        "url": f"https://github.com/{gh_user}",
                        "status": "FOUND",
                        "status_code": 200,
                    })
                    finding.discovered_entities.append(
                        NormalizedEntity(
                            type="USERNAME",
                            value=gh_user,
                            normalized_value=gh_user.lower(),
                            confidence=0.95,
                            metadata={"platform": "GitHub", "matched_email": email}
                        )
                    )
                else:
                    all_email_sites.append({
                        "platform": "GitHub (Author / Committer)",
                        "category": "Code & Development",
                        "url": f"https://github.com/search?q={email}&type=users",
                        "status": "NOT_FOUND",
                        "status_code": 200,
                    })
        except Exception:
            pass

        # Mail Exchanger Public Infrastructure Site
        all_email_sites.append({
            "platform": f"Domain MX Gateway ({domain})",
            "category": "Mail Infrastructure",
            "url": f"https://{domain}",
            "status": "FOUND" if mx_records else "NOT_FOUND",
            "status_code": 200 if mx_records else 404,
        })

        evidence_snippet = (
            f"Email deliverability & passive identity assessed for {email}: "
            f"MX servers ({len(mx_records)} detected), SPF={'Configured' if spf_valid else 'Absent'}, "
            f"DMARC={'Configured' if dmarc_valid else 'Absent'}, Gravatar account={'Active' if has_gravatar else 'Unregistered'}."
        )

        finding.evidence.append(
            NormalizedEvidence(
                source_name="Holehe-Style Passive Account & Deliverability Probe",
                source_type="EMAIL",
                source_url=f"dns://{domain}",
                snippet=evidence_snippet,
                collection_method="DNS_AND_PASSIVE_HTTP",
                confidence=0.96,
                epistemic_label="OBSERVED",
                raw_payload={
                    "email": email,
                    "mx_servers": mx_records,
                    "spf_present": spf_valid,
                    "dmarc_present": dmarc_valid,
                    "gravatar_registered": has_gravatar,
                    "all_probed_sites": all_email_sites,
                    "gravatar_profile": gravatar_profile_data,
                },
                related_entity_values=[email, domain]
            )
        )

        # Connect Username entity derived from local part
        finding.discovered_entities.append(
            NormalizedEntity(
                type="USERNAME",
                value=username,
                normalized_value=username.lower(),
                confidence=0.80,
                metadata={"derived_from": "email_local_part"}
            )
        )
        finding.relationships.append(
            NormalizedRelationship(
                source_value=email,
                source_type="EMAIL",
                target_value=username,
                target_type="USERNAME",
                relation_type="ASSOCIATED_WITH",
                confidence=0.80,
                evidence_indices=[0]
            )
        )

        return finding

