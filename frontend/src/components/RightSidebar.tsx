import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Server,
  Database,
  Cpu,
  X,
  Send,
  Loader2,
} from "lucide-react";
import { api } from "../api/client";
import { AIChatMessage } from "../types";

interface RightSidebarProps {
  activeInvestigationId?: string;
  onOpenReport?: () => void;
  geminiActive: boolean;
}

const DEFAULT_PROMPTS = [
  "What did we discover?",
  "Show me related entities",
  "Find contradictions",
  "Generate a report",
  "What should I investigate next?",
];

export const RightSidebar: React.FC<RightSidebarProps> = ({
  activeInvestigationId,
  onOpenReport,
  geminiActive,
}) => {
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showProTip, setShowProTip] = useState(true);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    if (textToSend.toLowerCase().includes("generate a report") && onOpenReport) {
      onOpenReport();
    }

    const userMsg: AIChatMessage = {
      id: `u-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      if (activeInvestigationId) {
        const res = await api.aiChat({
          investigation_id: activeInvestigationId,
          message: textToSend,
        });

        const copilotMsg: AIChatMessage = {
          id: `c-${Date.now()}`,
          sender: "copilot",
          text: res.response,
          cited_evidence_ids: res.cited_evidence_ids,
          classification: res.classification,
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, copilotMsg]);
      } else {
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              id: `c-${Date.now()}`,
              sender: "copilot",
              text: "To analyze findings deeply, launch an investigation or select a target from Home. I'm ready to synthesize evidence with full provenance.",
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);
          setIsLoading(false);
        }, 500);
        return;
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: `c-${Date.now()}`,
          sender: "copilot",
          text: "Defensive synthesis ready. Select an active investigation or run a scan to correlate live records.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="w-80 bg-[#080b12] border-l border-[#151c2c] flex flex-col justify-between p-4 shrink-0 overflow-y-auto font-sans select-text space-y-6">
      {/* AI Copilot Card */}
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <h3 className="text-sm font-bold font-mono text-slate-100">AI Copilot</h3>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30">
            Beta
          </span>
        </div>

        {/* Greeting Bubble */}
        <div className="bg-[#0f1422] border border-[#1b2336] rounded-2xl p-4 flex items-start space-x-3 shadow-sm">
          <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/40 text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            Ask me anything about your investigation. I can analyze evidence, find connections, explain findings, or suggest next steps.
          </p>
        </div>

        {/* Message Log if chatted */}
        {messages.length > 0 && (
          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`p-2.5 rounded-xl text-xs font-mono leading-relaxed ${
                  m.sender === "user"
                    ? "bg-[#141c30] text-blue-200 border border-blue-500/30 ml-4"
                    : "bg-[#0f1422] text-slate-200 border border-[#1b2336] mr-4"
                }`}
              >
                {m.text}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-500 p-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                <span>Synthesizing intelligence...</span>
              </div>
            )}
          </div>
        )}

        {/* Suggestion Prompts */}
        {messages.length === 0 && (
          <div className="space-y-1.5">
            {DEFAULT_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(prompt)}
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-[#0e1320] hover:bg-[#141b2e] border border-[#1a2338] text-xs font-mono text-slate-300 hover:text-white transition-colors group text-left"
              >
                <span>{prompt}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </button>
            ))}
          </div>
        )}

        {/* Question Input */}
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSendMessage(input);
            }}
            placeholder="Ask a question..."
            className="w-full bg-[#0e1320] border border-[#1b2336] focus:border-blue-500 rounded-xl px-3 py-2 pr-10 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={() => handleSendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="absolute right-1.5 top-1.5 w-7 h-7 rounded-lg bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-colors disabled:opacity-40"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* System Status Section */}
      <div className="space-y-3 pt-3 border-t border-[#151c2c]">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold font-mono text-slate-200">System Status</h4>
          <span className="flex items-center space-x-1.5 text-[10px] font-mono text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>All systems operational</span>
          </span>
        </div>

        <div className="bg-[#0e1320] border border-[#1a2338] rounded-xl p-3 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400 flex items-center space-x-1.5">
              <Server className="w-3 h-3 text-slate-500" />
              <span>Backend API</span>
            </span>
            <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
              <span>Online</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400 flex items-center space-x-1.5">
              <Database className="w-3 h-3 text-slate-500" />
              <span>Database</span>
            </span>
            <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
              <span>Online</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400 flex items-center space-x-1.5">
              <Sparkles className="w-3 h-3 text-purple-400" />
              <span>Gemini API</span>
            </span>
            <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
              <span>{geminiActive ? "Connected" : "Standby"}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            </span>
          </div>

          <div className="flex items-center justify-between text-slate-300">
            <span className="text-slate-400 flex items-center space-x-1.5">
              <Cpu className="w-3 h-3 text-slate-500" />
              <span>Modules</span>
            </span>
            <span className="flex items-center space-x-1 text-emerald-400 text-[11px]">
              <span>102 enabled</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            </span>
          </div>
        </div>
      </div>

      {/* Pro Tip Dismissible Card */}
      {showProTip && (
        <div className="bg-[#0f1526] border border-blue-500/20 rounded-xl p-3 relative flex items-start space-x-2.5">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <div className="pr-4">
            <h5 className="text-[11px] font-bold font-mono text-slate-200">Pro Tip</h5>
            <p className="text-[10px] text-slate-400 font-sans mt-0.5 leading-relaxed">
              Use <kbd className="px-1 py-0.5 rounded bg-[#18233c] text-slate-300 font-mono text-[9px]">Ctrl + K</kbd> to open the command palette and access quick actions.
            </p>
          </div>
          <button
            onClick={() => setShowProTip(false)}
            className="absolute top-2 right-2 text-slate-500 hover:text-slate-300"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </aside>
  );
};
