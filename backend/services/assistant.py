from backend.services.user_services import create_or_update_user, get_user_profile, update_user_profession, \
    increment_request_count
from backend.astrological.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.psychology.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.astrological.prediction_services import generate_and_save_prediction, get_user_predictions, \
    format_data_for_user, format_data_for_model
from backend.biorhythms.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления всеми данными с AI интеграцией"""

    def __init__(self):
        self.ai_engine = None
        self._ai_engine_initialized = False

    async def _initialize_ai_engine(self):
        """Ленивая инициализация AI движка"""
        if not self._ai_engine_initialized:
            try:
                from backend.models.ai_engine import ai_engine
                self.ai_engine = ai_engine
                self._ai_engine_initialized = True
                logger.info("✅ AI движок инициализирован")
            except ImportError as e:
                logger.warning(f"⚠️ AI движок недоступен: {e}")
                self._ai_engine_initialized = True

    def _debug_print_complete_ai_data(self, telegram_id: int, user_profile: dict, prediction: dict,
                                      target_date: date, prepared_data: dict):
        """
        ПОЛНЫЙ вывод всех данных, отправляемых в AI модель
        """
        print("\n" + "🎯" * 50)
        print("🤖 ПОЛНЫЕ ДАННЫЕ ДЛЯ AI МОДЕЛИ")
        print("🎯" * 50)

        # 1. ОСНОВНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
        print(f"\n📋 ОСНОВНАЯ ИНФОРМАЦИЯ:")
        print(f"   👤 ID: {telegram_id}")
        print(f"   📅 Дата расчета: {target_date.strftime('%d.%m.%Y')}")
        print(f"   🎯 Возраст: {self._calculate_user_age(user_profile.get('birth_date'))} лет")
        print(f"   👨‍💼 Профессия: {user_profile.get('profession', 'не указана')}")
        print(f"   💼 Должность: {user_profile.get('job_position', 'не указана')}")
        print(f"   🏙️ Город: {user_profile.get('current_city', 'не указан')}")
        print(f"   🏠 Родной город: {user_profile.get('birth_city', 'не указан')}")
        print(f"   ⚧ Пол: {user_profile.get('gender', 'не указан')}")
        print(f"   📊 Запросов: {user_profile.get('request_count', 0)}")

        # 2. ДАННЫЕ ИЗ НАТАЛЬНОЙ КАРТЫ
        natal_chart = prediction.get('natal_chart', {})
        if natal_chart:
            print(f"\n🌟 НАТАЛЬНАЯ КАРТА:")
            metadata = natal_chart.get('metadata', {})
            location = metadata.get('location', {})
            print(f"   📍 Место рождения: {location.get('city', 'неизвестно')}")
            print(f"   📅 Дата рождения: {user_profile.get('birth_date')}")
            print(f"   ⏰ Время рождения: {user_profile.get('birth_time')}")

            # Планеты
            planets = natal_chart.get('planets', {})
            print(f"   🪐 Планет рассчитано: {len(planets)}")

            # Покажем основные планеты
            main_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
            for planet in main_planets:
                if planet in planets:
                    planet_data = planets[planet]
                    print(
                        f"     {planet}: {planet_data.get('sign', 'N/A')} ({planet_data.get('position_in_sign', 0):.1f}°)")

            # Дома
            houses = natal_chart.get('houses', {})
            print(f"   🏠 Домов рассчитано: {len(houses)}")

            # Аспекты
            aspects = natal_chart.get('aspects', [])
            print(f"   🔗 Аспектов в натале: {len(aspects)}")

            # ML фичи
            ml_features = natal_chart.get('ml_features', {})
            if ml_features:
                element_balance = ml_features.get('element_balance', {})
                print(f"   ⚖️ Баланс стихий: {element_balance}")

        # 3. ПСИХОМАТРИЦА
        psyho_matrix = prediction.get('psyho_matrix', {})
        if psyho_matrix:
            print(f"\n🔢 ПСИХОМАТРИЦА:")
            basic_numbers = psyho_matrix.get('basic_numbers', {})
            print(f"   🔸 Первое число: {basic_numbers.get('first', 'N/A')}")
            print(f"   🔸 Второе число: {basic_numbers.get('second', 'N/A')}")
            print(f"   🔸 Третье число: {basic_numbers.get('third', 'N/A')}")
            print(f"   🔸 Четвертое число: {basic_numbers.get('fourth', 'N/A')}")

            matrix_numbers = psyho_matrix.get('pythagoras_matrix', {})
            print(f"   🧮 Матрица Пифагора: {dict(list(matrix_numbers.items())[:5])}...")

        # 4. ЕЖЕДНЕВНЫЕ РАСЧЕТЫ
        daily_calculations = prediction.get('daily_calculations', {})
        if daily_calculations:
            print(f"\n📊 ЕЖЕДНЕВНЫЕ РАСЧЕТЫ:")

            # Биоритмы
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            if biorhythm_data:
                overall_energy = biorhythm_data.get('overall_energy', {})
                cycles = biorhythm_data.get('cycles', {})

                print(f"   ⚡ Общая энергия: {overall_energy.get('percentage', 0):.1f}%")
                print(f"   💪 Физический: {cycles.get('physical', {}).get('percentage', 0):.1f}%")
                print(f"   😊 Эмоциональный: {cycles.get('emotional', {}).get('percentage', 0):.1f}%")
                print(f"   🧠 Интеллектуальный: {cycles.get('intellectual', {}).get('percentage', 0):.1f}%")
                print(f"   🔮 Интуитивный: {cycles.get('intuitive', {}).get('percentage', 0):.1f}%")

                critical_days = biorhythm_data.get('critical_days', [])
                peak_days = biorhythm_data.get('peak_days', [])
                print(f"   ⚠️ Критических дней: {len(critical_days)}")
                print(f"   🚀 Пиковых дней: {len(peak_days)}")

            # Астрологические данные
            astro_data = daily_calculations.get('astro_data', {})
            if astro_data:
                print(f"   🌟 Аспектов сегодня: {astro_data.get('aspects_count', 0)}")
                print(f"   💥 Сильных аспектов: {astro_data.get('strong_aspects_count', 0)}")

                retrograde_planets = astro_data.get('retrograde_planets', [])
                print(f"   🔄 Ретроградных планет: {len(retrograde_planets)}")
                if retrograde_planets:
                    print(f"     📍 {', '.join(retrograde_planets)}")

                key_aspects = astro_data.get('key_aspects', [])
                print(f"   📈 Ключевых аспектов: {len(key_aspects)}")

                # Покажем топ-3 самых сильных аспекта
                strong_aspects = sorted(key_aspects, key=lambda x: x.get('strength', 0), reverse=True)[:3]
                for i, aspect in enumerate(strong_aspects, 1):
                    transit = aspect.get('transit_planet', '')
                    natal = aspect.get('natal_planet', '')
                    aspect_type = aspect.get('aspect', '')
                    strength = aspect.get('strength', 0)
                    orb = aspect.get('orb', 0)
                    print(f"     {i}. {transit}→{natal} ({aspect_type}) - сила: {strength:.2f}, орб: {orb:.2f}°")

        # 5. ОПТИМИЗИРОВАННЫЕ ДАННЫЕ ДЛЯ AI
        print(f"\n🎯 ОПТИМИЗИРОВАННЫЕ ДАННЫЕ ДЛЯ AI:")
        print(f"   🎯 Сезон: {prepared_data.get('season', 'неизвестно')}")
        print(f"   📅 День недели: {prepared_data.get('day_of_week', 'неизвестно')}")

        # Энергетическое состояние
        energy_state = prepared_data.get('energy_state', {})
        print(f"   ⚡ Общая энергия: {energy_state.get('overall_energy_percentage', 0)}%")
        print(f"   📊 Уровень энергии: {energy_state.get('overall_energy_level', 'неизвестно')}")

        # Детали биоритмов
        physical = energy_state.get('physical', {})
        emotional = energy_state.get('emotional', {})
        intellectual = energy_state.get('intellectual', {})

        print(
            f"   💪 Физический: {physical.get('percentage', 0)}% ({physical.get('phase', 'нейтральная')}) - {physical.get('trend', 'стабильно')}")
        print(
            f"   😊 Эмоциональный: {emotional.get('percentage', 0)}% ({emotional.get('phase', 'нейтральная')}) - {emotional.get('trend', 'стабильно')}")
        print(
            f"   🧠 Интеллектуальный: {intellectual.get('percentage', 0)}% ({intellectual.get('phase', 'нейтральная')}) - {intellectual.get('trend', 'стабильно')}")

        # Астрологические влияния
        astro_influences = prepared_data.get('astro_influences', {})
        print(f"   🌟 Всего аспектов: {astro_influences.get('total_aspects', 0)}")
        print(f"   💥 Сильных аспектов: {astro_influences.get('strong_aspects', 0)}")
        print(f"   🔄 Ретроградных планет: {astro_influences.get('retrograde_planets', 0)}")
        print(f"   📈 Интенсивность аспектов: {astro_influences.get('aspect_intensity', 'неизвестно')}")

        # Ключевые аспекты
        key_aspects = prepared_data.get('key_aspects', [])
        print(f"   🔑 Ключевых аспектов для AI: {len(key_aspects)}")
        for i, aspect in enumerate(key_aspects[:3], 1):
            print(f"     {i}. {aspect}")

        # 6. СТАТИСТИКА ДАННЫХ
        print(f"\n📈 СТАТИСТИКА ДАННЫХ:")
        total_data_points = 0

        # Считаем общее количество данных
        if natal_chart:
            total_data_points += len(natal_chart.get('planets', {}))
            total_data_points += len(natal_chart.get('houses', {}))
            total_data_points += len(natal_chart.get('aspects', []))

        if psyho_matrix:
            total_data_points += 4  # основные числа
            total_data_points += len(psyho_matrix.get('pythagoras_matrix', {}))

        if daily_calculations:
            total_data_points += 5  # биоритмы
            total_data_points += len(daily_calculations.get('astro_data', {}).get('key_aspects', []))

        print(f"   📊 Всего точек данных: {total_data_points}")
        print(f"   🎯 Дата актуальности: {prediction.get('calculation_date', 'неизвестно')}")

        # 7. JSON ПРЕДСТАВЛЕНИЕ ДЛЯ ОТЛАДКИ
        print(f"\n📋 JSON СТРУКТУРА ОПТИМИЗИРОВАННЫХ ДАННЫХ:")
        print("-" * 40)
        try:
            # Безопасное преобразование для отладки
            debug_data = {
                'user_context': prepared_data.get('user_profile', {}),
                'energy_state_summary': {
                    'overall_energy': energy_state.get('overall_energy_percentage'),
                    'physical': physical.get('percentage'),
                    'emotional': emotional.get('percentage'),
                    'intellectual': intellectual.get('percentage')
                },
                'astro_summary': {
                    'total_aspects': astro_influences.get('total_aspects'),
                    'strong_aspects': astro_influences.get('strong_aspects'),
                    'retrograde_planets': astro_influences.get('retrograde_planets'),
                    'intensity': astro_influences.get('aspect_intensity')
                },
                'key_aspects_count': len(key_aspects),
                'context': {
                    'season': prepared_data.get('season'),
                    'day_of_week': prepared_data.get('day_of_week'),
                    'target_date': prepared_data.get('target_date')
                }
            }
            print(json.dumps(debug_data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Ошибка форматирования JSON: {e}")

        print("-" * 40)
        print("✅ ВСЕ ДАННЫЕ ПОДГОТОВЛЕНЫ ДЛЯ AI МОДЕЛИ")
        print("🎯" * 50 + "\n")

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None, gender: str = None):
        """Сбор и сохранение всех данных пользователя"""
        try:
            logger.info(f"🔄 Начало сбора данных для пользователя {telegram_id}")

            # Используем транзакцию для атомарности операций
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

    async def get_recommendations(self, telegram_id: int, target_date: date, include_ai: bool = False):
        """
        Получение данных на выбранную дату
        include_ai: если False - возвращает только расчеты (мгновенно)
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

            # Получаем профиль пользователя для модели
            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {
                    'success': False,
                    'message': "❌ Профиль пользователя не найден"
                }

            # 1. Данные для пользователя (через бот)
            user_data = await format_data_for_user(prediction)

            result = {
                'success': True,
                'date': target_date.isoformat(),
                'user_data': user_data,
                'prediction_data': prediction,  # Данные для AI
                'user_profile': user_profile  # Профиль для AI
            }

            # 2. AI рекомендации ТОЛЬКО если явно запрошены
            if include_ai:
                print(f"\n🚀 ЗАПУСК AI ОБРАБОТКИ")
                print(f"   👤 Пользователь: {telegram_id}")
                print(f"   📅 Дата: {target_date.strftime('%d.%m.%Y')}")
                print(f"   💼 Профессия: {user_profile.get('profession', 'не указана')}")
                print(f"   🏙️ Город: {user_profile.get('current_city', 'не указан')}")

                logger.info(f"🤖 Включена генерация AI рекомендаций для {telegram_id}")
                ai_result = await self._get_ai_recommendations(telegram_id, user_profile, prediction, target_date)
                result.update({
                    'ai_recommendations': ai_result.get('recommendations', {}),
                    'ai_success': ai_result.get('success', False),
                    'is_fallback': ai_result.get('is_fallback', False),
                    'ai_error': ai_result.get('error')
                })
            else:
                logger.info(f"⚡ AI рекомендации отключены для быстрого показа данных {telegram_id}")

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить данные на выбранную дату: {str(e)}"
            }

    async def get_ai_recommendations_async(self, telegram_id: int, target_date: date,
                                           prediction_data: dict, user_profile: dict):
        """
        Асинхронное получение AI рекомендаций (для использования в handlers)
        """
        try:
            print(f"\n🎯 ЗАПУСК AI ОБРАБОТКИ ДЛЯ ПОЛЬЗОВАТЕЛЯ {telegram_id}")
            print(f"📅 Дата: {target_date.strftime('%d.%m.%Y')}")

            logger.info(f"🔄 Асинхронная генерация AI рекомендаций для {telegram_id}")

            # Ленивая инициализация AI движка
            await self._initialize_ai_engine()

            if not self.ai_engine:
                return self._get_fallback_ai_recommendations("AI движок недоступен")

            # Проверяем доступность AI сервиса
            health_check = await self.ai_engine.test_connection()
            if not health_check.get('ollama_available', False):
                return self._get_fallback_ai_recommendations("Ollama сервис недоступен")

            if not health_check.get('model_loaded', False):
                return self._get_fallback_ai_recommendations("AI модель не загружена")

            # Подготавливаем ОПТИМИЗИРОВАННЫЕ данные для AI
            prepared_data = self._prepare_optimized_ai_data(telegram_id, user_profile, prediction_data, target_date)

            # Генерируем рекомендации с таймаутом
            try:
                ai_result = await asyncio.wait_for(
                    self.ai_engine.generate_recommendations(prepared_data),
                    timeout=170  # 170 секунд для AI обработки
                )

                if ai_result.get('success', False):
                    logger.info(f"✅ AI рекомендации сгенерированы для {telegram_id}")
                    return ai_result
                else:
                    logger.warning(f"⚠️ AI не смог сгенерировать рекомендации: {ai_result.get('error')}")
                    return self._get_fallback_ai_recommendations(ai_result.get('error', 'Unknown AI error'))

            except asyncio.TimeoutError:
                logger.warning(f"⏰ Таймаут AI обработки для {telegram_id}")
                return self._get_fallback_ai_recommendations("Таймаут генерации рекомендаций")

            except Exception as e:
                logger.error(f"❌ Ошибка AI обработки для {telegram_id}: {e}")
                return self._get_fallback_ai_recommendations(str(e))

        except Exception as e:
            logger.error(f"❌ Критическая ошибка AI системы для {telegram_id}: {e}")
            return self._get_fallback_ai_recommendations(str(e))

    async def _get_ai_recommendations(self, telegram_id: int, user_profile: dict, prediction: dict, target_date: date):
        """Получение AI рекомендаций (синхронная версия)"""
        return await self.get_ai_recommendations_async(telegram_id, target_date, prediction, user_profile)

    def _prepare_optimized_ai_data(self, telegram_id: int, user_profile: dict, prediction: dict,
                                   target_date: date) -> dict:
        """
        ОПТИМИЗИРОВАННАЯ подготовка данных для AI модели
        Убраны избыточные поля, добавлены полезные контекстные данные
        """
        try:
            daily_calculations = prediction.get('daily_calculations', {})
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            astro_data = daily_calculations.get('astro_data', {})

            # Рассчитываем возраст пользователя для контекста
            user_age = self._calculate_user_age(user_profile.get('birth_date'))

            # Извлекаем ключевые сильные аспекты
            strong_aspects = self._extract_key_strong_aspects(astro_data)

            # Оптимизируем данные биоритмов
            optimized_biorhythms = self._optimize_biorhythm_data(biorhythm_data)

            # Оптимизируем астрологические данные
            optimized_astro = self._optimize_astro_data(astro_data)

            prepared_data = {
                'user_profile': {
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'current_city': user_profile.get('current_city', 'не указан'),
                    'age': user_age
                },
                'energy_state': optimized_biorhythms,
                'astro_influences': optimized_astro,
                'key_aspects': strong_aspects,
                'target_date': target_date.strftime('%d.%m.%Y'),  # Более читаемый формат
                'season': self._get_season(target_date),  # Добавляем сезон для контекста
                'day_of_week': target_date.strftime('%A')  # День недели для контекста
            }

            # 🔴 ДОБАВЛЕНО: ПОЛНЫЙ ВЫВОД ВСЕХ ДАННЫХ
            self._debug_print_complete_ai_data(telegram_id, user_profile, prediction, target_date, prepared_data)

            return prepared_data

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки оптимизированных данных для AI: {e}")
            # Fallback на старую структуру при ошибке
            return self._prepare_ai_data_fallback(user_profile, prediction, target_date)

    def _calculate_user_age(self, birth_date: date) -> int:
        """Расчет возраста пользователя"""
        try:
            if not birth_date:
                return 0
            today = date.today()
            age = today.year - birth_date.year
            # Корректируем если день рождения еще не наступил в этом году
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета возраста: {e}")
            return 0

    def _extract_key_strong_aspects(self, astro_data: dict) -> List[str]:
        """Извлечение ключевых сильных аспектов для AI"""
        try:
            key_aspects = astro_data.get('key_aspects', [])
            strong_aspects = []

            # Берем только топ-5 самых сильных аспектов
            sorted_aspects = sorted(key_aspects, key=lambda x: x.get('strength', 0), reverse=True)[:5]

            for aspect in sorted_aspects:
                if aspect.get('strength', 0) > 0.6:  # Более строгий порог для AI
                    transit = aspect.get('transit_planet', '')
                    natal = aspect.get('natal_planet', '')
                    aspect_type = aspect.get('aspect', '')

                    if transit and natal and aspect_type:
                        # Упрощенные названия для AI
                        strong_aspects.append(f"{transit}-{natal}-{aspect_type}")

            return strong_aspects

        except Exception as e:
            logger.warning(f"⚠️ Ошибка извлечения сильных аспектов для AI: {e}")
            return []

    def _optimize_biorhythm_data(self, biorhythm_data: dict) -> Dict[str, Any]:
        """Оптимизация данных биоритмов для AI"""
        try:
            overall = biorhythm_data.get('overall_energy', {})
            cycles = biorhythm_data.get('cycles', {})

            return {
                'overall_energy_percentage': overall.get('percentage', 0),
                'overall_energy_level': overall.get('level', 'средний'),
                'physical': {
                    'percentage': cycles.get('physical', {}).get('percentage', 0),
                    'phase': cycles.get('physical', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('physical', {}).get('trend', 'стабильно')
                },
                'emotional': {
                    'percentage': cycles.get('emotional', {}).get('percentage', 0),
                    'phase': cycles.get('emotional', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('emotional', {}).get('trend', 'стабильно')
                },
                'intellectual': {
                    'percentage': cycles.get('intellectual', {}).get('percentage', 0),
                    'phase': cycles.get('intellectual', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('intellectual', {}).get('trend', 'стабильно')
                }
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка оптимизации данных биоритмов: {e}")
            return {}

    def _optimize_astro_data(self, astro_data: dict) -> Dict[str, Any]:
        """Оптимизация астрологических данных для AI"""
        try:
            return {
                'total_aspects': astro_data.get('aspects_count', 0),
                'strong_aspects': astro_data.get('strong_aspects_count', 0),
                'retrograde_planets': len(astro_data.get('retrograde_planets', [])),
                'aspect_intensity': self._calculate_aspect_intensity(astro_data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка оптимизации астроданных: {e}")
            return {}

    def _calculate_aspect_intensity(self, astro_data: dict) -> str:
        """Расчет интенсивности аспектов для AI"""
        try:
            strong_count = astro_data.get('strong_aspects_count', 0)
            total_count = astro_data.get('aspects_count', 0)

            if total_count == 0:
                return 'низкая'

            intensity_ratio = strong_count / total_count

            if intensity_ratio > 0.7:
                return 'очень высокая'
            elif intensity_ratio > 0.5:
                return 'высокая'
            elif intensity_ratio > 0.3:
                return 'средняя'
            else:
                return 'низкая'

        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета интенсивности аспектов: {e}")
            return 'неизвестно'

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

    def _prepare_ai_data_fallback(self, user_profile: dict, prediction: dict, target_date: date) -> dict:
        """Fallback подготовка данных (старая структура)"""
        try:
            daily_calculations = prediction.get('daily_calculations', {})

            return {
                'user_context': {
                    'profession': user_profile.get('profession'),
                    'position': user_profile.get('job_position'),
                    'current_city': user_profile.get('current_city')
                },
                'energy_state': daily_calculations.get('biorhythm_data', {}),
                'astro_highlights': daily_calculations.get('astro_data', {}),
                'target_date': target_date.isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Критическая ошибка fallback подготовки данных: {e}")
            return {
                'user_context': {'profession': 'неизвестно'},
                'energy_state': {},
                'astro_highlights': {},
                'target_date': target_date.isoformat()
            }

    def _get_fallback_ai_recommendations(self, error: str) -> dict:
        """Резервные рекомендации при недоступности AI"""
        logger.info(f"🔄 Используются резервные рекомендации: {error}")

        return {
            'success': False,
            'is_fallback': True,
            'error': error,
            'recommendations': {
                'professional': [
                    "Сфокусируйтесь на текущих задачах",
                    "Планируйте работу по приоритетам"
                ],
                'personal_effectiveness': [
                    "Соблюдайте баланс работы и отдыха",
                    "Делайте регулярные перерывы"
                ],
                'emotional': [
                    "Сохраняйте эмоциональное равновесие",
                    "Избегайте импульсивных решений"
                ],
                'daily_focus': [
                    "Баланс между продуктивностью и восстановлением"
                ]
            }
        }

    async def get_todays_recommendations(self, telegram_id: int, include_ai: bool = False):
        """Получение данных на сегодня (для обратной совместимости)"""
        return await self.get_recommendations(telegram_id, date.today(), include_ai)

    async def get_tomorrows_recommendations(self, telegram_id: int, include_ai: bool = False):
        """Получение данных на завтра"""
        tomorrow = date.today() + timedelta(days=1)
        return await self.get_recommendations(telegram_id, tomorrow, include_ai)

    async def get_date_recommendations(self, telegram_id: int, target_date: date, include_ai: bool = False):
        """Получение данных на выбранную дату (alias для единообразия)"""
        return await self.get_recommendations(telegram_id, target_date, include_ai)

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None, gender: str = None):
        """Обновление профессиональной информации"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            # Обновляем город проживания и пол
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
            from backend.astrological.prediction_services import get_prediction_statistics
            from backend.biorhythms.biorhythm_services import get_biorhythm_statistics
            from backend.services.user_services import get_user_request_count

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
        """Очистка данных пользователя (для администрирования)"""
        try:
            from backend.biorhythms.biorhythm_services import cleanup_old_biorhythms
            from backend.astrological.prediction_services import cleanup_old_predictions

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
            from backend.astrological.prediction_services import validate_prediction_data

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

    async def test_ai_connection(self):
        """Тестирование подключения к AI сервису"""
        try:
            await self._initialize_ai_engine()

            if not self.ai_engine:
                return {
                    'available': False,
                    'error': 'AI движок недоступен'
                }

            return await self.ai_engine.test_connection()

        except Exception as e:
            logger.error(f"❌ Ошибка тестирования AI подключения: {e}")
            return {
                'available': False,
                'error': str(e)
            }


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()