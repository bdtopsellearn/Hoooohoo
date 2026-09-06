import { BotRecord, NodeRecord, VaultSnapshot, LogEntry, PlatformConfig } from '../types';

export const INITIAL_CONFIG: PlatformConfig = {
  botToken: '8975432264:AAH6xBY7QEB8IYxoCyW_0iAsVFCC0DQtVdk',
  ownerId: '7831629041',
  ownerUsername: 'CODINGJAMES_X',
  adminHandle: '@CODINGJAMES_X',
  botName: '⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧',
  brandName: '⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧',
  supportUser: '@CODINGJAMES_X',
  telegramWebhookSecret: 'sec_7f9c20a1b94d183e92cf4a0918',
  cipherVaultRepo: 'Lord-Cipher/cipher-vault',
  cipherVaultKey: '3WVZp-oDToQRpuQqjVXctyEl_uJva_Bz_coi3kaiINA=',
  cipherVaultBranch: 'main',
  oxapayApiKey: 'ZMUBYW-BZWDM9-OF7QS0-YJF4YL',
  announceChannel: '-1002481940123',
  port: 10460
};

export const INITIAL_BOTS: BotRecord[] = [
  {
    id: 'bot_01',
    name: '⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧ Master Bot',
    script: 'bot.py',
    runtime: 'python3',
    status: 'running',
    nodeId: 'node_local',
    nodeName: 'Control Plane Local',
    uptime: '14d 6h 32m',
    cpuPercent: 2.8,
    memoryMb: 142.5,
    maxMemoryMb: 512,
    pid: 24819,
    sandboxMode: 'docker',
    lastPing: '2s ago',
    telegramHandle: '@CodingHostingBot',
    autoRestart: true
  },
  {
    id: 'bot_02',
    name: 'Crypto & OxaPay Escrow Agent',
    script: 'escrow_service.py',
    runtime: 'python3',
    status: 'running',
    nodeId: 'node_vps_eu',
    nodeName: 'VPS-Frankfurt-01',
    uptime: '3d 18h 12m',
    cpuPercent: 1.4,
    memoryMb: 88.2,
    maxMemoryMb: 256,
    pid: 19402,
    sandboxMode: 'docker',
    lastPing: '5s ago',
    telegramHandle: '@CipherEscrow_bot',
    autoRestart: true
  },
  {
    id: 'bot_03',
    name: 'Auto-Forwarder & Channel Backup',
    script: 'forwarder_worker.py',
    runtime: 'python3',
    status: 'running',
    nodeId: 'node_vps_eu',
    nodeName: 'VPS-Frankfurt-01',
    uptime: '1d 04h 50m',
    cpuPercent: 0.9,
    memoryMb: 64.0,
    maxMemoryMb: 256,
    pid: 19830,
    sandboxMode: 'restricted_proc',
    lastPing: '12s ago',
    telegramHandle: '@CipherRelayBot',
    autoRestart: true
  },
  {
    id: 'bot_04',
    name: 'Kaalix AI Telegram Assistant',
    script: 'kaalix_bot.py',
    runtime: 'python3',
    status: 'stopped',
    nodeId: 'node_local',
    nodeName: 'Control Plane Local',
    uptime: 'Offline',
    cpuPercent: 0.0,
    memoryMb: 0.0,
    maxMemoryMb: 512,
    pid: 0,
    sandboxMode: 'docker',
    lastPing: '35m ago',
    telegramHandle: '@KaalixAiBot',
    autoRestart: false
  }
];

export const INITIAL_NODES: NodeRecord[] = [
  {
    id: 'node_local',
    name: 'Control-Plane Local Worker',
    provider: 'Self-Hosted Container',
    connectionType: 'local',
    ipv4: '127.0.0.1',
    sshPort: 22,
    username: 'runner',
    authMethod: 'key',
    enabled: true,
    status: 'ONLINE',
    dockerAvailable: true,
    activeBots: 2,
    latencyMs: 1,
    osInfo: 'Linux 6.6 x86_64 / Alpine',
    lastTested: 'Just now'
  },
  {
    id: 'node_vps_eu',
    name: 'VPS-Frankfurt-01',
    provider: 'Hetzner Cloud',
    connectionType: 'ssh',
    ipv4: '159.69.112.48',
    sshPort: 2222,
    username: 'cipher_worker',
    authMethod: 'key',
    enabled: true,
    status: 'ONLINE',
    dockerAvailable: true,
    activeBots: 2,
    latencyMs: 28,
    osInfo: 'Ubuntu 24.04 LTS (systemd)',
    lastTested: '45s ago'
  },
  {
    id: 'node_vps_sg',
    name: 'VPS-Singapore-Worker',
    provider: 'DigitalOcean',
    connectionType: 'ssh',
    ipv4: '128.199.204.15',
    sshPort: 22,
    username: 'root',
    authMethod: 'key',
    enabled: false,
    status: 'NEEDS SETUP',
    dockerAvailable: false,
    activeBots: 0,
    latencyMs: 140,
    osInfo: 'Debian 12 Bookworm',
    lastTested: '10m ago'
  }
];

export const INITIAL_SNAPSHOTS: VaultSnapshot[] = [
  {
    id: 'snap_01',
    commitHash: '7b8f9a2e1d034',
    branch: 'main',
    timestamp: 'Today at 05:40 UTC',
    sizeKb: 438.2,
    encryptedWith: 'Fernet AES-128-CBC',
    sha256: '9f83a290c01a9df8327cbfe194820bc39e1208a4bb28490a0d',
    status: 'synced',
    entriesCount: 84
  },
  {
    id: 'snap_02',
    commitHash: '3c19e84d9f002',
    branch: 'main',
    timestamp: 'Yesterday at 23:15 UTC',
    sizeKb: 421.7,
    encryptedWith: 'Fernet AES-128-CBC',
    sha256: '5d891bca7821034fe9a12884c98e204bca78921dfbb0923048',
    status: 'synced',
    entriesCount: 81
  },
  {
    id: 'snap_03',
    commitHash: 'a9018e24dc901',
    branch: 'main',
    timestamp: 'Sep 04 at 18:00 UTC',
    sizeKb: 410.5,
    encryptedWith: 'Fernet AES-128-CBC',
    sha256: 'e81249bcf0193489ae82049ba019247ebcca91048bc8923011',
    status: 'synced',
    entriesCount: 78
  }
];

export const INITIAL_LOGS: LogEntry[] = [
  {
    id: 'log_01',
    timestamp: '06:05:12',
    level: 'info',
    category: 'SYSTEM',
    message: '⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧ Control-Plane operational on port 10460. Owner ID: 7831629041'
  },
  {
    id: 'log_02',
    timestamp: '06:05:14',
    level: 'success',
    category: 'NODE',
    message: 'Local node connected: docker isolation verified (Docker Engine 27.1.1)'
  },
  {
    id: 'log_03',
    timestamp: '06:05:18',
    level: 'success',
    category: 'NODE',
    message: 'Remote node VPS-Frankfurt-01 SSH handshake authenticated (Latency 28ms)'
  },
  {
    id: 'log_04',
    timestamp: '06:06:02',
    level: 'info',
    category: 'SANDBOX',
    message: 'Bot container #bot_01 healthy. Memory usage 142.5 MB / 512.0 MB'
  },
  {
    id: 'log_05',
    timestamp: '06:07:00',
    level: 'success',
    category: 'VAULT',
    message: 'Cipher Vault auto-sync committed: Lord-Cipher/cipher-vault (ref main: 7b8f9a2e)'
  }
];

export const SAMPLE_CODES = {
  safe: `# Safe Telegram Bot using pyTelegramBotAPI
import os
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN", "123456:ABC-DEF")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Status"), types.KeyboardButton("ℹ️ Info"))
    bot.reply_to(message, "Welcome to Cipher Bot! How can I assist you today?", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text == "🚀 Status":
        bot.reply_to(message, "System is running at 100% efficiency!")
    else:
        bot.reply_to(message, f"Received: {message.text}")

if __name__ == "__main__":
    print("Bot polling started safely...")
    bot.infinity_polling()
`,
  suspicious: `# Suspicious Bot Script with Dynamic Code Exec & Sockets
import base64
import socket
import os

encoded_payload = "cHJpbnQoIkhlbGxvIGZyb20gaGlkZGVuIHBheWxvYWQiKQ=="

# Decoding and executing dynamically
decoded = base64.b64decode(encoded_payload).decode('utf-8')
exec(decoded)

# Raw socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(("192.168.1.100", 4444))
    s.sendall(b"PING")
except Exception as e:
    pass
`,
  malicious: `# Malicious System Traversal & Shell Command Injection
import os
import shutil
import subprocess

# Sensitive path walk
for root, dirs, files in os.walk("/root"):
    for file in files:
        print(os.path.join(root, file))

# Restricted path copy
shutil.copy("/root/.ssh/id_rsa", "/tmp/extracted_key")

# Shell execution receiving uncontrolled input
user_cmd = input("Enter cmd: ")
subprocess.Popen("rm -rf /" + user_cmd, shell=True)
`
};
