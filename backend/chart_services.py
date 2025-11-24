from backend.database import async_session, UserAstroProfile
from backend.natal_chart import MLNatalChartCalculator
from sqlalchemy.future import select
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)


async def create_and_save_natal_chart(telegram_id: int, city: str, birth_datetime, timezone: str):
    """Создание и сохранение натальной карты в объединенный астропрофиль"""
    try:
        calculator = MLNatalChartCalculator()
        natal_data = calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

        logger.info(f"🔮 Создание натальной карты для пользователя {telegram_id}")

        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем существующий астропрофиль
                astro_profile.natal_chart_data = natal_data
                # Психоматрица остается без изменений
                logger.info(f"📝 Обновлена натальная карта в астропрофиле для {telegram_id}")
            else:
                # Создаем новый астропрофиль с пустой психоматрицей
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data=natal_data,
                    psyho_matrix_data={},  # Пустая психоматрица, будет заполнена позже
                    dominant_energy=None,
                    personality_traits=None
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль с натальной картой для {telegram_id}")

            await session.commit()
            logger.info(f"💾 Натальная карта успешно сохранена для {telegram_id}")
            return astro_profile

    except Exception as e:
        logger.error(f"❌ Ошибка при создании натальной карты для {telegram_id}: {e}")
        raise


async def get_user_natal_chart(telegram_id: int):
    """Получение натальной карты пользователя из астропрофиля"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile and astro_profile.natal_chart_data:
                return astro_profile.natal_chart_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении натальной карты {telegram_id}: {e}")
        return None


async def update_user_astro_profile(telegram_id: int, psyho_matrix_data: dict = None,
                                    dominant_energy: str = None, personality_traits: list = None):
    """Обновление астропрофиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем только переданные поля
                if psyho_matrix_data is not None:
                    astro_profile.psyho_matrix_data = psyho_matrix_data
                if dominant_energy is not None:
                    astro_profile.dominant_energy = dominant_energy
                if personality_traits is not None:
                    astro_profile.personality_traits = personality_traits

                logger.info(f"📝 Обновлен астропрофиль для {telegram_id}")
            else:
                # Создаем новый астропрофиль только с психоматрицей
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data={},  # Пустая натальная карта
                    psyho_matrix_data=psyho_matrix_data or {},
                    dominant_energy=dominant_energy,
                    personality_traits=personality_traits
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль для {telegram_id}")

            await session.commit()
            return astro_profile

    except Exception as e:
        logger.error(f"❌ Ошибка обновления астропрофиля для {telegram_id}: {e}")
        raise


async def get_user_astro_profile(telegram_id: int):
    """Получение полного астропрофиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                return {
                    'telegram_id': astro_profile.telegram_id,
                    'natal_chart': astro_profile.natal_chart_data,
                    'psyho_matrix': astro_profile.psyho_matrix_data,
                    'dominant_energy': astro_profile.dominant_energy,
                    'personality_traits': astro_profile.personality_traits,
                    'created_at': astro_profile.created_at.isoformat() if astro_profile.created_at else None,
                    'updated_at': astro_profile.updated_at.isoformat() if astro_profile.updated_at else None
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении астропрофиля {telegram_id}: {e}")
        return None


async def validate_natal_chart_data(telegram_id: int) -> bool:
    """Проверка корректности данных натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return False

        # Проверяем обязательные поля
        required_fields = ['metadata', 'planets', 'houses', 'angles']
        for field in required_fields:
            if field not in natal_data:
                logger.warning(f"⚠️ Отсутствует поле {field} в натальной карте {telegram_id}")
                return False

        # Проверяем наличие основных планет
        planets = natal_data.get('planets', {})
        essential_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
        for planet in essential_planets:
            if planet not in planets:
                logger.warning(f"⚠️ Отсутствует планета {planet} в натальной карте {telegram_id}")
                return False

        logger.info(f"✅ Данные натальной карты валидны для {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации натальной карты для {telegram_id}: {e}")
        return False


async def get_natal_chart_summary(telegram_id: int) -> dict:
    """Получение краткой сводки натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        planets = natal_data.get('planets', {})
        houses = natal_data.get('houses', {})
        angles = natal_data.get('angles', {})

        # Анализ доминирующих знаков
        sign_distribution = {}
        for planet_data in planets.values():
            sign = planet_data.get('sign', 'Unknown')
            sign_distribution[sign] = sign_distribution.get(sign, 0) + 1

        dominant_sign = max(sign_distribution.items(), key=lambda x: x[1])[0] if sign_distribution else "Unknown"

        # Анализ аспектов
        aspects = natal_data.get('aspects', [])
        aspect_patterns = {
            'conjunctions': len([a for a in aspects if a.get('aspect') == 'conjunction']),
            'squares': len([a for a in aspects if a.get('aspect') == 'square']),
            'trines': len([a for a in aspects if a.get('aspect') == 'trine']),
            'oppositions': len([a for a in aspects if a.get('aspect') == 'opposition'])
        }

        summary = {
            'basic_info': {
                'planets_count': len(planets),
                'houses_count': len(houses),
                'aspects_count': len(aspects),
                'dominant_sign': dominant_sign
            },
            'key_placements': {
                'sun_sign': planets.get('Sun', {}).get('sign', 'Unknown'),
                'moon_sign': planets.get('Moon', {}).get('sign', 'Unknown'),
                'ascendant': angles.get('ascendant', {}).get('sign', 'Unknown'),
                'midheaven': angles.get('midheaven', {}).get('sign', 'Unknown')
            },
            'aspect_analysis': aspect_patterns,
            'element_balance': natal_data.get('ml_features', {}).get('element_balance', {})
        }

        return summary

    except Exception as e:
        logger.error(f"❌ Ошибка получения сводки натальной карты для {telegram_id}: {e}")
        return {}


async def calculate_dominant_energy(telegram_id: int) -> str:
    """Расчет доминирующей энергии на основе натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return "неизвестно"

        planets = natal_data.get('planets', {})
        element_balance = natal_data.get('ml_features', {}).get('element_balance', {})

        # Простой анализ на основе элементов
        if not element_balance:
            return "сбалансированная"

        max_element = max(element_balance.items(), key=lambda x: x[1])
        element_energy_map = {
            'fire': 'активная',
            'air': 'интеллектуальная',
            'water': 'эмоциональная',
            'earth': 'практическая'
        }

        dominant_energy = element_energy_map.get(max_element[0], "сбалансированная")

        # Сохраняем результат в астропрофиль
        await update_user_astro_profile(telegram_id, dominant_energy=dominant_energy)

        logger.info(f"✅ Рассчитана доминирующая энергия для {telegram_id}: {dominant_energy}")
        return dominant_energy

    except Exception as e:
        logger.error(f"❌ Ошибка расчета доминирующей энергии для {telegram_id}: {e}")
        return "неизвестно"


async def get_planet_positions(telegram_id: int, planet_names: list = None) -> dict:
    """Получение позиций конкретных планет"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        planets = natal_data.get('planets', {})

        if planet_names:
            # Фильтруем по запрошенным планетам
            positions = {name: planets.get(name) for name in planet_names if name in planets}
        else:
            # Возвращаем все планеты
            positions = planets

        return positions

    except Exception as e:
        logger.error(f"❌ Ошибка получения позиций планет для {telegram_id}: {e}")
        return {}


async def get_house_placements(telegram_id: int) -> dict:
    """Получение размещения планет по домам"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        placements = natal_data.get('placements', {})
        houses = natal_data.get('houses', {})

        # Группируем планеты по домам
        house_planets = {}
        for planet, house_num in placements.items():
            house_key = f"house_{house_num}"
            if house_key not in house_planets:
                house_planets[house_key] = []
            house_planets[house_key].append(planet)

        result = {
            'house_planets': house_planets,
            'houses_info': houses
        }

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка получения размещения по домам для {telegram_id}: {e}")
        return {}


async def cleanup_orphaned_astro_profiles():
    """Очистка астропрофилей без пользователей"""
    try:
        async with async_session() as session:
            # Находим астропрофили, у которых нет соответствующего пользователя
            orphan_query = """
            DELETE FROM user_astro_profile 
            WHERE telegram_id NOT IN (SELECT telegram_id FROM users)
            """

            result = await session.execute(orphan_query)
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.warning(f"🗑️ Удалено {deleted_count} orphaned астропрофилей")
            else:
                logger.info("✅ Orphaned астропрофилей не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка очистки orphaned астропрофилей: {e}")
        return 0


class NatalChartService:
    """Сервис для работы с натальными картами"""

    def __init__(self):
        self.calculator = MLNatalChartCalculator()

    async def create_complete_astro_profile(self, telegram_id: int, city: str,
                                            birth_datetime, timezone: str, psyho_matrix_data: dict = None):
        """Создание полного астропрофиля (натальная карта + психоматрица)"""
        try:
            # Создаем натальную карту
            natal_data = self.calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

            # Рассчитываем доминирующую энергию
            element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
            dominant_energy = self._calculate_dominant_energy_from_elements(element_balance)

            # Создаем/обновляем астропрофиль
            async with async_session() as session:
                result = await session.execute(
                    select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
                )
                astro_profile = result.scalar_one_or_none()

                if astro_profile:
                    # Обновляем существующий
                    astro_profile.natal_chart_data = natal_data
                    astro_profile.psyho_matrix_data = psyho_matrix_data or astro_profile.psyho_matrix_data
                    astro_profile.dominant_energy = dominant_energy
                else:
                    # Создаем новый
                    astro_profile = UserAstroProfile(
                        telegram_id=telegram_id,
                        natal_chart_data=natal_data,
                        psyho_matrix_data=psyho_matrix_data or {},
                        dominant_energy=dominant_energy,
                        personality_traits=None
                    )
                    session.add(astro_profile)

                await session.commit()
                logger.info(f"✅ Полный астропрофиль создан для {telegram_id}")
                return astro_profile

        except Exception as e:
            logger.error(f"❌ Ошибка создания полного астропрофиля для {telegram_id}: {e}")
            raise

    def _calculate_dominant_energy_from_elements(self, element_balance: dict) -> str:
        """Расчет доминирующей энергии на основе баланса элементов"""
        if not element_balance:
            return "сбалансированная"

        max_element = max(element_balance.items(), key=lambda x: x[1])
        element_energy_map = {
            'fire': 'активная',
            'air': 'интеллектуальная',
            'water': 'эмоциональная',
            'earth': 'практическая'
        }

        return element_energy_map.get(max_element[0], "сбалансированная")

    async def get_chart_complexity(self, telegram_id: int) -> str:
        """Оценка сложности натальной карты"""
        try:
            natal_data = await get_user_natal_chart(telegram_id)

            if not natal_data:
                return "неизвестно"

            aspects = natal_data.get('aspects', [])
            strong_aspects = len([a for a in aspects if a.get('strength', 0) > 0.7])

            if strong_aspects > 8:
                return "очень сложная"
            elif strong_aspects > 5:
                return "сложная"
            elif strong_aspects > 2:
                return "средняя"
            else:
                return "простая"

        except Exception as e:
            logger.error(f"❌ Ошибка оценки сложности карты для {telegram_id}: {e}")
            return "неизвестно"


# Глобальный экземпляр сервиса
natal_chart_service = NatalChartService()