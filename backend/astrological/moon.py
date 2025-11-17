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
