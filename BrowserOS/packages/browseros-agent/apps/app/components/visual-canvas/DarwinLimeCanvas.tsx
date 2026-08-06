import React, { useState } from 'react';

export type CanvasMode = 'mindmap' | 'knowledge-graph' | 'quadrants';

export interface MindMapNode {
  id: string;
  label: string;
  category?: string;
  children?: MindMapNode[];
  expanded?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  group: string;
  x: number;
  y: number;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export interface QuadrantItem {
  id: string;
  title: string;
  description: string;
  quadrant: 'Q1' | 'Q2' | 'Q3' | 'Q4';
}

const initialMindMap: MindMapNode = {
  id: 'root',
  label: 'DARWIN Sovereign Engine',
  expanded: true,
  children: [
    {
      id: 'core-ai',
      label: 'Core AI Router (C++)',
      category: 'Backend',
      expanded: true,
      children: [
        { id: 'mcp-server', label: 'MCP Protocol Daemon' },
        { id: 'telemetry', label: 'Objective-C++ Telemetry' }
      ]
    },
    {
      id: 'knowledge',
      label: 'TerminusDB Graph',
      category: 'Memory',
      expanded: true,
      children: [
        { id: 'akan-ontology', label: 'Akan Ontology Engine' },
        { id: 'triples', label: 'Triple Store' }
      ]
    },
    {
      id: 'standalone-app',
      label: 'Desktop App Engine',
      category: 'UI/UX',
      expanded: true,
      children: [
        { id: 'meta-ocr', label: 'Meta-OCR Menu Bar' },
        { id: 'lime-canvas', label: 'Lime-Green Mind Canvas' }
      ]
    }
  ]
};

const initialGraphNodes: GraphNode[] = [
  { id: '1', label: 'DARWIN Core', group: 'Engine', x: 250, y: 180 },
  { id: '2', label: 'TerminusDB', group: 'Database', x: 100, y: 80 },
  { id: '3', label: 'Akan Ontology', group: 'Memory', x: 400, y: 80 },
  { id: '4', label: 'C++ AI Router', group: 'Compute', x: 100, y: 280 },
  { id: '5', label: 'Meta-OCR', group: 'Vision', x: 400, y: 280 },
  { id: '6', label: 'Lime Canvas', group: 'UX', x: 250, y: 350 },
];

const initialGraphLinks: GraphLink[] = [
  { source: '1', target: '2', label: 'Persists Knowledge' },
  { source: '1', target: '3', label: 'Executes Rules' },
  { source: '1', target: '4', label: 'Routes Prompts' },
  { source: '1', target: '5', label: 'Captures Context' },
  { source: '1', target: '6', label: 'Renders Visuals' },
  { source: '2', target: '3', label: 'Stores Triples' },
];

const initialQuadrants: QuadrantItem[] = [
  { id: 'q1-1', title: 'Compile Chromium Binary', description: 'GitHub Actions macos-14 cloud builder', quadrant: 'Q1' },
  { id: 'q1-2', title: 'Initialize TerminusDB', description: 'Spin up graph database container on 6363', quadrant: 'Q1' },
  { id: 'q2-1', title: 'Lime Green Canvas', description: 'Interactive Mind Map & Quadrants view', quadrant: 'Q2' },
  { id: 'q2-2', title: 'Meta-OCR Menu Bar', description: 'Continuous screen comprehension engine', quadrant: 'Q2' },
  { id: 'q3-1', title: 'Telemetry Metrics', description: 'Log C++ router frame execution rates', quadrant: 'Q3' },
  { id: 'q4-1', title: 'Legacy Dependencies', description: 'Deprecate old browser wrappers', quadrant: 'Q4' },
];

export const DarwinLimeCanvas: React.FC = () => {
  const [activeTab, setActiveTab] = useState<CanvasMode>('mindmap');
  const [mindMapData, setMindMapData] = useState<MindMapNode>(initialMindMap);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const toggleNode = (nodeId: string, node: MindMapNode): MindMapNode => {
    if (node.id === nodeId) {
      return { ...node, expanded: !node.expanded };
    }
    if (node.children) {
      return {
        ...node,
        children: node.children.map(child => toggleNode(nodeId, child))
      };
    }
    return node;
  };

  const handleMindMapClick = (id: string) => {
    setSelectedNode(id);
    setMindMapData(prev => toggleNode(id, prev));
  };

  return (
    <div className="w-full h-full min-h-[650px] bg-[#0a0f0d] text-[#e0ffe8] p-6 rounded-2xl border border-[#00ff66]/30 shadow-[0_0_30px_rgba(0,255,102,0.15)] flex flex-col font-sans">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-[#00ff66]/20">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full bg-[#00ff66] shadow-[0_0_12px_#00ff66] animate-pulse" />
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            DARWIN <span className="text-[#00ff66] drop-shadow-[0_0_8px_#00ff66]">Lime Visual Studio</span>
          </h2>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center bg-[#111c16] p-1.5 rounded-xl border border-[#00ff66]/30">
          <button
            onClick={() => setActiveTab('mindmap')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === 'mindmap'
                ? 'bg-[#00ff66] text-[#051c0c] shadow-[0_0_15px_rgba(0,255,102,0.5)] font-bold'
                : 'text-[#a0e8b5] hover:text-white hover:bg-[#1a2d22]'
            }`}
          >
            🧠 Lime Mind Map
          </button>
          <button
            onClick={() => setActiveTab('knowledge-graph')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === 'knowledge-graph'
                ? 'bg-[#00ff66] text-[#051c0c] shadow-[0_0_15px_rgba(0,255,102,0.5)] font-bold'
                : 'text-[#a0e8b5] hover:text-white hover:bg-[#1a2d22]'
            }`}
          >
            🕸️ Knowledge Graph
          </button>
          <button
            onClick={() => setActiveTab('quadrants')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === 'quadrants'
                ? 'bg-[#00ff66] text-[#051c0c] shadow-[0_0_15px_rgba(0,255,102,0.5)] font-bold'
                : 'text-[#a0e8b5] hover:text-white hover:bg-[#1a2d22]'
            }`}
          >
            📊 2x2 Quadrant Studio
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="flex-1 mt-6 relative overflow-hidden bg-[#050a07] rounded-xl border border-[#00ff66]/15 p-6 flex flex-col justify-center">
        {/* View 1: Mind Map */}
        {activeTab === 'mindmap' && (
          <div className="w-full h-full flex flex-col items-center justify-center overflow-auto">
            <div className="text-center mb-4">
              <span className="text-xs uppercase tracking-widest text-[#00ff66] font-mono bg-[#00ff66]/10 px-3 py-1 rounded-full border border-[#00ff66]/30">
                Interactive Hierarchical Node Explorer
              </span>
            </div>
            
            <div className="flex flex-col items-center gap-6 my-auto">
              {/* Render Root */}
              <div 
                onClick={() => handleMindMapClick(mindMapData.id)}
                className={`cursor-pointer px-6 py-3.5 rounded-xl border-2 bg-[#0c1a12] font-bold text-lg text-white shadow-[0_0_20px_rgba(0,255,102,0.3)] transition-all transform hover:scale-105 ${
                  selectedNode === mindMapData.id ? 'border-[#00ff66] shadow-[0_0_30px_#00ff66]' : 'border-[#00ff66]/60'
                }`}
              >
                🌿 {mindMapData.label}
              </div>

              {/* Children Connector */}
              {mindMapData.expanded && mindMapData.children && (
                <div className="flex flex-wrap justify-center gap-8 relative pt-6 border-t-2 border-[#00ff66]/40">
                  {mindMapData.children.map((child) => (
                    <div key={child.id} className="flex flex-col items-center gap-4">
                      <div 
                        onClick={() => handleMindMapClick(child.id)}
                        className={`cursor-pointer px-5 py-2.5 rounded-lg border bg-[#11241a] font-semibold text-sm text-[#00ff66] shadow-[0_0_12px_rgba(0,255,102,0.2)] hover:bg-[#1a3325] transition-all transform hover:scale-105 ${
                          selectedNode === child.id ? 'border-[#00ff66] bg-[#1a3d2b] shadow-[0_0_20px_#00ff66]' : 'border-[#00ff66]/40'
                        }`}
                      >
                        ⚡ {child.label}
                      </div>

                      {child.expanded && child.children && (
                        <div className="flex flex-col gap-2 pl-4 border-l-2 border-[#00ff66]/30">
                          {child.children.map((subChild) => (
                            <div
                              key={subChild.id}
                              onClick={() => handleMindMapClick(subChild.id)}
                              className="cursor-pointer px-3.5 py-1.5 rounded-md bg-[#0a150f] border border-[#00ff66]/20 text-xs text-[#a0ffd0] hover:text-white hover:border-[#00ff66] transition-all"
                            >
                              • {subChild.label}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* View 2: Knowledge Graph */}
        {activeTab === 'knowledge-graph' && (
          <div className="w-full h-full flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs uppercase tracking-widest text-[#00ff66] font-mono bg-[#00ff66]/10 px-3 py-1 rounded-full border border-[#00ff66]/30">
                TerminusDB Semantic Triples & Entity Network
              </span>
              <span className="text-xs text-[#70c090]">6 Nodes · 6 Active Edges</span>
            </div>

            <svg className="w-full h-[400px] rounded-lg border border-[#00ff66]/20 bg-[#08120c]">
              {/* Lines */}
              {initialGraphLinks.map((link, idx) => {
                const sNode = initialGraphNodes.find(n => n.id === link.source);
                const tNode = initialGraphNodes.find(n => n.id === link.target);
                if (!sNode || !tNode) return null;
                return (
                  <g key={idx}>
                    <line
                      x1={sNode.x}
                      y1={sNode.y}
                      x2={tNode.x}
                      y2={tNode.y}
                      stroke="#00ff66"
                      strokeWidth="2"
                      strokeOpacity="0.5"
                      strokeDasharray="4 2"
                    />
                    <text
                      x={(sNode.x + tNode.x) / 2}
                      y={(sNode.y + tNode.y) / 2 - 6}
                      fill="#80e0a0"
                      fontSize="10"
                      textAnchor="middle"
                    >
                      {link.label}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {initialGraphNodes.map((node) => (
                <g key={node.id} transform={`translate(${node.x}, ${node.y})`} className="cursor-pointer">
                  <circle
                    r="22"
                    fill="#0e2417"
                    stroke="#00ff66"
                    strokeWidth="2"
                    className="hover:scale-125 transition-transform"
                    style={{ filter: 'drop-shadow(0px 0px 8px #00ff66)' }}
                  />
                  <text
                    y="4"
                    fill="#ffffff"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    {node.label.slice(0, 8)}
                  </text>
                  <text
                    y="36"
                    fill="#00ff66"
                    fontSize="10"
                    textAnchor="middle"
                    fontWeight="600"
                  >
                    {node.label}
                  </text>
                </g>
              ))}
            </svg>
          </div>
        )}

        {/* View 3: 2x2 Quadrant Studio */}
        {activeTab === 'quadrants' && (
          <div className="w-full h-full flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-widest text-[#00ff66] font-mono bg-[#00ff66]/10 px-3 py-1 rounded-full border border-[#00ff66]/30">
                Strategic 2x2 Matrix & Decision Framework
              </span>
            </div>

            <div className="grid grid-cols-2 grid-rows-2 gap-4 flex-1 min-h-[380px]">
              {/* Q1: High Impact / Urgent */}
              <div className="bg-[#102016] p-4 rounded-xl border border-[#00ff66]/50 shadow-[0_0_15px_rgba(0,255,102,0.15)] flex flex-col gap-2">
                <div className="flex items-center justify-between border-b border-[#00ff66]/30 pb-2">
                  <h4 className="font-bold text-[#00ff66] text-sm tracking-wide">Q1: DO NOW (High Impact / Urgent)</h4>
                  <span className="text-xs bg-[#00ff66] text-[#051c0c] px-2 py-0.5 rounded font-bold">Top Priority</span>
                </div>
                <div className="flex flex-col gap-2 mt-1">
                  {initialQuadrants.filter(i => i.quadrant === 'Q1').map(item => (
                    <div key={item.id} className="bg-[#09140d] p-3 rounded-lg border border-[#00ff66]/30">
                      <div className="font-semibold text-white text-sm">{item.title}</div>
                      <div className="text-xs text-[#90d8a5] mt-0.5">{item.description}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Q2: High Impact / Long Term */}
              <div className="bg-[#0b1c13] p-4 rounded-xl border border-[#00ff66]/30 flex flex-col gap-2">
                <div className="flex items-center justify-between border-b border-[#00ff66]/20 pb-2">
                  <h4 className="font-bold text-[#80ffb0] text-sm tracking-wide">Q2: SCHEDULE (High Impact / Strategic)</h4>
                  <span className="text-xs bg-[#00ff66]/20 text-[#00ff66] px-2 py-0.5 rounded font-semibold">Strategic</span>
                </div>
                <div className="flex flex-col gap-2 mt-1">
                  {initialQuadrants.filter(i => i.quadrant === 'Q2').map(item => (
                    <div key={item.id} className="bg-[#09140d] p-3 rounded-lg border border-[#00ff66]/20">
                      <div className="font-semibold text-white text-sm">{item.title}</div>
                      <div className="text-xs text-[#80c895] mt-0.5">{item.description}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Q3: Low Impact / Urgent */}
              <div className="bg-[#0b1c13] p-4 rounded-xl border border-[#00ff66]/20 flex flex-col gap-2">
                <div className="flex items-center justify-between border-b border-[#00ff66]/20 pb-2">
                  <h4 className="font-bold text-[#70a884] text-sm tracking-wide">Q3: DELEGATE (Low Impact / Urgent)</h4>
                  <span className="text-xs bg-[#1a3325] text-[#70d895] px-2 py-0.5 rounded">Operational</span>
                </div>
                <div className="flex flex-col gap-2 mt-1">
                  {initialQuadrants.filter(i => i.quadrant === 'Q3').map(item => (
                    <div key={item.id} className="bg-[#09140d] p-3 rounded-lg border border-[#00ff66]/15">
                      <div className="font-semibold text-[#d0ffd8] text-sm">{item.title}</div>
                      <div className="text-xs text-[#70a884] mt-0.5">{item.description}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Q4: Low Impact / Not Urgent */}
              <div className="bg-[#08140d] p-4 rounded-xl border border-[#00ff66]/10 flex flex-col gap-2">
                <div className="flex items-center justify-between border-b border-[#00ff66]/10 pb-2">
                  <h4 className="font-bold text-[#508864] text-sm tracking-wide">Q4: ELIMINATE (Low Impact / Low Urgency)</h4>
                  <span className="text-xs bg-[#102418] text-[#50a874] px-2 py-0.5 rounded">Low Priority</span>
                </div>
                <div className="flex flex-col gap-2 mt-1">
                  {initialQuadrants.filter(i => i.quadrant === 'Q4').map(item => (
                    <div key={item.id} className="bg-[#060d09] p-3 rounded-lg border border-[#00ff66]/10">
                      <div className="font-semibold text-[#a0c8b0] text-sm">{item.title}</div>
                      <div className="text-xs text-[#508864] mt-0.5">{item.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DarwinLimeCanvas;
