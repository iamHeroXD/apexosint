"""Temporal Intelligence and Timeline Analysis Engine for APEX OSINT.

Analyzes chronological state transitions, detects infrastructure deltas,
and answers investigative temporal questions ("What changed?", "What existed before?").
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.timeline import TimelineEvent


class TimelineEngine:
    """Provides high-precision chronological analysis and delta detection across OSINT events."""

    @classmethod
    def get_chronological_events(
        cls,
        events: List[TimelineEvent],
        reverse: bool = False
    ) -> List[TimelineEvent]:
        """Return events sorted strictly by timestamp."""
        return sorted(events, key=lambda e: e.timestamp or datetime.min.replace(tzinfo=timezone.utc), reverse=reverse)

    @classmethod
    def query_before(
        cls,
        events: List[TimelineEvent],
        pivot_time: datetime
    ) -> List[TimelineEvent]:
        """Retrieve all events that occurred prior to a pivot timestamp ('What existed before?')."""
        if pivot_time.tzinfo is None:
            pivot_time = pivot_time.replace(tzinfo=timezone.utc)
        filtered = [
            e for e in events
            if (e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) < pivot_time
        ]
        return cls.get_chronological_events(filtered)

    @classmethod
    def query_after(
        cls,
        events: List[TimelineEvent],
        pivot_time: datetime
    ) -> List[TimelineEvent]:
        """Retrieve all events that occurred after a pivot timestamp ('What appeared after?')."""
        if pivot_time.tzinfo is None:
            pivot_time = pivot_time.replace(tzinfo=timezone.utc)
        filtered = [
            e for e in events
            if (e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) > pivot_time
        ]
        return cls.get_chronological_events(filtered)

    @classmethod
    def detect_temporal_deltas(
        cls,
        events: List[TimelineEvent]
    ) -> List[Dict[str, Any]]:
        """
        Identify significant infrastructure, certificate, or operational shifts over time.
        Answers: 'What changed?'
        """
        sorted_events = cls.get_chronological_events(events)
        deltas: List[Dict[str, Any]] = []

        # Track previous states by event_type / category
        state_tracker: Dict[str, TimelineEvent] = {}

        for ev in sorted_events:
            cat = ev.event_type.upper()
            if cat in state_tracker:
                prev_ev = state_tracker[cat]
                # If titles or descriptions indicate a change
                if prev_ev.title != ev.title or prev_ev.description != ev.description:
                    deltas.append({
                        "category": cat,
                        "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
                        "delta_type": "STATE_TRANSITION",
                        "summary": f"Shift detected in {cat}: from '{prev_ev.title}' to '{ev.title}'",
                        "previous_event_id": prev_ev.id,
                        "current_event_id": ev.id,
                        "evidence_id": ev.evidence_id,
                        "confidence": ev.confidence
                    })
            state_tracker[cat] = ev

        return deltas

    @classmethod
    def generate_timeline_summary(
        cls,
        events: List[TimelineEvent]
    ) -> Dict[str, Any]:
        """Compile executive summary of temporal activity."""
        if not events:
            return {
                "total_events": 0,
                "first_event": None,
                "latest_event": None,
                "deltas_detected": 0,
                "categories": {}
            }

        sorted_events = cls.get_chronological_events(events)
        deltas = cls.detect_temporal_deltas(events)

        category_counts: Dict[str, int] = {}
        for ev in events:
            category_counts[ev.event_type] = category_counts.get(ev.event_type, 0) + 1

        first_ts = sorted_events[0].timestamp
        last_ts = sorted_events[-1].timestamp

        return {
            "total_events": len(events),
            "first_event_timestamp": first_ts.isoformat() if first_ts else None,
            "latest_event_timestamp": last_ts.isoformat() if last_ts else None,
            "span_days": round((last_ts - first_ts).total_seconds() / 86400.0, 1) if first_ts and last_ts else 0,
            "deltas_count": len(deltas),
            "deltas": deltas,
            "category_breakdown": category_counts
        }
