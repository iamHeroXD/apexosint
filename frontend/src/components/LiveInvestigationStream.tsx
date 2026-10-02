import React, { useState, useEffect } from "react";
import {
  Play,
  Pause,
  Square,
  Activity,
  Layers,
  CheckCircle,
  Compass,
  ShieldAlert,
  ArrowRight,
  Database,
} from "lucide-react";
import { Investigation } from "../types";
import { api } from "../api/client";

interface LiveInvestigationStreamProps {
  investigation: Investigation;
  onOpenGraph: () => void;
  onOpenEvidence: () => void;
  onOpenReport: () => void;
}

const PIPELINE_PHASES = [
  "PLAN",
  "DISCOVER",
  "COLLECT",
  "NORMALIZE",
  "CORRELATE",
  "VERIFY",
  "REPORT",
];

export const LiveInvestigationStream: React.FC<LiveInvestigationStreamProps> = ({
  investigation,
  onOpenGraph,
  onOpenEvidence,
  onOpenReport,
}) => {
  const [currentPhase, setCurrentPhase] = useState("COLLECT");
  const [logs, setLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Investigation initialized for target set.`,
    `[${new Date().toLocaleTimeString()}] Formulating autonomous collection plan...`,
  ]);
  const [isPaused, setIsPaused] = useState(false);
  const [invState, setInvState] = useState(investigation);

  useEffect(() => {
    // Poll investigation summary state periodically
    const interval = setInterval(async () => {
      try {
        const updated = await api.getInvestigation(investigation.id);
        setInvState(updated);
        if (updated.status === "completed") {
          setCurrentPhase("REPORT");
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 2500);

    // Connect Server-Sent Events stream
    const eventSource = new EventSource(`/api/investigations/${investigation.id}/stream`);
    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const time = new Date().toLocaleTimeString();

        if (payload.type === "phase_update") {
          setCurrentPhase(payload.data.phase);
          setLogs((prev) => [...prev, `[${time}] Entered phase: ${payload.data.phase}`]);
        } else if (payload.type === "module_started") {
          setLogs((prev) => [
            ...prev,
            `[${time}] Module ${payload.data.module_name} probing ${payload.data.target}...`,
          ]);
        } else if (payload.type === "evidence_discovered") {
          setLogs((prev) => [
            ...prev,
            `[${time}] Evidence captured from ${payload.data.source}: ${payload.data.snippet.slice(0, 80)}...`,
          ]);
        } else if (payload.type === "entity_discovered") {
          setLogs((prev) => [
            ...prev,
            `[${time}] Discovered ${payload.data.type}: ${payload.data.value}`,
          ]);
        } else if (payload.type === "contradiction_detected") {
          setLogs((prev) => [
            ...prev,
            `[${time}] [CONFLICT DETECTED] ${payload.data.attribute}: ${payload.data.explanation.slice(0, 90)}...`,
          ]);
        } else if (payload.type === "status_change") {
          if (payload.data.status === "completed") {
            setLogs((prev) => [...prev, `[${time}] Investigation workflow complete.`]);
          }
        }
      } catch (err) {
        // Ignored
      }
    };

    return () => {
      clearInterval(interval);
      eventSource.close();
    };
  }, [investigation.id]);

  const handleStop = async () => {
    await api.stopInvestigation(investigation.id);
    setIsPaused(true);
  };

  const handleResume = async () => {
    await api.runInvestigation(investigation.id);
    setIsPaused(false);
  };

  const summary = (invState.summary_json || {}) as any;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] p-6 overflow-y-auto">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header Bar */}
        <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></span>
              <span className="text-[11px] font-mono text-sky-400 uppercase tracking-wider font-bold">
                Investigation Status: {invState.status.toUpperCase()}
              </span>
            </div>
            <h2 className="text-xl font-bold font-mono text-slate-100 mt-1">
              {invState.title}
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Mode: {invState.mode.toUpperCase()} | Depth: {invState.depth} | Case ID: {invState.id}
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center space-x-2">
            {invState.status === "running" ? (
              <button
                onClick={handleStop}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-mono transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            ) : invState.status === "paused" ? (
              <button
                onClick={handleResume}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-mono transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            ) : null}

            <button
              onClick={onOpenGraph}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs font-mono transition-colors"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Explore Graph →</span>
            </button>
          </div>
        </div>

        {/* Phase Progress Bar */}
        <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-4">
          <div className="flex items-center justify-between text-xs font-mono mb-3">
            <span className="text-slate-400">PIPELINE PHASE:</span>
            <span className="text-sky-400 font-bold">{currentPhase}</span>
          </div>

          <div className="grid grid-cols-7 gap-1">
            {PIPELINE_PHASES.map((ph, idx) => {
              const activeIndex = PIPELINE_PHASES.indexOf(currentPhase);
              const isPast = idx <= activeIndex;
              const isCurrent = idx === activeIndex;

              return (
                <div key={ph} className="flex flex-col items-center">
                  <div
                    className={`w-full h-2 rounded-full mb-1.5 transition-all ${
                      isCurrent
                        ? "bg-sky-400 animate-pulse shadow-sm shadow-sky-400"
                        : isPast
                        ? "bg-sky-600"
                        : "bg-[#141824]"
                    }`}
                  ></div>
                  <span
                    className={`text-[10px] font-mono ${
                      isCurrent
                        ? "text-sky-300 font-bold"
                        : isPast
                        ? "text-slate-300"
                        : "text-slate-600"
                    }`}
                  >
                    {ph}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div
            onClick={onOpenGraph}
            className="bg-[#0f121a] hover:bg-[#141824] border border-[#1f2638] rounded-xl p-3 cursor-pointer transition-colors"
          >
            <span className="text-[10px] font-mono text-slate-500 block">ENTITIES</span>
            <span className="text-2xl font-bold font-mono text-sky-400">
              {summary.entities_count || 0}
            </span>
          </div>

          <div
            onClick={onOpenEvidence}
            className="bg-[#0f121a] hover:bg-[#141824] border border-[#1f2638] rounded-xl p-3 cursor-pointer transition-colors"
          >
            <span className="text-[10px] font-mono text-slate-500 block">EVIDENCE</span>
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {summary.evidence_count || 0}
            </span>
          </div>

          <div
            onClick={onOpenGraph}
            className="bg-[#0f121a] hover:bg-[#141824] border border-[#1f2638] rounded-xl p-3 cursor-pointer transition-colors"
          >
            <span className="text-[10px] font-mono text-slate-500 block">CORRELATIONS</span>
            <span className="text-2xl font-bold font-mono text-indigo-400">
              {summary.relationships_count || 0}
            </span>
          </div>

          <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-3">
            <span className="text-[10px] font-mono text-slate-500 block">SOURCES</span>
            <span className="text-2xl font-bold font-mono text-purple-400">
              {summary.sources_count || 0}
            </span>
          </div>

          <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-3">
            <span className="text-[10px] font-mono text-slate-500 block">HIGH CONFIDENCE</span>
            <span className="text-2xl font-bold font-mono text-amber-400">
              {summary.high_confidence_count || 0}
            </span>
          </div>

          <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-3">
            <span className="text-[10px] font-mono text-slate-500 block">CONTRADICTIONS</span>
            <span
              className={`text-2xl font-bold font-mono ${
                (summary.contradictions_count || 0) > 0 ? "text-rose-400" : "text-slate-500"
              }`}
            >
              {summary.contradictions_count || 0}
            </span>
          </div>
        </div>

        {/* Live SSE Telemetry Stream Terminal */}
        <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl overflow-hidden shadow-2xl">
          <div className="px-4 py-2.5 border-b border-[#1f2638] bg-[#0c0e15] flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-xs font-mono font-bold text-slate-200">
                Live Evidence & Event Stream
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">
              Telemetry Channel Active
            </span>
          </div>

          <div className="p-4 bg-[#08090d] font-mono text-xs text-slate-300 space-y-1.5 max-h-72 overflow-y-auto">
            {logs.map((log, idx) => (
              <div
                key={idx}
                className={`leading-relaxed ${
                  log.includes("[CONFLICT DETECTED]")
                    ? "text-rose-400 font-semibold"
                    : log.includes("Evidence captured")
                    ? "text-emerald-300"
                    : log.includes("Discovered")
                    ? "text-sky-300"
                    : "text-slate-400"
                }`}
              >
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
