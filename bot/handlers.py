from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, timedelta
import logging
import asyncio

from backend.assistant import assistant

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

# Глобальный словарь для отслеживания выполняющихся AI запросов
active_ai_requests = {}


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
            [KeyboardButton(text="📅 Получить рекомендации")],
            [KeyboardButton(text="📈 Статус данных"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


# Клавиатура для выбора даты
def get_date_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📅 Завтра")],
            [KeyboardButton(text="📅 Выбрать дату")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите дату..."
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


# Клавиатура только "Назад"
def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад в меню")]
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
• 🤖 AI-анализа всех данных

Выберите действие из меню ниже:
    """

    await message.answer(welcome_text, reply_markup=get_main_keyboard())


@router.message(lambda message: message.text == "🔙 Назад в меню")
async def go_back_to_main(message: types.Message, state: FSMContext):
    """Возврат в главное меню с очисткой состояния"""
    await state.clear()
    await message.answer(
        "Возвращаемся в главное меню:",
        reply_markup=get_main_keyboard()
    )


@router.message(lambda message: message.text == "📊 Расчет натальной карты")
async def start_data_collection(message: types.Message, state: FSMContext):
    """Начало сбора данных пользователя"""

    # Проверяем статус данных пользователя
    status = await assistant.get_user_data_status(message.from_user.id)

    if status['is_complete']:
        await message.answer(
            "✅ Ваши основные данные уже собраны!\n"
            "Если хотите обновить профессию или город, начните сбор данных заново.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "📊 Начнем сбор данных для персонализированных рекомендаций!\n\n"
            "Пожалуйста, введите вашу дату рождения в формате ГГГГ-ММ-ДД:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_date)


@router.message(DataCollectionStates.waiting_for_birth_date)
async def process_birth_date(message: types.Message, state: FSMContext):
    """Обработка даты рождения"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    try:
        birth_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(birth_date=birth_date)

        await message.answer(
            "✅ Дата рождения сохранена!\n\n"
            "Теперь введите время рождения в формате ЧЧ:ММ (24 часа):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_time)

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ГГГГ-ММ-ДД:",
            reply_markup=get_back_keyboard()
        )


@router.message(DataCollectionStates.waiting_for_birth_time)
async def process_birth_time(message: types.Message, state: FSMContext):
    """Обработка времени рождения"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    try:
        birth_time = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(birth_time=birth_time)

        await message.answer(
            "✅ Время рождения сохранено!\n\n"
            "Введите город рождения:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(DataCollectionStates.waiting_for_birth_city)

    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте формат ЧЧ:ММ:",
            reply_markup=get_back_keyboard()
        )


@router.message(DataCollectionStates.waiting_for_birth_city)
async def process_birth_city(message: types.Message, state: FSMContext):
    """Обработка города рождения"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    birth_city = message.text.strip()
    await state.update_data(birth_city=birth_city)

    await message.answer(
        "✅ Город рождения сохранен!\n\n"
        "Теперь введите город проживания:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DataCollectionStates.waiting_for_current_city)


@router.message(DataCollectionStates.waiting_for_current_city)
async def process_current_city(message: types.Message, state: FSMContext):
    """Обработка города проживания"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    current_city = message.text.strip()
    await state.update_data(current_city=current_city)

    await message.answer(
        "✅ Город проживания сохранен!\n\n"
        "Введите вашу специальность или профессию:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DataCollectionStates.waiting_for_profession)


@router.message(DataCollectionStates.waiting_for_profession)
async def process_profession(message: types.Message, state: FSMContext):
    """Обработка профессии"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    profession = message.text.strip()
    await state.update_data(profession=profession)

    await message.answer(
        "✅ Профессия сохранена!\n\n"
        "Введите вашу должность (если нет - напишите 'нет'):",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DataCollectionStates.waiting_for_job_position)


@router.message(DataCollectionStates.waiting_for_job_position)
async def process_job_position(message: types.Message, state: FSMContext):
    """Обработка должности и переход к выбору пола"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

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
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

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
        processing_msg = await message.answer("🔄 Сохраняем ваши данные...")

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

        await processing_msg.delete()

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
        logger.error(f"Ошибка при сохранении данных: {e}")
        await message.answer(
            f"❌ Произошла ошибка при сохранении данных: {str(e)}\n\n"
            "Попробуйте начать сбор данных заново.",
            reply_markup=get_main_keyboard()
        )

    await state.clear()


@router.message(lambda message: message.text == "📅 Получить рекомендации")
async def select_date_option(message: types.Message, state: FSMContext):
    """Выбор даты для получения рекомендаций"""
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
        "📅 Выберите дату для рекомендаций:",
        reply_markup=get_date_keyboard()
    )


@router.message(lambda message: message.text == "📅 Сегодня")
async def get_todays_data(message: types.Message):
    """Получение рекомендаций на сегодня"""
    await process_date_selection(message, date.today())


@router.message(lambda message: message.text == "📅 Завтра")
async def get_tomorrows_data(message: types.Message):
    """Получение рекомендаций на завтра"""
    tomorrow = date.today() + timedelta(days=1)
    await process_date_selection(message, tomorrow)


@router.message(lambda message: message.text == "📅 Выбрать дату")
async def request_custom_date(message: types.Message, state: FSMContext):
    """Запрос произвольной даты"""
    await message.answer(
        "Введите дату в формате ГГГГ-ММ-ДД:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(DateSelectionStates.waiting_for_custom_date)


@router.message(DateSelectionStates.waiting_for_custom_date)
async def process_custom_date(message: types.Message, state: FSMContext):
    """Обработка введенной пользователем даты"""
    if message.text == "🔙 Назад в меню":
        await go_back_to_main(message, state)
        return

    try:
        target_date = datetime.strptime(message.text, "%Y-%m-%d").date()

        # Проверяем что дата не в прошлом
        if target_date < date.today():
            await message.answer(
                "❌ Можно получить рекомендации только на сегодня или будущие даты",
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


def format_ai_recommendations(ai_recommendations: dict) -> str:
    """Форматирование AI рекомендаций для отображения"""
    try:
        if not ai_recommendations:
            return "🤖 AI рекомендации временно недоступны"

        lines = []

        # Профессиональные рекомендации
        if ai_recommendations.get('professional'):
            lines.append("💼 *Профессиональный фокус:*")
            for rec in ai_recommendations['professional'][:3]:
                lines.append(f"• {rec}")
            lines.append("")

        # Личная эффективность
        if ai_recommendations.get('personal_effectiveness'):
            lines.append("⚡ *Личная эффективность:*")
            for rec in ai_recommendations['personal_effectiveness'][:3]:
                lines.append(f"• {rec}")
            lines.append("")

        # Эмоциональный баланс
        if ai_recommendations.get('emotional'):
            lines.append("❤️ *Эмоциональный баланс:*")
            for rec in ai_recommendations['emotional'][:2]:
                lines.append(f"• {rec}")
            lines.append("")

        # Ключевая задача дня
        if ai_recommendations.get('daily_focus'):
            lines.append("🎯 *Ключевая задача дня:*")
            for rec in ai_recommendations['daily_focus'][:1]:
                lines.append(f"• {rec}")
            lines.append("")

        # Если структурированных данных нет, используем сырой текст
        if not lines and ai_recommendations.get('raw_recommendations'):
            return ai_recommendations['raw_recommendations']

        return "\n".join(lines) if lines else "🤖 Рекомендации будут доступны позже"

    except Exception as e:
        logger.error(f"Ошибка форматирования AI рекомендаций: {e}")
        return "🤖 Рекомендации временно недоступны"


async def send_ai_recommendations_async(telegram_id: int, target_date: date,
                                        prediction_data: dict, user_profile: dict,
                                        message: types.Message = None):
    """
    Асинхронная отправка AI рекомендаций отдельным процессом
    Работает даже если пользователь вышел из чата
    """
    try:
        logger.info(f"🔄 Запуск асинхронной генерации AI рекомендаций для {telegram_id}")

        # Получаем AI рекомендации через assistant
        ai_result = await assistant.get_ai_recommendations_async(
            telegram_id,
            target_date,
            prediction_data,
            user_profile
        )

        # Форматируем рекомендации
        recommendations_text = format_ai_recommendations(ai_result.get('recommendations', {}))

        # Отправляем сообщение пользователю
        bot = message.bot if message else None
        if not bot:
            from bot.main import setup_bot
            _, bot = await setup_bot()

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=f"🤖 *AI рекомендации на {target_date.strftime('%d.%m.%Y')}:*\n\n{recommendations_text}",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"✅ AI рекомендации отправлены пользователю {telegram_id}")

            # Удаляем из активных запросов
            if telegram_id in active_ai_requests:
                del active_ai_requests[telegram_id]

        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить AI рекомендации пользователю {telegram_id}: {e}")
            # Пользователь мог выйти из чата - это нормально

    except Exception as e:
        logger.error(f"❌ Ошибка в асинхронной отправке AI рекомендаций для {telegram_id}: {e}")
        # Удаляем из активных запросов даже при ошибке
        if telegram_id in active_ai_requests:
            del active_ai_requests[telegram_id]


async def process_date_selection(message: types.Message, target_date: date):
    """
    Общая обработка выбранной даты
    Данные расчетов показываются сразу, AI рекомендации приходят асинхронно
    """
    calculation_msg = await message.answer(
        f"🔄 *Расчеты на {target_date.strftime('%d.%m.%Y')}...*",
        parse_mode="Markdown"
    )

    try:
        # 1. ПОЛУЧАЕМ ДАННЫЕ РАСЧЕТОВ БЕЗ AI (мгновенно)
        result = await assistant.get_recommendations(
            message.from_user.id,
            target_date,
            include_ai=False  # ⚡ НЕ ЖДЕМ AI - данные приходят сразу!
        )

        if not result['success']:
            await calculation_msg.delete()
            await message.answer(
                result['message'],
                reply_markup=get_main_keyboard()
            )
            return

        # 2. СРАЗУ ПОКАЗЫВАЕМ ДАННЫЕ РАСЧЕТОВ
        await calculation_msg.edit_text(
            f"✅ *Расчеты завершены!*",
            parse_mode="Markdown"
        )

        await message.answer(
            f"📊 *Данные расчетов на {target_date.strftime('%d.%m.%Y')}:*",
            parse_mode="Markdown"
        )
        await message.answer(result['user_data'], parse_mode="Markdown")

        # 3. ЗАПУСКАЕМ AI РЕКОМЕНДАЦИИ АСИНХРОННО (после показа расчетов)
        ai_notification_msg = await message.answer(
            "🤖 *AI анализирует данные...*\n"
            "Рекомендации придут отдельным сообщением в течение 3 минут\n"
            "Вы можете продолжать пользоваться ботом 🚀",
            parse_mode="Markdown"
        )

        # Запускаем асинхронную задачу для AI рекомендаций
        telegram_id = message.from_user.id

        # Сохраняем информацию о активном запросе
        active_ai_requests[telegram_id] = {
            'started_at': datetime.now(),
            'target_date': target_date
        }

        # Запускаем асинхронную задачу с ДАННЫМИ ИЗ РЕЗУЛЬТАТА
        asyncio.create_task(
            send_ai_recommendations_async(
                telegram_id,
                target_date,
                result['prediction_data'],  # ✅ ИСПОЛЬЗУЕМ УЖЕ РАССЧИТАННЫЕ ДАННЫЕ
                result['user_profile'],
                message
            )
        )

        # Удаляем уведомление через несколько секунд
        await asyncio.sleep(3)
        try:
            await ai_notification_msg.delete()
        except:
            pass  # Не критично, если не удалось удалить

        # 4. ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ СРАЗУ
        await message.answer(
            "🎯 *Можете продолжать пользоваться ботом!*\n"
            "AI рекомендации придут отдельным сообщением 📨",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения данных на {target_date}: {e}")
        try:
            await calculation_msg.delete()
        except:
            pass

        await message.answer(
            "❌ *Произошла ошибка при формировании данных*\n"
            "Попробуйте позже или обратитесь в поддержку.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )


@router.message(lambda message: message.text == "📈 Статус данных")
async def cmd_status(message: types.Message):
    """Проверка статуса данных пользователя"""
    try:
        status = await assistant.get_user_data_status(message.from_user.id)

        status_text = "📊 *Статус ваших данных:*\n\n"

        if status['is_complete']:
            status_text += "✅ *Все данные собраны и готовы к использованию*\n\n"
        else:
            status_text += "❌ *Не все данные собраны*\n\n"

        status_text += f"• Основные данные: {'✅' if status['has_basic_data'] else '❌'}\n"
        status_text += f"• Натальная карта: {'✅' if status['has_natal_chart'] else '❌'}\n"
        status_text += f"• Психоматрица: {'✅' if status['has_psyho_matrix'] else '❌'}\n"
        status_text += f"• Биоритмы: {'✅' if status['has_biorhythms'] else '❌'}\n\n"

        # Проверяем активные AI запросы
        active_request = active_ai_requests.get(message.from_user.id)
        if active_request:
            elapsed = datetime.now() - active_request['started_at']
            minutes_elapsed = int(elapsed.total_seconds() / 60)
            status_text += f"🔄 *AI анализ запущен:* {active_request['target_date'].strftime('%d.%m.%Y')}\n"
            status_text += f"⏱️ *Прошло времени:* {minutes_elapsed} мин.\n\n"

        if not status['is_complete']:
            status_text += "Нажмите '📊 Расчет натальной карты' для сбора недостающих данных"

        await message.answer(status_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await message.answer(
            "❌ Не удалось проверить статус данных",
            reply_markup=get_main_keyboard()
        )


@router.message(lambda message: message.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам бота"""
    help_text = """
📋 *Доступные команды:*

/start - Начать работу с ботом
/status - Проверить статус ваших данных  
/help - Показать эту справку

*Основные действия:*

📊 *Расчет натальной карты* - Собрать или обновить ваши данные
📅 *Получить рекомендации* - Получить расчеты и AI рекомендации на выбранную дату
📈 *Статус данных* - Проверить статус собранных данных

*Выбор даты:*
• 📅 *Сегодня* - данные на текущий день
• 📅 *Завтра* - данные на следующий день  
• 📅 *Выбрать дату* - произвольная дата (ГГГГ-ММ-ДД)

*Как это работает:*
1. 📊 *Данные расчетов* показываются сразу (2-5 секунд) ⚡
2. 🤖 *AI рекомендации* приходят отдельным сообщением (1-3 минуты) 📨
3. 🎯 *Вы можете продолжать* пользоваться ботом во время AI анализа
4. 📱 *Рекомендации придут* даже если вы выйдете из чата

*Внимание:* AI рекомендации будут отправлены вам даже если вы закроете бота!
    """

    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@router.message(Command("status"))
async def cmd_status_command(message: types.Message):
    """Алиас для команды /status"""
    await cmd_status(message)


@router.message()
async def handle_other_messages(message: types.Message, state: FSMContext):
    """Обработка всех остальных сообщений"""
    current_state = await state.get_state()

    if current_state:
        # Если есть активное состояние, предлагаем вернуться в меню
        await message.answer(
            "Завершите текущее действие или вернитесь в меню:",
            reply_markup=get_back_keyboard()
        )
    else:
        # Если нет активного состояния, показываем главное меню
        await message.answer(
            "Выберите действие из меню ниже:",
            reply_markup=get_main_keyboard()
        )
