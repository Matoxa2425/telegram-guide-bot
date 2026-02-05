import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatMemberStatus

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Будет задан в Render
CHANNEL_USERNAME = "@mzhdnami"  # Твой канал
GUIDE_FILE = "guide.pdf"  # Имя файла гайда

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== БАЗА ДАННЫХ (Replit DB) =====
# Импортируем только если есть replit (будет на Replit, но не на Render)
try:
    from replit import db
    HAS_DB = True
    logger.info("Replit Database доступна")
except ImportError:
    HAS_DB = False
    logger.warning("Replit Database недоступна (работаем локально или на Render)")

# ===== СЧЕТЧИК =====
def get_counter():
    """Получить текущее значение счетчика"""
    if HAS_DB:
        # Пробуем получить из Replit DB
        try:
            return db.get("download_counter", 0)
        except:
            return 0
    else:
        # Fallback: переменная окружения или файл
        try:
            return int(os.environ.get("DOWNLOAD_COUNTER", "0"))
        except:
            return 0

def increment_counter():
    """Увеличить счетчик на 1 и сохранить"""
    current = get_counter()
    new_count = current + 1
    
    if HAS_DB:
        # Сохраняем в Replit DB
        try:
            db["download_counter"] = new_count
            logger.info(f"Счетчик сохранен в Replit DB: {new_count}")
        except Exception as e:
            logger.error(f"Ошибка сохранения в Replit DB: {e}")
    else:
        # Fallback: логируем и используем переменную окружения
        logger.info(f"=== СКАЧИВАНИЕ #{new_count} ===")
    
    return new_count

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME, 
            user_id=user_id
        )
        return member.status in [
            ChatMemberStatus.MEMBER, 
            ChatMemberStatus.ADMINISTRATOR, 
            ChatMemberStatus.OWNER
        ]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("📥 Скачать гайд", callback_data='download')]]
    
    text = f"""Привет, {user.first_name}! 👋

Я бот канала MZHDNAM! 📺
Здесь ты можешь получить полезный гайд.

✅ Для скачивания нужно быть подписанным на канал: {CHANNEL_USERNAME}

Нажми кнопку ниже👇"""
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'download':
        if await check_subscription(user_id, context):
            try:
                # Отправляем файл
                with open(GUIDE_FILE, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        caption="✅ Гайд от MZHDNAM!\n\nДелитесь каналом с друзьями! 👉 @mzhdnami"
                    )
                
                # Обновляем счетчик
                count = increment_counter()
                
                await query.edit_message_text(
                    text=f"🎉 Гайд отправлен в личные сообщения!\n\n📊 Скачано раз: {count}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("💎 Перейти в канал", url="https://t.me/mzhdnami")
                    ]])
                )
                logger.info(f"User {user_id} downloaded. Total: {count}")
                
            except FileNotFoundError:
                await query.edit_message_text("❌ Файл временно недоступен. Админ уже уведомлен!")
        else:
            # Не подписан
            keyboard = [
                [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/mzhdnami")],
                [InlineKeyboardButton("✅ Я подписался", callback_data='check')]
            ]
            await query.edit_message_text(
                text="❌ Вы не подписаны на канал!\n\n1. Нажмите кнопку 'Подписаться на канал'\n2. Вернитесь и нажмите 'Я подписался'",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == 'check':
        if await check_subscription(user_id, context):
            await query.edit_message_text(
                text="✅ Отлично! Теперь нажмите кнопку ниже для скачивания:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📥 Скачать гайд", callback_data='download')
                ]])
            )
        else:
            await query.answer("Вы еще не подписались. Подпишитесь и попробуйте снова.", show_alert=True)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats для админа"""
    ADMIN_ID = 395925643  # ЗАМЕНИ НА СВОЙ ID (узнай у @userinfobot)
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Эта команда только для администратора")
        return
    
    count = get_counter()
    await update.message.reply_text(
        f"📊 Статистика бота @Mzhdnami_bot\n\n"
        f"Всего скачиваний: {count}\n"
        f"ID администратора: {ADMIN_ID}\n"
        f"Используется {'Replit DB' if HAS_DB else 'локальное хранилище'}"
    )

# ===== ЗАПУСК =====
def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    PORT = int(os.environ.get('PORT', 8443))
    RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    
    if RENDER_HOST:
        webhook_url = f'https://{RENDER_HOST}/{BOT_TOKEN}'
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url
        )
        logger.info(f"Бот запущен на Render. Текущий счетчик: {get_counter()}")
    else:
        app.run_polling()
        logger.info("Бот запущен локально. Текущий счетчик: {get_counter()}")

if __name__ == '__main__':
    main()
