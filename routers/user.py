#user.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # Добавлен правильный импорт
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import sqlite3

user_router = Router()

@user_router.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        "🤖 Список доступных команд:\n\n"
        "/start — начать регистрацию на мероприятие\n"
        "/help — показать это сообщение\n\n"
        "⚙️ Администраторам доступны:\n"
        "/list — статистика участников\n"
        "/export — выгрузка данных\n"
        "/broadcast text — рассылка сообщений"
    )
    await message.answer(help_text)

# Исправленный класс состояний
class RegistrationStates(StatesGroup):
    print(f'user/RegistrationStates/{State()}')
    WAITING_PHONE = State()
    WAITING_USERNAME = State()

# Инициализация БД
def init_db():
    print(f'user/init_db/{sqlite3.connect('users.db')}')
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
    print(f'user/start_handler/{sqlite3.connect('users.db')}')
    user_id = message.from_user.id
    with sqlite3.connect('users.db') as conn:
        print(f'user/start_handler/sqlite3.connect/{sqlite3.connect('users.db')}')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_user_id = ?", (user_id,))
        if cursor.fetchone():
            print('user/start_handler/sqlite3.connect/if')
            await message.answer("Вы уже зарегистрированы!")
            return

    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(
        text="Отправить номер 📱",
        request_contact=True
    ))
    await message.answer(
        "Добро пожаловать! Регистрируйтесь на мероприятие «Бег, Кофе, Танцы».\n"
        "Пожалуйста, отправьте ваш номер телефона:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(RegistrationStates.WAITING_PHONE)


@user_router.message(F.contact)
async def contact_handler(message: types.Message, state: FSMContext):
    print('user/contact_handler')
    phone = message.contact.phone_number
    username = message.from_user.username

    if username:
        try:
            with sqlite3.connect('users.db') as conn:
                print('user/contact_handler/if/try/sqlite3.connect')
                conn.execute(
                    "INSERT INTO users (telegram_user_id, username, phone_number) VALUES (?, ?, ?)",
                    (message.from_user.id, username, phone)
                )
            await message.answer(
                "✅ Спасибо! Вы зарегистрированы!\n"
                "За день до события мы напомним вам о встрече!",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
        except sqlite3.IntegrityError:
            await message.answer("⚠️ Вы уже зарегистрированы!")
    else:
        await state.update_data(phone_number=phone)
        await message.answer("📛 Введите ваш username вручную:")
        await state.set_state(RegistrationStates.WAITING_USERNAME)

@user_router.message(RegistrationStates.WAITING_USERNAME)  # Теперь работает корректно
async def username_handler(message: types.Message, state: FSMContext):
    print('user/username_handler')
    data = await state.get_data()
    try:
        with sqlite3.connect('users.db') as conn:
            print('user/username_handler/try/sqlite3.connect')
            conn.execute(
                "INSERT INTO users (telegram_user_id, username, phone_number) VALUES (?, ?, ?)",
                (message.from_user.id, message.text, data['phone_number'])
            )
        await message.answer("✅ Регистрация завершена!")
        await state.clear()
    except sqlite3.IntegrityError:
        await message.answer("⚠️ Вы уже зарегистрированы!")