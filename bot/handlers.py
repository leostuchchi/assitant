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