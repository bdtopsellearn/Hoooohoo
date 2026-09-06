import React from 'react';
import { 
  Bot, 
  ShieldCheck, 
  Server, 
  Lock, 
  Settings, 
  Terminal, 
  BookOpen, 
  Radio
} from 'lucide-react';
import { PlatformConfig } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  config: PlatformConfig;
  onOpenDeployModal: () => void;
  runningBotsCount: number;
  totalBotsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  config,
  onOpenDeployModal,
  runningBotsCount,
  totalBotsCount
}) => {
  const navItems = [
    { id: 'bots', label: 'Bot Fleet', icon: Bot, badge: `${runningBotsCount}/${totalBotsCount}` },
    { id: 'scanner', label: 'Preflight Scanner', icon: ShieldCheck, badge: 'AST' },
    { id: 'nodes', label: 'Infrastructure', icon: Server, badge: '3 Nodes' },
    { id: 'vault', label: 'Cipher Vault', icon: Lock, badge: 'Encrypted' },
    { id: 'config', label: 'Credentials & .env', icon: Settings },
    { id: 'logs', label: 'Live Console', icon: Terminal, badge: 'Live' }
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Identity */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2.5">
              <div className="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono font-bold text-lg shadow-sm shadow-emerald-500/10">
                ⚡
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-extrabold tracking-tight text-white text-base sm:text-lg">
                    {config.brandName || '⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧'}
                  </span>
                  <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Radio className="w-2.5 h-2.5 mr-1 animate-pulse" />
                    ONLINE
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono">
                  Owner: <span className="text-slate-200">{config.adminHandle}</span> <span className="text-slate-500">({config.ownerId})</span>
                </p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2.5">
            <button
              id="nav-deploy-guide-btn"
              onClick={onOpenDeployModal}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md border border-slate-700 bg-slate-900/80 text-slate-200 hover:bg-slate-800 hover:border-slate-600 transition-colors shadow-sm"
            >
              <BookOpen className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
              VPS / Deploy Guides
            </button>
            <div className="hidden md:flex items-center text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded-md">
              <span className="text-slate-500 mr-1.5">PORT:</span>
              <span className="text-emerald-400 font-semibold">{config.port}</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 overflow-x-auto py-2 border-t border-slate-800/80 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`tab-btn-${item.id}`}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
