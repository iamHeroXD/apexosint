import React, { useState, useEffect } from "react";
import {
  Search,
  Sparkles,
  Sliders,
  Play,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Cpu,
  Globe,
  Database,
  Layers,
} from "lucide-react";
import { AnalyzedTarget } from "../types";
import { api } from "../api/client";

interface UniversalSearchProps {
  onStartInvestigation: (query: string, mode: string, depth: number) => void;
  onLaunchDemo: () => void;
  isStarting: boolean;
}

const QUICK_EXAMPLES = [
  { label: "apex-defense.org", type: "DOMAIN" },
  { label: "johnsmith", type: "USERNAME / NAME" },
  { label: "sec-ops@defense.gov", type: "EMAIL" },
  { label: "198.51.100.42", type: "IP" },
  { label: "+91 98765 43210", type: "PHONE" },
  { label: "github.com/torvalds/linux", type: "REPO" },
];

export const UniversalSearch: React.FC<UniversalSearchProps> = ({
  onStartInvestigation,
  onLaunchDemo,
  isStarting,
}) => {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"quick" | "standard" | "deep">("standard");
  const [depth, setDepth] = useState<number>(1);
  const [analyzedTargets, setAnalyzedTargets] = useState<AnalyzedTarget[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Debounced Universal Target Analysis
  useEffect(() => {
    if (!query.trim()) {
      setAnalyzedTargets([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsAnalyzing(true);
      try {
        const results = await api.analyzeTarget(query);
        setAnalyzedTargets(results);
      } catch (err) {
        console.error("Target analysis failed:", err);
      } finally {
        setIsAnalyzing(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isStarting) return;
    onStartInvestigation(query.trim(), mode, depth);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-start px-4 py-8 max-w-4xl mx-auto overflow-y-auto">
      {/* Hero Banner */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono mb-4">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Local-First Defensive Intelligence Platform</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-100 font-sans">
          A P E X <span className="text-sky-400 font-mono text-2xl font-normal ml-2">OSINT</span>
        </h1>
        <p className="text-slate-400 text-sm mt-2 max-w-lg mx-auto font-sans">
          Turn public information into structured, evidence-backed intelligence.
          One universal input. Zero manual categorizing.
        </p>
      </div>

      {/* Massive Universal Search Input */}
      <form onSubmit={handleSubmit} className="w-full">
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-sky-500/30 to-purple-500/30 rounded-xl blur opacity-30 group-hover:opacity-75 transition duration-300"></div>
          <div className="relative bg-[#0f121a] border border-[#2b354d] group-hover:border-sky-500/60 rounded-xl p-2.5 shadow-2xl transition-all">
            <div className="flex items-center space-x-3 px-3 py-2">
              <Search className="w-5 h-5 text-sky-400 shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter anything to investigate... (domain, IP, email, username, phone, repo, person, or multiple targets)"
                className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm sm:text-base focus:outline-none font-mono"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="text-xs text-slate-500 hover:text-slate-300 font-mono px-2"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Mode & Depth Controls Bar */}
            <div className="mt-3 pt-3 border-t border-[#1a2133] flex flex-wrap items-center justify-between gap-3 px-2 text-xs">
              {/* Investigation Mode */}
              <div className="flex items-center space-x-2">
                <span className="text-slate-500 font-mono text-[11px]">Mode:</span>
                <div className="inline-flex rounded-lg bg-[#141824] p-0.5 border border-[#1f2638]">
                  {(["quick", "standard", "deep"] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMode(m)}
                      className={`px-2.5 py-1 rounded text-[11px] font-mono capitalize transition-colors ${
                        mode === m
                          ? "bg-sky-500/20 text-sky-400 font-medium"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              {/* Recursion Depth */}
              <div className="flex items-center space-x-2">
                <span className="text-slate-500 font-mono text-[11px]">Depth:</span>
                <div className="inline-flex rounded-lg bg-[#141824] p-0.5 border border-[#1f2638]">
                  {[0, 1, 2, 3].map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDepth(d)}
                      className={`px-2 py-1 rounded text-[11px] font-mono transition-colors ${
                        depth === d
                          ? "bg-sky-500/20 text-sky-400 font-medium"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                      title={d === 0 ? "Target only" : `Depth ${d} auto-expansion`}
                    >
                      {d === 0 ? "D0" : `D${d}`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={!query.trim() || isStarting}
                className="ml-auto flex items-center space-x-2 px-5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs font-mono transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-sky-500/20"
              >
                {isStarting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></span>
                    <span>Starting...</span>
                  </>
                ) : (
                  <>
                    <span>INVESTIGATE</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Example Chips */}
      <div className="w-full mt-4 flex items-center flex-wrap gap-2 text-xs">
        <span className="text-slate-500 font-mono text-[11px]">Try sample:</span>
        {QUICK_EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            type="button"
            onClick={() => setQuery(ex.label)}
            className="px-2.5 py-1 rounded-md bg-[#121622] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-sky-300 font-mono text-[11px] transition-colors"
          >
            {ex.label}
          </button>
        ))}
      </div>

      {/* Target Interpretation & Hypotheses Panel */}
      {analyzedTargets.length > 0 && (
        <div className="w-full mt-6 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          {analyzedTargets.map((target, idx) => (
            <div
              key={idx}
              className="bg-[#0f121a] border border-[#232c42] rounded-xl p-5 shadow-xl"
            >
              <div className="flex items-center justify-between border-b border-[#1f2638] pb-3 mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-xs font-mono text-slate-500">INPUT:</span>
                  <span className="font-mono text-sm font-semibold text-slate-200">
                    {target.raw_input}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-slate-500">PRIMARY:</span>
                  <span className="px-2.5 py-0.5 rounded font-mono text-xs font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30">
                    {target.primary_type} ({Math.round(target.primary_confidence * 100)}%)
                  </span>
                </div>
              </div>

              {/* Hypotheses Bars */}
              <div className="space-y-2 mb-4">
                <span className="text-[11px] font-mono text-slate-400 block uppercase tracking-wider">
                  APEX Detected Possibilities:
                </span>
                {target.hypotheses.map((h, hIdx) => (
                  <div key={hIdx} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300 font-medium">{h.type}</span>
                      <span className="text-sky-400">{h.percentage}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#141824] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-sky-500 to-indigo-500 rounded-full transition-all duration-500"
                        style={{ width: `${h.percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-[11px] text-slate-500 font-sans">{h.explanation}</p>
                  </div>
                ))}
              </div>

              {/* Planned Investigation Pipeline */}
              <div className="pt-3 border-t border-[#1a2133]">
                <span className="text-[11px] font-mono text-slate-400 block mb-2 uppercase tracking-wider">
                  Planned Autonomous Pipeline:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {target.planned_investigation.map((modName, mIdx) => (
                    <span
                      key={mIdx}
                      className="inline-flex items-center space-x-1.5 px-2 py-1 rounded bg-[#141824] border border-[#232c42] text-[11px] font-mono text-slate-300"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>{modName}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Demo Sandbox Promo Card */}
      <div className="w-full mt-10 p-5 rounded-xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/20 to-[#0f121a] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="text-xs font-mono font-bold text-emerald-400 tracking-wider">
              OFFLINE DEMO SANDBOX AVAILABLE
            </span>
          </div>
          <h3 className="text-sm font-semibold text-slate-200 mt-1">
            Apex Demo Corporation (apex-defense.org)
          </h3>
          <p className="text-xs text-slate-400 max-w-md mt-0.5 font-sans">
            Explore 16+ connected nodes, DNS, TLS certificates, commit logs, a detected contradiction, and AI briefings instantly.
          </p>
        </div>
        <button
          type="button"
          onClick={onLaunchDemo}
          className="shrink-0 flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-semibold transition-colors"
        >
          <Play className="w-3.5 h-3.5 fill-emerald-400" />
          <span>Launch Demo Sandbox</span>
        </button>
      </div>
    </div>
  );
};
