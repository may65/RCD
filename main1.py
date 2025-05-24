# main.py (дополненный)
from aiogram import Bot, Dispatcher
from routers.user import user_router
from routers.admin import admin_router
from routers.scheduler import setup_scheduler
# import os
# from dotenv import load_dotenv
from config1 import TELEGRAM_BOT_TOKEN

# load_dotenv()

# bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    # print('1')
    await setup_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # print('2')
    import asyncio
    asyncio.run(main())