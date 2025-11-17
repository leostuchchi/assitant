import logging
import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional

from backend.database import async_session, AIRecommendations
from sqlalchemy.future import select
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Упрощенный сервис для управления рекомендациями и кэшем
    Объединяет логику кэширования и работы с рекомендациями
    """

    def __init__(self):
        self.cache_ttl_days = 1  # Кэшируем на 1 день

    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Генерация хэша данных для кэширования"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()

    async def get_cached_recommendations(self, telegram_id: int, target_date: date, data_hash: str) -> Optional[
        Dict[str, Any]]:
        """Получение закэшированных рекомендаций"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(AIRecommendations).where(
                        and_(
                            AIRecommendations.telegram_id == telegram_id,
                            AIRecommendations.target_date == target_date,
                            AIRecommendations.data_hash == data_hash
                        )
                    )
                )
                cached = result.scalar_one_or_none()

                if cached:
                    logger.info(f"✅ Найдены кэшированные рекомендации для {telegram_id} на {target_date}")
                    return {
                        'recommendations': cached.recommendations,
                        'model_version': cached.model_version,
                        'from_cache': True
                    }

                return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения кэша для {telegram_id}: {e}")
            return None

    async def save_recommendations(self, telegram_id: int, target_date: date, data_hash: str,
                                   recommendations: str, model_version: str = 'gemma:2b') -> bool:
        """Сохранение рекомендаций в кэш"""
        try:
            async with async_session() as session:
                # Удаляем старые записи для этой даты
                await session.execute(
                    AIRecommendations.__table__.delete().where(
                        and_(
                            AIRecommendations.telegram_id == telegram_id,
                            AIRecommendations.target_date == target_date
                        )
                    )
                )

                # Сохраняем новые рекомендации
                new_recommendation = AIRecommendations(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    data_hash=data_hash,
                    recommendations=recommendations,
                    model_version=model_version,
                    created_at=datetime.now()
                )

                session.add(new_recommendation)
                await session.commit()

                logger.info(f"💾 Рекомендации сохранены в кэш для {telegram_id} на {target_date}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения рекомендаций для {telegram_id}: {e}")
            return False

    async def cleanup_old_recommendations(self, days_old: int = 7) -> int:
        """Очистка устаревших рекомендаций"""
        try:
            cutoff_date = date.today() - timedelta(days=days_old)

            async with async_session() as session:
                result = await session.execute(
                    AIRecommendations.__table__.delete().where(
                        AIRecommendations.target_date < cutoff_date
                    )
                )
                deleted_count = result.rowcount
                await session.commit()

                if deleted_count > 0:
                    logger.info(f"🗑️ Удалено {deleted_count} устаревших рекомендаций")

                return deleted_count

        except Exception as e:
            logger.error(f"❌ Ошибка очистки рекомендаций: {e}")
            return 0


# Глобальный экземпляр
recommendation_service = RecommendationService()