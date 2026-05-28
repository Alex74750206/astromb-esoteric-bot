import asyncio
import logging
import sys
import os

# Добавляем папку bot в путь для импортов
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, FSInputFile

_PROFILE_PHOTO = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "assets", "profile_photo.jpg")
)

from config import BOT_TOKEN
from database import init_db
from handlers import start, catalog, payment, admin
from scheduler import setup_scheduler
from utils.file_server import start_file_server
from utils.excel_export import EXCEL_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN не задан в .env файле!")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(payment.router)

    await init_db()
    log.info("База данных инициализирована")

    from utils.excel_export import update_clients_excel
    await update_clients_excel()
    log.info("Клиенты.xlsx обновлён при старте")

    # Страница бота — описание и команды
    await bot.set_my_description(
        "🔮 Персональные разборы по дате рождения\n\n"
        "Нумерология · Матрица судьбы · Ба Цзы · Гороскоп 2026 · Натальная карта\n\n"
        "✨ Начните с бесплатного разбора числа судьбы — просто нажмите «Старт»\n\n"
        "Все разборы приходят мгновенно прямо в этот чат.\n"
        "Оплата через Telegram Stars — быстро и безопасно."
    )
    await bot.set_my_short_description(
        "🔮 Ваш личный астролог и нумеролог. Разбор по дате рождения — мгновенно."
    )
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start",   description="✨ Начать — бесплатный разбор"),
            BotCommand(command="catalog", description="🔮 Каталог персональных разборов"),
            BotCommand(command="help",    description="❓ Помощь и информация"),
            BotCommand(command="excel",   description="📥 Обновить Excel (только для админов)"),
        ],
        scope=BotCommandScopeDefault(),
    )
    log.info("Описание и команды бота обновлены")

    if os.path.exists(_PROFILE_PHOTO):
        log.info(f"Фото профиля готово: {_PROFILE_PHOTO} — установите через @BotFather /setuserpic")

    scheduler = setup_scheduler(bot)
    scheduler.start()
    log.info("Планировщик воронки запущен")

    download_port  = int(os.getenv("DOWNLOAD_PORT", "0"))
    download_token = os.getenv("DOWNLOAD_TOKEN", "")
    if download_port and download_token:
        start_file_server(EXCEL_PATH, download_port, download_token)

    log.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
