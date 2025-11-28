"""
ML Orchestrator Module for Astra Project
Централизованное управление ML вычислениями и координация между ML модулями
Оптимизирован для интеграции с существующей архитектурой Astra
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


class MLTaskType(Enum):
    """Типы ML задач для оптимизации вычислений"""
    FEATURE_ENGINEERING = "feature_engineering"
    BASIC_INSIGHTS = "basic_insights"
    TREND_ANALYSIS = "trend_analysis"
    ADVANCED_INSIGHTS = "advanced_insights"
    ALL = "all"


class MLTaskPriority(Enum):
    """Приоритеты выполнения ML задач"""
    HIGH = "high"  # Критичные для пользователя вычисления
    MEDIUM = "medium"  # Стандартные вычисления
    LOW = "low"  # Фоновые/оптимизационные вычисления


class MLOchestrator:
    """
    Оркестратор ML вычислений для координации и оптимизации работы ML модулей
    Интегрируется с существующей системой кэширования и БД
    """

    def __init__(self):
        self.cache_ttl_hours = 6  # Время жизни кэша ML вычислений
        self.computation_limits = {
            'max_trend_days': 90,
            'max_insight_types': 5,
            'batch_size': 10,
            'max_parallel_tasks': 4
        }

        # Статистика выполнения для мониторинга
        self.execution_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'execution_times': [],
            'errors': 0
        }

        # Активные задачи для предотвращения дублирования вычислений
        self.active_tasks = {}

    async def generate_ml_package(
            self,
            telegram_id: int,
            target_date: date = None,
            task_types: List[MLTaskType] = None,
            use_cache: bool = True,
            priority: MLTaskPriority = MLTaskPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Генерация полного ML пакета данных с оптимизацией вычислений
        Основной метод для интеграции с существующими сервисами
        """
        if target_date is None:
            target_date = date.today()

        if task_types is None:
            task_types = [MLTaskType.ALL]

        self.execution_stats['total_requests'] += 1

        try:
            logger.info(f"🔮 ML Orchestrator: запрос для {telegram_id} на {target_date}")

            # Проверка кэша в БД (интеграция с существующей системой)
            cache_key = self._generate_cache_key(telegram_id, target_date, task_types)

            if use_cache:
                cached_data = await self._get_ml_cache_from_db(telegram_id, target_date, task_types)
                if cached_data:
                    self.execution_stats['cache_hits'] += 1
                    logger.info(f"⚡ Использованы кэшированные ML данные для {telegram_id}")
                    return cached_data

            # Проверка активных задач для предотвращения дублирования
            task_key = f"{telegram_id}_{target_date}"
            if task_key in self.active_tasks:
                logger.info(f"🔄 Ожидание выполнения активной задачи для {telegram_id}")
                return await self.active_tasks[task_key]

            # Создание задачи
            task = asyncio.create_task(
                self._execute_ml_pipeline(telegram_id, target_date, task_types, priority)
            )
            self.active_tasks[task_key] = task

            try:
                ml_package = await task

                # Сохранение в кэш БД
                if use_cache:
                    await self._save_ml_cache_to_db(telegram_id, target_date, task_types, ml_package)

                logger.info(
                    f"✅ ML пакет сгенерирован для {telegram_id}: {len(ml_package.get('components', {}))} компонентов")
                return ml_package

            finally:
                # Очистка активных задач
                if task_key in self.active_tasks:
                    del self.active_tasks[task_key]

        except Exception as e:
            self.execution_stats['errors'] += 1
            logger.error(f"❌ Ошибка генерации ML пакета для {telegram_id}: {e}")
            return self._get_fallback_ml_package(telegram_id, target_date)

    async def generate_daily_ml_data(
            self,
            telegram_id: int,
            target_date: date = None,
            calculation_data: Dict = None
    ) -> Dict[str, Any]:
        """
        Оптимизированная генерация ежедневных ML данных для интеграции с prediction_services
        Специально для сохранения в daily_calculations
        """
        if target_date is None:
            target_date = date.today()

        try:
            # Если переданы готовые расчетные данные, используем их
            if calculation_data is None:
                calculation_data = await self._get_calculation_data(telegram_id, target_date)

            if not calculation_data:
                return self._get_minimal_ml_package()

            # Быстрая генерация только основных ML данных (без расширенных инсайтов)
            start_time = datetime.now()

            ml_features, basic_insights = await asyncio.gather(
                self._execute_feature_engineering(calculation_data, target_date),
                self._execute_basic_insights(calculation_data, target_date),
                return_exceptions=True
            )

            # Тренды генерируем только если есть достаточная история
            trend_data = await self._execute_trend_analysis(telegram_id, target_date)

            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_stats['execution_times'].append(execution_time)

            return {
                'ml_features': ml_features if not isinstance(ml_features, Exception) else {},
                'basic_insights': basic_insights if not isinstance(basic_insights, Exception) else [],
                'trend_data': trend_data if not isinstance(trend_data, Exception) else {},
                'generated_at': datetime.now().isoformat(),
                'execution_time_seconds': execution_time
            }

        except Exception as e:
            logger.error(f"❌ Ошибка генерации ежедневных ML данных: {e}")
            return self._get_minimal_ml_package()

    async def _execute_ml_pipeline(
            self,
            telegram_id: int,
            target_date: date,
            task_types: List[MLTaskType],
            priority: MLTaskPriority
    ) -> Dict[str, Any]:
        """Основной конвейер выполнения ML задач"""
        try:
            # Получение базовых расчетных данных
            calculation_data = await self._get_calculation_data(telegram_id, target_date)
            if not calculation_data:
                return self._get_fallback_ml_package(telegram_id, target_date)

            # Определение задач для выполнения
            tasks_to_execute = self._resolve_task_dependencies(task_types)

            # Параллельное выполнение задач с ограничением количества
            semaphore = asyncio.Semaphore(self.computation_limits['max_parallel_tasks'])

            async with semaphore:
                ml_results = await self._execute_ml_tasks(
                    telegram_id, target_date, tasks_to_execute, calculation_data, priority
                )

            # Формирование финального пакета
            ml_package = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'generated_at': datetime.now().isoformat(),
                'tasks_executed': [t.value for t in tasks_to_execute],
                'priority': priority.value,
                'components': ml_results,
                'metadata': {
                    'orchestrator_version': '1.0',
                    'computation_limits': self.computation_limits
                }
            }

            return ml_package

        except Exception as e:
            logger.error(f"❌ Ошибка в ML пайплайне для {telegram_id}: {e}")
            raise

    async def _execute_ml_tasks(
            self,
            telegram_id: int,
            target_date: date,
            task_types: List[MLTaskType],
            calculation_data: Dict,
            priority: MLTaskPriority
    ) -> Dict[str, Any]:
        """Параллельное выполнение ML задач с оптимизацией"""
        tasks = []
        task_map = {}

        # Подготовка задач для параллельного выполнения
        for task_type in task_types:
            if task_type == MLTaskType.FEATURE_ENGINEERING:
                task = self._execute_feature_engineering(calculation_data, target_date)
                task_map[task] = 'ml_features'

            elif task_type == MLTaskType.BASIC_INSIGHTS:
                task = self._execute_basic_insights(calculation_data, target_date)
                task_map[task] = 'basic_insights'

            elif task_type == MLTaskType.TREND_ANALYSIS:
                task = self._execute_trend_analysis(telegram_id, target_date)
                task_map[task] = 'trend_data'

            elif task_type == MLTaskType.ADVANCED_INSIGHTS:
                task = self._execute_advanced_insights(telegram_id, target_date, calculation_data)
                task_map[task] = 'advanced_insights'

            tasks.append(task)

        # Параллельное выполнение с обработкой исключений
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обработка результатов
        return self._process_ml_results(results, task_map, task_types)

    async def _execute_feature_engineering(self, calculation_data: Dict, target_date: date) -> Dict:
        """Выполнение feature engineering с обработкой ошибок"""
        try:
            from backend.feature_engineering import feature_engine

            calculations = calculation_data.get('calculations', {})
            biorhythm_data = calculations.get('biorhythms', {})
            astro_data = calculations.get('astrology', {})

            if not biorhythm_data or not astro_data:
                logger.warning("⚠️ Недостаточно данных для feature engineering")
                return {}

            ml_features = feature_engine.calculate_ml_features(
                biorhythm_data, astro_data, target_date
            )

            return ml_features

        except Exception as e:
            logger.error(f"❌ Ошибка feature engineering: {e}")
            return {}

    async def _execute_basic_insights(self, calculation_data: Dict, target_date: date) -> List[str]:
        """Генерация базовых инсайтов с обработкой ошибок"""
        try:
            from backend.feature_engineering import feature_engine

            calculations = calculation_data.get('calculations', {})
            biorhythm_data = calculations.get('biorhythms', {})

            # Получаем или вычисляем ML фичи
            ml_features = calculation_data.get('ml_features', {})
            if not ml_features:
                astro_data = calculations.get('astrology', {})
                ml_features = feature_engine.calculate_ml_features(
                    biorhythm_data, astro_data, target_date
                )

            basic_insights = feature_engine.generate_basic_insights(ml_features, biorhythm_data)
            return basic_insights

        except Exception as e:
            logger.error(f"❌ Ошибка генерации базовых инсайтов: {e}")
            return []

    async def _execute_trend_analysis(self, telegram_id: int, target_date: date) -> Dict:
        """Анализ трендов с оптимизацией периода"""
        try:
            from backend.trend_analyzer import trend_analyzer

            # Автоматическое определение оптимального периода
            analysis_period = await self._determine_optimal_trend_period(telegram_id)

            trend_data = await trend_analyzer.analyze_user_trends(
                telegram_id,
                analysis_period
            )
            return trend_data

        except Exception as e:
            logger.error(f"❌ Ошибка анализа трендов: {e}")
            return {}

    async def _execute_advanced_insights(self, telegram_id: int, target_date: date, calculation_data: Dict) -> Dict:
        """Генерация расширенных инсайтов"""
        try:
            from backend.insight_generator import insight_generator

            advanced_insights = await insight_generator.generate_comprehensive_insights(
                telegram_id, target_date
            )
            return advanced_insights

        except Exception as e:
            logger.error(f"❌ Ошибка генерации расширенных инсайтов: {e}")
            return {}

    async def _get_calculation_data(self, telegram_id: int, target_date: date) -> Optional[Dict]:
        """Получение расчетных данных через существующие сервисы"""
        try:
            from backend.calculation_services import calculation_service

            calculation_package = await calculation_service.get_full_calculation_package(
                telegram_id, target_date
            )

            if calculation_package.get('success'):
                return calculation_package
            else:
                logger.warning(f"⚠️ Не удалось получить расчетные данные для {telegram_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения расчетных данных: {e}")
            return None

    async def _determine_optimal_trend_period(self, telegram_id: int) -> int:
        """Определение оптимального периода для анализа трендов"""
        try:
            from backend.prediction_services import get_user_calculation_history

            # Проверяем доступность исторических данных
            history = await get_user_calculation_history(telegram_id, 7)  # Проверяем 1 неделю

            if len(history) >= 5:  # Если есть достаточно данных за неделю
                return 30  # Используем 30 дней для детального анализа
            elif len(history) >= 2:  # Минимальные данные
                return 14  # Используем 2 недели
            else:
                return 7  # Минимальный период

        except Exception:
            return 30  # Значение по умолчанию

    def _resolve_task_dependencies(self, task_types: List[MLTaskType]) -> List[MLTaskType]:
        """Разрешение зависимостей между задачами"""
        resolved_tasks = set()

        for task_type in task_types:
            if task_type == MLTaskType.ALL:
                return [MLTaskType.FEATURE_ENGINEERING, MLTaskType.BASIC_INSIGHTS,
                        MLTaskType.TREND_ANALYSIS, MLTaskType.ADVANCED_INSIGHTS]

            resolved_tasks.add(task_type)

            # Добавляем зависимости
            if task_type == MLTaskType.BASIC_INSIGHTS:
                resolved_tasks.add(MLTaskType.FEATURE_ENGINEERING)
            elif task_type == MLTaskType.ADVANCED_INSIGHTS:
                resolved_tasks.add(MLTaskType.FEATURE_ENGINEERING)

        return list(resolved_tasks)

    def _process_ml_results(
            self,
            results: List,
            task_map: Dict,
            task_types: List[MLTaskType]
    ) -> Dict[str, Any]:
        """Обработка результатов выполнения ML задач"""
        processed_results = {}

        for result, task in zip(results, task_map.keys()):
            component_name = task_map[task]

            if isinstance(result, Exception):
                logger.error(f"❌ Ошибка в задаче {component_name}: {result}")
                processed_results[component_name] = self._get_fallback_component(component_name)
            else:
                processed_results[component_name] = result

        return processed_results

    def _generate_cache_key(self, telegram_id: int, target_date: date, task_types: List[MLTaskType]) -> str:
        """Генерация ключа кэша"""
        task_str = '_'.join(sorted([t.value for t in task_types]))
        data_str = f"{telegram_id}_{target_date.isoformat()}_{task_str}"
        return hashlib.sha256(data_str.encode()).hexdigest()[:32]

    async def _get_ml_cache_from_db(
            self,
            telegram_id: int,
            target_date: date,
            task_types: List[MLTaskType]
    ) -> Optional[Dict]:
        """Получение кэшированных ML данных из БД"""
        try:
            from backend.database import async_session, DailyCalculations
            from sqlalchemy.future import select
            from datetime import datetime

            async with async_session() as session:
                result = await session.execute(
                    select(DailyCalculations).where(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
                daily_calc = result.scalar_one_or_none()

                if daily_calc and daily_calc.ml_features and daily_calc.basic_insights:
                    # Проверяем свежесть данных (младше cache_ttl_hours)
                    if daily_calc.calculation_timestamp:
                        data_age = (datetime.now() - daily_calc.calculation_timestamp).total_seconds() / 3600
                        if data_age < self.cache_ttl_hours:
                            return {
                                'ml_features': daily_calc.ml_features,
                                'basic_insights': daily_calc.basic_insights,
                                'trend_data': daily_calc.trend_data or {},
                                'from_cache': True,
                                'cache_age_hours': round(data_age, 2)
                            }

            return None

        except Exception as e:
            logger.debug(f"⚠️ Ошибка получения кэша из БД: {e}")
            return None

    async def _save_ml_cache_to_db(
            self,
            telegram_id: int,
            target_date: date,
            task_types: List[MLTaskType],
            ml_package: Dict
    ) -> bool:
        """Сохранение ML данных в БД для кэширования"""
        try:
            from backend.database import async_session, DailyCalculations
            from sqlalchemy.future import select

            async with async_session() as session:
                result = await session.execute(
                    select(DailyCalculations).where(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
                daily_calc = result.scalar_one_or_none()

                components = ml_package.get('components', {})

                if daily_calc:
                    # Обновляем существующую запись
                    if 'ml_features' in components:
                        daily_calc.ml_features = components['ml_features']
                    if 'basic_insights' in components:
                        daily_calc.basic_insights = components['basic_insights']
                    if 'trend_data' in components:
                        daily_calc.trend_data = components['trend_data']
                else:
                    # Создаем новую запись (редкий случай)
                    daily_calc = DailyCalculations(
                        telegram_id=telegram_id,
                        target_date=target_date,
                        biorhythm_data={},
                        astro_transits_data={},
                        calculation_metadata={},
                        data_hash='ml_cache',
                        ml_features=components.get('ml_features', {}),
                        basic_insights=components.get('basic_insights', []),
                        trend_data=components.get('trend_data', {})
                    )
                    session.add(daily_calc)

                await session.commit()
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ML кэша в БД: {e}")
            return False

    def _get_fallback_component(self, component_name: str) -> Any:
        """Fallback данные для компонентов при ошибках"""
        fallbacks = {
            'ml_features': {},
            'basic_insights': ["🔮 Используйте текущие данные для планирования дня"],
            'trend_data': {},
            'advanced_insights': {'success': False, 'error': 'Не удалось сгенерировать инсайты'}
        }
        return fallbacks.get(component_name, {})

    def _get_fallback_ml_package(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Fallback ML пакет при критических ошибках"""
        return {
            'success': False,
            'user_id': telegram_id,
            'target_date': target_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'error': 'Не удалось сгенерировать ML данные',
            'components': {
                'ml_features': {},
                'basic_insights': ["🔮 Базовые рекомендации временно недоступны"],
                'trend_data': {},
                'advanced_insights': {'success': False}
            },
            'fallback_mode': True
        }

    def _get_minimal_ml_package(self) -> Dict[str, Any]:
        """Минимальный ML пакет для критических случаев"""
        return {
            'ml_features': {},
            'basic_insights': [],
            'trend_data': {},
            'generated_at': datetime.now().isoformat(),
            'minimal_mode': True
        }

    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Статистика работы оркестратора для мониторинга"""
        total_requests = self.execution_stats['total_requests']
        cache_hits = self.execution_stats['cache_hits']
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

        execution_times = self.execution_stats['execution_times']
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'errors': self.execution_stats['errors'],
            'active_tasks': len(self.active_tasks),
            'avg_execution_time_seconds': round(avg_execution_time, 3),
            'computation_limits': self.computation_limits
        }

    async def cleanup_old_cache(self, hours_old: int = 24) -> int:
        """Очистка устаревшего кэша (интеграция с существующей системой очистки)"""
        try:
            # Используем существующую систему очистки
            from backend.calculation_services import calculation_optimizer

            cleanup_result = await calculation_optimizer.cleanup_old_calculations(hours_old // 24)
            return cleanup_result.get('total_deleted', 0)

        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья ML оркестратора
        Интеграция с существующей системой health checks
        """
        try:
            # Проверяем доступность ML модулей
            from backend.feature_engineering import feature_engine
            from backend.trend_analyzer import trend_analyzer
            from backend.insight_generator import insight_generator

            # Проверяем статистику выполнения
            stats = await self.get_orchestrator_stats()

            # Анализируем состояние
            cache_hit_rate = stats.get('cache_hit_rate', 0)
            error_rate = (stats.get('errors', 0) / stats.get('total_requests', 1)) * 100

            if error_rate > 10:
                status = 'degraded'
                message = f'Высокий уровень ошибок: {error_rate:.1f}%'
            elif cache_hit_rate < 20:
                status = 'degraded'
                message = f'Низкая эффективность кэша: {cache_hit_rate:.1f}%'
            else:
                status = 'healthy'
                message = 'ML система работает нормально'

            return {
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_requests': stats.get('total_requests', 0),
                    'cache_hit_rate': cache_hit_rate,
                    'error_rate': error_rate,
                    'active_tasks': stats.get('active_tasks', 0),
                    'avg_execution_time': stats.get('avg_execution_time_seconds', 0)
                },
                'components': {
                    'feature_engineering': 'available',
                    'trend_analyzer': 'available',
                    'insight_generator': 'available'
                }
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Ошибка проверки здоровья: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }


# Глобальный экземпляр для использования во всем проекте
ml_orchestrator = MLOchestrator()