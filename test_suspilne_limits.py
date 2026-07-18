import time
import random
import sys
import subprocess
from curl_cffi import requests as curl_requests
from bs4 import BeautifulSoup

# Установка pandas если не установлен
try:
    import pandas as pd
except ImportError:
    print("🔄 Installing pandas...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
}

BASE_URL = "https://suspilne.media"
RIVNE_URL = f"{BASE_URL}/rivne/latest/"

print("="*70)
print("🔍 ТЕСТ ЛИМИТОВ SUSPILNE.MEDIA")
print("="*70)

# ===== ТЕСТ 1: СТРАНИЦЫ =====
print("\n📄 ТЕСТ 1: СКОЛЬКО СТРАНИЦ МОЖНО ОТКРЫТЬ")
print("-"*70)

page_results = []
for page in range(1, 15):
    url = f"{RIVNE_URL}?page={page}"
    try:
        response = curl_requests.get(url, headers=HEADERS, timeout=30, impersonate="chrome120")
        status = response.status_code
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
        
        print(f"Page {page}: status={status}, articles={len(articles)}")
        page_results.append({"page": page, "status": status, "articles": len(articles)})
        
        if status == 403:
            print("🚫 БЛОКИРОВКА!")
            break
            
        time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:
        print(f"Page {page}: ERROR - {e}")
        break

# ===== ТЕСТ 2: СТАТЬИ =====
print("\n\n📄 ТЕСТ 2: СКОЛЬКО СТАТЕЙ МОЖНО ПРОЧИТАТЬ")
print("-"*70)

# Собираем ссылки
try:
    response = curl_requests.get(f"{RIVNE_URL}?page=1", headers=HEADERS, timeout=30, impersonate="chrome120")
    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_=lambda x: x and "c-article-card" in x)
    
    links = []
    for art in articles[:20]:
        link_tag = art.find("a", class_=lambda x: x and "headline" in x)
        if link_tag:
            href = link_tag.get("href")
            if href:
                if href.startswith("/"):
                    href = BASE_URL + href
                links.append(href)
    
    print(f"Найдено {len(links)} ссылок")
    
except Exception as e:
    print(f"Ошибка сбора ссылок: {e}")
    links = []

article_results = []
for i, link in enumerate(links, 1):
    try:
        response = curl_requests.get(link, headers=HEADERS, timeout=30, impersonate="chrome120")
        status = response.status_code
        
        print(f"Article {i}: status={status}")
        article_results.append({"article": i, "status": status})
        
        if status == 403:
            print("🚫 БЛОКИРОВКА!")
            break
            
        time.sleep(random.uniform(1, 3))
    except Exception as e:
        print(f"Article {i}: ERROR - {e}")
        break

# ===== ВЫВОД =====
print("\n" + "="*70)
print("📊 РЕЗУЛЬТАТЫ")
print("="*70)

if page_results:
    df_pages = pd.DataFrame(page_results)
    print("\nСТРАНИЦЫ:")
    print(df_pages.to_string(index=False))
    
    max_pages = df_pages[df_pages["status"] == 200]["page"].max()
    print(f"\n✅ Максимум страниц: {max_pages if max_pages else 0}")

if article_results:
    df_articles = pd.DataFrame(article_results)
    print("\nСТАТЬИ:")
    print(df_articles.to_string(index=False))
    
    max_articles = df_articles[df_articles["status"] == 200]["article"].max()
    print(f"\n✅ Максимум статей: {max_articles if max_articles else 0}")

print("\n" + "="*70)
print("🏁 ТЕСТ ЗАВЕРШЕН")
