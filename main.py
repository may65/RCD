# main.py
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from routers.user import user_router
from routers.admin import admin_router
from routers.scheduler import setup_scheduler
from config import TOKEN

# Инициализация бота с новым синтаксисом
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


dp = Dispatcher()
dp.include_router(user_router)
dp.include_router(admin_router)

async def main():
    await setup_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())