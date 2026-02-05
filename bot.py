import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatMemberStatus

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@mzhdnami"
GUIDE_FILE = "guide.pdf"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== СЧЕТЧИК В ФАЙЛЕ =====
COUNTER_FILE = "counter.txt"

def get_counter() -> int:
    """Получить текущее значение счетчика"""
    try:
        with open(COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def increment_counter() -> int:
    """Увеличить счетчик на 1"""
    count = get_counter() + 1
    with open(COUNTER_FILE, "w") as f:
        f.write(str(count))
    logger.info(f"📥 СКАЧИВАНИЕ #{count}")
    return count

# ===== ПРОВЕРКА ПОДПИСКИ =====
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
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
        return True  # В случае ошибки разрешаем скачивание

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
                logger.info(f"👤 User {user_id} скачал гайд. Всего: {count}")
                
            except FileNotFoundError:
                await query.edit_message_text(
                    "❌ Файл с гайдом не найден.\nАдминистратор уведомлен.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📱 Написать админу", url="https://t.me/matoxa2425")
                    ]])
                )
                logger.error(f"Файл {GUIDE_FILE} не найден!")
        else:
            # Не подписан
            keyboard = [
                [InlineKeyboardButton("📢 Подписаться на канал", url="https://t.me/mzhdnami")],
                [InlineKeyboardButton("✅ Я подписался", callback_data='check')]
            ]
            await query.edit_message_text(
                text="❌ Вы не подписаны на канал!\n\n1. Нажмите 'Подписаться на канал'\n2. Вернитесь и нажмите 'Я подписался'",
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
    ADMIN_ID = 395925643  # Это твой ID Angelina
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Эта команда только для администратора")
        return
    
    count = get_counter()
    await update.message.reply_text(
        f"📊 Статистика бота @Mzhdnami_bot\n\n"
        f"Всего скачиваний гайда: {count}\n"
        f"Сервер: VPS (Ubuntu)\n"
        f"Python: 3.12.3\n"
        f"Статус: ✅ Работает"
    )

# ===== ЗАПУСК =====
def main():
    """Запуск бота"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен! Создай файл .env с BOT_TOKEN=твой_токен")
        return
    
    if not os.path.exists(GUIDE_FILE):
        logger.warning(f"⚠️ Файл {GUIDE_FILE} не найден. Загрузи его на сервер.")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("🤖 Запускаю бота...")
    logger.info(f"📊 Текущий счетчик: {get_counter()}")
    logger.info(f"📢 Канал: {CHANNEL_USERNAME}")
    logger.info(f"🐍 Python: {os.sys.version}")
    
    # Используем polling
    application.run_polling()

if __name__ == '__main__':
    main()
