# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import sqlite3
from datetime import datetime, timedelta
import asyncpg  # Заменяем sqlite3 на asyncpg

async def setup_scheduler(bot: Bot):
    # print('scheduler/setup_scheduler')
    scheduler = AsyncIOScheduler()
    event_date = datetime(2024, 1, 1)  # Установите дату мероприятия

    async def send_reminders():
        conn = await asyncpg.connect(...)
        users = await conn.fetch(
            "SELECT telegram_user_id FROM users WHERE reminder_sent = FALSE"
        )
        for user in users:
            await conn.execute(
                "UPDATE users SET reminder_sent = TRUE WHERE telegram_user_id = $1",
                user['telegram_user_id']
            )
        await conn.close()

    # async def send_reminders():
    #     # print('scheduler/setup_scheduler/send_reminders')
    #     now = datetime.now()
    #     if now + timedelta(hours=24) < event_date:
    #         # print('scheduler/setup_scheduler/send_reminders/if')
    #         return
    #
    #     with sqlite3.connect('users.db') as conn:
    #         # print('scheduler/setup_scheduler/send_reminders/sqlite3.connect')
    #         users = conn.execute(
    #             "SELECT telegram_user_id FROM users WHERE reminder_sent = FALSE"
    #         ).fetchall()
    #
    #         for (user_id,) in users:
    #             try:
    #                 # print('scheduler/setup_scheduler/send_reminders/sqlite3.connect/try')
    #                 await bot.send_message(
    #                     user_id,
    #                     "⏰ Напоминаем: завтра состоится мероприятие «Бег, Кофе, Танцы»! Ждём вас!"
    #                 )
    #                 conn.execute(
    #                     "UPDATE users SET reminder_sent = TRUE WHERE telegram_user_id = ?",
    #                     (user_id,)
    #                 )
    #             except Exception as e:
    #                 print(f"Reminder error: {e}")
    #
    #         conn.commit()

    scheduler.add_job(send_reminders, 'interval', minutes=30)
    scheduler.start()