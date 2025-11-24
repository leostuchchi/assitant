from aiogram import Bot, Dispatcher
import asyncio
import logging

from bot.config import TOKEN
from bot.handlers import router
from backend.db_connection import check_db_connection

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def setup_bot() -> tuple[Bot, Dispatcher]:
    """
    Инициализация и настройка бота
    Returns:
        Кортеж (Bot, Dispatcher)
    """
    try:
        bot = Bot(token=TOKEN)
        dp = Dispatcher()

        # Подключаем роутер
        dp.include_router(router)

        logger.info("✅ Бот инициализирован успешно")
        return bot, dp

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        raise


async def health_checks() -> bool:
    """
    Проверка здоровья всех зависимостей
    Returns:
        bool: True если все проверки пройдены
    """
    checks_passed = True

    # Проверка базы данных
    logger.info("🔍 Проверка подключения к базе данных...")
    db_connected = await check_db_connection()
    if not db_connected:
        logger.error("❌ Не удалось подключиться к базе данных")
        checks_passed = False
    else:
        logger.info("✅ База данных подключена успешно")

    # Здесь можно добавить проверки других сервисов
    # - Проверка подключения к Ollama
    # - Проверка доступности эфемерид
    # - Проверка дискового пространства

    return checks_passed


async def start_polling(bot: Bot, dp: Dispatcher):
    """
    Запуск поллинга бота с обработкой ошибок
    """
    try:
        logger.info("🔄 Запуск поллинга бота...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при работе бота: {e}")
        raise

    finally:
        logger.info("🛑 Завершение работы бота...")


async def graceful_shutdown(bot: Bot):
    """
    Корректное завершение работы бота
    """
    try:
        await bot.close()
        logger.info("✅ Бот корректно остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")


async def main():
    """
    Главная функция запуска приложения
    """
    bot = None
    try:
        logger.info("🚀 Запуск Personal Assistant...")

        # Проверка здоровья системы
        if not await health_checks():
            logger.error("❌ Проверки здоровья не пройдены. Завершение работы.")
            return

        # Инициализация бота
        bot, dp = await setup_bot()

        logger.info("""
✅ Personal Assistant успешно запущен!

📊 Статус системы:
• База данных: ✅ подключена
• Telegram Bot: ✅ инициализирован
• Обработчики: ✅ загружены
• Готов к работе!
        """)

        # Запуск поллинга
        await start_polling(bot, dp)

    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал прерывания (Ctrl+C)")

    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка в главном процессе: {e}")

    finally:
        # Корректное завершение
        if bot:
            await graceful_shutdown(bot)

        logger.info("👋 Personal Assistant завершил работу")


if __name__ == "__main__":
    # Запуск асинхронного приложения
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Демон остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")