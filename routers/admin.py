#admin.py
from aiogram import Router, types
from aiogram.filters import Command
import csv
import sqlite3

admin_router = Router()

def is_admin(user_id: int) -> bool:
    # Добавить ID администраторов в .env
    print(f'admin/is_admin/{user_id}')
    return user_id in [123456789]

@admin_router.message(Command("list"))
async def list_handler(message: types.Message):
    print('admin/list_handler')
    # if not is_admin(message.from_user.id):
    #     print('admin/list_handler/is_admin')
    #     return

    with sqlite3.connect('users.db') as conn:
        print('admin/list_handler/sqlite3.connect')
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    print('admin/list_handler/message.answer')
    await message.answer(f"📊 Зарегистрировано участников: {count}")

@admin_router.message(Command("export"))
async def export_handler(message: types.Message):
    print(f'admin/export_handler/{types.Message}')
    # if not is_admin(message.from_user.id):
    #     print(f'admin/export_handler/if/{is_admin(message.from_user.id)}')
    #     return

    with sqlite3.connect('users.db') as conn:
        # print(f'admin/export_handler/with/{sqlite3.connect('users.db')}')
        users = conn.execute("SELECT * FROM users").fetchall()

    with open('users.csv', 'w', newline='', encoding='utf-8') as f:
        # print(f'admin/export_handler/with/{open('users.csv', 'w', newline='', encoding='utf-8')}')
        writer = csv.writer(f)
        writer.writerow(['ID', 'User ID', 'Username', 'Phone', 'Registration Time', 'Reminder Sent'])
        writer.writerows(users)
    print(f'admin/export_handler/{message.answer_document(types.FSInputFile('users.csv'))}')
    await message.answer_document(types.FSInputFile('users.csv'))

@admin_router.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    print(f'admin/broadcast_handler/{is_admin(message.from_user.id)}')
    # if not True:#is_admin(message.from_user.id):
    #     print(f'admin/broadcast_handler/if/{is_admin(message.from_user.id)}')
    #     return
    print(f'admin/broadcast_handler/')
    text = message.text.replace('/broadcast', '').strip()
    with sqlite3.connect('users.db') as conn:
        print('admin/broadcast_handler/sqlite3.connect')
        users = conn.execute("SELECT telegram_user_id FROM users").fetchall()

    for (user_id,) in users:
        try:
            print('admin/broadcast_handler/for/try')
            await message.bot.send_message(user_id, text)
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")