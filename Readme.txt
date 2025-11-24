проект astra является частью проекта personal_assistant состоящего из трех проектов:

astra: подготовка натальных карт, психоматриц, расчета биоритмов и рекоммендаций на один день

testing: психологическое тестирование и потребностей пользователя

assistant: на основании расчетов astra и testing выдает персонализированные рекоммендации на один день на базе ollama

astra: развернут локально (включая бд), взаимодействие телеграм бот 

расчеты: сбор первичной информации пользователя, расчет натальной карты, психоматрицы, биоритмов, лунных фаз, расчет данных на день.

Структура проекта:

backend:
backend.api_entrypoint.py
backend.aspect_recommendations.py
backend.assistant.py
backend.biorhythm_calculator.py
backend.biorhythm_services.py
backend.calculation_services.py
backend.chart_services.py
backend.database.py
backend.db_connection.py
backend.__init__.py
backend.matrix_services.py
backend.moon.py
backend.natal_chart.py
backend.predictions.py
backend.prediction_services.py
backend.psyho_matrix.py
backend.user_services.py

bot:
bot.config.py
bot.handlers.py
bot.__init__.py
bot.main.py
bot..env

ephe

init-scripts:
init-scripts.01-init-tables.sql

docker-compose.override.yml

docker-compose.yml

Dockerfile.api.dev

Dockerfile.bot.dev

requirements.txt

.env


код модулей проекта:

backend:

backend.api_entrypoint.py

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

backend.aspect_recommendations.py

import logging
from typing import Dict, List, Any
import random

logger = logging.getLogger(__name__)


class AspectRecommendationEngine:
    """
    Улучшенный движок рекомендаций с конкретными областями применения
    """

    def __init__(self):
        # Конкретные области применения для разных аспектов
        self.action_areas = {
            'conjunction': [
                "начало новых проектов", "решительные действия", "запуск инициатив",
                "активные перемены", "проявление инициативы", "старт важных дел"
            ],
            'opposition': [
                "переговоры и компромиссы", "поиск баланса", "урегулирование конфликтов",
                "работа в команде", "учет разных мнений", "дипломатические решения"
            ],
            'square': [
                "преодоление препятствий", "решение сложных задач", "борьба с трудностями",
                "устранение проблем", "преодоление кризисов", "исправление ошибок"
            ],
            'trine': [
                "творческие проекты", "сотрудничество", "реализация идей",
                "гармоничное развитие", "укрепление отношений", "обучение и рост"
            ],
            'sextile': [
                "установление связей", "профессиональный рост", "поиск возможностей",
                "планирование будущего", "расширение кругозора", "новые знакомства"
            ]
        }

        # Конкретные действия для планет
        self.planet_actions = {
            'Sun': [
                "проявление лидерства", "укрепление уверенности", "творческая реализация",
                "демонстрация талантов", "работа над имиджем", "развитие индивидуальности"
            ],
            'Moon': [
                "забота о эмоциях", "создание уюта", "работа с интуицией",
                "семейные дела", "отдых и восстановление", "кулинарные эксперименты"
            ],
            'Mercury': [
                "обучение и учеба", "переговоры", "письменная работа",
                "планирование", "анализ информации", "коммуникация"
            ],
            'Venus': [
                "укрепление отношений", "творчество", "финансовые вопросы",
                "создание красоты", "социальная активность", "искусство"
            ],
            'Mars': [
                "спорт и активность", "конкуренция", "решение задач",
                "техническая работа", "защита интересов", "физические нагрузки"
            ],
            'Jupiter': [
                "планирование путешествий", "обучение", "расширение бизнеса",
                "философские размышления", "поиск возможностей", "личностный рост"
            ],
            'Saturn': [
                "планирование", "организация", "работа с долгосрочными целями",
                "укрепление дисциплины", "завершение проектов", "структурирование"
            ],
            'Uranus': [
                "инновации", "эксперименты", "технологические проекты",
                "нестандартные решения", "изменение подходов", "свободное творчество"
            ],
            'Neptune': [
                "медитация", "творчество", "работа с интуицией",
                "помощь другим", "искусство", "духовные практики"
            ],
            'Pluto': [
                "трансформация", "избавление от старого", "глубинный анализ",
                "работа с кризисами", "психологические вопросы", "стратегические изменения"
            ]
        }

        # Улучшенные шаблоны рекомендаций
        self.aspect_templates = {
            'conjunction': {
                'positive': [
                    "Энергия {transit} и {natal} объединяется - идеальное время для {action} в области {area}",
                    "Соединение {transit} с {natal} дает мощный импульс для {action}, особенно в {area}",
                    "Используйте объединенную энергию {transit} и {natal} для {action}, например в {area}"
                ],
                'challenge': [
                    "Соединение {transit} и {natal} создает напряжение - будьте внимательны при {action} в {area}",
                    "Энергия аспекта очень концентрированная - сфокусируйтесь на {action} в {area}",
                    "Мощная энергия соединения требует осторожности в {area}, особенно при {action}"
                ]
            },
            'opposition': {
                'positive': [
                    "Оппозиция {transit} и {natal} помогает в {action} - ищите баланс в {area}",
                    "Идеальное время для {action} через компромиссы в {area}",
                    "Используйте противостояние энергий для {action} в {area}"
                ],
                'challenge': [
                    "Оппозиция {transit}-{natal} требует гибкости в {area}, особенно при {action}",
                    "Возможны противоречия в {area} - ищите золотую середину для {action}",
                    "Избегайте категоричных решений в {area}, лучше сосредоточьтесь на {action}"
                ]
            },
            'square': {
                'positive': [
                    "Квадрат {transit} и {natal} дает энергию для {action} в сложных ситуациях {area}",
                    "Используйте напряжение аспекта для {action} в проблемных {area}",
                    "Это время активных действий для {action} в трудных {area}"
                ],
                'challenge': [
                    "Квадратура {transit}-{natal} требует осторожности при {action} в {area}",
                    "Возможны сложности в {area} - имейте запасной план для {action}",
                    "Избегайте конфронтации в {area}, решайте вопросы через {action}"
                ]
            },
            'trine': {
                'positive': [
                    "Трин {transit} и {natal} приносит гармонию для {action} в {area}",
                    "Благоприятное время для {action} через сотрудничество в {area}",
                    "Энергия течет легко - идеально для {action} в {area}"
                ],
                'challenge': [
                    "При легкой энергии трина важно не упускать возможности для {action} в {area}",
                    "Не расслабляйтесь слишком - используйте период для {action} в {area}",
                    "Сохраняйте активность в {area}, особенно для {action}"
                ]
            },
            'sextile': {
                'positive': [
                    "Секстиль {transit} и {natal} открывает перспективы для {action} в {area}",
                    "Идеальное время для {action} через новые связи в {area}",
                    "Используйте возможности для {action} и роста в {area}"
                ],
                'challenge': [
                    "При множестве возможностей в {area} важно правильно выбрать направление для {action}",
                    "Не распыляйтесь в {area} - выберите самые перспективные варианты для {action}",
                    "Уделите внимание планированию {action} в {area}"
                ]
            }
        }

        # Русские названия планет
        self.planet_names_ru = {
            'Sun': 'Солнца', 'Moon': 'Луны', 'Mercury': 'Меркурия',
            'Venus': 'Венеры', 'Mars': 'Марса', 'Jupiter': 'Юпитера',
            'Saturn': 'Сатурна', 'Uranus': 'Урана', 'Neptune': 'Нептуна',
            'Pluto': 'Плутона', 'North_Node': 'Северного Узла',
            'Ascendant': 'Асцендента', 'Midheaven': 'Середины Неба'
        }

    def generate_aspect_recommendations(self, aspects_data: List[Dict]) -> List[str]:
        """
        Генерация конкретных рекомендаций с областями применения
        """
        recommendations = []

        try:
            # Сортируем аспекты по силе (самые сильные первые)
            strong_aspects = [a for a in aspects_data if a.get('strength', 0) > 0.7]
            sorted_aspects = sorted(strong_aspects, key=lambda x: x.get('strength', 0), reverse=True)

            # Берем только топ-3 самых сильных аспекта
            for aspect in sorted_aspects[:3]:
                rec = self._generate_specific_aspect_recommendation(aspect)
                if rec:
                    recommendations.append(rec)

            # Если сильных аспектов мало, добавляем общие рекомендации
            if len(recommendations) < 2:
                general_recs = self._get_general_recommendations(aspects_data)
                recommendations.extend(general_recs[:2])

        except Exception as e:
            logger.error(f"❌ Ошибка генерации рекомендаций аспектов: {e}")
            recommendations = [
                "Сегодня стабильный астрологический фон - хорошее время для плановых дел и рутинных задач"]

        return recommendations

    def _generate_specific_aspect_recommendation(self, aspect: Dict) -> str:
        """Генерация конкретной рекомендации с областями применения"""
        try:
            transit_planet = aspect.get('transit_planet', '')
            natal_planet = aspect.get('natal_planet', '')
            aspect_type = aspect.get('aspect', '')
            strength = aspect.get('strength', 0)

            if not all([transit_planet, natal_planet, aspect_type]):
                return None

            # Получаем русские названия планет
            transit_ru = self.planet_names_ru.get(transit_planet, transit_planet)
            natal_ru = self.planet_names_ru.get(natal_planet, natal_planet)

            # Выбираем тип рекомендации (позитивная или вызов)
            rec_type = 'positive' if strength > 0.8 else 'challenge'

            # Выбираем конкретную область и действие
            area = random.choice(self.action_areas.get(aspect_type, ["разных сферах жизни"]))
            action = random.choice(self.planet_actions.get(transit_planet, ["активных действий"]))

            # Получаем шаблоны для этого типа аспекта
            templates = self.aspect_templates.get(aspect_type, {}).get(rec_type, [])

            if templates:
                template = random.choice(templates)
                recommendation = template.format(
                    transit=transit_ru,
                    natal=natal_ru,
                    action=action,
                    area=area
                )

                # Добавляем эмодзи в зависимости от типа аспекта
                emoji_map = {
                    'conjunction': '⚡', 'opposition': '⚖️',
                    'square': '🎯', 'trine': '🌟', 'sextile': '💫'
                }
                emoji = emoji_map.get(aspect_type, '✨')

                return f"{emoji} {recommendation}"

        except Exception as e:
            logger.warning(f"⚠️ Ошибка генерации рекомендации для аспекта: {e}")

        return None

    def _get_general_recommendations(self, aspects_data: List[Dict]) -> List[str]:
        """Общие рекомендации с конкретными действиями"""
        general_recs = []

        try:
            total_aspects = len(aspects_data)
            strong_aspects = len([a for a in aspects_data if a.get('strength', 0) > 0.7])

            # Конкретные рекомендации по количеству аспектов
            if total_aspects == 0:
                actions = ["чтении книг", "уборке дома", "планировании недели", "отдыхе и восстановлении"]
                general_recs.append(
                    f"🌙 Сегодня спокойный астрологический фон - хорошее время для {random.choice(actions)}")
            elif total_aspects <= 3:
                actions = ["размеренной работе", "анализу информации", "подготовке документов", "обучению"]
                general_recs.append(f"⚖️ Небольшое количество аспектов - день подходит для {random.choice(actions)}")
            elif total_aspects > 8:
                actions = ["решению срочных вопросов", "многозадачности", "переговорам", "принятию решений"]
                general_recs.append(f"🎯 Много астрологических влияний - будьте готовы к {random.choice(actions)}")

            # Конкретные рекомендации по силе аспектов
            if strong_aspects >= 3:
                actions = ["важных решений", "стратегического планирования", "реализации проектов", "перемен"]
                general_recs.append(f"💥 Несколько сильных аспектов - важный день для {random.choice(actions)}")
            elif strong_aspects == 0 and total_aspects > 0:
                actions = ["подготовки и анализа", "исследования возможностей", "создания планов", "обучения новому"]
                general_recs.append(f"🌊 Аспекты слабые - хорошее время для {random.choice(actions)}")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка генерации общих рекомендаций: {e}")

        return general_recs


# Глобальный экземпляр движка рекомендаций
aspect_recommendations = AspectRecommendationEngine()

backend.assistant.py

from backend.user_services import create_or_update_user, get_user_profile, update_user_profession, \
    increment_request_count
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_user_predictions, \
    format_data_for_user, get_daily_calculations, save_daily_calculations
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
import logging
import asyncio
from typing import Dict, Any, List, Optional
import json
import math

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления расчетными данными (без AI логики)"""

    def __init__(self):
        self.calculation_cache = {}

    def _calculate_user_age(self, birth_date: date) -> int:
        """Расчет возраста пользователя"""
        try:
            if not birth_date:
                return 0
            today = date.today()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета возраста: {e}")
            return 0

    def _estimate_experience_level(self, age: int, profession: str) -> str:
        """Оценка уровня профессионального опыта"""
        if not profession or profession.lower() in ['не указана', 'нет', '']:
            return "неизвестно"

        if age < 22:
            return "начинающий"
        elif age < 30:
            return "опытный"
        elif age < 45:
            return "профессионал"
        else:
            return "эксперт"

    def _get_energy_level_description(self, percentage: float) -> Dict[str, str]:
        """Описание уровня энергии"""
        if percentage >= 90:
            return {"level": "очень высокий", "description": "идеально для сложных задач и важных решений"}
        elif percentage >= 75:
            return {"level": "высокий", "description": "отлично для продуктивной работы"}
        elif percentage >= 60:
            return {"level": "хороший", "description": "подходит для активной деятельности"}
        elif percentage >= 40:
            return {"level": "средний", "description": "стабильно для рутинных задач"}
        elif percentage >= 20:
            return {"level": "низкий", "description": "требует бережного отношения к силам"}
        else:
            return {"level": "критически низкий", "description": "необходим отдых и восстановление"}

    def _get_physical_recommendation(self, percentage: float) -> str:
        """Рекомендации по физической активности"""
        if percentage >= 90:
            return "идеальное время для спорта и физических нагрузок"
        elif percentage >= 70:
            return "хороший день для активной работы и движения"
        elif percentage >= 50:
            return "подходит для умеренной физической активности"
        elif percentage >= 30:
            return "берегите силы, избегайте перегрузок"
        else:
            return "требуется отдых и восстановление физических сил"

    def _get_emotional_recommendation(self, percentage: float) -> str:
        """Рекомендации по эмоциональному состоянию"""
        if percentage >= 90:
            return "отличное настроение для общения и новых знакомств"
        elif percentage >= 70:
            return "эмоционально стабильный день"
        elif percentage >= 50:
            return "сохраняйте эмоциональное равновесие"
        elif percentage >= 30:
            return "будьте осторожны в общении, контролируйте эмоции"
        else:
            return "критический эмоциональный фон - избегайте конфликтов и стрессов"

    def _get_intellectual_recommendation(self, percentage: float) -> str:
        """Рекомендации по интеллектуальной деятельности"""
        if percentage >= 90:
            return "пик умственных способностей - время для сложных задач и обучения"
        elif percentage >= 70:
            return "отличные когнитивные способности для анализа и планирования"
        elif percentage >= 50:
            return "стабильная умственная активность"
        elif percentage >= 30:
            return "сосредоточьтесь на простых задачах, избегайте сложного анализа"
        else:
            return "умственное истощение - время для отдыха и простых действий"

    def _get_season(self, target_date: date) -> str:
        """Определение сезона для контекста"""
        try:
            month = target_date.month
            if month in [12, 1, 2]:
                return 'зима'
            elif month in [3, 4, 5]:
                return 'весна'
            elif month in [6, 7, 8]:
                return 'лето'
            else:
                return 'осень'
        except Exception as e:
            logger.warning(f"⚠️ Ошибка определения сезона: {e}")
            return 'неизвестно'

    def _get_lunar_phase(self, target_date: date) -> str:
        """Упрощенный расчет лунной фазы"""
        try:
            day = target_date.day
            if day <= 7:
                return 'растущая луна'
            elif day <= 14:
                return 'полнолуние'
            elif day <= 21:
                return 'убывающая луна'
            else:
                return 'новолуние'
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета лунной фазы: {e}")
            return 'неизвестно'

    def _prepare_calculation_data(self, telegram_id: int, user_profile: dict, prediction: dict,
                                  target_date: date) -> dict:
        """
        Подготовка структурированных данных для внешнего потребления
        """
        try:
            daily_calculations = prediction.get('daily_calculations', {})
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            astro_data = daily_calculations.get('astro_data', {})
            natal_chart = prediction.get('natal_chart', {})
            psyho_matrix = prediction.get('psyho_matrix', {})

            # Базовые данные пользователя
            user_age = self._calculate_user_age(user_profile.get('birth_date'))
            experience_level = self._estimate_experience_level(user_age, user_profile.get('profession'))

            # Оптимизированные данные для внешнего API
            prepared_data = {
                # Контекст пользователя
                'user_context': {
                    'telegram_id': telegram_id,
                    'age': user_age,
                    'experience_level': experience_level,
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'current_city': user_profile.get('current_city', 'не указан'),
                    'birth_city': user_profile.get('birth_city', 'не указан'),
                    'gender': user_profile.get('gender', 'не указан')
                },

                # Энергетическое состояние
                'energy_state': {
                    'overall_energy': biorhythm_data.get('overall_energy', {}),
                    'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                    'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                    'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {})
                },

                # Астрологические данные
                'astro_data': {
                    'aspects_count': astro_data.get('aspects_count', 0),
                    'strong_aspects_count': astro_data.get('strong_aspects_count', 0),
                    'retrograde_planets': astro_data.get('retrograde_planets', []),
                    'key_aspects': astro_data.get('key_aspects', [])[:3]  # Только топ-3
                },

                # Статические данные
                'static_profile': {
                    'natal_chart_summary': {
                        'planets_count': len(natal_chart.get('planets', {})),
                        'dominant_element': self._get_dominant_element(natal_chart),
                        'ascendant': natal_chart.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
                    },
                    'psyho_matrix_summary': {
                        'life_path_number': psyho_matrix.get('basic_numbers', {}).get('first'),
                        'matrix_complexity': self._calculate_matrix_complexity(psyho_matrix)
                    }
                },

                # Контекст дня
                'daily_context': {
                    'season': self._get_season(target_date),
                    'day_of_week': target_date.strftime('%A'),
                    'lunar_phase': self._get_lunar_phase(target_date),
                    'is_weekend': target_date.weekday() >= 5
                },

                # Мета-информация
                'calculation_meta': {
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'calculation_timestamp': datetime.now().isoformat(),
                    'data_version': '1.0'
                }
            }

            logger.info(f"✅ Данные подготовлены для пользователя {telegram_id} на {target_date}")
            return prepared_data

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки данных: {e}")
            return self._prepare_data_fallback(user_profile, target_date)

    def _get_dominant_element(self, natal_chart: dict) -> str:
        """Определение доминирующего элемента в натальной карте"""
        try:
            element_balance = natal_chart.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _calculate_matrix_complexity(self, psyho_matrix: dict) -> str:
        """Оценка сложности психоматрицы"""
        try:
            matrix_data = psyho_matrix.get('pythagoras_matrix', {})
            total_digits = sum(matrix_data.values())
            if total_digits >= 15:
                return "сложная"
            elif total_digits >= 10:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"

    def _prepare_data_fallback(self, user_profile: dict, target_date: date) -> dict:
        """Резервная подготовка данных при ошибках"""
        return {
            'user_context': {
                'profession': user_profile.get('profession', 'не указана'),
                'position': user_profile.get('job_position', 'не указана'),
                'current_city': user_profile.get('current_city', 'не указан')
            },
            'energy_state': {},
            'astro_data': {},
            'static_profile': {},
            'daily_context': {
                'target_date': target_date.strftime('%Y-%m-%d')
            },
            'calculation_meta': {
                'fallback_mode': True,
                'error': 'Данные временно недоступны'
            }
        }

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None, gender: str = None):
        """Сбор и сохранение всех данных пользователя"""
        try:
            logger.info(f"🔄 Начало сбора данных для пользователя {telegram_id}")

            async with async_session() as session:
                try:
                    # 1. Сохраняем основные данные пользователя
                    user = await create_or_update_user(
                        telegram_id=telegram_id,
                        birth_date=birth_date,
                        birth_time=birth_time,
                        birth_city=birth_city,
                        current_city=current_city,
                        profession=profession,
                        job_position=job_position,
                        gender=gender
                    )
                    logger.info(f"✅ Данные пользователя сохранены")

                    # 2. Создаем натальную карту
                    birth_datetime = datetime.combine(birth_date, birth_time)
                    natal_chart = await create_and_save_natal_chart(
                        telegram_id=telegram_id,
                        city=birth_city,
                        birth_datetime=birth_datetime,
                        timezone="Europe/Moscow"
                    )
                    logger.info(f"✅ Натальная карта создана")

                    # 3. Рассчитываем психоматрицу
                    matrix_data = await calculate_and_save_psyho_matrix(telegram_id)
                    logger.info(f"✅ Психоматрица рассчитана")

                    # 4. Рассчитываем биоритмы на сегодня
                    biorhythms = await calculate_and_save_biorhythms(telegram_id)
                    logger.info(f"✅ Биоритмы рассчитаны")

                    await session.commit()

                    return {
                        'success': True,
                        'message': "✅ Все данные успешно собраны и сохранены!",
                        'data_collected': {
                            'user_profile': True,
                            'natal_chart': True,
                            'psyho_matrix': True,
                            'biorhythms': True
                        }
                    }

                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ Ошибка в транзакции сбора данных для {telegram_id}: {e}")
                    raise

        except Exception as e:
            logger.error(f"❌ Ошибка сбора данных для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка при сборе данных: {str(e)}"
            }

    async def get_recommendations(self, telegram_id: int, target_date: date):
        """
        Получение расчетных данных на выбранную дату (без AI рекомендаций)
        """
        try:
            logger.info(f"📅 Формирование данных на {target_date} для {telegram_id}")

            # Увеличиваем счетчик обращений
            await increment_request_count(telegram_id)
            logger.info(f"📈 Счетчик обращений увеличен для {telegram_id}")

            # Проверяем что дата не в прошлом
            if target_date < date.today():
                return {
                    'success': False,
                    'message': "❌ Нельзя получить данные для прошедших дат"
                }

            # Генерируем и сохраняем данные для выбранной даты
            prediction = await generate_and_save_prediction(telegram_id, target_date)

            # Получаем профиль пользователя
            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {
                    'success': False,
                    'message': "❌ Профиль пользователя не найден"
                }

            # 1. Данные для пользователя (через бот)
            user_data = await format_data_for_user(prediction)

            # 2. Структурированные данные для внешнего API
            structured_data = self._prepare_calculation_data(telegram_id, user_profile, prediction, target_date)

            result = {
                'success': True,
                'date': target_date.isoformat(),
                'user_data': user_data,  # Для бота
                'structured_data': structured_data,  # Для внешнего API
                'prediction_data': prediction,  # Полные данные
                'user_profile': user_profile
            }

            logger.info(f"✅ Данные сформированы для {telegram_id} на {target_date}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить данные на выбранную дату: {str(e)}"
            }

    async def get_calculation_package(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """
        Полный пакет расчетных данных для внешнего API
        Оптимизирован для проекта Assistant
        """
        try:
            # Проверяем кэш
            cache_key = f"{telegram_id}_{target_date}"
            if cache_key in self.calculation_cache:
                cached_data = self.calculation_cache[cache_key]
                # Проверяем актуальность кэша (5 минут)
                if datetime.now().timestamp() - cached_data['timestamp'] < 300:
                    logger.info(f"✅ Использованы кэшированные данные для {telegram_id}")
                    return cached_data['data']

            # Получаем основные данные
            result = await self.get_recommendations(telegram_id, target_date)

            if not result['success']:
                return {
                    'success': False,
                    'error': result['message'],
                    'timestamp': datetime.now().isoformat()
                }

            # Формируем оптимизированный пакет
            calculation_package = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': result['structured_data'],
                'raw_data_available': True,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'astra_calculations'
            }

            # Сохраняем в кэш
            self.calculation_cache[cache_key] = {
                'data': calculation_package,
                'timestamp': datetime.now().timestamp()
            }

            logger.info(f"✅ Пакет расчетов подготовлен для {telegram_id}")
            return calculation_package

        except Exception as e:
            logger.error(f"❌ Ошибка формирования пакета расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_todays_recommendations(self, telegram_id: int):
        """Получение данных на сегодня"""
        return await self.get_recommendations(telegram_id, date.today())

    async def get_tomorrows_recommendations(self, telegram_id: int):
        """Получение данных на завтра"""
        tomorrow = date.today() + timedelta(days=1)
        return await self.get_recommendations(telegram_id, tomorrow)

    async def get_date_recommendations(self, telegram_id: int, target_date: date):
        """Получение данных на выбранную дату"""
        return await self.get_recommendations(telegram_id, target_date)

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None, gender: str = None):
        """Обновление профессиональной информации"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            user_profile = await get_user_profile(telegram_id)
            if user_profile:
                await create_or_update_user(
                    telegram_id=telegram_id,
                    birth_date=user_profile['birth_date'],
                    birth_time=user_profile['birth_time'],
                    birth_city=user_profile['birth_city'],
                    current_city=current_city,
                    profession=profession,
                    job_position=job_position,
                    gender=gender
                )

            logger.info(f"✅ Профессиональные данные обновлены для {telegram_id}")
            return {
                'success': True,
                'message': "✅ Профессиональная информация успешно обновлена!"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка обновления профессии для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка обновления данных: {str(e)}"
            }

    async def get_user_data_status(self, telegram_id: int):
        """Проверка статуса собранных данных пользователя"""
        try:
            user_profile = await get_user_profile(telegram_id)
            natal_chart = await get_user_natal_chart(telegram_id)
            psyho_matrix = await get_user_matrix(telegram_id)
            biorhythms = await get_user_biorhythms(telegram_id)

            has_basic_data = user_profile is not None
            has_natal_chart = natal_chart is not None
            has_psyho_matrix = psyho_matrix is not None
            has_biorhythms = biorhythms is not None

            return {
                'has_basic_data': has_basic_data,
                'has_natal_chart': has_natal_chart,
                'has_psyho_matrix': has_psyho_matrix,
                'has_biorhythms': has_biorhythms,
                'is_complete': has_basic_data and has_natal_chart and has_psyho_matrix and has_biorhythms,
                'user_profile': user_profile
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса данных для {telegram_id}: {e}")
            return {
                'has_basic_data': False,
                'has_natal_chart': False,
                'has_psyho_matrix': False,
                'has_biorhythms': False,
                'is_complete': False
            }

    async def get_user_statistics(self, telegram_id: int):
        """Получение статистики пользователя"""
        try:
            from backend.prediction_services import get_prediction_statistics
            from backend.biorhythm_services import get_biorhythm_statistics
            from backend.user_services import get_user_request_count

            data_status = await self.get_user_data_status(telegram_id)
            prediction_stats = await get_prediction_statistics(telegram_id)
            biorhythm_stats = await get_biorhythm_statistics(telegram_id)
            request_count = await get_user_request_count(telegram_id)

            return {
                'data_status': data_status,
                'prediction_stats': prediction_stats,
                'biorhythm_stats': biorhythm_stats,
                'request_count': request_count,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {
                'data_status': {},
                'prediction_stats': {},
                'biorhythm_stats': {},
                'request_count': 0,
                'error': str(e)
            }

    async def cleanup_user_data(self, telegram_id: int):
        """Очистка данных пользователя"""
        try:
            from backend.biorhythm_services import cleanup_old_biorhythms
            from backend.prediction_services import cleanup_old_predictions

            biorhythm_cleaned = await cleanup_old_biorhythms()
            prediction_cleaned = await cleanup_old_predictions()

            logger.info(f"🧹 Очищены данные для пользователя {telegram_id}")
            return {
                'success': True,
                'biorhythm_records_cleaned': biorhythm_cleaned,
                'prediction_records_cleaned': prediction_cleaned,
                'message': f"✅ Очищено {biorhythm_cleaned} записей биоритмов и {prediction_cleaned} предсказаний"
            }

        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Ошибка при очистке данных: {str(e)}"
            }

    async def validate_user_data(self, telegram_id: int):
        """Проверка корректности данных пользователя"""
        try:
            from backend.prediction_services import validate_prediction_data

            data_status = await self.get_user_data_status(telegram_id)
            prediction_valid = await validate_prediction_data(telegram_id)

            issues = []

            if not data_status['has_basic_data']:
                issues.append("Отсутствуют основные данные пользователя")
            if not data_status['has_natal_chart']:
                issues.append("Отсутствует натальная карта")
            if not data_status['has_psyho_matrix']:
                issues.append("Отсутствует психоматрица")
            if not data_status['has_biorhythms']:
                issues.append("Отсутствуют данные биоритмов")
            if not prediction_valid:
                issues.append("Некорректные данные предсказаний")

            return {
                'is_valid': len(issues) == 0,
                'issues': issues,
                'data_status': data_status,
                'prediction_valid': prediction_valid
            }

        except Exception as e:
            logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
            return {
                'is_valid': False,
                'issues': [f"Ошибка валидации: {str(e)}"],
                'data_status': {},
                'prediction_valid': False
            }

    def clear_cache(self):
        """Очистка внутреннего кэша"""
        self.calculation_cache.clear()
        logger.info("✅ Кэш помощника очищен")


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()

backend.biorhythm_calculator.py

import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class BiorhythmCalculator:
    """
    Калькулятор биоритмов на основе даты рождения.
    Рассчитывает физический, эмоциональный и интеллектуальный циклы.
    """

    def __init__(self):
        # Периоды биоритмов в днях
        self.PHYSICAL_CYCLE = 23
        self.EMOTIONAL_CYCLE = 28
        self.INTELLECTUAL_CYCLE = 33
        self.INTUITIVE_CYCLE = 38  # Дополнительный цикл

    def calculate_biorhythms(self, birth_date: date, target_date: date) -> Dict:
        """
        Расчет биоритмов на заданную дату

        Args:
            birth_date: Дата рождения
            target_date: Дата для расчета

        Returns:
            Словарь с данными биоритмов
        """
        try:
            # Вычисляем количество прожитых дней
            days_lived = (target_date - birth_date).days

            if days_lived < 0:
                raise ValueError("Дата расчета не может быть раньше даты рождения")

            # Рассчитываем фазы биоритмов
            physical = self._calculate_cycle(days_lived, self.PHYSICAL_CYCLE)
            emotional = self._calculate_cycle(days_lived, self.EMOTIONAL_CYCLE)
            intellectual = self._calculate_cycle(days_lived, self.INTELLECTUAL_CYCLE)
            intuitive = self._calculate_cycle(days_lived, self.INTUITIVE_CYCLE)

            # Общий показатель энергии
            overall_energy = self._calculate_overall_energy(physical, emotional, intellectual, intuitive)

            biorhythm_data = {
                'calculation_date': target_date.isoformat(),
                'days_lived': days_lived,
                'cycles': {
                    'physical': physical,
                    'emotional': emotional,
                    'intellectual': intellectual,
                    'intuitive': intuitive
                },
                'overall_energy': overall_energy,
                'critical_days': self._find_critical_days(physical, emotional, intellectual, target_date),
                'peak_days': self._find_peak_days(physical, emotional, intellectual, target_date)
            }

            logger.info(f"✅ Биоритмы рассчитаны для {target_date}, прожито дней: {days_lived}")
            return biorhythm_data

        except Exception as e:
            logger.error(f"❌ Ошибка расчета биоритмов: {e}")
            raise

    def _calculate_cycle(self, days_lived: int, cycle_length: int) -> Dict:
        """
        Расчет одного цикла биоритма

        Args:
            days_lived: Количество прожитых дней
            cycle_length: Длина цикла в днях

        Returns:
            Данные цикла
        """
        # Текущая фаза в радианах (2π за полный цикл)
        phase = (2 * math.pi * days_lived) / cycle_length

        # Значение синусоиды (-1 до +1)
        value = math.sin(phase)

        # Процент от максимума (0% до 100%)
        percentage = ((value + 1) / 2) * 100

        # День в цикле (0 до cycle_length-1)
        day_in_cycle = days_lived % cycle_length

        return {
            'value': round(value, 4),
            'percentage': round(percentage, 2),
            'day_in_cycle': day_in_cycle,
            'phase': self._get_phase_description(value),
            'trend': self._get_trend(phase)
        }

    def _get_phase_description(self, value: float) -> str:
        """Описание фазы биоритма"""
        if value >= 0.7:
            return "пик энергии"
        elif value >= 0.3:
            return "высокая активность"
        elif value >= -0.3:
            return "нейтральная фаза"
        elif value >= -0.7:
            return "низкая активность"
        else:
            return "критическая точка"

    def _get_trend(self, phase: float) -> str:
        """Определение тренда (растет/падает)"""
        # Анализируем производную (cos(phase))
        derivative = math.cos(phase)

        if derivative > 0.1:
            return "растет"
        elif derivative < -0.1:
            return "падает"
        else:
            return "стабильно"

    def _calculate_overall_energy(self, physical: Dict, emotional: Dict, intellectual: Dict, intuitive: Dict) -> Dict:
        """Расчет общего уровня энергии"""
        # Взвешенная сумма всех циклов
        total_energy = (
                physical['value'] * 0.3 +  # Физический цикл - 30%
                emotional['value'] * 0.25 +  # Эмоциональный - 25%
                intellectual['value'] * 0.25 +  # Интеллектуальный - 25%
                intuitive['value'] * 0.2  # Интуитивный - 20%
        )

        # Нормализуем до 0-100%
        energy_percentage = ((total_energy + 1) / 2) * 100

        return {
            'value': round(total_energy, 4),
            'percentage': round(energy_percentage, 2)
        }

    def _find_critical_days(self, physical: Dict, emotional: Dict, intellectual: Dict, target_date: date) -> List[Dict]:
        """Определение критических дней"""
        critical_days = []

        # Проверяем текущий день
        if (abs(physical['value']) > 0.9 or
                abs(emotional['value']) > 0.9 or
                abs(intellectual['value']) > 0.9):
            critical_days.append({
                'date': target_date.isoformat(),
                'cycles': self._get_critical_cycles(physical, emotional, intellectual)
            })

        return critical_days

    def _find_peak_days(self, physical: Dict, emotional: Dict, intellectual: Dict, target_date: date) -> List[Dict]:
        """Определение пиковых дней"""
        peak_days = []

        # Проверяем текущий день
        if (physical['value'] > 0.8 or
                emotional['value'] > 0.8 or
                intellectual['value'] > 0.8):

            peak_cycles = []
            if physical['value'] > 0.8: peak_cycles.append('физический')
            if emotional['value'] > 0.8: peak_cycles.append('эмоциональный')
            if intellectual['value'] > 0.8: peak_cycles.append('интеллектуальный')

            peak_days.append({
                'date': target_date.isoformat(),
                'cycles': peak_cycles
            })

        return peak_days

    def _get_critical_cycles(self, physical: Dict, emotional: Dict, intellectual: Dict) -> List[str]:
        """Получение списка критических циклов"""
        critical = []
        if abs(physical['value']) > 0.9: critical.append('физический')
        if abs(emotional['value']) > 0.9: critical.append('эмоциональный')
        if abs(intellectual['value']) > 0.9: critical.append('интеллектуальный')
        return critical

    def calculate_weekly_forecast(self, birth_date: date, start_date: date, days: int = 7) -> List[Dict]:
        """Расчет прогноза биоритмов на несколько дней"""
        forecast = []

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            biorhythms = self.calculate_biorhythms(birth_date, current_date)

            forecast.append({
                'date': current_date.isoformat(),
                'overall_energy': biorhythms['overall_energy']['percentage'],
                'physical': biorhythms['cycles']['physical']['percentage'],
                'emotional': biorhythms['cycles']['emotional']['percentage'],
                'intellectual': biorhythms['cycles']['intellectual']['percentage'],
                'is_critical': len(biorhythms['critical_days']) > 0,
                'is_peak': len(biorhythms['peak_days']) > 0
            })

        return forecast

backend.biorhythm_services.py

from backend.database import async_session, Biorhythms, DailyCalculations
from backend.biorhythm_calculator import BiorhythmCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import date, datetime, timedelta
import logging
import asyncio
import json
import hashlib

logger = logging.getLogger(__name__)


async def calculate_and_save_biorhythms(telegram_id: int, target_date: date = None):
    """Расчет и сохранение биоритмов пользователя"""
    try:
        if target_date is None:
            target_date = date.today()

        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        # Рассчитываем биоритмы
        calculator = BiorhythmCalculator()
        biorhythm_data = calculator.calculate_biorhythms(
            user_profile['birth_date'],
            target_date
        )

        # Сохраняем в БД с атомарной операцией
        async with async_session() as session:
            try:
                # Сначала удаляем ВСЕ существующие записи для этой даты (на случай дублей)
                await session.execute(
                    Biorhythms.__table__.delete().where(
                        and_(
                            Biorhythms.telegram_id == telegram_id,
                            Biorhythms.calculation_date == target_date
                        )
                    )
                )

                # Создаем новую запись
                new_record = Biorhythms(
                    telegram_id=telegram_id,
                    biorhythm_data=biorhythm_data,
                    calculation_date=target_date
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы новые биоритмы для {telegram_id} на {target_date}")

                # Также сохраняем в daily_calculations для оптимизации
                await _save_to_daily_calculations(session, telegram_id, target_date, biorhythm_data)

                await session.commit()
                logger.info(f"💾 Биоритмы успешно сохранены для {telegram_id}")

            except Exception as db_error:
                await session.rollback()
                logger.error(f"❌ Ошибка БД при сохранении биоритмов {telegram_id}: {db_error}")
                raise

        return biorhythm_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете биоритмов для {telegram_id}: {e}")
        raise


async def _save_to_daily_calculations(session, telegram_id: int, target_date: date, biorhythm_data: dict):
    """Сохранение биоритмов в таблицу daily_calculations"""
    try:
        # Генерируем хэш данных
        data_str = json.dumps(biorhythm_data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Проверяем существующую запись
        result = await session.execute(
            select(DailyCalculations).where(
                and_(
                    DailyCalculations.telegram_id == telegram_id,
                    DailyCalculations.target_date == target_date
                )
            )
        )
        daily_calc = result.scalar_one_or_none()

        if daily_calc:
            # Обновляем существующую запись
            daily_calc.biorhythm_data = biorhythm_data
            daily_calc.data_hash = data_hash
            daily_calc.calculation_timestamp = datetime.now()
        else:
            # Создаем новую запись только с биоритмами
            daily_calc = DailyCalculations(
                telegram_id=telegram_id,
                target_date=target_date,
                biorhythm_data=biorhythm_data,
                astro_transits_data={},  # Пустые астрологические данные
                calculation_metadata={
                    'data_source': 'biorhythms_only',
                    'calculation_method': 'sine_wave_analysis'
                },
                data_hash=data_hash,
                calculation_timestamp=datetime.now()
            )
            session.add(daily_calc)

        logger.info(f"💾 Биоритмы сохранены в daily_calculations для {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в daily_calculations: {e}")
        raise


async def get_user_biorhythms(telegram_id: int, target_date: date = None):
    """Получение биоритмов пользователя с улучшенной обработкой ошибок"""
    try:
        if target_date is None:
            target_date = date.today()

        # Сначала пробуем получить из daily_calculations (оптимизированно)
        daily_calc = await _get_biorhythms_from_daily_calculations(telegram_id, target_date)
        if daily_calc:
            return daily_calc

        # Если нет в daily_calculations, ищем в основной таблице
        async with async_session() as session:
            result = await session.execute(
                select(Biorhythms).where(
                    and_(
                        Biorhythms.telegram_id == telegram_id,
                        Biorhythms.calculation_date == target_date
                    )
                )
            )
            biorhythms = result.scalar_one_or_none()

            if biorhythms:
                logger.info(f"✅ Найдены сохраненные биоритмы для {telegram_id} на {target_date}")
                return biorhythms.biorhythm_data

            # Если запись не найдена, рассчитываем заново
            logger.info(f"🔄 Биоритмы не найдены, рассчитываем заново для {telegram_id}")
            return await calculate_and_save_biorhythms(telegram_id, target_date)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении биоритмов {telegram_id}: {e}")
        return None


async def _get_biorhythms_from_daily_calculations(telegram_id: int, target_date: date):
    """Получение биоритмов из оптимизированной таблицы daily_calculations"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(DailyCalculations).where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
            )
            daily_calc = result.scalar_one_or_none()

            if daily_calc and daily_calc.biorhythm_data:
                logger.info(f"⚡ Биоритмы получены из daily_calculations для {telegram_id}")
                return daily_calc.biorhythm_data

        return None

    except Exception as e:
        logger.debug(f"⚠️ Ошибка получения из daily_calculations: {e}")
        return None


async def get_biorhythm_weekly_forecast(telegram_id: int, start_date: date = None, days: int = 7):
    """Получение недельного прогноза биоритмов с улучшенной обработкой"""
    try:
        if start_date is None:
            start_date = date.today()

        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        forecast = calculator.calculate_weekly_forecast(
            user_profile['birth_date'],
            start_date,
            days
        )

        logger.info(f"✅ Прогноз биоритмов рассчитан для {telegram_id} на {days} дней")
        return forecast

    except Exception as e:
        logger.error(f"❌ Ошибка при получении прогноза биоритмов {telegram_id}: {e}")
        return None


async def get_biorhythm_trend(telegram_id: int, period_days: int = 30):
    """Анализ тренда биоритмов за период"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        async with async_session() as session:
            result = await session.execute(
                select(Biorhythms).where(
                    and_(
                        Biorhythms.telegram_id == telegram_id,
                        Biorhythms.calculation_date >= start_date,
                        Biorhythms.calculation_date <= end_date
                    )
                ).order_by(Biorhythms.calculation_date)
            )
            biorhythms_records = result.scalars().all()

        if not biorhythms_records:
            return {"error": "Недостаточно данных для анализа тренда"}

        # Анализируем тренды
        trends = {
            'physical_trend': _calculate_trend(biorhythms_records, 'physical'),
            'emotional_trend': _calculate_trend(biorhythms_records, 'emotional'),
            'intellectual_trend': _calculate_trend(biorhythms_records, 'intellectual'),
            'overall_trend': _calculate_overall_trend(biorhythms_records),
            'analysis_period': f"{start_date.isoformat()} - {end_date.isoformat()}",
            'records_analyzed': len(biorhythms_records)
        }

        logger.info(f"📈 Проанализирован тренд биоритмов для {telegram_id}")
        return trends

    except Exception as e:
        logger.error(f"❌ Ошибка анализа тренда биоритмов {telegram_id}: {e}")
        return {"error": str(e)}


def _calculate_trend(biorhythms_records, cycle_type: str):
    """Расчет тренда для конкретного цикла"""
    try:
        percentages = []
        for record in biorhythms_records:
            cycle_data = record.biorhythm_data.get('cycles', {}).get(cycle_type, {})
            percentage = cycle_data.get('percentage', 0)
            percentages.append(percentage)

        if len(percentages) < 2:
            return "недостаточно данных"

        # Простой анализ тренда
        first_half = percentages[:len(percentages) // 2]
        second_half = percentages[len(percentages) // 2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_second > avg_first + 5:
            return "растущий"
        elif avg_second < avg_first - 5:
            return "падающий"
        else:
            return "стабильный"

    except Exception as e:
        logger.error(f"❌ Ошибка расчета тренда {cycle_type}: {e}")
        return "ошибка расчета"


def _calculate_overall_trend(biorhythms_records):
    """Расчет общего тренда энергии"""
    try:
        overall_energies = []
        for record in biorhythms_records:
            overall_energy = record.biorhythm_data.get('overall_energy', {})
            percentage = overall_energy.get('percentage', 0)
            overall_energies.append(percentage)

        if len(overall_energies) < 2:
            return "недостаточно данных"

        # Анализ общего тренда
        first_third = overall_energies[:len(overall_energies) // 3]
        last_third = overall_energies[-(len(overall_energies) // 3):]

        avg_first = sum(first_third) / len(first_third)
        avg_last = sum(last_third) / len(last_third)

        difference = avg_last - avg_first

        if difference > 10:
            return "сильный рост"
        elif difference > 5:
            return "умеренный рост"
        elif difference < -10:
            return "сильное падение"
        elif difference < -5:
            return "умеренное падение"
        else:
            return "стабильный"

    except Exception as e:
        logger.error(f"❌ Ошибка расчета общего тренда: {e}")
        return "ошибка расчета"


async def get_critical_days_forecast(telegram_id: int, days_ahead: int = 30):
    """Прогноз критических дней на указанный период"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        critical_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            critical_days_list = biorhythm_data.get('critical_days', [])
            if critical_days_list:
                critical_days.append({
                    'date': current_date.isoformat(),
                    'cycles': critical_days_list[0].get('cycles', []),
                    'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
                })

            current_date += timedelta(days=1)

        logger.info(f"⚠️  Найдено {len(critical_days)} критических дней для {telegram_id}")
        return critical_days

    except Exception as e:
        logger.error(f"❌ Ошибка прогноза критических дней {telegram_id}: {e}")
        return []


async def get_peak_days_forecast(telegram_id: int, days_ahead: int = 30):
    """Прогноз пиковых дней на указанный период"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        peak_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            peak_days_list = biorhythm_data.get('peak_days', [])
            if peak_days_list:
                peak_days.append({
                    'date': current_date.isoformat(),
                    'cycles': peak_days_list[0].get('cycles', []),
                    'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
                })

            current_date += timedelta(days=1)

        logger.info(f"📈 Найдено {len(peak_days)} пиковых дней для {telegram_id}")
        return peak_days

    except Exception as e:
        logger.error(f"❌ Ошибка прогноза пиковых дней {telegram_id}: {e}")
        return []


async def cleanup_duplicate_biorhythms():
    """Очистка дублирующихся записей биоритмов"""
    try:
        async with async_session() as session:
            # Находим дублирующиеся записи
            duplicate_query = """
            DELETE FROM biorhythms 
            WHERE ctid NOT IN (
                SELECT MIN(ctid) 
                FROM biorhythms 
                GROUP BY telegram_id, calculation_date
            )
            """

            result = await session.execute(duplicate_query)
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.warning(f"🗑️ Удалено {deleted_count} дублирующихся записей биоритмов")
            else:
                logger.info("✅ Дублирующихся записей биоритмов не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке дублирующихся биоритмов: {e}")
        return 0


async def get_biorhythm_statistics(telegram_id: int):
    """Получение статистики по биоритмам пользователя"""
    try:
        async with async_session() as session:
            # Количество записей биоритмов
            count_result = await session.execute(
                select(func.count(Biorhythms.telegram_id)).where(
                    Biorhythms.telegram_id == telegram_id
                )
            )
            total_records = count_result.scalar() or 0

            # Самая старая и новая запись
            dates_result = await session.execute(
                select(
                    func.min(Biorhythms.calculation_date),
                    func.max(Biorhythms.calculation_date)
                ).where(Biorhythms.telegram_id == telegram_id)
            )
            min_date, max_date = dates_result.first() or (None, None)

            # Средний уровень энергии
            energy_result = await session.execute(
                select(func.avg(Biorhythms.biorhythm_data['overall_energy']['percentage'].as_float())).where(
                    Biorhythms.telegram_id == telegram_id
                )
            )
            avg_energy = energy_result.scalar() or 0

            statistics = {
                'total_records': total_records,
                'first_calculation': min_date.isoformat() if min_date else None,
                'last_calculation': max_date.isoformat() if max_date else None,
                'calculation_range_days': (max_date - min_date).days if min_date and max_date else 0,
                'average_energy_level': round(avg_energy, 2),
                'calculation_frequency': _calculate_frequency(total_records, min_date, max_date)
            }

            logger.info(f"📊 Статистика биоритмов получена для {telegram_id}")
            return statistics

    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики биоритмов {telegram_id}: {e}")
        return {
            'total_records': 0,
            'first_calculation': None,
            'last_calculation': None,
            'calculation_range_days': 0,
            'average_energy_level': 0,
            'calculation_frequency': 'неизвестно'
        }


def _calculate_frequency(total_records, min_date, max_date):
    """Расчет частоты расчетов"""
    if not min_date or not max_date or total_records == 0:
        return "неизвестно"

    total_days = (max_date - min_date).days
    if total_days == 0:
        return "ежедневно"

    frequency = total_records / (total_days + 1)  # +1 чтобы избежать деления на 0

    if frequency >= 0.9:
        return "ежедневно"
    elif frequency >= 0.3:
        return "регулярно"
    elif frequency >= 0.1:
        return "периодически"
    else:
        return "редко"


async def cleanup_old_biorhythms(days_old: int = 30):
    """Очистка старых записей биоритмов"""
    try:
        cutoff_date = date.today() - timedelta(days=days_old)

        async with async_session() as session:
            result = await session.execute(
                Biorhythms.__table__.delete().where(
                    Biorhythms.calculation_date < cutoff_date
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} старых записей биоритмов (старше {days_old} дней)")
            else:
                logger.info("✅ Старых записей биоритмов для удаления не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке старых биоритмов: {e}")
        return 0


async def get_optimal_planning_days(telegram_id: int, days_ahead: int = 14):
    """Рекомендации оптимальных дней для планирования"""
    try:
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = BiorhythmCalculator()
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        optimal_days = []
        current_date = start_date

        while current_date <= end_date:
            biorhythm_data = calculator.calculate_biorhythms(
                user_profile['birth_date'],
                current_date
            )

            overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            cycles = biorhythm_data.get('cycles', {})
            physical = cycles.get('physical', {}).get('percentage', 0)
            emotional = cycles.get('emotional', {}).get('percentage', 0)
            intellectual = cycles.get('intellectual', {}).get('percentage', 0)

            # Оценка дня для планирования
            planning_score = _calculate_planning_score(overall_energy, physical, emotional, intellectual)

            if planning_score >= 80:
                day_type = "отличный"
                recommendation = "идеально для важных решений и планирования"
            elif planning_score >= 60:
                day_type = "хороший"
                recommendation = "подходит для стратегического планирования"
            elif planning_score >= 40:
                day_type = "удовлетворительный"
                recommendation = "можно планировать рутинные задачи"
            else:
                day_type = "неблагоприятный"
                recommendation = "лучше отложить важные решения"

            optimal_days.append({
                'date': current_date.isoformat(),
                'planning_score': planning_score,
                'day_type': day_type,
                'recommendation': recommendation,
                'energy_level': overall_energy,
                'physical': physical,
                'emotional': emotional,
                'intellectual': intellectual
            })

            current_date += timedelta(days=1)

        # Сортируем по убыванию оценки
        optimal_days.sort(key=lambda x: x['planning_score'], reverse=True)

        logger.info(f"🎯 Определены оптимальные дни для планирования {telegram_id}")
        return optimal_days

    except Exception as e:
        logger.error(f"❌ Ошибка определения оптимальных дней {telegram_id}: {e}")
        return []


def _calculate_planning_score(overall: float, physical: float, emotional: float, intellectual: float) -> float:
    """Расчет оценки дня для планирования"""
    # Веса для разных аспектов планирования
    weights = {
        'overall': 0.3,
        'intellectual': 0.4,  # Самый важный для планирования
        'emotional': 0.2,  # Важен для принятия решений
        'physical': 0.1  # Менее важен для планирования
    }

    score = (
            overall * weights['overall'] +
            intellectual * weights['intellectual'] +
            emotional * weights['emotional'] +
            physical * weights['physical']
    )

    return round(score, 2)


class BiorhythmAnalysisService:
    """Сервис для углубленного анализа биоритмов"""

    def __init__(self):
        self.calculator = BiorhythmCalculator()

    async def get_comprehensive_analysis(self, telegram_id: int, target_date: date = None):
        """Полный анализ биоритмов с рекомендациями"""
        try:
            if target_date is None:
                target_date = date.today()

            # Получаем текущие биоритмы
            biorhythm_data = await get_user_biorhythms(telegram_id, target_date)
            if not biorhythm_data:
                return {"error": "Не удалось получить данные биоритмов"}

            # Получаем прогнозы
            weekly_forecast = await get_biorhythm_weekly_forecast(telegram_id, target_date, 7)
            critical_days = await get_critical_days_forecast(telegram_id, 30)
            peak_days = await get_peak_days_forecast(telegram_id, 30)
            optimal_days = await get_optimal_planning_days(telegram_id, 14)

            # Анализ трендов
            trend_analysis = await get_biorhythm_trend(telegram_id, 30)

            # Формируем полный анализ
            analysis = {
                'current_data': biorhythm_data,
                'weekly_forecast': weekly_forecast,
                'critical_days_forecast': critical_days[:5],  # Только ближайшие 5
                'peak_days_forecast': peak_days[:5],
                'optimal_planning_days': optimal_days[:3],  # Только топ-3
                'trend_analysis': trend_analysis,
                'personalized_recommendations': self._generate_recommendations(biorhythm_data),
                'analysis_timestamp': datetime.now().isoformat()
            }

            logger.info(f"📊 Полный анализ биоритмов подготовлен для {telegram_id}")
            return analysis

        except Exception as e:
            logger.error(f"❌ Ошибка полного анализа биоритмов {telegram_id}: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, biorhythm_data: dict) -> list:
        """Генерация персонализированных рекомендаций"""
        recommendations = []

        overall_energy = biorhythm_data.get('overall_energy', {}).get('percentage', 0)
        cycles = biorhythm_data.get('cycles', {})
        physical = cycles.get('physical', {})
        emotional = cycles.get('emotional', {})
        intellectual = cycles.get('intellectual', {})

        # Рекомендации по общей энергии
        if overall_energy >= 80:
            recommendations.append("💪 Идеальный день для сложных задач и важных решений")
        elif overall_energy >= 60:
            recommendations.append("🚀 Хорошее время для активной работы и проектов")
        elif overall_energy <= 30:
            recommendations.append("🛌 Рекомендуется беречь силы, делать перерывы")

        # Рекомендации по физическому циклу
        physical_percentage = physical.get('percentage', 0)
        if physical_percentage >= 70:
            recommendations.append("🏃 Отличный день для спорта и физической активности")
        elif physical_percentage <= 30:
            recommendations.append("💤 Избегайте тяжелых физических нагрузок")

        # Рекомендации по эмоциональному циклу
        emotional_percentage = emotional.get('percentage', 0)
        if emotional_percentage >= 70:
            recommendations.append("😊 Благоприятное время для общения и встреч")
        elif emotional_percentage <= 30:
            recommendations.append("🧘 Контролируйте эмоции, избегайте конфликтов")

        # Рекомендации по интеллектуальному циклу
        intellectual_percentage = intellectual.get('percentage', 0)
        if intellectual_percentage >= 70:
            recommendations.append("📚 Идеально для обучения, анализа и планирования")
        elif intellectual_percentage <= 30:
            recommendations.append("📝 Отложите сложные интеллектуальные задачи")

        # Критические дни
        critical_days = biorhythm_data.get('critical_days', [])
        if critical_days:
            recommendations.append("⚠️ Критический день - будьте осторожны в принятии решений")

        return recommendations

    async def get_energy_optimization_plan(self, telegram_id: int, period_days: int = 7):
        """План оптимизации энергии на период"""
        try:
            forecast = await get_biorhythm_weekly_forecast(telegram_id, date.today(), period_days)
            if not forecast:
                return {"error": "Не удалось получить прогноз"}

            optimization_plan = []

            for day_data in forecast:
                date_str = day_data['date']
                energy_level = day_data['overall_energy']
                physical = day_data['physical']
                emotional = day_data['emotional']
                intellectual = day_data['intellectual']

                # Определяем тип дня и рекомендации
                if energy_level >= 75:
                    day_type = "энергичный"
                    focus = "сложные задачи, новые проекты"
                    activities = ["стратегическое планирование", "принятие решений", "переговоры"]
                elif energy_level >= 50:
                    day_type = "стабильный"
                    focus = "текущие задачи, рутинная работа"
                    activities = ["выполнение планов", "коммуникация", "обучение"]
                else:
                    day_type = "восстановительный"
                    focus = "отдых, подготовка, анализ"
                    activities = ["планирование", "анализ результатов", "восстановление сил"]

                optimization_plan.append({
                    'date': date_str,
                    'energy_level': energy_level,
                    'day_type': day_type,
                    'focus_area': focus,
                    'recommended_activities': activities,
                    'physical_energy': physical,
                    'emotional_energy': emotional,
                    'intellectual_energy': intellectual
                })

            return {
                'optimization_plan': optimization_plan,
                'period': f"{period_days} дней",
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка создания плана оптимизации для {telegram_id}: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
biorhythm_service = BiorhythmAnalysisService()

backend.calculation_services.py

from backend.database import async_session, DailyCalculations, CalculationCache, UserAstroProfile
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.chart_services import get_user_natal_chart
from backend.matrix_services import get_user_matrix
from backend.predictions import AstroPredictor
from sqlalchemy.future import select
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
import logging
import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Унифицированный сервис для управления всеми типами расчетов
    Объединяет биоритмы, астрологию и психоматрицу
    """

    def __init__(self):
        self.cache_ttl_hours = 24  # Время жизни кэша в часах

    async def get_full_calculation_package(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """
        Получение полного пакета расчетных данных
        Основной метод для внешнего API
        """
        try:
            # Проверяем кэш
            cached_data = await self._get_cached_calculation(telegram_id, target_date, 'full_package')
            if cached_data:
                logger.info(f"⚡ Использованы кэшированные данные для {telegram_id}")
                return cached_data

            # Получаем все типы расчетов
            calculations = await asyncio.gather(
                self._get_biorhythm_calculations(telegram_id, target_date),
                self._get_astrology_calculations(telegram_id, target_date),
                self._get_matrix_calculations(telegram_id),
                self._get_user_context(telegram_id),
                return_exceptions=True
            )

            # Обрабатываем результаты
            biorhythm_data = calculations[0] if not isinstance(calculations[0], Exception) else {}
            astrology_data = calculations[1] if not isinstance(calculations[1], Exception) else {}
            matrix_data = calculations[2] if not isinstance(calculations[2], Exception) else {}
            user_context = calculations[3] if not isinstance(calculations[3], Exception) else {}

            # Формируем полный пакет
            calculation_package = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': {
                    'biorhythms': biorhythm_data,
                    'astrology': astrology_data,
                    'psychomatrix': matrix_data
                },
                'user_context': user_context,
                'metadata': {
                    'calculation_timestamp': datetime.now().isoformat(),
                    'data_version': '2.0',
                    'sources_used': self._get_used_sources(biorhythm_data, astrology_data, matrix_data)
                }
            }

            # Сохраняем в кэш
            await self._save_to_cache(telegram_id, target_date, 'full_package', calculation_package)

            logger.info(f"✅ Полный пакет расчетов подготовлен для {telegram_id}")
            return calculation_package

        except Exception as e:
            logger.error(f"❌ Ошибка формирования пакета расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'timestamp': datetime.now().isoformat()
            }

    async def _get_biorhythm_calculations(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Получение расчетов биоритмов"""
        try:
            biorhythm_data = await get_user_biorhythms(telegram_id, target_date)

            if not biorhythm_data:
                # Если данных нет, рассчитываем заново
                biorhythm_data = await calculate_and_save_biorhythms(telegram_id, target_date)

            return {
                'energy_levels': {
                    'overall': biorhythm_data.get('overall_energy', {}).get('percentage', 0),
                    'physical': biorhythm_data.get('cycles', {}).get('physical', {}).get('percentage', 0),
                    'emotional': biorhythm_data.get('cycles', {}).get('emotional', {}).get('percentage', 0),
                    'intellectual': biorhythm_data.get('cycles', {}).get('intellectual', {}).get('percentage', 0)
                },
                'phases': {
                    'physical': biorhythm_data.get('cycles', {}).get('physical', {}).get('phase', 'неизвестно'),
                    'emotional': biorhythm_data.get('cycles', {}).get('emotional', {}).get('phase', 'неизвестно'),
                    'intellectual': biorhythm_data.get('cycles', {}).get('intellectual', {}).get('phase', 'неизвестно')
                },
                'special_days': {
                    'critical_days': len(biorhythm_data.get('critical_days', [])),
                    'peak_days': len(biorhythm_data.get('peak_days', []))
                },
                'days_lived': biorhythm_data.get('days_lived', 0)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения биоритмов для {telegram_id}: {e}")
            return {'error': str(e)}

    async def _get_astrology_calculations(self, telegram_id: int, target_date: date) -> Dict[str, Any]:
        """Получение астрологических расчетов"""
        try:
            # Получаем натальную карту
            natal_data = await get_user_natal_chart(telegram_id)
            if not natal_data:
                return {'error': 'Натальная карта не найдена'}

            # Рассчитываем транзиты
            predictor = AstroPredictor(natal_data)
            astro_prediction = predictor.generate_prediction(target_date)

            return {
                'transits': {
                    'total_planets': len(astro_prediction.get('transits', {})),
                    'retrograde_planets': astro_prediction.get('retrograde_planets', [])
                },
                'aspects': {
                    'total_count': astro_prediction.get('aspects_count', 0),
                    'strong_count': astro_prediction.get('strong_aspects_count', 0),
                    'key_aspects': astro_prediction.get('aspects', [])[:3]  # Топ-3 аспекта
                },
                'natal_summary': {
                    'dominant_element': self._get_dominant_element(natal_data),
                    'planets_count': len(natal_data.get('planets', {})),
                    'ascendant': natal_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
                }
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения астрологических данных для {telegram_id}: {e}")
            return {'error': str(e)}

    def _get_dominant_element(self, natal_data: dict) -> str:
        """Определение доминирующего элемента"""
        try:
            element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    async def _get_matrix_calculations(self, telegram_id: int) -> Dict[str, Any]:
        """Получение расчетов психоматрицы"""
        try:
            matrix_data = await get_user_matrix(telegram_id)
            if not matrix_data:
                return {'error': 'Психоматрица не найдена'}

            basic_numbers = matrix_data.get('basic_numbers', {})
            pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

            return {
                'life_path': basic_numbers.get('first'),
                'destiny_number': basic_numbers.get('second'),
                'personality_number': basic_numbers.get('third'),
                'matrix_analysis': {
                    'complexity': self._calculate_matrix_complexity(pythagoras_matrix),
                    'strong_digits': [digit for digit, count in pythagoras_matrix.items() if count >= 2],
                    'missing_digits': [digit for digit in map(str, range(1, 10)) if
                                       pythagoras_matrix.get(digit, 0) == 0]
                },
                'energy_centers': self._analyze_energy_centers(pythagoras_matrix)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения психоматрицы для {telegram_id}: {e}")
            return {'error': str(e)}

    def _calculate_matrix_complexity(self, matrix: dict) -> str:
        """Оценка сложности психоматрицы"""
        total_digits = sum(matrix.values())
        if total_digits >= 15:
            return "сложная"
        elif total_digits >= 10:
            return "средняя"
        else:
            return "простая"

    def _analyze_energy_centers(self, matrix: dict) -> Dict[str, int]:
        """Анализ энергетических центров"""
        return {
            'practical': sum(matrix.get(str(digit), 0) for digit in [4, 5, 6]),
            'spiritual': sum(matrix.get(str(digit), 0) for digit in [7, 8, 9]),
            'will': sum(matrix.get(str(digit), 0) for digit in [1, 2, 3])
        }

    async def _get_user_context(self, telegram_id: int) -> Dict[str, Any]:
        """Получение контекста пользователя"""
        try:
            from backend.user_services import get_user_profile

            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {}

            # Рассчитываем возраст
            age = self._calculate_age(user_profile.get('birth_date'))

            return {
                'demographics': {
                    'age': age,
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'city': user_profile.get('current_city', 'не указан'),
                    'gender': user_profile.get('gender', 'не указан')
                },
                'experience_level': self._estimate_experience_level(age, user_profile.get('profession')),
                'request_count': user_profile.get('request_count', 0)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения контекста пользователя {telegram_id}: {e}")
            return {}

    def _calculate_age(self, birth_date: date) -> int:
        """Расчет возраста"""
        if not birth_date:
            return 0
        today = date.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age

    def _estimate_experience_level(self, age: int, profession: str) -> str:
        """Оценка уровня опыта"""
        if not profession or profession.lower() in ['не указана', 'нет', '']:
            return "неизвестно"

        if age < 22:
            return "начинающий"
        elif age < 30:
            return "опытный"
        elif age < 45:
            return "профессионал"
        else:
            return "эксперт"

    def _get_used_sources(self, biorhythms: dict, astrology: dict, matrix: dict) -> List[str]:
        """Определение использованных источников данных"""
        sources = []

        if biorhythms and not biorhythms.get('error'):
            sources.append('biorhythms')
        if astrology and not astrology.get('error'):
            sources.append('astrology')
        if matrix and not matrix.get('error'):
            sources.append('psychomatrix')

        return sources

    async def _get_cached_calculation(self, telegram_id: int, target_date: date, data_type: str) -> Optional[
        Dict[str, Any]]:
        """Получение данных из кэша"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(CalculationCache).where(
                        and_(
                            CalculationCache.telegram_id == telegram_id,
                            CalculationCache.target_date == target_date,
                            CalculationCache.data_type == data_type,
                            CalculationCache.expires_at > datetime.now()
                        )
                    )
                )
                cached = result.scalar_one_or_none()

                if cached:
                    return cached.calculation_data
                return None

        except Exception as e:
            logger.debug(f"⚠️ Ошибка получения из кэша: {e}")
            return None

    async def _save_to_cache(self, telegram_id: int, target_date: date, data_type: str, data: Dict[str, Any]):
        """Сохранение данных в кэш"""
        try:
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)

            async with async_session() as session:
                # Удаляем старую запись
                await session.execute(
                    CalculationCache.__table__.delete().where(
                        and_(
                            CalculationCache.telegram_id == telegram_id,
                            CalculationCache.target_date == target_date,
                            CalculationCache.data_type == data_type
                        )
                    )
                )

                # Создаем новую запись
                cache_entry = CalculationCache(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    data_type=data_type,
                    calculation_data=data,
                    expires_at=expires_at
                )
                session.add(cache_entry)

                await session.commit()
                logger.debug(f"💾 Данные сохранены в кэш для {telegram_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кэш: {e}")
            # Не прерываем выполнение при ошибке кэширования


class CalculationOptimizer:
    """
    Сервис для оптимизации и управления расчетами
    """

    def __init__(self):
        self.calculation_service = CalculationService()

    async def get_optimized_calculations(self, telegram_id: int, target_date: date,
                                         include_types: List[str] = None) -> Dict[str, Any]:
        """
        Оптимизированное получение расчетов с фильтрацией по типам
        """
        if include_types is None:
            include_types = ['biorhythms', 'astrology', 'psychomatrix']

        try:
            # Получаем полный пакет
            full_package = await self.calculation_service.get_full_calculation_package(telegram_id, target_date)

            if not full_package.get('success'):
                return full_package

            # Фильтруем данные по запрошенным типам
            filtered_calculations = {}
            for calc_type in include_types:
                if calc_type in full_package['calculations']:
                    filtered_calculations[calc_type] = full_package['calculations'][calc_type]

            # Формируем оптимизированный ответ
            optimized_response = {
                'success': True,
                'user_id': telegram_id,
                'target_date': target_date.isoformat(),
                'calculations': filtered_calculations,
                'user_context': full_package.get('user_context', {}),
                'included_types': include_types,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"🎯 Оптимизированные расчеты подготовлены для {telegram_id}")
            return optimized_response

        except Exception as e:
            logger.error(f"❌ Ошибка оптимизированных расчетов для {telegram_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_id': telegram_id,
                'target_date': target_date.isoformat()
            }

    async def get_calculation_health_check(self, telegram_id: int) -> Dict[str, Any]:
        """
        Проверка здоровья расчетных данных пользователя
        """
        try:
            checks = await asyncio.gather(
                self._check_biorhythm_health(telegram_id),
                self._check_astrology_health(telegram_id),
                self._check_matrix_health(telegram_id),
                self._check_user_data_health(telegram_id)
            )

            health_status = {
                'user_id': telegram_id,
                'check_timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'detailed_checks': {
                    'biorhythms': checks[0],
                    'astrology': checks[1],
                    'psychomatrix': checks[2],
                    'user_data': checks[3]
                }
            }

            # Определяем общий статус
            all_healthy = all(check.get('status') == 'healthy' for check in checks)
            health_status['overall_status'] = 'healthy' if all_healthy else 'degraded'

            return health_status

        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья расчетов для {telegram_id}: {e}")
            return {
                'user_id': telegram_id,
                'overall_status': 'error',
                'error': str(e)
            }

    async def _check_biorhythm_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья данных биоритмов"""
        try:
            # Проверяем наличие свежих данных
            today = date.today()
            biorhythm_data = await get_user_biorhythms(telegram_id, today)

            if not biorhythm_data:
                return {
                    'status': 'missing',
                    'message': 'Отсутствуют данные биоритмов на сегодня',
                    'recommendation': 'Выполнить расчет биоритмов'
                }

            # Проверяем свежесть данных
            async with async_session() as session:
                result = await session.execute(
                    select(DailyCalculations.calculation_timestamp).where(
                        and_(
                            DailyCalculations.telegram_id == telegram_id,
                            DailyCalculations.target_date == today
                        )
                    )
                )
                timestamp = result.scalar_one_or_none()

            if timestamp:
                data_age = (datetime.now() - timestamp).total_seconds() / 3600  # в часах
                if data_age > 24:
                    return {
                        'status': 'stale',
                        'message': f'Данные биоритмов устарели ({data_age:.1f} часов)',
                        'recommendation': 'Обновить расчет биоритмов'
                    }

            return {
                'status': 'healthy',
                'message': 'Данные биоритмов актуальны',
                'energy_level': biorhythm_data.get('overall_energy', {}).get('percentage', 0)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_astrology_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья астрологических данных"""
        try:
            natal_data = await get_user_natal_chart(telegram_id)

            if not natal_data:
                return {
                    'status': 'missing',
                    'message': 'Отсутствует натальная карта',
                    'recommendation': 'Создать натальную карту'
                }

            # Проверяем полноту данных
            planets = natal_data.get('planets', {})
            essential_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
            missing_planets = [p for p in essential_planets if p not in planets]

            if missing_planets:
                return {
                    'status': 'incomplete',
                    'message': f'Отсутствуют планеты: {", ".join(missing_planets)}',
                    'recommendation': 'Пересчитать натальную карту'
                }

            return {
                'status': 'healthy',
                'message': 'Натальная карта в порядке',
                'planets_count': len(planets)
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_matrix_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья данных психоматрицы"""
        try:
            matrix_data = await get_user_matrix(telegram_id)

            if not matrix_data:
                return {
                    'status': 'missing',
                    'message': 'Отсутствует психоматрица',
                    'recommendation': 'Рассчитать психоматрицу'
                }

            # Проверяем базовые числа
            basic_numbers = matrix_data.get('basic_numbers', {})
            if not all(key in basic_numbers for key in ['first', 'second', 'third', 'fourth']):
                return {
                    'status': 'incomplete',
                    'message': 'Неполные базовые числа',
                    'recommendation': 'Пересчитать психоматрицу'
                }

            return {
                'status': 'healthy',
                'message': 'Психоматрица в порядке',
                'life_path': basic_numbers.get('first')
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def _check_user_data_health(self, telegram_id: int) -> Dict[str, Any]:
        """Проверка здоровья пользовательских данных"""
        try:
            from backend.user_services import get_user_profile

            user_profile = await get_user_profile(telegram_id)

            if not user_profile:
                return {
                    'status': 'missing',
                    'message': 'Отсутствуют основные данные пользователя',
                    'recommendation': 'Заполнить профиль'
                }

            # Проверяем обязательные поля
            missing_fields = []
            if not user_profile.get('birth_date'):
                missing_fields.append('дата рождения')
            if not user_profile.get('birth_time'):
                missing_fields.append('время рождения')
            if not user_profile.get('birth_city'):
                missing_fields.append('город рождения')

            if missing_fields:
                return {
                    'status': 'incomplete',
                    'message': f'Отсутствуют поля: {", ".join(missing_fields)}',
                    'recommendation': 'Дополнить профиль'
                }

            return {
                'status': 'healthy',
                'message': 'Данные пользователя полные',
                'profession': user_profile.get('profession', 'не указана')
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка проверки: {str(e)}'
            }

    async def cleanup_old_calculations(self, days_old: int = 30) -> Dict[str, int]:
        """
        Очистка устаревших расчетов и кэша
        """
        try:
            cutoff_date = date.today() - timedelta(days=days_old)

            async with async_session() as session:
                # Очищаем устаревшие daily calculations
                daily_result = await session.execute(
                    DailyCalculations.__table__.delete().where(
                        DailyCalculations.target_date < cutoff_date
                    )
                )
                daily_deleted = daily_result.rowcount

                # Очищаем просроченный кэш
                cache_result = await session.execute(
                    CalculationCache.__table__.delete().where(
                        CalculationCache.expires_at < datetime.now()
                    )
                )
                cache_deleted = cache_result.rowcount

                await session.commit()

            logger.info(f"🧹 Очистка расчетов: {daily_deleted} daily calculations, {cache_deleted} cache entries")

            return {
                'daily_calculations_deleted': daily_deleted,
                'cache_entries_deleted': cache_deleted,
                'total_deleted': daily_deleted + cache_deleted
            }

        except Exception as e:
            logger.error(f"❌ Ошибка очистки расчетов: {e}")
            return {
                'daily_calculations_deleted': 0,
                'cache_entries_deleted': 0,
                'total_deleted': 0,
                'error': str(e)
            }


# Глобальные экземпляры сервисов
calculation_service = CalculationService()
calculation_optimizer = CalculationOptimizer()

backend.chart_services.py

from backend.database import async_session, UserAstroProfile
from backend.natal_chart import MLNatalChartCalculator
from sqlalchemy.future import select
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)


async def create_and_save_natal_chart(telegram_id: int, city: str, birth_datetime, timezone: str):
    """Создание и сохранение натальной карты в объединенный астропрофиль"""
    try:
        calculator = MLNatalChartCalculator()
        natal_data = calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

        logger.info(f"🔮 Создание натальной карты для пользователя {telegram_id}")

        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем существующий астропрофиль
                astro_profile.natal_chart_data = natal_data
                # Психоматрица остается без изменений
                logger.info(f"📝 Обновлена натальная карта в астропрофиле для {telegram_id}")
            else:
                # Создаем новый астропрофиль с пустой психоматрицей
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data=natal_data,
                    psyho_matrix_data={},  # Пустая психоматрица, будет заполнена позже
                    dominant_energy=None,
                    personality_traits=None
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль с натальной картой для {telegram_id}")

            await session.commit()
            logger.info(f"💾 Натальная карта успешно сохранена для {telegram_id}")
            return astro_profile

    except Exception as e:
        logger.error(f"❌ Ошибка при создании натальной карты для {telegram_id}: {e}")
        raise


async def get_user_natal_chart(telegram_id: int):
    """Получение натальной карты пользователя из астропрофиля"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile and astro_profile.natal_chart_data:
                return astro_profile.natal_chart_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении натальной карты {telegram_id}: {e}")
        return None


async def update_user_astro_profile(telegram_id: int, psyho_matrix_data: dict = None,
                                    dominant_energy: str = None, personality_traits: list = None):
    """Обновление астропрофиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем только переданные поля
                if psyho_matrix_data is not None:
                    astro_profile.psyho_matrix_data = psyho_matrix_data
                if dominant_energy is not None:
                    astro_profile.dominant_energy = dominant_energy
                if personality_traits is not None:
                    astro_profile.personality_traits = personality_traits

                logger.info(f"📝 Обновлен астропрофиль для {telegram_id}")
            else:
                # Создаем новый астропрофиль только с психоматрицей
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data={},  # Пустая натальная карта
                    psyho_matrix_data=psyho_matrix_data or {},
                    dominant_energy=dominant_energy,
                    personality_traits=personality_traits
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль для {telegram_id}")

            await session.commit()
            return astro_profile

    except Exception as e:
        logger.error(f"❌ Ошибка обновления астропрофиля для {telegram_id}: {e}")
        raise


async def get_user_astro_profile(telegram_id: int):
    """Получение полного астропрофиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                return {
                    'telegram_id': astro_profile.telegram_id,
                    'natal_chart': astro_profile.natal_chart_data,
                    'psyho_matrix': astro_profile.psyho_matrix_data,
                    'dominant_energy': astro_profile.dominant_energy,
                    'personality_traits': astro_profile.personality_traits,
                    'created_at': astro_profile.created_at.isoformat() if astro_profile.created_at else None,
                    'updated_at': astro_profile.updated_at.isoformat() if astro_profile.updated_at else None
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении астропрофиля {telegram_id}: {e}")
        return None


async def validate_natal_chart_data(telegram_id: int) -> bool:
    """Проверка корректности данных натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return False

        # Проверяем обязательные поля
        required_fields = ['metadata', 'planets', 'houses', 'angles']
        for field in required_fields:
            if field not in natal_data:
                logger.warning(f"⚠️ Отсутствует поле {field} в натальной карте {telegram_id}")
                return False

        # Проверяем наличие основных планет
        planets = natal_data.get('planets', {})
        essential_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars']
        for planet in essential_planets:
            if planet not in planets:
                logger.warning(f"⚠️ Отсутствует планета {planet} в натальной карте {telegram_id}")
                return False

        logger.info(f"✅ Данные натальной карты валидны для {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации натальной карты для {telegram_id}: {e}")
        return False


async def get_natal_chart_summary(telegram_id: int) -> dict:
    """Получение краткой сводки натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        planets = natal_data.get('planets', {})
        houses = natal_data.get('houses', {})
        angles = natal_data.get('angles', {})

        # Анализ доминирующих знаков
        sign_distribution = {}
        for planet_data in planets.values():
            sign = planet_data.get('sign', 'Unknown')
            sign_distribution[sign] = sign_distribution.get(sign, 0) + 1

        dominant_sign = max(sign_distribution.items(), key=lambda x: x[1])[0] if sign_distribution else "Unknown"

        # Анализ аспектов
        aspects = natal_data.get('aspects', [])
        aspect_patterns = {
            'conjunctions': len([a for a in aspects if a.get('aspect') == 'conjunction']),
            'squares': len([a for a in aspects if a.get('aspect') == 'square']),
            'trines': len([a for a in aspects if a.get('aspect') == 'trine']),
            'oppositions': len([a for a in aspects if a.get('aspect') == 'opposition'])
        }

        summary = {
            'basic_info': {
                'planets_count': len(planets),
                'houses_count': len(houses),
                'aspects_count': len(aspects),
                'dominant_sign': dominant_sign
            },
            'key_placements': {
                'sun_sign': planets.get('Sun', {}).get('sign', 'Unknown'),
                'moon_sign': planets.get('Moon', {}).get('sign', 'Unknown'),
                'ascendant': angles.get('ascendant', {}).get('sign', 'Unknown'),
                'midheaven': angles.get('midheaven', {}).get('sign', 'Unknown')
            },
            'aspect_analysis': aspect_patterns,
            'element_balance': natal_data.get('ml_features', {}).get('element_balance', {})
        }

        return summary

    except Exception as e:
        logger.error(f"❌ Ошибка получения сводки натальной карты для {telegram_id}: {e}")
        return {}


async def calculate_dominant_energy(telegram_id: int) -> str:
    """Расчет доминирующей энергии на основе натальной карты"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return "неизвестно"

        planets = natal_data.get('planets', {})
        element_balance = natal_data.get('ml_features', {}).get('element_balance', {})

        # Простой анализ на основе элементов
        if not element_balance:
            return "сбалансированная"

        max_element = max(element_balance.items(), key=lambda x: x[1])
        element_energy_map = {
            'fire': 'активная',
            'air': 'интеллектуальная',
            'water': 'эмоциональная',
            'earth': 'практическая'
        }

        dominant_energy = element_energy_map.get(max_element[0], "сбалансированная")

        # Сохраняем результат в астропрофиль
        await update_user_astro_profile(telegram_id, dominant_energy=dominant_energy)

        logger.info(f"✅ Рассчитана доминирующая энергия для {telegram_id}: {dominant_energy}")
        return dominant_energy

    except Exception as e:
        logger.error(f"❌ Ошибка расчета доминирующей энергии для {telegram_id}: {e}")
        return "неизвестно"


async def get_planet_positions(telegram_id: int, planet_names: list = None) -> dict:
    """Получение позиций конкретных планет"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        planets = natal_data.get('planets', {})

        if planet_names:
            # Фильтруем по запрошенным планетам
            positions = {name: planets.get(name) for name in planet_names if name in planets}
        else:
            # Возвращаем все планеты
            positions = planets

        return positions

    except Exception as e:
        logger.error(f"❌ Ошибка получения позиций планет для {telegram_id}: {e}")
        return {}


async def get_house_placements(telegram_id: int) -> dict:
    """Получение размещения планет по домам"""
    try:
        natal_data = await get_user_natal_chart(telegram_id)

        if not natal_data:
            return {}

        placements = natal_data.get('placements', {})
        houses = natal_data.get('houses', {})

        # Группируем планеты по домам
        house_planets = {}
        for planet, house_num in placements.items():
            house_key = f"house_{house_num}"
            if house_key not in house_planets:
                house_planets[house_key] = []
            house_planets[house_key].append(planet)

        result = {
            'house_planets': house_planets,
            'houses_info': houses
        }

        return result

    except Exception as e:
        logger.error(f"❌ Ошибка получения размещения по домам для {telegram_id}: {e}")
        return {}


async def cleanup_orphaned_astro_profiles():
    """Очистка астропрофилей без пользователей"""
    try:
        async with async_session() as session:
            # Находим астропрофили, у которых нет соответствующего пользователя
            orphan_query = """
            DELETE FROM user_astro_profile 
            WHERE telegram_id NOT IN (SELECT telegram_id FROM users)
            """

            result = await session.execute(orphan_query)
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.warning(f"🗑️ Удалено {deleted_count} orphaned астропрофилей")
            else:
                logger.info("✅ Orphaned астропрофилей не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка очистки orphaned астропрофилей: {e}")
        return 0


class NatalChartService:
    """Сервис для работы с натальными картами"""

    def __init__(self):
        self.calculator = MLNatalChartCalculator()

    async def create_complete_astro_profile(self, telegram_id: int, city: str,
                                            birth_datetime, timezone: str, psyho_matrix_data: dict = None):
        """Создание полного астропрофиля (натальная карта + психоматрица)"""
        try:
            # Создаем натальную карту
            natal_data = self.calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

            # Рассчитываем доминирующую энергию
            element_balance = natal_data.get('ml_features', {}).get('element_balance', {})
            dominant_energy = self._calculate_dominant_energy_from_elements(element_balance)

            # Создаем/обновляем астропрофиль
            async with async_session() as session:
                result = await session.execute(
                    select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
                )
                astro_profile = result.scalar_one_or_none()

                if astro_profile:
                    # Обновляем существующий
                    astro_profile.natal_chart_data = natal_data
                    astro_profile.psyho_matrix_data = psyho_matrix_data or astro_profile.psyho_matrix_data
                    astro_profile.dominant_energy = dominant_energy
                else:
                    # Создаем новый
                    astro_profile = UserAstroProfile(
                        telegram_id=telegram_id,
                        natal_chart_data=natal_data,
                        psyho_matrix_data=psyho_matrix_data or {},
                        dominant_energy=dominant_energy,
                        personality_traits=None
                    )
                    session.add(astro_profile)

                await session.commit()
                logger.info(f"✅ Полный астропрофиль создан для {telegram_id}")
                return astro_profile

        except Exception as e:
            logger.error(f"❌ Ошибка создания полного астропрофиля для {telegram_id}: {e}")
            raise

    def _calculate_dominant_energy_from_elements(self, element_balance: dict) -> str:
        """Расчет доминирующей энергии на основе баланса элементов"""
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

    async def get_chart_complexity(self, telegram_id: int) -> str:
        """Оценка сложности натальной карты"""
        try:
            natal_data = await get_user_natal_chart(telegram_id)

            if not natal_data:
                return "неизвестно"

            aspects = natal_data.get('aspects', [])
            strong_aspects = len([a for a in aspects if a.get('strength', 0) > 0.7])

            if strong_aspects > 8:
                return "очень сложная"
            elif strong_aspects > 5:
                return "сложная"
            elif strong_aspects > 2:
                return "средняя"
            else:
                return "простая"

        except Exception as e:
            logger.error(f"❌ Ошибка оценки сложности карты для {telegram_id}: {e}")
            return "неизвестно"


# Глобальный экземпляр сервиса
natal_chart_service = NatalChartService()

backend.database.py

import os
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, String, Date, Time, Text, ForeignKey, Integer
from sqlalchemy import select, and_
from sqlalchemy.sql import func
from sqlalchemy import Index
import logging

logger = logging.getLogger(__name__)

# Настройка подключения к базе данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://astra_user:astra_password_2024@localhost:5435/astra_db"
)

logger.info(f"🔗 Подключаемся к БД Astra: postgresql+asyncpg://astra_user:******@localhost:5435/astra_db")

# Создание асинхронного движка
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Отключаем подробное логирование в продакшене
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo_pool=False
)

# Создание асинхронной сессии
async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Базовый класс для моделей
Base = declarative_base()


class User(Base):
    """
    Основная таблица пользователей проекта Astra
    """
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(Time, nullable=False)
    birth_city = Column(String(100), nullable=False)
    profession = Column(String(100), nullable=True)
    job_position = Column(String(100), nullable=True)
    current_city = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)  # 'male', 'female', None
    request_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, birth_date={self.birth_date})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'birth_city': self.birth_city,
            'profession': self.profession,
            'job_position': self.job_position,
            'current_city': self.current_city,
            'gender': self.gender,
            'request_count': self.request_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserAstroProfile(Base):
    """
    Статические астрологические данные пользователя
    Объединяет натальную карту и психоматрицу
    """
    __tablename__ = 'user_astro_profile'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    natal_chart_data = Column(JSON, nullable=False)
    psyho_matrix_data = Column(JSON, nullable=False)
    dominant_energy = Column(String(50), nullable=True)
    personality_traits = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserAstroProfile(telegram_id={self.telegram_id})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'natal_chart_summary': {
                'planets_count': len(self.natal_chart_data.get('planets', {})),
                'dominant_element': self._get_dominant_element(),
                'ascendant': self.natal_chart_data.get('angles', {}).get('ascendant', {}).get('sign', 'неизвестно')
            },
            'psyho_matrix_summary': {
                'life_path_number': self.psyho_matrix_data.get('basic_numbers', {}).get('first'),
                'matrix_complexity': self._calculate_matrix_complexity()
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def _get_dominant_element(self):
        """Определение доминирующего элемента"""
        try:
            element_balance = self.natal_chart_data.get('ml_features', {}).get('element_balance', {})
            if element_balance:
                return max(element_balance.items(), key=lambda x: x[1])[0]
            return 'неизвестно'
        except Exception:
            return 'неизвестно'

    def _calculate_matrix_complexity(self):
        """Оценка сложности психоматрицы"""
        try:
            matrix_data = self.psyho_matrix_data.get('pythagoras_matrix', {})
            total_digits = sum(matrix_data.values())
            if total_digits >= 15:
                return "сложная"
            elif total_digits >= 10:
                return "средняя"
            else:
                return "простая"
        except Exception:
            return "неизвестно"


class DailyCalculations(Base):
    """
    Ежедневные расчеты для конкретных дат
    Оптимизированная таблица для частых запросов
    """
    __tablename__ = 'daily_calculations'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    biorhythm_data = Column(JSON, nullable=False)
    astro_transits_data = Column(JSON, nullable=False)
    calculation_metadata = Column(JSON, nullable=False, default={})
    data_hash = Column(String(64), nullable=False)
    calculation_timestamp = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<DailyCalculations(telegram_id={self.telegram_id}, date={self.target_date})>"

    def to_dict(self):
        """Конвертация в словарь для API"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'astro_transits_data': self.astro_transits_data,
            'calculation_metadata': self.calculation_metadata,
            'data_hash': self.data_hash,
            'calculation_timestamp': self.calculation_timestamp.isoformat() if self.calculation_timestamp else None
        }


class Biorhythms(Base):
    """
    Исторические данные биоритмов
    Сохранена для обратной совместимости
    """
    __tablename__ = 'biorhythms'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    biorhythm_data = Column(JSON, nullable=False)
    calculation_date = Column(Date, primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Biorhythms(telegram_id={self.telegram_id}, date={self.calculation_date})>"

    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'calculation_date': self.calculation_date.isoformat(),
            'biorhythm_data': self.biorhythm_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CalculationCache(Base):
    """
    Кэш расчетов для оптимизации производительности
    """
    __tablename__ = 'calculation_cache'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    data_type = Column(String(20), primary_key=True)  # 'biorhythm', 'transits', 'combined'
    calculation_data = Column(JSON, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<CalculationCache(telegram_id={self.telegram_id}, date={self.target_date}, type={self.data_type})>"

    def is_expired(self):
        """Проверка истечения срока действия кэша"""
        from datetime import datetime
        return datetime.now() > self.expires_at

    def to_dict(self):
        """Конвертация в словарь"""
        return {
            'telegram_id': self.telegram_id,
            'target_date': self.target_date.isoformat(),
            'data_type': self.data_type,
            'calculation_data': self.calculation_data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired()
        }


# Создание индексов для оптимизации производительности
Index('idx_users_telegram_id', User.telegram_id)
Index('idx_users_birth_date', User.birth_date)
Index('idx_users_profession', User.profession)
Index('idx_users_gender', User.gender)
Index('idx_users_created_at', User.created_at)

Index('idx_astro_profile_telegram_id', UserAstroProfile.telegram_id)

Index('idx_daily_calc_telegram_id', DailyCalculations.telegram_id)
Index('idx_daily_calc_target_date', DailyCalculations.target_date)
Index('idx_daily_calc_composite', DailyCalculations.telegram_id, DailyCalculations.target_date)
Index('idx_daily_calc_hash', DailyCalculations.data_hash)
Index('idx_daily_calc_timestamp', DailyCalculations.calculation_timestamp)

Index('idx_biorhythms_telegram_id', Biorhythms.telegram_id)
Index('idx_biorhythms_calculation_date', Biorhythms.calculation_date)
Index('idx_biorhythms_composite', Biorhythms.telegram_id, Biorhythms.calculation_date)

Index('idx_cache_telegram_date', CalculationCache.telegram_id, CalculationCache.target_date)
Index('idx_cache_expires', CalculationCache.expires_at)
Index('idx_cache_type', CalculationCache.data_type)
Index('idx_cache_composite', CalculationCache.telegram_id, CalculationCache.target_date, CalculationCache.data_type)


async def get_db():
    """
    Dependency для получения сессии БД
    Используется в FastAPI endpoints
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Ошибка в сессии БД: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Инициализация базы данных
    Создание таблиц при первом запуске
    """
    try:
        async with async_engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False


async def check_db_connection():
    """
    Проверка подключения к базе данных
    """
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
        logger.info("✅ Подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False


async def get_database_stats():
    """
    Получение статистики базы данных
    """
    try:
        async with async_session() as session:
            # Статистика пользователей
            users_count = await session.execute("SELECT COUNT(*) FROM users")
            users_count = users_count.scalar()

            # Статистика астропрофилей
            profiles_count = await session.execute("SELECT COUNT(*) FROM user_astro_profile")
            profiles_count = profiles_count.scalar()

            # Статистика daily calculations
            calc_count = await session.execute("SELECT COUNT(*) FROM daily_calculations")
            calc_count = calc_count.scalar()

            # Статистика биоритмов
            bio_count = await session.execute("SELECT COUNT(*) FROM biorhythms")
            bio_count = bio_count.scalar()

            # Размер базы данных
            db_size = await session.execute("SELECT pg_size_pretty(pg_database_size('astra_db'))")
            db_size = db_size.scalar()

            return {
                'users_count': users_count,
                'profiles_count': profiles_count,
                'daily_calculations_count': calc_count,
                'biorhythms_count': bio_count,
                'database_size': db_size,
                'timestamp': func.now()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        return {}


async def cleanup_expired_cache():
    """
    Очистка просроченного кэша
    """
    try:
        from datetime import datetime

        async with async_session() as session:
            result = await session.execute(
                CalculationCache.__table__.delete().where(
                    CalculationCache.expires_at < datetime.now()
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} просроченных записей кэша")
            else:
                logger.debug("✅ Просроченных записей кэша не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка очистки кэша: {e}")
        return 0


class DatabaseManager:
    """
    Менеджер для работы с базой данных
    Предоставляет высокоуровневые методы для часто используемых операций
    """

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = async_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()

    async def get_user_with_profile(self, telegram_id: int) -> dict:
        """Получение пользователя с астропрофилем"""
        try:
            user_result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return None

            profile_result = await self.session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            profile = profile_result.scalar_one_or_none()

            return {
                'user': user.to_dict() if user else None,
                'astro_profile': profile.to_dict() if profile else None
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя с профилем: {e}")
            return None

    async def get_user_calculations_for_period(self, telegram_id: int, start_date: date, end_date: date) -> list:
        """Получение расчетов пользователя за период"""
        try:
            result = await self.session.execute(
                select(DailyCalculations)
                .where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date >= start_date,
                        DailyCalculations.target_date <= end_date
                    )
                )
                .order_by(DailyCalculations.target_date)
            )
            calculations = result.scalars().all()

            return [calc.to_dict() for calc in calculations]

        except Exception as e:
            logger.error(f"❌ Ошибка получения расчетов за период: {e}")
            return []

    async def increment_user_request_count(self, telegram_id: int) -> bool:
        """Увеличение счетчика запросов пользователя"""
        try:
            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.request_count = (user.request_count or 0) + 1
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка увеличения счетчика запросов: {e}")
            return False


# Глобальный экземпляр для быстрого доступа
db_manager = DatabaseManager()




backend.db_connection.py

from backend.database import async_session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def check_db_connection():
    """Проверка подключения к базе данных"""
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Подключение к БД успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False

backend.__init__.py

backend.matrix_services.py

from backend.database import async_session, UserAstroProfile
from backend.psyho_matrix import PsyhoMatrixCalculator
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def calculate_and_save_psyho_matrix(telegram_id: int):
    """Расчет и сохранение психоматрицы в объединенный астропрофиль"""
    try:
        # Получаем данные пользователя для расчета даты рождения
        from backend.user_services import get_user_profile
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError(f"Пользователь {telegram_id} не найден")

        calculator = PsyhoMatrixCalculator()
        matrix_data = calculator.calculate_matrix(user_profile['birth_date'])

        # Сохраняем психоматрицу в астропрофиль
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                # Обновляем существующий астропрофиль
                astro_profile.psyho_matrix_data = matrix_data
                # Натальная карта остается без изменений
                logger.info(f"📝 Обновлена психоматрица в астропрофиле для {telegram_id}")
            else:
                # Создаем новый астропрофиль с пустой натальной картой
                astro_profile = UserAstroProfile(
                    telegram_id=telegram_id,
                    natal_chart_data={},  # Пустая натальная карта
                    psyho_matrix_data=matrix_data,
                    dominant_energy=None,
                    personality_traits=None
                )
                session.add(astro_profile)
                logger.info(f"🆕 Создан новый астропрофиль с психоматрицей для {telegram_id}")

            await session.commit()
            logger.info(f"✅ Психоматрица рассчитана и сохранена для {telegram_id}")

        return matrix_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете психоматрицы для {telegram_id}: {e}")
        raise


async def get_user_matrix(telegram_id: int):
    """Получение психоматрицы пользователя из астропрофиля"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile and astro_profile.psyho_matrix_data:
                return astro_profile.psyho_matrix_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении психоматрицы {telegram_id}: {e}")
        return None


async def get_matrix_summary(telegram_id: int) -> dict:
    """Получение краткой сводки психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return {}

        basic_numbers = matrix_data.get('basic_numbers', {})
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        digit_counts = matrix_data.get('digit_counts', {})

        # Анализ основных чисел
        life_path = basic_numbers.get('first')
        destiny_number = basic_numbers.get('second')
        personality_number = basic_numbers.get('third')

        # Анализ матрицы Пифагора
        strong_digits = digit_counts.get('strong_digits', [])
        missing_digits = digit_counts.get('missing_digits', [])
        total_digits = digit_counts.get('total_digits', 0)

        # Определение типа матрицы по сложности
        if total_digits >= 15:
            matrix_type = "сложная"
        elif total_digits >= 10:
            matrix_type = "средняя"
        else:
            matrix_type = "простая"

        summary = {
            'basic_numbers': {
                'life_path': life_path,
                'destiny_number': destiny_number,
                'personality_number': personality_number
            },
            'matrix_analysis': {
                'matrix_type': matrix_type,
                'strong_digits': strong_digits,
                'missing_digits': missing_digits,
                'total_digits': total_digits
            },
            'key_characteristics': _analyze_matrix_characteristics(pythagoras_matrix)
        }

        return summary

    except Exception as e:
        logger.error(f"❌ Ошибка получения сводки психоматрицы для {telegram_id}: {e}")
        return {}


def _analyze_matrix_characteristics(pythagoras_matrix: dict) -> dict:
    """Анализ характеристик матрицы Пифагора"""
    characteristics = {
        'willpower': 0,  # Цифра 1
        'energy': 0,  # Цифра 2
        'interest': 0,  # Цифра 3
        'health': 0,  # Цифра 4
        'logic': 0,  # Цифра 5
        'labor': 0,  # Цифра 6
        'luck': 0,  # Цифра 7
        'duty': 0,  # Цифра 8
        'memory': 0  # Цифра 9
    }

    # Сопоставление цифр с характеристиками
    digit_characteristics = {
        '1': 'willpower',
        '2': 'energy',
        '3': 'interest',
        '4': 'health',
        '5': 'logic',
        '6': 'labor',
        '7': 'luck',
        '8': 'duty',
        '9': 'memory'
    }

    for digit, count in pythagoras_matrix.items():
        char_key = digit_characteristics.get(digit)
        if char_key:
            characteristics[char_key] = count

    return characteristics


async def calculate_personality_traits(telegram_id: int) -> list:
    """Расчет личностных черт на основе психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return []

        basic_numbers = matrix_data.get('basic_numbers', {})
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

        traits = []

        # Анализ по числу жизненного пути
        life_path = basic_numbers.get('first')
        if life_path:
            life_path_traits = {
                1: ["лидер", "амбициозный", "независимый"],
                2: ["дипломатичный", "чувствительный", "интуитивный"],
                3: ["творческий", "общительный", "оптимистичный"],
                4: ["практичный", "организованный", "надежный"],
                5: ["свободолюбивый", "авантюрный", "адаптивный"],
                6: ["ответственный", "заботливый", "гармоничный"],
                7: ["аналитический", "духовный", "интроспективный"],
                8: ["целеустремленный", "материалистичный", "властный"],
                9: ["гуманитарный", "сострадательный", "идеалистичный"]
            }
            traits.extend(life_path_traits.get(life_path, []))

        # Анализ по сильным цифрам в матрице
        strong_digits = []
        for digit, count in pythagoras_matrix.items():
            if count >= 2:
                strong_digits.append(int(digit))

        # Добавляем черты на основе сильных цифр
        digit_traits = {
            1: ["решительный", "инициативный"],
            2: ["эмпатичный", "тактичный"],
            3: ["артистичный", "выразительный"],
            4: ["трудолюбивый", "дисциплинированный"],
            5: ["любознательный", "гибкий"],
            6: ["семейный", "заботливый"],
            7: ["мудрый", "проницательный"],
            8: ["амбициозный", "практичный"],
            9: ["идеалистичный", "щедрый"]
        }

        for digit in strong_digits:
            if digit in digit_traits:
                traits.extend(digit_traits[digit])

        # Убираем дубликаты
        traits = list(set(traits))

        # Сохраняем черты в астропрофиль
        await update_personality_traits(telegram_id, traits)

        logger.info(f"✅ Рассчитаны личностные черты для {telegram_id}: {traits}")
        return traits

    except Exception as e:
        logger.error(f"❌ Ошибка расчета личностных черт для {telegram_id}: {e}")
        return []


async def update_personality_traits(telegram_id: int, traits: list):
    """Обновление личностных черт в астропрофиле"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if astro_profile:
                astro_profile.personality_traits = traits
                await session.commit()
                logger.info(f"📝 Обновлены личностные черты для {telegram_id}")
            else:
                logger.warning(f"⚠️ Астропрофиль не найден для обновления черт {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка обновления личностных черт для {telegram_id}: {e}")
        raise


async def validate_matrix_data(telegram_id: int) -> bool:
    """Проверка корректности данных психоматрицы"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return False

        # Проверяем обязательные поля
        required_fields = ['basic_numbers', 'pythagoras_matrix', 'digit_counts']
        for field in required_fields:
            if field not in matrix_data:
                logger.warning(f"⚠️ Отсутствует поле {field} в психоматрице {telegram_id}")
                return False

        # Проверяем базовые числа
        basic_numbers = matrix_data.get('basic_numbers', {})
        if not all(key in basic_numbers for key in ['first', 'second', 'third', 'fourth']):
            logger.warning(f"⚠️ Неполные базовые числа в психоматрице {telegram_id}")
            return False

        # Проверяем матрицу Пифагора
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        if not all(str(i) in pythagoras_matrix for i in range(1, 10)):
            logger.warning(f"⚠️ Неполная матрица Пифагора {telegram_id}")
            return False

        logger.info(f"✅ Данные психоматрицы валидны для {telegram_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации психоматрицы для {telegram_id}: {e}")
        return False


async def get_matrix_compatibility(user1_id: int, user2_id: int) -> dict:
    """Анализ совместимости по психоматрицам"""
    try:
        matrix1 = await get_user_matrix(user1_id)
        matrix2 = await get_user_matrix(user2_id)

        if not matrix1 or not matrix2:
            return {"error": "Не найдены данные психоматриц"}

        matrix1_data = matrix1.get('pythagoras_matrix', {})
        matrix2_data = matrix2.get('pythagoras_matrix', {})

        # Анализ совместимости по цифрам
        compatibility_score = 0
        max_score = 9  # Максимально возможный счет

        for digit in range(1, 10):
            digit_str = str(digit)
            count1 = matrix1_data.get(digit_str, 0)
            count2 = matrix2_data.get(digit_str, 0)

            # Чем ближе количество цифр, тем выше совместимость
            digit_compatibility = 1 - abs(count1 - count2) / 3  # Нормализуем до 0-1
            compatibility_score += digit_compatibility

        # Нормализуем общий счет
        overall_compatibility = (compatibility_score / max_score) * 100

        # Определяем уровень совместимости
        if overall_compatibility >= 80:
            level = "отличная"
        elif overall_compatibility >= 60:
            level = "хорошая"
        elif overall_compatibility >= 40:
            level = "средняя"
        else:
            level = "низкая"

        # Анализ сильных и слабых сторон совместимости
        strengths = []
        challenges = []

        # Анализ по конкретным цифрам
        for digit in range(1, 10):
            digit_str = str(digit)
            count1 = matrix1_data.get(digit_str, 0)
            count2 = matrix2_data.get(digit_str, 0)

            if count1 == count2 and count1 > 0:
                digit_meanings = {
                    1: "схожая воля и лидерские качества",
                    2: "совместимая энергия и чувствительность",
                    3: "общие творческие интересы",
                    4: "похожее отношение к здоровью",
                    5: "схожая логика и мышление",
                    6: "совместимость в трудовой деятельности",
                    7: "общая удача и везение",
                    8: "похожее чувство долга",
                    9: "схожие ментальные способности"
                }
                strengths.append(digit_meanings.get(digit, ""))

            elif abs(count1 - count2) >= 2:
                digit_challenges = {
                    1: "разные подходы к лидерству",
                    2: "разный уровень энергии",
                    3: "разные творческие интересы",
                    4: "разное отношение к здоровью",
                    5: "разные стили мышления",
                    6: "разное отношение к работе",
                    7: "разная удачливость",
                    8: "разное понимание долга",
                    9: "разные ментальные способности"
                }
                challenges.append(digit_challenges.get(digit, ""))

        return {
            'compatibility_score': round(overall_compatibility, 2),
            'compatibility_level': level,
            'strengths': [s for s in strengths if s],  # Убираем пустые строки
            'challenges': [c for c in challenges if c],
            'analysis_timestamp': await get_current_timestamp()
        }

    except Exception as e:
        logger.error(f"❌ Ошибка анализа совместимости для {user1_id} и {user2_id}: {e}")
        return {"error": str(e)}


async def get_current_timestamp():
    """Вспомогательная функция для получения текущего времени"""
    from datetime import datetime
    return datetime.now().isoformat()


async def get_matrix_energy_level(telegram_id: int) -> str:
    """Оценка уровня энергии по психоматрице"""
    try:
        matrix_data = await get_user_matrix(telegram_id)

        if not matrix_data:
            return "неизвестно"

        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})

        # Считаем общее количество цифр
        total_digits = sum(pythagoras_matrix.values())

        # Анализируем энергетические цифры (2, 5, 8)
        energy_digits = sum(pythagoras_matrix.get(str(digit), 0) for digit in [2, 5, 8])

        if total_digits >= 15 and energy_digits >= 4:
            return "очень высокий"
        elif total_digits >= 12 and energy_digits >= 3:
            return "высокий"
        elif total_digits >= 8 and energy_digits >= 2:
            return "средний"
        else:
            return "низкий"

    except Exception as e:
        logger.error(f"❌ Ошибка оценки уровня энергии для {telegram_id}: {e}")
        return "неизвестно"


class MatrixAnalysisService:
    """Сервис для углубленного анализа психоматриц"""

    def __init__(self):
        self.calculator = PsyhoMatrixCalculator()

    async def create_complete_matrix_profile(self, telegram_id: int, birth_date):
        """Создание полного профиля психоматрицы с расширенным анализом"""
        try:
            # Рассчитываем базовую матрицу
            matrix_data = self.calculator.calculate_matrix(birth_date)

            # Добавляем расширенный анализ
            extended_analysis = self._perform_extended_analysis(matrix_data)
            matrix_data['extended_analysis'] = extended_analysis

            # Сохраняем в астропрофиль
            async with async_session() as session:
                result = await session.execute(
                    select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
                )
                astro_profile = result.scalar_one_or_none()

                if astro_profile:
                    astro_profile.psyho_matrix_data = matrix_data
                else:
                    astro_profile = UserAstroProfile(
                        telegram_id=telegram_id,
                        natal_chart_data={},
                        psyho_matrix_data=matrix_data,
                        dominant_energy=None,
                        personality_traits=None
                    )
                    session.add(astro_profile)

                await session.commit()
                logger.info(f"✅ Полный профиль психоматрицы создан для {telegram_id}")
                return matrix_data

        except Exception as e:
            logger.error(f"❌ Ошибка создания полного профиля матрицы для {telegram_id}: {e}")
            raise

    def _perform_extended_analysis(self, matrix_data: dict) -> dict:
        """Расширенный анализ психоматрицы"""
        pythagoras_matrix = matrix_data.get('pythagoras_matrix', {})
        basic_numbers = matrix_data.get('basic_numbers', {})

        analysis = {
            'energy_centers': self._analyze_energy_centers(pythagoras_matrix),
            'life_periods': self._analyze_life_periods(basic_numbers.get('first')),
            'karmic_lessons': self._analyze_karmic_lessons(pythagoras_matrix),
            'talents_abilities': self._analyze_talents(pythagoras_matrix)
        }

        return analysis

    def _analyze_energy_centers(self, matrix: dict) -> dict:
        """Анализ энергетических центров"""
        centers = {
            'practical_center': sum(matrix.get(str(digit), 0) for digit in [4, 5, 6]),
            'spiritual_center': sum(matrix.get(str(digit), 0) for digit in [7, 8, 9]),
            'will_center': sum(matrix.get(str(digit), 0) for digit in [1, 2, 3])
        }

        return centers

    def _analyze_life_periods(self, life_path: int) -> list:
        """Анализ жизненных периодов"""
        if not life_path:
            return []

        periods = []
        base_age = 36  # Базовый возраст для расчета периодов

        for i in range(3):  # 3 основных периода
            period_number = (life_path + i) % 9 or 9
            start_age = i * 12
            end_age = (i + 1) * 12

            period_info = {
                'period': i + 1,
                'number': period_number,
                'age_range': f"{start_age}-{end_age}",
                'focus': self._get_period_focus(period_number)
            }
            periods.append(period_info)

        return periods

    def _get_period_focus(self, period_number: int) -> str:
        """Определение фокуса жизненного периода"""
        focuses = {
            1: "самоопределение и инициатива",
            2: "партнерство и сотрудничество",
            3: "творчество и самовыражение",
            4: "стабильность и организация",
            5: "свобода и изменения",
            6: "ответственность и служение",
            7: "анализ и духовность",
            8: "достижения и власть",
            9: "завершение и мудрость"
        }
        return focuses.get(period_number, "неопределенный период")

    def _analyze_karmic_lessons(self, matrix: dict) -> list:
        """Анализ кармических уроков (отсутствующие цифры)"""
        lessons = []
        digit_lessons = {
            1: "урок независимости и уверенности",
            2: "урок чувствительности и сотрудничества",
            3: "урок творчества и радости",
            4: "урок дисциплины и практичности",
            5: "урок свободы и адаптации",
            6: "урок ответственности и заботы",
            7: "урок мудрости и интуиции",
            8: "урок власти и изобилия",
            9: "урок сострадания и завершения"
        }

        for digit in range(1, 10):
            if matrix.get(str(digit), 0) == 0:
                lessons.append(digit_lessons.get(digit, f"урок цифры {digit}"))

        return lessons

    def _analyze_talents(self, matrix: dict) -> list:
        """Анализ талантов и способностей (сильные цифры)"""
        talents = []
        digit_talents = {
            1: "лидерские способности",
            2: "дипломатические навыки",
            3: "творческие таланты",
            4: "организаторские способности",
            5: "адаптивность и коммуникабельность",
            6: "педагогические способности",
            7: "аналитическое мышление",
            8: "бизнес-способности",
            9: "гуманитарные таланты"
        }

        for digit in range(1, 10):
            if matrix.get(str(digit), 0) >= 2:
                talents.append(digit_talents.get(digit, f"талант цифры {digit}"))

        return talents

    async def get_detailed_matrix_report(self, telegram_id: int) -> dict:
        """Получение детального отчета по психоматрице"""
        try:
            matrix_data = await get_user_matrix(telegram_id)

            if not matrix_data:
                return {"error": "Данные психоматрицы не найдены"}

            summary = await get_matrix_summary(telegram_id)
            traits = await calculate_personality_traits(telegram_id)
            energy_level = await get_matrix_energy_level(telegram_id)

            report = {
                'basic_info': summary,
                'personality_traits': traits,
                'energy_level': energy_level,
                'extended_analysis': matrix_data.get('extended_analysis', {}),
                'calculation_date': matrix_data.get('calculated_at'),
                'report_timestamp': await get_current_timestamp()
            }

            return report

        except Exception as e:
            logger.error(f"❌ Ошибка создания детального отчета для {telegram_id}: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
matrix_service = MatrixAnalysisService()

backend.moon.py

# backend/moon.py
from datetime import date
import math

def calculate_lunar_phase(target_date: date = None) -> str:
    """Вычисляет фазу луны для заданной даты.
    Возвращает строковое описание фазы луны."""
    if target_date is None:
        target_date = date.today()

    # Используем известный алгоритм расчёта фаз луны
    # 2001-01-01 - базовая дата нового месяца
    diff = (target_date - date(2001, 1, 1)).days
    lunations = 0.20439731 + (diff * 0.03386319269)
    lunation = lunations % 1
    index = int((lunation * 8) + 0.5) & 7
    phases = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]
    return phases[index]

backend.natal_chart.py

import os
import pytz
from datetime import datetime
import swisseph as swe
from math import floor
from typing import Dict, List, Tuple, Any
import logging
import requests
import time
from urllib.parse import quote

#from backend.database import async_session, UserNatalChart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLNatalChartCalculator:
    def __init__(self):
        current_dir = os.getcwd()
        ephe_path = os.path.join(current_dir, 'ephe')
        swe.set_ephe_path(ephe_path)
        swe.set_jpl_file('de441.eph')

        # Кэш для координат городов
        self.coordinates_cache = {}

        # Основные города России для быстрого доступа
        self.major_cities = {
            "москва": (55.7558, 37.6173, 156),
            "санкт-петербург": (59.9343, 30.3351, 3),
            "новосибирск": (55.0084, 82.9357, 150),
            "екатеринбург": (56.8389, 60.6057, 237),
            "нижний новгород": (56.3269, 44.0075, 78),
            "казань": (55.8304, 49.0661, 60),
            "челябинск": (55.1644, 61.4368, 228),
            "омск": (54.9884, 73.3242, 85),
            "самара": (53.2415, 50.2212, 87),
            "ростов-на-дону": (47.2225, 39.7187, 70),
            "уфа": (54.7355, 55.9587, 158),
            "красноярск": (56.0153, 92.8932, 136),
            "пермь": (58.0105, 56.2502, 149),
            "воронеж": (51.6720, 39.1843, 104),
            "волгоград": (48.7080, 44.5133, 80),
            "краснодар": (45.0355, 38.9750, 25),
            "саратов": (51.5924, 45.9608, 50),
            "тюмень": (57.1613, 65.5250, 70),
            "тольятти": (53.5088, 49.4192, 90),
            "ижевск": (56.8527, 53.2115, 140),
            "ульяновск": (54.3282, 48.3866, 80),
            "иркутск": (52.2864, 104.2806, 440),
            "хабаровск": (48.4802, 135.0719, 72),
            "ярославль": (57.6261, 39.8845, 100),
            "владивосток": (43.1332, 131.9113, 8),
            "мга": (59.7569, 31.0609, 33)
        }

        self.ORBS = {
            'conjunction': 8, 'opposition': 8, 'square': 8, 'trine': 8, 'sextile': 6,
            'quincunx': 3, 'semi-square': 3, 'semi-sextile': 3
        }

        self.planets_ml = {
            swe.SUN: 'Sun',
            swe.MOON: 'Moon',
            swe.MERCURY: 'Mercury',
            swe.VENUS: 'Venus',
            swe.MARS: 'Mars',
            swe.JUPITER: 'Jupiter',
            swe.SATURN: 'Saturn',
            swe.URANUS: 'Uranus',
            swe.NEPTUNE: 'Neptune',
            swe.PLUTO: 'Pluto',
            swe.TRUE_NODE: 'North_Node'
        }

        self.zodiac_signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]

        self.aspects_ml = {
            0: ('conjunction', self.ORBS['conjunction']),
            60: ('sextile', self.ORBS['sextile']),
            90: ('square', self.ORBS['square']),
            120: ('trine', self.ORBS['trine']),
            180: ('opposition', self.ORBS['opposition'])
        }

    def get_city_coordinates(self, city_name: str) -> Tuple[float, float, float]:
        """
        Надежное определение координат города.
        Сначала проверяет кэш, затем основные города, затем геокодинг.
        """
        city_lower = city_name.strip().lower()

        # 1. Проверяем кэш
        if city_lower in self.coordinates_cache:
            logger.info(f"Координаты из кэша для: {city_name}")
            return self.coordinates_cache[city_lower]

        # 2. Проверяем основные города России
        if city_lower in self.major_cities:
            coords = self.major_cities[city_lower]
            self.coordinates_cache[city_lower] = coords
            logger.info(f"Координаты из базы основных городов для: {city_name}")
            return coords

        # 3. Используем геокодинг через Nominatim (OpenStreetMap)
        try:
            coords = self._geocode_city(city_name)
            if coords:
                self.coordinates_cache[city_lower] = coords
                logger.info(f"Координаты получены через геокодинг для: {city_name}")
                return coords
        except Exception as e:
            logger.warning(f"Ошибка геокодинга для {city_name}: {e}")

        # 4. Резервный вариант - Москва
        logger.warning(f"Не удалось определить координаты для {city_name}, используем Москву")
        return (55.7558, 37.6173, 156)

    def _geocode_city(self, city_name: str) -> Tuple[float, float, float]:
        """
        Геокодинг города через Nominatim API (OpenStreetMap)
        """
        # Добавляем страну для лучшего определения
        search_query = f"{city_name}, Россия"
        encoded_query = quote(search_query)

        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"

        headers = {
            'User-Agent': 'AstrologyBot/1.0 (leostuchchi@example.com)',
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])

                # Определяем высоту (примерно, так как Nominatim не дает точную высоту)
                elevation = self._estimate_elevation(lat, lon)

                logger.info(f"Геокодинг успешен: {city_name} -> {lat}, {lon}, {elevation}м")
                return (lat, lon, elevation)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса геокодинга для {city_name}: {e}")
        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга ответа геокодинга для {city_name}: {e}")

        return None

    def _estimate_elevation(self, lat: float, lon: float) -> float:
        """
        Примерная оценка высоты над уровнем моря.
        Для точных данных лучше использовать специализированные API.
        """
        # Простая логика: прибрежные города ~0м, горные ~500м, равнинные ~100-200м
        if 43 <= lat <= 49 and 131 <= lon <= 142:  # Дальний Восток
            return 200
        elif 53 <= lat <= 58 and 48 <= lon <= 56:  # Поволжье
            return 100
        elif 55 <= lat <= 57 and 37 <= lon <= 40:  # Центральная Россия
            return 150
        elif 44 <= lat <= 46 and 38 <= lon <= 40:  # Юг России
            return 50
        elif 51 <= lat <= 53 and 103 <= lon <= 108:  # Байкал
            return 500
        else:
            return 100  # Средняя высота по умолчанию

    def _geocode_fallback(self, city_name: str) -> Tuple[float, float, float]:
        """
        Резервный метод геокодинга через альтернативный сервис
        """
        try:
            # Альтернативный сервис - GeoNames (требует API key)
            # Можно добавить при необходимости
            pass
        except Exception as e:
            logger.warning(f"Резервный геокодинг не сработал: {e}")

        return None

    def add_city_to_cache(self, city_name: str, lat: float, lon: float, elevation: float = 100):
        """
        Ручное добавление города в кэш
        """
        city_lower = city_name.strip().lower()
        self.coordinates_cache[city_lower] = (lat, lon, elevation)
        logger.info(f"Город добавлен в кэш: {city_name}")

    def get_cached_cities(self) -> List[str]:
        """
        Получить список всех закэшированных городов
        """
        return list(self.coordinates_cache.keys())

    # Остальные методы класса остаются без изменений
    def calculate_planet_positions(self, jd_ut: float) -> Dict[str, Dict]:
        positions = {}
        for planet_id, name in self.planets_ml.items():
            try:
                flags = swe.FLG_SWIEPH | swe.FLG_SPEED
                pos, ret_flags = swe.calc_ut(jd_ut, planet_id, flags)
                lon = pos[0] % 360
                sign_index = floor(lon / 30)
                positions[name] = {
                    'longitude': round(lon, 6),
                    'sign': self.zodiac_signs[sign_index],
                    'sign_index': sign_index,
                    'position_in_sign': round(lon % 30, 4),
                    'retrograde': pos[3] < 0,
                    'speed': round(pos[3], 6)
                }
            except Exception as e:
                logger.warning(f"Ошибка расчета для {name}: {e}")
                continue
        return positions

    def calculate_houses_ml(self, jd_ut: float, lat: float, lon: float) -> Dict:
        try:
            hsys = b'P'
            cusps, ascmc = swe.houses(jd_ut, lat, lon, hsys)
            houses = {}
            for i, cusp in enumerate(cusps[:12]):
                cusp_deg = cusp % 360
                sign_index = floor(cusp_deg / 30)
                houses[i + 1] = {
                    'cusp_longitude': round(cusp_deg, 6),
                    'sign': self.zodiac_signs[sign_index],
                    'sign_index': sign_index,
                    'position_in_sign': round(cusp_deg % 30, 4)
                }
            return {
                'houses': houses,
                'ascendant': round(ascmc[0] % 360, 6),
                'midheaven': round(ascmc[1] % 360, 6),
                'house_system': 'Placidus'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета домов: {e}")
            return self._get_default_houses()

    def _get_default_houses(self) -> Dict:
        houses = {}
        for i in range(12):
            houses[i + 1] = {
                'cusp_longitude': round(i * 30.0, 6),
                'sign': self.zodiac_signs[i],
                'sign_index': i,
                'position_in_sign': 0.0
            }
        return {
            'houses': houses,
            'ascendant': 0.0,
            'midheaven': 0.0,
            'house_system': 'Placidus'
        }

    def calculate_aspects_ml(self, planets: Dict, asc: float, mc: float) -> List[Dict]:
        aspects = []
        all_points = {**planets}
        all_points['Ascendant'] = {'longitude': asc}
        all_points['Midheaven'] = {'longitude': mc}
        point_names = list(all_points.keys())
        for i in range(len(point_names)):
            for j in range(i + 1, len(point_names)):
                p1, p2 = point_names[i], point_names[j]
                lon1, lon2 = all_points[p1]['longitude'], all_points[p2]['longitude']
                distance = abs(lon1 - lon2)
                angle = min(distance, 360 - distance)
                for aspect_angle, (aspect_name, orb) in self.aspects_ml.items():
                    if abs(angle - aspect_angle) <= orb:
                        aspects.append({
                            'point1': p1,
                            'point2': p2,
                            'aspect': aspect_name,
                            'exact_angle': aspect_angle,
                            'actual_angle': round(angle, 4),
                            'orb': round(abs(angle - aspect_angle), 4),
                            'strength': 1.0 - (abs(angle - aspect_angle) / orb)
                        })
                        break
        aspects.sort(key=lambda x: x['strength'], reverse=True)
        return aspects

    def get_planet_house_placement(self, planets: Dict, houses: Dict) -> Dict:
        house_placement = {}
        for planet_name, planet_data in planets.items():
            planet_lon = planet_data['longitude']
            for house_num, house_data in houses.items():
                next_house_num = house_num + 1 if house_num < 12 else 1
                next_house_lon = houses[next_house_num]['cusp_longitude']
                current_lon = house_data['cusp_longitude']
                if next_house_lon < current_lon:
                    next_house_lon += 360
                    adjusted_planet_lon = planet_lon + 360 if planet_lon < current_lon else planet_lon
                else:
                    adjusted_planet_lon = planet_lon
                if current_lon <= adjusted_planet_lon < next_house_lon:
                    house_placement[planet_name] = house_num
                    break
            else:
                house_placement[planet_name] = 1
        return house_placement

    def calculate_natal_chart_ml(self, city_name: str, birth_datetime_local: datetime, timezone_str: str) -> Dict[
        str, Any]:
        try:
            lat, lon, elevation = self.get_city_coordinates(city_name)
            local_tz = pytz.timezone(timezone_str)
            birth_local = local_tz.localize(birth_datetime_local)
            birth_utc = birth_local.astimezone(pytz.utc)
            jd_ut = swe.julday(
                birth_utc.year,
                birth_utc.month,
                birth_utc.day,
                birth_utc.hour + birth_utc.minute / 60 + birth_utc.second / 3600
            )
            planets = self.calculate_planet_positions(jd_ut)
            houses_data = self.calculate_houses_ml(jd_ut, lat, lon)
            house_placement = self.get_planet_house_placement(planets, houses_data['houses'])
            aspects = self.calculate_aspects_ml(planets, houses_data['ascendant'], houses_data['midheaven'])
            return {
                'metadata': {
                    'location': {
                        'city': city_name,
                        'lat': round(lat, 4),
                        'lon': round(lon, 4),
                        'elevation': round(elevation, 1)
                    },
                    'datetime': {
                        'local': birth_local.isoformat(),
                        'utc': birth_utc.isoformat(),
                        'jd': round(jd_ut, 6)
                    },
                    'calculation': {
                        'house_system': houses_data['house_system'],
                        'ephemeris': 'DE441'
                    }
                },
                'planets': planets,
                'houses': houses_data['houses'],
                'angles': {
                    'ascendant': {
                        'longitude': houses_data['ascendant'],
                        'sign': self.zodiac_signs[floor(houses_data['ascendant'] / 30)],
                        'sign_index': floor(houses_data['ascendant'] / 30)
                    },
                    'midheaven': {
                        'longitude': houses_data['midheaven'],
                        'sign': self.zodiac_signs[floor(houses_data['midheaven'] / 30)],
                        'sign_index': floor(houses_data['midheaven'] / 30)
                    }
                },
                'placements': house_placement,
                'aspects': aspects,
                'ml_features': {
                    'sign_distribution': self._get_sign_distribution(planets, houses_data),
                    'aspect_patterns': self._get_aspect_patterns(aspects),
                    'element_balance': self._get_element_balance(planets)
                }
            }
        except Exception as e:
            logger.error(f"Ошибка расчета натальной карты: {e}")
            raise

    def _get_sign_distribution(self, planets: Dict, houses_data: Dict) -> Dict[str, int]:
        distribution = {sign: 0 for sign in self.zodiac_signs}
        for planet_data in planets.values():
            distribution[planet_data['sign']] += 1
        return distribution

    def _get_aspect_patterns(self, aspects: List[Dict]) -> Dict[str, int]:
        patterns = {
            'conjunctions': 0,
            'squares': 0,
            'trines': 0,
            'oppositions': 0,
            'sextiles': 0
        }
        for aspect in aspects:
            if aspect['aspect'] in patterns:
                patterns[aspect['aspect']] += 1
        return patterns

    def _get_element_balance(self, planets: Dict) -> Dict[str, int]:
        elements = {
            'fire': ['Aries', 'Leo', 'Sagittarius'],
            'earth': ['Taurus', 'Virgo', 'Capricorn'],
            'air': ['Gemini', 'Libra', 'Aquarius'],
            'water': ['Cancer', 'Scorpio', 'Pisces']
        }
        balance = {element: 0 for element in elements}
        for planet_data in planets.values():
            for element, signs in elements.items():
                if planet_data['sign'] in signs:
                    balance[element] += 1
                    break
        return balance

    def save_ml_chart(self, natal_chart: Dict, filename: str = 'natal_chart_ml.json') -> None:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(natal_chart, f, ensure_ascii=False, indent=2, separators=(',', ':'))
        logger.info(f"ML-натальная карта сохранена: {filename}")

backend.predictions.py

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
        """Анализ аспектов с определением силы"""
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
                    aspect_data = {
                        'transit_planet': t_planet,
                        'natal_planet': n_planet,
                        'aspect': aspect_info[0],
                        'exact_angle': aspect_info[1],
                        'actual_angle': round(angle, 2),
                        'orb': round(abs(angle - aspect_info[1]), 2),
                        'strength': round(1.0 - (abs(angle - aspect_info[1]) / aspect_info[2]), 2)
                    }

                    # ✅ ДОБАВЛЕНО: ФЛАГ СИЛЬНОГО АСПЕКТА
                    aspect_data['is_strong'] = aspect_data['strength'] > 0.7

                    aspects.append(aspect_data)

        # Сортируем по силе аспектов
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

    def generate_prediction(self, target_date):
        """Основной метод генерации данных для предсказания на основе РАСЧЕТОВ"""
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

            # ✅ ДОБАВЛЕНО: Подсчет сильных аспектов
            strong_aspects_count = len([a for a in aspects if a.get('is_strong', False)])

            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'transits': transits,
                'aspects': aspects,
                'aspects_count': len(aspects),
                'strong_aspects_count': strong_aspects_count,  # ✅ ДОБАВЛЕНО
                'retrograde_planets': [p for p, data in transits.items() if data.get('retrograde')]
            }

        except Exception as e:
            # В случае ошибки возвращаем пустые данные с информацией об ошибке
            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'transits': {},
                'aspects': [],
                'aspects_count': 0,
                'strong_aspects_count': 0,
                'retrograde_planets': [],
                'calculation_error': True,
                'error_message': str(e)
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

backend.prediction_services.py

from backend.database import async_session, DailyCalculations, UserAstroProfile
from backend.predictions import AstroPredictor
from backend.chart_services import get_user_natal_chart
from backend.matrix_services import get_user_matrix
from backend.biorhythm_services import calculate_and_save_biorhythms
from backend.aspect_recommendations import aspect_recommendations
from sqlalchemy.future import select
from sqlalchemy import func, and_
import logging
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


class DataCombiner:
    """Класс для объединения данных астрологии и биоритмов"""

    def __init__(self):
        pass

    def combine_calculation_data(self, astro_prediction: dict, biorhythm_data: dict) -> dict:
        """Объединение данных из астрологии и биоритмов"""

        return {
            'calculation_date': datetime.now().isoformat(),
            'target_date': astro_prediction.get('prediction_date', datetime.now().date().isoformat()),
            'astro_data': {
                'transits_count': len(astro_prediction.get('transits', {})),
                'aspects_count': astro_prediction.get('aspects_count', 0),
                'strong_aspects_count': astro_prediction.get('strong_aspects_count', 0),
                'retrograde_planets': astro_prediction.get('retrograde_planets', []),
                'key_aspects': astro_prediction.get('aspects', [])[:5],
                'calculation_error': astro_prediction.get('calculation_error', False),
                'error_message': astro_prediction.get('error_message')
            },
            'biorhythm_data': {
                'overall_energy': biorhythm_data.get('overall_energy', {}),
                'cycles': biorhythm_data.get('cycles', {}),
                'critical_days_count': len(biorhythm_data.get('critical_days', [])),
                'peak_days_count': len(biorhythm_data.get('peak_days', [])),
                'days_lived': biorhythm_data.get('days_lived', 0)
            },
            'calculation_metadata': {
                'calculation_timestamp': datetime.now().isoformat(),
                'data_sources': ['astrology', 'biorhythms'],
                'calculation_methods': ['swiss_ephemeris', 'sine_wave_analysis'],
                'data_version': '2.0'
            }
        }


def _extract_strong_aspects(astro_data: dict) -> List[str]:
    """Извлечение и форматирование сильных аспектов"""
    strong_aspects = []

    try:
        key_aspects = astro_data.get('key_aspects', [])

        # Сортируем аспекты по силе (от самых сильных)
        sorted_aspects = sorted(key_aspects, key=lambda x: x.get('strength', 0), reverse=True)

        for aspect in sorted_aspects:
            # Фильтруем только сильные аспекты (strength > 0.7)
            if aspect.get('strength', 0) > 0.7:
                transit_planet = aspect.get('transit_planet', '')
                natal_planet = aspect.get('natal_planet', '')
                aspect_type = aspect.get('aspect', '')
                strength = aspect.get('strength', 0)

                # Форматируем для пользователя
                if transit_planet and natal_planet and aspect_type:
                    # Переводим названия планет на русский
                    planet_names = {
                        'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
                        'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
                        'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
                        'Pluto': 'Плутон', 'North_Node': 'Северный узел',
                        'Ascendant': 'Асцендент', 'Midheaven': 'МС'
                    }

                    aspect_names = {
                        'conjunction': 'соединение', 'opposition': 'оппозиция',
                        'square': 'квадрат', 'trine': 'трин', 'sextile': 'секстиль'
                    }

                    transit_ru = planet_names.get(transit_planet, transit_planet)
                    natal_ru = planet_names.get(natal_planet, natal_planet)
                    aspect_ru = aspect_names.get(aspect_type, aspect_type)

                    # Добавляем силу аспекта (★ за каждые 0.2 силы)
                    strength_stars = "★" * int(strength * 5)

                    strong_aspects.append(f"{transit_ru} → {natal_ru} ({aspect_ru}) {strength_stars}")

        return strong_aspects

    except Exception as e:
        logger.error(f"❌ Ошибка извлечения сильных аспектов: {e}")
        return []


def _generate_data_hash(telegram_id: int, target_date: date, calculation_data: dict) -> str:
    """Генерация хэша данных для кэширования"""
    try:
        data_str = f"{telegram_id}_{target_date.isoformat()}_{json.dumps(calculation_data, sort_keys=True)}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"❌ Ошибка генерации хэша: {e}")
        return "fallback_hash"


async def format_data_for_user(prediction: dict) -> str:
    """Форматирование данных для отображения пользователю в боте"""
    if not prediction:
        return "❌ Не удалось получить данные расчетов"

    try:
        daily_data = prediction.get('daily_calculations', {})
        target_date_str = daily_data.get('target_date', 'сегодня')

        # Преобразуем строку даты в читаемый формат
        try:
            target_date = datetime.fromisoformat(target_date_str).date()
            formatted_date = target_date.strftime('%d.%m.%Y')
        except:
            formatted_date = target_date_str

        lines = []
        lines.append(f"📊 **Результаты расчетов на {formatted_date}**")
        lines.append("")

        # Биоритмы
        biorhythms = daily_data.get('biorhythm_data', {})
        if biorhythms:
            overall_energy = biorhythms.get('overall_energy', {})
            lines.append(
                f"⚡ **Общая энергия:** {overall_energy.get('percentage', 0):.1f}%")

            cycles = biorhythms.get('cycles', {})
            physical = cycles.get('physical', {})
            emotional = cycles.get('emotional', {})
            intellectual = cycles.get('intellectual', {})

            lines.append(
                f"💪 **Физический цикл:** {physical.get('percentage', 0):.1f}% ({physical.get('phase', 'нейтральная')})")
            lines.append(
                f"😊 **Эмоциональный цикл:** {emotional.get('percentage', 0):.1f}% ({emotional.get('phase', 'нейтральная')})")
            lines.append(
                f"🧠 **Интеллектуальный цикл:** {intellectual.get('percentage', 0):.1f}% ({intellectual.get('phase', 'нейтральная')})")
            lines.append("")

        # Астрологические данные
        astro_data = daily_data.get('astro_data', {})
        if astro_data:
            lines.append(
                f"🌟 **Астрология:** {astro_data.get('aspects_count', 0)} аспектов, {astro_data.get('strong_aspects_count', 0)} сильных")

            # Рекомендации по аспектам
            key_aspects = astro_data.get('key_aspects', [])
            aspect_recommendations_list = aspect_recommendations.generate_aspect_recommendations(key_aspects)

            if aspect_recommendations_list:
                lines.append("🔮 **Астрологические рекомендации:**")
                for rec in aspect_recommendations_list[:3]:  # Максимум 3 рекомендации
                    lines.append(f"   • {rec}")
                lines.append("")

            # Сильные аспекты (детальные)
            strong_aspects = _extract_strong_aspects(astro_data)
            if strong_aspects:
                lines.append("📈 **Сильные аспекты:**")
                for aspect in strong_aspects[:2]:  # Только 2 самых сильных
                    lines.append(f"   • {aspect}")
                lines.append("")

            retrograde_planets = astro_data.get('retrograde_planets', [])
            if retrograde_planets:
                planet_names = {
                    'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
                    'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
                    'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун',
                    'Pluto': 'Плутон'
                }
                retrograde_ru = [planet_names.get(p, p) for p in retrograde_planets]
                lines.append(f"🔄 **Ретроградные планеты:** {', '.join(retrograde_ru)}")

        # Критические дни
        if biorhythms and biorhythms.get('critical_days_count', 0) > 0:
            lines.append("")
            lines.append("⚠️ **Критический день** - будьте осторожны в принятии решений")

        lines.append("")
        lines.append("🎯 *Используйте эти данные для планирования своего дня*")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Ошибка форматирования данных: {e}")
        return "❌ Произошла ошибка при формировании данных расчетов"


async def generate_and_save_prediction(telegram_id: int, target_date: date) -> Dict[str, Any]:
    """Генерация и сохранение данных для конкретной даты"""
    try:
        logger.info(f"🔮 Генерация данных для пользователя {telegram_id} на {target_date}")

        # Получаем натальную карту пользователя
        natal_data = await get_user_natal_chart(telegram_id)
        if not natal_data:
            logger.warning(f"⚠️ Натальная карта не найдена для пользователя {telegram_id}")
            raise ValueError("Натальная карта не найдена. Сначала создайте натальную карту с помощью /start")

        logger.info(f"✅ Натальная карта найдена для {telegram_id}")

        # Получаем психоматрицу пользователя
        matrix_data = await get_user_matrix(telegram_id)
        logger.info(f"✅ Психоматрица получена для {telegram_id}")

        # Рассчитываем биоритмы на целевую дату
        biorhythm_data = await calculate_and_save_biorhythms(telegram_id, target_date)
        logger.info(f"✅ Биоритмы рассчитаны для {telegram_id} на {target_date}")

        # Генерируем астрологические данные на целевую дату
        predictor = AstroPredictor(natal_data)
        astro_prediction = predictor.generate_prediction(target_date)
        logger.info(f"✅ Астрологические данные сгенерированы для {telegram_id} на {target_date}")

        # Объединяем данные
        combiner = DataCombiner()
        combined_data = combiner.combine_calculation_data(astro_prediction, biorhythm_data)

        logger.info(f"✅ Комбинированные данные созданы для {telegram_id}")

        # Сохраняем в daily_calculations
        await save_daily_calculations(telegram_id, target_date, combined_data)

        # Структура данных для возврата
        prediction_data = {
            'calculation_date': datetime.now().isoformat(),
            'target_date': target_date.isoformat(),
            'natal_chart': natal_data,
            'psyho_matrix': matrix_data,
            'daily_calculations': combined_data
        }

        logger.info(f"💾 Все данные сохранены для {telegram_id} на {target_date}")

        return prediction_data

    except ValueError as e:
        logger.warning(f"❌ Ошибка валидации для {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации данных для {telegram_id}: {e}")
        raise Exception(f"Не удалось сгенерировать данные на основе расчетов: {str(e)}")


async def save_daily_calculations(telegram_id: int, target_date: date, calculation_data: dict) -> bool:
    """Сохранение ежедневных расчетов в оптимизированную таблицу"""
    try:
        data_hash = _generate_data_hash(telegram_id, target_date, calculation_data)

        async with async_session() as session:
            # Проверяем существующую запись
            result = await session.execute(
                select(DailyCalculations).where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
            )
            existing_record = result.scalar_one_or_none()

            if existing_record:
                # Обновляем существующую запись
                existing_record.biorhythm_data = calculation_data.get('biorhythm_data', {})
                existing_record.astro_transits_data = calculation_data.get('astro_data', {})
                existing_record.calculation_metadata = calculation_data.get('calculation_metadata', {})
                existing_record.data_hash = data_hash
                existing_record.calculation_timestamp = datetime.now()
                logger.info(f"📝 Обновлены daily calculations для {telegram_id} на {target_date}")
            else:
                # Создаем новую запись
                new_record = DailyCalculations(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    biorhythm_data=calculation_data.get('biorhythm_data', {}),
                    astro_transits_data=calculation_data.get('astro_data', {}),
                    calculation_metadata=calculation_data.get('calculation_metadata', {}),
                    data_hash=data_hash,
                    calculation_timestamp=datetime.now()
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы daily calculations для {telegram_id} на {target_date}")

            await session.commit()
            return True

    except Exception as e:
        logger.error(f"❌ Ошибка сохранения daily calculations для {telegram_id}: {e}")
        await session.rollback()
        return False


async def get_daily_calculations(telegram_id: int, target_date: date) -> Optional[Dict[str, Any]]:
    """Получение ежедневных расчетов для конкретной даты"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(DailyCalculations).where(
                    and_(
                        DailyCalculations.telegram_id == telegram_id,
                        DailyCalculations.target_date == target_date
                    )
                )
            )
            daily_calc = result.scalar_one_or_none()

            if daily_calc:
                return {
                    'biorhythm_data': daily_calc.biorhythm_data,
                    'astro_transits_data': daily_calc.astro_transits_data,
                    'calculation_metadata': daily_calc.calculation_metadata,
                    'calculation_timestamp': daily_calc.calculation_timestamp.isoformat(),
                    'data_hash': daily_calc.data_hash
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка получения daily calculations для {telegram_id}: {e}")
        return None


async def get_user_predictions(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получение последних данных пользователя (для обратной совместимости)"""
    try:
        # Получаем статические данные
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if not astro_profile:
                return None

            # Получаем последние daily calculations
            today = date.today()
            daily_calc = await get_daily_calculations(telegram_id, today)

            return {
                'calculation_date': datetime.now().isoformat(),
                'target_date': today.isoformat(),
                'natal_chart': astro_profile.natal_chart_data,
                'psyho_matrix': astro_profile.psyho_matrix_data,
                'daily_calculations': daily_calc or {}
            }

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных {telegram_id}: {e}")
        return None


async def get_prediction_statistics(telegram_id: int) -> dict:
    """Получение статистики данных пользователя"""
    try:
        # Получаем количество записей daily calculations
        async with async_session() as session:
            count_result = await session.execute(
                select(func.count(DailyCalculations.telegram_id)).where(
                    DailyCalculations.telegram_id == telegram_id
                )
            )
            total_calculations = count_result.scalar() or 0

            # Получаем даты первой и последней записи
            dates_result = await session.execute(
                select(
                    func.min(DailyCalculations.target_date),
                    func.max(DailyCalculations.target_date)
                ).where(DailyCalculations.telegram_id == telegram_id)
            )
            min_date, max_date = dates_result.first() or (None, None)

        # Получаем последние расчеты
        latest_calc = await get_daily_calculations(telegram_id, date.today())

        return {
            'total_calculations': total_calculations,
            'first_calculation_date': min_date.isoformat() if min_date else None,
            'last_calculation_date': max_date.isoformat() if max_date else None,
            'calculation_range_days': (max_date - min_date).days if min_date and max_date else 0,
            'latest_energy_level': latest_calc.get('biorhythm_data', {}).get('overall_energy', {}).get('percentage', 0) if latest_calc else 0,
            'latest_aspects_count': latest_calc.get('astro_transits_data', {}).get('aspects_count', 0) if latest_calc else 0
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        return {}


async def validate_prediction_data(telegram_id: int) -> bool:
    """Проверка корректности данных"""
    try:
        # Проверяем наличие астропрофиля
        async with async_session() as session:
            result = await session.execute(
                select(UserAstroProfile).where(UserAstroProfile.telegram_id == telegram_id)
            )
            astro_profile = result.scalar_one_or_none()

            if not astro_profile:
                return False

            # Проверяем наличие основных данных
            if not astro_profile.natal_chart_data or not astro_profile.psyho_matrix_data:
                return False

            # Проверяем наличие хотя бы одной записи daily calculations
            today = date.today()
            daily_calc = await get_daily_calculations(telegram_id, today)

            return daily_calc is not None

    except Exception as e:
        logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
        return False


async def cleanup_old_predictions(days_old: int = 30) -> int:
    """Очистка устаревших данных daily calculations"""
    try:
        cutoff_date = date.today() - timedelta(days=days_old)

        async with async_session() as session:
            result = await session.execute(
                DailyCalculations.__table__.delete().where(
                    DailyCalculations.target_date < cutoff_date
                )
            )
            deleted_count = result.rowcount

            await session.commit()

            if deleted_count > 0:
                logger.info(f"🗑️ Удалено {deleted_count} устаревших записей daily calculations (старше {days_old} дней)")
            else:
                logger.info("✅ Устаревших записей daily calculations для удаления не найдено")

            return deleted_count

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке устаревших данных: {e}")
        return 0


async def get_user_calculation_history(telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получение истории расчетов пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(DailyCalculations)
                .where(DailyCalculations.telegram_id == telegram_id)
                .order_by(DailyCalculations.target_date.desc())
                .limit(limit)
            )
            calculations = result.scalars().all()

            history = []
            for calc in calculations:
                history.append({
                    'target_date': calc.target_date.isoformat(),
                    'energy_level': calc.biorhythm_data.get('overall_energy', {}).get('percentage', 0),
                    'aspects_count': calc.astro_transits_data.get('aspects_count', 0),
                    'calculation_timestamp': calc.calculation_timestamp.isoformat()
                })

            return history

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории расчетов для {telegram_id}: {e}")
        return []


async def calculate_data_freshness(telegram_id: int, target_date: date) -> Dict[str, Any]:
    """Проверка свежести данных"""
    try:
        daily_calc = await get_daily_calculations(telegram_id, target_date)

        if not daily_calc:
            return {
                'is_fresh': False,
                'age_hours': None,
                'status': 'NO_DATA'
            }

        calc_timestamp = datetime.fromisoformat(daily_calc['calculation_timestamp'])
        age_hours = (datetime.now() - calc_timestamp).total_seconds() / 3600

        return {
            'is_fresh': age_hours < 24,  # Считаем свежими данные младше 24 часов
            'age_hours': round(age_hours, 2),
            'calculation_timestamp': daily_calc['calculation_timestamp'],
            'status': 'FRESH' if age_hours < 24 else 'STALE'
        }

    except Exception as e:
        logger.error(f"❌ Ошибка проверки свежести данных для {telegram_id}: {e}")
        return {
            'is_fresh': False,
            'age_hours': None,
            'status': 'ERROR'
        }

backend.psyho_matrix.py

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PsyhoMatrixCalculator:
    def __init__(self):
        pass

    def calculate_matrix(self, birth_date: datetime.date):
        """Расчет психоматрицы по дате рождения (нумерология Пифагора)"""
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year

        # Преобразуем дату в строку для расчетов
        date_str = f"{day:02d}{month:02d}{year}"

        # Первое число - сумма всех цифр даты
        first_number = sum(int(d) for d in date_str)

        # Второе число - сумма цифр первого числа
        second_number = sum(int(d) for d in str(first_number))

        # Третье число - первое число минус удвоенная первая цифра дня рождения
        first_digit_of_day = day // 10
        third_number = first_number - 2 * first_digit_of_day

        # Четвертое число - сумма цифр третьего числа
        fourth_number = sum(int(d) for d in str(third_number))

        # Строим матрицу 3x3 по методу Пифагора
        matrix_numbers = self._build_pythagoras_matrix(day, month, year)

        # Анализируем характеристики на основе РАСЧЕТОВ
        matrix_data = {
            'basic_numbers': {
                'first': first_number,
                'second': second_number,
                'third': third_number,
                'fourth': fourth_number
            },
            'pythagoras_matrix': matrix_numbers,
            'digit_counts': self._calculate_digit_counts(matrix_numbers),
            'calculated_at': datetime.now().isoformat()
        }

        return matrix_data

    def _build_pythagoras_matrix(self, day: int, month: int, year: int):
        """Построение психоматрицы Пифагора 3x3"""
        # Собираем все цифры даты рождения
        all_digits = []
        all_digits.extend([int(d) for d in str(day)])
        all_digits.extend([int(d) for d in str(month)])
        all_digits.extend([int(d) for d in str(year)])

        # Считаем количество каждой цифры от 1 до 9
        matrix = {}
        for i in range(1, 10):
            matrix[str(i)] = all_digits.count(i)

        return matrix

    def _calculate_digit_counts(self, matrix):
        """Расчет статистики по цифрам"""
        return {
            'total_digits': sum(matrix.values()),
            'strong_digits': [digit for digit, count in matrix.items() if count >= 2],
            'missing_digits': [digit for digit in map(str, range(1, 10)) if matrix.get(digit, 0) == 0]
        }

backend.user_services.py

from backend.database import async_session, User
from sqlalchemy.future import select
from sqlalchemy import func  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ
from datetime import datetime  # ← ДОБАВИТЬ ДЛЯ calculated_at
import logging

logger = logging.getLogger(__name__)


async def create_or_update_user(
        telegram_id: int,
        birth_date,
        birth_time,
        birth_city: str,
        profession: str = None,
        job_position: str = None,
        current_city: str = None,
        gender: str = None
):
    """Создание или обновление пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Обновляем существующего пользователя
                user.birth_date = birth_date
                user.birth_time = birth_time
                user.birth_city = birth_city
                if profession:
                    user.profession = profession
                if job_position:
                    user.job_position = job_position
                if current_city:
                    user.current_city = current_city
                if gender is not None:
                    user.gender = gender
                logger.info(f"📝 Обновлен пользователь {telegram_id}")
            else:
                # Создаем нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    birth_city=birth_city,
                    profession=profession,
                    job_position=job_position,
                    current_city=current_city,
                    gender=gender,
                    request_count=0
                )
                session.add(user)
                logger.info(f"🆕 Создан новый пользователь {telegram_id}")

            await session.commit()
            return user

    except Exception as e:
        logger.error(f"❌ Ошибка при работе с пользователем {telegram_id}: {e}")
        raise


async def get_user_profile(telegram_id: int):
    """Получение профиля пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                return {
                    'telegram_id': user.telegram_id,
                    'birth_date': user.birth_date,
                    'birth_time': user.birth_time,
                    'birth_city': user.birth_city,
                    'profession': user.profession,
                    'job_position': user.job_position,
                    'current_city': user.current_city,
                    'gender': user.gender,
                    'request_count': user.request_count or 0,
                    'created_at': user.created_at
                }
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении профиля {telegram_id}: {e}")
        return None


async def update_user_profession(telegram_id: int, profession: str, job_position: str = None):
    """Обновление профессиональных данных пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.profession = profession
                if job_position:
                    user.job_position = job_position
                await session.commit()
                logger.info(f"📝 Обновлены профессиональные данные для {telegram_id}")
                return user
            else:
                raise ValueError("Пользователь не найден")

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении профессии {telegram_id}: {e}")
        raise


async def increment_request_count(telegram_id: int):
    """Увеличивает счетчик обращений пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                current_count = user.request_count or 0
                user.request_count = current_count + 1
                await session.commit()
                logger.info(f"📈 Увеличен счетчик обращений для {telegram_id}: {current_count} -> {user.request_count}")
                return user.request_count
            else:
                logger.warning(f"⚠️ Пользователь {telegram_id} не найден при увеличении счетчика")
                return None

    except Exception as e:
        logger.error(f"❌ Ошибка при увеличении счетчика обращений {telegram_id}: {e}")
        return None


async def get_user_request_count(telegram_id: int):
    """Получение текущего количества обращений пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User.request_count).where(User.telegram_id == telegram_id)
            )
            count = result.scalar_one_or_none()
            return count or 0

    except Exception as e:
        logger.error(f"❌ Ошибка при получении счетчика обращений {telegram_id}: {e}")
        return 0


async def update_user_gender(telegram_id: int, gender: str):
    """Обновление пола пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.gender = gender
                await session.commit()
                logger.info(f"📝 Обновлен пол пользователя {telegram_id}: {gender}")
                return user
            else:
                raise ValueError("Пользователь не найден")

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении пола {telegram_id}: {e}")
        raise


async def get_users_statistics():
    """Получение общей статистики пользователей"""
    try:
        async with async_session() as session:
            # Общее количество пользователей
            total_users_result = await session.execute(
                select(User).where(User.telegram_id.isnot(None))
            )
            total_users = len(total_users_result.scalars().all())

            # Пользователи с заполненным полом
            users_with_gender_result = await session.execute(
                select(User).where(User.gender.isnot(None))
            )
            users_with_gender = len(users_with_gender_result.scalars().all())

            # Среднее количество обращений
            avg_requests_result = await session.execute(
                select(func.avg(User.request_count)).where(User.request_count > 0)
            )
            avg_requests = avg_requests_result.scalar() or 0

            return {
                'total_users': total_users,
                'users_with_gender': users_with_gender,
                'gender_fill_rate': round((users_with_gender / total_users * 100) if total_users > 0 else 0, 2),
                'average_requests': round(avg_requests, 2),
                'calculated_at': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики пользователей: {e}")
        return {
            'total_users': 0,
            'users_with_gender': 0,
            'gender_fill_rate': 0,
            'average_requests': 0,
            'error': str(e)
        }


bot:

bot.config.py

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot.handlers.py

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, timedelta
import logging

from backend.assistant import assistant

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()


# Определяем состояния для сбора данных
class DataCollectionStates(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_city = State()
    waiting_for_current_city = State()
    waiting_for_profession = State()
    waiting_for_job_position = State()
    waiting_for_gender = State()


# Состояние для ввода даты
class DateSelectionStates(StatesGroup):
    waiting_for_custom_date = State()


# Основная клавиатура
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Расчет натальной карты")],
            [KeyboardButton(text="📅 Получить данные на сегодня")],
            [KeyboardButton(text="🔮 Получить данные на завтра")],
            [KeyboardButton(text="📋 Статус данных"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )


# Клавиатура для выбора даты
def get_date_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📅 Завтра")],
            [KeyboardButton(text="📅 Выбрать дату")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


# Клавиатура для выбора пола
def get_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👨 Мужской"), KeyboardButton(text="👩 Женский")],
            [KeyboardButton(text="🤷 Не указывать")]
        ],
        resize_keyboard=True
    )


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда начала работы с ботом"""
    welcome_text = """
👋 Добро пожаловать в ваш персональный ассистент Astra!

Я помогу вам получать персонализированные данные на основе:
• 🌟 Натальной карты и астрологических транзитов
• 🔢 Психоматрицы по дате рождения  
• ⚡ Биоритмов на каждый день
• 💼 Вашей профессиональной деятельности

Выберите действие из меню ниже:
    """

    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(lambda message: message.text == "📊 Расчет натальной карты")
async def start_data_collection(message: types.Message, state: FSMContext):
    """Начало сбора данных пользователя"""

    # Проверяем статус данных пользователя
    status = await assistant.get_user_data_status(message.from_user.id)

    if status['is_complete']:
        await message.answer(
            "✅ Ваши основные данные уже собраны!\n"
            "Если хотите обновить профессию или город, используйте соответствующую команду.\n\n"
            "Выберите действие из меню:",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "📊 Начнем сбор данных для персонализированных расчетов!\n\n"
            "Пожалуйста, введите вашу дату рождения в формате ГГГГ-ММ-ДД:\n"
            "Например: 1990-05-15",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_date)


@router.message(DataCollectionStates.waiting_for_birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    """Обработка даты рождения"""
    try:
        birth_date = datetime.strptime(message.text, "%Y-%m-%d").date()

        # Проверяем что дата не в будущем
        if birth_date > date.today():
            await message.answer(
                "❌ Дата рождения не может быть в будущем!\n"
                "Пожалуйста, введите корректную дату в формате ГГГГ-ММ-ДД:"
            )
            return

        await state.update_data(birth_date=birth_date)

        await message.answer(
            "✅ Дата рождения сохранена!\n\n"
            "Теперь введите время рождения в формате ЧЧ:ММ (24 часа):\n"
            "Например: 14:30"
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_time)

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте формат ГГГГ-ММ-ДД:\n"
            "Например: 1990-05-15"
        )


@router.message(DataCollectionStates.waiting_for_birth_time)
async def process_birth_time(message: types.Message, state: FSMContext):
    """Обработка времени рождения"""
    try:
        birth_time = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(birth_time=birth_time)

        await message.answer(
            "✅ Время рождения сохранено!\n\n"
            "Введите город рождения:"
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_city)

    except ValueError:
        await message.answer(
            "❌ Неверный формат времени.\n"
            "Используйте формат ЧЧ:ММ (24 часа):\n"
            "Например: 14:30"
        )


@router.message(DataCollectionStates.waiting_for_birth_city)
async def process_birth_city(message: types.Message, state: FSMContext):
    """Обработка города рождения"""
    birth_city = message.text.strip()

    if len(birth_city) < 2:
        await message.answer(
            "❌ Название города слишком короткое.\n"
            "Пожалуйста, введите корректное название города:"
        )
        return

    await state.update_data(birth_city=birth_city)

    await message.answer(
        "✅ Город рождения сохранен!\n\n"
        "Теперь введите город проживания:"
    )
    await state.set_state(DataCollectionStates.waiting_for_current_city)


@router.message(DataCollectionStates.waiting_for_current_city)
async def process_current_city(message: types.Message, state: FSMContext):
    """Обработка города проживания"""
    current_city = message.text.strip()

    if len(current_city) < 2:
        await message.answer(
            "❌ Название города слишком короткое.\n"
            "Пожалуйста, введите корректное название города:"
        )
        return

    await state.update_data(current_city=current_city)

    await message.answer(
        "✅ Город проживания сохранен!\n\n"
        "Введите вашу специальность или профессию:"
    )
    await state.set_state(DataCollectionStates.waiting_for_profession)


@router.message(DataCollectionStates.waiting_for_profession)
async def process_profession(message: types.Message, state: FSMContext):
    """Обработка профессии"""
    profession = message.text.strip()

    if len(profession) < 2:
        await message.answer(
            "❌ Название профессии слишком короткое.\n"
            "Пожалуйста, введите корректное название профессии:"
        )
        return

    await state.update_data(profession=profession)

    await message.answer(
        "✅ Профессия сохранена!\n\n"
        "Введите вашу должность (если нет - напишите 'нет'):"
    )
    await state.set_state(DataCollectionStates.waiting_for_job_position)


@router.message(DataCollectionStates.waiting_for_job_position)
async def process_job_position(message: types.Message, state: FSMContext):
    """Обработка должности и переход к выбору пола"""
    job_position = message.text.strip()
    if job_position.lower() == 'нет':
        job_position = None

    await state.update_data(job_position=job_position)

    await message.answer(
        "✅ Должность сохранена!\n\n"
        "Укажите ваш пол:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(DataCollectionStates.waiting_for_gender)


@router.message(DataCollectionStates.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    """Обработка пола и завершение сбора данных"""
    gender_map = {
        "👨 Мужской": "male",
        "👩 Женский": "female",
        "🤷 Не указывать": None
    }

    gender_text = message.text.lower()
    gender = None

    # Определяем пол по тексту
    for key, value in gender_map.items():
        if key.lower() in gender_text:
            gender = value
            break

    # Если пол не распознан, используем текст как есть
    if gender is None:
        if any(word in gender_text for word in ["муж", "male", "м"]):
            gender = "male"
        elif any(word in gender_text for word in ["жен", "female", "ж"]):
            gender = "female"
        else:
            gender = None

    await state.update_data(gender=gender)
    user_data = await state.get_data()

    try:
        # Сохраняем все данные через ассистента
        result = await assistant.collect_user_data(
            telegram_id=message.from_user.id,
            birth_date=user_data['birth_date'],
            birth_time=user_data['birth_time'],
            birth_city=user_data['birth_city'],
            current_city=user_data['current_city'],
            profession=user_data['profession'],
            job_position=user_data.get('job_position'),
            gender=gender
        )

        if result['success']:
            await message.answer(
                "🎉 Поздравляем! Все данные успешно собраны!\n\n"
                "Теперь вы можете получать персонализированные расчеты:",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result['message']}\n\n"
                "Попробуйте начать сбор данных заново.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}")
        await message.answer(
            f"❌ Произошла ошибка при сохранении данных: {str(e)}\n\n"
            "Попробуйте начать сбор данных заново.",
            reply_markup=get_main_keyboard()
        )

    await state.clear()


@router.message(lambda message: message.text == "📅 Получить данные на сегодня")
async def get_todays_data(message: types.Message):
    """Получение данных на сегодня"""
    await process_date_selection(message, date.today())


@router.message(lambda message: message.text == "🔮 Получить данные на завтра")
async def get_tomorrows_data(message: types.Message):
    """Получение данных на завтра"""
    tomorrow = date.today() + timedelta(days=1)
    await process_date_selection(message, tomorrow)


@router.message(lambda message: message.text == "📅 Выбрать дату")
async def request_custom_date(message: types.Message, state: FSMContext):
    """Запрос произвольной даты"""
    await message.answer(
        "📅 Введите дату в формате ГГГГ-ММ-ДД:\n"
        "Например: 2024-12-25",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(DateSelectionStates.waiting_for_custom_date)


@router.message(DateSelectionStates.waiting_for_custom_date)
async def process_custom_date(message: types.Message, state: FSMContext):
    """Обработка введенной пользователем даты"""
    try:
        target_date = datetime.strptime(message.text, "%Y-%m-%d").date()

        # Проверяем что дата не в прошлом
        if target_date < date.today():
            await message.answer(
                "❌ Можно получить данные только на сегодня или будущие даты",
                reply_markup=get_date_keyboard()
            )
            return

        await process_date_selection(message, target_date)

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте ГГГГ-ММ-ДД:\n"
            "Например: 2024-12-25",
            reply_markup=get_date_keyboard()
        )

    await state.clear()


@router.message(lambda message: message.text == "🔙 Назад")
async def go_back_to_main(message: types.Message):
    """Возврат в главное меню"""
    await message.answer(
        "Возвращаемся в главное меню:",
        reply_markup=get_main_keyboard()
    )


async def process_date_selection(message: types.Message, target_date: date):
    """Общая обработка выбранной даты"""
    # Проверяем наличие данных пользователя
    status = await assistant.get_user_data_status(message.from_user.id)
    if not status['is_complete']:
        await message.answer(
            "❌ Сначала необходимо собрать данные!\n"
            "Нажмите '📊 Расчет натальной карты' для сбора данных",
            reply_markup=get_main_keyboard()
        )
        return

    processing_msg = await message.answer(
        f"🔄 Формирую расчеты на {target_date.strftime('%d.%m.%Y')}...\n"
        "Это может занять несколько секунд"
    )

    try:
        result = await assistant.get_recommendations(message.from_user.id, target_date)

        if result['success']:
            # Отправляем пользователю форматированные данные
            await message.answer(result['user_data'], parse_mode="Markdown")

            # Дополнительная информация
            additional_info = (
                f"\n📊 *Расчеты на {target_date.strftime('%d.%m.%Y')} готовы!*\n\n"
                "💡 *Используйте эти данные для:*\n"
                "• Планирования важных дел\n"
                "• Оптимизации рабочего графика\n"
                "• Принятия взвешенных решений\n"
                "• Поддержания энергетического баланса\n\n"
                "Выберите следующее действие из меню 👇"
            )

            await message.answer(
                additional_info,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result['message']}",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка получения данных на сегодня: {e}")
        await message.answer(
            "❌ Произошла ошибка при формировании расчетов\n"
            "Попробуйте позже или обратитесь в поддержку.",
            reply_markup=get_main_keyboard()
        )

    await processing_msg.delete()


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Проверка статуса данных пользователя"""
    try:
        status = await assistant.get_user_data_status(message.from_user.id)

        status_text = "📊 **Статус ваших данных:**\n\n"

        if status['is_complete']:
            status_text += "✅ Все данные собраны и готовы к использованию\n\n"
        else:
            status_text += "❌ Не все данные собраны\n\n"

        status_text += f"• Основные данные: {'✅' if status['has_basic_data'] else '❌'}\n"
        status_text += f"• Натальная карта: {'✅' if status['has_natal_chart'] else '❌'}\n"
        status_text += f"• Психоматрица: {'✅' if status['has_psyho_matrix'] else '❌'}\n"
        status_text += f"• Биоритмы: {'✅' if status['has_biorhythms'] else '❌'}\n\n"

        if status['is_complete']:
            # Показываем статистику если данные есть
            stats = await assistant.get_user_statistics(message.from_user.id)
            if stats.get('request_count', 0) > 0:
                status_text += f"📈 **Статистика:**\n"
                status_text += f"• Запросов расчетов: {stats['request_count']}\n"

                if stats.get('prediction_stats', {}).get('total_calculations', 0) > 0:
                    status_text += f"• Всего расчетов: {stats['prediction_stats']['total_calculations']}\n"

                if stats.get('biorhythm_stats', {}).get('total_records', 0) > 0:
                    status_text += f"• Записей биоритмов: {stats['biorhythm_stats']['total_records']}\n"

        if not status['is_complete']:
            status_text += "Нажмите '📊 Расчет натальной карты' для сбора недостающих данных"

        await message.answer(status_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await message.answer(
            "❌ Не удалось проверить статус данных",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам бота"""
    help_text = """
📋 **Доступные команды:**

/start - Начать работу с ботом
/status - Проверить статус ваших данных  
/help - Показать эту справку

**Основные действия:**

📊 Расчет натальной карты - Собрать или обновить ваши данные
📅 Получить данные на сегодня - Расчеты на текущий день
🔮 Получить данные на завтра - Расчеты на следующий день

**Что рассчитывается:**
• ⚡ Биоритмы (физический, эмоциональный, интеллектуальный)
• 🌟 Астрологические транзиты и аспекты  
• 🔢 Нумерологическая психоматрица
• 💼 Профессиональные рекомендации

**Как использовать:**
1. Сначала соберите данные через '📊 Расчет натальной карты'
2. Получайте ежедневные расчеты через меню
3. Используйте данные для планирования своего дня

Все расчеты выполняются на основе научных методов и проверенных алгоритмов.
    """

    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Показать детальную статистику"""
    try:
        stats = await assistant.get_user_statistics(message.from_user.id)

        stats_text = "📈 **Детальная статистика:**\n\n"

        # Основная статистика
        stats_text += f"• Запросов расчетов: {stats.get('request_count', 0)}\n"

        # Статистика расчетов
        prediction_stats = stats.get('prediction_stats', {})
        if prediction_stats:
            stats_text += f"• Всего расчетов: {prediction_stats.get('total_calculations', 0)}\n"
            if prediction_stats.get('first_calculation_date'):
                stats_text += f"• Первый расчет: {prediction_stats['first_calculation_date'][:10]}\n"
            if prediction_stats.get('latest_energy_level', 0) > 0:
                stats_text += f"• Последняя энергия: {prediction_stats['latest_energy_level']}%\n"

        # Статистика биоритмов
        biorhythm_stats = stats.get('biorhythm_stats', {})
        if biorhythm_stats:
            stats_text += f"• Записей биоритмов: {biorhythm_stats.get('total_records', 0)}\n"
            if biorhythm_stats.get('average_energy_level', 0) > 0:
                stats_text += f"• Средняя энергия: {biorhythm_stats['average_energy_level']}%\n"

        stats_text += f"\n📅 Статистика обновлена: {stats.get('calculated_at', '')[:16]}"

        await message.answer(stats_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer(
            "❌ Не удалось получить статистику",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("cleanup"))
async def cmd_cleanup(message: types.Message):
    """Очистка данных пользователя (только для отладки)"""
    try:
        # Проверяем что пользователь существует
        status = await assistant.get_user_data_status(message.from_user.id)
        if not status['has_basic_data']:
            await message.answer(
                "❌ У вас нет данных для очистки",
                reply_markup=get_main_keyboard()
            )
            return

        # Запрашиваем подтверждение
        confirm_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Да, очистить"), KeyboardButton(text="❌ Нет, отменить")],
            ],
            resize_keyboard=True
        )

        await message.answer(
            "⚠️ **Внимание!**\n\n"
            "Вы собираетесь очистить все ваши данные:\n"
            "• Профиль пользователя\n"
            "• Натальную карту\n"
            "• Психоматрицу\n"
            "• Историю расчетов\n\n"
            "Это действие нельзя отменить!\n"
            "Вы уверены что хотите продолжить?",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка подготовки очистки: {e}")
        await message.answer(
            "❌ Ошибка подготовки очистки",
            reply_markup=get_main_keyboard()
        )


@router.message(lambda message: message.text == "✅ Да, очистить")
async def confirm_cleanup(message: types.Message):
    """Подтверждение очистки данных"""
    try:
        result = await assistant.cleanup_user_data(message.from_user.id)

        if result['success']:
            await message.answer(
                "🧹 Все ваши данные успешно очищены!\n\n"
                "Вы можете начать заново с команды /start",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result['message']}",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка очистки данных: {e}")
        await message.answer(
            "❌ Произошла ошибка при очистке данных",
            reply_markup=get_main_keyboard()
        )


@router.message(lambda message: message.text == "❌ Нет, отменить")
async def cancel_cleanup(message: types.Message):
    """Отмена очистки данных"""
    await message.answer(
        "✅ Очистка данных отменена",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("validate"))
async def cmd_validate(message: types.Message):
    """Проверка корректности данных"""
    try:
        validation = await assistant.validate_user_data(message.from_user.id)

        if validation['is_valid']:
            await message.answer(
                "✅ Все данные корректны и готовы к использованию!",
                reply_markup=get_main_keyboard()
            )
        else:
            issues_text = "❌ Обнаружены проблемы в данных:\n\n"
            for issue in validation['issues']:
                issues_text += f"• {issue}\n"

            issues_text += "\nИспользуйте '📊 Расчет натальной карты' для исправления"

            await message.answer(
                issues_text,
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка валидации данных: {e}")
        await message.answer(
            "❌ Не удалось проверить данные",
            reply_markup=get_main_keyboard()
        )


@router.message()
async def handle_other_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    # Проверяем если это текстовая команда
    text = message.text.lower()

    if any(word in text for word in ['привет', 'hello', 'start', 'начать']):
        await cmd_start(message)
    elif any(word in text for word in ['статус', 'status', 'данные']):
        await cmd_status(message)
    elif any(word in text for word in ['помощь', 'help', 'команды']):
        await cmd_help(message)
    else:
        await message.answer(
            "🤔 Я не понял ваше сообщение.\n\n"
            "Используйте меню ниже или команду /help для справки:",
            reply_markup=get_main_keyboard()
        )

bot.__init__.py

bot.main.py

from aiogram import Bot, Dispatcher
import asyncio
import logging

from bot.config import TOKEN
from bot.handlers import router
from backend.db_connection import check_db_connection

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def setup_bot() -> tuple[Bot, Dispatcher]:
    """
    Инициализация и настройка бота
    Returns:
        Кортеж (Bot, Dispatcher)
    """
    try:
        bot = Bot(token=TOKEN)
        dp = Dispatcher()

        # Подключаем роутер
        dp.include_router(router)

        logger.info("✅ Бот инициализирован успешно")
        return bot, dp

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        raise


async def health_checks() -> bool:
    """
    Проверка здоровья всех зависимостей
    Returns:
        bool: True если все проверки пройдены
    """
    checks_passed = True

    # Проверка базы данных
    logger.info("🔍 Проверка подключения к базе данных...")
    db_connected = await check_db_connection()
    if not db_connected:
        logger.error("❌ Не удалось подключиться к базе данных")
        checks_passed = False
    else:
        logger.info("✅ База данных подключена успешно")

    # Здесь можно добавить проверки других сервисов
    # - Проверка подключения к Ollama
    # - Проверка доступности эфемерид
    # - Проверка дискового пространства

    return checks_passed


async def start_polling(bot: Bot, dp: Dispatcher):
    """
    Запуск поллинга бота с обработкой ошибок
    """
    try:
        logger.info("🔄 Запуск поллинга бота...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при работе бота: {e}")
        raise

    finally:
        logger.info("🛑 Завершение работы бота...")


async def graceful_shutdown(bot: Bot):
    """
    Корректное завершение работы бота
    """
    try:
        await bot.close()
        logger.info("✅ Бот корректно остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")


async def main():
    """
    Главная функция запуска приложения
    """
    bot = None
    try:
        logger.info("🚀 Запуск Personal Assistant...")

        # Проверка здоровья системы
        if not await health_checks():
            logger.error("❌ Проверки здоровья не пройдены. Завершение работы.")
            return

        # Инициализация бота
        bot, dp = await setup_bot()

        logger.info("""
✅ Personal Assistant успешно запущен!

📊 Статус системы:
• База данных: ✅ подключена
• Telegram Bot: ✅ инициализирован
• Обработчики: ✅ загружены
• Готов к работе!
        """)

        # Запуск поллинга
        await start_polling(bot, dp)

    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал прерывания (Ctrl+C)")

    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка в главном процессе: {e}")

    finally:
        # Корректное завершение
        if bot:
            await graceful_shutdown(bot)

        logger.info("👋 Personal Assistant завершил работу")


if __name__ == "__main__":
    # Запуск асинхронного приложения
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Демон остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

bot..env

TELEGRAM_BOT_TOKEN = 7900025353:AAE4PznooxoJazUuQihtPspWG41ylwo9SEk



ephe

init-scripts:

init-scripts.01-init-tables.sql

-- Инициализация оптимизированной схемы БД для проекта Astra

-- Таблица пользователей (без изменений)
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    birth_city VARCHAR(100) NOT NULL,
    profession VARCHAR(100),
    job_position VARCHAR(100),
    current_city VARCHAR(100),
    gender VARCHAR(10),
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица натальных карт (переименована для ясности)
CREATE TABLE IF NOT EXISTS user_astro_profile (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_chart_data JSONB NOT NULL,
    psyho_matrix_data JSONB NOT NULL,
    dominant_energy VARCHAR(50),
    personality_traits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- УДАЛЕНА: Таблица психоматриц (данные перенесены в user_astro_profile)

-- ОПТИМИЗИРОВАННАЯ: Таблица ежедневных расчетов (вместо natal_predictions)
CREATE TABLE IF NOT EXISTS daily_calculations (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    biorhythm_data JSONB NOT NULL,
    astro_transits_data JSONB NOT NULL,
    calculation_metadata JSONB NOT NULL DEFAULT '{}',
    data_hash VARCHAR(64) NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date)
);

-- Таблица биоритмов (сохранена для обратной совместимости)
CREATE TABLE IF NOT EXISTS biorhythms (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, calculation_date)
);

-- НОВАЯ: Таблица кэша расчетов для производительности
CREATE TABLE IF NOT EXISTS calculation_cache (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    calculation_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date, data_type)
);

-- УДАЛЕНЫ: Таблицы AI рекомендаций и астрологических инсайтов
-- DROP TABLE IF EXISTS ai_recommendations;
-- DROP TABLE IF EXISTS astro_insights;

-- ОПТИМИЗИРОВАННЫЕ ИНДЕКСЫ:

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date);
CREATE INDEX IF NOT EXISTS idx_users_profession ON users(profession);
CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);

-- Индексы для астропрофиля
CREATE INDEX IF NOT EXISTS idx_astro_profile_telegram_id ON user_astro_profile(telegram_id);

-- ВЫСОКОЭФФЕКТИВНЫЕ индексы для daily_calculations
CREATE INDEX IF NOT EXISTS idx_daily_calc_target_date ON daily_calculations(target_date);
CREATE INDEX IF NOT EXISTS idx_daily_calc_telegram_date ON daily_calculations(telegram_id, target_date);
CREATE INDEX IF NOT EXISTS idx_daily_calc_hash ON daily_calculations(data_hash);
CREATE INDEX IF NOT EXISTS idx_daily_calc_timestamp ON daily_calculations(calculation_timestamp);

-- Индексы для биоритмов
CREATE INDEX IF NOT EXISTS idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX IF NOT EXISTS idx_biorhythms_calculation_date ON biorhythms(calculation_date);
CREATE INDEX IF NOT EXISTS idx_biorhythms_composite ON biorhythms(telegram_id, calculation_date);

-- Индексы для кэша
CREATE INDEX IF NOT EXISTS idx_cache_telegram_date ON calculation_cache(telegram_id, target_date);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON calculation_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_type ON calculation_cache(data_type);

-- Права для пользователя
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pers_assist;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Основная таблица пользователей проекта Astra';
COMMENT ON TABLE user_astro_profile IS 'Статические астрологические данные пользователя (натальная карта + психоматрица)';
COMMENT ON TABLE daily_calculations IS 'Ежедневные расчеты для конкретных дат (биоритмы + транзиты)';
COMMENT ON TABLE biorhythms IS 'Исторические данные биоритмов (для обратной совместимости)';
COMMENT ON TABLE calculation_cache IS 'Кэш расчетов для оптимизации производительности';

-- Миграция данных из старых таблиц (если существуют)
DO $$ 
BEGIN
    -- Миграция натальных карт
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_natal_charts') THEN
        INSERT INTO user_astro_profile (telegram_id, natal_chart_data, psyho_matrix_data)
        SELECT 
            unc.telegram_id,
            unc.natal_data as natal_chart_data,
            COALESCE(pm.matrix_data, '{}'::JSONB) as psyho_matrix_data
        FROM user_natal_charts unc
        LEFT JOIN psyho_matrix pm ON unc.telegram_id = pm.telegram_id
        ON CONFLICT (telegram_id) DO NOTHING;
        
        RAISE NOTICE '✅ Данные натальных карт и психоматриц мигрированы в user_astro_profile';
    END IF;

    -- Миграция предсказаний в daily_calculations
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'natal_predictions') THEN
        INSERT INTO daily_calculations (telegram_id, target_date, biorhythm_data, astro_transits_data, data_hash)
        SELECT 
            np.telegram_id,
            (np.predictions->>'target_date')::DATE as target_date,
            COALESCE(np.predictions->'daily_calculations'->'biorhythm_data', '{}'::JSONB) as biorhythm_data,
            COALESCE(np.predictions->'daily_calculations'->'astro_data', '{}'::JSONB) as astro_transits_data,
            COALESCE(np.data_hash, md5(np.predictions::text)) as data_hash
        FROM natal_predictions np
        WHERE np.predictions ? 'target_date'
        ON CONFLICT (telegram_id, target_date) DO NOTHING;
        
        RAISE NOTICE '✅ Данные предсказаний мигрированы в daily_calculations';
    END IF;

EXCEPTION
    WHEN others THEN
        RAISE NOTICE '⚠️ Миграция данных пропущена: %', SQLERRM;
END $$;

-- Удаление старых таблиц после успешной миграции
DROP TABLE IF EXISTS psyho_matrix CASCADE;
DROP TABLE IF EXISTS user_natal_charts CASCADE;
DROP TABLE IF EXISTS natal_predictions CASCADE;
DROP TABLE IF EXISTS ai_recommendations CASCADE;
DROP TABLE IF EXISTS astro_insights CASCADE;

-- Логирование успешной инициализации
DO $$ 
BEGIN
    RAISE NOTICE '🎉 База данных Astra успешно инициализирована с оптимизированной схемой';
    RAISE NOTICE '📊 Таблицы: users, user_astro_profile, daily_calculations, biorhythms, calculation_cache';
    RAISE NOTICE '⚡ Индексы оптимизированы для быстрых запросов по датам';
END $$;




docker-compose.override.yml

version: '3.8'

services:
  postgres:
    environment:
      - POSTGRES_HOST_AUTH_METHOD=trust
    ports:
      - "5432:5432"
    volumes:
      - ./init-scripts:/docker-entrypoint-initdb.d:ro

  astra_api:
    build:
      context: .
      dockerfile: Dockerfile.api.dev
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    volumes:
      - .:/app
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    command: >
      sh -c "python -m uvicorn backend.api_entrypoint:app 
             --host 0.0.0.0 
             --port 8000 
             --reload 
             --log-level debug"

  astra_bot:
    build:
      context: .
      dockerfile: Dockerfile.bot.dev
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
      - ./logs:/app/logs
    command: >
      sh -c "python -m bot.main --debug"

  pgadmin:
    profiles: ["admin-tools", "default"]


docker-compose.yml

services:
  postgres:
    image: postgres:16
    container_name: postgres_astra
    environment:
      POSTGRES_DB: astra_db
      POSTGRES_USER: astra_user
      POSTGRES_PASSWORD: astra_password_2024
    ports:
      - "5435:5432"  # Пробуем порт 5435
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts/01-init-tables.sql:/docker-entrypoint-initdb.d/01-init-tables.sql
    restart: unless-stopped

  astra_bot:
    build:
      context: .
      dockerfile: Dockerfile.bot
    container_name: astra_bot
    environment:
      - DATABASE_URL=postgresql+asyncpg://astra_user:astra_password_2024@postgres:5432/astra_db
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:


Dockerfile.api.dev

FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY backend/ ./backend/
COPY ephe/ ./ephe/

# Создание директории для логов
RUN mkdir -p /app/logs

# Порт приложения
EXPOSE 8000

# Запуск приложения
CMD ["python", "-m", "uvicorn", "backend.api_entrypoint:app", "--host", "0.0.0.0", "--port", "8000"]


Dockerfile.bot.dev

FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY backend/ ./backend/
COPY bot/ ./bot/
COPY ephe/ ./ephe/

# Создание директории для логов
RUN mkdir -p /app/logs

# Запуск бота
CMD ["python", "-m", "bot.main"]

requirements.txt

.env

# Telegram Bot Token
TELEGRAM_BOT_TOKEN='7900025353:AAE4PznooxoJazUuQihtPspWG41ylwo9SEk'

# Database Configuration
DATABASE_URL=postgresql+asyncpg://astra_user:astra_password_2024@localhost:5432/astra_db

# API Configuration
API_BASE_URL=http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Redis (опционально)
REDIS_URL=redis://:redis_astra_2024@localhost:6379/0

# Ephemeris Data
EPHE_PATH=/app/ephe















