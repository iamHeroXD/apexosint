import React, { useState, useEffect } from "react";
import { Activity, Calendar, ShieldCheck, GitCommit, FileText, Globe } from "lucide-react";
import { TimelineEvent } from "../types";
import { api } from "../api/client";

interface TimelineStreamProps {
  investigationId: string;
}

export const TimelineStream: React.FC<TimelineStreamProps> = ({ investigationId }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!investigationId) return;
    setIsLoading(true);
    api
      .getTimeline(investigationId)
      .then((data) => setEvents(data))
      .catch((err) => console.error("Error fetching timeline:", err))
      .finally(() => setIsLoading(false));
  }, [investigationId]);

  const getEventIcon = (type: string) => {
    if (type.includes("REGISTRATION")) return <Globe className="w-4 h-4 text-sky-400" />;
    if (type.includes("CERTIFICATE")) return <ShieldCheck className="w-4 h-4 text-amber-400" />;
    if (type.includes("REPOSITORY")) return <GitCommit className="w-4 h-4 text-emerald-400" />;
    return <FileText className="w-4 h-4 text-indigo-400" />;
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] p-6 overflow-y-auto">
      <div className="max-w-3xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-8">
          <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-mono text-slate-100">
              Chronological Intelligence Timeline
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Reconstructed historical sequence of domain registrations, certificate issuances, code activities, and exposures.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            Reconstructing chronological timeline...
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500">
            No temporal events recorded for this investigation.
          </div>
        ) : (
          <div className="relative border-l-2 border-[#1f2638] ml-4 pl-6 space-y-8">
            {events.map((ev) => {
              const date = new Date(ev.timestamp);
              const dateStr = date.toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
              });
              const timeStr = date.toLocaleTimeString(undefined, {
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <div key={ev.id} className="relative group">
                  {/* Timeline Node Point */}
                  <div className="absolute -left-[35px] top-1 w-6 h-6 rounded-full bg-[#0f121a] border-2 border-[#26314d] group-hover:border-sky-400 flex items-center justify-center transition-colors">
                    {getEventIcon(ev.event_type)}
                  </div>

                  {/* Event Card */}
                  <div className="bg-[#0f121a] border border-[#1f2638] group-hover:border-sky-500/40 rounded-xl p-4 transition-all">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-mono text-sky-400 font-bold">
                        {dateStr} — {timeStr}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#141824] text-slate-400 border border-[#232c42]">
                        {ev.event_type}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100 font-sans mt-1">
                      {ev.title}
                    </h4>
                    <p className="text-xs text-slate-300 font-sans mt-1 leading-relaxed">
                      {ev.description}
                    </p>

                    <div className="mt-3 pt-2 border-t border-[#1a2133] flex items-center justify-between text-[10px] font-mono text-slate-500">
                      <span>Evidence ID: {ev.evidence_id || "OBSERVED-STREAM"}</span>
                      <span>Confidence: {Math.round(ev.confidence * 100)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
