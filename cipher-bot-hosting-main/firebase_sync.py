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

_LAST_401_WARNED = 0


def _log_401_warning() -> None:
    global _LAST_401_WARNED
    now = time.time()
    # Log warning at most once every 15 minutes to keep production logs clean
    if now - _LAST_401_WARNED > 900:
        _LAST_401_WARNED = now
        print(
            "[firebase_sync] ℹ️ Firebase RTDB returned 401 Unauthorized.\n"
            "   Cause: Database security rules are locked.\n"
            "   Solution: In Firebase Console -> Realtime Database -> Rules, set:\n"
            "   {\n"
            '     "rules": {\n'
            '       ".read": true,\n'
            '       ".write": true\n'
            "     }\n"
            "   }\n"
            "   (Or add FIREBASE_DATABASE_SECRET to Render Environment Variables).",
            flush=True
        )


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
            _log_401_warning()
            return {
                "ok": False,
                "status": 401,
                "message": "Unauthorized. Set Firebase RTDB rules to { '.read': true, '.write': true } or provide FIREBASE_DATABASE_SECRET."
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
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        else:
            print(f"[firebase_sync] payment_methods HTTP {e.code}: {e.reason}", flush=True)
        return False
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
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        else:
            print(f"[firebase_sync] bot_status HTTP {e.code}: {e.reason}", flush=True)
        return False
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
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        return False
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
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
    except Exception as e:
        print(f"[firebase_sync] get_payment_methods: {e}", flush=True)
    return {}


# ═════════════════════════════════════════════════════════════════
# FULL DATABASE & BOT CLOUD PERSISTENCE (Anti-Wipe on Render Restarts)
# ═════════════════════════════════════════════════════════════════

import base64
from pathlib import Path


def sync_full_database_to_firebase(db_data: dict) -> bool:
    """Persist the complete panel_db (users, bots, plans) to Firebase RTDB."""
    try:
        url = _build_url("cipher_vault/panel_db.json")
        # Sanitize any non-serializable objects
        payload = json.dumps(db_data, default=str).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        return False
    except Exception as e:
        print(f"[firebase_sync] db sync error: {e}", flush=True)
        return False


def fetch_full_database_from_firebase() -> dict:
    """Fetch panel_db from Firebase RTDB."""
    try:
        url = _build_url("cipher_vault/panel_db.json")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode("utf-8")
            if data and data != "null":
                res = json.loads(data)
                if isinstance(res, dict) and "users" in res:
                    return res
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
    except Exception as e:
        print(f"[firebase_sync] db fetch error: {e}", flush=True)
    return {}


def sync_full_settings_to_firebase(settings_data: dict) -> bool:
    """Persist panel_settings to Firebase RTDB."""
    try:
        url = _build_url("cipher_vault/panel_settings.json")
        payload = json.dumps(settings_data, default=str).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        return False
    except Exception as e:
        print(f"[firebase_sync] settings sync error: {e}", flush=True)
        return False


def fetch_full_settings_from_firebase() -> dict:
    """Fetch panel_settings from Firebase RTDB."""
    try:
        url = _build_url("cipher_vault/panel_settings.json")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode("utf-8")
            if data and data != "null":
                res = json.loads(data)
                if isinstance(res, dict):
                    return res
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
    except Exception as e:
        print(f"[firebase_sync] settings fetch error: {e}", flush=True)
    return {}


def sync_key_to_firebase(key_id: str, key_bytes: bytes, meta: dict = None) -> bool:
    """Save encryption key to Firebase so decrypted files can be restored after restart."""
    try:
        url = _build_url(f"cipher_vault/keys/{key_id}.json")
        payload = {
            "key": key_bytes.decode("latin1") if isinstance(key_bytes, bytes) else str(key_bytes),
            "meta": meta or {},
            "ts": int(time.time()),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        return False
    except Exception as e:
        print(f"[firebase_sync] key sync error: {e}", flush=True)
        return False


def fetch_all_keys_from_firebase() -> dict:
    """Fetch all stored encryption keys from Firebase."""
    try:
        url = _build_url("cipher_vault/keys.json")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode("utf-8")
            if data and data != "null":
                return json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
    except Exception as e:
        print(f"[firebase_sync] keys fetch error: {e}", flush=True)
    return {}


def sync_encfile_to_firebase(key_id: str, enc_bytes: bytes, rel_path: str = "") -> bool:
    """Sync encrypted bot binary payload to Firebase RTDB."""
    try:
        url = _build_url(f"cipher_vault/enc_files/{key_id}.json")
        payload = {
            "key_id": key_id,
            "rel_path": rel_path,
            "b64": base64.b64encode(enc_bytes).decode("ascii"),
            "size": len(enc_bytes),
            "uploaded": int(time.time()),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
        return False
    except Exception as e:
        print(f"[firebase_sync] encfile sync error: {e}", flush=True)
        return False


def fetch_encfile_from_firebase(key_id: str) -> bytes:
    """Fetch encrypted bot file from Firebase RTDB."""
    try:
        url = _build_url(f"cipher_vault/enc_files/{key_id}.json")
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            if data and data != "null":
                doc = json.loads(data)
                b64 = doc.get("b64")
                if b64:
                    return base64.b64decode(b64.encode("ascii"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            _log_401_warning()
    except Exception as e:
        print(f"[firebase_sync] encfile fetch error: {e}", flush=True)
    return b""


def delete_bot_from_firebase(bot_id: str, key_ids: list = None) -> bool:
    """Delete bot records and associated files from Firebase when user deletes a bot."""
    try:
        url = _build_url(f"deployed_bots/{bot_id}.json")
        req = urllib.request.Request(url, method="DELETE")
        req.add_header("User-Agent", "CipherBotHosting/2.1")
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

        if key_ids:
            for kid in key_ids:
                try:
                    k_url = _build_url(f"cipher_vault/keys/{kid}.json")
                    urllib.request.urlopen(urllib.request.Request(k_url, method="DELETE"), timeout=4)
                    f_url = _build_url(f"cipher_vault/enc_files/{kid}.json")
                    urllib.request.urlopen(urllib.request.Request(f_url, method="DELETE"), timeout=4)
                except Exception:
                    pass
        return True
    except Exception as e:
        print(f"[firebase_sync] delete_bot error: {e}", flush=True)
        return False


