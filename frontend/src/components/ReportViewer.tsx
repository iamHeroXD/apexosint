import React, { useState, useEffect } from "react";
import { FileText, Download, Printer, Copy, Check, RefreshCw } from "lucide-react";
import { api } from "../api/client";

interface ReportViewerProps {
  investigationId: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ investigationId }) => {
  const [report, setReport] = useState<{ id: string; title: string; classification: string; content_markdown: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchOrGenerateReport = async () => {
    if (!investigationId) return;
    setIsLoading(true);
    try {
      const data = await api.generateReport(investigationId, {
        classification: "CONFIDENTIAL / DEFENSIVE RECONNAISSANCE DOSSIER",
        format: "markdown",
      });
      setReport(data);
    } catch (err) {
      console.error("Failed to generate report:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrGenerateReport();
  }, [investigationId]);

  const handleCopy = () => {
    if (!report) return;
    navigator.clipboard.writeText(report.content_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportBundle = async () => {
    try {
      const bundle = await api.exportBundle(investigationId);
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `apex-investigation-${investigationId}.json`;
      a.click();
    } catch (err) {
      console.error("Export bundle failed:", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto w-full space-y-4">
        {/* Header Action Bar */}
        <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-sky-400" />
            <div>
              <h2 className="text-sm font-bold font-mono text-slate-100">
                APEX Intelligence Dossier
              </h2>
              <span className="text-[10px] font-mono text-rose-400 uppercase font-semibold">
                {report?.classification || "CONFIDENTIAL"}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Markdown"}</span>
            </button>

            <button
              onClick={() => window.print()}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-xs font-mono text-slate-300 transition-colors"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / PDF</span>
            </button>

            <button
              onClick={handleExportBundle}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs font-mono transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Case JSON</span>
            </button>
          </div>
        </div>

        {/* Report Content Document */}
        {isLoading ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            Synthesizing intelligence dossier and cross-referencing evidence citations...
          </div>
        ) : report ? (
          <div className="bg-[#0f121a] border border-[#1f2638] rounded-xl p-8 shadow-2xl font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap select-text">
            {report.content_markdown}
          </div>
        ) : (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            No report generated yet.
          </div>
        )}
      </div>
    </div>
  );
};
