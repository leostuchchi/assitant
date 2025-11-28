# backend/chart_services.py - ПОЛНАЯ РЕАЛИЗАЦИЯ
import logging
from typing import Dict, Any
import asyncio
from datetime import datetime

# ✅ ВСЕ НЕОБХОДИМЫЕ ИМПОРТЫ
from backend.database import async_session, UserAstroProfile
from backend.natal_chart import MLNatalChartCalculator
from backend.psyho_matrix import PsyhoMatrixCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select

# ✅ ИМПОРТ ИНТЕГРАЦИИ С MAGIC PROFILE
from .magic_profile_integration import get_magic_integration, magic_health_check_daemon

logger = logging.getLogger(__name__)


async def create_and_save_natal_chart(telegram_id: int, city: str, birth_datetime: datetime, timezone: str):
    """
    Полная реализация создания натальной карты с интеграцией Magic Profile
    """
    try:
        logger.info(f"🔮 Создание натальной карты для пользователя {telegram_id}")

        # 1. Получаем профиль пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        # 2. Создаем натальную карту
        calculator = MLNatalChartCalculator()
        natal_data = await calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

        # 3. Рассчитываем психоматрицу
        matrix_calculator = PsyhoMatrixCalculator()
        matrix_data = matrix_calculator.calculate_matrix(user_profile['birth_date'])

        # 4. Сохраняем в астропрофиль Astra
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                astro_profile.natal_chart_data = natal_data
                astro_profile.psyho_matrix_data = matrix_data
                logger.info(f"📝 Обновлен астропрофиль для {telegram_id}")
            else:
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data=natal_data,
                    psyho_matrix_data=matrix_data,
                    dominant_energy=None,
                    personality_traits=None
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль для {telegram_id}")

            await session.commit()

        # 5. ✅ ИНТЕГРАЦИЯ С MAGIC PROFILE
        astra_complete_data = {
            'natal_chart': natal_data,
            'psyho_matrix': matrix_data,
            'user_profile': user_profile,
            'calculation_timestamp': datetime.now().isoformat()
        }

        integration = await get_magic_integration()

        # Интеллектуальная отправка с проверкой доступности
        if await integration.health_check():
            send_task = asyncio.create_task(
                integration.send_profile_data_to_magic(telegram_id, astra_complete_data)
            )

            # Обработка результата отправки
            def log_send_result(task):
                try:
                    success = task.result()
                    if success:
                        logger.info(f"✅ Профиль {telegram_id} успешно передан в Magic Profile")
                    else:
                        logger.warning(f"⚠️ Не удалось передать профиль {telegram_id} в Magic Profile")
                except Exception as e:
                    logger.error(f"❌ Ошибка при передаче в Magic Profile: {e}")

            send_task.add_done_callback(log_send_result)
        else:
            logger.warning(f"⏸️ Magic Profile недоступен, пропускаем отправку для {telegram_id}")

        logger.info(f"💾 Натальная карта успешно сохранена для {telegram_id}")
        return astro_profile

    except Exception as e:
        logger.error(f"❌ Ошибка при создании натальной карты для {telegram_id}: {e}")
        raise


async def update_existing_profiles_for_magic():
    """
    Миграция существующих профилей в Magic Profile
    """
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(
                    UserAstroProfile.natal_chart_data.isnot(None)
                )
            )
            profiles = result.scalars().all()

            integration = await get_magic_integration()
            migrated_count = 0

            for profile in profiles:
                try:
                    # Получаем данные пользователя
                    user_profile = await get_user_profile(profile.telegram_id)
                    if not user_profile:
                        continue

                    astra_data = {
                        'natal_chart': profile.natal_chart_data,
                        'psyho_matrix': profile.psyho_matrix_data,
                        'user_profile': user_profile
                    }

                    success = await integration.send_profile_data_to_magic(
                        profile.telegram_id,
                        astra_data
                    )

                    if success:
                        migrated_count += 1
                        logger.info(f"✅ Мигрирован профиль {profile.telegram_id}")

                    # Задержка чтобы не перегружать сервис
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"❌ Ошибка миграции профиля {profile.telegram_id}: {e}")

            logger.info(f"🎉 Миграция завершена: {migrated_count}/{len(profiles)} профилей")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка миграции: {e}")