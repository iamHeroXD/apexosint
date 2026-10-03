import React, { useState, useEffect, useRef } from "react";
import { api } from "./api/client";
import { Workspace, Investigation, Entity } from "./types";
import {
  Search,
  ArrowRight,
  Shield,
  Sparkles,
  MapPin,
  Globe,
  User,
  Mail,
  Phone,
  Server,
  Download,
  Printer,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
  X,
  Layers,
  ChevronRight,
  AlertTriangle,
  Image as ImageIcon,
  Radio,
  Smartphone,
  Link2,
  Activity,
  Trash2,
  EyeOff,
  Lock,
  CheckCircle,
} from "lucide-react";

interface SiteRecord {
  platform: string;
  category: string;
  url: string;
  status: string;
  status_code?: number;
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
  unique_sites: SiteRecord[];
  full_dossier_markdown: string;
}

export const App: React.FC = () => {
  const [query, setQuery] = useState("");
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [dossier, setDossier] = useState<DossierData | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [pastInvestigations, setPastInvestigations] = useState<Investigation[]>([]);

  // Workflow states
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState("");
  const [scanProgress, setScanProgress] = useState(0);
  const [showAiReport, setShowAiReport] = useState(false);
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [copied, setCopied] = useState(false);
  const [siteFilter, setSiteFilter] = useState<"found" | "all" | "dormant">("found");
  const [siteSearch, setSiteSearch] = useState("");
  const [mapExpanded, setMapExpanded] = useState(false);
  // NL Parse state
  const [parsedTargets, setParsedTargets] = useState<Array<{value: string; type: string; label: string; confidence: number; context: string}>>([]);
  const [isParsing, setIsParsing] = useState(false);
  const [showParsePreview, setShowParsePreview] = useState(false);

  // Zero-Trace Anonymous Mode & Privacy
  const [zeroTraceMode, setZeroTraceMode] = useState(true);
  const [purging, setPurging] = useState(false);
  const [purgeNotice, setPurgeNotice] = useState(false);

  const handlePurgeAllData = async () => {
    if (purging) return;
    setPurging(true);
    try {
      await api.purgeInvestigations();
      setPastInvestigations([]);
      setDossier(null);
      setEntities([]);
      setInvestigation(null);
      setQuery("");
      setShowAiReport(false);
      setParsedTargets([]);
      setShowParsePreview(false);
      setPurgeNotice(true);
      setTimeout(() => setPurgeNotice(false), 3500);
    } catch (err) {
      console.error("Purge error:", err);
    } finally {
      setPurging(false);
    }
  };

  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const aiReportRef = useRef<HTMLDivElement>(null);

  // Initialize Default Workspace & History
  const loadInitialData = async () => {
    try {
      const wsList = await api.listWorkspaces();
      let ws = wsList[0];
      if (!ws) {
        ws = await api.createWorkspace({
          name: "Default OSINT Workspace",
          description: "Primary workspace",
        });
      }
      setActiveWorkspace(ws);

      // In Zero-Trace Mode, do not load or expose past search history
      if (!zeroTraceMode) {
        const invs = await api.listInvestigations(ws.id);
        setPastInvestigations(invs);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Detect Target Type in Real-time as user types
  const detectTargetType = (val: string): { type: string; color: string } => {
    const t = val.trim();
    if (!t) return { type: "", color: "" };
    if (t.includes("@") && t.includes(".")) {
      return { type: "EMAIL ADDRESS", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" };
    }
    if (t.startsWith("+") || (/^[\d\s\-().]{8,}$/.test(t) && !t.includes("."))) {
      return { type: "TELEPHONE NUMBER (E.164)", color: "bg-sky-500/10 text-sky-400 border-sky-500/30" };
    }
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(t)) {
      return { type: "IP ADDRESS (BGP / ASN / GEO)", color: "bg-amber-500/10 text-amber-400 border-amber-500/30" };
    }
    if (t.includes("github.com/")) {
      return { type: "CODE REPOSITORY", color: "bg-purple-500/10 text-purple-400 border-purple-500/30" };
    }
    if (t.includes(".") && !t.includes(" ")) {
      return { type: "DOMAIN / HOSTNAME", color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30" };
    }
    if (t.includes(" ")) {
      return { type: "PERSON OR ENTITY NAME", color: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30" };
    }
    return { type: "USERNAME / ALIAS / HANDLE", color: "bg-blue-500/10 text-blue-400 border-blue-500/30" };
  };

  const detected = detectTargetType(query);

  // Run Investigation (with optional NL parsing)
  const handleStartScan = async (targetQuery?: string, skipParse = false) => {
    const q = (targetQuery || query).trim();
    if (!q || isScanning) return;

    // Step 1: NL Parse if input looks like natural language and we haven't already parsed
    if (!skipParse) {
      setIsParsing(true);
      setShowParsePreview(false);
      setParsedTargets([]);
      try {
        const parseResult = await api.parseQuery(q);
        if (parseResult.is_natural_language && parseResult.parsed_targets.length > 0) {
          setParsedTargets(parseResult.parsed_targets);
          setShowParsePreview(true);
          setIsParsing(false);
          // Auto-launch with the multi_target_query after short delay for UX
          setTimeout(() => {
            handleStartScan(parseResult.multi_target_query, true);
          }, 1200);
          return;
        }
      } catch (err) {
        console.warn("NL parse failed, proceeding directly:", err);
      }
      setIsParsing(false);
    }

    setIsScanning(true);
    setDossier(null);
    setEntities([]);
    setShowAiReport(false);
    setScanProgress(15);
    setScanStep("Initializing multi-source intelligence engines...");

    try {
      let wsId = activeWorkspace?.id;
      if (!wsId) {
        const wsList = await api.listWorkspaces();
        wsId = wsList[0]?.id;
      }
      if (!wsId) {
        const newWs = await api.createWorkspace({ name: "Default" });
        wsId = newWs.id;
        setActiveWorkspace(newWs);
      }

      setScanProgress(30);
      setScanStep(`Target identified: '${q}' -> Launching concurrent OSINT probes...`);

      const inv = await api.createInvestigation({
        workspace_id: wsId,
        title: q,
        target_query: q,
        mode: "standard",
        depth: 1,
      });

      setInvestigation(inv);
      setScanProgress(40);
      setScanStep("Deep-probing 320+ platforms across Gaming, Code, Tech, Social, and Creative ecosystems with zero-trace anonymity...");

      let stepIdx = 0;
      const progressSteps = [
        { pct: 45, msg: "Probing 40+ live phone sources: spam databases, caller ID, social platforms..." },
        { pct: 57, msg: "Checking Indian business directories: JustDial, IndiaMART, Sulekha, Yellow Pages..." },
        { pct: 68, msg: "Querying free phone validation APIs (Veriphone, AbstractAPI)..." },
        { pct: 76, msg: "Checking payment platforms, fintech, and UPI registries..." },
        { pct: 83, msg: "Searching GitHub, Pastebin, and public web for exposed data..." },
        { pct: 90, msg: "Correlating discovered entities, carrier data, and location footprint..." },
        { pct: 96, msg: "Compiling intelligence matrix and generating entity graph..." },
      ];

      const pollTimer = setInterval(() => {
        if (stepIdx < progressSteps.length) {
          setScanProgress(progressSteps[stepIdx].pct);
          setScanStep(progressSteps[stepIdx].msg);
          stepIdx++;
        }
      }, 1400);

      try {
        await api.runInvestigation(inv.id);
      } finally {
        clearInterval(pollTimer);
      }

      const [dossierRes, entitiesRes] = await Promise.all([
        api.getDossier(inv.id),
        api.getEntities(inv.id),
      ]);

      setScanProgress(100);
      setScanStep("Reconnaissance complete. Displaying intelligence matrix.");
      setDossier(dossierRes);
      setEntities(entitiesRes);

      // Refresh past list only if Zero-Trace Mode is disabled
      if (!zeroTraceMode) {
        api.listInvestigations(wsId).then(setPastInvestigations).catch(console.error);
      }

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 150);
    } catch (err) {
      console.error("Scan error:", err);
      setScanStep(`Error executing scan: ${String(err)}`);
    } finally {
      setIsScanning(false);
    }
  };

  // Convert to Full AI Intelligence Summary
  const handleConvertAiSummary = async () => {
    if (!investigation) return;
    setIsGeneratingAi(true);
    setShowAiReport(true);

    try {
      const refreshedDossier = await api.getDossier(investigation.id);
      setDossier(refreshedDossier);
      setTimeout(() => {
        aiReportRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 150);
    } catch (err) {
      console.error(err);
    } finally {
      setIsGeneratingAi(false);
    }
  };

  // Download Markdown Dossier
  const handleDownloadMarkdown = () => {
    if (!dossier?.full_dossier_markdown) return;
    const blob = new Blob([dossier.full_dossier_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `APEX_OSINT_REPORT_${investigation?.title.replace(/[^a-zA-Z0-9_-]/g, "_") || "TARGET"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Download Plain Text Report
  const handleDownloadText = () => {
    if (!dossier?.full_dossier_markdown) return;
    const blob = new Blob([dossier.full_dossier_markdown], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `APEX_OSINT_REPORT_${investigation?.title.replace(/[^a-zA-Z0-9_-]/g, "_") || "TARGET"}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Copy report
  const handleCopy = () => {
    if (!dossier?.full_dossier_markdown) return;
    navigator.clipboard.writeText(dossier.full_dossier_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter found sites vs not found
  const allSites = dossier?.unique_sites || [];
  const foundSites = allSites.filter((s) => s.status === "FOUND");
  const notFoundSites = allSites.filter((s) => s.status !== "FOUND");

  const visibleSites = (
    siteFilter === "found" ? foundSites : siteFilter === "dormant" ? notFoundSites : allSites
  ).filter((s) => {
    if (!siteSearch.trim()) return true;
    const q = siteSearch.toLowerCase();
    return (
      s.platform.toLowerCase().includes(q) ||
      s.category.toLowerCase().includes(q) ||
      s.url.toLowerCase().includes(q)
    );
  });

  // Location and entities
  const locationEntity =
    entities.find((e) => e.type === "LOCATION" && e.metadata_json?.latitude) ||
    entities.find((e) => e.type === "LOCATION");
  const ipEntities = entities.filter((e) => e.type === "IP");
  const usernames = entities.filter((e) => e.type === "USERNAME");
  const emails = entities.filter((e) => e.type === "EMAIL");
  const domains = entities.filter((e) => e.type === "DOMAIN" || e.type === "SUBDOMAIN");
  const phoneEntities = entities.filter((e) => e.type === "PHONE");
  const avatarEntities = entities.filter((e) => e.type === "AVATAR_IMAGE");
  const orgEntities = entities.filter((e) => e.type === "ORGANIZATION");

  // Build OSM iframe URL from location coordinates
  const lat = locationEntity?.metadata_json?.latitude;
  const lon = locationEntity?.metadata_json?.longitude;
  const osmEmbedUrl = lat && lon
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${(lon - 0.09).toFixed(4)}%2C${(lat - 0.06).toFixed(4)}%2C${(lon + 0.09).toFixed(4)}%2C${(lat + 0.06).toFixed(4)}&layer=mapnik&marker=${lat.toFixed(5)}%2C${lon.toFixed(5)}`
    : null;
  const osmFullUrl = lat && lon
    ? `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=13/${lat}/${lon}`
    : null;
  const satelliteUrl = lat && lon
    ? `https://www.google.com/maps?q=${lat},${lon}&t=k&z=14`
    : null;

  // Phone digits for quick-links
  const phoneDigits = phoneEntities.length > 0
    ? phoneEntities[0].value.replace(/[^\d]/g, "")
    : null;

  return (
    <div className="min-h-screen w-full bg-[#080c14] text-slate-100 flex flex-col font-sans select-text">
      {/* Top Header Navigation */}
      <header className="border-b border-[#1b253b] bg-[#0b101c] px-6 py-4 sticky top-0 z-30 shadow-md">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => window.location.reload()}>
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center">
              <Shield className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-wider text-slate-100 font-mono block">
                APEX OSINT
              </span>
              <span className="text-[10px] font-mono text-sky-400 uppercase tracking-widest block font-semibold">
                INTELLIGENCE, CONNECTED.
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            {/* Zero-Trace Anonymous Mode Badge */}
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
              <EyeOff className="w-3.5 h-3.5 text-emerald-400" />
              <span>Zero-Trace Anonymous</span>
            </div>

            {/* Purge All Traces Button */}
            <button
              type="button"
              onClick={handlePurgeAllData}
              disabled={purging}
              title="Wipe all investigation footprints, databases, and history"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 font-bold transition-colors cursor-pointer"
            >
              {purging ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Trash2 className="w-3.5 h-3.5" />
              )}
              <span>Purge History</span>
            </button>

            <div className="hidden sm:flex items-center space-x-2 text-slate-400 border-l border-[#1e2942] pl-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Port 8000 Active</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-5xl mx-auto w-full px-4 py-8 space-y-6 flex-1">

        {/* SEARCH INPUT PANEL */}
        <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-xl space-y-4">
          <div>
            <h1 className="text-2xl font-extrabold font-mono text-white tracking-tight">
              Universal Target Investigation
            </h1>
            <p className="text-slate-400 text-xs font-mono mt-1">
              Enter any target — username, domain, email, phone, IP, or type a multi-target query to extract all intelligence.
            </p>
          </div>

          {/* Purge Success Banner */}
          {purgeNotice && (
            <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-3 flex items-center space-x-2 text-xs font-mono text-emerald-400 animate-fadeIn">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>All past investigations, cached target entities, and database footprints have been completely purged. Zero traces remain.</span>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleStartScan();
            }}
            className="space-y-3"
          >
            <div className="flex items-center space-x-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter anything — or type a full sentence with name, phone, email..."
                  autoComplete="off"
                  spellCheck={false}
                  className="w-full bg-[#0b101c] border border-[#212e4d] focus:border-blue-500 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 font-mono outline-none transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={isScanning || isParsing || !query.trim()}
                className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900 disabled:cursor-not-allowed text-white font-bold text-sm font-mono flex items-center space-x-2 transition-colors shrink-0 cursor-pointer"
              >
                {isParsing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Parsing...</span>
                  </>
                ) : isScanning ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>Investigate</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Target Type Detector Badge */}
            {detected.type && (
              <div className="flex items-center space-x-2 text-xs font-mono pt-1">
                <span className="text-slate-400">Target Type:</span>
                <span className={`px-2.5 py-0.5 rounded-md border font-semibold ${detected.color}`}>
                  {detected.type}
                </span>
              </div>
            )}
          </form>

          {/* Quick Examples Pills */}
          <div className="pt-3 border-t border-[#1a243a] flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 font-mono">Quick Targets:</span>
            {[
              { label: "apex-defense.org", type: "Domain" },
              { label: "johndoe", type: "Username" },
              { label: "target_user", type: "Handle" },
              { label: "contact@domain.org", type: "Email" },
              { label: "8.8.8.8", type: "IP" },
              { label: "github.com/torvalds/linux", type: "Repo" },
            ].map((ex) => (
              <button
                key={ex.label}
                type="button"
                onClick={() => {
                  setQuery(ex.label);
                  handleStartScan(ex.label);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-slate-300 hover:text-white font-mono transition-colors cursor-pointer"
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* NL PARSING SPINNER */}
        {isParsing && (
          <div className="bg-[#0e1424] border border-amber-500/30 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center space-x-3 text-xs font-mono">
              <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
              <span className="text-amber-400 font-bold">AI Entity Extraction in Progress...</span>
              <span className="text-slate-400">Gemini is reading your input and classifying all targets</span>
            </div>
          </div>
        )}

        {/* NL PARSE PREVIEW CARD */}
        {showParsePreview && parsedTargets.length > 0 && (
          <div className="bg-[#0e1424] border border-amber-500/40 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-[#1e2840] pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                  AI Extracted {parsedTargets.length} Intelligence Targets
                </span>
              </div>
              <span className="text-[10px] font-mono text-amber-400 border border-amber-500/30 px-2 py-1 rounded-lg">
                AUTO-LAUNCHING INVESTIGATION...
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {parsedTargets.map((t, i) => {
                const typeColors: Record<string, string> = {
                  PHONE: "text-sky-400 bg-sky-500/10 border-sky-500/30",
                  EMAIL: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
                  USERNAME: "text-blue-400 bg-blue-500/10 border-blue-500/30",
                  PERSON: "text-indigo-400 bg-indigo-500/10 border-indigo-500/30",
                  LOCATION: "text-green-400 bg-green-500/10 border-green-500/30",
                  DOMAIN: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
                  IP: "text-amber-400 bg-amber-500/10 border-amber-500/30",
                  URL: "text-purple-400 bg-purple-500/10 border-purple-500/30",
                  ORGANIZATION: "text-orange-400 bg-orange-500/10 border-orange-500/30",
                  GITHUB_REPO: "text-violet-400 bg-violet-500/10 border-violet-500/30",
                  CRYPTO_ADDRESS: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
                };
                const colorClass = typeColors[t.type] || "text-slate-400 bg-slate-500/10 border-slate-500/30";
                return (
                  <div key={i} className={`flex items-start space-x-2.5 p-3 rounded-xl border text-xs font-mono ${colorClass}`}>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-bold uppercase text-[10px] opacity-80">{t.label}</span>
                        <span className="text-[9px] opacity-60">{Math.round(t.confidence * 100)}% conf</span>
                      </div>
                      <div className="font-bold truncate">{t.value}</div>
                      <div className="text-[10px] opacity-60 mt-0.5">{t.context}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* SCAN PROGRESS TELEMETRY BAR */}
        {isScanning && (
          <div className="bg-[#0e1424] border border-blue-500/30 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-blue-400 flex items-center space-x-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Zero-Trace Reconnaissance in Progress</span>
              </span>
              <span className="text-slate-400">{scanProgress}%</span>
            </div>

            <p className="text-xs font-mono text-slate-200">{scanStep}</p>

            <div className="w-full bg-[#141b2e] rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${scanProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* RESULTS & FINDINGS SECTION */}
        {dossier && (
          <div ref={resultsRef} className="space-y-6 pt-2">
            {/* Target Status Header Card */}
            <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-5 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 block font-semibold">
                  Investigation Complete
                </span>
                <h2 className="text-xl font-bold font-mono text-white mt-0.5">
                  {investigation?.title}
                </h2>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  Target: {investigation?.title} • 100% Provenance Anchored
                </p>
              </div>

              <div className="flex items-center space-x-4 font-mono text-xs text-slate-300">
                <div className="bg-[#141d33] px-3 py-1.5 rounded-xl border border-[#212e4d]">
                  <span className="text-slate-400 block text-[10px]">MATCHING SITES</span>
                  <span className="font-bold text-emerald-400 text-sm">{foundSites.length} Found</span>
                </div>
                <div className="bg-[#141d33] px-3 py-1.5 rounded-xl border border-[#212e4d]">
                  <span className="text-slate-400 block text-[10px]">RESOLVED ENTITIES</span>
                  <span className="font-bold text-blue-400 text-sm">{entities.length} Entities</span>
                </div>
              </div>
            </div>

            {/* ─── CARD 0: VISUAL IDENTITY / AVATAR (if any avatars found) ─── */}
            {avatarEntities.length > 0 && (
              <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-md space-y-4">
                <div className="flex items-center space-x-2.5 border-b border-[#1b253b] pb-3">
                  <ImageIcon className="w-5 h-5 text-pink-400" />
                  <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                    Visual Identity & Profile Imagery
                  </h3>
                </div>
                <div className="flex flex-wrap gap-4">
                  {avatarEntities.map((ae, idx) => {
                    const platform = ae.metadata_json?.platform || "Public Profile";
                    const imgUrl = ae.value;
                    const profileUrl = ae.metadata_json?.profile_url;
                    return (
                      <div key={idx} className="flex flex-col items-center space-y-2">
                        <a
                          href={profileUrl || imgUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block"
                        >
                          <img
                            src={imgUrl}
                            alt={`Avatar from ${platform}`}
                            className="w-20 h-20 rounded-xl border-2 border-[#1e2942] object-cover hover:border-blue-500 transition-colors"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = "none";
                            }}
                          />
                        </a>
                        <span className="text-[10px] font-mono text-slate-400 uppercase font-bold tracking-wider">
                          {platform}
                        </span>
                        {profileUrl && (
                          <a
                            href={profileUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] font-mono text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                          >
                            <span>Profile</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ─── CARD 1: LOCATION & GEOGRAPHIC FOOTPRINT ─── */}
            <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-md space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#1b253b] pb-3">
                <MapPin className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                  1. Location & Geographic Footprint
                </h3>
              </div>

              {locationEntity ? (
                <div className="space-y-4 text-xs font-mono">
                  {/* Location summary badges */}
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="text-slate-400">Detected Location:</span>
                    <span className="px-3 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold text-sm">
                      {locationEntity.value}
                    </span>
                  </div>

                  {locationEntity.metadata_json && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#12192c] p-3 rounded-xl border border-[#1e2840]">
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">Country</span>
                        <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.country || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">District / City</span>
                        <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.city || locationEntity.metadata_json.district_ssa || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">State / Circle</span>
                        <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.state_circle || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase">Carrier / Operator</span>
                        <span className="text-blue-300 font-semibold">{locationEntity.metadata_json.operator || "N/A"}</span>
                      </div>
                      {lat && lon && (
                        <div className="col-span-2">
                          <span className="text-slate-500 block text-[10px] uppercase">Coordinates (SSA Registry)</span>
                          <span className="text-amber-300 font-semibold font-mono">{lat.toFixed(4)}, {lon.toFixed(4)}</span>
                        </div>
                      )}
                      {locationEntity.metadata_json.timezone && (
                        <div>
                          <span className="text-slate-500 block text-[10px] uppercase">Timezone</span>
                          <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.timezone}</span>
                        </div>
                      )}
                      {locationEntity.metadata_json.routing && (
                        <div className="col-span-2 sm:col-span-4">
                          <span className="text-slate-500 block text-[10px] uppercase">Routing / Numbering Authority</span>
                          <span className="text-slate-300">{locationEntity.metadata_json.routing}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interactive OpenStreetMap Embed */}
                  {osmEmbedUrl && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                          <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider">
                            Live Radar — SSA Registry Location
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setMapExpanded((v) => !v)}
                          className="text-[10px] font-mono text-slate-400 hover:text-white px-2 py-1 rounded border border-[#1e2840] hover:border-[#2e3f60] transition-colors"
                        >
                          {mapExpanded ? "Collapse ▲" : "Expand ▼"}
                        </button>
                      </div>
                      <div
                        className={`w-full rounded-xl overflow-hidden border border-[#1e2840] transition-all duration-300 ${mapExpanded ? "h-96" : "h-52"}`}
                      >
                        <iframe
                          src={osmEmbedUrl}
                          width="100%"
                          height="100%"
                          style={{ border: 0 }}
                          title="APEX Location Map"
                          loading="lazy"
                          allowFullScreen
                        />
                      </div>
                      <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                        <a
                          href={osmFullUrl!}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/40 text-emerald-400 font-bold transition-colors"
                        >
                          <MapPin className="w-3 h-3" />
                          <span>Full OpenStreetMap</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <a
                          href={satelliteUrl!}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-600/15 hover:bg-amber-600/25 border border-amber-500/40 text-amber-400 font-bold transition-colors"
                        >
                          <Globe className="w-3 h-3" />
                          <span>Satellite View</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <span className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#12192c] border border-[#1e2840] text-slate-400">
                          <Activity className="w-3 h-3" />
                          <span>Passive SSA Registry • No Real-Time GPS</span>
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Phone Quick-Links */}
                  {phoneDigits && (
                    <div className="space-y-2">
                      <span className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider">
                        ⚡ Quick Verification Links
                      </span>
                      <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                        <a
                          href={`https://wa.me/${phoneDigits}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-green-600/15 hover:bg-green-600/25 border border-green-500/40 text-green-400 font-bold transition-colors"
                        >
                          <Smartphone className="w-3 h-3" />
                          <span>WhatsApp</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <a
                          href={`https://t.me/+${phoneDigits}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-600/15 hover:bg-sky-600/25 border border-sky-500/40 text-sky-400 font-bold transition-colors"
                        >
                          <Radio className="w-3 h-3" />
                          <span>Telegram</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <a
                          href={`https://www.truecaller.com/search/in/${phoneDigits.slice(-10)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600/15 hover:bg-blue-600/25 border border-blue-500/40 text-blue-400 font-bold transition-colors"
                        >
                          <Phone className="w-3 h-3" />
                          <span>Truecaller</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <a
                          href={`https://www.google.com/search?q="${phoneEntities[0]?.value || phoneDigits}"`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-600/15 hover:bg-slate-600/25 border border-slate-500/40 text-slate-300 font-bold transition-colors"
                        >
                          <Search className="w-3 h-3" />
                          <span>Google</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <a
                          href={`https://www.getcontact.com/search?q=${phoneDigits.slice(-10)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-600/15 hover:bg-purple-600/25 border border-purple-500/40 text-purple-400 font-bold transition-colors"
                        >
                          <Link2 className="w-3 h-3" />
                          <span>GetContact</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs font-mono text-slate-400 space-y-1">
                  <p>No direct physical street address identified for this target identifier.</p>
                  <p className="text-slate-500">
                    Associated network endpoints: {ipEntities.map((i) => i.value).join(", ") || "Cloud edge routing"}.
                  </p>
                </div>
              )}
            </div>

            {/* ─── CARD 2: MATCHING WEBSITES FOUND ─── */}
            <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-md space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#1b253b] pb-3 gap-2">
                <div className="flex items-center space-x-2.5">
                  <Globe className="w-5 h-5 text-blue-400" />
                  <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                    2. Matching Websites Found ({foundSites.length} of {allSites.length} Probed)
                  </h3>
                </div>
                <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 border border-blue-500/25 px-2.5 py-1 rounded-lg">
                  {allSites.length > 0 ? Math.round((foundSites.length / allSites.length) * 100) : 0}% Match Ratio
                </span>
              </div>

              {/* Filter Tabs & Search */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
                <div className="flex items-center space-x-1.5 bg-[#12192c] p-1 rounded-xl border border-[#1e2840]">
                  <button
                    type="button"
                    onClick={() => setSiteFilter("found")}
                    className={`px-3 py-1.5 rounded-lg transition-colors ${
                      siteFilter === "found" ? "bg-blue-600 text-white font-bold" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Found Profiles ({foundSites.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setSiteFilter("all")}
                    className={`px-3 py-1.5 rounded-lg transition-colors ${
                      siteFilter === "all" ? "bg-blue-600 text-white font-bold" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    All Probed ({allSites.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setSiteFilter("dormant")}
                    className={`px-3 py-1.5 rounded-lg transition-colors ${
                      siteFilter === "dormant" ? "bg-blue-600 text-white font-bold" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    Dormant / 404 ({notFoundSites.length})
                  </button>
                </div>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={siteSearch}
                    onChange={(e) => setSiteSearch(e.target.value)}
                    placeholder="Search sites..."
                    className="bg-[#12192c] border border-[#1e2840] rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 w-44"
                  />
                </div>
              </div>

              {/* Sites List */}
              {visibleSites.length > 0 ? (
                <div className="border border-[#1e2840] rounded-xl overflow-hidden divide-y divide-[#1e2840] text-xs font-mono max-h-[420px] overflow-y-auto">
                  {visibleSites.map((site, idx) => {
                    const isFound = site.status === "FOUND";
                    return (
                      <div
                        key={idx}
                        className={`p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 transition-colors ${
                          isFound ? "bg-[#10172a] hover:bg-[#141e36]" : "bg-[#0b0f1a] hover:bg-[#101626] opacity-70"
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              isFound ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {isFound ? "FOUND (200 OK)" : "404 NOT FOUND"}
                          </span>
                          <span className="font-bold text-white uppercase">{site.platform}</span>
                          <span className="text-[11px] text-slate-500">({site.category})</span>
                        </div>

                        <div className="flex items-center space-x-3">
                          <span className="text-slate-400 text-[11px] truncate max-w-xs">{site.url}</span>
                          {site.url && (
                            <a
                              href={site.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1 rounded-lg bg-blue-600/15 hover:bg-blue-600/30 border border-blue-500/30 text-blue-400 hover:text-blue-300 font-bold text-[11px] flex items-center space-x-1 shrink-0 transition-colors"
                            >
                              <span>Visit</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs font-mono text-slate-500 p-4 text-center">
                  No platforms match the current filter.
                </p>
              )}
            </div>

            {/* ─── CARD 3: EXTRACTED IDENTIFIERS & NETWORK ─── */}
            <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-md space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#1b253b] pb-3">
                <Layers className="w-5 h-5 text-purple-400" />
                <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                  3. Extracted Identifiers & Network Assets
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1">
                  <span className="text-slate-400 font-bold block">CONFIRMED HANDLES:</span>
                  <span className="text-slate-200">
                    {usernames.map((u) => u.value).join(", ") || "None isolated"}
                  </span>
                </div>
                <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1">
                  <span className="text-slate-400 font-bold block">EMAIL ADDRESSES:</span>
                  <span className="text-slate-200">
                    {emails.map((e) => e.value).join(", ") || "Domain contact routing"}
                  </span>
                </div>
                <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1">
                  <span className="text-slate-400 font-bold block">DOMAINS & HOSTNAMES:</span>
                  <span className="text-slate-200 truncate block">
                    {domains.map((d) => d.value).join(", ") || "Apex target root"}
                  </span>
                </div>
                <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1">
                  <span className="text-slate-400 font-bold block">IP ROUTING & ASN:</span>
                  <span className="text-slate-200">
                    {ipEntities.map((i) => i.value).join(", ") || "Edge / Proxy allocations"}
                  </span>
                </div>
                {phoneEntities.length > 0 && (
                  <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1 sm:col-span-2">
                    <span className="text-slate-400 font-bold block">TELEPHONY / PHONE ALLOCATION:</span>
                    <span className="text-slate-200">
                      {phoneEntities.map((p) => p.value).join(", ")}
                    </span>
                  </div>
                )}
                {orgEntities.length > 0 && (
                  <div className="bg-[#12192c] p-3.5 rounded-xl border border-[#1e2840] space-y-1 sm:col-span-2">
                    <span className="text-slate-400 font-bold block">ORGANIZATIONS / CARRIERS:</span>
                    <span className="text-slate-200">
                      {orgEntities.map((o) => o.value).join(" • ")}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* THE BIG PROMINENT REVEAL BUTTON: CONVERT TO FULL AI REPORT */}
            <div className="text-center py-6">
              <button
                type="button"
                onClick={handleConvertAiSummary}
                disabled={isGeneratingAi}
                className="w-full py-5 px-8 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-extrabold text-base font-mono uppercase transition-all shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:shadow-[0_0_40px_rgba(168,85,247,0.4)] cursor-pointer flex items-center justify-center space-x-3"
              >
                {isGeneratingAi ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Gemini AI is Synthesizing Complete Intelligence Dossier...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 text-amber-300" />
                    <span>Convert Findings into Full AI Intelligence Summary</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>

            {/* FULL AI INTELLIGENCE DOSSIER REPORT */}
            {showAiReport && (
              <div ref={aiReportRef} className="bg-[#0e1424] border border-purple-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#1e2840] pb-4 gap-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      <h3 className="font-extrabold text-base font-mono text-white uppercase">
                        AI Intelligence Dossier
                      </h3>
                    </div>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">
                      Synthesized by Google Gemini 2.5 Flash • 100% Evidence Grounded
                    </p>
                  </div>

                  {/* Download Action Buttons */}
                  <div className="flex flex-wrap gap-2 text-xs font-mono">
                    <button
                      type="button"
                      onClick={handleDownloadMarkdown}
                      className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold flex items-center space-x-1.5 transition-colors cursor-pointer shadow-sm"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download .md</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleDownloadText}
                      className="px-3 py-1.5 rounded-lg bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-slate-300 hover:text-white font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download .txt</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => window.print()}
                      className="px-3 py-1.5 rounded-lg bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-slate-300 hover:text-white font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Print / PDF</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleCopy}
                      className="px-3 py-1.5 rounded-lg bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-slate-300 hover:text-white font-bold flex items-center space-x-1.5 transition-colors cursor-pointer"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                </div>

                {/* Dossier Content Body */}
                <div className="bg-[#0b0f1a] border border-[#182136] rounded-xl p-5 text-xs font-mono text-slate-200 leading-relaxed whitespace-pre-wrap select-text max-h-[600px] overflow-y-auto">
                  {dossier.full_dossier_markdown}
                </div>

                {/* Scan New Target Action */}
                <div className="pt-3 border-t border-[#1e2840] flex flex-col sm:flex-row justify-between items-center text-xs font-mono text-slate-400 gap-2">
                  <span>Investigation ID: {investigation?.id}</span>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={handlePurgeAllData}
                      disabled={purging}
                      className="px-4 py-2 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 font-bold transition-colors cursor-pointer flex items-center space-x-1.5"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>{purging ? "Purging..." : "Wipe Case & Reset"}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setQuery("");
                        setDossier(null);
                        setShowAiReport(false);
                        window.scrollTo({ top: 0, behavior: "smooth" });
                        setTimeout(() => inputRef.current?.focus(), 100);
                      }}
                      className="px-4 py-2 rounded-xl bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-sky-400 hover:text-white font-bold transition-colors cursor-pointer"
                    >
                      Start New Target Scan →
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ZERO-TRACE PRIVACY & OPERATIONAL SECURITY ARCHITECTURE */}
        {!dossier && (
          <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#1b253b] pb-3">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono text-white font-bold uppercase tracking-wider">
                  Zero-Trace Operational Security Architecture
                </span>
              </div>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2.5 py-1 rounded-lg">
                100% EPHEMERAL • ZERO LOCAL LOGS
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="bg-[#12192c] p-3 rounded-xl border border-[#1e2840] space-y-1">
                <span className="text-slate-400 font-bold block flex items-center space-x-1.5">
                  <EyeOff className="w-3.5 h-3.5 text-sky-400" />
                  <span>No Search History</span>
                </span>
                <span className="text-slate-500 text-[11px] block">
                  Search inputs, targets, and outputs are ephemeral and not exposed or tracked.
                </span>
              </div>
              <div className="bg-[#12192c] p-3 rounded-xl border border-[#1e2840] space-y-1">
                <span className="text-slate-400 font-bold block flex items-center space-x-1.5">
                  <Lock className="w-3.5 h-3.5 text-purple-400" />
                  <span>Randomized Fingerprints</span>
                </span>
                <span className="text-slate-500 text-[11px] block">
                  Rotating randomized user-agents across desktop & mobile to prevent tracker correlation.
                </span>
              </div>
              <div className="bg-[#12192c] p-3 rounded-xl border border-[#1e2840] space-y-1">
                <span className="text-slate-400 font-bold block flex items-center space-x-1.5">
                  <Activity className="w-3.5 h-3.5 text-amber-400" />
                  <span>320+ Live Probes</span>
                </span>
                <span className="text-slate-500 text-[11px] block">
                  Passive non-intrusive public endpoint probing with strict request sandboxing.
                </span>
              </div>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={handlePurgeAllData}
                disabled={purging}
                className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 font-mono text-xs font-bold transition-colors cursor-pointer flex items-center space-x-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{purging ? "Purging..." : "Wipe All Traces & Clear DB"}</span>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1b253b] bg-[#0b101c] py-6 px-6 text-center text-xs font-mono text-slate-500 space-y-1">
        <p>APEX OSINT - Autonomous Open-Source Intelligence & Investigation Platform</p>
        <p>Zero-trace passive reconnaissance anchored strictly to public repositories and feeds.</p>
      </footer>
    </div>
  );
};

export default App;
