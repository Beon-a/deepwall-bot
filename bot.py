import logging
import os
import asyncio
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8925718280:AAEgxuChEdh0BLUfIwcsRIUldUkT7xyZxpQ")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1812923068"))
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

active_users = {}

# Хардкод серверов — обновлять при смене подписки OneConnect
SERVERS_JSON = '[{"id":"238","serverName":"AU-Melbourne","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote aus-melbourne.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"Australia","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/au.png","vpnUserName":"l4R0w8m7C6i4G0qp","vpnUserPassword":"DFrF^V4NAbWQv6Lv#Gbd"},{"id":"271","serverName":"KR-Seoul","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote japan.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"Korea, Republic of","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/kr.png","vpnUserName":"B4s0L8x7O6V440Zp","vpnUserPassword":"!FIF0ViNmbOQ46jvVGrd"},{"id":"311","serverName":"CA-Toronto","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote ca-toronto.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"Canada","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/ca.png","vpnUserName":"D4Q06887f6B4A0Jp","vpnUserPassword":"hFkFwV4N3brQX67vDG9d"},{"id":"356","serverName":"JP-Tokyo","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote japan.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"Japan","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/jp.png","vpnUserName":"O4Y0N8a7u624o0#p","vpnUserPassword":"zFjFBV3NlbnQa67vsGkd"},{"id":"397","serverName":"CA-Toronto Pro","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote ca-toronto.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"Canada","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/ca.png","vpnUserName":"D4Q06887f6B4A0Jp","vpnUserPassword":"hFkFwV4N3brQX67vDG9d"},{"id":"309","serverName":"US-Seattle","ovpnConfiguration":"client\r\ndev tun0\r\nproto udp\r\nremote us-seattle.privacy.network 1197\r\nresolv-retry infinite\r\nnobind\r\npersist-key\r\npersist-tun\r\ndata-ciphers AES-128-CBC:AES-128-GCM:AES-256-GCM\r\ndata-ciphers-fallback AES-128-CBC\r\nauth sha1\r\ntls-client\r\nremote-cert-tls server\r\npull-filter ignore \"route-ipv6\"\r\npull-filter ignore \"ifconfig-ipv6\"\r\nauth-user-pass\r\ncompress\r\nverb 1\r\nreneg-sec 0\r\nauth-user-pass\r\n","country":"United States","flag_url":"https://raw.githubusercontent.com/oneconnectapi/flag-sdk/main/us.png","vpnUserName":"l4R0w8m7C6i4G0qp","vpnUserPassword":"DFrF^V4NAbWQv6Lv#Gbd"}]'

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/servers':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(SERVERS_JSON.encode('utf-8'))
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"DeepWall Bot is running")

    def log_message(self, format, *args):
        pass

def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    active_users[user_id] = {
        "name": user.full_name,
        "username": f"@{user.username}" if user.username else "нет username",
    }
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 Новое обращение из DeepWall VPN\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 {active_users[user_id]['username']}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"Ответить: `/reply {user_id} текст`"
        ),
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "👋 Привет! Это служба поддержки DeepWall VPN.\n\n"
        "Опиши свою проблему или вопрос — мы ответим как можно скорее.\n\n"
        "⏱ Обычное время ответа: до 24 часов."
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if user_id == ADMIN_ID:
        return
    if user_id not in active_users:
        active_users[user_id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "нет username",
        }
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💬 Сообщение от пользователя\n"
            f"👤 {user.full_name} ({active_users[user_id]['username']})\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"📝 {update.message.text}\n\n"
            f"Ответить: `/reply {user_id} текст`"
        ),
        parse_mode="Markdown"
    )
    await update.message.reply_text("✅ Сообщение получено! Ожидайте ответа.")

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Использование: /reply <user_id> <текст>")
        return
    try:
        target_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ Неверный user_id")
        return
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 Ответ от поддержки DeepWall:\n\n{reply_text}"
        )
        await update.message.reply_text("✅ Ответ отправлен!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not active_users:
        await update.message.reply_text("Пока никто не писал.")
        return
    text = "📋 Пользователи написавшие в поддержку:\n\n"
    for uid, info in active_users.items():
        text += f"• {info['name']} ({info['username']}) — ID: `{uid}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))
    logger.info("Бот запущен...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True:
        await asyncio.sleep(3600)

def main():
    threading.Thread(target=run_web_server, daemon=True).start()
    logger.info(f"Web server started on port {PORT}")
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
