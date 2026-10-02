import React, { useState } from "react";
import {
  Sparkles,
  Send,
  Cpu,
  ShieldCheck,
  Bot,
  User,
  Wrench,
  ChevronDown,
  Layers,
  HelpCircle,
} from "lucide-react";
import { AIChatMessage } from "../types";
import { api } from "../api/client";

interface AICopilotPanelProps {
  investigationId: string;
  onOpenReport?: () => void;
}

const AGENT_MODES = [
  { id: "ANALYST", label: "Senior Analyst", desc: "Synthesizes evidence and identifies patterns" },
  { id: "INVESTIGATOR", label: "Lead Investigator", desc: "Selects tools and probes public sources" },
  { id: "CORRELATOR", label: "Graph Correlator", desc: "Links infrastructure and identities" },
  { id: "VERIFIER", label: "Adversarial Verifier", desc: "Challenges assumptions & spots contradictions" },
  { id: "REPORTER", label: "Dossier Reporter", desc: "Formats formal intelligence briefings" },
  { id: "SUMMARIZER", label: "Executive Summarizer", desc: "10-line executive takeaways" },
];

const PROMPT_SUGGESTIONS = [
  "What did we discover?",
  "Show me all domains connected to this target.",
  "Find contradictions across evidence.",
  "What should I investigate next?",
  "Summarize this investigation in 10 lines.",
];

export const AICopilotPanel: React.FC<AICopilotPanelProps> = ({
  investigationId,
  onOpenReport,
}) => {
  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      id: "welcome-msg",
      sender: "copilot",
      mode: "ANALYST",
      text: "APEX Intelligence Copilot initialized. I am grounded on the active investigation database and can select approved OSINT tools through function calling. What would you like to analyze?",
      timestamp: new Date().toLocaleTimeString(),
      classification: "OBSERVED EVIDENCE",
    },
  ]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("ANALYST");
  const [isSending, setIsSending] = useState(false);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || isSending || !investigationId) return;

    const userMsg: AIChatMessage = {
      id: `usr-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const res = await api.aiChat({
        investigation_id: investigationId,
        message: textToSend,
        mode: mode,
      });

      const copilotMsg: AIChatMessage = {
        id: `cpl-${Date.now()}`,
        sender: "copilot",
        mode: mode,
        text: res.response,
        cited_evidence_ids: res.cited_evidence_ids,
        classification: res.classification,
        tool_executed: res.tool_executed,
        tool_result: res.tool_result,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "copilot",
          mode: mode,
          text: `Analysis error: ${err.message || "Failed to reach AI copilot"}`,
          timestamp: new Date().toLocaleTimeString(),
          classification: "UNVERIFIED",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] border-l border-[#1f2638] overflow-hidden">
      {/* Top Copilot Bar */}
      <div className="p-3 border-b border-[#1f2638] bg-[#0c0e15] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-mono text-xs font-bold text-slate-200 block">
              APEX Intelligence Copilot
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              Grounded Evidence Reasoning
            </span>
          </div>
        </div>

        {/* Mode Selector */}
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          className="bg-[#141824] border border-[#1f2638] text-[11px] font-mono text-slate-300 rounded px-2 py-1 focus:outline-none focus:border-purple-500"
        >
          {AGENT_MODES.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {/* Suggestion Pills */}
      <div className="px-3 py-2 border-b border-[#141824] bg-[#0a0c12] flex items-center space-x-1.5 overflow-x-auto text-[11px] font-mono no-scrollbar">
        <span className="text-slate-600 shrink-0">Quick ask:</span>
        {PROMPT_SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(s)}
            className="shrink-0 px-2.5 py-0.5 rounded-full bg-[#121622] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-sky-300 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === "user" ? "items-end" : "items-start"
            }`}
          >
            <div className="flex items-center space-x-2 mb-1 text-[10px] font-mono text-slate-500">
              {msg.sender === "copilot" ? (
                <>
                  <Bot className="w-3 h-3 text-purple-400" />
                  <span className="text-purple-400 font-semibold">{msg.mode}</span>
                  {msg.classification && (
                    <span className="px-1.5 py-0.2 rounded bg-[#141824] border border-[#232c42] text-slate-400">
                      {msg.classification}
                    </span>
                  )}
                </>
              ) : (
                <>
                  <User className="w-3 h-3 text-sky-400" />
                  <span>Analyst</span>
                </>
              )}
              <span>{msg.timestamp}</span>
            </div>

            {/* Message Bubble */}
            <div
              className={`max-w-xl rounded-xl p-3.5 text-xs font-sans leading-relaxed ${
                msg.sender === "user"
                  ? "bg-sky-500/10 border border-sky-500/30 text-slate-200"
                  : "bg-[#0f121a] border border-[#1f2638] text-slate-200 shadow-md"
              }`}
            >
              {/* Tool Execution Alert Badge if Gemini invoked a tool */}
              {msg.tool_executed && (
                <div className="mb-2.5 p-2 rounded bg-[#141824] border border-purple-500/30 flex items-center space-x-2 text-[11px] font-mono text-purple-300">
                  <Wrench className="w-3.5 h-3.5" />
                  <span>Executed Tool: <strong>`{msg.tool_executed}`</strong></span>
                </div>
              )}

              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Cited Evidence IDs footer */}
              {msg.cited_evidence_ids && msg.cited_evidence_ids.length > 0 && (
                <div className="mt-3 pt-2 border-t border-[#1a2133] flex items-center flex-wrap gap-1.5 text-[10px] font-mono text-slate-400">
                  <span className="text-slate-500">Evidence Provenance:</span>
                  {msg.cited_evidence_ids.map((evId, idx) => (
                    <span
                      key={idx}
                      className="px-1.5 py-0.5 rounded bg-[#141824] border border-sky-500/30 text-sky-400 font-bold"
                    >
                      {evId}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isSending && (
          <div className="flex items-center space-x-2 text-xs font-mono text-purple-400 p-2">
            <span className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></span>
            <span>Gemini reasoning over investigation evidence...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 border-t border-[#1f2638] bg-[#0c0e15]"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            placeholder="Ask AI Copilot to correlate, analyze, or verify evidence..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isSending}
            className="w-full bg-[#141824] border border-[#1f2638] focus:border-purple-500/60 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none pr-10"
          />
          <button
            type="submit"
            disabled={!input.trim() || isSending}
            className="absolute right-2 p-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-40 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
};
