import React, { useState } from "react";
import {
  Search,
  ArrowRight,
  Shield,
  Clock,
  Globe,
  User,
  Server,
  Code2,
  Trash2,
  Download,
  ExternalLink,
  ChevronRight,
  Plus,
} from "lucide-react";
import { Investigation } from "../types";
import { api } from "../api/client";

interface InvestigationsListProps {
  investigations: Investigation[];
  onSelectInvestigation: (inv: Investigation) => void;
  onNewInvestigation: () => void;
}

export const InvestigationsList: React.FC<InvestigationsListProps> = ({
  investigations,
  onSelectInvestigation,
  onNewInvestigation,
}) => {
  const [filterQuery, setFilterQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const filtered = investigations.filter((inv) => {
    if (statusFilter !== "ALL" && inv.status.toLowerCase() !== statusFilter.toLowerCase()) return false;
    if (filterQuery.trim()) {
      const q = filterQuery.toLowerCase();
      return inv.title.toLowerCase().includes(q) || inv.id.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0a0d14] overflow-y-auto px-6 py-8 select-text font-sans">
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold font-mono text-slate-100">
              Investigations Case Vault
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              All ongoing and completed intelligence cases with full provenance records
            </p>
          </div>

          <button
            onClick={onNewInvestigation}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono font-bold transition-all shadow-md shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>New Investigation</span>
          </button>
        </div>

        {/* Filter Controls */}
        <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center space-x-2">
            {["ALL", "COMPLETED", "RUNNING", "PENDING"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                  statusFilter === st
                    ? "bg-blue-600 text-white font-bold"
                    : "bg-[#141b2e] text-slate-400 hover:text-slate-200 border border-[#1c263d]"
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder="Search cases..."
              className="bg-[#141b2e] border border-[#1c263d] rounded-xl pl-8 pr-3 py-1.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-52 sm:w-64"
            />
          </div>
        </div>

        {/* Case Table / Cards */}
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="p-12 text-center text-xs font-mono text-slate-500 bg-[#0f1422] border border-[#1b2336] rounded-2xl">
              No investigations match the current filter.
            </div>
          ) : (
            filtered.map((inv) => {
              const isRunning = inv.status === "running";
              return (
                <div
                  key={inv.id}
                  onClick={() => onSelectInvestigation(inv)}
                  className="bg-[#0f1422] border border-[#1b2336] hover:border-blue-500/50 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer transition-all group shadow-sm hover:shadow-md"
                >
                  <div className="flex items-center space-x-3.5 truncate">
                    <div className="w-10 h-10 rounded-xl bg-[#141b2e] border border-[#1e2840] flex items-center justify-center shrink-0">
                      <Globe className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="truncate">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-bold font-mono text-slate-100 group-hover:text-blue-400 transition-colors truncate">
                          {inv.title}
                        </h3>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-semibold uppercase ${
                            isRunning
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">
                        ID: {inv.id} • Mode: {inv.mode.toUpperCase()} (Depth {inv.depth})
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 shrink-0 sm:self-center">
                    <div className="text-right hidden md:block">
                      <span className="text-xs font-mono text-slate-300 block">
                        {inv.summary_json?.entities_count || 12} Entities Resolved
                      </span>
                      <span className="text-[11px] font-mono text-slate-500 block">
                        {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "Active"}
                      </span>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectInvestigation(inv);
                      }}
                      className="px-3.5 py-1.5 rounded-xl bg-blue-600/15 hover:bg-blue-600/25 border border-blue-500/30 text-blue-400 text-xs font-mono font-bold transition-colors flex items-center space-x-1"
                    >
                      <span>Open Case</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
