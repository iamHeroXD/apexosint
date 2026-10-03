import {
  Workspace,
  Investigation,
  AnalyzedTarget,
  Entity,
  Evidence,
  Relationship,
  TimelineEvent,
  Contradiction,
  OSINTModule,
} from "../types";

const API_BASE = "/api";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error (${res.status}): ${errorText}`);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: () => request<{ status: string; modules_count: number; gemini_active: boolean }>("/health"),

  // Workspaces
  listWorkspaces: () => request<Workspace[]>("/workspaces"),
  createWorkspace: (data: { name: string; description?: string }) =>
    request<Workspace>("/workspaces", { method: "POST", body: JSON.stringify(data) }),

  // Target Analysis (Universal Target Engine)
  analyzeTarget: (query: string) =>
    request<AnalyzedTarget[]>("/target/analyze", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  // Investigations
  listInvestigations: (workspaceId?: string) =>
    request<Investigation[]>(`/investigations${workspaceId ? `?workspace_id=${workspaceId}` : ""}`),
  getInvestigation: (id: string) => request<Investigation>(`/investigations/${id}`),
  createInvestigation: (data: {
    workspace_id: string;
    title: string;
    target_query: string;
    mode: string;
    depth: number;
    is_demo?: boolean;
  }) => request<Investigation>("/investigations", { method: "POST", body: JSON.stringify(data) }),
  runInvestigation: (id: string, wait: boolean = true) =>
    request<{ status: string; investigation_id: string }>(`/investigations/${id}/run${wait ? "?wait=true" : ""}`, { method: "POST" }),
  stopInvestigation: (id: string) =>
    request<{ status: string; investigation_id: string }>(`/investigations/${id}/stop`, { method: "POST" }),

  // Graph & Data
  getEntities: (id: string, type?: string) =>
    request<Entity[]>(`/investigations/${id}/entities${type ? `?type=${type}` : ""}`),
  getEvidence: (id: string, sourceType?: string) =>
    request<Evidence[]>(`/investigations/${id}/evidence${sourceType ? `?source_type=${sourceType}` : ""}`),
  getRelationships: (id: string) => request<Relationship[]>(`/investigations/${id}/relationships`),
  getTimeline: (id: string) => request<TimelineEvent[]>(`/investigations/${id}/timeline`),
  getContradictions: (id: string) => request<Contradiction[]>(`/investigations/${id}/contradictions`),
  getDossier: (id: string) => request<any>(`/investigations/${id}/dossier`),
  getGraph: (id: string, nodeType?: string, minConfidence: number = 0.0) =>
    request<{ nodes: any[]; edges: any[]; stats: any }>(
      `/investigations/${id}/graph?min_confidence=${minConfidence}${nodeType ? `&node_type=${nodeType}` : ""}`
    ),

  // AI Copilot
  aiChat: (data: { investigation_id: string; message: string; mode?: string }) =>
    request<{
      response: string;
      cited_evidence_ids: string[];
      confidence: number;
      classification: string;
      tool_executed?: string;
      tool_args?: any;
      tool_result?: any;
    }>("/ai/chat", { method: "POST", body: JSON.stringify(data) }),

  // Modules
  listModules: () => request<OSINTModule[]>("/modules"),
  toggleModule: (name: string) => request<{ module: string; enabled: boolean }>(`/modules/${name}/toggle`, { method: "POST" }),

  // Reports & Export
  generateReport: (id: string, data: { format?: string; classification?: string }) =>
    request<{ id: string; title: string; classification: string; content_markdown: string }>(
      `/investigations/${id}/reports`,
      { method: "POST", body: JSON.stringify(data) }
    ),
  exportBundle: (id: string) => request<any>(`/investigations/${id}/reports/export`),

  // Demo 1-Click Launch
  launchDemo: () => request<{ status: string; workspace_id: string; investigation_id: string; title: string }>("/demo/launch", { method: "POST" }),

  // Settings & Doctor
  getSettings: () => request<any>("/settings"),
  updateSettings: (data: any) => request<any>("/settings", { method: "POST", body: JSON.stringify(data) }),
  runDoctor: () => request<{ all_passed: boolean; checks: any[] }>("/settings/doctor"),

  // Natural Language Query Parser
  parseQuery: (text: string) =>
    request<{
      original_text: string;
      parsed_targets: Array<{
        value: string;
        type: string;
        label: string;
        confidence: number;
        context: string;
      }>;
      multi_target_query: string;
      is_natural_language: boolean;
    }>("/parse-query", { method: "POST", body: JSON.stringify({ text }) }),
};

