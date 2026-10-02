import React, { useState } from "react";
import {
  Search,
  ArrowRight,
  Bell,
  Moon,
  ChevronDown,
  User,
  Sliders,
} from "lucide-react";

interface TopNavbarProps {
  onSearch: (query: string) => void;
  onOpenSettings: () => void;
  onOpenCommandPalette: () => void;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  onSearch,
  onOpenSettings,
  onOpenCommandPalette,
}) => {
  const [topQuery, setTopQuery] = useState("");

  const handleTopSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topQuery.trim()) {
      onSearch(topQuery.trim());
      setTopQuery("");
    }
  };

  return (
    <header className="h-16 bg-[#080b12] border-b border-[#151c2c] px-6 flex items-center justify-between z-20 shrink-0 select-none">
      {/* Top Search Input Bar */}
      <form onSubmit={handleTopSubmit} className="flex-1 max-w-2xl">
        <div className="relative group">
          <div className="relative bg-[#0e1320] border border-[#1b2336] focus-within:border-blue-500 rounded-xl px-3.5 py-1.5 flex items-center space-x-2.5 transition-all">
            <Search className="w-4 h-4 text-slate-500 group-hover:text-slate-400" />
            <input
              type="text"
              value={topQuery}
              onChange={(e) => setTopQuery(e.target.value)}
              placeholder="Enter anything to investigate... (domain, email, username, IP, name, etc.)"
              className="w-full bg-transparent text-slate-200 placeholder-slate-500 text-xs font-mono focus:outline-none"
            />
            <button
              type="submit"
              disabled={!topQuery.trim()}
              className="w-7 h-7 rounded-lg bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-colors disabled:opacity-40 shrink-0"
            >
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </form>

      {/* Right Controls */}
      <div className="flex items-center space-x-3.5 pl-4">
        {/* Notification Bell */}
        <button
          onClick={onOpenCommandPalette}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-[#0e1320] transition-colors relative"
          title="Notifications & Activity (Ctrl+K)"
        >
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-blue-500 absolute top-1.5 right-1.5"></span>
        </button>

        {/* Theme Dark Mode Toggle */}
        <button
          className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-[#0e1320] transition-colors"
          title="Dark Mode Active"
        >
          <Moon className="w-4 h-4" />
        </button>

        {/* User Avatar & Dropdown */}
        <div
          onClick={onOpenSettings}
          className="flex items-center space-x-2 pl-2 border-l border-[#151c2c] cursor-pointer hover:opacity-85 transition-opacity"
        >
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold font-mono text-xs text-slate-200">
            R
          </div>
          <span className="text-xs font-mono font-semibold text-slate-200 hidden sm:inline">
            Rohan
          </span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
        </div>
      </div>
    </header>
  );
};
