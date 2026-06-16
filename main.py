#!/usr/bin/env python3
"""
Telegram-бот для управления Minecraft-сервером через RCON.
Использует библиотеку mcrcon (pip install mcrcon).
"""

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from mcrcon import MCRcon, MCRconException

# -------------------- НАСТРОЙКИ --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8627210638:AAF6NwrXnpokpAAeoqUT5U3ALa4fg-UUgik")

RCON_HOST = os.getenv("RCON_HOST", "188.127.241.239")
RCON_PORT = int(os.getenv("RCON_PORT", "21027"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "hyyppeeiittdd")


# Разрешённые Telegram user ID через запятую. Пустая строка = доступ всем.
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")
ALLOWED_USERS = [int(uid.strip()) for uid in ALLOWED_USERS if uid.strip().isdigit()]

# Таймаут RCON в секундах
RCON_TIMEOUT = 5

# -------------------- ЛОГИРОВАНИЕ --------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- ПРОВЕРКА ДОСТУПА --------------------
def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS

# -------------------- RCON-ЗАПРОС --------------------
async def execute_rcon(command: str) -> str:
    """Отправляет команду через mcrcon и возвращает ответ."""
    return await asyncio.to_thread(_execute_rcon_sync, command)

def _execute_rcon_sync(command: str) -> str:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=RCON_TIMEOUT) as rcon:
        response = rcon.command(command)
        return response.strip() or "(пустой ответ)"

# -------------------- ОБРАБОТЧИКИ --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    await update.message.reply_text(
        "🎮 <b>RCON Бот для Minecraft</b>\n\n"
        "Используйте команду:\n"
        "<code>/rcon ваша_команда</code>\n\n"
        "Например:\n"
        "<code>/rcon list</code> — список игроков\n"
        "<code>/rcon say Привет!</code> — сообщение в чат",
        parse_mode="HTML"
    )

async def rcon_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Укажите команду после /rcon, например: <code>/rcon list</code>",
            parse_mode="HTML"
        )
        return

    command = " ".join(context.args)
    await update.message.chat.send_action(action="typing")

    try:
        response = await execute_rcon(command)
        safe = response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if len(safe) > 4000:
            safe = safe[:4000] + "\n\n⚠️ Ответ обрезан (лимит Telegram)."
        await update.message.reply_text(
            f"📟 <b>Команда:</b> <code>{command}</code>\n"
            f"📋 <b>Ответ:</b>\n<pre>{safe}</pre>",
            parse_mode="HTML"
        )
    except MCRconException as e:
        await update.message.reply_text(f"❌ Ошибка RCON: {e}")
    except Exception as e:
        logger.exception("Неизвестная ошибка")
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Ошибка при обработке update:", exc_info=context.error)

# -------------------- ЗАПУСК --------------------
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("⛔ Укажите BOT_TOKEN в коде или через переменную окружения.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("rcon", rcon_handler))
    app.add_error_handler(error_handler)

    logger.info("🤖 Бот запущен. Ожидание команд...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
