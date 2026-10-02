import React from "react";
import {
  Home,
  Search,
  Share2,
  Clock,
  Users,
  ShieldCheck,
  FileText,
  Sparkles,
  Database,
  Cpu,
  Settings,
} from "lucide-react";

interface LeftSidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

const NAV_ITEMS = [
  { id: "home", label: "Home", icon: Home },
  { id: "investigations", label: "Investigations", icon: Search },
  { id: "graph", label: "Graph", icon: Share2 },
  { id: "timeline", label: "Timeline", icon: Clock },
  { id: "entities", label: "Entities", icon: Users },
  { id: "evidence", label: "Evidence", icon: ShieldCheck },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "analyst", label: "AI Analyst", icon: Sparkles },
  { id: "sources", label: "Sources", icon: Database },
  { id: "modules", label: "Modules", icon: Cpu },
  { id: "settings", label: "Settings", icon: Settings },
];

export const LeftSidebar: React.FC<LeftSidebarProps> = ({ activeTab, onSelectTab }) => {
  return (
    <aside className="w-60 bg-[#080b12] border-r border-[#151c2c] flex flex-col justify-between p-4 shrink-0 select-none">
      {/* Brand & Logo */}
      <div className="space-y-6">
        <div
          onClick={() => onSelectTab("home")}
          className="flex items-center space-x-3 cursor-pointer group px-2 py-1"
        >
          {/* Stylized Geometric Triangle 'A' Logo */}
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center relative overflow-hidden group-hover:border-blue-400 transition-colors">
            <svg
              className="w-5 h-5 text-blue-400 group-hover:scale-105 transition-transform"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="12 2 22 20 2 20" />
              <line x1="6.5" y1="14" x2="17.5" y2="14" />
            </svg>
          </div>
          <div>
            <span className="font-extrabold text-sm tracking-wider text-slate-100 font-mono block">
              APEX OSINT
            </span>
            <span className="text-[9px] font-mono text-sky-400 uppercase tracking-widest block font-semibold">
              INTELLIGENCE, CONNECTED.
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs font-mono transition-all text-left ${
                  isActive
                    ? "bg-[#131b2e] text-blue-400 font-bold border border-blue-500/20 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#0e1320]"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Local Status Card */}
      <div className="bg-[#0e1320] border border-[#1b2336] rounded-xl p-3 flex items-center space-x-3">
        <div className="w-7 h-7 rounded-lg bg-blue-600/10 border border-blue-500/30 flex items-center justify-center shrink-0">
          <svg className="w-3.5 h-3.5 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12 2 22 20 2 20" />
          </svg>
        </div>
        <div className="truncate">
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-bold font-mono text-slate-200">APEX OSINT</span>
            <span className="text-[9px] font-mono text-slate-500">v1.0.0</span>
          </div>
          <div className="flex items-center space-x-1.5 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[10px] font-mono text-emerald-400 font-medium">Running locally</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
