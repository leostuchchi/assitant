from backend.database import async_session, UserAstroProfile
from backend.psyho_matrix import PsyhoMatrixCalculator
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def calculate_and_save_psyho_matrix(telegram_id: int):
    """Расчет и сохранение психоматрицы в объединенный астропрофиль"""
    try:
        # Получаем данные пользователя для расчета даты рождения
        from backend.user_services import get_user_profile
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = PsyhoMatrixCalculator()
        matrix_data = calculator.calculate_matrix(user_profile['birth_date'])

        # Сохраняем психоматрицу в астропрофиль
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем существующий астропрофиль
                astro_profile.psyho_matrix_data = matrix_data
                # Натальная карта остается без изменений
                logger.info(f"📝 Обновлена психоматрица в астропрофиле для {telegram_id}")
            else:
                # Создаем новый астропрофиль с пустой натальной картой
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data={},  # Пустая натальная карта
                    psyho_matrix_data=matrix_data,
                    dominant_energy=None,
                    personality_traits=None
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль с психоматрицей для {telegram_id}")

            await session.commit()
            logger.info(f"✅ Психоматрица рассчитана и сохранена для {telegram_id}")

        return matrix_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете психоматрицы для {telegram_id}: {e}")
        raise


async def get_user_matrix(telegram_id: int):
    """Получение психоматрицы пользователя из астропрофиля"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile and astro_profile.psyho_matrix_data:
                return astro_profile.psyho_matrix_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении психоматрицы {telegram_id}: {e}")
        return None


async def get_matrix_summary(telegram_id: int) -> dict:
    """Получение краткой сводки психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return {}

        basic_numbers = matrix_data.get('basic_numbers', {})
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        digit_counts = matrix_data.get('digit_counts', {})

        # Анализ основных чисел
        life_path = basic_numbers.get('first')
        destiny_number = basic_numbers.get('second')
        personality_number = basic_numbers.get('third')

        # Анализ матрицы Пифагора
        strong_digits = digit_counts.get('strong_digits', [])
        missing_digits = digit_counts.get('missing_digits', [])
        total_digits = digit_counts.get('total_digits', 0)

        # Определение типа матрицы по сложности
        if total_digits >= 15:
            matrix_type = "сложная"
        elif total_digits >= 10:
            matrix_type = "средняя"
        else:
            matrix_type = "простая"

        summary = {
            'basic_numbers': {
                'life_path': life_path,
                'destiny_number': destiny_number,
                'personality_number': personality_number
            },
            'matrix_analysis': {
                'matrix_type': matrix_type,
                'strong_digits': strong_digits,
                'missing_digits': missing_digits,
                'total_digits': total_digits
            },
            'key_characteristics': _analyze_matrix_characteristics(pythagoras_matrix)
        }

        return summary

    except Exception as e:
        logger.error(f"❌ Ошибка получения сводки психоматрицы для {telegram_id}: {e}")
        return {}


def _analyze_matrix_characteristics(pythagoras_matrix: dict) -> dict:
    """Анализ характеристик матрицы Пифагора"""
    characteristics = {
        'willpower': 0,  # Цифра 1
        'energy': 0,  # Цифра 2
        'interest': 0,  # Цифра 3
        'health': 0,  # Цифра 4
        'logic': 0,  # Цифра 5
        'labor': 0,  # Цифра 6
        'luck': 0,  # Цифра 7
        'duty': 0,  # Цифра 8
        'memory': 0  # Цифра 9
    }

    # Сопоставление цифр с характеристиками
    digit_characteristics = {
        '1': 'willpower',
        '2': 'energy',
        '3': 'interest',
        '4': 'health',
        '5': 'logic',
        '6': 'labor',
        '7': 'luck',
        '8': 'duty',
        '9': 'memory'
    }

    for digit, count in pythagoras_matrix.items():
        char_key = digit_characteristics.get(digit)
        if char_key:
            characteristics[char_key] = count

    return characteristics


async def calculate_personality_traits(telegram_id: int) -> list:
    """Расчет личностных черт на основе психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return []

        basic_numbers = matrix_data.get('basic_numbers', {})
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

        traits = []

        # Анализ по числу жизненного пути
        life_path = basic_numbers.get('first')
        if life_path:
            life_path_traits = {
                1: ["лидер", "амбициозный", "независимый"],
                2: ["дипломатичный", "чувствительный", "интуитивный"],
                3: ["творческий", "общительный", "оптимистичный"],
                4: ["практичный", "организованный", "надежный"],
                5: ["свободолюбивый", "авантюрный", "адаптивный"],
                6: ["ответственный", "заботливый", "гармоничный"],
                7: ["аналитический", "духовный", "интроспективный"],
                8: ["целеустремленный", "материалистичный", "властный"],
                9: ["гуманитарный", "сострадательный", "идеалистичный"]
            }
            traits.extend(life_path_traits.get(life_path, []))

        # Анализ по сильным цифрам в матрице
        strong_digits = []
        for digit, count in pythagoras_matrix.items():
            if count >= 2:
                strong_digits.append(int(digit))

        # Добавляем черты на основе сильных цифр
        digit_traits = {
            1: ["решительный", "инициативный"],
            2: ["эмпатичный", "тактичный"],
            3: ["артистичный", "выразительный"],
            4: ["трудолюбивый", "дисциплинированный"],
            5: ["любознательный", "гибкий"],
            6: ["семейный", "заботливый"],
            7: ["мудрый", "проницательный"],
            8: ["амбициозный", "практичный"],
            9: ["идеалистичный", "щедрый"]
        }

        for digit in strong_digits:
            if digit in digit_traits:
                traits.extend(digit_traits[digit])

        # Убираем дубликаты
        traits = list(set(traits))

        # Сохраняем черты в астропрофиль
        await update_personality_traits(telegram_id, traits)

        logger.info(f"✅ Рассчитаны личностные черты для {telegram_id}: {traits}")
        return traits

    except Exception as e:
        logger.error(f"❌ Ошибка расчета личностных черт для {telegram_id}: {e}")
        return []


async def update_personality_traits(telegram_id: int, traits: list):
    """Обновление личностных черт в астропрофиле"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                astro_profile.personality_traits = traits
                await session.commit()
                logger.info(f"📝 Обновлены личностные черты для {telegram_id}")
            else:
                logger.warning(f"⚠️ Астропрофиль не найден для обновления черт {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка обновления личностных черт для {telegram_id}: {e}")
        raise


async def validate_matrix_data(telegram_id: int) -> bool:
    """Проверка корректности данных психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return False

        # Проверяем обязательные поля
        required_fields = ['basic_numbers', 'pythagoras_matrix', 'digit_counts']
        for field in required_fields:
            if field not in matrix_data:
                logger.warning(f"⚠️ Отсутствует поле {field} в психоматрице {telegram_id}")
                return False

        # Проверяем базовые числа
        basic_numbers = matrix_data.get('basic_numbers', {})
        if not all(key in basic_numbers for key in ['first', 'second', 'third', 'fourth']):
            logger.warning(f"⚠️ Неполные базовые числа в психоматрице {telegram_id}")
            return False

        # Проверяем матрицу Пифагора
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        if not all(str(i) in pythagoras_matrix for i in range(1, 10)):
            logger.warning(f"⚠️ Неполная матрица Пифагора {telegram_id}")
            return False

        logger.info(f"✅ Данные психоматрицы валидны для {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации психоматрицы для {telegram_id}: {e}")
        return False


async def get_matrix_compatibility(user1_id: int, user2_id: int) -> dict:
    """Анализ совместимости по психоматрицам"""
    try:
        matrix1 = await get_user_matrix(user1_id)
        matrix2 = await get_user_matrix(user2_id)

        if not matrix1 or not matrix2:
            return {"error": "Не найдены данные психоматриц"}

        matrix1_data = matrix1.get('pythagoras_matrix', {})
        matrix2_data = matrix2.get('pythagoras_matrix', {})

        # Анализ совместимости по цифрам
        compatibility_score = 0
        max_score = 9  # Максимально возможный счет

        for digit in range(1, 10):
            digit_str = str(digit)
            count1 = matrix1_data.get(digit_str, 0)
            count2 = matrix2_data.get(digit_str, 0)

            # Чем ближе количество цифр, тем выше совместимость
            digit_compatibility = 1 - abs(count1 - count2) / 3  # Нормализуем до 0-1
            compatibility_score += digit_compatibility

        # Нормализуем общий счет
        overall_compatibility = (compatibility_score / max_score) * 100

        # Определяем уровень совместимости
        if overall_compatibility >= 80:
            level = "отличная"
        elif overall_compatibility >= 60:
            level = "хорошая"
        elif overall_compatibility >= 40:
            level = "средняя"
        else:
            level = "низкая"

        # Анализ сильных и слабых сторон совместимости
        strengths = []
        challenges = []

        # Анализ по конкретным цифрам
        for digit in range(1, 10):
            digit_str = str(digit)
            count1 = matrix1_data.get(digit_str, 0)
            count2 = matrix2_data.get(digit_str, 0)

            if count1 == count2 and count1 > 0:
                digit_meanings = {
                    1: "схожая воля и лидерские качества",
                    2: "совместимая энергия и чувствительность",
                    3: "общие творческие интересы",
                    4: "похожее отношение к здоровью",
                    5: "схожая логика и мышление",
                    6: "совместимость в трудовой деятельности",
                    7: "общая удача и везение",
                    8: "похожее чувство долга",
                    9: "схожие ментальные способности"
                }
                strengths.append(digit_meanings.get(digit, ""))

            elif abs(count1 - count2) >= 2:
                digit_challenges = {
                    1: "разные подходы к лидерству",
                    2: "разный уровень энергии",
                    3: "разные творческие интересы",
                    4: "разное отношение к здоровью",
                    5: "разные стили мышления",
                    6: "разное отношение к работе",
                    7: "разная удачливость",
                    8: "разное понимание долга",
                    9: "разные ментальные способности"
                }
                challenges.append(digit_challenges.get(digit, ""))

        return {
            'compatibility_score': round(overall_compatibility, 2),
            'compatibility_level': level,
            'strengths': [s for s in strengths if s],  # Убираем пустые строки
            'challenges': [c for c in challenges if c],
            'analysis_timestamp': await get_current_timestamp()
        }

    except Exception as e:
        logger.error(f"❌ Ошибка анализа совместимости для {user1_id} и {user2_id}: {e}")
        return {"error": str(e)}


async def get_current_timestamp():
    """Вспомогательная функция для получения текущего времени"""
    from datetime import datetime
    return datetime.now().isoformat()


async def get_matrix_energy_level(telegram_id: int) -> str:
    """Оценка уровня энергии по психоматрице"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return "неизвестно"

        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

        # Считаем общее количество цифр
        total_digits = sum(pythagoras_matrix.values())

        # Анализируем энергетические цифры (2, 5, 8)
        energy_digits = sum(pythagoras_matrix.get(str(digit), 0) for digit in [2, 5, 8])

        if total_digits >= 15 and energy_digits >= 4:
            return "очень высокий"
        elif total_digits >= 12 and energy_digits >= 3:
            return "высокий"
        elif total_digits >= 8 and energy_digits >= 2:
            return "средний"
        else:
            return "низкий"

    except Exception as e:
        logger.error(f"❌ Ошибка оценки уровня энергии для {telegram_id}: {e}")
        return "неизвестно"


class MatrixAnalysisService:
    """Сервис для углубленного анализа психоматриц"""

    def __init__(self):
        self.calculator = PsyhoMatrixCalculator()

    async def create_complete_matrix_profile(self, telegram_id: int, birth_date):
        """Создание полного профиля психоматрицы с расширенным анализом"""
        try:
            # Рассчитываем базовую матрицу
            matrix_data = self.calculator.calculate_matrix(birth_date)

            # Добавляем расширенный анализ
            extended_analysis = self._perform_extended_analysis(matrix_data)
            matrix_data['extended_analysis'] = extended_analysis

            # Сохраняем в астропрофиль
            async with async_session() as session:
                result = await session.execute(
                    select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
                )
                astro_profile = result.scalar_one_or_none()

                if astro_profile:
                    astro_profile.psyho_matrix_data = matrix_data
                else:
                    astro_profile = UserAstroProfile(
                        telegram_id=telegram_id,
                        natal_chart_data={},
                        psyho_matrix_data=matrix_data,
                        dominant_energy=None,
                        personality_traits=None
                    )
                    session.add(astro_profile)

                await session.commit()
                logger.info(f"✅ Полный профиль психоматрицы создан для {telegram_id}")
                return matrix_data

        except Exception as e:
            logger.error(f"❌ Ошибка создания полного профиля матрицы для {telegram_id}: {e}")
            raise

    def _perform_extended_analysis(self, matrix_data: dict) -> dict:
        """Расширенный анализ психоматрицы"""
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        basic_numbers = matrix_data.get('basic_numbers', {})

        analysis = {
            'energy_centers': self._analyze_energy_centers(pythagoras_matrix),
            'life_periods': self._analyze_life_periods(basic_numbers.get('first')),
            'karmic_lessons': self._analyze_karmic_lessons(pythagoras_matrix),
            'talents_abilities': self._analyze_talents(pythagoras_matrix)
        }

        return analysis

    def _analyze_energy_centers(self, matrix: dict) -> dict:
        """Анализ энергетических центров"""
        centers = {
            'practical_center': sum(matrix.get(str(digit), 0) for digit in [4, 5, 6]),
            'spiritual_center': sum(matrix.get(str(digit), 0) for digit in [7, 8, 9]),
            'will_center': sum(matrix.get(str(digit), 0) for digit in [1, 2, 3])
        }

        return centers

    def _analyze_life_periods(self, life_path: int) -> list:
        """Анализ жизненных периодов"""
        if not life_path:
            return []

        periods = []
        base_age = 36  # Базовый возраст для расчета периодов

        for i in range(3):  # 3 основных периода
            period_number = (life_path + i) % 9 or 9
            start_age = i * 12
            end_age = (i + 1) * 12

            period_info = {
                'period': i + 1,
                'number': period_number,
                'age_range': f"{start_age}-{end_age}",
                'focus': self._get_period_focus(period_number)
            }
            periods.append(period_info)

        return periods

    def _get_period_focus(self, period_number: int) -> str:
        """Определение фокуса жизненного периода"""
        focuses = {
            1: "самоопределение и инициатива",
            2: "партнерство и сотрудничество",
            3: "творчество и самовыражение",
            4: "стабильность и организация",
            5: "свобода и изменения",
            6: "ответственность и служение",
            7: "анализ и духовность",
            8: "достижения и власть",
            9: "завершение и мудрость"
        }
        return focuses.get(period_number, "неопределенный период")

    def _analyze_karmic_lessons(self, matrix: dict) -> list:
        """Анализ кармических уроков (отсутствующие цифры)"""
        lessons = []
        digit_lessons = {
            1: "урок независимости и уверенности",
            2: "урок чувствительности и сотрудничества",
            3: "урок творчества и радости",
            4: "урок дисциплины и практичности",
            5: "урок свободы и адаптации",
            6: "урок ответственности и заботы",
            7: "урок мудрости и интуиции",
            8: "урок власти и изобилия",
            9: "урок сострадания и завершения"
        }

        for digit in range(1, 10):
            if matrix.get(str(digit), 0) == 0:
                lessons.append(digit_lessons.get(digit, f"урок цифры {digit}"))

        return lessons

    def _analyze_talents(self, matrix: dict) -> list:
        """Анализ талантов и способностей (сильные цифры)"""
        talents = []
        digit_talents = {
            1: "лидерские способности",
            2: "дипломатические навыки",
            3: "творческие таланты",
            4: "организаторские способности",
            5: "адаптивность и коммуникабельность",
            6: "педагогические способности",
            7: "аналитическое мышление",
            8: "бизнес-способности",
            9: "гуманитарные таланты"
        }

        for digit in range(1, 10):
            if matrix.get(str(digit), 0) >= 2:
                talents.append(digit_talents.get(digit, f"талант цифры {digit}"))

        return talents

    async def get_detailed_matrix_report(self, telegram_id: int) -> dict:
        """Получение детального отчета по психоматрице"""
        try:
            matrix_data = await get_user_matrix(telegram_id)

            if not matrix_data:
                return {"error": "Данные психоматрицы не найдены"}

            summary = await get_matrix_summary(telegram_id)
            traits = await calculate_personality_traits(telegram_id)
            energy_level = await get_matrix_energy_level(telegram_id)

            report = {
                'basic_info': summary,
                'personality_traits': traits,
                'energy_level': energy_level,
                'extended_analysis': matrix_data.get('extended_analysis', {}),
                'calculation_date': matrix_data.get('calculated_at'),
                'report_timestamp': await get_current_timestamp()
            }

            return report

        except Exception as e:
            logger.error(f"❌ Ошибка создания детального отчета для {telegram_id}: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
matrix_service = MatrixAnalysisService()