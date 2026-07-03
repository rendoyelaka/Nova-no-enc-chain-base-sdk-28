#!/usr/bin/env python3
"""
Device Client Bot — @Deviceclientbot
Nova package format    : com.mobile.tools.XXXXXXXXXXXXXXXXXXX (36 chars)
Companion package format: com.phone.helpXXXXX (19 chars)
"""

import telebot
import random
import string
import requests
import json
import os
import base64
import time
import traceback
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
GITHUB_TOKEN  = os.environ["GH_PAT"]
GITHUB_REPO   = os.environ["REPO_NAME"]

print(f"[*] Bot starting...")
print(f"[*] ADMIN_CHAT_ID: {ADMIN_CHAT_ID}")
print(f"[*] GITHUB_REPO: {GITHUB_REPO}")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ── Session state ─────────────────────────────────────────────────────────────
session = {
    "app_name": None,
    "icon_b64": None,
    "step":     None
}

# ── Package generators ────────────────────────────────────────────────────────

def generate_nova_package() -> str:
    suffix = ''.join(random.choices(string.ascii_lowercase, k=19))
    pkg = f"com.mobile.tools.{suffix}"
    assert len(pkg) == 36
    return pkg

def generate_companion_package() -> str:
    suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    pkg = f"com.phone.help{suffix}"
    assert len(pkg) == 19
    return pkg

# ── GitHub trigger ────────────────────────────────────────────────────────────

def trigger_workflow(inputs: dict) -> bool:
    url = (
        f"https://api.github.com/repos/{GITHUB_REPO}"
        f"/actions/workflows/build.yml/dispatches"
    )
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {"ref": "main", "inputs": inputs}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"[*] Workflow trigger status: {r.status_code}")
        return r.status_code == 204
    except Exception as e:
        print(f"[X] Trigger error: {e}")
        return False

# ── Keyboards ─────────────────────────────────────────────────────────────────

def main_menu():
    markup = InlineKeyboardMarkup()
    name_label = f"✏️ App Name {'✅' if session['app_name'] else '❌'}"
    icon_label = f"🖼️ Upload Icon {'✅' if session['icon_b64'] else '❌'}"
    markup.row(InlineKeyboardButton(name_label, callback_data="set_name"))
    markup.row(InlineKeyboardButton(icon_label, callback_data="set_icon"))
    markup.row(InlineKeyboardButton("🔨 Build Both Apps", callback_data="build_app"))
    return markup

def status_text() -> str:
    name = session["app_name"] or "❌ Not set"
    icon = "✅ Uploaded" if session["icon_b64"] else "❌ Not set"
    return (
        f"*Device Client Bot*\n\n"
        f"📱 App Name : {name}\n"
        f"🖼️ Icon      : {icon}\n\n"
        f"Select action:"
    )

# ── Handlers ──────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.reply_to(message, "⛔ Unauthorized")
        return
    bot.send_message(
        ADMIN_CHAT_ID,
        status_text(),
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    if session["step"] == "waiting_name" and message.content_type == "text":
        name = message.text.strip()
        if len(name) < 1 or len(name) > 30:
            bot.send_message(ADMIN_CHAT_ID, "⚠️ Name must be 1-30 characters. Try again:")
            return
        session["app_name"] = name
        session["step"] = None
        bot.send_message(
            ADMIN_CHAT_ID,
            f"✅ App name set to: `{name}`",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    if session["step"] == "waiting_icon" and message.content_type == "photo":
        photo     = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded = bot.download_file(file_info.file_path)
        session["icon_b64"] = base64.b64encode(downloaded).decode("utf-8")
        session["step"] = None
        bot.send_message(
            ADMIN_CHAT_ID,
            "✅ Icon uploaded!",
            reply_markup=main_menu()
        )
        return

    if session["step"] == "waiting_name":
        bot.send_message(ADMIN_CHAT_ID, "⚠️ Please send the app name as text.")
        return
    if session["step"] == "waiting_icon":
        bot.send_message(ADMIN_CHAT_ID, "⚠️ Please send a photo/image as the icon.")
        return

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.message.chat.id != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "Unauthorized")
        return

    bot.answer_callback_query(call.id)

    if call.data == "set_name":
        session["step"] = "waiting_name"
        bot.send_message(ADMIN_CHAT_ID, "✏️ Enter the app name (1-30 chars):")

    elif call.data == "set_icon":
        session["step"] = "waiting_icon"
        bot.send_message(ADMIN_CHAT_ID, "🖼️ Send the app icon as a PNG image:")

    elif call.data == "build_app":
        if not session["app_name"]:
            bot.send_message(
                ADMIN_CHAT_ID,
                "⚠️ Please set the app name first.",
                reply_markup=main_menu()
            )
            return
        if not session["icon_b64"]:
            bot.send_message(
                ADMIN_CHAT_ID,
                "⚠️ Please upload an icon first.",
                reply_markup=main_menu()
            )
            return

        nova_pkg = generate_nova_package()
        comp_pkg = generate_companion_package()
        app_name = session["app_name"]

        bot.send_message(
            ADMIN_CHAT_ID,
            f"🚀 *Starting Build...*\n\n"
            f"📱 App Name : `{app_name}`\n"
            f"📦 Nova Pkg : `{nova_pkg}`\n"
            f"📦 Comp Pkg : `{comp_pkg}`\n\n"
            f"⏳ Please wait 5-8 minutes...",
            parse_mode="Markdown"
        )

        inputs = {
            "build_type":        "both",
            "nova_package":      nova_pkg,
            "companion_package": comp_pkg,
            "app_name":          app_name,
            "icon_b64":          session["icon_b64"],
        }

        if trigger_workflow(inputs):
            session["app_name"] = None
            session["icon_b64"] = None
            bot.send_message(
                ADMIN_CHAT_ID,
                "✅ *Build triggered successfully!*\n"
                "Both APKs will be sent here when ready.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            bot.send_message(
                ADMIN_CHAT_ID,
                "❌ Failed to trigger build. Check GH_PAT secret.",
                reply_markup=main_menu()
            )

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[*] Verifying bot token...")
    try:
        me = bot.get_me()
        print(f"[OK] Bot: @{me.username}")
    except Exception as e:
        print(f"[X] Bot token invalid: {e}")
        exit(1)

    trigger = os.environ.get("GITHUB_EVENT_NAME", "")
    if trigger == "push":
        try:
            bot.send_message(
                ADMIN_CHAT_ID,
                status_text(),
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
            print("[OK] Menu sent after push")
        except Exception as e:
            print(f"[X] Failed to send menu: {e}")

    print("[*] Starting polling...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"[X] Polling error: {e}")
            traceback.print_exc()
            time.sleep(3)
            print("[*] Restarting polling...")
