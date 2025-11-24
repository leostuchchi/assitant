import os
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, String, Date, Time, Text, ForeignKey, Integer
from sqlalchemy import select, and_
from sqlalchemy.sql import func
from sqlalchemy import Index
import logging

logger = logging.getLogger(__name__)

# Настройка подключения к базе данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://astra_user:astra_password_2024@localhost:5435/astra_db"
)

logger.info(f"🔗 Подключаемся к БД Astra: postgresql+asyncpg://astra_user:******@localhost:5435/astra_db")

# Создание асинхронного движка
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Отключаем подробное логирование в продакшене
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo_pool=False
)

# Создание асинхронной сессии
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Базовый класс для моделей
Base = declarative_base()


class User(Base):
    """
    Основная таблица пользователей проекта Astra
    """
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(Time, nullable=False)
    birth_city = Column(String(100), nullable=False)
    profession = Column(String(100), nullable=True)
    job_position = Column(String(100), nullable=True)
    current_city = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)  # 'male', 'female', None
    request_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, birth_date={self.birth_date})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'birth_city': self.birth_city,
            'profession': self.profession,
            'job_position': self.job_position,
            'current_city': self.current_city,
            'gender': self.gender,
            'request_count': self.request_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserAstroProfile(Base):
    """
    Статические астрологические данные пользователя
    Объединяет натальную карту и психоматрицу
    """
    __tablename__ = 'user_astro_profile'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    natal_chart_data = Column(JSON, nullable=False)
    psyho_matrix_data = Column(JSON, nullable=False)
    dominant_energy = Column(String(50), nullable=True)
    personality_traits = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserAstroProfile(telegram_id={self.telegram_id})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'natal_chart_summary': {
                'planets_count': len(self.natal_chart_data.get('planets', {})),
                'dominant_element': self._get_dominant_element(),
                'ascendant': self.natal_chart_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
            },
            'psyho_matrix_summary': {
                'life_path_number': self.psyho_matrix_data.get('basic_numbers', {}).get('first'),
                'matrix_complexity': self._calculate_matrix_complexity()
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def _get_dominant_element(self):
        """Определение доминирующего элемента"""
        try:
            element_balance = self.natal_chart_data.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _calculate_matrix_complexity(self):
        """Оценка сложности психоматрицы"""
        try:
            matrix_data = self.psyho_matrix_data.get('pythagoras_matrix', {})
            total_digits = sum(matrix_data.values())
            if total_digits >= 15:
                return "сложная"
            elif total_digits >= 10:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"


class DailyCalculations(Base):
    """
    Ежедневные расчеты для конкретных дат
    Оптимизированная таблица для частых запросов
    """
    __tablename__ = 'daily_calculations'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    biorhythm_data = Column(JSON, nullable=False)
    astro_transits_data = Column(JSON, nullable=False)
    calculation_metadata = Column(JSON, nullable=False, default={})
    data_hash = Column(String(64), nullable=False)
    calculation_timestamp = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<DailyCalculations(telegram_id={self.telegram_id}, date={self.target_date})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'astro_transits_data': self.astro_transits_data,
            'calculation_metadata': self.calculation_metadata,
            'data_hash': self.data_hash,
            'calculation_timestamp': self.calculation_timestamp.isoformat() if self.calculation_timestamp else None
        }


class Biorhythms(Base):
    """
    Исторические данные биоритмов
    Сохранена для обратной совместимости
    """
    __tablename__ = 'biorhythms'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    biorhythm_data = Column(JSON, nullable=False)
    calculation_date = Column(Date, primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Biorhythms(telegram_id={self.telegram_id}, date={self.calculation_date})>"

    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'calculation_date': self.calculation_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CalculationCache(Base):
    """
    Кэш расчетов для оптимизации производительности
    """
    __tablename__ = 'calculation_cache'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    data_type = Column(String(20), primary_key=True)  # 'biorhythm', 'transits', 'combined'
    calculation_data = Column(JSON, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<CalculationCache(telegram_id={self.telegram_id}, date={self.target_date}, type={self.data_type})>"

    def is_expired(self):
        """Проверка истечения срока действия кэша"""
        from datetime import datetime
        return datetime.now() > self.expires_at

    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'data_type': self.data_type,
            'calculation_data': self.calculation_data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired()
        }


# Создание индексов для оптимизации производительности
Index('idx_users_telegram_id', User.telegram_id)
Index('idx_users_birth_date', User.birth_date)
Index('idx_users_profession', User.profession)
Index('idx_users_gender', User.gender)
Index('idx_users_created_at', User.created_at)

Index('idx_astro_profile_telegram_id', UserAstroProfile.telegram_id)

Index('idx_daily_calc_telegram_id', DailyCalculations.telegram_id)
Index('idx_daily_calc_target_date', DailyCalculations.target_date)
Index('idx_daily_calc_composite', DailyCalculations.telegram_id, DailyCalculations.target_date)
Index('idx_daily_calc_hash', DailyCalculations.data_hash)
Index('idx_daily_calc_timestamp', DailyCalculations.calculation_timestamp)

Index('idx_biorhythms_telegram_id', Biorhythms.telegram_id)
Index('idx_biorhythms_calculation_date', Biorhythms.calculation_date)
Index('idx_biorhythms_composite', Biorhythms.telegram_id, Biorhythms.calculation_date)

Index('idx_cache_telegram_date', CalculationCache.telegram_id, CalculationCache.target_date)
Index('idx_cache_expires', CalculationCache.expires_at)
Index('idx_cache_type', CalculationCache.data_type)
Index('idx_cache_composite', CalculationCache.telegram_id, CalculationCache.target_date, CalculationCache.data_type)


async def get_db():
    """
    Dependency для получения сессии БД
    Используется в FastAPI endpoints
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Ошибка в сессии БД: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Инициализация базы данных
    Создание таблиц при первом запуске
    """
    try:
        async with async_engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False


async def check_db_connection():
    """
    Проверка подключения к базе данных
    """
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
        logger.info("✅ Подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False


async def get_database_stats():
    """
    Получение статистики базы данных
    """
    try:
        async with async_session() as session:
            # Статистика пользователей
            users_count = await session.execute("SELECT COUNT(*) FROM users")
            users_count = users_count.scalar()

            # Статистика астропрофилей
            profiles_count = await session.execute("SELECT COUNT(*) FROM user_astro_profile")
            profiles_count = profiles_count.scalar()

            # Статистика daily calculations
            calc_count = await session.execute("SELECT COUNT(*) FROM daily_calculations")
            calc_count = calc_count.scalar()

            # Статистика биоритмов
            bio_count = await session.execute("SELECT COUNT(*) FROM biorhythms")
            bio_count = bio_count.scalar()

            # Размер базы данных
            db_size = await session.execute("SELECT pg_size_pretty(pg_database_size('astra_db'))")
            db_size = db_size.scalar()

            return {
                'users_count': users_count,
                'profiles_count': profiles_count,
                'daily_calculations_count': calc_count,
                'biorhythms_count': bio_count,
                'database_size': db_size,
                'timestamp': func.now()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        return {}


async def cleanup_expired_cache():
    """
    Очистка просроченного кэша
    """
    try:
        from datetime import datetime

        async with async_session() as session:
            result = await session.execute(
                CalculationCache.__table__.delete().where(
                    CalculationCache.expires_at < datetime.now()
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} просроченных записей кэша")
            else:
                logger.debug("✅ Просроченных записей кэша не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка очистки кэша: {e}")
        return 0


class DatabaseManager:
    """
    Менеджер для работы с базой данных
    Предоставляет высокоуровневые методы для часто используемых операций
    """

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = async_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()

    async def get_user_with_profile(self, telegram_id: int) -> dict:
        """Получение пользователя с астропрофилем"""
        try:
            user_result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return None

            profile_result = await self.session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            profile = profile_result.scalar_one_or_none()

            return {
                'user': user.to_dict() if user else None,
                'astro_profile': profile.to_dict() if profile else None
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя с профилем: {e}")
            return None

    async def get_user_calculations_for_period(self, telegram_id: int, start_date: date, end_date: date) -> list:
        """Получение расчетов пользователя за период"""
        try:
            result = await self.session.execute(
                select(DailyCalculations)
                .where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date >= start_date,
                        DailyCalculations.target_date <= end_date
                    )
                )
                .order_by(DailyCalculations.target_date)
            )
            calculations = result.scalars().all()

            return [calc.to_dict() for calc in calculations]

        except Exception as e:
            logger.error(f"❌ Ошибка получения расчетов за период: {e}")
            return []

    async def increment_user_request_count(self, telegram_id: int) -> bool:
        """Увеличение счетчика запросов пользователя"""
        try:
            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.request_count = (user.request_count or 0) + 1
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка увеличения счетчика запросов: {e}")
            return False


# Глобальный экземпляр для быстрого доступа
db_manager = DatabaseManager()



