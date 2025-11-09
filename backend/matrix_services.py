from backend.database import async_session, PsyhoMatrix
from backend.psyho_matrix import PsyhoMatrixCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def calculate_and_save_psyho_matrix(telegram_id: int):
    """Расчет и сохранение психоматрицы"""
    try:
        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError("Пользователь не найден")

        calculator = PsyhoMatrixCalculator()
        matrix_data = calculator.calculate_matrix(user_profile['birth_date'])

        # Сохраняем психоматрицу
        async with async_session() as session:
            result = await session.execute(
                select(PsyhoMatrix).where(PsyhoMatrix.telegram_id == telegram_id)
            )
            psyho_matrix = result.scalar_one_or_none()

            if psyho_matrix:
                # Обновляем существующую психоматрицу
                psyho_matrix.matrix_data = matrix_data
                logger.info(f"📝 Обновлена психоматрица для {telegram_id}")
            else:
                # Создаем новую психоматрицу
                psyho_matrix = PsyhoMatrix(
                    telegram_id=telegram_id,
                    matrix_data=matrix_data
                )
                session.add(psyho_matrix)
                logger.info(f"🆕 Создана новая психоматрица для {telegram_id}")

            await session.commit()
            logger.info(f"✅ Психоматрица рассчитана и сохранена для {telegram_id}")

        return matrix_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете психоматрицы для {telegram_id}: {e}")
        raise


async def get_user_matrix(telegram_id: int):
    """Получение психоматрицы пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(PsyhoMatrix).where(PsyhoMatrix.telegram_id == telegram_id)
            )
            matrix = result.scalar_one_or_none()

            if matrix:
                return matrix.matrix_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении психоматрицы {telegram_id}: {e}")
        return None