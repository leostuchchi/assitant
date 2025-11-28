import os
import requests


def check_config():
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ ПОРТОВ")

    # Проверка .env файла
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            api_port = [line for line in content.split('\n') if 'API_PORT' in line]
            api_base_url = [line for line in content.split('\n') if 'API_BASE_URL' in line]
            database_url = [line for line in content.split('\n') if 'DATABASE_URL' in line]

            print("📄 .env файл:")
            for line in api_port + api_base_url + database_url:
                print(f"  {line}")

    # Проверка доступности API
    print(f"\n🔌 Тестирование подключения...")
    try:
        response = requests.get('http://localhost:8001/', timeout=5)
        print(f"✅ API доступен на localhost:8001")
        print(f"📦 Ответ: {response.json()}")
    except Exception as e:
        print(f"❌ API недоступен на localhost:8001: {e}")

    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    print(f"• API_PORT должен быть 8000 (внутри контейнера)")
    print(f"• API_BASE_URL должен быть http://localhost:8001 (снаружи)")
    print(f"• DATABASE_URL должен использовать 'postgres' вместо 'localhost'")


if __name__ == "__main__":
    check_config()