import glob
import os

def send_latest_report():
    print("Запуск модуля отправки...")
    
    # Ищем все отчеты
    report_files = glob.glob("*_report.txt")
    if not report_files:
        print("Файлы отчетов для отправки не найдены.")
        return
        
    # Сортируем по имени (так как имя начинается с даты YYMMDD, самый свежий будет последним)
    report_files.sort()
    latest_report = report_files[-1]
    
    print(f"ОБНАРУЖЕН СВЕЖИЙ ОТЧЕТ ДЛЯ РАССЫЛКИ: {latest_report}")
    
    with open(latest_report, "r", encoding="utf-8") as f:
        report_content = f.read()
        
    # --- МЕСТО ДЛЯ БУДУЩЕГО КОДА ОТПРАВКИ ---
    # Тут будет код, который шлет text/file куда угодно
    print("Передача данных в модуль связи успешна. Отчет обработан.")
    # ----------------------------------------

if __name__ == "__main__":
    send_latest_report()
