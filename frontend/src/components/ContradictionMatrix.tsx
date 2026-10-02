import React, { useState, useEffect } from "react";
import { ShieldAlert, AlertTriangle, CheckCircle, HelpCircle } from "lucide-react";
import { Contradiction } from "../types";
import { api } from "../api/client";

interface ContradictionMatrixProps {
  investigationId: string;
}

export const ContradictionMatrix: React.FC<ContradictionMatrixProps> = ({ investigationId }) => {
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!investigationId) return;
    setIsLoading(true);
    api
      .getContradictions(investigationId)
      .then((data) => setContradictions(data))
      .catch((err) => console.error("Error fetching contradictions:", err))
      .finally(() => setIsLoading(false));
  }, [investigationId]);

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100">
              Contradiction & Divergent Claim Matrix
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              APEX preserves factual conflicts between independent sources rather than silently merging them.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            Scanning evidence for conflicting assertions...
          </div>
        ) : contradictions.length === 0 ? (
          <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-8 text-center space-y-2">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-200">No Factual Contradictions Detected</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              All independent sources are in consensus or uncorroborated without conflicting attributes.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {contradictions.map((c) => (
              <div
                key={c.id}
                className="bg-[#0f121a] border border-rose-500/30 rounded-xl p-5 shadow-xl space-y-4"
              >
                {/* Badge Header */}
                <div className="flex items-center justify-between border-b border-[#1f2638] pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse">
                      CONFLICT DETECTED
                    </span>
                    <span className="text-xs font-mono text-slate-300 font-semibold">
                      Attribute: {c.attribute_name}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">
                    Status: Unresolved Divergence
                  </span>
                </div>

                {/* Side-by-Side Claims Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Source A */}
                  <div className="bg-[#141824] border border-[#232c42] rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-mono text-sky-400">
                      <span>SOURCE A:</span>
                      <span className="font-semibold">{c.source_a_name}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-mono bg-[#0c0e15] p-2.5 rounded border border-[#1a2133]">
                      "{c.source_a_claim}"
                    </p>
                  </div>

                  {/* Source B */}
                  <div className="bg-[#141824] border border-[#232c42] rounded-lg p-3 space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-mono text-amber-400">
                      <span>SOURCE B:</span>
                      <span className="font-semibold">{c.source_b_name}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-mono bg-[#0c0e15] p-2.5 rounded border border-[#1a2133]">
                      "{c.source_b_claim}"
                    </p>
                  </div>
                </div>

                {/* Explanation & Investigation Guidance */}
                <div className="pt-2 border-t border-[#1a2133] flex items-start space-x-2 text-xs">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-mono text-slate-300 font-semibold block mb-0.5">
                      Analytical Explanation:
                    </span>
                    <p className="text-slate-400 font-sans leading-relaxed">
                      {c.explanation}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
