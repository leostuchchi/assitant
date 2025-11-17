import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.ai_engine import AIPredictionEngine

logging.basicConfig(level=logging.INFO)


async def test_ai_engine():
    """Тестирование AI движка"""
    print("🧪 Тестирование AI движка...")

    # Используем локальный хост
    ai_engine = AIPredictionEngine(base_url="http://localhost:11435")

    # 1. Тестируем подключение
    print("1. Проверка подключения к Ollama...")
    test_result = await ai_engine.test_connection()
    print(f"   Ollama доступен: {test_result['ollama_available']}")
    print(f"   Модель загружена: {test_result['model_loaded']}")
    print(f"   Тест пройден: {test_result['test_passed']}")

    if test_result['ollama_available']:
        print(f"   Доступные модели: {test_result['details'].get('available_models', [])}")

    if test_result['test_passed']:
        # 2. Тестируем генерацию рекомендаций
        print("\n2. Тестирование генерации рекомендаций...")
        test_data = {
            "user_context": {
                "profession": "разработчик",
                "position": "team lead",
                "current_city": "Москва",
                "gender": "male",
                "age": 35
            },
            "energy_state": {
                "overall_energy": {"percentage": 72.5},
                "physical_cycle": {"phase": "пик энергии"},
                "emotional_cycle": {"phase": "низкая активность"},
                "intellectual_cycle": {"phase": "высокая активность"}
            },
            "astro_highlights": {
                "key_aspects": ["Солнце-Марс соединение", "Луна-Венера трин"],
                "retrograde_planets": ["Меркурий"]
            }
        }

        result = await ai_engine.generate_recommendations(test_data)
        print(f"   Успешно: {result['success']}")
        print(f"   Время ответа: {result.get('response_time_seconds', 0)}с")
        print(f"   Использована модель: {result.get('model_used', 'неизвестно')}")

        if result['success']:
            print("   ✅ Рекомендации получены успешно!")
            recommendations = result['recommendations']

            if 'raw_recommendations' in recommendations:
                print(f"   📝 Ответ модели: {recommendations['raw_recommendations']}")
            else:
                for category, items in recommendations.items():
                    if items and isinstance(items, list):
                        print(f"   {category}:")
                        for item in items:
                            print(f"     • {item}")
        else:
            print(f"   ❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            if result.get('is_fallback'):
                print("   ℹ️  Используются резервные рекомендации")

    # 3. Показываем статистику
    print(f"\n3. Статистика: {ai_engine.get_stats()}")


if __name__ == "__main__":
    asyncio.run(test_ai_engine())