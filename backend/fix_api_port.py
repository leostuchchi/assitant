#!/usr/bin/env python3
"""
Скрипт для исправления порта в api_entrypoint.py
"""

import os


def fix_api_entrypoint():
    file_path = "backend/api_entrypoint.py"

    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Заменяем жестко заданный порт на переменную окружения
    old_code = '''if __name__ == "__main__":
    uvicorn.run(
        "api_entrypoint:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )'''

    new_code = '''if __name__ == "__main__":
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
    )'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ api_entrypoint.py успешно исправлен!")
        print("📋 Изменения:")
        print("   - Добавлен import os")
        print("   - Порт теперь берется из API_PORT переменной окружения")
        print("   - Добавлен вывод информации о запуске")
    else:
        print("❌ Код для замены не найден. Возможно файл уже исправлен.")


if __name__ == "__main__":
    fix_api_entrypoint()