import React from "react";
import { X, Search, Sparkles, ShieldCheck, Tag, Clock, ArrowRight, Layers } from "lucide-react";
import { Entity } from "../types";

interface EntityInspectorProps {
  entity: Entity | null;
  onClose: () => void;
  onInvestigateThis: (value: string) => void;
}

export const EntityInspector: React.FC<EntityInspectorProps> = ({
  entity,
  onClose,
  onInvestigateThis,
}) => {
  if (!entity) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0f121a] border-l border-[#2b354d] shadow-2xl z-40 flex flex-col font-sans animate-in slide-in-from-right-4 duration-200">
      {/* Drawer Header */}
      <div className="p-4 border-b border-[#1f2638] bg-[#141824] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-sky-400" />
          <span className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider">
            Entity Intelligence Panel
          </span>
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300 p-1">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="p-5 flex-1 overflow-y-auto space-y-5 text-xs font-sans">
        <div>
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30">
              {entity.type}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#141824] text-slate-400 border border-[#232c42]">
              {entity.provenance_label}
            </span>
          </div>

          <h3 className="text-base font-bold text-slate-100 font-mono break-all">
            {entity.value}
          </h3>
          <p className="text-[11px] font-mono text-slate-500 mt-0.5">
            Canonical: {entity.normalized_value}
          </p>
        </div>

        {/* Investigate This Button */}
        <button
          onClick={() => onInvestigateThis(entity.value)}
          className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold font-mono text-xs transition-colors shadow-md shadow-sky-500/20"
        >
          <Search className="w-3.5 h-3.5" />
          <span>INVESTIGATE THIS ENTITY →</span>
        </button>

        {/* Confidence & Epistemic Tier */}
        <div className="bg-[#141824] border border-[#1f2638] rounded-xl p-3.5 space-y-2">
          <div className="flex items-center justify-between font-mono">
            <span className="text-slate-400">Confidence Score:</span>
            <span className="text-emerald-400 font-bold">
              {Math.round(entity.confidence * 100)}%
            </span>
          </div>
          <div className="w-full h-1 bg-[#090a0f] rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${Math.round(entity.confidence * 100)}%` }}
            ></div>
          </div>
          <p className="text-[11px] text-slate-500 font-sans leading-relaxed">
            Every attribute is linked to verified public sources.
          </p>
        </div>

        {/* Disambiguation Cluster */}
        {entity.cluster_id && (
          <div className="bg-[#141824] border border-[#1f2638] rounded-xl p-3.5">
            <span className="text-[10px] font-mono text-slate-500 block mb-1">
              DISAMBIGUATION CLUSTER
            </span>
            <span className="font-mono text-sky-300 font-semibold text-xs">
              {entity.cluster_id}
            </span>
            <p className="text-[11px] text-slate-400 font-sans mt-1">
              Separated from potential identity collisions sharing similar identifiers.
            </p>
          </div>
        )}

        {/* Metadata Attributes */}
        {entity.metadata_json && Object.keys(entity.metadata_json).length > 0 && (
          <div className="space-y-2">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
              Observed Metadata Attributes
            </span>
            <div className="bg-[#141824] border border-[#1f2638] rounded-xl p-3 space-y-2 font-mono text-[11px]">
              {Object.entries(entity.metadata_json).map(([k, v]) => (
                <div key={k} className="flex items-start justify-between border-b border-[#1f2638] pb-1.5 last:border-0 last:pb-0">
                  <span className="text-slate-400">{k}:</span>
                  <span className="text-slate-200 text-right font-medium max-w-[180px] truncate">
                    {String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamps */}
        <div className="text-[10px] font-mono text-slate-500 space-y-1 pt-2 border-t border-[#1a2133]">
          <div>First Seen: {new Date(entity.first_seen).toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
};
