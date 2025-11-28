import logging
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
import asyncio
from datetime import datetime
import os
from contextlib import asynccontextmanager

# ✅ КРИТИЧЕСКИЕ ИМПОРТЫ ДЛЯ ASTRA
from backend.database import async_session, UserAstroProfile
from backend.natal_chart import MLNatalChartCalculator
from backend.psyho_matrix import PsyhoMatrixCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


class MagicProfileIntegration:
    def __init__(self):
        self.base_url = os.getenv("MAGIC_PROFILE_URL", "http://magic_profile:8001")
        self.timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        self.max_retries = int(os.getenv("MAGIC_PROFILE_MAX_RETRIES", "3"))
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        self._last_health_check: Optional[float] = None
        self._is_healthy: bool = True

    async def ensure_client(self) -> httpx.AsyncClient:
        """Создает или возвращает существующий клиент с health check"""
        async with self._client_lock:
            if self._client is None:
                self._client = httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=httpx.Limits(
                        max_keepalive_connections=5,
                        max_connections=10,
                        keepalive_expiry=30.0
                    ),
                    headers={
                        "User-Agent": "Astra-Service/1.0",
                        "Accept-Encoding": "gzip, deflate"
                    }
                )

                await self._perform_health_check()

            return self._client

    async def _perform_health_check(self) -> bool:
        """Внутренний health check с кэшированием"""
        current_time = asyncio.get_event_loop().time()

        if (self._last_health_check and
                current_time - self._last_health_check < 30 and
                not self._is_healthy):
            return False

        try:
            async with self.get_client() as client:
                resp = await client.get(
                    f"{self.base_url}/health",
                    timeout=httpx.Timeout(5.0)
                )
                self._is_healthy = resp.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            self._is_healthy = False

        self._last_health_check = current_time
        return self._is_healthy

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Корректный context manager для клиента"""
        client = await self.ensure_client()
        try:
            yield client
        except Exception:
            raise

    async def send_profile_data_to_magic(self, telegram_id: int, astra_data: Dict[str, Any]) -> bool:
        """Отправка данных с предварительной проверкой здоровья"""

        if not self._is_healthy and not await self._perform_health_check():
            logger.debug(f"Magic Profile недоступен, пропускаем {telegram_id}")
            return False

        if not self._validate_astra_data(astra_data):
            logger.warning(f"⚠️ Невалидные данные для {telegram_id}, пропускаем отправку")
            return False

        payload = self._prepare_magic_profile_payload(telegram_id, astra_data)

        for attempt in range(self.max_retries):
            try:
                async with self.get_client() as client:
                    resp = await client.post(
                        f"{self.base_url}/api/v1/profiles/{telegram_id}/create",
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-Request-ID": f"astra_{telegram_id}_{datetime.now().timestamp()}"
                        }
                    )

                if resp.status_code in [200, 201]:
                    logger.info(f"✅ Magic Profile создан для {telegram_id}")
                    self._is_healthy = True
                    return True
                elif resp.status_code == 409:
                    logger.info(f"ℹ️ Профиль {telegram_id} уже существует в Magic Profile")
                    self._is_healthy = True
                    return True
                elif resp.status_code in [400, 422]:
                    logger.error(f"❌ Невалидные данные для {telegram_id}: {resp.text}")
                    return False
                else:
                    logger.warning(f"⚠️ Попытка {attempt + 1}: {resp.status_code} для {telegram_id}")
                    if resp.status_code >= 500:
                        self._is_healthy = False

            except (httpx.ConnectTimeout, httpx.ConnectError) as e:
                self._is_healthy = False

                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Magic Profile недоступен для {telegram_id}: {e}")
                    return False
                backoff_delay = min(2 ** attempt, 10)
                logger.info(f"⏳ Retry {attempt + 1} через {backoff_delay}с для {telegram_id}")
                await asyncio.sleep(backoff_delay)

            except httpx.ReadTimeout as e:
                logger.warning(f"⏰ Timeout при отправке {telegram_id}: {e}")
                if attempt == self.max_retries - 1:
                    return False

            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка для {telegram_id}: {e}")
                return False

        return False

    def _validate_astra_data(self, astra_data: Dict[str, Any]) -> bool:
        """Быстрая валидация минимально необходимых данных"""
        try:
            natal = astra_data.get('natal_chart', {})
            if not natal.get('planets'):
                return False

            user_profile = astra_data.get('user_profile', {})
            if not user_profile.get('birth_date'):
                return False

            return True

        except Exception:
            return False

    def _prepare_magic_profile_payload(self, telegram_id: int, astra_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка payload с умной оптимизацией"""
        natal_data = astra_data.get('natal_chart', {})
        matrix_data = astra_data.get('psyho_matrix', {})
        user_data = astra_data.get('user_profile', {})

        aspects = natal_data.get('aspects', [])
        filtered_aspects = [
            a for a in aspects
            if a.get('strength', 0) > 0.5
        ][:15]

        optimized_natal = {
            'planets': natal_data.get('planets', {}),
            'houses': natal_data.get('houses', {}),
            'angles': natal_data.get('angles', {}),
            'aspects': filtered_aspects,
            'ml_features': {
                'element_balance': natal_data.get('ml_features', {}).get('element_balance', {}),
                'planet_strengths': natal_data.get('ml_features', {}).get('planet_strengths', {}),
                'house_emphasis': natal_data.get('ml_features', {}).get('house_emphasis', {})
            }
        }

        optimized_matrix = {
            'basic_numbers': matrix_data.get('basic_numbers', {}),
            'energy_centers': matrix_data.get('energy_centers', {}),
            'pythagoras_matrix': matrix_data.get('pythagoras_matrix', {})
        }

        return {
            'telegram_id': telegram_id,
            'source': 'astra',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'data': {
                'natal': optimized_natal,
                'psychomatrix': optimized_matrix,
                'user_context': {
                    'birth_date': user_data.get('birth_date'),
                    'birth_time': user_data.get('birth_time'),
                    'birth_city': user_data.get('birth_city'),
                    'gender': user_data.get('gender'),
                    'profession': user_data.get('profession')
                }
            }
        }

    async def health_check(self) -> bool:
        """Публичный health check"""
        return await self._perform_health_check()

    async def close(self):
        """Явное закрытие клиента"""
        async with self._client_lock:
            if self._client:
                await self._client.aclose()
                self._client = None
                self._is_healthy = False


class MagicIntegrationManager:
    def __init__(self):
        self._integration: Optional[MagicProfileIntegration] = None
        self._lock = asyncio.Lock()

    async def get_integration(self) -> MagicProfileIntegration:
        """Потокобезопасное получение экземпляра"""
        async with self._lock:
            if self._integration is None:
                self._integration = MagicProfileIntegration()
            return self._integration

    async def close(self):
        """Закрытие интеграции"""
        async with self._lock:
            if self._integration:
                await self._integration.close()
                self._integration = None


_magic_manager = MagicIntegrationManager()


async def get_magic_integration() -> MagicProfileIntegration:
    return await _magic_manager.get_integration()


async def close_magic_integration():
    await _magic_manager.close()


async def magic_health_check_daemon():
    """Фоновая задача для поддержания актуального статуса здоровья"""
    while True:
        try:
            integration = await get_magic_integration()
            await integration.health_check()
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Health check daemon error: {e}")
            await asyncio.sleep(30)