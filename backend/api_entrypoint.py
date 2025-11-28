from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, validator
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import uvicorn
from fastapi.responses import JSONResponse
import time
import asyncio

from backend.assistant import assistant
from backend.calculation_services import calculation_service, calculation_optimizer
from backend.database import check_db_connection, get_database_stats, init_db, db_manager
from backend.user_services import get_user_profile
from backend.ml_orchestrator import ml_orchestrator, MLTaskType
from backend.prediction_services import regenerate_ml_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Astra Calculations API",
    description="API для доступа к расчетным данным проекта Astra (биоритмы, астрология, психоматрицы, ML аналитика)",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "calculations",
            "description": "Основные расчетные операции"
        },
        {
            "name": "ml-analytics",
            "description": "ML аналитика и AI рекомендации"
        },
        {
            "name": "users",
            "description": "Операции с пользователями и данными"
        },
        {
            "name": "admin",
            "description": "Административные операции"
        },
        {
            "name": "health",
            "description": "Проверка здоровья системы"
        }
    ]
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для сжатия ответов
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Модели Pydantic для запросов и ответов
class CalculationRequest(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    target_date: date = Field(default_factory=date.today, description="Дата для расчетов")
    include_ml: bool = Field(True, description="Включить ML аналитику")
    priority: str = Field("normal", description="Приоритет расчета: 'low', 'normal', 'high'")


class MLRegenerationRequest(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    target_date: date = Field(default_factory=date.today, description="Дата для регенерации")
    force_refresh: bool = Field(False, description="Принудительная перегенерация всех данных")


class UserMLAnalyticsRequest(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    period_days: int = Field(7, ge=1, le=365, description="Период анализа в днях")
    include_trends: bool = Field(True, description="Включить анализ трендов")
    include_insights: bool = Field(True, description="Включить детальные инсайты")


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    database_connected: bool
    ml_system_status: str
    version: str
    performance_metrics: Dict[str, float]


class CalculationResponse(BaseModel):
    success: bool
    user_id: int
    target_date: str
    calculations: Dict[str, Any]
    ml_analytics: Optional[Dict[str, Any]] = None
    user_context: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None


class MLAnalyticsResponse(BaseModel):
    success: bool
    user_id: int
    period: str
    analytics: Dict[str, Any]
    trends: Dict[str, Any]
    recommendations: List[str]
    generated_at: str
    data_quality: Dict[str, Any]


class UserDataStatusResponse(BaseModel):
    user_id: int
    has_basic_data: bool
    has_natal_chart: bool
    has_psyho_matrix: bool
    has_biorhythms: bool
    ml_data_status: Dict[str, Any]
    is_complete: bool
    profile_exists: bool
    data_quality_score: int


class HealthCheckResponse(BaseModel):
    user_id: int
    overall_status: str
    check_timestamp: str
    detailed_checks: Dict[str, Any]
    recommendations: List[str]
    ml_data_health: Dict[str, Any]


class StatisticsResponse(BaseModel):
    user_id: int
    request_count: int
    calculations_count: int
    biorhythms_count: int
    ml_stats: Dict[str, Any]
    first_calculation: Optional[str]
    last_calculation: Optional[str]
    average_energy: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None


class SystemStatusResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, Any]
    performance: Dict[str, float]
    recommendations: List[str]


# Глобальные переменные для мониторинга производительности
request_count = 0
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске с ML системой"""
    logger.info("🚀 Запуск Astra Calculations API v3.0 с ML интеграцией...")

    # Проверяем подключение к БД
    db_connected = await check_db_connection()
    if not db_connected:
        logger.error("❌ Не удалось подключиться к базе данных")
        # Не прерываем запуск, но логируем ошибку

    # Инициализируем БД если нужно
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка инициализации БД: {e}")

    # 🔧 ЗАПУСКАЕМ АВТОМАТИЧЕСКИЕ ИСПРАВЛЕНИЯ БАЗЫ ДАННЫХ
    try:
        from backend.database_fixes import apply_database_fixes
        await apply_database_fixes()
        logger.info("✅ Автоматические исправления БД применены")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка применения исправлений БД: {e}")

    # Проверяем ML систему
    try:
        ml_health = await ml_orchestrator.health_check()
        if ml_health.get('status') == 'healthy':
            logger.info("✅ ML система готова к работе")
        else:
            logger.warning(f"⚠️ ML система имеет проблемы: {ml_health.get('message')}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка проверки ML системы: {e}")

    logger.info("✅ Astra Calculations API v3.0 готов к работе")


@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Middleware для мониторинга производительности"""
    global request_count
    request_count += 1

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-Count"] = str(request_count)

    # Логируем медленные запросы
    if process_time > 2.0:  # больше 2 секунд
        logger.warning(f"🐌 Медленный запрос {request.url.path}: {process_time:.2f}с")

    return response


@app.get("/", include_in_schema=False)
async def root():
    """Корневой endpoint с информацией о системе"""
    global request_count, start_time

    uptime = time.time() - start_time
    return {
        "message": "Astra Calculations API",
        "version": "3.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(uptime),
        "total_requests": request_count,
        "features": [
            "биоритмы",
            "астрология",
            "психоматрицы",
            "ML аналитика",
            "AI рекомендации",
            "тренды и прогнозы"
        ]
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Проверка здоровья сервиса с ML метриками"""
    db_connected = await check_db_connection()

    # Проверяем ML систему
    try:
        ml_health = await ml_orchestrator.health_check()
        ml_status = ml_health.get('status', 'unknown')
    except Exception as e:
        ml_status = 'error'
        logger.warning(f"⚠️ Ошибка проверки ML системы: {e}")

    # Собираем метрики производительности
    uptime = time.time() - start_time
    requests_per_second = request_count / uptime if uptime > 0 else 0

    return HealthResponse(
        status="healthy" if db_connected and ml_status == 'healthy' else "degraded",
        service="astra_calculations",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected,
        ml_system_status=ml_status,
        version="3.0.0",
        performance_metrics={
            "uptime_seconds": uptime,
            "total_requests": request_count,
            "requests_per_second": round(requests_per_second, 2),
            "response_time_avg": 0.1  # Заглушка, в реальности нужно вычислять
        }
    )


@app.post("/api/v1/calculations", response_model=CalculationResponse, tags=["calculations"])
async def get_calculations(request: CalculationRequest):
    """
    Получение полного пакета расчетных данных для пользователя
    ВКЛЮЧАЕТ ML АНАЛИТИКУ по умолчанию
    """
    try:
        logger.info(f"📥 Запрос расчетов для пользователя {request.telegram_id} на {request.target_date}")

        # Получаем полный пакет расчетов
        calculation_package = await calculation_service.get_full_calculation_package(
            request.telegram_id,
            request.target_date
        )

        if not calculation_package.get('success'):
            raise HTTPException(
                status_code=400,
                detail=calculation_package.get('error', 'Неизвестная ошибка расчетов')
            )

        # Если ML аналитика отключена, удаляем ML данные из ответа
        if not request.include_ml and 'ml_data' in calculation_package:
            calculation_package['ml_data'] = {}

        logger.info(f"✅ Расчеты отправлены для пользователя {request.telegram_id}")

        return CalculationResponse(**calculation_package)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения расчетов для {request.telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post("/api/v1/calculations/optimized", response_model=CalculationResponse, tags=["calculations"])
async def get_optimized_calculations(
        telegram_id: int = Query(..., description="ID пользователя в Telegram"),
        target_date: date = Query(default_factory=date.today, description="Дата для расчетов"),
        include_biorhythms: bool = Query(True, description="Включить биоритмы"),
        include_astrology: bool = Query(True, description="Включить астрологию"),
        include_psychomatrix: bool = Query(True, description="Включить психоматрицу"),
        include_ml_analytics: bool = Query(True, description="Включить ML аналитику")
):
    """
    Получение оптимизированного пакета расчетов с фильтрацией по типам
    ОБНОВЛЕНО: Добавлена опция ML аналитики
    """
    try:
        logger.info(f"📥 Оптимизированный запрос расчетов для пользователя {telegram_id}")

        # Формируем список включаемых типов расчетов
        include_types = []
        if include_biorhythms:
            include_types.append('biorhythms')
        if include_astrology:
            include_types.append('astrology')
        if include_psychomatrix:
            include_types.append('psychomatrix')
        if include_ml_analytics:
            include_types.append('ml_analysis')

        if not include_types:
            raise HTTPException(
                status_code=400,
                detail="Не выбран ни один тип расчетов для включения"
            )

        # Получаем оптимизированные расчеты
        optimized_data = await calculation_optimizer.get_optimized_calculations(
            telegram_id,
            target_date,
            include_types
        )

        if not optimized_data.get('success'):
            raise HTTPException(
                status_code=400,
                detail=optimized_data.get('error', 'Неизвестная ошибка расчетов')
            )

        logger.info(f"✅ Оптимизированные расчеты отправлены для пользователя {telegram_id}")

        return CalculationResponse(**optimized_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка оптимизированных расчетов для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post("/api/v1/ml/regenerate", tags=["ml-analytics"])
async def regenerate_ml_calculations(request: MLRegenerationRequest, background_tasks: BackgroundTasks):
    """
    Принудительная регенерация ML данных для пользователя
    Может выполняться в фоновом режиме
    """
    try:
        logger.info(f"🔄 Запрос регенерации ML данных для пользователя {request.telegram_id}")

        if request.force_refresh:
            # Фоновая задача для полной перегенерации
            background_tasks.add_task(
                assistant.regenerate_ml_data,
                request.telegram_id,
                request.target_date
            )

            return {
                "success": True,
                "message": "Запущена фоновая регенерация ML данных",
                "user_id": request.telegram_id,
                "target_date": request.target_date.isoformat(),
                "background_task": True
            }
        else:
            # Синхронная регенерация
            result = await assistant.regenerate_ml_data(request.telegram_id, request.target_date)

            return {
                "success": result.get('success', False),
                "message": result.get('message', 'Регенерация завершена'),
                "user_id": request.telegram_id,
                "target_date": request.target_date.isoformat(),
                "background_task": False,
                "details": result
            }

    except Exception as e:
        logger.error(f"❌ Ошибка регенерации ML данных для {request.telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка регенерации ML данных: {str(e)}"
        )


@app.post("/api/v1/ml/analytics", response_model=MLAnalyticsResponse, tags=["ml-analytics"])
async def get_ml_analytics(request: UserMLAnalyticsRequest):
    """
    Получение расширенной ML аналитики для пользователя за период
    """
    try:
        logger.info(f"📊 Запрос ML аналитики для пользователя {request.telegram_id} за {request.period_days} дней")

        # Получаем базовую аналитику через assistant
        user_stats = await assistant.get_user_statistics(request.telegram_id)

        # Получаем историю расчетов за период
        end_date = date.today()
        start_date = end_date - timedelta(days=request.period_days)

        async with db_manager as db:
            calculations = await db.get_ml_enhanced_calculations(
                request.telegram_id,
                request.period_days
            )

        # Анализируем тренды если требуется
        trends = {}
        if request.include_trends and calculations:
            trends = await _analyze_user_trends(calculations, request.period_days)

        # Формируем рекомендации
        recommendations = await _generate_ml_recommendations(user_stats, calculations)

        # Оцениваем качество данных
        data_quality = _assess_analytics_data_quality(calculations, request.period_days)

        return MLAnalyticsResponse(
            success=True,
            user_id=request.telegram_id,
            period=f"{request.period_days} дней",
            analytics=user_stats.get('ml_stats', {}),
            trends=trends,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat(),
            data_quality=data_quality
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения ML аналитики для {request.telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения ML аналитики: {str(e)}"
        )


async def _analyze_user_trends(calculations: List[Dict], period_days: int) -> Dict[str, Any]:
    """Анализ трендов пользователя на основе исторических данных"""
    try:
        if not calculations:
            return {"error": "Недостаточно данных для анализа"}

        # Анализ энергетических трендов
        energy_trends = []
        productivity_trends = []

        for calc in calculations:
            ml_features = calc.get('ml_features', {})
            if ml_features:
                energy_trends.append(ml_features.get('energy_overall', 0))
                productivity_trends.append(ml_features.get('productivity_index', 0))

        # Простой анализ трендов
        trend_analysis = {
            "energy_trend": _calculate_trend_direction(energy_trends),
            "productivity_trend": _calculate_trend_direction(productivity_trends),
            "data_points": len(energy_trends),
            "analysis_period": f"{period_days} дней",
            "confidence": "medium" if len(energy_trends) >= 5 else "low"
        }

        return trend_analysis

    except Exception as e:
        logger.error(f"❌ Ошибка анализа трендов: {e}")
        return {"error": str(e)}


def _calculate_trend_direction(values: List[float]) -> str:
    """Определение направления тренда"""
    if len(values) < 2:
        return "недостаточно данных"

    first_half = values[:len(values) // 2]
    second_half = values[len(values) // 2:]

    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)

    if avg_second > avg_first + 0.1:
        return "растущий"
    elif avg_second < avg_first - 0.1:
        return "падающий"
    else:
        return "стабильный"


async def _generate_ml_recommendations(user_stats: Dict, calculations: List[Dict]) -> List[str]:
    """Генерация ML рекомендаций на основе данных пользователя"""
    recommendations = []

    try:
        ml_stats = user_stats.get('ml_stats', {})

        # Рекомендации на основе покрытия ML данных
        ml_coverage = ml_stats.get('ml_coverage', 0)
        if ml_coverage < 50:
            recommendations.append("Увеличьте частоту использования для улучшения качества рекомендаций")
        elif ml_coverage > 80:
            recommendations.append("Отличное покрытие данных! Рекомендации основаны на полной истории")

        # Рекомендации на основе активности
        request_count = user_stats.get('request_count', 0)
        if request_count < 10:
            recommendations.append("Используйте систему регулярно для персонализации рекомендаций")

        # Рекомендации на основе трендов
        if calculations:
            latest_calc = calculations[0]
            ml_features = latest_calc.get('ml_features', {})
            daily_score = ml_features.get('daily_score', 0.5)

            if daily_score < 0.3:
                recommendations.append("Сегодняшний день требует особого внимания к планированию нагрузки")
            elif daily_score > 0.8:
                recommendations.append("Идеальный день для решения сложных задач и важных решений")

        if not recommendations:
            recommendations.append("Продолжайте использовать систему для получения персонализированных рекомендаций")

    except Exception as e:
        logger.warning(f"⚠️ Ошибка генерации рекомендаций: {e}")
        recommendations.append("Используйте систему регулярно для улучшения рекомендаций")

    return recommendations


def _assess_analytics_data_quality(calculations: List[Dict], period_days: int) -> Dict[str, Any]:
    """Оценка качества данных для аналитики"""
    try:
        total_days = period_days
        actual_days = len(calculations)
        coverage = (actual_days / total_days) * 100

        # Считаем дни с ML данными
        ml_days = sum(1 for calc in calculations if calc.get('ml_features'))
        ml_coverage = (ml_days / actual_days * 100) if actual_days > 0 else 0

        return {
            "data_coverage": round(coverage, 1),
            "ml_data_coverage": round(ml_coverage, 1),
            "total_data_points": actual_days,
            "ml_data_points": ml_days,
            "quality_score": min(100, int((coverage + ml_coverage) / 2)),
            "quality_level": "высокое" if coverage >= 80 and ml_coverage >= 70 else
            "среднее" if coverage >= 50 and ml_coverage >= 40 else "низкое"
        }

    except Exception as e:
        return {
            "data_coverage": 0,
            "ml_data_coverage": 0,
            "quality_score": 0,
            "quality_level": "неизвестно",
            "error": str(e)
        }


@app.get("/api/v1/users/{telegram_id}/status", response_model=UserDataStatusResponse, tags=["users"])
async def get_user_data_status(telegram_id: int):
    """
    Получение статуса данных пользователя с ML статусом
    """
    try:
        logger.info(f"📊 Запрос статуса данных для пользователя {telegram_id}")

        status = await assistant.get_user_data_status(telegram_id)
        user_profile = await get_user_profile(telegram_id)

        return UserDataStatusResponse(
            user_id=telegram_id,
            has_basic_data=status['has_basic_data'],
            has_natal_chart=status['has_natal_chart'],
            has_psyho_matrix=status['has_psyho_matrix'],
            has_biorhythms=status['has_biorhythms'],
            ml_data_status=status.get('ml_data_status', {}),
            is_complete=status['is_complete'],
            profile_exists=user_profile is not None,
            data_quality_score=user_profile.get('data_quality_score', 0) if user_profile else 0
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статуса: {str(e)}"
        )


@app.get("/api/v1/users/{telegram_id}/health", response_model=HealthCheckResponse, tags=["users", "health"])
async def get_user_health_check(telegram_id: int):
    """
    Проверка здоровья расчетных данных пользователя с ML проверкой
    """
    try:
        logger.info(f"🏥 Запрос проверки здоровья данных для пользователя {telegram_id}")

        health_status = await calculation_optimizer.get_calculation_health_check(telegram_id)

        # Дополнительная проверка ML данных
        ml_health = await _check_user_ml_health(telegram_id)

        # Формируем рекомендации на основе проверок
        recommendations = []
        detailed_checks = health_status.get('detailed_checks', {})

        for check_type, check_data in detailed_checks.items():
            if check_data.get('status') != 'healthy':
                recommendation = check_data.get('recommendation')
                if recommendation:
                    recommendations.append(recommendation)

        # Добавляем ML рекомендации
        ml_recommendations = ml_health.get('recommendations', [])
        recommendations.extend(ml_recommendations)

        # Добавляем общие рекомендации
        if not recommendations:
            recommendations.append("Все системы в порядке. Данные актуальны и готовы к использованию.")

        return HealthCheckResponse(
            user_id=telegram_id,
            overall_status=health_status['overall_status'],
            check_timestamp=health_status['check_timestamp'],
            detailed_checks=detailed_checks,
            recommendations=recommendations,
            ml_data_health=ml_health
        )

    except Exception as e:
        logger.error(f"❌ Ошибка проверки здоровья для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка проверки здоровья: {str(e)}"
        )


async def _check_user_ml_health(telegram_id: int) -> Dict[str, Any]:
    """Проверка здоровья ML данных пользователя"""
    try:
        # Получаем статус данных пользователя
        status = await assistant.get_user_data_status(telegram_id)
        ml_status = status.get('ml_data_status', {})

        # Проверяем наличие сегодняшних ML данных
        today_calc = await assistant.get_daily_calculations(telegram_id, date.today())
        has_today_ml = today_calc and today_calc.get('ml_features')

        # Формируем рекомендации
        recommendations = []

        if not ml_status.get('available', False):
            recommendations.append("Отсутствуют ML данные. Запросите расчеты для генерации рекомендаций.")
        elif not has_today_ml:
            recommendations.append("Отсутствуют сегодняшние ML данные. Обновите расчеты.")

        ml_coverage = ml_status.get('features_count', 0)
        if ml_coverage < 5:
            recommendations.append("ML данные неполные. Рекомендуется регенерация.")

        return {
            "status": "healthy" if ml_status.get('available') and has_today_ml else "degraded",
            "ml_data_available": ml_status.get('available', False),
            "today_ml_available": has_today_ml,
            "features_count": ml_coverage,
            "data_freshness": ml_status.get('data_freshness', 'unknown'),
            "recommendations": recommendations
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "recommendations": ["Ошибка проверки ML данных"]
        }


@app.get("/api/v1/users/{telegram_id}/statistics", response_model=StatisticsResponse, tags=["users"])
async def get_user_statistics(telegram_id: int):
    """
    Получение статистики пользователя с ML метриками
    """
    try:
        logger.info(f"📈 Запрос статистики для пользователя {telegram_id}")

        stats = await assistant.get_user_statistics(telegram_id)

        return StatisticsResponse(
            user_id=telegram_id,
            request_count=stats.get('request_count', 0),
            calculations_count=stats.get('prediction_stats', {}).get('total_calculations', 0),
            biorhythms_count=stats.get('biorhythm_stats', {}).get('total_records', 0),
            ml_stats=stats.get('ml_stats', {}),
            first_calculation=stats.get('prediction_stats', {}).get('first_calculation_date'),
            last_calculation=stats.get('prediction_stats', {}).get('last_calculation_date'),
            average_energy=stats.get('biorhythm_stats', {}).get('average_energy_level', 0)
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статистики: {str(e)}"
        )


@app.get("/api/v1/biorhythms/{telegram_id}", tags=["calculations"])
async def get_biorhythms_only(
        telegram_id: int,
        target_date: date = Query(default_factory=date.today, description="Дата для расчетов")
):
    """
    Получение только данных биоритмов
    """
    try:
        logger.info(f"⚡ Запрос биоритмов для пользователя {telegram_id}")

        from backend.biorhythm_services import get_user_biorhythms
        biorhythm_data = await get_user_biorhythms(telegram_id, target_date)

        if not biorhythm_data:
            raise HTTPException(
                status_code=404,
                detail="Данные биоритмов не найдены"
            )

        return {
            "success": True,
            "user_id": telegram_id,
            "target_date": target_date.isoformat(),
            "biorhythms": biorhythm_data,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения биоритмов для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения биоритмов: {str(e)}"
        )


@app.get("/api/v1/astrology/{telegram_id}", tags=["calculations"])
async def get_astrology_only(
        telegram_id: int,
        target_date: date = Query(default_factory=date.today, description="Дата для расчетов")
):
    """
    Получение только астрологических данных
    """
    try:
        logger.info(f"🌟 Запрос астрологических данных для пользователя {telegram_id}")

        from backend.chart_services import get_user_natal_chart
        from backend.predictions import AstroPredictor

        natal_data = await get_user_natal_chart(telegram_id)
        if not natal_data:
            raise HTTPException(
                status_code=404,
                detail="Натальная карта не найдена"
            )

        predictor = AstroPredictor(natal_data)
        astro_data = predictor.generate_prediction(target_date)

        return {
            "success": True,
            "user_id": telegram_id,
            "target_date": target_date.isoformat(),
            "astrology": astro_data,
            "natal_chart_summary": {
                "planets_count": len(natal_data.get('planets', {})),
                "dominant_element": _get_dominant_element(natal_data),
                "ascendant": natal_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения астрологических данных для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения астрологических данных: {str(e)}"
        )


def _get_dominant_element(natal_data: dict) -> str:
    """Определение доминирующего элемента"""
    try:
        element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
        if element_balance:
            return max(element_balance.items(), key=lambda x: x[1])[0]
        return 'неизвестно'
    except Exception:
        return 'неизвестно'


@app.get("/api/v1/psychomatrix/{telegram_id}", tags=["calculations"])
async def get_psychomatrix_only(telegram_id: int):
    """
    Получение только данных психоматрицы
    """
    try:
        logger.info(f"🔢 Запрос психоматрицы для пользователя {telegram_id}")

        from backend.matrix_services import get_user_matrix, get_matrix_summary

        matrix_data = await get_user_matrix(telegram_id)
        if not matrix_data:
            raise HTTPException(
                status_code=404,
                detail="Психоматрица не найдена"
            )

        matrix_summary = await get_matrix_summary(telegram_id)

        return {
            "success": True,
            "user_id": telegram_id,
            "psychomatrix": matrix_data,
            "summary": matrix_summary,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения психоматрицы для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения психоматрицы: {str(e)}"
        )


@app.get("/api/v1/system/status", response_model=SystemStatusResponse, tags=["health", "admin"])
async def get_system_status():
    """
    Получение полного статуса системы с ML метриками
    """
    try:
        logger.info("📊 Запрос статуса системы")

        # Получаем здоровье системы
        system_health = await assistant.get_system_health()

        # Статистика БД
        db_stats = await get_database_stats()

        # Метрики производительности
        uptime = time.time() - start_time
        performance = {
            "uptime_seconds": uptime,
            "total_requests": request_count,
            "requests_per_second": round(request_count / uptime, 2) if uptime > 0 else 0,
            "memory_usage_mb": 0,  # Заглушка, в реальности нужно получать из psutil
            "active_connections": 0  # Заглушка
        }

        return SystemStatusResponse(
            status=system_health.get('status', 'unknown'),
            timestamp=datetime.now().isoformat(),
            components=system_health.get('components', {}),
            performance=performance,
            recommendations=system_health.get('recommendations', [])
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса системы: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статуса системы: {str(e)}"
        )


@app.get("/api/v1/admin/database/stats", tags=["admin"])
async def get_database_statistics():
    """
    Получение статистики базы данных (только для администрирования)
    ОБНОВЛЕНО: Включает ML метрики
    """
    try:
        logger.info("📊 Запрос статистики базы данных")

        stats = await get_database_stats()

        return {
            "success": True,
            "database_stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статистики БД: {str(e)}"
        )


@app.post("/api/v1/admin/cleanup", tags=["admin"])
async def cleanup_old_data(days_old: int = Query(30, description="Удалять данные старше N дней")):
    """
    Очистка устаревших данных (только для администрирования)
    """
    try:
        logger.info(f"🧹 Запрос очистки данных старше {days_old} дней")

        if days_old < 1:
            raise HTTPException(
                status_code=400,
                detail="Параметр days_old должен быть положительным числом"
            )

        cleanup_result = await calculation_optimizer.cleanup_old_calculations(days_old)

        return {
            "success": True,
            "cleanup_result": cleanup_result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка очистки данных: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка очистки данных: {str(e)}"
        )


@app.get("/api/v1/version", tags=["health"])
async def get_version():
    """
    Получение информации о версии API
    """
    return {
        "service": "Astra Calculations API",
        "version": "3.0.0",
        "description": "API для расчетных данных (биоритмы, астрология, психоматрицы, ML аналитика)",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Биоритмы и энергетические циклы",
            "Астрологические расчеты и транзиты",
            "Нумерологическая психоматрица",
            "ML аналитика и рекомендации",
            "AI-инсайты и тренды",
            "Персонализированные прогнозы"
        ]
    }


# Обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    logger.warning(f"HTTP ошибка {exc.status_code}: {exc.detail}")

    # Генерируем ID запроса для отслеживания
    import uuid
    request_id = str(uuid.uuid4())[:8]

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Exception",
            detail=exc.detail,
            timestamp=datetime.now().isoformat(),
            request_id=request_id
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений"""
    logger.error(f"Необработанная ошибка: {exc}")

    # Генерируем ID запроса для отслеживания
    import uuid
    request_id = str(uuid.uuid4())[:8]

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="Произошла внутренняя ошибка сервера",
            timestamp=datetime.now().isoformat(),
            request_id=request_id
        ).dict()
    )


# Для запуска напрямую
#if __name__ == "__main__":
#    uvicorn.run(
#        "api_entrypoint:app",
#        host="0.0.0.0",
#        port=8000,
#        reload=True,
#        log_level="info"
#    )



if __name__ == "__main__":
    import os

    # Используем переменные окружения или значения по умолчанию
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))

    print(f"🚀 Запуск API на {API_HOST}:{API_PORT}")

    uvicorn.run(
        "api_entrypoint:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )