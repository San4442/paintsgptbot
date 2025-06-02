import asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes
from handlers.commands import ART_BOT_MENU, image_search
from services.image_search import search_images
from services.gpt import analyze_with_gpt
from services.yandex_client import get_links
import logging
from telegram.constants import ParseMode

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🎨 Анализ картины":
        cancel_keyboard = ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True)
        await update.message.reply_text(
            "🖋 Опишите картину, которую хотите проанализировать:",
            reply_markup=cancel_keyboard
        )
        context.user_data['expecting_description'] = True
    
    elif text == "🖼 Поиск изображений":
        await update.message.reply_text("🔍 Введите запрос для поиска изображений:", reply_markup=ART_BOT_MENU)
        context.user_data['expecting_image_query'] = True
    
    elif text == "ℹ️ Помощь":
        await update.message.reply_text(
            "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
            "1. <b>Анализ картины</b> - опишите картину или укажите её название\n"
            "2. <b>Поиск изображений</b> - найдите художественные работы по запросу\n"
            "3. <b>Избранное</b> - сохраняйте понравившиеся работы\n\n"
            "<b>Просто отправьте описание картины</b>, и я попробую её определить!\n\n"
            "Примеры запросов:\n"
            "- 'Звездная ночь Ван Гога'\n"
            "- 'Девочка с персиками'\n"
            "- 'Супрематизм Малевича'",
            parse_mode=ParseMode.HTML,
            reply_markup=ART_BOT_MENU
        )
    
    elif text == "⭐ Избранное":
        await update.message.reply_text("📌 Эта функция в разработке!", reply_markup=ART_BOT_MENU)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "❌ Отмена":
        await update.message.reply_text(
            "Действие отменено",
            reply_markup=ART_BOT_MENU
        )
        context.user_data.pop('expecting_description', None)
        context.user_data.pop('expecting_image_query', None)
        return

    if context.user_data.get('expecting_description'):
        context.user_data.pop('expecting_description', None)
        await analyze_art(update, context)
        return
        
    if context.user_data.get('expecting_image_query'):
        context.user_data.pop('expecting_image_query', None)
        context.args = [text]
        await image_search(update, context)
        return
        
    menu_options = ["🎨 Анализ картины", "🖼 Поиск изображений", "ℹ️ Помощь", "⭐ Избранное"]
    if text in menu_options:
        await handle_menu(update, context)
    else:
        await analyze_art(update, context)

async def analyze_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text

    await update.message.reply_text(
        "🔍 Анализирую описание картины...",
        reply_markup=ReplyKeyboardRemove()  # Убираем временную клавиатуру
    )

    await asyncio.sleep(0.5)

    await update.message.reply_text(
        "🔍 Ищу информацию о картине...",
        reply_markup=ART_BOT_MENU
    )

    result = await analyze_with_gpt(query)
    if not result or not result.get("is_painting"):
        await update.message.reply_text(
            "❌ Это не похоже на описание картины.",
            reply_markup=ART_BOT_MENU  # Возвращаем основное меню
        )
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
        image_urls = await search_images(search_query, n=1)
        
        loop = asyncio.get_running_loop()
        links = await loop.run_in_executor(None, get_links, search_query, 5)

        formatted_links = "\n".join(
            f"{i+1}. <a href='{item['url']}'>{item['title']}</a>" 
            for i, item in enumerate(links))

        caption = (
            f"🎨 <b>{details.get('название', 'Без названия')}</b>\n"
            f"👤 Автор: {details.get('автор', 'неизвестно')}\n"
            f"🏛 Стиль: {details.get('стиль', 'неизвестно')}\n\n"
            f"🔗 Ссылки:\n{formatted_links}"
        )

        if image_urls:
            await update.message.reply_photo(
                image_urls[0],
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=ART_BOT_MENU
            )
        else:
            await update.message.reply_text(
                caption,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=ART_BOT_MENU
            )
    except Exception as e:
        logging.error(f"Search error: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка при анализе картины.",
            reply_markup=ART_BOT_MENU  # Возвращаем меню при ошибке
        )
