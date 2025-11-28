"""
Database Diagnostic Script for Astra Project
Проверяет подключение, таблицы и базовые операции записи/чтения
"""

import asyncio
import logging
from datetime import date, datetime
from backend.database import (
    async_session, init_db, check_db_connection,
    User, UserAstroProfile, DailyCalculations, MLModels
)
from sqlalchemy.future import select
from sqlalchemy import text
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database_health():
    """Полная проверка здоровья базы данных"""
    print("🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ ASTRA")
    print("=" * 50)

    # 1. Проверка подключения
    print("1. 🔗 Проверка подключения к БД...")
    connected = await check_db_connection()
    print(f"   Результат: {'✅ Успешно' if connected else '❌ Ошибка'}")

    if not connected:
        print("   🗄️ Попытка инициализации БД...")
        await init_db()
        connected = await check_db_connection()
        print(f"   После инициализации: {'✅ Успешно' if connected else '❌ Ошибка'}")

    if not connected:
        return False

    # 2. Проверка существования таблиц
    print("\n2. 📊 Проверка структуры таблиц...")
    tables_status = await check_tables_existence()
    for table_name, exists in tables_status.items():
        print(f"   {table_name}: {'✅ Существует' if exists else '❌ Отсутствует'}")

    # 3. Проверка записи в таблицы
    print("\n3. ✍️ Тест записи в таблицы...")
    test_user_id = 999888777  # Тестовый пользователь

    # Тест записи пользователя
    user_write_ok = await test_user_write(test_user_id)
    print(f"   Таблица users: {'✅ Запись успешна' if user_write_ok else '❌ Ошибка записи'}")

    # Тест чтения пользователя
    user_read_ok = await test_user_read(test_user_id)
    print(f"   Таблица users: {'✅ Чтение успешно' if user_read_ok else '❌ Ошибка чтения'}")

    # Тест записи daily calculations
    daily_write_ok = await test_daily_calculations_write(test_user_id)
    print(f"   Таблица daily_calculations: {'✅ Запись успешна' if daily_write_ok else '❌ Ошибка записи'}")

    # 4. Проверка ML моделей
    print("\n4. 🤖 Проверка ML моделей...")
    ml_models_ok = await check_ml_models()
    print(f"   ML модели: {'✅ Настроены' if ml_models_ok else '⚠️ Требуют настройки'}")

    # 5. Статистика базы данных
    print("\n5. 📈 Статистика БД...")
    await show_database_stats()

    print("\n" + "=" * 50)
    print("🎯 ДИАГНОСТИКА ЗАВЕРШЕНА")

    return all([user_write_ok, user_read_ok, daily_write_ok])


async def check_tables_existence():
    """Проверка существования всех таблиц"""
    tables_status = {}

    try:
        async with async_session() as session:
            # Проверяем основные таблицы
            tables_to_check = [
                ('users', User),
                ('user_astro_profile', UserAstroProfile),
                ('daily_calculations', DailyCalculations),
                ('biorhythms', None),
                ('calculation_cache', None),
                ('ml_models', MLModels)
            ]

            for table_name, table_class in tables_to_check:
                if table_class:
                    # Проверяем через SQLAlchemy модель
                    try:
                        result = await session.execute(select(table_class).limit(1))
                        tables_status[table_name] = True
                    except Exception as e:
                        print(f"      Ошибка проверки {table_name}: {e}")
                        tables_status[table_name] = False
                else:
                    # Проверяем через raw SQL с text()
                    try:
                        await session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
                        tables_status[table_name] = True
                    except Exception as e:
                        print(f"      Ошибка проверки {table_name}: {e}")
                        tables_status[table_name] = False

    except Exception as e:
        logger.error(f"❌ Ошибка проверки таблиц: {e}")
        return {table: False for table, _ in tables_to_check}

    return tables_status


async def test_user_write(telegram_id: int):
    """Тест записи пользователя"""
    try:
        async with async_session() as session:
            # Проверяем, существует ли уже пользователь
            existing_user = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            existing_user = existing_user.scalar_one_or_none()

            if existing_user:
                # Если существует, обновляем
                existing_user.request_count = (existing_user.request_count or 0) + 1
                existing_user.updated_at = datetime.now()
                print(f"   👤 Обновлен существующий пользователь: {telegram_id}")
            else:
                # Создаем нового тестового пользователя
                new_user = User(
                    telegram_id=telegram_id,
                    birth_date=date(1990, 1, 1),
                    birth_time=datetime.now().time(),
                    birth_city="Тестовый город",
                    profession="Тестовая профессия",
                    job_position="Тестовая должность",
                    current_city="Текущий город",
                    gender="male",
                    request_count=1,
                    user_segment="beginner",
                    activity_level="medium",
                    data_quality_score=75
                )
                session.add(new_user)
                print(f"   👤 Создан новый пользователь: {telegram_id}")

            await session.commit()
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка записи пользователя: {e}")
        await session.rollback()
        return False


async def test_user_read(telegram_id: int):
    """Тест чтения пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                print(f"   👤 Найден пользователь: {user.telegram_id}, запросов: {user.request_count}")
                return True
            else:
                print("   ❌ Пользователь не найден")
                return False

    except Exception as e:
        logger.error(f"❌ Ошибка чтения пользователя: {e}")
        return False


async def test_daily_calculations_write(telegram_id: int):
    """Тест записи daily calculations"""
    try:
        async with async_session() as session:
            today = date.today()

            # Создаем тестовые данные
            test_biorhythm_data = {
                "cycles": {
                    "physical": {"percentage": 75, "phase": "rising"},
                    "emotional": {"percentage": 60, "phase": "stable"},
                    "intellectual": {"percentage": 80, "phase": "peak"}
                },
                "overall_energy": {"percentage": 72},
                "critical_days_count": 0,
                "peak_days_count": 1,
                "days_lived": 12000
            }

            test_astro_data = {
                "transits": {
                    "total_planets": 8,
                    "retrograde_planets": ["Mercury", "Venus"]
                },
                "aspects_count": 12,
                "strong_aspects_count": 4,
                "key_aspects": [
                    {"aspect": "trine", "planets": ["Sun", "Moon"], "strength": 0.8}
                ]
            }

            # Проверяем существующую запись
            existing_calc = await session.execute(
                select(DailyCalculations).where(
                    DailyCalculations.telegram_id == telegram_id,
                    DailyCalculations.target_date == today
                )
            )
            existing_calc = existing_calc.scalar_one_or_none()

            if existing_calc:
                # Обновляем существующую
                existing_calc.biorhythm_data = test_biorhythm_data
                existing_calc.astro_transits_data = test_astro_data
                existing_calc.ml_features = {"daily_score": 0.75, "energy_overall": 0.72}
                existing_calc.basic_insights = ["Тестовый инсайт 1", "Тестовый инсайт 2"]
                existing_calc.calculation_timestamp = datetime.now()
                print(f"   📅 Обновлен существующий расчет для {telegram_id}")
            else:
                # Создаем новую
                new_calc = DailyCalculations(
                    telegram_id=telegram_id,
                    target_date=today,
                    biorhythm_data=test_biorhythm_data,
                    astro_transits_data=test_astro_data,
                    calculation_metadata={"source": "diagnostic_test"},
                    data_hash="test_hash_123",
                    ml_features={"daily_score": 0.75, "energy_overall": 0.72},
                    basic_insights=["Тестовый инсайт 1", "Тестовый инсайт 2"],
                    ml_data_quality=85
                )
                session.add(new_calc)
                print(f"   📅 Создан новый расчет для {telegram_id} на {today}")

            await session.commit()
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка записи daily calculations: {e}")
        await session.rollback()
        return False


async def check_ml_models():
    """Проверка наличия ML моделей"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(MLModels).where(MLModels.is_active == 1)
            )
            models = result.scalars().all()

            if models:
                print(f"   🤖 Найдено активных ML моделей: {len(models)}")
                for model in models:
                    print(f"      - {model.model_id} v{model.model_version} ({model.model_type})")
                return True
            else:
                print("   ⚠️ Активные ML модели не найдены")
                # Создаем базовые ML модели
                await create_basic_ml_models()
                return False

    except Exception as e:
        logger.error(f"❌ Ошибка проверки ML моделей: {e}")
        return False


async def create_basic_ml_models():
    """Создание базовых ML моделей"""
    try:
        async with async_session() as session:
            basic_models = [
                MLModels(
                    model_id="feature_engineering",
                    model_version="1.0",
                    model_type="feature_engineering",
                    model_metadata={"description": "Basic feature engineering model"},
                    accuracy_score=85,
                    training_date=date.today(),
                    is_active=1
                ),
                MLModels(
                    model_id="trend_analyzer",
                    model_version="1.0",
                    model_type="trend_analysis",
                    model_metadata={"description": "Basic trend analysis model"},
                    accuracy_score=80,
                    training_date=date.today(),
                    is_active=1
                )
            ]

            for model in basic_models:
                session.add(model)

            await session.commit()
            print("   🤖 Созданы базовые ML модели")

    except Exception as e:
        logger.error(f"❌ Ошибка создания ML моделей: {e}")


async def show_database_stats():
    """Показать статистику базы данных"""
    try:
        async with async_session() as session:
            # Количество пользователей
            users_count = await session.execute(select(User))
            users_count = len(users_count.scalars().all())

            # Количество daily calculations
            daily_count = await session.execute(select(DailyCalculations))
            daily_count = len(daily_count.scalars().all())

            # Количество ML моделей
            ml_models_count = await session.execute(select(MLModels))
            ml_models_count = len(ml_models_count.scalars().all())

            print(f"   👥 Пользователей: {users_count}")
            print(f"   📊 Daily calculations: {daily_count}")
            print(f"   🤖 ML моделей: {ml_models_count}")

            # Последняя запись
            last_calc = await session.execute(
                select(DailyCalculations).order_by(DailyCalculations.calculation_timestamp.desc()).limit(1)
            )
            last_calc = last_calc.scalar_one_or_none()

            if last_calc:
                print(f"   🕒 Последний расчет: {last_calc.calculation_timestamp}")

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")


async def cleanup_test_data(telegram_id: int):
    """Очистка тестовых данных"""
    try:
        async with async_session() as session:
            # Удаляем тестового пользователя
            await session.execute(
                User.__table__.delete().where(User.telegram_id == telegram_id)
            )

            # Удаляем тестовые расчеты
            await session.execute(
                DailyCalculations.__table__.delete().where(DailyCalculations.telegram_id == telegram_id)
            )

            await session.commit()
            print(f"🧹 Тестовые данные для {telegram_id} очищены")

    except Exception as e:
        logger.error(f"❌ Ошибка очистки тестовых данных: {e}")


async def main():
    """Основная функция диагностики"""
    test_user_id = 999888777

    try:
        # Запускаем диагностику
        success = await check_database_health()

        if success:
            print("\n🎉 БАЗА ДАННЫХ РАБОТАЕТ КОРРЕКТНО!")
            print("   Все основные операции записи/чтения успешны")
        else:
            print("\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С БАЗОЙ ДАННЫХ")
            print("   Требуется дополнительная диагностика")

        # Очищаем тестовые данные
        await cleanup_test_data(test_user_id)

    except Exception as e:
        print(f"💥 Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())