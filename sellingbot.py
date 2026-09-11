#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#   𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 — 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗦𝗛𝗢𝗣 𝗕𝗢𝗧
#   Developer: @bd_top_admin  |  Firebase: just-sell-bot
# ═══════════════════════════════════════════════════════════════

import os
import sys
import logging
import asyncio
import re
import json
from datetime import datetime
from functools import wraps
from typing import Optional

import firebase_admin
from firebase_admin import credentials, db

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    BotCommand, MenuButtonCommands,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN      = os.environ.get("BOT_TOKEN", "8928084437:AAEVvfkDDMg7YDBygWaCVP6Af1i8X1xJxco")
ADMIN_IDS_RAW  = os.environ.get("ADMIN_ID", "7831629041")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@bd_top_admin")
FIREBASE_URL   = os.environ.get("FIREBASE_URL", "https://just-sell-bot-default-rtdb.firebaseio.com")
SERVICE_KEY    = os.environ.get("SERVICE_KEY", "serviceAccountKey.json")

# Parse comma-separated ADMIN_IDs
ADMIN_IDS = set()
for _part in re.split(r"[,;:\s]+", str(ADMIN_IDS_RAW).strip()):
    if _part.isdigit():
        ADMIN_IDS.add(int(_part))
if not ADMIN_IDS:
    ADMIN_IDS.add(7831629041)
ADMIN_ID = list(ADMIN_IDS)[0]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUTTON COLOR PATCH (from button_color_system.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _find_button_style(text: str) -> str:
    if not text:
        return "primary"
    t = text.lower()
    danger_kw = ["cancel","বাতিল","reject","remove","delete","ডিলিট",
                 "stop","exit","close","back","পিছনে","home","হোম",
                 "❌","🔴","🏠"]
    success_kw = ["approve","অ্যাপ্রুভ","confirm","submit","deposit",
                  "ডিপোজিট","withdraw","pay","পেমেন্ট","add","earn",
                  "ইনকাম","buy","কিনুন","wallet","balance","ব্যালেন্স",
                  "gmail","✅","🟢","💰","💎","profile","my profile",
                  "প্রোফাইল"]
    if any(k in t for k in danger_kw):
        return "danger"
    if any(k in t for k in success_kw):
        return "success"
    return "primary"

_orig_inline = InlineKeyboardButton.__init__
def _patched_inline(self, text, *args, style=None,
                    icon_custom_emoji_id=None, api_kwargs=None, **kwargs):
    if not style:
        style = _find_button_style(text)
    if style or icon_custom_emoji_id:
        if api_kwargs is None:
            api_kwargs = {}
        if style:
            api_kwargs["style"] = style
        if icon_custom_emoji_id:
            api_kwargs["icon_custom_emoji_id"] = str(icon_custom_emoji_id)
    if api_kwargs is not None:
        kwargs["api_kwargs"] = api_kwargs
    _orig_inline(self, text, *args, **kwargs)
InlineKeyboardButton.__init__ = _patched_inline

_orig_kb = KeyboardButton.__init__
def _patched_kb(self, text, *args, style=None,
                icon_custom_emoji_id=None, api_kwargs=None, **kwargs):
    if not style:
        style = _find_button_style(text)
    if style or icon_custom_emoji_id:
        if api_kwargs is None:
            api_kwargs = {}
        if style:
            api_kwargs["style"] = style
        if icon_custom_emoji_id:
            api_kwargs["icon_custom_emoji_id"] = str(icon_custom_emoji_id)
    if api_kwargs is not None:
        kwargs["api_kwargs"] = api_kwargs
    _orig_kb(self, text, *args, **kwargs)
KeyboardButton.__init__ = _patched_kb

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FIREBASE INIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
firebase_app = None
try:
    if os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"):
        service_account_dict = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
        cred = credentials.Certificate(service_account_dict)
        firebase_app = firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})
        logger.info(f"✅ Firebase initialized with environment service account for: {FIREBASE_URL}")
    elif os.path.exists(SERVICE_KEY):
        cred = credentials.Certificate(SERVICE_KEY)
        firebase_app = firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})
        logger.info(f"✅ Firebase initialized with certificate file '{SERVICE_KEY}' for: {FIREBASE_URL}")
    else:
        logger.warning(
            f"⚠️  '{SERVICE_KEY}' file not found! "
            f"Please place your Firebase serviceAccountKey.json in the project root or configure FIREBASE_SERVICE_ACCOUNT_JSON in your environment."
        )
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase: {e}")

import urllib.request
import urllib.error

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HYBRID LOCAL DB + FIREBASE STORAGE ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCAL_DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data.json")

def _load_local_store() -> dict:
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {LOCAL_DB_FILE}: {e}")
    return {}

def _save_local_store(data: dict):
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {LOCAL_DB_FILE}: {e}")

def _get_path_parts(path: str) -> list:
    return [p for p in str(path).strip("/").split("/") if p]

def _local_get(path: str, default=None):
    data = _load_local_store()
    parts = _get_path_parts(path)
    if not parts:
        return data if data else default
    curr = data
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return default
    return curr

def _local_set(path: str, val):
    data = _load_local_store()
    parts = _get_path_parts(path)
    if not parts:
        if isinstance(val, dict):
            _save_local_store(val)
        return
    curr = data
    for i, part in enumerate(parts[:-1]):
        if part not in curr or not isinstance(curr[part], dict):
            curr[part] = {}
        curr = curr[part]
    curr[parts[-1]] = val
    _save_local_store(data)

def _local_update(path: str, update_dict: dict):
    data = _load_local_store()
    parts = _get_path_parts(path)
    curr = data
    for part in parts:
        if part not in curr or not isinstance(curr[part], dict):
            curr[part] = {}
        curr = curr[part]
    if isinstance(curr, dict) and isinstance(update_dict, dict):
        curr.update(update_dict)
    _save_local_store(data)

def _local_delete(path: str):
    data = _load_local_store()
    parts = _get_path_parts(path)
    if not parts:
        _save_local_store({})
        return
    curr = data
    for part in parts[:-1]:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return
    if isinstance(curr, dict) and parts[-1] in curr:
        del curr[parts[-1]]
        _save_local_store(data)

def _firebase_rest_req(method: str, path: str, data=None):
    if not FIREBASE_URL or not FIREBASE_URL.startswith("http"):
        return None
    url = f"{FIREBASE_URL.rstrip('/')}/{path.strip('/')}.json"
    try:
        req = urllib.request.Request(url, method=method.upper())
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "TelegramShopBot/2.0")
        body = json.dumps(data).encode("utf-8") if data is not None else None
        with urllib.request.urlopen(req, data=body, timeout=4.0) as resp:
            resp_body = resp.read().decode("utf-8")
            if resp_body and resp_body != "null":
                return json.loads(resp_body)
            return True
    except Exception as e:
        logger.debug(f"Firebase REST {method} to {url} note: {e}")
        return None

def fb_get(path, default=None):
    # 1. Try Firebase Admin SDK
    if firebase_app:
        try:
            val = db.reference(path).get()
            if val is not None:
                _local_set(path, val)
                return val
        except Exception as e:
            logger.debug(f"Firebase Admin GET error for {path}: {e}")
    
    # 2. Try Firebase REST API
    rest_val = _firebase_rest_req("GET", path)
    if rest_val is not None and rest_val is not True:
        _local_set(path, rest_val)
        return rest_val

    # 3. Fallback to Local store
    return _local_get(path, default)

def fb_set(path, data):
    _local_set(path, data)
    if firebase_app:
        try:
            db.reference(path).set(data)
            return True
        except Exception as e:
            logger.debug(f"Firebase Admin SET error {path}: {e}")
    # Also attempt REST PUT sync
    _firebase_rest_req("PUT", path, data)
    return True

def fb_update(path, data):
    _local_update(path, data)
    if firebase_app:
        try:
            db.reference(path).update(data)
            return True
        except Exception as e:
            logger.debug(f"Firebase Admin UPDATE error {path}: {e}")
    # Also attempt REST PATCH sync
    _firebase_rest_req("PATCH", path, data)
    return True

def fb_push(path, data):
    push_id = f"-M{int(datetime.now().timestamp() * 1000)}"
    full_path = f"{path}/{push_id}"
    _local_set(full_path, data)
    if firebase_app:
        try:
            res = db.reference(path).push(data)
            return res
        except Exception as e:
            logger.debug(f"Firebase Admin PUSH error {path}: {e}")
    _firebase_rest_req("PUT", full_path, data)
    return type("PushResult", (), {"key": push_id})()

def fb_delete(path):
    _local_delete(path)
    if firebase_app:
        try:
            db.reference(path).delete()
            return True
        except Exception as e:
            logger.debug(f"Firebase Admin DELETE error {path}: {e}")
    _firebase_rest_req("DELETE", path)
    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEFAULT SETTINGS (written once if not exist)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def init_defaults():
    settings = fb_get("settings")
    if not settings:
        fb_set("settings", {
            "bot_name":        "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎",
            "welcome_text":    "𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝙎𝙃𝙊𝙋 𝘽𝙊𝙏",
            "currency_symbol": "$",
            "currency_name":   "USD",
            "local_currency":  "BDT",
            "exchange_rate":   125,          # 1 USD = 125 BDT
            "referral_pct":    5.0,
            "deposit_open":    True,         # DEFAULT: OPEN
            "withdraw_open":   True,
            "min_deposit":     1.0,
            "min_withdraw":    2.0,
            "support_link":    "https://t.me/bd_top_admin",
            "admin_ids":       list(ADMIN_IDS),
            "force_join_enabled": True,
            "dev_name":        "@bd_top_admin",
            "dev_url":         "https://t.me/bd_top_admin",
        })
    else:
        # Guarantee deposit is open if not specified
        if "deposit_open" not in settings or settings.get("deposit_open") is False:
            fb_update("settings", {"deposit_open": True})
        if "admin_ids" not in settings:
            fb_update("settings", {"admin_ids": list(ADMIN_IDS)})
        if "force_join_enabled" not in settings:
            fb_update("settings", {"force_join_enabled": True})
        if "dev_name" not in settings:
            fb_update("settings", {"dev_name": "@bd_top_admin", "dev_url": "https://t.me/bd_top_admin"})

    if fb_get("payment_methods") is None:
        fb_set("payment_methods", {
            "bkash":   {"enabled": True,  "number": "01XXXXXXXXX", "name": "𝗕𝗸𝗮𝘀𝗵"},
            "nagad":   {"enabled": True,  "number": "01XXXXXXXXX", "name": "𝗡𝗮𝗴𝗮𝗱"},
            "rocket":  {"enabled": True,  "number": "01XXXXXXXXX", "name": "𝗥𝗼𝗰𝗸𝗲𝘁"},
            "binance": {"enabled": False, "address": "", "name": "𝗕𝗶𝗻𝗮𝗻𝗰𝗲 𝗨𝗦𝗗𝗧"},
        })

    if fb_get("check_data_links") is None:
        fb_set("check_data_links", {
            "link_1": {"title": "🌐 বট হোস্টিং প্ল্যাটফর্ম", "url": "https://render.com"},
            "link_2": {"title": "📺 বট রান করার টিউটোরিয়াল", "url": "https://youtube.com"},
            "link_3": {"title": "💬 অফিসিয়াল সাপোর্ট গ্রুপ", "url": "https://t.me/bd_top_admin"},
        })

    if fb_get("force_join_channels") is None:
        fb_set("force_join_channels", {
            "ch_1": {"id": "@bd_top_admin", "name": "Join=ಌ", "url": "https://t.me/bd_top_admin"},
            "ch_2": {"id": "@bd_top_admin", "name": "Join✧˖°", "url": "https://t.me/bd_top_admin"},
        })

    if fb_get("admins") is None:
        init_admins = {}
        for aid in ADMIN_IDS:
            init_admins[str(aid)] = {
                "id": aid,
                "name": ADMIN_USERNAME,
                "role": "owner",
                "added_at": datetime.now().isoformat()
            }
        fb_set("admins", init_admins)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONVERSATION STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(
    ADMIN_MENU, ADMIN_PRODUCTS, ADMIN_ADD_CAT_NAME, ADMIN_ADD_PROD_NAME,
    ADMIN_ADD_PROD_DESC, ADMIN_ADD_PROD_PRICE, ADMIN_ADD_PROD_STOCK,
    ADMIN_EDIT_PROD, ADMIN_SETTINGS_MENU, ADMIN_SET_FIELD,
    ADMIN_PAYMENT_MENU, ADMIN_PAY_FIELD,
    ADMIN_BROADCAST, ADMIN_MANAGE_USERS,
    DEPOSIT_CHOOSE_METHOD, DEPOSIT_ENTER_AMOUNT, DEPOSIT_ENTER_TXID,
    WITHDRAW_ENTER_AMOUNT, WITHDRAW_ENTER_METHOD, WITHDRAW_ENTER_ACCOUNT,
    BUY_CHOOSE_CAT, BUY_CHOOSE_PROD, BUY_CONFIRM,
) = range(23)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEXT STYLES  (𝙎𝙡𝙖𝙣𝙩𝙚𝙙 𝘽𝙤𝙡𝙙)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def sb(text: str) -> str:
    """Slanted Bold Unicode"""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    slanted_bold = (
        "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕"
        "𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯"
        "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    )
    result = ""
    for ch in text:
        idx = normal.find(ch)
        result += slanted_bold[idx] if idx != -1 else ch
    return result

def bold(text: str) -> str:
    return f"<b>{text}</b>"

def divider() -> str:
    return "━━━━━━━━━━━━━━━━━━━━━━━━━━"

def mini_divider() -> str:
    return "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER & ROLE HELPERS (RBAC)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_user(uid: int) -> dict:
    return fb_get(f"users/{uid}", {})

def ensure_user(update: Update) -> dict:
    uid = update.effective_user.id
    user = get_user(uid)
    if not user:
        referrer = None
        args = update.message.text.split() if update.message else []
        if len(args) > 1 and args[1].isdigit():
            referrer = int(args[1])
        user = {
            "id":         uid,
            "name":       update.effective_user.full_name,
            "username":   update.effective_user.username or "",
            "balance":    0.0,
            "joined":     datetime.now().isoformat(),
            "referrer":   referrer,
            "referrals":  0,
            "verified_referrals": 0,
            "total_earned": 0.0,
            "banned":     False,
        }
        fb_set(f"users/{uid}", user)
        # notify referrer
        if referrer and referrer != uid:
            ref_user = get_user(referrer)
            if ref_user:
                total = (ref_user.get("referrals") or 0) + 1
                fb_update(f"users/{referrer}", {"referrals": total})
    return user

def get_admin_role(uid: int) -> Optional[str]:
    if uid in ADMIN_IDS:
        return "owner"
    admins = fb_get("admins", {})
    if isinstance(admins, dict) and str(uid) in admins:
        return admins[str(uid)].get("role", "viewer")
    s = get_settings()
    extra_admins = s.get("admin_ids", [])
    if uid in extra_admins or str(uid) in extra_admins:
        return "manager"
    user = get_user(uid)
    if user and (user.get("is_admin") or user.get("role") == "admin"):
        return "manager"
    return None

def is_admin(uid: int) -> bool:
    return get_admin_role(uid) is not None

def is_owner(uid: int) -> bool:
    return get_admin_role(uid) == "owner"

def can_manage(uid: int) -> bool:
    return get_admin_role(uid) in ["owner", "manager"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FORCE JOIN HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_force_join_channels() -> dict:
    chans = fb_get("force_join_channels")
    if chans is None or not isinstance(chans, dict):
        return {}
    return chans

async def check_force_join(bot, user_id: int) -> list:
    s = get_settings()
    if not s.get("force_join_enabled", True):
        return []
    if is_admin(user_id):
        return []
    channels = get_force_join_channels()
    if not channels:
        return []
    not_joined = []
    for cid, ch in channels.items():
        if not isinstance(ch, dict):
            continue
        chat_target = ch.get("id") or ch.get("chat_id") or ch.get("username")
        if not chat_target:
            continue
        try:
            member = await bot.get_chat_member(chat_id=chat_target, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                not_joined.append({"key": cid, **ch})
        except Exception as e:
            logger.info(f"Force join check member exception for {chat_target}: {e}")
            not_joined.append({"key": cid, **ch})
    return not_joined

async def send_force_join_screen(target, not_joined: list, is_edit: bool = False):
    text = (
        f"💡 <b>Join All Channels to Continue</b>\n\n"
        f"Then click ✅ <b>Joined</b>"
    )
    buttons = []
    row = []
    for ch in not_joined:
        name = ch.get("name") or ch.get("title") or "Join ♕"
        url = ch.get("url") or f"https://t.me/{str(ch.get('id','')).replace('@','')}"
        btn = InlineKeyboardButton(name, url=url)
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Green verify button as in screenshot
    buttons.append([InlineKeyboardButton("☠️ verify 🍃 ☠️", callback_data="verify_force_join")])
    kb = InlineKeyboardMarkup(buttons)

    if is_edit and hasattr(target, "edit_message_text"):
        await target.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    elif hasattr(target, "reply_text"):
        await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    elif hasattr(target, "message"):
        await target.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

def get_settings() -> dict:
    return fb_get("settings", {})

def get_payment_methods() -> dict:
    return fb_get("payment_methods", {})

def format_amount(amount: float, settings: dict = None) -> str:
    if settings is None:
        settings = get_settings()
    sym = settings.get("currency_symbol", "$")
    rate = settings.get("exchange_rate", 125)
    local = settings.get("local_currency", "BDT")
    local_amt = round(amount * rate)
    return f"{sym}{amount:.2f} ({local_amt:,} {local})"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN MENU KEYBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main_menu_keyboard(uid: int = None) -> ReplyKeyboardMarkup:
    keys = []
    if uid and is_admin(uid):
        keys.append([KeyboardButton("⚙️ " + sb("ADMIN PANEL"))])
    keys.extend([
        [KeyboardButton(sb("BUY PRODUCT")),    KeyboardButton(sb("DEPOSIT MONEY"))],
        [KeyboardButton(sb("REFER")),           KeyboardButton(sb("MY PRODUCT"))],
        [KeyboardButton(sb("MY PROFILE")),      KeyboardButton(sb("CHECK DATA"))],
        [KeyboardButton(sb("SUPPORT")),         KeyboardButton("🆔 " + sb("MY ID"))],
        [KeyboardButton("ℹ️ " + sb("ABOUT"))],
    ])
    return ReplyKeyboardMarkup(keys, resize_keyboard=True, one_time_keyboard=False)

def home_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(
        "🏠 " + sb("Home"), callback_data="home")]])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  /id and /myid
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def my_id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.full_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "None"
    admin_status = "👑 <b>ADMIN ACCESS ACTIVE</b>" if is_admin(uid) else "👤 <i>Regular User</i>"

    text = (
        f"🆔 {bold(sb('USER IDENTIFICATION'))}\n"
        f"{divider()}\n"
        f"👤 {sb('Name:')} {name}\n"
        f"🏷️ {sb('Username:')} {username}\n"
        f"🆔 {sb('Telegram ID:')} <code>{uid}</code>\n"
        f"🔰 {sb('Status:')} {admin_status}\n"
        f"{divider()}\n"
    )
    if is_admin(uid):
        text += f"💡 {sb('You have full admin privileges. Type')} <b>/admin</b> {sb('to open Admin Panel!')}"
    else:
        text += (
            f"💡 {sb('To gain Admin access, copy your ID')} <code>{uid}</code>\n"
            f"{sb('and add it into Admin ID in your Bot Dashboard!')}"
        )

    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  /start
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    uid = update.effective_user.id
    if user.get("banned"):
        await update.message.reply_text("🚫 You are banned from this bot.")
        return

    # Check Force Join for non-admin users
    if not is_admin(uid):
        not_joined = await check_force_join(ctx.bot, uid)
        if not_joined:
            await send_force_join_screen(update, not_joined)
            return

    s = get_settings()
    bot_name = s.get("bot_name", "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎")
    admin_banner = f"\n👑 {bold('Admin Access Enabled')} — Use /admin or button below\n" if is_admin(uid) else ""

    text = (
        f"🔥 {bold('Hello Hey!')}\n\n"
        f"🌟 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 {bold(bot_name)}\n"
        f"{admin_banner}"
        f"{divider()}\n"
        f"⚡ {sb('Instant Delivery')}\n"
        f"🛡️ {sb('Secure Purchase')}\n"
        f"💎 {sb('Premium Quality')}\n"
        f"✅ {sb('Trusted Service')}\n"
        f"{divider()}\n\n"
        f"👋 {sb('Welcome to the Shop Menu!')} Select an option below:"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(uid)
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUY PRODUCT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def shop_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    categories = fb_get("categories", {})
    if not categories:
        text = (
            f"🛒 {bold(sb('PREMIUM SHOP CENTER'))}\n"
            f"{divider()}\n"
            f"⚡ Instant Delivery\n🛡️ Secure Purchase\n"
            f"💎 Premium Quality\n✅ Trusted Service\n"
            f"{divider()}\n\n"
            f"📂 {sb('No categories available yet.')}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")
        ]])
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.message.reply_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    s = get_settings()
    text = (
        f"🎯 {bold(sb('PREMIUM SHOP CENTER'))}\n"
        f"{divider()}\n"
        f"⚡ {sb('Instant Delivery')}\n"
        f"🛡️ {sb('Secure Purchase')}\n"
        f"💎 {sb('Premium Quality')}\n"
        f"✅ {sb('Trusted Service')}\n"
        f"{divider()}\n\n"
        f"📂 {sb('Select Product Category')}\n"
        f"Choose your favorite category from the buttons below ➡️"
    )
    buttons = []
    for cat_id, cat in categories.items():
        prods = cat.get("products", {})
        count = len(prods)
        buttons.append([InlineKeyboardButton(
            f"🎁 {sb(cat.get('name','?'))} ({count})",
            callback_data=f"cat_{cat_id}"
        )])
    buttons.append([InlineKeyboardButton(
        "🏠 " + sb("Home"), callback_data="home")])

    kb = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def show_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace("cat_", "")
    cat = fb_get(f"categories/{cat_id}", {})
    if not cat:
        await query.answer("Category not found!", show_alert=True)
        return

    products = cat.get("products", {})
    text = (
        f"📦 {bold(sb(cat.get('name','?')))}\n"
        f"{divider()}\n"
        f"🛍️ {sb('Available Products:')} {len(products)}\n"
        f"{sb('Select a product to purchase:')}\n"
        f"{divider()}"
    )
    buttons = []
    for pid, prod in products.items():
        s = get_settings()
        price_str = format_amount(prod.get("price", 0), s)
        buttons.append([InlineKeyboardButton(
            f"🎁 {sb(prod.get('name','?'))}",
            callback_data=f"prod_{cat_id}_{pid}"
        )])
    buttons.append([InlineKeyboardButton(
        "⬅️ " + sb("Back to Shop"), callback_data="shop")])

    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

async def show_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, cat_id, pid = query.data.split("_", 2)
    prod = fb_get(f"categories/{cat_id}/products/{pid}", {})
    if not prod:
        await query.answer("Product not found!", show_alert=True)
        return

    s = get_settings()
    price_str = format_amount(prod.get("price", 0), s)
    stock = prod.get("stock", 0)
    stock_status = f"✅ {sb('In Stock')} ({stock})" if stock > 0 else f"❌ {sb('Out of Stock')}"

    text = (
        f"🎯 {bold(sb('VIP PACKAGE DETAILS'))}\n"
        f"{divider()}\n"
        f"📦 {bold(prod.get('name','?'))}\n"
        f"{mini_divider()}\n"
        f"💰 {sb('Price:')} {bold(price_str)}\n"
        f"📊 {sb('Stock:')} {stock_status}\n"
    )
    if prod.get("is_file") or prod.get("file_name"):
        fname = prod.get("file_name", "Script / Bot Archive")
        text += f"📁 {sb('File:')} <code>{fname}</code> (Instant Auto-Delivery ⚡)\n"

    demo_link = prod.get("demo_link")
    if demo_link:
        text += f"🤖 {sb('Demo Bot:')} {demo_link}\n"

    if prod.get("description"):
        text += f"📝 {sb('Description:')}\n{prod.get('description')}\n"
    text += f"{divider()}"

    buttons = []
    # Demo bot link button if available
    if demo_link:
        durl = demo_link if demo_link.startswith("http") else (f"https://t.me/{demo_link[1:]}" if demo_link.startswith("@") else f"https://{demo_link}")
        buttons.append([InlineKeyboardButton("🤖 " + sb("Live Demo Bot") + " ↗️", url=durl)])

    if stock > 0:
        buttons.append([InlineKeyboardButton(
            f"💎 {sb('Buy Now')} — {price_str}",
            callback_data=f"buy_{cat_id}_{pid}")])
    buttons.append([InlineKeyboardButton(
        "⬅️ " + sb("Back to Category"), callback_data=f"cat_{cat_id}")])

    # If product has an image/photo attached
    img = prod.get("image")
    if img:
        try:
            # delete previous message to post clean photo card
            chat_id = query.message.chat_id
            await query.message.delete()
            await ctx.bot.send_photo(
                chat_id=chat_id,
                photo=img,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        except Exception:
            pass

    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

async def confirm_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    _, cat_id, pid = query.data.split("_", 2)

    user = get_user(uid)
    prod = fb_get(f"categories/{cat_id}/products/{pid}", {})
    if not prod:
        await query.answer("Product not found!", show_alert=True)
        return

    s = get_settings()
    price = prod.get("price", 0)
    balance = user.get("balance", 0.0)

    if balance < price:
        short = format_amount(price - balance, s)
        text_insufficient = (
            f"❌ {bold(sb('Insufficient Balance!'))}\n"
            f"{divider()}\n"
            f"💰 {sb('Your Balance:')} {format_amount(balance, s)}\n"
            f"💎 {sb('Required:')} {format_amount(price, s)}\n"
            f"📉 {sb('Shortage:')} {bold(short)}\n"
            f"{divider()}\n\n"
            f"💡 {sb('Please deposit money to continue.')}"
        )
        kb_insufficient = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 " + sb("Deposit Now"), callback_data="deposit"),
            InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home"),
        ]])
        if query.message.photo:
            await query.message.delete()
            await ctx.bot.send_message(
                uid, text_insufficient, parse_mode=ParseMode.HTML, reply_markup=kb_insufficient)
        else:
            await query.edit_message_text(
                text_insufficient, parse_mode=ParseMode.HTML, reply_markup=kb_insufficient)
        return

    # check stock
    stock = prod.get("stock", 0)
    items = prod.get("items", [])
    if stock <= 0 or not items:
        await query.answer("Out of stock!", show_alert=True)
        return

    # deduct balance & deliver item
    item = items[0]
    is_file_prod = prod.get("is_file", False) or (isinstance(item, str) and item.startswith("FILE::"))
    
    # For file scripts with unlimited stock, keep item available; otherwise pop item
    if is_file_prod:
        remaining_items = items  # keep file in stock
        new_stock = stock - 1 if stock > 1 else 999
    else:
        remaining_items = items[1:]
        new_stock = max(0, stock - 1)

    new_balance = round(balance - price, 4)
    fb_update(f"users/{uid}", {"balance": new_balance})
    fb_update(f"categories/{cat_id}/products/{pid}", {
        "stock": new_stock,
        "items": remaining_items,
    })

    # determine file details if any
    file_id = None
    file_name = None
    if isinstance(item, str) and item.startswith("FILE::"):
        parts = item.split("::")
        if len(parts) >= 3:
            file_id = parts[1]
            file_name = parts[2]
    elif prod.get("file_id"):
        file_id = prod.get("file_id")
        file_name = prod.get("file_name", "script.zip")

    # log purchase
    purchase_data = {
        "uid":       uid,
        "name":      query.from_user.full_name,
        "prod":      prod.get("name"),
        "cat_id":    cat_id,
        "pid":       pid,
        "price":     price,
        "item":      item,
        "is_file":   bool(file_id),
        "file_id":   file_id,
        "file_name": file_name,
        "time":      datetime.now().isoformat(),
    }
    fb_push("purchases", purchase_data)
    purch_ref = fb_push(f"users/{uid}/products", purchase_data)
    purch_key = purch_ref.key if purch_ref else "item"

    # Send success response
    success_text = (
        f"✅ {bold(sb('Purchase Successful!'))}\n"
        f"{divider()}\n"
        f"📦 {sb('Product:')} {bold(prod.get('name','?'))}\n"
        f"💰 {sb('Paid:')} {format_amount(price, s)}\n"
        f"💳 {sb('Remaining Balance:')} {format_amount(new_balance, s)}\n"
        f"{divider()}\n"
    )

    if file_id:
        success_text += (
            f"🎁 {bold(sb('Your Script / File is delivering below! ⬇️'))}\n"
            f"📁 <code>{file_name}</code>\n"
            f"⚡ <i>File attached directly below. You can also re-download anytime from 'MY PRODUCT'.</i>"
        )
    else:
        success_text += (
            f"🎁 {bold(sb('Your Item / Content:'))}\n"
            f"<code>{item}</code>"
        )

    if query.message.photo:
        await query.message.delete()
        await ctx.bot.send_message(
            uid, success_text, parse_mode=ParseMode.HTML, reply_markup=home_inline())
    else:
        await query.edit_message_text(
            success_text, parse_mode=ParseMode.HTML, reply_markup=home_inline())

    # Send document file if product is a file
    if file_id:
        try:
            await ctx.bot.send_document(
                chat_id=uid,
                document=file_id,
                filename=file_name or "bot_script.zip",
                caption=(
                    f"🎁 <b>{prod.get('name')}</b>\n"
                    f"⚡ Instant Auto-Delivery\n"
                    f"✨ Thank you for your purchase!"
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send document to user {uid}: {e}")

    # notify admin
    try:
        await ctx.bot.send_message(
            ADMIN_ID,
            f"🛒 {bold('New Purchase!')}\n"
            f"👤 User: {query.from_user.full_name} ({uid})\n"
            f"📦 Product: {prod.get('name')}\n"
            f"💰 Price: {format_amount(price, s)}"
            + (f"\n📁 File: {file_name}" if file_name else ""),
            parse_mode=ParseMode.HTML
        )
    except:
        pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MY PROFILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def my_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    s = get_settings()
    balance = user.get("balance", 0.0)
    referrals = user.get("referrals", 0)
    verified = user.get("verified_referrals", 0)
    earned = user.get("total_earned", 0.0)
    joined = user.get("joined", "N/A")[:10]

    text = (
        f"👤 {bold(sb('MY PROFILE'))}\n"
        f"{divider()}\n"
        f"🆔 {sb('User ID:')} <code>{uid}</code>\n"
        f"📛 {sb('Name:')} {update.effective_user.full_name}\n"
        f"📅 {sb('Joined:')} {joined}\n"
        f"{mini_divider()}\n"
        f"💰 {sb('Balance:')} {bold(format_amount(balance, s))}\n"
        f"👥 {sb('Total Referrals:')} {referrals}\n"
        f"✅ {sb('Verified Referrals:')} {verified}\n"
        f"💎 {sb('Total Earned:')} {format_amount(earned, s)}\n"
        f"{divider()}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")
    ]])

    if update.callback_query:
        if update.callback_query.message.photo:
            await update.callback_query.message.delete()
            await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MY PRODUCTS & FILE RE-DOWNLOAD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def my_products(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    products = fb_get(f"users/{uid}/products", {})

    if not products:
        text = (
            f"📦 {bold(sb('MY PRODUCTS'))}\n"
            f"{divider()}\n"
            f"💎 " + sb("You don't have any products yet.") + "\n"
            f"🛍️ {sb('Purchase products from the shop to see them here.')}\n"
            f"{divider()}"
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 " + sb("Buy Products"), callback_data="shop")],
            [InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")],
        ])
    else:
        text = f"📦 {bold(sb('MY PRODUCTS & SCRIPTS'))}\n{divider()}\n"
        buttons = []
        for pkey, prod in list(products.items())[-8:]:  # show last 8
            ptime = prod.get("time","")[:10]
            pname = prod.get("name","Product")
            file_id = prod.get("file_id")
            item_raw = str(prod.get("item",""))

            if not file_id and item_raw.startswith("FILE::"):
                parts = item_raw.split("::")
                if len(parts) >= 2:
                    file_id = parts[1]

            text += (
                f"🎁 {bold(pname)}\n"
                f"   📅 {ptime}\n"
            )
            if file_id or prod.get("is_file"):
                fname = prod.get("file_name") or "script_archive"
                text += f"   📁 <code>{fname}</code> (File)\n"
                buttons.append([InlineKeyboardButton(f"📥 Download: {pname[:20]}", callback_data=f"dl_{pkey}")])
            else:
                text += f"   <code>{item_raw}</code>\n"
            text += f"{mini_divider()}\n"

        buttons.append([InlineKeyboardButton("🛒 " + sb("Buy More"), callback_data="shop")])
        buttons.append([InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")])
        kb = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        if update.callback_query.message.photo:
            await update.callback_query.message.delete()
            await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def download_purchased_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    pkey = query.data.replace("dl_", "")
    purch = fb_get(f"users/{uid}/products/{pkey}", {})
    if not purch:
        await query.answer("Product record not found!", show_alert=True)
        return

    file_id = purch.get("file_id")
    file_name = purch.get("file_name", "bot_script.zip")
    item_raw = str(purch.get("item", ""))

    if not file_id and item_raw.startswith("FILE::"):
        parts = item_raw.split("::")
        if len(parts) >= 3:
            file_id = parts[1]
            file_name = parts[2]

    if not file_id:
        await query.answer("No downloadable file attached to this product.", show_alert=True)
        return

    try:
        await ctx.bot.send_document(
            chat_id=uid,
            document=file_id,
            filename=file_name,
            caption=(
                f"📥 <b>{purch.get('name', 'Script File')}</b>\n"
                f"⚡ Re-download from My Products\n"
                f"✨ Instant Delivery"
            ),
            parse_mode=ParseMode.HTML
        )
        await query.answer("File sent successfully! Check below.", show_alert=True)
    except Exception as e:
        logger.error(f"Error re-sending file {file_id}: {e}")
        await query.answer("Failed to send file. Please contact support.", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REFER & EARN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def refer_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    s = get_settings()
    bot_info = await ctx.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    ref_pct = s.get("referral_pct", 5.0)
    referrals = user.get("referrals", 0)
    verified = user.get("verified_referrals", 0)
    earned = user.get("total_earned", 0.0)

    text = (
        f"🎁 {bold(sb('REFER & EARN'))}\n"
        f"{divider()}\n"
        f"🔗 {sb('YOUR LINK:')}\n"
        f"{ref_link}\n"
        f"{divider()}\n"
        f"👥 {sb('Your Referral Stats:')}\n"
        f"📊 {sb('Total Referrals:')} {referrals}\n"
        f"✅ {sb('Verified Referrals:')} {verified}\n"
        f"💰 {sb('Total Earnings:')} {format_amount(earned, s)}\n"
        f"{divider()}\n"
        f"💎 {bold(sb('COMMISSION:'))} {ref_pct}% {sb('ON DEPOSIT')}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")
    ]])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEPOSIT MONEY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def deposit_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_settings()
    if not s.get("deposit_open", False):
        text = (
            f"🚫 {bold(sb('DEPOSIT SYSTEM CLOSED!'))}\n"
            f"{divider()}\n"
            f"⚠️ {sb('Sorry, the deposit system is currently offline for maintenance.')}\n"
            f"{divider()}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 " + sb("Back to Home"), callback_data="home")
        ]])
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.message.reply_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    methods = get_payment_methods()
    enabled = {k: v for k, v in methods.items() if v.get("enabled")}
    if not enabled:
        text = f"❌ {bold(sb('No payment methods available.'))}"
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 " + sb("Back to Home"), callback_data="home")
        ]])
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=kb)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    sym = s.get("currency_symbol","$")
    rate = s.get("exchange_rate", 125)
    local = s.get("local_currency","BDT")
    min_dep = s.get("min_deposit", 1.0)

    text = (
        f"💳 {bold(sb('DEPOSIT MONEY'))}\n"
        f"{divider()}\n"
        f"💰 {sb('Min Deposit:')} {sym}{min_dep:.2f} ({int(min_dep*rate)} {local})\n"
        f"📈 {sb('Rate:')} 1 {s.get('currency_name','USD')} = {rate} {local}\n"
        f"{divider()}\n"
        f"📌 {sb('Select Payment Method:')}"
    )
    buttons = []
    for key, pm in enabled.items():
        buttons.append([InlineKeyboardButton(
            f"💳 {pm.get('name','?')}",
            callback_data=f"dep_{key}"
        )])
    buttons.append([InlineKeyboardButton(
        "🏠 " + sb("Back to Home"), callback_data="home")])

    kb = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def deposit_method_chosen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method_key = query.data.replace("dep_","")
    methods = get_payment_methods()
    pm = methods.get(method_key, {})
    s = get_settings()
    rate = s.get("exchange_rate", 125)
    local = s.get("local_currency","BDT")

    number = pm.get("number") or pm.get("address","")
    text = (
        f"💳 {bold(sb(pm.get('name','?')))}\n"
        f"{divider()}\n"
        f"📱 {sb('Send To:')} <code>{number}</code>\n"
        f"📊 {sb('Rate:')} 1 {s.get('currency_name','USD')} = {rate} {local}\n"
        f"{divider()}\n"
        f"✏️ {sb('Enter amount in')} {local} {sb('(e.g. 500):')}"
    )
    ctx.user_data["dep_method"] = method_key
    ctx.user_data["dep_number"] = number
    ctx.user_data["dep_name"]   = pm.get("name","")
    ctx.user_data["awaiting"]   = "deposit_amount"

    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ " + sb("Cancel"), callback_data="deposit")
        ]]))

async def deposit_handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    awaiting = ctx.user_data.get("awaiting")
    if awaiting == "deposit_amount":
        text = update.message.text.strip()
        s = get_settings()
        rate = s.get("exchange_rate", 125)
        local = s.get("local_currency","BDT")
        min_dep = s.get("min_deposit", 1.0)
        min_local = int(min_dep * rate)
        try:
            amount_local = float(text)
            if amount_local < min_local:
                await update.message.reply_text(
                    f"❌ {sb('Minimum deposit is')} {min_local} {local}")
                return
            amount_usd = round(amount_local / rate, 4)
            ctx.user_data["dep_amount_local"] = amount_local
            ctx.user_data["dep_amount_usd"]   = amount_usd
            ctx.user_data["awaiting"]          = "deposit_txid"
            sym = s.get("currency_symbol","$")
            await update.message.reply_text(
                f"✅ {sb('Amount:')} {amount_local} {local} = {sym}{amount_usd:.4f}\n\n"
                f"📝 {bold(sb('Now enter your Transaction ID / TxHash:'))}",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text(f"❌ {sb('Please enter a valid number.')}")

    elif awaiting == "deposit_txid":
        txid = update.message.text.strip()
        uid  = update.effective_user.id
        s    = get_settings()
        ctx.user_data["awaiting"] = None

        ref = fb_push("deposits", {
            "uid":    uid,
            "name":   update.effective_user.full_name,
            "method": ctx.user_data.get("dep_method"),
            "amount_local": ctx.user_data.get("dep_amount_local"),
            "amount_usd":   ctx.user_data.get("dep_amount_usd"),
            "txid":   txid,
            "status": "pending",
            "time":   datetime.now().isoformat(),
        })
        dep_id = ref.key if ref else "N/A"
        sym = s.get("currency_symbol","$")
        local = s.get("local_currency","BDT")
        rate  = s.get("exchange_rate",125)

        await update.message.reply_text(
            f"⏳ {bold(sb('Deposit Request Submitted!'))}\n"
            f"{divider()}\n"
            f"🆔 {sb('Deposit ID:')} <code>{dep_id}</code>\n"
            f"💰 {sb('Amount:')} {ctx.user_data.get('dep_amount_local')} {local} "
            f"= {sym}{ctx.user_data.get('dep_amount_usd'):.4f}\n"
            f"📱 {sb('Method:')} {ctx.user_data.get('dep_name')}\n"
            f"🧾 {sb('TxID:')} <code>{txid}</code>\n"
            f"{divider()}\n"
            f"✅ {sb('Admin will verify and add balance soon.')}",
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard()
        )

        # notify admin
        try:
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"adep_ok_{dep_id}_{uid}_{ctx.user_data.get('dep_amount_usd')}"),
                InlineKeyboardButton("❌ Reject",  callback_data=f"adep_no_{dep_id}_{uid}"),
            ]])
            await ctx.bot.send_message(
                ADMIN_ID,
                f"💳 {bold('New Deposit Request!')}\n"
                f"👤 User: {update.effective_user.full_name} ({uid})\n"
                f"💰 Amount: {ctx.user_data.get('dep_amount_local')} {local} "
                f"= {sym}{ctx.user_data.get('dep_amount_usd'):.4f}\n"
                f"📱 Method: {ctx.user_data.get('dep_name')}\n"
                f"🧾 TxID: <code>{txid}</code>\n"
                f"🆔 Dep ID: <code>{dep_id}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        except:
            pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SUPPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def support_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_settings()
    support_link = s.get("support_link", "https://t.me/bd_top_admin")
    text = f"🤖 {sb('Contact us for any help:')}"
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🆘 " + sb("SUPPORT"), url=support_link)
    ]])
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CHECK DATA (Custom Direct Link Buttons)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    links = fb_get("check_data_links", {})
    s = get_settings()
    bot_name = s.get("bot_name", "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎")

    text = (
        f"🌐 {bold(sb('CHECK DATA & IMPORTANT LINKS'))}\n"
        f"{divider()}\n"
        f"📌 <b>নিচে প্রয়োজনীয় সকল সাইট ও সার্ভিসের সরাসরি লিংক দেওয়া হলো:</b>\n"
        f"<i>(যেকোনো বাটনে ক্লিক করলেই সরাসরি কাঙ্খিত লিংকটি ওপেন হয়ে যাবে)</i>\n"
        f"{divider()}"
    )

    buttons = []
    if links and isinstance(links, dict):
        for lid, linfo in links.items():
            if not isinstance(linfo, dict):
                continue
            title = linfo.get("title", "🔗 লিংক")
            url = linfo.get("url", "https://t.me")
            buttons.append([InlineKeyboardButton(f"👉 {title}", url=url)])
    else:
        text += f"\n\n⚠️ <i>কোনো লিংক বা ডাটা বাটন এখনও যোগ করা হয়নি। এডমিন প্যানেল থেকে তৈরি করতে পারেন।</i>"

    buttons.append([InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")])
    kb = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HOME callback
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def home_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    s = get_settings()
    bot_name = s.get("bot_name","𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎")
    text = (
        f"🌟 {bold(bot_name)}\n"
        f"{divider()}\n"
        f"👋 {sb('Welcome to the Shop Menu!')} Select an option below:"
    )
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ██████████  ADMIN PANEL  ██████████
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not is_admin(uid):
            if update.message:
                await update.message.reply_text("🚫 Admin only!")
            elif update.callback_query:
                await update.callback_query.answer("🚫 Admin only!", show_alert=True)
            return
        return await func(update, ctx)
    return wrapper

def manager_or_owner(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not can_manage(uid):
            msg = "⚠️ আপনি শুধুমাত্র ভিউয়ার (View Only) এডমিন। এডিট বা পরিবর্তন করার অনুমতি নেই।"
            if update.message:
                await update.message.reply_text(msg)
            elif update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            return
        return await func(update, ctx)
    return wrapper

def owner_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not is_owner(uid):
            msg = "🚫 শুধুমাত্র Owner এডমিন এই পরিবর্তনটি করতে পারবেন।"
            if update.message:
                await update.message.reply_text(msg)
            elif update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            return
        return await func(update, ctx)
    return wrapper

@admin_only
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    role = get_admin_role(uid)
    role_badge = "👑 OWNER" if role == "owner" else ("🛠️ MANAGER" if role == "manager" else "👁️ VIEW ONLY")
    s = get_settings()
    fj_status = "✅ চালু" if s.get("force_join_enabled", True) else "❌ বন্ধ"
    
    text = (
        f"⚙️ {bold(sb('ADMIN CONTROL CENTER'))}\n"
        f"{divider()}\n"
        f"🤖 {sb('Full Bot Management System')}\n"
        f"👤 {sb('Admin:')} {update.effective_user.full_name} (@{update.effective_user.username or 'N/A'})\n"
        f"🔰 {sb('Your Role:')} <b>{role_badge}</b>\n"
        f"📢 {sb('Force Join Status:')} <b>{fj_status}</b>\n"
        f"{divider()}\n"
        f"📌 {sb('Select a section to manage:')}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 " + sb("Manage Products"),    callback_data="adm_products"),
         InlineKeyboardButton("👥 " + sb("Manage Users"),       callback_data="adm_users")],
        [InlineKeyboardButton("📢 Force Join চ্যানেল কন্ট্রোল",  callback_data="adm_forcejoin"),
         InlineKeyboardButton("👑 এডমিন ও রোল কন্ট্রোল",       callback_data="adm_roles")],
        [InlineKeyboardButton("💳 " + sb("Deposits"),           callback_data="adm_deposits"),
         InlineKeyboardButton("📤 " + sb("Withdrawals"),        callback_data="adm_withdrawals")],
        [InlineKeyboardButton("⚙️ " + sb("Bot Settings"),       callback_data="adm_settings"),
         InlineKeyboardButton("💰 " + sb("Payment Methods"),    callback_data="adm_payments")],
        [InlineKeyboardButton("🔗 CHECK DATA বাটন কন্ট্রোল",     callback_data="adm_checkdata")],
        [InlineKeyboardButton("🔥 Firebase স্ট্যাটাস ও সিঙ্ক",    callback_data="adm_fbstatus"),
         InlineKeyboardButton("📊 " + sb("Statistics"),         callback_data="adm_stats")],
        [InlineKeyboardButton("📢 " + sb("Broadcast"),          callback_data="adm_broadcast"),
         InlineKeyboardButton("🎁 " + sb("Add Balance"),        callback_data="adm_addbal")],
        [InlineKeyboardButton("⛔ " + sb("Ban / Unban User"),   callback_data="adm_ban"),
         InlineKeyboardButton("🏠 " + sb("Close Panel"),        callback_data="home")],
    ])
    if update.message:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ─── ADMIN: PRODUCTS ─────────────────────────────────────────
@admin_only
async def adm_products(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categories = fb_get("categories", {})
    text = (
        f"🛒 {bold(sb('MANAGE PRODUCTS'))}\n"
        f"{divider()}\n"
        f"📂 {sb('Total Categories:')} {len(categories)}\n"
        f"{divider()}"
    )
    buttons = []
    for cat_id, cat in categories.items():
        prods = cat.get("products",{})
        buttons.append([InlineKeyboardButton(
            f"📂 {cat.get('name','?')} ({len(prods)} prods)",
            callback_data=f"adm_cat_{cat_id}"
        )])
    buttons += [
        [InlineKeyboardButton("➕ " + sb("Add Category"),  callback_data="adm_addcat"),
         InlineKeyboardButton("🗑️ " + sb("Del Category"),  callback_data="adm_delcat")],
        [InlineKeyboardButton("⬅️ " + sb("Back"),          callback_data="adm_panel")],
    ]
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

@admin_only
async def adm_category_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace("adm_cat_","")
    cat = fb_get(f"categories/{cat_id}", {})
    products = cat.get("products",{})
    text = (
        f"📂 {bold(cat.get('name','?'))}\n"
        f"{divider()}\n"
        f"🎁 {sb('Products:')} {len(products)}\n"
        f"{divider()}"
    )
    buttons = []
    for pid, prod in products.items():
        stock = prod.get("stock",0)
        buttons.append([InlineKeyboardButton(
            f"🎁 {prod.get('name','?')} | Stock: {stock}",
            callback_data=f"adm_prod_{cat_id}_{pid}"
        )])
    buttons += [
        [InlineKeyboardButton("➕ " + sb("Add Product"),   callback_data=f"adm_addprod_{cat_id}"),
         InlineKeyboardButton("⬅️ " + sb("Back"),          callback_data="adm_products")],
    ]
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

@admin_only
async def adm_prod_detail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("adm_prod_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    cat = fb_get(f"categories/{cat_id}", {})
    cat_name = cat.get("name", cat_id)
    prod = fb_get(f"categories/{cat_id}/products/{pid}", {})
    if not prod:
        await query.answer("❌ Product not found!", show_alert=True)
        return

    s = get_settings()
    rate = s.get("exchange_rate", 125)
    local_sym = s.get("local_currency", "৳")
    price_val = float(prod.get("price", 0))
    local_price = round(price_val * rate, 2)

    p_name = prod.get("name", "N/A")
    demo_link = prod.get("demo_link") or "—"
    entry_file = prod.get("entry_file") or "main.py"
    source_file = prod.get("file_name") or ("File Attached" if prod.get("file_id") else "—")
    dl_count = prod.get("downloads", 0)
    is_hidden = prod.get("hidden", False)
    visibility_str = "🔴 হাইড (Hidden)" if is_hidden else "🟢 সক্রিয় (Active)"
    description = prod.get("description") or "—"

    text = (
        f"⚙️ <b>স্ক্রিপ্ট ডিটেইলস ও এডিটর</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• <b>নাম:</b> {p_name}\n"
        f"• <b>ক্যাটাগরি:</b> {cat_name}\n"
        f"• <b>মূল্য:</b> {price_val}$ ({local_price} {local_sym})\n"
        f"• <b>ডেমো লিংক:</b> {demo_link}\n"
        f"• <b>মেইন এন্ট্রি ফাইল:</b> {entry_file}\n"
        f"• <b>সোর্স ফাইল:</b> {source_file}\n"
        f"• <b>ডাউনলোড সংখ্যা:</b> {dl_count} বার\n"
        f"• <b>ভিজিবিলিটি:</b> {visibility_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>বিবরণ:</b>\n"
        f"{description}"
    )

    vis_label = "👁️ স্ট্যাটাস: শো করুন" if is_hidden else "👁️ স্ট্যাটাস: হাইড করুন"

    buttons = [
        [
            InlineKeyboardButton("✏️ নাম পরিবর্তন", callback_data=f"aedt_name_{cat_id}_{pid}"),
            InlineKeyboardButton("💰 মূল্য পরিবর্তন", callback_data=f"aedt_price_{cat_id}_{pid}")
        ],
        [
            InlineKeyboardButton("📁 ক্যাটাগরি বদলান", callback_data=f"aedt_cat_{cat_id}_{pid}"),
            InlineKeyboardButton("🔗 ডেমো লিংক এডিট", callback_data=f"aedt_demo_{cat_id}_{pid}")
        ],
        [
            InlineKeyboardButton("📝 ডেসক্রিপশন এডিট", callback_data=f"aedt_desc_{cat_id}_{pid}"),
            InlineKeyboardButton("🚀 এন্ট্রি ফাইল বদলান", callback_data=f"aedt_entry_{cat_id}_{pid}")
        ],
        [
            InlineKeyboardButton("📤 নতুন ফাইল আপলোড", callback_data=f"aedt_file_{cat_id}_{pid}"),
            InlineKeyboardButton("📥 টেস্ট ডাউনলোড", callback_data=f"aedt_testdl_{cat_id}_{pid}")
        ],
        [
            InlineKeyboardButton(vis_label, callback_data=f"aedt_vis_{cat_id}_{pid}"),
            InlineKeyboardButton("🗑️ স্ক্রিপ্ট ডিলিট", callback_data=f"adm_delprod_{cat_id}_{pid}")
        ],
        [
            InlineKeyboardButton("⬅️ ব্যাক", callback_data=f"adm_cat_{cat_id}")
        ]
    ]

    try:
        await query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception:
        await query.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

# ─── ADMIN: PRODUCT EDITORS (FROM SCREENSHOT) ────────────────
@admin_only
async def aedt_start_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_name_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_name_{cat_id}_{pid}"
    await query.edit_message_text(
        f"✏️ <b>স্ক্রিপ্ট / প্রোডাক্টের নাম পরিবর্তন</b>\n{divider()}\n"
        f"📝 অনুগ্রহ করে নতুন নামটি লিখে পাঠান:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_start_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_price_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_price_{cat_id}_{pid}"
    s = get_settings()
    rate = s.get("exchange_rate", 125)
    local_sym = s.get("local_currency", "BDT")
    await query.edit_message_text(
        f"💰 <b>মূল্য পরিবর্তন</b>\n{divider()}\n"
        f"💵 নতুন মূল্য USD তে লিখুন (যেমন: <code>5.0</code> বা <code>2.5</code>):\n"
        f"<i>(বর্তমান রেট: 1 USD = {rate} {local_sym})</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_start_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_cat_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    categories = fb_get("categories", {})
    buttons = []
    for c_id, c in categories.items():
        if c_id != cat_id:
            buttons.append([InlineKeyboardButton(
                f"📁 {c.get('name', c_id)}", callback_data=f"aedt_moveto_{cat_id}_{pid}_{c_id}"
            )])
    buttons.append([InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")])
    await query.edit_message_text(
        f"📁 <b>ক্যাটাগরি বদলান</b>\n{divider()}\n"
        f"এই প্রোডাক্টটি কোন ক্যাটাগরিতে সরাতে চান তা সিলেক্ট করুন:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

@admin_only
async def aedt_move_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_moveto_","").split("_", 2)
    from_cat, pid, to_cat = parts[0], parts[1], parts[2]
    prod = fb_get(f"categories/{from_cat}/products/{pid}", {})
    if prod:
        fb_set(f"categories/{to_cat}/products/{pid}", prod)
        fb_delete(f"categories/{from_cat}/products/{pid}")
        await query.answer("✅ ক্যাটাগরি সফলভাবে পরিবর্তন হয়েছে!", show_alert=True)
    query.data = f"adm_prod_{to_cat}_{pid}"
    await adm_prod_detail(update, ctx)

@admin_only
async def aedt_start_demo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_demo_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_demo_{cat_id}_{pid}"
    await query.edit_message_text(
        f"🔗 <b>ডেমো লিংক এডিট</b>\n{divider()}\n"
        f"🤖 নতুন ডেমো লিংক বা @ইউজারনেম লিখুন:\n"
        f"<i>(লিংক রিমুভ করতে <code>clear</code> লিখে পাঠান)</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_start_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_desc_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_desc_{cat_id}_{pid}"
    await query.edit_message_text(
        f"📝 <b>ডেসক্রিপশন এডিট</b>\n{divider()}\n"
        f"✏️ প্রোডাক্টের নতুন বিবরণ বা ফিচারসমূহ লিখে পাঠান:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_start_entry(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_entry_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_entry_{cat_id}_{pid}"
    await query.edit_message_text(
        f"🚀 <b>মেইন এন্ট্রি ফাইল বদলান</b>\n{divider()}\n"
        f"📄 মেইন স্ক্রিপ্ট ফাইলের নাম লিখুন:\n"
        f"<i>(যেমন: <code>main.py</code>, <code>server.js</code>, <code>bot.py</code>, <code>index.php</code>)</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_start_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_file_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"aedt_file_{cat_id}_{pid}"
    await query.edit_message_text(
        f"📤 <b>নতুন ফাইল আপলোড / স্টক আপডেট</b>\n{divider()}\n"
        f"📁 <b>Option 1:</b> সরাসরি কোনো ফাইল (<code>.zip</code>, <code>.py</code>, <code>.js</code>, <code>.rar</code>) টেলিগ্রামে সেন্ড করুন।\n\n"
        f"📝 <b>Option 2:</b> টেক্সট স্টক এক লাইন পর পর লিখে পাঠান।",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ বাতিল", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def aedt_test_download(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_testdl_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    prod = fb_get(f"categories/{cat_id}/products/{pid}", {})
    if not prod:
        await query.answer("Product not found!", show_alert=True)
        return

    pname = prod.get("name", pid)
    file_id = prod.get("file_id")
    file_name = prod.get("file_name", f"{pid}.zip")
    items = prod.get("items", [])

    if file_id:
        try:
            await ctx.bot.send_document(
                chat_id=query.from_user.id,
                document=file_id,
                filename=file_name,
                caption=f"📥 <b>[টেস্ট ডাউনলোড]</b> {pname}\n🚀 <i>এন্ট্রি ফাইল:</i> <code>{prod.get('entry_file', 'main.py')}</code>",
                parse_mode=ParseMode.HTML
            )
            await query.answer("✅ টেস্ট ফাইল পাঠানো হয়েছে!", show_alert=True)
            return
        except Exception as e:
            logger.error(f"Test download error: {e}")

    for it in items:
        if isinstance(it, str) and it.startswith("FILE::"):
            _, fid, fn = it.split("::", 2)
            try:
                await ctx.bot.send_document(
                    chat_id=query.from_user.id,
                    document=fid,
                    filename=fn,
                    caption=f"📥 <b>[টেস্ট ডাউনলোড]</b> {pname}",
                    parse_mode=ParseMode.HTML
                )
                await query.answer("✅ টেস্ট ফাইল পাঠানো হয়েছে!", show_alert=True)
                return
            except Exception as e:
                pass

    if items:
        preview_text = "\n".join(items[:5])
        await ctx.bot.send_message(
            query.from_user.id,
            f"📥 <b>[টেস্ট ডাটা প্রিভিউ]</b> {pname}\n{divider()}\n<code>{preview_text}</code>",
            parse_mode=ParseMode.HTML
        )
        await query.answer("✅ টেস্ট ডাটা পাঠানো হয়েছে!", show_alert=True)
    else:
        await query.answer("⚠️ কোনো ফাইল বা স্টক যুক্ত করা নেই!", show_alert=True)

@admin_only
async def aedt_toggle_visibility(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.replace("aedt_vis_","").split("_",1)
    cat_id, pid = parts[0], parts[1]
    prod = fb_get(f"categories/{cat_id}/products/{pid}", {})
    is_hidden = prod.get("hidden", False)
    fb_update(f"categories/{cat_id}/products/{pid}", {"hidden": not is_hidden})
    status_msg = "🔴 প্রোডাক্টটি এখন হাইড করা হয়েছে (ইউজার শপে দেখাবে না)" if not is_hidden else "🟢 প্রোডাক্টটি এখন সক্রিয় করা হয়েছে (ইউজার শপে দেখাবে)"
    await query.answer(status_msg, show_alert=True)
    query.data = f"adm_prod_{cat_id}_{pid}"
    await adm_prod_detail(update, ctx)

# ─── ADMIN: SETTINGS ─────────────────────────────────────────
@admin_only
async def adm_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    s = get_settings()
    text = (
        f"⚙️ {bold(sb('BOT SETTINGS'))}\n"
        f"{divider()}\n"
        f"🤖 {sb('Bot Name:')} {s.get('bot_name','')}\n"
        f"💱 {sb('Currency:')} {s.get('currency_name','')} ({s.get('currency_symbol','')})\n"
        f"🏦 {sb('Local Currency:')} {s.get('local_currency','')}\n"
        f"📈 {sb('Exchange Rate:')} {s.get('exchange_rate','')}\n"
        f"💳 {sb('Deposit Open:')} {'✅' if s.get('deposit_open') else '❌'}\n"
        f"📤 {sb('Withdraw Open:')} {'✅' if s.get('withdraw_open') else '❌'}\n"
        f"⬇️ {sb('Min Deposit:')} {s.get('min_deposit','')}\n"
        f"⬆️ {sb('Min Withdraw:')} {s.get('min_withdraw','')}\n"
        f"🔗 {sb('Support Link:')} {s.get('support_link','')}\n"
        f"🎁 {sb('Referral %:')} {s.get('referral_pct',5)}%\n"
        f"{divider()}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ " + sb("Bot Name"),      callback_data="aset_bot_name"),
         InlineKeyboardButton("✏️ " + sb("Welcome Text"),  callback_data="aset_welcome_text")],
        [InlineKeyboardButton("✏️ " + sb("Currency Name"), callback_data="aset_currency_name"),
         InlineKeyboardButton("✏️ " + sb("Currency Symbol"),callback_data="aset_currency_symbol")],
        [InlineKeyboardButton("✏️ " + sb("Local Currency"),callback_data="aset_local_currency"),
         InlineKeyboardButton("✏️ " + sb("Exchange Rate"), callback_data="aset_exchange_rate")],
        [InlineKeyboardButton("✏️ " + sb("Min Deposit"),   callback_data="aset_min_deposit"),
         InlineKeyboardButton("✏️ " + sb("Min Withdraw"),  callback_data="aset_min_withdraw")],
        [InlineKeyboardButton("✏️ " + sb("Referral %"),    callback_data="aset_referral_pct"),
         InlineKeyboardButton("✏️ " + sb("Support Link"),  callback_data="aset_support_link")],
        [InlineKeyboardButton(
            ("🔴 Close Deposit" if s.get("deposit_open") else "🟢 Open Deposit"),
            callback_data="aset_toggle_deposit"),
         InlineKeyboardButton(
            ("🔴 Close Withdraw" if s.get("withdraw_open") else "🟢 Open Withdraw"),
            callback_data="aset_toggle_withdraw")],
        [InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_panel")],
    ])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ─── ADMIN: PAYMENT METHODS ──────────────────────────────────
@admin_only
async def adm_payments(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    methods = get_payment_methods()
    text = f"💳 {bold(sb('PAYMENT METHODS'))}\n{divider()}\n"
    for key, pm in methods.items():
        status = "✅" if pm.get("enabled") else "❌"
        number = pm.get("number") or pm.get("address","N/A")
        text += f"{status} {bold(pm.get('name','?'))}: <code>{number}</code>\n"
    text += divider()

    buttons = []
    for key, pm in methods.items():
        toggle_label = ("🔴 Disable" if pm.get("enabled") else "🟢 Enable")
        buttons.append([
            InlineKeyboardButton(f"✏️ {pm.get('name','?')}", callback_data=f"apm_edit_{key}"),
            InlineKeyboardButton(toggle_label, callback_data=f"apm_toggle_{key}"),
        ])
    buttons.append([InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_panel")])

    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

# ─── ADMIN: DEPOSITS ─────────────────────────────────────────
@admin_only
async def adm_deposits(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    deposits = fb_get("deposits", {})
    pending = {k: v for k, v in deposits.items() if v.get("status")=="pending"}
    s = get_settings()
    sym = s.get("currency_symbol","$")
    local = s.get("local_currency","BDT")

    text = (
        f"💳 {bold(sb('DEPOSIT REQUESTS'))}\n"
        f"{divider()}\n"
        f"⏳ {sb('Pending:')} {len(pending)}\n"
        f"✅ {sb('Total:')} {len(deposits)}\n"
        f"{divider()}"
    )
    buttons = []
    for dep_id, dep in list(pending.items())[-10:]:
        uid_d = dep.get("uid","?")
        amt   = dep.get("amount_local","?")
        meth  = dep.get("method","?")
        buttons.append([
            InlineKeyboardButton(
                f"👤{uid_d} | {amt} {local} | {meth}",
                callback_data=f"adep_view_{dep_id}"
            )
        ])
    buttons.append([InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_panel")])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

@admin_only
async def adm_deposit_view(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.replace("adep_view_","")
    dep = fb_get(f"deposits/{dep_id}", {})
    s = get_settings()
    sym = s.get("currency_symbol","$")
    local = s.get("local_currency","BDT")
    uid_d = dep.get("uid","?")
    amt_u = dep.get("amount_usd", 0)

    text = (
        f"💳 {bold(sb('Deposit Details'))}\n"
        f"{divider()}\n"
        f"👤 {sb('User:')} {dep.get('name','?')} ({uid_d})\n"
        f"💰 {sb('Amount:')} {dep.get('amount_local','?')} {local} = {sym}{amt_u:.4f}\n"
        f"📱 {sb('Method:')} {dep.get('method','?')}\n"
        f"🧾 {sb('TxID:')} <code>{dep.get('txid','?')}</code>\n"
        f"📅 {sb('Time:')} {dep.get('time','?')[:16]}\n"
        f"📊 {sb('Status:')} {dep.get('status','?')}\n"
        f"{divider()}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"adep_ok_{dep_id}_{uid_d}_{amt_u}"),
         InlineKeyboardButton("❌ Reject",  callback_data=f"adep_no_{dep_id}_{uid_d}")],
        [InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_deposits")],
    ])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def adm_deposit_approve(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Admin only!", show_alert=True)
        return

    parts = query.data.split("_")
    dep_id = parts[2]
    uid_d  = int(parts[3])
    amount = float(parts[4]) if len(parts) > 4 else 0.0

    fb_update(f"deposits/{dep_id}", {"status": "approved"})
    user = get_user(uid_d)
    old_bal = user.get("balance", 0.0)
    new_bal = round(old_bal + amount, 4)

    # referral commission
    s = get_settings()
    ref_pct = s.get("referral_pct", 5.0)
    referrer = user.get("referrer")
    if referrer and referrer != uid_d:
        commission = round(amount * ref_pct / 100, 4)
        ref_user = get_user(referrer)
        if ref_user:
            ref_bal = ref_user.get("balance",0.0)
            ref_earned = ref_user.get("total_earned",0.0)
            v_refs = ref_user.get("verified_referrals",0)
            fb_update(f"users/{referrer}", {
                "balance":           round(ref_bal + commission, 4),
                "total_earned":      round(ref_earned + commission, 4),
                "verified_referrals": v_refs + 1,
            })
            try:
                await ctx.bot.send_message(
                    referrer,
                    f"🎉 {bold(sb('Referral Commission!'))}\n"
                    f"💰 {sb('Earned:')} {format_amount(commission, s)}\n"
                    f"📊 {sb('From deposit of your referral.')}",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass

    fb_update(f"users/{uid_d}", {"balance": new_bal})
    await query.edit_message_text(
        f"✅ {bold(sb('Deposit Approved!'))}\n"
        f"👤 User: {uid_d}\n"
        f"💰 Added: {format_amount(amount, s)}\n"
        f"💳 New Balance: {format_amount(new_bal, s)}",
        parse_mode=ParseMode.HTML)

    try:
        await ctx.bot.send_message(
            uid_d,
            f"✅ {bold(sb('Deposit Approved!'))}\n"
            f"{divider()}\n"
            f"💰 {sb('Added:')} {format_amount(amount, s)}\n"
            f"💳 {sb('Your Balance:')} {format_amount(new_bal, s)}\n"
            f"{divider()}\n"
            f"🛒 {sb('Start shopping now!')}",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

async def adm_deposit_reject(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("Admin only!", show_alert=True)
        return

    parts = query.data.split("_")
    dep_id = parts[2]
    uid_d  = int(parts[3])

    fb_update(f"deposits/{dep_id}", {"status": "rejected"})
    await query.edit_message_text(f"❌ Deposit {dep_id} rejected.")

    try:
        await ctx.bot.send_message(
            uid_d,
            f"❌ {bold(sb('Deposit Rejected'))}\n"
            f"{sb('Your deposit request was rejected. Please contact support if you think this is a mistake.')}",
            parse_mode=ParseMode.HTML
        )
    except:
        pass

# ─── ADMIN: ADD BALANCE ──────────────────────────────────────
@admin_only
async def adm_addbal_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_addbal_uid"
    await query.edit_message_text(
        f"💰 {bold(sb('ADD BALANCE'))}\n{divider()}\n"
        f"✏️ {sb('Enter User ID:')}", parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_panel")]]))

# ─── ADMIN: BAN/UNBAN ────────────────────────────────────────
@admin_only
async def adm_ban_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_ban_uid"
    await query.edit_message_text(
        f"⛔ {bold(sb('BAN / UNBAN USER'))}\n{divider()}\n"
        f"✏️ {sb('Enter User ID:')}", parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_panel")]]))

# ─── ADMIN: BROADCAST ────────────────────────────────────────
@admin_only
async def adm_broadcast_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_broadcast_msg"
    await query.edit_message_text(
        f"📢 {bold(sb('BROADCAST'))}\n{divider()}\n"
        f"✏️ {sb('Send the message to broadcast to all users:')}", parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_panel")]]))

# ─── ADMIN: FIREBASE STATUS & SYNC ───────────────────────────
@admin_only
async def adm_fbstatus(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = fb_get("users", {})
    categories = fb_get("categories", {})
    deposits = fb_get("deposit_requests", {}) or fb_get("deposits", {})
    orders = fb_get("purchases", {})
    payment_methods = fb_get("payment_methods", {})
    settings = fb_get("settings", {})

    total_prods = sum(len(c.get("products", {})) for c in categories.values())
    fb_mode = "🟢 Firebase Admin SDK (Active)" if firebase_app else "🟡 Firebase REST API (Active)"
    
    # Run test ping
    ping_ok = True
    try:
        fb_set("_fb_ping", {"last_check": datetime.now().isoformat()})
    except Exception:
        ping_ok = False

    conn_status = "🟢 অনলাইন ও সক্রিয় (Connected & Synced)" if ping_ok else "🔴 কানেকশন চেক ব্যর্থ"

    text = (
        f"🔥 <b>ফায়ারবেজ ডেটাবেজ স্ট্যাটাস ও সিঙ্ক রিপোর্ট</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>কানেকশন স্ট্যাটাস:</b> {conn_status}\n"
        f"• <b>মোড:</b> {fb_mode}\n"
        f"• <b>Firebase URL:</b> <code>{FIREBASE_URL}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>ফায়ারবেজে লোড হওয়া বর্তমান ডাটা:</b>\n"
        f"• 👥 মোট রেজিস্টার্ড ইউজার: <b>{len(users)} জন</b>\n"
        f"• 📁 ক্যাটাগরি সংখ্যা: <b>{len(categories)} টি</b>\n"
        f"• 🤖 মোট প্রোডাক্ট ও স্ক্রিপ্ট: <b>{total_prods} টি</b>\n"
        f"• 💳 মোট ডিপোজিট রেকর্ড: <b>{len(deposits)} টি</b>\n"
        f"• 🛍️ সম্পন্ন হওয়া অর্ডার: <b>{len(orders)} টি</b>\n"
        f"• 💰 পেমেন্ট মেথড সংখ্যা: <b>{len(payment_methods)} টি</b>\n"
        f"• ⚙️ গ্লোবাল সেটিংস: <b>সিঙ্কড (OK)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>বট আপলোড, ইউজার ব্যালেন্স বা এডমিন প্যানেলের যেকোনো পরিবর্তন সাথে সাথে ফায়ারবেজ ডাটাবেজে স্টোর হচ্ছে।</i>"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 এখনই ফুল রি-সিঙ্ক করুন", callback_data="adm_fbreforce")],
        [InlineKeyboardButton("⬅️ ব্যাক", callback_data="adm_panel")]
    ])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_fbreforce(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 ফায়ারবেজ ডাটাবেজ ফুল সিঙ্ক হচ্ছে...", show_alert=True)
    
    # Save local store back to Firebase
    data = _load_local_store()
    for root_key, root_val in data.items():
        fb_set(root_key, root_val)
    
    await adm_fbstatus(update, ctx)

# ─── ADMIN: STATS ────────────────────────────────────────────
@admin_only
async def adm_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users     = fb_get("users", {})
    purchases = fb_get("purchases", {})
    deposits  = fb_get("deposits", {})
    cats      = fb_get("categories", {})
    s = get_settings()
    sym = s.get("currency_symbol","$")
    local = s.get("local_currency","BDT")
    rate  = s.get("exchange_rate",125)

    total_bal = sum(u.get("balance",0) for u in users.values())
    total_rev = sum(p.get("price",0) for p in purchases.values())
    banned    = sum(1 for u in users.values() if u.get("banned"))
    total_prods= sum(len(c.get("products",{})) for c in cats.values())
    pending_d = sum(1 for d in deposits.values() if d.get("status")=="pending")
    approved_d= sum(1 for d in deposits.values() if d.get("status")=="approved")

    text = (
        f"📊 {bold(sb('FULL STATISTICS'))}\n"
        f"{divider()}\n"
        f"👥 {sb('Total Users:')} {len(users)}\n"
        f"🚫 {sb('Banned Users:')} {banned}\n"
        f"💰 {sb('Total Balance in System:')} {sym}{total_bal:.2f}\n"
        f"{mini_divider()}\n"
        f"🛒 {sb('Total Sales:')} {len(purchases)}\n"
        f"💵 {sb('Total Revenue:')} {sym}{total_rev:.2f}\n"
        f"📂 {sb('Categories:')} {len(cats)}\n"
        f"🎁 {sb('Products:')} {total_prods}\n"
        f"{mini_divider()}\n"
        f"💳 {sb('Pending Deposits:')} {pending_d}\n"
        f"✅ {sb('Approved Deposits:')} {approved_d}\n"
        f"{divider()}"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_panel")
    ]])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN: CHECK DATA LINK BUTTONS MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin_only
async def adm_checkdata(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    links = fb_get("check_data_links", {})
    if not isinstance(links, dict):
        links = {}

    text = (
        f"🔗 <b>CHECK DATA লিংক বাটন ম্যানেজমেন্ট</b>\n"
        f"{divider()}\n"
        f"📌 এখানে তৈরি করা লিংক বাটনগুলো ইউজাররা তাদের <b>CHECK DATA</b> অপশনে দেখতে পাবে।\n"
        f"যেকোনো বাটনে ক্লিক করলে সরাসরি ওই লিংকটি (যেমন: বট হোস্টিং সাইট, ডোমেইন, টিউটোরিয়াল) ওপেন হবে।\n"
        f"{divider()}\n\n"
    )

    buttons = []
    buttons.append([InlineKeyboardButton("➕ নতুন লিংক বাটন তৈরি করুন", callback_data="adm_addlink_start")])

    if links:
        text += f"📋 <b>বর্তমান সক্রিয় লিংক বাটনসমূহ ({len(links)} টি):</b>\n\n"
        for lid, linfo in links.items():
            if not isinstance(linfo, dict):
                continue
            title = linfo.get("title", "লিংক")
            url = linfo.get("url", "")
            text += f"🔹 <b>{title}</b>\n   🔗 <code>{url}</code>\n"
            buttons.append([
                InlineKeyboardButton(f"✏️ নাম: {title[:12]}", callback_data=f"adm_edlt_{lid}"),
                InlineKeyboardButton("🔗 লিংক এডিট", callback_data=f"adm_edlu_{lid}"),
                InlineKeyboardButton("🗑️", callback_data=f"adm_dellink_{lid}")
            ])
    else:
        text += "⚠️ <i>কোনো লিংক বাটন তৈরি করা নেই। উপরের বাটনে ক্লিক করে তৈরি করুন।</i>"

    buttons.append([InlineKeyboardButton("⬅️ এডমিন প্যানেল", callback_data="adm_panel")])
    kb = InlineKeyboardMarkup(buttons)

    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    elif update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

@admin_only
async def adm_addlink_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_addlink_title"
    text = (
        f"➕ <b>নতুন CHECK DATA লিংক বাটন তৈরি (ধাপ ১/২)</b>\n"
        f"{divider()}\n"
        f"📝 <b>বাটনের নাম / বিষয়বস্তু লিখুন:</b>\n"
        f"<i>(যেমন: 🌐 ভোট হোস্টিং প্ল্যাটফর্ম বা 📺 টিউটোরিয়াল ভিডিও বা 💬 হেল্প গ্রুপ)</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_checkdata")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_edlink_title_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lid = query.data.replace("adm_edlt_", "")
    ctx.user_data["awaiting"] = f"adm_edlt_{lid}"
    link = fb_get(f"check_data_links/{lid}", {})
    text = (
        f"✏️ <b>বাটন টাইটেল এডিট</b>\n"
        f"{divider()}\n"
        f"বর্তমান নাম: <b>{link.get('title', '')}</b>\n\n"
        f"📝 <b>নতুন বাটনের নাম লিখে পাঠান:</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_checkdata")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_edlink_url_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lid = query.data.replace("adm_edlu_", "")
    ctx.user_data["awaiting"] = f"adm_edlu_{lid}"
    link = fb_get(f"check_data_links/{lid}", {})
    text = (
        f"🔗 <b>বাটন লিংক (URL) এডিট</b>\n"
        f"{divider()}\n"
        f"বাটন: <b>{link.get('title', '')}</b>\n"
        f"বর্তমান লিংক: <code>{link.get('url', '')}</code>\n\n"
        f"🌐 <b>নতুন লিংকটি লিখে পাঠান (যেমন: https://...):</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_checkdata")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_dellink_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lid = query.data.replace("adm_dellink_", "")
    fb_delete(f"check_data_links/{lid}")
    await query.answer("🗑️ লিংক বাটন সফলভাবে ডিলিট করা হয়েছে!", show_alert=True)
    await adm_checkdata(update, ctx)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN: FORCE JOIN CHANNELS MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin_only
async def adm_forcejoin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    s = get_settings()
    is_enabled = s.get("force_join_enabled", True)
    channels = get_force_join_channels()
    
    status_text = "🟢 সক্রিয় (Active)" if is_enabled else "🔴 নিষ্ক্রিয় (Disabled)"
    toggle_label = "🔴 Force Join বন্ধ করুন" if is_enabled else "🟢 Force Join চালু করুন"
    
    text = (
        f"📢 <b>FORCE JOIN চ্যানেল ও গ্রুপ ম্যানেজমেন্ট</b>\n"
        f"{divider()}\n"
        f"📌 <b>বর্তমান অবস্থা:</b> {status_text}\n"
        f"💡 ইউজাররা বটে কাজ করার পূর্বে বাধ্যতামূলকভাবে এই চ্যানেলগুলোতে জয়েন করবে।\n"
        f"⚠️ <i>বটকে অবশ্যই চ্যানেল ও গ্রুপে <b>এডমিন (Admin)</b> করে রাখতে হবে যাতে মেম্বারশিপ চেক করতে পারে!</i>\n"
        f"{divider()}\n\n"
    )
    
    buttons = [
        [InlineKeyboardButton(f"🔘 {toggle_label}", callback_data="afj_toggle")],
        [InlineKeyboardButton("➕ নতুন চ্যানেল / গ্রুপ যোগ করুন", callback_data="afj_add_start")],
    ]
    
    if channels:
        text += f"📋 <b>বাধ্যতামূলক চ্যানেলসমূহ ({len(channels)} টি):</b>\n\n"
        for cid, ch in channels.items():
            if not isinstance(ch, dict):
                continue
            name = ch.get("name", "Join")
            chat_id = ch.get("id", "@channel")
            url = ch.get("url", "https://t.me/...")
            text += f"🔹 <b>{name}</b>\n   🆔 <code>{chat_id}</code>\n   🔗 <code>{url}</code>\n"
            buttons.append([
                InlineKeyboardButton(f"✏️ নাম: {name[:10]}", callback_data=f"afj_edname_{cid}"),
                InlineKeyboardButton("🆔 আইডি", callback_data=f"afj_edid_{cid}"),
                InlineKeyboardButton("🔗 লিংক", callback_data=f"afj_edurl_{cid}"),
                InlineKeyboardButton("🗑️", callback_data=f"afj_del_{cid}")
            ])
    else:
        text += "⚠️ <i>কোনো চ্যানেল সেট করা নেই। উপরের বাটনে ক্লিক করে চ্যানেল যোগ করুন।</i>\n"
        
    buttons.append([InlineKeyboardButton("⬅️ এডমিন প্যানেল", callback_data="adm_panel")])
    kb = InlineKeyboardMarkup(buttons)
    
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    elif update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

@admin_only
async def afj_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    s = get_settings()
    curr = s.get("force_join_enabled", True)
    new_val = not curr
    fb_update("settings", {"force_join_enabled": new_val})
    status_str = "চালু" if new_val else "বন্ধ"
    await query.answer(f"📢 Force Join সিস্টেম {status_str} করা হয়েছে!", show_alert=True)
    await adm_forcejoin(update, ctx)

@admin_only
async def afj_add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "afj_add_id"
    text = (
        f"➕ <b>নতুন Force Join চ্যানেল যোগ (ধাপ ১/৩)</b>\n"
        f"{divider()}\n"
        f"📌 <b>চ্যানেল বা গ্রুপের Username অথবা Chat ID লিখুন:</b>\n"
        f"<i>(যেমন: <code>@bd_top_admin</code> অথবা প্রাইভেট হলে <code>-1001234567890</code>)</i>\n\n"
        f"⚠️ <b>মনে রাখবেন:</b> বটকে অবশ্যই ওই চ্যানেলে এডমিন বানাতে হবে।"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def afj_del_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cid = query.data.replace("afj_del_", "")
    fb_delete(f"force_join_channels/{cid}")
    await query.answer("🗑️ চ্যানেলটি সফলভাবে মুছে ফেলা হয়েছে!", show_alert=True)
    await adm_forcejoin(update, ctx)

@admin_only
async def afj_edname_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = query.data.replace("afj_edname_", "")
    ctx.user_data["awaiting"] = f"afj_edname_{cid}"
    ch = fb_get(f"force_join_channels/{cid}", {})
    text = (
        f"✏️ <b>চ্যানেল বাটন নাম এডিট</b>\n"
        f"{divider()}\n"
        f"বর্তমান নাম: <b>{ch.get('name', '')}</b>\n\n"
        f"📝 <b>নতুন বাটনের নাম লিখে পাঠান (যেমন: Join=ಌ বা Join ♕):</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def afj_edid_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = query.data.replace("afj_edid_", "")
    ctx.user_data["awaiting"] = f"afj_edid_{cid}"
    ch = fb_get(f"force_join_channels/{cid}", {})
    text = (
        f"🆔 <b>চ্যানেল আইডি এডিট</b>\n"
        f"{divider()}\n"
        f"বর্তমান আইডি: <code>{ch.get('id', '')}</code>\n\n"
        f"📝 <b>নতুন Username বা Chat ID লিখে পাঠান:</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def afj_edurl_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = query.data.replace("afj_edurl_", "")
    ctx.user_data["awaiting"] = f"afj_edurl_{cid}"
    ch = fb_get(f"force_join_channels/{cid}", {})
    text = (
        f"🔗 <b>চ্যানেল ইনভাইট লিংক এডিট</b>\n"
        f"{divider()}\n"
        f"বর্তমান লিংক: <code>{ch.get('url', '')}</code>\n\n"
        f"🌐 <b>নতুন ইনভাইট লিংক লিখে পাঠান:</b>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN: ROLES & ADMIN MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin_only
async def adm_roles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    caller_uid = update.effective_user.id
    admins = fb_get("admins", {})
    if not isinstance(admins, dict):
        admins = {}
    
    text = (
        f"👑 <b>এডমিন ও রোল ম্যানেজমেন্ট (RBAC System)</b>\n"
        f"{divider()}\n"
        f"📌 <b>এডমিন রোলের বিবরণ:</b>\n"
        f"• 👑 <b>Owner:</b> সম্পূর্ণ মালিকানা ও সকল পারমিশন।\n"
        f"• 🛠️ <b>Manager:</b> প্রোডাক্ট, ক্যাটাগরি, ডিপোজিট ও লিংক ম্যানেজ করতে পারে।\n"
        f"• 👁️ <b>View Only:</b> শুধুমাত্র তথ্য ও স্ট্যাটিস্টিকস দেখতে পারে (এডিট ব্লক)।\n"
        f"{divider()}\n\n"
    )
    
    buttons = []
    if is_owner(caller_uid):
        buttons.append([InlineKeyboardButton("➕ নতুন এডমিন যুক্ত করুন", callback_data="adm_addadmin_start")])
    
    text += f"📋 <b>বর্তমান এডমিন তালিকা ({len(admins)} জন):</b>\n\n"
    for aid_str, ainfo in admins.items():
        if not isinstance(ainfo, dict):
            continue
        aid = ainfo.get("id", aid_str)
        aname = ainfo.get("name", "Admin")
        arole = ainfo.get("role", "viewer")
        
        badge = "👑 Owner" if arole == "owner" else ("🛠️ Manager" if arole == "manager" else "👁️ View Only")
        text += f"👤 <b>{aname}</b> (<code>{aid}</code>)\n   🔰 রোল: <b>{badge}</b>\n"
        
        if is_owner(caller_uid) and str(aid) not in [str(x) for x in ADMIN_IDS] and arole != "owner":
            next_role = "viewer" if arole == "manager" else "manager"
            next_label = "👁️ View Only করুন" if next_role == "viewer" else "🛠️ Manager করুন"
            buttons.append([
                InlineKeyboardButton(f"🔄 {next_label}", callback_data=f"adm_chrole_{aid}_{next_role}"),
                InlineKeyboardButton("🗑️ রিমুভ", callback_data=f"adm_deladmin_{aid}")
            ])
            
    buttons.append([InlineKeyboardButton("⬅️ এডমিন প্যানেল", callback_data="adm_panel")])
    kb = InlineKeyboardMarkup(buttons)
    
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@owner_only
async def adm_addadmin_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_addadmin_id"
    text = (
        f"➕ <b>নতুন এডমিন যুক্ত করুন</b>\n"
        f"{divider()}\n"
        f"📝 <b>যে ইউজারকে এডমিন বানাতে চান তার Telegram User ID লিখে পাঠান:</b>\n"
        f"<i>(ইউজার /id কমান্ড দিলে তার আইডি দেখতে পাবে)</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_roles")]])
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

@owner_only
async def adm_setrole_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # data: adm_setrole_{role}_{uid}
    parts = query.data.replace("adm_setrole_", "").split("_", 1)
    role, target_uid_str = parts[0], parts[1]
    target_uid = int(target_uid_str)
    
    u = get_user(target_uid)
    uname = u.get("name") or u.get("username") or f"User_{target_uid}"
    
    admin_obj = {
        "id": target_uid,
        "name": uname,
        "role": role,
        "added_at": datetime.now().isoformat()
    }
    fb_set(f"admins/{target_uid}", admin_obj)
    fb_update(f"users/{target_uid}", {"is_admin": True, "role": role})
    
    role_name = "Manager (ম্যানেজার)" if role == "manager" else "View Only (ভিউয়ার)"
    await query.answer(f"✅ {uname} কে সফলভাবে {role_name} করা হয়েছে!", show_alert=True)
    
    try:
        await ctx.bot.send_message(
            chat_id=target_uid,
            text=f"🎉 <b>অভিনন্দন!</b> আপনাকে বটের <b>{role_name}</b> হিসেবে নিয়োগ দেওয়া হয়েছে।\nব্যবহার করতে <b>/admin</b> কমান্ড দিন!",
            parse_mode=ParseMode.HTML
        )
    except:
        pass
        
    await adm_roles(update, ctx)

@owner_only
async def adm_chrole_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.replace("adm_chrole_", "").split("_", 1)
    target_uid_str, next_role = parts[0], parts[1]
    target_uid = int(target_uid_str)
    
    fb_update(f"admins/{target_uid}", {"role": next_role})
    fb_update(f"users/{target_uid}", {"role": next_role})
    
    role_name = "Manager" if next_role == "manager" else "View Only"
    await query.answer(f"✅ রোল পরিবর্তন করে {role_name} করা হয়েছে!", show_alert=True)
    await adm_roles(update, ctx)

@owner_only
async def adm_deladmin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    target_uid_str = query.data.replace("adm_deladmin_", "")
    target_uid = int(target_uid_str)
    
    fb_delete(f"admins/{target_uid}")
    fb_update(f"users/{target_uid}", {"is_admin": False, "role": "user"})
    
    await query.answer("🗑️ এডমিন রিমুভ করা হয়েছে!", show_alert=True)
    await adm_roles(update, ctx)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN INPUT HANDLER (text, photo, document upload)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin_only
async def admin_text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    awaiting = ctx.user_data.get("awaiting")
    text = update.message.text.strip() if update.message.text else ""

    if awaiting == "adm_broadcast_msg":
        ctx.user_data["awaiting"] = None
        users = fb_get("users", {})
        sent = 0
        for uid_s in users:
            try:
                await ctx.bot.send_message(int(uid_s), text, parse_mode=ParseMode.HTML)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                pass
        await update.message.reply_text(
            f"📢 {sb('Broadcast sent to')} {sent}/{len(users)} {sb('users.')}",
            reply_markup=main_menu_keyboard())

    elif awaiting == "adm_addbal_uid":
        if text.isdigit():
            ctx.user_data["adm_addbal_uid"] = int(text)
            ctx.user_data["awaiting"] = "adm_addbal_amount"
            await update.message.reply_text(
                f"💰 {sb('Enter amount to add (in USD):')}")
        else:
            await update.message.reply_text(f"❌ {sb('Invalid user ID.')}")

    elif awaiting == "adm_addbal_amount":
        try:
            amount = float(text)
            uid_t = ctx.user_data.get("adm_addbal_uid")
            user_t = get_user(uid_t)
            if not user_t:
                await update.message.reply_text(f"❌ {sb('User not found.')}")
            else:
                s = get_settings()
                old = user_t.get("balance",0)
                new = round(old + amount, 4)
                fb_update(f"users/{uid_t}", {"balance": new})
                ctx.user_data["awaiting"] = None
                await update.message.reply_text(
                    f"✅ {sb('Balance added!')}\n"
                    f"👤 {uid_t}\n"
                    f"💰 Added: {format_amount(amount, s)}\n"
                    f"💳 New Balance: {format_amount(new, s)}",
                    parse_mode=ParseMode.HTML)
                try:
                    await ctx.bot.send_message(
                        uid_t,
                        f"✅ {bold(sb('Balance Added by Admin!'))}\n"
                        f"💰 {sb('Added:')} {format_amount(amount, s)}\n"
                        f"💳 {sb('New Balance:')} {format_amount(new, s)}",
                        parse_mode=ParseMode.HTML)
                except:
                    pass
        except ValueError:
            await update.message.reply_text(f"❌ {sb('Invalid amount.')}")

    elif awaiting == "adm_ban_uid":
        if text.isdigit():
            uid_b = int(text)
            user_b = get_user(uid_b)
            if not user_b:
                await update.message.reply_text(f"❌ {sb('User not found.')}")
            else:
                is_banned = user_b.get("banned", False)
                fb_update(f"users/{uid_b}", {"banned": not is_banned})
                action = "Unbanned" if is_banned else "Banned"
                ctx.user_data["awaiting"] = None
                await update.message.reply_text(
                    f"✅ User {uid_b} {action} successfully.")
        else:
            await update.message.reply_text(f"❌ {sb('Invalid user ID.')}")

    # Settings text inputs
    elif awaiting and awaiting.startswith("aset_"):
        field = awaiting.replace("aset_","")
        ctx.user_data["awaiting"] = None
        # Type conversion
        if field in ["exchange_rate","min_deposit","min_withdraw","referral_pct"]:
            try:
                val = float(text)
            except:
                await update.message.reply_text("❌ Invalid number.")
                return
        else:
            val = text
        fb_update("settings", {field: val})
        await update.message.reply_text(
            f"✅ {sb('Setting updated!')}\n{field}: {val}",
            reply_markup=main_menu_keyboard())

    # Category creation
    elif awaiting == "adm_addcat_name":
        cat_id = text.lower().replace(" ","_").replace("/","_")
        fb_set(f"categories/{cat_id}", {"name": text, "products": {}})
        ctx.user_data["awaiting"] = None
        await update.message.reply_text(
            f"✅ {sb('Category')} '{text}' {sb('created!')}",
            reply_markup=main_menu_keyboard())

    # ─── 6-STEP PRODUCT CREATION WIZARD ───
    # STEP 1: Name -> Ask for Description
    elif awaiting == "adm_addprod_name":
        ctx.user_data["adm_new_prod"] = {"name": text}
        ctx.user_data["awaiting"] = "adm_addprod_desc"
        await update.message.reply_text(
            f"📝 {bold('STEP 2/6: Product Description & Details')}\n{divider()}\n"
            f"✏️ Enter product description and key features:\n"
            f"<i>(Or send <code>skip</code> to leave blank)</i>",
            parse_mode=ParseMode.HTML)

    # STEP 2: Description -> Ask for Photo/Image
    elif awaiting == "adm_addprod_desc":
        if text.lower() != "skip":
            ctx.user_data["adm_new_prod"]["description"] = text
        ctx.user_data["awaiting"] = "adm_addprod_image"
        await update.message.reply_text(
            f"🖼️ {bold('STEP 3/6: Product Photo / Banner')}\n{divider()}\n"
            f"📸 Send a <b>photo directly</b> or send an <b>image URL</b>:\n"
            f"<i>(Or send <code>skip</code> to continue without an image)</i>",
            parse_mode=ParseMode.HTML)

    # STEP 3: Photo/Image -> Ask for Demo Link
    elif awaiting == "adm_addprod_image":
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            ctx.user_data["adm_new_prod"]["image"] = photo_file_id
        elif text and text.lower() != "skip":
            ctx.user_data["adm_new_prod"]["image"] = text

        ctx.user_data["awaiting"] = "adm_addprod_demolink"
        await update.message.reply_text(
            f"🤖 {bold('STEP 4/6: Demo Bot Link / Username')}\n{divider()}\n"
            f"🔗 Enter Demo Bot link or @username:\n"
            f"<i>(e.g. <code>https://t.me/yourdemobot</code> or <code>@yourdemobot</code>, or send <code>skip</code>)</i>",
            parse_mode=ParseMode.HTML)

    # STEP 4: Demo Link -> Ask for Price (USD)
    elif awaiting == "adm_addprod_demolink":
        if text and text.lower() != "skip":
            dlink = text
            if not dlink.startswith("http") and not dlink.startswith("@"):
                dlink = f"https://t.me/{dlink}"
            ctx.user_data["adm_new_prod"]["demo_link"] = dlink

        ctx.user_data["awaiting"] = "adm_addprod_price"
        s = get_settings()
        rate = s.get("exchange_rate", 125)
        local = s.get("local_currency", "BDT")
        await update.message.reply_text(
            f"💰 {bold('STEP 5/6: Product Price (USD)')}\n{divider()}\n"
            f"💵 Enter price in USD (e.g. <code>5.0</code> or <code>2.5</code>):\n"
            f"<i>Current rate: 1 USD = {rate} {local} (e.g. $5 = {5*rate} {local})</i>",
            parse_mode=ParseMode.HTML)

    # STEP 5: Price -> Ask for File Upload (.zip/.py/.js/.html/etc.) OR text stock
    elif awaiting == "adm_addprod_price":
        try:
            price = float(text)
            ctx.user_data["adm_new_prod"]["price"] = price
            ctx.user_data["awaiting"] = "adm_addprod_file_or_stock"
            await update.message.reply_text(
                f"📁 {bold('STEP 6/6: Upload Bot Script / File or Stock Items')}\n{divider()}\n"
                f"📤 <b>Option A (Recommended for Bot Scripts & Codes):</b>\n"
                f"Send any document file (<code>.zip</code>, <code>.py</code>, <code>.js</code>, <code>.html</code>, <code>.txt</code>, <code>.rar</code>, etc.) directly in this chat!\n"
                f"⚡ <i>The bot will automatically deliver this file instantly to buyers upon payment!</i>\n\n"
                f"📝 <b>Option B (For Accounts / License Keys):</b>\n"
                f"Send text lines (one item per line).",
                parse_mode=ParseMode.HTML)
        except ValueError:
            await update.message.reply_text("❌ Invalid price. Please enter a valid number (e.g. 5.0).")

    # STEP 6: File upload OR text stock -> Save & Finalize Product
    elif awaiting == "adm_addprod_file_or_stock":
        prod_data = ctx.user_data.get("adm_new_prod", {})
        cat_id = ctx.user_data.get("adm_addprod_cat")
        pname = prod_data.get("name", "Product")
        pid = pname.lower().replace(" ", "_").replace("/", "_")
        s = get_settings()

        if update.message.document:
            doc = update.message.document
            file_id = doc.file_id
            file_name = doc.file_name or f"{pid}.zip"
            item_str = f"FILE::{file_id}::{file_name}"
            prod_data["is_file"] = True
            prod_data["file_id"] = file_id
            prod_data["file_name"] = file_name
            prod_data["items"] = [item_str] * 999
            prod_data["stock"] = 999
            fb_set(f"categories/{cat_id}/products/{pid}", prod_data)
            ctx.user_data["awaiting"] = None

            price_str = format_amount(prod_data.get("price", 0), s)
            await update.message.reply_text(
                f"✅ {bold(sb('Product Created Successfully!'))}\n"
                f"{divider()}\n"
                f"📦 {sb('Name:')} {bold(pname)}\n"
                f"💰 {sb('Price:')} {bold(price_str)}\n"
                f"📁 {sb('File:')} <code>{file_name}</code> (Auto Instant Delivery ⚡)\n"
                f"🖼️ {sb('Photo:')} {'✅ Yes' if prod_data.get('image') else '❌ No'}\n"
                f"🤖 {sb('Demo Bot:')} {prod_data.get('demo_link', 'None')}\n"
                f"📊 {sb('Stock:')} 999 Digital Available\n"
                f"{divider()}\n"
                f"🛒 {sb('Product is now live in the Shop menu!')}",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard())

        elif text and text.strip():
            items = [line.strip() for line in text.split("\n") if line.strip()]
            prod_data["is_file"] = False
            prod_data["items"] = items
            prod_data["stock"] = len(items)
            fb_set(f"categories/{cat_id}/products/{pid}", prod_data)
            ctx.user_data["awaiting"] = None

            price_str = format_amount(prod_data.get("price", 0), s)
            await update.message.reply_text(
                f"✅ {bold(sb('Product Created Successfully!'))}\n"
                f"{divider()}\n"
                f"📦 {sb('Name:')} {bold(pname)}\n"
                f"💰 {sb('Price:')} {bold(price_str)}\n"
                f"📝 {sb('Stock Items:')} {len(items)}\n"
                f"🖼️ {sb('Photo:')} {'✅ Yes' if prod_data.get('image') else '❌ No'}\n"
                f"🤖 {sb('Demo Bot:')} {prod_data.get('demo_link', 'None')}\n"
                f"{divider()}\n"
                f"🛒 {sb('Product is now live in the Shop menu!')}",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("❌ Please send a file or enter text items.")

    # Stock addition for existing products
    elif awaiting and awaiting.startswith("adm_addstock_"):
        parts = awaiting.replace("adm_addstock_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        prod = fb_get(f"categories/{cat_id}/products/{pid}", {})

        if update.message.document:
            doc = update.message.document
            file_id = doc.file_id
            file_name = doc.file_name or f"{pid}.zip"
            item_str = f"FILE::{file_id}::{file_name}"
            fb_update(f"categories/{cat_id}/products/{pid}", {
                "is_file": True,
                "file_id": file_id,
                "file_name": file_name,
                "items": [item_str] * 999,
                "stock": 999,
            })
            ctx.user_data["awaiting"] = None
            await update.message.reply_text(
                f"✅ {sb('Product script file updated to')} <code>{file_name}</code> (Stock: 999)",
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_keyboard())
        elif text and text.strip():
            new_items = [line.strip() for line in text.split("\n") if line.strip()]
            old_items = prod.get("items", [])
            merged = old_items + new_items
            fb_update(f"categories/{cat_id}/products/{pid}", {
                "items": merged,
                "stock": len(merged),
            })
            ctx.user_data["awaiting"] = None
            await update.message.reply_text(
                f"✅ {sb('Added')} {len(new_items)} {sb('items. Total stock:')} {len(merged)}",
                reply_markup=main_menu_keyboard())

    elif awaiting and awaiting.startswith("apm_edit_"):
        key = awaiting.replace("apm_edit_","")
        ctx.user_data["awaiting"] = None
        fb_update(f"payment_methods/{key}", {"number": text})
        await update.message.reply_text(
            f"✅ {sb('Payment number updated for')} {key}.",
            reply_markup=main_menu_keyboard())

    # Script/Product Editor: Name
    elif awaiting and awaiting.startswith("aedt_name_"):
        parts = awaiting.replace("aedt_name_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        ctx.user_data["awaiting"] = None
        fb_update(f"categories/{cat_id}/products/{pid}", {"name": text})
        await update.message.reply_text(
            f"✅ <b>স্ক্রিপ্ট/প্রোডাক্টের নাম পরিবর্তন করা হয়েছে:</b>\n<code>{text}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
        )

    # Script/Product Editor: Price
    elif awaiting and awaiting.startswith("aedt_price_"):
        parts = awaiting.replace("aedt_price_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        try:
            val = float(text)
            ctx.user_data["awaiting"] = None
            fb_update(f"categories/{cat_id}/products/{pid}", {"price": val})
            s = get_settings()
            rate = s.get("exchange_rate", 125)
            local_sym = s.get("local_currency", "৳")
            await update.message.reply_text(
                f"✅ <b>মূল্য সফলভাবে আপডেট করা হয়েছে:</b>\n💰 <code>{val}$</code> ({round(val*rate, 2)} {local_sym})",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
            )
        except ValueError:
            await update.message.reply_text("❌ অনুগ্রহ করে সঠিক সংখ্যা লিখুন (যেমন: 5.0)।")

    # Script/Product Editor: Demo Link
    elif awaiting and awaiting.startswith("aedt_demo_"):
        parts = awaiting.replace("aedt_demo_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        ctx.user_data["awaiting"] = None
        if text.lower() == "clear":
            val = ""
        elif text.startswith("http") or text.startswith("@"):
            val = text
        else:
            val = f"https://t.me/{text}"
        fb_update(f"categories/{cat_id}/products/{pid}", {"demo_link": val})
        await update.message.reply_text(
            f"✅ <b>ডেমো লিংক আপডেট করা হয়েছে:</b>\n🔗 {val if val else '<i>রিমুভ করা হয়েছে</i>'}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
        )

    # Script/Product Editor: Description
    elif awaiting and awaiting.startswith("aedt_desc_"):
        parts = awaiting.replace("aedt_desc_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        ctx.user_data["awaiting"] = None
        fb_update(f"categories/{cat_id}/products/{pid}", {"description": text})
        await update.message.reply_text(
            f"✅ <b>ডেসক্রিপশন সফলভাবে আপডেট করা হয়েছে!</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
        )

    # Script/Product Editor: Entry File
    elif awaiting and awaiting.startswith("aedt_entry_"):
        parts = awaiting.replace("aedt_entry_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        ctx.user_data["awaiting"] = None
        fb_update(f"categories/{cat_id}/products/{pid}", {"entry_file": text})
        await update.message.reply_text(
            f"✅ <b>মেইন এন্ট্রি ফাইল আপডেট করা হয়েছে:</b> <code>{text}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
        )

    # Script/Product Editor: Upload New File / Stock
    elif awaiting and awaiting.startswith("aedt_file_"):
        parts = awaiting.replace("aedt_file_","").split("_",1)
        cat_id, pid = parts[0], parts[1]
        if update.message.document:
            doc = update.message.document
            file_id = doc.file_id
            file_name = doc.file_name or f"{pid}.zip"
            item_str = f"FILE::{file_id}::{file_name}"
            fb_update(f"categories/{cat_id}/products/{pid}", {
                "is_file": True,
                "file_id": file_id,
                "file_name": file_name,
                "items": [item_str] * 999,
                "stock": 999,
            })
            ctx.user_data["awaiting"] = None
            await update.message.reply_text(
                f"✅ <b>নতুন স্ক্রিপ্ট ফাইল সফলভাবে আপলোড করা হয়েছে:</b>\n📁 <code>{file_name}</code> (অটো ডেলিভারি সক্রিয় ⚡)",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
            )
        elif text and text.strip():
            new_items = [line.strip() for line in text.split("\n") if line.strip()]
            fb_update(f"categories/{cat_id}/products/{pid}", {
                "items": new_items,
                "stock": len(new_items),
                "is_file": False
            })
            ctx.user_data["awaiting"] = None
            await update.message.reply_text(
                f"✅ <b>স্টক আইটেম আপডেট সম্পন্ন!</b> (মোট স্টক: {len(new_items)})",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚙️ এডিটরে ফিরুন", callback_data=f"adm_prod_{cat_id}_{pid}")]])
            )

    # ─── CHECK DATA LINK BUTTON BUILDER & EDITORS ───
    # Link Creation: Step 1 Title -> Ask for URL
    elif awaiting == "adm_addlink_title":
        ctx.user_data["new_link_title"] = text
        ctx.user_data["awaiting"] = "adm_addlink_url"
        await update.message.reply_text(
            f"🔗 <b>নতুন CHECK DATA লিংক বাটন তৈরি (ধাপ ২/২)</b>\n"
            f"{divider()}\n"
            f"বাটনের নাম: <b>{text}</b>\n\n"
            f"🌐 <b>এবার সরাসরি কাঙ্খিত লিংকটি (URL) পাঠান:</b>\n"
            f"<i>(যেমন: <code>https://render.com</code> বা <code>https://t.me/yourchannel</code>)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_checkdata")]])
        )

    # Link Creation: Step 2 URL -> Save
    elif awaiting == "adm_addlink_url":
        title = ctx.user_data.get("new_link_title", "লিংক")
        url = text.strip()
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("tg://"):
            url = f"https://{url}"
        lid = f"link_{int(datetime.now().timestamp() * 1000)}"
        fb_set(f"check_data_links/{lid}", {"title": title, "url": url})
        ctx.user_data["awaiting"] = None
        ctx.user_data["new_link_title"] = None
        await update.message.reply_text(
            f"✅ <b>নতুন CHECK DATA লিংক বাটন সফলভাবে তৈরি হয়েছে!</b>\n\n"
            f"👉 <b>বাটনের নাম:</b> {title}\n"
            f"🔗 <b>লিংক:</b> <code>{url}</code>\n\n"
            f"⚡ <i>ইউজাররা এখন <b>CHECK DATA</b> বাটনে ক্লিক করলেই সরাসরি এই লিংকে যেতে পারবে।</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ লিংক বাটন কন্ট্রোলে ফিরুন", callback_data="adm_checkdata")]])
        )

    # Link Title Edit
    elif awaiting and awaiting.startswith("adm_edlt_"):
        lid = awaiting.replace("adm_edlt_", "")
        ctx.user_data["awaiting"] = None
        fb_update(f"check_data_links/{lid}", {"title": text})
        await update.message.reply_text(
            f"✅ <b>বাটন টাইটেল আপডেট সম্পন্ন!</b>\n👉 <b>{text}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ লিংক বাটন কন্ট্রোলে ফিরুন", callback_data="adm_checkdata")]])
        )

    # Link URL Edit
    elif awaiting and awaiting.startswith("adm_edlu_"):
        lid = awaiting.replace("adm_edlu_", "")
        ctx.user_data["awaiting"] = None
        url = text.strip()
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("tg://"):
            url = f"https://{url}"
        fb_update(f"check_data_links/{lid}", {"url": url})
        await update.message.reply_text(
            f"✅ <b>বাটন লিংক আপডেট সম্পন্ন!</b>\n🔗 <code>{url}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ লিংক বাটন কন্ট্রোলে ফিরুন", callback_data="adm_checkdata")]])
        )

    # ─── FORCE JOIN CHANNELS BUILDER & EDITORS ───
    # Step 1: Channel ID -> Ask for Button Name
    elif awaiting == "afj_add_id":
        ctx.user_data["new_fj_id"] = text.strip()
        ctx.user_data["awaiting"] = "afj_add_name"
        await update.message.reply_text(
            f"➕ <b>নতুন Force Join চ্যানেল যোগ (ধাপ ২/৩)</b>\n"
            f"{divider()}\n"
            f"চ্যানেল আইডি: <code>{text.strip()}</code>\n\n"
            f"📝 <b>বাটনের নাম বা লেবেল লিখুন:</b>\n"
            f"<i>(যেমন: <code>Join=ಌ</code> বা <code>Join ♕</code> বা <code>Official Channel</code>)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
        )

    # Step 2: Button Name -> Ask for Invite Link
    elif awaiting == "afj_add_name":
        ctx.user_data["new_fj_name"] = text.strip()
        ctx.user_data["awaiting"] = "afj_add_url"
        await update.message.reply_text(
            f"➕ <b>নতুন Force Join চ্যানেল যোগ (ধাপ ৩/৩)</b>\n"
            f"{divider()}\n"
            f"বাটনের নাম: <b>{text.strip()}</b>\n\n"
            f"🌐 <b>চ্যানেলের ইনভাইট লিংক লিখে পাঠান:</b>\n"
            f"<i>(যেমন: <code>https://t.me/yourchannel</code>)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ বাতিল", callback_data="adm_forcejoin")]])
        )

    # Step 3: Invite Link -> Save to Firebase
    elif awaiting == "afj_add_url":
        ch_id = ctx.user_data.get("new_fj_id", "")
        ch_name = ctx.user_data.get("new_fj_name", "Join")
        url = text.strip()
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("tg://"):
            url = f"https://{url}"
        cid = f"ch_{int(datetime.now().timestamp() * 1000)}"
        ch_obj = {"id": ch_id, "name": ch_name, "url": url}
        fb_set(f"force_join_channels/{cid}", ch_obj)
        ctx.user_data["awaiting"] = None
        ctx.user_data["new_fj_id"] = None
        ctx.user_data["new_fj_name"] = None
        await update.message.reply_text(
            f"✅ <b>নতুন Force Join চ্যানেল সফলভাবে সংযুক্ত হয়েছে!</b>\n\n"
            f"🔹 <b>বাটন নাম:</b> {ch_name}\n"
            f"🆔 <b>আইডি:</b> <code>{ch_id}</code>\n"
            f"🔗 <b>লিংক:</b> <code>{url}</code>\n\n"
            f"⚡ <i>ইউজাররা এখন বটে প্রবেশ করতে হলে এই চ্যানেলে জয়েন করতে হবে।</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Force Join কন্ট্রোলে ফিরুন", callback_data="adm_forcejoin")]])
        )

    # Channel Name Edit
    elif awaiting and awaiting.startswith("afj_edname_"):
        cid = awaiting.replace("afj_edname_", "")
        ctx.user_data["awaiting"] = None
        fb_update(f"force_join_channels/{cid}", {"name": text})
        await update.message.reply_text(
            f"✅ <b>চ্যানেল বাটন নাম আপডেট সম্পন্ন!</b>\n👉 <b>{text}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Force Join কন্ট্রোলে ফিরুন", callback_data="adm_forcejoin")]])
        )

    # Channel ID Edit
    elif awaiting and awaiting.startswith("afj_edid_"):
        cid = awaiting.replace("afj_edid_", "")
        ctx.user_data["awaiting"] = None
        fb_update(f"force_join_channels/{cid}", {"id": text.strip()})
        await update.message.reply_text(
            f"✅ <b>চ্যানেল আইডি আপডেট সম্পন্ন!</b>\n🆔 <code>{text.strip()}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Force Join কন্ট্রোলে ফিরুন", callback_data="adm_forcejoin")]])
        )

    # Channel URL Edit
    elif awaiting and awaiting.startswith("afj_edurl_"):
        cid = awaiting.replace("afj_edurl_", "")
        ctx.user_data["awaiting"] = None
        url = text.strip()
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("tg://"):
            url = f"https://{url}"
        fb_update(f"force_join_channels/{cid}", {"url": url})
        await update.message.reply_text(
            f"✅ <b>চ্যানেল লিংক আপডেট সম্পন্ন!</b>\n🔗 <code>{url}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Force Join কন্ট্রোলে ফিরুন", callback_data="adm_forcejoin")]])
        )

    # ─── ADMIN ROLE ASSIGNMENT ───
    elif awaiting == "adm_addadmin_id":
        if text.isdigit():
            target_uid = int(text)
            ctx.user_data["awaiting"] = None
            u = get_user(target_uid)
            uname = u.get("name") or u.get("username") or f"User {target_uid}"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠️ Manager (এডিট ও ম্যানেজ)", callback_data=f"adm_setrole_manager_{target_uid}")],
                [InlineKeyboardButton("👁️ View Only (শুধুমাত্র ভিউ)", callback_data=f"adm_setrole_viewer_{target_uid}")],
                [InlineKeyboardButton("❌ বাতিল", callback_data="adm_roles")]
            ])
            await update.message.reply_text(
                f"👤 <b>ইউজার পাওয়া গেছে:</b> {uname} (<code>{target_uid}</code>)\n\n"
                f"🔰 <b>এই এডমিনকে কোন রোল দিতে চান নির্বাচন করুন:</b>\n"
                f"• <b>Manager:</b> প্রোডাক্ট, ক্যাটাগরি, ডিপোজিট এডিট করতে পারবে।\n"
                f"• <b>View Only:</b> শুধুমাত্র স্ট্যাটাস ও ইউজার লিস্ট দেখতে পারবে।",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        else:
            await update.message.reply_text("❌ অনুগ্রহ করে সঠিক সংখ্যার Telegram User ID পাঠান।")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN SETTINGS CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@admin_only
async def adm_settings_field(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.replace("aset_","")

    if field == "toggle_deposit":
        s = get_settings()
        fb_update("settings", {"deposit_open": not s.get("deposit_open", False)})
        await adm_settings(update, ctx)
        return
    if field == "toggle_withdraw":
        s = get_settings()
        fb_update("settings", {"withdraw_open": not s.get("withdraw_open", True)})
        await adm_settings(update, ctx)
        return

    labels = {
        "bot_name":       "Bot Name",
        "welcome_text":   "Welcome Text",
        "currency_name":  "Currency Name (e.g. USD)",
        "currency_symbol":"Currency Symbol (e.g. $)",
        "local_currency": "Local Currency (e.g. BDT)",
        "exchange_rate":  "Exchange Rate (number)",
        "min_deposit":    "Minimum Deposit (USD)",
        "min_withdraw":   "Minimum Withdraw (USD)",
        "referral_pct":   "Referral Commission %",
        "support_link":   "Support Link (URL)",
    }
    label = labels.get(field, field)
    ctx.user_data["awaiting"] = f"aset_{field}"
    await query.edit_message_text(
        f"✏️ {bold(sb('EDIT SETTING'))}\n{divider()}\n"
        f"🔧 {sb('Field:')} {label}\n"
        f"📝 {sb('Enter new value:')}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_settings")]]))

# ─── ADMIN: PAYMENT EDIT / TOGGLE ───────────────────────────
@admin_only
async def adm_pay_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("apm_edit_","")
    ctx.user_data["awaiting"] = f"apm_edit_{key}"
    methods = get_payment_methods()
    pm = methods.get(key, {})
    await query.edit_message_text(
        f"✏️ {bold(sb('Edit Payment Method'))}\n{divider()}\n"
        f"📱 {sb('Method:')} {pm.get('name','?')}\n"
        f"📝 {sb('Enter new number/address:')}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_payments")]]))

@admin_only
async def adm_pay_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("apm_toggle_","")
    methods = get_payment_methods()
    pm = methods.get(key, {})
    fb_update(f"payment_methods/{key}", {"enabled": not pm.get("enabled", True)})
    await adm_payments(update, ctx)

# ─── ADMIN: ADD CATEGORY / PRODUCT ──────────────────────────
@admin_only
async def adm_addcat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["awaiting"] = "adm_addcat_name"
    await query.edit_message_text(
        f"➕ {bold(sb('ADD CATEGORY'))}\n{divider()}\n"
        f"✏️ {sb('Enter category name:')}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="adm_products")]]))

@admin_only
async def adm_addprod(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace("adm_addprod_","")
    ctx.user_data["adm_addprod_cat"] = cat_id
    ctx.user_data["adm_new_prod"] = {}
    ctx.user_data["awaiting"] = "adm_addprod_name"
    await query.edit_message_text(
        f"➕ {bold(sb('STEP 1/6: PRODUCT NAME'))}\n{divider()}\n"
        f"✏️ {sb('Enter product / bot name:')}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"adm_cat_{cat_id}")]]))

@admin_only
async def adm_addstock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("adm_addstock_","")
    parts = data.split("_",1)
    cat_id, pid = parts[0], parts[1]
    ctx.user_data["awaiting"] = f"adm_addstock_{cat_id}_{pid}"
    await query.edit_message_text(
        f"📦 {bold(sb('ADD STOCK / UPDATE SCRIPT FILE'))}\n{divider()}\n"
        f"📤 <b>Option A:</b> Send a <code>.zip</code>, <code>.py</code>, <code>.js</code> file directly\n"
        f"📝 <b>Option B:</b> Enter text credentials (one per line)",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"adm_prod_{cat_id}_{pid}")]]))

@admin_only
async def adm_delprod(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("adm_delprod_","")
    parts = data.split("_",1)
    cat_id, pid = parts[0], parts[1]
    fb_delete(f"categories/{cat_id}/products/{pid}")
    await query.edit_message_text(
        f"🗑️ {sb('Product deleted.')}\n",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back", callback_data=f"adm_cat_{cat_id}")]]))

@admin_only
async def adm_delcat_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categories = fb_get("categories", {})
    buttons = [[InlineKeyboardButton(
        f"🗑️ {cat.get('name','?')}", callback_data=f"adm_delcat_{cat_id}")]
        for cat_id, cat in categories.items()]
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="adm_products")])
    await query.edit_message_text(
        f"🗑️ {bold(sb('DELETE CATEGORY'))}\n{divider()}\n"
        f"⚠️ {sb('Select category to delete (ALL products inside will be lost!):')}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

@admin_only
async def adm_delcat_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace("adm_delcat_","")
    fb_delete(f"categories/{cat_id}")
    await query.edit_message_text(
        f"🗑️ {sb('Category deleted.')}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back", callback_data="adm_products")]]))

@admin_only
async def adm_manage_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = fb_get("users", {})
    s = get_settings()
    sym = s.get("currency_symbol","$")
    text = (
        f"👥 {bold(sb('MANAGE USERS'))}\n"
        f"{divider()}\n"
        f"👤 {sb('Total:')} {len(users)}\n"
        f"🚫 {sb('Banned:')} {sum(1 for u in users.values() if u.get('banned'))}\n"
        f"{divider()}\n"
        f"💡 {sb('Use buttons below to manage:')}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 " + sb("Add Balance"),   callback_data="adm_addbal"),
         InlineKeyboardButton("⛔ " + sb("Ban/Unban"),     callback_data="adm_ban")],
        [InlineKeyboardButton("👑 এডমিন ও রোল কন্ট্রোল", callback_data="adm_roles"),
         InlineKeyboardButton("📋 " + sb("List Users"),    callback_data="adm_listusers")],
        [InlineKeyboardButton("⬅️ " + sb("Back"),          callback_data="adm_panel")],
    ])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_list_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = fb_get("users", {})
    s = get_settings()
    sym = s.get("currency_symbol","$")
    text = f"👥 {bold(sb('USER LIST'))} (last 20)\n{divider()}\n"
    for uid_s, u in list(users.items())[-20:]:
        ban = "🚫" if u.get("banned") else "✅"
        bal = round(u.get("balance",0),2)
        text += f"{ban} {u.get('name','?')} (<code>{uid_s}</code>) — {sym}{bal}\n"
    text += divider()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_users")
    ]])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML, reply_markup=kb)

@admin_only
async def adm_withdrawals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    withdrawals = fb_get("withdrawals", {})
    s = get_settings()
    sym = s.get("currency_symbol","$")
    pending = {k: v for k, v in withdrawals.items() if v.get("status")=="pending"}
    text = (
        f"📤 {bold(sb('WITHDRAWALS'))}\n"
        f"{divider()}\n"
        f"⏳ {sb('Pending:')} {len(pending)}\n"
        f"✅ {sb('Total:')} {len(withdrawals)}\n"
        f"{divider()}"
    )
    buttons = []
    for wid, w in list(pending.items())[-10:]:
        uid_w = w.get("uid","?")
        amt   = w.get("amount","?")
        meth  = w.get("method","?")
        buttons.append([InlineKeyboardButton(
            f"👤{uid_w} | {sym}{amt} | {meth}",
            callback_data=f"awdraw_view_{wid}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ " + sb("Back"), callback_data="adm_panel")])
    await query.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VERIFY FORCE JOIN & ABOUT CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def verify_force_join_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    not_joined = await check_force_join(ctx.bot, uid)
    if not_joined:
        await query.answer("⚠️ আপনি এখনো সব চ্যানেলে জয়েন করেননি! সবগুলো চ্যানেলে জয়েন করুন এবং আবার Verify বাটনে চাপুন।", show_alert=True)
        await send_force_join_screen(update, not_joined, is_edit=True)
        return
    
    await query.answer("✅ ভেরিফিকেশন সফল হয়েছে! স্বাগতম।", show_alert=True)
    s = get_settings()
    bot_name = s.get("bot_name", "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎")
    admin_banner = f"\n👑 {bold('Admin Access Enabled')} — Use /admin or button below\n" if is_admin(uid) else ""
    text = (
        f"🔥 {bold('Hello Hey!')}\n\n"
        f"🌟 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 {bold(bot_name)}\n"
        f"{admin_banner}"
        f"{divider()}\n"
        f"⚡ {sb('Instant Delivery')}\n"
        f"🛡️ {sb('Secure Purchase')}\n"
        f"💎 {sb('Premium Quality')}\n"
        f"✅ {sb('Trusted Service')}\n"
        f"{divider()}\n\n"
        f"👋 {sb('Welcome to the Shop Menu!')} Select an option below:"
    )
    try:
        await query.message.delete()
    except:
        pass
    await ctx.bot.send_message(
        chat_id=uid,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(uid)
    )

async def about_dev_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    s = get_settings()
    dev_name = s.get("dev_name", "@bd_top_admin")
    dev_url = s.get("dev_url", "https://t.me/bd_top_admin")
    bot_name = s.get("bot_name", "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎")
    
    text = (
        f"ℹ️ {bold(sb('DEVELOPER & PLATFORM INFO'))}\n"
        f"{divider()}\n"
        f"👑 {sb('Bot Platform:')} {bold(bot_name)}\n"
        f"💻 {sb('Developer / Owner:')} <b>{dev_name}</b>\n"
        f"🚀 {sb('System Version:')} <b>v3.5 Pro Cloud Realtime</b>\n"
        f"⚡ {sb('Feature:')} Instant Delivery & Auto Verification\n"
        f"🛡️ {sb('Security:')} RBAC Multi-Admin & Encrypted Storage\n"
        f"{divider()}\n"
        f"💡 {sb('For bot customization or inquiries, contact developer below:')}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Contact Developer", url=dev_url)],
        [InlineKeyboardButton("🏠 " + sb("Home"), callback_data="home")]
    ])
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
    elif update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN MESSAGE ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid  = update.effective_user.id
    user = get_user(uid)
    if user and user.get("banned"):
        await update.message.reply_text("🚫 You are banned.")
        return

    # Check Force Join for non-admin users before processing text/buttons
    if not is_admin(uid):
        not_joined = await check_force_join(ctx.bot, uid)
        if not_joined:
            await send_force_join_screen(update, not_joined)
            return

    txt = update.message.text or ""

    # Admin text inputs take priority
    if is_admin(uid) and ctx.user_data.get("awaiting"):
        await admin_text_handler(update, ctx)
        return

    # User deposit/general text inputs
    if ctx.user_data.get("awaiting") in ["deposit_amount","deposit_txid"]:
        await deposit_handle_text(update, ctx)
        return

    # Main menu routing
    txt_up = txt.upper().strip()
    for ch in "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯 ":
        pass

    # Normalize slanted bold to ASCII for comparison
    def normalize(s):
        normal_map = dict(zip(
            "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙖𝙗𝙘𝙙𝙚𝙛𝙜𝙝𝙞𝙟𝙠𝙡𝙢𝙣𝙤𝙥𝙦𝙧𝙨𝙩𝙪𝙫𝙬𝙭𝙮𝙯",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        ))
        return "".join(normal_map.get(c, c) for c in s).upper()

    ntxt = normalize(txt)

    if "BUY PRODUCT" in ntxt:
        await shop_menu(update, ctx)
    elif "DEPOSIT MONEY" in ntxt or "DEPOSIT" in ntxt:
        await deposit_menu(update, ctx)
    elif "REFER" in ntxt:
        await refer_menu(update, ctx)
    elif "MY PRODUCT" in ntxt:
        await my_products(update, ctx)
    elif "MY PROFILE" in ntxt or "PROFILE" in ntxt:
        await my_profile(update, ctx)
    elif "SUPPORT" in ntxt:
        await support_menu(update, ctx)
    elif "ABOUT" in ntxt:
        await about_dev_callback(update, ctx)
    elif "CHECK DATA" in ntxt:
        await check_data(update, ctx)
    elif "MY ID" in ntxt or "ID" == ntxt:
        await my_id_cmd(update, ctx)
    elif "ADMIN PANEL" in ntxt or "ADMIN" in ntxt or "/admin" in txt.lower():
        if is_admin(uid):
            await admin_panel(update, ctx)
        else:
            await admin_cmd(update, ctx)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CALLBACK ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def callback_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data  = query.data
    uid   = update.effective_user.id

    # Handle verification and about first
    if data == "verify_force_join":
        await verify_force_join_callback(update, ctx)
        return
    elif data == "about_dev":
        await about_dev_callback(update, ctx)
        return

    # Check Force Join for non-admins for regular callback queries
    if not is_admin(uid) and data not in ["home", "support", "about_dev", "verify_force_join"]:
        not_joined = await check_force_join(ctx.bot, uid)
        if not_joined:
            await query.answer("⚠️ অনুগ্রহ করে প্রথমে চ্যানেলগুলোতে জয়েন করুন!", show_alert=True)
            await send_force_join_screen(update, not_joined, is_edit=True)
            return

    if data == "home":
        await home_callback(update, ctx)
    elif data == "shop":
        await shop_menu(update, ctx)
    elif data == "deposit":
        await deposit_menu(update, ctx)
    elif data == "refer":
        await refer_menu(update, ctx)
    elif data == "support":
        await support_menu(update, ctx)
    elif data == "profile":
        await my_profile(update, ctx)

    # Shop
    elif data.startswith("cat_"):
        await show_category(update, ctx)
    elif data.startswith("prod_"):
        await show_product(update, ctx)
    elif data.startswith("buy_"):
        await confirm_buy(update, ctx)
    elif data.startswith("dl_"):
        await download_purchased_file(update, ctx)

    # Deposit gateway selection
    elif data.startswith("dep_"):
        await deposit_method_chosen(update, ctx)

    # Admin panel
    elif data == "adm_panel":
        await admin_panel(update, ctx)
    elif data == "adm_products":
        await adm_products(update, ctx)
    elif data.startswith("adm_cat_"):
        await adm_category_detail(update, ctx)
    elif data.startswith("adm_prod_"):
        await adm_prod_detail(update, ctx)
    elif data == "adm_settings":
        await adm_settings(update, ctx)
    elif data == "adm_payments":
        await adm_payments(update, ctx)
    elif data == "adm_deposits":
        await adm_deposits(update, ctx)
    elif data.startswith("adep_view_"):
        await adm_deposit_view(update, ctx)
    elif data.startswith("adep_ok_"):
        await adm_deposit_approve(update, ctx)
    elif data.startswith("adep_no_"):
        await adm_deposit_reject(update, ctx)
    elif data == "adm_broadcast":
        await adm_broadcast_start(update, ctx)
    elif data == "adm_stats":
        await adm_stats(update, ctx)
    elif data == "adm_fbstatus":
        await adm_fbstatus(update, ctx)
    elif data == "adm_fbreforce":
        await adm_fbreforce(update, ctx)
    elif data == "adm_addbal":
        await adm_addbal_start(update, ctx)
    elif data == "adm_ban":
        await adm_ban_start(update, ctx)
    elif data == "adm_users":
        await adm_manage_users(update, ctx)
    elif data == "adm_listusers":
        await adm_list_users(update, ctx)
    elif data == "adm_withdrawals":
        await adm_withdrawals(update, ctx)
    elif data == "adm_addcat":
        await adm_addcat(update, ctx)
    elif data == "adm_delcat":
        await adm_delcat_prompt(update, ctx)
    elif data.startswith("adm_delcat_"):
        await adm_delcat_confirm(update, ctx)
    elif data.startswith("adm_addprod_"):
        await adm_addprod(update, ctx)
    elif data.startswith("adm_addstock_"):
        await adm_addstock(update, ctx)
    elif data.startswith("adm_delprod_"):
        await adm_delprod(update, ctx)
    elif data == "adm_checkdata":
        await adm_checkdata(update, ctx)
    elif data == "adm_addlink_start":
        await adm_addlink_start(update, ctx)
    elif data.startswith("adm_edlt_"):
        await adm_edlink_title_start(update, ctx)
    elif data.startswith("adm_edlu_"):
        await adm_edlink_url_start(update, ctx)
    elif data.startswith("adm_dellink_"):
        await adm_dellink_confirm(update, ctx)
    # Force Join Admin Callbacks
    elif data == "adm_forcejoin":
        await adm_forcejoin(update, ctx)
    elif data == "afj_toggle":
        await afj_toggle(update, ctx)
    elif data == "afj_add_start":
        await afj_add_start(update, ctx)
    elif data.startswith("afj_del_"):
        await afj_del_confirm(update, ctx)
    elif data.startswith("afj_edname_"):
        await afj_edname_start(update, ctx)
    elif data.startswith("afj_edid_"):
        await afj_edid_start(update, ctx)
    elif data.startswith("afj_edurl_"):
        await afj_edurl_start(update, ctx)
    # Admin Roles
    elif data == "adm_roles":
        await adm_roles(update, ctx)
    elif data == "adm_addadmin_start":
        await adm_addadmin_start(update, ctx)
    elif data.startswith("adm_setrole_"):
        await adm_setrole_callback(update, ctx)
    elif data.startswith("adm_chrole_"):
        await adm_chrole_callback(update, ctx)
    elif data.startswith("adm_deladmin_"):
        await adm_deladmin_callback(update, ctx)
    # Bengali Script Details & Editor Callbacks
    elif data.startswith("aedt_name_"):
        await aedt_start_name(update, ctx)
    elif data.startswith("aedt_price_"):
        await aedt_start_price(update, ctx)
    elif data.startswith("aedt_cat_"):
        await aedt_start_cat(update, ctx)
    elif data.startswith("aedt_moveto_"):
        await aedt_move_cat(update, ctx)
    elif data.startswith("aedt_demo_"):
        await aedt_start_demo(update, ctx)
    elif data.startswith("aedt_desc_"):
        await aedt_start_desc(update, ctx)
    elif data.startswith("aedt_entry_"):
        await aedt_start_entry(update, ctx)
    elif data.startswith("aedt_file_"):
        await aedt_start_file(update, ctx)
    elif data.startswith("aedt_testdl_"):
        await aedt_test_download(update, ctx)
    elif data.startswith("aedt_vis_"):
        await aedt_toggle_visibility(update, ctx)
    elif data.startswith("aset_"):
        await adm_settings_field(update, ctx)
    elif data.startswith("apm_edit_"):
        await adm_pay_edit(update, ctx)
    elif data.startswith("apm_toggle_"):
        await adm_pay_toggle(update, ctx)
    else:
        await query.answer("Unknown action.", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  /admin command
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        text = (
            f"🚫 {bold('Access Restricted — Admin Only')}\n"
            f"{divider()}\n"
            f"🆔 {sb('Your Telegram User ID:')} <code>{uid}</code>\n"
            f"👤 {sb('Name:')} {update.effective_user.full_name}\n"
            f"🏷️ {sb('Username:')} @{update.effective_user.username or 'N/A'}\n"
            f"{divider()}\n"
            f"💡 {sb('To authorize this Telegram account:')}\n"
            f"1. Open your web app Config panel\n"
            f"2. Add <code>{uid}</code> to <b>Admin Telegram ID</b>\n"
            f"3. Click <b>Save & Restart</b>, then send <b>/admin</b> again!"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    await admin_panel(update, ctx)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POST-INIT: REGISTER BOT COMMANDS & MENU BUTTON (Single /start)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def post_init(application: Application):
    # Only single /start command in menu drawer as requested
    commands = [
        BotCommand("start", "Open main menu"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.info("✅ Telegram Bot command /start successfully set in menu button!")
    except Exception as e:
        logger.warning(f"Could not set bot commands or menu button: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    init_defaults()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("id", my_id_cmd))
    app.add_handler(CommandHandler("myid", my_id_cmd))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, handle_message))

    logger.info("🚀 DXA PAID ZONE Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
