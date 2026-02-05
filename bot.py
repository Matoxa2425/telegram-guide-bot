import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = "8453426857:AAFp-0VxpVn6pH0lOAETDys1-ag3MizbssI"
CHANNEL_ID = "@mezhdunami_bot"
PDF_FILE = "pet_guide.pdf"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- база данных ---
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    downloaded INTEGER DEFAULT 0
)
""")
conn.commit()

# --- проверка подписки ---
async def check_subscription(user_id):
    member = await bot.get_chat_member(CHANNEL_ID, user_id)
    return member.status in ["member", "creator", "administrator"]

# --- старт ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    subscribed = await check_subscription(message.from_user.id)

    if not subscribed:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Подписаться", url="https://t.me/mezhdunami_bot"))
        kb.add(types.InlineKeyboardButton("Проверить подписку", callback_data="check_sub"))
        await message.answer("Сначала подпишись на канал 👇", reply_markup=kb)
        return

    await send_guide(message.from_user.id)

# --- кнопка проверки ---
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_sub(callback_query: types.CallbackQuery):
    subscribed = await check_subscription(callback_query.from_user.id)

    if subscribed:
        await send_guide(callback_query.from_user.id)
    else:
        await bot.answer_callback_query(callback_query.id, "Ты ещё не подписан")

# --- отправка гайда + счётчик ---
async def send_guide(user_id):
    cursor.execute("SELECT downloaded FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result is None:
        cursor.execute("INSERT INTO users (user_id, downloaded) VALUES (?, 1)", (user_id,))
        conn.commit()

        # новый пользователь — увеличиваем счётчик
        await bot.send_document(user_id, open(PDF_FILE, "rb"))
        await bot.send_message(user_id, "Вот твой гайд 🐾")
    else:
        # уже скачивал — просто даём снова без увеличения счётчика
        await bot.send_document(user_id, open(PDF_FILE, "rb"))
        await bot.send_message(user_id, "Ты уже получал гайд, отправляю ещё раз")

# --- запуск ---
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

