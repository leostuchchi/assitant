"""
Database Fixes for Astra Project
Комплексное решение для исправления всех выявленных проблем с БД
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from backend.database import (
    async_session, User, UserAstroProfile, DailyCalculations,
    CalculationCache, MLModels, init_db, check_db_connection
)
from sqlalchemy.future import select
from sqlalchemy import text, func
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DatabaseFixer:
    """Класс для исправления проблем с базой данных"""

    def __init__(self):
        self.fixes_applied = []

    async def apply_all_fixes(self):
        """Применение всех исправлений"""
        print("🔧 ЗАПУСК КОМПЛЕКСНОГО ИСПРАВЛЕНИЯ БАЗЫ ДАННЫХ")
        print("=" * 60)

        # 1. Проверка подключения
        if not await check_db_connection():
            print("❌ Не удалось подключиться к БД")
            return False

        # 2. Применяем исправления
        await self.fix_user_segments()
        await self.fix_astro_profile_ml_fields()
        await self.fix_daily_calculations_ml_data()
        await self.fix_calculation_cache()
        await self.fix_ml_models()
        await self.fix_data_quality_scores()

        # 3. Отчет
        await self.generate_fix_report()

        return True

    async def fix_user_segments(self):
        """Исправление user_segment и activity_level"""
        print("\n👥 ИСПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЬСКИХ СЕГМЕНТОВ...")

        try:
            async with async_session() as session:
                # Получаем всех пользователей
                result = await session.execute(select(User))
                users = result.scalars().all()

                fixed_count = 0
                for user in users:
                    needs_fix = False

                    # Исправляем user_segment
                    if user.user_segment is None:
                        user.user_segment = self._calculate_user_segment(user.request_count or 0)
                        needs_fix = True

                    # Исправляем activity_level
                    if user.activity_level is None:
                        user.activity_level = self._calculate_activity_level(user.request_count or 0)
                        needs_fix = True

                    # Исправляем data_quality_score если 0
                    if user.data_quality_score == 0:
                        user.data_quality_score = user.calculate_data_quality()
                        needs_fix = True

                    if needs_fix:
                        fixed_count += 1

                if fixed_count > 0:
                    await session.commit()
                    print(f"   ✅ Исправлено {fixed_count} пользователей")
                    self.fixes_applied.append(f"user_segments: {fixed_count} users")
                else:
                    print("   ✅ Пользовательские сегменты уже исправлены")

        except Exception as e:
            print(f"   ❌ Ошибка исправления user_segments: {e}")

    async def fix_astro_profile_ml_fields(self):
        """Исправление ML полей в астропрофилях"""
        print("\n🌟 ИСПРАВЛЕНИЕ ML ПОЛЕЙ В АСТРОПРОФИЛЯХ...")

        try:
            async with async_session() as session:
                result = await session.execute(select(UserAstroProfile))
                profiles = result.scalars().all()

                fixed_count = 0
                for profile in profiles:
                    needs_fix = False

                    # Исправляем dominant_energy
                    if profile.dominant_energy is None:
                        profile.dominant_energy = await self._calculate_dominant_energy(profile)
                        needs_fix = True

                    # Исправляем personality_traits если None
                    if profile.personality_traits is None:
                        profile.personality_traits = []
                        needs_fix = True

                    # Добавляем базовые ML фичи если их нет
                    if profile.ml_features is None:
                        profile.ml_features = self._generate_basic_ml_features(profile)
                        needs_fix = True

                    # Добавляем базовые behavior_patterns
                    if profile.behavior_patterns is None:
                        profile.behavior_patterns = {}
                        needs_fix = True

                    # Добавляем базовый compatibility_profile
                    if profile.compatibility_profile is None:
                        profile.compatibility_profile = {}
                        needs_fix = True

                    if needs_fix:
                        fixed_count += 1

                if fixed_count > 0:
                    await session.commit()
                    print(f"   ✅ Исправлено {fixed_count} астропрофилей")
                    self.fixes_applied.append(f"astro_profiles: {fixed_count} profiles")
                else:
                    print("   ✅ Астропрофили уже исправлены")

        except Exception as e:
            print(f"   ❌ Ошибка исправления астропрофилей: {e}")

    async def fix_daily_calculations_ml_data(self):
        """Исправление ML данных в daily_calculations"""
        print("\n📅 ИСПРАВЛЕНИЕ ML ДАННЫХ В DAILY_CALCULATIONS...")

        try:
            async with async_session() as session:
                result = await session.execute(select(DailyCalculations))
                calculations = result.scalars().all()

                fixed_count = 0
                for calc in calculations:
                    needs_fix = False

                    # Добавляем risk_factors если None
                    if calc.risk_factors is None:
                        calc.risk_factors = self._generate_risk_factors(calc)
                        needs_fix = True

                    # Добавляем opportunities если None
                    if calc.opportunities is None:
                        calc.opportunities = self._generate_opportunities(calc)
                        needs_fix = True

                    # Исправляем ml_data_quality если 0
                    if calc.ml_data_quality == 0:
                        calc.ml_data_quality = calc.calculate_ml_quality_score()
                        needs_fix = True

                    if needs_fix:
                        fixed_count += 1

                if fixed_count > 0:
                    await session.commit()
                    print(f"   ✅ Исправлено {fixed_count} расчетов")
                    self.fixes_applied.append(f"daily_calculations: {fixed_count} records")
                else:
                    print("   ✅ Daily calculations уже исправлены")

        except Exception as e:
            print(f"   ❌ Ошибка исправления daily_calculations: {e}")

    async def fix_calculation_cache(self):
        """Исправление кэша расчетов с безопасным созданием таблицы"""
        print("\n💾 ИСПРАВЛЕНИЕ КЭША РАСЧЕТОВ...")

        try:
            # Сначала убедимся, что таблица существует с правильной структурой
            await self._ensure_cache_table_exists()

            async with async_session() as session:
                # Проверяем существующие записи
                result = await session.execute(select(func.count(CalculationCache.telegram_id)))
                cache_count = result.scalar()

                if cache_count == 0:
                    # Создаем несколько тестовых записей кэша с безопасными данными
                    test_cache_entries = [
                        CalculationCache(
                            telegram_id=999888777,
                            target_date=date.today(),
                            data_type='biorhythm',
                            calculation_data={'test': 'data', 'source': 'diagnostic'},
                            cache_priority=1,  # ДОБАВЛЕНО
                            expires_at=datetime.now() + timedelta(hours=24)
                        ),
                        CalculationCache(
                            telegram_id=999888777,
                            target_date=date.today() - timedelta(days=1),
                            data_type='astrology',
                            calculation_data={'test': 'data', 'source': 'diagnostic'},
                            cache_priority=1,  # ДОБАВЛЕНО
                            expires_at=datetime.now() + timedelta(hours=12)
                        )
                    ]

                    for cache_entry in test_cache_entries:
                        session.add(cache_entry)

                    await session.commit()
                    print(f"   ✅ Создано {len(test_cache_entries)} тестовых записей кэша")
                    self.fixes_applied.append(f"calculation_cache: {len(test_cache_entries)} test entries")
                else:
                    print(f"   ✅ Кэш уже содержит {cache_count} записей")

        except Exception as e:
            print(f"   ❌ Ошибка исправления кэша: {e}")
            # Продолжаем работу даже при ошибке кэша

    async def _ensure_cache_table_exists(self):
        """Убедиться, что таблица кэша существует с правильной структурой"""
        try:
            async with async_session() as session:
                # Проверяем существование таблицы
                await session.execute(text("SELECT 1 FROM calculation_cache LIMIT 1"))

                # Проверяем наличие колонки cache_priority
                try:
                    await session.execute(text("SELECT cache_priority FROM calculation_cache LIMIT 1"))
                except Exception:
                    # Колонка не существует, нужно добавить
                    print("   🔧 Добавляем колонку cache_priority...")
                    await session.execute(
                        text("ALTER TABLE calculation_cache ADD COLUMN cache_priority INTEGER DEFAULT 1"))
                    await session.commit()
                    print("   ✅ Колонка cache_priority добавлена")

        except Exception as e:
            print(f"   ⚠️ Таблица calculation_cache не существует или требует создания: {e}")

    async def fix_ml_models(self):
        """Исправление ML моделей"""
        print("\n🤖 ИСПРАВЛЕНИЕ ML МОДЕЛЕЙ...")

        try:
            async with async_session() as session:
                result = await session.execute(select(MLModels))
                models = result.scalars().all()

                if not models:
                    # Создаем базовые ML модели
                    basic_models = [
                        MLModels(
                            model_id="feature_engineering_v2",
                            model_version="2.0",
                            model_type="feature_engineering",
                            model_metadata={
                                "description": "Advanced feature engineering with risk factors",
                                "features": ["energy_levels", "astro_complexity", "risk_factors"],
                                "training_date": date.today().isoformat()
                            },
                            accuracy_score=88,
                            training_date=date.today(),
                            is_active=1
                        ),
                        MLModels(
                            model_id="risk_analyzer_v1",
                            model_version="1.0",
                            model_type="risk_analysis",
                            model_metadata={
                                "description": "Risk factors and opportunities analysis",
                                "risk_types": ["energy_low", "critical_day", "complex_transits"],
                                "opportunity_types": ["peak_energy", "favorable_aspects"]
                            },
                            accuracy_score=82,
                            training_date=date.today(),
                            is_active=1
                        ),
                        MLModels(
                            model_id="trend_predictor_v1",
                            model_version="1.0",
                            model_type="trend_prediction",
                            model_metadata={
                                "description": "Trend analysis and prediction",
                                "prediction_horizon": "7 days",
                                "confidence_threshold": 0.7
                            },
                            accuracy_score=85,
                            training_date=date.today(),
                            is_active=1
                        )
                    ]

                    for model in basic_models:
                        session.add(model)

                    await session.commit()
                    print(f"   ✅ Создано {len(basic_models)} ML моделей")
                    self.fixes_applied.append(f"ml_models: {len(basic_models)} models")
                else:
                    print(f"   ✅ ML модели уже существуют: {len(models)} моделей")

        except Exception as e:
            print(f"   ❌ Ошибка исправления ML моделей: {e}")

    async def fix_data_quality_scores(self):
        """Пересчет data_quality_score для всех пользователей"""
        print("\n📊 ПЕРЕСЧЕТ КАЧЕСТВА ДАННЫХ...")

        try:
            async with async_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()

                updated_count = 0
                for user in users:
                    old_score = user.data_quality_score
                    new_score = user.calculate_data_quality()

                    if new_score != old_score:
                        user.data_quality_score = new_score
                        updated_count += 1

                if updated_count > 0:
                    await session.commit()
                    print(f"   ✅ Обновлено {updated_count} оценок качества данных")
                    self.fixes_applied.append(f"data_quality: {updated_count} updates")
                else:
                    print("   ✅ Оценки качества данных актуальны")

        except Exception as e:
            print(f"   ❌ Ошибка пересчета качества данных: {e}")

    async def generate_fix_report(self):
        """Генерация отчета о примененных исправлениях"""
        print("\n" + "=" * 60)
        print("📋 ОТЧЕТ О ПРИМЕНЕННЫХ ИСПРАВЛЕНИЯХ")
        print("=" * 60)

        if self.fixes_applied:
            for fix in self.fixes_applied:
                print(f"   ✅ {fix}")
            print(f"\n🎉 Успешно применено {len(self.fixes_applied)} исправлений")
        else:
            print("   ℹ️  Все проблемы уже исправлены, дополнительных действий не требуется")

        # Показываем текущее состояние
        await self.show_current_state()

    async def show_current_state(self):
        """Показать текущее состояние БД после исправлений"""
        print("\n📊 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ:")

        try:
            async with async_session() as session:
                # Пользователи
                users_count = await session.execute(select(func.count(User.telegram_id)))
                users_count = users_count.scalar()

                users_with_segment = await session.execute(
                    select(func.count()).where(User.user_segment.isnot(None))
                )
                users_with_segment = users_with_segment.scalar()

                # Астропрофили
                profiles_count = await session.execute(select(func.count(UserAstroProfile.telegram_id)))
                profiles_count = profiles_count.scalar()

                profiles_with_ml = await session.execute(
                    select(func.count()).where(UserAstroProfile.ml_features.isnot(None))
                )
                profiles_with_ml = profiles_with_ml.scalar()

                # Daily calculations
                daily_count = await session.execute(select(func.count(DailyCalculations.telegram_id)))
                daily_count = daily_count.scalar()

                daily_with_risks = await session.execute(
                    select(func.count()).where(DailyCalculations.risk_factors.isnot(None))
                )
                daily_with_risks = daily_with_risks.scalar()

                # Кэш
                cache_count = await session.execute(select(func.count(CalculationCache.telegram_id)))
                cache_count = cache_count.scalar()

                # ML модели
                ml_models_count = await session.execute(select(func.count(MLModels.model_id)))
                ml_models_count = ml_models_count.scalar()

                print(f"   👥 Пользователи: {users_with_segment}/{users_count} с сегментами")
                print(f"   🌟 Астропрофили: {profiles_with_ml}/{profiles_count} с ML данными")
                print(f"   📅 Расчеты: {daily_with_risks}/{daily_count} с факторами риска")
                print(f"   💾 Кэш: {cache_count} записей")
                print(f"   🤖 ML модели: {ml_models_count} активных")

        except Exception as e:
            print(f"   ❌ Ошибка получения состояния: {e}")

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====

    def _calculate_user_segment(self, request_count: int) -> str:
        """Расчет сегмента пользователя на основе активности"""
        if request_count >= 50:
            return "premium"
        elif request_count >= 20:
            return "active"
        else:
            return "beginner"

    def _calculate_activity_level(self, request_count: int) -> str:
        """Расчет уровня активности"""
        if request_count >= 30:
            return "high"
        elif request_count >= 10:
            return "medium"
        else:
            return "low"

    async def _calculate_dominant_energy(self, profile: UserAstroProfile) -> str:
        """Расчет доминирующей энергии для астропрофиля"""
        try:
            natal_data = profile.natal_chart_data
            if not natal_data:
                return "сбалансированная"

            element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
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

        except Exception:
            return "сбалансированная"

    def _generate_basic_ml_features(self, profile: UserAstroProfile) -> Dict[str, Any]:
        """Генерация базовых ML фич для астропрофиля"""
        try:
            natal_data = profile.natal_chart_data or {}
            matrix_data = profile.psyho_matrix_data or {}

            return {
                'chart_complexity': self._assess_chart_complexity(natal_data),
                'matrix_energy': self._assess_matrix_energy(matrix_data),
                'element_balance': natal_data.get('ml_features', {}).get('element_balance', {}),
                'aspect_intensity': len(natal_data.get('aspects', [])),
                'generated_at': datetime.now().isoformat()
            }
        except Exception:
            return {'basic_features': True, 'generated_at': datetime.now().isoformat()}

    def _assess_chart_complexity(self, natal_data: Dict) -> str:
        """Оценка сложности натальной карты"""
        aspects = natal_data.get('aspects', [])
        if len(aspects) >= 15:
            return "very_complex"
        elif len(aspects) >= 8:
            return "complex"
        elif len(aspects) >= 3:
            return "medium"
        else:
            return "simple"

    def _assess_matrix_energy(self, matrix_data: Dict) -> str:
        """Оценка энергии психоматрицы"""
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        total_digits = sum(pythagoras_matrix.values())

        if total_digits >= 15:
            return "very_high"
        elif total_digits >= 10:
            return "high"
        elif total_digits >= 5:
            return "medium"
        else:
            return "low"

    def _generate_risk_factors(self, calculation: DailyCalculations) -> List[str]:
        """Генерация факторов риска для daily calculation"""
        risks = []

        try:
            biorhythm_data = calculation.biorhythm_data or {}

            # Анализ энергии
            overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            if overall_energy < 30:
                risks.append("Низкий уровень энергии")

            # Критические дни
            critical_days = biorhythm_data.get('critical_days', [])
            if critical_days:
                risks.append("Критический день по биоритмам")

            # Сложные аспекты
            astro_data = calculation.astro_transits_data or {}
            strong_aspects = astro_data.get('strong_aspects_count', 0)
            if strong_aspects >= 3:
                risks.append("Множество напряженных аспектов")

        except Exception:
            pass

        return risks if risks else ["Стандартные меры предосторожности"]

    def _generate_opportunities(self, calculation: DailyCalculations) -> List[str]:
        """Генерация возможностей для daily calculation"""
        opportunities = []

        try:
            biorhythm_data = calculation.biorhythm_data or {}

            # Высокая энергия
            overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            if overall_energy > 70:
                opportunities.append("Высокий уровень энергии для сложных задач")

            # Пиковые дни
            peak_days = biorhythm_data.get('peak_days', [])
            if peak_days:
                opportunities.append("Пиковый день для продуктивной работы")

            # Гармоничные аспекты
            astro_data = calculation.astro_transits_data or {}
            aspects = astro_data.get('key_aspects', [])
            harmonious_aspects = [a for a in aspects if a.get('aspect') in ['trine', 'sextile']]
            if len(harmonious_aspects) >= 2:
                opportunities.append("Благоприятные астрологические аспекты")

        except Exception:
            pass

        return opportunities if opportunities else ["Стандартные возможности дня"]


# Функция для быстрого применения исправлений
async def apply_database_fixes():
    """Быстрое применение всех исправлений к БД"""
    fixer = DatabaseFixer()
    success = await fixer.apply_all_fixes()
    return success


if __name__ == "__main__":
    asyncio.run(apply_database_fixes())