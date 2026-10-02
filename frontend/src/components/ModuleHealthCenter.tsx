import React, { useState, useEffect } from "react";
import { Activity, Power, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react";
import { OSINTModule } from "../types";
import { api } from "../api/client";

export const ModuleHealthCenter: React.FC = () => {
  const [modules, setModules] = useState<OSINTModule[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchModules = async () => {
    setIsLoading(true);
    try {
      const data = await api.listModules();
      setModules(data);
    } catch (err) {
      console.error("Failed to load modules:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchModules();
  }, []);

  const handleToggle = async (name: string) => {
    try {
      await api.toggleModule(name);
      setModules((prev) =>
        prev.map((m) => (m.name === name ? { ...m, enabled: !m.enabled } : m))
      );
    } catch (err) {
      console.error("Failed to toggle module:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] p-6 overflow-y-auto">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono text-slate-100">
                OSINT Module Health Center
              </h2>
              <p className="text-xs text-slate-400 font-sans">
                Real-time telemetry, execution latency, and safety controls for all registered collectors.
              </p>
            </div>
          </div>

          <button
            onClick={fetchModules}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((m) => (
            <div
              key={m.name}
              className={`bg-[#0f121a] border rounded-xl p-4 flex flex-col justify-between transition-all ${
                m.enabled ? "border-[#1f2638]" : "border-slate-800/60 opacity-60"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#141824] text-sky-400 border border-[#232c42]">
                    {m.category}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        m.status === "HEALTHY" ? "bg-emerald-400" : "bg-amber-400"
                      }`}
                    ></span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {m.status}
                    </span>
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-slate-200 font-mono">
                  {m.display_name}
                </h3>
                <p className="text-xs text-slate-400 font-sans mt-1 leading-relaxed">
                  {m.description}
                </p>

                <div className="mt-3 flex flex-wrap gap-1">
                  {m.target_types.map((tt) => (
                    <span
                      key={tt}
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#141824] text-slate-400 border border-[#1f2638]"
                    >
                      {tt}
                    </span>
                  ))}
                </div>
              </div>

              {/* Bottom Metrics & Toggle */}
              <div className="mt-4 pt-3 border-t border-[#1a2133] flex items-center justify-between text-[11px] font-mono">
                <div className="text-slate-500">
                  <span>Latency: </span>
                  <span className="text-slate-300">{m.average_latency_ms}ms</span>
                </div>

                <button
                  onClick={() => handleToggle(m.name)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border text-[11px] font-mono transition-colors ${
                    m.enabled
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
                      : "bg-slate-800/40 text-slate-400 border-slate-700 hover:bg-slate-800/80"
                  }`}
                >
                  <Power className="w-3 h-3" />
                  <span>{m.enabled ? "Enabled" : "Disabled"}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
