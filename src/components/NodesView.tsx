import React, { useState } from 'react';
import { 
  Server, 
  Cpu, 
  Terminal, 
  Plus, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Globe, 
  Key, 
  Box,
  Radio,
  Trash2
} from 'lucide-react';
import { NodeRecord } from '../types';

interface NodesViewProps {
  nodes: NodeRecord[];
  onTestNode: (id: string) => void;
  onToggleNode: (id: string) => void;
  onDeleteNode: (id: string) => void;
  onAddNode: (node: Partial<NodeRecord>) => void;
}

export const NodesView: React.FC<NodesViewProps> = ({
  nodes,
  onTestNode,
  onToggleNode,
  onDeleteNode,
  onAddNode
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);

  // New Node Form
  const [nodeName, setNodeName] = useState('');
  const [nodeProvider, setNodeProvider] = useState('Hetzner Cloud');
  const [connectionType, setConnectionType] = useState<'local' | 'ssh' | 'agent'>('ssh');
  const [ipv4, setIpv4] = useState('');
  const [sshPort, setSshPort] = useState(22);
  const [username, setUsername] = useState('root');

  const handleTest = (id: string) => {
    setTestingId(id);
    setTimeout(() => {
      onTestNode(id);
      setTestingId(null);
    }, 600);
  };

  const handleCreateNode = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nodeName.trim()) return;

    onAddNode({
      name: nodeName.trim(),
      provider: nodeProvider,
      connectionType,
      ipv4: ipv4.trim() || '127.0.0.1',
      sshPort: Number(sshPort),
      username: username.trim(),
      authMethod: 'key',
      enabled: true,
      status: 'AUTHENTICATED',
      dockerAvailable: true,
      activeBots: 0,
      latencyMs: Math.floor(Math.random() * 35) + 15,
      osInfo: 'Ubuntu 24.04 LTS (systemd)',
      lastTested: 'Just now'
    });

    setNodeName('');
    setIpv4('');
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Infrastructure Summary Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Server className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Infrastructure & Remote Worker Fleet
              </h2>
              <p className="text-xs text-slate-400">
                Safe node discovery and isolation boundary based on <span className="font-mono text-slate-300">node_manager.py</span>.
              </p>
            </div>
          </div>

          <button
            id="register-node-btn"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-lg shadow-sm transition-colors self-start sm:self-auto"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5 stroke-[3]" />
            Register VPS Worker Node
          </button>
        </div>
      </div>

      {/* Nodes Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {nodes.map((node) => {
          const isOnline = node.status === 'ONLINE' || node.status === 'AUTHENTICATED';

          return (
            <div
              key={node.id}
              id={`node-card-${node.id}`}
              className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition-all shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-semibold text-white">{node.name}</h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${
                          isOnline
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        }`}
                      >
                        {node.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{node.provider}</p>
                  </div>

                  <button
                    onClick={() => onToggleNode(node.id)}
                    className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      node.enabled ? 'bg-emerald-500' : 'bg-slate-700'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        node.enabled ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                {/* Node Details */}
                <div className="mt-4 space-y-2 text-xs font-mono">
                  <div className="flex justify-between text-slate-400">
                    <span>Connection:</span>
                    <span className="text-slate-200 uppercase">{node.connectionType}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>IP / Endpoint:</span>
                    <span className="text-slate-200">{node.ipv4}:{node.sshPort}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>OS Platform:</span>
                    <span className="text-slate-300 truncate max-w-[150px]">{node.osInfo}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Docker Daemon:</span>
                    <span className={node.dockerAvailable ? 'text-emerald-400 font-semibold' : 'text-amber-400'}>
                      {node.dockerAvailable ? '✓ Available' : '⚠ Missing (Needs Setup)'}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Latency:</span>
                    <span className="text-slate-200">{node.latencyMs} ms</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Active Containers:</span>
                    <span className="text-emerald-400 font-bold">{node.activeBots}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                <button
                  onClick={() => handleTest(node.id)}
                  disabled={testingId === node.id}
                  className="inline-flex items-center px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
                >
                  <RefreshCw className={`w-3 h-3 mr-1.5 ${testingId === node.id ? 'animate-spin text-emerald-400' : ''}`} />
                  Test Handshake
                </button>

                {node.connectionType !== 'local' && (
                  <button
                    onClick={() => onDeleteNode(node.id)}
                    className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                    title="Remove Node"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Node Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center">
                <Server className="w-4 h-4 mr-2 text-indigo-400" />
                Register Remote VPS Worker
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleCreateNode} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Node Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. VPS-Frankfurt-Worker-02"
                  value={nodeName}
                  onChange={(e) => setNodeName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Provider</label>
                  <select
                    value={nodeProvider}
                    onChange={(e) => setNodeProvider(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Hetzner Cloud">Hetzner Cloud</option>
                    <option value="DigitalOcean">DigitalOcean</option>
                    <option value="AWS EC2">AWS EC2</option>
                    <option value="OVHcloud">OVHcloud</option>
                    <option value="Custom VPS">Custom VPS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Protocol</label>
                  <select
                    value={connectionType}
                    onChange={(e) => setConnectionType(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="ssh">SSH (Port 22)</option>
                    <option value="agent">Agent REST Protocol</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-300 mb-1">IPv4 Address / Hostname</label>
                  <input
                    type="text"
                    required
                    placeholder="159.69.100.20"
                    value={ipv4}
                    onChange={(e) => setIpv4(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">SSH Port</label>
                  <input
                    type="number"
                    value={sshPort}
                    onChange={(e) => setSshPort(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">SSH Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="bg-slate-950 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-400 space-y-1">
                <div className="text-slate-300 font-medium flex items-center">
                  <Key className="w-3 h-3 mr-1 text-emerald-400" />
                  Keyring Security:
                </div>
                <p>Node credentials are encrypted with the platform Fernet key before persisting into <span className="font-mono text-slate-300">CredentialStore</span>.</p>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  Save & Authenticate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
