"""
Insight Generator Module for Astra Project
Генерация умных инсайтов и персонализированных рекомендаций на основе всех доступных данных
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import statistics
import math
import asyncio

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Типы генерируемых инсайтов"""
    ENERGY = "energy"
    PRODUCTIVITY = "productivity"
    RELATIONSHIPS = "relationships"
    HEALTH = "health"
    DECISION_MAKING = "decision_making"
    PERSONAL_GROWTH = "personal_growth"
    CAREER = "career"
    FINANCE = "finance"


class InsightLevel(Enum):
    """Уровень важности инсайта"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InsightGenerator:
    """
    Генератор умных инсайтов и рекомендаций
    Интегрируется с существующей системой расчетов и ML-фичами
    """

    def __init__(self):
        self.insight_templates = self._initialize_insight_templates()
        self.planet_meanings = self._initialize_planet_meanings()
        self.aspect_interpretations = self._initialize_aspect_interpretations()

    async def generate_comprehensive_insights(
            self,
            telegram_id: int,
            target_date: date = None,
            insight_types: List[InsightType] = None
    ) -> Dict[str, Any]:
        """
        Генерация комплексных инсайтов на основе всех доступных данных
        Основной метод для интеграции с существующей системой
        """
        try:
            if target_date is None:
                target_date = date.today()

            if insight_types is None:
                insight_types = list(InsightType)

            logger.info(f"🔮 Генерация инсайтов для {telegram_id} на {target_date}")

            # 1. Собираем все необходимые данные
            calculation_data = await self._gather_calculation_data(telegram_id, target_date)

            if not calculation_data:
                return self._get_fallback_insights()

            # 2. Генерируем ML-фичи (используем существующий движок)
            ml_features = await self._generate_ml_features(calculation_data, target_date)

            # 3. Генерируем инсайты по каждому запрошенному типу
            insights = {}
            for insight_type in insight_types:
                type_insights = await self._generate_typed_insights(
                    insight_type, calculation_data, ml_features, target_date
                )
                insights[insight_type.value] = type_insights

            # 4. Формируем общую сводку
            summary = await self._generate_insight_summary(insights, ml_features)

            result = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'insights': insights,
                'summary': summary,
                'ml_features_used': list(ml_features.keys()),
                'generated_at': datetime.now().isoformat(),
                'data_sources': self._get_used_data_sources(calculation_data)
            }

            logger.info(f"✅ Сгенерировано инсайтов: {self._count_total_insights(insights)}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка генерации инсайтов для {telegram_id}: {e}")
            return self._get_fallback_insights()

    async def generate_daily_insights(self, telegram_id: int, target_date: date = None) -> Dict[str, Any]:
        """
        Генерация ежедневных инсайтов для пользователя
        Оптимизированная версия для интеграции с ботом
        """
        try:
            if target_date is None:
                target_date = date.today()

            # Основные типы инсайтов для ежедневного использования
            daily_types = [
                InsightType.ENERGY,
                InsightType.PRODUCTIVITY,
                InsightType.DECISION_MAKING,
                InsightType.HEALTH
            ]

            insights = await self.generate_comprehensive_insights(
                telegram_id, target_date, daily_types
            )

            # Форматируем для пользователя
            formatted_insights = self._format_insights_for_user(insights)

            return {
                'success': True,
                'date': target_date.isoformat(),
                'key_insights': formatted_insights['key_insights'],
                'recommendations': formatted_insights['recommendations'],
                'energy_forecast': formatted_insights['energy_forecast'],
                'risk_factors': formatted_insights['risk_factors']
            }

        except Exception as e:
            logger.error(f"❌ Ошибка генерации ежедневных инсайтов: {e}")
            return {'success': False, 'error': str(e)}

    async def _gather_calculation_data(self, telegram_id: int, target_date: date) -> Optional[Dict[str, Any]]:
        """
        Сбор всех расчетных данных через существующие сервисы
        Интеграция с текущей архитектурой
        """
        try:
            # Используем существующий сервис расчетов
            from backend.calculation_services import calculation_service

            # Получаем полный пакет расчетов
            calculation_package = await calculation_service.get_full_calculation_package(
                telegram_id, target_date
            )

            if not calculation_package.get('success'):
                logger.warning(f"⚠️ Не удалось получить расчетные данные для {telegram_id}")
                return None

            # Дополнительные данные для углубленного анализа
            additional_data = await self._gather_additional_data(telegram_id, target_date)

            return {
                'calculation_package': calculation_package,
                'additional_data': additional_data,
                'user_context': calculation_package.get('user_context', {})
            }

        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных для инсайтов: {e}")
            return None

    async def _gather_additional_data(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Сбор дополнительных данных для улучшения инсайтов"""
        try:
            additional_data = {}

            # Исторические данные для анализа трендов
            from backend.prediction_services import get_user_calculation_history
            history = await get_user_calculation_history(telegram_id, 14)  # 2 недели
            additional_data['history'] = history

            # Данные астропрофиля
            from backend.chart_services import get_user_astro_profile
            astro_profile = await get_user_astro_profile(telegram_id)
            additional_data['astro_profile'] = astro_profile

            # Статистика пользователя
            from backend.assistant import assistant
            user_stats = await assistant.get_user_statistics(telegram_id)
            additional_data['user_stats'] = user_stats

            return additional_data

        except Exception as e:
            logger.debug(f"⚠️ Не удалось собрать дополнительные данные: {e}")
            return {}

    async def _generate_ml_features(self, calculation_data: Dict, target_date: date) -> Dict[str, float]:
        """
        Генерация ML-фич через существующий FeatureEngine
        Интеграция с feature_engineering.py
        """
        try:
            from backend.feature_engineering import feature_engine

            calculation_package = calculation_data.get('calculation_package', {})
            calculations = calculation_package.get('calculations', {})

            biorhythm_data = calculations.get('biorhythms', {})
            astro_data = calculations.get('astrology', {})

            # Используем существующий движок фич
            ml_features = feature_engine.calculate_ml_features(
                biorhythm_data, astro_data, target_date
            )

            # Дополнительные фичи для инсайтов
            ml_features.update(self._calculate_insight_specific_features(
                calculation_data, ml_features
            ))

            return ml_features

        except Exception as e:
            logger.error(f"❌ Ошибка генерации ML-фич: {e}")
            return {}

    async def _generate_typed_insights(
            self,
            insight_type: InsightType,
            calculation_data: Dict,
            ml_features: Dict[str, float],
            target_date: date
    ) -> List[Dict[str, Any]]:
        """Генерация инсайтов конкретного типа"""
        try:
            insights = []

            if insight_type == InsightType.ENERGY:
                insights = self._generate_energy_insights(calculation_data, ml_features)
            elif insight_type == InsightType.PRODUCTIVITY:
                insights = self._generate_productivity_insights(calculation_data, ml_features)
            elif insight_type == InsightType.RELATIONSHIPS:
                insights = self._generate_relationship_insights(calculation_data, ml_features)
            elif insight_type == InsightType.HEALTH:
                insights = self._generate_health_insights(calculation_data, ml_features)
            elif insight_type == InsightType.DECISION_MAKING:
                insights = self._generate_decision_insights(calculation_data, ml_features)
            elif insight_type == InsightType.PERSONAL_GROWTH:
                insights = self._generate_personal_growth_insights(calculation_data, ml_features)
            elif insight_type == InsightType.CAREER:
                insights = self._generate_career_insights(calculation_data, ml_features)
            elif insight_type == InsightType.FINANCE:
                insights = self._generate_finance_insights(calculation_data, ml_features)

            # Фильтруем и сортируем инсайты по релевантности
            filtered_insights = self._filter_insights_by_relevance(insights, ml_features)
            return filtered_insights[:5]  # Максимум 5 инсайтов каждого типа

        except Exception as e:
            logger.error(f"❌ Ошибка генерации инсайтов типа {insight_type}: {e}")
            return []

    def _generate_energy_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов об энергии и витальности"""
        insights = []

        energy_level = ml_features.get('energy_overall', 0.5)
        physical_energy = ml_features.get('energy_physical', 0.5)
        emotional_energy = ml_features.get('energy_emotional', 0.5)
        intellectual_energy = ml_features.get('energy_intellectual', 0.5)

        # Анализ общей энергии
        if energy_level > 0.8:
            insights.append({
                'type': 'energy_peak',
                'title': 'Пик энергии',
                'message': 'Сегодня у вас исключительно высокий уровень энергии - идеальное время для сложных задач и важных начинаний.',
                'level': InsightLevel.HIGH,
                'confidence': 0.9,
                'actions': ['начать новый проект', 'провести важные встречи', 'заняться спортом']
            })
        elif energy_level < 0.3:
            insights.append({
                'type': 'energy_low',
                'title': 'Энергия на минимуме',
                'message': 'Уровень энергии сегодня низкий. Рекомендуется бережный режим и отдых.',
                'level': InsightLevel.HIGH,
                'confidence': 0.8,
                'actions': ['делать перерывы', 'отложить сложные задачи', 'практиковать отдых']
            })

        # Баланс энергий
        energy_diff = max(physical_energy, emotional_energy, intellectual_energy) - min(physical_energy,
                                                                                        emotional_energy,
                                                                                        intellectual_energy)
        if energy_diff > 0.4:
            dominant = 'физическая' if physical_energy == max(physical_energy, emotional_energy,
                                                              intellectual_energy) else \
                'эмоциональная' if emotional_energy == max(physical_energy, emotional_energy,
                                                           intellectual_energy) else 'интеллектуальная'

            insights.append({
                'type': 'energy_imbalance',
                'title': 'Дисбаланс энергий',
                'message': f'Заметный перекос в {dominant} энергию. Попробуйте сбалансировать активность.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.7,
                'actions': ['медитация', 'сбалансированные упражнения', 'осознанное дыхание']
            })

        return insights

    def _generate_productivity_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о продуктивности"""
        insights = []

        productivity_index = ml_features.get('productivity_index', 0.5)
        intellectual_energy = ml_features.get('energy_intellectual', 0.5)
        astro_complexity = ml_features.get('astro_complexity', 0.0)

        if productivity_index > 0.7 and intellectual_energy > 0.6:
            insights.append({
                'type': 'productivity_peak',
                'title': 'Идеальный день для работы',
                'message': 'Отличное сочетание ментальной энергии и продуктивности. Сложные задачи будут даваться легко.',
                'level': InsightLevel.HIGH,
                'confidence': 0.85,
                'actions': ['аналитическая работа', 'обучение', 'стратегическое планирование']
            })

        if astro_complexity > 0.6:
            insights.append({
                'type': 'complexity_warning',
                'title': 'Сложный астрологический фон',
                'message': 'Множество аспектов может создавать информационный шум. Сосредоточьтесь на главном.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.7,
                'actions': ['приоритизация задач', 'избегание многозадачности', 'фокус на одном проекте']
            })

        return insights

    def _generate_relationship_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов об отношениях и коммуникации"""
        insights = []

        emotional_energy = ml_features.get('energy_emotional', 0.5)
        harmonic_balance = ml_features.get('harmonic_balance', 0.5)

        # Анализ астрологических данных для отношений
        calculation_package = calculation_data.get('calculation_package', {})
        astrology_data = calculation_package.get('calculations', {}).get('astrology', {})
        aspects = astrology_data.get('key_aspects', [])

        # Поиск аспектов связанных с отношениями (Венера, Луна)
        relationship_aspects = [a for a in aspects if a.get('natal_planet') in ['Venus', 'Moon'] or
                                a.get('transit_planet') in ['Venus', 'Moon']]

        if relationship_aspects and emotional_energy > 0.6:
            insights.append({
                'type': 'relationships_favorable',
                'title': 'Благоприятный день для общения',
                'message': 'Энергия способствует гармоничным отношениям и пониманию.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.75,
                'actions': ['социальные мероприятия', 'сердечные разговоры', 'укрепление связей']
            })

        return insights

    def _generate_health_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о здоровье"""
        insights = []

        physical_energy = ml_features.get('energy_physical', 0.5)
        is_critical_day = ml_features.get('is_critical_day', 0.0)

        if is_critical_day:
            insights.append({
                'type': 'health_critical',
                'title': 'Критический день для здоровья',
                'message': 'Биоритмы указывают на повышенную уязвимость организма. Берегите себя.',
                'level': InsightLevel.HIGH,
                'confidence': 0.8,
                'actions': ['избегать перегрузок', 'здоровое питание', 'достаточный сон']
            })

        if physical_energy > 0.7:
            insights.append({
                'type': 'health_optimal',
                'title': 'Отличное физическое состояние',
                'message': 'Идеальное время для физической активности и спорта.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.8,
                'actions': ['тренировка', 'активный отдых', 'физический труд']
            })

        return insights

    def _generate_decision_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о принятии решений"""
        insights = []

        intellectual_energy = ml_features.get('energy_intellectual', 0.5)
        energy_stability = ml_features.get('energy_stability', 0.5)
        retrograde_impact = ml_features.get('retrograde_impact', 0.0)

        if intellectual_energy > 0.7 and energy_stability > 0.6:
            insights.append({
                'type': 'decision_clarity',
                'title': 'Ясность мышления',
                'message': 'Идеальные условия для принятия важных решений и стратегического планирования.',
                'level': InsightLevel.HIGH,
                'confidence': 0.85,
                'actions': ['анализ вариантов', 'долгосрочное планирование', 'важные выборы']
            })

        if retrograde_impact > 0.5:
            insights.append({
                'type': 'decision_caution',
                'title': 'Время обдумывания',
                'message': 'Ретроградные планеты рекомендуют перепроверять решения и избегать поспешных выводов.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.7,
                'actions': ['консультации', 'анализ рисков', 'отсрочка решений']
            })

        return insights

    def _generate_personal_growth_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о личностном росте"""
        insights = []

        wellbeing_index = ml_features.get('wellbeing_index', 0.5)
        adaptability_index = ml_features.get('adaptability_index', 0.5)

        if wellbeing_index > 0.7 and adaptability_index > 0.6:
            insights.append({
                'type': 'growth_optimal',
                'title': 'Благоприятное время для роста',
                'message': 'Сочетание внутренней гармонии и адаптивности создает идеальные условия для развития.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.8,
                'actions': ['изучение нового', 'саморефлексия', 'постановка целей']
            })

        return insights

    def _generate_career_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о карьере"""
        insights = []

        productivity_index = ml_features.get('productivity_index', 0.5)

        # Анализ астрологических данных для карьеры (Сатурн, Юпитер, MC)
        calculation_package = calculation_data.get('calculation_package', {})
        astrology_data = calculation_package.get('calculations', {}).get('astrology', {})
        aspects = astrology_data.get('key_aspects', [])

        career_aspects = [a for a in aspects if a.get('natal_planet') in ['Saturn', 'Jupiter', 'Midheaven'] or
                          a.get('transit_planet') in ['Saturn', 'Jupiter', 'Midheaven']]

        if career_aspects and productivity_index > 0.6:
            insights.append({
                'type': 'career_opportunity',
                'title': 'Карьерные возможности',
                'message': 'Астрологические аспекты благоприятствуют профессиональному росту и признанию.',
                'level': InsightLevel.MEDIUM,
                'confidence': 0.75,
                'actions': ['профессиональное общение', 'представление идей', 'сетworking']
            })

        return insights

    def _generate_finance_insights(self, calculation_data: Dict, ml_features: Dict) -> List[Dict[str, Any]]:
        """Генерация инсайтов о финансах"""
        insights = []

        # Анализ астрологических данных для финансов (Венера, Юпитер)
        calculation_package = calculation_data.get('calculation_package', {})
        astrology_data = calculation_package.get('calculations', {}).get('astrology', {})
        aspects = astrology_data.get('key_aspects', [])

        finance_aspects = [a for a in aspects if a.get('natal_planet') in ['Venus', 'Jupiter'] or
                           a.get('transit_planet') in ['Venus', 'Jupiter']]

        if finance_aspects:
            positive_aspects = [a for a in finance_aspects if a.get('aspect') in ['trine', 'sextile']]
            if positive_aspects:
                insights.append({
                    'type': 'finance_positive',
                    'title': 'Благоприятные финансовые аспекты',
                    'message': 'Астрологическая конфигурация способствует финансовым операциям и инвестициям.',
                    'level': InsightLevel.MEDIUM,
                    'confidence': 0.7,
                    'actions': ['финансовое планирование', 'анализ инвестиций', 'бюджетирование']
                })

        return insights

    async def _generate_insight_summary(self, insights: Dict, ml_features: Dict) -> Dict[str, Any]:
        """Генерация общей сводки инсайтов"""
        try:
            # Собираем все инсайты в один список
            all_insights = []
            for insight_list in insights.values():
                all_insights.extend(insight_list)

            # Анализируем общую картину
            high_priority = [i for i in all_insights if i.get('level') == InsightLevel.HIGH]
            medium_priority = [i for i in all_insights if i.get('level') == InsightLevel.MEDIUM]

            daily_score = ml_features.get('daily_score', 0.5)
            if daily_score > 0.7:
                overall_mood = "отличный"
            elif daily_score > 0.5:
                overall_mood = "хороший"
            elif daily_score > 0.3:
                overall_mood = "умеренный"
            else:
                overall_mood = "сложный"

            return {
                'total_insights': len(all_insights),
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'overall_mood': overall_mood,
                'key_focus_areas': self._identify_focus_areas(all_insights),
                'risk_level': self._calculate_risk_level(all_insights),
                'opportunity_level': self._calculate_opportunity_level(all_insights)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка генерации сводки: {e}")
            return {}

    def _format_insights_for_user(self, insights_data: Dict) -> Dict[str, Any]:
        """Форматирование инсайтов для отображения пользователю"""
        try:
            insights = insights_data.get('insights', {})
            summary = insights_data.get('summary', {})

            # Собираем ключевые инсайты (высокий приоритет)
            key_insights = []
            for insight_type, insight_list in insights.items():
                high_priority = [i for i in insight_list if i.get('level') == InsightLevel.HIGH]
                key_insights.extend(high_priority[:2])  # Максимум 2 высокоприоритетных на тип

            # Формируем рекомендации
            recommendations = []
            for insight in key_insights[:5]:  # Топ-5 рекомендаций
                actions = insight.get('actions', [])
                if actions:
                    recommendations.extend(actions[:2])

            # Прогноз энергии
            energy_forecast = {
                'level': summary.get('overall_mood', 'умеренный'),
                'description': self._get_energy_description(summary.get('overall_mood'))
            }

            # Факторы риска
            risk_factors = []
            if summary.get('risk_level') == 'high':
                risk_factors.append("Высокая нагрузка требует осторожности")
            if summary.get('high_priority_count', 0) > 3:
                risk_factors.append("Множество важных аспектов требует внимания")

            return {
                'key_insights': key_insights[:3],  # Топ-3 ключевых инсайта
                'recommendations': list(set(recommendations))[:5],  # Уникальные рекомендации
                'energy_forecast': energy_forecast,
                'risk_factors': risk_factors
            }

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования инсайтов: {e}")
            return {'key_insights': [], 'recommendations': []}

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====

    def _calculate_insight_specific_features(self, calculation_data: Dict, base_features: Dict) -> Dict[str, float]:
        """Расчет дополнительных фич для инсайтов"""
        additional_features = {}

        try:
            # Анализ сложности дня
            calculation_package = calculation_data.get('calculation_package', {})
            calculations = calculation_package.get('calculations', {})

            astrology_data = calculations.get('astrology', {})
            aspects_count = astrology_data.get('aspects_count', 0)
            strong_aspects = astrology_data.get('strong_aspects_count', 0)

            additional_features['day_complexity'] = min((aspects_count * 0.3 + strong_aspects * 0.7) / 15.0, 1.0)

            # Анализ баланса энергий
            energies = [
                base_features.get('energy_physical', 0.5),
                base_features.get('energy_emotional', 0.5),
                base_features.get('energy_intellectual', 0.5)
            ]
            energy_balance = 1.0 - (max(energies) - min(energies))
            additional_features['energy_balance'] = energy_balance

        except Exception as e:
            logger.debug(f"⚠️ Ошибка расчета дополнительных фич: {e}")

        return additional_features

    def _filter_insights_by_relevance(self, insights: List[Dict], ml_features: Dict) -> List[Dict]:
        """Фильтрация инсайтов по релевантности"""
        try:
            relevant_insights = []

            for insight in insights:
                confidence = insight.get('confidence', 0.5)
                # Повышаем уверенность для инсайтов с высокими показателями соответствующих фич
                if 'energy' in insight.get('type', ''):
                    energy_level = ml_features.get('energy_overall', 0.5)
                    if energy_level > 0.7 or energy_level < 0.3:
                        confidence *= 1.2

                if confidence >= 0.6:  # Минимальный порог уверенности
                    insight['confidence'] = min(confidence, 1.0)
                    relevant_insights.append(insight)

            # Сортируем по уверенности
            relevant_insights.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            return relevant_insights

        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации инсайтов: {e}")
            return insights

    def _identify_focus_areas(self, insights: List[Dict]) -> List[str]:
        """Определение ключевых областей фокуса"""
        focus_areas = set()

        for insight in insights:
            insight_type = insight.get('type', '')
            if 'energy' in insight_type:
                focus_areas.add('энергия')
            elif 'productivity' in insight_type or 'career' in insight_type:
                focus_areas.add('работа')
            elif 'health' in insight_type:
                focus_areas.add('здоровье')
            elif 'relationship' in insight_type:
                focus_areas.add('отношения')
            elif 'decision' in insight_type:
                focus_areas.add('решения')

        return list(focus_areas)[:3]  # Максимум 3 области

    def _calculate_risk_level(self, insights: List[Dict]) -> str:
        """Расчет уровня риска"""
        high_risk_insights = len([i for i in insights if i.get('level') == InsightLevel.HIGH and
                                  'warning' in i.get('type', '').lower() or
                                  'critical' in i.get('type', '').lower()])

        if high_risk_insights >= 2:
            return "high"
        elif high_risk_insights >= 1:
            return "medium"
        else:
            return "low"

    def _calculate_opportunity_level(self, insights: List[Dict]) -> str:
        """Расчет уровня возможностей"""
        opportunity_insights = len([i for i in insights if 'opportunity' in i.get('type', '').lower() or
                                    'peak' in i.get('type', '').lower() or
                                    'optimal' in i.get('type', '').lower()])

        if opportunity_insights >= 2:
            return "high"
        elif opportunity_insights >= 1:
            return "medium"
        else:
            return "low"

    def _get_energy_description(self, mood: str) -> str:
        """Описание энергетического состояния"""
        descriptions = {
            "отличный": "Высокий уровень энергии и мотивации",
            "хороший": "Сбалансированное состояние, подходящее для большинства задач",
            "умеренный": "Стабильный уровень, требует разумного распределения сил",
            "сложный": "Энергия требует бережного отношения и отдыха"
        }
        return descriptions.get(mood, "Стабильное энергетическое состояние")

    def _count_total_insights(self, insights: Dict) -> int:
        """Подсчет общего количества инсайтов"""
        return sum(len(insight_list) for insight_list in insights.values())

    def _get_used_data_sources(self, calculation_data: Dict) -> List[str]:
        """Определение использованных источников данных"""
        sources = ['biorhythms', 'astrology', 'psychomatrix']

        calculation_package = calculation_data.get('calculation_package', {})
        calculations = calculation_package.get('calculations', {})

        used_sources = []
        for source in sources:
            if calculations.get(source):
                used_sources.append(source)

        return used_sources

    def _initialize_insight_templates(self) -> Dict:
        """Инициализация шаблонов инсайтов"""
        return {
            'energy_high': "Высокий уровень энергии ({level}%) идеален для {activities}",
            'energy_low': "Низкая энергия ({level}%) требует бережного режима. Рекомендуется {actions}",
            'productivity_peak': "Пик продуктивности - лучшее время для {tasks}",
            'complexity_warning': "Сложная астрологическая конфигурация требует {precautions}"
        }

    def _initialize_planet_meanings(self) -> Dict:
        """Значения планет для интерпретации"""
        return {
            'Sun': 'личность, воля, творчество',
            'Moon': 'эмоции, интуиция, потребности',
            'Mercury': 'коммуникация, мышление, обучение',
            'Venus': 'любовь, красота, гармония',
            'Mars': 'энергия, действие, мотивация',
            'Jupiter': 'расширение, удача, рост',
            'Saturn': 'дисциплина, ответственность, структура',
            'Uranus': 'изменения, инновации, свобода',
            'Neptune': 'интуиция, духовность, творчество',
            'Pluto': 'трансформация, сила, возрождение'
        }

    def _initialize_aspect_interpretations(self) -> Dict:
        """Интерпретации аспектов"""
        return {
            'conjunction': 'интенсивное объединение энергий',
            'opposition': 'противостояние и поиск баланса',
            'square': 'напряжение и вызовы',
            'trine': 'гармония и легкость',
            'sextile': 'возможности и поддержка'
        }

    def _get_fallback_insights(self) -> Dict[str, Any]:
        """Fallback при ошибках"""
        return {
            'success': False,
            'insights': {},
            'summary': {
                'total_insights': 0,
                'overall_mood': 'неизвестно',
                'risk_level': 'unknown'
            },
            'error': 'Не удалось сгенерировать инсайты'
        }

    def _get_fallback_energy_trends(self) -> Dict[str, Any]:
        """Fallback трендов энергии"""
        return {
            'direction': 'stable',
            'strength': 0.0,
            'volatility': 0.0,
            'stability_score': 0.5,
            'current_energy': 50,
            'average_energy': 50,
            'energy_change': 0
        }


# Глобальный экземпляр для использования во всем проекте
insight_generator = InsightGenerator()