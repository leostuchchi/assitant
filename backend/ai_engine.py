import aiohttp
import asyncio
import logging
import os
from typing import Dict, Any
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class AIPredictionEngine:
    """
    Оптимизированный движок для работы с Ollama API с одной моделью (gemma:2b)
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('OLLAMA_URL', 'http://localhost:11435')

        # Фиксированная модель - gemma:2b
        self.model = "gemma:2b"

        # Оптимизированные таймауты
        self.timeout = aiohttp.ClientTimeout(total=180)  # 120 секунд
        self.max_retries = 2
        self.retry_delay = 2

        # Статистика использования
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "current_model": self.model
        }

        logger.info(f"🤖 AI движок инициализирован: {self.base_url}, модель: {self.model}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Быстрая проверка подключения и доступности модели
        """
        test_result = {
            "ollama_available": False,
            "model_loaded": False,
            "test_passed": False,
            "response_time": None,
            "error": None,
            "details": {  # ✅ ДОБАВЛЯЕМ КЛЮЧ details
                "available_models": [],
                "test_response": None
            }
        }

        try:
            # Проверяем доступность Ollama
            test_result["ollama_available"] = await self.check_health()

            if test_result["ollama_available"]:
                # Проверяем наличие конкретной модели
                available_models = await self.get_available_models()
                test_result["model_loaded"] = self.model in available_models
                test_result["details"]["available_models"] = available_models  # ✅ ЗАПОЛНЯЕМ

                # Быстрый тестовый запрос
                if test_result["model_loaded"]:
                    start_time = time.time()
                    test_data = {
                        "user_context": {"profession": "тест"},
                        "energy_state": {"overall_energy": {"percentage": 75}}
                    }

                    test_response = await self.generate_recommendations(test_data)
                    test_result["test_passed"] = test_response["success"]
                    test_result["response_time"] = test_response.get("response_time_seconds")
                    test_result["details"]["test_response"] = test_response  # ✅ ЗАПОЛНЯЕМ

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Ошибка тестирования подключения: {e}")

        return test_result

    async def get_available_models(self) -> list:
        """Получение списка доступных моделей"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
                    return []
        except Exception as e:
            logger.debug(f"Не удалось получить список моделей: {e}")
            return []

    async def check_health(self) -> bool:
        """Проверка доступности Ollama сервиса"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        return True
        except Exception:
            pass
        return False

    async def generate_recommendations(self, prepared_data: Dict) -> Dict[str, Any]:
        """
        Основной метод генерации рекомендаций
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Проверяем доступность сервиса
        if not await self.check_health():
            return self._get_fallback_response(prepared_data, "Сервис AI недоступен")

        try:
            # Формируем промпт и выполняем запрос
            prompt = self._build_prompt(prepared_data)
            response_text = await self._make_ollama_request(prompt)
            recommendations = self._parse_response(response_text)

            # Обновляем статистику
            response_time = time.time() - start_time
            self.stats["successful_requests"] += 1

            # Обновляем среднее время ответа
            prev_avg = self.stats["average_response_time"]
            prev_count = self.stats["successful_requests"] - 1
            self.stats["average_response_time"] = (prev_avg * prev_count + response_time) / self.stats[
                "successful_requests"]

            logger.info(f"✅ Рекомендации сгенерированы за {response_time:.2f}с")

            return {
                "success": True,
                "recommendations": recommendations,
                "response_text": response_text,
                "model_used": self.model,
                "response_time_seconds": round(response_time, 2),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"❌ Ошибка генерации рекомендаций: {e}")
            return self._get_fallback_response(prepared_data, str(e))

    async def _make_ollama_request(self, prompt: str) -> str:
        """Оптимизированный запрос к Ollama API"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    # Оптимальные настройки для gemma:2b
                    options = {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 250,  # Оптимальная длина ответа
                        "num_thread": 2,  # 2 потока для баланса производительности
                        "repeat_penalty": 1.1,
                        "top_k": 40
                    }

                    request_data = {
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": options
                    }

                    logger.info(f"🔄 Запрос к {self.model} (попытка {attempt + 1}/{self.max_retries})")

                    async with session.post(f"{self.base_url}/api/generate", json=request_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "").strip()

                            # Логируем производительность
                            if "eval_duration" in result:
                                eval_time = result["eval_duration"] / 1_000_000_000
                                logger.debug(f"⏱️ Время генерации модели: {eval_time:.2f}с")

                            return response_text
                        else:
                            error_text = await response.text()
                            raise Exception(f"Ollama API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                last_exception = Exception(f"Таймаут запроса (попытка {attempt + 1})")
                logger.warning(f"⏰ Таймаут запроса, попытка {attempt + 1}")

            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Ошибка запроса (попытка {attempt + 1}): {e}")

            # Задержка перед повторной попыткой
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise last_exception or Exception("Не удалось выполнить запрос к AI")

    def _build_prompt(self, data: Dict) -> str:
        """Построение оптимального промпта для рекомендаций"""
        user_context = data.get("user_context", {})
        energy_state = data.get("energy_state", {})
        astro_highlights = data.get("astro_highlights", {})

        prompt = f"""На основе индивидуальных данных предоставь краткие практические рекомендации на день.

ПРОФИЛЬ:
• Профессия: {user_context.get('profession', 'не указана')}
• Должность: {user_context.get('position', 'не указана')}

СОСТОЯНИЕ:
• Общая энергия: {energy_state.get('overall_energy', {}).get('percentage', 0)}%
• Физический цикл: {energy_state.get('physical_cycle', {}).get('phase', 'нейтральный')}
• Эмоциональный цикл: {energy_state.get('emotional_cycle', {}).get('phase', 'нейтральный')}

СФОРМУЛИРУЙ КРАТКИЕ РЕКОМЕНДАЦИИ:
1. 💼 Профессиональная деятельность
2. 🏃 Личная эффективность  
3. ❤️ Эмоциональное состояние

ОТВЕТ:"""

        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Упрощенный парсинг ответа модели"""
        try:
            # Базовая структура для категорий
            categories = {
                "professional": [],
                "personal_effectiveness": [],
                "emotional": [],
                "daily_focus": []
            }

            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            current_category = None

            for line in lines:
                # Определяем категорию по маркерам
                if any(marker in line for marker in ['💼', 'работа', 'професси']):
                    current_category = "professional"
                elif any(marker in line for marker in ['🏃', 'личн', 'эффектив']):
                    current_category = "personal_effectiveness"
                elif any(marker in line for marker in ['❤️', 'эмоц', 'настроен']):
                    current_category = "emotional"
                elif any(marker in line for marker in ['🎯', 'акцент', 'фокус']):
                    current_category = "daily_focus"

                # Добавляем пункты в текущую категорию
                elif current_category and line.startswith(('•', '-', '—', '1.', '2.', '3.')):
                    clean_line = line.lstrip('•-—123456789. ').strip()
                    if clean_line and len(clean_line) > 5:  # Минимальная длина
                        categories[current_category].append(clean_line)

            # Если не удалось выделить структурированные данные, возвращаем как есть
            if not any(categories.values()):
                return {"raw_recommendations": response_text}

            return categories

        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга ответа: {e}")
            return {"raw_recommendations": response_text}

    def _get_fallback_response(self, data: Dict, error: str) -> Dict[str, Any]:
        """Резервный ответ при недоступности AI"""
        return {
            "success": False,
            "error": error,
            "is_fallback": True,
            "recommendations": self._get_fallback_recommendations(data),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model
        }

    def _get_fallback_recommendations(self, data: Dict) -> Dict[str, Any]:
        """Умные резервные рекомендации на основе данных"""
        energy_state = data.get("energy_state", {})
        overall_energy = energy_state.get("overall_energy", {}).get("percentage", 50)
        user_context = data.get("user_context", {})

        # Персонализированные рекомендации на основе энергии
        if overall_energy > 75:
            energy_advice = "Идеальный день для сложных задач и важных решений."
            professional_tip = "Беритесь за амбициозные проекты"
        elif overall_energy > 50:
            energy_advice = "Хороший уровень энергии для продуктивной работы."
            professional_tip = "Сфокусируйтесь на текущих задачах"
        elif overall_energy > 25:
            energy_advice = "Энергии достаточно для рутинных задач."
            professional_tip = "Планируйте работу небольшими блоками"
        else:
            energy_advice = "Рекомендуется беречь силы и делать перерывы."
            professional_tip = "Отложите сложные задачи на другой день"

        # Учитываем профессию пользователя
        profession = user_context.get('profession', '').lower()
        if any(word in profession for word in ['разработ', 'программ', 'техн']):
            professional_tip += ", уделите время техническим задачам"
        elif any(word in profession for word in ['управл', 'менедж', 'руковод']):
            professional_tip += ", проведите планерки и встречи"

        return {
            "professional": [
                professional_tip,
                "Расставьте приоритеты в задачах"
            ],
            "personal_effectiveness": [
                energy_advice,
                "Соблюдайте баланс работы и отдыха",
                "Делайте регулярные перерывы"
            ],
            "emotional": [
                "Сохраняйте эмоциональное равновесие",
                "Избегайте импульсивных решений"
            ],
            "daily_focus": [
                "Баланс между продуктивностью и восстановлением"
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики использования"""
        return self.stats.copy()


# Глобальный экземпляр движка
ai_engine = AIPredictionEngine()