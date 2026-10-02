import React, { useState, useEffect } from "react";
import { Settings, CheckCircle2, AlertTriangle, Key, Cpu, ShieldCheck, X, Activity } from "lucide-react";
import { api } from "../api/client";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose, onSaved }) => {
  const [settingsData, setSettingsData] = useState<any | null>(null);
  const [geminiKey, setGeminiKey] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [geminiModel, setGeminiModel] = useState("gemini-2.5-flash");
  const [isSaving, setIsSaving] = useState(false);
  const [doctorResults, setDoctorResults] = useState<any | null>(null);
  const [isRunningDoctor, setIsRunningDoctor] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    api.getSettings().then((data) => {
      setSettingsData(data);
      if (data.ai?.model) setGeminiModel(data.ai.model);
    });
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.updateSettings({
        gemini_api_key: geminiKey || undefined,
        github_token: githubToken || undefined,
        gemini_model: geminiModel,
      });
      onSaved();
      onClose();
    } catch (err) {
      console.error("Failed to update settings:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunDoctor = async () => {
    setIsRunningDoctor(true);
    try {
      const doc = await api.runDoctor();
      setDoctorResults(doc);
    } catch (err) {
      console.error("Doctor error:", err);
    } finally {
      setIsRunningDoctor(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-[#0f121a] border border-[#2b354d] rounded-2xl shadow-2xl overflow-hidden flex flex-col font-sans max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#1f2638] bg-[#141824] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Settings className="w-5 h-5 text-sky-400" />
            <h3 className="text-sm font-bold font-mono text-slate-100">
              System Settings & Integration Credentials
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* AI Settings Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Google Gemini Intelligence Model</span>
              </h4>
              <span className="text-[10px] font-mono text-slate-500">
                Configured via Environment / UI
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">
                  Gemini API Key
                </label>
                <input
                  type="password"
                  placeholder="Paste GEMINI_API_KEY..."
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-[#141824] border border-[#1f2638] focus:border-purple-500 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none"
                />
                <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                  Current: {settingsData?.ai?.key_preview || "NOT CONFIGURED"}
                </span>
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">
                  Model Identifier
                </label>
                <select
                  value={geminiModel}
                  onChange={(e) => setGeminiModel(e.target.value)}
                  className="w-full bg-[#141824] border border-[#1f2638] focus:border-purple-500 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none"
                >
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Fast & High Reasoning)</option>
                  <option value="gemini-1.5-pro">gemini-1.5-pro (Deep Multimodal)</option>
                  <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                </select>
              </div>
            </div>
          </div>

          {/* Optional Integrations Grid */}
          <div className="space-y-3 pt-3 border-t border-[#1f2638]">
            <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
              <Key className="w-4 h-4 text-sky-400" />
              <span>External Service Integrations</span>
            </h4>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              {settingsData?.integrations?.map((item: any) => (
                <div
                  key={item.service}
                  className="bg-[#141824] border border-[#1f2638] rounded-lg p-2.5 flex items-center justify-between"
                >
                  <span className="text-slate-300">{item.service}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded border ${
                      item.status.includes("CONNECTED")
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : "bg-slate-800 text-slate-500 border-slate-700"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* APEX Doctor Diagnostics */}
          <div className="space-y-3 pt-3 border-t border-[#1f2638]">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>APEX Doctor System Diagnostics</span>
              </h4>
              <button
                type="button"
                onClick={handleRunDoctor}
                disabled={isRunningDoctor}
                className="flex items-center space-x-1 px-3 py-1 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-[11px] font-mono text-sky-400"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>{isRunningDoctor ? "Checking..." : "Run Diagnostics"}</span>
              </button>
            </div>

            {doctorResults && (
              <div className="bg-[#141824] border border-[#1f2638] rounded-xl p-3 space-y-2">
                {doctorResults.checks.map((chk: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs font-mono border-b border-[#1f2638] pb-1.5 last:border-0 last:pb-0"
                  >
                    <span className="text-slate-300">{chk.component}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] text-slate-500">{chk.details}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                          chk.status === "PASS"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-amber-500/10 text-amber-400"
                        }`}
                      >
                        {chk.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#1f2638] bg-[#141824] flex items-center justify-between">
          <span className="text-xs text-slate-500 font-mono">
            Local-First Mode | SSRF Guard Active
          </span>
          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-[#2b354d] text-xs font-mono text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs font-mono"
            >
              {isSaving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
