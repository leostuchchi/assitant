import requests
import json
from datetime import datetime
import time
import os

# Для тестирования внутри Docker сети
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_USER_ID = 5960877187


def wait_for_api(timeout=60):
    """Ожидание запуска API"""
    print("⏳ Ожидание запуска API сервера...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API сервер запущен и готов к тестированию")
                return True
        except:
            pass

        print(".", end="", flush=True)
        time.sleep(2)

    print("\n❌ Таймаут ожидания API сервера")
    return False


def test_endpoint(name, endpoint, method="GET", json_data=None):
    """Тестирование одного эндпоинта"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n🔍 {name}")
        print(f"📡 URL: {url}")

        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=json_data, timeout=10)

        print(f"📊 Статус: {response.status_code}")

        if response.status_code == 200:
            print("✅ Успех")
            try:
                data = response.json()
                print(f"📦 Данные: {json.dumps(data, indent=2, ensure_ascii=False, default=str)[:500]}...")
            except:
                print(f"📄 Текст: {response.text[:200]}...")
            return True
        else:
            print("❌ Ошибка HTTP")
            print(f"💬 Ответ: {response.text[:200]}...")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Таймаут: {e}")
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return False


def main():
    print("🚀 ТЕСТИРОВАНИЕ ASTRA API В DOCKER")
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Base URL: {BASE_URL}")

    # Ожидаем запуск API
    if not wait_for_api():
        print("\n🔧 Рекомендуемые действия:")
        print("1. Запустите сервисы: docker-compose up -d")
        print("2. Проверьте логи API: docker-compose logs astra_api")
        print("3. Убедитесь что контейнер запущен: docker-compose ps")
        return

    print("\n" + "=" * 60)
    print("НАЧАЛО ТЕСТИРОВАНИЯ")
    print("=" * 60)

    # Тестируем эндпоинты
    endpoints = [
        ("GET /", "/"),
        ("GET /health", "/health"),
        ("GET /api/v1/version", "/api/v1/version"),
        ("GET /api/v1/system/status", "/api/v1/system/status"),
        (f"GET /api/v1/users/{TEST_USER_ID}/status", f"/api/v1/users/{TEST_USER_ID}/status"),
        (f"GET /api/v1/biorhythms/{TEST_USER_ID}", f"/api/v1/biorhythms/{TEST_USER_ID}"),
    ]

    success_count = 0
    for name, endpoint in endpoints:
        if test_endpoint(name, endpoint):
            success_count += 1

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print(f"✅ Успешных тестов: {success_count}/{len(endpoints)}")

    if success_count == len(endpoints):
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️ Есть проблемы с некоторыми эндпоинтами")

    print(f"⏰ Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()