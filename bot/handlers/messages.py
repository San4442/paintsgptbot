import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.gpt import analyze_with_gpt
from services.yandex_client import get_links
import logging

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text

    result = await analyze_with_gpt(query)
    if not result or not result.get("is_painting"):
        await update.message.reply_text("❌ Это не описание картины.")
        return

    details = result["details"]
    search_terms = [
        details.get("название", ""),
        details.get("автор", ""),
        details.get("стиль", ""),
        "картина",
        *details.get("ключевые_элементы", [])
    ]
    search_query = " ".join(filter(None, search_terms))

    try:
        loop = asyncio.get_running_loop()
        links = await loop.run_in_executor(None, get_links, search_query)
        text = (
            f"🎨 Результат анализа:\n"
            f"Название: {details.get('название')}\n"
            f"Автор: {details.get('автор')}\n"
            f"Стиль: {details.get('стиль')}\n"
            "\n🔗 Ссылки:\n" + "\n".join(f"{i+1}. {link}" for i, link in enumerate(links))
        )
        await update.message.reply_text(text)
    except Exception as e:
        logging.error(f"Search error: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при поиске.")
