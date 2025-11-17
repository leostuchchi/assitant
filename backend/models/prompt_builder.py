import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Оптимизированный построитель промптов для AI рекомендаций
    """

    def __init__(self):
        self.templates = {
            'daily_recommendations': self._daily_recommendations_template,
            'professional_focus': self._professional_focus_template,
            'energy_management': self._energy_management_template
        }

    def build_prompt(self, data: Dict[str, Any], prompt_type: str = 'daily_recommendations') -> str:
        """
        Строит оптимизированный промпт на основе данных пользователя
        """
        template = self.templates.get(prompt_type, self._daily_recommendations_template)
        #print(template(data))
        return template(data)

    def _daily_recommendations_template(self, data: Dict[str, Any]) -> str:
        """Шаблон для ежедневных рекомендаций"""
        user_context = data.get('user_context', {})
        energy_state = data.get('energy_state', {})
        astro_highlights = data.get('astro_highlights', {})

        # Ключевые инсайты из астроданных
        key_insights = self._extract_key_insights(astro_highlights)

        prompt = f"""(астрология,нумерология, биоэнергетика, психология, эмоциональный интеллект),
        тебе даны данные: астологических расчетов на день, психологической матрицы пользователя, расчет биоритмов на день.
        На основе предоставленных расчетов предоставь КОНКРЕТНЫЕ рекоммендации на день.

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
• Профессия: {user_context.get('profession', 'не указана')}
• Должность: {user_context.get('position', 'не указана')}
• Город: {user_context.get('current_city', 'не указан')}

ЭНЕРГЕТИЧЕСКИЙ ПРОФИЛЬ:
{self._format_energy_state(energy_state)}

АСТРОЛОГИЧЕСКИЕ ИНСАЙТЫ:
{key_insights}

СФОРМУЛИРУЙ 3-5 КОНКРЕТНЫХ РЕКОМЕНДАЦИЙ:
1. 💼 Личностный рост 
2. 🏃 Развитие интеллекта   
3. ❤️ Эмоциональный баланс (на что обратить внимание)
4. 🎯 Творческий подход

ОТВЕТ (только рекомендации, без пояснений):"""

        return prompt

    def _professional_focus_template(self, data: Dict[str, Any]) -> str:
        """Шаблон для профессиональных рекомендаций"""
        user_context = data.get('user_context', {})

        return f"""Сфокусируйся на профессиональных рекомендациях для:

Профессия: {user_context.get('profession', 'не указана')}
Должность: {user_context.get('position', 'не указана')}

Дай 3 конкретных совета по:
1. Оптимизации деятельности
2. Решению жизненных задач
3. Развитию навыков

ОТВЕТ:"""

    def _energy_management_template(self, data: Dict[str, Any]) -> str:
        """Шаблон для управления энергией"""
        energy_state = data.get('energy_state', {})

        return f"""Дай рекомендации по управлению энергией на основе:

{self._format_energy_state(energy_state)}

Советы по:
1. Распределению нагрузки
2. Восстановлению сил
3. Пикам продуктивности

ОТВЕТ:"""

    def _format_energy_state(self, energy_state: Dict[str, Any]) -> str:
        """Форматирование данных об энергии"""
        overall = energy_state.get('overall_energy', {})
        physical = energy_state.get('physical_cycle', {})
        emotional = energy_state.get('emotional_cycle', {})
        intellectual = energy_state.get('intellectual_cycle', {})

        return f"""• Общая энергия: {overall.get('percentage', 0)}% ({overall.get('level', 'средний')})
• Физический цикл: {physical.get('percentage', 0)}% ({physical.get('phase', 'нейтральный')})
• Эмоциональный цикл: {emotional.get('percentage', 0)}% ({emotional.get('phase', 'нейтральный')})
• Интеллектуальный цикл: {intellectual.get('percentage', 0)}% ({intellectual.get('phase', 'нейтральный')})"""

    def _extract_key_insights(self, astro_highlights: Dict[str, Any]) -> str:
        """Извлечение ключевых астрологических инсайтов"""
        if not astro_highlights:
            return "• Стабильный астрологический фон"

        insights = []

        # Сильные аспекты
        strong_aspects = astro_highlights.get('strong_aspects_count', 0)
        if strong_aspects > 3:
            insights.append(f"• {strong_aspects} сильных аспектов - день важных событий")
        elif strong_aspects > 0:
            insights.append(f"• {strong_aspects} значимых аспекта")

        # Ретроградные планеты
        retrograde = astro_highlights.get('retrograde_planets', [])
        if retrograde:
            insights.append(f"• Ретроградные: {', '.join(retrograde)} - время пересмотра")

        return '\n'.join(insights) if insights else "• Благоприятный день для плановых задач"


# Глобальный экземпляр
prompt_builder = PromptBuilder()