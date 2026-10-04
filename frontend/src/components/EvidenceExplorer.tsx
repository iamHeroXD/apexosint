import React, { useState, useEffect } from "react";
import {
  Compass,
  Filter,
  Search,
  ExternalLink,
  ShieldCheck,
  Sparkles,
  Layers,
  Code2,
  Clock,
  Bookmark,
} from "lucide-react";
import { Evidence } from "../types";
import { api } from "../api/client";

interface EvidenceExplorerProps {
  investigationId: string;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({ investigationId }) => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string>("");
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);

  useEffect(() => {
    if (!investigationId) return;
    setIsLoading(true);
    api
      .getEvidence(investigationId, sourceTypeFilter || undefined)
      .then((data) => {
        setEvidenceList(data);
        if (data.length > 0 && !selectedEvidence) {
          setSelectedEvidence(data[0]);
        }
      })
      .catch((err) => console.error("Error fetching evidence:", err))
      .finally(() => setIsLoading(false));
  }, [investigationId, sourceTypeFilter]);

  const filtered = evidenceList.filter(
    (ev) =>
      ev.source_name.toLowerCase().includes(search.toLowerCase()) ||
      ev.snippet.toLowerCase().includes(search.toLowerCase()) ||
      ev.source_type.toLowerCase().includes(search.toLowerCase())
  );

  const getEpistemicBadge = (label: string) => {
    switch (label) {
      case "OBSERVED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "CORROBORATED":
        return "bg-sky-500/10 text-sky-400 border-sky-500/30";
      case "AI_INFERENCE":
      case "INFERRED":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      case "CONFLICTED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "STALE":
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
      case "UNVERIFIED":
      default:
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    }
  };

  return (
    <div className="flex-1 flex h-full bg-[#08090d] overflow-hidden">
      {/* Evidence List Column */}
      <div className="w-full md:w-1/2 lg:w-3/5 flex flex-col border-r border-[#1f2638]">
        {/* Header Filters */}
        <div className="p-3 border-b border-[#1f2638] bg-[#0c0e15] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Compass className="w-4 h-4 text-sky-400" />
            <h2 className="text-xs font-mono font-bold text-slate-200">
              Evidence Provenance Matrix ({evidenceList.length})
            </h2>
          </div>

          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search snippets..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-[#141824] border border-[#1f2638] text-xs text-slate-200 pl-8 pr-3 py-1 rounded focus:outline-none focus:border-sky-500 font-mono w-40"
              />
            </div>

            <select
              value={sourceTypeFilter}
              onChange={(e) => setSourceTypeFilter(e.target.value)}
              className="bg-[#141824] border border-[#1f2638] text-xs text-slate-300 rounded px-2 py-1 font-mono focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="DNS">DNS</option>
              <option value="CERTIFICATE">Certificate</option>
              <option value="RDAP">RDAP</option>
              <option value="NETWORK">Network</option>
              <option value="CODE_REPOSITORY">GitHub</option>
              <option value="WEB">Web</option>
            </select>
          </div>
        </div>

        {/* Scrollable Cards */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
          {isLoading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500">
              Loading evidence records...
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500">
              No evidence records found matching criteria.
            </div>
          ) : (
            filtered.map((ev) => (
              <div
                key={ev.id}
                onClick={() => setSelectedEvidence(ev)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  selectedEvidence?.id === ev.id
                    ? "bg-[#141824] border-sky-500/60 shadow-lg"
                    : "bg-[#0f121a] hover:bg-[#121622] border-[#1f2638]"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {ev.source_name}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1a2133] text-slate-400 border border-[#26314d]">
                      {ev.source_type}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getEpistemicBadge(
                      ev.epistemic_label
                    )}`}
                  >
                    {ev.epistemic_label}
                  </span>
                </div>

                <p className="text-xs text-slate-300 font-sans line-clamp-2 leading-relaxed">
                  {ev.snippet}
                </p>

                <div className="mt-2 pt-2 border-t border-[#1a2133] flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Method: {ev.collection_method}</span>
                  <div className="flex items-center space-x-2">
                    {ev.source_reliability !== undefined && (
                      <span className="text-sky-400 font-semibold">Rel: {Math.round(ev.source_reliability * 100)}%</span>
                    )}
                    <span>Conf: {Math.round(ev.confidence * 100)}%</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Evidence Detail Inspector Panel */}
      <div className="hidden md:flex flex-col flex-1 bg-[#0c0e15] overflow-y-auto p-5">
        {selectedEvidence ? (
          <div className="space-y-5 animate-in fade-in duration-150">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-slate-500">ID:</span>
                <span className="font-mono text-xs text-sky-400">{selectedEvidence.id}</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ml-auto ${getEpistemicBadge(
                    selectedEvidence.epistemic_label
                  )}`}
                >
                  {selectedEvidence.epistemic_label}
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-100 font-sans mt-1">
                {selectedEvidence.source_name}
              </h3>
              {selectedEvidence.source_url && (
                <a
                  href={selectedEvidence.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-1 text-xs text-sky-400 hover:text-sky-300 font-mono mt-1"
                >
                  <span className="truncate max-w-sm">{selectedEvidence.source_url}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            {/* Evidence Snippet */}
            <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-4">
              <span className="text-[11px] font-mono text-slate-400 block mb-1 uppercase tracking-wider">
                Evidence Summary Snippet:
              </span>
              <p className="text-sm text-slate-200 leading-relaxed font-sans">
                {selectedEvidence.snippet}
              </p>
            </div>

            {/* Provenance Metadata Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">SOURCE TYPE</span>
                <span className="text-slate-200 font-semibold">{selectedEvidence.source_type}</span>
              </div>
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">COLLECTION METHOD</span>
                <span className="text-slate-200 font-semibold">{selectedEvidence.collection_method}</span>
              </div>
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">SOURCE RELIABILITY</span>
                <span className="text-sky-400 font-semibold">
                  {Math.round((selectedEvidence.source_reliability ?? 0.90) * 100)}%
                </span>
              </div>
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">CONFIDENCE SCORE</span>
                <span className="text-emerald-400 font-semibold">
                  {Math.round(selectedEvidence.confidence * 100)}%
                </span>
              </div>
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">CORROBORATIONS</span>
                <span className="text-amber-400 font-semibold">
                  {selectedEvidence.corroboration_count ?? 0} independent sources
                </span>
              </div>
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-lg p-3">
                <span className="text-slate-500 block text-[10px]">COLLECTION TIMESTAMP</span>
                <span className="text-slate-300 text-[11px]">
                  {new Date(selectedEvidence.collected_at).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Raw JSON Telemetry Payload */}
            {selectedEvidence.raw_payload_json && (
              <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-1.5 text-slate-400 text-xs font-mono">
                    <Code2 className="w-3.5 h-3.5" />
                    <span>Raw Telemetry Payload</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">Immutable Hash Provenance</span>
                </div>
                <pre className="p-3 bg-[#08090d] border border-[#1a2133] rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto max-h-60">
                  {JSON.stringify(selectedEvidence.raw_payload_json, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-xs font-mono text-slate-500">
            Select an evidence card to inspect provenance telemetry.
          </div>
        )}
      </div>
    </div>
  );
};
