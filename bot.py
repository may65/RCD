import os
import csv
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncpg
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
EVENT_DATE = datetime.strptime(os.getenv("EVENT_DATE"), "%Y-%m-%d %H:%M")
MESSAGES_FILE = os.getenv("MESSAGES_FILE", "messages.json")

bot = Bot(token=BOT_TOKEN)
scheduler = AsyncIOScheduler()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Загрузка сообщений из JSON
def load_messages(lang="ru"):
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
            return messages.get(lang, {})
    except Exception as e:
        print(f"Ошибка загрузки messages.json: {e}")
        return {}


messages = load_messages()


class Form(StatesGroup):
    waiting_for_username = State()


async def get_db_connection():
    return await asyncpg.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST")
    )


async def init_db():
    conn = await get_db_connection()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            phone_number VARCHAR(20) NOT NULL,
            registration_time TIMESTAMP NOT NULL,
            reminder_sent BOOLEAN DEFAULT FALSE
        )
    ''')
    await conn.close()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    conn = await get_db_connection()
    exists = await conn.fetchval(
        "SELECT 1 FROM participants WHERE telegram_user_id = $1",
        message.from_user.id
    )

    if exists:
        await message.answer(messages["start"]["already_registered"])
    else:
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(
            text=messages["start"]["phone_button"],
            request_contact=True
        ))
        welcome_msg = messages["start"]["welcome"].replace(
            "%event_name%",
            messages["event_name"]
        )
        await message.answer(
            welcome_msg,
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    await conn.close()


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = messages["help"]["base"]

    if message.from_user.id == ADMIN_ID:
        help_text += messages["help"]["admin_commands"]

    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(F.contact)
async def contact_handler(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    username = message.from_user.username

    if not username:
        await state.set_state(Form.waiting_for_username)
        await state.update_data(phone=phone)
        await message.answer(messages["registration"]["enter_username"])
        return

    await save_user(message.from_user.id, username, phone)
    await message.answer(messages["registration"]["success"])
    await state.clear()


@dp.message(F.text, StateFilter(Form.waiting_for_username))
async def username_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if 'phone' in data:
        await save_user(message.from_user.id, message.text, data['phone'])
        await state.clear()
        await message.answer(messages["registration"]["complete"])
    else:
        await message.answer(messages["errors"]["missing_phone"])


async def save_user(user_id: int, username: str, phone: str):
    conn = await get_db_connection()
    await conn.execute(
        "INSERT INTO participants (telegram_user_id, username, phone_number, registration_time) VALUES ($1, $2, $3, NOW())",
        user_id, username, phone
    )
    await conn.close()


async def send_reminders():
    conn = await get_db_connection()
    participants = await conn.fetch(
        "SELECT * FROM participants WHERE reminder_sent = FALSE"
    )

    reminder_text = messages["reminder"]["text"] \
        .replace("%event_time%", EVENT_DATE.strftime("%H:%M")) \
        .replace("%event_name%", messages["event_name"])

    for p in participants:
        if (EVENT_DATE - datetime.now()) <= timedelta(hours=24):
            try:
                await bot.send_message(p['telegram_user_id'], reminder_text)
                await conn.execute(
                    "UPDATE participants SET reminder_sent = TRUE WHERE id = $1",
                    p['id']
                )
            except Exception as e:
                print(f"Ошибка: {e}")
    await conn.close()


@dp.message(Command("list"))
async def list_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(messages["errors"]["no_access"])
        return

    conn = await get_db_connection()
    count = await conn.fetchval("SELECT COUNT(*) FROM participants")
    await message.answer(messages["admin"]["list"].replace("%count%", str(count)))
    await conn.close()


@dp.message(Command("export"))
async def export_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    conn = await get_db_connection()
    data = await conn.fetch("SELECT * FROM participants")

    with open("participants.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Telegram ID', 'Username', 'Phone', 'Registered At'])
        for row in data:
            writer.writerow(
                [row['id'], row['telegram_user_id'], row['username'], row['phone_number'], row['registration_time']])

    await message.answer_document(types.FSInputFile("participants.csv"))
    await conn.close()


@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    print('broadcast_1')
    # print(f'message.from_user.id-{message.from_user.id} message.text.split()-{message.text.split()}')
    if message.from_user.id != ADMIN_ID or len(message.text.split()) < 2:
        return
    # print('broadcast_2')
    text = message.text.split(maxsplit=1)[1]
    conn = await get_db_connection()
    users = await conn.fetch("SELECT telegram_user_id FROM participants")

    for user in users:
        try:
            await bot.send_message(user['telegram_user_id'], text)
        except:
            continue

    await conn.close()
    await message.answer(messages["admin"]["broadcast_sent"].replace("%users_count%", str(len(users))))


async def main():
    await init_db()
    scheduler.add_job(send_reminders, IntervalTrigger(minutes=30))
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())