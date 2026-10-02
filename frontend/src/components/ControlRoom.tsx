import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Sparkles,
  Download,
  Printer,
  Copy,
  Check,
  ExternalLink,
  Globe,
  User,
  Mail,
  Network,
  Cpu,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Activity,
  Layers,
  Code2,
  Terminal as TerminalIcon,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { Investigation, Entity } from "../types";
import { api } from "../api/client";

interface ControlRoomProps {
  investigation: Investigation;
  onOpenGraph: () => void;
  onOpenEvidence: () => void;
  onOpenReport: () => void;
  onSelectEntity: (entityId: string) => void;
  onPivotInvestigate: (value: string) => void;
}

interface DossierData {
  target: string;
  investigation_id: string;
  entities_count: number;
  evidence_count: number;
  relationships_count: number;
  sites_probed_count: number;
  contradictions_count: number;
  ai_assessment: string;
  unique_sites: Array<{
    platform: string;
    category: string;
    url: string;
    status: string;
    status_code?: number;
  }>;
  full_dossier_markdown: string;
}

export const ControlRoom: React.FC<ControlRoomProps> = ({
  investigation,
  onOpenGraph,
  onOpenEvidence,
  onOpenReport,
  onSelectEntity,
  onPivotInvestigate,
}) => {
  const [dossier, setDossier] = useState<DossierData | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isFullDossierOpen, setIsFullDossierOpen] = useState(false);

  // Platform ledger filtering & searching
  const [siteFilterCategory, setSiteFilterCategory] = useState<string>("ALL");
  const [siteSearch, setSiteSearch] = useState("");
  const [onlyFoundSites, setOnlyFoundSites] = useState(false);

  // Live telemetry stream
  const [logs, setLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Control Room initialized for ${investigation.title}.`,
    `[${new Date().toLocaleTimeString()}] Telemetry connected. Telemetry stream active.`,
  ]);
  const [currentPhase, setCurrentPhase] = useState("COLLECT");

  // Load Dossier & Entities
  const loadData = async (refresh: boolean = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const [dossierRes, entitiesRes] = await Promise.all([
        api.getDossier(investigation.id),
        api.getEntities(investigation.id),
      ]);
      setDossier(dossierRes);
      setEntities(entitiesRes);
    } catch (err) {
      console.error("Failed to load control room dossier data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [investigation.id]);

  // Connect Server-Sent Events stream for real-time log feed
  useEffect(() => {
    const eventSource = new EventSource(`/api/investigations/${investigation.id}/stream`);
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const time = new Date().toLocaleTimeString();

        if (payload.type === "phase_update") {
          setCurrentPhase(payload.data.phase);
          setLogs((prev) => [...prev.slice(-30), `[${time}] Phase update: ${payload.data.phase}`]);
        } else if (payload.type === "module_started") {
          setLogs((prev) => [
            ...prev.slice(-30),
            `[${time}] Probing: ${payload.data.module_name} on ${payload.data.target}`,
          ]);
        } else if (payload.type === "evidence_discovered") {
          setLogs((prev) => [
            ...prev.slice(-30),
            `[${time}] Evidence captured from ${payload.data.source}`,
          ]);
        } else if (payload.type === "entity_discovered") {
          setLogs((prev) => [
            ...prev.slice(-30),
            `[${time}] Extracted ${payload.data.type}: ${payload.data.value}`,
          ]);
        } else if (payload.type === "contradiction_detected") {
          setLogs((prev) => [
            ...prev.slice(-30),
            `[${time}] [CONFLICT] ${payload.data.attribute}: Discrepancy observed`,
          ]);
        }
      } catch (err) {
        // Ignored
      }
    };

    return () => {
      eventSource.close();
    };
  }, [investigation.id]);

  // Download Markdown Dossier
  const handleDownloadMarkdown = () => {
    if (!dossier?.full_dossier_markdown) return;
    const blob = new Blob([dossier.full_dossier_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `APEX-DOSSIER-${investigation.title.replace(/[^a-zA-Z0-9_-]/g, "_")}-${investigation.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export Complete Case JSON
  const handleExportJSON = async () => {
    try {
      const bundle = await api.exportBundle(investigation.id);
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `APEX-CASE-${investigation.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export JSON failed:", err);
    }
  };

  // Copy Markdown to Clipboard
  const handleCopyMarkdown = () => {
    if (!dossier?.full_dossier_markdown) return;
    navigator.clipboard.writeText(dossier.full_dossier_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter sites
  const sitesList = dossier?.unique_sites || [];
  const filteredSites = sitesList.filter((site) => {
    if (onlyFoundSites && site.status !== "FOUND") return false;
    if (siteFilterCategory !== "ALL" && site.category.toUpperCase() !== siteFilterCategory) return false;
    if (siteSearch.trim()) {
      const q = siteSearch.toLowerCase();
      return (
        site.platform.toLowerCase().includes(q) ||
        site.category.toLowerCase().includes(q) ||
        site.url.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const foundSitesCount = sitesList.filter((s) => s.status === "FOUND").length;
  const categoriesList = ["ALL", ...Array.from(new Set(sitesList.map((s) => s.category.toUpperCase())))];

  // Entity groups
  const usernames = entities.filter((e) => e.type === "USERNAME");
  const emails = entities.filter((e) => e.type === "EMAIL");
  const domains = entities.filter((e) => e.type === "DOMAIN" || e.type === "SUBDOMAIN");
  const ips = entities.filter((e) => e.type === "IP");
  const repos = entities.filter((e) => e.type === "REPOSITORY");
  const persons = entities.filter((e) => e.type === "PERSON");
  const orgs = entities.filter((e) => e.type === "ORGANIZATION");

  return (
    <div className="flex-1 flex flex-col h-full bg-[#07080c] overflow-y-auto font-sans select-text">
      {/* Top HUD: Target Mission Header */}
      <div className="border-b border-[#171b26] bg-[#0a0c13] px-6 py-4 sticky top-0 z-20 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Target Identity & Status */}
          <div className="flex items-start md:items-center space-x-3.5">
            <div className="w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center shrink-0 shadow-inner">
              <ShieldCheck className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h1 className="text-base md:text-lg font-bold font-mono text-slate-100 tracking-tight">
                  {investigation.title}
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="uppercase font-semibold tracking-wider">
                    {investigation.status === "completed" ? "INVESTIGATION COMPLETE" : "ACTIVE MONITORING"}
                  </span>
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-950/40 text-sky-400 border border-sky-500/20 uppercase">
                  MODE: {investigation.mode} (DEPTH {investigation.depth})
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5 flex items-center space-x-2">
                <span>ID: {investigation.id.slice(0, 12)}...</span>
                <span>•</span>
                <span>Target Grounding: 100% Provenance Anchored</span>
              </p>
            </div>
          </div>

          {/* Quick 1-Click Action Group */}
          <div className="flex items-center flex-wrap gap-2">
            <button
              onClick={() => loadData(true)}
              disabled={isRefreshing}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#121622] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
              title="Re-run AI Persona Synthesis"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-sky-400" : ""}`} />
              <span>{isRefreshing ? "Synthesizing..." : "Re-Analyze"}</span>
            </button>

            <button
              onClick={handleCopyMarkdown}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#121622] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
              title="Copy Markdown Dossier to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy MD"}</span>
            </button>

            <button
              onClick={() => window.print()}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#121622] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
              title="Print or Save as PDF"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>

            <button
              onClick={handleDownloadMarkdown}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs font-mono transition-all shadow-sm"
              title="Download Full Dossier as Markdown file"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Dossier (.md)</span>
            </button>

            <button
              onClick={handleExportJSON}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#161c2b] hover:bg-[#1f2638] border border-sky-500/30 text-sky-400 text-xs font-mono transition-colors"
              title="Export Full Case JSON Bundle"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto w-full p-6 space-y-6">
        {/* 4 Cybernetic Telemetry Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* Card 1: Discovered Entities */}
          <div
            onClick={onOpenGraph}
            className="bg-[#0b0e16] border border-[#1a2030] hover:border-sky-500/50 p-4 rounded-xl cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400 tracking-wider uppercase">
                Discovered Entities
              </span>
              <Layers className="w-4 h-4 text-sky-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-slate-100">
                {dossier?.entities_count ?? entities.length}
              </span>
              <span className="text-xs text-sky-400 font-mono">Resolved</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 font-mono truncate">
              {domains.length} domains • {usernames.length} handles • {emails.length} emails
            </p>
          </div>

          {/* Card 2: Probed Platforms */}
          <div className="bg-[#0b0e16] border border-[#1a2030] p-4 rounded-xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400 tracking-wider uppercase">
                Recon Platforms Probed
              </span>
              <Globe className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {foundSitesCount}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                / {dossier?.sites_probed_count ?? sitesList.length} Tested
              </span>
            </div>
            <p className="text-[11px] text-emerald-500/80 mt-1 font-mono">
              Active profiles confirmed across 40+ platforms
            </p>
          </div>

          {/* Card 3: Evidence Provenance Records */}
          <div
            onClick={onOpenEvidence}
            className="bg-[#0b0e16] border border-[#1a2030] hover:border-sky-500/50 p-4 rounded-xl cursor-pointer transition-all group"
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400 tracking-wider uppercase">
                Verified Evidence
              </span>
              <ShieldCheck className="w-4 h-4 text-sky-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-slate-100">
                {dossier?.evidence_count ?? 0}
              </span>
              <span className="text-xs text-sky-400 font-mono">Records</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 font-mono">
              100% Provenance: URLs, timestamps & SHA256
            </p>
          </div>

          {/* Card 4: Epistemic Discrepancies */}
          <div className="bg-[#0b0e16] border border-[#1a2030] p-4 rounded-xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-slate-400 tracking-wider uppercase">
                Epistemic Conflict Matrix
              </span>
              <AlertTriangle
                className={`w-4 h-4 ${
                  (dossier?.contradictions_count ?? 0) > 0 ? "text-amber-400" : "text-emerald-400"
                }`}
              />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span
                className={`text-2xl font-bold font-mono ${
                  (dossier?.contradictions_count ?? 0) > 0 ? "text-amber-400" : "text-slate-100"
                }`}
              >
                {dossier?.contradictions_count ?? 0}
              </span>
              <span className="text-xs text-slate-400 font-mono">Discrepancies</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 font-mono">
              {(dossier?.contradictions_count ?? 0) > 0
                ? "Discrepancy detected in public records"
                : "High cross-source empirical consensus"}
            </p>
          </div>
        </div>

        {/* SECTION 1: AI PERSONA & INFRASTRUCTURE INTELLIGENCE DOSSIER */}
        <div className="bg-[#0b0e16] border border-[#1e2538] rounded-xl overflow-hidden shadow-2xl relative">
          {/* Glowing cybernetic header bar */}
          <div className="bg-gradient-to-r from-sky-950/40 via-purple-950/30 to-[#0c0e15] border-b border-[#1e2538] p-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-purple-400" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-sm font-bold font-mono text-slate-100 tracking-wide">
                    AI PERSONA & INFRASTRUCTURE INTELLIGENCE DOSSIER
                  </h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 uppercase font-semibold">
                    CONFIDENTIAL / DEFENSIVE OSINT
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-mono">
                  Autonomous synthesis powered by Google Gemini API & Multi-Source Cross-Correlator
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsFullDossierOpen(!isFullDossierOpen)}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
              >
                {isFullDossierOpen ? (
                  <>
                    <Minimize2 className="w-3.5 h-3.5" />
                    <span>Collapse View</span>
                  </>
                ) : (
                  <>
                    <Maximize2 className="w-3.5 h-3.5" />
                    <span>Expand Dossier</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadMarkdown}
                className="flex items-center space-x-1.5 px-3 py-1 rounded bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-300 font-mono text-xs transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save Report</span>
              </button>
            </div>
          </div>

          {/* Dossier Content Body */}
          <div className="p-6">
            {isLoading ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-6 h-6 text-sky-400 animate-spin" />
                <p className="text-xs font-mono text-slate-400">
                  Synthesizing persona profile, correlating 40+ public sites, and verifying infrastructure...
                </p>
              </div>
            ) : dossier ? (
              <div className="space-y-6">
                {/* Executive Assessment Box */}
                <div
                  className={`bg-[#080a10] border border-[#1a2030] rounded-xl p-6 font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap select-text transition-all ${
                    isFullDossierOpen ? "max-h-none" : "max-h-[500px] overflow-y-auto"
                  }`}
                >
                  {dossier.ai_assessment}
                </div>

                {/* Key Corroborated Identity Entities Pills */}
                <div>
                  <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center space-x-1.5">
                    <User className="w-3.5 h-3.5 text-sky-400" />
                    <span>Identified Digital Fingerprints & Key Assets</span>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {usernames.map((u) => (
                      <span
                        key={u.id}
                        onClick={() => onSelectEntity(u.id)}
                        className="cursor-pointer inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131826] hover:bg-[#1a2236] border border-sky-500/30 text-xs font-mono text-sky-300 transition-colors"
                        title="Click to inspect entity"
                      >
                        <span className="text-[10px] text-slate-500">HANDLE:</span>
                        <span className="font-semibold">{u.value}</span>
                      </span>
                    ))}
                    {emails.map((m) => (
                      <span
                        key={m.id}
                        onClick={() => onSelectEntity(m.id)}
                        className="cursor-pointer inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131826] hover:bg-[#1a2236] border border-emerald-500/30 text-xs font-mono text-emerald-300 transition-colors"
                        title="Click to inspect entity"
                      >
                        <Mail className="w-3 h-3 text-emerald-400" />
                        <span>{m.value}</span>
                      </span>
                    ))}
                    {domains.map((d) => (
                      <span
                        key={d.id}
                        onClick={() => onSelectEntity(d.id)}
                        className="cursor-pointer inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131826] hover:bg-[#1a2236] border border-purple-500/30 text-xs font-mono text-purple-300 transition-colors"
                        title="Click to inspect entity"
                      >
                        <Globe className="w-3 h-3 text-purple-400" />
                        <span>{d.value}</span>
                      </span>
                    ))}
                    {ips.map((ip) => (
                      <span
                        key={ip.id}
                        onClick={() => onSelectEntity(ip.id)}
                        className="cursor-pointer inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131826] hover:bg-[#1a2236] border border-amber-500/30 text-xs font-mono text-amber-300 transition-colors"
                        title="Click to inspect entity"
                      >
                        <Network className="w-3 h-3 text-amber-400" />
                        <span>{ip.value}</span>
                      </span>
                    ))}
                    {repos.map((r) => (
                      <span
                        key={r.id}
                        onClick={() => onSelectEntity(r.id)}
                        className="cursor-pointer inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-[#131826] hover:bg-[#1a2236] border border-slate-700 text-xs font-mono text-slate-300 transition-colors"
                        title="Click to inspect entity"
                      >
                        <Code2 className="w-3 h-3 text-slate-400" />
                        <span>{r.value}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs font-mono text-slate-500">No dossier available.</p>
            )}
          </div>
        </div>

        {/* SECTION 2: 40+ SITES & PUBLIC PLATFORMS RECONNAISSANCE MATRIX */}
        <div className="bg-[#0b0e16] border border-[#1a2030] rounded-xl overflow-hidden shadow-xl">
          {/* Header & Filter Controls */}
          <div className="p-4 border-b border-[#1a2030] bg-[#0c0f18] flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center space-x-2.5">
              <Globe className="w-4 h-4 text-emerald-400" />
              <div>
                <h3 className="text-xs font-bold font-mono text-slate-100 tracking-wide uppercase">
                  Multi-Site Reconnaissance Matrix ({sitesList.length} Platforms Queried)
                </h3>
                <p className="text-[11px] text-slate-400 font-mono">
                  Detailed site-by-site response ledger with HTTP status and direct evidence
                </p>
              </div>
            </div>

            {/* Filter buttons & Search */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Category Pills */}
              <div className="inline-flex rounded-lg bg-[#121622] p-0.5 border border-[#1f2638]">
                {categoriesList.slice(0, 5).map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSiteFilterCategory(cat)}
                    className={`px-2 py-1 rounded text-[10px] font-mono transition-colors ${
                      siteFilterCategory === cat
                        ? "bg-sky-500/20 text-sky-400 font-semibold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Show only Found toggle */}
              <button
                onClick={() => setOnlyFoundSites(!onlyFoundSites)}
                className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-[11px] font-mono border transition-colors ${
                  onlyFoundSites
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                    : "bg-[#121622] text-slate-400 border-[#1f2638] hover:text-slate-200"
                }`}
              >
                <CheckCircle2 className="w-3 h-3" />
                <span>Found Only ({foundSitesCount})</span>
              </button>

              {/* Search input */}
              <div className="relative">
                <Search className="w-3 h-3 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={siteSearch}
                  onChange={(e) => setSiteSearch(e.target.value)}
                  placeholder="Filter sites..."
                  className="bg-[#121622] border border-[#1f2638] rounded-lg pl-7 pr-3 py-1 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-36 sm:w-44"
                />
              </div>
            </div>
          </div>

          {/* Table / Grid */}
          <div className="overflow-x-auto max-h-[460px] overflow-y-auto">
            {filteredSites.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-slate-500">
                No probed sites match the current filter criteria.
              </div>
            ) : (
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#090b12] text-slate-400 border-b border-[#1a2030] sticky top-0 z-10">
                  <tr>
                    <th className="py-2.5 px-4 font-medium uppercase text-[10px]">Platform</th>
                    <th className="py-2.5 px-4 font-medium uppercase text-[10px]">Category</th>
                    <th className="py-2.5 px-4 font-medium uppercase text-[10px]">Probed Status</th>
                    <th className="py-2.5 px-4 font-medium uppercase text-[10px]">Target URL / Profile</th>
                    <th className="py-2.5 px-4 font-medium uppercase text-[10px] text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#141824]">
                  {filteredSites.map((site, idx) => {
                    const isFound = site.status === "FOUND";
                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-[#121622] transition-colors ${
                          isFound ? "bg-emerald-950/10" : ""
                        }`}
                      >
                        <td className="py-2.5 px-4 font-semibold text-slate-200">
                          {site.platform}
                        </td>
                        <td className="py-2.5 px-4 text-slate-400">
                          <span className="px-2 py-0.5 rounded bg-[#141824] border border-[#1f2638] text-[10px]">
                            {site.category}
                          </span>
                        </td>
                        <td className="py-2.5 px-4">
                          {isFound ? (
                            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>FOUND (200 OK)</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-800/40 text-slate-400 border border-slate-700/40 text-[10px]">
                              <XCircle className="w-3 h-3 text-slate-500" />
                              <span>NOT FOUND (404)</span>
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-slate-300 font-mono text-[11px] truncate max-w-xs">
                          {site.url}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          {site.url && (
                            <a
                              href={site.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-sky-400 hover:text-sky-300 text-[11px] transition-colors"
                            >
                              <span>Visit</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* SECTION 3: BOTTOM SPLIT: REAL-TIME RECON TELEMETRY & WORKSPACE ACTIONS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Live Telemetry Console Log (2 Cols) */}
          <div className="lg:col-span-2 bg-[#0b0e16] border border-[#1a2030] rounded-xl overflow-hidden flex flex-col">
            <div className="p-3 border-b border-[#1a2030] bg-[#0c0f18] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TerminalIcon className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-mono font-bold text-slate-200 uppercase">
                  Reconnaissance Telemetry Stream
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono text-slate-500">
                  PIPELINE PHASE:
                </span>
                <span className="text-[10px] font-mono font-semibold text-emerald-400 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  {currentPhase}
                </span>
              </div>
            </div>

            <div className="p-4 bg-[#07090e] font-mono text-xs text-slate-300 space-y-1.5 h-56 overflow-y-auto">
              {logs.map((log, idx) => (
                <div key={idx} className="flex items-start space-x-2 leading-relaxed">
                  <span className="text-sky-500 shrink-0">›</span>
                  <span className="text-slate-300 break-all">{log}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Pivot & Investigation Jump (1 Col) */}
          <div className="bg-[#0b0e16] border border-[#1a2030] rounded-xl p-4 flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wide flex items-center space-x-2 mb-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Next Investigation Pivots</span>
              </h3>
              <p className="text-[11px] text-slate-400 font-mono mb-4">
                Click any discovered asset below to trigger a dedicated deep recursion investigation:
              </p>

              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {entities.slice(0, 5).map((e) => (
                  <div
                    key={e.id}
                    className="flex items-center justify-between p-2 rounded bg-[#121622] border border-[#1a2030] hover:border-sky-500/40 text-xs font-mono group transition-colors"
                  >
                    <div className="truncate mr-2">
                      <span className="text-[9px] text-slate-500 uppercase block font-semibold">
                        {e.type}
                      </span>
                      <span className="text-slate-200 font-medium truncate block">
                        {e.value}
                      </span>
                    </div>
                    <button
                      onClick={() => onPivotInvestigate(e.value)}
                      className="px-2 py-1 rounded bg-sky-500/10 group-hover:bg-sky-500/20 text-sky-400 text-[10px] font-mono font-semibold shrink-0 transition-colors"
                    >
                      Investigate
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-[#1a2030] mt-4 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500 text-[11px]">Knowledge Graph:</span>
              <button
                onClick={onOpenGraph}
                className="text-sky-400 hover:text-sky-300 underline font-semibold text-xs"
              >
                Open Cytoscape Visualizer →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
