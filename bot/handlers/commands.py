from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from services.image_search import search_images
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.yandex_client import get_links
import asyncio
import logging

PHOTOS_PER_PAGE = 3

ART_BOT_MENU = ReplyKeyboardMarkup(
    [
        ["🎨 Анализ картины", "🖼 Поиск изображений"],
        ["ℹ️ Помощь", "⭐ Избранное"]
    ],
    resize_keyboard=True,
    is_persistent=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎨 Привет! Я бот-искусствовед. Выберите действие:",
        reply_markup=ART_BOT_MENU
    )

async def image_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    if not query:
        await update.message.reply_text("Пожалуйста, укажите описание после команды /image")
        return
    
    await update.message.reply_text("🔎 Поиск и анализ изображений, подождите...")

    try:
        loop = asyncio.get_running_loop()
        links = await loop.run_in_executor(None, get_links, query, 15)
        if not links:
            await update.message.reply_text("По запросу ничего не найдено.")
            return
    except Exception as e:
        logging.error(f"Image search error: {e}")
        await update.message.reply_text("⚠️ Ошибка при поиске изображений.")
        return
    
    context.user_data['images'] = links
    context.user_data['page'] = 0
    await send_image_page(update, context)

async def send_image_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    links = context.user_data.get('images', [])
    page = context.user_data.get('page', 0)
    
    start = page * PHOTOS_PER_PAGE
    end = start + PHOTOS_PER_PAGE
    photos = links[start:end]

    if not photos:
        await update.message.reply_text("Больше изображений нет.")
        return

    media_group = [InputMediaPhoto(media=item['url']) for item in photos]

    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data='prev'),
            InlineKeyboardButton("➡️", callback_data='next')
        ],
        [
            InlineKeyboardButton("✅ Это те фото", callback_data='confirm'),
            InlineKeyboardButton("❌ Не то, ищи ещё", callback_data='reject')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text_links = "\n".join(
        f"[{item['title']}]({item['url']})"
        for item in photos
    )

    if update.callback_query:
        try:
            await update.callback_query.message.edit_media(media_group[0], reply_markup=reply_markup)
            if len(media_group) > 1:
                await update.callback_query.message.reply_media_group(media_group[1:])
            await update.callback_query.message.reply_text(
                f"🔗 Источники и ссылки:\n{text_links}",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Error editing media: {e}")
    else:
        await update.message.reply_media_group(media_group)
        await update.message.reply_text(
            "Выберите фото и пролистывайте, если нужно.\n\n"
            f"🔗 Источники и ссылки:\n{text_links}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if 'images' not in context.user_data:
        await query.edit_message_text("Нет активного поиска изображений. Попробуйте команду /image")
        return
    
    if query.data == 'next':
        max_page = (len(context.user_data['images']) - 1) // PHOTOS_PER_PAGE
        if context.user_data['page'] < max_page:
            context.user_data['page'] += 1
            await send_image_page(update, context)
        else:
            await query.answer("Это последняя страница", show_alert=True)

    elif query.data == 'prev':
        if context.user_data['page'] > 0:
            context.user_data['page'] -= 1
            await send_image_page(update, context)
        else:
            await query.answer("Это первая страница", show_alert=True)

    elif query.data == 'confirm':
        await query.edit_message_text("Спасибо за подтверждение! Если нужно — задайте новый запрос.")
        context.user_data.clear()

    elif query.data == 'reject':
        await query.edit_message_text("Ищу еще изображения, пожалуйста подождите...")
        try:
            context.user_data.clear()
            await query.message.reply_text("Пожалуйста, введите новый запрос командой /image <описание>")
        except Exception as e:
            logging.error(f"Error on reject: {e}")