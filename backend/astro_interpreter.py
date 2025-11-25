import logging
from datetime import date
from typing import Dict, List, Any
from backend.predictions import AstroPredictor
from backend.chart_services import get_user_natal_chart

logger = logging.getLogger(__name__)


class AstroInterpreter:
    """Сервис для преобразования сырых астрологических данных в понятные рекомендации"""

    def __init__(self):
        self.planet_names_ru = {
            'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
            'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
            'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
            'Pluto': 'Плутон', 'North_Node': 'Северный узел',
            'Ascendant': 'Асцендент', 'Midheaven': 'Середина неба'
        }

        self.aspect_names_ru = {
            'conjunction': 'соединение',
            'opposition': 'оппозиция',
            'square': 'квадрат',
            'trine': 'трин',
            'sextile': 'секстиль'
        }

        self.sign_names_ru = {
            'Aries': 'Овен', 'Taurus': 'Телец', 'Gemini': 'Близнецы',
            'Cancer': 'Рак', 'Leo': 'Лев', 'Virgo': 'Дева',
            'Libra': 'Весы', 'Scorpio': 'Скорпион', 'Sagittarius': 'Стрелец',
            'Capricorn': 'Козерог', 'Aquarius': 'Водолей', 'Pisces': 'Рыбы'
        }

    async def get_daily_astro_insights(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Получить понятные астрологические инсайты на день"""
        try:
            # Получаем натальную карту
            natal_data = await get_user_natal_chart(telegram_id)
            if not natal_data:
                return self._get_fallback_insights("Натальная карта не найдена")

            # Генерируем предсказания
            predictor = AstroPredictor(natal_data)
            astro_data = predictor.generate_prediction(target_date)

            # Форматируем в понятный вид
            insights = {
                'daily_overview': self._generate_daily_overview(astro_data),
                #'key_aspects': self._format_key_aspects(astro_data.get('aspects', [])),
                'key_aspects': self._format_key_aspects(astro_data.get('aspects', []), limit=5),
                'retrograde_planets': self._format_retrograde_planets(astro_data.get('retrograde_planets', [])),
                'recommendations': self._generate_recommendations(astro_data),
                'energy_forecast': self._calculate_energy_forecast(astro_data),
                'total_aspects_count': len(astro_data.get('aspects', []))
            }

            return insights

        except Exception as e:
            logger.error(f"❌ Ошибка генерации астрологических инсайтов: {e}")
            return self._get_fallback_insights("Временные технические неполадки")

    def _generate_daily_overview(self, astro_data: Dict) -> str:
        """Генерация общего обзора дня"""
        aspects_count = astro_data.get('aspects_count', 0)
        strong_aspects = astro_data.get('strong_aspects_count', 0)
        retrograde_count = len(astro_data.get('retrograde_planets', []))

        if strong_aspects >= 5:
            intensity = "очень напряженный"
            emoji = "⚡"
        elif strong_aspects >= 3:
            intensity = "напряженный"
            emoji = "🎯"
        elif aspects_count == 0:
            intensity = "спокойный"
            emoji = "😌"
        else:
            intensity = "умеренно активный"
            emoji = "⚖️"

        if retrograde_count >= 3:
            retro_note = " Много ретроградных планет - время пересмотра планов."
        elif retrograde_count >= 1:
            retro_note = " Есть ретроградные планеты - будьте гибче в решениях."
        else:
            retro_note = ""

        return f"{emoji} Сегодня {intensity} астрологический день. {strong_aspects} сильных аспектов из {aspects_count}.{retro_note}"

    def _format_key_aspects(self, aspects: List[Dict], limit: int = 5) -> List[str]:
    #def _format_key_aspects(self, aspects: List[Dict]) -> List[str]:
        """Форматирование ключевых аспектов"""
        if not aspects:
            return ["Сегодня нет значимых аспектов - стабильный день."]

        # Берем только сильные аспекты (сила > 0.7)
        strong_aspects = [a for a in aspects if a.get('strength', 0) > 0.7]
        strong_aspects.sort(key=lambda x: x.get('strength', 0), reverse=True)

        formatted = []
        for aspect in strong_aspects[:3]:  # Только топ-3 самых сильных
            transit_planet = self.planet_names_ru.get(aspect.get('transit_planet', ''),
                                                      aspect.get('transit_planet', ''))
            natal_planet = self.planet_names_ru.get(aspect.get('natal_planet', ''), aspect.get('natal_planet', ''))
            aspect_type = self.aspect_names_ru.get(aspect.get('aspect', ''), aspect.get('aspect', ''))

            # Генерируем описание аспекта
            description = self._get_aspect_description(
                transit_planet,
                natal_planet,
                aspect.get('aspect', ''),
                aspect.get('strength', 0)
            )

            strength_stars = "★" * int(aspect.get('strength', 0) * 5)
            formatted.append(f"• {transit_planet} → {natal_planet} ({aspect_type}) {strength_stars}\n  {description}")

        return formatted

    def _get_aspect_description(self, transit_planet: str, natal_planet: str, aspect_type: str, strength: float) -> str:
        """Генерация описания аспекта"""
        descriptions = {
            'conjunction': {
                'Sun': "Усиливает вашу индивидуальность и жизненную силу",
                'Moon': "Повышает эмоциональную чувствительность и интуицию",
                'Mercury': "Улучшает коммуникацию и мышление",
                'Venus': "Приносит гармонию в отношения и творчество",
                'Mars': "Дает энергию для действий и инициативы",
                'default': "Объединяет энергии, создавая новые возможности"
            },
            'opposition': {
                'default': "Создает напряжение, требующее баланса и компромиссов"
            },
            'square': {
                'default': "Вызывает вызовы, стимулирующие рост и изменения"
            },
            'trine': {
                'default': "Приносит легкость и благоприятные возможности"
            },
            'sextile': {
                'default': "Открывает возможности для сотрудничества и развития"
            }
        }

        aspect_descs = descriptions.get(aspect_type, {})
        return aspect_descs.get(transit_planet, aspect_descs.get('default', "Влияет на вашу энергию сегодня"))

    def _format_retrograde_planets(self, retrograde_planets: List[str]) -> List[str]:
        """Форматирование ретроградных планет"""
        if not retrograde_planets:
            return ["Ретроградных планет нет - прямое движение способствует прогрессу."]

        formatted = []
        for planet in retrograde_planets:
            planet_ru = self.planet_names_ru.get(planet, planet)
            advice = self._get_retrograde_advice(planet)
            formatted.append(f"• {planet_ru} ретрограден. {advice}")

        return formatted

    def _get_retrograde_advice(self, planet: str) -> str:
        """Советы по ретроградным планетам"""
        advice = {
            'Mercury': "Перепроверяйте информацию, будьте внимательны в общении.",
            'Venus': "Пересмотрите отношения и финансовые вопросы.",
            'Mars': "Энергия направлена внутрь, планируйте а не действуйте.",
            'Jupiter': "Время внутреннего роста и переоценки ценностей.",
            'Saturn': "Пересмотр ответственности и долгосрочных планов.",
            'default': "Время переосмысления и внутренней работы."
        }
        return advice.get(planet, advice['default'])

    def _generate_recommendations(self, astro_data: Dict) -> List[str]:
        """Генерация практических рекомендаций"""
        recommendations = []
        aspects = astro_data.get('aspects', [])
        retrograde_planets = astro_data.get('retrograde_planets', [])

        # Анализируем аспекты для рекомендаций
        strong_aspects = [a for a in aspects if a.get('strength', 0) > 0.7]

        if len(strong_aspects) >= 4:
            recommendations.append("📝 Сегодня много сильных аспектов - отличный день для важных решений и начинаний.")
        elif len(strong_aspects) == 0:
            recommendations.append("🔄 День подходит для рутинных дел и отдыха - значимых аспектов нет.")

        # Проверяем наличие квадратов (вызовы)
        squares = [a for a in aspects if a.get('aspect') == 'square' and a.get('strength', 0) > 0.6]
        if squares:
            recommendations.append("⚡ Есть напряженные аспекты - будьте готовы к вызовам, они ведут к росту.")

        # Проверяем наличие тринов (благоприятные)
        trines = [a for a in aspects if a.get('aspect') == 'trine' and a.get('strength', 0) > 0.6]
        if trines:
            recommendations.append("🌟 Благоприятные аспекты открывают возможности - доверяйте интуиции.")

        # Рекомендации по ретроградным планетам
        if 'Mercury' in retrograde_planets:
            recommendations.append("💬 Меркурий ретрограден - уточняйте детали, перечитывайте сообщения.")
        if 'Venus' in retrograde_planets:
            recommendations.append("💝 Венера ретроградна - время гармонизировать отношения.")

        if not recommendations:
            recommendations.append("🌱 Стабильный день - следуйте своему обычному ритму.")

        return recommendations

    def _calculate_energy_forecast(self, astro_data: Dict) -> str:
        """Расчет энергетического прогноза"""
        aspects = astro_data.get('aspects', [])
        strong_aspects = len([a for a in aspects if a.get('strength', 0) > 0.7])
        retrograde_count = len(astro_data.get('retrograde_planets', []))

        # Логика расчета энергии
        if strong_aspects >= 5:
            return "очень высокая"
        elif strong_aspects >= 3:
            return "высокая"
        elif retrograde_count >= 3:
            return "направленная внутрь"
        elif len(aspects) == 0:
            return "стабильная"
        else:
            return "умеренная"

    def _get_fallback_insights(self, reason: str) -> Dict[str, Any]:
        """Резервные данные при ошибках"""
        return {
            'daily_overview': f"Астрологические данные временно недоступны. {reason}",
            'key_aspects': ["Используйте биоритмы для планирования дня."],
            'retrograde_planets': [],
            'recommendations': ["Обратитесь к биоритмам и интуиции для принятия решений."],
            'energy_forecast': "неопределенная"
        }


# Глобальный экземпляр
astro_interpreter = AstroInterpreter()