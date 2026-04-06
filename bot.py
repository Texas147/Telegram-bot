#!/usr/bin/env python3
"""
🤖 AI Telegram Bot — Groq (БЕСПЛАТНО)
Профессиональный бот на базе LLaMA 3 через Groq API
"""

import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from telegram.constants import ParseMode, ChatAction
from groq import Groq

load_dotenv()

# ── Логирование ───────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s │ %(levelname)s │ %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

# ── Конфигурация ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise RuntimeError("❌ Заполни TELEGRAM_TOKEN и GROQ_API_KEY в файле .env")

groq_client = Groq(api_key=GROQ_API_KEY)

# ── Память диалогов ───────────────────────────────────────────────────────────
conversations: dict[int, list] = {}
MAX_HISTORY = 20

# ── Системный промпт ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Ты — профессиональный ИИ-ассистент в Telegram. Умный, полезный и дружелюбный.

Твои возможности:
• Отвечаешь на любые вопросы чётко и по делу
• Помогаешь с текстами, кодом, переводом, анализом
• Даёшь советы по бизнесу, маркетингу, продажам
• Помнишь весь контекст разговора
• Поддерживаешь клиентов и решаешь их проблемы

Правила:
• Пиши структурированно, используй списки
• Форматируй для Telegram: *жирный*, _курсив_, `код`
• Отвечай на языке пользователя
• Если не знаешь точного ответа — честно скажи
• Будь краток, но исчерпывающим"""

# ── Вспомогательные функции ───────────────────────────────────────────────────

def get_history(user_id: int) -> list:
    return conversations.get(user_id, [])

def add_message(user_id: int, role: str, content: str):
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": role, "content": content})
    if len(conversations[user_id]) > MAX_HISTORY:
        conversations[user_id] = conversations[user_id][-MAX_HISTORY:]

def clear_history(user_id: int):
    conversations[user_id] = []

def ask_groq(user_id: int, message: str) -> str:
    """Синхронный запрос к Groq API."""
    add_message(user_id, "user", message)
    history = get_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # лучшая бесплатная модель
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content or "Не удалось получить ответ."
        add_message(user_id, "assistant", reply)
        return reply

    except Exception as e:
        logger.error(f"Groq error: {e}")
        err = str(e).lower()
        if "rate_limit" in err:
            return "⏳ Слишком много запросов. Подожди 10 секунд и попробуй снова."
        if "invalid_api_key" in err or "auth" in err:
            return "🔑 Неверный GROQ_API_KEY. Проверь файл .env"
        return f"⚠️ Ошибка: {str(e)[:200]}"

# ── Команды ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    clear_history(user.id)
    name = user.first_name or "друг"

    text = (
        f"👋 Привет, *{name}*!\n\n"
        "Я — ИИ-ассистент на базе *LLaMA 3* (Groq).\n"
        "Работаю быстро и *полностью бесплатно*! 🆓\n\n"
        "🧠 *Что умею:*\n"
        "• Отвечаю на любые вопросы\n"
        "• Помогаю с текстами и кодом\n"
        "• Консультирую по бизнесу\n"
        "• Помню весь разговор\n"
        "• Работаю на любом языке\n\n"
        "💬 Просто напиши свой вопрос!\n\n"
        "📋 /help — все команды"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"START: {user.id} @{user.username}")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *Команды бота:*\n\n"
        "/start — Начать заново\n"
        "/help — Эта справка\n"
        "/clear — Очистить память\n"
        "/status — Статус бота\n"
        "/about — О боте\n\n"
        "💡 *Советы:*\n"
        "• Задавай вопросы как обычно\n"
        "• Я помню весь разговор\n"
        "• Можно ссылаться на прошлые сообщения\n"
        "• Для сброса контекста — /clear"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    clear_history(update.effective_user.id)
    await update.message.reply_text("🗑 *Память очищена.* Начинаем заново!", parse_mode=ParseMode.MARKDOWN)


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count   = len(get_history(user_id))
    now     = datetime.now().strftime("%d.%m.%Y %H:%M")
    text = (
        "✅ *Бот работает*\n\n"
        f"🕐 Время: {now}\n"
        f"💬 Сообщений в памяти: {count}/{MAX_HISTORY}\n"
        "🧠 Модель: LLaMA 3.3 70B (Groq)\n"
        "⚡ Скорость: очень быстрая\n"
        "🆓 Тариф: бесплатный"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *AI Telegram Bot*\n\n"
        "Стек технологий:\n"
        "• *LLaMA 3.3 70B* — языковая модель Meta\n"
        "• *Groq API* — молниеносный инференс\n"
        "• *python-telegram-bot* — Telegram интеграция\n\n"
        "💰 *Стоимость:* полностью бесплатно\n"
        "⚡ *Скорость:* ~0.5 сек на ответ\n\n"
        "Разработан с помощью Claude AI ✨"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик сообщений."""
    user    = update.effective_user
    message = update.message.text
    if not message:
        return

    logger.info(f"MSG {user.id} @{user.username}: {message[:80]}")

    # Показываем «печатает...»
    await ctx.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    # Запрос к Groq в отдельном потоке (не блокируем event loop)
    reply = await asyncio.to_thread(ask_groq, user.id, message)

    # Отправка (разбиваем длинные ответы)
    chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
    for i, chunk in enumerate(chunks):
        try:
            await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(chunk)   # без форматирования если ошибка
        if i < len(chunks) - 1:
            await asyncio.sleep(0.3)


async def error_handler(update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}")


# ── Запуск ────────────────────────────────────────────────────────────────────

def main():
    logger.info("🚀 Запуск AI Telegram Bot (Groq)...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("clear",  cmd_clear))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("about",  cmd_about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("✅ Бот слушает сообщения...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
