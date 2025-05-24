from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import sqlite3
from datetime import datetime, timedelta
from utils import get_event_date, load_messages

messages = load_messages()

async def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    event_date = get_event_date()

    async def send_reminders():
        now = datetime.now()
        if now + timedelta(hours=24) < event_date or now > event_date:
            return

        with sqlite3.connect('users.db') as conn:
            users = conn.execute(
                "SELECT telegram_user_id FROM users WHERE reminder_sent = FALSE"
            ).fetchall()

            for (user_id,) in users:
                try:
                    await bot.send_message(user_id, messages['reminder'])
                    conn.execute(
                        "UPDATE users SET reminder_sent = TRUE WHERE telegram_user_id = ?",
                        (user_id,)
                    )
                except Exception as e:
                    print(f"Ошибка: {e}")
            conn.commit()

    scheduler.add_job(send_reminders, 'interval', minutes=30)
    scheduler.start()