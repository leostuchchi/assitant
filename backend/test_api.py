#!/usr/bin/env python3
"""
ДИАГНОСТИКА ПРОБЛЕМЫ С ПОРТОМ 8001
"""

import subprocess
import requests
import socket
import os
from datetime import datetime


def run_command(cmd, description=""):
    """Выполнить команду и вернуть результат"""
    print(f"\n🔍 {description}")
    print(f"   Команда: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print("   ✅ Успех")
            return result.stdout
        else:
            print(f"   ❌ Ошибка: {result.stderr}")
            return None
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return None


def diagnose_docker():
    """Диагностика Docker контейнеров"""
    print("🐳 ДИАГНОСТИКА DOCKER КОНТЕЙНЕРОВ")

    # Статус контейнеров
    run_command(["docker", "compose", "ps"], "Статус сервисов")

    # Проброс портов
    run_command(["docker", "compose", "port", "astra_api", "8000"], "Проброс портов astra_api")

    # Логи API
    logs = run_command(["docker", "compose", "logs", "astra_api", "--tail=20"], "Логи astra_api")
    if logs:
        print("   📋 Последние логи API:")
        for line in logs.split('\n')[-10:]:
            print(f"      {line}")


def diagnose_ports():
    """Диагностика портов"""
    print("\n🔌 ДИАГНОСТИКА ПОРТОВ")

    # Проверка порта 8001 на хосте
    print("   Проверка порта 8001 на хосте...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8001))
    sock.close()

    if result == 0:
        print("   ✅ Порт 8001 открыт на хосте")
    else:
        print("   ❌ Порт 8001 НЕ открыт на хосте")

    # Проверка что слушает порты
    run_command(["netstat", "-tulpn", "|", "grep", "800"], "Слушающие порты 800x")
    run_command(["docker", "port", "astra_api"], "Порты контейнера astra_api")


def diagnose_network():
    """Диагностика сети"""
    print("\n🌐 ДИАГНОСТИКА СЕТИ")

    # Проверка DNS разрешения
    try:
        socket.gethostbyname('localhost')
        print("   ✅ localhost разрешается")
    except:
        print("   ❌ localhost не разрешается")

    # Проверка подключения к localhost
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('127.0.0.1', 8001))
    sock.close()

    if result == 0:
        print("   ✅ Подключение к 127.0.0.1:8001 возможно")
    else:
        print("   ❌ Подключение к 127.0.0.1:8001 невозможно")


def test_different_urls():
    """Тестирование разных URL"""
    print("\n🎯 ТЕСТИРОВАНИЕ РАЗНЫХ URL")

    urls = [
        "http://localhost:8001/",
        "http://127.0.0.1:8001/",
        "http://0.0.0.0:8001/",
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"   ✅ {url}: {response.status_code}")
            if response.status_code == 200:
                print(f"      📦 {response.json()}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {url}: Connection refused")
        except Exception as e:
            print(f"   ❌ {url}: {e}")


def check_config_files():
    """Проверка конфигурационных файлов"""
    print("\n📄 ПРОВЕРКА КОНФИГУРАЦИОННЫХ ФАЙЛОВ")

    # Проверка docker-compose.yml
    if os.path.exists('docker-compose.yml'):
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            if '8001:8000' in content:
                print("   ✅ docker-compose.yml: порт 8001:8000 настроен")
            else:
                print("   ❌ docker-compose.yml: порт 8001:8000 НЕ настроен")
                # Покажем что есть
                for line in content.split('\n'):
                    if 'port' in line.lower() and '800' in line:
                        print(f"      Найден: {line.strip()}")

    # Проверка .env файла
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            api_lines = [line for line in content.split('\n') if 'API' in line or 'PORT' in line]
            if api_lines:
                print("   📋 .env файл (API настройки):")
                for line in api_lines:
                    print(f"      {line.strip()}")


def quick_fix_suggestions():
    """Предложения по быстрому исправлению"""
    print("\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ")

    print("   1. 🔄 Перезапуск контейнеров:")
    print("      docker compose down && docker compose up -d")

    print("   2. 🐛 Проверка запуска API:")
    print("      docker compose logs astra_api --tail=10")

    print("   3. 🔧 Проверка проброса портов:")
    print("      docker compose port astra_api 8000")

    print("   4. 🌐 Проверка сети Docker:")
    print("      docker network ls")
    print("      docker network inspect astra_default")

    print("   5. ⚡ Альтернативный порт:")
    print("      Измените в docker-compose.yml на '8002:8000'")


def main():
    print("🚀 ПОЛНАЯ ДИАГНОСТИКА ПРОБЛЕМЫ С API")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    diagnose_docker()
    diagnose_ports()
    diagnose_network()
    check_config_files()
    test_different_urls()
    quick_fix_suggestions()


if __name__ == "__main__":
    main()