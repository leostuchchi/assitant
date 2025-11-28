"""
Feature Engineering Module for Astra Project
Генерация ML-признаков и базовых инсайтов для AI Assistant
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import math

logger = logging.getLogger(__name__)


class FeatureEngine:
    """
    Движок для генерации нормализованных признаков и инсайтов
    Оптимизирован для интеграции с существующей архитектурой
    """

    def __init__(self):
        self.season_modifiers = {
            'winter': 0.9,  # Зима - немного сниженная энергия
            'spring': 1.1,  # Весна - повышенная энергия
            'summer': 1.0,  # Лето - нейтрально
            'autumn': 0.95  # Осень - слегка снижена
        }

        self.day_of_week_modifiers = {
            'Monday': 0.9,  # Понедельник - сложный день
            'Tuesday': 1.05,  # Вторник - продуктивный
            'Wednesday': 1.1,  # Среда - пик продуктивности
            'Thursday': 1.05,  # Четверг - стабильный
            'Friday': 1.0,  # Пятница - нейтральный
            'Saturday': 1.2,  # Суббота - высокая энергия
            'Sunday': 1.15  # Воскресенье - хорошая энергия
        }

    def calculate_ml_features(self, biorhythm_data: Dict, astro_data: Dict, target_date: date) -> Dict[str, float]:
        """
        Расчет нормализованных ML-признаков (0-1)
        Основной метод для AI Assistant
        """
        try:
            features = {}

            # 1. Базовые энергетические показатели (нормализованные 0-1)
            features.update(self._calculate_energy_features(biorhythm_data))

            # 2. Астрологические индексы
            features.update(self._calculate_astrological_features(astro_data))

            # 3. Контекстные модификаторы
            features.update(self._calculate_contextual_features(target_date))

            # 4. Составные показатели
            features.update(self._calculate_composite_features(features))

            logger.debug(f"✅ ML features calculated: {len(features)} features")
            return features

        except Exception as e:
            logger.error(f"❌ Error calculating ML features: {e}")
            return self._get_fallback_features()

    def _calculate_energy_features(self, biorhythm_data: Dict) -> Dict[str, float]:
        """Расчет энергетических признаков"""
        cycles = biorhythm_data.get('cycles', {})
        overall_energy = biorhythm_data.get('overall_energy', {})

        return {
            # Нормализованные биоритмы (0-1)
            'energy_physical': cycles.get('physical', {}).get('percentage', 0) / 100,
            'energy_emotional': cycles.get('emotional', {}).get('percentage', 0) / 100,
            'energy_intellectual': cycles.get('intellectual', {}).get('percentage', 0) / 100,

            # Общая энергия (0-1)
            'energy_overall': overall_energy.get('percentage', 0) / 100,

            # Специальные дни
            'is_critical_day': 1.0 if biorhythm_data.get('critical_days_count', 0) > 0 else 0.0,
            'is_peak_day': 1.0 if biorhythm_data.get('peak_days_count', 0) > 0 else 0.0,

            # Стабильность энергии (чем ближе к 0.5, тем стабильнее)
            'energy_stability': self._calculate_energy_stability(cycles)
        }

    def _calculate_astrological_features(self, astro_data: Dict) -> Dict[str, float]:
        """Расчет астрологических индексов"""
        aspects_count = astro_data.get('aspects_count', 0)
        strong_aspects = astro_data.get('strong_aspects_count', 0)
        retrograde_count = len(astro_data.get('retrograde_planets', []))

        return {
            # Интенсивность астрологической активности (0-1)
            'aspect_intensity': min(strong_aspects / 10.0, 1.0),  # макс 10 сильных аспектов
            'astro_activity': min(aspects_count / 20.0, 1.0),  # макс 20 аспектов

            # Ретроградное влияние (0-1)
            'retrograde_impact': min(retrograde_count / 5.0, 1.0),  # макс 5 ретроградных планет

            # Баланс астрологических влияний
            'harmonic_balance': self._calculate_harmonic_balance(astro_data),

            # Сложность астрологической конфигурации
            'astro_complexity': min((aspects_count * 0.3 + strong_aspects * 0.7) / 10.0, 1.0)
        }

    def _calculate_contextual_features(self, target_date: date) -> Dict[str, float]:
        """Расчет контекстных признаков (время, сезон)"""
        # День недели
        day_name = target_date.strftime('%A')
        day_modifier = self.day_of_week_modifiers.get(day_name, 1.0)

        # Сезон
        season = self._get_season(target_date)
        season_modifier = self.season_modifiers.get(season, 1.0)

        # Выходной день
        is_weekend = 1.0 if target_date.weekday() >= 5 else 0.0

        return {
            'day_of_week_effect': day_modifier,
            'seasonal_effect': season_modifier,
            'is_weekend': is_weekend,

            # Время месяца (0-1, где 0 - начало, 1 - конец)
            'month_progress': target_date.day / 31.0,

            # Время года (0-1)
            'year_progress': self._calculate_year_progress(target_date)
        }

    def _calculate_composite_features(self, base_features: Dict) -> Dict[str, float]:
        """Расчет составных показателей"""
        # Общий индекс продуктивности
        productivity = (
                base_features.get('energy_overall', 0.5) * 0.4 +
                base_features.get('energy_intellectual', 0.5) * 0.3 +
                base_features.get('day_of_week_effect', 1.0) * 0.2 +
                base_features.get('seasonal_effect', 1.0) * 0.1
        )

        # Индекс благополучия
        wellbeing = (
                base_features.get('energy_emotional', 0.5) * 0.5 +
                base_features.get('energy_physical', 0.5) * 0.3 +
                (1.0 - base_features.get('is_critical_day', 0.0)) * 0.2
        )

        # Адаптивность (способность справляться с нагрузками)
        adaptability = (
                base_features.get('energy_stability', 0.5) * 0.4 +
                (1.0 - base_features.get('retrograde_impact', 0.0)) * 0.3 +
                base_features.get('harmonic_balance', 0.5) * 0.3
        )

        return {
            'productivity_index': min(productivity, 1.0),
            'wellbeing_index': min(wellbeing, 1.0),
            'adaptability_index': min(adaptability, 1.0),

            # Общий score для быстрой оценки дня
            'daily_score': (
                    base_features.get('energy_overall', 0.5) * 0.3 +
                    base_features.get('productivity_index', 0.5) * 0.3 +
                    base_features.get('wellbeing_index', 0.5) * 0.2 +
                    base_features.get('adaptability_index', 0.5) * 0.2
            )
        }

    def generate_basic_insights(self, features: Dict, biorhythm_data: Dict) -> List[str]:
        """
        Генерация простых инсайтов для пользователя
        На основе рассчитанных features
        """
        insights = []

        try:
            # Инсайты по энергии
            energy_level = features.get('energy_overall', 0.5)
            if energy_level > 0.8:
                insights.append("💪 **Высокий уровень энергии** - идеальный день для сложных задач и важных решений")
            elif energy_level < 0.3:
                insights.append("🔄 **Энергия на низком уровне** - рекомендуется бережный режим и отдых")

            # Инсайты по продуктивности
            productivity = features.get('productivity_index', 0.5)
            if productivity > 0.7:
                insights.append("🚀 **Отличная продуктивность** - время для выполнения сложных проектов")
            elif productivity < 0.4:
                insights.append("📝 **Лучше сосредоточиться на рутине** - сложные задачи могут требовать больше усилий")

            # Инсайты по астрологии
            aspect_intensity = features.get('aspect_intensity', 0.0)
            if aspect_intensity > 0.7:
                insights.append("🌟 **Сильные астрологические влияния** - день может быть насыщенным событиями")

            retrograde_impact = features.get('retrograde_impact', 0.0)
            if retrograde_impact > 0.5:
                insights.append("🔄 **Ретроградные планеты активны** - будьте внимательны в общении и планировании")

            # Инсайты по контексту
            if features.get('is_weekend', 0.0) == 1.0:
                insights.append("🎉 **Выходной день** - хорошее время для отдыха и хобби")

            # Критические дни
            if features.get('is_critical_day', 0.0) == 1.0:
                insights.append("⚠️ **Критический день по биоритмам** - будьте осторожны в принятии решений")

            # Всегда добавляем общий инсайт если мало специфических
            if len(insights) < 2:
                daily_score = features.get('daily_score', 0.5)
                if daily_score > 0.6:
                    insights.append("🌈 **Хороший сбалансированный день** - подходит для большинства активностей")
                else:
                    insights.append(
                        "🌊 **День требует внимания к балансу** - планируйте дела с учетом энергетических циклов")

            return insights[:4]  # Максимум 4 инсайта

        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            return ["🔮 Используйте текущие данные для планирования своего дня"]

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====

    def _calculate_energy_stability(self, cycles: Dict) -> float:
        """Расчет стабильности энергии (чем ближе к 0.5, тем стабильнее)"""
        try:
            energies = [
                cycles.get('physical', {}).get('percentage', 50),
                cycles.get('emotional', {}).get('percentage', 50),
                cycles.get('intellectual', {}).get('percentage', 50)
            ]

            # Стабильность = 1 - (стандартное отклонение / 50)
            mean = sum(energies) / len(energies)
            variance = sum((x - mean) ** 2 for x in energies) / len(energies)
            std_dev = math.sqrt(variance)

            stability = 1.0 - (std_dev / 50.0)
            return max(0.0, min(1.0, stability))

        except Exception:
            return 0.5  # Нейтральное значение при ошибке

    def _calculate_harmonic_balance(self, astro_data: Dict) -> float:
        """Расчет баланса гармоничных/напряженных аспектов"""
        try:
            key_aspects = astro_data.get('key_aspects', [])
            if not key_aspects:
                return 0.5

            harmonious = 0
            challenging = 0

            for aspect in key_aspects:
                aspect_type = aspect.get('aspect', '')
                if aspect_type in ['trine', 'sextile']:
                    harmonious += 1
                elif aspect_type in ['square', 'opposition']:
                    challenging += 1

            total = harmonious + challenging
            if total == 0:
                return 0.5

            return harmonious / total

        except Exception:
            return 0.5

    def _get_season(self, target_date: date) -> str:
        """Определение сезона"""
        month = target_date.month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'

    def _calculate_year_progress(self, target_date: date) -> float:
        """Прогресс года (0-1)"""
        start_of_year = date(target_date.year, 1, 1)
        end_of_year = date(target_date.year, 12, 31)
        year_duration = (end_of_year - start_of_year).days
        current_progress = (target_date - start_of_year).days

        return current_progress / year_duration

    def _get_fallback_features(self) -> Dict[str, float]:
        """Fallback features при ошибках"""
        return {
            'energy_physical': 0.5,
            'energy_emotional': 0.5,
            'energy_intellectual': 0.5,
            'energy_overall': 0.5,
            'energy_stability': 0.5,
            'is_critical_day': 0.0,
            'is_peak_day': 0.0,
            'aspect_intensity': 0.0,
            'astro_activity': 0.0,
            'retrograde_impact': 0.0,
            'harmonic_balance': 0.5,
            'astro_complexity': 0.0,
            'day_of_week_effect': 1.0,
            'seasonal_effect': 1.0,
            'is_weekend': 0.0,
            'month_progress': 0.5,
            'year_progress': 0.5,
            'productivity_index': 0.5,
            'wellbeing_index': 0.5,
            'adaptability_index': 0.5,
            'daily_score': 0.5
        }

    def calculate_risk_factors(self, biorhythm_data: Dict, astro_data: Dict, ml_features: Dict) -> List[str]:
        """Расчет факторов риска"""
        risks = []

        try:
            # Анализ низкой энергии
            energy_level = ml_features.get('energy_overall', 0.5)
            if energy_level < 0.3:
                risks.append("Критически низкий уровень энергии")

            # Анализ критических дней
            if biorhythm_data.get('critical_days_count', 0) > 0:
                risks.append("Критический день по биоритмам")

            # Анализ сложных астрологических аспектов
            aspect_intensity = ml_features.get('aspect_intensity', 0)
            if aspect_intensity > 0.7:
                risks.append("Высокая интенсивность астрологических влияний")

            # Анализ ретроградных планет
            retrograde_impact = ml_features.get('retrograde_impact', 0)
            if retrograde_impact > 0.6:
                risks.append("Сильное влияние ретроградных планет")

        except Exception as e:
            logger.error(f"❌ Ошибка расчета факторов риска: {e}")

        return risks if risks else ["Стандартные меры предосторожности"]

    def calculate_opportunities(self, biorhythm_data: Dict, astro_data: Dict, ml_features: Dict) -> List[str]:
        """Расчет возможностей"""
        opportunities = []

        try:
            # Анализ высокой энергии
            energy_level = ml_features.get('energy_overall', 0.5)
            if energy_level > 0.8:
                opportunities.append("Идеальный уровень энергии для сложных задач")

            # Анализ пиковых дней
            if biorhythm_data.get('peak_days_count', 0) > 0:
                opportunities.append("Пиковый день для продуктивной работы")

            # Анализ гармоничных аспектов
            harmonic_balance = ml_features.get('harmonic_balance', 0.5)
            if harmonic_balance > 0.7:
                opportunities.append("Гармоничные астрологические влияния")

            # Анализ продуктивности
            productivity = ml_features.get('productivity_index', 0.5)
            if productivity > 0.7:
                opportunities.append("Высокий потенциал продуктивности")

        except Exception as e:
            logger.error(f"❌ Ошибка расчета возможностей: {e}")

        return opportunities if opportunities else ["Стандартные возможности дня"]


# Глобальный экземпляр для использования во всем проекте
feature_engine = FeatureEngine()