import React, { useState } from 'react';
import { 
  Play, 
  Square, 
  RotateCw, 
  Plus, 
  Cpu, 
  HardDrive, 
  Box, 
  CheckCircle2, 
  AlertCircle, 
  Search,
  ExternalLink,
  Shield,
  Trash2
} from 'lucide-react';
import { BotRecord, NodeRecord } from '../types';

interface BotFleetViewProps {
  bots: BotRecord[];
  nodes: NodeRecord[];
  onStartBot: (id: string) => void;
  onStopBot: (id: string) => void;
  onRestartBot: (id: string) => void;
  onDeleteBot: (id: string) => void;
  onAddBot: (bot: Partial<BotRecord>) => void;
}

export const BotFleetView: React.FC<BotFleetViewProps> = ({
  bots,
  nodes,
  onStartBot,
  onStopBot,
  onRestartBot,
  onDeleteBot,
  onAddBot
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);

  // New Bot Form State
  const [newBotName, setNewBotName] = useState('');
  const [newBotScript, setNewBotScript] = useState('main.py');
  const [newBotHandle, setNewBotHandle] = useState('');
  const [newBotNode, setNewBotNode] = useState(nodes[0]?.id || 'node_local');
  const [newBotMaxMem, setNewBotMaxMem] = useState(256);

  const filteredBots = bots.filter(bot => {
    const matchesSearch = bot.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          bot.script.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (bot.telegramHandle && bot.telegramHandle.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || bot.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const runningCount = bots.filter(b => b.status === 'running').length;
  const totalMemoryUsed = bots.reduce((acc, b) => acc + (b.status === 'running' ? b.memoryMb : 0), 0);
  const avgCpu = runningCount > 0 
    ? (bots.reduce((acc, b) => acc + (b.status === 'running' ? b.cpuPercent : 0), 0) / runningCount).toFixed(1)
    : '0.0';

  const handleCreateBot = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBotName.trim()) return;

    const selectedNodeObj = nodes.find(n => n.id === newBotNode);
    onAddBot({
      name: newBotName.trim(),
      script: newBotScript.trim(),
      telegramHandle: newBotHandle.trim() ? (newBotHandle.startsWith('@') ? newBotHandle : `@${newBotHandle}`) : undefined,
      nodeId: newBotNode,
      nodeName: selectedNodeObj?.name || 'Local Host',
      maxMemoryMb: Number(newBotMaxMem),
      runtime: 'python3',
      sandboxMode: 'docker',
      autoRestart: true
    });

    setNewBotName('');
    setNewBotScript('main.py');
    setNewBotHandle('');
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Telemetry Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Fleet Health</span>
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-white">{runningCount} / {bots.length}</span>
            <span className="text-xs text-emerald-400 font-mono">Running</span>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Memory Allocation</span>
            <HardDrive className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-white">{totalMemoryUsed.toFixed(1)} MB</span>
            <span className="text-xs text-slate-400 font-mono">Pooled</span>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Avg CPU Utilization</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-white">{avgCpu}%</span>
            <span className="text-xs text-slate-400 font-mono">Real-Time</span>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Sandbox Isolation</span>
            <Shield className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-emerald-400">100%</span>
            <span className="text-xs text-slate-400 font-mono">Docker/cgroups</span>
          </div>
        </div>
      </div>

      {/* Action Bar & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
        <div className="flex items-center space-x-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by bot name, script or handle..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="all">All States ({bots.length})</option>
            <option value="running">Running Only ({runningCount})</option>
            <option value="stopped">Stopped Only ({bots.length - runningCount})</option>
          </select>

          <button
            id="open-add-bot-modal-btn"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-semibold rounded-lg shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5 mr-1 stroke-[3]" />
            Deploy Bot
          </button>
        </div>
      </div>

      {/* Bots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredBots.map((bot) => {
          const isRunning = bot.status === 'running';
          const memUsagePercent = Math.round((bot.memoryMb / bot.maxMemoryMb) * 100);

          return (
            <div
              key={bot.id}
              id={`bot-card-${bot.id}`}
              className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition-all shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-semibold text-white tracking-tight">{bot.name}</h3>
                    {isRunning ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        RUNNING
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-800 text-slate-400 border border-slate-700">
                        STOPPED
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 mt-1">
                    {bot.telegramHandle && (
                      <span className="text-xs font-mono text-emerald-400 flex items-center">
                        {bot.telegramHandle}
                      </span>
                    )}
                    <span className="text-xs font-mono text-slate-500">PID: {bot.pid || '—'}</span>
                    <span className="text-xs font-mono text-slate-500">•</span>
                    <span className="text-xs font-mono text-slate-400">{bot.script}</span>
                  </div>
                </div>

                {/* Power Controls */}
                <div className="flex items-center space-x-1.5">
                  {isRunning ? (
                    <>
                      <button
                        title="Restart Bot Container"
                        onClick={() => onRestartBot(bot.id)}
                        className="p-1.5 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        <RotateCw className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="Stop Bot"
                        onClick={() => onStopBot(bot.id)}
                        className="p-1.5 rounded-md bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 transition-colors"
                      >
                        <Square className="w-3.5 h-3.5" />
                      </button>
                    </>
                  ) : (
                    <button
                      title="Start Bot"
                      onClick={() => onStartBot(bot.id)}
                      className="p-1.5 rounded-md bg-emerald-500 text-slate-950 hover:bg-emerald-400 font-bold transition-colors"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                  )}
                  <button
                    title="Delete Bot"
                    onClick={() => onDeleteBot(bot.id)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Resource Consumption Telemetry */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2.5">
                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-slate-400 flex items-center">
                      <Cpu className="w-3 h-3 mr-1 text-slate-500" /> CPU
                    </span>
                    <span className="text-slate-200">{bot.cpuPercent}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        bot.cpuPercent > 50 ? 'bg-amber-400' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, bot.cpuPercent * 10)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-slate-400 flex items-center">
                      <HardDrive className="w-3 h-3 mr-1 text-slate-500" /> Memory
                    </span>
                    <span className="text-slate-200">
                      {bot.memoryMb} MB / {bot.maxMemoryMb} MB ({memUsagePercent}%)
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        memUsagePercent > 80 ? 'bg-rose-500' : 'bg-cyan-500'
                      }`}
                      style={{ width: `${memUsagePercent}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Node & Sandbox Metadata Footer */}
              <div className="mt-4 flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
                <div className="flex items-center space-x-1.5">
                  <Box className="w-3 h-3 text-indigo-400" />
                  <span className="text-slate-300">{bot.nodeName}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                    {bot.sandboxMode === 'docker' ? 'Docker Sandbox' : 'cgroup Sandbox'}
                  </span>
                  <span>Uptime: {bot.uptime}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Deploy Bot Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center">
                <Box className="w-4 h-4 mr-2 text-emerald-400" />
                Deploy New Bot to Fleet
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                ✕ Close
              </button>
            </div>

            <form onSubmit={handleCreateBot} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Bot Service Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. VIP Subscription Handler"
                  value={newBotName}
                  onChange={(e) => setNewBotName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Entry Script</label>
                  <input
                    type="text"
                    required
                    placeholder="bot.py"
                    value={newBotScript}
                    onChange={(e) => setNewBotScript(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Telegram Handle (Optional)</label>
                  <input
                    type="text"
                    placeholder="@MyBot"
                    value={newBotHandle}
                    onChange={(e) => setNewBotHandle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Target Infrastructure Node</label>
                  <select
                    value={newBotNode}
                    onChange={(e) => setNewBotNode(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    {nodes.map(n => (
                      <option key={n.id} value={n.id} disabled={n.status !== 'ONLINE'}>
                        {n.name} ({n.status})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">RAM Limit (MB)</label>
                  <input
                    type="number"
                    min="64"
                    max="4096"
                    step="64"
                    value={newBotMaxMem}
                    onChange={(e) => setNewBotMaxMem(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-400 space-y-1">
                <div className="text-slate-300 font-medium">🛡️ Preflight Sandbox Policy:</div>
                <p>Bot will automatically undergo AST and regex scanning before the Docker daemon assigns a container PID.</p>
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
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  Deploy & Initialize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
