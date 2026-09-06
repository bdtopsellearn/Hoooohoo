"""
Firebase Realtime Database & Cloud Sync Helper for ⟦𝗖𝗢𝗗𝗜𝗡𝗚_𝙃𝙊𝙎𝙏𝙄𝙉𝙂⟧
Project: bot-host-website-9f118
Database URL: https://bot-host-website-9f118-default-rtdb.firebaseio.com
"""

import os
import time
import json
import urllib.request
import urllib.error

# ── Firebase Web Configuration ──
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyAIw4w6nMR440pZh-zw4GBsd0o0fUllgSo"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "bot-host-website-9f118.firebaseapp.com"),
    "databaseURL": os.environ.get(
        "FIREBASE_DATABASE_URL",
        "https://bot-host-website-9f118-default-rtdb.firebaseio.com"
    ).rstrip("/"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "bot-host-website-9f118"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "bot-host-website-9f118.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "11293173080"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:11293173080:web:2a6dbf296e61378b03b12d"),
    "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID", "G-ZZGT8KMYWG"),
}

FIREBASE_DATABASE_URL = FIREBASE_CONFIG["databaseURL"]
FIREBASE_DATABASE_SECRET = os.environ.get("FIREBASE_DATABASE_SECRET", "").strip()


def _build_url(endpoint: str) -> str:
    path = endpoint.lstrip("/")
    url = f"{FIREBASE_DATABASE_URL}/{path}"
    if FIREBASE_DATABASE_SECRET:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}auth={FIREBASE_DATABASE_SECRET}"
    return url


def test_firebase_connection() -> dict:
    """Test connection to Firebase Realtime Database."""
    try:
        url = _build_url(".json?shallow=true")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"ok": True, "status": resp.status, "message": "Connected to Firebase RTDB"}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {
                "ok": False,
                "status": 401,
                "message": "Unauthorized. Please set Firebase RTDB rules to { '.read': true, '.write': true } or provide FIREBASE_DATABASE_SECRET in .env."
            }
        return {"ok": False, "status": e.code, "message": f"HTTP Error {e.code}: {e.reason}"}
    except Exception as e:
        return {"ok": False, "status": 0, "message": str(e)}


def sync_payment_methods_to_firebase(payment_methods: dict) -> bool:
    """Sync payment methods to Firebase Realtime Database at /payment_methods.json"""
    try:
        url = _build_url("payment_methods.json")
        data = json.dumps(payment_methods).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[firebase_sync] payment_methods sync: {e}", flush=True)
        return False


def sync_bot_status_to_firebase(status_data: dict) -> bool:
    """Sync live bot status & telemetry to Firebase Realtime Database at /bot_status.json"""
    try:
        url = _build_url("bot_status.json")
        payload = {
            **status_data,
            "last_synced_at": int(time.time()),
            "last_synced_readable": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[firebase_sync] bot_status sync: {e}", flush=True)
        return False


def sync_deployed_bot_to_firebase(bot_id: str, bot_data: dict) -> bool:
    """Sync metadata for a user's deployed bot to /deployed_bots/<bot_id>.json"""
    try:
        url = _build_url(f"deployed_bots/{bot_id}.json")
        data = json.dumps(bot_data).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PATCH")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[firebase_sync] deployed_bot sync: {e}", flush=True)
        return False


def get_firebase_payment_methods() -> dict:
    """Fetch payment methods from Firebase Realtime Database"""
    try:
        url = _build_url("payment_methods.json")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode("utf-8")
            if data and data != "null":
                return json.loads(data)
    except Exception as e:
        print(f"[firebase_sync] get_payment_methods: {e}", flush=True)
    return {}

