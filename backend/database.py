import os
from datetime import date, datetime, timedelta
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
    ОПТИМИЗИРОВАНА: Добавлены поля для ML контекста
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

    # НОВЫЕ ПОЛЯ ДЛЯ ML КОНТЕКСТА
    user_segment = Column(String(50), nullable=True)  # 'beginner', 'active', 'premium'
    activity_level = Column(String(20), nullable=True)  # 'low', 'medium', 'high'
    data_quality_score = Column(Integer, default=0)  # 0-100 баллов качества данных

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, birth_date={self.birth_date})>"

    def to_dict(self):
        """Конвертация в словарь для API с ML контекстом"""
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
            # Новые ML поля
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
            if self.birth_city:
                score += 10

            # Проверка дополнительных полей (30 баллов)
            if self.profession and self.profession != 'не указана':
                score += 15
            if self.current_city:
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
    ОБНОВЛЕНА: Добавлены ML-ориентированные поля
    """
    __tablename__ = 'user_astro_profile'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    natal_chart_data = Column(JSON, nullable=False)
    psyho_matrix_data = Column(JSON, nullable=False)
    dominant_energy = Column(String(50), nullable=True)
    personality_traits = Column(JSON, nullable=True)

    # НОВЫЕ ПОЛЯ ДЛЯ ML АНАЛИТИКИ
    ml_features = Column(JSON, nullable=True)  # Статические ML фичи пользователя
    behavior_patterns = Column(JSON, nullable=True)  # Паттерны поведения
    compatibility_profile = Column(JSON, nullable=True)  # Профиль совместимости

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserAstroProfile(telegram_id={self.telegram_id})>"

    def to_dict(self):
        """Конвертация в словарь для API с ML данными"""
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

    def _get_chart_complexity(self):
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

    def _get_matrix_energy_level(self):
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

    def update_ml_features(self, ml_data: dict):
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
    ОПТИМИЗИРОВАНА: Добавлены колонки для ML данных и аналитики
    """
    __tablename__ = 'daily_calculations'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    biorhythm_data = Column(JSON, nullable=False)
    astro_transits_data = Column(JSON, nullable=False)
    calculation_metadata = Column(JSON, nullable=False, default={})

    # НОВЫЕ КОЛОНКИ ДЛЯ ML ДАННЫХ
    ml_features = Column(JSON, nullable=True)  # ML фичи дня
    basic_insights = Column(JSON, nullable=True)  # Базовые инсайты
    trend_data = Column(JSON, nullable=True)  # Данные трендов
    risk_factors = Column(JSON, nullable=True)  # Факторы риска
    opportunities = Column(JSON, nullable=True)  # Возможности дня

    # ТЕХНИЧЕСКИЕ ПОЛЯ
    data_hash = Column(String(64), nullable=False)
    calculation_timestamp = Column(TIMESTAMP, server_default=func.now())

    # ИНДЕКСЫ ДЛЯ ML АНАЛИТИКИ
    ml_data_quality = Column(Integer, default=0)  # Качество ML данных (0-100)

    def __repr__(self):
        return f"<DailyCalculations(telegram_id={self.telegram_id}, date={self.target_date})>"

    def to_dict(self):
        """Конвертация в словарь для API с полными ML данными"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'astro_transits_data': self.astro_transits_data,
            'calculation_metadata': self.calculation_metadata,

            # ML данные
            'ml_features': self.ml_features or {},
            'basic_insights': self.basic_insights or [],
            'trend_data': self.trend_data or {},
            'risk_factors': self.risk_factors or [],
            'opportunities': self.opportunities or [],

            # Техническая информация
            'data_hash': self.data_hash,
            'calculation_timestamp': self.calculation_timestamp.isoformat() if self.calculation_timestamp else None,
            'ml_data_quality': self.ml_data_quality,
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

    def update_ml_data(self, ml_package: dict):
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
    ОБНОВЛЕН: Поддержка ML-кэширования
    """
    __tablename__ = 'calculation_cache'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    data_type = Column(String(20), primary_key=True)  # 'biorhythm', 'transits', 'combined', 'ml_data'
    calculation_data = Column(JSON, nullable=False)

    # НОВЫЕ ПОЛЯ ДЛЯ ML КЭША
    ml_specific = Column(JSON, nullable=True)  # ML-специфичные данные
    cache_priority = Column(Integer, default=1)  # Приоритет кэша (1-10)

    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<CalculationCache(telegram_id={self.telegram_id}, date={self.target_date}, type={self.data_type})>"

    def is_expired(self):
        """Проверка истечения срока действия кэша"""
        from datetime import datetime
        return datetime.now() > self.expires_at

    def to_dict(self):
        """Конвертация в словарь с ML контекстом"""
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


class MLModels(Base):
    """
    НОВАЯ ТАБЛИЦА: Метаданные ML моделей и их версии
    Для управления жизненным циклом ML моделей
    """
    __tablename__ = 'ml_models'

    model_id = Column(String(50), primary_key=True)  # 'feature_engineering', 'trend_analyzer' и т.д.
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(30), nullable=False)  # 'feature_engineering', 'classification', 'clustering'
    model_metadata = Column(JSON, nullable=False)

    # Производительность модели
    accuracy_score = Column(Integer, nullable=True)  # 0-100
    training_date = Column(Date, nullable=False)
    is_active = Column(Integer, default=1)  # 1 - активна, 0 - неактивна

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MLModels(model_id={self.model_id}, version={self.model_version})>"

    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'model_id': self.model_id,
            'model_version': self.model_version,
            'model_type': self.model_type,
            'model_metadata': self.model_metadata,
            'accuracy_score': self.accuracy_score,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Создание индексов для оптимизации производительности
Index('idx_users_telegram_id', User.telegram_id)
Index('idx_users_birth_date', User.birth_date)
Index('idx_users_profession', User.profession)
Index('idx_users_gender', User.gender)
Index('idx_users_created_at', User.created_at)
Index('idx_users_activity', User.activity_level)  # НОВЫЙ ИНДЕКС
Index('idx_users_data_quality', User.data_quality_score)  # НОВЫЙ ИНДЕКС

Index('idx_astro_profile_telegram_id', UserAstroProfile.telegram_id)
Index('idx_astro_profile_ml', UserAstroProfile.ml_features)  # НОВЫЙ ИНДЕКС

Index('idx_daily_calc_telegram_id', DailyCalculations.telegram_id)
Index('idx_daily_calc_target_date', DailyCalculations.target_date)
Index('idx_daily_calc_composite', DailyCalculations.telegram_id, DailyCalculations.target_date)
Index('idx_daily_calc_hash', DailyCalculations.data_hash)
Index('idx_daily_calc_timestamp', DailyCalculations.calculation_timestamp)
Index('idx_daily_calc_ml_quality', DailyCalculations.ml_data_quality)  # НОВЫЙ ИНДЕКС
Index('idx_daily_calc_has_ml', DailyCalculations.ml_features)  # НОВЫЙ ИНДЕКС

Index('idx_biorhythms_telegram_id', Biorhythms.telegram_id)
Index('idx_biorhythms_calculation_date', Biorhythms.calculation_date)
Index('idx_biorhythms_composite', Biorhythms.telegram_id, Biorhythms.calculation_date)

Index('idx_cache_telegram_date', CalculationCache.telegram_id, CalculationCache.target_date)
Index('idx_cache_expires', CalculationCache.expires_at)
Index('idx_cache_type', CalculationCache.data_type)
Index('idx_cache_composite', CalculationCache.telegram_id, CalculationCache.target_date, CalculationCache.data_type)
Index('idx_cache_priority', CalculationCache.cache_priority)  # НОВЫЙ ИНДЕКС

Index('idx_ml_models_active', MLModels.is_active)  # НОВЫЙ ИНДЕКС
Index('idx_ml_models_type', MLModels.model_type)  # НОВЫЙ ИНДЕКС


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
    Получение статистики базы данных с ML метриками
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

            # НОВАЯ СТАТИСТИКА: ML данные
            ml_data_count = await session.execute(
                "SELECT COUNT(*) FROM daily_calculations WHERE ml_features IS NOT NULL"
            )
            ml_data_count = ml_data_count.scalar()

            # Статистика биоритмов
            bio_count = await session.execute("SELECT COUNT(*) FROM biorhythms")
            bio_count = bio_count.scalar()

            # Статистика ML моделей
            ml_models_count = await session.execute("SELECT COUNT(*) FROM ml_models WHERE is_active = 1")
            ml_models_count = ml_models_count.scalar()

            # Размер базы данных
            db_size = await session.execute("SELECT pg_size_pretty(pg_database_size('astra_db'))")
            db_size = db_size.scalar()

            # Среднее качество ML данных
            avg_ml_quality = await session.execute(
                "SELECT AVG(ml_data_quality) FROM daily_calculations WHERE ml_data_quality > 0"
            )
            avg_ml_quality = round(avg_ml_quality.scalar() or 0, 1)

            return {
                'users_count': users_count,
                'profiles_count': profiles_count,
                'daily_calculations_count': calc_count,
                'biorhythms_count': bio_count,
                'ml_models_count': ml_models_count,
                'ml_data_coverage': f"{(ml_data_count / calc_count * 100) if calc_count > 0 else 0:.1f}%",
                'average_ml_quality': avg_ml_quality,
                'database_size': db_size,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        return {}


async def cleanup_expired_cache():
    """
    Очистка просроченного кэша с приоритетом ML данных
    """
    try:
        from datetime import datetime

        async with async_session() as session:
            # Сначала удаляем обычный кэш
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


async def optimize_ml_data_storage():
    """
    Оптимизация хранения ML данных
    """
    try:
        async with async_session() as session:
            # Очистка устаревших ML данных (старше 90 дней)
            cutoff_date = date.today() - timedelta(days=90)

            result = await session.execute(
                DailyCalculations.__table__.update()
                .where(DailyCalculations.target_date < cutoff_date)
                .values(
                    ml_features=None,
                    basic_insights=None,
                    trend_data=None,
                    risk_factors=None,
                    opportunities=None
                )
            )
            optimized_count = result.rowcount

            await session.commit()

            if optimized_count > 0:
                logger.info(f"🔄 Оптимизировано {optimized_count} записей ML данных (старше 90 дней)")
            else:
                logger.info("✅ Оптимизация ML данных не требуется")

            return optimized_count

    except Exception as e:
        logger.error(f"❌ Ошибка оптимизации ML данных: {e}")
        return 0


class DatabaseManager:
    """
    Менеджер для работы с базой данных
    ОБНОВЛЕН: Поддержка ML операций
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
        """Получение пользователя с астропрофилем и ML контекстом"""
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
                'astro_profile': profile.to_dict() if profile else None,
                'ml_context': {
                    'has_ml_profile': bool(profile and profile.ml_features),
                    'data_quality': user.data_quality_score if user else 0
                }
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя с профилем: {e}")
            return None

    async def get_user_calculations_for_period(self, telegram_id: int, start_date: date, end_date: date) -> list:
        """Получение расчетов пользователя за период с ML данными"""
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

    async def get_ml_enhanced_calculations(self, telegram_id: int, days: int = 7) -> list:
        """Получение расчетов с ML данными за указанный период"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            result = await self.session.execute(
                select(DailyCalculations)
                .where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date >= start_date,
                        DailyCalculations.target_date <= end_date,
                        DailyCalculations.ml_features.isnot(None)  # Только с ML данными
                    )
                )
                .order_by(DailyCalculations.target_date.desc())
            )
            calculations = result.scalars().all()

            return [calc.to_dict() for calc in calculations]

        except Exception as e:
            logger.error(f"❌ Ошибка получения ML-расчетов: {e}")
            return []

    async def increment_user_request_count(self, telegram_id: int) -> bool:
        """Увеличение счетчика запросов пользователя с обновлением сегмента"""
        try:
            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.request_count = (user.request_count or 0) + 1

                # Автоматическое обновление сегмента пользователя
                if user.request_count >= 50:
                    user.user_segment = 'premium'
                elif user.request_count >= 20:
                    user.user_segment = 'active'
                else:
                    user.user_segment = 'beginner'

                # Обновление качества данных
                user.data_quality_score = user.calculate_data_quality()

                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка увеличения счетчика запросов: {e}")
            return False

    async def update_user_ml_context(self, telegram_id: int, ml_context: dict) -> bool:
        """Обновление ML контекста пользователя"""
        try:
            result = await self.session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            profile = result.scalar_one_or_none()

            if profile:
                profile.ml_features = ml_context.get('ml_features', profile.ml_features)
                profile.behavior_patterns = ml_context.get('behavior_patterns', profile.behavior_patterns)
                profile.compatibility_profile = ml_context.get('compatibility_profile', profile.compatibility_profile)
                profile.updated_at = datetime.now()
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка обновления ML контекста: {e}")
            return False


# Глобальный экземпляр для быстрого доступа
db_manager = DatabaseManager()
