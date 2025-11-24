"""
Trend Analyzer Module for Astra Project
Анализ трендов и паттернов на основе исторических данных
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import statistics
import math
from enum import Enum

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Направление тренда"""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class TrendAnalyzer:
    """
    Анализатор трендов на основе исторических данных пользователя
    Оптимизирован для работы с существующей архитектурой DailyCalculations
    """

    def __init__(self):
        self.default_analysis_period = 30  # дней для анализа
        self.min_data_points = 7  # минимальное количество точек для анализа

    async def analyze_user_trends(self, telegram_id: int, period_days: int = None) -> Dict[str, Any]:
        """
        Основной метод анализа трендов пользователя
        Возвращает тренды энергии, паттерны и прогнозы
        """
        try:
            if period_days is None:
                period_days = self.default_analysis_period

            # Получаем исторические данные
            history = await self._get_user_history(telegram_id, period_days)

            if len(history) < self.min_data_points:
                logger.warning(f"⚠️ Not enough data for trend analysis: {len(history)} points")
                return self._get_fallback_trends()

            # Анализируем различные аспекты
            trends = {
                'analysis_period': f"{period_days} days",
                'data_points': len(history),
                'analysis_date': datetime.now().isoformat(),

                # Основные тренды энергии
                'energy_trends': await self._analyze_energy_trends(history),

                # Паттерны и цикличность
                'patterns': await self._detect_patterns(history),

                # Прогнозы
                'predictions': await self._generate_predictions(history),

                # Статистика
                'statistics': await self._calculate_statistics(history),

                # Рекомендации
                'recommendations': await self._generate_recommendations(history)
            }

            logger.info(f"✅ Trend analysis completed for {telegram_id}: {len(history)} data points")
            return trends

        except Exception as e:
            logger.error(f"❌ Error in trend analysis for {telegram_id}: {e}")
            return self._get_fallback_trends()

    async def _get_user_history(self, telegram_id: int, period_days: int) -> List[Dict]:
        """
        Получение исторических данных пользователя
        Интегрируется с существующей функцией get_user_calculation_history
        """
        try:
            from backend.prediction_services import get_user_calculation_history

            # Используем существующую функцию
            history = await get_user_calculation_history(telegram_id, period_days)

            # Обогащаем данными ML features если они есть
            enriched_history = []
            for record in history:
                enriched_record = {
                    'date': record['target_date'],
                    'energy_level': record['energy_level'],
                    'aspects_count': record['aspects_count'],
                    'timestamp': record['calculation_timestamp']
                }
                enriched_history.append(enriched_record)

            return enriched_history

        except Exception as e:
            logger.error(f"❌ Error getting user history: {e}")
            return []

    async def _analyze_energy_trends(self, history: List[Dict]) -> Dict[str, Any]:
        """Анализ трендов энергии"""
        try:
            energy_levels = [point['energy_level'] for point in history]
            dates = [point['date'] for point in history]

            # Линейный тренд
            trend_direction, trend_strength = self._calculate_linear_trend(energy_levels)

            # Волатильность
            volatility = self._calculate_volatility(energy_levels)

            # Стабильность
            stability = self._calculate_stability(energy_levels)

            # Текущий статус
            current_energy = energy_levels[-1] if energy_levels else 50
            avg_energy = statistics.mean(energy_levels) if energy_levels else 50

            return {
                'direction': trend_direction.value,
                'strength': round(trend_strength, 3),
                'volatility': round(volatility, 3),
                'stability_score': round(stability, 3),
                'current_energy': current_energy,
                'average_energy': round(avg_energy, 1),
                'energy_change': round(current_energy - avg_energy, 1),
                'min_energy': min(energy_levels) if energy_levels else 0,
                'max_energy': max(energy_levels) if energy_levels else 100,
                'trend_duration': self._estimate_trend_duration(energy_levels)
            }

        except Exception as e:
            logger.error(f"❌ Error analyzing energy trends: {e}")
            return self._get_fallback_energy_trends()

    async def _detect_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """Детекция паттернов в данных"""
        try:
            energy_levels = [point['energy_level'] for point in history]
            aspects_data = [point.get('aspects_count', 0) for point in history]

            patterns = {
                'weekly_patterns': self._detect_weekly_patterns(history),
                'peak_periods': self._find_peak_periods(history),
                'low_periods': self._find_low_periods(history),
                'recovery_patterns': self._analyze_recovery_patterns(history),
                'seasonal_trends': self._detect_seasonal_trends(history),
                'correlation_with_astrology': self._analyze_astrology_correlation(history)
            }

            return patterns

        except Exception as e:
            logger.error(f"❌ Error detecting patterns: {e}")
            return {}

    async def _generate_predictions(self, history: List[Dict]) -> Dict[str, Any]:
        """Генерация простых прогнозов"""
        try:
            energy_levels = [point['energy_level'] for point in history]

            if len(energy_levels) < 10:
                return {'confidence': 0.0, 'message': 'Not enough data for predictions'}

            # Простой прогноз на основе скользящего среднего
            next_energy = self._predict_next_energy(energy_levels)
            confidence = self._calculate_prediction_confidence(energy_levels)

            # Прогноз пиков и спадов
            next_peak = self._predict_next_peak(history)
            next_low = self._predict_next_low(history)

            return {
                'next_energy_level': round(next_energy, 1),
                'confidence': round(confidence, 3),
                'next_peak_prediction': next_peak,
                'next_low_prediction': next_low,
                'prediction_horizon': '3-5 days',
                'method': 'moving_average_simple'
            }

        except Exception as e:
            logger.error(f"❌ Error generating predictions: {e}")
            return {'confidence': 0.0, 'error': str(e)}

    async def _calculate_statistics(self, history: List[Dict]) -> Dict[str, Any]:
        """Расчет статистики"""
        try:
            energy_levels = [point['energy_level'] for point in history]
            aspects_data = [point.get('aspects_count', 0) for point in history]

            if not energy_levels:
                return {}

            return {
                'energy_mean': round(statistics.mean(energy_levels), 1),
                'energy_median': round(statistics.median(energy_levels), 1),
                'energy_std_dev': round(statistics.stdev(energy_levels) if len(energy_levels) > 1 else 0, 2),
                'energy_variance': round(statistics.variance(energy_levels) if len(energy_levels) > 1 else 0, 2),
                'high_energy_days': len([e for e in energy_levels if e > 70]),
                'low_energy_days': len([e for e in energy_levels if e < 30]),
                'average_aspects': round(statistics.mean(aspects_data) if aspects_data else 0, 1),
                'data_quality_score': self._calculate_data_quality(history)
            }

        except Exception as e:
            logger.error(f"❌ Error calculating statistics: {e}")
            return {}

    async def _generate_recommendations(self, history: List[Dict]) -> List[str]:
        """Генерация рекомендаций на основе трендов"""
        try:
            recommendations = []
            trends = await self._analyze_energy_trends(history)
            patterns = await self._detect_patterns(history)

            # Рекомендации по тренду энергии
            trend_direction = trends.get('direction', 'stable')
            energy_change = trends.get('energy_change', 0)

            if trend_direction == 'rising' and energy_change > 5:
                recommendations.append("📈 **Энергия растет** - хорошее время для начала новых проектов")
            elif trend_direction == 'falling' and energy_change < -5:
                recommendations.append("🔄 **Энергия снижается** - планируйте более легкие задачи")

            # Рекомендации по стабильности
            stability = trends.get('stability_score', 0.5)
            if stability > 0.8:
                recommendations.append("🎯 **Высокая стабильность энергии** - можно планировать на длительный срок")
            elif stability < 0.3:
                recommendations.append("🌊 **Энергия нестабильна** - будьте гибкими в планировании")

            # Рекомендации по паттернам
            weekly_patterns = patterns.get('weekly_patterns', {})
            best_day = weekly_patterns.get('best_day')
            if best_day:
                recommendations.append(f"💫 **Наиболее продуктивный день: {best_day}** - используйте для важных задач")

            return recommendations[:5]  # Максимум 5 рекомендаций

        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            return ["📊 Анализ трендов временно недоступен"]

    # ===== МАТЕМАТИЧЕСКИЕ МЕТОДЫ =====

    def _calculate_linear_trend(self, values: List[float]) -> Tuple[TrendDirection, float]:
        """Расчет линейного тренда"""
        if len(values) < 2:
            return TrendDirection.STABLE, 0.0

        n = len(values)
        x = list(range(n))

        # Простая линейная регрессия
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        except ZeroDivisionError:
            slope = 0

        # Сила тренда (нормализованная 0-1)
        strength = min(abs(slope) * 10, 1.0)

        # Направление тренда
        if strength < 0.1:
            return TrendDirection.STABLE, strength
        elif slope > 0:
            return TrendDirection.RISING, strength
        else:
            return TrendDirection.FALLING, strength

    def _calculate_volatility(self, values: List[float]) -> float:
        """Расчет волатильности (0-1)"""
        if len(values) < 2:
            return 0.0

        returns = []
        for i in range(1, len(values)):
            if values[i - 1] != 0:
                returns.append(abs(values[i] - values[i - 1]) / values[i - 1])

        if not returns:
            return 0.0

        volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
        return min(volatility * 10, 1.0)  # Нормализация

    def _calculate_stability(self, values: List[float]) -> float:
        """Расчет стабильности (0-1, где 1 - идеальная стабильность)"""
        if len(values) < 2:
            return 1.0

        volatility = self._calculate_volatility(values)
        return 1.0 - volatility

    def _estimate_trend_duration(self, values: List[float]) -> str:
        """Оценка длительности тренда"""
        if len(values) < 10:
            return "short_term"

        # Простой анализ persistence
        changes = [values[i] - values[i - 1] for i in range(1, len(values))]
        consistent_changes = sum(1 for change in changes if abs(change) > 2)

        ratio = consistent_changes / len(changes)
        if ratio > 0.7:
            return "long_term"
        elif ratio > 0.4:
            return "medium_term"
        else:
            return "short_term"

    def _detect_weekly_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """Детекция недельных паттернов"""
        try:
            day_energy = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday

            for point in history:
                try:
                    point_date = datetime.fromisoformat(point['date']).date()
                    day_of_week = point_date.weekday()
                    day_energy[day_of_week].append(point['energy_level'])
                except (ValueError, KeyError):
                    continue

            # Находим лучший и худший день
            day_avg = {}
            for day, energies in day_energy.items():
                if energies:
                    day_avg[day] = statistics.mean(energies)

            if not day_avg:
                return {}

            best_day_num = max(day_avg.items(), key=lambda x: x[1])[0]
            worst_day_num = min(day_avg.items(), key=lambda x: x[1])[0]

            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            return {
                'best_day': day_names[best_day_num],
                'worst_day': day_names[worst_day_num],
                'day_energies': {day_names[k]: round(v, 1) for k, v in day_avg.items()},
                'weekly_consistency': self._calculate_weekly_consistency(day_energy)
            }

        except Exception as e:
            logger.debug(f"Error detecting weekly patterns: {e}")
            return {}

    def _find_peak_periods(self, history: List[Dict]) -> List[Dict]:
        """Поиск пиковых периодов"""
        peaks = []
        energy_levels = [point['energy_level'] for point in history]
        dates = [point['date'] for point in history]

        for i in range(1, len(energy_levels) - 1):
            if (energy_levels[i] > energy_levels[i - 1] and
                    energy_levels[i] > energy_levels[i + 1] and
                    energy_levels[i] > 70):
                peaks.append({
                    'date': dates[i],
                    'energy_level': energy_levels[i],
                    'intensity': 'high' if energy_levels[i] > 85 else 'medium'
                })

        return peaks[:5]  # Только топ-5 пиков

    def _find_low_periods(self, history: List[Dict]) -> List[Dict]:
        """Поиск периодов низкой энергии"""
        lows = []
        energy_levels = [point['energy_level'] for point in history]
        dates = [point['date'] for point in history]

        for i in range(1, len(energy_levels) - 1):
            if (energy_levels[i] < energy_levels[i - 1] and
                    energy_levels[i] < energy_levels[i + 1] and
                    energy_levels[i] < 40):
                lows.append({
                    'date': dates[i],
                    'energy_level': energy_levels[i],
                    'intensity': 'critical' if energy_levels[i] < 25 else 'low'
                })

        return lows[:5]  # Только топ-5 спадов

    def _analyze_recovery_patterns(self, history: List[Dict]) -> Dict[str, Any]:
        """Анализ паттернов восстановления энергии"""
        # Упрощенная реализация - можно расширить
        return {
            'recovery_speed': 'medium',
            'typical_recovery_time': '2-3 days',
            'recovery_consistency': 0.75
        }

    def _detect_seasonal_trends(self, history: List[Dict]) -> Dict[str, Any]:
        """Детекция сезонных трендов"""
        # Упрощенная реализация
        return {
            'seasonal_impact': 'moderate',
            'best_season': 'spring',
            'seasonal_consistency': 0.65
        }

    def _analyze_astrology_correlation(self, history: List[Dict]) -> Dict[str, Any]:
        """Анализ корреляции с астрологическими данными"""
        try:
            energy_levels = [point['energy_level'] for point in history]
            aspects_counts = [point.get('aspects_count', 0) for point in history]

            if len(energy_levels) < 5 or len(aspects_counts) < 5:
                return {'correlation': 0.0, 'confidence': 'low'}

            # Простая корреляция
            if len(energy_levels) == len(aspects_counts):
                correlation = self._calculate_correlation(energy_levels, aspects_counts)
                return {
                    'correlation': round(correlation, 3),
                    'confidence': 'high' if abs(correlation) > 0.5 else 'low',
                    'interpretation': 'positive' if correlation > 0 else 'negative'
                }

            return {'correlation': 0.0, 'confidence': 'low'}

        except Exception:
            return {'correlation': 0.0, 'confidence': 'low'}

    def _predict_next_energy(self, energy_levels: List[float]) -> float:
        """Простой прогноз следующего значения энергии"""
        if len(energy_levels) < 3:
            return energy_levels[-1] if energy_levels else 50

        # Скользящее среднее за 3 дня
        window = min(3, len(energy_levels))
        return statistics.mean(energy_levels[-window:])

    def _predict_next_peak(self, history: List[Dict]) -> str:
        """Прогноз следующего пика"""
        # Упрощенная реализация
        next_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        return next_date

    def _predict_next_low(self, history: List[Dict]) -> str:
        """Прогноз следующего спада"""
        # Упрощенная реализация
        next_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        return next_date

    def _calculate_prediction_confidence(self, energy_levels: List[float]) -> float:
        """Расчет уверенности в прогнозе"""
        if len(energy_levels) < 10:
            return 0.3

        stability = self._calculate_stability(energy_levels)
        data_points = len(energy_levels)

        confidence = stability * min(data_points / 30.0, 1.0)
        return round(confidence, 3)

    def _calculate_weekly_consistency(self, day_energy: Dict[int, List[float]]) -> float:
        """Расчет консистентности недельных паттернов"""
        day_std = []
        for energies in day_energy.values():
            if len(energies) > 1:
                day_std.append(statistics.stdev(energies))

        if not day_std:
            return 0.5

        avg_std = statistics.mean(day_std)
        consistency = 1.0 - min(avg_std / 20.0, 1.0)  # Нормализация
        return round(consistency, 3)

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Расчет корреляции Пирсона"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_data_quality(self, history: List[Dict]) -> float:
        """Оценка качества данных"""
        if not history:
            return 0.0

        # Проверяем полноту данных
        complete_records = sum(1 for point in history
                               if point.get('energy_level') is not None
                               and point.get('aspects_count') is not None)

        completeness = complete_records / len(history)

        # Проверяем временную консистентность
        dates = [datetime.fromisoformat(point['date']).date() for point in history]
        date_diffs = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]

        if date_diffs:
            consistency = sum(1 for diff in date_diffs if diff == 1) / len(date_diffs)
        else:
            consistency = 1.0

        quality_score = (completeness + consistency) / 2
        return round(quality_score, 3)

    def _get_fallback_trends(self) -> Dict[str, Any]:
        """Fallback данные при ошибках"""
        return {
            'analysis_period': '0 days',
            'data_points': 0,
            'analysis_date': datetime.now().isoformat(),
            'energy_trends': self._get_fallback_energy_trends(),
            'patterns': {},
            'predictions': {'confidence': 0.0, 'message': 'Insufficient data'},
            'statistics': {},
            'recommendations': ['📊 Соберите больше данных для анализа трендов']
        }

    def _get_fallback_energy_trends(self) -> Dict[str, Any]:
        """Fallback тренды энергии"""
        return {
            'direction': 'stable',
            'strength': 0.0,
            'volatility': 0.0,
            'stability_score': 0.5,
            'current_energy': 50,
            'average_energy': 50,
            'energy_change': 0,
            'min_energy': 0,
            'max_energy': 100,
            'trend_duration': 'unknown'
        }


# Глобальный экземпляр для использования во всем проекте
trend_analyzer = TrendAnalyzer()