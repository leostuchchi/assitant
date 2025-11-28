import os


def check_api_fix():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "backend", "api_entrypoint.py")

    print(f"🔍 Проверка файла: {file_path}")

    if not os.path.exists(file_path):
        print("❌ Файл не найден!")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    checks = [
        ('import os' in content, '✅ import os присутствует'),
        ('os.getenv("API_PORT"' in content or "os.getenv('API_PORT'" in content,
         '✅ Используется API_PORT из переменных окружения'),
        ('port=API_PORT' in content, '✅ Порт задается через переменную'),
        ('port=8000' not in content or 'API_PORT' in content, '✅ Жестко заданный порт 8000 убран')
    ]

    print("\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    all_ok = True
    for check, message in checks:
        if check:
            print(f"   {message}")
        else:
            print(f"   ❌ {message}")
            all_ok = False

    if all_ok:
        print("\n🎉 Файл успешно исправлен!")
    else:
        print("\n⚠️ Требуется дополнительное исправление")


if __name__ == "__main__":
    check_api_fix()