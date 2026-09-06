import React, { useState } from 'react';
import { 
  Terminal, 
  Trash2, 
  Copy, 
  Check, 
  Filter, 
  PlayCircle
} from 'lucide-react';
import { LogEntry } from '../types';

interface TerminalLogsViewProps {
  logs: LogEntry[];
  onClearLogs: () => void;
  onAddLog: (entry: LogEntry) => void;
}

export const TerminalLogsView: React.FC<TerminalLogsViewProps> = ({
  logs,
  onClearLogs,
  onAddLog
}) => {
  const [filter, setFilter] = useState<string>('ALL');
  const [copied, setCopied] = useState(false);

  const filteredLogs = logs.filter(
    (l) => filter === 'ALL' || l.category === filter
  );

  const handleCopyLogs = () => {
    const text = filteredLogs.map((l) => `[${l.timestamp}] [${l.category}] [${l.level.toUpperCase()}]: ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleInjectPing = () => {
    onAddLog({
      id: `log_${Date.now()}`,
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      category: 'NODE',
      message: 'Heartbeat echo received: Control-plane -> Node-01 (Round-trip 1.2ms, Docker daemon OK)'
    });
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
            Audit & Execution Telemetry
          </span>
          <span className="text-xs font-mono text-slate-500">
            ({filteredLogs.length} events)
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-mono">
            {['ALL', 'SYSTEM', 'SECURITY', 'VAULT', 'NODE', 'SANDBOX'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  filter === cat
                    ? 'bg-emerald-500/20 text-emerald-300 font-semibold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <button
            onClick={handleInjectPing}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Ping Host"
          >
            <PlayCircle className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleCopyLogs}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title="Copy Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={onClearLogs}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-rose-400 hover:bg-slate-700 transition-colors"
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal Window */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs shadow-2xl h-[520px] overflow-y-auto scrollbar-thin">
        {filteredLogs.length === 0 ? (
          <div className="text-center py-20 text-slate-600">
            No events recorded under category: {filter}
          </div>
        ) : (
          <div className="space-y-1.5">
            {filteredLogs.map((log) => {
              let color = 'text-slate-300';
              if (log.level === 'success') color = 'text-emerald-400';
              if (log.level === 'warn') color = 'text-amber-400';
              if (log.level === 'error') color = 'text-rose-400';
              if (log.level === 'info') color = 'text-sky-300';

              return (
                <div key={log.id} className="flex items-start space-x-2.5 hover:bg-slate-900/40 py-0.5 px-1 rounded transition-colors">
                  <span className="text-slate-500 select-none text-[11px] shrink-0">
                    [{log.timestamp}]
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-900 text-slate-400 border border-slate-800 select-none shrink-0">
                    {log.category}
                  </span>
                  <span className={`${color} leading-relaxed break-all`}>
                    {log.message}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
