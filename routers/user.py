from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import sqlite3
from utils import load_messages, get_logo

user_router = Router()
messages = load_messages()


class RegistrationStates(StatesGroup):
    WAITING_PHONE = State()
    WAITING_USERNAME = State()


def init_db():
    with sqlite3.connect('users.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      telegram_user_id INTEGER UNIQUE,
                      username TEXT,
                      phone_number TEXT,
                      registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      reminder_sent BOOLEAN DEFAULT FALSE)''')


init_db()


@user_router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
        if cursor.fetchone():
            await message.answer(messages['error_exists'])
            return

    logo = get_logo()
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(
        text="📱 Поделиться номером",
        request_contact=True
    ))

    await message.answer_photo(photo=logo, caption=messages['welcome'])
    await message.answer(
        messages['registration_request'],
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(RegistrationStates.WAITING_PHONE)


@user_router.message(F.contact)
async def contact_handler(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    username = message.from_user.username

    if username:
        try:
            with sqlite3.connect('users.db') as conn:
                conn.execute(
                    "INSERT INTO users (telegram_user_id, username, phone_number) VALUES (?, ?, ?)",
                    (message.from_user.id, username, phone)
                )
            await message.answer(messages['registration_success'], reply_markup=ReplyKeyboardRemove())
            await state.clear()
        except sqlite3.IntegrityError:
            await message.answer(messages['error_exists'])
    else:
        await state.update_data(phone_number=phone)
        await message.answer(messages['username_request'])
        await state.set_state(RegistrationStates.WAITING_USERNAME)


@user_router.message(RegistrationStates.WAITING_USERNAME)
async def username_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        with sqlite3.connect('users.db') as conn:
            conn.execute(
                "INSERT INTO users (telegram_user_id, username, phone_number) VALUES (?, ?, ?)",
                (message.from_user.id, message.text, data['phone_number'])
            )
        await message.answer(messages['registration_success'])
        await state.clear()
    except sqlite3.IntegrityError:
        await message.answer(messages['error_exists'])

# @user_router.message(Command("help"))
# async def help_handler(message: types.Message):
#     await message.answer(messages['help_text'])
@user_router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        text=messages['help_text'],
        # parse_mode=None  # Отключаем HTML до проверки
        parse_mode="HTML"  # Явно указываем корректный режим разметки
    )