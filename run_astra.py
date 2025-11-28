#!/usr/bin/env python3
"""
Astra Project Runner - запуск из корня проекта
"""

import os
import sys
import subprocess


def main():
    """Запуск Astra API"""
    # Определяем путь к backend
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')

    if not os.path.exists(backend_dir):
        print(f"❌ Папка backend не найдена: {backend_dir}")
        return

    # Переходим в папку backend и запускаем
    os.chdir(backend_dir)

    print("🚀 Запуск Astra Calculations API...")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    print("🌐 Сервер будет доступен по: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print("-" * 50)

    # Запускаем uvicorn
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api_entrypoint:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")


if __name__ == "__main__":
    main()