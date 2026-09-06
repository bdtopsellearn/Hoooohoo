import React, { useState } from 'react';
import { 
  BotRecord, 
  NodeRecord, 
  VaultSnapshot, 
  LogEntry, 
  PlatformConfig 
} from './types';
import { 
  INITIAL_CONFIG, 
  INITIAL_BOTS, 
  INITIAL_NODES, 
  INITIAL_SNAPSHOTS, 
  INITIAL_LOGS 
} from './data/initialData';
import { Navbar } from './components/Navbar';
import { BotFleetView } from './components/BotFleetView';
import { SecurityScannerView } from './components/SecurityScannerView';
import { NodesView } from './components/NodesView';
import { CipherVaultView } from './components/CipherVaultView';
import { ConfigView } from './components/ConfigView';
import { TerminalLogsView } from './components/TerminalLogsView';
import { DeployModal } from './components/DeployModal';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('bots');
  const [config, setConfig] = useState<PlatformConfig>(INITIAL_CONFIG);
  const [bots, setBots] = useState<BotRecord[]>(INITIAL_BOTS);
  const [nodes, setNodes] = useState<NodeRecord[]>(INITIAL_NODES);
  const [snapshots, setSnapshots] = useState<VaultSnapshot[]>(INITIAL_SNAPSHOTS);
  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);
  const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);
  const [isVaultSyncing, setIsVaultSyncing] = useState(false);

  // Append new log helper
  const addLog = (entry: LogEntry) => {
    setLogs((prev) => [entry, ...prev]);
  };

  // Bot actions
  const handleStartBot = (id: string) => {
    setBots((prev) =>
      prev.map((b) => {
        if (b.id === id) {
          const newPid = Math.floor(Math.random() * 80000) + 10000;
          return {
            ...b,
            status: 'running',
            pid: newPid,
            uptime: 'Just now',
            cpuPercent: +(Math.random() * 2 + 0.8).toFixed(1),
            memoryMb: 85.0
          };
        }
        return b;
      })
    );

    const target = bots.find((b) => b.id === id);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      category: 'SANDBOX',
      message: `Started container for bot "${target?.name || id}" in Docker sandbox mode`
    });
  };

  const handleStopBot = (id: string) => {
    setBots((prev) =>
      prev.map((b) =>
        b.id === id
          ? { ...b, status: 'stopped', cpuPercent: 0, memoryMb: 0, uptime: 'Offline' }
          : b
      )
    );

    const target = bots.find((b) => b.id === id);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'warn',
      category: 'SANDBOX',
      message: `Terminated process group PID ${target?.pid} for bot "${target?.name || id}"`
    });
  };

  const handleRestartBot = (id: string) => {
    setBots((prev) =>
      prev.map((b) => (b.id === id ? { ...b, status: 'restarting' } : b))
    );

    const target = bots.find((b) => b.id === id);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      category: 'SANDBOX',
      message: `Restart requested for bot "${target?.name || id}". Re-applying AST policy...`
    });

    setTimeout(() => {
      setBots((prev) =>
        prev.map((b) =>
          b.id === id
            ? {
                ...b,
                status: 'running',
                uptime: '0m',
                pid: Math.floor(Math.random() * 80000) + 10000,
                cpuPercent: 1.8,
                memoryMb: 92.4
              }
            : b
        )
      );

      addLog({
        id: `log_${Date.now() + 1}`,
        timestamp: new Date().toLocaleTimeString(),
        level: 'success',
        category: 'SANDBOX',
        message: `Bot "${target?.name || id}" restarted successfully.`
      });
    }, 800);
  };

  const handleDeleteBot = (id: string) => {
    const target = bots.find((b) => b.id === id);
    setBots((prev) => prev.filter((b) => b.id !== id));
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'warn',
      category: 'SYSTEM',
      message: `Bot "${target?.name || id}" uninstalled and storage purged.`
    });
  };

  const handleAddBot = (botData: Partial<BotRecord>) => {
    const newId = `bot_${Date.now().toString().slice(-4)}`;
    const newRecord: BotRecord = {
      id: newId,
      name: botData.name || 'New Custom Bot',
      script: botData.script || 'main.py',
      runtime: 'python3',
      status: 'running',
      nodeId: botData.nodeId || 'node_local',
      nodeName: botData.nodeName || 'Control Plane Local',
      uptime: 'Just now',
      cpuPercent: 1.2,
      memoryMb: 76.5,
      maxMemoryMb: botData.maxMemoryMb || 256,
      pid: Math.floor(Math.random() * 80000) + 10000,
      sandboxMode: 'docker',
      lastPing: '1s ago',
      telegramHandle: botData.telegramHandle,
      autoRestart: true
    };

    setBots((prev) => [newRecord, ...prev]);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      category: 'SANDBOX',
      message: `Deployed new bot "${newRecord.name}" on ${newRecord.nodeName} with cgroup isolation.`
    });
  };

  // Node actions
  const handleTestNode = (nodeId: string) => {
    const target = nodes.find((n) => n.id === nodeId);
    const newLatency = Math.floor(Math.random() * 15) + (nodeId === 'node_local' ? 1 : 24);
    
    setNodes((prev) =>
      prev.map((n) =>
        n.id === nodeId
          ? { ...n, latencyMs: newLatency, lastTested: 'Just now', status: 'ONLINE' }
          : n
      )
    );

    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      category: 'NODE',
      message: `SSH probe on "${target?.name || nodeId}": handshake OK, Docker daemon online, latency ${newLatency}ms.`
    });
  };

  const handleToggleNode = (nodeId: string) => {
    setNodes((prev) =>
      prev.map((n) =>
        n.id === nodeId ? { ...n, enabled: !n.enabled } : n
      )
    );
  };

  const handleDeleteNode = (nodeId: string) => {
    const target = nodes.find((n) => n.id === nodeId);
    setNodes((prev) => prev.filter((n) => n.id !== nodeId));
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      category: 'NODE',
      message: `Node "${target?.name || nodeId}" detached from worker fleet.`
    });
  };

  const handleAddNode = (nodeData: Partial<NodeRecord>) => {
    const newId = `node_vps_${Date.now().toString().slice(-4)}`;
    const newRecord: NodeRecord = {
      id: newId,
      name: nodeData.name || 'Remote VPS Node',
      provider: nodeData.provider || 'Custom VPS',
      connectionType: nodeData.connectionType || 'ssh',
      ipv4: nodeData.ipv4 || '127.0.0.1',
      sshPort: nodeData.sshPort || 22,
      username: nodeData.username || 'root',
      authMethod: 'key',
      enabled: true,
      status: 'AUTHENTICATED',
      dockerAvailable: true,
      activeBots: 0,
      latencyMs: nodeData.latencyMs || 32,
      osInfo: nodeData.osInfo || 'Ubuntu 24.04 LTS (systemd)',
      lastTested: 'Just now'
    };

    setNodes((prev) => [...prev, newRecord]);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      category: 'NODE',
      message: `Registered new node "${newRecord.name}" (${newRecord.ipv4}:${newRecord.sshPort}).`
    });
  };

  // Vault actions
  const handleTriggerBackup = () => {
    setIsVaultSyncing(true);
    const newCommit = Math.random().toString(16).substring(2, 12);
    const newSnapshot: VaultSnapshot = {
      id: `snap_${Date.now().toString().slice(-4)}`,
      commitHash: newCommit,
      branch: config.cipherVaultBranch,
      timestamp: 'Just now',
      sizeKb: +(Math.random() * 30 + 440).toFixed(1),
      encryptedWith: 'Fernet AES-128-CBC',
      sha256: Array.from({ length: 48 }, () => Math.floor(Math.random() * 16).toString(16)).join(''),
      status: 'synced',
      entriesCount: 86
    };

    setSnapshots((prev) => [newSnapshot, ...prev]);
    setIsVaultSyncing(false);

    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      category: 'VAULT',
      message: `Encrypted Cipher Vault snapshot committed -> ${config.cipherVaultRepo} (commit: ${newCommit})`
    });
  };

  // Config save
  const handleSaveConfig = (updated: PlatformConfig) => {
    setConfig(updated);
    addLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      category: 'SYSTEM',
      message: 'Platform configuration and webhook secret updated.'
    });
  };

  const runningBotsCount = bots.filter((b) => b.status === 'running').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-emerald-500/20 selection:text-emerald-300">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        config={config}
        onOpenDeployModal={() => setIsDeployModalOpen(true)}
        runningBotsCount={runningBotsCount}
        totalBotsCount={bots.length}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'bots' && (
          <BotFleetView
            bots={bots}
            nodes={nodes}
            onStartBot={handleStartBot}
            onStopBot={handleStopBot}
            onRestartBot={handleRestartBot}
            onDeleteBot={handleDeleteBot}
            onAddBot={handleAddBot}
          />
        )}

        {activeTab === 'scanner' && <SecurityScannerView />}

        {activeTab === 'nodes' && (
          <NodesView
            nodes={nodes}
            onTestNode={handleTestNode}
            onToggleNode={handleToggleNode}
            onDeleteNode={handleDeleteNode}
            onAddNode={handleAddNode}
          />
        )}

        {activeTab === 'vault' && (
          <CipherVaultView
            config={config}
            snapshots={snapshots}
            onTriggerBackup={handleTriggerBackup}
            isSyncing={isVaultSyncing}
          />
        )}

        {activeTab === 'config' && (
          <ConfigView config={config} onSaveConfig={handleSaveConfig} />
        )}

        {activeTab === 'logs' && (
          <TerminalLogsView
            logs={logs}
            onClearLogs={() => setLogs([])}
            onAddLog={addLog}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs font-mono text-slate-500">
          <div>
            <span className="text-slate-400 font-semibold">{config.brandName}</span> • Control-Plane v2.4 (Port {config.port})
          </div>
          <div className="flex items-center space-x-3">
            <span>Owner: <span className="text-slate-400">{config.adminHandle}</span></span>
            <span>•</span>
            <span className="text-emerald-500">All Nodes Connected</span>
          </div>
        </div>
      </footer>

      {/* Deploy Instructions Modal */}
      <DeployModal
        isOpen={isDeployModalOpen}
        onClose={() => setIsDeployModalOpen(false)}
      />
    </div>
  );
}
