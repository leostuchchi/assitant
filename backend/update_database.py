"""
Database Structure Updater for Astra Project
Принудительное обновление структуры базы данных
"""

import asyncio
import logging
from backend.database import async_session, init_db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_database_structure():
    """Обновление структуры базы данных"""
    print("🔄 ОБНОВЛЕНИЕ СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 50)

    try:
        # Инициализируем БД (создаст недостающие таблицы)
        await init_db()
        print("✅ База данных инициализирована")

        # Добавляем недостающие колонки
        await add_missing_columns()

        print("🎯 Структура базы данных обновлена")

    except Exception as e:
        print(f"❌ Ошибка обновления структуры БД: {e}")


async def add_missing_columns():
    """Добавление недостающих колонок"""
    print("\n🔧 ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ КОЛОНОК...")

    column_updates = [
        {
            'table': 'calculation_cache',
            'column': 'cache_priority',
            'type': 'INTEGER',
            'default': '1'
        }
    ]

    async with async_session() as session:
        for update in column_updates:
            try:
                # Проверяем существование колонки
                check_query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{update['table']}' 
                AND column_name = '{update['column']}'
                """

                result = await session.execute(text(check_query))
                exists = result.scalar() is not None

                if not exists:
                    # Добавляем колонку
                    alter_query = f"""
                    ALTER TABLE {update['table']} 
                    ADD COLUMN {update['column']} {update['type']} DEFAULT {update['default']}
                    """

                    await session.execute(text(alter_query))
                    await session.commit()
                    print(f"   ✅ Добавлена колонка {update['table']}.{update['column']}")
                else:
                    print(f"   ✅ Колонка {update['table']}.{update['column']} уже существует")

            except Exception as e:
                print(f"   ❌ Ошибка добавления колонки {update['table']}.{update['column']}: {e}")


if __name__ == "__main__":
    asyncio.run(update_database_structure())