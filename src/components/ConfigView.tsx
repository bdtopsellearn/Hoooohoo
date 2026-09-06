import React, { useState } from 'react';
import { 
  Settings, 
  Key, 
  Copy, 
  Check, 
  Download, 
  RefreshCw, 
  Eye, 
  EyeOff, 
  CreditCard,
  Send,
  Save
} from 'lucide-react';
import { PlatformConfig } from '../types';

interface ConfigViewProps {
  config: PlatformConfig;
  onSaveConfig: (updated: PlatformConfig) => void;
}

export const ConfigView: React.FC<ConfigViewProps> = ({ config, onSaveConfig }) => {
  const [formData, setFormData] = useState<PlatformConfig>({ ...config });
  const [copied, setCopied] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);
  const [showTokens, setShowTokens] = useState(false);

  const generateWebhookSecret = () => {
    const chars = 'abcdef0123456789';
    let secret = 'sec_';
    for (let i = 0; i < 28; i++) {
      secret += chars[Math.floor(Math.random() * chars.length)];
    }
    setFormData(prev => ({ ...prev, telegramWebhookSecret: secret }));
  };

  const handleCopyEnv = () => {
    const envContent = `# 🤖 Telegram Bot Token
BOT_TOKEN=${formData.botToken}

# 👤 Platform Owner
OWNER_ID=${formData.ownerId}
OWNER_USERNAME=${formData.ownerUsername}
ADMIN_HANDLE=${formData.adminHandle}
BOT_NAME=${formData.botName}
BRAND_NAME=${formData.brandName}
SUPPORT_USR=${formData.supportUser}

# 🌐 Webhook Secret
TELEGRAM_WEBHOOK_SECRET=${formData.telegramWebhookSecret}

# 🔐 Cipher Vault
CIPHER_VAULT_REPO=${formData.cipherVaultRepo}
CIPHER_VAULT_KEY=${formData.cipherVaultKey}
CIPHER_VAULT_BRANCH=${formData.cipherVaultBranch}

# 💳 OxaPay Merchant API
OXAPAY_API_KEY=${formData.oxapayApiKey}

# 📢 Announce Channel
ANNOUNCE_CHANNEL=${formData.announceChannel}

# 🌐 Port
PORT=${formData.port}
`;
    navigator.clipboard.writeText(envContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaveConfig(formData);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <span className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Settings className="w-5 h-5" />
            </span>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">
                Platform Credentials & Environment
              </h2>
              <p className="text-xs text-slate-400">
                Synchronized with <span className="font-mono text-slate-300">.env</span> in the host root directory.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowTokens(!showTokens)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs font-mono text-slate-300 hover:text-white transition-colors"
            >
              {showTokens ? <EyeOff className="w-3.5 h-3.5 mr-1.5" /> : <Eye className="w-3.5 h-3.5 mr-1.5" />}
              {showTokens ? 'Hide Secrets' : 'Show Secrets'}
            </button>
            <button
              onClick={handleCopyEnv}
              className="inline-flex items-center px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 mr-1.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 mr-1.5" />}
              {copied ? 'Copied .env!' : 'Copy .env'}
            </button>
          </div>
        </div>
      </div>

      {savedNotice && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs font-mono text-emerald-400 flex items-center justify-between">
          <span>✓ Environment configuration saved successfully to runtime state!</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Telegram Core & Owner Config */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
          <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
            <Send className="w-4 h-4 mr-2 text-sky-400" />
            Telegram Bot & Owner Authority
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Bot Token (@BotFather)</label>
              <input
                type={showTokens ? 'text' : 'password'}
                value={formData.botToken}
                onChange={(e) => setFormData({ ...formData, botToken: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Telegram Webhook Secret</label>
              <div className="flex space-x-2">
                <input
                  type={showTokens ? 'text' : 'password'}
                  value={formData.telegramWebhookSecret}
                  onChange={(e) => setFormData({ ...formData, telegramWebhookSecret: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                />
                <button
                  type="button"
                  onClick={generateWebhookSecret}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono rounded-lg transition-colors"
                  title="Generate Random Secret"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Owner Telegram User ID</label>
              <input
                type="text"
                value={formData.ownerId}
                onChange={(e) => setFormData({ ...formData, ownerId: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Admin Telegram Handle</label>
              <input
                type="text"
                value={formData.adminHandle}
                onChange={(e) => setFormData({ ...formData, adminHandle: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* OxaPay Merchant & Payments */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
          <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
            <CreditCard className="w-4 h-4 mr-2 text-amber-400" />
            OxaPay Automatic Merchant Gateway
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">OxaPay API Key</label>
              <input
                type={showTokens ? 'text' : 'password'}
                value={formData.oxapayApiKey}
                onChange={(e) => setFormData({ ...formData, oxapayApiKey: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Telegram Announcement Channel ID</label>
              <input
                type="text"
                value={formData.announceChannel}
                onChange={(e) => setFormData({ ...formData, announceChannel: e.target.value })}
                placeholder="-1002481940123"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Firebase Realtime Database & Cloud Sync */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider flex items-center">
              <span className="w-2 h-2 rounded-full bg-amber-400 mr-2 animate-pulse"></span>
              Firebase Realtime Database & Cloud Sync
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Connected: bot-host-website-9f118
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <label className="block text-slate-400 mb-1">Database URL (RTDB)</label>
              <input
                type="text"
                readOnly
                value="https://bot-host-website-9f118-default-rtdb.firebaseio.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 select-all"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Project ID / Auth Domain</label>
              <input
                type="text"
                readOnly
                value="bot-host-website-9f118.firebaseapp.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-300 select-all"
              />
            </div>
          </div>

          <div className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <div>
              <span className="text-emerald-400 font-semibold">Live Sync Endpoints: </span>
              <code>/payment_methods.json</code>, <code>/bot_status.json</code>, <code>/deployed_bots.json</code>
            </div>
          </div>
        </div>

        {/* Save Bar */}
        <div className="flex justify-end space-x-3 pt-2">
          <button
            type="submit"
            className="inline-flex items-center px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold font-mono rounded-lg shadow-sm transition-all"
          >
            <Save className="w-4 h-4 mr-1.5" />
            Save Environment Changes
          </button>
        </div>
      </form>
    </div>
  );
};
