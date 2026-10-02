import React, { useState, useEffect } from "react";
import {
  Search,
  Compass,
  FileText,
  Activity,
  Layers,
  Sparkles,
  ShieldAlert,
  Play,
  Settings,
  X,
} from "lucide-react";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectAction: (actionId: string) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectAction,
}) => {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose();
        else onSelectAction("open_palette");
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, onSelectAction]);

  if (!isOpen) return null;

  const commands = [
    { id: "nav_control", title: "Control Room & AI Persona Dossier", category: "Cockpit", icon: Sparkles, shortcut: "G O" },
    { id: "nav_search", title: "Universal Target Search", category: "Investigation", icon: Search, shortcut: "G T" },
    { id: "nav_graph", title: "Open Evidence Graph Visualizer", category: "Visualization", icon: Layers, shortcut: "G G" },
    { id: "nav_evidence", title: "Inspect Evidence Provenance Matrix", category: "Intelligence", icon: Compass, shortcut: "G E" },
    { id: "nav_contradictions", title: "View Detected Contradictions", category: "Verification", icon: ShieldAlert, shortcut: "G X" },
    { id: "nav_timeline", title: "Inspect Chronological Timeline", category: "Intelligence", icon: Activity, shortcut: "G L" },
    { id: "nav_report", title: "Generate Intelligence Dossier", category: "Reporting", icon: FileText, shortcut: "G R" },
    { id: "nav_modules", title: "Open Module Health Center", category: "Modules", icon: Activity, shortcut: "G M" },
    { id: "launch_demo", title: "Load Apex Demo Corporation Sandbox", category: "Demo", icon: Play, shortcut: "Ctrl+D" },
    { id: "open_settings", title: "System Diagnostics & API Keys", category: "System", icon: Settings, shortcut: "Ctrl+," },
  ];

  const filtered = commands.filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-[#0f121a] border border-[#2b354d] rounded-xl shadow-2xl overflow-hidden flex flex-col font-sans">
        {/* Search Input */}
        <div className="flex items-center px-4 py-3 border-b border-[#1f2638] bg-[#141824]">
          <Search className="w-4 h-4 text-sky-400 mr-3" />
          <input
            autoFocus
            type="text"
            placeholder="Type a command or search action..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none font-mono"
          />
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-300 p-1 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500 font-mono">
              No matching commands found.
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    onSelectAction(item.id);
                    onClose();
                  }}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-[#1a2133] cursor-pointer text-xs group transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-1.5 rounded bg-[#141824] border border-[#252f47] group-hover:border-sky-500/40 text-slate-400 group-hover:text-sky-400">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <span className="text-slate-200 font-medium group-hover:text-sky-300">
                        {item.title}
                      </span>
                      <span className="ml-2 text-[10px] text-slate-500 font-mono">
                        {item.category}
                      </span>
                    </div>
                  </div>
                  {item.shortcut && (
                    <span className="font-mono text-[10px] text-slate-500 bg-[#121622] px-1.5 py-0.5 rounded border border-[#1f2638]">
                      {item.shortcut}
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts hint */}
        <div className="px-4 py-2 border-t border-[#1f2638] bg-[#0c0e15] flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <div className="flex items-center space-x-3">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>Esc Close</span>
          </div>
          <span>APEX Intelligence</span>
        </div>
      </div>
    </div>
  );
};
