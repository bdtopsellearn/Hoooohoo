import React, { useState } from 'react';
import { 
  Lock, 
  ShieldCheck, 
  GitBranch, 
  GitCommit, 
  Download, 
  RefreshCw, 
  FileArchive, 
  Key, 
  CheckCircle2, 
  HardDrive
} from 'lucide-react';
import { VaultSnapshot, PlatformConfig } from '../types';

interface CipherVaultViewProps {
  config: PlatformConfig;
  snapshots: VaultSnapshot[];
  onTriggerBackup: () => void;
  isSyncing: boolean;
}

export const CipherVaultView: React.FC<CipherVaultViewProps> = ({
  config,
  snapshots,
  onTriggerBackup,
  isSyncing
}) => {
  const [showKey, setShowKey] = useState(false);
  const [syncStep, setSyncStep] = useState<string | null>(null);

  const handleSyncClick = () => {
    setSyncStep('Collecting state directories (storage, sandbox)...');
    setTimeout(() => {
      setSyncStep('Compressing tar.gz archive...');
      setTimeout(() => {
        setSyncStep('Encrypting with Fernet AES-128-CBC...');
        setTimeout(() => {
          setSyncStep('Creating Git Blobs -> Tree -> Commit -> Ref update...');
          setTimeout(() => {
            onTriggerBackup();
            setSyncStep(null);
          }, 600);
        }, 600);
      }, 500);
    }, 500);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Lock className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Encrypted Cipher Vault Engine
              </h2>
              <p className="text-xs text-slate-400">
                End-to-end Fernet encryption synced to GitHub via <span className="font-mono text-slate-300">vault_sync.py</span> Git Data API.
              </p>
            </div>
          </div>

          <button
            id="trigger-vault-sync-btn"
            onClick={handleSyncClick}
            disabled={isSyncing || syncStep !== null}
            className="inline-flex items-center px-4 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 text-xs font-bold font-mono rounded-lg shadow-sm transition-all self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isSyncing || syncStep ? 'animate-spin' : ''}`} />
            {syncStep ? 'Processing Pipeline...' : 'Trigger Encrypted Snapshot'}
          </button>
        </div>

        {/* Sync Progress Pipeline Indicator */}
        {syncStep && (
          <div className="mt-4 p-3 bg-slate-950 border border-emerald-500/30 rounded-lg flex items-center space-x-3">
            <div className="h-4 w-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
            <div className="text-xs font-mono text-emerald-300 animate-pulse">
              {syncStep}
            </div>
          </div>
        )}
      </div>

      {/* Target Repo & Key Specs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
            <GitBranch className="w-4 h-4 mr-1.5 text-emerald-400" />
            Remote Vault Repository
          </h3>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>GitHub Target:</span>
              <span className="text-emerald-400 font-semibold">{config.cipherVaultRepo}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Branch Reference:</span>
              <span className="text-slate-200">{config.cipherVaultBranch}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>State Scope:</span>
              <span className="text-slate-200">/storage, /sandbox (Clean excludes)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Atomic Mode:</span>
              <span className="text-emerald-400">Git Data API (Blobs -&gt; Tree -&gt; Commit)</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
              <Key className="w-4 h-4 mr-1.5 text-indigo-400" />
              Fernet Encryption Keyring
            </h3>
            <button
              onClick={() => setShowKey(!showKey)}
              className="text-[11px] font-mono text-emerald-400 hover:text-emerald-300"
            >
              {showKey ? 'Mask Key' : 'Reveal Key'}
            </button>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Cipher:</span>
              <span className="text-slate-200">AES-128-CBC + HMAC-SHA256</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Key Signature:</span>
              <span className="text-slate-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 truncate max-w-[220px]">
                {showKey ? config.cipherVaultKey : '••••••••••••••••••••••••••••••••••••••••'}
              </span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Key Status:</span>
              <span className="text-emerald-400 font-semibold">✓ Verified Active Key</span>
            </div>
          </div>
        </div>
      </div>

      {/* Snapshots History Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
            <FileArchive className="w-4 h-4 mr-1.5 text-cyan-400" />
            Snapshot Ledger & Checksums
          </h3>
          <span className="text-xs font-mono text-slate-400">{snapshots.length} Verified Commits</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-800 text-[11px]">
                <th className="p-3">Commit Hash</th>
                <th className="p-3">Created</th>
                <th className="p-3">Payload Size</th>
                <th className="p-3">Entities</th>
                <th className="p-3">SHA-256 Digest</th>
                <th className="p-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {snapshots.map((snap) => (
                <tr key={snap.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3 text-emerald-400 font-semibold">
                    <span className="flex items-center">
                      <GitCommit className="w-3 h-3 mr-1 text-slate-500" />
                      {snap.commitHash}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300">{snap.timestamp}</td>
                  <td className="p-3 text-slate-300">{snap.sizeKb} KB</td>
                  <td className="p-3 text-slate-400">{snap.entriesCount} records</td>
                  <td className="p-3 text-slate-500 truncate max-w-[180px]" title={snap.sha256}>
                    {snap.sha256.substring(0, 16)}...
                  </td>
                  <td className="p-3 text-right">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-2.5 h-2.5 mr-1" />
                      VERIFIED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
