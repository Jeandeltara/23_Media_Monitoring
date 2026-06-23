import os
import re
from datetime import datetime, timedelta

def remove_old_reports():
    # Вычисляем дату, которая была ровно 3 дня назад
    target_date = datetime.now() - timedelta(days=3)
    # Форматируем её в YYMMDD (например, 260621)
    date_prefix = target_date.strftime("%y%m%d")
    
    print(f"Ищу файлы отчетов за дату: {target_date.strftime('%Y-%m-%d')} (префикс: {date_prefix})")
    
    # Регулярное выражение для проверки точного соответствия формата имени файла
    # YYMMDD_hhmm_report.txt
    report_pattern = re.compile(rf"^{date_prefix}_\d{{4}}_report\.txt$")
    
    deleted_count = 0
    
    # Обходим файлы в текущей корневой директории
    for filename in os.listdir("."):
        if report_pattern.match(filename):
            try:
                os.remove(filename)
                print(f"  [Удален] файл: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"  [Ошибка] Не удалось удалить {filename}: {e}")
                
    print(f"Очистка завершена. Всего удалено файлов: {deleted_count}")

if __name__ == "__main__":
    remove_old_reports()
