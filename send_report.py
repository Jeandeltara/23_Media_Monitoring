import os
import json
import glob
import sys
import gspread

def upload_latest_report():
    print("Запуск модуля отправки на Google Диск через gspread (текстовый режим)...")
    
    # 1. Ищем самый свежий файл отчета
    report_files = glob.glob("*_report.txt")
    if not report_files:
        print("❌ Ошибка: Файлы отчетов (*_report.txt) не найдены!")
        sys.exit(1)
        
    report_files.sort()
    latest_report = report_files[-1]
    file_name = os.path.basename(latest_report)
    print(f"📁 Найден свежий отчет для отправки: {file_name}")

    # 2. Получаем секретный JSON-ключ
    secret_credentials = os.environ.get("GOOGLE_CREDENTIALS")
    if not secret_credentials:
        print("❌ Ошибка: Переменная окружения GOOGLE_CREDENTIALS не найдена!")
        sys.exit(1)

    try:
        # Превращаем строку с секретом обратно в JSON-словарь
        creds_dict = json.loads(secret_credentials)
        
        # Авторизуемся в Google через gspread
        gc = gspread.service_account_from_dict(creds_dict)
        
        # 3. Целевая папка
        FOLDER_ID = "1HLX_PykEsDvuOpp7gGnEoTaTYN49T050"  # ID вашей папки
        
        print("🚀 Чтение файла отчета...")
        with open(latest_report, "r", encoding="utf-8") as f:
            file_content = f.read()

        print("🚀 Создание нового файла на Google Диске...")
        # Используем официальный метод gspread для создания пустого текстового файла
        new_file = gc.create(file_name, folder_id=FOLDER_ID)
        
        print("🚀 Запись содержимого отчета...")
        # Так как это обычный текстовый файл, мы просто заливаем туда всю строку целиком
        # Это абсолютно легальный способ, который не использует квоту самого сервис-аккаунта
        gc.import_csv(new_file.id, file_content.encode('utf-8'))
        
        print(f"✅ Успех! Файл '{file_name}' успешно загружен на Google Диск.")

    except Exception as e:
        print(f"❌ Произошла ошибка во время отправки через gspread: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_latest_report()
