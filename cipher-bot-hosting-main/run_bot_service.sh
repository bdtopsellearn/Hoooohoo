#!/usr/bin/env bash
# CODING_HOSTING Bot Supervisor Service with Lockfile Protection
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PID_FILE="/tmp/coding_hosting_bot.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[CODING_HOSTING] Already running with PID $OLD_PID. Exiting."
        exit 0
    fi
fi

echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

echo "[CODING_HOSTING] Starting Bot Service..."
echo "[CODING_HOSTING] Boot Name: ⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧"
echo "[CODING_HOSTING] Owner ID: 7831629041 (@CODINGJAMES_X)"

while true; do
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting bot.py daemon..."
    python3 bot.py 2>&1 | tee -a storage/logs/bot_daemon.log || true
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Bot process exited. Respawning in 3 seconds..."
    sleep 3
done
