from backend.user_services import create_or_update_user, get_user_profile, update_user_profession
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_todays_prediction, \
    format_prediction_for_display
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
from backend.moon import calculate_lunar_phase
import logging

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления всеми данными и рекомендациями"""

    def __init__(self):
        pass

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None):
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
                        job_position=job_position
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

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None):
        """Обновление профессиональной информации"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            # Обновляем город проживания
            user_profile = await get_user_profile(telegram_id)
            if user_profile:
                await create_or_update_user(
                    telegram_id=telegram_id,
                    birth_date=user_profile['birth_date'],
                    birth_time=user_profile['birth_time'],
                    birth_city=user_profile['birth_city'],
                    current_city=current_city,
                    profession=profession,
                    job_position=job_position
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

    async def get_todays_recommendations(self, telegram_id: int):
        """Получение рекомендаций на сегодня"""
        try:
            target_date = date.today()
            logger.info(f"📅 Формирование рекомендаций на сегодня для {telegram_id}")

            # Генерируем предсказание на сегодня
            prediction = await generate_and_save_prediction(telegram_id, target_date)

            # Форматируем для отображения - теперь это строка
            formatted_prediction = await format_prediction_for_display(prediction)

            # Добавляем лунную фазу
            lunar_phase = calculate_lunar_phase(target_date)

            # ✅ Теперь formatted_prediction - это строка, а не список
            final_recommendations = f"{formatted_prediction}\n\n🌙 Текущая лунная фаза: {lunar_phase}"

            # Вывод рекомендаций для отладки
            print(f"Recommendations for user {telegram_id} on {target_date.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': target_date.isoformat(),
                'recommendations': final_recommendations,  # ✅ Теперь это строка
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на сегодня для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на сегодня: {str(e)}"
            }

    async def get_tomorrows_recommendations(self, telegram_id: int):
        """Получение рекомендаций на завтра"""
        try:
            tomorrow = date.today() + timedelta(days=1)
            logger.info(f"📅 Формирование рекомендаций на завтра ({tomorrow}) для {telegram_id}")

            prediction = await generate_and_save_prediction(telegram_id, tomorrow)
            formatted_prediction = await format_prediction_for_display(prediction)

            lunar_phase = calculate_lunar_phase(tomorrow)
            final_recommendations = f"{formatted_prediction}\n\n🌙 Лунная фаза на завтра: {lunar_phase}"

            print(f"Recommendations for user {telegram_id} on {tomorrow.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': tomorrow.isoformat(),
                'recommendations': final_recommendations,
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на завтра для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на завтра: {str(e)}"
            }

    async def get_date_recommendations(self, telegram_id: int, target_date: date):
        """Получение рекомендаций на выбранную дату"""
        try:
            logger.info(f"📅 Формирование рекомендаций на {target_date} для {telegram_id}")

            if target_date < date.today():
                return {
                    'success': False,
                    'message': "❌ Нельзя получить рекомендации для прошедших дат"
                }

            prediction = await generate_and_save_prediction(telegram_id, target_date)
            formatted_prediction = await format_prediction_for_display(prediction)

            lunar_phase = calculate_lunar_phase(target_date)
            final_recommendations = f"{formatted_prediction}\n\n🌙 Лунная фаза на {target_date}: {lunar_phase}"

            print(f"Recommendations for user {telegram_id} on {target_date.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': target_date.isoformat(),
                'recommendations': final_recommendations,
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на выбранную дату: {str(e)}"
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

            data_status = await self.get_user_data_status(telegram_id)
            prediction_stats = await get_prediction_statistics(telegram_id)
            biorhythm_stats = await get_biorhythm_statistics(telegram_id)

            return {
                'data_status': data_status,
                'prediction_stats': prediction_stats,
                'biorhythm_stats': biorhythm_stats,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {
                'data_status': {},
                'prediction_stats': {},
                'biorhythm_stats': {},
                'error': str(e)
            }

    async def cleanup_user_data(self, telegram_id: int):
        """Очистка данных пользователя (для администрирования)"""
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


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()