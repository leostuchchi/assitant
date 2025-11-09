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