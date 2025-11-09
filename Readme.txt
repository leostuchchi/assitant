проект personal_assistant

итоговая задача проекта: 
персонализированные основанные на расчетах и данных, рекоммендации человеку на один день. для развития, самореализации человека на базе модели ИИ.

текущая задача проекта: 
сбор, подготовка данных, произведение всех возможных, обоснованных, и необходимых расчетов. которые потребуются для наиболее полных, полезных, строго персонализированных рекоммендаций. итоговые рекоммендации впоследствии будут готовится моделью. 

логика проекта:
сбор данных пользователя (tegram bot)
подготовка натальной карты
подготовка психоматрицы
расчет биоритмов
подготовка рекоммендаций на один день, на основе: натальной карты, психоматрицы, биоритмов
 позже будут добавлены расчеты и добавление к рекоммендациям лунных фаз
передача всех необходимых для ИИ данных в модуль assistant (все собранные и расчитаные данные)
 позже будет подключена модель для оптимизации рекоммендаций
вывод рекоммендаций на один день пользователю (telegram bot)

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

data_base p_assistant_bd: postges


-- Таблица пользователей
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    birth_city VARCHAR(100) NOT NULL,
    profession VARCHAR(100),
    job_position VARCHAR(100),
    current_city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Обновляем таблицу натальных карт
CREATE TABLE user_natal_charts (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    natal_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица психоматриц (нумерология)
CREATE TABLE psyho_matrix (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    matrix_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предсказаний (оставляем как есть)
CREATE TABLE natal_predictions (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    predictions JSONB NOT NULL,
    assistant_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_birth_date ON users(birth_date);
CREATE INDEX idx_user_natal_charts_telegram_id ON user_natal_charts(telegram_id);
CREATE INDEX idx_psyho_matrix_telegram_id ON psyho_matrix(telegram_id);
CREATE INDEX idx_natal_predictions_telegram_id ON natal_predictions(telegram_id);

-- Даем права пользователю
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pers_assist;

select * from psyho_matrix


-- Таблица для биоритмов
CREATE TABLE biorhythms (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    biorhythm_data JSONB NOT NULL,
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого поиска
CREATE INDEX idx_biorhythms_telegram_id ON biorhythms(telegram_id);
CREATE INDEX idx_biorhythms_calculation_date ON biorhythms(calculation_date);

docker-compose.yml:
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: postgres_astrology
    environment:
      POSTGRES_DB: p_assistant_bd
      POSTGRES_USER: pers_assist
      POSTGRES_PASSWORD: astra123  # Простой пароль без специальных символов
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pers_assist -d p_assistant_bd"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  
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
from datetime import datetime, date
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


# Создаем клавиатуру с двумя основными кнопками
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Расчет натальной карты")],
            [KeyboardButton(text="📅 Рекомендации на сегодня")],
        ],
        resize_keyboard=True
    )


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда начала работы с ботом"""
    welcome_text = """
👋 Добро пожаловать в ваш персональный ассистент!

Я помогу вам получать персонализированные рекомендации на основе:
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
            "📊 Начнем сбор данных для персонализированных рекомендаций!\n\n"
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
    """Обработка должности и завершение сбора данных"""
    job_position = message.text.strip()
    if job_position.lower() == 'нет':
        job_position = None

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
            job_position=job_position
        )

        if result['success']:
            await message.answer(
                "🎉 Поздравляем! Все данные успешно собраны!\n\n"
                "Теперь вы можете получать персонализированные рекомендации:",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result['message']}\n\n"
                "Попробуйте начать сбор данных заново.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при сохранении данных: {str(e)}\n\n"
            "Попробуйте начать сбор данных заново.",
            reply_markup=get_main_keyboard()
        )

    await state.clear()


@router.message(lambda message: message.text == "📅 Рекомендации на сегодня")
async def get_todays_recommendations(message: types.Message):
    """Получение рекомендаций на сегодня"""

    # Проверяем наличие данных
    status = await assistant.get_user_data_status(message.from_user.id)
    if not status['is_complete']:
        await message.answer(
            "❌ Сначала необходимо собрать данные для рекомендаций!\n"
            "Нажмите '📊 Расчет натальной карты'",
            reply_markup=get_main_keyboard()
        )
        return

    processing_msg = await message.answer("🔄 Формирую рекомендации на сегодня...")

    try:
        result = await assistant.get_todays_recommendations(message.from_user.id)

        if result['success']:
            await message.answer(result['recommendations'], parse_mode="Markdown")
        else:
            await message.answer(result['message'])

    except Exception as e:
        logger.error(f"Ошибка получения рекомендаций на сегодня: {e}")
        await message.answer(
            "❌ Произошла ошибка при формировании рекомендаций\n"
            "Попробуйте позже или обратитесь в поддержку."
        )

    await processing_msg.delete()


@router.message()
async def handle_other_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    await message.answer(
        "Выберите действие из меню ниже:",
        reply_markup=get_main_keyboard()
    )


__init__.py

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

assistant.py:

from backend.user_services import create_or_update_user, get_user_profile, update_user_profession
from backend.chart_services import create_and_save_natal_chart, get_user_natal_chart
from backend.matrix_services import calculate_and_save_psyho_matrix, get_user_matrix
from backend.prediction_services import generate_and_save_prediction, get_todays_prediction, \
    format_prediction_for_display
from backend.biorhythm_services import calculate_and_save_biorhythms, get_user_biorhythms
from backend.database import async_session
from datetime import datetime, date, timedelta
from backend.moon import calculate_lunar_phase
import logging

logger = logging.getLogger(__name__)


class PersonalAssistant:
    """Главный класс помощника для управления всеми данными и рекомендациями"""

    def __init__(self):
        pass

    async def collect_user_data(self, telegram_id: int, birth_date: date, birth_time: datetime.time,
                                birth_city: str, current_city: str = None, profession: str = None,
                                job_position: str = None):
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
                        job_position=job_position
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

    async def update_professional_info(self, telegram_id: int, current_city: str, profession: str,
                                       job_position: str = None):
        """Обновление профессиональной информации"""
        try:
            await update_user_profession(telegram_id, profession, job_position)

            # Обновляем город проживания
            user_profile = await get_user_profile(telegram_id)
            if user_profile:
                await create_or_update_user(
                    telegram_id=telegram_id,
                    birth_date=user_profile['birth_date'],
                    birth_time=user_profile['birth_time'],
                    birth_city=user_profile['birth_city'],
                    current_city=current_city,
                    profession=profession,
                    job_position=job_position
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

    async def get_todays_recommendations(self, telegram_id: int):
        """Получение рекомендаций на сегодня"""
        try:
            target_date = date.today()
            logger.info(f"📅 Формирование рекомендаций на сегодня для {telegram_id}")

            # Генерируем предсказание на сегодня
            prediction = await generate_and_save_prediction(telegram_id, target_date)

            # Форматируем для отображения - теперь это строка
            formatted_prediction = await format_prediction_for_display(prediction)

            # Добавляем лунную фазу
            lunar_phase = calculate_lunar_phase(target_date)

            # ✅ Теперь formatted_prediction - это строка, а не список
            final_recommendations = f"{formatted_prediction}\n\n🌙 Текущая лунная фаза: {lunar_phase}"

            # Вывод рекомендаций для отладки
            print(f"Recommendations for user {telegram_id} on {target_date.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': target_date.isoformat(),
                'recommendations': final_recommendations,  # ✅ Теперь это строка
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на сегодня для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на сегодня: {str(e)}"
            }

    async def get_tomorrows_recommendations(self, telegram_id: int):
        """Получение рекомендаций на завтра"""
        try:
            tomorrow = date.today() + timedelta(days=1)
            logger.info(f"📅 Формирование рекомендаций на завтра ({tomorrow}) для {telegram_id}")

            prediction = await generate_and_save_prediction(telegram_id, tomorrow)
            formatted_prediction = await format_prediction_for_display(prediction)

            lunar_phase = calculate_lunar_phase(tomorrow)
            final_recommendations = f"{formatted_prediction}\n\n🌙 Лунная фаза на завтра: {lunar_phase}"

            print(f"Recommendations for user {telegram_id} on {tomorrow.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': tomorrow.isoformat(),
                'recommendations': final_recommendations,
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на завтра для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на завтра: {str(e)}"
            }

    async def get_date_recommendations(self, telegram_id: int, target_date: date):
        """Получение рекомендаций на выбранную дату"""
        try:
            logger.info(f"📅 Формирование рекомендаций на {target_date} для {telegram_id}")

            if target_date < date.today():
                return {
                    'success': False,
                    'message': "❌ Нельзя получить рекомендации для прошедших дат"
                }

            prediction = await generate_and_save_prediction(telegram_id, target_date)
            formatted_prediction = await format_prediction_for_display(prediction)

            lunar_phase = calculate_lunar_phase(target_date)
            final_recommendations = f"{formatted_prediction}\n\n🌙 Лунная фаза на {target_date}: {lunar_phase}"

            print(f"Recommendations for user {telegram_id} on {target_date.isoformat()}:")
            print(final_recommendations)

            return {
                'success': True,
                'date': target_date.isoformat(),
                'recommendations': final_recommendations,
                'raw_data': prediction,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендаций на {target_date} для {telegram_id}: {e}")
            return {
                'success': False,
                'message': f"❌ Не удалось получить рекомендации на выбранную дату: {str(e)}"
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

            data_status = await self.get_user_data_status(telegram_id)
            prediction_stats = await get_prediction_statistics(telegram_id)
            biorhythm_stats = await get_biorhythm_statistics(telegram_id)

            return {
                'data_status': data_status,
                'prediction_stats': prediction_stats,
                'biorhythm_stats': biorhythm_stats,
                'calculated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
            return {
                'data_status': {},
                'prediction_stats': {},
                'biorhythm_stats': {},
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

biorhythm_services.py:

from backend.database import async_session, Biorhythms
from backend.biorhythm_calculator import BiorhythmCalculator
from backend.user_services import get_user_profile
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import date, datetime
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
from sqlalchemy import Column, BigInteger, JSON, TIMESTAMP, String, Date, Time, Text, ForeignKey
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
        # Русские названия для пользователя
        self.planet_names_ru = {
            'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
            'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
            'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун', 'Pluto': 'Плутон'
        }
        self.sign_names_ru = {
            'Aries': 'Овен', 'Taurus': 'Телец', 'Gemini': 'Близнецы',
            'Cancer': 'Рак', 'Leo': 'Лев', 'Virgo': 'Дева',
            'Libra': 'Весы', 'Scorpio': 'Скорпион', 'Sagittarius': 'Стрелец',
            'Capricorn': 'Козерог', 'Aquarius': 'Водолей', 'Pisces': 'Рыбы'
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
                    aspects.append({
                        'transit_planet': t_planet,
                        'natal_planet': n_planet,
                        'aspect': aspect_info[0],
                        'exact_angle': aspect_info[1],
                        'actual_angle': angle,
                        'orb': abs(angle - aspect_info[1]),
                        'strength': 1.0 - (abs(angle - aspect_info[1]) / aspect_info[2])
                    })
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

    def get_planet_influence(self, planet_name):
        """Определяет сферу влияния планеты на основе астрологических принципов"""
        influences = {
            'Sun': 'личную энергию, творчество, самореализацию',
            'Moon': 'эмоции, интуицию, домашние дела',
            'Mercury': 'общение, обучение, документы',
            'Venus': 'отношения, финансы, искусство',
            'Mars': 'действия, инициативу, спорт',
            'Jupiter': 'расширение, возможности, путешествия',
            'Saturn': 'ответственность, карьеру, долгосрочные планы',
            'Uranus': 'изменения, инновации, неожиданные события',
            'Neptune': 'интуицию, творчество, духовность',
            'Pluto': 'трансформацию, глубокие изменения'
        }
        return influences.get(planet_name, 'личное развитие')

    def get_aspect_meaning(self, aspect_type, strength):
        """Получает значение аспекта в зависимости от силы на основе астрологических принципов"""
        if aspect_type == 'conjunction':
            if strength > 0.7:
                return "мощное соединение - время начинаний"
            else:
                return "соединение - новые возможности"
        elif aspect_type == 'opposition':
            if strength > 0.7:
                return "сильная оппозиция - важные решения"
            else:
                return "оппозиция - требует баланса"
        elif aspect_type == 'square':
            if strength > 0.7:
                return "напряженный квадрат - преодоление препятствий"
            else:
                return "квадрат - вызовы для роста"
        elif aspect_type == 'trine':
            if strength > 0.7:
                return "гармоничный трин - благоприятное время"
            else:
                return "трин - поддержка и удача"
        elif aspect_type == 'sextile':
            if strength > 0.7:
                return "благоприятный секстиль - хорошие возможности"
            else:
                return "секстиль - шансы для развития"
        return "влияние на вашу энергию"

    def generate_personal_recommendations(self, aspects, transits):
        """Генерация персонализированных рекомендаций на основе РАСЧЕТОВ аспектов"""
        recommendations = []
        warnings = []

        # Анализируем самые сильные аспекты (топ-3)
        strong_aspects = [a for a in aspects if a['strength'] > 0.6][:3]

        for aspect in strong_aspects:
            transit_planet_ru = self.planet_names_ru.get(aspect['transit_planet'], aspect['transit_planet'])
            natal_planet_ru = self.planet_names_ru.get(aspect['natal_planet'], aspect['natal_planet'])
            influence_area = self.get_planet_influence(aspect['natal_planet'])
            aspect_meaning = self.get_aspect_meaning(aspect['aspect'], aspect['strength'])

            recommendation = f"{transit_planet_ru} {aspect_meaning} в сфере {influence_area}"

            if aspect['aspect'] in ['trine', 'sextile', 'conjunction']:
                # Благоприятные аспекты на основе РАСЧЕТОВ
                if aspect['aspect'] == 'conjunction':
                    actions = {
                        'Sun': 'начинайте новые проекты, проявляйте инициативу',
                        'Moon': 'доверяйте интуиции, займитесь домом',
                        'Mercury': 'общайтесь, учитесь, подписывайте документы',
                        'Venus': 'укрепляйте отношения, занимайтесь творчеством',
                        'Mars': 'действуйте решительно, занимайтесь спортом',
                        'Jupiter': 'расширяйте горизонты, путешествуйте',
                        'Saturn': 'стройте долгосрочные планы, берите ответственность',
                        'Uranus': 'экспериментируйте, будьте открыты новому',
                        'Neptune': 'развивайте интуицию, занимайтесь творчеством',
                        'Pluto': 'трансформируйте старые привычки'
                    }
                elif aspect['aspect'] in ['trine', 'sextile']:
                    actions = {
                        'Sun': 'используйте свою энергию для творчества',
                        'Moon': 'положитесь на внутренние ощущения',
                        'Mercury': 'эффективно общайтесь и договаривайтесь',
                        'Venus': 'гармонизируйте отношения и финансы',
                        'Mars': 'реализуйте планы с энтузиазмом',
                        'Jupiter': 'используйте расширяющиеся возможности',
                        'Saturn': 'стройте прочный фундамент',
                        'Uranus': 'внедряйте инновационные идеи',
                        'Neptune': 'развивайте духовные практики',
                        'Pluto': 'глубоко трансформируйтесь'
                    }

                action = actions.get(aspect['natal_planet'], 'используйте эту энергию для роста')
                recommendations.append(f"{recommendation}. {action} (сила аспекта: {aspect['strength']:.2f})")

            else:
                # Сложные аспекты (квадрат, оппозиция) на основе РАСЧЕТОВ
                cautions = {
                    'Sun': 'избегайте конфликтов, будьте дипломатичны',
                    'Moon': 'контролируйте эмоции, избегайте импульсивности',
                    'Mercury': 'проверяйте информацию, избегайте споров',
                    'Venus': 'будьте осторожны в отношениях и финансах',
                    'Mars': 'избегайте рисков, действуйте обдуманно',
                    'Jupiter': 'не переоценивайте возможности',
                    'Saturn': 'не избегайте ответственности, но и не перегружайтесь',
                    'Uranus': 'будьте готовы к неожиданностям',
                    'Neptune': 'различайте иллюзии и реальность',
                    'Pluto': 'избегайте манипуляций и давления'
                }

                caution = cautions.get(aspect['natal_planet'], 'будьте внимательны и осторожны')
                warnings.append(f"{recommendation}. {caution} (сила аспекта: {aspect['strength']:.2f})")

        # Добавляем информацию о ретроградных планетах на основе РАСЧЕТОВ
        retrograde_planets = [p for p, data in transits.items() if data.get('retrograde')]
        if retrograde_planets:
            retro_names = [self.planet_names_ru.get(p, p) for p in retrograde_planets]
            if len(retro_names) > 0:
                warnings.append(f"Ретроградные {', '.join(retro_names)} - время пересмотра и анализа")

        # Если аспектов мало, добавляем рекомендации на основе общей картины РАСЧЕТОВ
        if not recommendations and not warnings:
            total_aspects = len(aspects)
            if total_aspects > 0:
                avg_strength = sum(a['strength'] for a in aspects) / total_aspects
                recommendations.append(
                    f"Наблюдается {total_aspects} аспектов со средней силой {avg_strength:.2f} - следите за изменениями в соответствующих сферах")
            else:
                # Если аспектов нет вообще - это тоже результат расчета
                recommendations.append(
                    "Сегодня минимальная астрологическая активность - хороший день для рутинных дел и планирования")

        return recommendations[:4], warnings[:3]  # Ограничиваем количество

    def analyze_natal_elements(self):
        """Анализирует элементный баланс натальной карты на основе РАСЧЕТОВ"""
        if 'ml_features' in self.natal_chart and 'element_balance' in self.natal_chart['ml_features']:
            return self.natal_chart['ml_features']['element_balance']
        return None

    def get_element_recommendation(self, elements):
        """Рекомендации на основе РАСЧЕТОВ элементного баланса"""
        if not elements:
            return None

        max_element = max(elements.items(), key=lambda x: x[1])
        element_value = max_element[1]

        recommendations = {
            'fire': f"Доминирует огонь ({element_value} планет) - используйте свою энергию и инициативу для новых начинаний",
            'earth': f"Доминирует земля ({element_value} планет) - сосредоточьтесь на практических задачах и стабильности",
            'air': f"Доминирует воздух ({element_value} планет) - развивайте общение, обучение и интеллектуальную деятельность",
            'water': f"Доминирует вода ({element_value} планет) - доверяйте интуиции и развивайте эмоциональную чувствительность"
        }

        return recommendations.get(max_element[0])

    def generate_prediction(self, target_date):
        """Основной метод генерации предсказания на основе РАСЧЕТОВ"""
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

            # Генерируем персонализированные рекомендации и предостережения на основе РАСЧЕТОВ
            recommendations, warnings = self.generate_personal_recommendations(aspects, transits)

            # Добавляем рекомендации на основе элементного баланса если есть
            element_balance = self.analyze_natal_elements()
            if element_balance:
                element_recommendation = self.get_element_recommendation(element_balance)
                if element_recommendation and len(recommendations) < 4:
                    recommendations.append(element_recommendation)

            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'significant_aspects': aspects[:5],
                'recommendations': recommendations,
                'warnings': warnings,
                'transits_count': len(transits),
                'aspects_count': len(aspects),
                'strong_aspects_count': len([a for a in aspects if a['strength'] > 0.7])
            }

        except Exception as e:
            # В случае ошибки возвращаем пустое предсказание с информацией об ошибке
            return {
                'prediction_date': target_date.strftime('%Y-%m-%d'),
                'significant_aspects': [],
                'recommendations': [f"Ошибка расчета: {str(e)} - обратитесь к администратору"],
                'warnings': ["Временные технические трудности при расчете аспектов"],
                'transits_count': 0,
                'aspects_count': 0,
                'strong_aspects_count': 0,
                'calculation_error': True
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
from backend.biorhythm_services import calculate_and_save_biorhythms
from sqlalchemy.future import select
from sqlalchemy import func
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


class PredictionCombiner:
    """Класс для объединения астрологических предсказаний и биоритмов"""

    def __init__(self):
        pass

    def combine_recommendations(self, astro_prediction: dict, biorhythm_data: dict) -> list:
        """Объединение рекомендаций из астрологии и биоритмов на основе РАСЧЕТОВ"""

        # Берем рекомендации из обоих источников
        astro_recommendations = astro_prediction.get('recommendations', [])
        biorhythm_recommendations = biorhythm_data.get('recommendations', [])

        # Объединяем рекомендации
        all_recommendations = astro_recommendations + biorhythm_recommendations

        # Сортируем по приоритету на основе РАСЧЕТОВ
        priority_recommendations = self._prioritize_recommendations(all_recommendations)

        return priority_recommendations[:8]  # Не более 8 рекомендаций

    def _prioritize_recommendations(self, recommendations: list) -> list:
        """Приоритизация рекомендаций на основе РАСЧЕТОВ"""
        high_priority = []
        medium_priority = []
        low_priority = []

        for rec in recommendations:
            rec_lower = rec.lower()

            # Высокий приоритет - предостережения и критические дни на основе РАСЧЕТОВ
            if any(word in rec_lower for word in
                   ['осторожн', 'избегай', 'опасн', 'критич', 'не рискуй', 'береги', 'ретроградн']):
                high_priority.append(rec)
            # Средний приоритет - активные действия на основе РАСЧЕТОВ
            elif any(word in rec_lower for word in ['идеальн', 'отличн', 'благоприятн', 'используй', 'высок', 'пик']):
                medium_priority.append(rec)
            # Низкий приоритет - информационные рекомендации
            else:
                low_priority.append(rec)

        return high_priority + medium_priority + low_priority

    def generate_energy_analysis(self, astro_prediction: dict, biorhythm_data: dict) -> str:
        """Анализ энергетического состояния на основе РАСЧЕТОВ обоих методов"""

        # Данные из биоритмов
        energy_level = biorhythm_data.get('overall_energy', {}).get('level', 'средний')
        energy_percentage = biorhythm_data.get('overall_energy', {}).get('percentage', 50)

        # Данные из астрологии
        aspects = astro_prediction.get('significant_aspects', [])
        strong_aspects = [a for a in aspects if a.get('strength', 0) > 0.7]
        challenging_aspects = [a for a in strong_aspects if a.get('aspect') in ['square', 'opposition']]
        harmonious_aspects = [a for a in strong_aspects if a.get('aspect') in ['trine', 'sextile', 'conjunction']]

        # Формируем анализ на основе РАСЧЕТОВ
        analysis_parts = []

        # Анализ энергии из биоритмов
        analysis_parts.append(f"⚡ Уровень энергии: {energy_level} ({energy_percentage:.1f}%)")

        # Анализ аспектов из астрологии
        if challenging_aspects:
            analysis_parts.append(f"🎯 Сложных аспектов: {len(challenging_aspects)}")

        if harmonious_aspects:
            analysis_parts.append(f"🌟 Гармоничных аспектов: {len(harmonious_aspects)}")

        # Общий вывод на основе РАСЧЕТОВ
        if energy_percentage > 70 and len(challenging_aspects) == 0:
            analysis_parts.append("✅ Идеальный день для активных действий")
        elif energy_percentage < 30 and len(challenging_aspects) > 2:
            analysis_parts.append("⚠️ Сохраняйте спокойствие, избегайте нагрузок")
        elif len(harmonious_aspects) > len(challenging_aspects):
            analysis_parts.append("📊 Преобладают гармоничные влияния")
        else:
            analysis_parts.append("📈 Сбалансированный энергетический профиль")

        return " | ".join(analysis_parts)

    def create_daily_schedule(self, biorhythm_data: dict) -> list:
        """Создание рекомендуемого расписания дня на основе РАСЧЕТОВ биоритмов"""

        cycles = biorhythm_data.get('cycles', {})
        schedule = []

        # Утренние рекомендации на основе РАСЧЕТОВ интеллектуального цикла
        morning_rec = "🌅 Утро: "
        intellectual_value = cycles.get('intellectual', {}).get('value', 0)
        if intellectual_value > 0.3:
            morning_rec += f"планирование и анализ (интеллектуальный цикл: {intellectual_value:.2f})"
        else:
            morning_rec += f"легкая разминка и рутина (интеллектуальный цикл: {intellectual_value:.2f})"
        schedule.append(morning_rec)

        # Дневные рекомендации на основе РАСЧЕТОВ физического цикла
        day_rec = "🌞 День: "
        physical_value = cycles.get('physical', {}).get('value', 0)
        if physical_value > 0.5:
            day_rec += f"активная работа и движение (физический цикл: {physical_value:.2f})"
        elif physical_value > 0:
            day_rec += f"умеренная активность (физический цикл: {physical_value:.2f})"
        else:
            day_rec += f"спокойная деятельность (физический цикл: {physical_value:.2f})"
        schedule.append(day_rec)

        # Вечерние рекомендации на основе РАСЧЕТОВ эмоционального цикла
        evening_rec = "🌙 Вечер: "
        emotional_value = cycles.get('emotional', {}).get('value', 0)
        if emotional_value > 0.4:
            evening_rec += f"общение и творчество (эмоциональный цикл: {emotional_value:.2f})"
        else:
            evening_rec += f"отдых и уединение (эмоциональный цикл: {emotional_value:.2f})"
        schedule.append(evening_rec)

        return schedule

    def _extract_critical_notes(self, astro_prediction: dict, biorhythm_data: dict) -> list:
        """Извлечение критических замечаний на основе РАСЧЕТОВ обоих источников"""
        critical_notes = []

        # Критические дни из биоритмов на основе РАСЧЕТОВ
        critical_days = biorhythm_data.get('critical_days', [])
        if critical_days:
            for day in critical_days:
                critical_notes.append(f"⚠️ {day.get('description', 'Критический день по биоритмам')}")

        # Сложные аспекты из астрологии на основе РАСЧЕТОВ
        aspects = astro_prediction.get('significant_aspects', [])
        challenging_aspects = [a for a in aspects if
                               a.get('aspect') in ['square', 'opposition'] and a.get('strength', 0) > 0.7]

        for aspect in challenging_aspects[:2]:  # Не более 2 самых сильных
            planet1 = aspect.get('transit_planet', '')
            planet2 = aspect.get('natal_planet', '')
            aspect_type = aspect.get('aspect', '')
            strength = aspect.get('strength', 0)

            planet1_ru = self._get_planet_name_ru(planet1)
            planet2_ru = self._get_planet_name_ru(planet2)

            if aspect_type == 'square':
                critical_notes.append(f"🔺 Напряженный аспект: {planet1_ru} - {planet2_ru} (сила: {strength:.2f})")
            elif aspect_type == 'opposition':
                critical_notes.append(f"⚖️ Сложный выбор: {planet1_ru} - {planet2_ru} (сила: {strength:.2f})")

        # Предостережения из астрологии
        warnings = astro_prediction.get('warnings', [])
        critical_notes.extend(warnings[:2])  # Не более 2 предостережений

        return critical_notes[:4]  # Не более 4 критических заметок

    def _get_planet_name_ru(self, planet_name: str) -> str:
        """Получение русского названия планеты"""
        planet_names_ru = {
            'Sun': 'Солнце', 'Moon': 'Луна', 'Mercury': 'Меркурий',
            'Venus': 'Венера', 'Mars': 'Марс', 'Jupiter': 'Юпитер',
            'Saturn': 'Сатурн', 'Uranus': 'Уран', 'Neptune': 'Нептун', 'Pluto': 'Плутон'
        }
        return planet_names_ru.get(planet_name, planet_name)


async def generate_and_save_prediction(telegram_id: int, target_date: date):
    """Генерация и сохранение предсказания с биоритмами на основе РАСЧЕТОВ"""
    try:
        logger.info(f"🔮 Генерация предсказания для пользователя {telegram_id} на {target_date}")

        # Получаем натальную карту пользователя
        natal_data = await get_user_natal_chart(telegram_id)
        if not natal_data:
            logger.warning(f"⚠️ Натальная карта не найдена для пользователя {telegram_id}")
            raise ValueError("Натальная карта не найдена. Сначала создайте натальную карту с помощью /start")

        logger.info(f"✅ Натальная карта найдена для {telegram_id}")

        # Рассчитываем биоритмы на основе РАСЧЕТОВ
        biorhythm_data = await calculate_and_save_biorhythms(telegram_id, target_date)
        logger.info(f"✅ Биоритмы рассчитаны для {telegram_id}")

        # Генерируем астрологическое предсказание на основе РАСЧЕТОВ
        predictor = AstroPredictor(natal_data)
        astro_prediction = predictor.generate_prediction(target_date)
        logger.info(f"✅ Астрологическое предсказание сгенерировано для {telegram_id}")

        # Объединяем предсказания на основе РАСЧЕТОВ
        combiner = PredictionCombiner()
        combined_recommendations = combiner.combine_recommendations(astro_prediction, biorhythm_data)
        energy_analysis = combiner.generate_energy_analysis(astro_prediction, biorhythm_data)
        daily_schedule = combiner.create_daily_schedule(biorhythm_data)
        critical_notes = combiner._extract_critical_notes(astro_prediction, biorhythm_data)

        # Создаем финальное предсказание на основе РАСЧЕТОВ
        final_prediction = {
            'prediction_date': target_date.isoformat(),
            'energy_analysis': energy_analysis,
            'biorhythms_summary': {
                'overall_energy': biorhythm_data.get('overall_energy', {}),
                'physical_cycle': biorhythm_data.get('cycles', {}).get('physical', {}),
                'emotional_cycle': biorhythm_data.get('cycles', {}).get('emotional', {}),
                'intellectual_cycle': biorhythm_data.get('cycles', {}).get('intellectual', {}),
                'critical_days_count': len(biorhythm_data.get('critical_days', [])),
                'peak_days_count': len(biorhythm_data.get('peak_days', []))
            },
            'astro_summary': {
                'significant_aspects_count': len(astro_prediction.get('significant_aspects', [])),
                'strong_aspects_count': astro_prediction.get('strong_aspects_count', 0),
                'transits_count': astro_prediction.get('transits_count', 0),
                'key_aspects': astro_prediction.get('significant_aspects', [])[:3]
            },
            'combined_recommendations': combined_recommendations,
            'daily_schedule': daily_schedule,
            'critical_notes': critical_notes,

            # Полные данные для детального анализа
            'full_astro_prediction': astro_prediction,
            'full_biorhythm_data': biorhythm_data,

            # Мета-информация о расчетах
            'calculation_metadata': {
                'calculation_timestamp': datetime.now().isoformat(),
                'data_sources': ['astrology', 'biorhythms'],
                'calculation_methods': ['swiss_ephemeris', 'sine_wave_analysis']
            }
        }

        logger.info(f"✅ Комбинированное предсказание создано для {telegram_id}")

        # Сохраняем предсказание в БД
        async with async_session() as session:
            result = await session.execute(
                select(NatalPredictions).where(NatalPredictions.telegram_id == telegram_id)
            )
            existing_record = result.scalar_one_or_none()

            if existing_record:
                # Обновляем существующую запись
                existing_record.predictions = final_prediction
                existing_record.updated_at = func.now()
                logger.info(f"📝 Обновлено существующее предсказание для {telegram_id}")
            else:
                # Создаем новую запись
                new_record = NatalPredictions(
                    telegram_id=telegram_id,
                    predictions=final_prediction,
                    assistant_data={},
                )
                session.add(new_record)
                logger.info(f"🆕 Создано новое предсказание для {telegram_id}")

            await session.commit()
            logger.info(f"💾 Предсказание успешно сохранено в БД для {telegram_id}")

        return final_prediction

    except ValueError as e:
        logger.warning(f"❌ Ошибка валидации для {telegram_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации предсказания для {telegram_id}: {e}")
        raise Exception(f"Не удалось сгенерировать предсказание на основе расчетов: {str(e)}")


async def get_user_predictions(telegram_id: int):
    """Получение предсказаний пользователя"""
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
        logger.error(f"❌ Ошибка при получении предсказаний {telegram_id}: {e}")
        return None


async def get_todays_prediction(telegram_id: int):
    """Получение предсказания на сегодня"""
    try:
        today = datetime.now().date()

        # Получаем сохраненное предсказание
        predictions = await get_user_predictions(telegram_id)

        if predictions and predictions.get('prediction_date') == today.isoformat():
            logger.info(f"✅ Использовано сохраненное предсказание для {telegram_id}")
            return predictions

        # Если предсказания на сегодня нет, генерируем новое на основе РАСЧЕТОВ
        logger.info(f"🔄 Генерация нового предсказания для {telegram_id}")
        return await generate_and_save_prediction(telegram_id, today)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении сегодняшнего предсказания {telegram_id}: {e}")
        return None


async def format_prediction_for_display(prediction: dict) -> str:
    """Форматирование предсказания для отображения в боте на основе РАСЧЕТОВ"""
    if not prediction:
        return "❌ Не удалось получить предсказание на основе расчетов"

    try:
        lines = []
        prediction_date = prediction.get('prediction_date', 'сегодня')
        lines.append(f"🔮 **Ваше предсказание на {prediction_date}**")
        lines.append("")

        # Анализ энергии на основе РАСЧЕТОВ
        energy_analysis = prediction.get('energy_analysis', '')
        if energy_analysis:
            lines.append(f"⚡ {energy_analysis}")
            lines.append("")

        # Биоритмы на основе РАСЧЕТОВ
        biorhythms = prediction.get('biorhythms_summary', {})
        if biorhythms:
            overall_energy = biorhythms.get('overall_energy', {})
            lines.append(
                f"📊 **Биоритмы:** {overall_energy.get('level', 'средний').title()} уровень энергии ({overall_energy.get('percentage', 0):.1f}%)")

            physical = biorhythms.get('physical_cycle', {})
            emotional = biorhythms.get('emotional_cycle', {})
            intellectual = biorhythms.get('intellectual_cycle', {})

            lines.append(
                f"💪 Физический: {physical.get('phase', 'нейтральная')} ({physical.get('percentage', 0):.1f}%) - {physical.get('trend', 'стабильно')}")
            lines.append(
                f"😊 Эмоциональный: {emotional.get('phase', 'нейтральная')} ({emotional.get('percentage', 0):.1f}%) - {emotional.get('trend', 'стабильно')}")
            lines.append(
                f"🧠 Интеллектуальный: {intellectual.get('phase', 'нейтральная')} ({intellectual.get('percentage', 0):.1f}%) - {intellectual.get('trend', 'стабильно')}")
            lines.append("")

        # Астрологическая сводка на основе РАСЧЕТОВ
        astro_summary = prediction.get('astro_summary', {})
        if astro_summary:
            lines.append(
                f"🌟 **Астрология:** {astro_summary.get('significant_aspects_count', 0)} аспектов, {astro_summary.get('strong_aspects_count', 0)} сильных")
            lines.append("")

        # Расписание дня на основе РАСЧЕТОВ биоритмов
        schedule = prediction.get('daily_schedule', [])
        if schedule:
            lines.append("🕒 **Рекомендуемое расписание на основе биоритмов:**")
            for item in schedule:
                lines.append(f"   {item}")
            lines.append("")

        # Рекомендации на основе РАСЧЕТОВ
        recommendations = prediction.get('combined_recommendations', [])
        if recommendations:
            lines.append("💫 **Рекомендации на день (на основе расчетов):**")
            for i, rec in enumerate(recommendations[:6], 1):  # Не более 6 рекомендаций
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Критические заметки на основе РАСЧЕТОВ
        critical_notes = prediction.get('critical_notes', [])
        if critical_notes:
            lines.append("⚠️ **Обратите внимание (на основе расчетов):**")
            for note in critical_notes[:3]:  # Не более 3 заметок
                lines.append(f"   • {note}")
            lines.append("")

        # Информация о расчетах
        lines.append("📈 *Все рекомендации основаны на математических расчетах:*")
        lines.append("   • Астрологические транзиты и аспекты")
        lines.append("   • Биоритмы (физический, эмоциональный, интеллектуальный циклы)")
        lines.append("   • Статистический анализ влияний")

        # ✅ ВАЖНО: Возвращаем объединенную строку, а не список
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Ошибка форматирования предсказания: {e}")
        return "❌ Произошла ошибка при формировании предсказания на основе расчетов"


async def get_prediction_statistics(telegram_id: int) -> dict:
    """Получение статистики предсказаний пользователя"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return {}

        return {
            'last_calculation_date': prediction.get('prediction_date'),
            'biorhythm_energy': prediction.get('biorhythms_summary', {}).get('overall_energy', {}).get('percentage', 0),
            'astro_aspects_count': prediction.get('astro_summary', {}).get('significant_aspects_count', 0),
            'recommendations_count': len(prediction.get('combined_recommendations', [])),
            'critical_notes_count': len(prediction.get('critical_notes', []))
        }

    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики для {telegram_id}: {e}")
        return {}


async def validate_prediction_data(telegram_id: int) -> bool:
    """Проверка корректности данных предсказания"""
    try:
        prediction = await get_user_predictions(telegram_id)
        if not prediction:
            return False

        # Проверяем наличие обязательных полей
        required_fields = ['prediction_date', 'energy_analysis', 'combined_recommendations']
        for field in required_fields:
            if field not in prediction or not prediction[field]:
                return False

        # Проверяем что рекомендации не пустые
        if not prediction.get('combined_recommendations'):
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка валидации данных предсказания для {telegram_id}: {e}")
        return False


async def cleanup_old_predictions():
    """Очистка устаревших предсказаний (для администрирования)"""
    try:
        # В текущей структуре у нас только одно предсказание на пользователя
        # Эта функция может быть использована для будущих расширений
        logger.info("🔄 Очистка устаревших предсказаний не требуется в текущей структуре")
        return 0

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке предсказаний: {e}")
        return 0

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
            'characteristics': self._calculate_characteristics(matrix_numbers),
            'energy_level': self._analyze_energy(first_number),
            'life_purpose': self._analyze_life_purpose(fourth_number),
            'talents': self._analyze_talents(matrix_numbers),
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

    def _calculate_characteristics(self, matrix):
        """Расчет характеристик на основе матрицы"""
        characteristics = {
            'character': self._analyze_character(matrix),
            'energy': self._analyze_energy_level(matrix),
            'interest': self._analyze_interest(matrix),
            'health': self._analyze_health(matrix),
            'logic': self._analyze_logic(matrix),
            'labor': self._analyze_labor(matrix),
            'luck': self._analyze_luck(matrix),
            'duty': self._analyze_duty(matrix),
            'memory': self._analyze_memory(matrix)
        }
        return characteristics

    def _analyze_character(self, matrix):
        """Анализ характера по цифре 1 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_1 = matrix.get('1', 0)
        if count_1 == 1:
            return "Уравновешенный характер"
        elif count_1 == 2:
            return "Сильный характер, лидерские качества"
        elif count_1 >= 3:
            return "Очень сильный характер, возможна жесткость"
        else:
            return "Мягкий характер, нуждается в поддержке"

    def _analyze_energy_level(self, matrix):
        """Анализ энергии по цифре 2 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_2 = matrix.get('2', 0)
        if count_2 == 1:
            return "Средний уровень энергии"
        elif count_2 == 2:
            return "Высокая энергия, экстрасенсорные способности"
        elif count_2 >= 3:
            return "Очень высокая энергия, нужно учиться управлять"
        else:
            return "Низкая энергия, берегите силы"

    def _analyze_interest(self, matrix):
        """Анализ интересов по цифре 3 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_3 = matrix.get('3', 0)
        if count_3 == 1:
            return "Разносторонние интересы"
        elif count_3 >= 2:
            return "Глубокие интересы в точных науках"
        else:
            return "Творческие интересы"

    def _analyze_health(self, matrix):
        """Анализ здоровья по цифре 4 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_4 = matrix.get('4', 0)
        if count_4 == 1:
            return "Хорошее здоровье"
        elif count_4 >= 2:
            return "Отличное здоровье, выносливость"
        else:
            return "Внимание к здоровью"

    def _analyze_logic(self, matrix):
        """Анализ логики по цифре 5 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_5 = matrix.get('5', 0)
        if count_5 == 1:
            return "Практическая логика"
        elif count_5 >= 2:
            return "Сильная интуиция, предвидение"
        else:
            return "Образное мышление"

    def _analyze_labor(self, matrix):
        """Анализ трудолюбия по цифре 6 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_6 = matrix.get('6', 0)
        if count_6 == 1:
            return "Физический труд приносит удовольствие"
        elif count_6 >= 2:
            return "Трудоголик, любит ручной труд"
        else:
            return "Интеллектуальный труд"

    def _analyze_luck(self, matrix):
        """Анализ удачи по цифре 7 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_7 = matrix.get('7', 0)
        if count_7 == 1:
            return "Удача в мелочах"
        elif count_7 >= 2:
            return "Везение, ангел-хранитель"
        else:
            return "Нужно прилагать усилия"

    def _analyze_duty(self, matrix):
        """Анализ чувства долга по цифре 8 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_8 = matrix.get('8', 0)
        if count_8 == 1:
            return "Ответственность, надежность"
        elif count_8 >= 2:
            return "Сильное чувство долга"
        else:
            return "Свобода важнее обязательств"

    def _analyze_memory(self, matrix):
        """Анализ памяти по цифре 9 - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        count_9 = matrix.get('9', 0)
        if count_9 == 1:
            return "Хорошая память"
        elif count_9 >= 2:
            return "Отличная память, умственные способности"
        else:
            return "Практическая память"

    def _analyze_energy(self, first_number):
        """Анализ общего уровня энергии - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        if first_number < 10:
            return f"Низкая энергия (число {first_number}) - рекомендуется отдых и восстановление"
        elif first_number < 20:
            return f"Сбалансированная энергия (число {first_number}) - стабильность в действиях"
        else:
            return f"Высокая энергия (число {first_number}) - время активных действий"

    def _analyze_life_purpose(self, fourth_number):
        """Анализ жизненного предназначения - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        # Основано на нумерологическом значении четвертого числа
        purposes = {
            1: f"Лидерство и инициатива (число {fourth_number}) - ваше призвание вести за собой",
            2: f"Гармония и сотрудничество (число {fourth_number}) - ваш путь в партнерстве",
            3: f"Творчество и самовыражение (число {fourth_number}) - ваша миссия в искусстве",
            4: f"Стабильность и порядок (число {fourth_number}) - ваша задача в организации",
            5: f"Свобода и изменения (число {fourth_number}) - ваша судьба в трансформациях",
            6: f"Семья и ответственность (число {fourth_number}) - ваше предназначение в заботе",
            7: f"Знания и анализ (число {fourth_number}) - ваш дар в исследованиях",
            8: f"Деньги и власть (число {fourth_number}) - ваша сила в управлении",
            9: f"Служение и гуманизм (число {fourth_number}) - ваше призвание в помощи людям"
        }
        return purposes.get(fourth_number,
                            f"Многогранное предназначение (число {fourth_number}) - исследуйте разные пути")

    def _analyze_talents(self, matrix):
        """Анализ талантов на основе матрицы - ТОЛЬКО НА ОСНОВЕ РАСЧЕТОВ"""
        talents = []

        # Каждый талант основан на конкретных расчетах матрицы
        if matrix.get('3', 0) >= 2:
            talents.append(f"Технические способности (цифра 3: {matrix.get('3', 0)})")
        if matrix.get('5', 0) >= 1:
            talents.append(f"Интуиция и предвидение (цифра 5: {matrix.get('5', 0)})")
        if matrix.get('7', 0) >= 2:
            talents.append(f"Творческие способности (цифра 7: {matrix.get('7', 0)})")
        if matrix.get('9', 0) >= 2:
            talents.append(f"Аналитический ум (цифра 9: {matrix.get('9', 0)})")
        if matrix.get('2', 0) >= 2:
            talents.append(f"Экстрасенсорные способности (цифра 2: {matrix.get('2', 0)})")

        # Если талантов не найдено по расчетам, анализируем доминирующие цифры
        if not talents:
            max_digit = max(matrix.items(), key=lambda x: x[1])
            if max_digit[1] > 0:
                talents.append(f"Практические навыки (доминирующая цифра {max_digit[0]}: {max_digit[1]})")

        return talents

user_services.py:  

from backend.database import async_session, User
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


async def create_or_update_user(
        telegram_id: int,
        birth_date,
        birth_time,
        birth_city: str,
        profession: str = None,
        job_position: str = None,
        current_city: str = None
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
                if profession: user.profession = profession
                if job_position: user.job_position = job_position
                if current_city: user.current_city = current_city
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
                    current_city=current_city
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

moon.py

from datetime import date

def calculate_lunar_phase(target_date: date = None) -> str:
    if target_date is None:
        target_date = date.today()
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






