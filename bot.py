import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# Конфиг
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8925718280:AAEgxuChEdh0BLUfIwcsRIUldUkT7xyZxpQ")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1812923068"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище диалогов: user_id -> информация о пользователе
active_users = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие при нажатии 'Связаться с нами' из приложения"""
    user = update.effective_user
    user_id = user.id

    # Запоминаем пользователя
    active_users[user_id] = {
        "name": user.full_name,
        "username": f"@{user.username}" if user.username else "нет username",
    }

    # Уведомляем админа о новом обращении
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 Новое обращение из DeepWall VPN\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 {active_users[user_id]['username']}\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"Чтобы ответить используй:\n`/reply {user_id} текст ответа`"
        ),
        parse_mode="Markdown"
    )

    # Приветствие пользователю
    await update.message.reply_text(
        "👋 Привет! Это служба поддержки DeepWall VPN.\n\n"
        "Опиши свою проблему или вопрос — мы ответим как можно скорее.\n\n"
        "⏱ Обычное время ответа: до 24 часов."
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщения пользователей админу"""
    user = update.effective_user
    user_id = user.id

    # Если пользователь не делал /start — всё равно запоминаем
    if user_id not in active_users:
        active_users[user_id] = {
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "нет username",
        }

    # Пересылаем админу
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

    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ Сообщение получено! Ожидайте ответа."
    )


async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для админа: /reply <user_id> <текст>"""
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Использование: /reply <user_id> <текст ответа>"
        )
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
        await update.message.reply_text(f"❌ Ошибка отправки: {e}")


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /users — показывает всех кто писал"""
    if update.effective_user.id != ADMIN_ID:
        return

    if not active_users:
        await update.message.reply_text("Пока никто не писал.")
        return

    text = "📋 Пользователи написавшие в поддержку:\n\n"
    for uid, info in active_users.items():
        text += f"• {info['name']} ({info['username']}) — ID: `{uid}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_user))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    logger.info("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
