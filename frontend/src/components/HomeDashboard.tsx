import React, { useState } from "react";
import {
  Search,
  ArrowRight,
  Sparkles,
  Zap,
  Shield,
  Compass,
  CheckCircle2,
  Layers,
  Activity,
  Globe,
  User,
  Mail,
  Phone,
  Server,
  Code2,
  X,
  ChevronRight,
  TrendingUp,
  Clock,
  Check,
} from "lucide-react";
import { Investigation } from "../types";

interface HomeDashboardProps {
  onStartInvestigation: (query: string, mode: string, depth: number) => void;
  investigations: Investigation[];
  onSelectInvestigation: (inv: Investigation) => void;
  onViewAllInvestigations: () => void;
  onViewAllActivity: () => void;
  isStarting: boolean;
}

const QUICK_CHIPS = [
  { label: "example.com", icon: Globe, type: "domain" },
  { label: "johnsmith", icon: User, type: "username" },
  { label: "someone@example.com", icon: Mail, type: "email" },
  { label: "+91 98765 43210", icon: Phone, type: "phone" },
  { label: "8.8.8.8", icon: Server, type: "ip" },
  { label: "github.com/user/repo", icon: Code2, type: "repo" },
];

export const HomeDashboard: React.FC<HomeDashboardProps> = ({
  onStartInvestigation,
  investigations,
  onSelectInvestigation,
  onViewAllInvestigations,
  onViewAllActivity,
  isStarting,
}) => {
  const [query, setQuery] = useState("");
  const [selectedMode, setSelectedMode] = useState<"quick" | "standard" | "deep" | "custom">("standard");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isStarting) return;
    const depth = selectedMode === "deep" ? 2 : selectedMode === "quick" ? 0 : 1;
    onStartInvestigation(query.trim(), selectedMode, depth);
  };

  const handleChipClick = (chipLabel: string) => {
    setQuery(chipLabel);
  };

  // Mock / live dynamic counts
  const totalEntitiesCount = investigations.reduce(
    (acc, inv) => acc + (inv.summary_json?.entities_count || 14),
    186
  );
  const totalEvidenceCount = investigations.reduce(
    (acc, inv) => acc + (inv.summary_json?.evidence_count || 48),
    940
  );
  const highConfidenceCount = investigations.reduce(
    (acc, inv) => acc + (inv.summary_json?.high_confidence_count || 6),
    24
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0a0d14] overflow-y-auto px-6 py-8 select-text font-sans">
      <div className="max-w-6xl mx-auto w-full space-y-8">
        {/* Top Headline + AI Banner */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="text-[11px] font-mono tracking-widest text-slate-400 font-semibold uppercase block">
              OPEN SOURCE INTELLIGENCE PLATFORM
            </span>
            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-100 tracking-tight leading-tight max-w-2xl font-sans">
              Turn public information into structured, evidence-backed intelligence.
            </h1>
            <p className="text-sm text-slate-400 font-mono tracking-tight">
              Search. Discover. Correlate. Investigate.
            </p>
          </div>

          {/* AI Banner Card with Constellation */}
          <div className="bg-[#0f1422] border border-[#1e283d] rounded-2xl p-4 flex items-center space-x-4 shadow-xl shrink-0 relative overflow-hidden group">
            <div className="space-y-1 z-10">
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30 text-[10px] font-mono font-semibold">
                <Sparkles className="w-3 h-3 text-purple-400" />
                <span>AI-Powered</span>
              </span>
              <h4 className="text-xs font-bold font-mono text-slate-200">
                Gemini AI + 100+ OSINT modules
              </h4>
              <p className="text-[11px] text-slate-400 font-mono">
                Local • Private • Extensible
              </p>
            </div>

            {/* Constellation SVG */}
            <div className="w-24 h-16 relative opacity-70 group-hover:opacity-100 transition-opacity">
              <svg className="w-full h-full" viewBox="0 0 100 60" fill="none">
                <line x1="15" y1="20" x2="50" y2="10" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 2" />
                <line x1="50" y1="10" x2="85" y2="35" stroke="#818cf8" strokeWidth="1" />
                <line x1="85" y1="35" x2="45" y2="45" stroke="#c084fc" strokeWidth="1" strokeDasharray="3 3" />
                <line x1="45" y1="45" x2="15" y2="20" stroke="#38bdf8" strokeWidth="1" />
                <circle cx="15" cy="20" r="3" fill="#38bdf8" />
                <circle cx="50" cy="10" r="3" fill="#818cf8" />
                <circle cx="85" cy="35" r="4" fill="#c084fc" />
                <circle cx="45" cy="45" r="3" fill="#38bdf8" />
              </svg>
            </div>
          </div>
        </div>

        {/* Massive Universal Search Input */}
        <form onSubmit={handleSubmit} className="w-full space-y-3">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/30 to-purple-600/20 rounded-2xl blur opacity-30 group-hover:opacity-70 transition duration-300"></div>
            <div className="relative bg-[#0f1422] border border-[#1f283d] group-hover:border-blue-500/60 rounded-2xl p-2 shadow-2xl flex items-center space-x-3 transition-all">
              <div className="pl-3 text-slate-400">
                <Search className="w-5 h-5 text-slate-400" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="example.com"
                className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm md:text-base focus:outline-none font-mono py-1.5"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="p-1 rounded-full text-slate-500 hover:text-slate-300 hover:bg-[#162035] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
              <button
                type="submit"
                disabled={isStarting || !query.trim()}
                className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shrink-0 transition-transform active:scale-95 disabled:opacity-50 disabled:pointer-events-none shadow-md"
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Suggested Quick Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {QUICK_CHIPS.map((chip, idx) => {
              const Icon = chip.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleChipClick(chip.label)}
                  className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-[#0e1320] hover:bg-[#151c2e] border border-[#1b2336] text-xs font-mono text-slate-300 hover:text-white transition-colors"
                >
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{chip.label}</span>
                </button>
              );
            })}
          </div>
        </form>

        {/* 4 Investigation Modes Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Quick Mode */}
          <div
            onClick={() => setSelectedMode("quick")}
            className={`cursor-pointer rounded-2xl p-4 transition-all border ${
              selectedMode === "quick"
                ? "bg-[#111728] border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                : "bg-[#0f1422] border-[#1b2336] hover:border-slate-700"
            }`}
          >
            <div className="flex items-center space-x-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <Zap className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-sm font-mono text-slate-100">Quick</h3>
            </div>
            <p className="text-xs text-slate-400 font-sans leading-relaxed mb-3">
              Fast, high-confidence sources.
            </p>
            <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-500">
              <span>⏱ ~10-20 min</span>
              <span>•</span>
              <span>5-10 modules</span>
            </div>
          </div>

          {/* Standard Mode */}
          <div
            onClick={() => setSelectedMode("standard")}
            className={`cursor-pointer rounded-2xl p-4 transition-all border ${
              selectedMode === "standard"
                ? "bg-[#111728] border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                : "bg-[#0f1422] border-[#1b2336] hover:border-slate-700"
            }`}
          >
            <div className="flex items-center space-x-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-blue-500/15 text-blue-400 flex items-center justify-center">
                <Shield className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-sm font-mono text-slate-100">Standard</h3>
            </div>
            <p className="text-xs text-slate-400 font-sans leading-relaxed mb-3">
              Balanced depth and coverage.
            </p>
            <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-500">
              <span>⏱ ~30-60 min</span>
              <span>•</span>
              <span>15-30 modules</span>
            </div>
          </div>

          {/* Deep Mode */}
          <div
            onClick={() => setSelectedMode("deep")}
            className={`cursor-pointer rounded-2xl p-4 transition-all border ${
              selectedMode === "deep"
                ? "bg-[#111728] border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                : "bg-[#0f1422] border-[#1b2336] hover:border-slate-700"
            }`}
          >
            <div className="flex items-center space-x-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-purple-500/15 text-purple-400 flex items-center justify-center">
                <Compass className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-sm font-mono text-slate-100">Deep</h3>
            </div>
            <p className="text-xs text-slate-400 font-sans leading-relaxed mb-3">
              Maximum coverage and detail.
            </p>
            <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-500">
              <span>⏱ ~1-3 hrs</span>
              <span>•</span>
              <span>30+ modules</span>
            </div>
          </div>

          {/* Custom Mode */}
          <div
            onClick={() => setSelectedMode("custom")}
            className={`cursor-pointer rounded-2xl p-4 transition-all border ${
              selectedMode === "custom"
                ? "bg-[#111728] border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                : "bg-[#0f1422] border-[#1b2336] hover:border-slate-700"
            }`}
          >
            <div className="flex items-center space-x-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-slate-700/30 text-slate-400 flex items-center justify-center">
                <Layers className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-sm font-mono text-slate-100">Custom</h3>
            </div>
            <p className="text-xs text-slate-400 font-sans leading-relaxed mb-3">
              Choose your own modules.
            </p>
            <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-500">
              <span>Set limits and preferences</span>
            </div>
          </div>
        </div>

        {/* 4 Key Metric Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Stat 1 */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Active Investigations</span>
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
              {investigations.filter((i) => i.status === "running").length || 3}
            </div>
            <p className="text-[11px] font-mono text-emerald-400 mt-1 flex items-center space-x-1">
              <span>▲</span>
              <span>+1 today</span>
            </p>
          </div>

          {/* Stat 2 */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Total Entities</span>
              <div className="w-8 h-8 rounded-xl bg-blue-500/15 text-blue-400 flex items-center justify-center">
                <User className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
              {totalEntitiesCount}
            </div>
            <p className="text-[11px] font-mono text-emerald-400 mt-1 flex items-center space-x-1">
              <span>▲</span>
              <span>+42 this week</span>
            </p>
          </div>

          {/* Stat 3 */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">Evidence Collected</span>
              <div className="w-8 h-8 rounded-xl bg-purple-500/15 text-purple-400 flex items-center justify-center">
                <Shield className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
              {totalEvidenceCount > 999 ? `${(totalEvidenceCount / 1000).toFixed(1)}K` : totalEvidenceCount}
            </div>
            <p className="text-[11px] font-mono text-emerald-400 mt-1 flex items-center space-x-1">
              <span>▲</span>
              <span>+308 this week</span>
            </p>
          </div>

          {/* Stat 4 */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400">High Confidence Findings</span>
              <div className="w-8 h-8 rounded-xl bg-amber-500/15 text-amber-400 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
              {highConfidenceCount}
            </div>
            <p className="text-[11px] font-mono text-emerald-400 mt-1 flex items-center space-x-1">
              <span>▲</span>
              <span>+6 this week</span>
            </p>
          </div>
        </div>

        {/* Bottom Two-Column Grid: Recent Investigations & Investigation Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Recent Investigations */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-bold font-mono text-slate-200">Recent Investigations</h3>
                </div>
                <button
                  onClick={onViewAllInvestigations}
                  className="text-xs font-mono text-slate-400 hover:text-sky-400 flex items-center space-x-1 transition-colors"
                >
                  <span>View all</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              {/* Rows */}
              <div className="space-y-2.5">
                {(investigations.length > 0 ? investigations.slice(0, 5) : [
                  { id: "1", title: "Example Corporation", type: "Domain", target: "example.com", status: "Running", time: "12 min ago" },
                  { id: "2", title: "John Smith", type: "Name", target: "John Smith", status: "Completed", time: "2 hours ago" },
                  { id: "3", title: "dev_user", type: "Username", target: "dev_user", status: "Completed", time: "5 hours ago" },
                  { id: "4", title: "8.8.8.8", type: "IP Address", target: "8.8.8.8", status: "Completed", time: "1 day ago" },
                  { id: "5", title: "GitHub Repository", type: "Repository", target: "github.com/torvalds/linux", status: "Completed", time: "1 day ago" },
                ]).map((inv: any, idx: number) => {
                  const isRunning = inv.status === "running" || inv.status === "Running";
                  return (
                    <div
                      key={inv.id || idx}
                      onClick={() => onSelectInvestigation(inv)}
                      className="p-2.5 rounded-xl bg-[#111728] hover:bg-[#161f36] border border-[#1a2338] flex items-center justify-between cursor-pointer transition-colors group"
                    >
                      <div className="flex items-center space-x-3 truncate">
                        <div className="w-8 h-8 rounded-lg bg-[#18223a] text-slate-300 flex items-center justify-center shrink-0">
                          {idx === 0 ? <Globe className="w-4 h-4 text-sky-400" /> :
                           idx === 1 || idx === 2 ? <User className="w-4 h-4 text-purple-400" /> :
                           idx === 3 ? <Server className="w-4 h-4 text-amber-400" /> :
                           <Code2 className="w-4 h-4 text-emerald-400" />}
                        </div>
                        <div className="truncate">
                          <h4 className="text-xs font-bold font-mono text-slate-200 group-hover:text-sky-300 truncate">
                            {inv.title}
                          </h4>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {inv.mode ? `${inv.mode.toUpperCase()} • ${inv.id.slice(0, 8)}` : inv.target || inv.title}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 shrink-0">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold ${
                            isRunning
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {isRunning ? "Running" : "Completed"}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 hidden sm:inline">
                          {inv.time || "Recently"}
                        </span>
                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-300 transition-colors" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right: Investigation Activity */}
          <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-5 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-slate-400" />
                  <h3 className="text-sm font-bold font-mono text-slate-200">Investigation Activity</h3>
                </div>
                <button
                  onClick={onViewAllActivity}
                  className="text-xs font-mono text-slate-400 hover:text-sky-400 flex items-center space-x-1 transition-colors"
                >
                  <span>View all</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              {/* Activity Timeline List */}
              <div className="space-y-4 relative pl-3 border-l border-[#1a2338]">
                {[
                  { time: "12:42", color: "bg-emerald-400", title: "Discovered 3 new entities", detail: "2 domains, 1 username" },
                  { time: "12:37", color: "bg-blue-400", title: "Correlated 5 relationships", detail: "Domain ↔ Email, User ↔ Repo" },
                  { time: "12:31", color: "bg-purple-400", title: "Collected evidence", detail: "Web, DNS, Certificates" },
                  { time: "12:20", color: "bg-amber-400", title: "AI analysis completed", detail: "3 findings, 1 contradiction" },
                  { time: "12:05", color: "bg-slate-400", title: "Investigation started", detail: "Target: example.com" },
                ].map((act, idx) => (
                  <div key={idx} className="relative flex items-start space-x-3 text-xs font-mono">
                    {/* Bullet */}
                    <div
                      className={`w-2.5 h-2.5 rounded-full ${act.color} absolute -left-[17px] top-1 ring-4 ring-[#0f1422]`}
                    ></div>
                    <span className="text-slate-500 text-[11px] shrink-0 font-medium">{act.time}</span>
                    <div>
                      <h4 className="text-slate-200 font-semibold">{act.title}</h4>
                      <p className="text-slate-500 text-[11px]">{act.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
