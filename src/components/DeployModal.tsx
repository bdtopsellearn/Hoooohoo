import React, { useState } from 'react';
import { Terminal, Copy, Check, Server, ExternalLink, Shield } from 'lucide-react';

interface DeployModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeployModal: React.FC<DeployModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'render' | 'vps' | 'railway'>('render');
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(id);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const renderEnvVars = `BOT_TOKEN=8975432264:AAH6xBY7QEB8IYxoCyW_0iAsVFCC0DQtVdk
OWNER_ID=7831629041
PORT=10000
ADMIN_HANDLE=@CODINGJAMES_X
BRAND_NAME=⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧
SUPPORT_USR=@CODINGJAMES_X
UPDATE_CH=https://t.me/CODINGJAMES_X
FIREBASE_DATABASE_URL=https://bot-host-website-9f118-default-rtdb.firebaseio.com
FIREBASE_PROJECT_ID=bot-host-website-9f118
FIREBASE_API_KEY=AIzaSyAIw4w6nMR440pZh-zw4GBsd0o0fUllgSo
FIREBASE_AUTH_DOMAIN=bot-host-website-9f118.firebaseapp.com
FIREBASE_STORAGE_BUCKET=bot-host-website-9f118.firebasestorage.app
FIREBASE_APP_ID=1:11293173080:web:2a6dbf296e61378b03b12d
CIPHER_VAULT_KEY=3WVZp-oDToQRpuQqjVXctyEl_uJva_Bz_coi3kaiINA=
OXAPAY_API_KEY=ZMUBYW-BZWDM9-OF7QS0-YJF4YL`;

  const vpsCommands = `# 1. Update and install packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl

# 2. Clone repository & initialize virtual environment
git clone https://github.com/Lord-Cipher/cipher-bot-hosting.git /opt/cipher-bot
cd /opt/cipher-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
nano .env
# Enter BOT_TOKEN, OWNER_ID=7831629041, CIPHER_VAULT_KEY

# 4. Run through systemd service or background manager
bash run_bot_service.sh
`;

  const railwayConfig = `# Railway Procfile Execution
web: python3 bot.py

# Required environment variables in Railway dashboard:
# BOT_TOKEN=your_bot_token
# OWNER_ID=7831629041
# CIPHER_VAULT_KEY=3WVZp-oDToQRpuQqjVXctyEl_uJva_Bz_coi3kaiINA=
# PORT=10460
`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2.5">
            <span className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Server className="w-4 h-4" />
            </span>
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">
                Production Deployment Instructions
              </h3>
              <p className="text-[11px] text-slate-400">
                Render Cloud, Linux VPS & Railway configuration
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xs font-mono"
          >
            ✕ Close
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex space-x-2 border-b border-slate-800/80 pb-2">
          <button
            onClick={() => setActiveTab('render')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
              activeTab === 'render'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Render Cloud (dashboard.render.com)
          </button>
          <button
            onClick={() => setActiveTab('vps')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
              activeTab === 'vps'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            VPS / Linux (Ubuntu)
          </button>
          <button
            onClick={() => setActiveTab('railway')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
              activeTab === 'railway'
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Railway Cloud
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'render' && (
          <div className="space-y-3">
            <div className="p-3 bg-slate-950/80 border border-sky-500/30 rounded-xl text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-sky-400 flex items-center">
                  🚀 Render Web Service Settings:
                </span>
                <a
                  href="https://dashboard.render.com"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center text-sky-400 hover:underline text-[11px]"
                >
                  Open dashboard.render.com <ExternalLink className="w-3 h-3 ml-1" />
                </a>
              </div>
              <ul className="text-slate-300 space-y-1 font-mono text-[11px] list-disc list-inside">
                <li><span className="text-white font-semibold">Service Type:</span> Web Service</li>
                <li><span className="text-white font-semibold">Root Directory:</span> <code className="bg-slate-800 px-1 rounded text-amber-300">cipher-bot-hosting-main</code> (বা খালি রাখুন যদি ফোল্ডারের ভেতরের ফাইলগুলো গিটহাবে রাখেন)</li>
                <li><span className="text-white font-semibold">Runtime:</span> Python 3</li>
                <li><span className="text-white font-semibold">Build Command:</span> <code className="bg-slate-800 px-1 rounded text-emerald-300">pip install -r requirements.txt</code></li>
                <li><span className="text-white font-semibold">Start Command:</span> <code className="bg-slate-800 px-1 rounded text-emerald-300">python bot.py</code></li>
                <li><span className="text-white font-semibold">Health Check Path:</span> <code className="bg-slate-800 px-1 rounded text-emerald-300">/health</code></li>
              </ul>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Environment Variables (Render Dashboard):</span>
              <button
                onClick={() => copyText(renderEnvVars, 'render')}
                className="inline-flex items-center text-sky-400 hover:text-sky-300"
              >
                {copiedSection === 'render' ? <Check className="w-3.5 h-3.5 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
                {copiedSection === 'render' ? 'Copied Env Vars!' : 'Copy All Env Vars'}
              </button>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-[160px] leading-relaxed scrollbar-thin">
              <pre>{renderEnvVars}</pre>
            </div>

            <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-[11px] font-mono text-amber-300">
              <span className="font-bold">⚠️ Firebase Realtime Database Security Rule:</span>
              <br />
              Firebase Console &gt; Realtime Database &gt; Rules এ গিয়ে <code className="bg-black/30 px-1 rounded">{'{ ".read": true, ".write": true }'}</code> করে Publish করে দিন যেন বট ডেটাবেজে সরাসরি সিঙ্ক হতে পারে।
            </div>
          </div>
        )}

        {activeTab === 'vps' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Terminal Setup Commands:</span>
              <button
                onClick={() => copyText(vpsCommands, 'vps')}
                className="inline-flex items-center text-emerald-400 hover:text-emerald-300"
              >
                {copiedSection === 'vps' ? <Check className="w-3.5 h-3.5 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
                {copiedSection === 'vps' ? 'Copied script!' : 'Copy Script'}
              </button>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-[280px] leading-relaxed scrollbar-thin">
              <pre>{vpsCommands}</pre>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-400">
              <span className="text-emerald-400 font-bold">Tip: </span>
              Verify systemd availability by checking <span className="text-slate-200">ps -p 1 -o comm=</span> before running the background service daemon.
            </div>
          </div>
        )}

        {activeTab === 'railway' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>Railway Procfile Configuration:</span>
              <button
                onClick={() => copyText(railwayConfig, 'railway')}
                className="inline-flex items-center text-indigo-400 hover:text-indigo-300"
              >
                {copiedSection === 'railway' ? <Check className="w-3.5 h-3.5 mr-1" /> : <Copy className="w-3.5 h-3.5 mr-1" />}
                {copiedSection === 'railway' ? 'Copied!' : 'Copy'}
              </button>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-[280px] leading-relaxed scrollbar-thin">
              <pre>{railwayConfig}</pre>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};
