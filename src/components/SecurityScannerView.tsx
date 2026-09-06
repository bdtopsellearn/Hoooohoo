import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  XCircle, 
  CheckCircle2, 
  Code2, 
  FileCode, 
  Zap, 
  RotateCcw,
  Sparkles
} from 'lucide-react';
import { ScanResult } from '../types';
import { runSecurityScan } from '../utils/securityScanner';
import { SAMPLE_CODES } from '../data/initialData';

export const SecurityScannerView: React.FC = () => {
  const [code, setCode] = useState<string>(SAMPLE_CODES.safe);
  const [activeSample, setActiveSample] = useState<'safe' | 'suspicious' | 'malicious'>('safe');
  const [scanResult, setScanResult] = useState<ScanResult>(() => runSecurityScan(SAMPLE_CODES.safe));
  const [isScanning, setIsScanning] = useState<boolean>(false);

  const handleSelectSample = (type: 'safe' | 'suspicious' | 'malicious') => {
    setActiveSample(type);
    setCode(SAMPLE_CODES[type]);
    const res = runSecurityScan(SAMPLE_CODES[type]);
    setScanResult(res);
  };

  const handleScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      const res = runSecurityScan(code);
      setScanResult(res);
      setIsScanning(false);
    }, 350);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  AST & Static Preflight Security Scanner
                </h2>
                <p className="text-xs text-slate-400">
                  Deterministic code analysis based on <span className="font-mono text-slate-300">security_scanner_free.py</span> & <span className="font-mono text-slate-300">ai_preflight.py</span>.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 mr-1">Load Preset:</span>
            <button
              onClick={() => handleSelectSample('safe')}
              className={`px-3 py-1.5 text-xs font-mono font-medium rounded-lg border transition-all ${
                activeSample === 'safe'
                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              🟢 Safe Bot
            </button>
            <button
              onClick={() => handleSelectSample('suspicious')}
              className={`px-3 py-1.5 text-xs font-mono font-medium rounded-lg border transition-all ${
                activeSample === 'suspicious'
                  ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              🟡 Suspicious Exec
            </button>
            <button
              onClick={() => handleSelectSample('malicious')}
              className={`px-3 py-1.5 text-xs font-mono font-medium rounded-lg border transition-all ${
                activeSample === 'malicious'
                  ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              🔴 Malicious Exploit
            </button>
          </div>
        </div>
      </div>

      {/* Main Analysis Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Code Input & Editor */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <span>Python Source Code (bot.py)</span>
            </div>
            <button
              onClick={handleScan}
              disabled={isScanning}
              className="inline-flex items-center px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold font-mono transition-all shadow-sm"
            >
              {isScanning ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  Analyzing AST...
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5 mr-1.5 fill-current" />
                  Analyze Code
                </>
              )}
            </button>
          </div>

          <div className="relative rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
            <textarea
              value={code}
              onChange={(e) => {
                setCode(e.target.value);
                setActiveSample('safe'); // Custom
              }}
              rows={18}
              className="w-full bg-transparent p-4 text-xs font-mono text-slate-200 leading-relaxed resize-y focus:outline-none scrollbar-thin"
              spellCheck={false}
            />
          </div>
        </div>

        {/* Scan Verdict & Findings */}
        <div className="lg:col-span-5 space-y-4">
          {/* Verdict Card */}
          <div
            className={`border rounded-xl p-5 transition-all shadow-sm ${
              scanResult.verdict === 'APPROVED'
                ? 'bg-emerald-950/30 border-emerald-500/30'
                : scanResult.verdict === 'MANUAL_REVIEW'
                ? 'bg-amber-950/30 border-amber-500/30'
                : 'bg-rose-950/30 border-rose-500/30'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                {scanResult.verdict === 'APPROVED' && (
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                )}
                {scanResult.verdict === 'MANUAL_REVIEW' && (
                  <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
                )}
                {scanResult.verdict === 'REJECTED' && (
                  <XCircle className="w-6 h-6 text-rose-400 shrink-0" />
                )}
                <div>
                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                    Verdict Status
                  </span>
                  <h3
                    className={`text-lg font-bold font-mono tracking-tight ${
                      scanResult.verdict === 'APPROVED'
                        ? 'text-emerald-400'
                        : scanResult.verdict === 'MANUAL_REVIEW'
                        ? 'text-amber-400'
                        : 'text-rose-400'
                    }`}
                  >
                    {scanResult.verdict === 'APPROVED' && 'APPROVED FOR LAUNCH'}
                    {scanResult.verdict === 'MANUAL_REVIEW' && 'MANUAL REVIEW REQUIRED'}
                    {scanResult.verdict === 'REJECTED' && 'CRITICAL POLICY REJECTION'}
                  </h3>
                </div>
              </div>

              <div className="text-right font-mono">
                <span className="text-[10px] text-slate-400 uppercase">Risk Score</span>
                <p
                  className={`text-xl font-bold ${
                    scanResult.score === 0
                      ? 'text-emerald-400'
                      : scanResult.score < 45
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}
                >
                  {scanResult.score} pts
                </p>
              </div>
            </div>

            <p className="mt-3 text-xs text-slate-300 leading-relaxed border-t border-slate-800/80 pt-3">
              {scanResult.verdictReason}
            </p>

            <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>AST Statements Analyzed: {scanResult.astNodeCount}</span>
              <span>Time: {scanResult.timestamp}</span>
            </div>
          </div>

          {/* Findings List */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Detected Security Rules ({scanResult.findings.length})
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                Threshold: &gt;= 45 Block | &gt;= 8 Review
              </span>
            </div>

            {scanResult.findings.length === 0 ? (
              <div className="text-center py-6 border border-dashed border-slate-800 rounded-lg">
                <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500/60 mb-2" />
                <p className="text-xs font-mono text-slate-300">0 Violations Detected</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Code adheres to non-destructive hosting policies.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[320px] overflow-y-auto scrollbar-thin pr-1">
                {scanResult.findings.map((f, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-xs space-y-1.5 ${
                      f.severity === 'critical'
                        ? 'bg-rose-950/20 border-rose-500/30'
                        : 'bg-amber-950/20 border-amber-500/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{f.category}</span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
                        Line {f.line} • +{f.weight} pts
                      </span>
                    </div>
                    <p className="text-slate-300 text-xs">{f.description}</p>
                    <div className="bg-slate-950 p-1.5 rounded font-mono text-[11px] text-slate-400 truncate">
                      {f.snippet}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
