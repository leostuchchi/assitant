from backend.user_services import create_or_update_user, get_user_profile, update_user_profession, \
    increment_request_count
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_user_predictions, \
    format_data_for_user, get_daily_calculations, save_daily_calculations
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.calculation_services import calculation_service, calculation_optimizer
from backend.ml_orchestrator import ml_orchestrator, MLTaskType
from backend.database import async_session
from datetime import datetime, date, timedelta
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
import math

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """
    Главный класс помощника для управления расчетными данными
    ОБНОВЛЕН: Интеграция с ML системой и оптимизация кэширования
    """

    def __init__(self):
        self.calculation_cache = {}
        self.ml_cache = {}
        self.cache_ttl = 300  # 5 минут в секундах
        self.ml_cache_ttl = 600  # 10 минут для ML данных

    def _calculate_user_age(self, birth_date: date) -> int:
        """Расчет возраста пользователя с обработкой ошибок"""
        try:
            if not birth_date:
                return 0
            today = date.today()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета возраста: {e}")
            return 0

    def _estimate_experience_level(self, age: int, profession: str) -> str:
        """Оценка уровня профессионального опыта"""
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

    def _get_energy_level_description(self, percentage: float) -> Dict[str, str]:
        """Описание уровня энергии с ML-контекстом"""
        if percentage >= 90:
            return {
                "level": "очень высокий",
                "description": "идеально для сложных задач и важных решений",
                "ml_confidence": "high"
            }
        elif percentage >= 75:
            return {
                "level": "высокий",
                "description": "отлично для продуктивной работы",
                "ml_confidence": "medium"
            }
        elif percentage >= 60:
            return {
                "level": "хороший",
                "description": "подходит для активной деятельности",
                "ml_confidence": "medium"
            }
        elif percentage >= 40:
            return {
                "level": "средний",
                "description": "стабильно для рутинных задач",
                "ml_confidence": "medium"
            }
        elif percentage >= 20:
            return {
                "level": "низкий",
                "description": "требует бережного отношения к силам",
                "ml_confidence": "high"
            }
        else:
            return {
                "level": "критически низкий",
                "description": "необходим отдых и восстановление",
                "ml_confidence": "high"
            }

    def _get_season(self, target_date: date) -> str:
        """Определение сезона для контекста с кэшированием"""
        try:
            month = target_date.month
            if month in [12, 1, 2]:
                return 'зима'
            elif month in [3, 4, 5]:
                return 'весна'
            elif month in [6, 7, 8]:
                return 'лето'
            else:
                return 'осень'
        except Exception as e:
            logger.warning(f"⚠️ Ошибка определения сезона: {e}")
            return 'неизвестно'

    def _get_lunar_phase(self, target_date: date) -> str:
        """Упрощенный расчет лунной фазы"""
        try:
            day = target_date.day
            if day <= 7:
                return 'растущая луна'
            elif day <= 14:
                return 'полнолуние'
            elif day <= 21:
                return 'убывающая луна'
            else:
                return 'новолуние'
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета лунной фазы: {e}")
            return 'неизвестно'

    def _prepare_calculation_data(self, telegram_id: int, user_profile: dict, prediction: dict,
                                  target_date: date) -> dict:
        """
        Подготовка структурированных данных для внешнего потребления
        ОБНОВЛЕНО: Интеграция ML данных
        """
        try:
            daily_calculations = prediction.get('daily_calculations', {})
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            astro_data = daily_calculations.get('astro_data', {})
            natal_chart = prediction.get('natal_chart', {})
            psyho_matrix = prediction.get('psyho_matrix', {})

            # НОВОЕ: ML данные
            ml_features = daily_calculations.get('ml_features', {})
            basic_insights = daily_calculations.get('basic_insights', [])
            trend_data = daily_calculations.get('trend_data', {})

            # Базовые данные пользователя
            user_age = self._calculate_user_age(user_profile.get('birth_date'))
            experience_level = self._estimate_experience_level(user_age, user_profile.get('profession'))

            # Оптимизированные данные для внешнего API с ML контекстом
            prepared_data = {
                # Контекст пользователя
                'user_context': {
                    'telegram_id': telegram_id,
                    'age': user_age,
                    'experience_level': experience_level,
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'current_city': user_profile.get('current_city', 'не указан'),
                    'birth_city': user_profile.get('birth_city', 'не указан'),
                    'gender': user_profile.get('gender', 'не указан'),
                    'data_completeness': self._calculate_user_data_completeness(user_profile)
                },

                # Энергетическое состояние с ML оценкой
                'energy_state': {
                    'overall_energy': biorhythm_data.get('overall_energy', {}),
                    'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                    'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                    'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {}),
                    'ml_energy_assessment': ml_features.get('energy_assessment', 'стабильная')
                },

                # Астрологические данные
                'astro_data': {
                    'aspects_count': astro_data.get('aspects_count', 0),
                    'strong_aspects_count': astro_data.get('strong_aspects_count', 0),
                    'retrograde_planets': astro_data.get('retrograde_planets', []),
                    'key_aspects': astro_data.get('key_aspects', [])[:3],  # Только топ-3
                    'astro_complexity': self._calculate_astrology_complexity(astro_data)
                },

                # Статические данные
                'static_profile': {
                    'natal_chart_summary': {
                        'planets_count': len(natal_chart.get('planets', {})),
                        'dominant_element': self._get_dominant_element(natal_chart),
                        'ascendant': natal_chart.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно'),
                        'chart_complexity': self._get_chart_complexity(natal_chart)
                    },
                    'psyho_matrix_summary': {
                        'life_path_number': psyho_matrix.get('basic_numbers', {}).get('first'),
                        'matrix_complexity': self._calculate_matrix_complexity(psyho_matrix),
                        'energy_level': self._get_matrix_energy_level(psyho_matrix)
                    }
                },

                # НОВОЕ: ML данные и аналитика
                'ml_analytics': {
                    'daily_score': ml_features.get('daily_score', 0),
                    'productivity_index': ml_features.get('productivity_index', 0),
                    'energy_overall': ml_features.get('energy_overall', 0),
                    'focus_recommendation': ml_features.get('focus_recommendation', 'сбалансированная активность'),
                    'risk_factors': ml_features.get('risk_factors', []),
                    'opportunities': ml_features.get('opportunities', []),
                    'basic_insights': basic_insights[:5],  # Только топ-5 инсайтов
                    'trend_indicators': trend_data.get('indicators', {}),
                    'data_quality': self._assess_ml_data_quality(ml_features, basic_insights)
                },

                # Контекст дня
                'daily_context': {
                    'season': self._get_season(target_date),
                    'day_of_week': target_date.strftime('%A'),
                    'lunar_phase': self._get_lunar_phase(target_date),
                    'is_weekend': target_date.weekday() >= 5,
                    'day_type': self._classify_day_type(biorhythm_data, astro_data, ml_features)
                },

                # Мета-информация
                'calculation_meta': {
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'calculation_timestamp': datetime.now().isoformat(),
                    'data_version': '3.0',  # Обновлено для ML данных
                    'ml_integration': True,
                    'sources_used': self._get_used_sources(biorhythm_data, astro_data, ml_features)
                }
            }

            logger.info(f"✅ Данные подготовлены для пользователя {telegram_id} на {target_date} с ML контекстом")
            return prepared_data

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки данных: {e}")
            return self._prepare_data_fallback(user_profile, target_date, str(e))

    def _calculate_user_data_completeness(self, user_profile: dict) -> float:
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

    def _calculate_astrology_complexity(self, astro_data: dict) -> str:
        """Оценка сложности астрологической конфигурации"""
        try:
            aspects_count = astro_data.get('aspects_count', 0)
            strong_aspects = astro_data.get('strong_aspects_count', 0)

            if aspects_count >= 10 or strong_aspects >= 5:
                return "сложная"
            elif aspects_count >= 5 or strong_aspects >= 2:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"

    def _get_chart_complexity(self, natal_chart: dict) -> str:
        """Оценка сложности натальной карты"""
        try:
            aspects = natal_chart.get('aspects', [])
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

    def _get_matrix_energy_level(self, psyho_matrix: dict) -> str:
        """Оценка уровня энергии по психоматрице"""
        try:
            matrix_data = psyho_matrix.get('pythagoras_matrix', {})
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

    def _assess_ml_data_quality(self, ml_features: dict, basic_insights: list) -> dict:
        """Оценка качества ML данных"""
        try:
            quality_score = 0.0
            factors = 0

            if ml_features:
                # Проверяем ключевые ML фичи
                key_features = ['daily_score', 'energy_overall', 'productivity_index']
                present_features = sum(1 for feat in key_features if feat in ml_features)
                quality_score += (present_features / len(key_features)) * 0.6
                factors += 1

            if basic_insights and len(basic_insights) >= 2:
                quality_score += 0.4
                factors += 1

            if factors > 0:
                quality_score /= factors

            return {
                'score': round(quality_score, 3),
                'level': 'высокое' if quality_score >= 0.7 else 'среднее' if quality_score >= 0.4 else 'низкое',
                'features_count': len(ml_features) if ml_features else 0,
                'insights_count': len(basic_insights),
                'completeness': round(quality_score * 100, 1)
            }

        except Exception:
            return {'score': 0.0, 'level': 'неизвестно', 'completeness': 0.0}

    def _classify_day_type(self, biorhythm_data: dict, astro_data: dict, ml_features: dict) -> str:
        """Классификация типа дня на основе всех данных"""
        try:
            # Анализ биоритмов
            overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 50)
            critical_days = biorhythm_data.get('critical_days_count', 0)

            # Анализ астрологии
            strong_aspects = astro_data.get('strong_aspects_count', 0)
            retrograde_count = len(astro_data.get('retrograde_planets', []))

            # Анализ ML данных
            daily_score = ml_features.get('daily_score', 0.5)
            energy_assessment = ml_features.get('energy_assessment', 'стабильная')

            # Логика классификации
            if critical_days > 0 or daily_score < 0.3:
                return "критический"
            elif overall_energy >= 75 and daily_score >= 0.7 and strong_aspects <= 2:
                return "благоприятный"
            elif overall_energy >= 60 and daily_score >= 0.5:
                return "продуктивный"
            elif overall_energy < 40 or daily_score < 0.4:
                return "восстановительный"
            else:
                return "сбалансированный"

        except Exception:
            return "неопределенный"

    def _get_used_sources(self, biorhythms: dict, astrology: dict, ml_features: dict) -> List[str]:
        """Определение использованных источников данных"""
        sources = []

        if biorhythms and biorhythms.get('overall_energy'):
            sources.append('biorhythms')
        if astrology and astrology.get('aspects_count', 0) > 0:
            sources.append('astrology')
        if ml_features and ml_features.get('daily_score') is not None:
            sources.append('ml_analysis')

        return sources

    def _get_dominant_element(self, natal_chart: dict) -> str:
        """Определение доминирующего элемента в натальной карте"""
        try:
            element_balance = natal_chart.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _calculate_matrix_complexity(self, psyho_matrix: dict) -> str:
        """Оценка сложности психоматрицы"""
        try:
            matrix_data = psyho_matrix.get('pythagoras_matrix', {})
            total_digits = sum(matrix_data.values())
            if total_digits >= 15:
                return "сложная"
            elif total_digits >= 10:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"

    def _prepare_data_fallback(self, user_profile: dict, target_date: date, error_msg: str = None) -> dict:
        """Резервная подготовка данных при ошибках"""
        fallback_data = {
            'user_context': {
                'profession': user_profile.get('profession', 'не указана'),
                'position': user_profile.get('job_position', 'не указана'),
                'current_city': user_profile.get('current_city', 'не указан')
            },
            'energy_state': {},
            'astro_data': {},
            'static_profile': {},
            'ml_analytics': {
                'daily_score': 0.5,
                'basic_insights': ['Данные временно недоступны. Используются базовые рекомендации.'],
                'data_quality': {'level': 'низкое', 'score': 0.0}
            },
            'daily_context': {
                'target_date': target_date.strftime('%Y-%m-%d'),
                'day_type': 'неопределенный'
            },
            'calculation_meta': {
                'fallback_mode': True,
                'error': error_msg or 'Данные временно недоступны',
                'ml_integration': False
            }
        }

        logger.warning(f"🔄 Использован резервный режим подготовки данных: {error_msg}")
        return fallback_data

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None, gender: str = None):
        """Сбор и сохранение всех данных пользователя с ML инициализацией"""
        try:
            logger.info(f"🔄 Начало сбора данных для пользователя {telegram_id}")

            async with async_session() as session:
                try:
                    # 1. Сохраняем основные данные пользователя
                    user = await create_or_update_user(
                        telegram_id=telegram_id,
                        birth_date=birth_date,
                        birth_time=birth_time,
                        birth_city=birth_city,
                        current_city=current_city,
                        profession=profession,
                        job_position=job_position,
                        gender=gender
                    )
                    logger.info(f"✅ Данные пользователя сохранены")

                    # 2. Создаем натальную карту
                    birth_datetime = datetime.combine(birth_date, birth_time)
                    natal_chart = await create_and_save_natal_chart(
                        telegram_id=telegram_id,
                        city=birth_city,
                        birth_datetime=birth_datetime,
                        timezone="Europe/Moscow"
                    )
                    logger.info(f"✅ Натальная карта создана")

                    # 3. Рассчитываем психоматрицу
                    matrix_data = await calculate_and_save_psyho_matrix(telegram_id)
                    logger.info(f"✅ Психоматрица рассчитана")

                    # 4. Рассчитываем биоритмы на сегодня
                    biorhythms = await calculate_and_save_biorhythms(telegram_id)
                    logger.info(f"✅ Биоритмы рассчитаны")

                    # 5. НОВОЕ: Инициализация ML профиля пользователя
                    try:
                        ml_init_result = await ml_orchestrator.initialize_user_profile(
                            telegram_id,
                            {
                                'birth_date': birth_date,
                                'profession': profession,
                                'user_context': {
                                    'age': self._calculate_user_age(birth_date),
                                    'experience_level': self._estimate_experience_level(
                                        self._calculate_user_age(birth_date), profession
                                    )
                                }
                            }
                        )
                        if ml_init_result.get('success'):
                            logger.info(f"✅ ML профиль инициализирован для {telegram_id}")
                        else:
                            logger.warning(
                                f"⚠️ ML инициализация завершена с предупреждениями: {ml_init_result.get('error')}")
                    except Exception as ml_error:
                        logger.warning(f"⚠️ Ошибка ML инициализации (не критично): {ml_error}")

                    await session.commit()

                    return {
                        'success': True,
                        'message': "✅ Все данные успешно собраны и сохранены!",
                        'data_collected': {
                            'user_profile': True,
                            'natal_chart': True,
                            'psyho_matrix': True,
                            'biorhythms': True,
                            'ml_initialized': True
                        }
                    }

                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ Ошибка в транзакции сбора данных для {telegram_id}: {e}")
                    raise

        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка при сборе данных: {str(e)}"
            }

    async def get_recommendations(self, telegram_id: int, target_date: date):
        """
        Получение расчетных данных на выбранную дату с ML интеграцией
        ОБНОВЛЕНО: Интеграция с ML оркестратором
        """
        try:
            logger.info(f"📅 Формирование данных на {target_date} для {telegram_id}")

            # Проверяем кэш
            cache_key = f"{telegram_id}_{target_date}"
            current_time = datetime.now().timestamp()

            if cache_key in self.calculation_cache:
                cached_data = self.calculation_cache[cache_key]
                if current_time - cached_data['timestamp'] < self.cache_ttl:
                    logger.info(f"⚡ Использованы кэшированные данные для {telegram_id}")
                    return cached_data['data']

            # Увеличиваем счетчик обращений
            await increment_request_count(telegram_id)
            logger.info(f"📈 Счетчик обращений увеличен для {telegram_id}")

            # Проверяем что дата не в прошлом (кроме анализа истории)
            if target_date < date.today():
                logger.warning(f"⚠️ Запрос данных для прошедшей даты: {target_date}")

            # Генерируем и сохраняем данные для выбранной даты
            prediction = await generate_and_save_prediction(telegram_id, target_date)

            # Получаем профиль пользователя
            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {
                    'success': False,
                    'message': "❌ Профиль пользователя не найден"
                }

            # 1. Данные для пользователя (через бот)
            user_data = await format_data_for_user(prediction)

            # 2. Структурированные данные для внешнего API с ML
            structured_data = self._prepare_calculation_data(telegram_id, user_profile, prediction, target_date)

            # 3. НОВОЕ: Дополнительная ML аналитика если доступна
            ml_analytics = {}
            try:
                daily_calc = prediction.get('daily_calculations', {})
                if daily_calc.get('ml_features'):
                    ml_analytics = await ml_orchestrator.get_user_analytics_summary(telegram_id, target_date)
            except Exception as ml_error:
                logger.warning(f"⚠️ Ошибка получения ML аналитики: {ml_error}")

            result = {
                'success': True,
                'date': target_date.isoformat(),
                'user_data': user_data,  # Для бота
                'structured_data': structured_data,  # Для внешнего API
                'prediction_data': prediction,  # Полные данные
                'user_profile': user_profile,
                'ml_analytics': ml_analytics,  # НОВОЕ: Расширенная ML аналитика
                'cache_info': {
                    'cached': False,
                    'generated_at': datetime.now().isoformat()
                }
            }

            # Сохраняем в кэш
            self.calculation_cache[cache_key] = {
                'data': result,
                'timestamp': current_time
            }

            logger.info(f"✅ Данные сформированы для {telegram_id} на {target_date} с ML контекстом")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить данные на выбранную дату: {str(e)}"
            }

    async def get_calculation_package(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """
        Полный пакет расчетных данных для внешнего API
        ОПТИМИЗИРОВАНО: Использование calculation_service с ML данными
        """
        try:
            # Используем оптимизированный сервис расчетов
            calculation_package = await calculation_service.get_full_calculation_package(
                telegram_id,
                target_date
            )

            if calculation_package.get('success'):
                logger.info(f"✅ Пакет расчетов подготовлен через calculation_service для {telegram_id}")
            else:
                logger.warning(f"⚠️ Пакет расчетов завершен с ошибками для {telegram_id}")

            return calculation_package

        except Exception as e:
            logger.error(f"❌ Ошибка формирования пакета расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_todays_recommendations(self, telegram_id: int):
        """Получение данных на сегодня с приоритетным кэшированием"""
        return await self.get_recommendations(telegram_id, date.today())

    async def get_tomorrows_recommendations(self, telegram_id: int):
        """Получение данных на завтра"""
        tomorrow = date.today() + timedelta(days=1)
        return await self.get_recommendations(telegram_id, tomorrow)

    async def get_date_recommendations(self, telegram_id: int, target_date: date):
        """Получение данных на выбранную дату"""
        return await self.get_recommendations(telegram_id, target_date)

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None, gender: str = None):
        """Обновление профессиональной информации с ML синхронизацией"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            user_profile = await get_user_profile(telegram_id)
            if user_profile:
                await create_or_update_user(
                    telegram_id=telegram_id,
                    birth_date=user_profile['birth_date'],
                    birth_time=user_profile['birth_time'],
                    birth_city=user_profile['birth_city'],
                    current_city=current_city,
                    profession=profession,
                    job_position=job_position,
                    gender=gender
                )

            # НОВОЕ: Обновление ML контекста
            try:
                await ml_orchestrator.update_user_context(
                    telegram_id,
                    {'profession': profession, 'position': job_position}
                )
            except Exception as ml_error:
                logger.warning(f"⚠️ Ошибка обновления ML контекста: {ml_error}")

            logger.info(f"✅ Профессиональные данные обновлены для {telegram_id} с ML синхронизацией")
            return {
                'success': True,
                'message': "✅ Профессиональная информация успешно обновлена!"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка обновления профессии для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка обновления данных: {str(e)}"
            }

    async def get_user_data_status(self, telegram_id: int):
        """Проверка статуса собранных данных пользователя с ML статусом"""
        try:
            user_profile = await get_user_profile(telegram_id)
            natal_chart = await get_user_natal_chart(telegram_id)
            psyho_matrix = await get_user_matrix(telegram_id)
            biorhythms = await get_user_biorhythms(telegram_id)

            has_basic_data = user_profile is not None
            has_natal_chart = natal_chart is not None
            has_psyho_matrix = psyho_matrix is not None
            has_biorhythms = biorhythms is not None

            # НОВОЕ: Проверка ML данных
            ml_status = await self._check_ml_data_status(telegram_id)

            return {
                'has_basic_data': has_basic_data,
                'has_natal_chart': has_natal_chart,
                'has_psyho_matrix': has_psyho_matrix,
                'has_biorhythms': has_biorhythms,
                'ml_data_status': ml_status,
                'is_complete': has_basic_data and has_natal_chart and has_psyho_matrix and has_biorhythms,
                'user_profile': user_profile
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса данных для {telegram_id}: {e}")
            return {
                'has_basic_data': False,
                'has_natal_chart': False,
                'has_psyho_matrix': False,
                'has_biorhythms': False,
                'ml_data_status': {'available': False, 'error': str(e)},
                'is_complete': False
            }

    async def _check_ml_data_status(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка статуса ML данных"""
        try:
            # Проверяем наличие сегодняшних расчетов с ML данными
            today_calc = await get_daily_calculations(telegram_id, date.today())

            if not today_calc:
                return {'available': False, 'reason': 'no_calculations'}

            ml_features = today_calc.get('ml_features', {})
            basic_insights = today_calc.get('basic_insights', [])

            has_ml_features = bool(ml_features)
            has_insights = len(basic_insights) > 0

            return {
                'available': has_ml_features and has_insights,
                'features_available': has_ml_features,
                'insights_available': has_insights,
                'features_count': len(ml_features),
                'insights_count': len(basic_insights),
                'data_freshness': await self._check_ml_data_freshness(today_calc)
            }

        except Exception as e:
            return {'available': False, 'error': str(e)}

    async def _check_ml_data_freshness(self, daily_calc: Dict) -> str:
        """Проверка свежести ML данных"""
        try:
            calc_timestamp = datetime.fromisoformat(daily_calc['calculation_timestamp'])
            age_hours = (datetime.now() - calc_timestamp).total_seconds() / 3600

            if age_hours < 6:
                return 'свежие'
            elif age_hours < 24:
                return 'нормальные'
            else:
                return 'устаревшие'
        except Exception:
            return 'неизвестно'

    async def get_user_statistics(self, telegram_id: int):
        """Получение статистики пользователя с ML метриками"""
        try:
            from backend.prediction_services import get_prediction_statistics
            from backend.biorhythm_services import get_biorhythm_statistics
            from backend.user_services import get_user_request_count

            data_status = await self.get_user_data_status(telegram_id)
            prediction_stats = await get_prediction_statistics(telegram_id)
            biorhythm_stats = await get_biorhythm_statistics(telegram_id)
            request_count = await get_user_request_count(telegram_id)

            # НОВОЕ: ML статистика
            ml_stats = await self._get_ml_statistics(telegram_id)

            return {
                'data_status': data_status,
                'prediction_stats': prediction_stats,
                'biorhythm_stats': biorhythm_stats,
                'ml_stats': ml_stats,  # НОВОЕ
                'request_count': request_count,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {
                'data_status': {},
                'prediction_stats': {},
                'biorhythm_stats': {},
                'ml_stats': {},
                'request_count': 0,
                'error': str(e)
            }

    async def _get_ml_statistics(self, telegram_id: int) -> Dict[str, Any]:
        """Получение ML статистики"""
        try:
            # Получаем историю расчетов за последнюю неделю
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            async with async_session() as session:
                from backend.database import DailyCalculations
                from sqlalchemy import and_, select

                result = await session.execute(
                    select(DailyCalculations)
                    .where(and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date >= start_date,
                        DailyCalculations.target_date <= end_date
                    ))
                    .order_by(DailyCalculations.target_date)
                )
                calculations = result.scalars().all()

            ml_data_days = 0
            total_daily_score = 0
            insights_count = 0

            for calc in calculations:
                if calc.ml_features:
                    ml_data_days += 1
                    total_daily_score += calc.ml_features.get('daily_score', 0)
                    insights_count += len(calc.basic_insights or [])

            avg_daily_score = total_daily_score / ml_data_days if ml_data_days > 0 else 0

            return {
                'ml_data_days': ml_data_days,
                'total_calculation_days': len(calculations),
                'ml_coverage': round(ml_data_days / len(calculations) * 100, 1) if calculations else 0,
                'average_daily_score': round(avg_daily_score, 3),
                'total_insights_generated': insights_count,
                'analysis_period': f"{start_date.isoformat()} - {end_date.isoformat()}"
            }

        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения ML статистики: {e}")
            return {'error': str(e)}

    async def cleanup_user_data(self, telegram_id: int):
        """Очистка данных пользователя с ML данными"""
        try:
            from backend.biorhythm_services import cleanup_old_biorhythms
            from backend.prediction_services import cleanup_old_predictions

            biorhythm_cleaned = await cleanup_old_biorhythms()
            prediction_cleaned = await cleanup_old_predictions()

            # НОВОЕ: Очистка ML кэша
            self._cleanup_user_ml_cache(telegram_id)

            logger.info(f"🧹 Очищены данные для пользователя {telegram_id}")
            return {
                'success': True,
                'biorhythm_records_cleaned': biorhythm_cleaned,
                'prediction_records_cleaned': prediction_cleaned,
                'ml_cache_cleaned': True,
                'message': f"✅ Очищено {biorhythm_cleaned} записей биоритмов и {prediction_cleaned} предсказаний"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка при очистке данных: {str(e)}"
            }

    def _cleanup_user_ml_cache(self, telegram_id: int):
        """Очистка ML кэша пользователя"""
        try:
            keys_to_remove = [key for key in self.calculation_cache.keys() if key.startswith(f"{telegram_id}_")]
            for key in keys_to_remove:
                del self.calculation_cache[key]

            ml_keys_to_remove = [key for key in self.ml_cache.keys() if key.startswith(f"{telegram_id}_")]
            for key in ml_keys_to_remove:
                del self.ml_cache[key]

            logger.info(f"🧹 Очищен ML кэш для пользователя {telegram_id}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка очистки ML кэша: {e}")

    async def validate_user_data(self, telegram_id: int):
        """Проверка корректности данных пользователя с ML валидацией"""
        try:
            from backend.prediction_services import validate_prediction_data

            data_status = await self.get_user_data_status(telegram_id)
            prediction_valid = await validate_prediction_data(telegram_id)

            issues = []

            if not data_status['has_basic_data']:
                issues.append("Отсутствуют основные данные пользователя")
            if not data_status['has_natal_chart']:
                issues.append("Отсутствует натальная карта")
            if not data_status['has_psyho_matrix']:
                issues.append("Отсутствует психоматрица")
            if not data_status['has_biorhythms']:
                issues.append("Отсутствуют данные биоритмов")
            if not prediction_valid:
                issues.append("Некорректные данные предсказаний")

            # НОВОЕ: Проверка ML данных
            ml_status = data_status.get('ml_data_status', {})
            if not ml_status.get('available', False):
                issues.append("Отсутствуют или устарели ML данные")

            return {
                'is_valid': len(issues) == 0,
                'issues': issues,
                'data_status': data_status,
                'prediction_valid': prediction_valid,
                'ml_data_available': ml_status.get('available', False)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
            return {
                'is_valid': False,
                'issues': [f"Ошибка валидации: {str(e)}"],
                'data_status': {},
                'prediction_valid': False,
                'ml_data_available': False
            }

    async def regenerate_ml_data(self, telegram_id: int, target_date: date = None) -> Dict[str, Any]:
        """Принудительная регенерация ML данных для пользователя"""
        try:
            from backend.prediction_services import regenerate_ml_data as regenerate_ml

            if target_date is None:
                target_date = date.today()

            result = await regenerate_ml(telegram_id, target_date)

            if result.get('success'):
                # Очищаем кэш для этой даты
                cache_key = f"{telegram_id}_{target_date}"
                if cache_key in self.calculation_cache:
                    del self.calculation_cache[cache_key]

                logger.info(f"✅ ML данные перегенерированы для {telegram_id} на {target_date}")
            else:
                logger.warning(f"⚠️ Регенерация ML данных завершена с ошибками: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка регенерации ML данных для {telegram_id}: {e}")
            return {'success': False, 'error': str(e)}

    def clear_cache(self):
        """Очистка внутреннего кэша"""
        self.calculation_cache.clear()
        self.ml_cache.clear()
        logger.info("✅ Кэш помощника полностью очищен")

    async def get_system_health(self) -> Dict[str, Any]:
        """Проверка здоровья системы помощника"""
        try:
            # Проверка подключения к БД
            from backend.db_connection import check_db_connection
            db_healthy = await check_db_connection()

            # Проверка ML оркестратора
            ml_healthy = await ml_orchestrator.health_check()

            # Статистика кэша
            cache_stats = {
                'calculation_cache_size': len(self.calculation_cache),
                'ml_cache_size': len(self.ml_cache),
                'cache_ttl': self.cache_ttl,
                'ml_cache_ttl': self.ml_cache_ttl
            }

            overall_health = 'healthy' if db_healthy and ml_healthy.get('status') == 'healthy' else 'degraded'

            return {
                'status': overall_health,
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': {'status': 'healthy' if db_healthy else 'unhealthy'},
                    'ml_orchestrator': ml_healthy,
                    'cache_system': {'status': 'healthy', **cache_stats}
                },
                'recommendations': self._generate_health_recommendations(db_healthy, ml_healthy)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья системы: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _generate_health_recommendations(self, db_healthy: bool, ml_health: Dict) -> List[str]:
        """Генерация рекомендаций по здоровью системы"""
        recommendations = []

        if not db_healthy:
            recommendations.append("Проверить подключение к базе данных")

        if ml_health.get('status') != 'healthy':
            recommendations.append("Проверить работу ML оркестратора")

        if len(self.calculation_cache) > 1000:
            recommendations.append("Рассмотреть очистку кэша для оптимизации памяти")

        if not recommendations:
            recommendations.append("Все системы работают нормально")

        return recommendations


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()