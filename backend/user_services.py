from backend.database import async_session, User
from sqlalchemy.future import select
from sqlalchemy import func  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ
from datetime import datetime  # ← ДОБАВИТЬ ДЛЯ calculated_at
import logging

logger = logging.getLogger(__name__)


async def create_or_update_user(
        telegram_id: int,
        birth_date,
        birth_time,
        birth_city: str,
        profession: str = None,
        job_position: str = None,
        current_city: str = None,
        gender: str = None
):
    """Создание или обновление пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Обновляем существующего пользователя
                user.birth_date = birth_date
                user.birth_time = birth_time
                user.birth_city = birth_city
                if profession:
                    user.profession = profession
                if job_position:
                    user.job_position = job_position
                if current_city:
                    user.current_city = current_city
                if gender is not None:
                    user.gender = gender
                logger.info(f"📝 Обновлен пользователь {telegram_id}")
            else:
                # Создаем нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    birth_city=birth_city,
                    profession=profession,
                    job_position=job_position,
                    current_city=current_city,
                    gender=gender,
                    request_count=0
                )
                session.add(user)
                logger.info(f"🆕 Создан новый пользователь {telegram_id}")

            await session.commit()
            return user

    except Exception as e:
        logger.error(f"❌ Ошибка при работе с пользователем {telegram_id}: {e}")
        raise


async def get_user_profile(telegram_id: int):
    """Получение профиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                return {
                    'telegram_id': user.telegram_id,
                    'birth_date': user.birth_date,
                    'birth_time': user.birth_time,
                    'birth_city': user.birth_city,
                    'profession': user.profession,
                    'job_position': user.job_position,
                    'current_city': user.current_city,
                    'gender': user.gender,
                    'request_count': user.request_count or 0,
                    'created_at': user.created_at
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении профиля {telegram_id}: {e}")
        return None


async def update_user_profession(telegram_id: int, profession: str, job_position: str = None):
    """Обновление профессиональных данных пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.profession = profession
                if job_position:
                    user.job_position = job_position
                await session.commit()
                logger.info(f"📝 Обновлены профессиональные данные для {telegram_id}")
                return user
            else:
                raise ValueError("Пользователь не найден")

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении профессии {telegram_id}: {e}")
        raise


async def increment_request_count(telegram_id: int):
    """Увеличивает счетчик обращений пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                current_count = user.request_count or 0
                user.request_count = current_count + 1
                await session.commit()
                logger.info(f"📈 Увеличен счетчик обращений для {telegram_id}: {current_count} -> {user.request_count}")
                return user.request_count
            else:
                logger.warning(f"⚠️ Пользователь {telegram_id} не найден при увеличении счетчика")
                return None

    except Exception as e:
        logger.error(f"❌ Ошибка при увеличении счетчика обращений {telegram_id}: {e}")
        return None


async def get_user_request_count(telegram_id: int):
    """Получение текущего количества обращений пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User.request_count).where(User.telegram_id == telegram_id)
            )
            count = result.scalar_one_or_none()
            return count or 0

    except Exception as e:
        logger.error(f"❌ Ошибка при получении счетчика обращений {telegram_id}: {e}")
        return 0


async def update_user_gender(telegram_id: int, gender: str):
    """Обновление пола пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.gender = gender
                await session.commit()
                logger.info(f"📝 Обновлен пол пользователя {telegram_id}: {gender}")
                return user
            else:
                raise ValueError("Пользователь не найден")

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении пола {telegram_id}: {e}")
        raise


async def get_users_statistics():
    """Получение общей статистики пользователей"""
    try:
        async with async_session() as session:
            # Общее количество пользователей
            total_users_result = await session.execute(
                select(User).where(User.telegram_id.isnot(None))
            )
            total_users = len(total_users_result.scalars().all())

            # Пользователи с заполненным полом
            users_with_gender_result = await session.execute(
                select(User).where(User.gender.isnot(None))
            )
            users_with_gender = len(users_with_gender_result.scalars().all())

            # Среднее количество обращений
            avg_requests_result = await session.execute(
                select(func.avg(User.request_count)).where(User.request_count > 0)
            )
            avg_requests = avg_requests_result.scalar() or 0

            return {
                'total_users': total_users,
                'users_with_gender': users_with_gender,
                'gender_fill_rate': round((users_with_gender / total_users * 100) if total_users > 0 else 0, 2),
                'average_requests': round(avg_requests, 2),
                'calculated_at': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики пользователей: {e}")
        return {
            'total_users': 0,
            'users_with_gender': 0,
            'gender_fill_rate': 0,
            'average_requests': 0,
            'error': str(e)
        }


