#!/usr/bin/env python3
"""
ПОЛНАЯ ДИАГНОСТИКА СЕТИ И UVICORN
"""

import socket
import subprocess
import requests
import os


def full_network_debug():
    print("🔍 ПОЛНАЯ ДИАГНОСТИКА СЕТИ UVICORN")

    # 1. Проверка портов на разных интерфейсах
    print("\n1. 🌐 ПРОВЕРКА ПОРТОВ НА РАЗНЫХ ИНТЕРФЕЙСАХ:")
    interfaces = [
        ('0.0.0.0', 'все интерфейсы'),
        ('127.0.0.1', 'localhost'),
        ('localhost', 'DNS localhost')
    ]

    for host, desc in interfaces:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, 8000))
        sock.close()
        status = "✅ ОТКРЫТ" if result == 0 else "❌ ЗАКРЫТ"
        print(f"   {host:15} ({desc:20}): {status}")

    # 2. Проверка сетевых соединений через ss
    print("\n2. 📡 СЕТЕВЫЕ СОЕДИНЕНИЯ:")
    try:
        result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
        port_lines = [line for line in result.stdout.split('\n') if ':8000' in line]
        if port_lines:
            for line in port_lines:
                print(f"   {line}")
                if '127.0.0.1:8000' in line:
                    print("      ❌ Слушает только на 127.0.0.1!")
                elif '0.0.0.0:8000' in line:
                    print("      ✅ Слушает на 0.0.0.0!")
        else:
            print("   ❌ Порт 8000 не найден в ss")
    except Exception as e:
        print(f"   ⚠️ Ошибка ss: {e}")

    # 3. Тестирование API изнутри контейнера
    print("\n3. 🎯 ТЕСТИРОВАНИЕ API ИЗНУТРИ КОНТЕЙНЕРА:")
    test_urls = [
        "http://0.0.0.0:8000/",
        "http://127.0.0.1:8000/",
        "http://localhost:8000/"
    ]

    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"   ✅ {url}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"      📦 {data.get('message', 'OK')}")
        except Exception as e:
            print(f"   ❌ {url}: {e}")

    # 4. Проверка конфигурации uvicorn
    print("\n4. ⚙️ КОНФИГУРАЦИЯ UVICORN:")
    try:
        import uvicorn
        from backend.api_entrypoint import app

        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        print(f"   ✅ Uvicorn config: host={config.host}, port={config.port}")

        # Попробуем создать сервер
        server = uvicorn.Server(config)
        print("   ✅ Сервер создан успешно")

    except Exception as e:
        print(f"   ❌ Ошибка конфигурации: {e}")


if __name__ == "__main__":
    full_network_debug()