import os
import glob
from datetime import datetime, timedelta

# Сколько дней хранить файлы в репозитории
DAYS_TO_KEEP = 7

def clean_old_reports():
    print("Запуск модуля очистки старых отчетов...")
    now = datetime.now()
    cutoff_date = now - timedelta(days=DAYS_TO_KEEP)
    
    # Находим все файлы отчетов в текущей папке
    report_files = glob.glob("*_report.txt")
    
    for file_path in report_files:
        file_name = os.path.basename(file_path)
        # Имя файла имеет формат: YYMMDD_HHMM_report.txt (длина даты-времени — 11 символов)
        try:
            date_part = file_name.split('_')[0] # Получаем YYMMDD
            file_date = datetime.strptime(date_part, "%y%m%d")
            
            if file_date < cutoff_date:
                os.remove(file_path)
                print(f"🗑️ Удален старый отчет: {file_name}")
        except Exception as e:
            print(f"Не удалось обработать файл {file_name}: {e}")

if __name__ == "__main__":
    clean_old_reports()
