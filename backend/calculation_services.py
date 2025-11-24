from backend.database import async_session, DailyCalculations, CalculationCache, UserAstroProfile
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.chart_services import get_user_natal_chart
from backend.matrix_services import get_user_matrix
from backend.predictions import AstroPredictor
from backend.ml_orchestrator import ml_orchestrator, MLTaskType
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
import logging
import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Унифицированный сервис для управления всеми типами расчетов
    Обновлен для интеграции с ML оркестратором и новыми ML модулями
    """

    def __init__(self):
        self.cache_ttl_hours = 24  # Время жизни кэша в часах

    async def get_full_calculation_package(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """
        Получение полного пакета расчетных данных
        Основной метод для внешнего API - обновлен с ML интеграцией
        """
        try:
            # Проверяем кэш
            cached_data = await self._get_cached_calculation(telegram_id, target_date, 'full_package')
            if cached_data:
                logger.info(f"⚡ Использованы кэшированные данные для {telegram_id}")
                return cached_data

            # Получаем все типы расчетов с оптимизацией через ML оркестратор
            calculations = await asyncio.gather(
                self._get_biorhythm_calculations(telegram_id, target_date),
                self._get_astrology_calculations(telegram_id, target_date),
                self._get_matrix_calculations(telegram_id),
                self._get_user_context(telegram_id),
                self._get_ml_calculations(telegram_id, target_date),  # НОВАЯ ФУНКЦИОНАЛЬНОСТЬ
                return_exceptions=True
            )

            # Обрабатываем результаты
            biorhythm_data = calculations[0] if not isinstance(calculations[0], Exception) else {}
            astrology_data = calculations[1] if not isinstance(calculations[1], Exception) else {}
            matrix_data = calculations[2] if not isinstance(calculations[2], Exception) else {}
            user_context = calculations[3] if not isinstance(calculations[3], Exception) else {}
            ml_data = calculations[4] if not isinstance(calculations[4], Exception) else {}

            # Формируем полный пакет с ML данными
            calculation_package = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': {
                    'biorhythms': biorhythm_data,
                    'astrology': astrology_data,
                    'psychomatrix': matrix_data
                },
                'ml_data': ml_data,  # НОВАЯ СЕКЦИЯ ДЛЯ ML ДАННЫХ
                'user_context': user_context,
                'metadata': {
                    'calculation_timestamp': datetime.now().isoformat(),
                    'data_version': '3.0',  # Обновлена версия из-за ML данных
                    'sources_used': self._get_used_sources(biorhythm_data, astrology_data, matrix_data, ml_data),
                    'ml_integration': True
                }
            }

            # Сохраняем в кэш
            await self._save_to_cache(telegram_id, target_date, 'full_package', calculation_package)

            logger.info(f"✅ Полный пакет расчетов подготовлен для {telegram_id} с ML данными")
            return calculation_package

        except Exception as e:
            logger.error(f"❌ Ошибка формирования пакета расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'timestamp': datetime.now().isoformat()
            }

    async def _get_ml_calculations(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """
        Получение ML расчетов через оркестратор
        НОВАЯ ФУНКЦИОНАЛЬНОСТЬ - интеграция с ML системой
        """
        try:
            # Используем ML оркестратор для получения данных
            ml_package = await ml_orchestrator.generate_daily_ml_data(
                telegram_id,
                target_date
            )

            # Форматируем ML данные для единообразия с другими расчетами
            return {
                'features': ml_package.get('ml_features', {}),
                'insights': ml_package.get('basic_insights', []),
                'trends': ml_package.get('trend_data', {}),
                'generated_at': ml_package.get('generated_at'),
                'execution_time': ml_package.get('execution_time_seconds', 0),
                'data_quality': self._assess_ml_data_quality(ml_package)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения ML данных для {telegram_id}: {e}")
            return {
                'features': {},
                'insights': [],
                'trends': {},
                'error': str(e),
                'fallback_mode': True
            }

    async def _get_biorhythm_calculations(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Получение расчетов биоритмов"""
        try:
            biorhythm_data = await get_user_biorhythms(telegram_id, target_date)

            if not biorhythm_data:
                # Если данных нет, рассчитываем заново
                biorhythm_data = await calculate_and_save_biorhythms(telegram_id, target_date)

            return {
                'energy_levels': {
                    'overall': biorhythm_data.get('overall_energy', {}).get('percentage', 0),
                    'physical': biorhythm_data.get('cycles', {}).get('physical', {}).get('percentage', 0),
                    'emotional': biorhythm_data.get('cycles', {}).get('emotional', {}).get('percentage', 0),
                    'intellectual': biorhythm_data.get('cycles', {}).get('intellectual', {}).get('percentage', 0)
                },
                'phases': {
                    'physical': biorhythm_data.get('cycles', {}).get('physical', {}).get('phase', 'неизвестно'),
                    'emotional': biorhythm_data.get('cycles', {}).get('emotional', {}).get('phase', 'неизвестно'),
                    'intellectual': biorhythm_data.get('cycles', {}).get('intellectual', {}).get('phase', 'неизвестно')
                },
                'special_days': {
                    'critical_days': len(biorhythm_data.get('critical_days', [])),
                    'peak_days': len(biorhythm_data.get('peak_days', []))
                },
                'days_lived': biorhythm_data.get('days_lived', 0),
                'stability_score': self._calculate_biorhythm_stability(biorhythm_data)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения биоритмов для {telegram_id}: {e}")
            return {'error': str(e)}

    async def _get_astrology_calculations(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Получение астрологических расчетов"""
        try:
            # Получаем натальную карту
            natal_data = await get_user_natal_chart(telegram_id)
            if not natal_data:
                return {'error': 'Натальная карта не найдена'}

            # Рассчитываем транзиты
            predictor = AstroPredictor(natal_data)
            astro_prediction = predictor.generate_prediction(target_date)

            return {
                'transits': {
                    'total_planets': len(astro_prediction.get('transits', {})),
                    'retrograde_planets': astro_prediction.get('retrograde_planets', [])
                },
                'aspects': {
                    'total_count': astro_prediction.get('aspects_count', 0),
                    'strong_count': astro_prediction.get('strong_aspects_count', 0),
                    'key_aspects': astro_prediction.get('aspects', [])[:3]  # Топ-3 аспекта
                },
                'natal_summary': {
                    'dominant_element': self._get_dominant_element(natal_data),
                    'planets_count': len(natal_data.get('planets', {})),
                    'ascendant': natal_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно'),
                    'complexity_score': self._calculate_astrology_complexity(astro_prediction)
                }
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения астрологических данных для {telegram_id}: {e}")
            return {'error': str(e)}

    async def _get_matrix_calculations(self, telegram_id: int) -> Dict[str, Any]:
        """Получение расчетов психоматрицы"""
        try:
            matrix_data = await get_user_matrix(telegram_id)
            if not matrix_data:
                return {'error': 'Психоматрица не найдена'}

            basic_numbers = matrix_data.get('basic_numbers', {})
            pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

            return {
                'life_path': basic_numbers.get('first'),
                'destiny_number': basic_numbers.get('second'),
                'personality_number': basic_numbers.get('third'),
                'matrix_analysis': {
                    'complexity': self._calculate_matrix_complexity(pythagoras_matrix),
                    'strong_digits': [digit for digit, count in pythagoras_matrix.items() if count >= 2],
                    'missing_digits': [digit for digit in map(str, range(1, 10)) if
                                       pythagoras_matrix.get(digit, 0) == 0],
                    'energy_centers': self._analyze_energy_centers(pythagoras_matrix)
                },
                'calculated_at': matrix_data.get('calculated_at')
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения психоматрицы для {telegram_id}: {e}")
            return {'error': str(e)}

    async def _get_user_context(self, telegram_id: int) -> Dict[str, Any]:
        """Получение контекста пользователя"""
        try:
            from backend.user_services import get_user_profile

            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {}

            # Рассчитываем возраст
            age = self._calculate_age(user_profile.get('birth_date'))

            return {
                'demographics': {
                    'age': age,
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'city': user_profile.get('current_city', 'не указан'),
                    'gender': user_profile.get('gender', 'не указан')
                },
                'experience_level': self._estimate_experience_level(age, user_profile.get('profession')),
                'request_count': user_profile.get('request_count', 0),
                'data_completeness': self._calculate_user_data_completeness(user_profile)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста пользователя {telegram_id}: {e}")
            return {}

    def _calculate_biorhythm_stability(self, biorhythm_data: Dict) -> float:
        """Расчет стабильности биоритмов"""
        try:
            cycles = biorhythm_data.get('cycles', {})
            energies = [
                cycles.get('physical', {}).get('percentage', 50),
                cycles.get('emotional', {}).get('percentage', 50),
                cycles.get('intellectual', {}).get('percentage', 50)
            ]

            # Стабильность = 1 - (коэффициент вариации)
            mean = sum(energies) / len(energies)
            if mean == 0:
                return 0.5

            variance = sum((x - mean) ** 2 for x in energies) / len(energies)
            std_dev = variance ** 0.5
            coefficient_of_variation = std_dev / mean

            stability = 1.0 - min(coefficient_of_variation, 1.0)
            return round(stability, 3)

        except Exception:
            return 0.5

    def _calculate_astrology_complexity(self, astro_prediction: Dict) -> float:
        """Расчет сложности астрологической конфигурации"""
        try:
            aspects_count = astro_prediction.get('aspects_count', 0)
            strong_aspects = astro_prediction.get('strong_aspects_count', 0)
            retrograde_count = len(astro_prediction.get('retrograde_planets', []))

            # Сложность = взвешенная сумма факторов
            complexity = (
                                 aspects_count * 0.3 +
                                 strong_aspects * 0.5 +
                                 retrograde_count * 0.2
                         ) / 10.0  # Нормализация

            return min(complexity, 1.0)

        except Exception:
            return 0.0

    def _assess_ml_data_quality(self, ml_package: Dict) -> Dict[str, Any]:
        """Оценка качества ML данных"""
        try:
            features = ml_package.get('ml_features', {})
            insights = ml_package.get('basic_insights', [])
            trends = ml_package.get('trend_data', {})

            quality_score = 0
            factors = 0

            if features:
                quality_score += 0.4
                factors += 1

            if insights and len(insights) >= 2:
                quality_score += 0.3
                factors += 1

            if trends:
                quality_score += 0.3
                factors += 1

            if factors > 0:
                quality_score /= factors

            return {
                'score': round(quality_score, 3),
                'features_available': bool(features),
                'insights_count': len(insights),
                'trends_available': bool(trends),
                'completeness': round(quality_score * 100, 1)
            }

        except Exception:
            return {'score': 0.0, 'completeness': 0.0}

    def _calculate_user_data_completeness(self, user_profile: Dict) -> float:
        """Расчет полноты данных пользователя"""
        try:
            required_fields = [
                user_profile.get('birth_date'),
                user_profile.get('birth_time'),
                user_profile.get('birth_city'),
                user_profile.get('profession')
            ]

            filled_fields = sum(1 for field in required_fields if field)
            completeness = filled_fields / len(required_fields)

            return round(completeness * 100, 1)

        except Exception:
            return 0.0

    def _get_dominant_element(self, natal_data: dict) -> str:
        """Определение доминирующего элемента"""
        try:
            element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _calculate_matrix_complexity(self, matrix: dict) -> str:
        """Оценка сложности психоматрицы"""
        total_digits = sum(matrix.values())
        if total_digits >= 15:
            return "сложная"
        elif total_digits >= 10:
            return "средняя"
        else:
            return "простая"

    def _analyze_energy_centers(self, matrix: dict) -> Dict[str, int]:
        """Анализ энергетических центров"""
        return {
            'practical': sum(matrix.get(str(digit), 0) for digit in [4, 5, 6]),
            'spiritual': sum(matrix.get(str(digit), 0) for digit in [7, 8, 9]),
            'will': sum(matrix.get(str(digit), 0) for digit in [1, 2, 3])
        }

    def _calculate_age(self, birth_date: date) -> int:
        """Расчет возраста"""
        if not birth_date:
            return 0
        today = date.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age

    def _estimate_experience_level(self, age: int, profession: str) -> str:
        """Оценка уровня опыта"""
        if not profession or profession.lower() in ['не указана', 'нет', '']:
            return "неизвестно"

        if age < 22:
            return "начинающий"
        elif age < 30:
            return "опытный"
        elif age < 45:
            return "профессионал"
        else:
            return "эксперт"

    def _get_used_sources(self, biorhythms: dict, astrology: dict, matrix: dict, ml_data: dict) -> List[str]:
        """Определение использованных источников данных"""
        sources = []

        if biorhythms and not biorhythms.get('error'):
            sources.append('biorhythms')
        if astrology and not astrology.get('error'):
            sources.append('astrology')
        if matrix and not matrix.get('error'):
            sources.append('psychomatrix')
        if ml_data and not ml_data.get('fallback_mode'):
            sources.append('ml_analysis')

        return sources

    async def _get_cached_calculation(self, telegram_id: int, target_date: date, data_type: str) -> Optional[
        Dict[str, Any]]:
        """Получение данных из кэша"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(CalculationCache).where(
                        and_(
                            CalculationCache.telegram_id == telegram_id,
                            CalculationCache.target_date == target_date,
                            CalculationCache.data_type == data_type,
                            CalculationCache.expires_at > datetime.now()
                        )
                    )
                )
                cached = result.scalar_one_or_none()

                if cached:
                    return cached.calculation_data
                return None

        except Exception as e:
            logger.debug(f"⚠️ Ошибка получения из кэша: {e}")
            return None

    async def _save_to_cache(self, telegram_id: int, target_date: date, data_type: str, data: Dict[str, Any]):
        """Сохранение данных в кэш"""
        try:
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)

            async with async_session() as session:
                # Удаляем старую запись
                await session.execute(
                    CalculationCache.__table__.delete().where(
                        and_(
                            CalculationCache.telegram_id == telegram_id,
                            CalculationCache.target_date == target_date,
                            CalculationCache.data_type == data_type
                        )
                    )
                )

                # Создаем новую запись
                cache_entry = CalculationCache(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    data_type=data_type,
                    calculation_data=data,
                    expires_at=expires_at
                )
                session.add(cache_entry)

                await session.commit()
                logger.debug(f"💾 Данные сохранены в кэш для {telegram_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш: {e}")
            # Не прерываем выполнение при ошибке кэширования


class CalculationOptimizer:
    """
    Сервис для оптимизации и управления расчетами
    Обновлен для работы с ML данными
    """

    def __init__(self):
        self.calculation_service = CalculationService()

    async def get_optimized_calculations(self, telegram_id: int, target_date: date,
                                         include_types: List[str] = None) -> Dict[str, Any]:
        """
        Оптимизированное получение расчетов с фильтрацией по типам
        Обновлен для поддержки ML данных
        """
        if include_types is None:
            include_types = ['biorhythms', 'astrology', 'psychomatrix', 'ml_analysis']  # Добавлен ML анализ

        try:
            # Получаем полный пакет
            full_package = await self.calculation_service.get_full_calculation_package(telegram_id, target_date)

            if not full_package.get('success'):
                return full_package

            # Фильтруем данные по запрошенным типам
            filtered_calculations = {}
            ml_data_included = False

            for calc_type in include_types:
                if calc_type == 'ml_analysis' and 'ml_data' in full_package:
                    filtered_calculations['ml_analysis'] = full_package['ml_data']
                    ml_data_included = True
                elif calc_type in full_package['calculations']:
                    filtered_calculations[calc_type] = full_package['calculations'][calc_type]

            # Формируем оптимизированный ответ
            optimized_response = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': filtered_calculations,
                'user_context': full_package.get('user_context', {}),
                'included_types': include_types,
                'ml_integration': ml_data_included,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"🎯 Оптимизированные расчеты подготовлены для {telegram_id} с ML: {ml_data_included}")
            return optimized_response

        except Exception as e:
            logger.error(f"❌ Ошибка оптимизированных расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': telegram_id,
                'target_date': target_date.isoformat()
            }

    async def get_calculation_health_check(self, telegram_id: int) -> Dict[str, Any]:
        """
        Проверка здоровья расчетных данных пользователя
        Обновлен для проверки ML данных
        """
        try:
            checks = await asyncio.gather(
                self._check_biorhythm_health(telegram_id),
                self._check_astrology_health(telegram_id),
                self._check_matrix_health(telegram_id),
                self._check_user_data_health(telegram_id),
                self._check_ml_data_health(telegram_id)  # НОВАЯ ПРОВЕРКА
            )

            health_status = {
                'user_id': telegram_id,
                'check_timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'detailed_checks': {
                    'biorhythms': checks[0],
                    'astrology': checks[1],
                    'psychomatrix': checks[2],
                    'user_data': checks[3],
                    'ml_data': checks[4]  # НОВАЯ ПРОВЕРКА
                }
            }

            # Определяем общий статус с учетом ML данных
            all_healthy = all(check.get('status') in ['healthy', 'degraded'] for check in checks)
            critical_issues = any(check.get('status') == 'critical' for check in checks)

            if critical_issues:
                health_status['overall_status'] = 'critical'
            elif all_healthy:
                health_status['overall_status'] = 'healthy'
            else:
                health_status['overall_status'] = 'degraded'

            return health_status

        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья расчетов для {telegram_id}: {e}")
            return {
                'user_id': telegram_id,
                'overall_status': 'error',
                'error': str(e)
            }

    async def _check_ml_data_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья ML данных"""
        try:
            today = date.today()

            # Проверяем наличие ML данных в daily_calculations
            async with async_session() as session:
                result = await session.execute(
                    select(DailyCalculations).where(
                        and_(
                            DailyCalculations.telegram_id == telegram_id,
                            DailyCalculations.target_date == today
                        )
                    )
                )
                daily_calc = result.scalar_one_or_none()

            if not daily_calc:
                return {
                    'status': 'missing',
                    'message': 'Отсутствуют расчетные данные для проверки ML',
                    'recommendation': 'Выполнить расчет данных'
                }

            # Проверяем наличие ML данных
            ml_features = daily_calc.ml_features
            basic_insights = daily_calc.basic_insights

            if not ml_features and not basic_insights:
                return {
                    'status': 'missing',
                    'message': 'Отсутствуют ML данные',
                    'recommendation': 'Запустить генерацию ML данных'
                }

            # Проверяем свежесть ML данных
            if daily_calc.calculation_timestamp:
                data_age = (datetime.now() - daily_calc.calculation_timestamp).total_seconds() / 3600
                if data_age > 24:
                    return {
                        'status': 'stale',
                        'message': f'ML данные устарели ({data_age:.1f} часов)',
                        'recommendation': 'Обновить ML расчеты'
                    }

            # Проверяем качество ML данных
            ml_quality = self._assess_stored_ml_quality(ml_features, basic_insights)

            if ml_quality['score'] < 0.5:
                return {
                    'status': 'degraded',
                    'message': f'Низкое качество ML данных ({ml_quality["score"]:.2f})',
                    'recommendation': 'Перегенерировать ML данные',
                    'quality_metrics': ml_quality
                }

            return {
                'status': 'healthy',
                'message': 'ML данные в порядке',
                'quality_metrics': ml_quality,
                'features_count': len(ml_features) if ml_features else 0,
                'insights_count': len(basic_insights) if basic_insights else 0
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    def _assess_stored_ml_quality(self, ml_features: Dict, basic_insights: List) -> Dict[str, Any]:
        """Оценка качества сохраненных ML данных"""
        try:
            quality_score = 0.0
            factors = 0

            if ml_features and isinstance(ml_features, dict):
                # Проверяем ключевые ML фичи
                key_features = ['daily_score', 'energy_overall', 'productivity_index']
                present_features = sum(1 for feat in key_features if feat in ml_features)
                quality_score += (present_features / len(key_features)) * 0.6
                factors += 1

            if basic_insights and isinstance(basic_insights, list) and len(basic_insights) >= 2:
                quality_score += 0.4
                factors += 1

            if factors > 0:
                quality_score /= factors

            return {
                'score': round(quality_score, 3),
                'features_available': bool(ml_features),
                'insights_available': bool(basic_insights and len(basic_insights) >= 2),
                'completeness': round(quality_score * 100, 1)
            }

        except Exception:
            return {'score': 0.0, 'completeness': 0.0}

    async def _check_biorhythm_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья данных биоритмов"""
        try:
            today = date.today()
            biorhythm_data = await get_user_biorhythms(telegram_id, today)

            if not biorhythm_data:
                return {
                    'status': 'missing',
                    'message': 'Отсутствуют данные биоритмов на сегодня',
                    'recommendation': 'Выполнить расчет биоритмов'
                }

            # Проверяем свежесть данных
            async with async_session() as session:
                result = await session.execute(
                    select(DailyCalculations.calculation_timestamp).where(
                        and_(
                            DailyCalculations.telegram_id == telegram_id,
                            DailyCalculations.target_date == today
                        )
                    )
                )
                timestamp = result.scalar_one_or_none()

            if timestamp:
                data_age = (datetime.now() - timestamp).total_seconds() / 3600
                if data_age > 24:
                    return {
                        'status': 'stale',
                        'message': f'Данные биоритмов устарели ({data_age:.1f} часов)',
                        'recommendation': 'Обновить расчет биоритмов'
                    }

            return {
                'status': 'healthy',
                'message': 'Данные биоритмов актуальны',
                'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_astrology_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья астрологических данных"""
        try:
            natal_data = await get_user_natal_chart(telegram_id)

            if not natal_data:
                return {
                    'status': 'critical',  # Критическая ошибка - без натальной карты астрология не работает
                    'message': 'Отсутствует натальная карта',
                    'recommendation': 'Создать натальную карту'
                }

            # Проверяем полноту данных
            planets = natal_data.get('planets', {})
            essential_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
            missing_planets = [p for p in essential_planets if p not in planets]

            if missing_planets:
                return {
                    'status': 'degraded',
                    'message': f'Отсутствуют планеты: {", ".join(missing_planets)}',
                    'recommendation': 'Пересчитать натальную карту'
                }

            return {
                'status': 'healthy',
                'message': 'Натальная карта в порядке',
                'planets_count': len(planets)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_matrix_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья данных психоматрицы"""
        try:
            matrix_data = await get_user_matrix(telegram_id)

            if not matrix_data:
                return {
                    'status': 'missing',
                    'message': 'Отсутствует психоматрица',
                    'recommendation': 'Рассчитать психоматрицу'
                }

            # Проверяем базовые числа
            basic_numbers = matrix_data.get('basic_numbers', {})
            if not all(key in basic_numbers for key in ['first', 'second', 'third', 'fourth']):
                return {
                    'status': 'incomplete',
                    'message': 'Неполные базовые числа',
                    'recommendation': 'Пересчитать психоматрицу'
                }

            return {
                'status': 'healthy',
                'message': 'Психоматрица в порядке',
                'life_path': basic_numbers.get('first')
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_user_data_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья пользовательских данных"""
        try:
            from backend.user_services import get_user_profile

            user_profile = await get_user_profile(telegram_id)

            if not user_profile:
                return {
                    'status': 'critical',  # Критическая ошибка - без профиля расчеты невозможны
                    'message': 'Отсутствуют основные данные пользователя',
                    'recommendation': 'Заполнить профиль'
                }

            # Проверяем обязательные поля
            missing_fields = []
            if not user_profile.get('birth_date'):
                missing_fields.append('дата рождения')
            if not user_profile.get('birth_time'):
                missing_fields.append('время рождения')
            if not user_profile.get('birth_city'):
                missing_fields.append('город рождения')

            if missing_fields:
                return {
                    'status': 'critical',
                    'message': f'Отсутствуют обязательные поля: {", ".join(missing_fields)}',
                    'recommendation': 'Дополнить профиль'
                }

            return {
                'status': 'healthy',
                'message': 'Данные пользователя полные',
                'profession': user_profile.get('profession', 'не указана')
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def cleanup_old_calculations(self, days_old: int = 30) -> Dict[str, int]:
        """
        Очистка устаревших расчетов и кэша
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_old)

            async with async_session() as session:
                # Очищаем устаревшие daily calculations
                daily_result = await session.execute(
                    DailyCalculations.__table__.delete().where(
                        DailyCalculations.target_date < cutoff_date
                    )
                )
                daily_deleted = daily_result.rowcount

                # Очищаем просроченный кэш
                cache_result = await session.execute(
                    CalculationCache.__table__.delete().where(
                        CalculationCache.expires_at < datetime.now()
                    )
                )
                cache_deleted = cache_result.rowcount

                await session.commit()

            logger.info(f"🧹 Очистка расчетов: {daily_deleted} daily calculations, {cache_deleted} cache entries")

            return {
                'daily_calculations_deleted': daily_deleted,
                'cache_entries_deleted': cache_deleted,
                'total_deleted': daily_deleted + cache_deleted
            }

        except Exception as e:
            logger.error(f"❌ Ошибка очистки расчетов: {e}")
            return {
                'daily_calculations_deleted': 0,
                'cache_entries_deleted': 0,
                'total_deleted': 0,
                'error': str(e)
            }


# Глобальные экземпляры сервисов
calculation_service = CalculationService()
calculation_optimizer = CalculationOptimizer()