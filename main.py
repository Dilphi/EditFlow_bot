#!/usr/bin/env python3
"""
Telegram бот для обработки текстовых файлов с веб-панелью управления
Версия: 1.0
"""

import asyncio
import logging
import threading
import sys

from aiogram import Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TELEGRAM_TOKEN, check_config
from handlers import router, bot
from web_panel import run_web_panel
import handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("text_bot")

# Проверяем конфигурацию
try:
    check_config()
except RuntimeError as e:
    logger.error(e)
    sys.exit(1)

# Создаем диспетчер
dp = Dispatcher()
dp.include_router(router)

async def set_commands():
    """Устанавливает команды бота."""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="📖 Помощь и инструкция"),
        BotCommand(command="mode", description="🎯 Выбрать режим обработки"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Главная функция."""
    # Запускаем веб-панель в отдельном потоке
    web_thread = threading.Thread(
        target=run_web_panel,
        args=(handlers,),
        daemon=True
    )
    web_thread.start()
    logger.info("🌐 Веб-панель запущена в фоновом режиме")
    
    # Устанавливаем команды
    await set_commands()
    
    # Запускаем бота
    logger.info("🚀 Запуск бота...")
    logger.info(f"📡 Используются модели: Gemini + Groq (автопереключение)")
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Завершение работы...")
        sys.exit(0)