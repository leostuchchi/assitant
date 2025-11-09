from backend.database import async_session, UserNatalChart
from backend.natal_chart import MLNatalChartCalculator
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def create_and_save_natal_chart(telegram_id: int, city: str, birth_datetime, timezone: str):
    """Создание и сохранение натальной карты"""
    try:
        calculator = MLNatalChartCalculator()
        natal_data = calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

        logger.info(f"Создание натальной карты для пользователя {telegram_id}")

        async with async_session() as session:
            result = await session.execute(
                select(UserNatalChart).where(UserNatalChart.telegram_id == telegram_id)
            )
            natal_chart = result.scalar_one_or_none()

            if natal_chart:
                # Обновляем существующую натальную карту
                natal_chart.natal_data = natal_data
                logger.info(f"📝 Обновлена натальная карта для {telegram_id}")
            else:
                # Создаем новую натальную карту
                natal_chart = UserNatalChart(
                    telegram_id=telegram_id,
                    natal_data=natal_data
                )
                session.add(natal_chart)
                logger.info(f"🆕 Создана новая натальная карта для {telegram_id}")

            await session.commit()
            logger.info(f"💾 Натальная карта успешно сохранена для {telegram_id}")
            return natal_chart

    except Exception as e:
        logger.error(f"❌ Ошибка при создании натальной карты для {telegram_id}: {e}")
        raise


async def get_user_natal_chart(telegram_id: int):
    """Получение натальной карты пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserNatalChart).where(UserNatalChart.telegram_id == telegram_id)
            )
            natal_chart = result.scalar_one_or_none()

            if natal_chart:
                return natal_chart.natal_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении натальной карты {telegram_id}: {e}")
        return None