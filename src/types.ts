export interface BotRecord {
  id: string;
  name: string;
  script: string;
  runtime: 'python3' | 'nodejs';
  status: 'running' | 'stopped' | 'restarting' | 'error';
  nodeId: string;
  nodeName: string;
  uptime: string;
  cpuPercent: number;
  memoryMb: number;
  maxMemoryMb: number;
  pid: number;
  sandboxMode: 'docker' | 'restricted_proc' | 'unisolated';
  lastPing: string;
  telegramHandle?: string;
  autoRestart: boolean;
}

export interface NodeRecord {
  id: string;
  name: string;
  provider: string;
  connectionType: 'local' | 'ssh' | 'agent';
  ipv4: string;
  sshPort: number;
  username: string;
  authMethod: 'key' | 'password';
  enabled: boolean;
  status: 'ONLINE' | 'AUTHENTICATED' | 'OFFLINE' | 'NEEDS SETUP' | 'AUTHENTICATION FAILED';
  dockerAvailable: boolean;
  activeBots: number;
  latencyMs: number;
  osInfo: string;
  lastTested: string;
}

export interface SecurityFinding {
  severity: 'critical' | 'warning' | 'info';
  category: '🔴 Restricted Access' | '🔴 System Integrity' | '🟡 Review Needed' | '🟢 Safe Pattern';
  description: string;
  line: number;
  snippet: string;
  weight: number;
}

export interface ScanResult {
  score: number;
  verdict: 'APPROVED' | 'MANUAL_REVIEW' | 'REJECTED';
  verdictReason: string;
  findings: SecurityFinding[];
  astNodeCount: number;
  timestamp: string;
  fileName: string;
}

export interface VaultSnapshot {
  id: string;
  commitHash: string;
  branch: string;
  timestamp: string;
  sizeKb: number;
  encryptedWith: string;
  sha256: string;
  status: 'synced' | 'in_progress' | 'failed';
  entriesCount: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success' | 'debug';
  category: 'SYSTEM' | 'SECURITY' | 'VAULT' | 'SANDBOX' | 'NODE';
  message: string;
}

export interface PlatformConfig {
  botToken: string;
  ownerId: string;
  ownerUsername: string;
  adminHandle: string;
  botName: string;
  brandName: string;
  supportUser: string;
  telegramWebhookSecret: string;
  cipherVaultRepo: string;
  cipherVaultKey: string;
  cipherVaultBranch: string;
  oxapayApiKey: string;
  announceChannel: string;
  port: number;
}
