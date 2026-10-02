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

      const invs = await api.listInvestigations(ws.id);
      setPastInvestigations(invs);
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

  // Run Investigation
  const handleStartScan = async (targetQuery?: string) => {
    const q = (targetQuery || query).trim();
    if (!q || isScanning) return;

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
      setScanStep("Deep-probing 125+ platforms across Gaming, Code, Tech, Social, and Creative ecosystems...");

      // Launch investigation with wait=true
      let stepIdx = 0;
      const progressSteps = [
        { pct: 55, msg: "Probing developer platforms, code repositories, and public endpoints..." },
        { pct: 70, msg: "Checking DNS, RDAP, Geolocation coordinates, and Certificate Transparency..." },
        { pct: 85, msg: "Correlating discovered identities, usernames, and organization relationships..." },
        { pct: 95, msg: "Resolving entity graph clusters and compiling intelligence matrix..." },
      ];

      const pollTimer = setInterval(() => {
        if (stepIdx < progressSteps.length) {
          setScanProgress(progressSteps[stepIdx].pct);
          setScanStep(progressSteps[stepIdx].msg);
          stepIdx++;
        }
      }, 700);

      try {
        await api.runInvestigation(inv.id, true);
      } finally {
        clearInterval(pollTimer);
      }

      setScanProgress(98);
      setScanStep("Loading synthesized intelligence dossier and discovered entities...");

      // Fetch resulting dossier and entities
      const [dossierRes, entitiesRes] = await Promise.all([
        api.getDossier(inv.id),
        api.getEntities(inv.id),
      ]);

      setScanProgress(100);
      setScanStep("Reconnaissance complete. Displaying intelligence matrix.");
      setDossier(dossierRes);
      setEntities(entitiesRes);

      // Refresh past list
      api.listInvestigations(wsId).then(setPastInvestigations).catch(console.error);

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

          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-400">Local Engine Active (Port 8000)</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10 space-y-8">
        {/* Hero Headline */}
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/25 text-blue-400 text-xs font-mono font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Multi-Source OSINT Investigation Platform</span>
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Investigate Any Public Target
          </h1>
          <p className="text-sm text-slate-400">
            One input for email, phone, username, full name, IP, domain, or repository.
            Passively searches 40+ platforms, resolves geographic locations, and summarizes with AI.
          </p>
        </div>

        {/* ONE MASSIVE UNIVERSAL SEARCH INPUT */}
        <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-2xl space-y-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleStartScan();
            }}
            className="space-y-3"
          >
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter email, phone number, username, name, IP, or domain..."
                  className="w-full bg-[#131b2e] border border-[#233150] focus:border-blue-500 focus:bg-[#162038] text-white text-base rounded-xl pl-12 pr-10 py-3 font-mono focus:outline-none placeholder-slate-500 transition-colors"
                  disabled={isScanning}
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery("")}
                    className="absolute right-3 top-3.5 text-slate-400 hover:text-white p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={isScanning || !query.trim()}
                className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm font-mono flex items-center justify-center space-x-2 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 disabled:pointer-events-none cursor-pointer shrink-0"
              >
                {isScanning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Investigating...</span>
                  </>
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
              { label: "johnsmith", type: "Username" },
              { label: "rohan123", type: "Handle" },
              { label: "someone@example.com", type: "Email" },
              { label: "+91 98765 43210", type: "Phone" },
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

            {/* CARD 1: LOCATION & GEOGRAPHIC FOOTPRINT */}
            <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-6 shadow-md space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-[#1b253b] pb-3">
                <MapPin className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                  1. Location & Geographic Footprint
                </h3>
              </div>

              {locationEntity ? (
                <div className="space-y-3 text-xs font-mono">
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className="text-slate-400">Detected Location:</span>
                    <span className="px-3 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold text-sm">
                      {locationEntity.value}
                    </span>
                  </div>

                  {locationEntity.metadata_json && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-[#12192c] p-3 rounded-xl border border-[#1e2840]">
                      <div>
                        <span className="text-slate-500 block text-[10px]">COUNTRY:</span>
                        <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.country || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">CITY / REGION:</span>
                        <span className="text-slate-200 font-semibold">{locationEntity.metadata_json.city || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">COORDINATES:</span>
                        <span className="text-slate-200 font-semibold">
                          {locationEntity.metadata_json.latitude && locationEntity.metadata_json.longitude
                            ? `${locationEntity.metadata_json.latitude}, ${locationEntity.metadata_json.longitude}`
                            : "Approximate BGP"}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* OpenStreetMap Direct Map Button */}
                  {locationEntity.metadata_json?.latitude && locationEntity.metadata_json?.longitude && (
                    <a
                      href={`https://www.openstreetmap.org/?mlat=${locationEntity.metadata_json.latitude}&mlon=${locationEntity.metadata_json.longitude}#map=12/${locationEntity.metadata_json.latitude}/${locationEntity.metadata_json.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/40 text-emerald-400 font-bold text-xs transition-colors"
                    >
                      <MapPin className="w-3.5 h-3.5" />
                      <span>Open Interactive Location on OpenStreetMap</span>
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
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

            {/* CARD 2: MATCHING WEBSITES FOUND (COUNT & PROFILE MATRIX) */}
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

            {/* CARD 3: EXTRACTED IDENTIFIERS & NETWORK */}
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
            )}
          </div>
        )}

        {/* PAST INVESTIGATIONS HISTORY */}
        {pastInvestigations.length > 0 && !dossier && (
          <div className="bg-[#0e1424] border border-[#1e2942] rounded-2xl p-5 space-y-3">
            <span className="text-xs font-mono text-slate-400 font-bold block uppercase tracking-wider">
              Recent Case History:
            </span>
            <div className="flex flex-wrap gap-2 text-xs font-mono">
              {pastInvestigations.slice(0, 8).map((inv) => (
                <button
                  key={inv.id}
                  type="button"
                  onClick={() => {
                    setQuery(inv.title);
                    handleStartScan(inv.title);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-[#141d33] hover:bg-[#1a2642] border border-[#212e4d] text-slate-300 hover:text-white transition-colors cursor-pointer flex items-center space-x-1.5"
                >
                  <span>{inv.title}</span>
                  <ChevronRight className="w-3 h-3 text-slate-500" />
                </button>
              ))}
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
