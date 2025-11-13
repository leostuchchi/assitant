проект personal_assistant

итоговая задача проекта: 
персонализированные основанные на расчетах и данных, рекоммендации человеку на один день. для развития, самореализации человека на базе модели ИИ.



логика проекта:
сбор данных пользователя (tegram bot)
подготовка натальной карты
подготовка психоматрицы
расчет биоритмов
подготовка рекоммендаций на один день, на основе: натальной карты, психоматрицы, биоритмов
вывод рекоммендаций на один день пользователю (telegram bot)

текущая задача проекта: 
## 🔧 **3. МОДУЛИ, ЗАТРОНУТЫЕ ИЗМЕНЕНИЯМИ**

### **🔴 ТРЕБУЮТ ИЗМЕНЕНИЙ:**

1. **`backend/database.py`** - новые модели и связи
2. **`backend/assistant.py`** - интеграция AI движка
3. **`backend/prediction_services.py`** - подготовка данных для AI
4. **`bot/handlers.py`** - вывод AI рекомендаций
5. **`docker-compose.yml`** - добавление Ollama сервиса

### **🟢 НОВЫЕ МОДУЛИ:**

1. **`backend/ai_engine.py`** - работа с Ollama API
2. **`backend/astro_interpreter.py`** - пре-обработка астроданных
3. **`backend/prompt_builder.py`** - построение оптимизированных промптов
4. **`backend/recommendation_cache.py`** - управление кэшем рекомендаций
5. **`backend/data_optimizer.py`** - сжатие и оптимизация данных

## ⚖️ **4. ВЛИЯНИЕ НА СЛОЖНОСТЬ ПРОЕКТА**

### **🟢 УПРОЩЕНИЕ:**
- **Более чистые интерфейсы** - модули общаются через стандартизированные форматы
- **Улучшенная обработка ошибок** - изоляция AI компонентов
- **Легче тестировать** - моки для AI вызовов
- **Предсказуемая производительность** - кэширование стабилизирует отклик

### **🔴 УСЛОЖНЕНИЕ:**
- **Увеличивается количество модулей** +5 новых файлов
- **Новые зависимости** - асинхронные HTTP запросы, хэширование
- **Сложнее дебажить** - распределенная логика между модулями
- **Требует мониторинга** - здоровье Ollama, использование памяти

### **⚖️ БАЛАНС:**
**ЧИСТЫЙ ВЫИГРЫШ** - архитектура становится более масштабируемой и поддерживаемой, несмотря на увеличение количества компонентов.

## 🏗️ **5. ИТОГОВАЯ СТРУКТУРА ПРОЕКТА**

```
personal_assistant/
├── 📁 bot/
│   ├── config.py                          # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── handlers.py                        # 🔴 ИЗМЕНИТЬ - вывод AI рекомендаций
│   ├── main.py                            # ✅ БЕЗ ИЗМЕНЕНИЙ  
│   └── __init__.py
├── 📁 backend/
│   ├── 🆕 ai_engine.py                    # 🟢 НОВЫЙ - работа с Ollama API
│   ├── 🆕 astro_interpreter.py            # 🟢 НОВЫЙ - пре-обработка астроданных
│   ├── 🆕 prompt_builder.py               # 🟢 НОВЫЙ - построение промптов
│   ├── 🆕 recommendation_cache.py         # 🟢 НОВЫЙ - управление кэшем
│   ├── 🆕 data_optimizer.py               # 🟢 НОВЫЙ - сжатие данных для AI
│   ├── assistant.py                       # 🔴 ИЗМЕНИТЬ - интеграция AI движка
│   ├── prediction_services.py             # 🔴 ИЗМЕНИТЬ - подготовка для AI
│   ├── database.py                        # 🔴 ИЗМЕНИТЬ - новые модели БД
│   ├── biorhythm_calculator.py            # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── biorhythm_services.py              # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── chart_services.py                  # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── matrix_services.py                 # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── natal_chart.py                     # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── predictions.py                     # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── psyho_matrix.py                    # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── user_services.py                   # ✅ БЕЗ ИЗМЕНЕНИЙ
│   ├── db_connection.py                   # ✅ БЕЗ ИЗМЕНЕНИЙ
│   └── __init__.py
├── 📁 ollama/
│   └── docker-compose.yml                 # 🔴 ИЗМЕНИТЬ - добавить сети
├── docker-compose.yml                     # 🔴 ИЗМЕНИТЬ - добавить Ollama
└── requirements.txt                       # 🔴 ИЗМЕНИТЬ - новые зависимости
```


структура проекта personal_assistant:

docker-compose.yml

bot: 
config.py
handlers.py
__init__.py
main.py

backend: 
__init__.py
assistant.py
biorhythm_calculator.py
biorhythm_services.py
chart_services.py
database.py
db_connection.py
matrix_services.py
moon.py
natal_chart.py
predictions.py
prediction_services.py
psyho_matrix.py
user_services.py

ollama:
docker-compose.yml:
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama_assistant
    ports:
      - "11435:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_NUM_GPU=0                    # Отключаем GPU
      - OLLAMA_CPU_COUNT=4                  # Используем 4 CPU ядра
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 15s
      retries: 5
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 8G                        # 8GB для CPU-режима
          cpus: "4.0"                       # 4 CPU ядра
        reservations:
          memory: 6G
          cpus: "3.0"

volumes:
  ollama_data:
    driver: local

networks:
  assistant_net:
    name: personal_assistant_network
    external: true

init-scripts.01-init-tables.sql

-- Инициализация таблиц при первом запуске контейнера

-- Таблица пользователей
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

-- Таблица натальных карт
CREATE TABLE IF NOT EXISTS user_natal_charts (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица психоматриц
CREATE TABLE IF NOT EXISTS psyho_matrix (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    matrix_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предсказаний
CREATE TABLE IF NOT EXISTS natal_predictions (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    predictions JSONB NOT NULL,
    assistant_data JSONB NOT NULL DEFAULT '{}',
    data_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица биоритмов
CREATE TABLE IF NOT EXISTS biorhythms (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, calculation_date)
);

-- НОВЫЕ ТАБЛИЦЫ ДЛЯ AI РЕКОМЕНДАЦИЙ:

-- Таблица для кэширования AI рекомендаций
CREATE TABLE IF NOT EXISTS ai_recommendations (
    telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_date DATE NOT NULL,
    data_hash VARCHAR(64) NOT NULL,
    recommendations TEXT NOT NULL,
    model_version VARCHAR(20) DEFAULT 'gemma:2b',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, target_date)
);

-- Таблица для пре-обработанных астрологических инсайтов
CREATE TABLE IF NOT EXISTS astro_insights (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    dominant_energy JSONB NOT NULL,
    personality_traits JSONB NOT NULL,
    planetary_strengths JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ:

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date);
CREATE INDEX IF NOT EXISTS idx_users_profession ON users(profession);

-- Индексы для натальных карт
CREATE INDEX IF NOT EXISTS idx_user_natal_charts_telegram_id ON user_natal_charts(telegram_id);

-- Индексы для психоматриц
CREATE INDEX IF NOT EXISTS idx_psyho_matrix_telegram_id ON psyho_matrix(telegram_id);

-- Индексы для предсказаний
CREATE INDEX IF NOT EXISTS idx_natal_predictions_telegram_id ON natal_predictions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_natal_predictions_hash ON natal_predictions(data_hash);

-- Индексы для биоритмов
CREATE INDEX IF NOT EXISTS idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX IF NOT EXISTS idx_biorhythms_calculation_date ON biorhythms(calculation_date);

-- Индексы для AI рекомендаций
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_hash ON ai_recommendations(data_hash);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_date ON ai_recommendations(target_date);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_created ON ai_recommendations(created_at);

-- Права для пользователя
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pers_assist;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Основная таблица пользователей персонального ассистента';
COMMENT ON TABLE ai_recommendations IS 'Кэш AI рекомендаций от модели Llama';
COMMENT ON TABLE astro_insights IS 'Пре-обработанные астрологические инсайты для AI';

-- Логирование успешной инициализации
DO $$ 
BEGIN
    RAISE NOTICE '✅ База данных personal_assistant успешно инициализирована';
END $$;




   

docker-compose.yml:
services:
  postgres:
    image: postgres:16
    container_name: postgres_astrology
    environment:
      POSTGRES_DB: p_assistant_bd
      POSTGRES_USER: pers_assist
      POSTGRES_PASSWORD: astra123
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C --lc-ctype=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pers_assist -d p_assistant_bd"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # ОПЦИОНАЛЬНО: pgAdmin для управления БД
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: pgadmin_astrology
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@astrology.local
      PGADMIN_DEFAULT_PASSWORD: admin123
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "8080:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    profiles:
      - admin-tools

volumes:
  postgres_data:
    driver: local
  pgadmin_data:
    driver: local

networks:
  assistant_net:
    driver: bridge
  
модули проекта:

bot: 

config.py:

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

handlers.py:

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
    waiting_for_gender = State()  # НОВОЕ СОСТОЯНИЕ


# Состояние для ввода даты
class DateSelectionStates(StatesGroup):
    waiting_for_custom_date = State()


# Основная клавиатура
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Расчет натальной карты")],
            [KeyboardButton(text="📅 Получить данные")],
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
👋 Добро пожаловать в ваш персональный ассистент!

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
            "Если хотите обновить профессию или город, используйте соответствующую команду.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "📊 Начнем сбор данных для персонализированных данных!\n\n"
            "Пожалуйста, введите вашу дату рождения в формате ГГГГ-ММ-ДД:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_date)


@router.message(DataCollectionStates.waiting_for_birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    """Обработка даты рождения"""
    try:
        birth_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(birth_date=birth_date)

        await message.answer(
            "✅ Дата рождения сохранена!\n\n"
            "Теперь введите время рождения в формате ЧЧ:ММ (24 часа):"
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_time)

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте формат ГГГГ-ММ-ДД:")


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
        await message.answer("❌ Неверный формат времени. Используйте формат ЧЧ:ММ:")


@router.message(DataCollectionStates.waiting_for_birth_city)
async def process_birth_city(message: types.Message, state: FSMContext):
    """Обработка города рождения"""
    birth_city = message.text.strip()
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
        "👨 мужской": "male",
        "👩 женский": "female",
        "🤷 не указывать": None
    }

    gender_text = message.text.lower()
    gender = None

    # Определяем пол по тексту
    for key, value in gender_map.items():
        if key in gender_text:
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
            gender=gender  # ПЕРЕДАЕМ ПОЛ
        )

        if result['success']:
            await message.answer(
                "🎉 Поздравляем! Все данные успешно собраны!\n\n"
                "Теперь вы можете получать персонализированные данные:",
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


@router.message(lambda message: message.text == "📅 Получить данные")
async def select_date_option(message: types.Message):
    """Выбор даты для получения данных"""
    # Проверяем наличие данных
    status = await assistant.get_user_data_status(message.from_user.id)
    if not status['is_complete']:
        await message.answer(
            "❌ Сначала необходимо собрать данные!\n"
            "Нажмите '📊 Расчет натальной карты'",
            reply_markup=get_main_keyboard()
        )
        return

    await message.answer(
        "📅 Выберите дату для расчетов:",
        reply_markup=get_date_keyboard()
    )


@router.message(lambda message: message.text == "📅 Сегодня")
async def get_todays_data(message: types.Message):
    """Получение данных на сегодня"""
    await process_date_selection(message, date.today())


@router.message(lambda message: message.text == "📅 Завтра")
async def get_tomorrows_data(message: types.Message):
    """Получение данных на завтра"""
    tomorrow = date.today() + timedelta(days=1)
    await process_date_selection(message, tomorrow)


@router.message(lambda message: message.text == "📅 Выбрать дату")
async def request_custom_date(message: types.Message, state: FSMContext):
    """Запрос произвольной даты"""
    await message.answer(
        "Введите дату в формате ГГГГ-ММ-ДД:",
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
            "❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД",
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
    processing_msg = await message.answer(f"🔄 Формирую данные на {target_date.strftime('%d.%m.%Y')}...")

    try:
        result = await assistant.get_recommendations(message.from_user.id, target_date)

        if result['success']:
            # Отправляем пользователю форматированные данные
            await message.answer(result['user_data'], parse_mode="Markdown")

            # Данные для модели уже выводятся через print в assistant.py
            await message.answer(
                f"🤖 *Данные на {target_date.strftime('%d.%m.%Y')} отправлены в AI модель*\n"
                "Результаты будут доступны в ближайшее время!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                result['message'],
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка получения данных на сегодня: {e}")
        await message.answer(
            "❌ Произошла ошибка при формировании данных\n"
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

        if not status['is_complete']:
            status_text += "Нажмите '📊 Расчет натальной карты' для сбора недостающих данных"

        await message.answer(status_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await message.answer("❌ Не удалось проверить статус данных")


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
📅 Получить данные - Получить расчеты на выбранную дату

**Выбор даты:**
• 📅 Сегодня - данные на текущий день
• 📅 Завтра - данные на следующий день  
• 📅 Выбрать дату - произвольная дата (ГГГГ-ММ-ДД)

**Что рассчитывается:**
• Астрологические транзиты и аспекты
• Биоритмы (физический, эмоциональный, интеллектуальный)
• Нумерологическая психоматрица
• Все данные передаются в AI модель для формирования персонализированных рекомендаций
    """

    await message.answer(help_text, parse_mode="Markdown")


@router.message()
async def handle_other_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    await message.answer(
        "Выберите действие из меню ниже:",
        reply_markup=get_main_keyboard()
    )


__init__.py:
"""
Пакет бота Personal Assistant
"""

__version__ = "1.0.0"
__author__ = "Personal Assistant Team"

from bot.main import main

__all__ = ['main']

main.py:

from aiogram import Bot, Dispatcher
import asyncio
import logging

from bot.config import TOKEN
from bot.handlers import router
from backend.db_connection import check_db_connection
import math
from datetime import date, datetime
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

            # Рекомендации на основе биоритмов
            recommendations = self._generate_recommendations(physical, emotional, intellectual, intuitive,
                                                             overall_energy)

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
                'recommendations': recommendations,
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

        # Определяем уровень энергии
        if energy_percentage >= 80:
            level = "очень высокий"
            description = "Отличный день для активных действий и важных решений"
        elif energy_percentage >= 60:
            level = "высокий"
            description = "Хороший день для продуктивной работы"
        elif energy_percentage >= 40:
            level = "средний"
            description = "Стабильный день, подходит для рутинных задач"
        elif energy_percentage >= 20:
            level = "низкий"
            description = "День для отдыха и восстановления сил"
        else:
            level = "очень низкий"
            description = "Рекомендуется беречь энергию, избегать нагрузок"

        return {
            'value': round(total_energy, 4),
            'percentage': round(energy_percentage, 2),
            'level': level,
            'description': description
        }

    def _generate_recommendations(self, physical: Dict, emotional: Dict, intellectual: Dict, intuitive: Dict,
                                  overall: Dict) -> List[str]:
        """Генерация рекомендаций на основе биоритмов"""
        recommendations = []

        # Физические рекомендации
        if physical['value'] > 0.5:
            recommendations.append("💪 Идеальный день для спорта и физической активности")
        elif physical['value'] < -0.5:
            recommendations.append("🛌 Избегайте тяжелых физических нагрузок")

        # Эмоциональные рекомендации
        if emotional['value'] > 0.6:
            recommendations.append("😊 Отличное время для общения и новых знакомств")
        elif emotional['value'] < -0.4:
            recommendations.append("🧘 Контролируйте эмоции, избегайте конфликтов")

        # Интеллектуальные рекомендации
        if intellectual['value'] > 0.5:
            recommendations.append("📚 Благоприятный период для обучения и анализа")
        elif intellectual['value'] < -0.3:
            recommendations.append("📝 Отложите сложные интеллектуальные задачи")

        # Интуитивные рекомендации
        if intuitive['value'] > 0.4:
            recommendations.append("🔮 Доверяйте интуиции при принятии решений")

        # Общие рекомендации по энергии
        if overall['percentage'] > 70:
            recommendations.append("🚀 Используйте высокую энергию для важных проектов")
        elif overall['percentage'] < 30:
            recommendations.append("⚡ Экономьте силы, планируйте короткие перерывы")

        # Если рекомендаций мало, добавляем общие
        if len(recommendations) < 3:
            recommendations.extend([
                "📅 Следуйте своему естественному ритму",
                "⏰ Планируйте задачи в соответствии с энергетическими пиками",
                "💧 Пейте足够 воды для поддержания энергии"
            ])

        return recommendations[:5]  # Не более 5 рекомендаций

    def _find_critical_days(self, physical: Dict, emotional: Dict, intellectual: Dict, target_date: date) -> List[Dict]:
        """Определение критических дней (ближайшие 7 дней)"""
        critical_days = []

        # Проверяем текущий день
        if (abs(physical['value']) > 0.9 or
                abs(emotional['value']) > 0.9 or
                abs(intellectual['value']) > 0.9):
            critical_days.append({
                'date': target_date.isoformat(),
                'cycles': self._get_critical_cycles(physical, emotional, intellectual),
                'description': 'Критический день - будьте осторожны'
            })

        return critical_days

    def _find_peak_days(self, physical: Dict, emotional: Dict, intellectual: Dict, target_date: date) -> List[Dict]:
        """Определение пиковых дней (ближайшие 7 дней)"""
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
                'cycles': peak_cycles,
                'description': f'Пик энергии в циклах: {", ".join(peak_cycles)}'
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


async def main():
    try:
        # Проверяем подключение к БД перед запуском
        logger.info("🔍 Проверка подключения к базе данных...")
        db_connected = await check_db_connection()

        if not db_connected:
            logger.error("❌ Не удалось подключиться к базе данных. Завершение работы.")
            return

        bot = Bot(token=TOKEN)
        dp = Dispatcher()

        # Подключаем роутер
        dp.include_router(router)

        logger.info("✅ Бот запущен и готов к работе...")
        logger.info("✅ База данных подключена успешно")
        logger.info("✅ Personal Assistant инициализирован")

        # Запускаем поллинг
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        if 'bot' in locals():
            await bot.close()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())


backend: 

__init__.py

from backend.user_services import create_or_update_user, get_user_profile, update_user_profession, \
    increment_request_count
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_user_predictions, \
    format_data_for_user, format_data_for_model
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
from backend.moon import calculate_lunar_phase
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления всеми данными с AI интеграцией"""

    def __init__(self):
        self.ai_engine = None
        self._ai_engine_initialized = False

    async def _initialize_ai_engine(self):
        """Ленивая инициализация AI движка"""
        if not self._ai_engine_initialized:
            try:
                from backend.ai_engine import ai_engine
                self.ai_engine = ai_engine
                self._ai_engine_initialized = True
                logger.info("✅ AI движок инициализирован")
            except ImportError as e:
                logger.warning(f"⚠️ AI движок недоступен: {e}")
                self._ai_engine_initialized = True

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None, gender: str = None):
        """Сбор и сохранение всех данных пользователя"""
        try:
            logger.info(f"🔄 Начало сбора данных для пользователя {telegram_id}")

            # Используем транзакцию для атомарности операций
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

    async def get_recommendations(self, telegram_id: int, target_date: date, include_ai: bool = False):
        """
        Получение данных на выбранную дату
        include_ai: если False - возвращает только расчеты (мгновенно)
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

            # Получаем профиль пользователя для модели
            user_profile = await get_user_profile(telegram_id)
            if not user_profile:
                return {
                    'success': False,
                    'message': "❌ Профиль пользователя не найден"
                }

            # 1. Данные для пользователя (через бот)
            user_data = await format_data_for_user(prediction)

            result = {
                'success': True,
                'date': target_date.isoformat(),
                'user_data': user_data,
                'prediction_data': prediction,  # Данные для AI
                'user_profile': user_profile  # Профиль для AI
            }

            # 2. AI рекомендации ТОЛЬКО если явно запрошены
            if include_ai:
                logger.info(f"🤖 Включена генерация AI рекомендаций для {telegram_id}")
                ai_result = await self._get_ai_recommendations(telegram_id, user_profile, prediction, target_date)
                result.update({
                    'ai_recommendations': ai_result.get('recommendations', {}),
                    'ai_success': ai_result.get('success', False),
                    'is_fallback': ai_result.get('is_fallback', False),
                    'ai_error': ai_result.get('error')
                })
            else:
                logger.info(f"⚡ AI рекомендации отключены для быстрого показа данных {telegram_id}")

            return result

        except Exception as e:
            logger.error(f"❌ Ошибка получения данных на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить данные на выбранную дату: {str(e)}"
            }

    async def get_ai_recommendations_async(self, telegram_id: int, target_date: date,
                                           prediction_data: dict, user_profile: dict):
        """
        Асинхронное получение AI рекомендаций (для использования в handlers)
        """
        try:
            logger.info(f"🔄 Асинхронная генерация AI рекомендаций для {telegram_id}")

            # Ленивая инициализация AI движка
            await self._initialize_ai_engine()

            if not self.ai_engine:
                return self._get_fallback_ai_recommendations("AI движок недоступен")

            # Проверяем доступность AI сервиса
            health_check = await self.ai_engine.test_connection()
            if not health_check.get('ollama_available', False):
                return self._get_fallback_ai_recommendations("Ollama сервис недоступен")

            if not health_check.get('model_loaded', False):
                return self._get_fallback_ai_recommendations("AI модель не загружена")

            # Подготавливаем ОПТИМИЗИРОВАННЫЕ данные для AI
            prepared_data = self._prepare_optimized_ai_data(telegram_id, user_profile, prediction_data, target_date)

            # Генерируем рекомендации с таймаутом
            try:
                ai_result = await asyncio.wait_for(
                    self.ai_engine.generate_recommendations(prepared_data),
                    timeout=170  # 170 секунд для AI обработки
                )

                if ai_result.get('success', False):
                    logger.info(f"✅ AI рекомендации сгенерированы для {telegram_id}")
                    return ai_result
                else:
                    logger.warning(f"⚠️ AI не смог сгенерировать рекомендации: {ai_result.get('error')}")
                    return self._get_fallback_ai_recommendations(ai_result.get('error', 'Unknown AI error'))

            except asyncio.TimeoutError:
                logger.warning(f"⏰ Таймаут AI обработки для {telegram_id}")
                return self._get_fallback_ai_recommendations("Таймаут генерации рекомендаций")

            except Exception as e:
                logger.error(f"❌ Ошибка AI обработки для {telegram_id}: {e}")
                return self._get_fallback_ai_recommendations(str(e))

        except Exception as e:
            logger.error(f"❌ Критическая ошибка AI системы для {telegram_id}: {e}")
            return self._get_fallback_ai_recommendations(str(e))

    async def _get_ai_recommendations(self, telegram_id: int, user_profile: dict, prediction: dict, target_date: date):
        """Получение AI рекомендаций (синхронная версия)"""
        return await self.get_ai_recommendations_async(telegram_id, target_date, prediction, user_profile)

    def _prepare_optimized_ai_data(self, telegram_id: int, user_profile: dict, prediction: dict,
                                   target_date: date) -> dict:
        """
        ОПТИМИЗИРОВАННАЯ подготовка данных для AI модели
        Убраны избыточные поля, добавлены полезные контекстные данные
        """
        try:
            daily_calculations = prediction.get('daily_calculations', {})
            biorhythm_data = daily_calculations.get('biorhythm_data', {})
            astro_data = daily_calculations.get('astro_data', {})

            # Рассчитываем возраст пользователя для контекста
            user_age = self._calculate_user_age(user_profile.get('birth_date'))

            # Извлекаем ключевые сильные аспекты
            strong_aspects = self._extract_key_strong_aspects(astro_data)

            # Оптимизируем данные биоритмов
            optimized_biorhythms = self._optimize_biorhythm_data(biorhythm_data)

            # Оптимизируем астрологические данные
            optimized_astro = self._optimize_astro_data(astro_data)

            return {
                'user_profile': {
                    'profession': user_profile.get('profession', 'не указана'),
                    'position': user_profile.get('job_position', 'не указана'),
                    'current_city': user_profile.get('current_city', 'не указан'),
                    'age': user_age
                },
                'energy_state': optimized_biorhythms,
                'astro_influences': optimized_astro,
                'key_aspects': strong_aspects,
                'target_date': target_date.strftime('%d.%m.%Y'),  # Более читаемый формат
                'season': self._get_season(target_date),  # Добавляем сезон для контекста
                'day_of_week': target_date.strftime('%A')  # День недели для контекста
            }

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки оптимизированных данных для AI: {e}")
            # Fallback на старую структуру при ошибке
            return self._prepare_ai_data_fallback(user_profile, prediction, target_date)

    def _calculate_user_age(self, birth_date: date) -> int:
        """Расчет возраста пользователя"""
        try:
            if not birth_date:
                return 0
            today = date.today()
            age = today.year - birth_date.year
            # Корректируем если день рождения еще не наступил в этом году
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета возраста: {e}")
            return 0

    def _extract_key_strong_aspects(self, astro_data: dict) -> List[str]:
        """Извлечение ключевых сильных аспектов для AI"""
        try:
            key_aspects = astro_data.get('key_aspects', [])
            strong_aspects = []

            # Берем только топ-5 самых сильных аспектов
            sorted_aspects = sorted(key_aspects, key=lambda x: x.get('strength', 0), reverse=True)[:5]

            for aspect in sorted_aspects:
                if aspect.get('strength', 0) > 0.6:  # Более строгий порог для AI
                    transit = aspect.get('transit_planet', '')
                    natal = aspect.get('natal_planet', '')
                    aspect_type = aspect.get('aspect', '')

                    if transit and natal and aspect_type:
                        # Упрощенные названия для AI
                        strong_aspects.append(f"{transit}-{natal}-{aspect_type}")

            return strong_aspects

        except Exception as e:
            logger.warning(f"⚠️ Ошибка извлечения сильных аспектов для AI: {e}")
            return []

    def _optimize_biorhythm_data(self, biorhythm_data: dict) -> Dict[str, Any]:
        """Оптимизация данных биоритмов для AI"""
        try:
            overall = biorhythm_data.get('overall_energy', {})
            cycles = biorhythm_data.get('cycles', {})

            return {
                'overall_energy_percentage': overall.get('percentage', 0),
                'overall_energy_level': overall.get('level', 'средний'),
                'physical': {
                    'percentage': cycles.get('physical', {}).get('percentage', 0),
                    'phase': cycles.get('physical', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('physical', {}).get('trend', 'стабильно')
                },
                'emotional': {
                    'percentage': cycles.get('emotional', {}).get('percentage', 0),
                    'phase': cycles.get('emotional', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('emotional', {}).get('trend', 'стабильно')
                },
                'intellectual': {
                    'percentage': cycles.get('intellectual', {}).get('percentage', 0),
                    'phase': cycles.get('intellectual', {}).get('phase', 'нейтральная'),
                    'trend': cycles.get('intellectual', {}).get('trend', 'стабильно')
                }
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка оптимизации данных биоритмов: {e}")
            return {}

    def _optimize_astro_data(self, astro_data: dict) -> Dict[str, Any]:
        """Оптимизация астрологических данных для AI"""
        try:
            return {
                'total_aspects': astro_data.get('aspects_count', 0),
                'strong_aspects': astro_data.get('strong_aspects_count', 0),
                'retrograde_planets': len(astro_data.get('retrograde_planets', [])),
                'aspect_intensity': self._calculate_aspect_intensity(astro_data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка оптимизации астроданных: {e}")
            return {}

    def _calculate_aspect_intensity(self, astro_data: dict) -> str:
        """Расчет интенсивности аспектов для AI"""
        try:
            strong_count = astro_data.get('strong_aspects_count', 0)
            total_count = astro_data.get('aspects_count', 0)

            if total_count == 0:
                return 'низкая'

            intensity_ratio = strong_count / total_count

            if intensity_ratio > 0.7:
                return 'очень высокая'
            elif intensity_ratio > 0.5:
                return 'высокая'
            elif intensity_ratio > 0.3:
                return 'средняя'
            else:
                return 'низкая'

        except Exception as e:
            logger.warning(f"⚠️ Ошибка расчета интенсивности аспектов: {e}")
            return 'неизвестно'

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

    def _prepare_ai_data_fallback(self, user_profile: dict, prediction: dict, target_date: date) -> dict:
        """Fallback подготовка данных (старая структура)"""
        try:
            daily_calculations = prediction.get('daily_calculations', {})

            return {
                'user_context': {
                    'profession': user_profile.get('profession'),
                    'position': user_profile.get('job_position'),
                    'current_city': user_profile.get('current_city')
                },
                'energy_state': daily_calculations.get('biorhythm_data', {}),
                'astro_highlights': daily_calculations.get('astro_data', {}),
                'target_date': target_date.isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Критическая ошибка fallback подготовки данных: {e}")
            return {
                'user_context': {'profession': 'неизвестно'},
                'energy_state': {},
                'astro_highlights': {},
                'target_date': target_date.isoformat()
            }

    def _get_fallback_ai_recommendations(self, error: str) -> dict:
        """Резервные рекомендации при недоступности AI"""
        logger.info(f"🔄 Используются резервные рекомендации: {error}")

        return {
            'success': False,
            'is_fallback': True,
            'error': error,
            'recommendations': {
                'professional': [
                    "Сфокусируйтесь на текущих задачах",
                    "Планируйте работу по приоритетам"
                ],
                'personal_effectiveness': [
                    "Соблюдайте баланс работы и отдыха",
                    "Делайте регулярные перерывы"
                ],
                'emotional': [
                    "Сохраняйте эмоциональное равновесие",
                    "Избегайте импульсивных решений"
                ],
                'daily_focus': [
                    "Баланс между продуктивностью и восстановлением"
                ]
            }
        }

    async def get_todays_recommendations(self, telegram_id: int, include_ai: bool = False):
        """Получение данных на сегодня (для обратной совместимости)"""
        return await self.get_recommendations(telegram_id, date.today(), include_ai)

    async def get_tomorrows_recommendations(self, telegram_id: int, include_ai: bool = False):
        """Получение данных на завтра"""
        tomorrow = date.today() + timedelta(days=1)
        return await self.get_recommendations(telegram_id, tomorrow, include_ai)

    async def get_date_recommendations(self, telegram_id: int, target_date: date, include_ai: bool = False):
        """Получение данных на выбранную дату (alias для единообразия)"""
        return await self.get_recommendations(telegram_id, target_date, include_ai)

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None, gender: str = None):
        """Обновление профессиональной информации"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            # Обновляем город проживания и пол
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
        """Очистка данных пользователя (для администрирования)"""
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

    async def test_ai_connection(self):
        """Тестирование подключения к AI сервису"""
        try:
            await self._initialize_ai_engine()

            if not self.ai_engine:
                return {
                    'available': False,
                    'error': 'AI движок недоступен'
                }

            return await self.ai_engine.test_connection()

        except Exception as e:
            logger.error(f"❌ Ошибка тестирования AI подключения: {e}")
            return {
                'available': False,
                'error': str(e)
            }


# Создаем глобальный экземпляр помощника
assistant = PersonalAssistant()

biorhythm_calculator.py:

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

biorhythm_services.py:

from backend.database import async_session, Biorhythms
from backend.biorhythm_calculator import BiorhythmCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import date, datetime, timedelta
import logging
import asyncio

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


async def get_user_biorhythms(telegram_id: int, target_date: date = None):
    """Получение биоритмов пользователя с улучшенной обработкой ошибок"""
    try:
        if target_date is None:
            target_date = date.today()

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

            statistics = {
                'total_records': total_records,
                'first_calculation': min_date.isoformat() if min_date else None,
                'last_calculation': max_date.isoformat() if max_date else None,
                'calculation_range_days': (max_date - min_date).days if min_date and max_date else 0
            }

            logger.info(f"📊 Статистика биоритмов получена для {telegram_id}")
            return statistics

    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики биоритмов {telegram_id}: {e}")
        return {
            'total_records': 0,
            'first_calculation': None,
            'last_calculation': None,
            'calculation_range_days': 0
        }


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

chart_services.py:

from backend.database import async_session, UserNatalChart
from backend.natal_chart import MLNatalChartCalculator
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def create_and_save_natal_chart(telegram_id: int, city: str, birth_datetime, timezone: str):
    """Создание и сохранение натальной карты"""
    try:
        calculator = MLNatalChartCalculator()
        natal_data = calculator.calculate_natal_chart_ml(city, birth_datetime, timezone)

        logger.info(f"Создание натальной карты для пользователя {telegram_id}")

        async with async_session() as session:
            result = await session.execute(
                select(UserNatalChart).where(UserNatalChart.telegram_id == telegram_id)
            )
            natal_chart = result.scalar_one_or_none()

            if natal_chart:
                # Обновляем существующую натальную карту
                natal_chart.natal_data = natal_data
                logger.info(f"📝 Обновлена натальная карта для {telegram_id}")
            else:
                # Создаем новую натальную карту
                natal_chart = UserNatalChart(
                    telegram_id=telegram_id,
                    natal_data=natal_data
                )
                session.add(natal_chart)
                logger.info(f"🆕 Создана новая натальная карта для {telegram_id}")

            await session.commit()
            logger.info(f"💾 Натальная карта успешно сохранена для {telegram_id}")
            return natal_chart

    except Exception as e:
        logger.error(f"❌ Ошибка при создании натальной карты для {telegram_id}: {e}")
        raise


async def get_user_natal_chart(telegram_id: int):
    """Получение натальной карты пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(UserNatalChart).where(UserNatalChart.telegram_id == telegram_id)
            )
            natal_chart = result.scalar_one_or_none()

            if natal_chart:
                return natal_chart.natal_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении натальной карты {telegram_id}: {e}")
        return None

database.py:

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, String, Date, Time, Text
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, String, Date, Time, Text, ForeignKey, Integer
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://pers_assist:astra123@localhost:5432/p_assistant_bd"
)

logger.info(f"Подключаемся к БД: postgresql+asyncpg://pers_assist:******@localhost:5432/p_assistant_bd")

async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300
)

async_session = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    birth_date = Column(Date, nullable=False)
    birth_time = Column(Time, nullable=False)
    birth_city = Column(String(100), nullable=False)
    profession = Column(String(100), nullable=True)
    job_position = Column(String(100), nullable=True)
    current_city = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    gender = Column(String(10), nullable=True)  # 'male', 'female', None
    request_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, birth_date={self.birth_date})>"

class UserNatalChart(Base):
    __tablename__ = 'user_natal_charts'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    natal_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserNatalChart(telegram_id={self.telegram_id})>"

class PsyhoMatrix(Base):
    __tablename__ = 'psyho_matrix'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    matrix_data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PsyhoMatrix(telegram_id={self.telegram_id})>"

class NatalPredictions(Base):
    __tablename__ = 'natal_predictions'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    predictions = Column(JSON, nullable=False)
    assistant_data = Column(JSON, nullable=False, default={})
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NatalPredictions(telegram_id={self.telegram_id})>"


class Biorhythms(Base):
    __tablename__ = 'biorhythms'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    biorhythm_data = Column(JSON, nullable=False)
    calculation_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Biorhythms(telegram_id={self.telegram_id}, date={self.calculation_date})>"



# Добавить недостающие модели для AI рекомендаций:
class AIRecommendations(Base):
    __tablename__ = 'ai_recommendations'
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), primary_key=True)
    target_date = Column(Date, primary_key=True)
    data_hash = Column(String(64), nullable=False)
    recommendations = Column(Text, nullable=False)
    model_version = Column(String(20), default='gemma:2b')
    created_at = Column(TIMESTAMP, server_default=func.now())

class AstroInsights(Base):
    __tablename__ = 'astro_insights'
    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id'), primary_key=True)
    dominant_energy = Column(JSON, nullable=False)
    personality_traits = Column(JSON, nullable=False)
    planetary_strengths = Column(JSON, nullable=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


class Biorhythms(Base):
    __tablename__ = 'biorhythms'

    telegram_id = Column(BigInteger, ForeignKey('users.telegram_id', ondelete='CASCADE'), primary_key=True, index=True)
    biorhythm_data = Column(JSON, nullable=False)
    calculation_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Biorhythms(telegram_id={self.telegram_id}, date={self.calculation_date})>"



async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()





db_connection.py:

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

matrix_services.py:

from backend.database import async_session, PsyhoMatrix
from backend.psyho_matrix import PsyhoMatrixCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def calculate_and_save_psyho_matrix(telegram_id: int):
    """Расчет и сохранение психоматрицы"""
    try:
        # Получаем данные пользователя
        user_profile = await get_user_profile(telegram_id)
        if not user_profile:
            raise ValueError("Пользователь не найден")

        calculator = PsyhoMatrixCalculator()
        matrix_data = calculator.calculate_matrix(user_profile['birth_date'])

        # Сохраняем психоматрицу
        async with async_session() as session:
            result = await session.execute(
                select(PsyhoMatrix).where(PsyhoMatrix.telegram_id == telegram_id)
            )
            psyho_matrix = result.scalar_one_or_none()

            if psyho_matrix:
                # Обновляем существующую психоматрицу
                psyho_matrix.matrix_data = matrix_data
                logger.info(f"📝 Обновлена психоматрица для {telegram_id}")
            else:
                # Создаем новую психоматрицу
                psyho_matrix = PsyhoMatrix(
                    telegram_id=telegram_id,
                    matrix_data=matrix_data
                )
                session.add(psyho_matrix)
                logger.info(f"🆕 Создана новая психоматрица для {telegram_id}")

            await session.commit()
            logger.info(f"✅ Психоматрица рассчитана и сохранена для {telegram_id}")

        return matrix_data

    except Exception as e:
        logger.error(f"❌ Ошибка при расчете психоматрицы для {telegram_id}: {e}")
        raise


async def get_user_matrix(telegram_id: int):
    """Получение психоматрицы пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(PsyhoMatrix).where(PsyhoMatrix.telegram_id == telegram_id)
            )
            matrix = result.scalar_one_or_none()

            if matrix:
                return matrix.matrix_data
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении психоматрицы {telegram_id}: {e}")
        return None

natal_chart.py:

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

from backend.database import async_session, UserNatalChart

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

predictions.py:

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
        
        
prediction_services.py:

from backend.database import async_session, NatalPredictions
from backend.predictions import AstroPredictor
from backend.chart_services import get_user_natal_chart
from backend.matrix_services import get_user_matrix
from backend.biorhythm_services import calculate_and_save_biorhythms
from backend.aspect_recommendations import aspect_recommendations
from sqlalchemy.future import select
from sqlalchemy import func, and_
import logging
import json
from datetime import datetime, date
from typing import List, Dict, Any  # ✅ ДОБАВЛЕННЫЙ ИМПОРТ

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
                'key_aspects': astro_prediction.get('aspects', [])[:5]  # ✅ ТЕПЕРЬ СОДЕРЖИТ ДАННЫЕ ДЛЯ СИЛЬНЫХ АСПЕКТОВ
            },
            'biorhythm_data': {
                'overall_energy': biorhythm_data.get('overall_energy', {}),
                'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {}),
                'critical_days_count': len(biorhythm_data.get('critical_days', [])),
                'peak_days_count': len(biorhythm_data.get('peak_days', []))
            },
            'calculation_metadata': {
                'calculation_timestamp': datetime.now().isoformat(),
                'data_sources': ['astrology', 'biorhythms'],
                'calculation_methods': ['swiss_ephemeris', 'sine_wave_analysis']
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


# Добавить в начало файла:
from backend.aspect_recommendations import aspect_recommendations


# Обновить функцию format_data_for_user:
async def format_data_for_user(prediction: dict) -> str:
    """Форматирование данных для отображения пользователю"""
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

            physical = biorhythms.get('physical_cycle', {})
            emotional = biorhythms.get('emotional_cycle', {})
            intellectual = biorhythms.get('intellectual_cycle', {})

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

            # ✅ ДОБАВЛЕНО: ПРОСТЫЕ РЕКОМЕНДАЦИИ ПО АСПЕКТАМ
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

        lines.append("")
        lines.append("🎯 *Используйте эти данные для планирования своего дня*")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Ошибка форматирования данных: {e}")
        return "❌ Произошла ошибка при формировании данных расчетов"


# ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ
async def generate_and_save_prediction(telegram_id: int, target_date: date):
    """Генерация и сохранение данных для конкретной даты (перезапись существующих)"""
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

        # Сохраняем данные в БД с ПЕРЕЗАПИСЬЮ
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            existing_record = result.scalar_one_or_none()

            # Структура данных для сохранения
            prediction_data = {
                'calculation_date': datetime.now().isoformat(),
                'target_date': target_date.isoformat(),
                'natal_chart': natal_data,
                'psyho_matrix': matrix_data,
                'daily_calculations': combined_data
            }

            if existing_record:
                # ПЕРЕЗАПИСЫВАЕМ существующую запись
                existing_record.predictions = prediction_data
                existing_record.updated_at = func.now()
                logger.info(f"📝 Перезаписаны данные для {telegram_id} на {target_date}")
            else:
                # Создаем новую запись
                new_record = NatalPredictions(
                    telegram_id=telegram_id,
                    predictions=prediction_data,
                    assistant_data={},
                )
                session.add(new_record)
                logger.info(f"🆕 Созданы новые данные для {telegram_id} на {target_date}")

            await session.commit()
            logger.info(f"💾 Данные успешно сохранены в БД для {telegram_id}")

        return prediction_data

    except ValueError as e:
        logger.warning(f"❌ Ошибка валидации для {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации данных для {telegram_id}: {e}")
        raise Exception(f"Не удалось сгенерировать данные на основе расчетов: {str(e)}")



async def format_data_for_model(telegram_id: int, user_profile: dict, prediction: dict) -> str:
    """Форматирование данных для модели ИИ"""
    if not prediction:
        return "❌ No calculation data available"

    try:
        model_data = {
            'user_profile': {
                'telegram_id': telegram_id,
                'gender': user_profile.get('gender'),
                'profession': user_profile.get('profession'),
                'job_position': user_profile.get('job_position'),
                'current_city': user_profile.get('current_city'),
                'birth_date': user_profile.get('birth_date').isoformat() if user_profile.get('birth_date') else None,
                'birth_city': user_profile.get('birth_city')
            },
            'natal_chart': prediction.get('natal_chart', {}),
            'psyho_matrix': prediction.get('psyho_matrix', {}),
            'daily_calculations': prediction.get('daily_calculations', {}),
            'target_date': prediction.get('target_date'),
            'timestamp': datetime.now().isoformat()
        }

        # Красивый вывод для отладки
        print("\n" + "=" * 80)
        print("🤖 DATA FOR AI MODEL:")
        print("=" * 80)
        print(f"👤 User ID: {telegram_id}")
        print(f"📅 Target Date: {prediction.get('target_date', 'Unknown')}")
        print(f"💼 Profession: {user_profile.get('profession', 'Not specified')}")
        print(f"📋 Position: {user_profile.get('job_position', 'Not specified')}")
        print(f"🏙️ City: {user_profile.get('current_city', 'Not specified')}")

        # Натальная карта
        natal_chart = prediction.get('natal_chart', {})
        if natal_chart:
            planets = natal_chart.get('planets', {})
            print(f"\n🌟 Natal Chart: {len(planets)} planets calculated")
            print(f"   📍 Birth location: {natal_chart.get('metadata', {}).get('location', {}).get('city', 'Unknown')}")

        # Психоматрица
        matrix = prediction.get('psyho_matrix', {})
        if matrix:
            basic_numbers = matrix.get('basic_numbers', {})
            print(f"🔢 Psyho Matrix: First number: {basic_numbers.get('first', 'N/A')}")

        # Ежедневные расчеты
        daily = prediction.get('daily_calculations', {})
        if daily:
            biorhythms = daily.get('biorhythm_data', {})
            astro = daily.get('astro_data', {})
            print(f"📊 Daily Calculations:")
            print(f"   ⚡ Energy: {biorhythms.get('overall_energy', {}).get('percentage', 0):.1f}%")
            print(f"   🌟 Aspects: {astro.get('aspects_count', 0)}")

        print("=" * 80)
        print("JSON Data for AI Model:")
        print("=" * 80)
        print(json.dumps(model_data, ensure_ascii=False, indent=2))
        print("=" * 80 + "\n")

        return json.dumps(model_data, ensure_ascii=False)

    except Exception as e:
        logger.error(f"❌ Error formatting data for model: {e}")
        return json.dumps({'error': str(e)})



async def get_user_predictions(telegram_id: int):
    """Получение последних данных пользователя"""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            predictions = result.scalar_one_or_none()

            if predictions:
                return predictions.predictions
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных {telegram_id}: {e}")
        return None



async def get_prediction_statistics(telegram_id: int) -> dict:
    """Получение статистики данных пользователя"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return {}

        daily_data = prediction.get('daily_calculations', {})
        return {
            'last_calculation_date': prediction.get('calculation_date'),
            'target_date': prediction.get('target_date'),
            'biorhythm_energy': daily_data.get('biorhythm_data', {}).get('overall_energy', {}).get('percentage', 0),
            'astro_aspects_count': daily_data.get('astro_data', {}).get('aspects_count', 0)
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        return {}


async def validate_prediction_data(telegram_id: int) -> bool:
    """Проверка корректности данных"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return False

        # Проверяем наличие обязательных полей
        required_fields = ['natal_chart', 'psyho_matrix', 'daily_calculations', 'target_date']
        for field in required_fields:
            if field not in prediction:
                return False

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации данных для {telegram_id}: {e}")
        return False


async def cleanup_old_predictions():
    """Очистка устаревших данных"""
    try:
        logger.info("🔄 Очистка устаревших данных не требуется в текущей структуре")
        return 0

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке данных: {e}")
        return 0
        
        
prompt_builder.py

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
        return template(data)

    def _daily_recommendations_template(self, data: Dict[str, Any]) -> str:
        """Шаблон для ежедневных рекомендаций"""
        user_context = data.get('user_context', {})
        energy_state = data.get('energy_state', {})
        astro_highlights = data.get('astro_highlights', {})

        # Ключевые инсайты из астроданных
        key_insights = self._extract_key_insights(astro_highlights)

        prompt = f"""На основе индивидуальных расчетов предоставь КОНКРЕТНЫЕ практические рекомендации на день.

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
• Профессия: {user_context.get('profession', 'не указана')}
• Должность: {user_context.get('position', 'не указана')}
• Город: {user_context.get('current_city', 'не указан')}

ЭНЕРГЕТИЧЕСКИЙ ПРОФИЛЬ:
{self._format_energy_state(energy_state)}

АСТРОЛОГИЧЕСКИЕ ИНСАЙТЫ:
{key_insights}

СФОРМУЛИРУЙ 3-5 КОНКРЕТНЫХ РЕКОМЕНДАЦИЙ:
1. 💼 Профессиональный фокус (что делать на работе)
2. 🏃 Личная эффективность (как организовать день)  
3. ❤️ Эмоциональный баланс (на что обратить внимание)
4. 🎯 Ключевая задача дня (самое важное)

ОТВЕТ (только рекомендации, без пояснений):"""

        return prompt

    def _professional_focus_template(self, data: Dict[str, Any]) -> str:
        """Шаблон для профессиональных рекомендаций"""
        user_context = data.get('user_context', {})

        return f"""Сфокусируйся на профессиональных рекомендациях для:

Профессия: {user_context.get('profession', 'не указана')}
Должность: {user_context.get('position', 'не указана')}

Дай 3 конкретных совета по:
1. Оптимизации рабочего процесса
2. Решению профессиональных задач
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


psyho_matrix.py:

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

user_services.py:  

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
        
ai_engine.py:

import aiohttp
import asyncio
import logging
import os
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIPredictionEngine:
    """
    Оптимизированный движок для работы с Ollama API с одной моделью (gemma:2b)
    Интегрирован с prompt_builder и recommendation_service
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('OLLAMA_URL', 'http://localhost:11435')

        # Фиксированная модель - gemma:2b
        #self.model = "gemma:2b"
        self.model = "tinyllama:1.1b"

        # Оптимизированные таймауты
        self.timeout = aiohttp.ClientTimeout(total=600)  # 180 секунд
        self.max_retries = 2
        self.retry_delay = 2

        # Инициализация зависимостей
        self.prompt_builder = None
        self.recommendation_service = None
        self._dependencies_initialized = False

        # Статистика использования
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "current_model": self.model,
            "last_health_check": None,
            "service_available": False
        }

        logger.info(f"🤖 AI движок инициализирован: {self.base_url}, модель: {self.model}")

    async def _initialize_dependencies(self):
        """Ленивая инициализация зависимостей"""
        if not self._dependencies_initialized:
            try:
                from backend.prompt_builder import prompt_builder
                from backend.recommendation_service import recommendation_service

                self.prompt_builder = prompt_builder
                self.recommendation_service = recommendation_service
                self._dependencies_initialized = True
                logger.info("✅ Зависимости AI движка инициализированы")
            except ImportError as e:
                logger.warning(f"⚠️ Не удалось инициализировать зависимости: {e}")
                self._dependencies_initialized = True  # Помечаем как инициализированные, даже если есть ошибки

    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Генерация хэша данных для кэширования"""
        try:
            # Создаем стабильное представление данных для хэширования
            stable_data = {
                'user_context': data.get('user_context', {}),
                'energy_state': data.get('energy_state', {}),
                'target_date': data.get('target_date'),
                'telegram_id': data.get('user_profile', {}).get('telegram_id')
            }

            data_str = json.dumps(stable_data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"❌ Ошибка генерации хэша данных: {e}")
            return "fallback_hash"

    async def test_connection(self) -> Dict[str, Any]:
        """
        Быстрая проверка подключения и доступности модели
        """
        test_result = {
            "ollama_available": False,
            "model_loaded": False,
            "test_passed": False,
            "response_time": None,
            "error": None,
            "details": {
                "available_models": [],
                "test_response": None,
                "model_details": {}
            }
        }

        try:
            start_time = time.time()

            # Проверяем доступность Ollama
            test_result["ollama_available"] = await self.check_health()

            if test_result["ollama_available"]:
                # Проверяем наличие конкретной модели
                available_models = await self.get_available_models()
                test_result["model_loaded"] = self.model in available_models
                test_result["details"]["available_models"] = available_models

                # Получаем детали модели
                if test_result["model_loaded"]:
                    model_details = await self.get_model_details()
                    test_result["details"]["model_details"] = model_details

                # Быстрый тестовый запрос
                if test_result["model_loaded"]:
                    test_data = {
                        "user_context": {"profession": "тест", "position": "тест"},
                        "energy_state": {
                            "overall_energy": {"percentage": 75},
                            "physical_cycle": {"phase": "высокая активность"},
                            "emotional_cycle": {"phase": "нейтральная"}
                        },
                        "target_date": datetime.now().date().isoformat()
                    }

                    test_response = await self.generate_recommendations(test_data)
                    test_result["test_passed"] = test_response["success"]
                    test_result["response_time"] = test_response.get("response_time_seconds")

            test_result["response_time"] = time.time() - start_time
            self.stats["service_available"] = test_result["ollama_available"]
            self.stats["last_health_check"] = datetime.now().isoformat()

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Ошибка тестирования подключения: {e}")
            self.stats["service_available"] = False

        return test_result

    async def get_available_models(self) -> List[str]:
        """Получение списка доступных моделей"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
                    else:
                        logger.warning(f"❌ Ошибка получения моделей: {response.status}")
                        return []
        except Exception as e:
            logger.debug(f"Не удалось получить список моделей: {e}")
            return []

    async def get_model_details(self) -> Dict[str, Any]:
        """Получение деталей текущей модели"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"{self.base_url}/api/show", json={"name": self.model}) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Status {response.status}"}
        except Exception as e:
            return {"error": str(e)}

    async def check_health(self) -> bool:
        """Проверка доступности Ollama сервиса"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        self.stats["service_available"] = True
                        return True
        except Exception as e:
            logger.debug(f"❌ Ollama недоступен: {e}")

        self.stats["service_available"] = False
        return False

    async def ensure_model_loaded(self) -> bool:
        """Проверка и при необходимости загрузка модели"""
        try:
            available_models = await self.get_available_models()
            if self.model not in available_models:
                logger.info(f"🔄 Модель {self.model} не найдена, пытаюсь загрузить...")
                return await self.pull_model()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки модели: {e}")
            return False

    async def pull_model(self) -> bool:
        """Загрузка модели"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(f"{self.base_url}/api/pull", json={"name": self.model}) as response:
                    if response.status == 200:
                        logger.info(f"✅ Модель {self.model} успешно загружена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка загрузки модели: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке модели: {e}")
            return False

    async def generate_recommendations(self, prepared_data: Dict) -> Dict[str, Any]:
        """
        Основной метод генерации рекомендаций с кэшированием
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Инициализируем зависимости
        await self._initialize_dependencies()

        # ПРОВЕРЯЕМ КЭШ
        try:
            if self.recommendation_service:
                data_hash = self._generate_data_hash(prepared_data)
                telegram_id = prepared_data.get('user_profile', {}).get('telegram_id')
                target_date_str = prepared_data.get('target_date')

                if telegram_id and target_date_str:
                    target_date = datetime.fromisoformat(target_date_str).date()
                    cached = await self.recommendation_service.get_cached_recommendations(
                        telegram_id, target_date, data_hash
                    )
                    if cached:
                        logger.info(f"✅ Использованы кэшированные рекомендации для {telegram_id}")
                        return {
                            "success": True,
                            "recommendations": cached['recommendations'],
                            "from_cache": True,
                            "model_used": cached.get('model_version', self.model),
                            "response_time_seconds": 0.1,
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки кэша: {e}")

        # Проверяем доступность сервиса
        if not await self.check_health():
            return self._get_fallback_response(prepared_data, "Сервис AI недоступен")

        # Проверяем наличие модели
        if not await self.ensure_model_loaded():
            return self._get_fallback_response(prepared_data, "Модель AI не загружена")

        try:
            # Формируем промпт с использованием prompt_builder
            prompt = await self._build_prompt_optimized(prepared_data)
            response_text = await self._make_ollama_request(prompt)
            recommendations = self._parse_response(response_text)

            # Сохраняем в кэш
            try:
                if self.recommendation_service and telegram_id and target_date_str:
                    await self.recommendation_service.save_recommendations(
                        telegram_id,
                        datetime.fromisoformat(target_date_str).date(),
                        data_hash,
                        response_text,
                        self.model
                    )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка сохранения в кэш: {e}")

            # Обновляем статистику
            response_time = time.time() - start_time
            self.stats["successful_requests"] += 1

            # Обновляем среднее время ответа
            prev_avg = self.stats["average_response_time"]
            prev_count = self.stats["successful_requests"] - 1
            self.stats["average_response_time"] = (
                (prev_avg * prev_count + response_time) / self.stats["successful_requests"]
                if self.stats["successful_requests"] > 0 else response_time
            )

            logger.info(f"✅ Рекомендации сгенерированы за {response_time:.2f}с")

            return {
                "success": True,
                "recommendations": recommendations,
                "response_text": response_text,
                "model_used": self.model,
                "response_time_seconds": round(response_time, 2),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"❌ Ошибка генерации рекомендаций: {e}")
            return self._get_fallback_response(prepared_data, str(e))

    async def _build_prompt_optimized(self, data: Dict) -> str:
        """Оптимизированное построение промпта с использованием prompt_builder"""
        try:
            if self.prompt_builder:
                return self.prompt_builder.build_prompt(data)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка prompt_builder, используем fallback: {e}")

        # Fallback промпт
        user_context = data.get("user_context", {})
        energy_state = data.get("energy_state", {})

        return f"""На основе индивидуальных данных предоставь краткие практические рекомендации на день.

ПРОФИЛЬ:
• Профессия: {user_context.get('profession', 'не указана')}
• Должность: {user_context.get('position', 'не указана')}

СОСТОЯНИЕ:
• Общая энергия: {energy_state.get('overall_energy', {}).get('percentage', 0)}%
• Физический цикл: {energy_state.get('physical_cycle', {}).get('phase', 'нейтральный')}
• Эмоциональный цикл: {energy_state.get('emotional_cycle', {}).get('phase', 'нейтральный')}

СФОРМУЛИРУЙ КРАТКИЕ РЕКОМЕНДАЦИИ:
1. 💼 Профессиональная деятельность
2. 🏃 Личная эффективность  
3. ❤️ Эмоциональное состояние

ОТВЕТ:"""

    async def _make_ollama_request(self, prompt: str) -> str:
        """Оптимизированный запрос к Ollama API"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    # Оптимальные настройки для gemma:2b
                    options = {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 250,
                        "num_thread": 2,
                        "repeat_penalty": 1.1,
                        "top_k": 40
                    }

                    request_data = {
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": options
                    }

                    logger.info(f"🔄 Запрос к {self.model} (попытка {attempt + 1}/{self.max_retries})")

                    async with session.post(f"{self.base_url}/api/generate", json=request_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "").strip()

                            # Логируем производительность
                            if "eval_duration" in result:
                                eval_time = result["eval_duration"] / 1_000_000_000
                                logger.debug(f"⏱️ Время генерации модели: {eval_time:.2f}с")

                            return response_text
                        else:
                            error_text = await response.text()
                            raise Exception(f"Ollama API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                last_exception = Exception(f"Таймаут запроса (попытка {attempt + 1})")
                logger.warning(f"⏰ Таймаут запроса, попытка {attempt + 1}")

            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Ошибка запроса (попытка {attempt + 1}): {e}")

            # Задержка перед повторной попыткой
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise last_exception or Exception("Не удалось выполнить запрос к AI")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Упрощенный парсинг ответа модели"""
        try:
            # Базовая структура для категорий
            categories = {
                "professional": [],
                "personal_effectiveness": [],
                "emotional": [],
                "daily_focus": []
            }

            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            current_category = None

            for line in lines:
                # Определяем категорию по маркерам
                line_lower = line.lower()
                if any(marker in line_lower for marker in ['💼', 'работа', 'професси', 'professional']):
                    current_category = "professional"
                elif any(marker in line_lower for marker in ['🏃', 'личн', 'эффектив', 'personal']):
                    current_category = "personal_effectiveness"
                elif any(marker in line_lower for marker in ['❤️', 'эмоц', 'настроен', 'emotional']):
                    current_category = "emotional"
                elif any(marker in line_lower for marker in ['🎯', 'акцент', 'фокус', 'focus']):
                    current_category = "daily_focus"

                # Добавляем пункты в текущую категорию
                elif current_category and line.startswith(('•', '-', '—', '1.', '2.', '3.')):
                    clean_line = line.lstrip('•-—123456789. ').strip()
                    if clean_line and len(clean_line) > 5:  # Минимальная длина
                        categories[current_category].append(clean_line)

            # Если не удалось выделить структурированные данные, возвращаем как есть
            if not any(categories.values()):
                return {"raw_recommendations": response_text}

            return categories

        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга ответа: {e}")
            return {"raw_recommendations": response_text}

    def _get_fallback_response(self, data: Dict, error: str) -> Dict[str, Any]:
        """Резервный ответ при недоступности AI"""
        logger.warning(f"🔄 Используется fallback из-за: {error}")

        return {
            "success": False,
            "error": error,
            "is_fallback": True,
            "recommendations": self._get_fallback_recommendations(data),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model
        }

    def _get_fallback_recommendations(self, data: Dict) -> Dict[str, Any]:
        """Умные резервные рекомендации на основе данных"""
        energy_state = data.get("energy_state", {})
        overall_energy = energy_state.get("overall_energy", {}).get("percentage", 50)
        user_context = data.get("user_context", {})

        # Персонализированные рекомендации на основе энергии
        if overall_energy > 75:
            energy_advice = "Идеальный день для сложных задач и важных решений."
            professional_tip = "Беритесь за амбициозные проекты"
        elif overall_energy > 50:
            energy_advice = "Хороший уровень энергии для продуктивной работы."
            professional_tip = "Сфокусируйтесь на текущих задачах"
        elif overall_energy > 25:
            energy_advice = "Энергии достаточно для рутинных задач."
            professional_tip = "Планируйте работу небольшими блоками"
        else:
            energy_advice = "Рекомендуется беречь силы и делать перерывы."
            professional_tip = "Отложите сложные задачи на другой день"

        # Учитываем профессию пользователя
        profession = user_context.get('profession', '').lower()
        if any(word in profession for word in ['разработ', 'программ', 'техн']):
            professional_tip += ", уделите время техническим задачам"
        elif any(word in profession for word in ['управл', 'менедж', 'руковод']):
            professional_tip += ", проведите планерки и встречи"

        return {
            "professional": [
                professional_tip,
                "Расставьте приоритеты в задачах"
            ],
            "personal_effectiveness": [
                energy_advice,
                "Соблюдайте баланс работы и отдыха",
                "Делайте регулярные перерывы"
            ],
            "emotional": [
                "Сохраняйте эмоциональное равновесие",
                "Избегайте импульсивных решений"
            ],
            "daily_focus": [
                "Баланс между продуктивностью и восстановлением"
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики использования"""
        return self.stats.copy()

    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Здесь можно добавить очистку кэша или других ресурсов
            logger.info("🧹 Ресурсы AI движка очищены")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки ресурсов: {e}")


# Глобальный экземпляр движка
ai_engine = AIPredictionEngine()



aspect_recommendations.py

import logging
from typing import Dict, List, Any
import random

logger = logging.getLogger(__name__)


class AspectRecommendationEngine:
    """
    Простой движок рекомендаций на основе астрологических аспектов
    Использует шаблоны для генерации понятных рекомендаций
    """

    def __init__(self):
        # Шаблоны рекомендаций по типам аспектов
        self.aspect_templates = {
            'conjunction': {
                'positive': [
                    "Энергия {transit} и {natal} объединяется - идеальное время для начала новых проектов",
                    "Соединение {transit} с {natal} дает мощный импульс для действий",
                    "Используйте объединенную энергию {transit} и {natal} для решительных шагов"
                ],
                'challenge': [
                    "Соединение {transit} и {natal} может создавать напряжение - будьте внимательны в общении",
                    "Энергия аспекта очень концентрированная - избегайте поспешных решений",
                    "Сфокусируйте мощную энергию соединения на одной важной задаче"
                ]
            },
            'opposition': {
                'positive': [
                    "Оппозиция {transit} и {natal} помогает увидеть разные точки зрения",
                    "Идеальное время для переговоров и поиска компромиссов",
                    "Используйте противостояние энергий для баланса в отношениях"
                ],
                'challenge': [
                    "Оппозиция {transit}-{natal} может создавать конфликты - проявляйте гибкость",
                    "Возможны противоречия - ищите золотую середину",
                    "Избегайте категоричных решений при этом аспекте"
                ]
            },
            'square': {
                'positive': [
                    "Квадрат {transit} и {natal} дает энергию для преодоления препятствий",
                    "Используйте напряжение аспекта для мобилизации сил",
                    "Это время активных действий и решения накопившихся проблем"
                ],
                'challenge': [
                    "Квадратура {transit}-{natal} требует осторожности в действиях",
                    "Возможны непредвиденные сложности - имейте запасной план",
                    "Избегайте конфронтации, решайте вопросы дипломатично"
                ]
            },
            'trine': {
                'positive': [
                    "Трин {transit} и {natal} приносит гармонию и удачные возможности",
                    "Благоприятное время для творчества и сотрудничества",
                    "Энергия течет легко - доверяйте интуиции и действуйте"
                ],
                'challenge': [
                    "При легкой энергии трина важно не упускать возможности",
                    "Не расслабляйтесь слишком - используйте благоприятный период",
                    "Сохраняйте активность, даже когда все дается легко"
                ]
            },
            'sextile': {
                'positive': [
                    "Секстиль {transit} и {natal} открывает новые перспективы",
                    "Идеальное время для установления полезных связей",
                    "Используйте возможности для профессионального роста"
                ],
                'challenge': [
                    "При множестве возможностей важно правильно расставить приоритеты",
                    "Не распыляйтесь - выберите самые перспективные направления",
                    "Уделите внимание планированию на будущее"
                ]
            }
        }

        # Рекомендации по конкретным планетам
        self.planet_recommendations = {
            'Sun': {
                'focus': "личная энергия, уверенность, творчество",
                'action': "проявляйте инициативу, будьте в центре внимания"
            },
            'Moon': {
                'focus': "эмоции, интуиция, домашние дела",
                'action': "прислушивайтесь к чувствам, заботьтесь о комфорте"
            },
            'Mercury': {
                'focus': "общение, обучение, информация",
                'action': "учитесь, договаривайтесь, планируйте"
            },
            'Venus': {
                'focus': "отношения, красота, финансы",
                'action': "укрепляйте связи, создавайте гармонию"
            },
            'Mars': {
                'focus': "действия, энергия, конкуренция",
                'action': "будьте активны, решайте задачи"
            },
            'Jupiter': {
                'focus': "рост, возможности, путешествия",
                'action': "расширяйте горизонты, учитесь новому"
            },
            'Saturn': {
                'focus': "ответственность, структура, дисциплина",
                'action': "планируйте, организуйте, завершайте дела"
            },
            'Uranus': {
                'focus': "изменения, инновации, свобода",
                'action': "будьте гибкими, экспериментируйте"
            },
            'Neptune': {
                'focus': "интуиция, творчество, духовность",
                'action': "мечтайте, творите, доверяйте внутреннему голосу"
            },
            'Pluto': {
                'focus': "трансформация, глубина, власть",
                'action': "избавляйтесь от старого, обновляйтесь"
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
        Генерация простых рекомендаций на основе аспектов
        """
        recommendations = []

        try:
            # Сортируем аспекты по силе (самые сильные первые)
            strong_aspects = [a for a in aspects_data if a.get('strength', 0) > 0.7]
            sorted_aspects = sorted(strong_aspects, key=lambda x: x.get('strength', 0), reverse=True)

            # Берем только топ-3 самых сильных аспекта
            for aspect in sorted_aspects[:3]:
                rec = self._generate_single_aspect_recommendation(aspect)
                if rec:
                    recommendations.append(rec)

            # Если сильных аспектов мало, добавляем общие рекомендации
            if len(recommendations) < 2:
                general_recs = self._get_general_recommendations(aspects_data)
                recommendations.extend(general_recs[:2])

        except Exception as e:
            logger.error(f"❌ Ошибка генерации рекомендаций аспектов: {e}")
            recommendations = ["Сегодня стабильный астрологический фон - хорошее время для плановых дел"]

        return recommendations

    def _generate_single_aspect_recommendation(self, aspect: Dict) -> str:
        """Генерация рекомендации для одного аспекта"""
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

            # Получаем шаблоны для этого типа аспекта
            templates = self.aspect_templates.get(aspect_type, {}).get(rec_type, [])

            if templates:
                template = random.choice(templates)
                recommendation = template.format(transit=transit_ru, natal=natal_ru)

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
        """Общие рекомендации на основе общего анализа аспектов"""
        general_recs = []

        try:
            total_aspects = len(aspects_data)
            strong_aspects = len([a for a in aspects_data if a.get('strength', 0) > 0.7])

            # Рекомендации по количеству аспектов
            if total_aspects == 0:
                general_recs.append("🌙 Сегодня спокойный астрологический фон - хорошее время для отдыха и рутинных дел")
            elif total_aspects <= 3:
                general_recs.append("⚖️ Небольшое количество аспектов - день подходит для размеренной работы")
            elif total_aspects > 8:
                general_recs.append("🎯 Много астрологических влияний - будьте готовы к разным событиям")

            # Рекомендации по силе аспектов
            if strong_aspects >= 3:
                general_recs.append("💥 Несколько сильных аспектов - важный день для решений и действий")
            elif strong_aspects == 0 and total_aspects > 0:
                general_recs.append("🌊 Аспекты слабые - хорошее время для подготовки и планирования")

            # Рекомендации по ретроградным планетам
            retrograde_planets = self._detect_retrograde_influences(aspects_data)
            if retrograde_planets:
                planet_names = [self.planet_names_ru.get(p, p) for p in retrograde_planets]
                general_recs.append(
                    f"🔄 Влияние ретроградных планет ({', '.join(planet_names)}) - время для пересмотра и анализа")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка генерации общих рекомендаций: {e}")

        return general_recs

    def _detect_retrograde_influences(self, aspects_data: List[Dict]) -> List[str]:
        """Обнаружение ретроградных влияний в аспектах"""
        retrograde_planets = set()

        for aspect in aspects_data:
            # Проверяем транзитные планеты на ретроградность
            if aspect.get('transit_planet') in ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune',
                                                'Pluto']:
                # В реальной системе здесь была бы проверка на ретроградность
                # Сейчас используем случайное определение для демонстрации
                if random.random() < 0.3:  # 30% шанс что планета ретроградная
                    retrograde_planets.add(aspect['transit_planet'])

        return list(retrograde_planets)


# Глобальный экземпляр движка рекомендаций
aspect_recommendations = AspectRecommendationEngine()


recommendation_service.py

import logging
import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional

from backend.database import async_session, AIRecommendations
from sqlalchemy.future import select
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Упрощенный сервис для управления рекомендациями и кэшем
    Объединяет логику кэширования и работы с рекомендациями
    """

    def __init__(self):
        self.cache_ttl_days = 1  # Кэшируем на 1 день

    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Генерация хэша данных для кэширования"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()

    async def get_cached_recommendations(self, telegram_id: int, target_date: date, data_hash: str) -> Optional[
        Dict[str, Any]]:
        """Получение закэшированных рекомендаций"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(AIRecommendations).where(
                        and_(
                            AIRecommendations.telegram_id == telegram_id,
                            AIRecommendations.target_date == target_date,
                            AIRecommendations.data_hash == data_hash
                        )
                    )
                )
                cached = result.scalar_one_or_none()

                if cached:
                    logger.info(f"✅ Найдены кэшированные рекомендации для {telegram_id} на {target_date}")
                    return {
                        'recommendations': cached.recommendations,
                        'model_version': cached.model_version,
                        'from_cache': True
                    }

                return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения кэша для {telegram_id}: {e}")
            return None

    async def save_recommendations(self, telegram_id: int, target_date: date, data_hash: str,
                                   recommendations: str, model_version: str = 'gemma:2b') -> bool:
        """Сохранение рекомендаций в кэш"""
        try:
            async with async_session() as session:
                # Удаляем старые записи для этой даты
                await session.execute(
                    AIRecommendations.__table__.delete().where(
                        and_(
                            AIRecommendations.telegram_id == telegram_id,
                            AIRecommendations.target_date == target_date
                        )
                    )
                )

                # Сохраняем новые рекомендации
                new_recommendation = AIRecommendations(
                    telegram_id=telegram_id,
                    target_date=target_date,
                    data_hash=data_hash,
                    recommendations=recommendations,
                    model_version=model_version,
                    created_at=datetime.now()
                )

                session.add(new_recommendation)
                await session.commit()

                logger.info(f"💾 Рекомендации сохранены в кэш для {telegram_id} на {target_date}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения рекомендаций для {telegram_id}: {e}")
            return False

    async def cleanup_old_recommendations(self, days_old: int = 7) -> int:
        """Очистка устаревших рекомендаций"""
        try:
            cutoff_date = date.today() - timedelta(days=days_old)

            async with async_session() as session:
                result = await session.execute(
                    AIRecommendations.__table__.delete().where(
                        AIRecommendations.target_date < cutoff_date
                    )
                )
                deleted_count = result.rowcount
                await session.commit()

                if deleted_count > 0:
                    logger.info(f"🗑️ Удалено {deleted_count} устаревших рекомендаций")

                return deleted_count

        except Exception as e:
            logger.error(f"❌ Ошибка очистки рекомендаций: {e}")
            return 0


# Глобальный экземпляр
recommendation_service = RecommendationService()


