from backend.database import async_session, Biorhythms, DailyCalculations
from backend.biorhythm_calculator import BiorhythmCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import date, datetime, timedelta
import logging
import asyncio
import json
import hashlib

logger = logging.getLogger(__name__)


async def calculate_and_save_biorhythms(telegram_id: int, target_date: date = None):
    """Расчет и сохранение биоритмов пользователя"""
    try:
        if target_date is None:
            target_date = date.today()

        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        # Рассчитываем биоритмы
        calculator = BiorhythmCalculator()
        biorhythm_data = calculator.calculate_biorhythms(
            user_profile['birth_date'],
            target_date
        )

        # Сохраняем в БД с атомарной операцией
        async with async_session() as session:
            try:
                # Сначала удаляем ВСЕ существующие записи для этой даты (на случай дублей)
                await session.execute(
                    Biorhythms.__table__.delete().where(
                        and_(
                            Biorhythms.telegram_id == telegram_id,
                            Biorhythms.calculation_date == target_date
                        )
                    )
                )

                # Создаем новую запись
                new_record = Biorhythms(
                    telegram_id=telegram_id,
                    biorhythm_data=biorhythm_data,
                    calculation_date=target_date
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы новые биоритмы для {telegram_id} на {target_date}")

                # Также сохраняем в daily_calculations для оптимизации
                await _save_to_daily_calculations(session, telegram_id, target_date, biorhythm_data)

                await session.commit()
                logger.info(f"💾 Биоритмы успешно сохранены для {telegram_id}")

            except Exception as db_error:
                await session.rollback()
                logger.error(f"❌ Ошибка БД при сохранении биоритмов {telegram_id}: {db_error}")
                raise

        return biorhythm_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете биоритмов для {telegram_id}: {e}")
        raise


async def _save_to_daily_calculations(session, telegram_id: int, target_date: date, biorhythm_data: dict):
    """Сохранение биоритмов в таблицу daily_calculations"""
    try:
        # Генерируем хэш данных
        data_str = json.dumps(biorhythm_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Проверяем существующую запись
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
            # Обновляем существующую запись
            daily_calc.biorhythm_data = biorhythm_data
            daily_calc.data_hash = data_hash
            daily_calc.calculation_timestamp = datetime.now()
        else:
            # Создаем новую запись только с биоритмами
            daily_calc = DailyCalculations(
                telegram_id=telegram_id,
                target_date=target_date,
                biorhythm_data=biorhythm_data,
                astro_transits_data={},  # Пустые астрологические данные
                calculation_metadata={
                    'data_source': 'biorhythms_only',
                    'calculation_method': 'sine_wave_analysis'
                },
                data_hash=data_hash,
                calculation_timestamp=datetime.now()
            )
            session.add(daily_calc)

        logger.info(f"💾 Биоритмы сохранены в daily_calculations для {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в daily_calculations: {e}")
        raise


async def get_user_biorhythms(telegram_id: int, target_date: date = None):
    """Получение биоритмов пользователя с улучшенной обработкой ошибок"""
    try:
        if target_date is None:
            target_date = date.today()

        # Сначала пробуем получить из daily_calculations (оптимизированно)
        daily_calc = await _get_biorhythms_from_daily_calculations(telegram_id, target_date)
        if daily_calc:
            return daily_calc

        # Если нет в daily_calculations, ищем в основной таблице
        async with async_session() as session:
            result = await session.execute(
                select(Biorhythms).where(
                    and_(
                        Biorhythms.telegram_id == telegram_id,
                        Biorhythms.calculation_date == target_date
                    )
                )
            )
            biorhythms = result.scalar_one_or_none()

            if biorhythms:
                logger.info(f"✅ Найдены сохраненные биоритмы для {telegram_id} на {target_date}")
                return biorhythms.biorhythm_data

            # Если запись не найдена, рассчитываем заново
            logger.info(f"🔄 Биоритмы не найдены, рассчитываем заново для {telegram_id}")
            return await calculate_and_save_biorhythms(telegram_id, target_date)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении биоритмов {telegram_id}: {e}")
        return None


async def _get_biorhythms_from_daily_calculations(telegram_id: int, target_date: date):
    """Получение биоритмов из оптимизированной таблицы daily_calculations"""
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

            if daily_calc and daily_calc.biorhythm_data:
                logger.info(f"⚡ Биоритмы получены из daily_calculations для {telegram_id}")
                return daily_calc.biorhythm_data

        return None

    except Exception as e:
        logger.debug(f"⚠️ Ошибка получения из daily_calculations: {e}")
        return None


async def get_biorhythm_weekly_forecast(telegram_id: int, start_date: date = None, days: int = 7):
    """Получение недельного прогноза биоритмов с улучшенной обработкой"""
    try:
        if start_date is None:
            start_date = date.today()

        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        forecast = calculator.calculate_weekly_forecast(
            user_profile['birth_date'],
            start_date,
            days
        )

        logger.info(f"✅ Прогноз биоритмов рассчитан для {telegram_id} на {days} дней")
        return forecast

    except Exception as e:
        logger.error(f"❌ Ошибка при получении прогноза биоритмов {telegram_id}: {e}")
        return None


async def get_biorhythm_trend(telegram_id: int, period_days: int = 30):
    """Анализ тренда биоритмов за период"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        async with async_session() as session:
            result = await session.execute(
                select(Biorhythms).where(
                    and_(
                        Biorhythms.telegram_id == telegram_id,
                        Biorhythms.calculation_date >= start_date,
                        Biorhythms.calculation_date <= end_date
                    )
                ).order_by(Biorhythms.calculation_date)
            )
            biorhythms_records = result.scalars().all()

        if not biorhythms_records:
            return {"error": "Недостаточно данных для анализа тренда"}

        # Анализируем тренды
        trends = {
            'physical_trend': _calculate_trend(biorhythms_records, 'physical'),
            'emotional_trend': _calculate_trend(biorhythms_records, 'emotional'),
            'intellectual_trend': _calculate_trend(biorhythms_records, 'intellectual'),
            'overall_trend': _calculate_overall_trend(biorhythms_records),
            'analysis_period': f"{start_date.isoformat()} - {end_date.isoformat()}",
            'records_analyzed': len(biorhythms_records)
        }

        logger.info(f"📈 Проанализирован тренд биоритмов для {telegram_id}")
        return trends

    except Exception as e:
        logger.error(f"❌ Ошибка анализа тренда биоритмов {telegram_id}: {e}")
        return {"error": str(e)}


def _calculate_trend(biorhythms_records, cycle_type: str):
    """Расчет тренда для конкретного цикла"""
    try:
        percentages = []
        for record in biorhythms_records:
            cycle_data = record.biorhythm_data.get('cycles', {}).get(cycle_type, {})
            percentage = cycle_data.get('percentage', 0)
            percentages.append(percentage)

        if len(percentages) < 2:
            return "недостаточно данных"

        # Простой анализ тренда
        first_half = percentages[:len(percentages) // 2]
        second_half = percentages[len(percentages) // 2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first + 5:
            return "растущий"
        elif avg_second < avg_first - 5:
            return "падающий"
        else:
            return "стабильный"

    except Exception as e:
        logger.error(f"❌ Ошибка расчета тренда {cycle_type}: {e}")
        return "ошибка расчета"


def _calculate_overall_trend(biorhythms_records):
    """Расчет общего тренда энергии"""
    try:
        overall_energies = []
        for record in biorhythms_records:
            overall_energy = record.biorhythm_data.get('overall_energy', {})
            percentage = overall_energy.get('percentage', 0)
            overall_energies.append(percentage)

        if len(overall_energies) < 2:
            return "недостаточно данных"

        # Анализ общего тренда
        first_third = overall_energies[:len(overall_energies) // 3]
        last_third = overall_energies[-(len(overall_energies) // 3):]

        avg_first = sum(first_third) / len(first_third)
        avg_last = sum(last_third) / len(last_third)

        difference = avg_last - avg_first

        if difference > 10:
            return "сильный рост"
        elif difference > 5:
            return "умеренный рост"
        elif difference < -10:
            return "сильное падение"
        elif difference < -5:
            return "умеренное падение"
        else:
            return "стабильный"

    except Exception as e:
        logger.error(f"❌ Ошибка расчета общего тренда: {e}")
        return "ошибка расчета"


async def get_critical_days_forecast(telegram_id: int, days_ahead: int = 30):
    """Прогноз критических дней на указанный период"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        critical_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            critical_days_list = biorhythm_data.get('critical_days', [])
            if critical_days_list:
                critical_days.append({
                    'date': current_date.isoformat(),
                    'cycles': critical_days_list[0].get('cycles', []),
                    'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
                })

            current_date += timedelta(days=1)

        logger.info(f"⚠️  Найдено {len(critical_days)} критических дней для {telegram_id}")
        return critical_days

    except Exception as e:
        logger.error(f"❌ Ошибка прогноза критических дней {telegram_id}: {e}")
        return []


async def get_peak_days_forecast(telegram_id: int, days_ahead: int = 30):
    """Прогноз пиковых дней на указанный период"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        peak_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            peak_days_list = biorhythm_data.get('peak_days', [])
            if peak_days_list:
                peak_days.append({
                    'date': current_date.isoformat(),
                    'cycles': peak_days_list[0].get('cycles', []),
                    'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
                })

            current_date += timedelta(days=1)

        logger.info(f"📈 Найдено {len(peak_days)} пиковых дней для {telegram_id}")
        return peak_days

    except Exception as e:
        logger.error(f"❌ Ошибка прогноза пиковых дней {telegram_id}: {e}")
        return []


async def cleanup_duplicate_biorhythms():
    """Очистка дублирующихся записей биоритмов"""
    try:
        async with async_session() as session:
            # Находим дублирующиеся записи
            duplicate_query = """
            DELETE FROM biorhythms 
            WHERE ctid NOT IN (
                SELECT MIN(ctid) 
                FROM biorhythms 
                GROUP BY telegram_id, calculation_date
            )
            """

            result = await session.execute(duplicate_query)
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.warning(f"🗑️ Удалено {deleted_count} дублирующихся записей биоритмов")
            else:
                logger.info("✅ Дублирующихся записей биоритмов не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке дублирующихся биоритмов: {e}")
        return 0


async def get_biorhythm_statistics(telegram_id: int):
    """Получение статистики по биоритмам пользователя"""
    try:
        async with async_session() as session:
            # Количество записей биоритмов
            count_result = await session.execute(
                select(func.count(Biorhythms.telegram_id)).where(
                    Biorhythms.telegram_id == telegram_id
                )
            )
            total_records = count_result.scalar() or 0

            # Самая старая и новая запись
            dates_result = await session.execute(
                select(
                    func.min(Biorhythms.calculation_date),
                    func.max(Biorhythms.calculation_date)
                ).where(Biorhythms.telegram_id == telegram_id)
            )
            min_date, max_date = dates_result.first() or (None, None)

            # Средний уровень энергии
            energy_result = await session.execute(
                select(func.avg(Biorhythms.biorhythm_data['overall_energy']['percentage'].as_float())).where(
                    Biorhythms.telegram_id == telegram_id
                )
            )
            avg_energy = energy_result.scalar() or 0

            statistics = {
                'total_records': total_records,
                'first_calculation': min_date.isoformat() if min_date else None,
                'last_calculation': max_date.isoformat() if max_date else None,
                'calculation_range_days': (max_date - min_date).days if min_date and max_date else 0,
                'average_energy_level': round(avg_energy, 2),
                'calculation_frequency': _calculate_frequency(total_records, min_date, max_date)
            }

            logger.info(f"📊 Статистика биоритмов получена для {telegram_id}")
            return statistics

    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики биоритмов {telegram_id}: {e}")
        return {
            'total_records': 0,
            'first_calculation': None,
            'last_calculation': None,
            'calculation_range_days': 0,
            'average_energy_level': 0,
            'calculation_frequency': 'неизвестно'
        }


def _calculate_frequency(total_records, min_date, max_date):
    """Расчет частоты расчетов"""
    if not min_date or not max_date or total_records == 0:
        return "неизвестно"

    total_days = (max_date - min_date).days
    if total_days == 0:
        return "ежедневно"

    frequency = total_records / (total_days + 1)  # +1 чтобы избежать деления на 0

    if frequency >= 0.9:
        return "ежедневно"
    elif frequency >= 0.3:
        return "регулярно"
    elif frequency >= 0.1:
        return "периодически"
    else:
        return "редко"


async def cleanup_old_biorhythms(days_old: int = 30):
    """Очистка старых записей биоритмов"""
    try:
        cutoff_date = date.today() - timedelta(days=days_old)

        async with async_session() as session:
            result = await session.execute(
                Biorhythms.__table__.delete().where(
                    Biorhythms.calculation_date < cutoff_date
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} старых записей биоритмов (старше {days_old} дней)")
            else:
                logger.info("✅ Старых записей биоритмов для удаления не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке старых биоритмов: {e}")
        return 0


async def get_optimal_planning_days(telegram_id: int, days_ahead: int = 14):
    """Рекомендации оптимальных дней для планирования"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        optimal_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            cycles = biorhythm_data.get('cycles', {})
            physical = cycles.get('physical', {}).get('percentage', 0)
            emotional = cycles.get('emotional', {}).get('percentage', 0)
            intellectual = cycles.get('intellectual', {}).get('percentage', 0)

            # Оценка дня для планирования
            planning_score = _calculate_planning_score(overall_energy, physical, emotional, intellectual)

            if planning_score >= 80:
                day_type = "отличный"
                recommendation = "идеально для важных решений и планирования"
            elif planning_score >= 60:
                day_type = "хороший"
                recommendation = "подходит для стратегического планирования"
            elif planning_score >= 40:
                day_type = "удовлетворительный"
                recommendation = "можно планировать рутинные задачи"
            else:
                day_type = "неблагоприятный"
                recommendation = "лучше отложить важные решения"

            optimal_days.append({
                'date': current_date.isoformat(),
                'planning_score': planning_score,
                'day_type': day_type,
                'recommendation': recommendation,
                'energy_level': overall_energy,
                'physical': physical,
                'emotional': emotional,
                'intellectual': intellectual
            })

            current_date += timedelta(days=1)

        # Сортируем по убыванию оценки
        optimal_days.sort(key=lambda x: x['planning_score'], reverse=True)

        logger.info(f"🎯 Определены оптимальные дни для планирования {telegram_id}")
        return optimal_days

    except Exception as e:
        logger.error(f"❌ Ошибка определения оптимальных дней {telegram_id}: {e}")
        return []


def _calculate_planning_score(overall: float, physical: float, emotional: float, intellectual: float) -> float:
    """Расчет оценки дня для планирования"""
    # Веса для разных аспектов планирования
    weights = {
        'overall': 0.3,
        'intellectual': 0.4,  # Самый важный для планирования
        'emotional': 0.2,  # Важен для принятия решений
        'physical': 0.1  # Менее важен для планирования
    }

    score = (
            overall * weights['overall'] +
            intellectual * weights['intellectual'] +
            emotional * weights['emotional'] +
            physical * weights['physical']
    )

    return round(score, 2)


class BiorhythmAnalysisService:
    """Сервис для углубленного анализа биоритмов"""

    def __init__(self):
        self.calculator = BiorhythmCalculator()

    async def get_comprehensive_analysis(self, telegram_id: int, target_date: date = None):
        """Полный анализ биоритмов с рекомендациями"""
        try:
            if target_date is None:
                target_date = date.today()

            # Получаем текущие биоритмы
            biorhythm_data = await get_user_biorhythms(telegram_id, target_date)
            if not biorhythm_data:
                return {"error": "Не удалось получить данные биоритмов"}

            # Получаем прогнозы
            weekly_forecast = await get_biorhythm_weekly_forecast(telegram_id, target_date, 7)
            critical_days = await get_critical_days_forecast(telegram_id, 30)
            peak_days = await get_peak_days_forecast(telegram_id, 30)
            optimal_days = await get_optimal_planning_days(telegram_id, 14)

            # Анализ трендов
            trend_analysis = await get_biorhythm_trend(telegram_id, 30)

            # Формируем полный анализ
            analysis = {
                'current_data': biorhythm_data,
                'weekly_forecast': weekly_forecast,
                'critical_days_forecast': critical_days[:5],  # Только ближайшие 5
                'peak_days_forecast': peak_days[:5],
                'optimal_planning_days': optimal_days[:3],  # Только топ-3
                'trend_analysis': trend_analysis,
                'personalized_recommendations': self._generate_recommendations(biorhythm_data),
                'analysis_timestamp': datetime.now().isoformat()
            }

            logger.info(f"📊 Полный анализ биоритмов подготовлен для {telegram_id}")
            return analysis

        except Exception as e:
            logger.error(f"❌ Ошибка полного анализа биоритмов {telegram_id}: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, biorhythm_data: dict) -> list:
        """Генерация персонализированных рекомендаций"""
        recommendations = []

        overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
        cycles = biorhythm_data.get('cycles', {})
        physical = cycles.get('physical', {})
        emotional = cycles.get('emotional', {})
        intellectual = cycles.get('intellectual', {})

        # Рекомендации по общей энергии
        if overall_energy >= 80:
            recommendations.append("💪 Идеальный день для сложных задач и важных решений")
        elif overall_energy >= 60:
            recommendations.append("🚀 Хорошее время для активной работы и проектов")
        elif overall_energy <= 30:
            recommendations.append("🛌 Рекомендуется беречь силы, делать перерывы")

        # Рекомендации по физическому циклу
        physical_percentage = physical.get('percentage', 0)
        if physical_percentage >= 70:
            recommendations.append("🏃 Отличный день для спорта и физической активности")
        elif physical_percentage <= 30:
            recommendations.append("💤 Избегайте тяжелых физических нагрузок")

        # Рекомендации по эмоциональному циклу
        emotional_percentage = emotional.get('percentage', 0)
        if emotional_percentage >= 70:
            recommendations.append("😊 Благоприятное время для общения и встреч")
        elif emotional_percentage <= 30:
            recommendations.append("🧘 Контролируйте эмоции, избегайте конфликтов")

        # Рекомендации по интеллектуальному циклу
        intellectual_percentage = intellectual.get('percentage', 0)
        if intellectual_percentage >= 70:
            recommendations.append("📚 Идеально для обучения, анализа и планирования")
        elif intellectual_percentage <= 30:
            recommendations.append("📝 Отложите сложные интеллектуальные задачи")

        # Критические дни
        critical_days = biorhythm_data.get('critical_days', [])
        if critical_days:
            recommendations.append("⚠️ Критический день - будьте осторожны в принятии решений")

        return recommendations

    async def get_energy_optimization_plan(self, telegram_id: int, period_days: int = 7):
        """План оптимизации энергии на период"""
        try:
            forecast = await get_biorhythm_weekly_forecast(telegram_id, date.today(), period_days)
            if not forecast:
                return {"error": "Не удалось получить прогноз"}

            optimization_plan = []

            for day_data in forecast:
                date_str = day_data['date']
                energy_level = day_data['overall_energy']
                physical = day_data['physical']
                emotional = day_data['emotional']
                intellectual = day_data['intellectual']

                # Определяем тип дня и рекомендации
                if energy_level >= 75:
                    day_type = "энергичный"
                    focus = "сложные задачи, новые проекты"
                    activities = ["стратегическое планирование", "принятие решений", "переговоры"]
                elif energy_level >= 50:
                    day_type = "стабильный"
                    focus = "текущие задачи, рутинная работа"
                    activities = ["выполнение планов", "коммуникация", "обучение"]
                else:
                    day_type = "восстановительный"
                    focus = "отдых, подготовка, анализ"
                    activities = ["планирование", "анализ результатов", "восстановление сил"]

                optimization_plan.append({
                    'date': date_str,
                    'energy_level': energy_level,
                    'day_type': day_type,
                    'focus_area': focus,
                    'recommended_activities': activities,
                    'physical_energy': physical,
                    'emotional_energy': emotional,
                    'intellectual_energy': intellectual
                })

            return {
                'optimization_plan': optimization_plan,
                'period': f"{period_days} дней",
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания плана оптимизации для {telegram_id}: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
biorhythm_service = BiorhythmAnalysisService()