import os
import time
import requests
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

# ============================================================================
# НАСТРОЙКИ
# ============================================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
}

URL = "https://suspilne.media/rivne/latest/"

# ============================================================================
# ЗАПРОС И СОХРАНЕНИЕ
# ============================================================================

print("="*60)
print("📡 Загрузка страницы suspilne.media")
print("="*60)

try:
    # Делаем запрос с имитацией Chrome
    print(f"Запрос: {URL}")
    response = curl_requests.get(URL, headers=HEADERS, timeout=30, impersonate="chrome120")
    
    print(f"Статус: {response.status_code}")
    print(f"Длина: {len(response.text)} байт")
    
    if response.status_code == 200:
        # Парсим HTML и ищем контейнер
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.find("main", id="main_content", class_="l-main-content")
        
        if main_content:
            content_html = str(main_content)
            
            # Сохраняем в файл
            with open("suspilne_content.txt", "w", encoding="utf-8") as f:
                f.write(content_html)
            
            print("\n✅ Контент сохранен в suspilne_content.txt")
            print(f"   Размер: {len(content_html)} символов")
            
            # Показываем структуру
            print("\n📋 СТРУКТУРА КОНТЕЙНЕРА:")
            print("="*60)
            
            # Считаем элементы внутри
            articles = main_content.find_all("article", class_=lambda x: x and "c-article-card" in x)
            print(f"Статей в контейнере: {len(articles)}")
            
            # Заголовки первых 5 статей
            for i, art in enumerate(articles[:5], 1):
                link_tag = art.find("a", class_=lambda x: x and "headline" in x)
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    print(f"{i}. {title}")
            
            print("="*60)
            
        else:
            print("\n❌ Контейнер <main id='main_content' class='l-main-content'> не найден")
            print("💾 Сохраняю полный HTML для диагностики")
            with open("suspilne_full_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("   Сохранен как suspilne_full_page.html")
    
    else:
        print(f"\n❌ Ошибка: статус {response.status_code}")
        print("💾 Сохраняю ответ для диагностики")
        with open("suspilne_error_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("   Сохранен как suspilne_error_response.html")

except Exception as e:
    print(f"\n❌ Ошибка: {e}")

print("\n" + "="*60)
print("🏁 ЗАВЕРШЕНО")
print("="*60)
