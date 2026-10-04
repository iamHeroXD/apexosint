export interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  investigations_count: number;
}

export interface TargetHypothesis {
  type: string;
  confidence: number;
  percentage: number;
  explanation: string;
  recommended_modules: string[];
}

export interface AnalyzedTarget {
  raw_input: string;
  normalized_value: string;
  primary_type: string;
  primary_confidence: number;
  hypotheses: TargetHypothesis[];
  planned_investigation: string[];
  extraction_metadata: Record<string, any>;
}

export interface Investigation {
  id: string;
  workspace_id: string;
  title: string;
  status: "pending" | "running" | "paused" | "completed" | "failed";
  mode: "quick" | "standard" | "deep" | "custom";
  depth: number;
  is_demo: boolean;
  summary_json?: {
    entities_count: number;
    evidence_count: number;
    relationships_count: number;
    sources_count: number;
    high_confidence_count: number;
    contradictions_count: number;
    clusters_count?: number;
    identity_hypotheses?: any[];
    timeline_metrics?: any;
    executive_summary?: string;
  };
  created_at: string;
}

export interface Entity {
  id: string;
  type: string;
  value: string;
  normalized_value: string;
  cluster_id?: string;
  confidence: number;
  provenance_label: "OBSERVED" | "CORROBORATED" | "AI_INFERENCE" | "UNVERIFIED" | "CONFLICTED";
  is_bookmarked: boolean;
  first_seen: string;
  metadata_json?: Record<string, any>;
}

export interface Evidence {
  id: string;
  source_name: string;
  source_type: string;
  source_url?: string;
  collection_method: string;
  confidence: number;
  source_reliability?: number;
  epistemic_label: "OBSERVED" | "CORROBORATED" | "CONFLICTED" | "INFERRED" | "UNVERIFIED" | "STALE";
  corroboration_count?: number;
  independent_source_count?: number;
  snippet: string;
  raw_payload_json?: Record<string, any>;
  related_entity_ids_json?: string[];
  collected_at: string;
  first_seen?: string;
  last_seen?: string;
  is_bookmarked: boolean;
}

export interface Relationship {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relation_type: string;
  confidence: number;
  discovery_method?: string;
  explanation?: string;
  discovered_at?: string;
  is_ai_inferred: boolean;
  evidence_ids_json?: string[];
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  description: string;
  confidence: number;
  entity_id?: string;
  evidence_id?: string;
}

export interface Contradiction {
  id: string;
  attribute_name: string;
  source_a_name: string;
  source_a_claim: string;
  source_b_name: string;
  source_b_claim: string;
  explanation: string;
  resolved: boolean;
}

export interface OSINTModule {
  name: string;
  display_name: string;
  description: string;
  category: string;
  target_types: string[];
  rate_limit: number;
  source: string;
  license: string;
  enabled: boolean;
  safety_level: string;
  average_latency_ms: number;
  error_rate: number;
  last_run?: string;
  status: "HEALTHY" | "DEGRADED" | "DISABLED";
}

export interface AIChatMessage {
  id: string;
  sender: "user" | "copilot";
  mode?: string;
  text: string;
  cited_evidence_ids?: string[];
  classification?: string;
  tool_executed?: string;
  tool_result?: any;
  timestamp: string;
}
