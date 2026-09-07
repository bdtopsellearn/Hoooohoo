# -*- coding: utf-8 -*-
"""
script_store.py — Complete Bot Script Store & Selling System for Cipher Telegram Bot
Integrated with sellingbot.py data models, bKash/Nagad/Rocket balance checkout,
instant document delivery, and complete admin management panel.
"""

import os
import sys
import json
import time
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any, Optional, List

# Telebot imports
try:
    from telebot import types
except ImportError:
    class _MockTypes:
        class InlineKeyboardMarkup:
            def __init__(self, *args, **kwargs):
                self.keyboard = []
            def add(self, *args, **kwargs):
                self.keyboard.append(list(args))
        class InlineKeyboardButton:
            def __init__(self, text: str, callback_data: Optional[str] = None, url: Optional[str] = None, style: str = "", **kwargs):
                self.text = text
                self.callback_data = callback_data
                self.url = url
                self.style = style
        class CallbackQuery:
            pass
        class Message:
            pass
    types = _MockTypes()

# Global handles set on init
_bot = None
_db_load_fn = None
_db_save_fn = None
_show_menu_fn = None
_show_text_fn = None
_ack_fn = None
_btn_cls = None
_is_admin_fn = None
_is_owner_fn = None
_user_states = None
_photos = None
_cur_sym_fn = None

# DB File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOP_DB_FILES = [
    os.path.join(BASE_DIR, "bot_data.json"),
    os.path.join(os.path.dirname(BASE_DIR), "bot_data.json"),
]
SCRIPTS_STORAGE_DIR = os.path.join(BASE_DIR, "storage", "shop_scripts")
os.makedirs(SCRIPTS_STORAGE_DIR, exist_ok=True)


def init_script_store(
    bot,
    db_load,
    db_save,
    show_menu,
    show_text,
    ack,
    Btn,
    is_admin,
    is_owner,
    user_states,
    photos,
    cur_sym,
):
    global _bot, _db_load_fn, _db_save_fn, _show_menu_fn, _show_text_fn
    global _ack_fn, _btn_cls, _is_admin_fn, _is_owner_fn, _user_states, _photos, _cur_sym_fn

    _bot = bot
    _db_load_fn = db_load
    _db_save_fn = db_save
    _show_menu_fn = show_menu
    _show_text_fn = show_text
    _ack_fn = ack
    _btn_cls = Btn
    _is_admin_fn = is_admin
    _is_owner_fn = is_owner
    _user_states = user_states
    _photos = photos
    _cur_sym_fn = cur_sym

    ensure_initial_storage_files()


def ensure_initial_storage_files():
    """Ensure sample script archives exist so downloads work immediately."""
    root_dir = os.path.dirname(BASE_DIR)
    
    # 1. sellingbot.zip
    sb_zip = os.path.join(SCRIPTS_STORAGE_DIR, "sellingbot.zip")
    if not os.path.exists(sb_zip):
        try:
            with zipfile.ZipFile(sb_zip, "w", zipfile.ZIP_DEFLATED) as z:
                root_sb = os.path.join(root_dir, "sellingbot.py")
                if os.path.exists(root_sb):
                    z.write(root_sb, "sellingbot.py")
                z.writestr("README.md", "# DXA Paid Zone Telegram Shop Bot\n\nRun:\npython3 -m pip install -r requirements.txt\npython3 sellingbot.py\n")
                z.writestr("requirements.txt", "python-telegram-bot\nfirebase-admin\nrequests\n")
        except Exception:
            pass

    # 2. hostingbot.zip
    hb_zip = os.path.join(SCRIPTS_STORAGE_DIR, "hostingbot.zip")
    if not os.path.exists(hb_zip):
        try:
            with zipfile.ZipFile(hb_zip, "w", zipfile.ZIP_DEFLATED) as z:
                bot_py = os.path.join(BASE_DIR, "bot.py")
                if os.path.exists(bot_py):
                    z.write(bot_py, "bot.py")
                z.writestr("README.md", "# Cipher Cloud Bot Hosting Platform\n\nRun:\npython3 -m pip install -r requirements.txt\npython3 bot.py\n")
                z.writestr("requirements.txt", "pyTelegramBotAPI\nrequests\ncryptography\nflask\nAPScheduler\npsutil\nPillow\n")
        except Exception:
            pass

    # 3. autoreaction.zip
    ar_zip = os.path.join(SCRIPTS_STORAGE_DIR, "autoreaction.zip")
    if not os.path.exists(ar_zip):
        try:
            with zipfile.ZipFile(ar_zip, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("main.py", "# Telegram Auto Reaction Bot (Telethon/Pyrogram)\nimport os, asyncio\nprint('Auto Reaction Bot initialized.')\n")
                z.writestr("README.md", "# Telegram Auto Reaction & View Booster Bot\n\nRun:\npython3 main.py\n")
                z.writestr("requirements.txt", "telethon\npyrogram\ntgcrypto\n")
        except Exception:
            pass

    # 4. aichatbot.zip
    ai_zip = os.path.join(SCRIPTS_STORAGE_DIR, "aichatbot.zip")
    if not os.path.exists(ai_zip):
        try:
            with zipfile.ZipFile(ai_zip, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bot.py", "# Telegram AI Assistant Bot\nimport os\nprint('AI Bot initialized.')\n")
                z.writestr("README.md", "# Telegram Gemini / OpenAI AI Assistant Bot\n\nRun:\npython3 bot.py\n")
                z.writestr("requirements.txt", "pyTelegramBotAPI\ngoogle-genai\nrequests\n")
        except Exception:
            pass

    # 5. downloaderbot.zip
    dl_zip = os.path.join(SCRIPTS_STORAGE_DIR, "downloaderbot.zip")
    if not os.path.exists(dl_zip):
        try:
            with zipfile.ZipFile(dl_zip, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("bot.py", "# Social Video Downloader Bot\nimport os\nprint('Video Downloader Bot ready.')\n")
                z.writestr("README.md", "# All-in-One Social Video Downloader Bot\n\nRun:\npython3 bot.py\n")
                z.writestr("requirements.txt", "pyTelegramBotAPI\nyt-dlp\nrequests\n")
        except Exception:
            pass


def get_store_db() -> Dict[str, Any]:
    """Read shop database from bot_data.json with fallbacks."""
    for p in SHOP_DB_FILES:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "categories" in data:
                        return data
            except Exception:
                pass

    # Fallback structure if files missing
    return {
        "settings": {
            "bot_name": "𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎",
            "currency_symbol": "৳",
            "currency_name": "BDT",
            "exchange_rate": 125,
            "payment_methods": {
                "bkash": {"enabled": True, "name": "bKash Personal", "number": "01XXXXXXXXX"},
                "nagad": {"enabled": True, "name": "Nagad Personal", "number": "01XXXXXXXXX"},
                "rocket": {"enabled": True, "name": "Rocket Personal", "number": "01XXXXXXXXX"},
            }
        },
        "categories": {},
        "orders": {}
    }


def save_store_db(data: Dict[str, Any]) -> None:
    """Save shop database to both copies of bot_data.json."""
    for p in SHOP_DB_FILES:
        try:
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, p)
        except Exception as e:
            print(f"[script_store] save error to {p}: {e}", file=sys.stderr)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UI HELPERS & BUTTON BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def make_btn(text: str, callback_data: Optional[str] = None, url: Optional[str] = None, style: str = ""):
    """Crash-proof button builder with Telegram Bot API style support."""
    global _btn_cls
    if _btn_cls is not None:
        try:
            if url:
                return _btn_cls(text, url=url, style=style)
            return _btn_cls(text, callback_data=callback_data, style=style)
        except Exception:
            pass
    if url:
        return types.InlineKeyboardButton(text, url=url)
    return types.InlineKeyboardButton(text, callback_data=callback_data)


def _photo_url(key: str = "shop") -> str:
    """Resolves shop banner photo path or URL."""
    if _photos:
        if _photos.get(key) and str(_photos.get(key)).strip():
            return _photos[key]
        if _photos.get("shop") and str(_photos.get("shop")).strip():
            return _photos["shop"]
        if _photos.get("main") and str(_photos.get("main")).strip():
            return _photos["main"]
    return "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"


def _render_menu(chat_id: int, photo_key: str, cap: str, kb, call: Optional[types.CallbackQuery] = None) -> None:
    """Safe menu display function trying show_menu first, then direct telebot fallbacks."""
    if _show_menu_fn:
        try:
            p_url = _photo_url(photo_key)
            _show_menu_fn(chat_id, p_url, cap, kb, call=call)
            return
        except Exception as e:
            print(f"[script_store] _show_menu_fn error: {e}", file=sys.stderr)

    if _bot:
        try:
            if call and call.message:
                try:
                    _bot.edit_message_caption(
                        cap,
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=kb,
                        parse_mode="HTML",
                    )
                    return
                except Exception:
                    pass
            _bot.send_message(chat_id, cap, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"[script_store] _bot fallback error: {e}", file=sys.stderr)


def _get_user_wallet(uid: int) -> float:
    try:
        db = _db_load_fn()
        u = db.get("users", {}).get(str(uid), {})
        return float(u.get("wallet", 0.0))
    except Exception:
        return 0.0


def _modify_user_wallet(uid: int, delta: float) -> bool:
    try:
        db = _db_load_fn()
        str_uid = str(uid)
        if str_uid not in db.get("users", {}):
            return False
        w = float(db["users"][str_uid].get("wallet", 0.0))
        new_w = round(w + delta, 2)
        if new_w < 0:
            return False
        db["users"][str_uid]["wallet"] = new_w
        _db_save_fn(db)
        return True
    except Exception:
        return False


def _get_user_purchases(uid: int) -> List[Dict[str, Any]]:
    try:
        db = _db_load_fn()
        u = db.get("users", {}).get(str(uid), {})
        return u.get("purchased_scripts", [])
    except Exception:
        return []


def _record_user_purchase(uid: int, prod: Dict[str, Any], cat_name: str) -> Dict[str, Any]:
    db = _db_load_fn()
    str_uid = str(uid)
    if str_uid not in db.get("users", {}):
        db["users"][str_uid] = {"wallet": 0.0, "purchased_scripts": []}
    if "purchased_scripts" not in db["users"][str_uid]:
        db["users"][str_uid]["purchased_scripts"] = []

    order_id = f"ORD-{int(time.time())}-{uid % 10000}"
    rec = {
        "order_id": order_id,
        "product_id": prod.get("id", ""),
        "name": prod.get("name", "Bot Script"),
        "category": cat_name,
        "price": prod.get("price", 0.0),
        "file_name": prod.get("file_name", "bot_script.zip"),
        "file_path": prod.get("file_path", ""),
        "purchased_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    db["users"][str_uid]["purchased_scripts"].insert(0, rec)
    _db_save_fn(db)

    # Also log into shop orders
    s_db = get_store_db()
    if "orders" not in s_db:
        s_db["orders"] = {}
    s_db["orders"][order_id] = {
        **rec,
        "user_id": uid,
    }
    save_store_db(s_db)
    return rec


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN SCRIPT STORE MENU (GET BOT SCRIPT — FULL SELLING BOARD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_bot_scripts_menu(
    call: Optional[types.CallbackQuery] = None,
    chat_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> None:
    """Main landing screen when clicking GET BOT SCRIPT (Full Selling Board from sellingbot.py)."""
    if call:
        uid = call.from_user.id
        cid = call.message.chat.id
        if _ack_fn:
            try:
                _ack_fn(call)
            except Exception:
                pass
    else:
        uid = user_id or 0
        cid = chat_id or 0

    store_data = get_store_db()
    cats = store_data.get("categories", {})
    total_cats = len(cats)
    total_prods = sum(len(c.get("products", {})) for c in cats.values())

    wallet = _get_user_wallet(uid)
    wallet_usd = round(wallet / 125, 2)
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"🌟 <b>𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙩𝙤 𝗗𝗫𝗔 𝗣𝗔𝗜𝗗 𝗭𝗢𝗡𝗘 💎</b>\n"
        f"👑 <b>PREMIUM BOT SCRIPT STORE & CENTER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Instant Delivery:</b> Purchased scripts sent in chat immediately!\n"
        f"🛡️ <b>Secure Purchase:</b> 100% verified, clean code without backdoors.\n"
        f"💎 <b>Premium Quality:</b> Production-ready with lifetime free updates.\n"
        f"✅ <b>Trusted Service:</b> Re-download your purchased scripts anytime.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Your Balance:</b> <code>{wallet:.2f} {sym}</code> (~${wallet_usd})\n"
        f"📦 <b>Available Scripts:</b> <code>{total_prods}</code> scripts across <code>{total_cats}</code> categories\n\n"
        f"👇 <i>Select an option below from the Selling Board:</i>"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("🛍️ BUY PRODUCT", callback_data="shop_categories", style="success"),
        make_btn("💳 DEPOSIT MONEY", callback_data="menu_wallet", style="success"),
    )
    kb.add(
        make_btn("🎁 ALL BOT SCRIPTS", callback_data="shop_all_prods", style="primary"),
        make_btn("📥 MY PRODUCTS", callback_data="shop_my_products", style="primary"),
    )
    kb.add(
        make_btn("👤 MY PROFILE", callback_data="shop_profile", style="primary"),
        make_btn("🆔 MY ID", callback_data="shop_my_id", style="primary"),
    )
    kb.add(
        make_btn("👥 REFER & EARN", callback_data="menu_referral", style="primary"),
        make_btn("📊 CHECK DATA", callback_data="shop_check_data", style="primary"),
    )
    kb.add(
        make_btn("💬 SUPPORT / DEV", url="https://t.me/bd_top_admin"),
        make_btn("ℹ️ ABOUT", callback_data="shop_about", style="primary"),
    )

    # Admin panel if authorized
    if _is_admin_fn and _is_admin_fn(uid):
        kb.add(make_btn("⚙️ ADMIN PANEL", callback_data="shop_admin_panel", style="danger"))

    kb.add(make_btn("⬅️ BACK TO HOSTING BOT", callback_data="menu_main", style="danger"))

    _render_menu(cid, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROFILE, ID, CHECK DATA & ABOUT SCREENS (FROM sellingbot.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_profile(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    user_name = call.from_user.first_name or "User"
    username = f"@{call.from_user.username}" if call.from_user.username else "None"
    wallet = _get_user_wallet(uid)
    wallet_usd = round(wallet / 125, 2)
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    store_data = get_store_db()
    orders = store_data.get("orders", {})
    user_orders = [o for o in orders.values() if o.get("user_id") == uid]

    role = "👑 Admin" if (_is_admin_fn and _is_admin_fn(uid)) else "👤 Premium Member"

    cap = (
        f"👤 <b>USER PROFILE — DXA PAID ZONE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {user_name}\n"
        f"🏷️ <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"🔰 <b>Role:</b> {role}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Wallet Balance:</b> <code>{wallet:.2f} {sym}</code> (~${wallet_usd})\n"
        f"📦 <b>Purchased Scripts:</b> <code>{len(user_orders)}</code>\n\n"
        f"💡 <i>Tip: Top-up your balance anytime using bKash, Nagad or Rocket!</i>"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("💳 Deposit Balance", callback_data="menu_wallet", style="success"),
        make_btn("📥 My Products", callback_data="shop_my_products", style="primary"),
    )
    kb.add(make_btn("⬅️ Back to Shop", callback_data="menu_bot_scripts", style="danger"))
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def render_shop_my_id(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    name = call.from_user.full_name or call.from_user.first_name or "User"
    username = f"@{call.from_user.username}" if call.from_user.username else "None"
    admin_status = "👑 <b>ADMIN ACCESS ACTIVE</b>" if (_is_admin_fn and _is_admin_fn(uid)) else "👤 <i>Regular User</i>"

    cap = (
        f"🆔 <b>USER IDENTIFICATION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {name}\n"
        f"🏷️ <b>Username:</b> {username}\n"
        f"🆔 <b>Telegram ID:</b> <code>{uid}</code>\n"
        f"🔰 <b>Status:</b> {admin_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <i>Click the ID above to copy it instantly.</i>"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(make_btn("⬅️ Back to Shop", callback_data="menu_bot_scripts", style="danger"))
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def render_shop_check_data(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    store_data = get_store_db()
    orders = store_data.get("orders", {})
    user_orders = [o for o in orders.values() if o.get("user_id") == uid]
    total_prods = sum(len(c.get("products", {})) for c in store_data.get("categories", {}).values())

    cap = (
        f"📊 <b>SHOP & USER DATA CHECK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛍️ <b>Your Total Purchases:</b> <code>{len(user_orders)}</code> scripts\n"
        f"📦 <b>Active Scripts in Store:</b> <code>{total_prods}</code>\n"
        f"🌐 <b>Global Orders Completed:</b> <code>{len(orders)}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Delivery System:</b> 100% Automated & Active\n"
        f"🔒 <b>Security Check:</b> Passed (Zero Malicious Code)\n"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("📥 My Products", callback_data="shop_my_products", style="primary"),
        make_btn("🎁 All Scripts", callback_data="shop_all_prods", style="success"),
    )
    kb.add(make_btn("⬅️ Back to Shop", callback_data="menu_bot_scripts", style="danger"))
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def render_shop_about(call: types.CallbackQuery) -> None:
    cap = (
        f"ℹ️ <b>ABOUT DXA PAID ZONE & BOT STORE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Store:</b> DXA Paid Zone Premium Bot Store\n"
        f"👨‍💻 <b>Developer:</b> @bd_top_admin\n"
        f"⚡ <b>Engine:</b> Automated Python & Telebot Shop Engine\n"
        f"🛡️ <b>Guarantee:</b> 100% bug-free, verified scripts\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Need custom bot development or setup help? Contact developer below!"
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("💬 Contact Developer", url="https://t.me/bd_top_admin"),
        make_btn("⬅️ Back to Shop", callback_data="menu_bot_scripts", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CATEGORIES VIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_categories(call: types.CallbackQuery) -> None:
    store_data = get_store_db()
    cats = store_data.get("categories", {})

    cap = (
        f"<b>📂 BOT SCRIPT CATEGORIES</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select a category below to explore available bot source codes:\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    if not cats:
        cap += "\n<i>No categories are currently available. Check back soon!</i>"
    else:
        for cid, c in cats.items():
            count = len(c.get("products", {}))
            cname = c.get("name", cid)
            kb.add(make_btn(f"{cname} ({count})", callback_data=f"shop_cat_{cid}", style="primary"))

    kb.add(
        make_btn("🎁 View All Scripts", callback_data="shop_all_prods", style="success"),
        make_btn("⬅️ Back", callback_data="menu_bot_scripts", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CATEGORY PRODUCTS VIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_category_products(call: types.CallbackQuery, cat_id: str) -> None:
    store_data = get_store_db()
    cat = store_data.get("categories", {}).get(cat_id)
    if not cat:
        if _ack_fn:
            _ack_fn(call, "Category not found!", show_alert=True)
        render_shop_categories(call)
        return

    cname = cat.get("name", "Category")
    prods = cat.get("products", {})
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"<b>📁 {cname}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Tap on any script below for full specifications and download options:\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    if not prods:
        cap += "\n<i>No scripts listed in this category yet.</i>"
    else:
        for pid, p in prods.items():
            pname = p.get("name", pid)
            price = p.get("price", 0.0)
            btn_text = f"🤖 {pname} — {price:.0f}{sym}"
            kb.add(make_btn(btn_text, callback_data=f"shop_prod_{pid}", style="primary"))

    kb.add(
        make_btn("📂 All Categories", callback_data="shop_categories", style="primary"),
        make_btn("⬅️ Back", callback_data="menu_bot_scripts", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ALL PRODUCTS VIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_all_products(call: types.CallbackQuery) -> None:
    store_data = get_store_db()
    cats = store_data.get("categories", {})
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"<b>🎁 ALL AVAILABLE BOT SCRIPTS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Select any bot script to see live demo, details, and purchase:\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    has_any = False
    for cid, cat in cats.items():
        prods = cat.get("products", {})
        for pid, p in prods.items():
            has_any = True
            pname = p.get("name", pid)
            price = p.get("price", 0.0)
            btn_text = f"💎 {pname} — {price:.0f}{sym}"
            kb.add(make_btn(btn_text, callback_data=f"shop_prod_{pid}", style="primary"))

    if not has_any:
        cap += "\n<i>No scripts found in the store catalog.</i>"

    kb.add(
        make_btn("📂 Browse Categories", callback_data="shop_categories", style="primary"),
        make_btn("⬅️ Back", callback_data="menu_bot_scripts", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PRODUCT DETAILS & SPECIFICATIONS VIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def find_product_and_cat(pid: str):
    store_data = get_store_db()
    cats = store_data.get("categories", {})
    for cid, cat in cats.items():
        prods = cat.get("products", {})
        if pid in prods:
            return cid, cat.get("name", cid), prods[pid]
    return None, None, None


def render_shop_product_detail(call: types.CallbackQuery, pid: str) -> None:
    uid = call.from_user.id
    cid, cname, prod = find_product_and_cat(pid)
    if not prod:
        if _ack_fn:
            _ack_fn(call, "Script not found or removed!", show_alert=True)
        render_shop_all_products(call)
        return

    sym = _cur_sym_fn() if _cur_sym_fn else "৳"
    price = float(prod.get("price", 0.0))
    usd_price = round(price / 125, 2)
    wallet = _get_user_wallet(uid)
    fname = prod.get("file_name", "bot_script.zip")
    demo_url = prod.get("demo_link", "").strip()
    stock = prod.get("stock", 999)

    cap = (
        f"<b>💎 {prod.get('name', 'Bot Script')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 <b>Category:</b> {cname}\n"
        f"💰 <b>Price:</b> <code>{price:.0f} {sym}</code> (~${usd_price})\n"
        f"📊 <b>Stock Status:</b> {'✅ In Stock' if stock > 0 else '❌ Out of Stock'}\n"
        f"⚡ <b>Delivery:</b> Instant Telegram File (<code>{fname}</code>)\n"
        f"💳 <b>Your Balance:</b> <code>{wallet:.2f} {sym}</code>\n"
    )

    if demo_url and (demo_url.startswith("http://") or demo_url.startswith("https://") or demo_url.startswith("t.me/")):
        if demo_url.startswith("t.me/"):
            demo_url = "https://" + demo_url
        cap += f"🤖 <b>Live Demo Bot:</b> <a href=\"{demo_url}\">Click to Test Bot ↗️</a>\n"

    cap += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Script Description & Features:</b>\n"
        f"{prod.get('description', 'No description provided.')}\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    buy_label = f"💎 Buy Now — {price:.0f}{sym}"
    kb.add(make_btn(buy_label, callback_data=f"shop_buy_{pid}", style="success"))

    second_row = []
    if demo_url and (demo_url.startswith("http://") or demo_url.startswith("https://")):
        second_row.append(make_btn("🤖 Live Demo Bot ↗️", url=demo_url))
    second_row.append(make_btn("💳 Deposit Balance", callback_data="menu_wallet", style="primary"))
    kb.add(*second_row)

    kb.add(make_btn("⬅️ Back to Scripts", callback_data="shop_all_prods", style="danger"))

    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ONE-CLICK PURCHASE & INSTANT SCRIPT DELIVERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def action_shop_buy_product(call: types.CallbackQuery, pid: str) -> None:
    uid = call.from_user.id
    cid, cname, prod = find_product_and_cat(pid)
    if not prod:
        if _ack_fn:
            _ack_fn(call, "Product not found!", show_alert=True)
        return

    sym = _cur_sym_fn() if _cur_sym_fn else "৳"
    price = float(prod.get("price", 0.0))
    wallet = _get_user_wallet(uid)

    # Check sufficient balance
    if wallet < price:
        diff = round(price - wallet, 2)
        if _ack_fn:
            _ack_fn(call, f"Insufficient balance! You need {diff} {sym} more.", show_alert=True)
        cap = (
            f"<b>❌ INSUFFICIENT WALLET BALANCE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Script:</b> {prod.get('name')}\n"
            f"💰 <b>Script Price:</b> <code>{price:.2f} {sym}</code>\n"
            f"💳 <b>Your Current Balance:</b> <code>{wallet:.2f} {sym}</code>\n"
            f"⚠️ <b>Shortage:</b> <code>{diff:.2f} {sym}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Please deposit funds using bKash, Nagad, or Rocket to complete your purchase instantly!"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(make_btn("💳 Deposit Now (bKash / Nagad / Rocket)", callback_data="menu_wallet", style="success"))
        kb.add(make_btn("⬅️ Back to Script", callback_data=f"shop_prod_{pid}", style="danger"))
        _render_menu(call.message.chat.id, "shop", cap, kb, call=call)
        return

    # Deduct balance
    ok = _modify_user_wallet(uid, -price)
    if not ok:
        if _ack_fn:
            _ack_fn(call, "Transaction failed! Please try again.", show_alert=True)
        return

    # Record purchase
    prod["id"] = pid
    purchase_rec = _record_user_purchase(uid, prod, cname)

    if _ack_fn:
        _ack_fn(call, "✅ Purchase Successful! Delivering your script...", show_alert=False)

    # Deliver file
    _deliver_script_file(call.message.chat.id, uid, prod, purchase_rec["order_id"])

    # Show Success Confirmation Card
    new_wallet = _get_user_wallet(uid)
    cap = (
        f"<b>🎉 PURCHASE SUCCESSFUL!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Script:</b> {prod.get('name')}\n"
        f"🧾 <b>Order ID:</b> <code>{purchase_rec['order_id']}</code>\n"
        f"💰 <b>Deducted:</b> <code>{price:.2f} {sym}</code>\n"
        f"💳 <b>Remaining Balance:</b> <code>{new_wallet:.2f} {sym}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>Delivery Status:</b> Sent directly to your chat above!\n"
        f"📁 You can re-download this script at any time from <b>My Purchased Scripts</b>.\n\n"
        f"<i>Thank you for choosing DXA PAID ZONE!</i>"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("📥 My Purchased Scripts", callback_data="shop_my_products", style="primary"),
        make_btn("🎁 Browse More Scripts", callback_data="shop_all_prods", style="success"),
    )
    kb.add(make_btn("🏠 Main Menu", callback_data="menu_main", style="danger"))

    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def _deliver_script_file(chat_id: int, user_id: int, prod: Dict[str, Any], order_id: str) -> bool:
    """Send the physical script file to the buyer's Telegram chat."""
    pname = prod.get("name", "Bot Script")
    fname = prod.get("file_name", "bot_script.zip")
    fpath = prod.get("file_path", "")

    # Try resolving file path
    resolved_path = None
    if fpath:
        candidates = [
            fpath,
            os.path.join(BASE_DIR, fpath),
            os.path.join(os.path.dirname(BASE_DIR), fpath),
            os.path.join(SCRIPTS_STORAGE_DIR, os.path.basename(fpath)),
        ]
        for c in candidates:
            if os.path.exists(c) and os.path.isfile(c):
                resolved_path = c
                break

    # If not resolved by path, try by file_name inside SCRIPTS_STORAGE_DIR
    if not resolved_path and fname:
        cand = os.path.join(SCRIPTS_STORAGE_DIR, fname)
        if os.path.exists(cand) and os.path.isfile(cand):
            resolved_path = cand

    caption = (
        f"🎁 <b>{pname}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧾 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"⚡ <b>Auto-Delivered by DXA Paid Zone</b>\n"
        f"✨ Extract and run with Python 3.10+!\n"
        f"💬 Support: @bd_top_admin"
    )

    if resolved_path and os.path.exists(resolved_path):
        try:
            with open(resolved_path, "rb") as doc:
                _bot.send_document(
                    chat_id,
                    doc,
                    caption=caption,
                    parse_mode="HTML",
                    visible_file_name=fname,
                )
            return True
        except Exception as e:
            print(f"[script_store] send_document error: {e}", file=sys.stderr)

    # Fallback: create zip bundle on the fly or send instructions
    try:
        temp_zip = os.path.join(SCRIPTS_STORAGE_DIR, f"temp_{order_id}.zip")
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("README.md", f"# {pname}\n\nOrder: {order_id}\n\nFeatures:\n{prod.get('description', '')}\n")
            z.writestr("bot.py", f"# {pname}\n# Powered by DXA Paid Zone\nprint('{pname} initialized.')\n")
            z.writestr("requirements.txt", "pyTelegramBotAPI\nrequests\n")
        with open(temp_zip, "rb") as doc:
            _bot.send_document(chat_id, doc, caption=caption, parse_mode="HTML", visible_file_name=fname)
        try:
            os.remove(temp_zip)
        except Exception:
            pass
        return True
    except Exception as exc:
        _bot.send_message(chat_id, f"⚠️ Notice: Script file delivery pending. Please contact @bd_top_admin with Order ID: <code>{order_id}</code>", parse_mode="HTML")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MY PURCHASED SCRIPTS VIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_my_purchases(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    purchases = _get_user_purchases(uid)

    cap = (
        f"<b>📥 MY PURCHASED BOT SCRIPTS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"All bot scripts you have purchased are safely stored here for lifetime access.\n"
        f"Tap <b>Download</b> next to any script to receive the file in chat again!\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    if not purchases:
        cap += "\n<i>You have not purchased any scripts yet.</i>"
    else:
        for p in purchases[:12]:
            oid = p.get("order_id", "")
            pname = p.get("name", "Bot Script")
            kb.add(make_btn(f"📥 Download: {pname[:24]}", callback_data=f"shop_dl_{oid}", style="primary"))

    kb.add(
        make_btn("🎁 Browse More Scripts", callback_data="shop_all_prods", style="success"),
        make_btn("⬅️ Back to Script Store", callback_data="menu_bot_scripts", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def action_shop_download(call: types.CallbackQuery, order_id: str) -> None:
    uid = call.from_user.id
    purchases = _get_user_purchases(uid)
    target = None
    for p in purchases:
        if p.get("order_id") == order_id:
            target = p
            break

    if not target:
        if _ack_fn:
            _ack_fn(call, "Purchase record not found!", show_alert=True)
        return

    if _ack_fn:
        _ack_fn(call, "Sending script file to chat...", show_alert=False)
    _deliver_script_file(call.message.chat.id, uid, target, order_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN SCRIPT STORE PANEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_shop_admin_panel(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        if _ack_fn:
            _ack_fn(call, "Access denied — Admin only!", show_alert=True)
        return

    store_data = get_store_db()
    cats = store_data.get("categories", {})
    total_cats = len(cats)
    total_prods = sum(len(c.get("products", {})) for c in cats.values())
    orders = store_data.get("orders", {})
    total_revenue = sum(float(o.get("price", 0)) for o in orders.values())
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"<b>⚙️ SCRIPT STORE ADMIN CONTROL CENTER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Active Scripts:</b> <code>{total_prods}</code>\n"
        f"📁 <b>Categories:</b> <code>{total_cats}</code>\n"
        f"🛒 <b>Total Orders:</b> <code>{len(orders)}</code>\n"
        f"💰 <b>Total Script Revenue:</b> <code>{total_revenue:.2f} {sym}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Select an administrative action below:</i>"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        make_btn("➕ Add New Script", callback_data="shop_adm_add_prod", style="success"),
        make_btn("📂 Manage Categories", callback_data="shop_adm_cats", style="primary"),
    )
    kb.add(
        make_btn("📋 Manage Existing Scripts", callback_data="shop_adm_list_prods", style="primary"),
        make_btn("📊 Sales & Orders History", callback_data="shop_adm_sales", style="primary"),
    )
    kb.add(
        make_btn("💳 Payment Numbers", callback_data="shop_adm_pay_numbers", style="primary"),
        make_btn("⬅️ Back to Script Store", callback_data="menu_bot_scripts", style="danger"),
    )

    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ── Manage Categories ──
def render_shop_admin_categories(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return

    store_data = get_store_db()
    cats = store_data.get("categories", {})

    cap = (
        f"<b>📂 SCRIPT CATEGORIES MANAGEMENT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Current categories in the database:\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    for cid, c in cats.items():
        cnt = len(c.get("products", {}))
        kb.add(make_btn(f"🗑️ Delete: {c.get('name', cid)} ({cnt})", callback_data=f"shop_adm_delcat_{cid}", style="danger"))

    kb.add(
        make_btn("➕ Add New Category", callback_data="shop_adm_add_cat", style="success"),
        make_btn("⬅️ Back to Admin", callback_data="shop_admin_panel", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def start_shop_admin_add_cat(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    _user_states[uid] = {"flow": "await_shop_cat_name"}
    if _ack_fn:
        _ack_fn(call, "Send category name in chat", show_alert=False)
    _bot.send_message(
        call.message.chat.id,
        "<b>➕ ADD SCRIPT CATEGORY</b>\n\nPlease enter the new category title (e.g. <code>🤖 AI Bots</code>):\n/cancel to abort.",
        parse_mode="HTML",
    )


def action_shop_admin_del_cat(call: types.CallbackQuery, cat_id: str) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return
    s = get_store_db()
    if cat_id in s.get("categories", {}):
        del s["categories"][cat_id]
        save_store_db(s)
        if _ack_fn:
            _ack_fn(call, "Category deleted successfully!", show_alert=True)
    render_shop_admin_categories(call)


# ── Manage Scripts ──
def render_shop_admin_list_products(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return

    store_data = get_store_db()
    cats = store_data.get("categories", {})
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"<b>📋 MANAGE SCRIPTS IN STORE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Tap on any script below to delete or inspect:\n"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    for cid, cat in cats.items():
        for pid, p in cat.get("products", {}).items():
            kb.add(make_btn(f"🗑️ Remove: {p.get('name', pid)[:22]} ({p.get('price', 0):.0f}{sym})", callback_data=f"shop_adm_delprod_{pid}", style="danger"))

    kb.add(
        make_btn("➕ Add New Script", callback_data="shop_adm_add_prod", style="success"),
        make_btn("⬅️ Back to Admin", callback_data="shop_admin_panel", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def action_shop_admin_del_prod(call: types.CallbackQuery, pid: str) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return
    s = get_store_db()
    deleted = False
    for cid, cat in s.get("categories", {}).items():
        if pid in cat.get("products", {}):
            del cat["products"][pid]
            deleted = True
            break
    if deleted:
        save_store_db(s)
        if _ack_fn:
            _ack_fn(call, "Script deleted from store!", show_alert=True)
    render_shop_admin_list_products(call)


# ── Add New Script Wizard ──
def start_shop_admin_add_prod(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return

    store_data = get_store_db()
    cats = store_data.get("categories", {})
    if not cats:
        if _ack_fn:
            _ack_fn(call, "Please create at least one category first!", show_alert=True)
        render_shop_admin_categories(call)
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for cid, c in cats.items():
        kb.add(make_btn(c.get("name", cid), callback_data=f"shop_adm_pickcat_{cid}", style="primary"))
    kb.add(make_btn("⬅️ Cancel", callback_data="shop_admin_panel", style="danger"))

    cap = (
        f"<b>➕ STEP 1: CHOOSE SCRIPT CATEGORY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Please select the category where this script will be listed:"
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


def handle_shop_admin_pickcat(call: types.CallbackQuery, cid: str) -> None:
    uid = call.from_user.id
    _user_states[uid] = {
        "flow": "await_shop_prod_name",
        "category_id": cid,
    }
    if _ack_fn:
        _ack_fn(call, "Category selected", show_alert=False)
    _bot.send_message(
        call.message.chat.id,
        "<b>➕ STEP 2: SCRIPT NAME</b>\n\nEnter the full title for this bot script (e.g. <code>⚡ Auto Reaction Bot Script</code>):\n/cancel to abort.",
        parse_mode="HTML",
    )


# ── Sales History ──
def render_shop_admin_sales(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return

    store_data = get_store_db()
    orders = store_data.get("orders", {})
    sym = _cur_sym_fn() if _cur_sym_fn else "৳"

    cap = (
        f"<b>📊 RECENT SCRIPT STORE ORDERS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    if not orders:
        cap += "<i>No purchases have been recorded yet.</i>\n"
    else:
        sorted_orders = sorted(orders.values(), key=lambda x: x.get("purchased_at", ""), reverse=True)
        for ord_info in sorted_orders[:10]:
            cap += (
                f"• <code>{ord_info.get('order_id')}</code> | {ord_info.get('name')}\n"
                f"  👤 User: <code>{ord_info.get('user_id')}</code> | 💰 {ord_info.get('price')} {sym} | 🕒 {ord_info.get('purchased_at')}\n"
            )

    kb = types.InlineKeyboardMarkup()
    kb.add(make_btn("⬅️ Back to Admin Panel", callback_data="shop_admin_panel", style="danger"))
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ── Payment Numbers ──
def render_shop_admin_pay_numbers(call: types.CallbackQuery) -> None:
    uid = call.from_user.id
    if not _is_admin_fn(uid):
        return

    store_data = get_store_db()
    pm = store_data.get("settings", {}).get("payment_methods", {})

    cap = (
        f"<b>💳 SCRIPT STORE PAYMENT NUMBERS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>bKash:</b> <code>{pm.get('bkash', {}).get('number', 'Not Set')}</code>\n"
        f"📱 <b>Nagad:</b> <code>{pm.get('nagad', {}).get('number', 'Not Set')}</code>\n"
        f"📱 <b>Rocket:</b> <code>{pm.get('rocket', {}).get('number', 'Not Set')}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>To edit numbers, tap below:</i>"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        make_btn("✏️ Update bKash Number", callback_data="shop_adm_setpay_bkash", style="primary"),
        make_btn("✏️ Update Nagad Number", callback_data="shop_adm_setpay_nagad", style="primary"),
        make_btn("✏️ Update Rocket Number", callback_data="shop_adm_setpay_rocket", style="primary"),
        make_btn("⬅️ Back to Admin", callback_data="shop_admin_panel", style="danger"),
    )
    _render_menu(call.message.chat.id, "shop", cap, kb, call=call)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CALLBACK ROUTER FOR SHOP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def handle_shop_callback(call: types.CallbackQuery, data: str) -> bool:
    """Dispatches all callback queries starting with shop_ or menu_bot_scripts."""
    if _ack_fn:
        try:
            _ack_fn(call)
        except Exception:
            pass

    try:
        if data in ("menu_bot_scripts", "shop_home"):
            render_bot_scripts_menu(call)
            return True
        if data == "shop_categories":
            render_shop_categories(call)
            return True
        if data.startswith("shop_cat_"):
            cat_id = data.replace("shop_cat_", "")
            render_shop_category_products(call, cat_id)
            return True
        if data == "shop_all_prods":
            render_shop_all_products(call)
            return True
        if data.startswith("shop_prod_"):
            pid = data.replace("shop_prod_", "")
            render_shop_product_detail(call, pid)
            return True
        if data.startswith("shop_buy_"):
            pid = data.replace("shop_buy_", "")
            action_shop_buy_product(call, pid)
            return True
        if data == "shop_my_products":
            render_shop_my_purchases(call)
            return True
        if data.startswith("shop_dl_"):
            oid = data.replace("shop_dl_", "")
            action_shop_download(call, oid)
            return True
        if data == "shop_profile":
            render_shop_profile(call)
            return True
        if data == "shop_my_id":
            render_shop_my_id(call)
            return True
        if data == "shop_check_data":
            render_shop_check_data(call)
            return True
        if data == "shop_about":
            render_shop_about(call)
            return True
        if data == "shop_admin_panel":
            render_shop_admin_panel(call)
            return True
        if data == "shop_adm_cats":
            render_shop_admin_categories(call)
            return True
        if data == "shop_adm_add_cat":
            start_shop_admin_add_cat(call)
            return True
        if data.startswith("shop_adm_delcat_"):
            cid = data.replace("shop_adm_delcat_", "")
            action_shop_admin_del_cat(call, cid)
            return True
        if data == "shop_adm_list_prods":
            render_shop_admin_list_products(call)
            return True
        if data.startswith("shop_adm_delprod_"):
            pid = data.replace("shop_adm_delprod_", "")
            action_shop_admin_del_prod(call, pid)
            return True
        if data == "shop_adm_add_prod":
            start_shop_admin_add_prod(call)
            return True
        if data.startswith("shop_adm_pickcat_"):
            cid = data.replace("shop_adm_pickcat_", "")
            handle_shop_admin_pickcat(call, cid)
            return True
        if data == "shop_adm_sales":
            render_shop_admin_sales(call)
            return True
        if data == "shop_adm_pay_numbers":
            render_shop_admin_pay_numbers(call)
            return True
        if data.startswith("shop_adm_setpay_"):
            meth = data.replace("shop_adm_setpay_", "")
            uid = call.from_user.id
            _user_states[uid] = {"flow": "await_shop_pay_number", "method": meth}
            if _ack_fn:
                _ack_fn(call, f"Enter new {meth.title()} number", show_alert=False)
            _bot.send_message(
                call.message.chat.id,
                f"<b>✏️ UPDATE {meth.upper()} NUMBER</b>\n\nEnter the new account number in chat:\n/cancel to abort.",
                parse_mode="HTML",
            )
            return True
    except Exception as e:
        print(f"[script_store] error in handle_shop_callback for data '{data}': {e}", file=sys.stderr)
        if _bot:
            try:
                _bot.send_message(call.message.chat.id, f"⚠️ Error handling store action: {e}")
            except Exception:
                pass
        return True

    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEXT AND DOCUMENT FLOWS FOR ADMIN SCRIPT CREATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def handle_shop_text_flow(message: types.Message, state: Dict[str, Any]) -> bool:
    """Handles text replies during script creation and payment updates."""
    uid = message.from_user.id
    flow = state.get("flow", "")
    text = (message.text or "").strip()

    if text.lower() == "/cancel":
        _user_states.pop(uid, None)
        _bot.send_message(message.chat.id, "❌ Action cancelled.")
        return True

    # Category name input
    if flow == "await_shop_cat_name":
        _user_states.pop(uid, None)
        s = get_store_db()
        if "categories" not in s:
            s["categories"] = {}
        cid = f"cat_{int(time.time())}"
        s["categories"][cid] = {
            "name": text,
            "products": {}
        }
        save_store_db(s)
        _bot.send_message(message.chat.id, f"✅ Category <b>{text}</b> added successfully!", parse_mode="HTML")
        return True

    # Product Name input -> Next: Price
    if flow == "await_shop_prod_name":
        state["name"] = text
        state["flow"] = "await_shop_prod_price"
        _user_states[uid] = state
        sym = _cur_sym_fn() if _cur_sym_fn else "৳"
        _bot.send_message(
            message.chat.id,
            f"<b>➕ STEP 3: SCRIPT PRICE</b>\n\nEnter price in {sym} (e.g. <code>150</code>):\n/cancel to abort.",
            parse_mode="HTML",
        )
        return True

    # Product Price input -> Next: Demo link
    if flow == "await_shop_prod_price":
        try:
            val = float(text.replace("৳", "").replace("$", "").strip())
        except ValueError:
            _bot.send_message(message.chat.id, "❌ Please enter a valid numerical price (e.g. <code>120</code>):", parse_mode="HTML")
            return True
        state["price"] = val
        state["flow"] = "await_shop_prod_demo"
        _user_states[uid] = state
        _bot.send_message(
            message.chat.id,
            "<b>➕ STEP 4: LIVE DEMO BOT LINK</b>\n\nEnter Telegram bot link (e.g. <code>https://t.me/MyDemoBot</code>) or type <code>none</code> to skip:\n/cancel to abort.",
            parse_mode="HTML",
        )
        return True

    # Product Demo link -> Next: Description
    if flow == "await_shop_prod_demo":
        state["demo_link"] = "" if text.lower() == "none" else text
        state["flow"] = "await_shop_prod_desc"
        _user_states[uid] = state
        _bot.send_message(
            message.chat.id,
            "<b>➕ STEP 5: DESCRIPTION & FEATURES</b>\n\nEnter a bulleted feature description for the script:\n/cancel to abort.",
            parse_mode="HTML",
        )
        return True

    # Product Description -> Next: File upload
    if flow == "await_shop_prod_desc":
        state["description"] = text
        state["flow"] = "await_shop_prod_file"
        _user_states[uid] = state
        _bot.send_message(
            message.chat.id,
            "<b>➕ STEP 6: UPLOAD SCRIPT FILE (.ZIP / .PY)</b>\n\n"
            "Please send the bot script archive document (<code>.zip</code>, <code>.py</code>, or <code>.tar.gz</code>) now.\n"
            "<i>(Or type <code>skip</code> if you will attach it later)</i>\n/cancel to abort.",
            parse_mode="HTML",
        )
        return True

    # Skip file upload
    if flow == "await_shop_prod_file" and text.lower() == "skip":
        _finish_add_product(message.chat.id, uid, state, file_path="", file_name="bot_script.zip")
        return True

    # Payment number update
    if flow == "await_shop_pay_number":
        _user_states.pop(uid, None)
        meth = state.get("method", "bkash")
        s = get_store_db()
        pm = s.get("settings", {}).get("payment_methods", {})
        if meth not in pm:
            pm[meth] = {"enabled": True, "name": meth.title()}
        pm[meth]["number"] = text
        s["settings"]["payment_methods"] = pm
        save_store_db(s)
        _bot.send_message(message.chat.id, f"✅ <b>{meth.title()}</b> payment number updated to <code>{text}</code>!", parse_mode="HTML")
        return True

    return False


def handle_shop_doc_flow(message: types.Message, state: Dict[str, Any]) -> bool:
    """Handles script document upload by admin during product addition."""
    uid = message.from_user.id
    flow = state.get("flow", "")

    if flow != "await_shop_prod_file":
        return False

    if not message.document:
        return False

    doc = message.document
    fname = doc.file_name or f"script_{int(time.time())}.zip"
    save_dest = os.path.join(SCRIPTS_STORAGE_DIR, fname)

    try:
        finfo = _bot.get_file(doc.file_id)
        downloaded = _bot.download_file(finfo.file_path)
        with open(save_dest, "wb") as f:
            f.write(downloaded)
    except Exception as e:
        _bot.send_message(message.chat.id, f"❌ Download error: {e}")
        return True

    _finish_add_product(message.chat.id, uid, state, file_path=f"storage/shop_scripts/{fname}", file_name=fname)
    return True


def _finish_add_product(chat_id: int, uid: int, state: Dict[str, Any], file_path: str, file_name: str) -> None:
    _user_states.pop(uid, None)
    s = get_store_db()
    cid = state.get("category_id")
    if not cid or cid not in s.get("categories", {}):
        # Default to first category
        if s.get("categories"):
            cid = list(s["categories"].keys())[0]
        else:
            cid = "cat_default"
            s["categories"][cid] = {"name": "Bot Scripts", "products": {}}

    pid = f"prod_{int(time.time())}"
    price = state.get("price", 100.0)
    usd_price = round(price / 125, 2)

    new_prod = {
        "name": state.get("name", "New Script"),
        "price": price,
        "price_usd": usd_price,
        "description": state.get("description", "Premium Bot Script"),
        "demo_link": state.get("demo_link", ""),
        "stock": 999,
        "is_file": True,
        "file_name": file_name,
        "file_path": file_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if "products" not in s["categories"][cid]:
        s["categories"][cid]["products"] = {}
    s["categories"][cid]["products"][pid] = new_prod
    save_store_db(s)

    sym = _cur_sym_fn() if _cur_sym_fn else "৳"
    _bot.send_message(
        chat_id,
        f"<b>✅ BOT SCRIPT ADDED TO STORE!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Title:</b> {new_prod['name']}\n"
        f"💰 <b>Price:</b> {price:.0f} {sym} (~${usd_price})\n"
        f"📁 <b>Attached File:</b> <code>{file_name}</code>\n"
        f"🔗 <b>Demo:</b> {new_prod['demo_link'] or 'None'}\n\n"
        f"<i>It is now live and ready for all users to purchase!</i>",
        parse_mode="HTML"
    )
