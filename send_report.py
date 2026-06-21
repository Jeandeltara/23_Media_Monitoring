import os
import json
import glob
import sys
import gspread

def upload_latest_report():
    print("Запуск модуля отправки на Google Диск через gspread...")
    
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
        # Он автоматически запрашивает права и на Таблицы, и на Диск (Drive)
        gc = gspread.service_account_from_dict(creds_dict)
        
        # 3. Целевая папка
        FOLDER_ID = "1HLX_PykEsDvuOpp7gGnEoTaTYN49T050"  # ID твоей папки
        
        print("🚀 Чтение и отправка файла в Google Drive...")
        
        # Читаем содержимое отчета
        with open(latest_report, "r", encoding="utf-8") as f:
            file_content = f.read()

        # Используем встроенный в gspread клиент Диска для создания текстового файла
        # Метод .client.drive.files().create выполняет нужный обход ограничений
        gc.client.drive.files().create(
            body={
                'name': file_name,
                'parents': [FOLDER_ID],
                'mimeType': 'text/plain'
            },
            media_body=file_content
        )
        
        print(f"✅ Успех! Файл успешно загружен на Google Диск через gspread-bypass.")

    except Exception as e:
        print(f"❌ Произошла ошибка во время отправки через gspread: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_latest_report()
