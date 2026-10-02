"""Master Investigation Orchestrator and Agent Execution Loop for APEX OSINT."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.investigation import Investigation
from app.models.target import Target
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.relationship import Relationship
from app.models.observation import Observation
from app.models.contradiction import Contradiction
from app.models.timeline import TimelineEvent
from app.models.module_run import ModuleRun
from app.core.events import event_bus
from app.engine.universal_detector import UniversalTargetEngine, AnalyzedTarget
from app.engine.normalizer import DataNormalizer
from app.engine.correlation import DeterministicCorrelator
from app.engine.contradiction import ContradictionDetector
from app.engine.entity_resolver import EntityResolver
from app.modules.base import NormalizedFinding
from app.modules.registry import module_registry
from app.modules.demo_provider import get_demo_investigation_data

logger = logging.getLogger("apex.orchestrator")


class InvestigationOrchestrator:
    """Manages the full multi-phase OSINT collection, expansion, and correlation pipeline."""

    def __init__(self):
        # Maps investigation_id -> asyncio.Task for cancellation/pause support
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def is_running(self, investigation_id: str) -> bool:
        task = self._running_tasks.get(investigation_id)
        return task is not None and not task.done()

    def cancel_investigation(self, investigation_id: str) -> bool:
        task = self._running_tasks.get(investigation_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def get_task(self, investigation_id: str) -> Optional[asyncio.Task]:
        """Return the running task for this investigation if any."""
        return self._running_tasks.get(investigation_id)

    async def wait_for_investigation(self, investigation_id: str, timeout: float = 25.0) -> bool:
        """Wait for an active investigation task to finish or reach timeout."""
        task = self._running_tasks.get(investigation_id)
        if not task or task.done():
            return True
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
            return True
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return False

    async def run_investigation(self, investigation_id: str) -> None:
        """Entrypoint for kicking off an investigation in the background."""
        task = asyncio.create_task(self._execute_pipeline(investigation_id))
        self._running_tasks[investigation_id] = task

    async def _execute_pipeline(self, investigation_id: str) -> None:
        """The main agent loop: PLAN -> DISCOVER -> COLLECT -> NORMALIZE -> CORRELATE -> VERIFY -> REPORT."""
        start_time = time.monotonic()
        logger.info("Starting investigation loop for %s", investigation_id)

        async with async_session_factory() as session:
            inv = await session.get(Investigation, investigation_id)
            if not inv:
                logger.error("Investigation %s not found", investigation_id)
                return

            if inv.is_demo:
                await self._populate_demo_investigation(session, inv)
                return

            inv.status = "running"
            await session.commit()

        await event_bus.publish(investigation_id, "status_change", {"status": "running", "phase": "PLANNING"})

        try:
            async with async_session_factory() as session:
                # Load targets
                targets_query = await session.execute(
                    select(Target).where(Target.investigation_id == investigation_id)
                )
                targets = list(targets_query.scalars().all())

                budget = inv.budget_json or {
                    "max_depth": 2,
                    "max_requests": 150,
                    "max_modules": 30,
                    "max_runtime": 180,
                }
                max_depth = min(inv.depth, budget.get("max_depth", 2))
                max_runtime = budget.get("max_runtime", 180)

                # Process initial targets through depths
                current_depth = 0
                active_targets = targets

                while current_depth <= max_depth and active_targets:
                    # Check runtime timeout budget
                    if (time.monotonic() - start_time) > max_runtime:
                        logger.warning("Investigation budget exceeded runtime limit (%ss)", max_runtime)
                        break

                    await event_bus.publish(
                        investigation_id,
                        "phase_update",
                        {"phase": "COLLECTING", "depth": current_depth, "target_count": len(active_targets)}
                    )

                    newly_discovered_candidates = []

                    for tgt in active_targets:
                        tgt.status = "analyzing"
                        await session.commit()

                        # Smart module selection
                        applicable_modules = module_registry.get_applicable_modules(tgt.detected_type, mode=inv.mode)
                        
                        await event_bus.publish(
                            investigation_id,
                            "plan_update",
                            {
                                "target": tgt.normalized_value,
                                "type": tgt.detected_type,
                                "modules_planned": [m.name for m in applicable_modules]
                            }
                        )

                        async def run_single_module(mod_obj):
                            m_start = time.monotonic()
                            await event_bus.publish(
                                investigation_id,
                                "module_started",
                                {"module_name": mod_obj.name, "target": tgt.normalized_value}
                            )
                            try:
                                f = await asyncio.wait_for(
                                    module_registry.execute_module(
                                        mod_obj.name,
                                        tgt.normalized_value,
                                        tgt.detected_type,
                                        {"investigation_id": investigation_id}
                                    ),
                                    timeout=20.0
                                )
                                dur = (time.monotonic() - m_start) * 1000.0
                                return mod_obj, f, dur, None
                            except Exception as mod_err:
                                dur = (time.monotonic() - m_start) * 1000.0
                                logger.error("Module %s error on %s: %s", mod_obj.name, tgt.normalized_value, mod_err)
                                return mod_obj, NormalizedFinding(), dur, str(mod_err)

                        # Execute all applicable modules concurrently in parallel!
                        mod_executions = await asyncio.gather(*(run_single_module(m) for m in applicable_modules))

                        for mod, finding, mod_dur, mod_err in mod_executions:
                            if mod_err and not finding.discovered_entities and not finding.evidence:
                                continue

                            try:
                                # Normalize finding
                                finding = DataNormalizer.process_finding(finding, investigation_id)

                                # Persist module run telemetry
                                m_run = ModuleRun(
                                    investigation_id=investigation_id,
                                    target_id=tgt.id,
                                    module_name=mod.name,
                                    category=mod.category,
                                    status="completed",
                                    duration_ms=mod_dur,
                                    findings_count=len(finding.discovered_entities) + len(finding.evidence)
                                )
                                session.add(m_run)

                                # Persist Primary Entity if not existing
                                primary_ent_id = None
                                if finding.primary_entity:
                                    pe = finding.primary_entity
                                    existing = await session.execute(
                                        select(Entity).where(
                                            Entity.investigation_id == investigation_id,
                                            Entity.normalized_value == pe.normalized_value
                                        )
                                    )
                                    existing_ent = existing.scalars().first()
                                    if not existing_ent:
                                        new_pe = Entity(
                                            investigation_id=investigation_id,
                                            type=pe.type,
                                            value=pe.value,
                                            normalized_value=pe.normalized_value,
                                            confidence=pe.confidence,
                                            provenance_label="OBSERVED",
                                            metadata_json=pe.metadata
                                        )
                                        session.add(new_pe)
                                        await session.flush()
                                        primary_ent_id = new_pe.id
                                    else:
                                        primary_ent_id = existing_ent.id

                                # Persist Evidence records
                                created_evidence_ids = []
                                for ev in finding.evidence:
                                    db_ev = Evidence(
                                        investigation_id=investigation_id,
                                        source_name=ev.source_name,
                                        source_type=ev.source_type,
                                        source_url=ev.source_url,
                                        collection_method=ev.collection_method,
                                        confidence=ev.confidence,
                                        epistemic_label=ev.epistemic_label,
                                        snippet=ev.snippet,
                                        raw_payload_json=ev.raw_payload,
                                        hash_signature=ev.hash_signature,
                                        related_entity_ids_json=[primary_ent_id] if primary_ent_id else []
                                    )
                                    session.add(db_ev)
                                    await session.flush()
                                    created_evidence_ids.append(db_ev.id)

                                    await event_bus.publish(
                                        investigation_id,
                                        "evidence_discovered",
                                        {
                                            "id": db_ev.id,
                                            "source": db_ev.source_name,
                                            "snippet": db_ev.snippet,
                                            "confidence": db_ev.confidence
                                        }
                                    )

                                # Persist Discovered Entities & Relationships
                                for de in finding.discovered_entities:
                                    existing_sub = await session.execute(
                                        select(Entity).where(
                                            Entity.investigation_id == investigation_id,
                                            Entity.normalized_value == de.normalized_value
                                        )
                                    )
                                    existing_ent = existing_sub.scalars().first()
                                    if not existing_ent:
                                        new_sub_ent = Entity(
                                            investigation_id=investigation_id,
                                            type=de.type,
                                            value=de.value,
                                            normalized_value=de.normalized_value,
                                            confidence=de.confidence,
                                            provenance_label="OBSERVED",
                                            metadata_json=de.metadata
                                        )
                                        session.add(new_sub_ent)
                                        await session.flush()
                                        sub_id = new_sub_ent.id

                                        await event_bus.publish(
                                            investigation_id,
                                            "entity_discovered",
                                            {"id": sub_id, "type": de.type, "value": de.value}
                                        )

                                        # Add to candidate queue for expansion if within depth limit
                                        if current_depth < max_depth and de.type in ("DOMAIN", "IP", "EMAIL", "USERNAME", "REPOSITORY"):
                                            newly_discovered_candidates.append(de)
                                    else:
                                        sub_id = existing_ent.id

                                    # Connect to primary entity if defined
                                    if primary_ent_id and sub_id != primary_ent_id:
                                        rel = Relationship(
                                            investigation_id=investigation_id,
                                            source_entity_id=primary_ent_id,
                                            target_entity_id=sub_id,
                                            relation_type="ASSOCIATED_WITH",
                                            confidence=de.confidence,
                                            evidence_ids_json=created_evidence_ids[:2]
                                        )
                                        session.add(rel)

                                # Persist Relationships
                                for r in finding.relationships:
                                    s_res = await session.execute(
                                        select(Entity).where(
                                            Entity.investigation_id == investigation_id,
                                            Entity.value == r.source_value
                                        )
                                    )
                                    t_res = await session.execute(
                                        select(Entity).where(
                                            Entity.investigation_id == investigation_id,
                                            Entity.value == r.target_value
                                        )
                                    )
                                    s_ent = s_res.scalars().first()
                                    t_ent = t_res.scalars().first()

                                    if s_ent and t_ent:
                                        db_rel = Relationship(
                                            investigation_id=investigation_id,
                                            source_entity_id=s_ent.id,
                                            target_entity_id=t_ent.id,
                                            relation_type=r.relation_type,
                                            confidence=r.confidence,
                                            is_ai_inferred=r.is_ai_inferred,
                                            evidence_ids_json=created_evidence_ids
                                        )
                                        session.add(db_rel)
                                        await event_bus.publish(
                                            investigation_id,
                                            "relationship_discovered",
                                            {
                                                "source": s_ent.value,
                                                "target": t_ent.value,
                                                "relation_type": r.relation_type
                                            }
                                        )

                                # Persist Timeline Events
                                for te in finding.timeline_events:
                                    db_te = TimelineEvent(
                                        investigation_id=investigation_id,
                                        timestamp=te.timestamp,
                                        event_type=te.event_type,
                                        title=te.title,
                                        description=te.description,
                                        confidence=te.confidence,
                                        entity_id=primary_ent_id,
                                        evidence_id=created_evidence_ids[0] if created_evidence_ids else None
                                    )
                                    session.add(db_te)

                                await session.commit()
                                await event_bus.publish(
                                    investigation_id,
                                    "module_completed",
                                    {"module_name": mod.name, "findings": len(finding.discovered_entities), "duration_ms": mod_dur}
                                )

                            except Exception as mod_err:
                                logger.error("Module %s error: %s", mod.name, mod_err)

                        tgt.status = "completed"
                        await session.commit()

                    # Auto-Expansion to next depth
                    current_depth += 1
                    if current_depth <= max_depth and newly_discovered_candidates:
                        # Convert candidate entities into Target models
                        active_targets = []
                        for cand in newly_discovered_candidates[:5]:  # Bounded expansion per depth
                            analyzed = UniversalTargetEngine.analyze_input(cand.value)
                            new_tgt = Target(
                                investigation_id=investigation_id,
                                raw_input=cand.value,
                                detected_type=analyzed.primary_type,
                                normalized_value=analyzed.normalized_value,
                                confidence=analyzed.primary_confidence,
                                depth=current_depth,
                                status="pending"
                            )
                            session.add(new_tgt)
                            await session.flush()
                            active_targets.append(new_tgt)
                        await session.commit()
                    else:
                        active_targets = []

                # PHASE: DETERMINISTIC CORRELATION
                await event_bus.publish(investigation_id, "phase_update", {"phase": "CORRELATING"})
                all_entities = list((await session.execute(select(Entity).where(Entity.investigation_id == investigation_id))).scalars().all())
                all_rels = list((await session.execute(select(Relationship).where(Relationship.investigation_id == investigation_id))).scalars().all())
                all_evs = list((await session.execute(select(Evidence).where(Evidence.investigation_id == investigation_id))).scalars().all())

                correlations = DeterministicCorrelator.evaluate_correlations(all_entities, all_rels, all_evs)
                for corr in correlations:
                    new_rel = Relationship(
                        investigation_id=investigation_id,
                        source_entity_id=corr["source_entity_id"],
                        target_entity_id=corr["target_entity_id"],
                        relation_type=corr["relation_type"],
                        confidence=corr["confidence"],
                        is_ai_inferred=corr["is_ai_inferred"],
                        evidence_ids_json=corr["evidence_ids"]
                    )
                    session.add(new_rel)
                await session.commit()

                # PHASE: CONTRADICTION DETECTION
                await event_bus.publish(investigation_id, "phase_update", {"phase": "VERIFYING"})
                conflicts = ContradictionDetector.scan_for_contradictions(all_entities, all_evs)
                for conf in conflicts:
                    db_conf = Contradiction(
                        investigation_id=investigation_id,
                        entity_id=conf["entity_id"],
                        attribute_name=conf["attribute_name"],
                        source_a_id=conf["source_a_id"],
                        source_a_name=conf["source_a_name"],
                        source_a_claim=conf["source_a_claim"],
                        source_b_id=conf["source_b_id"],
                        source_b_name=conf["source_b_name"],
                        source_b_claim=conf["source_b_claim"],
                        explanation=conf["explanation"]
                    )
                    session.add(db_conf)
                    await event_bus.publish(
                        investigation_id,
                        "contradiction_detected",
                        {"attribute": conf["attribute_name"], "explanation": conf["explanation"]}
                    )
                await session.commit()

                # PHASE: ENTITY RESOLUTION CLUSTERING
                EntityResolver.resolve_and_cluster(all_entities, all_evs)
                await session.commit()

                # Update Investigation Summary
                inv = await session.get(Investigation, investigation_id)
                if inv:
                    inv.status = "completed"
                    inv.summary_json = {
                        "entities_count": len(all_entities),
                        "evidence_count": len(all_evs),
                        "relationships_count": len(all_rels) + len(correlations),
                        "sources_count": len(set(e.source_name for e in all_evs)),
                        "high_confidence_count": sum(1 for e in all_evs if e.confidence >= 0.9),
                        "contradictions_count": len(conflicts),
                        "executive_summary": f"Investigation complete. Discovered {len(all_entities)} entities across {len(all_evs)} evidence records with {len(correlations)} correlated links and {len(conflicts)} detected contradictions."
                    }
                    await session.commit()

            await event_bus.publish(investigation_id, "status_change", {"status": "completed"})
            logger.info("Investigation %s completed successfully", investigation_id)

        except asyncio.CancelledError:
            logger.info("Investigation %s was cancelled by user", investigation_id)
            async with async_session_factory() as session:
                inv = await session.get(Investigation, investigation_id)
                if inv:
                    inv.status = "paused"
                    await session.commit()
            await event_bus.publish(investigation_id, "status_change", {"status": "paused"})
        except Exception as e:
            logger.error("Investigation %s failed: %s", investigation_id, e)
            async with async_session_factory() as session:
                inv = await session.get(Investigation, investigation_id)
                if inv:
                    inv.status = "failed"
                    await session.commit()
            await event_bus.publish(investigation_id, "status_change", {"status": "failed", "error": str(e)})

    async def _populate_demo_investigation(self, session: AsyncSession, inv: Investigation) -> None:
        """Hydrate investigation with the rich synthetic demo dataset."""
        demo_data = get_demo_investigation_data()

        # Targets
        for t in demo_data["targets"]:
            session.add(Target(
                investigation_id=inv.id,
                raw_input=t["raw_input"],
                detected_type=t["detected_type"],
                normalized_value=t["normalized_value"],
                confidence=t["confidence"],
                hypotheses_json=t["hypotheses_json"],
                status="completed"
            ))

        # Entities
        entity_map = {}
        for e in demo_data["entities"]:
            ent = Entity(
                investigation_id=inv.id,
                type=e["type"],
                value=e["value"],
                normalized_value=e["normalized_value"],
                confidence=e["confidence"],
                provenance_label=e["provenance_label"],
                cluster_id=e.get("cluster_id"),
                metadata_json=e.get("metadata_json", {})
            )
            session.add(ent)
            await session.flush()
            entity_map[e["id"]] = ent.id

        # Evidence
        evidence_map = {}
        for ev in demo_data["evidence"]:
            db_ev = Evidence(
                investigation_id=inv.id,
                source_name=ev["source_name"],
                source_type=ev["source_type"],
                source_url=ev["source_url"],
                collection_method=ev["collection_method"],
                confidence=ev["confidence"],
                epistemic_label=ev["epistemic_label"],
                snippet=ev["snippet"],
                raw_payload_json=ev["raw_payload_json"],
                related_entity_ids_json=[entity_map.get(eid) for eid in ev["related_entity_ids_json"] if eid in entity_map]
            )
            session.add(db_ev)
            await session.flush()
            evidence_map[ev["id"]] = db_ev.id

        # Relationships
        for r in demo_data["relationships"]:
            s_id = entity_map.get(r["source_entity_id"])
            t_id = entity_map.get(r["target_entity_id"])
            if s_id and t_id:
                session.add(Relationship(
                    investigation_id=inv.id,
                    source_entity_id=s_id,
                    target_entity_id=t_id,
                    relation_type=r["relation_type"],
                    confidence=r["confidence"],
                    evidence_ids_json=[evidence_map.get(evid) for evid in r["evidence_ids_json"] if evid in evidence_map]
                ))

        # Timeline Events
        for te in demo_data["timeline_events"]:
            session.add(TimelineEvent(
                investigation_id=inv.id,
                timestamp=te["timestamp"],
                event_type=te["event_type"],
                title=te["title"],
                description=te["description"],
                entity_id=entity_map.get(te.get("entity_id")),
                evidence_id=evidence_map.get(te.get("evidence_id")),
                confidence=te["confidence"]
            ))

        # Contradictions
        for c in demo_data["contradictions"]:
            session.add(Contradiction(
                investigation_id=inv.id,
                entity_id=entity_map.get(c.get("entity_id")),
                attribute_name=c["attribute_name"],
                source_a_id=evidence_map.get(c["source_a_id"]),
                source_a_name=c["source_a_name"],
                source_a_claim=c["source_a_claim"],
                source_b_id=evidence_map.get(c["source_b_id"]),
                source_b_name=c["source_b_name"],
                source_b_claim=c["source_b_claim"],
                explanation=c["explanation"]
            ))

        inv.status = "completed"
        inv.summary_json = demo_data["summary"]
        await session.commit()
        await event_bus.publish(inv.id, "status_change", {"status": "completed"})


orchestrator = InvestigationOrchestrator()
