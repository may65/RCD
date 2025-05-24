# admin.py (исправленный)
from aiogram import Router, types
from aiogram.filters import Command
import csv
import sqlite3
from config1 import ADMINS  # Импортируем список администраторов
import asyncpg  # Заменяем sqlite3 на asyncpg

admin_router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS  # Используем список из config1.py

# @admin_router.message(Command("list"))
# async def list_handler(message: types.Message):
#     if not is_admin(message.from_user.id):
#         return  # Блокируем неадминистраторов
#     with sqlite3.connect('users.db') as conn:
#         count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
#     await message.answer(f"📊 Зарегистрировано участников: {count}")

@admin_router.message(Command("list"))
async def list_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    conn = await asyncpg.connect(...)  # Используйте настройки из config1.py
    count = await conn.fetchval("SELECT COUNT(*) FROM users")
    await message.answer(f"📊 Участников: {count}")
    await conn.close()

@admin_router.message(Command("export"))
async def export_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return  # Блокируем неадминистраторов

    with sqlite3.connect('users.db') as conn:
        users = conn.execute("SELECT * FROM users").fetchall()

    with open('users.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'User ID', 'Username', 'Phone', 'Registration Time', 'Reminder Sent'])
        writer.writerows(users)
    await message.answer_document(types.FSInputFile('users.csv'))

@admin_router.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return  # Блокируем неадминистраторов
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        await message.answer("🔴 Ошибка: укажите текст для рассылки - /broadcast абв")
        return

    with sqlite3.connect('users.db') as conn:
        users = conn.execute("SELECT telegram_user_id FROM users").fetchall()

    for (user_id,) in users:
        try:
            await message.bot.send_message(user_id, text)
        except Exception as e:
            print(f"Ошибка отправки {user_id}: {e}")