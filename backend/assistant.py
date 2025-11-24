from backend.user_services import create_or_update_user, get_user_profile, update_user_profession, \
    increment_request_count
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_user_predictions, \
    format_data_for_user, get_daily_calculations, save_daily_calculations
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
import math

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления расчетными данными (без AI логики)"""

    def __init__(self):
        self.calculation_cache = {}

    def _calculate_user_age(self, birth_date: date) -> int:
        """Расчет возраста пользователя"""
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
        """Описание уровня энергии"""
        if percentage >= 90:
            return {"level": "очень высокий", "description": "идеально для сложных задач и важных решений"}
        elif percentage >= 75:
            return {"level": "высокий", "description": "отлично для продуктивной работы"}
        elif percentage >= 60:
            return {"level": "хороший", "description": "подходит для активной деятельности"}
        elif percentage >= 40:
            return {"level": "средний", "description": "стабильно для рутинных задач"}
        elif percentage >= 20:
            return {"level": "низкий", "description": "требует бережного отношения к силам"}
        else:
            return {"level": "критически низкий", "description": "необходим отдых и восстановление"}

    def _get_physical_recommendation(self, percentage: float) -> str:
        """Рекомендации по физической активности"""
        if percentage >= 90:
            return "идеальное время для спорта и физических нагрузок"
        elif percentage >= 70:
            return "хороший день для активной работы и движения"
        elif percentage >= 50:
            return "подходит для умеренной физической активности"
        elif percentage >= 30:
            return "берегите силы, избегайте перегрузок"
        else:
            return "требуется отдых и восстановление физических сил"

    def _get_emotional_recommendation(self, percentage: float) -> str:
        """Рекомендации по эмоциональному состоянию"""
        if percentage >= 90:
            return "отличное настроение для общения и новых знакомств"
        elif percentage >= 70:
            return "эмоционально стабильный день"
        elif percentage >= 50:
            return "сохраняйте эмоциональное равновесие"
        elif percentage >= 30:
            return "будьте осторожны в общении, контролируйте эмоции"
        else:
            return "критический эмоциональный фон - избегайте конфликтов и стрессов"

    def _get_intellectual_recommendation(self, percentage: float) -> str:
        """Рекомендации по интеллектуальной деятельности"""
        if percentage >= 90:
            return "пик умственных способностей - время для сложных задач и обучения"
        elif percentage >= 70:
            return "отличные когнитивные способности для анализа и планирования"
        elif percentage >= 50:
            return "стабильная умственная активность"
        elif percentage >= 30:
            return "сосредоточьтесь на простых задачах, избегайте сложного анализа"
        else:
            return "умственное истощение - время для отдыха и простых действий"

    def _get_season(self, target_date: date) -> str:
        """Определение сезона для контекста"""
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
        """
        try:
            daily_calculations = prediction.get('daily_calculations', {})
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            astro_data = daily_calculations.get('astro_data', {})
            natal_chart = prediction.get('natal_chart', {})
            psyho_matrix = prediction.get('psyho_matrix', {})

            # Базовые данные пользователя
            user_age = self._calculate_user_age(user_profile.get('birth_date'))
            experience_level = self._estimate_experience_level(user_age, user_profile.get('profession'))

            # Оптимизированные данные для внешнего API
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
                    'gender': user_profile.get('gender', 'не указан')
                },

                # Энергетическое состояние
                'energy_state': {
                    'overall_energy': biorhythm_data.get('overall_energy', {}),
                    'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                    'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                    'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {})
                },

                # Астрологические данные
                'astro_data': {
                    'aspects_count': astro_data.get('aspects_count', 0),
                    'strong_aspects_count': astro_data.get('strong_aspects_count', 0),
                    'retrograde_planets': astro_data.get('retrograde_planets', []),
                    'key_aspects': astro_data.get('key_aspects', [])[:3]  # Только топ-3
                },

                # Статические данные
                'static_profile': {
                    'natal_chart_summary': {
                        'planets_count': len(natal_chart.get('planets', {})),
                        'dominant_element': self._get_dominant_element(natal_chart),
                        'ascendant': natal_chart.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
                    },
                    'psyho_matrix_summary': {
                        'life_path_number': psyho_matrix.get('basic_numbers', {}).get('first'),
                        'matrix_complexity': self._calculate_matrix_complexity(psyho_matrix)
                    }
                },

                # Контекст дня
                'daily_context': {
                    'season': self._get_season(target_date),
                    'day_of_week': target_date.strftime('%A'),
                    'lunar_phase': self._get_lunar_phase(target_date),
                    'is_weekend': target_date.weekday() >= 5
                },

                # Мета-информация
                'calculation_meta': {
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'calculation_timestamp': datetime.now().isoformat(),
                    'data_version': '1.0'
                }
            }

            logger.info(f"✅ Данные подготовлены для пользователя {telegram_id} на {target_date}")
            return prepared_data

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки данных: {e}")
            return self._prepare_data_fallback(user_profile, target_date)

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

    def _prepare_data_fallback(self, user_profile: dict, target_date: date) -> dict:
        """Резервная подготовка данных при ошибках"""
        return {
            'user_context': {
                'profession': user_profile.get('profession', 'не указана'),
                'position': user_profile.get('job_position', 'не указана'),
                'current_city': user_profile.get('current_city', 'не указан')
            },
            'energy_state': {},
            'astro_data': {},
            'static_profile': {},
            'daily_context': {
                'target_date': target_date.strftime('%Y-%m-%d')
            },
            'calculation_meta': {
                'fallback_mode': True,
                'error': 'Данные временно недоступны'
            }
        }

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None, gender: str = None):
        """Сбор и сохранение всех данных пользователя"""
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

                    await session.commit()

                    return {
                        'success': True,
                        'message': "✅ Все данные успешно собраны и сохранены!",
                        'data_collected': {
                            'user_profile': True,
                            'natal_chart': True,
                            'psyho_matrix': True,
                            'biorhythms': True
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
        Получение расчетных данных на выбранную дату (без AI рекомендаций)
        """
        try:
            logger.info(f"📅 Формирование данных на {target_date} для {telegram_id}")

            # Увеличиваем счетчик обращений
            await increment_request_count(telegram_id)
            logger.info(f"📈 Счетчик обращений увеличен для {telegram_id}")

            # Проверяем что дата не в прошлом
            if target_date < date.today():
                return {
                    'success': False,
                    'message': "❌ Нельзя получить данные для прошедших дат"
                }

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

            # 2. Структурированные данные для внешнего API
            structured_data = self._prepare_calculation_data(telegram_id, user_profile, prediction, target_date)

            result = {
                'success': True,
                'date': target_date.isoformat(),
                'user_data': user_data,  # Для бота
                'structured_data': structured_data,  # Для внешнего API
                'prediction_data': prediction,  # Полные данные
                'user_profile': user_profile
            }

            logger.info(f"✅ Данные сформированы для {telegram_id} на {target_date}")
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
        Оптимизирован для проекта Assistant
        """
        try:
            # Проверяем кэш
            cache_key = f"{telegram_id}_{target_date}"
            if cache_key in self.calculation_cache:
                cached_data = self.calculation_cache[cache_key]
                # Проверяем актуальность кэша (5 минут)
                if datetime.now().timestamp() - cached_data['timestamp'] < 300:
                    logger.info(f"✅ Использованы кэшированные данные для {telegram_id}")
                    return cached_data['data']

            # Получаем основные данные
            result = await self.get_recommendations(telegram_id, target_date)

            if not result['success']:
                return {
                    'success': False,
                    'error': result['message'],
                    'timestamp': datetime.now().isoformat()
                }

            # Формируем оптимизированный пакет
            calculation_package = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': result['structured_data'],
                'raw_data_available': True,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'astra_calculations'
            }

            # Сохраняем в кэш
            self.calculation_cache[cache_key] = {
                'data': calculation_package,
                'timestamp': datetime.now().timestamp()
            }

            logger.info(f"✅ Пакет расчетов подготовлен для {telegram_id}")
            return calculation_package

        except Exception as e:
            logger.error(f"❌ Ошибка формирования пакета расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_todays_recommendations(self, telegram_id: int):
        """Получение данных на сегодня"""
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
        """Обновление профессиональной информации"""
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

            logger.info(f"✅ Профессиональные данные обновлены для {telegram_id}")
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
        """Проверка статуса собранных данных пользователя"""
        try:
            user_profile = await get_user_profile(telegram_id)
            natal_chart = await get_user_natal_chart(telegram_id)
            psyho_matrix = await get_user_matrix(telegram_id)
            biorhythms = await get_user_biorhythms(telegram_id)

            has_basic_data = user_profile is not None
            has_natal_chart = natal_chart is not None
            has_psyho_matrix = psyho_matrix is not None
            has_biorhythms = biorhythms is not None

            return {
                'has_basic_data': has_basic_data,
                'has_natal_chart': has_natal_chart,
                'has_psyho_matrix': has_psyho_matrix,
                'has_biorhythms': has_biorhythms,
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
                'is_complete': False
            }

    async def get_user_statistics(self, telegram_id: int):
        """Получение статистики пользователя"""
        try:
            from backend.prediction_services import get_prediction_statistics
            from backend.biorhythm_services import get_biorhythm_statistics
            from backend.user_services import get_user_request_count

            data_status = await self.get_user_data_status(telegram_id)
            prediction_stats = await get_prediction_statistics(telegram_id)
            biorhythm_stats = await get_biorhythm_statistics(telegram_id)
            request_count = await get_user_request_count(telegram_id)

            return {
                'data_status': data_status,
                'prediction_stats': prediction_stats,
                'biorhythm_stats': biorhythm_stats,
                'request_count': request_count,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {
                'data_status': {},
                'prediction_stats': {},
                'biorhythm_stats': {},
                'request_count': 0,
                'error': str(e)
            }

    async def cleanup_user_data(self, telegram_id: int):
        """Очистка данных пользователя"""
        try:
            from backend.biorhythm_services import cleanup_old_biorhythms
            from backend.prediction_services import cleanup_old_predictions

            biorhythm_cleaned = await cleanup_old_biorhythms()
            prediction_cleaned = await cleanup_old_predictions()

            logger.info(f"🧹 Очищены данные для пользователя {telegram_id}")
            return {
                'success': True,
                'biorhythm_records_cleaned': biorhythm_cleaned,
                'prediction_records_cleaned': prediction_cleaned,
                'message': f"✅ Очищено {biorhythm_cleaned} записей биоритмов и {prediction_cleaned} предсказаний"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка при очистке данных: {str(e)}"
            }

    async def validate_user_data(self, telegram_id: int):
        """Проверка корректности данных пользователя"""
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

            return {
                'is_valid': len(issues) == 0,
                'issues': issues,
                'data_status': data_status,
                'prediction_valid': prediction_valid
            }

        except Exception as e:
            logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
            return {
                'is_valid': False,
                'issues': [f"Ошибка валидации: {str(e)}"],
                'data_status': {},
                'prediction_valid': False
            }

    def clear_cache(self):
        """Очистка внутреннего кэша"""
        self.calculation_cache.clear()
        logger.info("✅ Кэш помощника очищен")


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()