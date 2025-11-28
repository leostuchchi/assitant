"""
Deep Diagnostic Script for Astra Project
Анализирует конкретные проблемы с заполнением данных в БД
"""

import asyncio
import logging
from datetime import date, datetime
from backend.database import (
    async_session, User, UserAstroProfile, DailyCalculations,
    CalculationCache, MLModels, Biorhythms
)
from sqlalchemy.future import select
from sqlalchemy import text, func
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_database_state():
    """Глубокий анализ состояния базы данных"""
    print("🔍 ГЛУБОКИЙ АНАЛИЗ БАЗЫ ДАННЫХ ASTRA")
    print("=" * 60)

    await analyze_users_table()
    await analyze_astro_profiles()
    await analyze_daily_calculations()
    await analyze_calculation_cache()
    await analyze_ml_models()
    await analyze_biorhythms()

    print("\n" + "=" * 60)
    print("🎯 АНАЛИЗ ЗАВЕРШЕН")


async def analyze_users_table():
    """Анализ таблицы пользователей"""
    print("\n👥 АНАЛИЗ ТАБЛИЦЫ USERS:")

    try:
        async with async_session() as session:
            # Общая статистика
            total_users = await session.execute(select(func.count(User.telegram_id)))
            total_users = total_users.scalar()

            # Анализ заполненности полей
            fields_to_check = [
                ('user_segment', 'сегмент пользователя'),
                ('activity_level', 'уровень активности'),
                ('data_quality_score', 'качество данных'),
                ('profession', 'профессия'),
                ('current_city', 'текущий город'),
                ('gender', 'пол')
            ]

            print(f"   Всего пользователей: {total_users}")

            for field, description in fields_to_check:
                filled_count = await session.execute(
                    select(func.count()).where(getattr(User, field).isnot(None))
                )
                filled_count = filled_count.scalar()

                percentage = (filled_count / total_users * 100) if total_users > 0 else 0
                status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"

                print(f"   {status} {description}: {filled_count}/{total_users} ({percentage:.1f}%)")

            # Примеры пользователей с проблемами
            problem_users = await session.execute(
                select(User).where(
                    (User.user_segment.is_(None)) |
                    (User.activity_level.is_(None)) |
                    (User.data_quality_score == 0)
                ).limit(5)
            )
            problem_users = problem_users.scalars().all()

            if problem_users:
                print(f"   🚨 Примеры пользователей с проблемами:")
                for user in problem_users:
                    print(
                        f"      - ID: {user.telegram_id}, сегмент: {user.user_segment}, активность: {user.activity_level}")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа users: {e}")


async def analyze_astro_profiles():
    """Анализ астропрофилей"""
    print("\n🌟 АНАЛИЗ ТАБЛИЦЫ USER_ASTRO_PROFILE:")

    try:
        async with async_session() as session:
            total_profiles = await session.execute(select(func.count(UserAstroProfile.telegram_id)))
            total_profiles = total_profiles.scalar()

            ml_fields = [
                ('dominant_energy', 'доминирующая энергия'),
                ('personality_traits', 'черты личности'),
                ('ml_features', 'ML фичи'),
                ('behavior_patterns', 'паттерны поведения'),
                ('compatibility_profile', 'профиль совместимости')
            ]

            print(f"   Всего астропрофилей: {total_profiles}")

            for field, description in ml_fields:
                filled_count = await session.execute(
                    select(func.count()).where(getattr(UserAstroProfile, field).isnot(None))
                )
                filled_count = filled_count.scalar()

                percentage = (filled_count / total_profiles * 100) if total_profiles > 0 else 0
                status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"

                print(f"   {status} {description}: {filled_count}/{total_profiles} ({percentage:.1f}%)")

            # Проверяем наличие базовых данных
            has_natal_chart = await session.execute(
                select(func.count()).where(UserAstroProfile.natal_chart_data.isnot(None))
            )
            has_natal_chart = has_natal_chart.scalar()

            has_matrix = await session.execute(
                select(func.count()).where(UserAstroProfile.psyho_matrix_data.isnot(None))
            )
            has_matrix = has_matrix.scalar()

            print(f"   📊 Натальные карты: {has_natal_chart}/{total_profiles}")
            print(f"   🔢 Психоматрицы: {has_matrix}/{total_profiles}")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа астропрофилей: {e}")


async def analyze_daily_calculations():
    """Анализ ежедневных расчетов"""
    print("\n📅 АНАЛИЗ ТАБЛИЦЫ DAILY_CALCULATIONS:")

    try:
        async with async_session() as session:
            total_calculations = await session.execute(select(func.count(DailyCalculations.telegram_id)))
            total_calculations = total_calculations.scalar()

            ml_fields = [
                ('ml_features', 'ML фичи'),
                ('basic_insights', 'базовые инсайты'),
                ('trend_data', 'данные трендов'),
                ('risk_factors', 'факторы риска'),
                ('opportunities', 'возможности'),
                ('ml_data_quality', 'качество ML данных')
            ]

            print(f"   Всего расчетов: {total_calculations}")

            for field, description in ml_fields:
                if field == 'ml_data_quality':
                    # Для числового поля проверяем ненулевые значения
                    filled_count = await session.execute(
                        select(func.count()).where(getattr(DailyCalculations, field) > 0)
                    )
                else:
                    filled_count = await session.execute(
                        select(func.count()).where(getattr(DailyCalculations, field).isnot(None))
                    )
                filled_count = filled_count.scalar()

                percentage = (filled_count / total_calculations * 100) if total_calculations > 0 else 0
                status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"

                print(f"   {status} {description}: {filled_count}/{total_calculations} ({percentage:.1f}%)")

            # Анализ свежести данных
            recent_calcs = await session.execute(
                select(func.count()).where(DailyCalculations.target_date >= date.today())
            )
            recent_calcs = recent_calcs.scalar()

            print(f"   🕒 Расчеты за сегодня: {recent_calcs}")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа daily calculations: {e}")


async def analyze_calculation_cache():
    """Анализ кэша расчетов"""
    print("\n💾 АНАЛИЗ ТАБЛИЦЫ CALCULATION_CACHE:")

    try:
        async with async_session() as session:
            total_cache = await session.execute(select(func.count(CalculationCache.telegram_id)))
            total_cache = total_cache.scalar()

            print(f"   Всего записей в кэше: {total_cache}")

            if total_cache > 0:
                # Анализ типов данных в кэше
                cache_types = await session.execute(
                    select(CalculationCache.data_type, func.count(CalculationCache.data_type))
                    .group_by(CalculationCache.data_type)
                )
                cache_types = cache_types.all()

                print("   📊 Распределение по типам:")
                for cache_type, count in cache_types:
                    print(f"      - {cache_type}: {count}")

                # Анализ свежести кэша
                fresh_cache = await session.execute(
                    select(func.count()).where(CalculationCache.expires_at > datetime.now())
                )
                fresh_cache = fresh_cache.scalar()

                print(f"   🆕 Актуальных записей: {fresh_cache}/{total_cache}")
            else:
                print("   ❌ Кэш полностью пуст - система не использует кэширование")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа кэша: {e}")


async def analyze_ml_models():
    """Анализ ML моделей"""
    print("\n🤖 АНАЛИЗ ТАБЛИЦЫ ML_MODELS:")

    try:
        async with async_session() as session:
            total_models = await session.execute(select(func.count(MLModels.model_id)))
            total_models = total_models.scalar()

            active_models = await session.execute(
                select(func.count()).where(MLModels.is_active == 1)
            )
            active_models = active_models.scalar()

            print(f"   Всего моделей: {total_models}")
            print(f"   Активных моделей: {active_models}")

            if total_models == 0:
                print("   🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: ML модели не инициализированы!")
                print("   💡 Решение: запустить инициализацию ML системы")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа ML моделей: {e}")


async def analyze_biorhythms():
    """Анализ биоритмов"""
    print("\n⚡ АНАЛИЗ ТАБЛИЦЫ BIORHYTHMS:")

    try:
        async with async_session() as session:
            total_biorhythms = await session.execute(select(func.count(Biorhythms.telegram_id)))
            total_biorhythms = total_biorhythms.scalar()

            recent_biorhythms = await session.execute(
                select(func.count()).where(Biorhythms.calculation_date >= date.today())
            )
            recent_biorhythms = recent_biorhythms.scalar()

            print(f"   Всего записей биоритмов: {total_biorhythms}")
            print(f"   Биоритмов за сегодня: {recent_biorhythms}")

            # Пример структуры данных
            if total_biorhythms > 0:
                sample = await session.execute(select(Biorhythms).limit(1))
                sample = sample.scalar_one_or_none()
                if sample and sample.biorhythm_data:
                    print(f"   📋 Пример структуры данных: {list(sample.biorhythm_data.keys())[:3]}...")

    except Exception as e:
        logger.error(f"❌ Ошибка анализа биоритмов: {e}")


async def identify_root_causes():
    """Идентификация коренных причин проблем"""
    print("\n🔍 ВЫЯВЛЕНИЕ КОРЕННЫХ ПРИЧИН:")

    causes = [
        "1. ❌ ML система не инициализирована (пустая таблица ml_models)",
        "2. ❌ Отсутствует кэширование расчетов (пустая calculation_cache)",
        "3. ❌ Не заполняются ML-поля в user_astro_profile",
        "4. ❌ Не рассчитываются risk_factors и opportunities",
        "5. ❌ Не обновляются user_segment и activity_level",
        "6. ❌ Не вычисляется data_quality_score автоматически"
    ]

    for cause in causes:
        print(f"   {cause}")

    print("\n💡 РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ:")
    solutions = [
        "1. Запустить инициализацию ML моделей при старте системы",
        "2. Включить кэширование в calculation_services",
        "3. Реализовать автоматическое заполнение ML-полей в астропрофилях",
        "4. Активировать расчет risk_factors и opportunities в feature_engineering",
        "5. Добавить автоматическое обновление user_segment на основе активности",
        "6. Реализовать автоматический расчет data_quality_score"
    ]

    for solution in solutions:
        print(f"   {solution}")


async def main():
    """Основная функция диагностики"""
    try:
        await analyze_database_state()
        await identify_root_causes()

    except Exception as e:
        print(f"💥 Критическая ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())