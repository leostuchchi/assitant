from backend.database import async_session, NatalPredictions
from backend.astrological.predictions import AstroPredictor
from backend.astrological.chart_services import get_user_natal_chart
from backend.psychology.matrix_services import get_user_matrix
from backend.biorhythms.biorhythm_services import calculate_and_save_biorhythms
from sqlalchemy.future import select
from sqlalchemy import func
import logging
import json
from datetime import datetime, date
from typing import List  # ✅ ДОБАВЛЕННЫЙ ИМПОРТ

logger = logging.getLogger(__name__)


class DataCombiner:
    """Класс для объединения данных астрологии и биоритмов"""

    def __init__(self):
        pass

    def combine_calculation_data(self, astro_prediction: dict, biorhythm_data: dict) -> dict:
        """Объединение данных из астрологии и биоритмов"""

        return {
            'calculation_date': datetime.now().isoformat(),
            'target_date': astro_prediction.get('prediction_date', datetime.now().date().isoformat()),
            'astro_data': {
                'transits_count': len(astro_prediction.get('transits', {})),
                'aspects_count': astro_prediction.get('aspects_count', 0),
                'strong_aspects_count': astro_prediction.get('strong_aspects_count', 0),
                'retrograde_planets': astro_prediction.get('retrograde_planets', []),
                'key_aspects': astro_prediction.get('aspects', [])[:5]  # ✅ ТЕПЕРЬ СОДЕРЖИТ ДАННЫЕ ДЛЯ СИЛЬНЫХ АСПЕКТОВ
            },
            'biorhythm_data': {
                'overall_energy': biorhythm_data.get('overall_energy', {}),
                'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {}),
                'critical_days_count': len(biorhythm_data.get('critical_days', [])),
                'peak_days_count': len(biorhythm_data.get('peak_days', []))
            },
            'calculation_metadata': {
                'calculation_timestamp': datetime.now().isoformat(),
                'data_sources': ['astrology', 'biorhythms'],
                'calculation_methods': ['swiss_ephemeris', 'sine_wave_analysis']
            }
        }


def _extract_strong_aspects(astro_data: dict) -> List[str]:
    """Извлечение и форматирование сильных аспектов"""
    strong_aspects = []

    try:
        key_aspects = astro_data.get('key_aspects', [])

        # Сортируем аспекты по силе (от самых сильных)
        sorted_aspects = sorted(key_aspects, key=lambda x: x.get('strength', 0), reverse=True)

        for aspect in sorted_aspects:
            # Фильтруем только сильные аспекты (strength > 0.7)
            if aspect.get('strength', 0) > 0.7:
                transit_planet = aspect.get('transit_planet', '')
                natal_planet = aspect.get('natal_planet', '')
                aspect_type = aspect.get('aspect', '')
                strength = aspect.get('strength', 0)

                # Форматируем для пользователя
                if transit_planet and natal_planet and aspect_type:
                    # Переводим названия планет на русский
                    planet_names = {
                        'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
                        'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
                        'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
                        'Pluto': 'Плутон', 'North_Node': 'Северный узел',
                        'Ascendant': 'Асцендент', 'Midheaven': 'МС'
                    }

                    aspect_names = {
                        'conjunction': 'соединение', 'opposition': 'оппозиция',
                        'square': 'квадрат', 'trine': 'трин', 'sextile': 'секстиль'
                    }

                    transit_ru = planet_names.get(transit_planet, transit_planet)
                    natal_ru = planet_names.get(natal_planet, natal_planet)
                    aspect_ru = aspect_names.get(aspect_type, aspect_type)

                    # Добавляем силу аспекта (★ за каждые 0.2 силы)
                    strength_stars = "★" * int(strength * 5)

                    strong_aspects.append(f"{transit_ru} → {natal_ru} ({aspect_ru}) {strength_stars}")

        return strong_aspects

    except Exception as e:
        logger.error(f"❌ Ошибка извлечения сильных аспектов: {e}")
        return []


# Добавить в начало файла:
from backend.astrological.aspect_recommendations import aspect_recommendations


# Обновить функцию format_data_for_user:
async def format_data_for_user(prediction: dict) -> str:
    """Форматирование данных для отображения пользователю"""
    if not prediction:
        return "❌ Не удалось получить данные расчетов"

    try:
        daily_data = prediction.get('daily_calculations', {})
        target_date_str = daily_data.get('target_date', 'сегодня')

        # Преобразуем строку даты в читаемый формат
        try:
            target_date = datetime.fromisoformat(target_date_str).date()
            formatted_date = target_date.strftime('%d.%m.%Y')
        except:
            formatted_date = target_date_str

        lines = []
        lines.append(f"📊 **Результаты расчетов на {formatted_date}**")
        lines.append("")

        # Биоритмы
        biorhythms = daily_data.get('biorhythm_data', {})
        if biorhythms:
            overall_energy = biorhythms.get('overall_energy', {})
            lines.append(
                f"⚡ **Общая энергия:** {overall_energy.get('percentage', 0):.1f}%")

            physical = biorhythms.get('physical_cycle', {})
            emotional = biorhythms.get('emotional_cycle', {})
            intellectual = biorhythms.get('intellectual_cycle', {})

            lines.append(
                f"💪 **Физический цикл:** {physical.get('percentage', 0):.1f}% ({physical.get('phase', 'нейтральная')})")
            lines.append(
                f"😊 **Эмоциональный цикл:** {emotional.get('percentage', 0):.1f}% ({emotional.get('phase', 'нейтральная')})")
            lines.append(
                f"🧠 **Интеллектуальный цикл:** {intellectual.get('percentage', 0):.1f}% ({intellectual.get('phase', 'нейтральная')})")
            lines.append("")

        # Астрологические данные
        astro_data = daily_data.get('astro_data', {})
        if astro_data:
            lines.append(
                f"🌟 **Астрология:** {astro_data.get('aspects_count', 0)} аспектов, {astro_data.get('strong_aspects_count', 0)} сильных")

            # ✅ ДОБАВЛЕНО: ПРОСТЫЕ РЕКОМЕНДАЦИИ ПО АСПЕКТАМ
            key_aspects = astro_data.get('key_aspects', [])
            aspect_recommendations_list = aspect_recommendations.generate_aspect_recommendations(key_aspects)

            if aspect_recommendations_list:
                lines.append("🔮 **Астрологические рекомендации:**")
                for rec in aspect_recommendations_list[:3]:  # Максимум 3 рекомендации
                    lines.append(f"   • {rec}")
                lines.append("")

            # Сильные аспекты (детальные)
            strong_aspects = _extract_strong_aspects(astro_data)
            if strong_aspects:
                lines.append("📈 **Сильные аспекты:**")
                for aspect in strong_aspects[:2]:  # Только 2 самых сильных
                    lines.append(f"   • {aspect}")
                lines.append("")

            retrograde_planets = astro_data.get('retrograde_planets', [])
            if retrograde_planets:
                planet_names = {
                    'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
                    'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
                    'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
                    'Pluto': 'Плутон'
                }
                retrograde_ru = [planet_names.get(p, p) for p in retrograde_planets]
                lines.append(f"🔄 **Ретроградные планеты:** {', '.join(retrograde_ru)}")

        lines.append("")
        lines.append("🎯 *Используйте эти данные для планирования своего дня*")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Ошибка форматирования данных: {e}")
        return "❌ Произошла ошибка при формировании данных расчетов"


# ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ
async def generate_and_save_prediction(telegram_id: int, target_date: date):
    """Генерация и сохранение данных для конкретной даты (перезапись существующих)"""
    try:
        logger.info(f"🔮 Генерация данных для пользователя {telegram_id} на {target_date}")

        # Получаем натальную карту пользователя
        natal_data = await get_user_natal_chart(telegram_id)
        if not natal_data:
            logger.warning(f"⚠️ Натальная карта не найдена для пользователя {telegram_id}")
            raise ValueError("Натальная карта не найдена. Сначала создайте натальную карту с помощью /start")

        logger.info(f"✅ Натальная карта найдена для {telegram_id}")

        # Получаем психоматрицу пользователя
        matrix_data = await get_user_matrix(telegram_id)
        logger.info(f"✅ Психоматрица получена для {telegram_id}")

        # Рассчитываем биоритмы на целевую дату
        biorhythm_data = await calculate_and_save_biorhythms(telegram_id, target_date)
        logger.info(f"✅ Биоритмы рассчитаны для {telegram_id} на {target_date}")

        # Генерируем астрологические данные на целевую дату
        predictor = AstroPredictor(natal_data)
        astro_prediction = predictor.generate_prediction(target_date)
        logger.info(f"✅ Астрологические данные сгенерированы для {telegram_id} на {target_date}")

        # Объединяем данные
        combiner = DataCombiner()
        combined_data = combiner.combine_calculation_data(astro_prediction, biorhythm_data)

        logger.info(f"✅ Комбинированные данные созданы для {telegram_id}")

        # Сохраняем данные в БД с ПЕРЕЗАПИСЬЮ
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            existing_record = result.scalar_one_or_none()

            # Структура данных для сохранения
            prediction_data = {
                'calculation_date': datetime.now().isoformat(),
                'target_date': target_date.isoformat(),
                'natal_chart': natal_data,
                'psyho_matrix': matrix_data,
                'daily_calculations': combined_data
            }

            if existing_record:
                # ПЕРЕЗАПИСЫВАЕМ существующую запись
                existing_record.predictions = prediction_data
                existing_record.updated_at = func.now()
                logger.info(f"📝 Перезаписаны данные для {telegram_id} на {target_date}")
            else:
                # Создаем новую запись
                new_record = NatalPredictions(
                    telegram_id=telegram_id,
                    predictions=prediction_data,
                    assistant_data={},
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы новые данные для {telegram_id} на {target_date}")

            await session.commit()
            logger.info(f"💾 Данные успешно сохранены в БД для {telegram_id}")

        return prediction_data

    except ValueError as e:
        logger.warning(f"❌ Ошибка валидации для {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации данных для {telegram_id}: {e}")
        raise Exception(f"Не удалось сгенерировать данные на основе расчетов: {str(e)}")



async def format_data_for_model(telegram_id: int, user_profile: dict, prediction: dict) -> str:
    """Форматирование данных для модели ИИ"""
    if not prediction:
        return "❌ No calculation data available"

    try:
        model_data = {
            'user_profile': {
                'telegram_id': telegram_id,
                'gender': user_profile.get('gender'),
                'profession': user_profile.get('profession'),
                'job_position': user_profile.get('job_position'),
                'current_city': user_profile.get('current_city'),
                'birth_date': user_profile.get('birth_date').isoformat() if user_profile.get('birth_date') else None,
                'birth_city': user_profile.get('birth_city')
            },
            'natal_chart': prediction.get('natal_chart', {}),
            'psyho_matrix': prediction.get('psyho_matrix', {}),
            'daily_calculations': prediction.get('daily_calculations', {}),
            'target_date': prediction.get('target_date'),
            'timestamp': datetime.now().isoformat()
        }

        # Красивый вывод для отладки
        print("\n" + "=" * 80)
        print("🤖 DATA FOR AI MODEL:")
        print("=" * 80)
        print(f"👤 User ID: {telegram_id}")
        print(f"📅 Target Date: {prediction.get('target_date', 'Unknown')}")
        print(f"💼 Profession: {user_profile.get('profession', 'Not specified')}")
        print(f"📋 Position: {user_profile.get('job_position', 'Not specified')}")
        print(f"🏙️ City: {user_profile.get('current_city', 'Not specified')}")

        # Натальная карта
        natal_chart = prediction.get('natal_chart', {})
        if natal_chart:
            planets = natal_chart.get('planets', {})
            print(f"\n🌟 Natal Chart: {len(planets)} planets calculated")
            print(f"   📍 Birth location: {natal_chart.get('metadata', {}).get('location', {}).get('city', 'Unknown')}")

        # Психоматрица
        matrix = prediction.get('psyho_matrix', {})
        if matrix:
            basic_numbers = matrix.get('basic_numbers', {})
            print(f"🔢 Psyho Matrix: First number: {basic_numbers.get('first', 'N/A')}")

        # Ежедневные расчеты
        daily = prediction.get('daily_calculations', {})
        if daily:
            biorhythms = daily.get('biorhythm_data', {})
            astro = daily.get('astro_data', {})
            print(f"📊 Daily Calculations:")
            print(f"   ⚡ Energy: {biorhythms.get('overall_energy', {}).get('percentage', 0):.1f}%")
            print(f"   🌟 Aspects: {astro.get('aspects_count', 0)}")

        print("=" * 80)
        print("JSON Data for AI Model:")
        print("=" * 80)
        print(json.dumps(model_data, ensure_ascii=False, indent=2))
        print("=" * 80 + "\n")

        return json.dumps(model_data, ensure_ascii=False)

    except Exception as e:
        logger.error(f"❌ Error formatting data for model: {e}")
        return json.dumps({'error': str(e)})



async def get_user_predictions(telegram_id: int):
    """Получение последних данных пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            predictions = result.scalar_one_or_none()

            if predictions:
                return predictions.predictions
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных {telegram_id}: {e}")
        return None



async def get_prediction_statistics(telegram_id: int) -> dict:
    """Получение статистики данных пользователя"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return {}

        daily_data = prediction.get('daily_calculations', {})
        return {
            'last_calculation_date': prediction.get('calculation_date'),
            'target_date': prediction.get('target_date'),
            'biorhythm_energy': daily_data.get('biorhythm_data', {}).get('overall_energy', {}).get('percentage', 0),
            'astro_aspects_count': daily_data.get('astro_data', {}).get('aspects_count', 0)
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        return {}


async def validate_prediction_data(telegram_id: int) -> bool:
    """Проверка корректности данных"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return False

        # Проверяем наличие обязательных полей
        required_fields = ['natal_chart', 'psyho_matrix', 'daily_calculations', 'target_date']
        for field in required_fields:
            if field not in prediction:
                return False

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
        return False


async def cleanup_old_predictions():
    """Очистка устаревших данных"""
    try:
        logger.info("🔄 Очистка устаревших данных не требуется в текущей структуре")
        return 0

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке данных: {e}")
        return 0