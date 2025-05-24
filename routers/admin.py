from aiogram import Router, types
from aiogram.filters import Command
import csv
import sqlite3
from config import ADMINS
from utils import load_messages

messages = load_messages()
admin_router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


@admin_router.message(Command("list"))
async def list_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    with sqlite3.connect('users.db') as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    await message.answer(messages['admin_list'].format(count=count))


@admin_router.message(Command("export"))
async def export_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    with sqlite3.connect('users.db') as conn:
        users = conn.execute("SELECT * FROM users").fetchall()

    with open('users.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'User ID', 'Username', 'Phone', 'Registration Time', 'Reminder Sent'])
        writer.writerows(users)

    await message.answer_document(types.FSInputFile('users.csv'), caption=messages['export_success'])


# @admin_router.message(Command("broadcast"))
# async def broadcast_handler(message: types.Message):
#     if not is_admin(message.from_user.id):
#         return
#
#     text = message.text.replace('/broadcast', '').strip()
#     if not text:
#         await message.answer("❌ Укажите текст: /broadcast <текст>")
#         return
#
#     with sqlite3.connect('users.db') as conn:
#         users = conn.execute("SELECT telegram_user_id FROM users").fetchall()
#
#     success = 0
#     errors = 0
#     for (user_id,) in users:
#         try:
#             await message.bot.send_message(user_id, text)
#             success += 1
#         except:
#             errors += 1
#
#     await message.answer(messages['broadcast_success'].format(success=success, errors=errors))
@admin_router.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    # Разделяем команду и текст
    parts = message.text.split(maxsplit=1)

    # Если после команды нет текста
    if len(parts) < 2:
        await message.answer(messages['broadcast_empty'])
        return

    text = parts[1].strip()  # Удаляем пробелы по краям

    # Если текст состоит только из пробелов
    if not text:
        await message.answer(messages['broadcast_empty'])
        return

    # Отправка сообщений пользователям
    success = 0
    errors = 0
    with sqlite3.connect('users.db') as conn:
        users = conn.execute("SELECT telegram_user_id FROM users").fetchall()

    for (user_id,) in users:
        try:
            await message.bot.send_message(user_id, text)
            success += 1
        except Exception as e:
            errors += 1

    await message.answer(
        messages['broadcast_result'].format(success=success, errors=errors)
    )