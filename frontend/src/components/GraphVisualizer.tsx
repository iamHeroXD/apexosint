import React, { useEffect, useRef, useState } from "react";
import cytoscape, { Core } from "cytoscape";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Search,
  RefreshCw,
  EyeOff,
  Sliders,
  Layers,
} from "lucide-react";
import { api } from "../api/client";

interface GraphVisualizerProps {
  investigationId: string;
  onSelectEntityId: (id: string) => void;
  onInvestigateEntity: (value: string) => void;
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({
  investigationId,
  onSelectEntityId,
  onInvestigateEntity,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>("");
  const [minConfidence, setMinConfidence] = useState<number>(0.0);
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState<{ node_count: number; edge_count: number; node_types: string[] }>({
    node_count: 0,
    edge_count: 0,
    node_types: [],
  });
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [selectedEdgeData, setSelectedEdgeData] = useState<any | null>(null);

  const fetchAndRenderGraph = async () => {
    if (!containerRef.current || !investigationId) return;
    setIsLoading(true);

    try {
      const data = await api.getGraph(investigationId, selectedType || undefined, minConfidence);
      setStats(data.stats);

      if (cyRef.current) {
        cyRef.current.destroy();
      }

      const cy = cytoscape({
        container: containerRef.current,
        elements: [...data.nodes, ...data.edges],
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "background-color": "data(color)",
              "color": "#f1f5f9",
              "font-family": "JetBrains Mono, monospace",
              "font-size": "10px",
              "text-valign": "bottom",
              "text-margin-y": 5,
              "text-background-color": "#090a0f",
              "text-background-opacity": 0.8,
              "text-background-padding": "2px",
              "text-background-shape": "roundrectangle",
              width: 32,
              height: 32,
              "border-width": 2,
              "border-color": "#1f2638",
              "transition-property": "border-width, border-color, width, height",
              "transition-duration": 0.2,
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-color": "#38bdf8",
              "border-width": 4,
              width: 38,
              height: 38,
            },
          },
          {
            selector: "edge",
            style: {
              width: 1.5,
              "line-color": "#2a344d",
              "target-arrow-color": "#38bdf8",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-family": "JetBrains Mono, monospace",
              "font-size": "8px",
              "color": "#64748b",
              "text-rotation": "autorotate",
              "text-background-color": "#090a0f",
              "text-background-opacity": 0.8,
              "text-background-padding": "1px",
            },
          },
          {
            selector: "edge[?is_ai_inferred]",
            style: {
              "line-style": "dashed",
              "line-color": "#818cf8",
            },
          },
        ],
        layout: {
          name: "cose",
          idealEdgeLength: 100,
          nodeOverlap: 20,
          refresh: 20,
          fit: true,
          padding: 30,
          randomize: false,
          componentSpacing: 100,
          nodeRepulsion: 400000,
          edgeElasticity: 100,
          nestingFactor: 5,
          gravity: 80,
          numIter: 1000,
          initialTemp: 200,
          coolingFactor: 0.95,
          minTemp: 1.0,
        },
      });

      // Events
      cy.on("tap", "node", (evt) => {
        const node = evt.target;
        setSelectedNodeData(node.data());
        setSelectedEdgeData(null);
        onSelectEntityId(node.data("id"));
      });

      cy.on("tap", "edge", (evt) => {
        const edge = evt.target;
        setSelectedEdgeData(edge.data());
        setSelectedNodeData(null);
      });

      cy.on("tap", (evt) => {
        if (evt.target === cy) {
          setSelectedNodeData(null);
          setSelectedEdgeData(null);
        }
      });

      cyRef.current = cy;
    } catch (err) {
      console.error("Failed to render graph:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAndRenderGraph();
    return () => {
      if (cyRef.current) cyRef.current.destroy();
    };
  }, [investigationId, selectedType, minConfidence]);

  // Handle Search Filtering
  const handleSearch = (term: string) => {
    setSearchQuery(term);
    if (!cyRef.current) return;
    const cy = cyRef.current;
    if (!term.trim()) {
      cy.elements().removeClass("highlighted dimmed");
      return;
    }
    const matching = cy.nodes().filter((n) =>
      n.data("full_value").toLowerCase().includes(term.toLowerCase())
    );
    if (matching.length > 0) {
      cy.elements().addClass("dimmed");
      matching.removeClass("dimmed").addClass("highlighted");
      cy.fit(matching, 50);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#08090d] relative overflow-hidden select-none">
      {/* Top Toolbar */}
      <div className="h-12 border-b border-[#1f2638] bg-[#0c0e15] px-4 flex items-center justify-between z-10">
        <div className="flex items-center space-x-3">
          {/* Search in graph */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search graph node..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="bg-[#141824] border border-[#1f2638] text-xs text-slate-200 pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-sky-500 w-48 font-mono"
            />
          </div>

          {/* Filter by Type */}
          <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-[#141824] border border-[#1f2638] text-xs text-slate-300 rounded px-2 py-1 focus:outline-none focus:border-sky-500 font-mono"
            >
              <option value="">All Entity Types</option>
              {stats.node_types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Minimum Confidence Slider */}
          <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-slate-400 pl-2 border-l border-[#1f2638]">
            <span>Min Conf:</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-16 accent-sky-400 cursor-pointer"
            />
            <span className="text-slate-300 w-8">{Math.round(minConfidence * 100)}%</span>
          </div>
        </div>

        {/* Zoom & Layout Actions */}
        <div className="flex items-center space-x-1 text-xs">
          <div className="px-2.5 py-1 rounded bg-[#141824] border border-[#1f2638] text-slate-400 font-mono text-[11px] mr-2">
            Nodes: <span className="text-sky-400 font-bold">{stats.node_count}</span> | Edges:{" "}
            <span className="text-indigo-400 font-bold">{stats.edge_count}</span>
          </div>

          <button
            onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.25)}
            className="p-1.5 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-slate-200"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
            className="p-1.5 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-slate-200"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => cyRef.current?.fit(undefined, 30)}
            className="p-1.5 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-slate-200"
            title="Fit to view"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={fetchAndRenderGraph}
            className="p-1.5 rounded bg-[#141824] hover:bg-[#1a2133] border border-[#1f2638] text-slate-400 hover:text-slate-200"
            title="Relayout Graph"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Graph Canvas Container */}
      <div className="flex-1 w-full h-full relative">
        <div ref={containerRef} className="w-full h-full bg-[#08090d]" />

        {isLoading && (
          <div className="absolute inset-0 bg-[#08090d]/60 backdrop-blur-xs flex items-center justify-center font-mono text-xs text-sky-400">
            <div className="flex items-center space-x-2">
              <span className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></span>
              <span>Rendering topological evidence graph...</span>
            </div>
          </div>
        )}

        {/* Selected Node Quick Preview Overlay */}
        {selectedNodeData && (
          <div className="absolute bottom-4 left-4 z-20 max-w-sm w-full bg-[#0f121a]/95 backdrop-blur-md border border-[#2b354d] rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-bottom-2 duration-150">
            <div className="flex items-center justify-between border-b border-[#1f2638] pb-2 mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase" style={{ backgroundColor: `${selectedNodeData.color}20`, color: selectedNodeData.color }}>
                {selectedNodeData.type}
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                Confidence: {Math.round(selectedNodeData.confidence * 100)}%
              </span>
            </div>
            <p className="font-mono text-sm font-semibold text-slate-100 break-all mb-2">
              {selectedNodeData.full_value}
            </p>
            <div className="flex items-center justify-between pt-2 border-t border-[#1a2133]">
              <span className="text-[10px] font-mono text-slate-500">
                Tier: {selectedNodeData.provenance_label}
              </span>
              <button
                onClick={() => onInvestigateEntity(selectedNodeData.full_value)}
                className="px-2.5 py-1 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold font-mono text-[11px] transition-colors"
              >
                Investigate This →
              </button>
            </div>
          </div>
        )}

        {/* Selected Edge Explanation Overlay */}
        {selectedEdgeData && (
          <div className="absolute bottom-4 left-4 z-20 max-w-md w-full bg-[#0f121a]/95 backdrop-blur-md border border-sky-500/30 rounded-xl p-4 shadow-2xl animate-in fade-in slide-in-from-bottom-2 duration-150">
            <div className="flex items-center justify-between border-b border-[#1f2638] pb-2 mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-sky-500/10 text-sky-400 border border-sky-500/20">
                {selectedEdgeData.label}
              </span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold">
                {Math.round(selectedEdgeData.confidence * 100)}% Confidence
              </span>
            </div>
            <div className="space-y-2 mb-3">
              <div className="text-[11px] font-mono text-slate-400">
                <span className="text-slate-500">Discovery Method: </span>
                <span className="text-amber-400 font-semibold">{selectedEdgeData.discovery_method || "DIRECT_CORRELATION"}</span>
              </div>
              <p className="font-mono text-xs text-slate-200 bg-[#090b10] p-2.5 rounded-lg border border-[#1f2638]">
                {selectedEdgeData.explanation || "Deterministic connection established through observed infrastructure telemetry."}
              </p>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-[#1a2133] text-[10px] font-mono text-slate-500">
              <span>Backing Evidence: {selectedEdgeData.evidence_count || (selectedEdgeData.evidence_ids ? selectedEdgeData.evidence_ids.length : 0)} source records</span>
              <span className={selectedEdgeData.is_ai_inferred ? "text-indigo-400" : "text-emerald-400"}>
                {selectedEdgeData.is_ai_inferred ? "AI INFERRED" : "DETERMINISTIC"}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
