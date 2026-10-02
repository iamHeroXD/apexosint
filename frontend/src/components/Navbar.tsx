import React from "react";
import {
  ShieldAlert,
  Terminal,
  Search,
  Sparkles,
  Settings as SettingsIcon,
  Activity,
  FolderOpen,
  Play,
  Crosshair,
  Sliders,
  ChevronDown,
  Layers,
  FileText,
} from "lucide-react";
import { Workspace, Investigation } from "../types";

interface NavbarProps {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  investigations: Investigation[];
  activeInvestigation: Investigation | null;
  onSelectInvestigation: (inv: Investigation) => void;
  onOpenCommandPalette: () => void;
  onOpenSettings: () => void;
  onLaunchDemo: () => void;
  geminiActive: boolean;
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  investigations,
  activeInvestigation,
  onSelectInvestigation,
  onOpenCommandPalette,
  onOpenSettings,
  onLaunchDemo,
  geminiActive,
  activeTab,
  onSelectTab,
}) => {
  return (
    <header className="h-14 border-b border-[#171b26] bg-[#080a10] px-4 flex items-center justify-between z-30 select-none shadow-md">
      {/* Brand & Left Navigation */}
      <div className="flex items-center space-x-5">
        <div
          onClick={() => onSelectTab("control")}
          className="flex items-center space-x-2.5 cursor-pointer group"
        >
          {/* Cybernetic geometric icon */}
          <div className="w-8 h-8 rounded-lg border border-sky-500/40 bg-sky-950/40 flex items-center justify-center relative overflow-hidden group-hover:border-sky-400 group-hover:shadow-[0_0_12px_rgba(56,189,248,0.3)] transition-all">
            <svg
              className="w-4 h-4 text-sky-400 group-hover:scale-110 transition-transform"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
              <circle cx="12" cy="12" r="3" fill="#38bdf8" fillOpacity="0.5" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-extrabold text-sm tracking-widest text-slate-100 font-mono">
                APEX
              </span>
              <span className="text-[10px] font-mono font-semibold px-1.5 py-0.2 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                CONTROL
              </span>
            </div>
            <p className="text-[10px] text-slate-500 tracking-tight font-mono">
              Intelligence, connected.
            </p>
          </div>
        </div>

        {/* Workspace Dropdown */}
        <div className="hidden lg:flex items-center space-x-1.5 pl-3 border-l border-[#1a2030]">
          <FolderOpen className="w-3.5 h-3.5 text-slate-500" />
          <select
            value={activeWorkspace?.id || ""}
            onChange={(e) => {
              const ws = workspaces.find((w) => w.id === e.target.value);
              if (ws) onSelectWorkspace(ws);
            }}
            className="bg-[#10141f] border border-[#1e2538] text-xs text-slate-300 rounded px-2 py-0.5 focus:outline-none focus:border-sky-500 font-mono"
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name}
              </option>
            ))}
          </select>
        </div>

        {/* Active Target Quick Switcher */}
        {investigations.length > 0 && (
          <div className="flex items-center space-x-1.5 pl-3 border-l border-[#1a2030]">
            <Crosshair className="w-3.5 h-3.5 text-sky-400" />
            <select
              value={activeInvestigation?.id || ""}
              onChange={(e) => {
                const inv = investigations.find((i) => i.id === e.target.value);
                if (inv) onSelectInvestigation(inv);
              }}
              className="bg-[#10141f] border border-sky-500/30 text-xs text-sky-300 rounded px-2.5 py-1 focus:outline-none focus:border-sky-400 font-mono max-w-[220px] truncate"
            >
              {investigations.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.title}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Center Nav tabs: High-Density Control Room Navigation */}
      <nav className="hidden xl:flex items-center space-x-1">
        {[
          { id: "control", label: "Control Room", highlight: true },
          { id: "search", label: "New Target" },
          { id: "graph", label: "Graph" },
          { id: "evidence", label: "Evidence" },
          { id: "contradictions", label: "Conflicts" },
          { id: "timeline", label: "Timeline" },
          { id: "report", label: "Dossier" },
          { id: "modules", label: "Engines" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center space-x-1.5 ${
              activeTab === tab.id
                ? "bg-sky-500/15 text-sky-400 border border-sky-500/35 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#121622]"
            }`}
          >
            {tab.id === "control" && (
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping"></span>
            )}
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>

      {/* Right Quick Controls */}
      <div className="flex items-center space-x-2">
        {/* Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center space-x-2 bg-[#10141f] hover:bg-[#161c2b] border border-[#1e2538] text-slate-400 hover:text-slate-200 text-xs px-2.5 py-1 rounded-lg transition-colors"
          title="Command Palette (Ctrl + K)"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline font-mono text-[11px]">Ctrl+K</span>
        </button>

        {/* 1-Click Demo Sandbox */}
        <button
          onClick={onLaunchDemo}
          className="flex items-center space-x-1.5 bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-500/40 text-emerald-400 text-xs px-2.5 py-1 rounded-lg font-mono transition-all shadow-sm"
          title="Load Apex Demo Corporation synthetic investigation"
        >
          <Play className="w-3 h-3 fill-emerald-400" />
          <span className="hidden sm:inline">Demo Sandbox</span>
        </button>

        {/* AI Copilot Status Badge */}
        <div
          className={`flex items-center space-x-1.5 text-[11px] font-mono px-2 py-0.5 rounded-md border ${
            geminiActive
              ? "bg-purple-950/30 text-purple-300 border-purple-500/40 shadow-[0_0_8px_rgba(168,85,247,0.15)]"
              : "bg-slate-900/50 text-slate-400 border-slate-700/40"
          }`}
          title={
            geminiActive
              ? "Gemini Intelligence Engine connected"
              : "Local Grounded Engine active"
          }
        >
          <Sparkles className="w-3 h-3 text-purple-400" />
          <span className="hidden sm:inline">
            {geminiActive ? "Gemini AI" : "Local AI"}
          </span>
        </div>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          className="p-1.5 rounded-lg bg-[#10141f] hover:bg-[#161c2b] border border-[#1e2538] text-slate-400 hover:text-slate-200 transition-colors"
          title="Settings & System Diagnostics"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
