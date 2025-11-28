"""
Database Monitor for Astra Project
Автоматический мониторинг и поддержание целостности данных
"""

import asyncio
import logging
from datetime import datetime, timedelta
from backend.database_fixes import DatabaseFixer
from backend.database import check_db_connection
import schedule
import time

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Монитор для автоматического поддержания целостности БД"""

    def __init__(self):
        self.fixer = DatabaseFixer()
        self.check_interval_hours = 24  # Проверка раз в сутки

    async def start_monitoring(self):
        """Запуск автоматического мониторинга"""
        print("🔍 ЗАПУСК АВТОМАТИЧЕСКОГО МОНИТОРИНГА БАЗЫ ДАННЫХ")

        # Немедленная проверка при запуске
        await self.run_health_check()

        # Планируем регулярные проверки
        schedule.every(self.check_interval_hours).hours.do(
            lambda: asyncio.create_task(self.run_health_check())
        )

        print(f"✅ Мониторинг запущен. Проверки каждые {self.check_interval_hours} часов")

        # Бесконечный цикл для выполнения запланированных задач
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Проверяем каждую минуту

    async def run_health_check(self):
        """Запуск проверки здоровья и исправлений"""
        print(f"\n🕒 Проверка здоровья БД: {datetime.now()}")

        try:
            # Проверяем подключение
            if not await check_db_connection():
                print("❌ Потеряно подключение к БД")
                return

            # Запускаем исправления
            await self.fixer.apply_all_fixes()

            print("✅ Проверка здоровья завершена")

        except Exception as e:
            print(f"❌ Ошибка при проверке здоровья: {e}")


# Запуск мониторинга
async def start_database_monitor():
    """Запуск монитора БД"""
    monitor = DatabaseMonitor()
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(start_database_monitor())