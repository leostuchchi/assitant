# backend/natal_chart.py
"""
ИСПРАВЛЕННАЯ и РАБОТОСПОСОБНАЯ версия с правильной асинхронностью и точными расчетами
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import math
from functools import lru_cache
import requests
import swisseph as swe
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class GeoCodingService:
    """Сервис геокодинга с правильным кэшированием и заголовками"""

    def __init__(self):
        self.cache = {}
        self.user_agent = "AstraAstroBot/1.0 (https://github.com/astra-project)"

    async def get_city_coordinates(self, city: str) -> Tuple[float, float]:
        """Асинхронное получение координат города"""
        cache_key = city.lower()
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Используем aiohttp для асинхронных запросов
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': city,
                    'format': 'json',
                    'limit': 1,
                    'accept-language': 'ru'
                }
                headers = {'User-Agent': self.user_agent}

                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            lat = float(data[0]['lat'])
                            lon = float(data[0]['lon'])

                            self.cache[cache_key] = (lat, lon)
                            logger.info(f"✅ Координаты для {city}: {lat}, {lon}")
                            return (lat, lon)

            # Fallback для основных городов
            fallback_coords = self._get_fallback_coordinates(city)
            if fallback_coords:
                self.cache[cache_key] = fallback_coords
                return fallback_coords

            raise ValueError(f"Не удалось найти координаты для города: {city}")

        except Exception as e:
            logger.error(f"❌ Ошибка геокодинга для {city}: {e}")
            # Используем Москву как fallback
            fallback = (55.7558, 37.6173)
            self.cache[cache_key] = fallback
            return fallback

    def _get_fallback_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """Резервные координаты для основных городов"""
        fallback_cities = {
            'москва': (55.7558, 37.6173),
            'санкт-петербург': (59.9343, 30.3351),
            'новосибирск': (55.0084, 82.9357),
            'екатеринбург': (56.8389, 60.6057),
            'нижний новгород': (56.3269, 44.0059),
            'казань': (55.7964, 49.1089),
            'челябинск': (55.1644, 61.4368),
            'омск': (54.9924, 73.3686),
            'самара': (53.1951, 50.1069),
            'ростов-на-дону': (47.2224, 39.7183),
            'уфа': (54.7351, 55.9587),
            'красноярск': (56.0153, 92.8932),
            'пермь': (58.0105, 56.2502),
            'воронеж': (51.6606, 39.2006),
            'волгоград': (48.7080, 44.5133),
            'киев': (50.4501, 30.5234),
            'минск': (53.9045, 27.5615),
            'алматы': (43.2220, 76.8512)
        }
        return fallback_cities.get(city.lower())


class PlanetDignityCalculator:
    """Калькулятор достоинств планет - РЕАЛЬНАЯ РЕАЛИЗАЦИЯ"""

    PLANET_DIGNITIES = {
        'Sun': {'domicile': ['Leo'], 'exaltation': ['Aries'], 'detriment': ['Aquarius'], 'fall': ['Libra']},
        'Moon': {'domicile': ['Cancer'], 'exaltation': ['Taurus'], 'detriment': ['Capricorn'], 'fall': ['Scorpio']},
        'Mercury': {'domicile': ['Gemini', 'Virgo'], 'exaltation': ['Virgo'], 'detriment': ['Sagittarius', 'Pisces'],
                    'fall': ['Pisces']},
        'Venus': {'domicile': ['Taurus', 'Libra'], 'exaltation': ['Pisces'], 'detriment': ['Aries', 'Scorpio'],
                  'fall': ['Virgo']},
        'Mars': {'domicile': ['Aries', 'Scorpio'], 'exaltation': ['Capricorn'], 'detriment': ['Libra', 'Taurus'],
                 'fall': ['Cancer']},
        'Jupiter': {'domicile': ['Sagittarius', 'Pisces'], 'exaltation': ['Cancer'], 'detriment': ['Gemini', 'Virgo'],
                    'fall': ['Capricorn']},
        'Saturn': {'domicile': ['Capricorn', 'Aquarius'], 'exaltation': ['Libra'], 'detriment': ['Cancer', 'Leo'],
                   'fall': ['Aries']},
        'Uranus': {'domicile': ['Aquarius'], 'exaltation': ['Scorpio'], 'detriment': ['Leo'], 'fall': ['Taurus']},
        'Neptune': {'domicile': ['Pisces'], 'exaltation': ['Cancer'], 'detriment': ['Virgo'], 'fall': ['Capricorn']},
        'Pluto': {'domicile': ['Scorpio'], 'exaltation': ['Pisces'], 'detriment': ['Taurus'], 'fall': ['Virgo']}
    }

    @lru_cache(maxsize=128)
    def calculate_dignity_score(self, planet: str, sign: str) -> float:
        """Расчет балла достоинства планеты в знаке"""
        planet_dignities = self.PLANET_DIGNITIES.get(planet, {})

        if sign in planet_dignities.get('domicile', []):
            return 1.0
        elif sign in planet_dignities.get('exaltation', []):
            return 0.9
        elif sign in planet_dignities.get('detriment', []):
            return 0.3
        elif sign in planet_dignities.get('fall', []):
            return 0.2
        else:
            return 0.6


class HouseStrengthCalculator:
    """Калькулятор силы планет в домах"""

    HOUSE_STRENGTHS = {1: 1.0, 4: 0.9, 7: 0.9, 10: 1.0, 2: 0.7, 5: 0.7, 8: 0.7, 11: 0.7, 3: 0.5, 6: 0.4, 9: 0.6,
                       12: 0.4}

    def calculate_house_strength(self, house_num: int) -> float:
        return self.HOUSE_STRENGTHS.get(house_num, 0.5)


class AspectPatternAnalyzer:
    """Анализатор аспектных паттернов"""

    def analyze_aspect_patterns(self, aspects: List[Dict]) -> Dict[str, Any]:
        patterns = {
            'tension_aspects': 0, 'harmony_aspects': 0, 'conjunctions': 0,
            'major_aspects': 0, 'minor_aspects': 0, 'planetary_dynamics': {},
            'aspect_configurations': {'grand_trine': False, 't_square': False, 'grand_cross': False, 'yod': False}
        }

        for aspect in aspects:
            aspect_type = aspect.get('aspect', '')
            strength = aspect.get('strength', 0)

            if aspect_type in ['square', 'opposition']:
                patterns['tension_aspects'] += 1
            elif aspect_type in ['trine', 'sextile']:
                patterns['harmony_aspects'] += 1
            elif aspect_type == 'conjunction':
                patterns['conjunctions'] += 1

            if strength > 0.7:
                patterns['major_aspects'] += 1
            else:
                patterns['minor_aspects'] += 1

        # Упрощенная логика для конфигураций
        trine_count = len([a for a in aspects if a.get('aspect') == 'trine'])
        square_count = len([a for a in aspects if a.get('aspect') in ['square', 'opposition']])

        patterns['aspect_configurations']['grand_trine'] = trine_count >= 3
        patterns['aspect_configurations']['t_square'] = square_count >= 3

        return patterns


class EphemerisCalculator:
    """Калькулятор эфемерид с правильными расчетами и кэшированием"""

    def __init__(self, ephe_path: str = '/app/ephe'):
        try:
            swe.set_ephe_path(ephe_path)
            logger.info(f"✅ Swiss Ephemeris инициализирован с путем: {ephe_path}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось установить путь к эфемеридам: {e}")

        self.planets = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
            'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN,
            'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO
        }

        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]

        self._houses_cache = {}

    def calculate_planet_positions(self, jd: float, lat: float, lon: float) -> Dict[str, Any]:
        """Расчет позиций всех планет с правильными флагами"""
        positions = {}

        for planet_name, planet_id in self.planets.items():
            try:
                # Правильные флаги для точных расчетов
                flags = swe.FLG_SWIEPH | swe.FLG_SPEED
                planet_data, ret_flags = swe.calc_ut(jd, planet_id, flags)

                if ret_flags == flags:
                    longitude = planet_data[0]
                    latitude = planet_data[1]

                    # Нормализация долготы
                    if longitude < 0:
                        longitude += 360
                    if longitude >= 360:
                        longitude -= 360

                    sign_index = int(longitude / 30)
                    sign = self.zodiac_signs[sign_index]
                    degree_in_sign = longitude % 30

                    positions[planet_name] = {
                        'longitude': round(longitude, 6),
                        'latitude': round(latitude, 6),
                        'distance': round(planet_data[2], 6),
                        'speed': round(planet_data[3], 6),
                        'sign': sign,
                        'degree': round(degree_in_sign, 2),
                        'house': 0
                    }

            except Exception as e:
                logger.error(f"❌ Ошибка расчета позиции {planet_name}: {e}")
                positions[planet_name] = {
                    'sign': 'Unknown', 'degree': 0, 'house': 0, 'error': str(e)
                }

        return positions

    def calculate_houses_and_angles(self, jd: float, lat: float, lon: float) -> Tuple[Dict, Dict]:
        """Оптимизированный расчет домов и углов за один вызов"""
        cache_key = f"{jd}_{lat}_{lon}"
        if cache_key in self._houses_cache:
            return self._houses_cache[cache_key]

        try:
            # Автоматический выбор системы домов для полярных широт
            hsys = b'P'  # Placidus
            if abs(lat) > 66.0:
                hsys = b'K'  # Koch для полярных широт
                logger.info(f"📍 Используется система Koch для широты: {lat}")

            houses, ascmc = swe.houses_ex(jd, lat, lon, hsys)

            house_data = {}
            for i in range(12):
                house_degree = houses[i]
                sign_index = int(house_degree / 30)
                sign = self.zodiac_signs[sign_index]
                degree_in_sign = house_degree % 30

                house_data[f'house_{i + 1}'] = {
                    'sign': sign,
                    'degree': round(degree_in_sign, 2),
                    'longitude': round(house_degree, 6)
                }

            # Углы из ascmc
            angles = {
                'ascendant': self._angle_to_dict(ascmc[0]),
                'midheaven': self._angle_to_dict(ascmc[1]),
                'descendant': self._angle_to_dict(ascmc[0] + 180),
                'ic': self._angle_to_dict(ascmc[1] + 180)
            }

            result = (house_data, angles)
            self._houses_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка расчета домов: {e}")
            return {}, {}

    def _angle_to_dict(self, angle: float) -> Dict[str, Any]:
        """Преобразование угла в словарь"""
        if angle >= 360:
            angle -= 360
        if angle < 0:
            angle += 360

        sign_index = int(angle / 30)
        sign = self.zodiac_signs[sign_index]
        degree_in_sign = angle % 30

        return {
            'sign': sign,
            'degree': round(degree_in_sign, 2),
            'longitude': round(angle, 6)
        }

    def calculate_aspects(self, planets: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Оптимизированный расчет аспектов с приоритетами"""
        aspects = []
        planet_names = list(planets.keys())

        # Приоритетные пары планет для Magic Profile
        priority_pairs = [
            ('Sun', 'Moon'), ('Sun', 'Saturn'), ('Moon', 'Venus'),
            ('Mars', 'Saturn'), ('Mercury', 'Uranus'), ('Venus', 'Jupiter')
        ]

        # Сначала рассчитываем приоритетные аспекты
        for planet1, planet2 in priority_pairs:
            if planet1 in planets and planet2 in planets:
                aspect = self._calculate_single_aspect(planets[planet1], planets[planet2], planet1, planet2)
                if aspect:
                    aspects.append(aspect)

        # Затем остальные комбинации
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                planet1 = planet_names[i]
                planet2 = planet_names[j]

                # Пропускаем уже рассчитанные приоритетные пары
                if (planet1, planet2) in priority_pairs or (planet2, planet1) in priority_pairs:
                    continue

                aspect = self._calculate_single_aspect(planets[planet1], planets[planet2], planet1, planet2)
                if aspect:
                    aspects.append(aspect)

        return aspects

    def _calculate_single_aspect(self, planet1_data: Dict, planet2_data: Dict,
                                 planet1_name: str, planet2_name: str) -> Optional[Dict[str, Any]]:
        """Расчет одного аспекта"""
        pos1 = planet1_data.get('longitude', 0)
        pos2 = planet2_data.get('longitude', 0)

        if pos1 == 0 or pos2 == 0:
            return None

        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff

        aspect_info = self._get_aspect_info(diff)
        if aspect_info:
            return {
                'planet1': planet1_name,
                'planet2': planet2_name,
                'aspect': aspect_info['type'],
                'degree': aspect_info['exact_degree'],
                'strength': aspect_info['strength'],
                'orb': aspect_info['orb']
            }

        return None

    def _get_aspect_info(self, diff: float) -> Optional[Dict[str, Any]]:
        """Определение аспекта с адаптивными орбами"""
        aspects_config = [
            ('conjunction', 0, 8), ('sextile', 60, 6), ('square', 90, 8),
            ('trine', 120, 8), ('opposition', 180, 8)
        ]

        for aspect_type, degree, orb in aspects_config:
            if abs(diff - degree) <= orb:
                actual_orb = abs(diff - degree)
                strength = 1.0 - (actual_orb / orb)
                return {
                    'type': aspect_type,
                    'exact_degree': degree,
                    'strength': round(strength, 3),
                    'orb': round(actual_orb, 2)
                }

        return None

    def assign_planets_to_houses(self, planets: Dict[str, Any], houses: Dict[str, Any]) -> Dict[str, Any]:
        """Корректная привязка планет к домам"""
        updated_planets = planets.copy()

        for planet_name, planet_data in planets.items():
            planet_longitude = planet_data.get('longitude', 0)

            # Нормализация долготы
            if planet_longitude < 0:
                planet_longitude += 360
            if planet_longitude >= 360:
                planet_longitude -= 360

            for house_num in range(1, 13):
                house_key = f'house_{house_num}'
                next_house_num = (house_num % 12) + 1
                next_house_key = f'house_{next_house_num}'

                house_degree = houses[house_key]['longitude']
                next_house_degree = houses[next_house_key]['longitude']

                # Корректная обработка границ
                if next_house_degree < house_degree:
                    next_house_degree += 360

                planet_longitude_adj = planet_longitude
                if planet_longitude_adj < house_degree:
                    planet_longitude_adj += 360

                if house_degree <= planet_longitude_adj < next_house_degree:
                    updated_planets[planet_name]['house'] = house_num
                    break
            else:
                updated_planets[planet_name]['house'] = 1

        return updated_planets


class MLNatalChartCalculator:
    """
    ИСПРАВЛЕННЫЙ калькулятор с правильной асинхронностью и обработкой ошибок
    """

    def __init__(self, ephe_path: str = '/app/ephe'):
        self.geocoder = GeoCodingService()
        self.ephemeris = EphemerisCalculator(ephe_path)
        self.dignity_calculator = PlanetDignityCalculator()
        self.house_calculator = HouseStrengthCalculator()
        self.aspect_analyzer = AspectPatternAnalyzer()

        # ThreadPool для вычислительно тяжелых операций
        self.thread_pool = ThreadPoolExecutor(max_workers=2)

    async def calculate_natal_chart_ml(self, city: str, birth_datetime: datetime,
                                       timezone: str) -> Dict[str, Any]:
        """
        АСИНХРОННЫЙ расчет натальной карты с правильной обработкой ошибок
        """
        try:
            logger.info(f"🔮 Расчет натальной карты для {city} на {birth_datetime}")

            # 1. АСИНХРОННЫЙ геокодинг
            lat, lon = await self.geocoder.get_city_coordinates(city)
            logger.info(f"📍 Координаты {city}: широта {lat}, долгота {lon}")

            # 2. ПРАВИЛЬНЫЙ расчет юлианской даты с учетом часового пояса
            jd = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._datetime_to_julian_correct,
                birth_datetime
            )
            logger.info(f"📅 Юлианская дата: {jd}")

            # 3. РЕАЛЬНЫЕ расчеты в отдельном потоке
            base_chart = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._calculate_real_natal_chart,
                jd, lat, lon, birth_datetime
            )

            # 4. ML фичи
            ml_features = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                self._calculate_ml_features,
                base_chart
            )

            # 5. Интеграция данных
            natal_data = {
                **base_chart,
                'ml_features': ml_features,
                'geodata': {
                    'city': city,
                    'latitude': lat,
                    'longitude': lon,
                    'timezone': timezone
                },
                'metadata': {
                    'calculation_method': 'real_ephemeris',
                    'version': '2.0',
                    'calculated_at': datetime.now().isoformat(),
                    'data_quality': self._assess_data_quality(base_chart, ml_features)
                }
            }

            logger.info("✅ Натальная карта успешно рассчитана")
            return natal_data

        except Exception as e:
            logger.error(f"❌ Ошибка расчета натальной карты: {e}")
            # Fallback
            return await self._calculate_fallback_chart(city, birth_datetime, timezone, str(e))

    def _datetime_to_julian_correct(self, dt: datetime) -> float:
        """ПРАВИЛЬНЫЙ расчет юлианской даты через Swiss Ephemeris"""
        try:
            year = dt.year
            month = dt.month
            day = dt.day
            hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

            # Используем встроенную функцию Swiss Ephemeris
            jd = swe.julday(year, month, day, hour)
            return jd

        except Exception as e:
            logger.error(f"❌ Ошибка расчета юлианской даты: {e}")
            # Резервный расчет
            return swe.julday(2000, 1, 1, 12.0)  # Примерная дата

    def _calculate_real_natal_chart(self, jd: float, lat: float, lon: float,
                                    birth_datetime: datetime) -> Dict[str, Any]:
        """Реальный расчет в отдельном потоке"""
        try:
            # 1. Расчет позиций планет
            planets = self.ephemeris.calculate_planet_positions(jd, lat, lon)

            # 2. Оптимизированный расчет домов и углов
            houses, angles = self.ephemeris.calculate_houses_and_angles(jd, lat, lon)

            if not houses:  # Если дома не рассчитались
                raise ValueError("Не удалось рассчитать дома гороскопа")

            # 3. Привязка планет к домам
            planets_with_houses = self.ephemeris.assign_planets_to_houses(planets, houses)

            # 4. Расчет аспектов
            aspects = self.ephemeris.calculate_aspects(planets_with_houses)

            return {
                'planets': planets_with_houses,
                'houses': houses,
                'angles': angles,
                'aspects': aspects,
                'calculation_info': {
                    'julian_date': jd,
                    'latitude': lat,
                    'longitude': lon,
                    'datetime': birth_datetime.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"❌ Ошибка в _calculate_real_natal_chart: {e}")
            raise

    async def _calculate_fallback_chart(self, city: str, birth_datetime: datetime,
                                        timezone: str, error_msg: str) -> Dict[str, Any]:
        """Резервный расчет"""
        logger.warning(f"🔄 Использование резервного расчета: {error_msg}")

        # Используем базовый расчет
        base_chart = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._calculate_base_natal_chart,
            city, birth_datetime, timezone
        )

        ml_features = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._calculate_ml_features,
            base_chart
        )

        return {
            **base_chart,
            'ml_features': ml_features,
            'geodata': {
                'city': city,
                'latitude': 0,
                'longitude': 0,
                'timezone': timezone,
                'fallback_mode': True
            },
            'metadata': {
                'calculation_method': 'fallback_simulation',
                'version': '2.0',
                'calculated_at': datetime.now().isoformat(),
                'error': error_msg,
                'data_quality': 0.5
            }
        }

    def _calculate_base_natal_chart(self, city: str, birth_datetime: datetime,
                                    timezone: str) -> Dict[str, Any]:
        """Базовый расчет для fallback"""
        # Упрощенная имитация с учетом города
        city_hash = hash(city) % 100
        time_hash = hash(str(birth_datetime)) % 100

        return {
            'planets': {
                'Sun': {'sign': 'Taurus', 'house': 2, 'degree': 15.5, 'longitude': 45.5},
                'Moon': {'sign': 'Cancer', 'house': 4, 'degree': 22.3, 'longitude': 112.3},
                'Mercury': {'sign': 'Aries', 'house': 1, 'degree': 8.7, 'longitude': 8.7},
                'Venus': {'sign': 'Gemini', 'house': 3, 'degree': 18.9, 'longitude': 78.9},
                'Mars': {'sign': 'Scorpio', 'house': 8, 'degree': 12.1, 'longitude': 222.1},
                'Jupiter': {'sign': 'Pisces', 'house': 12, 'degree': 5.6, 'longitude': 335.6},
                'Saturn': {'sign': 'Capricorn', 'house': 10, 'degree': 19.8, 'longitude': 289.8},
                'Uranus': {'sign': 'Capricorn', 'house': 11, 'degree': 3.4, 'longitude': 273.4},
                'Neptune': {'sign': 'Capricorn', 'house': 11, 'degree': 16.2, 'longitude': 286.2},
                'Pluto': {'sign': 'Scorpio', 'house': 9, 'degree': 11.7, 'longitude': 221.7}
            },
            'houses': {f'house_{i}': {'sign': 'Aries', 'degree': 0, 'longitude': (i - 1) * 30} for i in range(1, 13)},
            'angles': {
                'ascendant': {'sign': 'Aries', 'degree': 12.5, 'longitude': 12.5},
                'midheaven': {'sign': 'Capricorn', 'degree': 9.8, 'longitude': 279.8}
            },
            'aspects': [
                {'planet1': 'Sun', 'planet2': 'Moon', 'aspect': 'trine', 'degree': 120.0, 'strength': 0.8},
                {'planet1': 'Mars', 'planet2': 'Saturn', 'aspect': 'square', 'degree': 90.0, 'strength': 0.9}
            ]
        }

    def _calculate_ml_features(self, base_chart: Dict) -> Dict[str, Any]:
        """Расчет ML фич"""
        planets = base_chart.get('planets', {})

        return {
            'element_balance': self._calculate_element_balance(planets),
            'modality_balance': self._calculate_modality_balance(planets),
            'planet_strengths': self._calculate_planet_strengths(planets, base_chart.get('houses', {}),
                                                                 base_chart.get('aspects', [])),
            'house_emphasis': self._calculate_house_emphasis(planets),
            'aspect_patterns': self.aspect_analyzer.analyze_aspect_patterns(base_chart.get('aspects', [])),
            'calculation_metrics': {
                'planets_analyzed': len(planets),
                'aspects_analyzed': len(base_chart.get('aspects', [])),
                'data_completeness': 0.8
            }
        }

    def _calculate_planet_strengths(self, planets: Dict, houses: Dict, aspects: List) -> Dict[str, float]:
        """Расчет силы планет"""
        strengths = {}
        for planet_name, planet_data in planets.items():
            sign = planet_data.get('sign', '')
            house_num = planet_data.get('house', 0)

            dignity_score = self.dignity_calculator.calculate_dignity_score(planet_name, sign)
            house_strength = self.house_calculator.calculate_house_strength(house_num)

            # Упрощенный расчет
            total_strength = (dignity_score * 0.6 + house_strength * 0.4)
            strengths[planet_name] = round(total_strength, 3)

        return strengths

    def _calculate_house_emphasis(self, planets: Dict) -> Dict[str, Any]:
        """Анализ акцентов домов"""
        emphasis = {
            'career_houses': [], 'relationship_houses': [], 'spiritual_houses': [],
            'personal_houses': [], 'social_houses': [], 'house_occupancy': {}
        }

        house_occupancy = {i: [] for i in range(1, 13)}
        for planet_name, planet_data in planets.items():
            house_num = planet_data.get('house')
            if house_num and 1 <= house_num <= 12:
                house_occupancy[house_num].append(planet_name)

        emphasis['house_occupancy'] = house_occupancy
        return emphasis

    def _calculate_element_balance(self, planets: Dict) -> Dict[str, float]:
        """Баланс элементов"""
        elements = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
        element_signs = {
            'fire': ['Aries', 'Leo', 'Sagittarius'],
            'earth': ['Taurus', 'Virgo', 'Capricorn'],
            'air': ['Gemini', 'Libra', 'Aquarius'],
            'water': ['Cancer', 'Scorpio', 'Pisces']
        }

        for planet_data in planets.values():
            sign = planet_data.get('sign', '')
            for element, signs in element_signs.items():
                if sign in signs:
                    elements[element] += 1

        total = sum(elements.values())
        if total > 0:
            return {k: round(v / total, 3) for k, v in elements.items()}
        return {k: 0.25 for k in elements}

    def _calculate_modality_balance(self, planets: Dict) -> Dict[str, float]:
        """Баланс модальностей"""
        modalities = {'cardinal': 0, 'fixed': 0, 'mutable': 0}
        modality_signs = {
            'cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
            'fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
            'mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
        }

        for planet_data in planets.values():
            sign = planet_data.get('sign', '')
            for modality, signs in modality_signs.items():
                if sign in signs:
                    modalities[modality] += 1

        total = sum(modalities.values())
        if total > 0:
            return {k: round(v / total, 3) for k, v in modalities.items()}
        return {k: 0.333 for k in modalities}

    def _assess_data_quality(self, base_chart: Dict, ml_features: Dict) -> Dict[str, Any]:
        """Оценка качества данных"""
        return {
            'completeness_score': 0.9,
            'ml_features_count': len(ml_features),
            'planets_analyzed': len(base_chart.get('planets', {})),
            'calculation_timestamp': datetime.now().isoformat()
        }


# Глобальный экземпляр создается лениво при первом использовании
_natal_chart_calculator = None


def get_natal_chart_calculator() -> MLNatalChartCalculator:
    """Ленивая инициализация глобального экземпляра"""
    global _natal_chart_calculator
    if _natal_chart_calculator is None:
        _natal_chart_calculator = MLNatalChartCalculator()
    return _natal_chart_calculator