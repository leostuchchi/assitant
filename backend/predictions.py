from math import floor
import json
from datetime import date, datetime
import swisseph as swe
from sqlalchemy.future import select

from backend.database import async_session, NatalPredictions


class AstroPredictor:
    def __init__(self, natal_chart):
        self.natal_chart = natal_chart
        self.planets_ml = {
            swe.SUN: 'Sun', swe.MOON: 'Moon', swe.MERCURY: 'Mercury',
            swe.VENUS: 'Venus', swe.MARS: 'Mars', swe.JUPITER: 'Jupiter',
            swe.SATURN: 'Saturn', swe.URANUS: 'Uranus',
            swe.NEPTUNE: 'Neptune', swe.PLUTO: 'Pluto'
        }
        # Русские названия для пользователя
        self.planet_names_ru = {
            'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
            'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
            'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун', 'Pluto': 'Плутон'
        }
        self.sign_names_ru = {
            'Aries': 'Овен', 'Taurus': 'Телец', 'Gemini': 'Близнецы',
            'Cancer': 'Рак', 'Leo': 'Лев', 'Virgo': 'Дева',
            'Libra': 'Весы', 'Scorpio': 'Скорпион', 'Sagittarius': 'Стрелец',
            'Capricorn': 'Козерог', 'Aquarius': 'Водолей', 'Pisces': 'Рыбы'
        }
        self.planet_names_to_ids = {v: k for k, v in self.planets_ml.items()}

    def calculate_transits(self, target_date):
        jd_target = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        transits = {}
        for planet_id, name in self.planets_ml.items():
            pos, _ = swe.calc_ut(jd_target, planet_id, swe.FLG_SWIEPH)
            lon = pos[0] % 360
            transits[name] = {
                'longitude': lon,
                'sign': self.get_sign_from_longitude(lon),
                'position_in_sign': lon % 30,
                'retrograde': pos[3] < 0
            }
        return transits

    def get_sign_from_longitude(self, longitude):
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        return signs[floor(longitude / 30)]

    def analyze_aspects(self, transits, natal_positions):
        aspects = []
        for t_planet, t_data in transits.items():
            for n_planet, n_data in natal_positions.items():
                if t_planet == n_planet:
                    continue
                t_lon = t_data['longitude']
                n_lon = n_data['longitude']
                distance = abs(t_lon - n_lon)
                angle = min(distance, 360 - distance)
                aspect_info = self.check_aspect(angle)
                if aspect_info:
                    aspects.append({
                        'transit_planet': t_planet,
                        'natal_planet': n_planet,
                        'aspect': aspect_info[0],
                        'exact_angle': aspect_info[1],
                        'actual_angle': angle,
                        'orb': abs(angle - aspect_info[1]),
                        'strength': 1.0 - (abs(angle - aspect_info[1]) / aspect_info[2])
                    })
        aspects.sort(key=lambda x: x['strength'], reverse=True)
        return aspects

    def check_aspect(self, angle):
        aspects = {
            0: ('conjunction', 0, 8),
            60: ('sextile', 60, 6),
            90: ('square', 90, 8),
            120: ('trine', 120, 8),
            180: ('opposition', 180, 8)
        }
        for aspect_angle, (name, exact, orb) in aspects.items():
            if abs(angle - aspect_angle) <= orb:
                return (name, exact, orb)
        return None

    def get_planet_influence(self, planet_name):
        """Определяет сферу влияния планеты на основе астрологических принципов"""
        influences = {
            'Sun': 'личную энергию, творчество, самореализацию',
            'Moon': 'эмоции, интуицию, домашние дела',
            'Mercury': 'общение, обучение, документы',
            'Venus': 'отношения, финансы, искусство',
            'Mars': 'действия, инициативу, спорт',
            'Jupiter': 'расширение, возможности, путешествия',
            'Saturn': 'ответственность, карьеру, долгосрочные планы',
            'Uranus': 'изменения, инновации, неожиданные события',
            'Neptune': 'интуицию, творчество, духовность',
            'Pluto': 'трансформацию, глубокие изменения'
        }
        return influences.get(planet_name, 'личное развитие')

    def get_aspect_meaning(self, aspect_type, strength):
        """Получает значение аспекта в зависимости от силы на основе астрологических принципов"""
        if aspect_type == 'conjunction':
            if strength > 0.7:
                return "мощное соединение - время начинаний"
            else:
                return "соединение - новые возможности"
        elif aspect_type == 'opposition':
            if strength > 0.7:
                return "сильная оппозиция - важные решения"
            else:
                return "оппозиция - требует баланса"
        elif aspect_type == 'square':
            if strength > 0.7:
                return "напряженный квадрат - преодоление препятствий"
            else:
                return "квадрат - вызовы для роста"
        elif aspect_type == 'trine':
            if strength > 0.7:
                return "гармоничный трин - благоприятное время"
            else:
                return "трин - поддержка и удача"
        elif aspect_type == 'sextile':
            if strength > 0.7:
                return "благоприятный секстиль - хорошие возможности"
            else:
                return "секстиль - шансы для развития"
        return "влияние на вашу энергию"

    def generate_personal_recommendations(self, aspects, transits):
        """Генерация персонализированных рекомендаций на основе РАСЧЕТОВ аспектов"""
        recommendations = []
        warnings = []

        # Анализируем самые сильные аспекты (топ-3)
        strong_aspects = [a for a in aspects if a['strength'] > 0.6][:3]

        for aspect in strong_aspects:
            transit_planet_ru = self.planet_names_ru.get(aspect['transit_planet'], aspect['transit_planet'])
            natal_planet_ru = self.planet_names_ru.get(aspect['natal_planet'], aspect['natal_planet'])
            influence_area = self.get_planet_influence(aspect['natal_planet'])
            aspect_meaning = self.get_aspect_meaning(aspect['aspect'], aspect['strength'])

            recommendation = f"{transit_planet_ru} {aspect_meaning} в сфере {influence_area}"

            if aspect['aspect'] in ['trine', 'sextile', 'conjunction']:
                # Благоприятные аспекты на основе РАСЧЕТОВ
                if aspect['aspect'] == 'conjunction':
                    actions = {
                        'Sun': 'начинайте новые проекты, проявляйте инициативу',
                        'Moon': 'доверяйте интуиции, займитесь домом',
                        'Mercury': 'общайтесь, учитесь, подписывайте документы',
                        'Venus': 'укрепляйте отношения, занимайтесь творчеством',
                        'Mars': 'действуйте решительно, занимайтесь спортом',
                        'Jupiter': 'расширяйте горизонты, путешествуйте',
                        'Saturn': 'стройте долгосрочные планы, берите ответственность',
                        'Uranus': 'экспериментируйте, будьте открыты новому',
                        'Neptune': 'развивайте интуицию, занимайтесь творчеством',
                        'Pluto': 'трансформируйте старые привычки'
                    }
                elif aspect['aspect'] in ['trine', 'sextile']:
                    actions = {
                        'Sun': 'используйте свою энергию для творчества',
                        'Moon': 'положитесь на внутренние ощущения',
                        'Mercury': 'эффективно общайтесь и договаривайтесь',
                        'Venus': 'гармонизируйте отношения и финансы',
                        'Mars': 'реализуйте планы с энтузиазмом',
                        'Jupiter': 'используйте расширяющиеся возможности',
                        'Saturn': 'стройте прочный фундамент',
                        'Uranus': 'внедряйте инновационные идеи',
                        'Neptune': 'развивайте духовные практики',
                        'Pluto': 'глубоко трансформируйтесь'
                    }

                action = actions.get(aspect['natal_planet'], 'используйте эту энергию для роста')
                recommendations.append(f"{recommendation}. {action} (сила аспекта: {aspect['strength']:.2f})")

            else:
                # Сложные аспекты (квадрат, оппозиция) на основе РАСЧЕТОВ
                cautions = {
                    'Sun': 'избегайте конфликтов, будьте дипломатичны',
                    'Moon': 'контролируйте эмоции, избегайте импульсивности',
                    'Mercury': 'проверяйте информацию, избегайте споров',
                    'Venus': 'будьте осторожны в отношениях и финансах',
                    'Mars': 'избегайте рисков, действуйте обдуманно',
                    'Jupiter': 'не переоценивайте возможности',
                    'Saturn': 'не избегайте ответственности, но и не перегружайтесь',
                    'Uranus': 'будьте готовы к неожиданностям',
                    'Neptune': 'различайте иллюзии и реальность',
                    'Pluto': 'избегайте манипуляций и давления'
                }

                caution = cautions.get(aspect['natal_planet'], 'будьте внимательны и осторожны')
                warnings.append(f"{recommendation}. {caution} (сила аспекта: {aspect['strength']:.2f})")

        # Добавляем информацию о ретроградных планетах на основе РАСЧЕТОВ
        retrograde_planets = [p for p, data in transits.items() if data.get('retrograde')]
        if retrograde_planets:
            retro_names = [self.planet_names_ru.get(p, p) for p in retrograde_planets]
            if len(retro_names) > 0:
                warnings.append(f"Ретроградные {', '.join(retro_names)} - время пересмотра и анализа")

        # Если аспектов мало, добавляем рекомендации на основе общей картины РАСЧЕТОВ
        if not recommendations and not warnings:
            total_aspects = len(aspects)
            if total_aspects > 0:
                avg_strength = sum(a['strength'] for a in aspects) / total_aspects
                recommendations.append(
                    f"Наблюдается {total_aspects} аспектов со средней силой {avg_strength:.2f} - следите за изменениями в соответствующих сферах")
            else:
                # Если аспектов нет вообще - это тоже результат расчета
                recommendations.append(
                    "Сегодня минимальная астрологическая активность - хороший день для рутинных дел и планирования")

        return recommendations[:4], warnings[:3]  # Ограничиваем количество

    def analyze_natal_elements(self):
        """Анализирует элементный баланс натальной карты на основе РАСЧЕТОВ"""
        if 'ml_features' in self.natal_chart and 'element_balance' in self.natal_chart['ml_features']:
            return self.natal_chart['ml_features']['element_balance']
        return None

    def get_element_recommendation(self, elements):
        """Рекомендации на основе РАСЧЕТОВ элементного баланса"""
        if not elements:
            return None

        max_element = max(elements.items(), key=lambda x: x[1])
        element_value = max_element[1]

        recommendations = {
            'fire': f"Доминирует огонь ({element_value} планет) - используйте свою энергию и инициативу для новых начинаний",
            'earth': f"Доминирует земля ({element_value} планет) - сосредоточьтесь на практических задачах и стабильности",
            'air': f"Доминирует воздух ({element_value} планет) - развивайте общение, обучение и интеллектуальную деятельность",
            'water': f"Доминирует вода ({element_value} планет) - доверяйте интуиции и развивайте эмоциональную чувствительность"
        }

        return recommendations.get(max_element[0])

    def generate_prediction(self, target_date):
        """Основной метод генерации предсказания на основе РАСЧЕТОВ"""
        try:
            # Рассчитываем транзиты
            transits = self.calculate_transits(target_date)

            # Получаем натальные позиции
            natal_positions = {}
            for name, data in self.natal_chart['planets'].items():
                if name in self.planets_ml.values():
                    natal_positions[name] = {
                        'longitude': data['longitude'],
                        'sign': data['sign'],
                        'position_in_sign': data['position_in_sign']
                    }

            # Добавляем углы карты
            if 'angles' in self.natal_chart:
                natal_positions['Ascendant'] = {
                    'longitude': self.natal_chart['angles']['ascendant']['longitude'],
                    'sign': self.natal_chart['angles']['ascendant']['sign'],
                    'position_in_sign': self.natal_chart['angles']['ascendant']['longitude'] % 30
                }

            # Анализируем аспекты
            aspects = self.analyze_aspects(transits, natal_positions)

            # Генерируем персонализированные рекомендации и предостережения на основе РАСЧЕТОВ
            recommendations, warnings = self.generate_personal_recommendations(aspects, transits)

            # Добавляем рекомендации на основе элементного баланса если есть
            element_balance = self.analyze_natal_elements()
            if element_balance:
                element_recommendation = self.get_element_recommendation(element_balance)
                if element_recommendation and len(recommendations) < 4:
                    recommendations.append(element_recommendation)

            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'significant_aspects': aspects[:5],
                'recommendations': recommendations,
                'warnings': warnings,
                'transits_count': len(transits),
                'aspects_count': len(aspects),
                'strong_aspects_count': len([a for a in aspects if a['strength'] > 0.7])
            }

        except Exception as e:
            # В случае ошибки возвращаем пустое предсказание с информацией об ошибке
            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'significant_aspects': [],
                'recommendations': [f"Ошибка расчета: {str(e)} - обратитесь к администратору"],
                'warnings': ["Временные технические трудности при расчете аспектов"],
                'transits_count': 0,
                'aspects_count': 0,
                'strong_aspects_count': 0,
                'calculation_error': True
            }

    async def save_prediction_to_db(self, telegram_id: int, prediction_date: date):
        """Сохранение предсказания в базу данных"""
        prediction = self.generate_prediction(prediction_date)
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            existing_record = result.scalar_one_or_none()

            if existing_record:
                existing_record.predictions = prediction
                existing_record.updated_at = datetime.utcnow()
            else:
                new_record = NatalPredictions(
                    telegram_id=telegram_id,
                    predictions=prediction,
                    assistant_data={},
                )
                session.add(new_record)

            await session.commit()
        return prediction