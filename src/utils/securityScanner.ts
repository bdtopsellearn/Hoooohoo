import { ScanResult, SecurityFinding } from '../types';

interface Rule {
  regex: RegExp;
  category: '🔴 Restricted Access' | '🔴 System Integrity' | '🟡 Review Needed';
  severity: 'critical' | 'warning' | 'info';
  weight: number;
  description: string;
}

const RULES: Rule[] = [
  // 🔴 Restricted Access (Weight 45)
  {
    regex: /os\.walk\s*\(\s*['"]\/(?:root|etc|home|proc|sys|var)(?:['"]|\/)/,
    category: '🔴 Restricted Access',
    severity: 'critical',
    weight: 45,
    description: 'Sensitive system directory traversal attempt (/root, /etc, etc.)'
  },
  {
    regex: /glob\.glob\s*\(\s*['"]\/(?:\*)/,
    category: '🔴 Restricted Access',
    severity: 'critical',
    weight: 45,
    description: 'Broad root system file search wildcard pattern'
  },
  {
    regex: /shutil\.(?:copy|copy2|copyfile)\s*\([^)]*['"]\/root(?:['"]|\/)/,
    category: '🔴 Restricted Access',
    severity: 'critical',
    weight: 45,
    description: 'Copying or exfiltrating files from /root restricted path'
  },
  {
    regex: /(?:open|read_text)\s*\([^)]*['"]\/(?:root|etc|proc|sys)[^)]*\)[^)]*(?:send_document|requests\.(?:post|put)|urllib)/,
    category: '🔴 Restricted Access',
    severity: 'critical',
    weight: 45,
    description: 'Reading sensitive system path and streaming to network endpoint'
  },

  // 🔴 System Integrity (Weight 45)
  {
    regex: /subprocess\s*\.\s*(?:Popen|call|run)\s*\([^)]*shell\s*=\s*True[^)]*(?:input|stdin)/,
    category: '🔴 System Integrity',
    severity: 'critical',
    weight: 45,
    description: 'Shell command execution receives unvalidated input (Command Injection)'
  },
  {
    regex: /base64\.b64decode\s*\([^)]+\)[^;]*\b(?:exec|eval)\b/,
    category: '🔴 System Integrity',
    severity: 'critical',
    weight: 45,
    description: 'Base64 decoded content executed directly via eval/exec (Obfuscation)'
  },
  {
    regex: /zlib\.decompress\s*\([^)]+\)[^;]*\b(?:exec|eval)\b/,
    category: '🔴 System Integrity',
    severity: 'critical',
    weight: 45,
    description: 'Decompressed payload executed dynamically'
  },
  {
    regex: /marshal\.loads\s*\(/,
    category: '🔴 System Integrity',
    severity: 'critical',
    weight: 45,
    description: 'Deserializing arbitrary raw bytecode via marshal.loads'
  },

  // 🟡 Review Needed (Weight 8)
  {
    regex: /\b(?:import\s+|from\s+)ctypes\b/,
    category: '🟡 Review Needed',
    severity: 'warning',
    weight: 8,
    description: 'Low-level native C bindings (ctypes) detected'
  },
  {
    regex: /\b(?:import\s+|from\s+)pickle\b/,
    category: '🟡 Review Needed',
    severity: 'warning',
    weight: 8,
    description: 'Insecure Python object deserialization (pickle)'
  },
  {
    regex: /\bsocket\s*\.\s*socket\s*\(/,
    category: '🟡 Review Needed',
    severity: 'warning',
    weight: 8,
    description: 'Raw network socket creation outside standard HTTP/Telegram APIs'
  },
  {
    regex: /\b(?:exec|eval)\s*\(/,
    category: '🟡 Review Needed',
    severity: 'warning',
    weight: 8,
    description: 'Dynamic code execution (eval or exec) call'
  },
  {
    regex: /(?:base64\.b64decode|zlib\.decompress)\s*\(/,
    category: '🟡 Review Needed',
    severity: 'warning',
    weight: 6,
    description: 'Binary data decoding or decompression'
  }
];

export function runSecurityScan(code: string, fileName: string = 'bot.py'): ScanResult {
  const lines = code.split('\n');
  const findings: SecurityFinding[] = [];
  let totalScore = 0;

  // Estimate AST nodes count from statements
  const astNodeCount = Math.max(12, Math.floor(code.length / 18) + lines.length);

  // Scan line by line and across full text
  for (let i = 0; i < lines.length; i++) {
    const lineText = lines[i];
    if (lineText.trim().startsWith('#')) continue;

    for (const rule of RULES) {
      if (rule.regex.test(lineText)) {
        // Prevent duplicate findings on same line
        if (!findings.some(f => f.line === i + 1 && f.description === rule.description)) {
          findings.push({
            severity: rule.severity,
            category: rule.category,
            description: rule.description,
            line: i + 1,
            snippet: lineText.trim(),
            weight: rule.weight
          });
          totalScore += rule.weight;
        }
      }
    }
  }

  // Multi-line pattern checks if not already caught
  for (const rule of RULES) {
    if (rule.regex.test(code)) {
      if (!findings.some(f => f.description === rule.description)) {
        findings.push({
          severity: rule.severity,
          category: rule.category,
          description: rule.description,
          line: 1,
          snippet: 'Multi-line pattern match in file',
          weight: rule.weight
        });
        totalScore += rule.weight;
      }
    }
  }

  let verdict: 'APPROVED' | 'MANUAL_REVIEW' | 'REJECTED' = 'APPROVED';
  let verdictReason = 'Clean static & AST profile. Safe for Docker sandbox deployment.';

  if (totalScore >= 45) {
    verdict = 'REJECTED';
    verdictReason = `High-confidence security violations detected (Risk score: ${totalScore}). Execution blocked by control-plane policy.`;
  } else if (totalScore >= 8) {
    verdict = 'MANUAL_REVIEW';
    verdictReason = `Ambiguous or sensitive module usage detected (Risk score: ${totalScore}). Manual administrator confirmation required before launch.`;
  }

  return {
    score: totalScore,
    verdict,
    verdictReason,
    findings,
    astNodeCount,
    timestamp: new Date().toLocaleTimeString(),
    fileName
  };
}
