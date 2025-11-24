from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import logging
import uvicorn
from fastapi.responses import JSONResponse

from backend.assistant import assistant
from backend.calculation_services import calculation_service, calculation_optimizer
from backend.database import check_db_connection, get_database_stats, init_db
from backend.user_services import get_user_profile

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Astra Calculations API",
    description="API для доступа к расчетным данным проекта Astra (биоритмы, астрология, психоматрицы)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модели Pydantic для запросов и ответов
class CalculationRequest(BaseModel):
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    target_date: date = Field(default_factory=date.today, description="Дата для расчетов")


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    database_connected: bool
    version: str


class CalculationResponse(BaseModel):
    success: bool
    user_id: int
    target_date: str
    calculations: Dict[str, Any]
    user_context: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None


class UserDataStatusResponse(BaseModel):
    user_id: int
    has_basic_data: bool
    has_natal_chart: bool
    has_psyho_matrix: bool
    has_biorhythms: bool
    is_complete: bool
    profile_exists: bool


class HealthCheckResponse(BaseModel):
    user_id: int
    overall_status: str
    check_timestamp: str
    detailed_checks: Dict[str, Any]
    recommendations: List[str]


class StatisticsResponse(BaseModel):
    user_id: int
    request_count: int
    calculations_count: int
    biorhythms_count: int
    first_calculation: Optional[str]
    last_calculation: Optional[str]
    average_energy: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Запуск Astra Calculations API...")

    # Проверяем подключение к БД
    db_connected = await check_db_connection()
    if not db_connected:
        logger.error("❌ Не удалось подключиться к базе данных")
        return

    # Инициализируем БД если нужно
    await init_db()
    logger.info("✅ Astra Calculations API готов к работе")


@app.get("/", include_in_schema=False)
async def root():
    """Корневой endpoint"""
    return {
        "message": "Astra Calculations API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    db_connected = await check_db_connection()

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        service="astra_calculations",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected,
        version="2.0.0"
    )


@app.post("/api/v1/calculations", response_model=CalculationResponse)
async def get_calculations(request: CalculationRequest):
    """
    Получение полного пакета расчетных данных для пользователя
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


@app.post("/api/v1/calculations/optimized", response_model=CalculationResponse)
async def get_optimized_calculations(
        telegram_id: int = Query(..., description="ID пользователя в Telegram"),
        target_date: date = Query(default_factory=date.today, description="Дата для расчетов"),
        include_biorhythms: bool = Query(True, description="Включить биоритмы"),
        include_astrology: bool = Query(True, description="Включить астрологию"),
        include_psychomatrix: bool = Query(True, description="Включить психоматрицу")
):
    """
    Получение оптимизированного пакета расчетов с фильтрацией по типам
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


@app.get("/api/v1/users/{telegram_id}/status", response_model=UserDataStatusResponse)
async def get_user_data_status(telegram_id: int):
    """
    Получение статуса данных пользователя
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
            is_complete=status['is_complete'],
            profile_exists=user_profile is not None
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статуса: {str(e)}"
        )


@app.get("/api/v1/users/{telegram_id}/health", response_model=HealthCheckResponse)
async def get_user_health_check(telegram_id: int):
    """
    Проверка здоровья расчетных данных пользователя
    """
    try:
        logger.info(f"🏥 Запрос проверки здоровья данных для пользователя {telegram_id}")

        health_status = await calculation_optimizer.get_calculation_health_check(telegram_id)

        # Формируем рекомендации на основе проверок
        recommendations = []
        detailed_checks = health_status.get('detailed_checks', {})

        for check_type, check_data in detailed_checks.items():
            if check_data.get('status') != 'healthy':
                recommendation = check_data.get('recommendation')
                if recommendation:
                    recommendations.append(recommendation)

        # Добавляем общие рекомендации
        if not recommendations:
            recommendations.append("Все системы в порядке. Данные актуальны и готовы к использованию.")

        return HealthCheckResponse(
            user_id=telegram_id,
            overall_status=health_status['overall_status'],
            check_timestamp=health_status['check_timestamp'],
            detailed_checks=detailed_checks,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"❌ Ошибка проверки здоровья для {telegram_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка проверки здоровья: {str(e)}"
        )


@app.get("/api/v1/users/{telegram_id}/statistics", response_model=StatisticsResponse)
async def get_user_statistics(telegram_id: int):
    """
    Получение статистики пользователя
    """
    try:
        logger.info(f"📈 Запрос статистики для пользователя {telegram_id}")

        stats = await assistant.get_user_statistics(telegram_id)

        return StatisticsResponse(
            user_id=telegram_id,
            request_count=stats.get('request_count', 0),
            calculations_count=stats.get('prediction_stats', {}).get('total_calculations', 0),
            biorhythms_count=stats.get('biorhythm_stats', {}).get('total_records', 0),
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


@app.get("/api/v1/biorhythms/{telegram_id}")
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


@app.get("/api/v1/astrology/{telegram_id}")
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


@app.get("/api/v1/psychomatrix/{telegram_id}")
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


@app.get("/api/v1/admin/database/stats")
async def get_database_statistics():
    """
    Получение статистики базы данных (только для администрирования)
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


@app.post("/api/v1/admin/cleanup")
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


@app.get("/api/v1/version")
async def get_version():
    """
    Получение информации о версии API
    """
    return {
        "service": "Astra Calculations API",
        "version": "2.0.0",
        "description": "API для расчетных данных (биоритмы, астрология, психоматрицы)",
        "timestamp": datetime.now().isoformat()
    }


# Обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    logger.warning(f"HTTP ошибка {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Exception",
            detail=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений"""
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="Произошла внутренняя ошибка сервера",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# Для запуска напрямую
if __name__ == "__main__":
    uvicorn.run(
        "api_entrypoint:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )