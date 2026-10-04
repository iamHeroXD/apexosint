"""Deterministic Correlation Rule Engine for APEX OSINT.

Discovers evidence-backed graph edges across infrastructure, certificates,
code repositories, identities, and email domains.
Every edge contains an explicit explanation, discovery method, and provenance evidence IDs.
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.models.evidence import Evidence


class DeterministicCorrelator:
    """Computes evidence-backed correlations across discovered entities with explainable provenance."""

    @classmethod
    def evaluate_correlations(
        cls,
        entities: List[Entity],
        relationships: List[Relationship],
        evidence_list: List[Evidence]
    ) -> List[Dict[str, Any]]:
        """Evaluate deterministic rules to discover cross-entity connections."""
        new_correlations: List[Dict[str, Any]] = []
        entity_by_norm = {e.normalized_value: e for e in entities}
        entity_by_id = {e.id: e for e in entities}

        # Existing edges set to prevent duplicate generation
        existing_edges: Set[tuple] = {
            (r.source_entity_id, r.target_entity_id, r.relation_type)
            for r in relationships
        }

        # Helper to avoid adding existing edge
        def add_corr(s_id: str, t_id: str, r_type: str, conf: float, method: str, reason: str, ev_ids: List[str]):
            if (s_id, t_id, r_type) not in existing_edges and (t_id, s_id, r_type) not in existing_edges:
                existing_edges.add((s_id, t_id, r_type))
                new_correlations.append({
                    "source_entity_id": s_id,
                    "target_entity_id": t_id,
                    "relation_type": r_type,
                    "confidence": round(conf, 3),
                    "discovery_method": method,
                    "explanation": reason,
                    "is_ai_inferred": False,
                    "evidence_ids": ev_ids[:3]
                })

        # --- Rule 1: Co-Hosting / Shared Infrastructure (Multiple domains resolving to same IP) ---
        ip_to_domains = defaultdict(list)
        for r in relationships:
            if r.relation_type in ("RESOLVES_TO", "HOSTED_ON"):
                src = entity_by_id.get(r.source_entity_id)
                tgt = entity_by_id.get(r.target_entity_id)
                if src and tgt and tgt.type == "IP":
                    ip_to_domains[tgt.id].append(src)
                elif src and tgt and src.type == "IP":
                    ip_to_domains[src.id].append(tgt)

        for ip_id, dom_entities in ip_to_domains.items():
            ip_ent = entity_by_id.get(ip_id)
            ip_val = ip_ent.value if ip_ent else "shared IP"
            if len(dom_entities) > 1:
                ip_ev_ids = [e.id for e in evidence_list if ip_id in (e.related_entity_ids_json or [])]
                for i in range(len(dom_entities)):
                    for j in range(i + 1, len(dom_entities)):
                        d1 = dom_entities[i]
                        d2 = dom_entities[j]
                        add_corr(
                            d1.id,
                            d2.id,
                            "SHARED_INFRASTRUCTURE",
                            0.88,
                            "PASSIVE_DNS",
                            f"Both '{d1.value}' and '{d2.value}' share identical hosting infrastructure at IP {ip_val}.",
                            ip_ev_ids
                        )

        # --- Rule 2: Shared Mail Exchanger (MX) Infrastructure ---
        # Look for MX records inside evidence raw_payload_json
        mx_to_domains = defaultdict(list)
        for ev in evidence_list:
            payload = ev.raw_payload_json or {}
            mx_records = payload.get("mx_records") or payload.get("mx") or []
            if isinstance(mx_records, list):
                for mx in mx_records:
                    mx_host = mx if isinstance(mx, str) else mx.get("host", "")
                    if mx_host and ev.related_entity_ids_json:
                        for eid in ev.related_entity_ids_json:
                            ent = entity_by_id.get(eid)
                            if ent and ent.type in ("DOMAIN", "SUBDOMAIN"):
                                mx_to_domains[mx_host.lower()].append((ent, ev.id))

        for mx_host, dom_pairs in mx_to_domains.items():
            if len(dom_pairs) > 1:
                # Group unique domains
                seen_doms = {}
                for ent, ev_id in dom_pairs:
                    seen_doms[ent.id] = (ent, ev_id)
                u_list = list(seen_doms.values())
                for i in range(len(u_list)):
                    for j in range(i + 1, len(u_list)):
                        e1, ev1_id = u_list[i]
                        e2, ev2_id = u_list[j]
                        add_corr(
                            e1.id,
                            e2.id,
                            "SHARED_MX",
                            0.92,
                            "PASSIVE_DNS",
                            f"Both domains share configured Mail Exchanger '{mx_host}'.",
                            [ev1_id, ev2_id]
                        )

        # --- Rule 3: Shared Certificate Transparency (CT Log SANs) ---
        cert_san_groups = defaultdict(list)
        for ev in evidence_list:
            if "crt.sh" in ev.source_name.lower() or "cert" in ev.source_name.lower():
                payload = ev.raw_payload_json or {}
                sans = payload.get("san_list") or payload.get("matching_identities") or []
                if isinstance(sans, list) and len(sans) > 1:
                    for san in sans:
                        san_norm = san.lower().strip().lstrip("*.")
                        san_ent = entity_by_norm.get(san_norm)
                        if san_ent:
                            cert_san_groups[ev.id].append(san_ent)

        for ev_id, matched_entities in cert_san_groups.items():
            if len(matched_entities) > 1:
                for i in range(len(matched_entities)):
                    for j in range(i + 1, len(matched_entities)):
                        e1 = matched_entities[i]
                        e2 = matched_entities[j]
                        add_corr(
                            e1.id,
                            e2.id,
                            "SHARED_CERTIFICATE",
                            0.95,
                            "CT_LOG",
                            f"Co-listed in x509 Subject Alternative Name (SAN) certificate extension.",
                            [ev_id]
                        )

        # --- Rule 4: Subdomain Hierarchy ---
        subdomains = [e for e in entities if e.type in ("SUBDOMAIN", "DOMAIN")]
        for s in subdomains:
            parts = s.normalized_value.split(".")
            if len(parts) > 2:
                parent_domain = ".".join(parts[1:])
                parent_ent = entity_by_norm.get(parent_domain)
                if parent_ent and parent_ent.id != s.id:
                    add_corr(
                        s.id,
                        parent_ent.id,
                        "SUBDOMAIN_OF",
                        0.99,
                        "DIRECT_CORRELATION",
                        f"Hierarchical DNS subdomain of apex domain '{parent_domain}'.",
                        []
                    )

        # --- Rule 5: Shared Domain Email Correlation ---
        for ent in entities:
            if ent.type == "EMAIL" and "@" in ent.value:
                domain_part = ent.value.split("@")[1].lower()
                domain_ent = entity_by_norm.get(domain_part)
                if domain_ent:
                    add_corr(
                        ent.id,
                        domain_ent.id,
                        "ASSOCIATED_WITH",
                        0.98,
                        "DIRECT_CORRELATION",
                        f"Email address identity belongs to domain '{domain_part}'.",
                        []
                    )

        # --- Rule 6: Repository Contributor & Code Ownership ---
        for ent in entities:
            if ent.type == "REPOSITORY" and "/" in ent.value:
                owner_part = ent.value.split("/")[0].lower()
                owner_ent = entity_by_norm.get(owner_part)
                if owner_ent:
                    add_corr(
                        owner_ent.id,
                        ent.id,
                        "OWNS",
                        0.96,
                        "REPO_COMMIT",
                        f"Entity is authoritative owner/namespace of repository '{ent.value}'.",
                        []
                    )

        # --- Rule 7: Similar / Matching Username Alignment ---
        usernames = [e for e in entities if e.type == "USERNAME"]
        for i in range(len(usernames)):
            for j in range(i + 1, len(usernames)):
                u1 = usernames[i]
                u2 = usernames[j]
                if u1.normalized_value == u2.normalized_value:
                    add_corr(
                        u1.id,
                        u2.id,
                        "SIMILAR_USERNAME",
                        0.90,
                        "HEURISTIC",
                        f"Exact handle identity collision across discovered platform services.",
                        []
                    )

        return new_correlations
