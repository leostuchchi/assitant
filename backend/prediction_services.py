from backend.database import async_session, DailyCalculations, UserAstroProfile
from backend.predictions import AstroPredictor
from backend.chart_services import get_user_natal_chart
from backend.matrix_services import get_user_matrix
from backend.biorhythm_services import calculate_and_save_biorhythms
#from backend.aspect_recommendations import aspect_recommendations
from sqlalchemy.future import select
from sqlalchemy import func, and_
import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import hashlib

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
                'key_aspects': astro_prediction.get('aspects', [])[:5],
                'calculation_error': astro_prediction.get('calculation_error', False),
                'error_message': astro_prediction.get('error_message')
            },
            'biorhythm_data': {
                'overall_energy': biorhythm_data.get('overall_energy', {}),
                'cycles': biorhythm_data.get('cycles', {}),
                'critical_days_count': len(biorhythm_data.get('critical_days', [])),
                'peak_days_count': len(biorhythm_data.get('peak_days', [])),
                'days_lived': biorhythm_data.get('days_lived', 0)
            },
            'calculation_metadata': {
                'calculation_timestamp': datetime.now().isoformat(),
                'data_sources': ['astrology', 'biorhythms'],
                'calculation_methods': ['swiss_ephemeris', 'sine_wave_analysis'],
                'data_version': '2.0'
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


def _generate_data_hash(telegram_id: int, target_date: date, calculation_data: dict) -> str:
    """Генерация хэша данных для кэширования"""
    try:
        data_str = f"{telegram_id}_{target_date.isoformat()}_{json.dumps(calculation_data, sort_keys=True)}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"❌ Ошибка генерации хэша: {e}")
        return "fallback_hash"


def _generate_aspect_recommendations(key_aspects: List[Dict]) -> List[str]:
    """Упрощенная генерация рекомендаций без отдельного модуля"""
    if not key_aspects:
        return []

    # Простая логика на основе силы аспектов
    recommendations = []
    strong_aspects = [a for a in key_aspects if a.get('strength', 0) > 0.7]

    for aspect in strong_aspects[:3]:  # Только топ-3
        rec = _format_aspect_recommendation(aspect)
        if rec:
            recommendations.append(rec)

    return recommendations


def _format_aspect_recommendation(aspect: Dict) -> str:
    """Форматирование одного аспекта в рекомендацию"""
    try:
        transit_planet = aspect.get('transit_planet', '')
        natal_planet = aspect.get('natal_planet', '')
        aspect_type = aspect.get('aspect', '')
        strength = aspect.get('strength', 0)

        if not all([transit_planet, natal_planet, aspect_type]):
            return None

        # Перевод названий планет на русский
        planet_names = {
            'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
            'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
            'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
            'Pluto': 'Плутон', 'North_Node': 'Северный узел',
            'Ascendant': 'Асцендент', 'Midheaven': 'МС'
        }

        # Перевод типов аспектов
        aspect_names = {
            'conjunction': 'соединение',
            'opposition': 'оппозиция',
            'square': 'квадрат',
            'trine': 'трин',
            'sextile': 'секстиль'
        }

        transit_ru = planet_names.get(transit_planet, transit_planet)
        natal_ru = planet_names.get(natal_planet, natal_planet)
        aspect_ru = aspect_names.get(aspect_type, aspect_type)

        # Эмодзи для разных типов аспектов
        emoji_map = {
            'conjunction': '⚡',
            'opposition': '⚖️',
            'square': '🎯',
            'trine': '🌟',
            'sextile': '💫'
        }
        emoji = emoji_map.get(aspect_type, '✨')

        # Уровень силы (звездочки)
        strength_stars = "★" * int(strength * 5)

        return f"{emoji} {transit_ru} → {natal_ru} ({aspect_ru}) {strength_stars}"

    except Exception as e:
        logger.debug(f"Ошибка форматирования аспекта: {e}")
        return None



async def format_data_for_user(prediction: dict) -> str:
    """Форматирование данных для отображения пользователю в боте"""
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

            cycles = biorhythms.get('cycles', {})
            physical = cycles.get('physical', {})
            emotional = cycles.get('emotional', {})
            intellectual = cycles.get('intellectual', {})

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

            # Рекомендации по аспектам
            key_aspects = astro_data.get('key_aspects', [])
            aspect_recommendations_list = _generate_aspect_recommendations(key_aspects)

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

        # Критические дни
        if biorhythms and biorhythms.get('critical_days_count', 0) > 0:
            lines.append("")
            lines.append("⚠️ **Критический день** - будьте осторожны в принятии решений")

        lines.append("")
        lines.append("🎯 *Используйте эти данные для планирования своего дня*")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Ошибка форматирования данных: {e}")
        return "❌ Произошла ошибка при формировании данных расчетов"


async def generate_and_save_prediction(telegram_id: int, target_date: date) -> Dict[str, Any]:
    """Генерация и сохранение данных для конкретной даты"""
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

        # Сохраняем в daily_calculations
        await save_daily_calculations(telegram_id, target_date, combined_data)

        # Структура данных для возврата
        prediction_data = {
            'calculation_date': datetime.now().isoformat(),
            'target_date': target_date.isoformat(),
            'natal_chart': natal_data,
            'psyho_matrix': matrix_data,
            'daily_calculations': combined_data
        }

        logger.info(f"💾 Все данные сохранены для {telegram_id} на {target_date}")

        return prediction_data

    except ValueError as e:
        logger.warning(f"❌ Ошибка валидации для {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации данных для {telegram_id}: {e}")
        raise Exception(f"Не удалось сгенерировать данные на основе расчетов: {str(e)}")


async def save_daily_calculations(telegram_id: int, target_date: date, calculation_data: dict) -> bool:
    """Сохранение ежедневных расчетов в оптимизированную таблицу"""
    try:
        data_hash = _generate_data_hash(telegram_id, target_date, calculation_data)

        async with async_session() as session:
            # Проверяем существующую запись
            result = await session.execute(
                select(DailyCalculations).where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
            )
            existing_record = result.scalar_one_or_none()

            if existing_record:
                # Обновляем существующую запись
                existing_record.biorhythm_data = calculation_data.get('biorhythm_data', {})
                existing_record.astro_transits_data = calculation_data.get('astro_data', {})
                existing_record.calculation_metadata = calculation_data.get('calculation_metadata', {})
                existing_record.data_hash = data_hash
                existing_record.calculation_timestamp = datetime.now()
                logger.info(f"📝 Обновлены daily calculations для {telegram_id} на {target_date}")
            else:
                # Создаем новую запись
                new_record = DailyCalculations(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    biorhythm_data=calculation_data.get('biorhythm_data', {}),
                    astro_transits_data=calculation_data.get('astro_data', {}),
                    calculation_metadata=calculation_data.get('calculation_metadata', {}),
                    data_hash=data_hash,
                    calculation_timestamp=datetime.now()
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы daily calculations для {telegram_id} на {target_date}")

            await session.commit()
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка сохранения daily calculations для {telegram_id}: {e}")
        await session.rollback()
        return False


async def get_daily_calculations(telegram_id: int, target_date: date) -> Optional[Dict[str, Any]]:
    """Получение ежедневных расчетов для конкретной даты"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(DailyCalculations).where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
            )
            daily_calc = result.scalar_one_or_none()

            if daily_calc:
                return {
                    'biorhythm_data': daily_calc.biorhythm_data,
                    'astro_transits_data': daily_calc.astro_transits_data,
                    'calculation_metadata': daily_calc.calculation_metadata,
                    'calculation_timestamp': daily_calc.calculation_timestamp.isoformat(),
                    'data_hash': daily_calc.data_hash
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка получения daily calculations для {telegram_id}: {e}")
        return None


async def get_user_predictions(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получение последних данных пользователя (для обратной совместимости)"""
    try:
        # Получаем статические данные
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if not astro_profile:
                return None

            # Получаем последние daily calculations
            today = date.today()
            daily_calc = await get_daily_calculations(telegram_id, today)

            return {
                'calculation_date': datetime.now().isoformat(),
                'target_date': today.isoformat(),
                'natal_chart': astro_profile.natal_chart_data,
                'psyho_matrix': astro_profile.psyho_matrix_data,
                'daily_calculations': daily_calc or {}
            }

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных {telegram_id}: {e}")
        return None


async def get_prediction_statistics(telegram_id: int) -> dict:
    """Получение статистики данных пользователя"""
    try:
        # Получаем количество записей daily calculations
        async with async_session() as session:
            count_result = await session.execute(
                select(func.count(DailyCalculations.telegram_id)).where(
                    DailyCalculations.telegram_id == telegram_id
                )
            )
            total_calculations = count_result.scalar() or 0

            # Получаем даты первой и последней записи
            dates_result = await session.execute(
                select(
                    func.min(DailyCalculations.target_date),
                    func.max(DailyCalculations.target_date)
                ).where(DailyCalculations.telegram_id == telegram_id)
            )
            min_date, max_date = dates_result.first() or (None, None)

        # Получаем последние расчеты
        latest_calc = await get_daily_calculations(telegram_id, date.today())

        return {
            'total_calculations': total_calculations,
            'first_calculation_date': min_date.isoformat() if min_date else None,
            'last_calculation_date': max_date.isoformat() if max_date else None,
            'calculation_range_days': (max_date - min_date).days if min_date and max_date else 0,
            'latest_energy_level': latest_calc.get('biorhythm_data', {}).get('overall_energy', {}).get('percentage', 0) if latest_calc else 0,
            'latest_aspects_count': latest_calc.get('astro_transits_data', {}).get('aspects_count', 0) if latest_calc else 0
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        return {}


async def validate_prediction_data(telegram_id: int) -> bool:
    """Проверка корректности данных"""
    try:
        # Проверяем наличие астропрофиля
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if not astro_profile:
                return False

            # Проверяем наличие основных данных
            if not astro_profile.natal_chart_data or not astro_profile.psyho_matrix_data:
                return False

            # Проверяем наличие хотя бы одной записи daily calculations
            today = date.today()
            daily_calc = await get_daily_calculations(telegram_id, today)

            return daily_calc is not None

    except Exception as e:
        logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
        return False


async def cleanup_old_predictions(days_old: int = 30) -> int:
    """Очистка устаревших данных daily calculations"""
    try:
        cutoff_date = date.today() - timedelta(days=days_old)

        async with async_session() as session:
            result = await session.execute(
                DailyCalculations.__table__.delete().where(
                    DailyCalculations.target_date < cutoff_date
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} устаревших записей daily calculations (старше {days_old} дней)")
            else:
                logger.info("✅ Устаревших записей daily calculations для удаления не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке устаревших данных: {e}")
        return 0


async def get_user_calculation_history(telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получение истории расчетов пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(DailyCalculations)
                .where(DailyCalculations.telegram_id == telegram_id)
                .order_by(DailyCalculations.target_date.desc())
                .limit(limit)
            )
            calculations = result.scalars().all()

            history = []
            for calc in calculations:
                history.append({
                    'target_date': calc.target_date.isoformat(),
                    'energy_level': calc.biorhythm_data.get('overall_energy', {}).get('percentage', 0),
                    'aspects_count': calc.astro_transits_data.get('aspects_count', 0),
                    'calculation_timestamp': calc.calculation_timestamp.isoformat()
                })

            return history

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории расчетов для {telegram_id}: {e}")
        return []


async def calculate_data_freshness(telegram_id: int, target_date: date) -> Dict[str, Any]:
    """Проверка свежести данных"""
    try:
        daily_calc = await get_daily_calculations(telegram_id, target_date)

        if not daily_calc:
            return {
                'is_fresh': False,
                'age_hours': None,
                'status': 'NO_DATA'
            }

        calc_timestamp = datetime.fromisoformat(daily_calc['calculation_timestamp'])
        age_hours = (datetime.now() - calc_timestamp).total_seconds() / 3600

        return {
            'is_fresh': age_hours < 24,  # Считаем свежими данные младше 24 часов
            'age_hours': round(age_hours, 2),
            'calculation_timestamp': daily_calc['calculation_timestamp'],
            'status': 'FRESH' if age_hours < 24 else 'STALE'
        }

    except Exception as e:
        logger.error(f"❌ Ошибка проверки свежести данных для {telegram_id}: {e}")
        return {
            'is_fresh': False,
            'age_hours': None,
            'status': 'ERROR'
        }