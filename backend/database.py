# backend/database.py
"""
Полная реализация моделей базы данных для Astra с поддержкой Magic Profile
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import Column, BigInteger, String, Date, Time, JSON, Boolean, Integer, Float, Text
from sqlalchemy import ForeignKey, DateTime, func, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base: DeclarativeBase = declarative_base()

# Настройка подключения к базе данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://astra_user:astra_password_2024@localhost:5432/astra_db"
)

# Создание асинхронного движка
async_engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo_pool=False
)

# Создание асинхронной сессии
async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True
)


class User(Base):
    """
    Основная таблица пользователей проекта Astra
    """
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, index=True, comment="ID пользователя в Telegram")
    birth_date = Column(Date, nullable=False, comment="Дата рождения")
    birth_time = Column(Time, nullable=False, comment="Время рождения")
    birth_city = Column(String(100), nullable=False, comment="Город рождения")

    # Профессиональная информация
    profession = Column(String(100), nullable=True, comment="Профессия")
    job_position = Column(String(100), nullable=True, comment="Должность")
    current_city = Column(String(100), nullable=True, comment="Текущий город проживания")

    # Демографическая информация
    gender = Column(String(10), nullable=True, comment="Пол: male/female/other")

    # Статистика использования
    request_count = Column(Integer, default=0, comment="Количество запросов пользователя")

    # ML и аналитические поля
    user_segment = Column(String(50), nullable=True, comment="Сегмент пользователя: beginner/active/premium")
    activity_level = Column(String(20), nullable=True, comment="Уровень активности: low/medium/high")
    data_quality_score = Column(Integer, default=0, comment="Оценка качества данных (0-100)")

    # Технические поля
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                        comment="Дата обновления")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, birth_date={self.birth_date})>"

    def to_dict(self) -> Dict[str, Any]:
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
            'user_segment': self.user_segment,
            'activity_level': self.activity_level,
            'data_quality_score': self.data_quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_data_quality(self) -> int:
        """Автоматический расчет качества данных пользователя"""
        try:
            score = 0
            max_score = 100

            # Проверка обязательных полей (40 баллов)
            if self.birth_date:
                score += 20
            if self.birth_time:
                score += 10
            if self.birth_city and self.birth_city.strip():
                score += 10

            # Проверка дополнительных полей (30 баллов)
            if self.profession and self.profession.lower() not in ['не указана', 'нет', '']:
                score += 15
            if self.current_city and self.current_city.strip():
                score += 10
            if self.gender:
                score += 5

            # Активность пользователя (30 баллов)
            if self.request_count > 50:
                score += 30
            elif self.request_count > 20:
                score += 20
            elif self.request_count > 5:
                score += 10

            return min(score, max_score)

        except Exception as e:
            logger.error(f"❌ Ошибка расчета качества данных для {self.telegram_id}: {e}")
            return 0


class UserAstroProfile(Base):
    """
    Статические астрологические данные пользователя
    Объединяет натальную карту и психоматрицу
    """
    __tablename__ = 'user_astro_profile'

    telegram_id = Column(
        BigInteger,
        ForeignKey('users.telegram_id', ondelete='CASCADE'),
        primary_key=True,
        index=True,
        comment="ID пользователя в Telegram"
    )

    # Основные астрологические данные
    natal_chart_data = Column(JSONB, nullable=False, comment="Данные натальной карты")
    psyho_matrix_data = Column(JSONB, nullable=False, comment="Данные психоматрицы")

    # Аналитические поля
    dominant_energy = Column(String(50), nullable=True, comment="Доминирующая энергия")
    personality_traits = Column(JSONB, nullable=True, comment="Личностные черты")

    # ML и аналитические поля
    ml_features = Column(JSONB, nullable=True, comment="Статические ML фичи пользователя")
    behavior_patterns = Column(JSONB, nullable=True, comment="Паттерны поведения")
    compatibility_profile = Column(JSONB, nullable=True, comment="Профиль совместимости")

    # Технические поля
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
                        comment="Дата обновления")

    def __repr__(self):
        return f"<UserAstroProfile(telegram_id={self.telegram_id})>"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'natal_chart_summary': {
                'planets_count': len(self.natal_chart_data.get('planets', {})),
                'dominant_element': self._get_dominant_element(),
                'ascendant': self.natal_chart_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно'),
                'chart_complexity': self._get_chart_complexity()
            },
            'psyho_matrix_summary': {
                'life_path_number': self.psyho_matrix_data.get('basic_numbers', {}).get('first'),
                'matrix_complexity': self._calculate_matrix_complexity(),
                'energy_level': self._get_matrix_energy_level()
            },
            'ml_context': {
                'has_ml_features': bool(self.ml_features),
                'behavior_patterns_count': len(self.behavior_patterns or {}),
                'compatibility_available': bool(self.compatibility_profile)
            },
            'dominant_energy': self.dominant_energy,
            'personality_traits': self.personality_traits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def _get_dominant_element(self) -> str:
        """Определение доминирующего элемента"""
        try:
            element_balance = self.natal_chart_data.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _get_chart_complexity(self) -> str:
        """Оценка сложности натальной карты"""
        try:
            aspects = self.natal_chart_data.get('aspects', [])
            strong_aspects = len([a for a in aspects if a.get('strength', 0) > 0.7])

            if len(aspects) >= 15 or strong_aspects >= 8:
                return "очень сложная"
            elif len(aspects) >= 8 or strong_aspects >= 5:
                return "сложная"
            elif len(aspects) >= 3:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"

    def _calculate_matrix_complexity(self) -> str:
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

    def _get_matrix_energy_level(self) -> str:
        """Оценка уровня энергии по психоматрице"""
        try:
            matrix_data = self.psyho_matrix_data.get('pythagoras_matrix', {})
            total_digits = sum(matrix_data.values())

            if total_digits >= 15:
                return "очень высокий"
            elif total_digits >= 10:
                return "высокий"
            elif total_digits >= 5:
                return "средний"
            else:
                return "низкий"
        except Exception:
            return "неизвестно"

    def update_ml_features(self, ml_data: Dict[str, Any]):
        """Обновление ML фич пользователя"""
        try:
            self.ml_features = ml_data
            self.updated_at = datetime.now()
            logger.info(f"✅ ML фичи обновлены для пользователя {self.telegram_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ML фич для {self.telegram_id}: {e}")


class DailyCalculations(Base):
    """
    Ежедневные расчеты для конкретных дат
    """
    __tablename__ = 'daily_calculations'

    telegram_id = Column(
        BigInteger,
        ForeignKey('users.telegram_id', ondelete='CASCADE'),
        primary_key=True,
        comment="ID пользователя в Telegram"
    )
    target_date = Column(Date, primary_key=True, comment="Дата расчета")

    # Основные расчетные данные
    biorhythm_data = Column(JSONB, nullable=False, comment="Данные биоритмов")
    astro_transits_data = Column(JSONB, nullable=False, comment="Астрологические транзиты")
    calculation_metadata = Column(JSONB, nullable=False, default={}, comment="Метаданные расчета")

    # ML данные и аналитика
    ml_features = Column(JSONB, nullable=True, comment="ML фичи дня")
    basic_insights = Column(JSONB, nullable=True, comment="Базовые инсайты")
    trend_data = Column(JSONB, nullable=True, comment="Данные трендов")
    risk_factors = Column(JSONB, nullable=True, comment="Факторы риска")
    opportunities = Column(JSONB, nullable=True, comment="Возможности дня")

    # Технические поля
    data_hash = Column(String(64), nullable=False, comment="Хэш данных для дедупликации")
    ml_data_quality = Column(Integer, default=0, comment="Качество ML данных (0-100)")
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), comment="Время расчета")

    def __repr__(self):
        return f"<DailyCalculations(telegram_id={self.telegram_id}, date={self.target_date})>"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'astro_transits_data': self.astro_transits_data,
            'calculation_metadata': self.calculation_metadata,
            'ml_features': self.ml_features or {},
            'basic_insights': self.basic_insights or [],
            'trend_data': self.trend_data or {},
            'risk_factors': self.risk_factors or [],
            'opportunities': self.opportunities or [],
            'data_hash': self.data_hash,
            'ml_data_quality': self.ml_data_quality,
            'calculation_timestamp': self.calculation_timestamp.isoformat() if self.calculation_timestamp else None,
            'has_ml_data': self._has_ml_data()
        }

    def _has_ml_data(self) -> bool:
        """Проверка наличия ML данных"""
        return bool(
            self.ml_features or
            self.basic_insights or
            self.trend_data
        )

    def calculate_ml_quality_score(self) -> int:
        """Автоматический расчет качества ML данных"""
        try:
            score = 0
            max_score = 100

            # Наличие ML фич (40 баллов)
            if self.ml_features:
                score += 30
                # Дополнительные баллы за полноту фич
                key_features = ['daily_score', 'energy_overall', 'productivity_index']
                present_features = sum(1 for feat in key_features if feat in self.ml_features)
                score += (present_features / len(key_features)) * 10

            # Наличие инсайтов (30 баллов)
            if self.basic_insights and len(self.basic_insights) >= 2:
                score += 20
                if len(self.basic_insights) >= 5:
                    score += 10

            # Наличие трендов (20 баллов)
            if self.trend_data:
                score += 20

            # Дополнительные данные (10 баллов)
            if self.risk_factors or self.opportunities:
                score += 10

            return min(score, max_score)

        except Exception as e:
            logger.error(f"❌ Ошибка расчета качества ML данных: {e}")
            return 0

    def update_ml_data(self, ml_package: Dict[str, Any]):
        """Обновление ML данных записи"""
        try:
            self.ml_features = ml_package.get('ml_features', {})
            self.basic_insights = ml_package.get('basic_insights', [])
            self.trend_data = ml_package.get('trend_data', {})
            self.risk_factors = ml_package.get('risk_factors', [])
            self.opportunities = ml_package.get('opportunities', [])
            self.ml_data_quality = self.calculate_ml_quality_score()
            self.calculation_timestamp = datetime.now()

            logger.info(f"✅ ML данные обновлены для {self.telegram_id} на {self.target_date}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления ML данных: {e}")


class CalculationCache(Base):
    """
    Кэш расчетов для оптимизации производительности
    """
    __tablename__ = 'calculation_cache'

    telegram_id = Column(
        BigInteger,
        ForeignKey('users.telegram_id', ondelete='CASCADE'),
        primary_key=True,
        comment="ID пользователя в Telegram"
    )
    target_date = Column(Date, primary_key=True, comment="Дата расчета")
    data_type = Column(String(20), primary_key=True, comment="Тип данных: biorhythm/transits/combined/ml_data")

    calculation_data = Column(JSONB, nullable=False, comment="Кэшированные данные расчета")

    # ML-специфичные поля
    ml_specific = Column(JSONB, nullable=True, comment="ML-специфичные данные")
    cache_priority = Column(Integer, default=1, comment="Приоритет кэша (1-10)")

    expires_at = Column(DateTime(timezone=True), nullable=False, comment="Время истечения кэша")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания")

    def __repr__(self):
        return f"<CalculationCache(telegram_id={self.telegram_id}, date={self.target_date}, type={self.data_type})>"

    def is_expired(self) -> bool:
        """Проверка истечения срока действия кэша"""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'data_type': self.data_type,
            'calculation_data': self.calculation_data,
            'ml_specific': self.ml_specific or {},
            'cache_priority': self.cache_priority,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired(),
            'is_ml_enhanced': bool(self.ml_specific)
        }


class IntegrationLog(Base):
    """
    Логи интеграции с внешними системами (Magic Profile и др.)
    """
    __tablename__ = 'integration_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID записи")
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), index=True,
                         comment="ID пользователя")

    # Информация об интеграции
    integration_type = Column(String(50), nullable=False, comment="Тип интеграции: magic_profile/assistant")
    action = Column(String(50), nullable=False, comment="Действие: create/update/delete/sync")
    status = Column(String(20), nullable=False, comment="Статус: success/error/pending")

    # Данные запроса и ответа
    request_data = Column(JSONB, nullable=True, comment="Данные запроса")
    response_data = Column(JSONB, nullable=True, comment="Данные ответа")
    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке")

    # Технические поля
    external_id = Column(String(100), nullable=True, comment="ID во внешней системе")
    retry_count = Column(Integer, default=0, comment="Количество повторных попыток")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Дата создания")

    def __repr__(self):
        return f"<IntegrationLog(telegram_id={self.telegram_id}, type={self.integration_type}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'integration_type': self.integration_type,
            'action': self.action,
            'status': self.status,
            'external_id': self.external_id,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_request_data': bool(self.request_data),
            'has_response_data': bool(self.response_data)
        }


# Индексы для оптимизации производительности
Index('idx_users_telegram_id', User.telegram_id)
Index('idx_users_birth_date', User.birth_date)
Index('idx_users_profession', User.profession)
Index('idx_users_gender', User.gender)
Index('idx_users_created_at', User.created_at)
Index('idx_users_activity', User.activity_level)
Index('idx_users_data_quality', User.data_quality_score)

Index('idx_astro_profile_telegram_id', UserAstroProfile.telegram_id)
Index('idx_astro_profile_ml', UserAstroProfile.ml_features, postgresql_using='gin')

Index('idx_daily_calc_telegram_id', DailyCalculations.telegram_id)
Index('idx_daily_calc_target_date', DailyCalculations.target_date)
Index('idx_daily_calc_composite', DailyCalculations.telegram_id, DailyCalculations.target_date)
Index('idx_daily_calc_hash', DailyCalculations.data_hash)
Index('idx_daily_calc_timestamp', DailyCalculations.calculation_timestamp)
Index('idx_daily_calc_ml_quality', DailyCalculations.ml_data_quality)
Index('idx_daily_calc_has_ml', DailyCalculations.ml_features, postgresql_using='gin')

Index('idx_cache_telegram_date', CalculationCache.telegram_id, CalculationCache.target_date)
Index('idx_cache_expires', CalculationCache.expires_at)
Index('idx_cache_type', CalculationCache.data_type)
Index('idx_cache_composite', CalculationCache.telegram_id, CalculationCache.target_date, CalculationCache.data_type)
Index('idx_cache_priority', CalculationCache.cache_priority)

Index('idx_integration_logs_telegram_id', IntegrationLog.telegram_id)
Index('idx_integration_logs_type', IntegrationLog.integration_type)
Index('idx_integration_logs_status', IntegrationLog.status)
Index('idx_integration_logs_created', IntegrationLog.created_at)


# Утилиты для работы с базой данных
async def get_db() -> AsyncSession:
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
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False


async def check_db_connection() -> bool:
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


async def get_database_stats() -> Dict[str, Any]:
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

            # Статистика интеграций
            integrations_count = await session.execute("SELECT COUNT(*) FROM integration_logs")
            integrations_count = integrations_count.scalar()

            # Размер базы данных
            db_size = await session.execute("SELECT pg_size_pretty(pg_database_size('astra_db'))")
            db_size = db_size.scalar()

            return {
                'users_count': users_count,
                'profiles_count': profiles_count,
                'daily_calculations_count': calc_count,
                'integrations_count': integrations_count,
                'database_size': db_size,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        return {}


async def log_integration_event(
        telegram_id: int,
        integration_type: str,
        action: str,
        status: str,
        request_data: Dict[str, Any] = None,
        response_data: Dict[str, Any] = None,
        error_message: str = None,
        external_id: str = None
):
    """
    Логирование события интеграции
    """
    try:
        async with async_session() as session:
            log_entry = IntegrationLog(
                telegram_id=telegram_id,
                integration_type=integration_type,
                action=action,
                status=status,
                request_data=request_data,
                response_data=response_data,
                error_message=error_message,
                external_id=external_id
            )
            session.add(log_entry)
            await session.commit()

            logger.info(f"📝 Записано событие интеграции для {telegram_id}: {integration_type}.{action} - {status}")

    except Exception as e:
        logger.error(f"❌ Ошибка логирования интеграции: {e}")


